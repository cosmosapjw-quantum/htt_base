from __future__ import annotations

import numpy as np
import pytest

from bass.likelihood.observer_frame_adapter import (
    DeltaObserverBoostPrior,
    FlatObserverBoostPrior,
    GaussianObserverBoostPrior,
    ObserverFrameLikelihood,
)
from bass.observer.discriminator import ObservedSpectrumDataset
from bass.observer.observer_boost import ObserverBoost


def _dataset(amplitude: float = 0.0) -> ObservedSpectrumDataset:
    ell = np.arange(10, dtype=float)
    spectra = {
        "TT": 12.0 / (ell + 1.0),
        "EE": 2.0 / (ell + 1.0),
        "TE": 0.8 / (ell + 1.0),
        "BB": np.zeros(ell.size, dtype=float),
    }
    return ObservedSpectrumDataset(
        spectra=spectra,
        axis_vector=np.array([0.0, 0.0, 1.0]),
        amplitude=amplitude,
    )


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"amplitude": 0.0},
        {"axis_vector": np.array([0.0, 0.0, 1.0])},
        {"spectra_TT": np.linspace(1.0, 0.2, 10)},
        {
            "spectra_TT": np.linspace(1.0, 0.2, 10),
            "spectra_EE": np.linspace(0.5, 0.1, 10),
        },
    ],
)
def test_fb86_delta_prior_at_zero_matches_cosmological_frame(params: dict[str, object]) -> None:
    dataset = _dataset(amplitude=0.0)
    adapter = ObserverFrameLikelihood(
        cosmo_likelihood=dataset.cosmo_likelihood,
        boost_prior=DeltaObserverBoostPrior(ObserverBoost(rapidity=0.0)),
    )
    assert adapter.log_prob(dict(params)) == pytest.approx(
        dataset.cosmo_likelihood.log_prob(dict(params)),
        rel=1.0e-15,
        abs=1.0e-15,
    )


@pytest.mark.parametrize(
    "boost",
    [
        ObserverBoost(rapidity=0.0),
        ObserverBoost(rapidity=float(np.arctanh(6.0e-4)), v_hat=(0.0, 0.0, 1.0)),
        ObserverBoost(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0)),
    ],
)
def test_fb86_profile_boost_recovers_best_candidate(boost: ObserverBoost) -> None:
    dataset = _dataset(amplitude=boost.velocity)
    support = (
        ObserverBoost(rapidity=0.0, v_hat=(0.0, 0.0, 1.0)),
        boost,
        ObserverBoost(rapidity=float(np.arctanh(8.0e-4)), v_hat=(1.0, 0.0, 0.0)),
    )
    adapter = ObserverFrameLikelihood(
        cosmo_likelihood=dataset.cosmo_likelihood,
        boost_prior=FlatObserverBoostPrior(support),
    )
    best_logp, best_boost = adapter.profile_boost({"boost_grid": support})
    assert np.isfinite(best_logp)
    assert best_boost == boost or boost == ObserverBoost(rapidity=0.0)


@pytest.mark.parametrize(
    "support",
    [
        (ObserverBoost(rapidity=0.0),),
        (
            ObserverBoost(rapidity=0.0),
            ObserverBoost(rapidity=float(np.arctanh(6.0e-4))),
        ),
        (
            ObserverBoost(rapidity=0.0),
            ObserverBoost(rapidity=float(np.arctanh(6.0e-4))),
            ObserverBoost(rapidity=float(np.arctanh(1.23e-3))),
        ),
    ],
)
def test_fb86_marginalise_boost_returns_finite_value(
    support: tuple[ObserverBoost, ...],
) -> None:
    dataset = _dataset(amplitude=0.0)
    adapter = ObserverFrameLikelihood(
        cosmo_likelihood=dataset.cosmo_likelihood,
        boost_prior=FlatObserverBoostPrior(support),
    )
    value = adapter.marginalise_boost({"boost_grid": support})
    assert np.isfinite(value)


def test_fb86_delta_prior_marginalisation_equals_log_prob() -> None:
    dataset = _dataset(amplitude=0.0)
    prior = DeltaObserverBoostPrior(ObserverBoost(rapidity=0.0))
    adapter = ObserverFrameLikelihood(
        cosmo_likelihood=dataset.cosmo_likelihood,
        boost_prior=prior,
    )
    params: dict[str, object] = {}
    assert adapter.marginalise_boost(params) == pytest.approx(
        adapter.log_prob(params),
        rel=1.0e-15,
        abs=1.0e-15,
    )


@pytest.mark.parametrize("beta_obs", [0.0, 6.0e-4, 1.23e-3, 2.0e-3])
def test_fb86_explicit_beta_obs_parses_without_observer_boost_object(beta_obs: float) -> None:
    dataset = _dataset(amplitude=beta_obs)
    adapter = ObserverFrameLikelihood(
        cosmo_likelihood=dataset.cosmo_likelihood,
        boost_prior=FlatObserverBoostPrior(
            (
                ObserverBoost(rapidity=0.0),
                ObserverBoost(rapidity=float(np.arctanh(min(beta_obs, 0.9)))),
            )
        ),
    )
    value = adapter.log_prob({"beta_obs": beta_obs, "v_hat_obs": (0.0, 0.0, 1.0)})
    assert np.isfinite(value)


def test_fb86_gaussian_prior_support_points_have_expected_count() -> None:
    prior = GaussianObserverBoostPrior(
        mean=ObserverBoost(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0)),
        sigma_rapidity=float(np.arctanh(1.23e-3)),
        num_points=9,
    )
    assert len(prior.support_points()) == 9


def test_fb86_gaussian_prior_peaks_at_mean() -> None:
    mean = ObserverBoost(rapidity=float(np.arctanh(1.23e-3)), v_hat=(0.0, 0.0, 1.0))
    prior = GaussianObserverBoostPrior(
        mean=mean,
        sigma_rapidity=5.0e-4,
        num_points=7,
    )
    shifted = ObserverBoost(rapidity=mean.rapidity + 5.0e-4, v_hat=mean.v_hat)
    assert prior.log_prob(mean) > prior.log_prob(shifted)


@pytest.mark.parametrize("bad_num_points", [0, 1])
def test_fb86_gaussian_prior_rejects_too_small_support_grid(bad_num_points: int) -> None:
    with pytest.raises(ValueError):
        GaussianObserverBoostPrior(
            mean=ObserverBoost(rapidity=0.0),
            sigma_rapidity=1.0e-3,
            num_points=bad_num_points,
        )


@pytest.mark.parametrize("bad_sigma", [0.0, -1.0e-3, np.nan])
def test_fb86_gaussian_prior_rejects_invalid_sigma(bad_sigma: float) -> None:
    with pytest.raises(ValueError):
        GaussianObserverBoostPrior(
            mean=ObserverBoost(rapidity=0.0),
            sigma_rapidity=float(bad_sigma),
        )


def test_fb86_invalid_boost_grid_entries_are_rejected() -> None:
    dataset = _dataset()
    adapter = ObserverFrameLikelihood(
        cosmo_likelihood=dataset.cosmo_likelihood,
        boost_prior=FlatObserverBoostPrior(),
    )
    with pytest.raises(TypeError):
        adapter.profile_boost({"boost_grid": (object(),)})


def test_fb86_docstring_keeps_wrapper_scope_pin() -> None:
    doc = ObserverFrameLikelihood.__doc__ or ""
    assert "wraps an FB-7 cosmological-frame likelihood" in doc
