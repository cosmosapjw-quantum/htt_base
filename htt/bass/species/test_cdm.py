"""Tests for bass/species/cdm.py (LB-1, T-13)."""
from __future__ import annotations

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.cdm import CDMBackground
from bass.species.constants import default_constants


@pytest.fixture(scope="module")
def bg():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def cdm(bg):
    c = default_constants()
    return CDMBackground(bg, c.Omega_c_0)


# --- T-13: ρ_c × a³ = const ------------------------------------------------


def test_T13_rho_cdm_times_a3_constant(bg, cdm):
    """ρ_c × a³ is constant across η-grid (dust)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 50)[1:]
    a = bg.interp_a(eta_sample)
    product = np.asarray(cdm.rho_rest(eta_sample)) * a ** 3
    rel_spread = np.max(np.abs(product - product.mean()) / product.mean())
    assert rel_spread < 1e-12


def test_cdm_rho_today(bg, cdm):
    """ρ_c(η_today) = Ω_c,0 exactly."""
    c = default_constants()
    assert cdm.rho_rest(bg.eta_today) == pytest.approx(
        c.Omega_c_0, rel=1e-10,
    )


def test_cdm_pressure_zero(bg, cdm):
    """p_c = 0 everywhere (pressureless dust)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    p = cdm.p_rest(eta_sample)
    assert np.all(np.asarray(p) == 0.0)
    assert cdm.p_rest(bg.eta_today) == 0.0


def test_cdm_temperature_none(bg, cdm):
    """CDM has no associated thermal bath."""
    assert cdm.temperature(bg.eta_today) is None


def test_cdm_dot_rho_continuity(bg, cdm):
    """ρ̇_c = −Θ × ρ_c along η-grid."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 20)[1:]
    theta = bg.interp_Theta(eta_sample)
    rho = np.asarray(cdm.rho_rest(eta_sample))
    dot = np.asarray(cdm.dot_rho(eta_sample))
    assert np.allclose(dot, -theta * rho, rtol=1e-12)


def test_cdm_w_is_zero(bg, cdm):
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    w = cdm.w(eta_sample)
    assert np.allclose(w, 0.0, atol=1e-15)


def test_negative_Omega_c_raises(bg):
    with pytest.raises(ValueError):
        CDMBackground(bg, -0.1)
