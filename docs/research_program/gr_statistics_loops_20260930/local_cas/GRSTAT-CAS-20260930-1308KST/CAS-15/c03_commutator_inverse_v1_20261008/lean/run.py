#!/usr/bin/env python3
"""Read and verify the frozen Lean C03 evidence; emit one aggregate payload."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "CAS15C03.lean"
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
TASK = HERE.parent
CONTRACT = TASK / "EXECUTION_CONTRACT.json"
ADMITTED = TASK / "ADMITTED_INPUTS.json"
COMMON = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md")
RESULT = HERE / "axis_result.json"
EXPECTED = {
    CONTRACT: "536b6e955deb1627fcad72a332fe63db2622792421202d5865c4650e6e7a46b9",
    ADMITTED: "392be3feb939fa3f211ff827077ddeb132c63d1fbdf10eed0eeba38e4aa0de9d",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    ORACLE / "lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    ORACLE / "lake-manifest.json": "1a7cbb6b0487b078e2e5f768fc9e1bd78e2e36d0d896477cadf1d8971464db08",
}
BRIDGES = [
    "mixed operator/Frobenius commutator perturbation estimate for arbitrary rotated symmetric Mhat",
    "coercivity bridge from spectral gap for arbitrary rotated Mhat",
    "Weyl operator-norm to ordered-eigenvalue matching theorem",
]
EXPECTED_MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
EXPECTED_AXIOMS = "[propext, Classical.choice, Quot.sound]"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> None:
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"frozen input hash mismatch: {path}")
    result = json.loads(RESULT.read_text())
    if result["axis"] != "lean" or result["status"] != "INCONCLUSIVE":
        raise ValueError("stored Lean status changed")
    if result["contract_sha256"] != sha(CONTRACT):
        raise ValueError("stored contract binding changed")
    if result["checks"]["source_sha256"] != sha(SOURCE):
        raise ValueError("Lean source changed after the recorded compile")
    if result["checks"]["runner_sha256"] != sha(Path(__file__)):
        raise ValueError("runner changed after envelope binding")
    if result["checks"]["remaining"] != BRIDGES:
        raise ValueError("missing-bridge inventory changed")
    if result["checks"]["input_sha256"] != {str(path): digest for path, digest in EXPECTED.items()}:
        raise ValueError("stored input binding changed")
    if not result["checks"]["source_compiled"] or not result["checks"]["no_sorryAx_printed"]:
        raise ValueError("stored Lean compile is not clean")
    if re.search(r"\b(sorry|admit|axiom)\b", SOURCE.read_text()):
        raise ValueError("forbidden proof shortcut token in Lean source")
    commands = result["commands"]
    if len(commands) != 2 or any(command["exit_code"] != 0 for command in commands):
        raise ValueError("stored version/compile commands are incomplete")
    for command in commands:
        for stream in ("stdout", "stderr"):
            path = Path(command[stream])
            if path.parent != HERE or sha(path) != command[f"{stream}_sha256"]:
                raise ValueError(f"stored {stream} log changed")
    version_stdout = Path(commands[0]["stdout"]).read_text()
    if "Lean (version 4.31.0" not in version_stdout:
        raise ValueError("stored Lean version changed")
    compile_stdout = Path(commands[1]["stdout"]).read_text()
    if "sorryAx" in compile_stdout:
        raise ValueError("compiled proof depends on sorryAx")
    for theorem in (
        "cm_inverse", "commLinear_rank_three", "sq_gap", "least_squares_unique",
        "ordered_gap_bound", "perturbation_from_coercivity",
        "repeated01_kernel", "isotropic_zero",
    ):
        if f"'CAS15C03.{theorem}' depends on axioms: {EXPECTED_AXIOMS}" not in compile_stdout:
            raise ValueError(f"axiom print missing or changed: {theorem}")
    rev = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ORACLE / ".lake/packages/mathlib",
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if rev != EXPECTED_MATHLIB_REV or result["checks"]["mathlib_revision"] != rev:
        raise ValueError("pinned mathlib revision changed")


def main() -> None:
    verify()
    print(json.dumps({
        "checks": {"CAS-15-C03": False},
        "domain_assumption_diff": BRIDGES,
        "counterexample": None,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

