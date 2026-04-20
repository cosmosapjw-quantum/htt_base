from __future__ import annotations

import numpy as np
import pytest

from bass.observer.composition import GlobalTiltState
from bass.observer.discriminator import (
    CoverageReport,
    DiscriminatorResult,
    ObservedSpectrumDataset,
    ObserverHypothesis,
    TiltHypothesis,
    coverage_report,
    likelihood_ratio,
)
from bass.observer.observer_boost import ObserverBoost


def _base_spectra(L_max: int = 12) -> dict[str, np.ndarray]:
    ell = np.arange(L_max + 1, dtype=float)
    return {
        "TT": 20.0 / (ell + 1.0),
        "EE": 3.0 / (ell + 1.0),
        "TE": 1.2 / (ell + 1.0),
        "BB": np.zeros(L_max + 1, dtype=float),
    }


def _neutral_models() -> tuple[ObserverHypothesis, TiltHypothesis]:
    base = _base_spectra()
    obs = ObserverHypothesis(
        base_spectra=base,
        candidates=(
            ObserverBoost(rapidity=0.0, v_hat=(0.0, 0.0, 1.0)),
            ObserverBoost(rapidity=float(np.arctanh(6.0e-4)), v_hat=(0.0, 0.0, 1.0)),
            ObserverBoost(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0)),
        ),
        lambda_sigma=0.02,
    )
    tilt = TiltHypothesis(
        base_spectra=base,
        candidates=(
            GlobalTiltState(rapidity=0.0, v_hat=(0.0, 0.0, 1.0)),
            GlobalTiltState(rapidity=float(np.arctanh(6.0e-4)), v_hat=(0.0, 0.0, 1.0)),
            GlobalTiltState(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0)),
        ),
        lambda_sigma=0.02,
    )
    return obs, tilt


def _coverage_models() -> tuple[ObserverHypothesis, TiltHypothesis]:
    base = _base_spectra()
    obs = ObserverHypothesis(
        base_spectra=base,
        candidates=(
            ObserverBoost(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0)),
            ObserverBoost(rapidity=0.0, v_hat=(0.0, 0.0, 1.0)),
            ObserverBoost(rapidity=float(np.arctanh(8.0e-4)), v_hat=(1.0, 0.0, 0.0)),
        ),
        lambda_sigma=0.02,
    )
    tilt = TiltHypothesis(
        base_spectra=base,
        candidates=(
            GlobalTiltState(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0)),
            GlobalTiltState(rapidity=0.0, v_hat=(0.0, 0.0, 1.0)),
            GlobalTiltState(rapidity=float(np.arctanh(8.0e-4)), v_hat=(1.0, 0.0, 0.0)),
        ),
        lambda_sigma=0.02,
    )
    return obs, tilt


def test_fb85_discriminator_result_is_dataclass() -> None:
    assert hasattr(DiscriminatorResult, "__dataclass_fields__")


def test_fb85_coverage_report_is_dataclass() -> None:
    assert hasattr(CoverageReport, "__dataclass_fields__")


def test_fb85_zero_signal_dataset_gives_lambda_zero_and_p_half() -> None:
    dataset = ObservedSpectrumDataset(
        spectra=_base_spectra(),
        axis_vector=np.array([0.0, 0.0, 1.0]),
        amplitude=0.0,
    )
    obs, tilt = _neutral_models()
    result = likelihood_ratio(dataset, obs, tilt, seed=7)
    assert result.Lambda == pytest.approx(0.0, abs=1.0e-15)
    assert result.p_value == pytest.approx(0.5, abs=1.0e-15)


@pytest.mark.parametrize("seed", [1, 7, 42, 99, 314])
def test_fb85_likelihood_ratio_is_deterministic_for_fixed_seed(seed: int) -> None:
    dataset = ObservedSpectrumDataset(
        spectra=_base_spectra(),
        axis_vector=np.array([0.0, 0.0, 1.0]),
        amplitude=0.0,
    )
    obs, tilt = _neutral_models()
    lhs = likelihood_ratio(dataset, obs, tilt, seed=seed)
    rhs = likelihood_ratio(dataset, obs, tilt, seed=seed)
    assert lhs == rhs


@pytest.mark.parametrize("seed", [3, 11, 29])
def test_fb85_pure_kinematic_dataset_prefers_h_obs(seed: int) -> None:
    obs, tilt = _coverage_models()
    dataset = obs.simulate(obs.candidates[0], rng=np.random.default_rng(seed), noise_fraction=0.02)
    result = likelihood_ratio(dataset, obs, tilt, seed=seed)
    assert result.Lambda < 0.0
    assert result.p_value < 0.05
    assert result.boost_MLE == obs.candidates[0]


@pytest.mark.parametrize("seed", [13, 59])
def test_fb85_pure_cosmological_dataset_prefers_h_cosmo(seed: int) -> None:
    obs, tilt = _coverage_models()
    dataset = tilt.simulate(tilt.candidates[0], rng=np.random.default_rng(seed), noise_fraction=0.02)
    result = likelihood_ratio(dataset, obs, tilt, seed=seed)
    assert result.Lambda > 0.0
    assert result.tilt_MLE == tilt.candidates[0]


@pytest.mark.parametrize("seed", [2, 17, 61, 101])
def test_fb85_result_flags_convergence_and_positive_dof(seed: int) -> None:
    dataset = ObservedSpectrumDataset(
        spectra=_base_spectra(),
        axis_vector=np.array([0.0, 0.0, 1.0]),
        amplitude=0.0,
    )
    obs, tilt = _neutral_models()
    result = likelihood_ratio(dataset, obs, tilt, seed=seed)
    assert result.converged is True
    assert result.dof >= 1


@pytest.mark.parametrize("beta", [2.0e-4, 6.0e-4, 1.23e-3])
def test_fb85_stronger_kinematic_truth_pushes_lambda_more_negative(beta: float) -> None:
    base = _base_spectra()
    truth = ObserverBoost(rapidity=float(np.arctanh(beta)), v_hat=(0.0, 0.0, 1.0))
    obs = ObserverHypothesis(
        base_spectra=base,
        candidates=(
            ObserverBoost(rapidity=0.0, v_hat=(0.0, 0.0, 1.0)),
            truth,
        ),
        lambda_sigma=0.04,
    )
    tilt = TiltHypothesis(
        base_spectra=base,
        candidates=(
            GlobalTiltState(rapidity=0.0, v_hat=(0.0, 0.0, 1.0)),
            GlobalTiltState(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0)),
        ),
        lambda_sigma=0.04,
    )
    dataset = obs.simulate(truth, rng=np.random.default_rng(1234), noise_fraction=0.02)
    result = likelihood_ratio(dataset, obs, tilt, seed=1234)
    assert result.Lambda <= 0.0


def test_fb85_coverage_report_under_h_obs_passes_ks_uniformity() -> None:
    obs, tilt = _coverage_models()
    report = coverage_report(obs, tilt, hypothesis="H_obs", n_draws=500, seed=123)
    assert report.passed_99pct is True
    assert report.ks_p_value > 0.01


def test_fb85_coverage_report_under_h_cosmo_passes_ks_uniformity() -> None:
    obs, tilt = _coverage_models()
    report = coverage_report(obs, tilt, hypothesis="H_cosmo", n_draws=500, seed=321)
    assert report.passed_99pct is True
    assert report.ks_p_value > 0.01


@pytest.mark.parametrize("hypothesis", ["H_obs", "H_cosmo"])
def test_fb85_coverage_report_has_expected_vector_lengths(hypothesis: str) -> None:
    obs, tilt = _coverage_models()
    report = coverage_report(obs, tilt, hypothesis=hypothesis, n_draws=32, seed=11)
    assert report.p_values.shape == (32,)
    assert report.lambda_values.shape == (32,)


def test_fb85_invalid_hypothesis_label_is_rejected() -> None:
    obs, tilt = _coverage_models()
    with pytest.raises(ValueError):
        coverage_report(obs, tilt, hypothesis="bad", n_draws=4, seed=0)


def test_fb85_docstring_keeps_operational_formula_and_locator() -> None:
    doc = likelihood_ratio.__doc__ or ""
    assert "Lambda(data; H_obs, H_cosmo)" in doc
    assert "1007.4539" in doc
