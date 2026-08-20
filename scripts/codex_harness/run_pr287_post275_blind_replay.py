#!/usr/bin/env python3
"""Fail-closed PR-287 activation and fresh-blind validation runner.

The predecessor stack is open at the exact sealed head.  Fresh execution is
still typed-INCONCLUSIVE because the capability-isolated analyst executor is
not installed.  ``check`` and ``historical`` validate that precise boundary
and never turn it into a fresh replay pass.
"""

from __future__ import annotations

from io import BytesIO
import hashlib
from importlib import metadata as importlib_metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr287_spec.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
FRESH_OUTPUTS = (
    "docs/research_program/post_pr275/blind_replay/FRESH_CHALLENGE_V1.json",
    "docs/research_program/post_pr275/blind_replay/FRESH_TRUTH_VAULT_V1.json",
    "docs/research_program/post_pr275/blind_replay/FROZEN_SUBMISSION_V1.json",
    "docs/research_program/post_pr275/blind_replay/SUBMISSION_FREEZE_RECEIPT_V1.json",
    "docs/research_program/post_pr275/blind_replay/REGISTERED_ADJUDICATION_V1.json",
    "docs/research_program/post_pr275/blind_replay/PACK_A_V1.json",
    "docs/research_program/post_pr275/blind_replay/PACK_B_V1.json",
    "docs/research_program/post_pr275/blind_replay/PACK_C_V1.json",
    "docs/research_program/post_pr275/blind_replay/HISTORICAL_REPLAY_RECEIPT_V1.json",
    "docs/generated/pr287_fresh_blind_typed_replay_receipt.json",
)
EXECUTION_BLOCKER = "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED"


def _activate_sources(root: Path = ROOT) -> None:
    for path in reversed((root / "htt", root / "htt/src")):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _activation(root: Path = ROOT):
    _activate_sources(root)
    from common.post275_blind_replay import build_dependency_activation_receipt

    return build_dependency_activation_receipt(
        spec_path=root / SPEC.relative_to(ROOT),
        status_path=root / STATUS.relative_to(ROOT),
        repository_root=root,
    )


def _fresh_outputs(root: Path = ROOT) -> tuple[Path, ...]:
    return tuple(root / relative for relative in FRESH_OUTPUTS)


def _assert_no_fresh_outputs(root: Path = ROOT) -> None:
    present = [str(path.relative_to(root)) for path in _fresh_outputs(root) if path.exists()]
    if present:
        raise RuntimeError(
            "fresh artifacts exist without completed isolated execution: "
            + ", ".join(present)
        )


def _verify_activated_blocker(*, lane: str, root: Path = ROOT) -> int:
    from common.post275_blind_replay import (
        DependencyActivationStatus,
        require_dependency_activation,
    )

    receipt = _activation(root)
    if receipt.status is not DependencyActivationStatus.ACTIVATED:
        raise RuntimeError("exact predecessor activation is not satisfied")
    require_dependency_activation(receipt)
    _assert_no_fresh_outputs(root)
    print(
        json.dumps(
            {
                "status": receipt.status.value,
                "terminal": receipt.terminal,
                "execution_disposition": "INCONCLUSIVE",
                "execution_blocker": EXECUTION_BLOCKER,
                "requested_lane": lane,
                "receipt_content_id": receipt.receipt_content_id,
                "fresh_artifacts_present": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _pytest(paths: tuple[str, ...]) -> int:
    env = dict(os.environ)
    for key in (
        "PYTHONHOME",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONSTARTUP",
        "PR287_ORBIT_ACTIVATION_OVERRIDE",
    ):
        env.pop(key, None)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "htt/src"), str(ROOT / "htt")))
    command = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        *paths,
    ]
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def _tracked_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("git tracked-file inventory failed")
    return tuple(
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    )


def _manifest(root: Path, paths: tuple[str, ...]) -> dict[str, object]:
    identities: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"tracked manifest member is not regular: {relative}")
        identities[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    encoded = json.dumps(
        identities, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    path_inventory = "\0".join(identities).encode("utf-8")
    content_inventory = "\0".join(identities.values()).encode("ascii")
    return {
        "file_count": len(identities),
        "manifest_sha256": hashlib.sha256(encoded).hexdigest(),
        "path_inventory_sha256": hashlib.sha256(path_inventory).hexdigest(),
        "content_identity_inventory_sha256": hashlib.sha256(
            content_inventory
        ).hexdigest(),
        "per_file_sha256": identities,
    }


def _manifest_evidence(manifest: dict[str, object]) -> dict[str, object]:
    return {
        key: manifest[key]
        for key in (
            "file_count",
            "manifest_sha256",
            "path_inventory_sha256",
            "content_identity_inventory_sha256",
        )
    }


def _dependency_versions() -> dict[str, str]:
    versions = {"python": sys.version.split()[0]}
    for distribution in ("numpy", "scipy", "PyYAML", "pytest"):
        try:
            versions[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            versions[distribution] = "UNAVAILABLE"
    return versions


def _portable() -> int:
    source_activation = _activation(ROOT)
    from common.post275_blind_replay import (
        DependencyActivationStatus,
        require_dependency_activation,
    )
    if source_activation.status is not DependencyActivationStatus.ACTIVATED:
        print("portable lane requires exact predecessor activation", file=sys.stderr)
        return 1
    require_dependency_activation(source_activation)
    _assert_no_fresh_outputs(ROOT)
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0 or status.stdout:
        print("portable replay requires a clean committed candidate", file=sys.stderr)
        return 1
    tracked_paths = _tracked_paths()
    source_before = _manifest(ROOT, tracked_paths)
    archived = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if archived.returncode != 0:
        print("git archive failed", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="pr287-portable-") as directory:
        clean_root = Path(directory) / "source"
        clean_root.mkdir()
        with tarfile.open(fileobj=BytesIO(archived.stdout), mode="r:") as archive:
            archive.extractall(clean_root, filter="data")
        clean_before = _manifest(clean_root, tracked_paths)
        if clean_before != source_before:
            print("clean archive manifest differs from source", file=sys.stderr)
            return 1
        before = tuple(path.exists() for path in _fresh_outputs(clean_root))
        env = dict(os.environ)
        for key in (
            "PYTHONPATH",
            "PYTHONHOME",
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "PYTHONSTARTUP",
            "PR287_ORBIT_ACTIVATION_OVERRIDE",
        ):
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join(
            (str(clean_root / "htt/src"), str(clean_root / "htt"))
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr287_post275_blind_replay.py",
            "check",
        ]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=clean_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        runtime_seconds = time.perf_counter() - started
        after = tuple(path.exists() for path in _fresh_outputs(clean_root))
        if before != after or any(after):
            print("portable replay created a fresh artifact", file=sys.stderr)
            return 1
        clean_after = _manifest(clean_root, tracked_paths)
        source_after = _manifest(ROOT, tracked_paths)
        if clean_after != clean_before or source_after != source_before:
            print("portable replay changed source or clean tracked bytes", file=sys.stderr)
            return 1
        scrubbed = (
            "PYTHONPATH",
            "PYTHONHOME",
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "PYTHONSTARTUP",
            "PR287_ORBIT_ACTIVATION_OVERRIDE",
        )
        evidence = {
            "schema": "PR287_PORTABLE_ACTIVATED_BLOCKER_EVIDENCE_V1",
            "source_activation_receipt_content_id": (
                source_activation.receipt_content_id
            ),
            "execution_disposition": "INCONCLUSIVE",
            "execution_blocker": EXECUTION_BLOCKER,
            "tracked_source_manifest_and_content_ids": _manifest_evidence(
                source_before
            ),
            "interpreter_and_dependency_versions": _dependency_versions(),
            "scrubbed_environment_keys": {
                key: key not in env for key in scrubbed if key != "PYTHONPATH"
            }
            | {"PYTHONPATH": "CLEAN_ROOT_ONLY"},
            "exact_command": command,
            "exact_command_exit_code": completed.returncode,
            "exact_command_runtime_seconds": runtime_seconds,
            "nested_stdout_sha256": hashlib.sha256(
                completed.stdout.encode("utf-8")
            ).hexdigest(),
            "nested_stderr_sha256": hashlib.sha256(
                completed.stderr.encode("utf-8")
            ).hexdigest(),
            "source_root_pre_hash": source_before["manifest_sha256"],
            "source_root_post_hash": source_after["manifest_sha256"],
            "clean_root_pre_hash": clean_before["manifest_sha256"],
            "clean_root_post_hash": clean_after["manifest_sha256"],
            "source_root_differs_from_execution_root": ROOT != clean_root,
            "zero_untracked_truth_submission_adjudication_or_pack_inputs": (
                not any(after)
            ),
        }
        print(json.dumps(evidence, sort_keys=True))
        return completed.returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    modes = {"activation", "build", "check", "focused", "adjacent", "historical", "portable"}
    if len(args) != 1 or args[0] not in modes:
        print(
            "usage: run_pr287_post275_blind_replay.py "
            "{activation|build|check|focused|adjacent|historical|portable}",
            file=sys.stderr,
        )
        return 2
    mode = args[0]
    if mode == "focused":
        return _pytest(("tests/integration/test_post275_blind_replay.py",))
    if mode == "adjacent":
        return _pytest(
            (
                "tests/contracts/test_joint_anisotropy_state.py",
                "tests/obsstat/test_exact_parity_readiness.py",
                "tests/contracts/test_weak_identification.py",
                "tests/contracts/test_depth_path_doob_calibration.py",
                "tests/contracts/test_pillar_t_complete_adjudication.py",
                "tests/contracts/test_pillar_s_complete_adjudication.py",
            )
        )
    if mode == "portable":
        return _portable()

    _activate_sources()
    from common.post275_blind_replay import (
        DependencyActivationStatus,
        require_dependency_activation,
    )

    receipt = _activation()
    if mode == "activation":
        print(json.dumps(receipt.as_payload(), indent=2, sort_keys=True))
        return 0 if receipt.status is DependencyActivationStatus.ACTIVATED else 2
    if receipt.status is DependencyActivationStatus.BLOCKED:
        print(receipt.terminal, file=sys.stderr)
        return 2
    require_dependency_activation(receipt)
    if mode in {"check", "historical"}:
        return _verify_activated_blocker(lane=mode)
    print(EXECUTION_BLOCKER, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
