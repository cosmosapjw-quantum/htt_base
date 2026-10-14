#!/usr/bin/env python3
"""Run and retain the independent CAS-11-C01 Wolfram+xTensor axis."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "bregman_three_point.wl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    attempt = 1
    while (HERE / f"attempt_{attempt:02d}.execution.json").exists():
        attempt += 1
    prefix = f"attempt_{attempt:02d}"
    argv = ["wolframscript", "-file", str(SOURCE)]
    started = utc()
    try:
        proc = subprocess.run(argv, cwd=REPO, capture_output=True, timeout=1800, check=False)
        stdout, stderr, exit_code, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, exit_code, timed_out = exc.stdout or b"", exc.stderr or b"", None, True
    completed = utc()
    (HERE / f"{prefix}.stdout.log").write_bytes(stdout)
    (HERE / f"{prefix}.stderr.log").write_bytes(stderr)
    output = stdout.decode("utf-8", "replace")
    required_true = [
        "H_CONSTANT_ZERO",
        "COORDINATE_KERNEL_ZERO",
        "VECTOR_EMPTY_BASE_ZERO",
        "VECTOR_INDUCTION_STEP_ZERO",
        "INNER_EMPTY_BASE_ZERO",
        "INNER_K_INDUCTION_STEP_ZERO",
        "OUTER_EMPTY_BASE_ZERO",
        "OUTER_N_INDUCTION_STEP_ZERO",
        "FUBINI_EMPTY_N_ZERO",
        "FUBINI_EMPTY_K_ZERO",
        "FUBINI_DOUBLE_INDUCTION_STEP_ZERO",
        "MOMENT_ZERO_EMPTY_BASE",
        "MOMENT_ZERO_K_STEP",
    ]
    checks = {key: f"{key}=True" in output for key in required_true}
    checks.update({
        "orientation_control": "ORIENTATION_FG=4/3" in output and "ORIENTATION_GF=5/3" in output,
        "approximate_nonzero_control": "APPROXIMATE_RESIDUAL=1/10" in output,
        "xTensor_1_3_0": "XTENSOR_VERSION={1.3.0, {2025, 12, 29}}" in output,
        "Wolfram_15_0_0": "ENGINE_VERSION=15.0.0" in output,
        "engine_pass": "CERTIFICATE_STATUS=PASS" in output,
    })
    binary = Path("/usr/bin/wolframscript")
    execution = {
        "argv": argv,
        "cwd": str(REPO),
        "started_at": started,
        "completed_at": completed,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout_path": str(HERE / f"{prefix}.stdout.log"),
        "stderr_path": str(HERE / f"{prefix}.stderr.log"),
        "stdout_sha256": sha256(HERE / f"{prefix}.stdout.log"),
        "stderr_sha256": sha256(HERE / f"{prefix}.stderr.log"),
        "checks": checks,
        "versions": {
            "wolfram": re.search(r"ENGINE_VERSION=([^\n]+)", output).group(1) if "ENGINE_VERSION=" in output else None,
            "xTensor": re.search(r"XTENSOR_VERSION=([^\n]+)", output).group(1) if "XTENSOR_VERSION=" in output else None,
        },
        "artifacts": {
            "source": {"path": str(SOURCE), "sha256": sha256(SOURCE)},
            "runner": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
            "wolframscript": {"path": str(binary.resolve()), "sha256": sha256(binary.resolve())},
        },
        "bindings": {
            "contract_sha256": sha256(CONTRACT),
            "admitted_inputs_sha256": sha256(INPUTS),
            "common_spec_sha256": sha256(COMMON),
        },
    }
    (HERE / f"{prefix}.execution.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    success = exit_code == 0 and all(checks.values())
    if success:
        contract = json.loads(CONTRACT.read_text())
        obligations = contract["axes"]["wolfram_xact"]["obligation"]
        result = {
            "axis": "wolfram_xact",
            "component": "CAS-11-C01",
            "status": "PASS",
            "evidence_class": "exact",
            "checks": {item: True for item in obligations},
            "detail_checks": checks,
            "counterexample": None,
            "domain_assumption_diff": [],
            "statement_alignment": {
                "definition": "D_H(x||y)=H(x)-H(y)-<grad H(y),x-y>",
                "identity": "D_H(f||g)-D_H(f||h)-D_H(h||g)=<grad H(h)-grad H(g),f-h>",
                "cancellation": "grad H(h)-grad H(g)=V lambda and V^T(f-h)=0 imply exact zero",
                "dimensions": "arbitrary finite n,k including zero",
                "branches": "none",
                "proof_method": "executed exact generic coordinate polynomial identities plus n,k and rectangular double-induction finite-sum reduction",
            },
            "scope": "finite Bregman three-point algebra and exact moment cancellation only",
            "scientific_admission": "HOLD",
            "remaining": ["integrability", "continuum entropy bounds", "science"],
            "contract_sha256": sha256(CONTRACT),
            "admitted_inputs_sha256": sha256(INPUTS),
            "common_spec_sha256": sha256(COMMON),
            "execution_path": str(HERE / f"{prefix}.execution.json"),
            "first_failure_execution_path": str(HERE / "attempt_01.execution.json"),
            "completed_at": completed,
        }
        (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        commands = [
            {
                "argv": record["argv"],
                "cwd": record["cwd"],
                "started_at": record["started_at"],
                "completed_at": record["completed_at"],
                "exit_code": record["exit_code"],
                "timed_out": record["timed_out"],
                "stdout_path": record["stdout_path"],
                "stderr_path": record["stderr_path"],
                "stdout_sha256": record["stdout_sha256"],
                "stderr_sha256": record["stderr_sha256"],
            }
            for path in sorted(HERE.glob("attempt_*.execution.json"))
            for record in [json.loads(path.read_text())]
        ]
        axis_result = {
            **result,
            "commands": commands,
            "engine_versions": execution["versions"],
            "executable_artifacts": execution["artifacts"],
            "launch_id": None,
            "registration_authority": "UNAVAILABLE_ABSENT",
            "observed_runtime": {"model": "UNKNOWN", "effort": "UNKNOWN"},
            "independence_mode": "blind-results-and-derivations",
            "correlation_disclosure": "Native worker model and effort unavailable from observed turn metadata; no independence beyond blinded axis work is inferred.",
            "result_path": str(HERE / "result.json"),
            "result_sha256": sha256(HERE / "result.json"),
        }
        (HERE / "axis_result.json").write_text(json.dumps(axis_result, indent=2, sort_keys=True) + "\n")
    gate_payload = {
        "checks": {"CAS-11-C01": success},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    print(json.dumps(gate_payload, sort_keys=True))
    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())
