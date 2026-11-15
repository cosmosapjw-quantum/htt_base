"""Acceptance Test 13 & GBI-07/GBI-08 verification: Matrix A..I, 4-chain Rhat/ESS, 5-views, MIO G19, PPC/LOPO, & no-overclaim."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

WORKTREE_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(WORKTREE_ROOT / "htt"), str(WORKTREE_ROOT / "htt" / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
if str(WORKTREE_ROOT) not in sys.path:
    sys.path.append(str(WORKTREE_ROOT))

from common.semantic_guards.no_overclaim import scan_paths
from htt.infer.r49_general_bianchi_likelihood import (
    PARAM_NAMES_24,
    SplitPosteriorFiveViewError,
    compute_r49_htt_five_views_from_posterior,
)
from scripts.r49.run_r49_production_inference_and_benchmark import (
    ALL_PROBES,
    CHAINS_OUT_NPZ,
    R49_DOC_DIR,
    compute_vehtari_diagnostics,
)

GBI07_RECEIPT = R49_DOC_DIR / "GBI07_ADVERSARIAL_BENCHMARK_RECEIPT.json"
GBI08_RECEIPT = R49_DOC_DIR / "GBI08_PRODUCTION_INFERENCE_RECEIPT.json"
RUNNER_SCRIPT = WORKTREE_ROOT / "scripts" / "r49" / "run_r49_production_inference_and_benchmark.py"


def _forbid_posterior_keys(obj: object) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert "posterior" not in str(k).lower(), f"Forbidden key containing 'posterior' in MIO payload: {k}"
            _forbid_posterior_keys(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _forbid_posterior_keys(item)


def test_gbi07_matrix_a_through_i_synthetic_and_degeneracies() -> None:
    assert GBI07_RECEIPT.exists(), f"Missing GBI-07 receipt: {GBI07_RECEIPT}"
    rec = json.loads(GBI07_RECEIPT.read_text())

    assert rec["cmb_lane"] == "PR3_CALIBRATED"
    assert rec["cmb_mc_source"] == "FFP10_PR3"

    matrix = rec["competitor_matrix"]
    expected_competitors = {
        "A_ISOTROPIC_LCDM",
        "B_PURE_LOCAL_BOOST",
        "C_PURE_GLOBAL_SHEAR_UNTILT",
        "D_TILTED_BIANCHI_I",
        "E_TILTED_BIANCHI_V",
        "F_TILTED_BIANCHI_VII0",
        "G_TILTED_BIANCHI_VIIH",
        "H_TILTED_BIANCHI_IX",
        "I_NON_FLRW_GEODESIC_ENVELOPE",
    }
    assert set(matrix.keys()) == expected_competitors
    for cname, entry in matrix.items():
        assert np.isfinite(entry["log_likelihood_map"]), cname
        assert np.isfinite(entry["log_z_laplace"]), cname
        assert np.isfinite(entry["log_z_is"]), cname
        assert np.isfinite(entry["delta_log_z_vs_A"]), cname
        assert np.isfinite(entry["delta_log_z_vs_B"]), cname

    geo = matrix["I_NON_FLRW_GEODESIC_ENVELOPE"]
    assert geo["transfer_mode"] == "exact_geodesic_background"
    assert set(geo["envelope_families"]) == {"II", "III", "IV", "VI_0", "VI_h", "VIII"}
    for fam in ("II", "III", "IV", "VI_0", "VI_h", "VIII"):
        assert np.isfinite(geo["per_family_geodesic"][fam]["log_z_laplace"])

    syn = rec["synthetic_injection_recovery"]
    assert set(syn.keys()) == {"A", "B", "C", "D", "E", "G"}
    for code, entry in syn.items():
        assert entry["max_scaled_map_error"] < 2.0, f"High MAP error on synthetic {code}: {entry}"
    # Strong synthetic signals must distinguish planted boost/shear/curved models over isotropic LCDM A
    assert syn["B"]["delta_log_z_planted_minus_A"] > 10.0
    assert syn["C"]["delta_log_z_planted_minus_A"] > 10.0
    assert syn["D"]["delta_log_z_planted_minus_A"] > 10.0
    assert syn["G"]["delta_log_z_planted_minus_A"] > 10.0

    deg = rec["degeneracy_limits"]
    assert deg["vii0_to_i_alm_norm_diff"] < 1.0e-7
    assert deg["ix_to_i_alm_norm_diff"] < 1.0e-6
    assert deg["viih_h1e4_to_v_alm_norm_diff"] < 1.0e-3

    reg = rec["htt_regime_comparison"]
    for key in ("wins", "ties", "loses", "not_comparable"):
        assert len(reg[key].strip()) > 20


def test_acceptance_13_gbi08_chains_five_views_mio_ppc_lopo_and_adjudication() -> None:
    assert GBI08_RECEIPT.exists(), f"Missing GBI-08 receipt: {GBI08_RECEIPT}"
    assert CHAINS_OUT_NPZ.exists(), f"Missing external MCMC chains NPZ: {CHAINS_OUT_NPZ}"

    rec = json.loads(GBI08_RECEIPT.read_text())
    assert rec["claim_tier"] == "TRANSFER_CONDITIONAL_OBSERVATIONAL_FRAMEWORK"
    assert rec["cobaya_wrapper_parity_err"] < 1.0e-11

    mcmc = rec["mcmc"]
    assert mcmc["n_chains"] == 4
    assert mcmc["max_split_rhat"] < 1.05
    assert mcmc["min_ess_bulk"] >= 400.0
    assert mcmc["min_ess_tail"] >= 400.0

    # Independently recompute Vehtari diagnostics directly from external raw chains NPZ
    z = np.load(CHAINS_OUT_NPZ, allow_pickle=False)
    chains = np.asarray(z["chains"], dtype=np.float64)
    assert chains.ndim == 3 and chains.shape[0] == 4 and chains.shape[2] == 24
    # Chains must be distinct trajectories (no duplicated chain trick)
    for c_i in range(1, 4):
        assert not np.allclose(chains[0], chains[c_i]), "Duplicate MCMC chains detected"

    diag = compute_vehtari_diagnostics(chains)
    assert float(np.max(diag["split_rhat"])) == pytest.approx(mcmc["max_split_rhat"], rel=1.0e-6)
    assert float(np.min(diag["ess_bulk"])) == pytest.approx(mcmc["min_ess_bulk"], rel=1.0e-6)
    assert float(np.min(diag["ess_tail"])) == pytest.approx(mcmc["min_ess_tail"], rel=1.0e-6)
    assert float(np.max(diag["split_rhat"])) < 1.05
    assert float(np.min(diag["ess_bulk"])) >= 400.0
    assert float(np.min(diag["ess_tail"])) >= 400.0
    assert set(rec["parameter_posterior_24d"].keys()) == set(PARAM_NAMES_24)

    # One-posterior 5-views check + live SplitPosteriorFiveViewError check
    fv = rec["htt_five_views_single_posterior"]
    assert fv["split_posterior_guard_verified"] is True
    assert fv["G_F_depth"]["cov_min_eig"] > 0.0
    assert fv["G_F_depth"]["n_contrasts"] >= 3
    thinned = np.asarray(z["posterior_draws_thinned"], dtype=np.float64)
    with pytest.raises(SplitPosteriorFiveViewError):
        compute_r49_htt_five_views_from_posterior(thinned, split_draws_for_q=thinned)

    # Scalar x_C ablation check
    xc = rec["scalar_xc_ablation"]
    assert np.isfinite(xc["scalar_x_C_mean"])
    assert np.isfinite(xc["vector_beta_MO_mean_norm"])

    # MIO diagnostic-only & G19 firewall checks
    mio = rec["mio_diagnostic_certificate"]
    assert mio["reduction_status"] == "diagnostic-only"
    assert mio["as_posterior_bundle_blocked"] is True
    _forbid_posterior_keys(mio["payload"])

    # PPC & LOPO across all 8 probes
    ppc = rec["ppc_per_probe"]
    lopo = rec["lopo_heldout_predictive"]
    assert set(ppc.keys()) == set(ALL_PROBES)
    assert set(lopo.keys()) == set(ALL_PROBES)
    for p_name in ALL_PROBES:
        assert ppc[p_name]["dof"] >= 3
        assert np.isfinite(ppc[p_name]["chi2_per_dof"])
        assert 0.0 <= ppc[p_name]["ppc_pvalue"] <= 1.0
        assert np.isfinite(lopo[p_name]["elpd_lopo_G_tilted_viih"])
        assert np.isfinite(lopo[p_name]["elpd_lopo_B_pure_boost"])
        assert np.isfinite(lopo[p_name]["elpd_lopo_A_lcdm"])

    # NPIPE PR4 & RACS sensitivity checks (strict isolation)
    npipe_sens = rec["sensitivity_lanes"]["npipe_pr4_isolated"]
    assert npipe_sens["cmb_lane"] == "NPIPE_PR4_ROBUSTNESS"
    assert npipe_sens["mc_source"] == "PR4_NULL_NOT_FORMABLE"
    assert npipe_sens["pr3_sims_used"] is False
    assert np.isfinite(npipe_sens["max_shift_sigma_24d"])
    assert np.isfinite(rec["sensitivity_lanes"]["racs_unflagged_raw_variance"]["max_shift_sigma_24d"])

    # Equivalence-set adjudication without family overclaim
    adj = rec["equivalence_set_adjudication"]
    assert adj["family_level_discrimination_claimed"] is False
    assert set(adj["equivalence_classes"].keys()) == {
        "FLAT_K0_FLRW_LIMIT",
        "OPEN_KNEG_FLRW_LIMIT",
        "CLOSED_KPOS_FLRW_LIMIT",
        "NON_FLRW_LIMIT_GEODESIC",
    }
    assert adj["highest_evidence_equivalence_class"] in adj["equivalence_classes"]


def test_no_overclaim_guard_clean_across_r49_outputs() -> None:
    issues = scan_paths([GBI07_RECEIPT, GBI08_RECEIPT, RUNNER_SCRIPT, Path(__file__)])
    assert issues == (), f"Semantic no-overclaim issues detected: {issues}"
