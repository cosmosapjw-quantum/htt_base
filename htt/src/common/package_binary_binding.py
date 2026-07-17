"""Fail-closed byte binding for binary inputs shipped in audit packages.

Package manifests must not authenticate a binary merely by hashing the bytes
that the package builder just read.  In particular, the mutable Git index and a
sidecar changed in the same patch are not independent authorities.  This module
therefore accepts only one of these bindings:

* exact bytes at the same path in ``HEAD``;
* for immutable historical evidence only, an exact binary blob reachable from
  ``HEAD`` (the relocation path itself may be new); or
* an adjacent JSON sidecar whose own bytes are unchanged in ``HEAD`` or match an
  explicit digest supplied by a reviewed caller.

New or changed active/public binaries are always checked against both committed
and worktree legacy bytes before a sidecar can bind them.  In all cases the
binary and any digest-bearing sidecar must be regular files with no symlink
component.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any, Mapping, Sequence


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

# Binary formats admitted by current audit-package builders, plus common
# scientific/container formats so a future entry cannot silently bypass the
# gate by changing only its extension.
BINARY_SUFFIXES = frozenset(
    {
        ".avro",
        ".bin",
        ".bz2",
        ".db",
        ".feather",
        ".fit",
        ".fits",
        ".gif",
        ".gz",
        ".h5",
        ".hdf5",
        ".jpeg",
        ".jpg",
        ".npy",
        ".npz",
        ".parquet",
        ".pdf",
        ".pickle",
        ".pkl",
        ".png",
        ".sqlite",
        ".tar",
        ".webp",
        ".xz",
        ".zip",
    }
)

DEFAULT_LEGACY_BINARY_ROOTS = (
    "legacy/cf4_p0",
    "figures/conditioned_legacy",
    "figures/quarantined_legacy",
)


@dataclass(frozen=True)
class BinaryBinding:
    """Auditable result of binding one package binary to trusted bytes."""

    method: str
    sha256: str
    trusted_source: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def is_binary_path(path: Path | str) -> bool:
    """Return whether ``path`` has a package-gated binary suffix."""

    name = Path(path).name.lower()
    return any(name.endswith(suffix) for suffix in BINARY_SUFFIXES)


def _normalise_relative(path: Path | str, *, field: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{field} must be a safe repository-relative path: {path}")
    text = candidate.as_posix()
    if not text or text == ".":
        raise ValueError(f"{field} must not be empty")
    return text


def _assert_regular_nonsymlink(
    repo_root: Path,
    relative_path: Path | str,
    *,
    label: str,
) -> Path:
    """Return a path only when every component is non-symlink and final is regular."""

    relative = _normalise_relative(relative_path, field=label)
    current = repo_root
    parts = Path(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"{label} is missing: {relative}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"{label} cannot contain a symlink: {relative}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"{label} parent is not a directory: {relative}")
    if not stat.S_ISREG(current.lstat().st_mode):
        raise ValueError(f"{label} must be a regular file: {relative}")
    return current


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _git_toplevel(repo_root: Path) -> Path | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    try:
        top = Path(completed.stdout.strip()).resolve(strict=True)
        root = repo_root.resolve(strict=True)
    except (FileNotFoundError, OSError):
        return None
    return top if top == root else None


def _git_head_bytes(repo_root: Path, relative_path: str) -> bytes | None:
    if _git_toplevel(repo_root) is None:
        return None
    try:
        completed = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    return completed.stdout if completed.returncode == 0 else None


def _git_head_blob_oids(
    repo_root: Path,
    paths: Sequence[str] = (),
    *,
    binary_paths_only: bool,
) -> set[str] | None:
    """Return blob OIDs reachable from HEAD, never from the mutable index."""

    if _git_toplevel(repo_root) is None:
        return None
    command = ["git", "ls-tree", "-r", "-z", "HEAD"]
    if paths:
        command.extend(("--", *paths))
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    result: set[str] = set()
    for record in completed.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        if not separator:
            continue
        fields = metadata.split()
        if len(fields) < 3 or fields[1] != b"blob":
            continue
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if not binary_paths_only or is_binary_path(path):
            result.add(fields[2].decode("ascii"))
    return result


def _manifest_payload(data: bytes, *, relative_path: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"binary binding manifest is invalid JSON: {relative_path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"binary binding manifest must be a JSON object: {relative_path}")
    nested = payload.get("manifest")
    return nested if isinstance(nested, Mapping) else payload


def _sidecar_candidates(source_path: str) -> tuple[str, ...]:
    source = Path(source_path)
    base = source.with_suffix("")
    candidates = (
        base.with_name(base.name + ".manifest.json").as_posix(),
        source.with_name(source.name + ".manifest.json").as_posix(),
    )
    return tuple(dict.fromkeys(candidates))


def _sidecar_binding(
    repo_root: Path,
    source_path: str,
    actual_sha256: str,
    *,
    explicit_manifest_path: str | None,
    explicit_manifest_sha256: str | None,
) -> BinaryBinding | None:
    if explicit_manifest_sha256 is not None:
        if explicit_manifest_path is None:
            raise ValueError(
                "explicit_manifest_sha256 requires explicit_manifest_path"
            )
        explicit_manifest_sha256 = explicit_manifest_sha256.lower()
        if not _SHA256_RE.fullmatch(explicit_manifest_sha256):
            raise ValueError("explicit_manifest_sha256 must be sha256:<64 hex>")

    candidates = list(_sidecar_candidates(source_path))
    explicit: str | None = None
    if explicit_manifest_path is not None:
        explicit = _normalise_relative(
            explicit_manifest_path,
            field="binary binding manifest path",
        )
        candidates.insert(0, explicit)

    for candidate in dict.fromkeys(candidates):
        absolute = repo_root / candidate
        # lexists catches a broken symlink, which Path.exists() would hide.
        if not os.path.lexists(absolute):
            continue
        manifest_path = _assert_regular_nonsymlink(
            repo_root,
            candidate,
            label="binary binding manifest",
        )
        manifest_bytes = manifest_path.read_bytes()
        payload = _manifest_payload(manifest_bytes, relative_path=candidate)
        digest = payload.get("artifact_sha256")
        if digest is None:
            if explicit_manifest_path is not None and candidate == explicit_manifest_path:
                raise ValueError(
                    f"explicit binary binding manifest lacks artifact_sha256: {candidate}"
                )
            continue
        expected = str(digest).lower()
        if not _SHA256_RE.fullmatch(expected):
            raise ValueError(
                f"binary binding manifest has invalid artifact_sha256: {candidate}"
            )
        declared_path = payload.get("artifact_path")
        if declared_path is None:
            raise ValueError(
                f"binary binding manifest lacks artifact_path: {candidate}"
            )
        if str(declared_path) != source_path:
            raise ValueError(
                "binary binding manifest artifact_path mismatch for "
                f"{source_path}: {declared_path!r}"
            )
        if expected != actual_sha256:
            raise ValueError(
                "binary binding manifest digest mismatch for "
                f"{source_path}: expected {expected}, got {actual_sha256}"
            )

        head_bytes = _git_head_bytes(repo_root, candidate)
        if head_bytes == manifest_bytes:
            authority = f"git-head:{candidate}"
        elif candidate == explicit and explicit_manifest_sha256 is not None:
            sidecar_sha256 = _sha256_bytes(manifest_bytes)
            if sidecar_sha256 != explicit_manifest_sha256:
                raise ValueError(
                    "explicit binary binding manifest pin mismatch for "
                    f"{candidate}: expected {explicit_manifest_sha256}, "
                    f"got {sidecar_sha256}"
                )
            authority = f"reviewed-pin:{candidate}@{explicit_manifest_sha256}"
        else:
            raise ValueError(
                "binary binding manifest is not independently trusted; it must "
                "be unchanged at the same path in HEAD or match an explicit "
                f"reviewed SHA-256 pin: {candidate}"
            )
        return BinaryBinding(
            method="sidecar_artifact_sha256",
            sha256=actual_sha256,
            trusted_source=authority,
        )
    return None


def _quarantine_inventory_pin(repo_root: Path, relative: str) -> str | None:
    """Return the canonical PR-120 inventory sha256 for a legacy path.

    Reads ``docs/generated/cf4_p0_quarantine_inventory.json`` and returns the
    ``legacy_reproduction_only`` entry's ``sha256:``-prefixed digest, or
    ``None`` when the path is not inventoried (callers then fall through to
    the fail-closed sidecar/raise path).
    """

    inventory_path = repo_root / "docs/generated/cf4_p0_quarantine_inventory.json"
    try:
        payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    for row in payload.get("entries", []):
        if (
            isinstance(row, Mapping)
            and row.get("mode") == "legacy_reproduction_only"
            and row.get("path") == relative
        ):
            sha = row.get("sha256")
            if isinstance(sha, str) and sha:
                return sha if sha.startswith("sha256:") else f"sha256:{sha}"
    return None


def _git_blob_oid(repo_root: Path, data: bytes) -> str | None:
    if _git_toplevel(repo_root) is None:
        return None
    try:
        completed = subprocess.run(
            ["git", "hash-object", "--stdin"],
            cwd=repo_root,
            input=data,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.decode("ascii", errors="strict").strip()


def _git_legacy_blob_oids(
    repo_root: Path,
    legacy_roots: Sequence[str],
) -> set[str] | None:
    return _git_head_blob_oids(
        repo_root,
        legacy_roots,
        binary_paths_only=True,
    )


def _legacy_sha256s_without_git(
    repo_root: Path,
    legacy_roots: Sequence[str],
    *,
    source_path: str,
) -> set[str]:
    result: set[str] = set()
    for root_text in legacy_roots:
        root = repo_root / root_text
        if not root.exists() or root.is_symlink():
            continue
        for candidate in root.rglob("*"):
            if not is_binary_path(candidate):
                continue
            try:
                relative = candidate.relative_to(repo_root).as_posix()
            except ValueError:
                continue
            if relative == source_path or candidate.is_symlink() or not candidate.is_file():
                continue
            result.add(_sha256_bytes(candidate.read_bytes()))
    return result


def _assert_not_legacy_copy(
    repo_root: Path,
    source_path: str,
    data: bytes,
    actual_sha256: str,
    *,
    legacy_roots: Sequence[str],
) -> None:
    oid = _git_blob_oid(repo_root, data)
    legacy_oids = _git_legacy_blob_oids(repo_root, legacy_roots)
    # The committed and worktree sets are deliberately additive.  HEAD is the
    # immutable authority; scanning the current legacy lanes additionally
    # catches files relocated into a new typed root by the patch under review.
    # Neither the mutable index nor a changed sidecar can remove a collision.
    duplicated = bool(oid is not None and legacy_oids is not None and oid in legacy_oids)
    duplicated = duplicated or actual_sha256 in _legacy_sha256s_without_git(
        repo_root,
        legacy_roots,
        source_path=source_path,
    )
    if duplicated:
        raise ValueError(
            "active/public package binary duplicates immutable legacy bytes: "
            f"{source_path}"
        )


def verify_package_binary_binding(
    repo_root: Path | str,
    source_path: Path | str,
    *,
    content_mode: str,
    explicit_manifest_path: str | None = None,
    explicit_manifest_sha256: str | None = None,
    legacy_roots: Sequence[str] = DEFAULT_LEGACY_BINARY_ROOTS,
) -> dict[str, str] | None:
    """Verify one source binary and return its independent binding metadata.

    Text inputs return ``None``.  Binary inputs fail closed if they are symlinks,
    are not regular files, duplicate legacy bytes in an active/public lane, or
    cannot be bound either to exact bytes reachable from ``HEAD`` or to
    ``artifact_sha256`` in an independently trusted sidecar.  For temporary
    roots without Git history, callers must pin the explicit sidecar's own
    SHA-256 via ``explicit_manifest_sha256``.
    """

    relative = _normalise_relative(source_path, field="package binary source")
    if not is_binary_path(relative):
        return None
    root = Path(repo_root)
    binary = _assert_regular_nonsymlink(
        root,
        relative,
        label="package binary source",
    )
    data = binary.read_bytes()
    actual_sha256 = _sha256_bytes(data)
    is_legacy_source = any(
        relative == root_text.rstrip("/")
        or relative.startswith(root_text.rstrip("/") + "/")
        for root_text in legacy_roots
    )
    if is_legacy_source and content_mode != "immutable_historical_evidence":
        raise ValueError(
            "legacy package binary requires immutable_historical_evidence mode: "
            f"{relative}"
        )

    head_bytes = _git_head_bytes(root, relative)
    if head_bytes == data:
        return BinaryBinding(
            method="git_head_exact_bytes",
            sha256=actual_sha256,
            trusted_source=f"git-head:{relative}",
        ).to_dict()

    # Active/public bytes that are new or changed relative to the same path in
    # HEAD must face the collision gate before any sidecar is considered.
    if content_mode == "active_public":
        _assert_not_legacy_copy(
            root,
            relative,
            data,
            actual_sha256,
            legacy_roots=legacy_roots,
        )

    # Relocation is expected for immutable evidence.  The exact blob must still
    # be reachable from HEAD; merely staging the bytes does not satisfy this
    # branch because the index is never consulted.
    if content_mode == "immutable_historical_evidence":
        oid = _git_blob_oid(root, data)
        head_binary_oids = _git_head_blob_oids(
            root,
            binary_paths_only=True,
        )
        if oid is not None and head_binary_oids is not None and oid in head_binary_oids:
            return BinaryBinding(
                method="git_head_reachable_binary_blob",
                sha256=actual_sha256,
                trusted_source=f"git-head-blob:{oid}",
            ).to_dict()

        # PR-124 preflight: the legacy/cf4_p0 tree was untracked (and its
        # pre-PR-119 snapshots stripped from history), so git can no longer
        # bind these bytes.  The canonical PR-120 quarantine inventory —
        # itself config-hash-bound and validated by validate_repository —
        # is the surviving byte authority.  Fail closed on any mismatch.
        if is_legacy_source:
            inventory_pin = _quarantine_inventory_pin(root, relative)
            if inventory_pin is not None:
                if inventory_pin != actual_sha256:
                    raise ValueError(
                        "legacy package binary does not match its canonical "
                        f"quarantine inventory pin: {relative}"
                    )
                return BinaryBinding(
                    method="cf4_p0_inventory_sha256",
                    sha256=actual_sha256,
                    trusted_source=f"quarantine-inventory:{inventory_pin}",
                ).to_dict()

    sidecar = _sidecar_binding(
        root,
        relative,
        actual_sha256,
        explicit_manifest_path=explicit_manifest_path,
        explicit_manifest_sha256=explicit_manifest_sha256,
    )
    if sidecar is not None:
        return sidecar.to_dict()

    raise ValueError(
        "package binary has no independent byte binding in HEAD; provide an "
        "adjacent regular JSON sidecar with artifact_path and artifact_sha256 "
        "whose own bytes are unchanged in HEAD, or pass an explicit reviewed "
        f"sidecar SHA-256 pin: {relative}"
    )


def verify_packaged_entry_bytes(
    repo_root: Path | str,
    source_path: Path | str,
    data: bytes,
    *,
    expected_sha256: str,
    content_mode: str,
    expected_binary_binding: Mapping[str, str] | None,
) -> bytes:
    """Revalidate bytes immediately before they are written to an archive.

    Builders first create manifest rows and only later serialize a ZIP.  This
    second check prevents a source mutation or symlink swap in that interval
    from producing bytes that no longer match the disclosed row/binding.
    """

    actual_sha256 = _sha256_bytes(data)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "package source bytes changed after manifest construction: "
            f"{source_path}"
        )
    explicit_manifest_path: str | None = None
    explicit_manifest_sha256: str | None = None
    if expected_binary_binding is not None:
        trusted_source = str(expected_binary_binding.get("trusted_source", ""))
        prefix = "reviewed-pin:"
        if trusted_source.startswith(prefix):
            pinned_source = trusted_source[len(prefix) :]
            manifest_path, separator, digest_hex = pinned_source.rpartition(
                "@sha256:"
            )
            if not separator or not manifest_path or len(digest_hex) != 64:
                raise ValueError(
                    "expected binary binding has malformed reviewed pin: "
                    f"{trusted_source}"
                )
            explicit_manifest_path = manifest_path
            explicit_manifest_sha256 = "sha256:" + digest_hex
    actual_binding = verify_package_binary_binding(
        repo_root,
        source_path,
        content_mode=content_mode,
        explicit_manifest_path=explicit_manifest_path,
        explicit_manifest_sha256=explicit_manifest_sha256,
    )
    if actual_binding != expected_binary_binding:
        raise ValueError(
            "package binary binding changed after manifest construction: "
            f"{source_path}"
        )
    return data
