from __future__ import annotations

import numpy as np
import pytest

from bass.inference import (
    ESS_THRESHOLD,
    GEWEKE_ABS_Z_THRESHOLD,
    R_HAT_THRESHOLD,
    convergence_report,
    ess,
    geweke,
    r_hat,
    trace_plot_data,
)


def _iid_samples(seed: int, *, n_chains: int = 4, n_draws: int = 256, n_dim: int = 3) -> np.ndarray:
    return np.random.default_rng(seed).normal(size=(n_chains, n_draws, n_dim))


def _biased_samples() -> np.ndarray:
    samples = _iid_samples(7, n_chains=4, n_draws=256, n_dim=2)
    samples[0, :, 0] += 0.8
    return samples


def _ar1_samples(phi: float, seed: int, *, n_chains: int = 4, n_draws: int = 256, n_dim: int = 2) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.zeros((n_chains, n_draws, n_dim), dtype=float)
    noise = rng.normal(size=out.shape)
    for chain in range(n_chains):
        for dim in range(n_dim):
            for index in range(1, n_draws):
                out[chain, index, dim] = phi * out[chain, index - 1, dim] + noise[chain, index, dim]
    return out


def test_fb114_threshold_constants_are_frozen() -> None:
    assert R_HAT_THRESHOLD == 1.01
    assert ESS_THRESHOLD == 400.0
    assert GEWEKE_ABS_Z_THRESHOLD == 2.0


@pytest.mark.parametrize("n_dim", [1, 2, 4, 6])
def test_fb114_r_hat_is_close_to_one_for_stationary_iid_chains(n_dim: int) -> None:
    values = r_hat(_iid_samples(1 + n_dim, n_dim=n_dim))
    assert np.all(values < 1.01)


def test_fb114_r_hat_detects_biased_chain() -> None:
    values = r_hat(_biased_samples())
    assert values[0] > 1.01


@pytest.mark.parametrize("phi", [0.0, 0.25, 0.5])
def test_fb114_ess_is_large_for_weakly_correlated_chains(phi: float) -> None:
    values = ess(_ar1_samples(phi, 4, n_draws=512))
    assert np.all(values > 400.0)


@pytest.mark.parametrize("phi", [0.8, 0.9, 0.95])
def test_fb114_ess_detects_strong_autocorrelation(phi: float) -> None:
    values = ess(_ar1_samples(phi, 5))
    assert np.any(values < 400.0)


def test_fb114_geweke_is_small_for_stationary_chains() -> None:
    values = geweke(_iid_samples(6))
    assert np.all(np.abs(values) < 2.0)


def test_fb114_geweke_detects_drift() -> None:
    samples = _iid_samples(8, n_chains=4, n_draws=256, n_dim=2)
    samples[:, -64:, 1] += 3.0
    values = geweke(samples)
    assert abs(values[1]) > 2.0


def test_fb114_trace_plot_payload_has_expected_shapes() -> None:
    samples = _iid_samples(9, n_chains=4, n_draws=128, n_dim=3)
    payload = trace_plot_data(samples)
    assert np.asarray(payload["mean_by_step"]).shape == (128, 3)
    assert np.asarray(payload["std_by_step"]).shape == (128, 3)
    assert np.asarray(payload["chain_means"]).shape == (4, 3)


def test_fb114_convergence_report_passes_good_chains() -> None:
    report = convergence_report(_iid_samples(10, n_chains=4, n_draws=512, n_dim=2))
    assert report["converged"] is True


def test_fb114_convergence_report_fails_bad_chains() -> None:
    report = convergence_report(_ar1_samples(0.97, 11, n_chains=4, n_draws=128, n_dim=2))
    assert report["converged"] is False


@pytest.mark.parametrize("bad_shape", [(4, 3), (4,), (2, 2, 2, 2)])
def test_fb114_invalid_sample_shapes_are_rejected(bad_shape: tuple[int, ...]) -> None:
    samples = np.zeros(bad_shape, dtype=float)
    with pytest.raises(ValueError):
        r_hat(samples)
