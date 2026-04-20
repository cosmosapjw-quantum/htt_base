from __future__ import annotations

import numpy as np
import pytest

from bass.species.massive_neutrino.phase_space import (
    MASSLESS_FD_ENERGY_INTEGRAL,
    phase_space_grid,
)


_APERY_ZETA3 = 1.2020569031595942


@pytest.mark.parametrize("mass_eV", [0.0, 0.02, 0.04, 0.08])
@pytest.mark.parametrize("N_q", [10, 15, 30])
def test_fb91_phase_space_grid_is_byte_deterministic(
    mass_eV: float,
    N_q: int,
) -> None:
    q_a, w_a = phase_space_grid(mass_eV, N_q=N_q)
    q_b, w_b = phase_space_grid(mass_eV, N_q=N_q)
    assert np.array_equal(q_a, q_b)
    assert np.array_equal(w_a, w_b)


@pytest.mark.parametrize("N_q", [10, 15, 30])
def test_fb91_q_grid_is_strictly_increasing_and_positive(N_q: int) -> None:
    q_grid, _ = phase_space_grid(0.04, N_q=N_q)
    assert q_grid.dtype == np.float64
    assert np.all(np.isfinite(q_grid))
    assert np.all(q_grid > 0.0)
    assert np.all(np.diff(q_grid) > 0.0)


@pytest.mark.parametrize("N_q", [10, 15, 30])
def test_fb91_weights_are_positive_and_finite(N_q: int) -> None:
    _, weights = phase_space_grid(0.04, N_q=N_q)
    assert weights.dtype == np.float64
    assert np.all(np.isfinite(weights))
    assert np.all(weights > 0.0)


@pytest.mark.parametrize("N_q", [10, 15, 30])
def test_fb91_massless_number_density_moment_is_accurate(N_q: int) -> None:
    q_grid, weights = phase_space_grid(0.0, N_q=N_q)
    exact = 1.5 * _APERY_ZETA3
    approx = float(np.sum(weights))
    assert approx == pytest.approx(exact, rel=2e-3 if N_q == 10 else 2e-4)
    # The momentum measure is independent of the mass argument.
    q_massive, w_massive = phase_space_grid(0.08, N_q=N_q)
    assert np.array_equal(q_grid, q_massive)
    assert np.array_equal(weights, w_massive)


@pytest.mark.parametrize("N_q, rtol", [(10, 3e-4), (15, 5e-7), (30, 5e-11)])
def test_fb91_massless_energy_density_moment_is_accurate(
    N_q: int,
    rtol: float,
) -> None:
    q_grid, weights = phase_space_grid(0.0, N_q=N_q)
    approx = float(np.dot(weights, q_grid))
    assert approx == pytest.approx(MASSLESS_FD_ENERGY_INTEGRAL, rel=rtol)


def test_fb91_massless_energy_integral_converges_monotonically_with_N_q() -> None:
    errors = []
    for N_q in (10, 15, 30):
        q_grid, weights = phase_space_grid(0.0, N_q=N_q)
        approx = float(np.dot(weights, q_grid))
        errors.append(abs(approx - MASSLESS_FD_ENERGY_INTEGRAL))
    assert errors[1] < errors[0]
    assert errors[2] < errors[1]


def test_fb91_invalid_mass_raises() -> None:
    with pytest.raises(ValueError):
        phase_space_grid(-0.01, N_q=15)


def test_fb91_invalid_quadrature_size_raises() -> None:
    with pytest.raises(ValueError):
        phase_space_grid(0.04, N_q=0)
