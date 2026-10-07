#!/usr/bin/env python3
"""Execute the independent CAS14 Wolfram+xTensor proof source."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
UNIT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
EXPECTED_CONTRACT = "afee8b0f823bb89f9a1507a5c8fbcff97c95f152296f88e55e15cdcdbce21639"
EXPECTED_INPUTS = "ed8d777bf74f3b35af925e807a90842af9530355a6f392dab5d5e0bbcf1a7591"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    source = HERE / "Main.wl"
    math_output = HERE / "math_result.json"
    result_path = HERE / "result.json"
    contract_sha = digest(CONTRACT)
    input_sha = digest(INPUTS)
    source_sha = digest(source)
    alignment = contract_sha == EXPECTED_CONTRACT and input_sha == EXPECTED_INPUTS
    if not alignment:
        result = {
            "status": "FAIL",
            "checks": {"INPUT_HASH_ALIGNMENT": False},
            "domain_assumption_diff": ["Frozen contract or admitted-input hash changed"],
            "counterexample": None,
            "contract_sha256": contract_sha,
            "input_sha256": input_sha,
            "source_sha256": source_sha,
            "launch_id": None,
            "authority_status": "UNAVAILABLE_BY_OWNER_OVERRIDE",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
        }
        write_json(result_path, result)
        print(json.dumps({**result, "result_path": str(result_path.relative_to(ROOT))}))
        return 2

    if math_output.exists():
        math_output.unlink()
    argv = ["wolframscript", "-file", str(source), str(math_output)]
    cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=1700)
    (HERE / "run.stdout.log").write_text(cp.stdout)
    (HERE / "run.stderr.log").write_text(cp.stderr)
    execution = {
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": cp.returncode,
        "contract_sha256": contract_sha,
        "input_sha256": input_sha,
        "source_sha256": source_sha,
        "stdout_sha256": digest(HERE / "run.stdout.log"),
        "stderr_sha256": digest(HERE / "run.stderr.log"),
        "math_output_exists": math_output.exists(),
    }
    write_json(HERE / "execution.json", execution)
    try:
        math = json.loads(math_output.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        math = {
            "status": "FAIL",
            "checks": {"WOLFRAM_OUTPUT_PARSE": False},
            "domain_assumption_diff": [f"Wolfram output unavailable: {type(exc).__name__}"],
            "counterexample": None,
        }
    required = {
        "C01_LEVI_CROSS_ORIENTATION", "C01_TRIPLE_PROJECTION", "C01_GRAM_BLOCK",
        "C01_DATA_NORMAL_EQUATION", "C02_PSD_QUADRATIC_IDENTITY",
        "C02_KERNEL_PROJECTION", "C02_PAIR_MINORS", "C02_PAIR_POSITIVE_DEFINITE",
        "C02_INVERSE_IDENTITY", "C02_ALL_PARALLEL_KERNEL", "C02_E1_E2_CONTROL",
        "C03_EXACT_SVD_COEFFICIENTS", "C03_EXACT_SVD_BOUND",
        "C03_PERTURBED_RESIDUAL_IDENTITY", "C03_PERTURBED_BOUND_SIGN",
        "C03_FROBENIUS", "C03_ZERO_DATA_ERROR_CONTROL",
        "C03_ZERO_OPERATOR_ERROR_CONTROL", "C03_ZERO_AMPLITUDE_CONTROL",
        "C03_NO_AMPLITUDE_COUNTERCONTROL",
    }
    checks = math.get("checks", {})
    toolchain = math.get("toolchain", {})
    toolchain_aligned = (isinstance(toolchain, dict)
                         and str(toolchain.get("wolfram_version", "")).startswith("15.0.0")
                         and "1.3.0" in str(toolchain.get("xtensor_version", "")))
    all_pass = (cp.returncode == 0 and math.get("status") == "PASS"
                and toolchain_aligned
                and isinstance(checks, dict) and required <= checks.keys()
                and all(checks.get(k) is True for k in required))
    result = {
        "status": "PASS" if all_pass else "FAIL",
        "checks": checks,
        "details": math.get("details", {}),
        "domain_assumption_diff": math.get("domain_assumption_diff", []),
        "counterexample": math.get("counterexample"),
        "contract_sha256": contract_sha,
        "input_sha256": input_sha,
        "source_sha256": source_sha,
        "wolfram": math.get("toolchain", {}),
        "execution": execution,
        "launch_id": None,
        "authority_status": "UNAVAILABLE_BY_OWNER_OVERRIDE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "evidence_class": "exact",
        "claim_ceiling": "finite_vorticity_inverse_math_only_no_observation_or_science",
    }
    write_json(result_path, result)
    envelope = {
        "status": result["status"],
        "checks": checks,
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": result["counterexample"],
        "result_path": str(result_path.relative_to(ROOT)),
    }
    print(json.dumps(envelope, sort_keys=True))
    return 0 if all_pass else 2


if __name__ == "__main__":
    sys.exit(main())
