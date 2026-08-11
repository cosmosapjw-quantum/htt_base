#!/usr/bin/env python3
"""Portable PR-291 CF4 preactivation runner.

Only the content-bound non-execution receipt can be built or replayed.  The
runner accepts no catalogue root, imports no OBSSTAT code before activation,
creates no observed-result directory, and performs no network or download.
"""

from __future__ import annotations

from io import BytesIO
import hashlib
import importlib.util
from importlib import metadata as importlib_metadata
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import time
import stat


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

# Reuse the already hostile-reviewed PR-290 filesystem transaction without
# modifying it.  Its implementation is explicitly source-bound below.
from run_pr290_planck_lane import (  # noqa: E402
    _atomic_write,
    _encoded,
    _tracked_manifest,
    _tracked_paths,
    _validate_output_destinations,
)


SPEC = ROOT / "docs/research_program/post_pr275/pr291_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr291_publication_policy.json"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
IDENTITY = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"
PR289_PROVENANCE_SOURCES = (
    ROOT / "docs/research_program/post_pr275/data_runbooks.yaml",
    ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json",
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
CLAIM_LEDGER = ROOT / "docs/harness/CLAIM_LEDGER.md"
PR290_COMMON_MODULE = ROOT / "htt/src/common/observed_lane_activation.py"
COMMON_MODULE = ROOT / "htt/src/common/cf4_observed_lane_activation.py"
DEPTH_MODULE = ROOT / "htt/src/common/depth_path.py"
SKY_SUPPORT_MODULE = ROOT / "htt/src/common/sky_support.py"
OBSSTAT_MODULE = ROOT / "htt/obsstat/cf4_post275_lane.py"
PR290_TRANSACTION_RUNNER = ROOT / "scripts/codex_harness/run_pr290_planck_lane.py"
TEST = ROOT / "tests/integration/test_cf4_post275_lane.py"
RUNNER = Path(__file__).resolve()
PR287_TERMINAL = ROOT / "docs/generated/pr287_fresh_blind_typed_replay_receipt.json"
OUTPUT = (
    ROOT
    / "docs/research_program/post_pr275/data_runs/cf4/"
    "PR291_NONEXECUTION_RECEIPT.json"
)
OBSERVED_RESULT_DIRECTORY = (
    ROOT / "docs/research_program/post_pr275/data_runs/cf4/results"
)
BOUND_SOURCES = (
    SPEC,
    POLICY,
    STATUS,
    IDENTITY,
    *PR289_PROVENANCE_SOURCES,
    CLAIM_LEDGER,
    PR290_COMMON_MODULE,
    COMMON_MODULE,
    DEPTH_MODULE,
    SKY_SUPPORT_MODULE,
    OBSSTAT_MODULE,
    TEST,
    PR290_TRANSACTION_RUNNER,
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


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(16 << 20):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _load_common_module(
    root: Path,
    *,
    source_bindings: dict[str, str],
) -> object:
    dependency_path = root / PR290_COMMON_MODULE.relative_to(ROOT)
    module_path = root / COMMON_MODULE.relative_to(ROOT)
    root_resolved = root.resolve(strict=True)
    dependency_relative = PR290_COMMON_MODULE.relative_to(ROOT).as_posix()
    module_relative = COMMON_MODULE.relative_to(ROOT).as_posix()
    for path, relative, label in (
        (dependency_path, dependency_relative, "PR-290 COMMON dependency"),
        (module_path, module_relative, "PR-291 COMMON module"),
    ):
        try:
            metadata = path.lstat()
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise RuntimeError(f"{label} is unavailable") from exc
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or not resolved.is_relative_to(root_resolved)
            or _sha(path) != source_bindings[relative]
        ):
            raise RuntimeError(f"{label} origin or bytes drifted")

    canonical_dependency_name = "common.observed_lane_activation"
    previous_dependency = sys.modules.get(canonical_dependency_name)
    dependency_spec = importlib.util.spec_from_file_location(
        canonical_dependency_name, dependency_path
    )
    if dependency_spec is None or dependency_spec.loader is None:
        raise RuntimeError("PR-290 COMMON dependency loader is unavailable")
    dependency = importlib.util.module_from_spec(dependency_spec)
    sys.modules[canonical_dependency_name] = dependency
    try:
        dependency_spec.loader.exec_module(dependency)
        dependency_origin = dependency_path.resolve(strict=True)
        if (
            Path(str(getattr(dependency, "__file__", ""))).resolve()
            != dependency_origin
            or _sha(dependency_path) != source_bindings[dependency_relative]
            or any(
                not callable(getattr(dependency, symbol, None))
                or Path(getattr(dependency, symbol).__code__.co_filename).resolve()
                != dependency_origin
                for symbol in (
                    "_load_pr289_identity_module",
                    "_validate_pr289_receipt_provenance",
                )
            )
        ):
            raise RuntimeError("executed PR-290 COMMON dependency origin drifted")

        module_name = "_htt_pr291_cf4_observed_lane_" + hashlib.sha256(
            (str(module_path.resolve()) + source_bindings[module_relative]).encode(
                "utf-8"
            )
        ).hexdigest()
        module_spec = importlib.util.spec_from_file_location(module_name, module_path)
        if module_spec is None or module_spec.loader is None:
            raise RuntimeError("PR-291 COMMON module loader is unavailable")
        module = importlib.util.module_from_spec(module_spec)
        sys.modules.pop(module_name, None)
        sys.modules[module_name] = module
        try:
            module_spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(module_name, None)
            raise RuntimeError("PR-291 COMMON module execution failed") from exc
        module_origin = module_path.resolve(strict=True)
        if (
            Path(str(getattr(module, "__file__", ""))).resolve() != module_origin
            or _sha(module_path) != source_bindings[module_relative]
            or any(
                not callable(getattr(module, symbol, None))
                or Path(getattr(module, symbol).__code__.co_filename).resolve()
                != module_origin
                for symbol in (
                    "build_cf4_activation_decision",
                    "build_cf4_nonexecution_receipt",
                )
            )
        ):
            sys.modules.pop(module_name, None)
            raise RuntimeError("executed PR-291 COMMON module origin drifted")
        return module
    finally:
        if previous_dependency is None:
            sys.modules.pop(canonical_dependency_name, None)
        else:
            sys.modules[canonical_dependency_name] = previous_dependency


def _base_source_bindings(root: Path = ROOT) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for source in BOUND_SOURCES:
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
    bindings = _base_source_bindings(root)
    module = _load_common_module(root, source_bindings=bindings)
    decision = module.build_cf4_activation_decision(
        repository_root=root,
        evaluated_at_utc=FROZEN_EVALUATION_TIME,
    )
    if decision.terminal != "BLOCKED_PREDECESSOR_FINAL_SUCCESS":
        raise RuntimeError(
            "frozen PR-291 preactivation terminal drifted; review before regeneration"
        )
    for row in decision.dependency_snapshot:
        terminal = row.get("terminal_receipt")
        if isinstance(terminal, dict) and terminal.get("file_sha256") is not None:
            relative = Path(str(terminal["path"]))
            path = root / relative
            if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
                raise RuntimeError(
                    f"terminal source binding is not a single-link file: {relative}"
                )
            bindings[relative.as_posix()] = _sha(path)
    return module.build_cf4_nonexecution_receipt(
        decision=decision,
        source_bindings=bindings,
        generation_identity=_generation_identity(bindings),
    )


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
        raise RuntimeError("frozen PR-291 receipt drifted; rerun build")
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
            ["-p", "no:cacheprovider", "-q", *(str(root / path) for path in paths)]
        )
    )


def _versions() -> dict[str, str]:
    values = {"python": sys.version.split()[0]}
    for distribution in ("PyYAML", "numpy", "pytest"):
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
    with tempfile.TemporaryDirectory(prefix="pr291-portable-") as temporary:
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
                "HTT_H_CF4_AUTHORITY_KEY_FILE",
            }
        }
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(clean), str(clean / "htt/src"), str(clean / "htt"))
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr291_cf4_lane.py",
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
                "clean PR-291 portable replay failed: "
                + (completed.stderr or completed.stdout)
            )
        clean_after = _tracked_manifest(clean, tracked)
        source_after = _tracked_manifest(ROOT, tracked)
        if clean_after != clean_before or source_after != source_before:
            raise RuntimeError("portable replay changed tracked bytes")
        print(
            json.dumps(
                {
                    "schema": "PR291_PORTABLE_CLEAN_EVIDENCE_V1",
                    "tracked_source_manifest": source_before,
                    "interpreter_and_dependency_versions": _versions(),
                    "scrubbed_environment_keys": {
                        "PYTHONHOME": "PYTHONHOME" not in environment,
                        "PYTHONPATH": "CLEAN_ROOT_ONLY",
                        "PYTHONSTARTUP": "PYTHONSTARTUP" not in environment,
                        "PYTEST_ADDOPTS": "PYTEST_ADDOPTS" not in environment,
                        "PYTEST_PLUGINS": "PYTEST_PLUGINS" not in environment,
                        "HTT_H_CF4_AUTHORITY_KEY_FILE": (
                            "HTT_H_CF4_AUTHORITY_KEY_FILE" not in environment
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
        return _pytest(("tests/integration/test_cf4_post275_lane.py",))
    if args.mode == "adjacent":
        return _pytest(
            (
                "tests/contracts/test_data_identity_registry_v2.py",
                "tests/contracts/test_depth_path.py",
                "tests/pr_cards/test_pr_251_orbit_nonlinearity.py",
                "tests/contracts/test_pr137_weak_id_coverage.py",
                "tests/contracts/test_weak_identification.py",
                "tests/obsstat/test_k6_cf4_curl_posterior.py",
                "tests/integration/test_planck_post275_lane.py",
            )
        )
    if args.mode == "check":
        return _check()
    return _portable()


if __name__ == "__main__":
    raise SystemExit(main())
