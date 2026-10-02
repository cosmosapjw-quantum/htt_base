#!/usr/bin/env python3
"""Execute the independent Wolfram/xAct CAS-01 component and emit one JSON payload."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "axis.wl"
ENGINE_RESULT = HERE / "engine_result.json"
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/EXECUTION_CONTRACT.json"
COMMON_SPEC = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
ENVIRONMENT = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS_ENVIRONMENT.json"
CONTRACT_SHA = "edc2df3348528a699b987ae1893ab76630e96b9915d11117db7916d005c406f1"
SPEC_SHA = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"
ENV_SHA = "6d2253dbababe14cfb84a246b3093b738a961dd7c175b36a5f9f1fc29f086297"
HEAD = "0db3cad2ae6e7da42c80f0fd2d4a3c9af9a82234"
KEYS = ("CAS-01-C01", "CAS-01-C02", "CAS-01-C03", "CAS-01-C04")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError("Run from the exact primary repository root")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    git_dir = subprocess.check_output(
        ["git", "rev-parse", "--absolute-git-dir"], cwd=ROOT, text=True
    ).strip()
    if head != HEAD or git_dir != str(ROOT / ".git"):
        raise RuntimeError(f"Frozen repository identity mismatch: {head}, {git_dir}")
    actual_hashes = {"contract": sha(CONTRACT), "common_spec": sha(COMMON_SPEC),
                     "environment": sha(ENVIRONMENT), "source": sha(SOURCE)}
    if (actual_hashes["contract"], actual_hashes["common_spec"],
        actual_hashes["environment"]) != (CONTRACT_SHA, SPEC_SHA, ENV_SHA):
        raise RuntimeError(f"Frozen inputs changed: {actual_hashes}")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if tuple(contract["target"]["exact_test_obligations"]) != KEYS:
        raise RuntimeError("Contract component list changed")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    argv = ["/usr/bin/wolframscript", "-file", str(SOURCE.relative_to(ROOT))]
    ENGINE_RESULT.unlink(missing_ok=True)
    started = utc()
    try:
        process = subprocess.run(
            argv, cwd=ROOT, capture_output=True, timeout=1800, check=False
        )
        exit_code = process.returncode
        stdout, stderr = process.stdout, process.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        timed_out = True
    completed = utc()
    stdout_path = HERE / f"engine.{timestamp}.stdout.log"
    stderr_path = HERE / f"engine.{timestamp}.stderr.log"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)

    engine = None
    engine_error = None
    try:
        if exit_code != 0 or timed_out:
            raise RuntimeError(f"Wolfram exited {exit_code}, timed_out={timed_out}")
        engine = json.loads(ENGINE_RESULT.read_text(encoding="utf-8"))
        checks = engine["checks"]
        if set(checks) != set(KEYS) or any(type(v) is not bool for v in checks.values()):
            raise RuntimeError("Engine returned incorrect check schema")
        expected_version = contract["axes"]["wolfram_xact"]["pinned_toolchain"][
            "observed_toolchain"]["stdout"].splitlines()[0]
        if engine["wolfram_version"] != expected_version:
            raise RuntimeError(f"Wolfram version drift: {engine['wolfram_version']}")
        if engine["xTensor_version"] != ["1.3.0", [2025, 12, 29]]:
            raise RuntimeError(f"xTensor version drift: {engine['xTensor_version']}")
        if b"::" in stdout or b"::" in stderr:
            raise RuntimeError("Wolfram emitted a diagnostic message")
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        engine_error = str(exc)

    evidence = {
        "axis": "wolfram_xact",
        "contract_sha256": CONTRACT_SHA,
        "status": "INCONCLUSIVE" if engine_error else (
            "PASS" if all(engine["checks"].values()) else "FAIL"
        ),
        "evidence_class": "exact",
        "completed_at": completed,
        "started_at": started,
        "repo_root": str(ROOT),
        "git_head": head,
        "git_dir": git_dir,
        "input_sha256": actual_hashes,
        "commands": [{"argv": argv, "cwd": str(ROOT), "exit_code": exit_code,
                      "timed_out": timed_out, "stdout_path": str(stdout_path),
                      "stderr_path": str(stderr_path),
                      "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path)}],
        "solver_executed": True,
        "engine_result_path": str(ENGINE_RESULT),
        "engine_result_sha256": sha(ENGINE_RESULT) if ENGINE_RESULT.exists() else None,
        "checks": engine["checks"] if engine else None,
        "details": engine.get("details") if engine else None,
        "engine_version": engine.get("wolfram_version") if engine else None,
        "xTensor_version": engine.get("xTensor_version") if engine else None,
        "execution_error": engine_error,
        "analytical_obligations": {
            "Jacobi_vertex_Taylor_and_screen_invariance": "OPEN",
            "smooth_timelike_neighborhood_local_flow_and_source_extension": "OPEN",
        },
        "claim_ceiling": "specified_mathematical_component_only_no_scientific_admission",
    }
    write_json(HERE / "AXIS_RESULT.json", evidence)
    if engine_error:
        print(json.dumps({"error": engine_error}, separators=(",", ":")))
        return 2
    payload = {"checks": engine["checks"], "domain_assumption_diff": [],
               "counterexample": None}
    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, separators=(",", ":")))
        raise SystemExit(2)
