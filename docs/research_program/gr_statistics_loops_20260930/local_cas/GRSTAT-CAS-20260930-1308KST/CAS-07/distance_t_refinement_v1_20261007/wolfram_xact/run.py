#!/usr/bin/env python3
"""Run the frozen M06 Wolfram+xAct axis and preserve each raw attempt."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[8]
AXIS = pathlib.Path(__file__).resolve().parent
UNIT = AXIS.parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "e4169b089e5c19accb838e3b43daa0fe44bfab43b0a5025a3167280069a6eb13",
    INPUTS: "9c85a30bdde1a294930ae40009b121e0e1a767a5c2d5e97fa9e27a3dc14b5bd3",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
CHECKS = (
    "CAS-07-M06-T-DOMAIN",
    "CAS-07-M06-ETA-ORDER",
    "CAS-07-M06-REFINED-FD1",
    "CAS-07-M06-NO-WORSE-THAN-FD2",
)


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for path, expected in EXPECTED.items():
        actual = digest(path)
        if actual != expected:
            raise SystemExit(f"frozen input mismatch: {path}: {actual} != {expected}")

    executable = shutil.which("wolframscript")
    kernel = shutil.which("WolframKernel")
    if not executable or not kernel:
        raise SystemExit("Wolfram executables unavailable")
    attempt_root = AXIS / "attempts"
    attempt_root.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt = attempt_root / stamp
    attempt.mkdir()
    command = [executable, "-file", str(AXIS / "proof.wls")]
    start = datetime.now(timezone.utc)
    try:
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=1800, check=False
        )
        returncode = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = None
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timed_out = True
    finish = datetime.now(timezone.utc)
    (attempt / "stdout.log").write_text(stdout)
    (attempt / "stderr.log").write_text(stderr)

    found = dict(re.findall(r"^CHECK\t([^\t\n]+)\t(True|False)$", stdout, re.MULTILINE))
    detail = dict(re.findall(r"^DETAIL\t([^\t\n]+)\t(True|False)$", stdout, re.MULTILINE))
    tensor = re.search(r"^TENSOR_SANITY\t(True|False)$", stdout, re.MULTILINE)
    checks = {key: found.get(key) == "True" for key in CHECKS}
    passed = returncode == 0 and not timed_out and all(checks.values()) and tensor is not None and tensor.group(1) == "True"
    version = re.search(r"^VERSION\tWolfram\t([^\n]+)$", stdout, re.MULTILINE)
    xtensor = re.search(r"Package xAct`xTensor` version ([^,\n]+)", stdout)
    result = {
        "schema_version": 1,
        "axis": "wolfram_xact",
        "contract_id": "GRSTAT-20260930-CAS-07-M06-DISTANCE-T-REFINEMENT-V1",
        "contract_sha256": EXPECTED[CONTRACT],
        "input_sha256": EXPECTED[INPUTS],
        "common_spec_sha256": EXPECTED[COMMON],
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "execution": {
            "mode": "owner_authorized_direct_local",
            "launch_id": None,
            "global_authority": "UNAVAILABLE",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
            "argv": command,
            "cwd": str(ROOT),
            "started_utc": start.isoformat(),
            "finished_utc": finish.isoformat(),
            "returncode": returncode,
            "timed_out": timed_out,
            "attempt": str(attempt.relative_to(ROOT)),
            "wolfram_version": version.group(1).strip() if version else None,
            "xtensor_version": xtensor.group(1).strip() if xtensor else None,
            "wolframscript_path": executable,
            "wolframscript_sha256": digest(pathlib.Path(executable)),
            "kernel_path": kernel,
            "kernel_resolved_path": str(pathlib.Path(kernel).resolve()),
            "kernel_sha256": digest(pathlib.Path(kernel).resolve()),
            "proof_source_sha256": digest(AXIS / "proof.wls"),
            "runner_source_sha256": digest(AXIS / "run.py"),
            "stdout_sha256": digest(attempt / "stdout.log"),
            "stderr_sha256": digest(attempt / "stderr.log"),
            "detail_checks": detail,
            "tensor_sanity": tensor.group(1) == "True" if tensor else False,
        },
        "claim_ceiling": "distance-only analytic component; no endpoint identification or scientific admission",
        "scientific_admission": "HOLD",
    }
    (attempt / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (AXIS / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "result_path": str((AXIS / "result.json").relative_to(ROOT)),
    }))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
