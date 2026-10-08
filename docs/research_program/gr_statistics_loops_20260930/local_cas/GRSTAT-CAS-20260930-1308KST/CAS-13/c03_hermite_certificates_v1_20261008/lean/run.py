#!/usr/bin/env python3
"""Execute only the frozen CAS-13-C03 Lean certificate in the pinned oracle."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = HERE / "CAS13C03.lean"
CONTRACT = PACKAGE / "EXECUTION_CONTRACT.json"
INPUTS = PACKAGE / "ADMITTED_INPUTS.json"
TEFF = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "d9b1e59d9e8648e74db64bdf9e7ef82d23e409c9456a5f307fb30dabb0e8e21e",
    INPUTS: "916055a8eff4787ff56bd4e7629cef837333890a9dc5c1a9e8a33aa82c1665b4",
    TEFF: "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
THEOREMS = {
    "p5_identity", "p6_identity", "q5_coeff_unique", "q6_coeff_unique",
    "q5_hasDerivAt", "q6_hasDerivAt", "p5_pos", "p6_pos",
    "lower5", "lower6", "upper5", "upper6", "integral_q5", "integral_q6",
    "q5_two_node_fixed_moments", "q6_two_node_fixed_moments",
    "p5_boundary_polynomial", "p6_boundary_polynomial",
}
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv: list[str], cwd: Path, timeout: int = 60) -> dict:
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout, check=False)
        return {
            "argv": argv, "cwd": str(cwd), "exit_code": proc.returncode,
            "timed_out": False, "stdout": proc.stdout.decode("utf-8", "replace"),
            "stderr": proc.stderr.decode("utf-8", "replace"),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv, "cwd": str(cwd), "exit_code": None,
            "timed_out": True,
            "stdout": (exc.stdout or b"").decode("utf-8", "replace"),
            "stderr": (exc.stderr or b"").decode("utf-8", "replace"),
        }


def main() -> int:
    errors: list[str] = []
    hashes = {str(path): sha256(path) for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if hashes[str(path)] != expected:
            errors.append(f"FROZEN_HASH_MISMATCH:{path}")
    source_text = SOURCE.read_text()
    if re.search(r"\b(sorry|admit|sorryAx)\b", source_text):
        errors.append("FORBIDDEN_PROOF_SHORTCUT")
    lean_version = command(["lean", "--version"], ORACLE)
    lake_version = command(["lake", "--version"], ORACLE)
    mathlib_rev = command(["git", "rev-parse", "HEAD"], ORACLE / ".lake/packages/mathlib")
    toolchain = (ORACLE / "lean-toolchain").read_text().strip()
    if "4.31.0" not in lean_version["stdout"] or toolchain != "leanprover/lean4:v4.31.0":
        errors.append("LEAN_PIN_MISMATCH")
    if mathlib_rev["stdout"].strip() != "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f":
        errors.append("MATHLIB_PIN_MISMATCH")
    for receipt in (lean_version, lake_version, mathlib_rev):
        if receipt["exit_code"] != 0:
            errors.append("TOOL_VERSION_QUERY_FAILED")

    argv = ["lake", "env", "lean", "-j1", str(SOURCE)]
    build = command(argv, ORACLE, timeout=3600) if not errors else {
        "argv": argv, "cwd": str(ORACLE), "exit_code": None, "timed_out": False,
        "stdout": "", "stderr": "PREFLIGHT_FAILED: " + ",".join(errors),
    }
    (HERE / "run.stdout").write_text(build["stdout"])
    (HERE / "run.stderr").write_text(build["stderr"])
    if build["exit_code"] != 0 or build["timed_out"]:
        errors.append("LEAN_COMPILE_NONZERO_OR_TIMEOUT")
    if "error:" in build["stdout"] or "error:" in build["stderr"]:
        errors.append("LEAN_DIAGNOSTIC_ERROR")
    axiom_rows = re.findall(
        r"'CAS13C03\.([A-Za-z0-9_]+)' depends on axioms: \[([^]]*)\]",
        build["stdout"],
    )
    observed_theorems = {name for name, _ in axiom_rows}
    if observed_theorems != THEOREMS or len(axiom_rows) != len(THEOREMS):
        errors.append("AXIOM_REPORT_INCOMPLETE")
    for name, raw in axiom_rows:
        if {part.strip() for part in raw.split(",") if part.strip()} - ALLOWED_AXIOMS:
            errors.append(f"UNAPPROVED_AXIOM:{name}")

    completed_at = datetime.now(timezone.utc).isoformat()
    execution = {
        "axis": "lean", "contract_id": "GRSTAT-20260930-CAS-13-C03-HERMITE-V1",
        "contract_sha256": hashes[str(CONTRACT)],
        "source_input_hashes": {str(p): h for p, h in hashes.items() if p != CONTRACT},
        "tool_versions": {
            "lean": lean_version, "lake": lake_version,
            "mathlib_git_head": mathlib_rev, "lean_toolchain": toolchain,
        },
        "commands": [{k: build[k] for k in ("argv", "cwd", "exit_code", "timed_out")}],
        "source_sha256": sha256(SOURCE),
        "axiom_reports": {name: raw for name, raw in axiom_rows},
        "errors": errors, "completed_at": completed_at,
    }
    (HERE / "run.execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    passed = not errors
    result = {
        "schema_version": 1,
        "axis": "lean", "contract_id": execution["contract_id"],
        "contract_sha256": execution["contract_sha256"],
        "input_sha256": hashes[str(INPUTS)],
        "result": "PASS" if passed else "INCONCLUSIVE",
        "status": "PASS" if passed else "INCONCLUSIVE",
        "checks": {"CAS-13-C03": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "evidence_class": "exact",
        "commands": execution["commands"],
        "tool_versions": {
            "lean": lean_version["stdout"].strip(),
            "lake": lake_version["stdout"].strip(),
            "mathlib_git_head": mathlib_rev["stdout"].strip(),
            "lean_toolchain": toolchain,
        },
        "artifacts": {
            "source": {"path": str(SOURCE), "sha256": sha256(SOURCE)},
            "runner": {"path": str(HERE / "run.py"), "sha256": sha256(HERE / "run.py")},
            "stdout": {"path": str(HERE / "run.stdout"), "sha256": sha256(HERE / "run.stdout")},
            "stderr": {"path": str(HERE / "run.stderr"), "sha256": sha256(HERE / "run.stderr")},
            "execution": {"path": str(HERE / "run.execution.json"), "sha256": sha256(HERE / "run.execution.json")},
        },
        "axiom_reports": execution["axiom_reports"],
        "scope": "p=5,6 positive-node finite Hermite interpolation, signs, conditional moments, polynomial boundaries",
        "claim_ceiling": "finite component only; node existence, moment feasibility, general p and scientific admission remain open",
        "completed_at": completed_at,
        "errors": errors,
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"checks": {"CAS-13-C03": passed}, "domain_assumption_diff": [], "counterexample": None}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
