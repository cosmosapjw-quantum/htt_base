#!/usr/bin/env python3
"""Portable PR-289 identity-preflight runner with no acquisition side effects."""

from __future__ import annotations

from io import BytesIO
import hashlib
import importlib
from importlib import metadata as importlib_metadata
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT
    / "docs/research_program/post_pr275/data_registry_v2/"
    "LANE_REGISTRY_V2.json"
)
SPEC = ROOT / "docs/research_program/post_pr275/pr289_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr289_publication_policy.json"
RUNBOOKS = ROOT / "docs/research_program/post_pr275/data_runbooks.yaml"
CLAIM_LEDGER = ROOT / "docs/harness/CLAIM_LEDGER.md"
PR274_REGISTRY = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_DATA_IDENTITY_REGISTRY.yaml"
)
PR274_RESULT = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_ADMISSION_RESULT.json"
)
MODULE = ROOT / "htt/src/common/data_identity.py"
TEST = ROOT / "tests/contracts/test_data_identity_registry_v2.py"
RUNNER = Path(__file__).resolve()
OUTPUT = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"
SOURCE_PATHS = (ROOT, ROOT / "htt/src", ROOT / "htt")
BOUND_SOURCES = (
    REGISTRY,
    SPEC,
    POLICY,
    RUNBOOKS,
    CLAIM_LEDGER,
    PR274_REGISTRY,
    PR274_RESULT,
    MODULE,
    TEST,
    RUNNER,
)
PR274_REPLAY_COMMIT = "ff9ef9f45747e559c5343b463cf010dfc3a7432a"
PR274_LIVE_COMPATIBILITY_EXCLUSIONS = (
    "test_frozen_inputs_match_bytes_and_live_pr151_semantics",
    "test_committed_result_is_deterministic_and_source_bound",
    "test_live_status_self_closeout_does_not_mutate_result_provenance",
    "test_live_status_semantic_drift_still_fails_closed",
)


def _activate(root: Path = ROOT) -> None:
    paths = [str(root), str(root / "htt/src"), str(root / "htt")]
    sys.path[:] = paths + [entry for entry in sys.path if entry not in paths]
    existing = [
        entry
        for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep)
        if entry and entry not in paths
    ]
    os.environ["PYTHONPATH"] = os.pathsep.join((*paths, *existing))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_bindings(root: Path = ROOT) -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): _sha(
            root / path.relative_to(ROOT)
        )
        for path in BOUND_SOURCES
    }


def _generation_identity(source_bindings: dict[str, str]) -> dict[str, object]:
    normalized = {
        path: "sha256:" + digest.removeprefix("sha256:")
        for path, digest in source_bindings.items()
    }
    return {
        "schema": "common.source_bound_generation_identity.v1",
        "git_commit_or_worktree_state": "BOUND_SOURCE_WORKTREE:sha256:"
        + hashlib.sha256(
            json.dumps(
                normalized,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        ).hexdigest(),
        "generating_procedure": [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr289_data_identity_v2.py",
            "build",
        ],
    }


def _load_bound_data_identity_module(root: Path = ROOT):
    _activate(root)
    module_name = "common.data_identity"
    expected = (root / MODULE.relative_to(ROOT)).resolve()
    sys.modules.pop(module_name, None)
    importlib.invalidate_caches()
    module = importlib.import_module(module_name)
    origin = getattr(module, "__file__", None)
    spec = getattr(module, "__spec__", None)
    spec_origin = getattr(spec, "origin", None)
    loader = getattr(spec, "loader", None)
    if (
        not isinstance(origin, str)
        or Path(origin).resolve() != expected
        or not isinstance(spec_origin, str)
        or Path(spec_origin).resolve() != expected
        or loader is None
        or not hasattr(loader, "get_data")
    ):
        raise RuntimeError("PR-289 data-identity module escaped candidate root")
    loaded_bytes = loader.get_data(str(expected))
    expected_bytes = expected.read_bytes()
    if hashlib.sha256(loaded_bytes).digest() != hashlib.sha256(
        expected_bytes
    ).digest():
        raise RuntimeError("PR-289 data-identity module byte provenance drifted")
    for name in ("build_data_identity_v2_receipt", "load_lane_registry"):
        function = getattr(module, name, None)
        if function is None or getattr(function, "__module__", None) != module_name:
            raise RuntimeError("PR-289 data-identity factory origin drifted")
    return module


def _build(root: Path = ROOT) -> dict[str, object]:
    module = _load_bound_data_identity_module(root)

    source_bindings = _source_bindings(root)
    receipt = module.build_data_identity_v2_receipt(
        registry=module.load_lane_registry(
            root / REGISTRY.relative_to(ROOT)
        ),
        root_descriptors={},
        inspected_at_utc="2026-08-09T00:00:00+00:00",
        spec_path=root / SPEC.relative_to(ROOT),
        source_bindings=source_bindings,
        generation_identity=_generation_identity(source_bindings),
    )
    payload = receipt.as_payload()
    if payload["aggregate_status"] != "NO_ADMITTED_IDENTITIES":
        raise RuntimeError("clean preflight unexpectedly admitted a lane")
    if any(
        row["status"] != "NOT_AUTHORIZED"
        for row in payload["authorization_receipts"]
    ):
        raise RuntimeError("clean preflight unexpectedly authorized a lane")
    return payload


def _encoded(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def _validate_output_destination(
    *, root: Path, output: Path, require_existing: bool
) -> None:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("receipt root must be a regular directory")
    try:
        relative = output.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("receipt output escaped repository root") from exc
    cursor = root
    for part in relative.parent.parts:
        cursor /= part
        if cursor.is_symlink() or not cursor.is_dir():
            raise RuntimeError(
                f"receipt parent must be an existing regular directory: {cursor}"
            )
    if output.is_symlink():
        raise RuntimeError("receipt output must be a single-link regular file")
    if require_existing and not output.is_file():
        raise RuntimeError("receipt output must be a single-link regular file")
    if output.exists() and (
        not output.is_file() or output.stat().st_nlink != 1
    ):
        raise RuntimeError("receipt output must be a single-link regular file")


def _atomic_write(payload: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=OUTPUT.parent,
        prefix=f".{OUTPUT.name}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, OUTPUT)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write() -> int:
    try:
        _validate_output_destination(
            root=ROOT, output=OUTPUT, require_existing=False
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    payload = _build()
    _atomic_write(_encoded(payload))
    print(
        json.dumps(
            {
                "terminal": payload["terminal"],
                "receipt_content_id": payload["receipt_content_id"],
                "output": OUTPUT.relative_to(ROOT).as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


def _check(root: Path = ROOT) -> int:
    output = root / OUTPUT.relative_to(ROOT)
    _validate_output_destination(
        root=root, output=output, require_existing=True
    )
    expected = _encoded(_build(root))
    observed = output.read_bytes()
    if observed != expected:
        raise RuntimeError("frozen PR-289 receipt drifted; rerun build")
    print(
        json.dumps(
            {
                "terminal": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
                "aggregate_status": "NO_ADMITTED_IDENTITIES",
                "receipt_sha256": hashlib.sha256(observed).hexdigest(),
                "observed_data_executed": False,
                "public_use": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _pytest(
    paths: tuple[str, ...],
    root: Path = ROOT,
    *,
    extra: tuple[str, ...] = (),
) -> int:
    _activate(root)
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *extra,
                *(str(root / path) for path in paths),
            ]
        )
    )


def _preflight() -> int:
    payload = _build()
    print(
        json.dumps(
            {
                "terminal": payload["terminal"],
                "aggregate_status": payload["aggregate_status"],
                "lane_statuses": [
                    row["status"] for row in payload["lane_decisions"]
                ],
                "authorization_statuses": [
                    row["status"]
                    for row in payload["authorization_receipts"]
                ],
                "network_or_download_side_effect": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _tracked_paths(root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("tracked-file inventory failed")
    return tuple(
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    )


def _tracked_manifest(root: Path, paths: tuple[str, ...]) -> dict[str, object]:
    identities: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"tracked member is not regular: {relative}")
        identities[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    encoded = json.dumps(
        identities, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return {
        "file_count": len(identities),
        "manifest_sha256": hashlib.sha256(encoded).hexdigest(),
        "path_inventory_sha256": hashlib.sha256(
            "\0".join(identities).encode("utf-8")
        ).hexdigest(),
        "content_identity_inventory_sha256": hashlib.sha256(
            "\0".join(identities.values()).encode("ascii")
        ).hexdigest(),
    }


def _versions() -> dict[str, str]:
    values = {"python": sys.version.split()[0]}
    for distribution in ("PyYAML", "pytest"):
        try:
            values[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            values[distribution] = "UNAVAILABLE"
    return values


def _safe_extract_archive(archive: tarfile.TarFile, destination: Path) -> None:
    root = destination.resolve(strict=True)
    members = archive.getmembers()
    for member in members:
        relative = PurePosixPath(member.name)
        target = root.joinpath(*relative.parts)
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
            or (target != root and root not in target.resolve().parents)
            or not (member.isfile() or member.isdir())
        ):
            raise RuntimeError(f"unsafe archive member: {member.name}")
    archive.extractall(destination, members=members)


def _adjacent() -> int:
    selector = " and ".join(
        f"not {name}" for name in PR274_LIVE_COMPATIBILITY_EXCLUSIONS
    )
    current_exit = _pytest(
        ("tests/contracts/test_vector_tensor_data_admission.py",),
        extra=("-k", selector),
    )
    if current_exit != 0:
        return current_exit

    archive = subprocess.check_output(
        ["git", "archive", PR274_REPLAY_COMMIT], cwd=ROOT
    )
    with tempfile.TemporaryDirectory(prefix="pr289-pr274-replay-") as temporary:
        replay_root = Path(temporary) / "repo"
        replay_root.mkdir()
        with tarfile.open(fileobj=BytesIO(archive), mode="r:") as handle:
            _safe_extract_archive(handle, replay_root)
        environment = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "PYTHONHOME",
                "PYTHONPATH",
                "PYTHONSTARTUP",
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
            }
        }
        environment["PYTHONPATH"] = os.pathsep.join(
            (
                str(replay_root),
                str(replay_root / "htt/src"),
                str(replay_root / "htt"),
            )
        )
        command = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "tests/contracts/test_vector_tensor_data_admission.py",
        ]
        completed = subprocess.run(
            command,
            cwd=replay_root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        if completed.returncode != 0:
            print(completed.stdout + completed.stderr, file=sys.stderr)
            return completed.returncode
        print(completed.stdout, end="")
    print(
        json.dumps(
            {
                "terminal": "PASS_PR274_IMMUTABLE_AND_LIVE_COMPATIBILITY",
                "historical_replay_commit": PR274_REPLAY_COMMIT,
                "live_source_bound_tests_replayed_only_in_historical_context": list(
                    PR274_LIVE_COMPATIBILITY_EXCLUSIONS
                ),
            },
            sort_keys=True,
        )
    )
    return 0


def _portable() -> int:
    if subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        cwd=ROOT,
        text=True,
    ):
        raise RuntimeError("portable replay requires a clean committed candidate")
    tracked = _tracked_paths(ROOT)
    source_before = _tracked_manifest(ROOT, tracked)
    archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix="pr289-portable-") as temporary:
        clean = Path(temporary) / "repo"
        clean.mkdir()
        with tarfile.open(fileobj=BytesIO(archive), mode="r:") as handle:
            _safe_extract_archive(handle, clean)
        clean_before = _tracked_manifest(clean, tracked)
        if clean_before != source_before:
            raise RuntimeError("clean archive manifest differs from source")
        environment = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "PYTHONHOME",
                "PYTHONPATH",
                "PYTHONSTARTUP",
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
            }
        }
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(clean), str(clean / "htt/src"), str(clean / "htt"))
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr289_data_identity_v2.py",
            "check",
        ]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=clean,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        elapsed = time.perf_counter() - started
        if completed.returncode != 0:
            raise RuntimeError(
                "clean portable replay failed: "
                + (completed.stderr or completed.stdout)
            )
        clean_after = _tracked_manifest(clean, tracked)
        source_after = _tracked_manifest(ROOT, tracked)
        if clean_after != clean_before or source_after != source_before:
            raise RuntimeError("portable replay changed tracked bytes")
        print(
            json.dumps(
                {
                    "schema": "PR289_PORTABLE_CLEAN_EVIDENCE_V2",
                    "tracked_source_manifest": source_before,
                    "interpreter_and_dependency_versions": _versions(),
                    "scrubbed_environment_keys": {
                        "PYTHONHOME": "PYTHONHOME" not in environment,
                        "PYTHONPATH": "CLEAN_ROOT_ONLY",
                        "PYTHONSTARTUP": "PYTHONSTARTUP" not in environment,
                        "PYTEST_ADDOPTS": "PYTEST_ADDOPTS" not in environment,
                        "PYTEST_PLUGINS": "PYTEST_PLUGINS" not in environment,
                    },
                    "exact_command": command,
                    "exact_command_runtime_seconds": elapsed,
                    "nested_exit_code": completed.returncode,
                    "nested_stdout_sha256": hashlib.sha256(
                        completed.stdout.encode("utf-8")
                    ).hexdigest(),
                    "source_tracked_manifest_sha256": source_before[
                        "manifest_sha256"
                    ],
                    "source_tracked_file_count": source_before["file_count"],
                    "clean_extracted_file_count": clean_before["file_count"],
                    "clean_extracted_content_sha256": clean_before[
                        "manifest_sha256"
                    ],
                    "source_root_pre_hash": source_before["manifest_sha256"],
                    "source_root_post_hash": source_after["manifest_sha256"],
                    "clean_root_pre_hash": clean_before["manifest_sha256"],
                    "clean_root_post_hash": clean_after["manifest_sha256"],
                    "source_root_differs_from_execution_root": clean != ROOT,
                    "external_roots_supplied": False,
                    "network_or_download_side_effect": False,
                },
                sort_keys=True,
            )
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=(
            "build",
            "focused",
            "preflight",
            "adjacent",
            "check",
            "portable",
        ),
    )
    args = parser.parse_args(argv)
    if args.mode == "build":
        return _write()
    if args.mode == "focused":
        return _pytest(("tests/contracts/test_data_identity_registry_v2.py",))
    if args.mode == "preflight":
        return _preflight()
    if args.mode == "adjacent":
        return _adjacent()
    if args.mode == "check":
        return _check()
    return _portable()


if __name__ == "__main__":
    raise SystemExit(main())
