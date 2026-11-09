from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.r45.run_model_posterior_information_loss import (
    common_covariance_experiment,
    covariance_change_experiment,
    parameter_vs_model_information_experiment,
    radial_and_directional_experiment,
)


def test_common_covariance_k_minus_one_discriminant_scores_preserve_model_posterior():
    result = common_covariance_experiment(n_rep=3000, seed=101)
    exact = result["exact_common_covariance_discriminant_score"]
    lossy = result["lossy_one_score_projection"]
    assert exact["expected_posterior_kl_direct"] < 1e-10
    assert exact["expected_posterior_tv"] < 1e-10
    assert lossy["expected_posterior_kl_direct"] > 1e-3
    identity_mcse = np.hypot(lossy["posterior_kl_mcse"], lossy["mi_information_difference_mcse"])
    assert lossy["chain_rule_identity_absolute_discrepancy"] < 5.0 * identity_mcse


def test_model_dependent_covariance_requires_quadratic_information():
    result = covariance_change_experiment(n_rep=4000, seed=202)
    mean_only = result["mean_only_summary"]
    exact_lr = result["exact_log_likelihood_ratio_summary"]
    assert mean_only["expected_posterior_kl_direct"] > 1e-3
    assert exact_lr["expected_posterior_kl_direct"] < 1e-10
    assert exact_lr["expected_posterior_tv"] < 1e-10


def test_norm_can_destroy_direction_but_be_exact_for_radial_scale_models():
    result = radial_and_directional_experiment(n_rep=4000, seed=303)
    directional = result["directional_signal"]
    radial = result["radial_scale_control"]
    assert directional["expected_posterior_kl_direct"] > 1e-2
    assert abs(directional["summary_model_information_nats"]) < 1e-12
    assert radial["expected_posterior_kl_direct"] < 1e-10


def test_model_index_and_continuous_parameter_posterior_losses_are_distinct():
    result = parameter_vs_model_information_experiment(n_rep=12000, seed=404)
    case_a = result["case_A_model_index_preserved_parameter_posterior_lost"]
    case_b = result["case_B_within_model_parameter_sufficient_but_model_index_lost"]
    assert case_a["model_index_information_loss"]["expected_posterior_kl_direct"] < 1e-10
    assert abs(case_a["within_model_parameter_posterior_information_loss_nats"] - 0.5 * np.log(2.0)) < 0.025
    assert case_b["model_index_information_loss"]["expected_posterior_kl_direct"] > 1e-2
    assert case_b["within_model_parameter_posterior_information_loss_nats"] == 0.0


def test_risk_and_pinsker_bounds_hold_with_monte_carlo_margin():
    result = common_covariance_experiment(n_rep=25000, seed=505)
    for key in ("lossy_one_score_projection",):
        m = result[key]
        bound = m["pinsker_expected_tv_upper_bound_from_direct_loss"]
        assert m["expected_posterior_tv"] <= bound + 5 * m["posterior_tv_mcse"]
        assert m["bayes_risk_increase"] >= -5 * m["risk_gap_mcse"]
        assert m["bayes_risk_increase"] <= m["expected_posterior_tv"] + 5 * m["posterior_tv_mcse"]
