from __future__ import annotations

import math
from dataclasses import is_dataclass

import numpy as np
import pytest
from scipy.special import erf
from scipy.stats import kstest, norm

from bass.inference import (
    Prior,
    SUN_CMB_DIPOLE_DIRECTION,
    prior_direction,
    prior_observer_boost,
    prior_rapidity,
    prior_structure_constants,
    prior_Sigma_mnu,
)


def _half_normal_cdf(x: np.ndarray, sigma: float) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    out = np.zeros_like(arr, dtype=float)
    pos = arr > 0.0
    out[pos] = erf(arr[pos] / (sigma * math.sqrt(2.0)))
    out[arr >= np.inf] = 1.0
    return out


def test_fb111_prior_is_a_dataclass() -> None:
    assert is_dataclass(Prior)


@pytest.mark.parametrize("sigma", [5.0e-4, 1.0e-3, 2.0e-3, 5.0e-3])
def test_fb111_rapidity_samples_are_nonnegative(sigma: float) -> None:
    prior = prior_rapidity("eta", sigma=sigma)
    draws = prior.sample(np.random.default_rng(7), 1024)
    assert np.all(draws >= 0.0)


@pytest.mark.parametrize("value", [-1.0, -1.0e-12, np.nan, np.inf])
def test_fb111_rapidity_log_pdf_rejects_invalid_values(value: float) -> None:
    prior = prior_rapidity("eta", sigma=1.0e-3)
    score = float(prior.log_pdf(np.array([value]))[0])
    assert not np.isfinite(score)


@pytest.mark.parametrize("sigma", [5.0e-4, 1.0e-3, 2.0e-3])
def test_fb111_rapidity_ks_matches_half_normal(sigma: float) -> None:
    prior = prior_rapidity("eta", sigma=sigma)
    draws = prior.sample(np.random.default_rng(42), 10_000)
    result = kstest(draws, lambda value: _half_normal_cdf(np.asarray(value), sigma))
    assert result.pvalue > 1.0e-3


def test_fb111_sigma_mnu_ks_matches_half_normal() -> None:
    prior = prior_Sigma_mnu()
    draws = prior.sample(np.random.default_rng(123), 10_000)
    result = kstest(draws, lambda value: _half_normal_cdf(np.asarray(value), 0.15))
    assert result.pvalue > 1.0e-3


@pytest.mark.parametrize("seed", [1, 3, 7, 42, 99])
def test_fb111_direction_samples_are_unit_vectors(seed: int) -> None:
    prior = prior_direction()
    draws = prior.sample(np.random.default_rng(seed), 256)
    norms = np.linalg.norm(draws, axis=1)
    assert np.allclose(norms, 1.0, atol=1.0e-12, rtol=0.0)


def test_fb111_direction_log_pdf_is_constant_on_the_sphere() -> None:
    prior = prior_direction()
    draws = prior.sample(np.random.default_rng(11), 16)
    scores = prior.log_pdf(draws)
    assert np.allclose(scores, scores[0], atol=1.0e-14, rtol=0.0)


def test_fb111_direction_ks_matches_uniform_cos_theta() -> None:
    prior = prior_direction()
    draws = prior.sample(np.random.default_rng(5), 10_000)
    u = 0.5 * (draws[:, 2] + 1.0)
    result = kstest(u, "uniform")
    assert result.pvalue > 1.0e-3


def test_fb111_observer_boost_mode_is_the_planck_dipole_vector() -> None:
    prior = prior_observer_boost()
    mean = 1.23e-3 * SUN_CMB_DIPOLE_DIRECTION
    orthogonal = 1.23e-3 * np.array([SUN_CMB_DIPOLE_DIRECTION[1], -SUN_CMB_DIPOLE_DIRECTION[0], 0.0])
    assert float(prior.log_pdf(mean)[0]) > float(prior.log_pdf(orthogonal)[0])


def test_fb111_observer_boost_ks_matches_marginal_normal_projection() -> None:
    prior = prior_observer_boost()
    draws = prior.sample(np.random.default_rng(21), 10_000)
    projected = draws @ SUN_CMB_DIPOLE_DIRECTION
    z = (projected - 1.23e-3) / 1.23e-3
    result = kstest(z, "norm")
    assert result.pvalue > 1.0e-3


@pytest.mark.parametrize(
    "label",
    ["FLRW", "I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"],
)
def test_fb111_structure_prior_is_constructible_for_every_type(label: str) -> None:
    prior = prior_structure_constants(label)
    assert isinstance(prior, Prior)


@pytest.mark.parametrize("label", ["II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"])
def test_fb111_structure_prior_samples_stay_in_domain(label: str) -> None:
    prior = prior_structure_constants(label)
    low, high = prior.domain or (None, None)
    draws = prior.sample(np.random.default_rng(8), 2048)
    assert np.all(draws >= float(low))
    assert np.all(draws <= float(high))


@pytest.mark.parametrize("label", ["II", "V", "VI_h", "VII_h", "IX"])
def test_fb111_structure_prior_ks_is_uniform_in_log_space(label: str) -> None:
    prior = prior_structure_constants(label)
    low, high = prior.domain or (None, None)
    draws = prior.sample(np.random.default_rng(9), 10_000)
    u = (np.log(draws) - math.log(float(low))) / (math.log(float(high)) - math.log(float(low)))
    result = kstest(u, "uniform")
    assert result.pvalue > 1.0e-3


@pytest.mark.parametrize("label", ["FLRW", "I"])
def test_fb111_zero_dim_structure_prior_returns_empty_samples(label: str) -> None:
    prior = prior_structure_constants(label)
    draws = prior.sample(np.random.default_rng(0), 4)
    assert draws.shape == (4, 0)


def test_fb111_docstrings_keep_the_external_anchors() -> None:
    assert "Planck 2018 VI" in (prior_Sigma_mnu.__doc__ or "")
    assert "Kosowsky" in (prior_observer_boost.__doc__ or "")
