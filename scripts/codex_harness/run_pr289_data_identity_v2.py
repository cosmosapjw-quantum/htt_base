#!/usr/bin/env python3
"""Portable PR-289 identity-preflight runner with no acquisition side effects."""

from __future__ import annotations

from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT
    / "docs/research_program/post_pr275/data_registry_v2/"
    "LANE_REGISTRY_V2.json"
)
SPEC = ROOT / "docs/research_program/post_pr275/pr289_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr289_publication_policy.json"
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
    PR274_REGISTRY,
    PR274_RESULT,
    MODULE,
    TEST,
    RUNNER,
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
    return {
        "source_commit_or_external_candidate_seal_id": hashlib.sha256(
            json.dumps(
                source_bindings,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest(),
        "worktree_state": "source_hash_bound_dirty_or_committed",
        "exact_replay_environment": "repository_python_contract",
    }


def _build(root: Path = ROOT) -> dict[str, object]:
    _activate(root)
    from common.data_identity import build_data_identity_v2_receipt
    from common.data_identity import load_lane_registry

    source_bindings = _source_bindings(root)
    receipt = build_data_identity_v2_receipt(
        registry=load_lane_registry(
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


def _write() -> int:
    payload = _build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.is_symlink():
        raise RuntimeError("receipt output must not be a symlink")
    if OUTPUT.exists() and OUTPUT.stat().st_nlink != 1:
        raise RuntimeError("receipt output must not be a hardlink")
    temporary = OUTPUT.with_suffix(".json.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError("receipt temporary path already exists")
    temporary.write_bytes(_encoded(payload))
    os.replace(temporary, OUTPUT)
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
    if output.is_symlink() or not output.is_file():
        raise RuntimeError("frozen PR-289 receipt is missing or nonregular")
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


def _tracked_manifest(root: Path) -> tuple[str, int]:
    paths = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root
    ).split(b"\0")
    digest = hashlib.sha256()
    count = 0
    for raw in paths:
        if not raw:
            continue
        relative = raw.decode("utf-8")
        data = (root / relative).read_bytes()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(data).digest())
        count += 1
    return digest.hexdigest(), count


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
    source_manifest, source_count = _tracked_manifest(ROOT)
    archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix="pr289-portable-") as temporary:
        clean = Path(temporary) / "repo"
        clean.mkdir()
        with tarfile.open(fileobj=BytesIO(archive), mode="r:") as handle:
            handle.extractall(clean, filter="data")
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
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py",
                "check",
            ],
            cwd=clean,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "clean portable replay failed: "
                + (completed.stderr or completed.stdout)
            )
        clean_paths = sorted(
            path
            for path in clean.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
        clean_digest = hashlib.sha256()
        for path in clean_paths:
            relative = path.relative_to(clean).as_posix()
            clean_digest.update(relative.encode("utf-8") + b"\0")
            clean_digest.update(hashlib.sha256(path.read_bytes()).digest())
        print(
            json.dumps(
                {
                    "schema": "PR289_PORTABLE_CLEAN_EVIDENCE_V1",
                    "nested_exit_code": completed.returncode,
                    "nested_stdout_sha256": hashlib.sha256(
                        completed.stdout.encode("utf-8")
                    ).hexdigest(),
                    "source_tracked_manifest_sha256": source_manifest,
                    "source_tracked_file_count": source_count,
                    "clean_extracted_file_count": len(clean_paths),
                    "clean_extracted_content_sha256": clean_digest.hexdigest(),
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
        return _pytest(("tests/contracts/test_vector_tensor_data_admission.py",))
    if args.mode == "check":
        return _check()
    return _portable()


if __name__ == "__main__":
    raise SystemExit(main())
