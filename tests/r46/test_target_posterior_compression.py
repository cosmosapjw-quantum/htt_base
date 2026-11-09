from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.r46.run_target_posterior_compression import (
    gaussian_kl,
    run_experiment,
)


def test_gaussian_kl_matches_closed_form_scalar_case():
    # KL[N(0,1/2)||N(0,3/4)] = 0.5*(log(3/2)-1/3).
    got = gaussian_kl(np.array([0.0]), np.array([[0.5]]), np.array([0.0]), np.array([[0.75]]))
    expected = 0.5 * (np.log(1.5) - 1.0 / 3.0)
    assert abs(got - expected) < 1e-13


def test_target_aligned_rank_two_summary_preserves_target_in_17d_model():
    result = run_experiment(n_rep=5000, seed=101)
    item = result["experiments"]["seventeen_dimensional_target_aligned"]
    assert item["target_aligned_summary_rank"] == 2
    assert item["exact_target_summary"]["expected_target_posterior_kl_nats"] < 1e-10
    assert item["exact_target_summary"]["target_mmse_risk_gap_direct"] < 1e-10
    assert item["full_latent_posterior_loss_under_exact_target_summary_nats"] > 1e-2
    assert item["one_direction_dropped_summary"]["expected_target_posterior_kl_nats"] > 1e-3
    lossy = item["one_direction_dropped_summary"]
    assert abs(lossy["target_mmse_risk_gap_direct"] - lossy["target_mmse_risk_gap_covariance_trace"]) < 5 * lossy["target_mmse_risk_gap_mcse"]
    assert item["data_processing_target_loss_le_full_loss_margin_nats"] > 0.0
    assert item["data_processing_margin_under_lossy_summary_nats"] > 0.0


def test_two_dimensional_exact_examples_match_analytic_kl_and_mmse():
    result = run_experiment(n_rep=15000, seed=202)
    item = result["experiments"]["two_dimensional_controls"]
    aligned = item["aligned_sum_target"]
    misaligned = item["misaligned_first_component_target"]
    assert aligned["expected_target_posterior_kl_nats"] < 1e-10
    assert abs(misaligned["expected_target_posterior_kl_nats"] - 0.5 * np.log(1.5)) < 0.015
    assert abs(misaligned["target_mmse_risk_gap_direct"] - 0.25) < 0.015
    assert abs(misaligned["target_mmse_risk_gap_covariance_trace"] - 0.25) < 1e-12


def test_isotropic_norm_preserves_radial_target_but_anisotropy_breaks_it():
    result = run_experiment(n_rep=3000, seed=303)
    item = result["experiments"]["radial_symmetry_and_anisotropy"]
    isotropic = item["isotropic_radial_target"]
    anisotropic = item["anisotropic_radial_counterexample"]
    assert isotropic["target_posterior_preserved"] is True
    assert isotropic["same_norm_noncentrality_mismatch_max"] < 1e-12
    assert abs(anisotropic["posterior_target_mean_difference_same_norm"] - 0.39) < 1e-12
    assert anisotropic["target_posterior_preserved_by_norm"] is False
