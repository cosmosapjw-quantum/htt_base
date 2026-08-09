#!/usr/bin/env python3
"""Execute and replay the frozen PR-288 synthetic Bayesian semantics contract."""

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
SPEC = ROOT / "docs/research_program/post_pr275/pr288_spec.yaml"
OUTPUT = ROOT / "docs/generated/pr288_bayesian_semantics_receipt.json"
SCRUBBED_ENVIRONMENT_KEYS = (
    "PYTHONHOME",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTHONSTARTUP",
    "PR288_ENGINE_OVERRIDE",
    "PR288_RECEIPT_OVERRIDE",
)


def _activate_sources(root: Path = ROOT) -> None:
    for path in reversed((root / "htt", root / "htt/src")):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _build(root: Path = ROOT):
    _activate_sources(root)
    from htt.infer.bayesian_semantics import (
        build_bayesian_semantics_receipt,
        validate_bayesian_semantics_receipt,
    )

    spec = root / SPEC.relative_to(ROOT)
    receipt = build_bayesian_semantics_receipt(
        spec,
        repository_root=root,
        generation_identity="EXTERNAL_CANDIDATE_SEAL_OR_SOURCE_HASHES",
    )
    return validate_bayesian_semantics_receipt(
        receipt,
        spec_path=spec,
        repository_root=root,
    )


def _encoded(receipt) -> bytes:
    return (
        json.dumps(
            receipt.payload(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _exit_for_terminal(terminal: str) -> int:
    if terminal == "PASS_BAYESIAN_SEMANTICS_REPAIR":
        return 0
    if terminal == "BLOCKED_DEPENDENCY_OR_ENGINE":
        return 2
    return 1


def _validate_output_destination_for_write() -> None:
    try:
        relative = OUTPUT.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError("receipt destination escaped repository root") from exc
    cursor = ROOT
    for part in relative.parent.parts:
        cursor /= part
        if cursor.is_symlink() or not cursor.is_dir():
            raise RuntimeError(
                f"receipt parent must be an existing regular directory: {cursor}"
            )
    if OUTPUT.is_symlink():
        raise RuntimeError("receipt destination must not be a symlink")
    if OUTPUT.exists():
        if not OUTPUT.is_file() or OUTPUT.stat().st_nlink != 1:
            raise RuntimeError(
                "receipt destination must be a single-link regular file"
            )


def _atomic_write_receipt(payload: bytes) -> None:
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
        _validate_output_destination_for_write()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    receipt = _build()
    code = _exit_for_terminal(receipt.terminal)
    if code != 0:
        print(
            json.dumps(
                {
                    "terminal": receipt.terminal,
                    "reasons": list(receipt.reasons),
                    "receipt_written": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return code
    _atomic_write_receipt(_encoded(receipt))
    print(
        json.dumps(
            {
                "terminal": receipt.terminal,
                "receipt_content_id": receipt.receipt_content_id,
                "output": str(OUTPUT.relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


def _check(root: Path = ROOT) -> int:
    output = root / OUTPUT.relative_to(ROOT)
    if output.is_symlink() or not output.is_file():
        print("frozen PR-288 receipt is missing or nonregular", file=sys.stderr)
        return 1
    receipt = _build(root)
    code = _exit_for_terminal(receipt.terminal)
    if code != 0:
        print(
            json.dumps(
                {"terminal": receipt.terminal, "reasons": list(receipt.reasons)},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return code
    expected = _encoded(receipt)
    observed = output.read_bytes()
    if observed != expected:
        print("frozen PR-288 receipt differs from recomputation", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "terminal": receipt.terminal,
                "receipt_content_id": receipt.receipt_content_id,
                "exact_replay": True,
            },
            sort_keys=True,
        )
    )
    return 0


def _engines() -> int:
    receipt = _build()
    print(
        json.dumps(
            {
                "terminal": receipt.terminal,
                "reasons": list(receipt.reasons),
                "engine_results": [
                    {
                        "engine_id": row.engine_id,
                        "fixture_id": row.fixture_id,
                        "status": row.status.value,
                        "log_evidence": row.log_evidence,
                        "declared_standard_uncertainty": (
                            row.declared_standard_uncertainty
                        ),
                        "engine_version": row.engine_version,
                    }
                    for row in receipt.engine_results
                ],
                "crosschecks": [
                    row.payload() for row in receipt.evidence_crosschecks
                ],
                "null_control": receipt.null_control.unsigned_payload(),
                "negative_control": receipt.negative_control.unsigned_payload(),
                "mutations_killed": sum(
                    row.killed for row in receipt.mutation_results
                ),
            },
            sort_keys=True,
        )
    )
    return _exit_for_terminal(receipt.terminal)


def _pytest(paths: tuple[str, ...]) -> int:
    env = dict(os.environ)
    for key in SCRUBBED_ENVIRONMENT_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "htt"), str(ROOT / "htt/src"))
    )
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=",
            "-q",
            *paths,
        ],
        cwd=ROOT / "htt",
        env=env,
        check=False,
    ).returncode


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
        item.decode("utf-8") for item in completed.stdout.split(b"\0") if item
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
    for distribution in ("numpy", "scipy", "dynesty", "PyYAML", "pytest"):
        try:
            values[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            values[distribution] = "UNAVAILABLE"
    return values


def _portable() -> int:
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
    tracked = _tracked_paths()
    source_before = _manifest(ROOT, tracked)
    archived = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if archived.returncode != 0:
        print("git archive failed", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="pr288-portable-") as directory:
        clean_root = Path(directory) / "source"
        clean_root.mkdir()
        with tarfile.open(fileobj=BytesIO(archived.stdout), mode="r:") as archive:
            archive.extractall(clean_root, filter="data")
        clean_before = _manifest(clean_root, tracked)
        if clean_before != source_before:
            print("clean archive manifest differs from source", file=sys.stderr)
            return 1
        env = dict(os.environ)
        for key in (*SCRUBBED_ENVIRONMENT_KEYS, "PYTHONPATH"):
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join(
            (str(clean_root / "htt"), str(clean_root / "htt/src"))
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr288_bayesian_semantics.py",
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
        elapsed = time.perf_counter() - started
        clean_after = _manifest(clean_root, tracked)
        source_after = _manifest(ROOT, tracked)
        if clean_after != clean_before or source_after != source_before:
            print("portable replay changed tracked bytes", file=sys.stderr)
            return 1
        evidence = {
            "schema": "PR288_PORTABLE_CLEAN_REPLAY_EVIDENCE_V1",
            "tracked_source_manifest": source_before,
            "interpreter_and_dependency_versions": _versions(),
            "scrubbed_environment_keys": {
                key: key not in env for key in SCRUBBED_ENVIRONMENT_KEYS
            }
            | {"PYTHONPATH": "CLEAN_ROOT_ONLY"},
            "exact_command": command,
            "exact_command_exit_code": completed.returncode,
            "exact_command_runtime_seconds": elapsed,
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
        }
        print(json.dumps(evidence, sort_keys=True))
        return completed.returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    modes = {"build", "focused", "engines", "adjacent", "check", "portable"}
    if len(args) != 1 or args[0] not in modes:
        print(
            "usage: run_pr288_bayesian_semantics.py "
            "{build|focused|engines|adjacent|check|portable}",
            file=sys.stderr,
        )
        return 2
    mode = args[0]
    if mode == "build":
        return _write()
    if mode == "focused":
        return _pytest(("../tests/htt/test_bayesian_semantics_repair.py",))
    if mode == "engines":
        return _engines()
    if mode == "adjacent":
        return _pytest(
            (
                "../tests/htt/test_inference_adequacy_gates.py",
                "src/common/test_bulkflow_likelihood.py",
                "../tests/contracts/test_optional_dependencies.py",
            )
        )
    if mode == "check":
        return _check()
    return _portable()


if __name__ == "__main__":
    raise SystemExit(main())
