"""Numerical and claim-boundary tests for the PR-154 hierarchy."""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import multivariate_t

from htt.infer.jwst_host_hierarchy import (
    HostPair,
    JWSTHierarchyError,
    analyze_family,
    cf4_scenario_grid,
    collapsed_gls_offset,
    contrast_covariance,
    fixed_diagonal_mean_se_bounds,
    gaussian_hierarchical_posterior,
    latent_gls_offset,
    method_cell_covariance,
    simulation_based_calibration,
    student_t_hierarchical_posterior,
    validate_pairs,
)
from htt.infer import jwst_host_hierarchy as hierarchy

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "dl_pipeline/data/jwst_host_distance_comparisons.csv"


def _families() -> dict[str, list[HostPair]]:
    with TABLE.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(line for line in handle if not line.startswith("#"))
        result: dict[str, list[HostPair]] = {}
        for row in rows:
            result.setdefault(row["dataset"], []).append(HostPair(
                dataset=row["dataset"], host=row["host"],
                method_a=row["method_a"], mu_a_mag=float(row["mu_a_mag"]),
                sigma_a_mag=float(row["sigma_a_mag"]),
                method_b=row["method_b"], mu_b_mag=float(row["mu_b_mag"]),
                sigma_b_mag=float(row["sigma_b_mag"]),
            ))
    return result


def test_sign_and_source_family_contracts_are_exact() -> None:
    families = _families()
    cchp = validate_pairs(families["cchp_trgb_jagb"], "cchp_trgb_jagb")
    shoes = validate_pairs(families["shoes_jwst_hst"], "shoes_jwst_hst")
    assert np.mean([row.delta_mag for row in cchp]) == pytest.approx(
        -0.008142857142857451)
    assert np.mean([row.delta_mag for row in shoes]) == pytest.approx(
        -0.03384615384615422)
    mutated = list(cchp)
    first = mutated[0]
    mutated[0] = HostPair(first.dataset, first.host, "TRGB", first.mu_a_mag,
                          first.sigma_a_mag, "JAGB", first.mu_b_mag,
                          first.sigma_b_mag)
    with pytest.raises(JWSTHierarchyError, match="method/sign"):
        validate_pairs(mutated, "cchp_trgb_jagb")


@pytest.mark.parametrize("dataset", ["cchp_trgb_jagb", "shoes_jwst_hst"])
def test_latent_host_and_collapsed_gls_are_algebraically_equivalent(dataset: str) -> None:
    pairs = _families()[dataset]
    assert latent_gls_offset(pairs) == pytest.approx(
        collapsed_gls_offset(pairs), abs=1e-12)


@pytest.mark.parametrize("dataset", ["cchp_trgb_jagb", "shoes_jwst_hst"])
@pytest.mark.parametrize("block", [
    "global_all_cell_factor", "method_block_factor",
    "authenticated_group_block_factor",
])
@pytest.mark.parametrize("q", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_structured_covariance_is_psd_and_preserves_method_diagonal(
        dataset: str, block: str, q: float) -> None:
    pairs = _families()[dataset]
    covariance = method_cell_covariance(pairs, q, block)
    expected = np.asarray([
        value for row in pairs for value in
        (row.sigma_a_mag ** 2, row.sigma_b_mag ** 2)
    ])
    assert np.diag(covariance) == pytest.approx(expected, abs=1e-12)
    assert np.linalg.eigvalsh(covariance).min() >= -1e-10
    assert np.linalg.eigvalsh(contrast_covariance(covariance)).min() >= -1e-10


def test_fixed_diagonal_bounds_reproduce_independent_audit() -> None:
    families = _families()
    cchp = fixed_diagonal_mean_se_bounds(families["cchp_trgb_jagb"])
    shoes = fixed_diagonal_mean_se_bounds(families["shoes_jwst_hst"])
    assert cchp["minimum_se_mag"] == 0.0
    assert cchp["independence_se_mag"] == pytest.approx(0.029509251403032014)
    assert cchp["maximum_se_mag"] == pytest.approx(0.0766360554961976)
    assert cchp["full_method_level_minimum_se_mag"] == 0.0
    assert cchp["full_method_level_maximum_se_mag"] == pytest.approx(
        0.10471428571428572
    )
    assert shoes["minimum_se_mag"] == 0.0
    assert shoes["independence_se_mag"] == pytest.approx(0.02804265559008952)
    assert shoes["maximum_se_mag"] == pytest.approx(0.09415091604207533)
    assert shoes["full_method_level_minimum_se_mag"] == 0.0
    assert shoes["full_method_level_maximum_se_mag"] == pytest.approx(
        0.12538461538461537
    )


def test_gaussian_and_student_t_posteriors_are_finite() -> None:
    pairs = _families()["cchp_trgb_jagb"]
    deltas = [row.delta_mag for row in pairs]
    covariance = np.diag([row.independence_variance_mag2 for row in pairs])
    gaussian = gaussian_hierarchical_posterior(deltas, covariance, tau_points=101)
    student = student_t_hierarchical_posterior(
        deltas, covariance, 8, delta_points=401, tau_points=101)
    assert gaussian["numerical_status"] == "PASS"
    assert student["numerical_status"] == "PASS"
    assert all(math.isfinite(value) for value in
               gaussian["delta_equal_tail_95pct_mag"])
    assert all(math.isfinite(value) for value in
               student["delta_equal_tail_95pct_mag"])


def test_gaussian_numerical_gate_fails_for_edge_concentrated_grid() -> None:
    values = np.asarray([-0.25, 0.25, -0.25, 0.25])
    covariance = np.eye(4) * 1e-6
    result = gaussian_hierarchical_posterior(
        values, covariance, tau_points=21, tau_max=0.01,
        validation_tau_max=0.50,
    )
    assert result["numerical_status"] == "NUMERICAL_GATE_FAIL"
    assert result["numerical_diagnostics"]["normalization_relative_error"] > 1e-8


def test_student_t_tau_zero_matches_independent_scipy_oracle() -> None:
    values = np.asarray([0.04, -0.02, 0.01])
    covariance = np.diag([0.01, 0.02, 0.03])
    nu = 8
    delta = np.asarray([-0.03, 0.02])
    observed = hierarchy._student_log_posterior_grid(
        values, covariance, nu, delta, np.asarray([0.0]),
        0.30, 0.10, 128,
    )[0]
    scale = (nu - 2.0) / nu * covariance
    prior = (-0.5 * np.square(delta / 0.30)
             - math.log(0.30 * math.sqrt(2.0 * math.pi)))
    tau_prior = math.log(math.sqrt(2.0 / math.pi) / 0.10)
    expected = np.asarray([
        multivariate_t.logpdf(
            values, loc=np.full(len(values), value), shape=scale, df=nu
        )
        + prior[index] + tau_prior
        for index, value in enumerate(delta)
    ])
    assert observed == pytest.approx(expected, abs=2e-10)


def test_student_t_large_nu_tends_to_gaussian_posterior() -> None:
    pairs = _families()["cchp_trgb_jagb"]
    deltas = [row.delta_mag for row in pairs]
    covariance = np.diag([row.independence_variance_mag2 for row in pairs])
    gaussian = gaussian_hierarchical_posterior(deltas, covariance, tau_points=101)
    student = student_t_hierarchical_posterior(
        deltas, covariance, 100, delta_points=401, tau_points=101,
    )
    assert student["delta_posterior_median_mag"] == pytest.approx(
        gaussian["delta_posterior_median_mag"], abs=2e-3
    )


def test_small_full_family_analysis_is_concrete_nonidentification() -> None:
    for dataset, pairs in _families().items():
        result = analyze_family(pairs, dataset, production=False)
        assert result["latent_pair_collapse_check"]["status"] == "PASS"
        assert result["group_zero_point_status"] == "GROUP_ZERO_POINT_NOT_IDENTIFIED"
        latent = result["latent_host_distance_moduli"]
        assert latent["covariance_role"] == "independence_sensitivity_only"
        assert len(latent["rows"]) == len(pairs)
        assert all(
            row["equal_tail_95pct_distance_modulus_mag"][0]
            < row["posterior_median_distance_modulus_mag"]
            < row["equal_tail_95pct_distance_modulus_mag"][1]
            for row in latent["rows"]
        )
        assert result["terminal_classification"] == "TOTAL_UNCERTAINTY_NOT_IDENTIFIED"
        assert not result["independence_sensitivity"]["primary_total_uncertainty"]
        assert result["ppc"]["gaussian"]["meaning"].endswith("only")


def test_sbc_receipt_has_frozen_rank_shape_even_in_small_smoke() -> None:
    pairs = _families()["cchp_trgb_jagb"]
    covariance = np.diag([row.independence_variance_mag2 for row in pairs])
    result = simulation_based_calibration(
        covariance, simulations=70, posterior_draws=20, seed=20260720,
        tau_points=51,
    )
    assert result["rank_bins"] == 7
    assert set(result["reports"]) == {
        "known_good", "variance_scale_0.5", "variance_scale_2.0"
    }
    assert all(len(row["rank_bins"]) == 7 for row in result["reports"].values())


def test_cf4_grid_is_scenario_only_and_never_observed() -> None:
    result = cf4_scenario_grid(
        _families()["cchp_trgb_jagb"], "cchp_trgb_jagb",
        replicates=20,
    )
    assert result["observed_nonzero_overlap_count"] == 0
    assert result["scenario_only"] is True
    assert len(result["cells"]) == 1215
    assert all(row["observed_result"] is False for row in result["cells"])
    assert all(
        row["classification"] != "MATERIAL_GAIN_SCENARIO"
        for row in result["cells"] if row["nuisance_slope_mag"] == 0.0
    )
    zero_overlap = [
        row for row in result["cells"]
        if row["verified_overlap_fraction"] == 0.0
    ]
    assert all(row["rank_deficient_fraction"] == 1.0 for row in zero_overlap)
    assert all(row["design_status"] == "BASELINE_NO_AUXILIARY_DESIGN"
               for row in zero_overlap)
    assert all(row["adjusted_interval_95pct_mag"]
               == row["baseline_interval_95pct_mag"] for row in zero_overlap)
    material = [row for row in result["cells"]
                if row["classification"] == "MATERIAL_GAIN_SCENARIO"]
    assert all(row["rmse_gain_lower_guard"] >= 0.10 for row in material)


def test_cf4_identity_errors_are_independent_bernoulli_draws() -> None:
    result = cf4_scenario_grid(
        _families()["cchp_trgb_jagb"], "cchp_trgb_jagb",
        replicates=500,
    )
    audited = [
        row for row in result["cells"]
        if row["verified_overlap_fraction"] == 1.0
        and row["identity_error_rate"] == 0.25
    ]
    assert audited
    assert all(
        abs(row["realized_identity_error_rate"] - 0.25)
        <= 5.0 * row["identity_error_rate_mc_se"]
        for row in audited
    )


def test_family_pooling_fails_contract() -> None:
    families = _families()
    pooled = families["cchp_trgb_jagb"] + families["shoes_jwst_hst"]
    with pytest.raises(JWSTHierarchyError):
        validate_pairs(pooled, "cchp_trgb_jagb")
