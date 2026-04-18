"""Tests for bass/species/lambda_.py (LB-1, T-14, T-15)."""
from __future__ import annotations

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.constants import default_constants
from bass.species.lambda_ import LambdaBackground


@pytest.fixture(scope="module")
def bg():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def lamb(bg):
    c = default_constants()
    return LambdaBackground(bg, c.Omega_Lambda_0)


# --- T-14: ρ_Λ constant ----------------------------------------------------


def test_T14_rho_Lambda_constant(bg, lamb):
    """ρ_Λ(η) = Ω_Λ,0 everywhere, 1e-15 abs."""
    c = default_constants()
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 30)[1:]
    rho = np.asarray(lamb.rho_rest(eta_sample))
    assert np.allclose(rho, c.Omega_Lambda_0, atol=1e-15, rtol=0.0)


# --- T-15: w_Λ = -1 ---------------------------------------------------------


def test_T15_w_Lambda_minus_one(bg, lamb):
    """w_Λ = −1 everywhere, 1e-15 abs."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 30)[1:]
    w = lamb.w(eta_sample)
    assert np.allclose(w, -1.0, atol=1e-15, rtol=0.0)


def test_Lambda_pressure_equals_negative_rho(bg, lamb):
    c = default_constants()
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    p = np.asarray(lamb.p_rest(eta_sample))
    assert np.allclose(p, -c.Omega_Lambda_0, atol=1e-15)


def test_Lambda_dot_rho_zero(bg, lamb):
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    dot = np.asarray(lamb.dot_rho(eta_sample))
    assert np.all(dot == 0.0)
    assert lamb.dot_rho(bg.eta_today) == 0.0


def test_Lambda_temperature_none(bg, lamb):
    assert lamb.temperature(bg.eta_today) is None


def test_negative_Omega_Lambda_raises(bg):
    with pytest.raises(ValueError):
        LambdaBackground(bg, -0.5)
