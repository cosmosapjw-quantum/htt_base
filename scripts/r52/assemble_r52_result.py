"""Assemble R52_RESULT.json and joint_posterior_summary.json from R52 products.

Run: python scripts/r52/assemble_r52_result.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R52"


def exit_code(log: Path):
    m = re.findall(r"^exit=(\d+)$", log.read_text(errors="replace"), flags=re.M)
    return int(m[-1]) if m else None


def main() -> None:
    r = json.loads((D / "R52_JOINT_RESULT.json").read_text())
    rev = json.loads((D / "INDEPENDENT_REVIEW.json").read_text())
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    diff = subprocess.run(["git", "diff", "HEAD"], cwd=ROOT, capture_output=True).stdout
    b, p = r["baseline"], r["physical"]
    summary = {"theta": r["theta"], "posterior_mean": b["posterior_mean"], "posterior_sd": b["posterior_sd"],
               "prior_sd": r["scale"], "prior_dominated": b["prior_dominated"], "likelihood_rank": b["likelihood_rank"],
               "block_ranks": b["block_ranks"], "ppc": b["ppc_at_posterior_mean"], "cobaya": r["cobaya"],
               "stacked_gls_check": r["stacked_gls_check"]}
    (D / "joint_posterior_summary.json").write_text(json.dumps(summary, indent=1, allow_nan=False) + "\n")
    doc = {
        "node_id": "R52", "status": "complete_scoped", "claim_tier": "C0", "owner": "htt",
        "transfer_source": "R51 source-bound/conditional operators; no native solver",
        "source_git_sha": head, "dirty_patch_sha256_at_assembly": hashlib.sha256(diff).hexdigest(),
        "input_sha256": r["input_sha256"],
        "conventions": "beta_RM = v_R - v_M, beta_MO = v_O - v_M (first order, common Galactic triad); CMB dipole = beta_MO - beta_RM; counts = c_EB beta_MO; CF4 source bulk = -c beta_RM; sigma/H0, omega/H0 today (matter congruence); A/(c H0) matter 4-acceleration",
        "actual_commands": {
            "tests": ["PYTHONPATH=htt/src:htt:. python -m pytest tests/r49 tests/r50 tests/r51 tests/r52 -q", exit_code(D / "logs/test_log.txt")],
            "observed_run": ["PYTHONPATH=htt/src:htt:. python scripts/r52/run_r52_joint.py", exit_code(D / "logs/run_r52_joint.log")],
            "superseded_runs": ["logs/run_r52_joint_attempt1_unconverged_cobaya.log", "logs/run_r52_joint_attempt2_prereview_signbug.log"],
        },
        "identification": {"likelihood_rank": b["likelihood_rank"], "block_ranks": b["block_ranks"],
                           "null_directions": "omega (3): no source-bound response (Gaia B1 degenerate with frame spin)",
                           "A": "rank 3 in baseline but rank 0 with a CF4 directional calibration-dipole nuisance -> not physically identified",
                           "per_depth": "each CF4 window alone nearly degenerate between A and beta_RM (3 weak eigenvalues); depth dependence across windows separates them"},
        "results": {
            "beta_MO_kms": p["beta_MO_kms"], "beta_MO_sd_kms": p["beta_MO_sd_kms"],
            "frame_offset_beta_RM0_kms": p["beta_RM0_kms"], "frame_offset_beta_RM0_sd_kms": p["beta_RM0_sd_kms"],
            "frame_offset_zero_wald_measurement_cov_only": p["beta_RM0_zero_wald"],
            "frame_offset_wald_with_bulk_cosmic_variance_250kms": r["sensitivity"]["cf4_bulk_250kms"]["beta_RM0_zero_wald"],
            "frame_offset_wald_with_cf4_calibration_dipole": r["sensitivity"]["cf4_calibration_dipole"]["beta_RM0_zero_wald"],
            "counts_vs_cf4_consistency": r["counts_vs_cf4_tension"],
            "sigma_over_H0": p["sigma_over_H0"], "sigma_over_H0_sd": p["sigma_over_H0_sd"],
            "A_over_cH0": p["A_over_cH0"], "A_over_cH0_sd": p["A_over_cH0_sd"],
            "gaia_K_eff": r["meta"]["gaia"]["K_eff_information_weighted"],
            "ppc": b["ppc_at_posterior_mean"],
        },
        "interpretation": p["interpretation"],
        "cross_probe_independence": "count dipoles: correlated-clustering rho=0.5 case; CF4 bulk cosmic variance 150/250 km/s cases; leave-one-probe-out; Pantheon+ excluded (shared hosts/field with CF4)",
        "five_views": r["five_views"],
        "independent_review": {"path": "INDEPENDENT_REVIEW.json", "verdict_before_fixes": rev["verdict_before_fixes"], "closeout": rev["closeout"]},
        "unresolved": [
            "count-dipole systematics budget (clustering dipole, x/alpha/c_EB) not modelled beyond sensitivity",
            "CF4 covariance is a stipulated conditional law; CF4 adequacy fails (PPC)",
            "Gaia E2 residual unexplained by Bianchi-I shear (chi2 110/5): E2 systematics or nuisance incompleteness",
            "Gaia K_eff uses information weights, not the carrier estimator weights",
            "omega unidentified; A degenerate with distance-calibration dipole",
            "no same-estimator joint velocity null; Pi unavailable",
        ],
        "next_node": "R53",
    }
    (D / "R52_RESULT.json").write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
