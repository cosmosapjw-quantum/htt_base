from __future__ import annotations

import numpy as np
import pytest

from bass.observer.aberration import aberration_kernel
from bass.observer.observer_boost import ObserverBoost


@pytest.mark.parametrize("L_max", [0, 1, 2, 4, 8, 16])
def test_fb82_zero_boost_is_exact_identity(L_max: int) -> None:
    kernel = aberration_kernel(L_max, ObserverBoost(rapidity=0.0))
    assert np.array_equal(kernel, np.eye(L_max + 1))


@pytest.mark.parametrize("bad_L_max", [-1, -2, -10])
def test_fb82_negative_L_max_is_rejected(bad_L_max: int) -> None:
    with pytest.raises(ValueError):
        aberration_kernel(bad_L_max, ObserverBoost(rapidity=0.0))


@pytest.mark.parametrize("L_max", [1, 3, 5, 9])
def test_fb82_kernel_has_expected_shape_and_dtype(L_max: int) -> None:
    kernel = aberration_kernel(L_max, ObserverBoost(rapidity=1.0e-3))
    assert kernel.shape == (L_max + 1, L_max + 1)
    assert kernel.dtype == np.float64


@pytest.mark.parametrize("L_max", [2, 4, 8, 12])
def test_fb82_kernel_is_tridiagonal_at_linear_order(L_max: int) -> None:
    kernel = aberration_kernel(L_max, ObserverBoost(rapidity=1.0e-3))
    rows, cols = np.nonzero(np.abs(kernel) > 0.0)
    assert np.all(np.abs(rows - cols) <= 1)


@pytest.mark.parametrize(
    "ell,beta",
    [
        (1, 1.0e-4),
        (1, 1.0e-3),
        (2, 1.0e-4),
        (2, 1.0e-3),
        (3, 1.0e-4),
        (3, 1.0e-3),
        (4, 1.0e-4),
        (4, 1.0e-3),
    ],
)
def test_fb82_lower_offdiagonal_matches_linear_formula(ell: int, beta: float) -> None:
    kernel = aberration_kernel(ell + 1, ObserverBoost(rapidity=float(np.arctanh(beta))))
    expected = beta * ell / (2.0 * ell - 1.0)
    assert kernel[ell, ell - 1] == pytest.approx(expected, rel=1.0e-12)


@pytest.mark.parametrize(
    "ell,beta",
    [
        (0, 1.0e-4),
        (0, 1.0e-3),
        (1, 1.0e-4),
        (1, 1.0e-3),
        (2, 1.0e-4),
        (2, 1.0e-3),
        (3, 1.0e-4),
        (3, 1.0e-3),
    ],
)
def test_fb82_upper_offdiagonal_matches_linear_formula(ell: int, beta: float) -> None:
    kernel = aberration_kernel(ell + 1, ObserverBoost(rapidity=float(np.arctanh(beta))))
    expected = -beta * (ell + 1.0) / (2.0 * ell + 3.0)
    assert kernel[ell, ell + 1] == pytest.approx(expected, rel=1.0e-12)


def test_fb82_planck_scale_pin_for_k22_and_k23() -> None:
    beta = 1.0e-3
    kernel = aberration_kernel(4, ObserverBoost(rapidity=float(np.arctanh(beta))))
    assert kernel[2, 2] == pytest.approx(1.0, abs=0.0)
    assert kernel[2, 3] == pytest.approx(-(3.0 / 7.0) * beta, rel=1.0e-12)


@pytest.mark.parametrize(
    "L_max,beta",
    [
        (4, 1.0e-4),
        (4, 1.0e-3),
        (8, 1.0e-4),
        (8, 1.0e-3),
        (8, 1.23e-3),
        (12, 1.23e-3),
    ],
)
def test_fb82_power_kernel_row_sums_preserve_total_power_to_linear_order(
    L_max: int,
    beta: float,
) -> None:
    kernel = aberration_kernel(L_max, ObserverBoost(rapidity=float(np.arctanh(beta))))
    power_kernel = kernel * kernel
    row_sums = power_kernel.sum(axis=1)
    assert np.max(np.abs(row_sums - 1.0)) < 5.0e-3


def test_fb82_docstring_keeps_corrected_external_locators() -> None:
    doc = aberration_kernel.__doc__ or ""
    assert "astro-ph/0112457" in doc
    assert "1303.5087" in doc
