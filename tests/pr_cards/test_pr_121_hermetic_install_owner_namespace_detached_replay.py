from __future__ import annotations

import base64
import copy
import csv
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from typing import Callable
import zipfile

import pytest

from common.package_topology import (
    PackageTopologyError,
    bind_files,
    canonicalize_sdist,
    declared_package_data,
    inspect_sdist,
    inspect_wheel,
    normalize_ephemeral_paths,
    require_executed_tests,
    safe_extract_git_archive,
    tree_hash,
    validate_archive_path,
    validate_compatibility_sdist,
    validate_declared_package_data,
    validate_fileless_compatibility_wheel,
    validate_main_wheel,
    validate_receipt_metadata,
    validate_wheel_collision,
    verify_bound_files,
    verify_wheel_record,
)


def _record_row(name: str, data: bytes) -> tuple[str, str, str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return name, f"sha256={digest.decode('ascii')}", str(len(data))


def _write_wheel(
    path: Path,
    *,
    distribution: str,
    version: str,
    payload: dict[str, bytes] | None = None,
    requires: tuple[str, ...] = (),
    record_override: list[tuple[str, str, str]] | None = None,
) -> Path:
    normalized = distribution.replace("-", "_")
    dist_info = f"{normalized}-{version}.dist-info"
    metadata = [
        "Metadata-Version: 2.4",
        f"Name: {distribution}",
        f"Version: {version}",
    ]
    metadata.extend(f"Requires-Dist: {requirement}" for requirement in requires)
    entries = dict(payload or {})
    entries[f"{dist_info}/METADATA"] = ("\n".join(metadata) + "\n").encode()
    entries[f"{dist_info}/WHEEL"] = b"Wheel-Version: 1.0\nTag: py3-none-any\n"
    record_name = f"{dist_info}/RECORD"
    rows = [_record_row(name, data) for name, data in sorted(entries.items())]
    rows.append((record_name, "", ""))
    if record_override is not None:
        rows = record_override
    stream = io.StringIO()
    csv.writer(stream, lineterminator="\n").writerows(rows)
    entries[record_name] = stream.getvalue().encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return path


def _main_wheel(path: Path, *, extra: dict[str, bytes] | None = None) -> Path:
    payload = {
        "bass/__init__.py": b"",
        "common/__init__.py": b"",
        "htt/__init__.py": b"",
    }
    payload.update(extra or {})
    return _write_wheel(
        path,
        distribution="bass-py",
        version="1.2.3",
        payload=payload,
    )


def _write_sdist(
    path: Path,
    *,
    distribution: str = "htt",
    version: str = "8.3.0",
    requires: tuple[str, ...] = ("bass-py==1.2.3",),
    payload: dict[str, bytes] | None = None,
) -> Path:
    root = f"{distribution.replace('_', '-')}-{version}"
    metadata = [
        "Metadata-Version: 2.4",
        f"Name: {distribution}",
        f"Version: {version}",
    ]
    metadata.extend(f"Requires-Dist: {requirement}" for requirement in requires)
    entries = {
        "PKG-INFO": ("\n".join(metadata) + "\n").encode(),
        "MANIFEST.in": b"include README.md\ninclude pyproject.toml\n",
        "README.md": b"Compatibility metadata only.\n",
        "pyproject.toml": b"[tool.setuptools]\npackages = []\n",
        "setup.py": b"from setuptools import setup\nsetup()\n",
        "htt.egg-info/PKG-INFO": ("\n".join(metadata) + "\n").encode(),
        "htt.egg-info/SOURCES.txt": b"README.md\npyproject.toml\nsetup.py\n",
        "htt.egg-info/dependency_links.txt": b"\n",
        "htt.egg-info/requires.txt": b"bass-py==1.2.3\n",
        "htt.egg-info/top_level.txt": b"\n",
    }
    entries.update(payload or {})
    with tarfile.open(path, "w:gz") as archive:
        for relative, data in sorted(entries.items()):
            info = tarfile.TarInfo(f"{root}/{relative}")
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    return path


def _rewrite_zip(path: Path, *, replacements: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path) as archive:
        entries = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
        }
    entries.update(replacements)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def _rewrite_record_rows(
    path: Path, transform: Callable[[list[list[str]]], list[list[str]]]
) -> None:
    with zipfile.ZipFile(path) as archive:
        record_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/RECORD")
        )
        rows = list(csv.reader(archive.read(record_name).decode().splitlines()))
    updated = transform(rows)
    stream = io.StringIO()
    csv.writer(stream, lineterminator="\n").writerows(updated)
    _rewrite_zip(path, replacements={record_name: stream.getvalue().encode()})


@pytest.mark.parametrize(
    "raw",
    ("../escape", "/absolute", "C:/drive", "a\\b", "a/../../b", ""),
)
def test_archive_path_traversal_is_rejected(raw: str) -> None:
    with pytest.raises(PackageTopologyError):
        validate_archive_path(raw)


def test_main_and_fileless_compatibility_wheels_validate(tmp_path: Path) -> None:
    main = inspect_wheel(_main_wheel(tmp_path / "main.whl"))
    compat = inspect_wheel(
        _write_wheel(
            tmp_path / "compat.whl",
            distribution="htt",
            version="8.3.0",
            requires=("bass-py==1.2.3",),
        )
    )

    validate_main_wheel(
        main,
        expected_distribution="bass-py",
        owned_top_levels=("bass", "common", "htt"),
    )
    validate_fileless_compatibility_wheel(
        compat,
        expected_distribution="htt",
        exact_dependency="bass-py",
        exact_version="1.2.3",
    )
    assert validate_wheel_collision(main, compat) == ()
    assert verify_wheel_record(tmp_path / "main.whl")["status"] == "pass"
    assert verify_wheel_record(tmp_path / "compat.whl")["status"] == "pass"


def test_compatibility_wheel_python_payload_is_rejected(tmp_path: Path) -> None:
    compat = inspect_wheel(
        _write_wheel(
            tmp_path / "compat.whl",
            distribution="htt",
            version="8.3.0",
            payload={"htt/__init__.py": b"shadow = True\n"},
            requires=("bass-py==1.2.3",),
        )
    )
    with pytest.raises(PackageTopologyError, match="fileless"):
        validate_fileless_compatibility_wheel(
            compat,
            expected_distribution="htt",
            exact_dependency="bass-py",
            exact_version="1.2.3",
        )


def test_compatibility_wheel_extra_dependency_is_rejected(tmp_path: Path) -> None:
    compat = inspect_wheel(
        _write_wheel(
            tmp_path / "compat.whl",
            distribution="htt",
            version="8.3.0",
            requires=("bass-py==1.2.3", "numpy>=1"),
        )
    )
    with pytest.raises(PackageTopologyError, match="exactly one"):
        validate_fileless_compatibility_wheel(
            compat,
            expected_distribution="htt",
            exact_dependency="bass-py",
            exact_version="1.2.3",
        )


def test_compatibility_sdist_metadata_allowlist_validates(tmp_path: Path) -> None:
    inspection = inspect_sdist(_write_sdist(tmp_path / "htt-8.3.0.tar.gz"))
    validate_compatibility_sdist(
        inspection,
        expected_distribution="htt",
        exact_dependency="bass-py",
        exact_version="1.2.3",
    )


@pytest.mark.parametrize(
    "injected",
    (
        "htt/__init__.py",
        "tests/test_shadow.py",
        "shadow.py",
        "docs/nested.md",
        "htt.egg-info/payload.json",
    ),
)
def test_compatibility_sdist_rejects_non_allowlisted_payload(
    tmp_path: Path, injected: str
) -> None:
    inspection = inspect_sdist(
        _write_sdist(
            tmp_path / "htt-8.3.0.tar.gz",
            payload={injected: b"injected\n"},
        )
    )
    with pytest.raises(PackageTopologyError, match="forbidden|allowlist|undeclared"):
        validate_compatibility_sdist(
            inspection,
            expected_distribution="htt",
            exact_dependency="bass-py",
            exact_version="1.2.3",
        )


def test_sdist_symlink_member_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "htt-8.3.0.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo("htt-8.3.0/PKG-INFO")
        data = b"Metadata-Version: 2.4\nName: htt\nVersion: 8.3.0\n"
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
        link = tarfile.TarInfo("htt-8.3.0/README.md")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        archive.addfile(link)
    with pytest.raises(PackageTopologyError, match="non-regular"):
        inspect_sdist(path)


def test_wheel_path_collision_is_rejected(tmp_path: Path) -> None:
    left = inspect_wheel(_main_wheel(tmp_path / "left.whl"))
    right = inspect_wheel(
        _write_wheel(
            tmp_path / "right.whl",
            distribution="htt",
            version="8.3.0",
            payload={"htt/__init__.py": b"collision\n"},
        )
    )
    with pytest.raises(PackageTopologyError, match="collision"):
        validate_wheel_collision(left, right)


def test_build_cache_package_leak_is_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(
        tmp_path / "cache.whl",
        extra={"htt/build/lib/htt/__init__.py": b"cache\n"},
    )
    with pytest.raises(PackageTopologyError, match="cache"):
        inspect_wheel(wheel)


def test_compiled_bytecode_payload_is_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(
        tmp_path / "pyc.whl",
        extra={"htt/__pycache__/shadow.cpython-312.pyc": b"compiled-cache"},
    )
    with pytest.raises(PackageTopologyError, match="cache"):
        inspect_wheel(wheel)


def test_declared_package_data_missing_resource_is_rejected(tmp_path: Path) -> None:
    project = tmp_path / "project"
    resources = project / "demo" / "resources"
    data_root = resources / "data"
    data_root.mkdir(parents=True)
    (project / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (resources / "__init__.py").write_text("", encoding="utf-8")
    (data_root / "first.json").write_bytes(b'{"value":1}\n')
    (data_root / "second.bin").write_bytes(b"\x00\x01resource\n")
    (project / "pyproject.toml").write_text(
        """[tool.setuptools]
include-package-data = false

[tool.setuptools.packages.find]
where = ["."]
namespaces = false

[tool.setuptools.package-data]
"demo.resources" = ["data/first.json", "data/second.bin"]
""",
        encoding="utf-8",
    )
    declared = declared_package_data(project)
    assert [row.wheel_path for row in declared] == [
        "demo/resources/data/first.json",
        "demo/resources/data/second.bin",
    ]

    complete = _write_wheel(
        tmp_path / "complete.whl",
        distribution="bass-py",
        version="1.2.3",
        payload={
            "demo/__init__.py": b"",
            "demo/resources/__init__.py": b"",
            "demo/resources/data/first.json": b'{"value":1}\n',
            "demo/resources/data/second.bin": b"\x00\x01resource\n",
        },
    )
    assert validate_declared_package_data(complete, declared)["entry_count"] == 2

    missing = _write_wheel(
        tmp_path / "missing.whl",
        distribution="bass-py",
        version="1.2.3",
        payload={
            "demo/__init__.py": b"",
            "demo/resources/__init__.py": b"",
            "demo/resources/data/first.json": b'{"value":1}\n',
        },
    )
    with pytest.raises(PackageTopologyError, match="missing"):
        validate_declared_package_data(missing, declared)

    undeclared = _write_wheel(
        tmp_path / "undeclared.whl",
        distribution="bass-py",
        version="1.2.3",
        payload={
            "demo/__init__.py": b"",
            "demo/resources/__init__.py": b"",
            "demo/resources/data/first.json": b'{"value":1}\n',
            "demo/resources/data/second.bin": b"\x00\x01resource\n",
            "demo/resources/data/extra.bin": b"undeclared\n",
        },
    )
    with pytest.raises(PackageTopologyError, match="undeclared"):
        validate_declared_package_data(undeclared, declared)


def test_record_duplicate_archive_member_is_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(tmp_path / "tampered.whl")
    with pytest.warns(UserWarning, match="Duplicate name"):
        with zipfile.ZipFile(wheel, "a") as archive:
            archive.writestr("bass/__init__.py", b"tampered")
    with pytest.raises(PackageTopologyError, match="duplicate"):
        verify_wheel_record(wheel)


def test_record_hash_tamper_with_unique_members_is_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(tmp_path / "bad-hash.whl")
    _rewrite_zip(wheel, replacements={"bass/__init__.py": b"tampered"})
    with pytest.raises(PackageTopologyError, match="hash mismatch"):
        verify_wheel_record(wheel)


def test_record_size_tamper_with_unique_members_is_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(tmp_path / "bad-size.whl")

    def mutate(rows: list[list[str]]) -> list[list[str]]:
        return [
            [row[0], row[1], "999"] if row[0] == "bass/__init__.py" else row
            for row in rows
        ]

    _rewrite_record_rows(wheel, mutate)
    with pytest.raises(PackageTopologyError, match="size mismatch"):
        verify_wheel_record(wheel)


def test_record_nonself_blank_hash_and_size_are_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(tmp_path / "blank-row.whl")

    def mutate(rows: list[list[str]]) -> list[list[str]]:
        return [
            [row[0], "", ""] if row[0] == "bass/__init__.py" else row
            for row in rows
        ]

    _rewrite_record_rows(wheel, mutate)
    with pytest.raises(PackageTopologyError, match="lacks sha256/size"):
        verify_wheel_record(wheel)


def test_record_missing_row_with_unique_members_is_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(tmp_path / "missing-row.whl")
    _rewrite_record_rows(
        wheel,
        lambda rows: [row for row in rows if row[0] != "bass/__init__.py"],
    )
    with pytest.raises(PackageTopologyError, match="membership mismatch"):
        verify_wheel_record(wheel)


def test_record_extra_row_with_unique_members_is_rejected(tmp_path: Path) -> None:
    wheel = _main_wheel(tmp_path / "extra-row.whl")
    _rewrite_record_rows(
        wheel,
        lambda rows: [*rows, ["ghost.py", "sha256=bad", "1"]],
    )
    with pytest.raises(PackageTopologyError, match="membership mismatch"):
        verify_wheel_record(wheel)


def test_record_self_row_must_be_blank(tmp_path: Path) -> None:
    dist_info = "htt-8.3.0.dist-info"
    metadata = b"Metadata-Version: 2.4\nName: htt\nVersion: 8.3.0\n"
    wheel_data = b"Wheel-Version: 1.0\nTag: py3-none-any\n"
    record_name = f"{dist_info}/RECORD"
    rows = [
        _record_row(f"{dist_info}/METADATA", metadata),
        _record_row(f"{dist_info}/WHEEL", wheel_data),
        (record_name, "sha256=bad", "1"),
    ]
    wheel = _write_wheel(
        tmp_path / "bad-self.whl",
        distribution="htt",
        version="8.3.0",
        record_override=rows,
    )
    with pytest.raises(PackageTopologyError, match="self row"):
        verify_wheel_record(wheel)


def test_git_archive_cache_member_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "snapshot.tar"
    with tarfile.open(archive_path, "w") as archive:
        info = tarfile.TarInfo("htt/build/lib/htt/__init__.py")
        data = b"cache\n"
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    with pytest.raises(PackageTopologyError, match="cache"):
        safe_extract_git_archive(archive_path, tmp_path / "out")


def test_git_index_archive_excludes_untracked_sentinel(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    declared = repository / "declared"
    declared.mkdir()
    (declared / "tracked.py").write_text("TRACKED = True\n", encoding="utf-8")
    subprocess.run(["git", "add", "declared/tracked.py"], cwd=repository, check=True)
    tree = subprocess.run(
        ["git", "write-tree"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (declared / "untracked_sentinel.py").write_text(
        "raise RuntimeError('must not enter archive')\n", encoding="utf-8"
    )
    archive = tmp_path / "index.tar"
    subprocess.run(
        [
            "git",
            "archive",
            "--format=tar",
            f"--output={archive}",
            tree,
            "--",
            "declared",
        ],
        cwd=repository,
        check=True,
    )
    members = safe_extract_git_archive(archive, tmp_path / "extracted")
    assert "declared/tracked.py" in members
    assert "declared/untracked_sentinel.py" not in members
    assert not (tmp_path / "extracted/declared/untracked_sentinel.py").exists()


def test_source_byte_and_untracked_injection_change_tree_hash(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    tracked = source / "tracked.py"
    tracked.write_text("VALUE = 1\n", encoding="utf-8")
    baseline = tree_hash(source)
    tracked.write_text("VALUE = 2\n", encoding="utf-8")
    assert tree_hash(source) != baseline
    tracked.write_text("VALUE = 1\n", encoding="utf-8")
    (source / "untracked.py").write_text("SENTINEL = True\n", encoding="utf-8")
    assert tree_hash(source) != baseline


def test_executable_mode_mutation_changes_tree_hash(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    tracked = source / "runner.py"
    tracked.write_text("VALUE = 1\n", encoding="utf-8")
    tracked.chmod(0o644)
    baseline = tree_hash(source)
    tracked.chmod(0o755)
    assert tree_hash(source) != baseline


def test_ephemeral_build_and_pip_paths_normalize_identically() -> None:
    left = (
        "$BUILD/out/.tmp-kqlvyrkr/member and "
        "$TEMP/pip-build-env-ab12CD/overlay sha256=" + "a" * 64
        + "\nCreated wheel for demo: filename=demo.whl size=3050 sha256="
        + "c" * 64
        + "\nStored in directory: $TEMP/pip-ephem-wheel-cache-one/wheels/6d/c4/89/key"
    )
    right = (
        "$BUILD/out/.tmp-hgunoiz5/member and "
        "$TEMP/pip-build-env-Z9y8x7/overlay sha256=" + "b" * 64
        + "\nCreated wheel for demo: filename=demo.whl size=3046 sha256="
        + "d" * 64
        + "\nStored in directory: $TEMP/pip-ephem-wheel-cache-two/wheels/9d/8a/02/other"
    )
    assert normalize_ephemeral_paths(left) == normalize_ephemeral_paths(right)


def test_sdist_tar_and_gzip_metadata_canonicalize_identically(tmp_path: Path) -> None:
    payload = {
        "htt-8.3.0": None,
        "htt-8.3.0/PKG-INFO": b"Metadata-Version: 2.4\nName: htt\nVersion: 8.3.0\n",
        "htt-8.3.0/README.md": b"compatibility metadata only\n",
        "htt-8.3.0/pyproject.toml": b"[tool.setuptools]\npackages = []\n",
    }

    def write_variant(path: Path, *, reverse: bool, stamp: int, identity: int) -> None:
        tar_buffer = io.BytesIO()
        rows = list(payload.items())
        if reverse:
            rows.reverse()
        with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, data in rows:
                member = tarfile.TarInfo(name)
                member.uid = identity
                member.gid = identity
                member.uname = f"user{identity}"
                member.gname = f"group{identity}"
                member.mtime = stamp
                member.pax_headers = {"mtime": f"{stamp}.125"}
                if data is None:
                    member.type = tarfile.DIRTYPE
                    member.mode = 0o700
                    archive.addfile(member)
                else:
                    member.mode = 0o600
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
        with path.open("wb") as raw:
            with gzip.GzipFile(
                filename=f"variant-{identity}.tar",
                mode="wb",
                fileobj=raw,
                mtime=stamp + identity,
            ) as compressed:
                compressed.write(tar_buffer.getvalue())

    left = tmp_path / "left.tar.gz"
    right = tmp_path / "right.tar.gz"
    write_variant(left, reverse=False, stamp=101, identity=1000)
    write_variant(right, reverse=True, stamp=202, identity=2000)
    epoch = 123456789
    canonicalize_sdist(left, source_date_epoch=epoch)
    canonicalize_sdist(right, source_date_epoch=epoch)

    assert left.read_bytes() == right.read_bytes()
    raw = left.read_bytes()
    assert raw[3] & 0x08 == 0  # no original filename in the gzip envelope
    assert int.from_bytes(raw[4:8], "little") == epoch
    with tarfile.open(left, "r:gz") as archive:
        members = archive.getmembers()
    assert [member.name for member in members] == sorted(payload)
    assert all(member.mtime == epoch for member in members)
    assert all(member.uid == member.gid == 0 for member in members)
    assert all(member.uname == member.gname == "" for member in members)


def test_bound_input_drift_fails_check(tmp_path: Path) -> None:
    path = tmp_path / "spec.yaml"
    path.write_text("schema: one\n", encoding="utf-8")
    bound = bind_files(tmp_path, ["spec.yaml"])
    verify_bound_files(tmp_path, bound)
    path.write_text("schema: two\n", encoding="utf-8")
    with pytest.raises(PackageTopologyError, match="drift"):
        verify_bound_files(tmp_path, bound)


@pytest.mark.parametrize("count", (0, -1, True))
def test_zero_or_invalid_test_execution_is_rejected(count: int) -> None:
    with pytest.raises(PackageTopologyError, match="zero tests"):
        require_executed_tests(count, selector="clean-smoke")


def test_receipt_requires_common_diagnostic_metadata() -> None:
    payload = {
        "schema": "htt.pr121.hermetic_replay_receipt.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "config_hash": "a" * 64,
        "input_hashes": [],
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "caveats": ["mechanics only"],
        "generating_command": "python scripts/codex_harness/hermetic_replay.py --write",
        "source_tree_hash": "b" * 64,
        "dependency_layer_hash": "c" * 64,
        "install_matrix": [],
        "overall_status": "pass",
    }
    validate_receipt_metadata(payload)
    payload["claim_tier"] = "validated"
    with pytest.raises(PackageTopologyError, match="claim tier"):
        validate_receipt_metadata(payload)


def _load_detached_runner():
    repository = Path(__file__).resolve().parents[2]
    path = repository / "scripts/codex_harness/hermetic_replay.py"
    spec = importlib.util.spec_from_file_location("pr121_test_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _synthetic_read_only_dependency_layer(runner, root: Path):
    site = root / "lib/python3.12/site-packages"
    site.mkdir(parents=True)
    (site / "dependency.py").write_text("VALUE = 1\n", encoding="utf-8")
    executable = root / "bin/tool"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    runner._seal_dependency_tree(root)
    manifest = runner._dependency_manifest(root)
    return runner.DependencyLayer(
        root=root,
        site_packages=site,
        content_hash=runner.sha256_bytes(runner.canonical_json_bytes(manifest)),
        file_count=sum(row["kind"] == "file" for row in manifest),
        directory_count=sum(row["kind"] == "directory" for row in manifest),
        distributions=(),
    )


def test_dependency_layer_is_physically_read_only_and_mode_bound(tmp_path: Path) -> None:
    runner = _load_detached_runner()
    layer = _synthetic_read_only_dependency_layer(runner, tmp_path / "dependencies")
    receipt = runner.verify_dependency_layer(layer, phase="test:baseline")
    assert receipt["status"] == "pass"
    assert receipt["writable_entry_count"] == 0
    assert receipt["mode_policy"] == "files=0444_or_0555;directories=0555"
    assert (layer.site_packages / "dependency.py").stat().st_mode & 0o777 == 0o444
    assert (layer.root / "bin/tool").stat().st_mode & 0o777 == 0o555
    assert all(
        path.stat().st_mode & 0o222 == 0
        for path in [layer.root, *layer.root.rglob("*")]
    )


@pytest.mark.parametrize("mutation", ("mode", "content"))
def test_dependency_layer_mode_or_content_mutation_fails_closed(
    tmp_path: Path, mutation: str
) -> None:
    runner = _load_detached_runner()
    layer = _synthetic_read_only_dependency_layer(runner, tmp_path / "dependencies")
    target = layer.site_packages / "dependency.py"
    target.chmod(0o644)
    if mutation == "content":
        target.write_text("VALUE = 2\n", encoding="utf-8")
        target.chmod(0o444)
    with pytest.raises(
        runner.HermeticReplayError,
        match="writable shared dependency|content/mode drift",
    ):
        runner.verify_dependency_layer(layer, phase=f"test:{mutation}")


@pytest.mark.parametrize("mutation", ("path", "type", "size"))
def test_dependency_layer_path_type_or_size_mutation_fails_closed(
    tmp_path: Path, mutation: str
) -> None:
    runner = _load_detached_runner()
    layer = _synthetic_read_only_dependency_layer(runner, tmp_path / "dependencies")
    target = layer.site_packages / "dependency.py"
    if mutation == "size":
        target.chmod(0o644)
        target.write_text("VALUE = 100\n", encoding="utf-8")
        target.chmod(0o444)
    else:
        layer.site_packages.chmod(0o755)
        if mutation == "path":
            target.rename(layer.site_packages / "renamed_dependency.py")
        else:
            target.chmod(0o644)
            target.unlink()
            target.mkdir(mode=0o555)
        layer.site_packages.chmod(0o555)
    with pytest.raises(
        runner.HermeticReplayError,
        match="content/mode drift|shape drift",
    ):
        runner.verify_dependency_layer(layer, phase=f"test:{mutation}")


def test_installed_status_cli_write_and_parser_replay(tmp_path: Path) -> None:
    runner = _load_detached_runner()
    repository = Path(runner.REPO_ROOT)
    policy = runner.load_policy(
        repository / "docs/research_program/long_horizon_rescue/pr121_spec.yaml"
    )
    cwd = tmp_path / "unrelated-cwd"
    cwd.mkdir()
    env = runner.sanitized_environment(
        tmp_path / "home", source_date_epoch=policy.source_date_epoch
    )
    env["TMPDIR"] = str(tmp_path / "process-tmp")
    Path(env["TMPDIR"]).mkdir()
    structured, structured_hash, commands, checks = runner._replay_status(
        python=Path(sys.executable),
        cwd=cwd,
        detached=repository,
        env=env,
        policy=policy,
        receipt_roots={tmp_path: "$CELL", repository: "$DETACHED"},
    )
    assert len(commands) == 2
    assert list(commands[0].argv[1:4]) == ["-I", "-m", "common.status_snapshot"]
    assert checks["status_matrix_matches_snapshot"] is True
    assert checks["canonical_json_companions"] is True
    assert checks["status_matrix_excludes_generated_on"] is True
    metadata = structured["snapshot"]["metadata"]
    assert metadata["generated_on"] == policy.fixed_generated_on
    assert metadata["source_commit"] == policy.fixed_source_commit
    assert structured_hash == runner.sha256_bytes(
        runner.canonical_json_bytes(structured)
    )
    assert str(repository.resolve()) not in json.dumps(structured, sort_keys=True)


def test_build_receipt_success_and_divergent_replay_failure(monkeypatch) -> None:
    runner = _load_detached_runner()
    repository = Path(runner.REPO_ROOT)
    policy = runner.load_policy(
        repository / "docs/research_program/long_horizon_rescue/pr121_spec.yaml"
    )

    def fake_snapshot(*, destination: Path, **_kwargs):
        destination.mkdir(parents=True)
        return {
            "authority": "git_index",
            "authority_id": "sha256:" + "2" * 64,
            "declared_index_hash": "2" * 64,
            "declared_index_entry_count": 1,
            "archived_roots": ["htt"],
            "member_count": 1,
            "member_manifest_hash": "3" * 64,
            "source_tree_hash": "4" * 64,
            "contains_git_directory": False,
            "untracked_policy": "excluded_by_git_index_archive",
        }

    def fake_dependency(*, destination: Path, **_kwargs):
        return _synthetic_read_only_dependency_layer(runner, destination)

    def fake_artifacts(*, work: Path, **_kwargs):
        work.mkdir()
        placeholder = work / "artifact"
        return runner.BuildArtifacts(
            main_version="0.8.2+w8.2",
            compatibility_version="8.3.0",
            direct_main_wheel=placeholder,
            direct_compatibility_wheel=placeholder,
            main_sdist=placeholder,
            compatibility_sdist=placeholder,
            sdist_main_wheel=placeholder,
            sdist_compatibility_wheel=placeholder,
            receipt={"wheel_records": {}},
        )

    mutation_tests = [
        "test_source_byte_and_untracked_injection_change_tree_hash",
        "test_git_index_archive_excludes_untracked_sentinel",
        "test_wheel_path_collision_is_rejected",
        "test_compatibility_wheel_python_payload_is_rejected",
        "test_declared_package_data_missing_resource_is_rejected",
        "test_bound_input_drift_fails_check",
        "test_dependency_layer_mode_or_content_mutation_fails_closed[mode]",
        "test_dependency_layer_mode_or_content_mutation_fails_closed[content]",
    ]

    generator_checks = {
        "cli_module": "common.status_snapshot",
        "canonical_json_companions": True,
        "status_matrix_parser": "validate_status_matrix_matches_snapshot",
        "status_matrix_matches_snapshot": True,
        "claim_status_artifact_identity": True,
        "status_matrix_excludes_generated_on": True,
        "generated_on_normalized_to_policy": True,
    }

    def fake_cell(*, cell: str, index: int, dependency_layer, **_kwargs):
        ownership = {name: [policy.main_distribution] for name in policy.owned_top_levels}
        aliases = [
            {"canonical": canonical, "alias": alias, "identity": "same_object"}
            for canonical, alias in policy.compatibility_aliases
        ]
        before = runner.verify_dependency_layer(
            dependency_layer, phase=f"{cell}:before"
        )
        after = runner.verify_dependency_layer(
            dependency_layer, phase=f"{cell}:after"
        )
        return {
            "cell": cell,
            "status": "pass",
            "resolution_mode": "stubbed_process_boundary",
            "tests": {
                "executed": 1,
                "skipped": 0,
                "testcases": mutation_tests if index == 0 else ["smoke"],
            },
            "structured_hash": "6" * 64,
            "optional_dependencies": {
                name: {
                    "available": False,
                    "status": policy.optional_dispositions[name],
                    "counted_as_pass": False,
                }
                for name in policy.optional_imports
            },
            "generator_replay": generator_checks,
            "import_probe": {"ownership": ownership, "aliases": aliases},
            "dependency_layer_guard": {
                "before": before,
                "after": after,
                "unchanged": True,
            },
            "hostile_sentinels": {
                "pip_cache": "disabled_and_pre_post_immutable",
                "tmpdir_isolation": "per_cell_private",
                "tmpdir_relative_path": f"{cell}/process-tmp",
            },
        }

    monkeypatch.setattr(runner, "materialize_index_snapshot", fake_snapshot)
    monkeypatch.setattr(runner, "build_dependency_layer", fake_dependency)
    monkeypatch.setattr(runner, "build_project_artifacts", fake_artifacts)
    monkeypatch.setattr(runner, "run_install_cell", fake_cell)
    monkeypatch.setattr(
        runner,
        "bind_files",
        lambda *_args, **_kwargs: ({"path": "bound", "sha256": "7" * 64, "size": 1},),
    )
    receipt = runner.build_receipt(policy)
    assert receipt["overall_status"] == "pass"
    assert receipt["receipt_content_hash"] == runner.receipt_content_hash(receipt)
    markdown = runner.render_markdown(receipt)
    for field in (
        "config_hash",
        "sky_support_status",
        "null_mock_status",
        "source_authority_id",
        "worktree_state",
        "generating_command",
        "receipt_content_hash",
    ):
        assert f"- {field}:" in markdown
    assert "## Input hashes" in markdown
    assert "## Caveats" in markdown
    assert "## Dependency layer seal" in markdown
    assert "- physical_read_only: `True`" in markdown
    assert "- mode_policy: `files=0444_or_0555;directories=0555`" in markdown
    assert "- verified_cell_guard_count: `6`" in markdown
    assert "### Phase evidence" in markdown
    assert "`receipt:baseline`" in markdown
    assert "`build:before`" in markdown
    assert "`direct_main_then_compat:after`" in markdown
    assert "## Installed generator replay" in markdown
    assert "- execution_path: `python -I -m common.status_snapshot" in markdown
    assert "- check.status_matrix_excludes_generated_on: `True`" in markdown

    null_dependency = copy.deepcopy(receipt)
    null_dependency["dependency_layer_hash"] = None
    dependency = null_dependency["dependency_layer"]
    dependency["content_hash"] = None
    verification_rows = [
        dependency["baseline_verification"],
        dependency["build_guard"]["before"],
        dependency["build_guard"]["after"],
    ]
    verification_rows.extend(
        row[phase]
        for row in dependency["cell_guards"]
        for phase in ("before", "after")
    )
    verification_rows.extend(
        row["dependency_layer_guard"][phase]
        for row in null_dependency["install_matrix"]
        for phase in ("before", "after")
    )
    for row in verification_rows:
        row["content_mode_hash"] = None
    with pytest.raises(runner.HermeticReplayError, match="lowercase SHA-256"):
        runner.validate_policy_receipt(policy, null_dependency)

    for count_field in ("file_count", "directory_count"):
        null_count = copy.deepcopy(receipt)
        dependency = null_count["dependency_layer"]
        dependency[count_field] = None
        rows = [
            dependency["baseline_verification"],
            dependency["build_guard"]["before"],
            dependency["build_guard"]["after"],
        ]
        rows.extend(
            row[phase]
            for row in dependency["cell_guards"]
            for phase in ("before", "after")
        )
        rows.extend(
            row["dependency_layer_guard"][phase]
            for row in null_count["install_matrix"]
            for phase in ("before", "after")
        )
        for row in rows:
            row[count_field] = None
        with pytest.raises(runner.HermeticReplayError, match="positive integer"):
            runner.validate_policy_receipt(policy, null_count)

    null_structured_hash = copy.deepcopy(receipt)
    for row in null_structured_hash["install_matrix"]:
        row["structured_hash"] = None
    null_structured_hash["detached_generator_replay"]["structured_hash"] = None
    with pytest.raises(runner.HermeticReplayError, match="lowercase SHA-256"):
        runner.validate_policy_receipt(policy, null_structured_hash)

    reused_phase = copy.deepcopy(receipt)
    reused_phase["dependency_layer"]["build_guard"]["after"] = copy.deepcopy(
        reused_phase["dependency_layer"]["build_guard"]["before"]
    )
    with pytest.raises(runner.HermeticReplayError, match="build:after"):
        runner.validate_policy_receipt(policy, reused_phase)

    shared_tmpdir = copy.deepcopy(receipt)
    shared_tmpdir["install_matrix"][0]["hostile_sentinels"][
        "tmpdir_isolation"
    ] = "shared"
    with pytest.raises(runner.HermeticReplayError, match="private TMPDIR"):
        runner.validate_policy_receipt(policy, shared_tmpdir)

    receipt["install_matrix"][0]["status"] = "tampered"
    with pytest.raises(runner.HermeticReplayError, match="not passing|content hash"):
        runner.validate_policy_receipt(policy, receipt)

    def divergent_cell(**kwargs):
        row = fake_cell(**kwargs)
        if kwargs["index"] == 5:
            row["structured_hash"] = "8" * 64
        return row

    monkeypatch.setattr(runner, "run_install_cell", divergent_cell)
    with pytest.raises(runner.HermeticReplayError, match="differs across install cells"):
        runner.build_receipt(policy)
