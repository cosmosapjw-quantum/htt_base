from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.r44.run_bayes_factor_design_mock import (
    beta_mo_readout_counterexample,
    binary_gaussian_data_processing,
    common_covariance_model_experiment,
    norm_sufficiency_counterexample,
    optimize_shell_design,
    run_design_calibration,
)


def test_common_covariance_bayes_factors_are_preserved_by_score_and_full_posterior():
    out = common_covariance_model_experiment(seed=20261109, n_rep=40)
    assert out["max_abs_log_bf_error_raw_vs_score"] < 1e-9
    assert out["max_abs_log_bf_error_raw_vs_complete_posterior_mV"] < 1e-9
    assert out["mean_only_is_also_exact_when_reference_V_is_fixed"] is True


def test_fixed_covariance_score_is_not_sufficient_for_covariance_alternatives():
    out = common_covariance_model_experiment(seed=20261109, n_rep=10)
    c = out["model_dependent_covariance_counterexample"]
    assert c["same_common_score_max_abs_difference"] < 1e-8
    assert c["log_bf_difference_despite_same_q"] > 0.1


def test_beta_mo_only_vector_does_not_preserve_boost_vs_tilt_bayes_factor():
    out = beta_mo_readout_counterexample()
    assert out["beta_MO_posterior_mean_vector_gap"] < 1e-12
    assert out["global_tilt_plus_boost_M2_log_bf_gap"] > 0.05


def test_scalar_norm_sufficiency_requires_rotational_symmetry():
    out = norm_sufficiency_counterexample()
    iso = out["isotropic_control"]
    assert abs(iso["log_bfs"][0] - iso["log_bfs"][1]) < 1e-12
    aniso = out["anisotropic_equal_norm_pair"]
    assert abs(aniso["posterior_mean_norms"][0] - aniso["posterior_mean_norms"][1]) < 1e-12
    assert aniso["absolute_log_bf_difference"] > 0.3


def test_kl_and_total_variation_contract_under_deterministic_linear_compression():
    out = binary_gaussian_data_processing()
    assert out["compressed_kl_P1T_P0T"] <= out["raw_kl_P1_P0"]
    assert out["compressed_total_variation"] <= out["raw_total_variation"]


def test_c_optimal_design_targets_beta_rm_minus_beta_mo_better_than_d_optimal():
    out = optimize_shell_design()
    a = out["allocations"]
    assert a["c_optimal"]["optimizer_success"]
    assert a["d_optimal"]["optimizer_success"]
    assert a["c_optimal"]["target_variance"] < a["d_optimal"]["target_variance"]
    assert a["no_independent_beta_MO_anchor"]["rank"] == 1
    assert np.isfinite(a["c_optimal"]["target_sigma"])


def test_sampling_from_each_design_recovers_nominal_contrast_coverage():
    out = optimize_shell_design()
    cal = run_design_calibration(out, seed=20261110, n_rep=400)
    for name in ("uniform", "c_optimal", "d_optimal"):
        assert 0.90 <= cal[name]["coverage_95"] <= 0.99
