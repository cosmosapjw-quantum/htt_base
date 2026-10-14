#!/usr/bin/env python3
"""Execute the frozen CAS-15 C04 Lean certificate in the pinned local oracle."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
UNIT = HERE.parent
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
CONTRACT_SHA = "67422619e47fda896d7516d48e980ec693d878f3c63e5d61e0c151ffaef65ed8"
INPUT_SHA = "1b98962616a8a43aca614c18a7e69304653c84f0d1b54846a81811642d2491d8"
MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
OBLIGATION = "CAS-15-C04"
THEOREMS = (
    "skew_represents_all",
    "orthonormal_skew_basis",
    "gram_frobenius",
    "gram_kernel_iff",
    "gram_kernel_all_skew",
    "one_axis_rank_two",
    "pair_gram_posDef_rank_three",
    "parallel_pair_kernel_dimension_one",
)
STANDARD_AXIOMS = "[propext, Classical.choice, Quot.sound]"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: Path, stem: str, env: dict[str, str], timeout: int = 3600) -> dict:
    proc = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    out = HERE / f"{stem}.stdout.log"
    err = HERE / f"{stem}.stderr.log"
    out.write_text(proc.stdout)
    err.write_text(proc.stderr)
    return {
        "argv": argv,
        "cwd": str(cwd),
        "ELAN_TOOLCHAIN": env["ELAN_TOOLCHAIN"],
        "exit_code": proc.returncode,
        "stdout_path": str(out.relative_to(UNIT)),
        "stderr_path": str(err.relative_to(UNIT)),
        "stdout_sha256": sha256(out),
        "stderr_sha256": sha256(err),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    commands: list[dict] = []
    differences: list[str] = []
    source = HERE / "Main.lean"
    contract = UNIT / "EXECUTION_CONTRACT.json"
    inputs = UNIT / "ADMITTED_INPUTS.json"
    observed_hashes = {
        "source": sha256(source),
        "contract": sha256(contract),
        "inputs": sha256(inputs),
        "lean_toolchain": sha256(ORACLE / "lean-toolchain"),
        "lake_manifest": sha256(ORACLE / "lake-manifest.json"),
    }
    if observed_hashes["contract"] != CONTRACT_SHA:
        differences.append("contract SHA256 mismatch")
    if observed_hashes["inputs"] != INPUT_SHA:
        differences.append("admitted inputs SHA256 mismatch")
    if re.search(r"\b(?:sorry|admit|axiom|unsafe|native_decide)\b", source.read_text()):
        differences.append("forbidden proof shortcut in Lean source")

    env = os.environ.copy()
    env["ELAN_TOOLCHAIN"] = "leanprover/lean4:v4.31.0"
    for argv, stem in (
        (["lake", "env", "lean", "--version"], "lean_version"),
        (["git", "-C", str(ORACLE / ".lake/packages/mathlib"), "rev-parse", "HEAD"], "mathlib_rev"),
        (["lake", "env", "lean", str(source)], "lean_compile"),
    ):
        commands.append(run(argv, ORACLE, stem, env))

    version, revision, compile_result = commands
    if version["exit_code"] or "Lean (version 4.31.0" not in version["stdout"]:
        differences.append("Lean 4.31.0 executable not observed")
    if revision["exit_code"] or revision["stdout"].strip() != MATHLIB_REV:
        differences.append("mathlib revision mismatch")
    axioms = {
        name: f"'CAS15C04.{name}' depends on axioms: {STANDARD_AXIOMS}"
        for name in THEOREMS
    }
    missing_axioms = [name for name, line in axioms.items() if line not in compile_result["stdout"]]
    if missing_axioms:
        differences.append("missing or nonstandard axioms: " + ", ".join(missing_axioms))
    check = compile_result["exit_code"] == 0 and not differences
    result = {
        "axis": "lean",
        "status": "PASS" if check else "INCONCLUSIVE",
        "evidence_class": "exact",
        "contract_sha256": CONTRACT_SHA,
        "input_sha256": INPUT_SHA,
        "source_sha256": observed_hashes["source"],
        "source_path": str(source.relative_to(UNIT)),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": {OBLIGATION: check},
        "domain_assumption_diff": differences,
        "counterexample": None,
        "toolchain": {
            "oracle_path": str(ORACLE),
            "lean_version": version["stdout"].strip(),
            "mathlib_revision": revision["stdout"].strip(),
            "environment_sha256": observed_hashes,
            "ELAN_TOOLCHAIN": env["ELAN_TOOLCHAIN"],
        },
        "commands": [{k: v for k, v in c.items() if k not in ("stdout", "stderr")} for c in commands],
        "axiom_lines": axioms,
        "execution_route": "owner_authorized_direct_local_no_global_harness",
        "launch_id": None,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "claim_ceiling": "C04_finite_commutant_only_no_transport_or_science",
    }
    target = HERE / "result.json"
    temp = HERE / "result.json.tmp"
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    temp.replace(target)
    print(json.dumps({
        "checks": result["checks"],
        "domain_assumption_diff": differences,
        "counterexample": None,
        "result_path": str(target),
    }, sort_keys=True))
    return 0 if check else 1


if __name__ == "__main__":
    sys.exit(main())
