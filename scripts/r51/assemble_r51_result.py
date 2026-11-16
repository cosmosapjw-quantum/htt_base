"""Assemble R51_RESULT.json (node summary) from committed R51 products and logs.

Run: python scripts/r51/assemble_r51_result.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R51"


def exit_code(log: Path):
    m = re.findall(r"^exit=(\d+)$", log.read_text(errors="replace"), flags=re.M)
    return int(m[-1]) if m else None


def main() -> None:
    pr3 = json.loads((D / "R51_PR3_LOWELL_RESULT.json").read_text())
    review = json.loads((D / "INDEPENDENT_REVIEW.json").read_text())
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    diff = subprocess.run(["git", "diff", "HEAD"], cwd=ROOT, capture_output=True).stdout
    cal = pr3["calibration"]
    ic = pr3["interval_calibration"]
    doc = {
        "node_id": "R51",
        "status": "complete_scoped",
        "claim_tier": "C0",
        "owner": "htt",
        "transfer_source": "first-order Bianchi-I integrated-shear ISW (source-bound); no native solver",
        "source_git_sha": head,
        "dirty_patch_sha256_at_assembly": hashlib.sha256(diff).hexdigest(),
        "source_ids": pr3["input_sha256"],
        "lane": pr3["lane"],
        "commander_primary_calibration": pr3["commander_primary_calibration"],
        "equations": {
            "cmb_response": "dT/T(n) = -n^a n^b Sigma_ab, Sigma_ab = int_{t_*}^{t_0} sigma_ab dt",
            "exact_reference": "T(n)/T_bar = (n^T exp(2 Sigma) n)^{-1/2}",
            "history_operator_conditional": "Sigma = I_hist (sigma/H)_0, I_hist = int_{a_*}^1 a^-4/E(a) da",
            "finite_mc_law": "Sellentin & Heavens 2016",
            "carrier": "(F, t, Q0); Q(s) = Q0 - 2 s.t + s.F.s",
        },
        "parameter_names_units_frames_epochs": "R51_SOURCE_OPERATOR_CONTRACT.json#components",
        "law_and_nuisance_spec": {"law": "finite-MC on T45; E/B dropped (no source-bound polarization response)",
                                  "covariance": "300 SMICA FFP10 CMB+noise pairs, same masked estimator", "prior": "flat box |s_k|<=1e-3"},
        "actual_commands": {
            "baseline_pytest": ["PYTHONPATH=htt/src:htt:. python -m pytest tests/r50 htt/src/common/test_r50_optional_calibration.py tests/r42/test_five_variable_repair.py tests/r48/test_core03_repairs.py -q", exit_code(D / "logs/baseline_pytest.txt")],
            "baseline_gaia_benchmark": ["PYTHONPATH=htt/src:htt:. python scripts/r50/benchmark_owned_gaia_carrier.py", exit_code(D / "logs/baseline_gaia_benchmark_stdout.txt")],
            "tests": ["PYTHONPATH=htt/src:htt:. python -m pytest tests/r49 tests/r50 tests/r51 htt/src/common/test_r50_optional_calibration.py tests/r42/test_five_variable_repair.py tests/r48/test_core03_repairs.py -q", exit_code(D / "logs/test_log.txt")],
            "observed_run": ["PYTHONPATH=htt/src:htt:. python scripts/r51/run_r51_pr3_lowell.py", exit_code(D / "logs/run_r51_pr3_lowell.log")],
            "observed_run_prereview": ["same", exit_code(D / "logs/run_r51_pr3_lowell_run1_prereview.log")],
            "contract": ["PYTHONPATH=htt/src:htt:. python scripts/r51/build_r51_contract.py", exit_code(D / "logs/build_contract.log")],
        },
        "baseline_reuse": "R50 tests and Gaia benchmark reproduced (max abs diff 3.9e-12); not counted as new results",
        "results": {
            "Sigma_hat": pr3["Sigma_hat"], "Sigma_sd_fisher": pr3["Sigma_sd_gaussian"],
            "Sigma_sd_loo_calibrated": [s * r for s, r in zip(pr3["Sigma_sd_gaussian"], ic["loo_sampling_sd_over_fisher_sd"])],
            "zero_shear_mc_p": pr3["zero_shear_test"]["mc_same_estimator_loo"]["p_mc"],
            "Sigma_frobenius_95pct_upper_loo_calibrated": ic["Sigma_frobenius_95pct_upper_loo_calibrated"],
            "conditional_sigma_over_H0_frobenius_95pct_upper": pr3["conditional_sigma_over_H0_today"]["frobenius_norm_95pct_upper_loo_calibrated"],
            "I_hist": pr3["history_operator"]["I_hist"],
            "heldout_calibration": {k: {"cov68": v["cov68"], "cov95": v["cov95"], "rejected": v["rejected_at_bonferroni"]} for k, v in cal.items()},
            "parameter_coverage_nominal95": ic["sigma0_loo_component_coverage_nominal95"],
            "adequacy": pr3["adequacy_ppc"],
        },
        "comparisons_wins_ties_losses": {
            "tensor (F,t,Q0) vs raw 45D finite-MC": "TIE (max |dlogLR| %.1e)" % pr3["comparisons"]["tensor_carrier_F_t_Q0_finite_mc_max_abs_logLR_err"],
            "tensor vs optimal linear score": "TIE",
            "(F,t) without Q0 under finite-MC law": "LOSS for (F,t)-only (max |dlogLR| %.1f)" % pr3["comparisons"]["tensor_F_t_without_Q0_under_finite_mc_max_abs_logLR_err"],
            "tensor vs scalar fixed axis e1": "tensor WIN for 5D target; TIE for e1 marginal",
            "tensor vs power-only": "tensor WIN (power-only sign-blind)",
            "finite-MC law vs plug-in Gaussian covariance": "finite-MC WIN on heldout predictive calibration",
        },
        "checks": pr3["checks"],
        "claims": [
            {"claim": "R49 CMB path used (sigma/H)_0 as integrated shear (history operator := 1)", "status": "implementation-verified"},
            {"claim": "type-I linear ISW is the first-order term of the exact Bianchi-I redshift", "status": "derived; numerically checked"},
            {"claim": "unsourced R49 coefficients quarantined from physical likelihood", "status": "implementation-verified"},
            {"claim": "finite-MC law calibrated for the FFP10 predictive data law; plug-in Gaussian rejected", "status": "numerically checked (preregistered heldout; not blind to R49 data analysis)"},
            {"claim": "SMICA PR3 T45 integrated shear consistent with zero", "status": "numerically checked (SMICA diagnostic lane; Commander unavailable; KQ unbound <=0.25 sd)"},
            {"claim": "conditional (sigma/H)_0 bound", "status": "conditional; unquantified neutrino anisotropic-stress systematic"},
            {"claim": "HTT tensor carrier superiority over GLS/score", "status": "not claimed; tie"},
        ],
        "unresolved": [
            "Commander matched MC absent -> primary calibration unavailable",
            "kinematic-quadrupole removal contract unbound",
            "no source-bound polarization response",
            "history operator excludes neutrino anisotropic stress; finite-curvature families remain working models",
            "Gaia E2 history operator, Pantheon low-z jet, CF4 grouped likelihood, beta_MO/beta_RM separation and same-estimator velocity null -> R52",
            "Cobaya Likelihood/Theory provider extension -> R52",
        ],
        "independent_review": {"path": "INDEPENDENT_REVIEW.json", "verdict": review["verdict"]},
        "next_node": "R52",
    }
    (D / "R51_RESULT.json").write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
