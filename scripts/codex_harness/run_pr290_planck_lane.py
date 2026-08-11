#!/usr/bin/env python3
"""Portable PR-290 Planck preactivation runner.

The runner can build or replay only the non-execution receipt.  It supplies no
observed input root, imports no OBSSTAT module before activation, creates no
observed result directory, and performs no network or download operation.
"""

from __future__ import annotations

from io import BytesIO
import hashlib
import importlib.util
from importlib import metadata as importlib_metadata
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import tarfile
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr290_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr290_publication_policy.json"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
IDENTITY = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"
PR289_PROVENANCE_SOURCES = (
    ROOT / "docs/research_program/post_pr275/data_runbooks.yaml",
    ROOT
    / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json",
    ROOT / "docs/research_program/post_pr275/pr289_publication_policy.json",
    ROOT / "docs/research_program/post_pr275/pr289_spec.yaml",
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_ADMISSION_RESULT.json",
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_DATA_IDENTITY_REGISTRY.yaml",
    ROOT / "htt/src/common/data_identity.py",
    ROOT / "scripts/codex_harness/run_pr289_data_identity_v2.py",
    ROOT / "tests/contracts/test_data_identity_registry_v2.py",
)
PR287_TERMINAL = ROOT / "docs/generated/pr287_fresh_blind_typed_replay_receipt.json"
PR288_TERMINAL = ROOT / "docs/generated/pr288_bayesian_semantics_receipt.json"
CLAIM_LEDGER = ROOT / "docs/harness/CLAIM_LEDGER.md"
COMMON_MODULE = ROOT / "htt/src/common/observed_lane_activation.py"
OBSSTAT_MODULE = ROOT / "htt/obsstat/planck_post275_lane.py"
BOOST_MODULE = ROOT / "htt/obsstat/boost_biposh_residual.py"
TEST = ROOT / "tests/integration/test_planck_post275_lane.py"
RUNNER = Path(__file__).resolve()
OUTPUT = (
    ROOT
    / "docs/research_program/post_pr275/data_runs/planck/"
    "PR290_NONEXECUTION_RECEIPT.json"
)
OBSERVED_RESULT_DIRECTORY = (
    ROOT / "docs/research_program/post_pr275/data_runs/planck/results"
)
BOUND_SOURCES = (
    SPEC,
    POLICY,
    STATUS,
    IDENTITY,
    *PR289_PROVENANCE_SOURCES,
    PR288_TERMINAL,
    CLAIM_LEDGER,
    COMMON_MODULE,
    OBSSTAT_MODULE,
    BOOST_MODULE,
    TEST,
    RUNNER,
)
FROZEN_EVALUATION_TIME = "2026-08-09T00:00:00+00:00"


def _activate(root: Path = ROOT) -> None:
    paths = [str(root), str(root / "htt/src"), str(root / "htt")]
    sys.path[:] = paths + [entry for entry in sys.path if entry not in paths]
    existing = [
        entry
        for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep)
        if entry and entry not in paths
    ]
    os.environ["PYTHONPATH"] = os.pathsep.join((*paths, *existing))


def _load_common_module(
    root: Path, *, expected_sha256: str
) -> object:
    module_path = root / COMMON_MODULE.relative_to(ROOT)
    root_resolved = root.resolve(strict=True)
    try:
        metadata = module_path.lstat()
        resolved = module_path.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("PR-290 COMMON module is unavailable") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or not resolved.is_relative_to(root_resolved)
        or _sha(module_path) != expected_sha256
    ):
        raise RuntimeError("PR-290 COMMON module origin or bytes drifted")
    module_name = "_htt_pr290_observed_lane_" + hashlib.sha256(
        (str(resolved) + expected_sha256).encode("utf-8")
    ).hexdigest()
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("PR-290 COMMON module loader is unavailable")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules.pop(module_name, None)
    sys.modules[module_name] = module
    try:
        module_spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise RuntimeError("PR-290 COMMON module execution failed") from exc
    required_symbols = (
        "build_planck_activation_decision",
        "build_planck_nonexecution_receipt",
    )
    if (
        Path(str(getattr(module, "__file__", ""))).resolve() != resolved
        or _sha(module_path) != expected_sha256
        or any(
            not callable(getattr(module, symbol, None))
            or Path(getattr(module, symbol).__code__.co_filename).resolve()
            != resolved
            for symbol in required_symbols
        )
    ):
        sys.modules.pop(module_name, None)
        raise RuntimeError("executed PR-290 COMMON module origin drifted")
    return module


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(16 << 20):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _source_bindings(root: Path = ROOT) -> dict[str, str]:
    bindings: dict[str, str] = {}
    sources = list(BOUND_SOURCES)
    optional_pr287 = root / PR287_TERMINAL.relative_to(ROOT)
    if optional_pr287.exists() or optional_pr287.is_symlink():
        sources.append(PR287_TERMINAL)
    for source in sources:
        relative = source.relative_to(ROOT)
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            raise RuntimeError(f"source binding is not a single-link file: {relative}")
        bindings[relative.as_posix()] = _sha(path)
    return bindings


def _generation_identity(source_bindings: dict[str, str]) -> dict[str, object]:
    encoded = json.dumps(
        source_bindings, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return {
        "source_commit_or_external_candidate_seal_id": (
            "sha256:" + hashlib.sha256(encoded).hexdigest()
        ),
        "worktree_state": "source_hash_bound_dirty_or_committed",
        "exact_replay_environment": "repository_python_contract",
    }


def _build(root: Path = ROOT) -> dict[str, object]:
    _activate(root)
    bindings = _source_bindings(root)
    common_relative = COMMON_MODULE.relative_to(ROOT).as_posix()
    module = _load_common_module(
        root, expected_sha256=bindings[common_relative]
    )
    decision = module.build_planck_activation_decision(
        repository_root=root,
        evaluated_at_utc=FROZEN_EVALUATION_TIME,
    )
    if decision.terminal != "BLOCKED_PREDECESSOR_FINAL_SUCCESS":
        raise RuntimeError(
            "frozen preactivation terminal drifted; review before regenerating"
        )
    return module.build_planck_nonexecution_receipt(
        decision=decision,
        source_bindings=bindings,
        generation_identity=_generation_identity(bindings),
    )


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


def _validate_output_destinations(
    *,
    root: Path,
    output: Path,
    observed_result_directory: Path,
    require_existing: bool,
) -> None:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("receipt root must be a regular directory")
    root_resolved = root.resolve(strict=True)
    try:
        relative = output.relative_to(root)
        result_relative = observed_result_directory.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("PR-290 output escaped repository root") from exc
    cursor = root
    for part in relative.parent.parts:
        cursor /= part
        try:
            metadata = cursor.lstat()
        except OSError as exc:
            raise RuntimeError(f"receipt parent is missing: {cursor}") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(
                f"receipt parent must be a regular directory: {cursor}"
            )
        if not cursor.resolve(strict=True).is_relative_to(root_resolved):
            raise RuntimeError("receipt parent resolved outside repository")
    if output.exists() or output.is_symlink():
        metadata = output.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
        ):
            raise RuntimeError("receipt output must be a single-link regular file")
        if not output.resolve(strict=True).is_relative_to(root_resolved):
            raise RuntimeError("receipt output resolved outside repository")
    elif require_existing:
        raise RuntimeError("receipt output is missing")
    # A blocked preactivation may not even create the future observed result
    # directory.  An alias and an ordinary directory are both refused.
    result_path = root / result_relative
    if result_path.exists() or result_path.is_symlink():
        raise RuntimeError(
            "observed result directory must remain absent while PR-290 is blocked"
        )


def _atomic_write(
    output: Path,
    payload: bytes,
    *,
    root: Path,
    observed_result_directory: Path,
) -> None:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory_fd = os.open(output.parent, directory_flags)
    temporary_name = f".{output.name}.{secrets.token_hex(16)}"
    temporary_path = output.parent / temporary_name
    temporary_exists = False

    def require_stable_parent() -> None:
        try:
            current = output.parent.lstat()
            opened = os.fstat(directory_fd)
            root_resolved = root.resolve(strict=True)
            parent_resolved = output.parent.resolve(strict=True)
        except OSError as exc:
            raise RuntimeError("receipt parent changed during commit") from exc
        if (
            stat.S_ISLNK(current.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino)
            or not parent_resolved.is_relative_to(root_resolved)
        ):
            raise RuntimeError("receipt parent changed during commit")

    def remove_committed_output() -> None:
        try:
            metadata = os.stat(
                output.name, dir_fd=directory_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            return
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise RuntimeError("receipt rollback found an unsafe output")
        os.unlink(output.name, dir_fd=directory_fd)
        os.fsync(directory_fd)

    try:
        require_stable_parent()
        file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            file_flags |= os.O_NOFOLLOW
        file_fd = os.open(
            temporary_name,
            file_flags,
            0o600,
            dir_fd=directory_fd,
        )
        temporary_exists = True
        with os.fdopen(file_fd, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _validate_output_destinations(
            root=root,
            output=output,
            observed_result_directory=observed_result_directory,
            require_existing=False,
        )
        require_stable_parent()
        try:
            destination_stat = os.stat(
                output.name, dir_fd=directory_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            destination_stat = None
        if destination_stat is not None and (
            not stat.S_ISREG(destination_stat.st_mode)
            or destination_stat.st_nlink != 1
        ):
            raise RuntimeError(
                "receipt output changed to a non-single-link destination"
            )
        try:
            # Resolve both source and destination through the live repository
            # path.  A displaced open dirfd cannot redirect the commit.
            os.replace(temporary_path, output)
        except OSError as exc:
            raise RuntimeError("receipt commit path changed") from exc
        temporary_exists = False
        try:
            require_stable_parent()
            _validate_output_destinations(
                root=root,
                output=output,
                observed_result_directory=observed_result_directory,
                require_existing=True,
            )
            os.fsync(directory_fd)
            # The durability barrier is part of the transaction.  Recheck
            # both the open directory identity and the forbidden output lane
            # after it completes.
            require_stable_parent()
            _validate_output_destinations(
                root=root,
                output=output,
                observed_result_directory=observed_result_directory,
                require_existing=True,
            )
        except (OSError, RuntimeError) as exc:
            remove_committed_output()
            if isinstance(exc, RuntimeError):
                raise
            raise RuntimeError("receipt commit validation failed") from exc
    except OSError as exc:
        raise RuntimeError("receipt atomic write failed") from exc
    finally:
        if temporary_exists:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        os.close(directory_fd)


def _write(*, root: Path = ROOT, output: Path | None = None) -> int:
    destination = output or (root / OUTPUT.relative_to(ROOT))
    observed = root / OBSERVED_RESULT_DIRECTORY.relative_to(ROOT)
    try:
        _validate_output_destinations(
            root=root,
            output=destination,
            observed_result_directory=observed,
            require_existing=False,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    # Payload generation intentionally occurs only after all destinations pass.
    payload = _build(root)
    try:
        _validate_output_destinations(
            root=root,
            output=destination,
            observed_result_directory=observed,
            require_existing=False,
        )
        _atomic_write(
            destination,
            _encoded(payload),
            root=root,
            observed_result_directory=observed,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "terminal": payload["terminal"],
                "receipt_content_sha256": payload["receipt_content_sha256"],
                "output": destination.relative_to(root).as_posix(),
                "numeric_outputs_written": [],
                "observed_data_executed": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _check(root: Path = ROOT) -> int:
    output = root / OUTPUT.relative_to(ROOT)
    observed = root / OBSERVED_RESULT_DIRECTORY.relative_to(ROOT)
    _validate_output_destinations(
        root=root,
        output=output,
        observed_result_directory=observed,
        require_existing=True,
    )
    expected = _encoded(_build(root))
    observed_bytes = output.read_bytes()
    if observed_bytes != expected:
        raise RuntimeError("frozen PR-290 receipt drifted; rerun build")
    payload = json.loads(observed_bytes)
    print(
        json.dumps(
            {
                "terminal": payload["terminal"],
                "receipt_sha256": hashlib.sha256(observed_bytes).hexdigest(),
                "numeric_outputs_written": payload["numeric_outputs_written"],
                "observed_data_executed": payload["observed_data_executed"],
                "network_or_download_side_effect": payload[
                    "network_or_download_side_effect"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


def _pytest(paths: tuple[str, ...], root: Path = ROOT) -> int:
    _activate(root)
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *(str(root / path) for path in paths),
            ]
        )
    )


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
        item.decode("utf-8") for item in completed.stdout.split(b"\0") if item
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
    for distribution in ("PyYAML", "numpy", "healpy", "pytest"):
        try:
            values[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            values[distribution] = "UNAVAILABLE"
    return values


def _portable() -> int:
    if subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
    ):
        raise RuntimeError("portable replay requires a clean committed candidate")
    tracked = _tracked_paths(ROOT)
    source_before = _tracked_manifest(ROOT, tracked)
    archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix="pr290-portable-") as temporary:
        clean = Path(temporary) / "repo"
        clean.mkdir()
        with tarfile.open(fileobj=BytesIO(archive), mode="r:") as handle:
            handle.extractall(clean, filter="data")
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
                "HTT_H_PLANCK_AUTHORITY_KEY_FILE",
            }
        }
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(clean), str(clean / "htt/src"), str(clean / "htt"))
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr290_planck_lane.py",
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
                    "schema": "PR290_PORTABLE_CLEAN_EVIDENCE_V1",
                    "tracked_source_manifest": source_before,
                    "interpreter_and_dependency_versions": _versions(),
                    "scrubbed_environment_keys": {
                        "PYTHONHOME": "PYTHONHOME" not in environment,
                        "PYTHONPATH": "CLEAN_ROOT_ONLY",
                        "PYTHONSTARTUP": "PYTHONSTARTUP" not in environment,
                        "PYTEST_ADDOPTS": "PYTEST_ADDOPTS" not in environment,
                        "PYTEST_PLUGINS": "PYTEST_PLUGINS" not in environment,
                        "HTT_H_PLANCK_AUTHORITY_KEY_FILE": (
                            "HTT_H_PLANCK_AUTHORITY_KEY_FILE" not in environment
                        ),
                    },
                    "exact_command": command,
                    "exact_command_runtime_seconds": elapsed,
                    "nested_exit_code": completed.returncode,
                    "nested_stdout_sha256": hashlib.sha256(
                        completed.stdout.encode("utf-8")
                    ).hexdigest(),
                    "source_root_pre_hash": source_before["manifest_sha256"],
                    "source_root_post_hash": source_after["manifest_sha256"],
                    "clean_root_pre_hash": clean_before["manifest_sha256"],
                    "clean_root_post_hash": clean_after["manifest_sha256"],
                    "source_root_differs_from_execution_root": clean != ROOT,
                    "external_roots_supplied": False,
                    "network_or_download_side_effect": False,
                    "observed_data_executed": False,
                },
                sort_keys=True,
            )
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("build", "focused", "adjacent", "check", "portable")
    )
    args = parser.parse_args(argv)
    if args.mode == "build":
        return _write()
    if args.mode == "focused":
        return _pytest(("tests/integration/test_planck_post275_lane.py",))
    if args.mode == "adjacent":
        return _pytest(
            (
                "tests/contracts/test_data_identity_registry_v2.py",
                "tests/contracts/test_pr135_finite_null_ranking.py",
                "tests/contracts/test_pr149_k1_convention.py",
                "tests/contracts/test_k1_evenl_biposh_rank.py",
                "tests/obsstat/test_lowell_map_features.py",
                "tests/obsstat/test_scalar_lowell.py",
                "tests/obsstat/test_biposh_features.py",
            )
        )
    if args.mode == "check":
        return _check()
    return _portable()


if __name__ == "__main__":
    raise SystemExit(main())
