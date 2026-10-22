#!/usr/bin/env python3
"""Compile the blind CAS-07 M02 Lean axis and emit its single result document."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
TASK = HERE.parent
REPO = HERE.parents[7]
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
MAIN = HERE / "Main.lean"
RESULT = HERE / "RESULT.json"
EXPECTED = {
    "EXECUTION_CONTRACT.json": "eacc294fa147bd4cabaf295c76f29814b461cae2c8d10eb0a44fdbe2254e0799",
    "ADMITTED_INPUTS.json": "18bfcfb302209caaeac08df72137040ea0939826c551045e7f798d86921db125",
    "COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    "formal_mathlib/lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    "formal_mathlib/lake-manifest.json": "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)


def main() -> int:
    paths = {
        "EXECUTION_CONTRACT.json": TASK / "EXECUTION_CONTRACT.json",
        "ADMITTED_INPUTS.json": TASK / "ADMITTED_INPUTS.json",
        "COMMON_SPEC.md": REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md",
        "formal_mathlib/lean-toolchain": REPO / "formal_mathlib/lean-toolchain",
        "formal_mathlib/lake-manifest.json": REPO / "formal_mathlib/lake-manifest.json",
    }
    input_hashes = {name: sha(path) for name, path in paths.items()}
    input_seals_match = all(input_hashes[k] == v for k, v in EXPECTED.items())
    source = MAIN.read_text()
    forbidden = [
        token for token in ("sorry", "admit", "unsafe", "native_decide")
        if re.search(r"\b" + token + r"\b", source)
    ]
    forbidden += [
        "new_axiom_or_constant" if re.search(r"(?m)^\s*(?:axiom|constant)\b", source) else ""
    ]
    forbidden = [item for item in forbidden if item]

    lean_version = run(["lake", "env", "lean", "--version"], ORACLE)
    lake_version = run(["lake", "--version"], ORACLE)
    mathlib_revision = run(["git", "rev-parse", "HEAD"], ORACLE / ".lake/packages/mathlib")
    argv = ["lake", "env", "lean", str(MAIN)]
    compile_result = run(argv, ORACLE, timeout=3600)
    (HERE / "compile.stdout.log").write_text(compile_result.stdout)
    (HERE / "compile.stderr.log").write_text(compile_result.stderr)

    theorem_names = (
        "remainder_identity",
        "remainder_bound",
        "remainder_identity_physical",
        "remainder_bound_physical",
    )
    axioms_printed = {
        name: bool(re.search(r"'CAS07M02\." + name + r"' depends on axioms: \[[^\]]+\]", compile_result.stdout))
        for name in theorem_names
    }
    axioms_clean = "sorryAx" not in compile_result.stdout and all(axioms_printed.values())
    toolchain_match = (
        "version 4.31.0" in lean_version.stdout
        and mathlib_revision.stdout.strip() == "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
        and sha(ORACLE / "lean-toolchain") == EXPECTED["formal_mathlib/lean-toolchain"]
    )
    passed = (
        compile_result.returncode == 0
        and input_seals_match
        and toolchain_match
        and not forbidden
        and axioms_clean
    )
    result = {
        "schema": "htt.cas07.m02.lean-result.v1",
        "axis": "lean",
        "contract_id": "GRSTAT-20260930-CAS-07-M02-TAYLOR-REMAINDER-V1",
        "status": "PASS" if passed else "FAIL",
        "checks": {
            "CAS-07-M02-REMAINDER-IDENTITY": passed,
            "CAS-07-M02-REMAINDER-BOUND": passed,
        },
        "domain_assumption_diff": [],
        "domain_assumption_alignment": {
            "status": "ALIGNED",
            "detail": "Real functions on [0,L], endpoint HasDerivAt witnesses, continuous Z2, 0<=s<=L, c>0, M2>=0 and pointwise |Z2|<=M2. The exact identity theorem uses only regularity and interval-order assumptions; the bound theorem retains the declared M2 condition. Z0=Z(0) and H0=c*Z1(0) are explicit in the physical corollaries.",
        },
        "counterexample": None,
        "model": "UNKNOWN",
        "effort": "UNKNOWN",
        "executed_utc": datetime.now(timezone.utc).isoformat(),
        "input_sha256": input_hashes,
        "input_seals_match": input_seals_match,
        "toolchain": {
            "lean_version": lean_version.stdout.strip(),
            "lean_version_exit_code": lean_version.returncode,
            "lake_version": lake_version.stdout.strip(),
            "lake_version_exit_code": lake_version.returncode,
            "mathlib_revision": mathlib_revision.stdout.strip(),
            "mathlib_revision_exit_code": mathlib_revision.returncode,
            "oracle_lean_toolchain_sha256": sha(ORACLE / "lean-toolchain"),
            "oracle_lake_manifest_sha256": sha(ORACLE / "lake-manifest.json"),
            "pinned_repo_lean_toolchain_sha256": input_hashes["formal_mathlib/lean-toolchain"],
            "pinned_repo_lake_manifest_sha256": input_hashes["formal_mathlib/lake-manifest.json"],
            "matches_contract": toolchain_match,
        },
        "execution": {
            "cwd": str(ORACLE),
            "argv": argv,
            "exit_code": compile_result.returncode,
            "stdout_log": str(HERE / "compile.stdout.log"),
            "stderr_log": str(HERE / "compile.stderr.log"),
            "axioms_printed": axioms_printed,
            "axioms_clean": axioms_clean,
            "forbidden_scan": forbidden,
        },
        "executable_artifacts": {
            "Main.lean": sha(MAIN),
            "run.py": sha(Path(__file__)),
            "compile.stdout.log": sha(HERE / "compile.stdout.log"),
            "compile.stderr.log": sha(HERE / "compile.stderr.log"),
            "compile_failures.log": sha(HERE / "compile_failures.log"),
        },
        "scope": "Integral Taylor remainder component only; scientific admission HOLD.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
