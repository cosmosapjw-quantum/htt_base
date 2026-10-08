#!/usr/bin/env python3
"""Fresh CAS-07 M03 Wolfram+xTensor axis; writes only this axis's result."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT_DIR = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / "AGENTS.md").is_file())
CONTRACT = INPUT_DIR / "EXECUTION_CONTRACT.json"
ADMITTED = INPUT_DIR / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
CHECK = HERE / "check.wl"
PROOF = HERE / "PROOF.md"
RAW = HERE / "wolfram_run_raw.log"
RESULT = HERE / "result.json"
EXPECTED = {
    CONTRACT: "6c840eaffac0744da3d1b2f9c7de3f8b1c45af2d949ba4831b5e90d4ec9a51ae",
    ADMITTED: "bbb0f93dc43ddd3ee96cdee065f8173ccac44007a6908ae66714f25e3214661d",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
REQUIRED_WL = {
    "beta_convolution",
    "monomial_induction",
    "kernel_mass",
    "remainder_ratio",
    "ratio_limit",
    "sinh_series",
    "zero_k",
    "vertex",
    "equality_solution",
    "zero_function_control",
    "xtensor_metric_contraction_symmetry",
    "xtensor_weighted_norm_contraction",
    "positive_volterra_weight",
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    actual_inputs = {str(path.relative_to(ROOT)): sha(path) for path in EXPECTED}
    inputs_match = all(sha(path) == expected for path, expected in EXPECTED.items())
    executable = shutil.which("WolframKernel")
    resolved = Path(executable).resolve() if executable else None
    command = [executable, "-script", str(CHECK)] if executable else []
    process_code = None
    raw_text = ""
    error = None
    if not executable:
        error = "WolframKernel executable unavailable"
    else:
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=1800,
                check=False,
            )
            process_code = completed.returncode
            raw_text = completed.stdout
        except subprocess.TimeoutExpired as exc:
            error = "WolframKernel timed out after 1800 seconds"
            raw_text = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        RAW.write_text(raw_text, encoding="utf-8")

    check_matches = re.findall(r"^CHECKS_JSON=(\{.*\})$", raw_text, flags=re.MULTILINE)
    wl_checks = json.loads(check_matches[-1]) if len(check_matches) == 1 else {}
    wolfram_version = re.search(r"^WOLFRAM_VERSION=(.*)$", raw_text, flags=re.MULTILINE)
    xtensor_version = re.search(r"Package xAct`xTensor` version ([^,\n]+)", raw_text)
    versions_match = (
        wolfram_version is not None
        and "15.0.0" in wolfram_version.group(1)
        and xtensor_version is not None
        and xtensor_version.group(1).strip() == "1.3.0"
    )
    all_wl = set(wl_checks) == REQUIRED_WL and all(wl_checks.values())
    passed = (
        inputs_match
        and CHECK.is_file()
        and PROOF.is_file()
        and process_code == 0
        and versions_match
        and all_wl
    )
    result = {
        "axis": "wolfram_xact",
        "contract_id": "GRSTAT-20260930-CAS-07-M03-SCALAR-VOLTERRA-V1",
        "status": "PASS" if passed else "FAIL",
        "checks": {"CAS-07-M03-SCALAR-VOLTERRA": bool(passed)},
        "domain_assumption_diff": [],
        "counterexample": None,
        "global_launch_id": None,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "execution": {
            "command": command,
            "cwd": str(ROOT),
            "exit_code": process_code,
            "error": error,
            "wolfram_version": wolfram_version.group(1) if wolfram_version else None,
            "xtensor_version": xtensor_version.group(1).strip() if xtensor_version else None,
            "executable_path": executable,
            "resolved_executable_path": str(resolved) if resolved else None,
            "executable_sha256": sha(resolved) if resolved and resolved.is_file() else None,
        },
        "inputs_sha256": actual_inputs,
        "artifacts_sha256": {
            "check.wl": sha(CHECK) if CHECK.is_file() else None,
            "PROOF.md": sha(PROOF) if PROOF.is_file() else None,
            "wolfram_run_raw.log": sha(RAW) if RAW.is_file() else None,
            "probe_failure_excerpt.txt": sha(HERE / "probe_failure_excerpt.txt") if (HERE / "probe_failure_excerpt.txt").is_file() else None,
        },
        "wolfram_exact_checks": wl_checks,
        "evidence": ["check.wl", "PROOF.md", "wolfram_run_raw.log", "probe_failure_excerpt.txt"],
        "claim_ceiling": "scalar_Volterra_comparison_only_no_matrix_or_science",
        "scientific_admission": "HOLD",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
