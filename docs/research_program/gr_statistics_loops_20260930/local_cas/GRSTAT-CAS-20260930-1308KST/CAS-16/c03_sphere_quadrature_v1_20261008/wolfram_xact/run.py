#!/usr/bin/env python3
"""Run the frozen CAS-16-C03 Wolfram/xAct axis with preserved raw evidence."""

import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone


AXIS = Path(__file__).resolve().parent
COMPONENT = AXIS.parent
REPO = next(p for p in AXIS.parents if (p / ".git").exists())
CONTRACT = COMPONENT / "EXECUTION_CONTRACT.json"
INPUTS = COMPONENT / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = AXIS / "sphere_quadrature.wl"
EXPECTED = {
    CONTRACT: "d36ffedcbeb64c201671e78e42be41ea9b6d160d148d7aadf51134a9dfbe068c",
    INPUTS: "6c536bf89687f6f4f8aaeec90154e1c9cf20b994870e789faa3cff5d5735ac82",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(raw: str, name: str) -> str | None:
    matches = re.findall(rf"^{re.escape(name)}=(.*)$", raw, re.MULTILINE)
    return matches[-1].strip() if len(matches) == 1 else None


def main() -> int:
    bad_inputs = [str(p) for p, digest in EXPECTED.items() if sha256(p) != digest]
    if bad_inputs:
        raise RuntimeError(f"Frozen input hash mismatch: {bad_inputs}")
    attempts = sorted(AXIS.glob("run_[0-9][0-9][0-9].execution.json"))
    number = max((int(p.name[4:7]) for p in attempts), default=0) + 1
    prefix = f"run_{number:03d}"
    argv = ["/usr/local/bin/WolframKernel", "-script", str(SOURCE)]
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(argv, cwd=AXIS, capture_output=True, timeout=1800, check=False)
        stdout, stderr, exit_code, timed_out = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, exit_code, timed_out = exc.stdout or b"", exc.stderr or b"", 124, True
    out_path = AXIS / f"{prefix}.stdout.log"
    err_path = AXIS / f"{prefix}.stderr.log"
    out_path.write_bytes(stdout)
    err_path.write_bytes(stderr)
    output = stdout.decode("utf-8", errors="replace")
    marker_count = field(output, "MONOMIAL_COUNT")
    angle_count = field(output, "ANGLE_PAIR_COUNT")
    failure_count = field(output, "FAILURE_COUNT")
    gl4 = field(output, "GL4_MU8_DIFFERENCE")
    n8 = field(output, "NPHI8_COS8_DIFFERENCE")
    xact_loaded = field(output, "XACT_MANIFOLD_DEFINED")
    pass_check = (
        exit_code == 0 and not timed_out and marker_count == "165" and angle_count == "45"
        and failure_count == "0" and gl4 == "-128/11025"
        and n8 == "1/128" and xact_loaded == "True"
    )
    raw_failures = re.findall(r"^FAILURE=(.*)$", output, re.MULTILINE)
    counterexample = raw_failures[0] if raw_failures else None
    execution = {
        "attempt": prefix,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(AXIS),
        "argv": argv,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": {"path": out_path.name, "sha256": sha256(out_path), "size": out_path.stat().st_size},
        "stderr": {"path": err_path.name, "sha256": sha256(err_path), "size": err_path.stat().st_size},
        "wolfram_version": field(output, "WOLFRAM_VERSION"),
        "xact_xTensor_version": field(output, "XACT_XTENSOR_VERSION"),
        "xact_version_symbols": field(output, "XACT_VERSION_SYMBOLS"),
        "xact_manifold_defined": xact_loaded,
    }
    execution_path = AXIS / f"{prefix}.execution.json"
    execution_path.write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    gate = {
        "axis": "wolfram_xact",
        "contract_id": "GRSTAT-20260930-CAS-16-C03-SPHERE-QUADRATURE-V1",
        "contract_sha256": sha256(CONTRACT),
        "admitted_inputs_sha256": sha256(INPUTS),
        "common_spec_sha256": sha256(COMMON),
        "status": "PASS" if pass_check else "FAIL",
        "checks": {"CAS-16-C03": pass_check},
        "domain_assumption_diff": [],
        "counterexample": counterexample,
        "evidence_class": "exact" if pass_check else "incomplete",
        "commands": [{
            "cmd": shlex.join(argv),
            "cwd": str(AXIS),
            "exit": exit_code,
            "stdout": out_path.name,
            "stderr": err_path.name,
        }],
        "completed_at": execution["finished_utc"],
        "statement_alignment": "Exact 165 normalized scalar monomials on fixed GL5 x Nphi9 grid; GL4 mu^8 and Nphi8 cos^8 witnesses",
        "claim_ceiling": "CAS-16-C03 finite scalar monomial product quadrature only",
        "source": {"path": SOURCE.name, "sha256": sha256(SOURCE)},
        "runner": {"path": Path(__file__).name, "sha256": sha256(Path(__file__))},
        "execution": {"path": execution_path.name, "sha256": sha256(execution_path)},
        "tool_versions": {
            "wolfram": execution["wolfram_version"],
            "xact_xTensor": execution["xact_xTensor_version"],
            "python": sys.version.split()[0],
        },
        "launch_id": None,
        "global_harness_used": False,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "lifecycle": "BLOCKED_NO_GLOBAL_REGISTERED_LAUNCH",
        "scientific_admission": "HOLD",
    }
    (AXIS / "axis_result.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    print(json.dumps(gate, sort_keys=True))
    return 0 if pass_check else 1


if __name__ == "__main__":
    raise SystemExit(main())
