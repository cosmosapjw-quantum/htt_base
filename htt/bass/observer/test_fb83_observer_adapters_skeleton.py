from __future__ import annotations

import numpy as np
import pytest

from bass.observer.aberration import aberration_kernel
from bass.observer.adapters import apply_observer_boost, observed_alm_mixing
from bass.observer.observer_boost import ObserverBoost


def _spectra(L_max: int) -> dict[str, np.ndarray]:
    ell = np.arange(L_max + 1, dtype=float)
    return {
        "TT": 10.0 / (ell + 1.0),
        "EE": 1.0 / (ell + 1.0),
        "TE": 0.5 / (ell + 1.0),
        "BB": np.zeros(L_max + 1, dtype=float),
    }


def _weighted_power_kernel(L_max: int, boost: ObserverBoost) -> np.ndarray:
    kernel = aberration_kernel(L_max, boost)
    power_kernel = kernel * kernel
    ells = np.arange(L_max + 1, dtype=float)
    shared_m_weight = (
        2.0 * np.minimum.outer(ells, ells) + 1.0
    ) / (2.0 * ells[:, None] + 1.0)
    return power_kernel * shared_m_weight


@pytest.mark.parametrize("key", ["TT", "EE", "TE", "BB"])
def test_fb83_zero_boost_preserves_spectra_exactly(key: str) -> None:
    spectra = _spectra(8)
    out = apply_observer_boost(spectra, ObserverBoost(rapidity=0.0), 8)
    assert np.array_equal(out[key], spectra[key])


@pytest.mark.parametrize(
    "shape",
    [
        (9,),
        (9, 1),
        (9, 3),
        (9, 2, 2),
    ],
)
def test_fb83_zero_boost_preserves_alm_exactly(shape: tuple[int, ...]) -> None:
    arr = np.arange(np.prod(shape), dtype=float).reshape(shape)
    out = observed_alm_mixing(arr, ObserverBoost(rapidity=0.0), 8)
    assert np.array_equal(out, arr)


@pytest.mark.parametrize("key", ["TT", "EE", "TE", "BB"])
def test_fb83_apply_observer_boost_matches_power_kernel_formula(key: str) -> None:
    spectra = _spectra(8)
    beta = 1.23e-3
    boost = ObserverBoost(rapidity=float(np.arctanh(beta)))
    expected = _weighted_power_kernel(8, boost) @ spectra[key]
    observed = apply_observer_boost(spectra, boost, 8)[key]
    assert np.allclose(observed, expected, rtol=1.0e-12, atol=1.0e-15)


@pytest.mark.parametrize("source_ell", [0, 1, 2, 3, 4, 5])
def test_fb83_observed_alm_mixing_matches_kernel_action_on_axisymmetric_slice(
    source_ell: int,
) -> None:
    L_max = 8
    beta = 1.0e-3
    boost = ObserverBoost(rapidity=float(np.arctanh(beta)))
    alm = np.zeros(L_max + 1, dtype=float)
    alm[source_ell] = 1.0
    expected = aberration_kernel(L_max, boost) @ alm
    observed = observed_alm_mixing(alm, boost, L_max)
    assert np.allclose(observed, expected, rtol=1.0e-12, atol=1.0e-15)


@pytest.mark.parametrize("source_ell", [0, 1, 2, 3, 4, 5])
def test_fb83_single_source_alm_and_cl_adapters_agree(source_ell: int) -> None:
    L_max = 8
    beta = 1.23e-3
    boost = ObserverBoost(rapidity=float(np.arctanh(beta)))
    spectra = {
        key: np.zeros(L_max + 1, dtype=float) for key in ("TT", "EE", "TE", "BB")
    }
    spectra["TT"][source_ell] = 1.0

    alm = np.zeros((L_max + 1, 2 * L_max + 1), dtype=float)
    active = 2 * source_ell + 1
    alm[source_ell, :active] = 1.0

    mixed_alm = observed_alm_mixing(alm, boost, L_max)
    mixed_cl_from_alm = np.zeros(L_max + 1, dtype=float)
    for ell in range(L_max + 1):
        active = 2 * ell + 1
        mixed_cl_from_alm[ell] = np.sum(np.abs(mixed_alm[ell, :active]) ** 2) / active
    mixed_cl = apply_observer_boost(spectra, boost, L_max)["TT"]
    assert np.allclose(mixed_cl_from_alm, mixed_cl, rtol=1.0e-12, atol=1.0e-15)


@pytest.mark.parametrize("key", ["TT", "EE", "TE", "BB"])
def test_fb83_input_dict_is_not_mutated(key: str) -> None:
    spectra = _spectra(6)
    before = spectra[key].copy()
    _ = apply_observer_boost(
        spectra,
        ObserverBoost(rapidity=float(np.arctanh(1.0e-3))),
        6,
    )
    assert np.array_equal(spectra[key], before)


def test_fb83_invalid_spectrum_rank_is_rejected() -> None:
    spectra = {"TT": np.ones((3, 3), dtype=float)}
    with pytest.raises(ValueError):
        apply_observer_boost(spectra, ObserverBoost(rapidity=1.0e-3), 2)


def test_fb83_invalid_spectrum_length_is_rejected() -> None:
    spectra = {"TT": np.ones(3, dtype=float)}
    with pytest.raises(ValueError):
        apply_observer_boost(spectra, ObserverBoost(rapidity=1.0e-3), 4)


def test_fb83_invalid_alm_shape_is_rejected() -> None:
    with pytest.raises(ValueError):
        observed_alm_mixing(np.array(1.0), ObserverBoost(rapidity=1.0e-3), 0)


def test_fb83_invalid_alm_length_is_rejected() -> None:
    with pytest.raises(ValueError):
        observed_alm_mixing(np.ones(3), ObserverBoost(rapidity=1.0e-3), 4)
