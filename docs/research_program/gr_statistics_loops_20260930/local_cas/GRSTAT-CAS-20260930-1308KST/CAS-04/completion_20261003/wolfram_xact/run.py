#!/usr/bin/env python3
"""CAS-04 Wolfram/xAct runner; stdout is exactly one typed JSON document."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
CONTRACT = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-04/EXECUTION_CONTRACT.json"
SPEC = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "058da4a8716fd06bc67100b8490df88a6783b780ac0ff66bf1221a02ab7e8741",
    SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
OBLIGATIONS = [f"CAS-04-C0{i}" for i in range(1, 5)]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    checks = {key: False for key in OBLIGATIONS}
    payload: dict = {"checks": checks, "domain_assumption_diff": [], "counterexample": None}
    actual_hashes = {str(path): sha256(path) for path in [*EXPECTED, HERE / "axis.wl", Path(__file__)]}
    mismatches = [str(path) for path, expected in EXPECTED.items() if actual_hashes[str(path)] != expected]
    if mismatches:
        payload["domain_assumption_diff"] = [f"Frozen source hash changed: {path}" for path in mismatches]
        print(json.dumps(payload, sort_keys=True))
        return 2

    argv = ["wolframscript", "-file", str(HERE / "axis.wl")]
    started = now()
    timed_out = False
    try:
        result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=1800, check=False)
        stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        exit_code = None
    completed = now()
    runs = HERE / "raw_runs"
    runs.mkdir(exist_ok=True)
    index = len(list(runs.glob("run-*.json"))) + 1
    stem = f"run-{index:03d}"
    (runs / f"{stem}.stdout.log").write_text(stdout)
    (runs / f"{stem}.stderr.log").write_text(stderr)
    marker = "CAS04_RESULT_JSON="
    matches = [line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
    engine_result = None
    if len(matches) == 1:
        try:
            engine_result = json.loads(matches[0])
        except json.JSONDecodeError:
            pass
    if isinstance(engine_result, dict) and isinstance(engine_result.get("checks"), dict):
        raw_checks = engine_result["checks"]
        if set(raw_checks) == set(OBLIGATIONS) and all(type(v) is bool for v in raw_checks.values()):
            payload["checks"] = raw_checks
    payload["engine_result_parsed"] = engine_result is not None
    payload["engine_exit_code"] = exit_code
    payload["engine_timed_out"] = timed_out
    payload["run_record"] = str((runs / f"{stem}.json").relative_to(REPO))
    record = {
        "axis": "wolfram_xact", "actual_argv": argv, "actual_cwd": str(REPO),
        "started_at": started, "completed_at": completed, "exit_code": exit_code,
        "timed_out": timed_out, "source_sha256": actual_hashes,
        "stdout_path": str((runs / f"{stem}.stdout.log").relative_to(REPO)),
        "stderr_path": str((runs / f"{stem}.stderr.log").relative_to(REPO)),
        "engine_result": engine_result,
    }
    (runs / f"{stem}.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    status = "PASS" if exit_code == 0 and not timed_out and all(payload["checks"].values()) else "INCONCLUSIVE"
    envelope = {
        "axis": "wolfram_xact", "status": status, "contract_sha256": actual_hashes[str(CONTRACT)],
        "evidence_class": "exact", "completed_at": completed,
        "commands": [{"argv": argv, "cwd": str(REPO), "exit_code": exit_code,
                      "stdout_path": record["stdout_path"], "stderr_path": record["stderr_path"]}],
        "checks": payload["checks"], "domain_assumption_diff": payload["domain_assumption_diff"],
        "counterexample": None, "source_sha256": actual_hashes,
        "claim_ceiling": "specified_mathematical_component_only_no_scientific_admission",
        "remaining_analytic_obligations": ["smooth eigenfield existence/IFT and spectral norm", "EF6 local existence and CAS05/06"],
    }
    (HERE / "AXIS_RESULT.json").write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
