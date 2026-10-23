"""Narrow numerical checks for the R23 conditional distance factor."""

import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from distance_factor import (extract_selected_rows, gaussian_distance_logpdf,
                             marked_log_probability, selected_joint_loglik)


def test_actual_selected_cohort_identity_and_missing_mass():
    rows, marks = extract_selected_rows()
    assert len(rows) == 274
    assert marks["undefined"] == 354
    assert sum(sum(pair) for pair in marks["counts"]) == 628
    assert sum(pair[1] for pair in marks["counts"]) == len(rows)
    assert {row["outcome"] for row in rows} == {
        "accepted", "other_quality", "confused", "nondetection"}
    assert all(row["e_DMbest_mag"] > 0 and row["e_logWmxi"] > 0 for row in rows)


def test_density_normalizes_and_missing_marks_integrate():
    counts = np.array([[1, 1], [0, 0], [0, 0], [0, 0]], dtype=int)
    probabilities = np.array([[0.4, 0.6], [0, 0], [0, 0], [0, 0]])
    # Eight Gaussian standard deviations contain all but ~1.3e-15 mass.
    integral, error = quad(lambda y: math.exp(gaussian_distance_logpdf(
        [y], [0.7], [[0.25]])), -3.3, 4.7, epsabs=1e-12, epsrel=1e-12)
    assert abs(integral - 1) < 1e-10 and error < 1e-10
    assert math.exp(selected_joint_loglik(counts, probabilities, [0.7], [0.7],
                                          [[0.25]]) -
                    gaussian_distance_logpdf([0.7], [0.7], [[0.25]])) == pytest.approx(0.24)
    assert marked_log_probability(counts, probabilities) == pytest.approx(math.log(0.24))


def test_one_total_covariance_and_whole_group_mock_coverage():
    # Constructed covariance only; it is not a fitted CF4 calibration/PV law.
    rng = np.random.default_rng(42323)
    groups = np.repeat(np.arange(8), 4)
    n = len(groups)
    error = np.linspace(0.2, 0.5, n)
    group_design = (groups[:, None] == np.arange(8)).astype(float)
    covariance = np.diag(error ** 2) + 0.07 ** 2 * np.ones((n, n)) + \
        0.11 ** 2 * group_design @ group_design.T
    mean = np.linspace(31, 35, n)
    truth = 0.13
    precision_ones = np.linalg.solve(covariance, np.ones(n))
    variance = 1 / precision_ones.sum()
    draws = mean[:, None] + truth + np.linalg.cholesky(covariance) @ rng.normal(size=(n, 4096))
    estimates = precision_ones @ (draws - mean[:, None]) * variance
    z = norm.ppf(0.95)
    coverage = np.mean(abs(estimates - truth) <= z * math.sqrt(variance))
    assert abs(coverage - 0.90) < 0.025
    assert gaussian_distance_logpdf(draws[:, 0], mean + truth, covariance) == pytest.approx(
        gaussian_distance_logpdf(draws[:, 0], mean + truth, covariance.T))
    with pytest.raises(np.linalg.LinAlgError):
        gaussian_distance_logpdf([0, 0], [0, 0], [[1, 2], [2, 1]])
