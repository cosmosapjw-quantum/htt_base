#!/usr/bin/env python3
"""Execute the frozen CAS11-C02 Lean axis in the existing primary checkout."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
AXIS = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C02-20260930T090559Z/lean"
SOURCE = AXIS / "FiniteGram.lean"
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas11_c02_local_start_20260930/contracts/CAS11-C02-FINITE-GRAM.json"
CONTRACT_SHA256 = "c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a"
LEAN = Path("/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lean")
PACKAGES = Path("/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages")
MATHLIB = PACKAGES / "mathlib"
MATHLIB_COMMIT = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
OBLIGATION = "CAS11-C02-FINITE-GRAM"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name: str, data: object) -> None:
    (AXIS / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def fail(message: str, code: int = 2) -> int:
    write_json("coverage.json", {"status": "INCOMPLETE", "gap": message})
    sys.stderr.write(message + "\n")
    return code


def main() -> int:
    if Path.cwd().resolve() != ROOT.resolve():
        return fail(f"Wrong cwd: {Path.cwd()}; expected {ROOT}")
    if sha256(CONTRACT) != CONTRACT_SHA256:
        return fail("Frozen contract SHA-256 mismatch")
    if not LEAN.is_file() or not SOURCE.is_file():
        return fail("Pinned Lean executable or source missing")

    packages = sorted(p for p in PACKAGES.iterdir() if p.is_dir())
    lean_paths = [p / ".lake/build/lib/lean" for p in packages]
    lean_paths = [p for p in lean_paths if p.is_dir()]
    if not (MATHLIB / ".lake/build/lib/lean/Mathlib.olean").is_file():
        return fail("Existing Mathlib.olean missing")
    commit = subprocess.run(
        ["git", "-C", str(MATHLIB), "rev-parse", "HEAD"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if commit.returncode or commit.stdout.strip() != MATHLIB_COMMIT:
        return fail("Pinned mathlib commit mismatch")

    source_text = SOURCE.read_text()
    if re.search(r"\b(sorry|admit|axiom)\b", source_text):
        return fail("Source contains a forbidden proof shortcut")
    argv = [str(LEAN), str(SOURCE.relative_to(ROOT))]
    env = os.environ.copy()
    env["LEAN_PATH"] = os.pathsep.join(map(str, lean_paths))
    manifest = {
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "wrapper_sha256": sha256(AXIS / "run_axis.py"),
        "contract": str(CONTRACT),
        "contract_sha256": CONTRACT_SHA256,
        "mathlib_commit": MATHLIB_COMMIT,
        "mathlib_manifest_sha256": sha256(MATHLIB / "lake-manifest.json"),
        "lean_path": env["LEAN_PATH"].split(os.pathsep),
        "argv": argv,
        "cwd": str(ROOT),
    }
    # This seal is written before either Lean invocation.
    write_json("source_manifest.json", manifest)
    version = subprocess.run(
        [str(LEAN), "--version"], cwd=ROOT, env=env, text=True,
        capture_output=True, check=False, timeout=90,
    )
    (AXIS / "lean_version.stdout.log").write_text(version.stdout)
    (AXIS / "lean_version.stderr.log").write_text(version.stderr)
    if version.returncode or "Lean (version 4.31.0" not in version.stdout:
        return fail("Pinned Lean 4.31.0 version invocation failed")
    try:
        proc = subprocess.run(
            argv, cwd=ROOT, env=env, text=True, capture_output=True,
            check=False, timeout=180,
        )
    except subprocess.TimeoutExpired as exc:
        (AXIS / "lean.stdout.log").write_bytes(exc.stdout or b"")
        (AXIS / "lean.stderr.log").write_bytes(exc.stderr or b"")
        write_json("execution.json", {**manifest, "exit_code": None, "timeout_seconds": 180})
        return fail("Lean compiler timed out")

    (AXIS / "lean.stdout.log").write_text(proc.stdout)
    (AXIS / "lean.stderr.log").write_text(proc.stderr)
    write_json("execution.json", {
        **manifest, "exit_code": proc.returncode,
        "lean_version": version.stdout.strip(),
        "stdout_file": str(AXIS / "lean.stdout.log"),
        "stderr_file": str(AXIS / "lean.stderr.log"),
    })
    if proc.returncode:
        return fail(f"Lean compiler exited {proc.returncode}", proc.returncode)
    if "sorryAx" in proc.stdout or "sorryAx" in proc.stderr:
        return fail("Lean axiom inspection found sorryAx")
    if "'CAS11C02.finiteGramForward' depends on axioms:" not in proc.stdout:
        return fail("Required #print axioms output missing")
    if "theorem CAS11C02.finiteGramForward :" not in proc.stdout:
        return fail("Required theorem statement printout missing")

    coverage = {
        "status": "PROVED_BY_PINNED_LEAN",
        "statement_alignment": "The matrix theorem quantifies n>0, every real PSD R, every e, epsilon>=0, and every a; its conclusion repeats PSD and proves range(R) plus the spectral pseudoinverse quadratic bound.",
        "spectral_definition": "Orthonormal eigenvector basis; diagonal inverse of each nonzero real eigenvalue; zero eigenvalues map to zero via inv_zero. PSD ensures all eigenvalues are nonnegative.",
        "branches": ["positive definite", "singular nonzero", "R=0", "epsilon=0", "epsilon>0"],
        "rank_restriction": None,
        "gaps_within_contract": [],
        "outside_contract": ["physical residual construction", "continuum bounds", "CAS11-C01", "CAS11-C03", "scientific admission"],
        "imported_mathlib_lemmas": [
            "LinearMap.IsSymmetric.eigenvectorBasis",
            "LinearMap.IsSymmetric.eigenvalues",
            "LinearMap.IsSymmetric.apply_eigenvectorBasis",
            "LinearMap.IsSymmetric.eigenvectorBasis_apply_self_apply",
            "Matrix.isSymmetric_toEuclideanLin_iff",
            "Matrix.isPositive_toEuclideanLin_iff",
            "LinearMap.IsPositive.inner_nonneg_right",
            "OrthonormalBasis.repr_apply_apply",
            "Matrix.mulVec_diagonal",
            "EuclideanSpace.inner_eq_star_dotProduct",
            "Matrix.toEuclideanLin_apply",
        ],
        "compiler_axioms": ["propext", "Classical.choice", "Quot.sound"],
    }
    write_json("coverage.json", coverage)
    payload = {
        "checks": {OBLIGATION: True},
        "domain_assumption_diff": [],
        "counterexample": None,
        "source_sha256": manifest["source_sha256"],
        "statement_alignment": coverage["statement_alignment"],
        "proof_coverage": coverage,
        "execution_file": str(AXIS / "execution.json"),
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
