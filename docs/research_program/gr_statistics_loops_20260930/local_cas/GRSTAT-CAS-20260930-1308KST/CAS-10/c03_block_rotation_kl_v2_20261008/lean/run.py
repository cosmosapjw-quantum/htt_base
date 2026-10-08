#!/usr/bin/env python3
"""Run the independent Lean axis for frozen CAS-10-C03 v2."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUT = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = HERE / "CAS10C03.lean"
OLEAN = HERE / "CAS10C03.olean"
EXPECTED = {
    "contract": "d64d348c940ea7b37c522fb1043eaa29a6558798104d953fe554b3844ca9811e",
    "input": "d538b90a28b749702209c68e0c73444607295e4b66f2c55d1640d9bd75cf5e53",
    "common": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    "manifest": "1a7cbb6b0487b078e2e5f768fc9e1bd78e2e36d0d896477cadf1d8971464db08",
    "toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    "mathlib_revision": "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def command(argv: list[str], cwd: Path, label: str, timeout: int = 3600) -> dict:
    started = stamp()
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        output = {"exit_code": p.returncode, "timed_out": False,
                  "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as exc:
        output = {"exit_code": None, "timed_out": True,
                  "stdout": (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
                  "stderr": (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")}
    (HERE / f"{label}.stdout.log").write_text(output["stdout"])
    (HERE / f"{label}.stderr.log").write_text(output["stderr"])
    return {"argv": argv, "cwd": str(cwd), "started_at": started,
            "completed_at": stamp(), "exit_code": output["exit_code"],
            "timed_out": output["timed_out"],
            "stdout_log": str(HERE / f"{label}.stdout.log"),
            "stderr_log": str(HERE / f"{label}.stderr.log")}


def main() -> int:
    checks = {
        "contract": sha256(CONTRACT) == EXPECTED["contract"],
        "input": sha256(INPUT) == EXPECTED["input"],
        "common": sha256(COMMON) == EXPECTED["common"],
        "manifest": sha256(ORACLE / "lake-manifest.json") == EXPECTED["manifest"],
        "toolchain": sha256(ORACLE / "lean-toolchain") == EXPECTED["toolchain"],
        "mathlib_olean": (ORACLE / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib.olean").is_file(),
    }
    revision = command(["git", "-C", str(ORACLE / ".lake/packages/mathlib"),
                        "rev-parse", "HEAD"], ORACLE, "mathlib_revision", 30)
    revision_value = (HERE / "mathlib_revision.stdout.log").read_text().strip()
    checks["mathlib_revision"] = revision["exit_code"] == 0 and revision_value == EXPECTED["mathlib_revision"]
    source_text = SOURCE.read_text()
    checks["no_placeholders_or_target_axioms"] = not re.search(
        r"\b(sorry|admit|axiom|constant)\b", source_text
    )
    version = command(["env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0",
                       "lean", "--version"], ORACLE, "lean_version", 30)
    version_value = (HERE / "lean_version.stdout.log").read_text().strip()
    checks["lean_version"] = version["exit_code"] == 0 and version_value.startswith("Lean (version 4.31.0,")
    compile_result = None
    if all(checks.values()):
        compile_result = command(
            ["env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0", "lake", "env", "lean",
             "-R", str(HERE), "-o", str(OLEAN), str(SOURCE)], ORACLE, "lean_compile", 3600
        )
    checks["compiled"] = compile_result is not None and compile_result["exit_code"] == 0 and OLEAN.is_file()
    artifacts = {}
    for path in [SOURCE, OLEAN, HERE / "lean_version.stdout.log",
                 HERE / "lean_version.stderr.log", HERE / "lean_compile.stdout.log",
                 HERE / "lean_compile.stderr.log"]:
        if path.is_file():
            artifacts[str(path)] = {"sha256": sha256(path), "size": path.stat().st_size}
    result = {
        "schema_version": 1,
        "axis": "lean",
        "status": "PASS" if all(checks.values()) else "INCONCLUSIVE",
        "evidence_class": "exact",
        "contract_id": "GRSTAT-20260930-CAS-10-C03-BLOCK-ROTATION-KL-V2",
        "contract_sha256": sha256(CONTRACT),
        "input_sha256": sha256(INPUT),
        "common_spec_sha256": sha256(COMMON),
        "completed_at": stamp(),
        "commands": [revision, version] + ([compile_result] if compile_result else []),
        "checks": {"CAS-10-C03": all(checks.values())},
        "check_details": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "statement_alignment": {
            "field": "real", "blocks": [1, 3, 1, 3, 5],
            "order": ["Z0", "Z1", "m", "p", "T"],
            "slope_block_zero_based_index": 3,
            "positive_scales": ["sigma_0", "sigma_1", "sigma_m", "sigma_p", "sigma_T"],
            "scope": "finite block rotation and common-covariance KL quadratic only",
            "theorems": ["R_orthogonal", "R_det", "R_maps_p", "R_preserves_sqNorm",
                         "rotate_first", "rotate_preserves_block_norms", "block_norms_agree",
                         "block_variances_positive", "kl_formula", "control_zero", "control_one"],
        },
        "toolchain": {"lean_version": version_value, "mathlib_revision": revision_value,
                      "manifest_sha256": sha256(ORACLE / "lake-manifest.json"),
                      "toolchain_sha256": sha256(ORACLE / "lean-toolchain"),
                      "mathlib_olean_sha256": sha256(ORACLE / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib.olean")},
        "artifacts": artifacts,
        "independence_mode": "blind-results-and-derivations",
        "sibling_scripts_derivations_results_read": False,
        "global_launch_id": None,
        "global_launch_status": "UNAVAILABLE",
        "observed_author_model": "UNKNOWN",
        "observed_author_effort": "UNKNOWN",
        "remaining_analytical_obligations": ["compressed probability-law equality",
                                             "test-power conclusion", "science"],
        "scientific_admission": "HOLD",
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2) + "\n")
    payload = {"checks": result["checks"], "domain_assumption_diff": [], "counterexample": None}
    print(json.dumps(payload))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
