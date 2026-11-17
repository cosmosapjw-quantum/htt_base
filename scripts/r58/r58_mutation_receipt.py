#!/usr/bin/env python3
"""R58 mutation gates and their receipt (same semantics as the R54 receipt of scripts/r54/build_r54_contract.py).

Each gate replaces one pattern that occurs exactly once in one source file, runs one named test, and restores the file.
KILLED means pytest exit code 1. The unmutated suite runs first; if it fails, no gate runs and the receipt is not rewritten.
The receipt stores the sha256 of every source file; tests/r58/test_r58_receipts.py fails when a source changes without a
new receipt. Never run this while another process is running or queued: sources are rewritten in place for one test each.

    python scripts/r58/r58_mutation_receipt.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117"
RECEIPT = PKG / "MUTATION_GATE_RECEIPT.json"
MOD = "htt/htt/htt/infer/r58_mixed_tensor_likelihood.py"
VIEWS = "scripts/r58/build_r58_views.py"
RUNNER = "scripts/r58/run_r58_owned_tensor.py"
BACKUP_SUFFIX = ".r58_mutation_backup"
T_LIK = "tests/r58/test_mixed_tensor_likelihood.py"
T_RUN = "tests/r58/test_owned_tensor_runner.py"

#: (id, file, pattern, mutation, test, meaning); a surviving mutation means a missing test, never a gate to delete
GATES = [
    ("G58-01", MOD, "c2 = float(stats.chi2.ppf(level, rank)) if simultaneous and rank",
     "c2 = float(stats.chi2.ppf(level, 1)) if simultaneous and rank",
     T_LIK + "::test_common_cylinder_versus_pointwise_radius",
     "simultaneous radius from chi2 with `rank` degrees of freedom replaced by one degree of freedom"),
    ("G58-02", MOD, "    return float(np.max(values))", "    return float(np.min(values))",
     T_LIK + "::test_union_interval_is_union_not_intersection_or_independent_product",
     "union-null p over the nuisance variants taken as the minimum instead of the maximum"),
    ("G58-03", VIEWS, "k[3:6,8:11]=-np.eye(3)", "k[3:6,8:11]=np.eye(3)",
     "tests/r58/test_five_views.py::test_acceleration_sign_from_incoming_null_contraction",
     "sign of the A/(cH) block in d_H flipped (k[3:6,8:11] = -I -> +I)"),
    ("G58-04", RUNNER, "        fit = mt.fit_linear(y, c, d, parameter_scale=SCALE)",
     "        fit = mt.fit_linear(y, linalg.block_diag(c[:12, :12], c[12:, 12:]), d, parameter_scale=SCALE)",
     T_RUN + "::test_existing_data_reanalysis_reproduces_frozen_marginals_and_mixed_covariance",
     "reported fit uses the block-diagonal covariance instead of the full polar-STF covariance"),
    ("G58-05", MOD, "    if rank != eq_rank:", "    if False:",
     T_LIK + "::test_disagreeing_numerical_ranks_fail_closed_before_calibrated_tests",
     "fit_linear accepts a numerically ambiguous rank (declared-scale and column-equilibrated ranks disagree) instead of failing closed"),
    ("G58-06", RUNNER, '        if fit["rank"] != 11 or approx["rank"] != 11:', "        if False:",
     T_RUN + "::test_rank_deficient_common_target_fails_closed_before_any_output",
     "runner accepts a rank-deficient common 11-coefficient target instead of failing closed"),
]
#: the unmutated suite; tests/r58/test_r58_receipts.py and test_r59_documents.py bind receipts and documents and are excluded
SUITE = (T_LIK, "tests/r58/test_five_views.py", T_RUN, "tests/r58/test_r54_repairs.py")
SOURCES = (MOD, VIEWS, RUNNER) + SUITE


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def restore_interrupted() -> list[str]:
    restored = []
    for rel in sorted({g[1] for g in GATES}):
        backup = ROOT / (rel + BACKUP_SUFFIX)
        if backup.is_file():
            (ROOT / rel).write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            backup.unlink()
            restored.append(rel)
    return restored


def main() -> int:
    env = dict(os.environ, PYTHONPATH="htt/src:htt:.", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    for rel in restore_interrupted():
        print("restored after an interrupted run:", rel)
    clean = subprocess.run([sys.executable, "-m", "pytest", *SUITE, "-q", "-p", "no:cacheprovider"], cwd=ROOT, env=env, capture_output=True, text=True)
    if clean.returncode != 0:
        tail = "\n".join((clean.stdout + clean.stderr).strip().splitlines()[-15:])
        raise SystemExit(f"R58 receipt: the unmutated suite does not pass (exit {clean.returncode}); no gate ran and the receipt was not rewritten.\n{tail}")
    rows = []
    for gid, rel, old, new, test, meaning in GATES:
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        if original.count(old) != 1:
            rows.append({"id": gid, "file": rel, "status": "INVALID_GATE", "reason": f"pattern occurs {original.count(old)} times"})
            print(gid, "INVALID_GATE")
            continue
        backup = ROOT / (rel + BACKUP_SUFFIX)
        try:
            backup.write_text(original, encoding="utf-8")
            path.write_text(original.replace(old, new), encoding="utf-8")
            run = subprocess.run([sys.executable, "-m", "pytest", test, "-q", "-x", "-p", "no:cacheprovider"], cwd=ROOT, env=env, capture_output=True, text=True)
        finally:
            path.write_text(original, encoding="utf-8")
            backup.unlink(missing_ok=True)
        rows.append({"id": gid, "file": rel, "pattern": old, "mutation": new, "test": test, "meaning": meaning,
                     "pytest_exit_code": run.returncode, "status": "KILLED" if run.returncode == 1 else "SURVIVED_OR_ERROR"})
        print(gid, rows[-1]["status"], flush=True)
    receipt = {"schema": "htt.r58.mutation_receipt/1", "unmutated_suite": list(SUITE), "unmutated_suite_exit_code": clean.returncode,
               "sources_sha256": {rel: sha(ROOT / rel) for rel in SOURCES},
               "all_killed": all(r["status"] == "KILLED" for r in rows), "gates": rows}
    RECEIPT.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    if not receipt["all_killed"]:
        raise SystemExit("R58 receipt: a gate did not kill its mutation: " + ", ".join(f"{r['id']}={r.get('pytest_exit_code', r['status'])}" for r in rows if r["status"] != "KILLED"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
