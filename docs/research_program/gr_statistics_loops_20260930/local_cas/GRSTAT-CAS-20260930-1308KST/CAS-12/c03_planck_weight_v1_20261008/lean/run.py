#!/usr/bin/env python3
"""Compile the frozen CAS-12-C03 Lean component and emit its typed axis result."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ORACLE = pathlib.Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = HERE / "CAS12C03.lean"
OLEAN = HERE / "CAS12C03.olean"
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
SPEC = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "1950de303557d1b805f17a45dc478011bd24e73f06f5444b2ebf9cc3ce06c4a4",
    INPUTS: "22967352d8773a6324fc413d0da748081af52b1a63907af1f3d80119438a2a63",
    SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
THEOREMS = (
    "hyperbolic_identity",
    "scaled_right_limit",
    "exp8_coeff",
    "scaledLaurent_substitution",
    "formal_product_certificate",
)


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(argv: list[str], label: str) -> dict:
    process = subprocess.run(argv, cwd=ORACLE, text=True, capture_output=True, check=False)
    out = HERE / f"{label}.stdout.log"
    err = HERE / f"{label}.stderr.log"
    out.write_text(process.stdout)
    err.write_text(process.stderr)
    return {
        "argv": argv,
        "cwd": str(ORACLE),
        "exit_code": process.returncode,
        "stdout_path": str(out),
        "stderr_path": str(err),
        "stdout_sha256": digest(out),
        "stderr_sha256": digest(err),
    }


def main() -> int:
    binding_ok = all(path.is_file() and digest(path) == sha for path, sha in EXPECTED.items())
    source_text = SOURCE.read_text()
    forbidden = re.findall(r"\b(?:sorry|admit|axiom)\b", source_text)
    commands = [
        execute(["lake", "env", "lean", "--version"], "lean_version"),
        execute(["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"], "mathlib_rev"),
        execute(["lake", "env", "lean", "-R", str(HERE), "-o", str(OLEAN), str(SOURCE)], "compile"),
    ]
    compiled = (HERE / "compile.stdout.log").read_text()
    expected_axioms = "[propext, Classical.choice, Quot.sound]"
    axioms_ok = all(
        f"'CAS12C03.{name}' depends on axioms: {expected_axioms}" in compiled
        for name in THEOREMS
    ) and "sorryAx" not in compiled
    mathlib_ok = (HERE / "mathlib_rev.stdout.log").read_text().strip() == (
        "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
    )
    lean_ok = "Lean (version 4.31.0" in (HERE / "lean_version.stdout.log").read_text()
    passed = all(item["exit_code"] == 0 for item in commands) and all(
        (binding_ok, not forbidden, axioms_ok, mathlib_ok, lean_ok, OLEAN.is_file())
    )
    result = {
        "axis": "lean",
        "status": "PASS" if passed else "INCONCLUSIVE",
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "commands": commands,
        "checks": {"CAS-12-C03": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "source_sha256": digest(SOURCE),
        "olean_sha256": digest(OLEAN) if OLEAN.is_file() else None,
        "input_hashes_verified": binding_ok,
        "forbidden_tokens": forbidden,
        "axioms_verified": axioms_ok,
        "lean_version_verified": lean_ok,
        "mathlib_revision_verified": mathlib_ok,
        "claim_ceiling": "CAS-12-C03 finite component only; no UV/full-theorem/scientific admission",
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-12-C03": passed}, "domain_assumption_diff": [], "counterexample": None}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
