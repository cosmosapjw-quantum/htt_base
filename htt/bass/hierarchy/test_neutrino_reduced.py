"""Tests for bass/hierarchy/neutrino_reduced.py (LB-5 supplementary).

The 4-scalar reduced ν fluid is a simple diagonal block at LB-5 (k=0
background); these tests pin the expansion-damping relation against
Ma-Bertschinger 1995 eq (49) radiation-limit coefficients and
validate the shape contract.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.neutrino_reduced import (
    NEUTRINO_REDUCED_LABELS,
    neutrino_reduced_rhs,
)
from bass.species.background_table import build_flrw_background_table


@pytest.fixture(scope="module")
def bg():
    return build_flrw_background_table()


def test_neutrino_rhs_shape_contract(bg) -> None:
    """The RHS returns a shape-(4,) array regardless of ``η`` input."""
    eta = 0.5 * bg.eta_today
    nu = np.array([1e-3, 2e-4, -5e-5, 3e-6])
    out = neutrino_reduced_rhs(eta, nu, bg_table=bg)
    assert out.shape == (4,)
    assert np.all(np.isfinite(out))


def test_neutrino_rhs_radiation_coefficient(bg) -> None:
    """Δ_ν' / Δ_ν = −a Θ (1 + 1/3) = −(4/3) a Θ to machine precision.

    Reference: Ma-Bertschinger 1995 eq (49); Kolb §3.3 (w = 1/3).
    """
    eta = 0.1 * bg.eta_today
    a = float(bg.interp_a(eta))
    theta = float(bg.interp_Theta(eta))
    nu = np.array([1.0, 0.0, 0.0, 0.0])
    out = neutrino_reduced_rhs(eta, nu, bg_table=bg)

    expected = -a * theta * (4.0 / 3.0)
    assert out[0] == pytest.approx(expected, rel=1e-14)
    assert out[1] == 0.0
    assert out[2] == 0.0
    assert out[3] == 0.0


def test_neutrino_rhs_qnu_pinu_G3_coefficient(bg) -> None:
    """q_ν', π_ν', G_3' all decay with coefficient −a Θ exactly.

    This is the k = 0 limit of MB-1995 eq (49) (gradient terms vanish
    in orthogonal Bianchi I / V / VII₀ at k = 0).
    """
    eta = 0.3 * bg.eta_today
    a = float(bg.interp_a(eta))
    theta = float(bg.interp_Theta(eta))
    # Probe each non-Δ slot independently.
    for idx, expected_coeff in enumerate([
        -a * theta * (4.0 / 3.0),   # Δ_ν
        -a * theta,                  # q_ν
        -a * theta,                  # π_ν
        -a * theta,                  # G_3
    ]):
        nu = np.zeros(4)
        nu[idx] = 1.0
        out = neutrino_reduced_rhs(eta, nu, bg_table=bg)
        assert out[idx] == pytest.approx(expected_coeff, rel=1e-14)


def test_neutrino_rhs_zero_state_is_zero(bg) -> None:
    """RHS(0) ≡ 0 (a linear system has a trivial fixed point at zero)."""
    eta = 0.5 * bg.eta_today
    out = neutrino_reduced_rhs(eta, np.zeros(4), bg_table=bg)
    np.testing.assert_array_equal(out, np.zeros(4))


def test_neutrino_rhs_rejects_bad_shape(bg) -> None:
    with pytest.raises(ValueError, match="shape"):
        neutrino_reduced_rhs(0.5 * bg.eta_today, np.zeros(3), bg_table=bg)


def test_labels_order() -> None:
    """``NEUTRINO_REDUCED_LABELS`` is the canonical (Δ, q, π, G_3) order."""
    assert NEUTRINO_REDUCED_LABELS == ("Delta_nu", "q_nu", "pi_nu", "G_3")
