#!/usr/bin/python3.12
"""Independent Lean+mathlib runner for frozen CAS-07-M01."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/eta_monotonicity_input_aligned_v1_20261007"
OWN = BASE / "lean"
SOURCE = OWN / "M01.lean"
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
MATHLIB = ORACLE / ".lake/packages/mathlib"
EXPECTED = {
    BASE / "EXECUTION_CONTRACT.json": "b5a49f066f95a010607eb800d323094d5d4050c986c3cb26f78bba022977cc70",
    BASE / "ADMITTED_INPUTS.json": "89949f14b9671720a7df7e73ab2bdf2e8cede8ed7937a86ea531635f29259400",
    REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SOURCE: "42ebc3e44a3104a7c7f67b8f608b41de704cba0d379f6191138aea580503443d",
    REPO / "formal_mathlib/lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    REPO / "formal_mathlib/lake-manifest.json": "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
}
MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=1800, check=False)


def main() -> int:
    seals_ok = all(path.is_file() and sha(path) == expected for path, expected in EXPECTED.items())
    forbidden = re.findall(r"(?m)\b(sorry|admit|native_decide|axiom)\b", SOURCE.read_text())
    version = command(["env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0", "lean", "--version"], ORACLE)
    revision = command(["git", "-C", str(MATHLIB), "rev-parse", "HEAD"], ORACLE)
    compile_run = command(["env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0", "lake", "env", "lean", str(SOURCE)], ORACLE)
    (OWN / "compile.stdout.log").write_text(compile_run.stdout)
    (OWN / "compile.stderr.log").write_text(compile_run.stderr)
    version_ok = version.returncode == 0 and "Lean (version 4.31.0" in version.stdout
    revision_ok = revision.returncode == 0 and revision.stdout.strip() == MATHLIB_REV
    axioms_line = next((line for line in compile_run.stdout.splitlines() if "depends on axioms:" in line), "")
    axioms_ok = all(name in axioms_line for name in ("propext", "Classical.choice", "Quot.sound")) and "sorryAx" not in axioms_line
    compile_ok = compile_run.returncode == 0 and "error:" not in compile_run.stderr.lower()
    full = seals_ok and not forbidden and version_ok and revision_ok and compile_ok and axioms_ok
    record = {
        "argv": ["env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0", "lake", "env", "lean", str(SOURCE)],
        "cwd": str(ORACLE),
        "exit_code": compile_run.returncode,
        "lean_version": version.stdout.strip(),
        "mathlib_revision": revision.stdout.strip(),
        "source_sha256": sha(SOURCE),
        "forbidden_tokens": forbidden,
        "axioms_line": axioms_line,
        "seals_ok": seals_ok,
        "compile_ok": compile_ok,
        "pinned_environment_note": "Uses the pre-existing exact-revision oracle Lake environment; the broken formal_mathlib/.lake symlinks and /mnt/sn850x2t were not modified.",
    }
    (OWN / "proof_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-07-M01": full}, "domain_assumption_diff": [], "counterexample": None}, sort_keys=True))
    return 0 if full else 2


if __name__ == "__main__":
    raise SystemExit(main())
