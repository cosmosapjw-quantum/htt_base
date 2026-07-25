"""Fail-closed package-topology helpers for PR-121 hermetic replay.

The functions in this module deliberately use the Python standard library,
with the declared ``tomli`` compatibility dependency on Python 3.10. They
inspect source snapshots and built archives; they do not import the project
being inspected and therefore cannot be made green by the current
editable-install state.

This is COMMON-owned reproducibility infrastructure.  A successful topology
check is implementation evidence only, not scientific validation.
"""
from __future__ import annotations

from dataclasses import dataclass
import base64
import csv
from email.parser import Parser
import fnmatch
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
from typing import Iterable, Mapping, Sequence
import zipfile

try:  # Python 3.11+ stdlib; bass-py metadata supplies tomli on Python 3.10.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by import fallback probe
    import tomli as tomllib


class PackageTopologyError(RuntimeError):
    """Raised when a source archive, wheel, or receipt fails closed."""


_FORBIDDEN_CACHE_COMPONENTS = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "__pycache__",
        "build",
        "dist",
    }
)


def canonical_json_bytes(value: object) -> bytes:
    """Return the repository's compact canonical JSON representation."""

    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_ephemeral_paths(value: str) -> str:
    """Tokenize backend/pip random directory basenames in process evidence."""

    normalized = re.sub(r"(?<=/)\.tmp-[A-Za-z0-9_-]+", ".tmp-$ID", value)
    normalized = re.sub(
        r"(?<=/)pip-(build-env|ephem-wheel-cache|install|modern-metadata|unpack|wheel)-[A-Za-z0-9_-]+",
        r"pip-\1-$ID",
        normalized,
    )
    normalized = re.sub(
        r"(pip-ephem-wheel-cache-\$ID/wheels/)[^\s]+",
        r"\1$WHEEL_KEY",
        normalized,
    )
    normalized = re.sub(
        r"(Created wheel for [^\n]+?\bsize=)\d+",
        r"\1$SIZE",
        normalized,
    )
    normalized = re.sub(r"\bsha256=[0-9a-fA-F]{64}\b", "sha256=$EPHEMERAL", normalized)
    return normalized


def validate_archive_path(raw_path: str) -> PurePosixPath:
    """Validate one archive path without touching the filesystem.

    Both ZIP and tar archives use POSIX member names.  Backslashes are rejected
    rather than normalized because accepting them would make traversal checks
    platform-dependent.
    """

    if not raw_path or "\\" in raw_path or "\x00" in raw_path:
        raise PackageTopologyError(f"unsafe archive path: {raw_path!r}")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or raw_path.startswith("/"):
        raise PackageTopologyError(f"absolute archive path: {raw_path!r}")
    if not path.parts or raw_path != path.as_posix():
        raise PackageTopologyError(f"noncanonical archive path: {raw_path!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise PackageTopologyError(f"traversing archive path: {raw_path!r}")
    if path.parts and path.parts[0].endswith(":"):
        raise PackageTopologyError(f"drive-qualified archive path: {raw_path!r}")
    return path


def is_generated_cache_path(path: PurePosixPath) -> bool:
    for component in path.parts:
        lowered = component.lower()
        if lowered in _FORBIDDEN_CACHE_COMPONENTS:
            return True
        if lowered.endswith((".egg-info", ".dist-info")):
            return True
        if lowered.endswith((".pyc", ".pyo")):
            return True
    return False


def validate_source_member(path: PurePosixPath) -> None:
    """Reject VCS, untracked-build-cache, and bytecode paths in a snapshot."""

    if is_generated_cache_path(path):
        raise PackageTopologyError(f"generated/cache path in source snapshot: {path}")


def safe_extract_git_archive(archive: Path, destination: Path) -> tuple[str, ...]:
    """Extract a Git-produced tar without trusting tar member paths or links."""

    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[str] = []
    with tarfile.open(archive, mode="r:*") as handle:
        for member in handle.getmembers():
            member_path = validate_archive_path(member.name.rstrip("/"))
            validate_source_member(member_path)
            target = destination.joinpath(*member_path.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise PackageTopologyError(
                    f"non-regular member in Git snapshot: {member.name!r}"
                )
            source = handle.extractfile(member)
            if source is None:
                raise PackageTopologyError(f"cannot read snapshot member: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())
            target.chmod(0o755 if member.mode & stat.S_IXUSR else 0o644)
            extracted.append(member_path.as_posix())
    if not extracted:
        raise PackageTopologyError("Git snapshot contains no regular files")
    return tuple(sorted(extracted))


def tree_manifest(root: Path) -> tuple[dict[str, object], ...]:
    """Return a deterministic manifest for regular files below *root*."""

    if not root.is_dir():
        raise PackageTopologyError(f"tree root does not exist: {root}")
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        validate_archive_path(relative.as_posix())
        validate_source_member(relative)
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise PackageTopologyError(f"non-regular path in source tree: {relative}")
        rows.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "executable": bool(mode & stat.S_IXUSR),
                "size": path.stat().st_size,
            }
        )
    if not rows:
        raise PackageTopologyError("source tree contains no regular files")
    return tuple(rows)


def tree_hash(root: Path) -> str:
    return sha256_bytes(canonical_json_bytes(tree_manifest(root)))


@dataclass(frozen=True)
class SdistInspection:
    """Content-addressed description of one source distribution."""

    path: str
    distribution: str
    version: str
    sha256: str
    root: str
    payload_entries: tuple[str, ...]
    payload_hash: str
    requires_dist: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "distribution": self.distribution,
            "version": self.version,
            "sha256": self.sha256,
            "root": self.root,
            "payload_entries": list(self.payload_entries),
            "payload_hash": self.payload_hash,
            "requires_dist": list(self.requires_dist),
        }


def _validate_sdist_source_path(path: PurePosixPath) -> None:
    """Reject generated source caches while permitting root ``*.egg-info``.

    Setuptools creates a distribution-root ``*.egg-info`` directory while
    assembling an sdist.  It is packaging metadata, not source ownership, and
    is the sole exception to the normal generated-cache prohibition.
    """

    egg_info_positions = [
        index
        for index, component in enumerate(path.parts)
        if component.lower().endswith(".egg-info")
    ]
    if egg_info_positions:
        if egg_info_positions != [0]:
            raise PackageTopologyError(
                f"nested or repeated egg-info path in sdist: {path}"
            )
        tail = PurePosixPath(*path.parts[1:]) if len(path.parts) > 1 else None
        if tail is not None and is_generated_cache_path(tail):
            raise PackageTopologyError(f"generated/cache path in sdist: {path}")
        return
    if is_generated_cache_path(path):
        raise PackageTopologyError(f"generated/cache path in sdist: {path}")


def inspect_sdist(path: Path) -> SdistInspection:
    """Inspect an sdist without trusting member paths, links, or caches."""

    if not path.is_file() or not (
        path.name.endswith(".tar.gz") or path.name.endswith(".tar.bz2")
    ):
        raise PackageTopologyError(f"not a supported source distribution: {path}")

    payload_rows: list[tuple[str, str]] = []
    relative_entries: list[str] = []
    root_names: set[str] = set()
    normalized_members: set[str] = set()
    root_metadata: bytes | None = None
    with tarfile.open(path, mode="r:*") as archive:
        for member in archive.getmembers():
            normalized_name = member.name.rstrip("/")
            member_path = validate_archive_path(normalized_name)
            normalized = member_path.as_posix()
            if normalized in normalized_members:
                raise PackageTopologyError(
                    f"sdist contains duplicate member name: {normalized}"
                )
            normalized_members.add(normalized)
            root_names.add(member_path.parts[0])
            relative = (
                PurePosixPath(*member_path.parts[1:])
                if len(member_path.parts) > 1
                else None
            )
            if relative is not None:
                _validate_sdist_source_path(relative)
            if member.isdir():
                continue
            if not member.isfile():
                raise PackageTopologyError(
                    f"sdist contains non-regular member: {member.name!r}"
                )
            if len(member_path.parts) < 2:
                raise PackageTopologyError(
                    f"sdist file is not below a distribution root: {member.name!r}"
                )
            if relative is None:  # guarded by the length check above
                raise PackageTopologyError(f"invalid sdist member: {member.name!r}")
            source = archive.extractfile(member)
            if source is None:
                raise PackageTopologyError(f"cannot read sdist member: {member.name}")
            data = source.read()
            relative_name = relative.as_posix()
            relative_entries.append(relative_name)
            payload_rows.append((relative_name, sha256_bytes(data)))
            if relative_name == "PKG-INFO":
                root_metadata = data

    if len(root_names) != 1:
        raise PackageTopologyError(
            f"sdist must have exactly one distribution root, found {sorted(root_names)}"
        )
    if not relative_entries:
        raise PackageTopologyError("sdist contains no regular files")
    if root_metadata is None:
        raise PackageTopologyError("sdist lacks root PKG-INFO metadata")
    metadata = Parser().parsestr(root_metadata.decode("utf-8"))
    distribution = str(metadata.get("Name", "")).strip()
    version = str(metadata.get("Version", "")).strip()
    if not distribution or not version:
        raise PackageTopologyError("sdist PKG-INFO lacks Name/Version")
    return SdistInspection(
        path=path.name,
        distribution=distribution,
        version=version,
        sha256=sha256_file(path),
        root=next(iter(root_names)),
        payload_entries=tuple(sorted(relative_entries)),
        payload_hash=sha256_bytes(canonical_json_bytes(sorted(payload_rows))),
        requires_dist=tuple(str(value) for value in metadata.get_all("Requires-Dist", [])),
    )


def canonicalize_sdist(path: Path, *, source_date_epoch: int) -> dict[str, object]:
    """Repack a validated ``.tar.gz`` sdist with deterministic metadata.

    Setuptools can leak wall-clock PAX mtimes and host uid/gid names even when
    ``SOURCE_DATE_EPOCH`` is set.  Rebuilding both the tar members and gzip
    envelope makes the archive content-addressable without changing member
    paths or bytes.
    """

    if not isinstance(source_date_epoch, int) or isinstance(source_date_epoch, bool):
        raise PackageTopologyError("sdist source_date_epoch must be an integer")
    if source_date_epoch < 0 or source_date_epoch > 0xFFFFFFFF:
        raise PackageTopologyError("sdist source_date_epoch is outside gzip range")
    inspection_before = inspect_sdist(path)
    members: list[tuple[str, bool, bool, bytes]] = []
    seen: set[str] = set()
    with tarfile.open(path, mode="r:*") as archive:
        for member in archive.getmembers():
            raw_name = member.name.rstrip("/")
            normalized = validate_archive_path(raw_name).as_posix()
            if normalized in seen:
                raise PackageTopologyError(
                    f"sdist contains duplicate member name: {normalized}"
                )
            seen.add(normalized)
            if member.isdir():
                members.append((normalized, True, True, b""))
                continue
            if not member.isfile():
                raise PackageTopologyError(
                    f"sdist contains non-regular member: {member.name!r}"
                )
            source = archive.extractfile(member)
            if source is None:
                raise PackageTopologyError(f"cannot read sdist member: {member.name}")
            members.append(
                (normalized, False, bool(member.mode & stat.S_IXUSR), source.read())
            )

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, is_directory, executable, data in sorted(members):
            member = tarfile.TarInfo(name)
            member.uid = 0
            member.gid = 0
            member.uname = ""
            member.gname = ""
            member.mtime = source_date_epoch
            member.pax_headers = {}
            if is_directory:
                member.type = tarfile.DIRTYPE
                member.mode = 0o755
                member.size = 0
                archive.addfile(member)
            else:
                member.type = tarfile.REGTYPE
                member.mode = 0o755 if executable else 0o644
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

    gzip_buffer = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=gzip_buffer,
        mtime=source_date_epoch,
    ) as compressed:
        compressed.write(tar_buffer.getvalue())
    path.write_bytes(gzip_buffer.getvalue())
    path.chmod(0o644)

    inspection_after = inspect_sdist(path)
    if (
        inspection_after.payload_entries != inspection_before.payload_entries
        or inspection_after.payload_hash != inspection_before.payload_hash
        or inspection_after.distribution != inspection_before.distribution
        or inspection_after.version != inspection_before.version
        or inspection_after.requires_dist != inspection_before.requires_dist
    ):
        raise PackageTopologyError("sdist canonicalization changed semantic payload")
    return {
        "status": "pass",
        "sha256": inspection_after.sha256,
        "payload_hash": inspection_after.payload_hash,
        "member_count": len(members),
        "source_date_epoch": source_date_epoch,
        "uid_gid": 0,
        "names": "empty",
        "gzip_filename": "empty",
    }


_COMPAT_ROOT_METADATA = frozenset(
    {"MANIFEST.in", "PKG-INFO", "pyproject.toml", "setup.cfg", "setup.py"}
)
_COMPAT_EGG_INFO_METADATA = frozenset(
    {
        "PKG-INFO",
        "SOURCES.txt",
        "dependency_links.txt",
        "entry_points.txt",
        "namespace_packages.txt",
        "not-zip-safe",
        "requires.txt",
        "top_level.txt",
    }
)
_COMPAT_DOCUMENT_PREFIXES = (
    "AUTHORS",
    "CHANGELOG",
    "CHANGES",
    "COPYING",
    "LICENSE",
    "NOTICE",
    "README",
)


def _is_compatibility_document(filename: str) -> bool:
    upper = filename.upper()
    return any(
        upper == prefix
        or upper.startswith(f"{prefix}.")
        or upper.startswith(f"{prefix}-")
        or upper.startswith(f"{prefix}_")
        for prefix in _COMPAT_DOCUMENT_PREFIXES
    )


def _exact_requirement_rows(requirements: Sequence[str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for raw_requirement in requirements:
        compact = raw_requirement.replace(" ", "").replace("(", "").replace(")", "")
        if "==" not in compact or ";" in compact:
            continue
        name, version = compact.split("==", 1)
        rows.append((normalize_distribution_name(name), version.lower()))
    return rows


def validate_compatibility_sdist(
    inspection: SdistInspection,
    *,
    expected_distribution: str,
    exact_dependency: str | None = None,
    exact_version: str | None = None,
) -> None:
    """Enforce the fileless compatibility sdist's metadata-only allowlist."""

    if normalize_distribution_name(inspection.distribution) != normalize_distribution_name(
        expected_distribution
    ):
        raise PackageTopologyError(
            f"expected compatibility distribution {expected_distribution!r}, "
            f"got {inspection.distribution!r}"
        )

    egg_info_roots: set[str] = set()
    for raw_entry in inspection.payload_entries:
        entry = validate_archive_path(raw_entry)
        lowered_parts = tuple(part.lower() for part in entry.parts)
        if lowered_parts[0] in {"htt", "tests"}:
            raise PackageTopologyError(
                f"compatibility sdist contains forbidden source tree: {raw_entry}"
            )
        if entry.suffix.lower() == ".py" and raw_entry != "setup.py":
            raise PackageTopologyError(
                f"compatibility sdist contains forbidden Python source: {raw_entry}"
            )
        if len(entry.parts) == 1:
            filename = entry.name
            if filename not in _COMPAT_ROOT_METADATA and not _is_compatibility_document(
                filename
            ):
                raise PackageTopologyError(
                    f"compatibility sdist path is outside metadata/docs allowlist: {raw_entry}"
                )
            continue
        first = entry.parts[0]
        if not first.lower().endswith(".egg-info"):
            raise PackageTopologyError(
                f"compatibility sdist path is outside metadata/docs allowlist: {raw_entry}"
            )
        egg_info_roots.add(first)
        if len(entry.parts) != 2 or entry.parts[1] not in _COMPAT_EGG_INFO_METADATA:
            raise PackageTopologyError(
                f"compatibility sdist has undeclared egg-info payload: {raw_entry}"
            )
    if len(egg_info_roots) > 1:
        raise PackageTopologyError(
            f"compatibility sdist has multiple egg-info roots: {sorted(egg_info_roots)}"
        )
    for egg_info_root in egg_info_roots:
        stem = egg_info_root[: -len(".egg-info")]
        if normalize_distribution_name(stem) != normalize_distribution_name(
            expected_distribution
        ):
            raise PackageTopologyError(
                f"compatibility sdist has foreign egg-info root: {egg_info_root}"
            )
    if "pyproject.toml" not in inspection.payload_entries:
        raise PackageTopologyError("compatibility sdist lacks pyproject.toml")
    if exact_dependency is not None:
        if exact_version is None:
            raise PackageTopologyError("exact compatibility dependency needs a version")
        expected = (normalize_distribution_name(exact_dependency), exact_version.lower())
        if len(inspection.requires_dist) != 1:
            raise PackageTopologyError(
                "compatibility sdist must declare exactly one dependency; "
                f"found {inspection.requires_dist}"
            )
        if _exact_requirement_rows(inspection.requires_dist) != [expected]:
            raise PackageTopologyError(
                "compatibility sdist must have one exact dependency "
                f"{exact_dependency}=={exact_version}; found {inspection.requires_dist}"
            )


@dataclass(frozen=True)
class DeclaredPackageData:
    """One package-data file bound to its source bytes and wheel destination."""

    package: str
    source_path: str
    wheel_path: str
    sha256: str
    size: int

    def as_dict(self) -> dict[str, object]:
        return {
            "package": self.package,
            "source_path": self.source_path,
            "wheel_path": self.wheel_path,
            "sha256": self.sha256,
            "size": self.size,
        }


def _string_list(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise PackageTopologyError(f"{field} must be a list of non-empty strings")
    return tuple(value)


def declared_package_data(project_root: Path) -> tuple[DeclaredPackageData, ...]:
    """Resolve the exact ``tool.setuptools.package-data`` source-byte set.

    Package directories are located using the declared ``packages.find.where``
    roots.  Every include pattern must resolve to at least one regular tracked
    snapshot file; symlinks, path traversal, ambiguous package roots, and cache
    paths fail closed.
    """

    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file() or pyproject.is_symlink():
        raise PackageTopologyError(f"project lacks regular pyproject.toml: {project_root}")
    try:
        config = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        setuptools_config = config["tool"]["setuptools"]
    except (KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise PackageTopologyError(f"invalid setuptools configuration: {pyproject}") from exc
    if not isinstance(setuptools_config, dict):
        raise PackageTopologyError("tool.setuptools must be a table")
    raw_package_data = setuptools_config.get("package-data", {})
    if not isinstance(raw_package_data, dict):
        raise PackageTopologyError("tool.setuptools.package-data must be a table")
    raw_find = setuptools_config.get("packages", {}).get("find", {})
    if not isinstance(raw_find, dict):
        raise PackageTopologyError("tool.setuptools.packages.find must be a table")
    raw_where = raw_find.get("where", ["."])
    where = _string_list(raw_where, field="tool.setuptools.packages.find.where")
    roots: list[Path] = []
    for raw_root in where:
        if raw_root == ".":
            roots.append(project_root)
            continue
        relative_root = validate_archive_path(raw_root)
        validate_source_member(relative_root)
        roots.append(project_root.joinpath(*relative_root.parts))

    raw_excludes = setuptools_config.get("exclude-package-data", {})
    if not isinstance(raw_excludes, dict):
        raise PackageTopologyError("tool.setuptools.exclude-package-data must be a table")

    rows_by_wheel_path: dict[str, DeclaredPackageData] = {}
    for package, raw_patterns in sorted(raw_package_data.items()):
        if not isinstance(package, str) or not package or "*" in package:
            raise PackageTopologyError(
                f"package-data key must name one concrete package: {package!r}"
            )
        patterns = _string_list(
            raw_patterns, field=f"tool.setuptools.package-data.{package}"
        )
        package_relative = PurePosixPath(*package.split("."))
        candidates = [
            root.joinpath(*package_relative.parts)
            for root in roots
            if root.joinpath(*package_relative.parts).is_dir()
            and not root.joinpath(*package_relative.parts).is_symlink()
            and root.joinpath(*package_relative.parts, "__init__.py").is_file()
        ]
        if len(candidates) != 1:
            raise PackageTopologyError(
                f"package-data package {package!r} has {len(candidates)} source roots"
            )
        package_root = candidates[0]
        exclude_patterns: list[str] = []
        for exclude_key in ("*", package):
            if exclude_key in raw_excludes:
                declared_excludes = _string_list(
                    raw_excludes[exclude_key],
                    field=f"tool.setuptools.exclude-package-data.{exclude_key}",
                )
                for excluded in declared_excludes:
                    validate_archive_path(excluded)
                exclude_patterns.extend(declared_excludes)
        for pattern in patterns:
            pattern_path = validate_archive_path(pattern)
            validate_source_member(pattern_path)
            matches = sorted(package_root.glob(pattern))
            regular_matches: list[Path] = []
            for match in matches:
                if match.is_symlink():
                    raise PackageTopologyError(
                        f"declared package data is a symlink: {match}"
                    )
                if match.is_file():
                    regular_matches.append(match)
            if not regular_matches:
                raise PackageTopologyError(
                    f"declared package-data pattern matched no files: {package}:{pattern}"
                )
            for source in regular_matches:
                data_relative = PurePosixPath(source.relative_to(package_root).as_posix())
                if any(
                    fnmatch.fnmatchcase(data_relative.as_posix(), excluded)
                    for excluded in exclude_patterns
                ):
                    continue
                wheel_path = package_relative.joinpath(data_relative).as_posix()
                validate_source_member(validate_archive_path(wheel_path))
                source_path = PurePosixPath(source.relative_to(project_root).as_posix())
                row = DeclaredPackageData(
                    package=package,
                    source_path=source_path.as_posix(),
                    wheel_path=wheel_path,
                    sha256=sha256_file(source),
                    size=source.stat().st_size,
                )
                existing = rows_by_wheel_path.get(wheel_path)
                if existing is not None and existing != row:
                    raise PackageTopologyError(
                        f"package-data declarations collide at wheel path: {wheel_path}"
                    )
                rows_by_wheel_path[wheel_path] = row
    return tuple(rows_by_wheel_path[path] for path in sorted(rows_by_wheel_path))


def validate_declared_package_data(
    wheel: Path, declared: Sequence[DeclaredPackageData]
) -> dict[str, object]:
    """Require every declared resource in a wheel with identical source bytes."""

    expected = {row.wheel_path: row for row in declared}
    if len(expected) != len(declared):
        raise PackageTopologyError("declared package-data manifest has duplicate wheel paths")
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != len(set(names)):
            raise PackageTopologyError(f"wheel contains duplicate member names: {wheel}")
        for name in names:
            validate_archive_path(name)
        missing = sorted(set(expected) - set(names))
        if missing:
            raise PackageTopologyError(
                "declared package data missing from wheel: " + ", ".join(missing)
            )
        dist_info = _dist_info_prefix(names)
        code_suffixes = (".py", ".pyi", ".so", ".pyd", ".dll", ".dylib")
        undeclared = sorted(
            name
            for name in names
            if not (name == dist_info or name.startswith(f"{dist_info}/"))
            and name not in expected
            and not name.endswith(code_suffixes)
        )
        if undeclared:
            raise PackageTopologyError(
                "undeclared non-code package data in wheel: " + ", ".join(undeclared)
            )
        for name, row in sorted(expected.items()):
            data = archive.read(name)
            if sha256_bytes(data) != row.sha256 or len(data) != row.size:
                raise PackageTopologyError(
                    f"declared package data byte mismatch in wheel: {name}"
                )
    manifest = [row.as_dict() for row in declared]
    return {
        "entry_count": len(manifest),
        "undeclared_entry_count": 0,
        "manifest_hash": sha256_bytes(canonical_json_bytes(manifest)),
        "status": "pass",
    }


def _dist_info_prefix(entries: Iterable[str]) -> str:
    candidates = sorted(
        {
            path.split("/", 1)[0]
            for path in entries
            if ".dist-info/" in path and path.split("/", 1)[0].endswith(".dist-info")
        }
    )
    if len(candidates) != 1:
        raise PackageTopologyError(
            f"wheel must contain exactly one .dist-info directory, found {candidates}"
        )
    return candidates[0]


@dataclass(frozen=True)
class WheelInspection:
    path: str
    distribution: str
    version: str
    sha256: str
    payload_entries: tuple[str, ...]
    payload_hash: str
    top_levels: tuple[str, ...]
    dist_info: str
    requires_dist: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "distribution": self.distribution,
            "version": self.version,
            "sha256": self.sha256,
            "payload_entries": list(self.payload_entries),
            "payload_hash": self.payload_hash,
            "top_levels": list(self.top_levels),
            "dist_info": self.dist_info,
            "requires_dist": list(self.requires_dist),
        }


def inspect_wheel(path: Path) -> WheelInspection:
    """Inspect a wheel and reject unsafe or cache-derived payload paths."""

    if not path.is_file() or path.suffix != ".whl":
        raise PackageTopologyError(f"not a wheel: {path}")
    payload_rows: list[tuple[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise PackageTopologyError(f"wheel contains duplicate member names: {path}")
        validated = [validate_archive_path(name.rstrip("/")) for name in names]
        dist_info = _dist_info_prefix(path_.as_posix() for path_ in validated)
        metadata_name = f"{dist_info}/METADATA"
        if metadata_name not in names:
            raise PackageTopologyError(f"wheel missing {metadata_name}: {path}")
        metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
        distribution = str(metadata.get("Name", "")).strip()
        version = str(metadata.get("Version", "")).strip()
        requires_dist = tuple(str(value) for value in metadata.get_all("Requires-Dist", []))
        if not distribution or not version:
            raise PackageTopologyError(f"wheel metadata lacks Name/Version: {path}")
        payload_entries: list[str] = []
        for member, member_path in zip(names, validated, strict=True):
            normalized = member_path.as_posix()
            if normalized == dist_info or normalized.startswith(f"{dist_info}/"):
                continue
            if member.endswith("/"):
                continue
            if is_generated_cache_path(member_path):
                raise PackageTopologyError(
                    f"generated/cache path leaked into wheel {path.name}: {normalized}"
                )
            data = archive.read(member)
            payload_entries.append(normalized)
            payload_rows.append((normalized, sha256_bytes(data)))
    payload_entries = sorted(payload_entries)
    top_levels = sorted({entry.split("/", 1)[0] for entry in payload_entries})
    return WheelInspection(
        path=path.name,
        distribution=distribution,
        version=version,
        sha256=sha256_file(path),
        payload_entries=tuple(payload_entries),
        payload_hash=sha256_bytes(canonical_json_bytes(sorted(payload_rows))),
        top_levels=tuple(top_levels),
        dist_info=dist_info,
        requires_dist=requires_dist,
    )


def verify_wheel_record(path: Path) -> dict[str, object]:
    """Verify wheel RECORD completeness, hashes, sizes, and the self row."""

    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != len(set(names)):
            raise PackageTopologyError(f"wheel contains duplicate member names: {path}")
        validated = [validate_archive_path(name).as_posix() for name in names]
        dist_info = _dist_info_prefix(validated)
        record_name = f"{dist_info}/RECORD"
        if record_name not in names:
            raise PackageTopologyError(f"wheel missing RECORD: {path}")
        rows = list(
            csv.reader(archive.read(record_name).decode("utf-8").splitlines())
        )
        if any(len(row) != 3 for row in rows):
            raise PackageTopologyError(f"malformed RECORD row in {path}")
        by_name: dict[str, tuple[str, str]] = {}
        for raw_name, encoded_hash, raw_size in rows:
            name = validate_archive_path(raw_name).as_posix()
            if name in by_name:
                raise PackageTopologyError(f"duplicate RECORD row {name} in {path}")
            by_name[name] = (encoded_hash, raw_size)
        if set(by_name) != set(names):
            missing = sorted(set(names) - set(by_name))
            extra = sorted(set(by_name) - set(names))
            raise PackageTopologyError(
                f"RECORD/archive membership mismatch in {path}; missing={missing}, extra={extra}"
            )
        for name in names:
            encoded_hash, raw_size = by_name[name]
            if name == record_name:
                if encoded_hash or raw_size:
                    raise PackageTopologyError("RECORD self row must have blank hash and size")
                continue
            if not encoded_hash.startswith("sha256=") or not raw_size.isdigit():
                raise PackageTopologyError(f"RECORD row lacks sha256/size: {name}")
            data = archive.read(name)
            encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
            if encoded_hash[7:].encode("ascii") != encoded:
                raise PackageTopologyError(f"RECORD hash mismatch: {name}")
            if int(raw_size) != len(data):
                raise PackageTopologyError(f"RECORD size mismatch: {name}")
    return {
        "record": record_name,
        "entry_count": len(names),
        "record_sha256": sha256_bytes(archive_bytes(path, record_name)),
        "status": "pass",
    }


def archive_bytes(path: Path, member: str) -> bytes:
    with zipfile.ZipFile(path) as archive:
        return archive.read(member)


def validate_main_wheel(
    inspection: WheelInspection,
    *,
    expected_distribution: str,
    owned_top_levels: Sequence[str],
) -> None:
    if normalize_distribution_name(inspection.distribution) != normalize_distribution_name(
        expected_distribution
    ):
        raise PackageTopologyError(
            f"expected distribution {expected_distribution!r}, got {inspection.distribution!r}"
        )
    expected = set(owned_top_levels)
    actual = set(inspection.top_levels)
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected or missing:
        raise PackageTopologyError(
            f"main wheel top-level mismatch; missing={missing}, unexpected={unexpected}"
        )
    for namespace in sorted(expected):
        if f"{namespace}/__init__.py" not in inspection.payload_entries:
            raise PackageTopologyError(
                f"owned namespace lacks package initializer in wheel: {namespace}"
            )


def validate_fileless_compatibility_wheel(
    inspection: WheelInspection,
    *,
    expected_distribution: str,
    exact_dependency: str | None = None,
    exact_version: str | None = None,
) -> None:
    if normalize_distribution_name(inspection.distribution) != normalize_distribution_name(
        expected_distribution
    ):
        raise PackageTopologyError(
            f"expected compatibility distribution {expected_distribution!r}, "
            f"got {inspection.distribution!r}"
        )
    if inspection.payload_entries:
        raise PackageTopologyError(
            "compatibility wheel must be fileless outside .dist-info; found "
            + ", ".join(inspection.payload_entries[:8])
        )
    if exact_dependency is not None:
        if exact_version is None:
            raise PackageTopologyError("exact compatibility dependency needs a version")
        expected = (
            normalize_distribution_name(exact_dependency),
            exact_version.lower(),
        )
        if len(inspection.requires_dist) != 1:
            raise PackageTopologyError(
                "compatibility distribution must declare exactly one dependency; "
                f"found {inspection.requires_dist}"
            )
        exact_rows: list[tuple[str, str]] = []
        for raw_requirement in inspection.requires_dist:
            compact = raw_requirement.replace(" ", "").replace("(", "").replace(")", "")
            if "==" not in compact or ";" in compact:
                continue
            name, version = compact.split("==", 1)
            exact_rows.append((normalize_distribution_name(name), version.lower()))
        if exact_rows != [expected]:
            raise PackageTopologyError(
                "compatibility distribution must have one exact dependency "
                f"{exact_dependency}=={exact_version}; found {inspection.requires_dist}"
            )


def validate_wheel_collision(
    left: WheelInspection, right: WheelInspection
) -> tuple[str, ...]:
    collisions = tuple(sorted(set(left.payload_entries) & set(right.payload_entries)))
    if collisions:
        raise PackageTopologyError(
            "wheel payload collision: " + ", ".join(collisions[:12])
        )
    return collisions


def normalize_distribution_name(name: str) -> str:
    return "-".join(filter(None, _split_distribution_name(name.lower())))


def _split_distribution_name(name: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    for character in name:
        if character in "-_.":
            if current:
                parts.append("".join(current))
                current = []
        else:
            current.append(character)
    if current:
        parts.append("".join(current))
    return parts


def require_executed_tests(count: int, *, selector: str) -> None:
    """Reject zero-test receipts; collection success alone is not execution."""

    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise PackageTopologyError(
            f"test selector {selector!r} executed zero tests; receipt cannot pass"
        )


def bind_files(root: Path, paths: Sequence[str]) -> tuple[dict[str, object], ...]:
    """Hash a declared set of regular tracked inputs."""

    rows: list[dict[str, object]] = []
    for raw_path in sorted(set(paths)):
        relative = validate_archive_path(raw_path)
        validate_source_member(relative)
        path = root.joinpath(*relative.parts)
        mode = path.lstat().st_mode if path.exists() else 0
        if not stat.S_ISREG(mode):
            raise PackageTopologyError(f"bound input is missing or non-regular: {raw_path}")
        rows.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return tuple(rows)


def verify_bound_files(root: Path, rows: Sequence[Mapping[str, object]]) -> None:
    for row in rows:
        raw_path = str(row.get("path", ""))
        expected_hash = str(row.get("sha256", ""))
        expected_size = row.get("size")
        current = bind_files(root, [raw_path])[0]
        if current["sha256"] != expected_hash or current["size"] != expected_size:
            raise PackageTopologyError(f"bound source/input drift: {raw_path}")


def validate_receipt_metadata(payload: Mapping[str, object]) -> None:
    required = {
        "schema",
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "null_mock_status",
        "caveats",
        "generating_command",
        "source_tree_hash",
        "dependency_layer_hash",
        "install_matrix",
        "overall_status",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise PackageTopologyError(
            "hermetic receipt missing required metadata: " + ", ".join(missing)
        )
    if payload.get("owner") != "COMMON":
        raise PackageTopologyError("hermetic receipt owner must be COMMON")
    if payload.get("claim_tier") != "diagnostic_only":
        raise PackageTopologyError("hermetic receipt claim tier must be diagnostic_only")
    if payload.get("transfer_source") != "none":
        raise PackageTopologyError("hermetic receipt transfer source must be none")
    if payload.get("overall_status") != "pass":
        raise PackageTopologyError("hermetic receipt is not a passing process receipt")


def structured_hash(payload: Mapping[str, object], *, excluded: Sequence[str] = ()) -> str:
    """Hash a mapping after removing explicitly nondeterministic top-level keys."""

    excluded_keys = set(excluded)
    normalized = {key: value for key, value in payload.items() if key not in excluded_keys}
    return sha256_bytes(canonical_json_bytes(normalized))
