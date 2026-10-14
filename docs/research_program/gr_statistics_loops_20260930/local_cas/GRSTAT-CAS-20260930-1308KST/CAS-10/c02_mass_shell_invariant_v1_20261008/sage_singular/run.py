#!/usr/bin/env python3
"""Repository runner binding for the independent CAS-10-C02 Sage/Singular axis."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AXIS_DIR = Path(__file__).resolve().parent
UNIT_DIR = AXIS_DIR.parent
COMMON_SPEC = AXIS_DIR.parents[4] / "cas" / "COMMON_SPEC.md"
RESULT_PATH = AXIS_DIR / "result.json"

SAGE = "/usr/local/bin/sage"
SINGULAR = "/home/cosmosapjw/opt/sage/local/bin/Singular"
SINGULAR_BINARY_SHA256 = "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c"

FROZEN_HASHES = {
    UNIT_DIR / "EXECUTION_CONTRACT.json": "c6957c9d87d416668d2f33ee94946aa04f3bf0da09aa06cac7cdb07b0eaab2ef",
    UNIT_DIR / "ADMITTED_INPUTS.json": "6f699739b3835b3bbaa02202bcabf7381a0d57860e2eb28f8441c8d392fda074",
    COMMON_SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    AXIS_DIR / "prove_c02.sage": "119cc2aa53e673ab00af39b30824e3a30f4dfafd12c0fca88b87555f01342ae7",
    AXIS_DIR / "prove_c02.sing": "94d4af51d51f538083a844e4ef1a90b4f569aeaa54fec6f2e828f1bf3bfe2079",
    Path(SINGULAR): SINGULAR_BINARY_SHA256,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def run_and_record(argv: list[str], stem: str) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        cwd=AXIS_DIR,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout_path = AXIS_DIR / f"{stem}.stdout.log"
    stderr_path = AXIS_DIR / f"{stem}.stderr.log"
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    return {
        "argv": argv,
        "cwd": str(AXIS_DIR),
        "exit_code": completed.returncode,
        "stdout": file_record(stdout_path),
        "stderr": file_record(stderr_path),
        "stdout_text": completed.stdout.decode("utf-8", errors="replace"),
        "stderr_text": completed.stderr.decode("utf-8", errors="replace"),
    }


def public_execution(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in {"stdout_text", "stderr_text"}}


def contains_all(text: str, fragments: list[str]) -> tuple[bool, dict[str, bool]]:
    observed = {fragment: fragment in text for fragment in fragments}
    return all(observed.values()), observed


def relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(AXIS_DIR))
    except ValueError:
        return str(path)


def main() -> int:
    frozen = []
    for path, expected in FROZEN_HASHES.items():
        actual = sha256(path) if path.is_file() else None
        frozen.append({
            "path": relative_label(path),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "matches": actual == expected,
        })
    frozen_ok = all(item["matches"] for item in frozen)

    sage_version = run_and_record([SAGE, "--version"], "runner.sage.version")
    singular_version = run_and_record([SINGULAR, "--version"], "runner.singular.version")
    sage_proof = run_and_record([SAGE, "prove_c02.sage"], "runner.sage")
    singular_proof = run_and_record([SINGULAR, "-q", "prove_c02.sing"], "runner.singular")

    sage_fragments = [
        "sage_version=SageMath version 10.9",
        "orth_minus_h_mass_shell=0",
        "orth_remainder=0",
        "b_norm_minus_Jgeo_minus_h2_mass_shell=0",
        "Jgeo_minus_b_norm_remainder=0",
        "A_norm_minus_4c2_b_norm=0",
        "u0sq_b_norm_minus_sos_remainder=0",
        "rest_exact_residuals={'mass_shell': 0, 'orthogonality': 0, 'Jgeo_minus_b_norm': 0, 'A_norm_minus_4c2J': 0}",
        "boosted_rational_exact_residuals={'mass_shell': 0, 'orthogonality': 0, 'Jgeo_minus_b_norm': 0, 'A_norm_minus_4c2J': 0}",
        "c_zero_control_b=(0, 1, 0, 0);A=(0, 0, 0, 0);Jgeo=1",
        "nonunit_control_mass_shell=-3;orthogonality=-12",
        "unconstrained_timelike_covector_norm=-1",
        "CAS-10-C02=PASS",
    ]
    singular_fragments = [
        "singular_numeric_version=\n44100",
        "Gmass[1]=u0^2-u1^2-u2^2-u3^2-1",
        "orth_minus_h_mass_shell=\n0",
        "orth_remainder=\n0",
        "b_norm_minus_Jgeo_minus_h2_mass_shell=\n0",
        "Jgeo_minus_b_norm_remainder=\n0",
        "A_norm_minus_4c2_b_norm=\n0",
        "u0sq_b_norm_minus_sos_remainder=\n0",
        "rest_residuals_mass_orth_JB_AJ=\n0 0 0 0",
        "boosted_residuals_mass_orth_JB_AJ=\n0 0 0 0",
        "A_zero_control_b_A_J=\n0 0 0 0 0 0 0 0 0",
        "c_zero_control_b_A_J=\n0 1 0 0 0 0 0 0 1",
        "nonunit_control_mass_orth=\n-3 -12",
        "failure_count=\n0",
        "CAS-10-C02=PASS",
    ]
    sage_diagnostics_ok, sage_markers = contains_all(sage_proof["stdout_text"], sage_fragments)
    singular_diagnostics_ok, singular_markers = contains_all(singular_proof["stdout_text"], singular_fragments)

    version_ok = (
        sage_version["exit_code"] == 0
        and singular_version["exit_code"] == 0
        and "SageMath version 10.9" in sage_version["stdout_text"]
        and "version 4.4.1 (44100" in singular_version["stdout_text"]
    )
    sage_ok = sage_proof["exit_code"] == 0 and sage_proof["stderr"]["bytes"] == 0 and sage_diagnostics_ok
    singular_ok = singular_proof["exit_code"] == 0 and singular_proof["stderr"]["bytes"] == 0 and singular_diagnostics_ok
    component_ok = frozen_ok and version_ok and sage_ok and singular_ok

    result: dict[str, Any] = {
        "schema": "htt.cas.axis-result.v2",
        "contract_id": "GRSTAT-20260930-CAS-10-C02-MASS-SHELL-INVARIANT-V1",
        "component": "CAS-10-C02",
        "axis": "sage_singular",
        "status": "PASS" if component_ok else "FAIL",
        "evidence_class": "exact",
        "checks": {"CAS-10-C02": component_ok},
        "domain_assumption_diff": [],
        "counterexample": None,
        "scientific_admission": "HOLD",
        "claim_ceiling": "C02 finite mass-shell invariant only; no statistics/science admission",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "result_path": str(RESULT_PATH),
        "execution_identity": {
            "execution_authorization": "direct owner-authorized local execution",
            "launch_id": None,
            "authority": "unavailable",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
            "independence_mode": "blind-results-and-derivations",
            "sibling_or_historical_axis_reads": False,
        },
        "frozen_hash_verification": frozen,
        "source_hashes": [
            file_record(AXIS_DIR / "run.py"),
            file_record(AXIS_DIR / "prove_c02.sage"),
            file_record(AXIS_DIR / "prove_c02.sing"),
        ],
        "versions": {
            "sage": "10.9",
            "singular": "4.4.1/44100",
            "singular_binary_sha256": SINGULAR_BINARY_SHA256,
        },
        "version_executions": [public_execution(sage_version), public_execution(singular_version)],
        "engine_executions": [public_execution(sage_proof), public_execution(singular_proof)],
        "diagnostic_validation": {
            "sage": {
                "passed": sage_diagnostics_ok,
                "markers": sage_markers,
            },
            "singular": {
                "passed": singular_diagnostics_ok,
                "markers": singular_markers,
                "summary": {
                    "coefficient_field": "QQ",
                    "ring_variable_count": 15,
                    "mass_shell_groebner_basis": "u0^2-u1^2-u2^2-u3^2-1",
                    "universal_and_factor_remainders": [0, 0, 0, 0, 0, 0],
                    "rest_residuals": [0, 0, 0, 0],
                    "boosted_rational_residuals": [0, 0, 0, 0],
                    "A_zero_control_b_A_J": [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    "c_zero_control_b_A_J": [0, 1, 0, 0, 0, 0, 0, 0, 1],
                    "nonunit_control_mass_orth": [-3, -12],
                    "failure_count": 0,
                },
            },
        },
        "statement_alignment": {
            "assumptions": ["real symmetric S", "u^T g u=-1", "u0>0", "c>0"],
            "targets": {
                "u^T b=0": component_ok,
                "Jgeo=b^T g^-1 b=A^T g^-1 A/(4c^2)": component_ok,
                "Jgeo>=0_on_future_unit_mass_shell": component_ok,
                "Jgeo=0_iff_A=0": component_ok,
            },
            "positivity_certificate": "u0^2 b^T g^-1 b=b1^2+b2^2+b3^2+(u1b2-u2b1)^2+(u1b3-u3b1)^2+(u2b3-u3b2)^2",
            "units": "No numerical value substituted for c; Jgeo and A^2/(4c^2) have the same declared units.",
            "limits": "No limits taken.",
        },
        "controls": {
            "rest_exact": sage_ok and singular_ok,
            "boosted_rational_exact": sage_ok and singular_ok,
            "A_zero": sage_ok and singular_ok,
            "c_zero_excluded": sage_ok and singular_ok,
            "nonunit_u_excluded": sage_ok and singular_ok,
            "positivity_without_orthogonality_excluded": sage_ok and singular_ok,
        },
        "preserved_history": {
            "uppercase_result_renamed_byte_identically": file_record(AXIS_DIR / "RESULT.initial.json"),
            "packaging_lineage": file_record(AXIS_DIR / "PACKAGING_LINEAGE.json"),
            "initial_sage_failure_stdout": file_record(AXIS_DIR / "sage.attempt1.stdout.log"),
            "initial_sage_failure_stderr": file_record(AXIS_DIR / "sage.attempt1.stderr.log"),
        },
        "remaining_obligations": [
            "CAS10 C01,C03,C04 exact input alignment",
            "probability-law and analytic obligations",
            "science",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    envelope = {
        "status": result["status"],
        "checks": result["checks"],
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": result["counterexample"],
        "result_path": str(RESULT_PATH),
    }
    sys.stdout.write(json.dumps(envelope, separators=(",", ":"), sort_keys=True) + "\n")
    return 0 if component_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
