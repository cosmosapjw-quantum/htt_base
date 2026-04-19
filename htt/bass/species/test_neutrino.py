"""Tests for bass/species/neutrino.py (LB-1, T-06..T-08, T-20, T-23)."""
from __future__ import annotations

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.constants import default_constants
from bass.species.neutrino import NeutrinoBackground


@pytest.fixture(scope="module")
def bg():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def neutrino(bg):
    c = default_constants()
    return NeutrinoBackground(bg, c.Omega_nu_0, N_eff=c.N_eff)


# --- T-06: T_ν / T_γ = (4/11)^{1/3} ----------------------------------------


def test_T06_T_nu_over_T_gamma_at_today(bg, neutrino):
    """T_ν(z=0) / T_γ(z=0) = (4/11)^{1/3} to 1e-12."""
    c = default_constants()
    T_nu = neutrino.temperature(bg.eta_today)
    ratio = T_nu / c.T_gamma_0_K
    expected = (4.0 / 11.0) ** (1.0 / 3.0)
    assert ratio == pytest.approx(expected, rel=1e-12)


# --- T-07: Ω_ν / Ω_γ Kolb eq 5.17 -------------------------------------------


def test_T07_Omega_nu_over_Omega_gamma():
    """Ω_ν,0 / Ω_γ,0 = (7/8)(4/11)^{4/3} N_eff exactly (1e-14)."""
    c = default_constants()
    expected = (7.0 / 8.0) * (4.0 / 11.0) ** (4.0 / 3.0) * c.N_eff
    assert c.Omega_nu_0 / c.Omega_gamma_0 == pytest.approx(
        expected, rel=1e-14,
    )


# --- T-08: ρ_ν × a⁴ = const ------------------------------------------------


def test_T08_rho_nu_times_a4_constant(bg, neutrino):
    """ρ_ν × a⁴ is constant across η-grid (massless limit)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 50)[1:]
    a = bg.interp_a(eta_sample)
    product = np.asarray(neutrino.rho_rest(eta_sample)) * a ** 4
    rel_spread = np.max(np.abs(product - product.mean()) / product.mean())
    assert rel_spread < 1e-12


# --- T-20: massive-neutrino request raises NotImplementedError ------------


def test_T20_massive_neutrino_raises(bg):
    """Passing m_nu_eV != 0 raises NotImplementedError (LB-1 scope)."""
    c = default_constants()
    with pytest.raises(NotImplementedError) as exc:
        NeutrinoBackground(bg, c.Omega_nu_0, m_nu_eV=0.06)
    assert "Massive neutrinos deferred" in str(exc.value)


def test_massive_neutrino_zero_allowed(bg):
    """m_nu_eV=0.0 (default) constructs without error."""
    c = default_constants()
    nu = NeutrinoBackground(bg, c.Omega_nu_0, m_nu_eV=0.0)
    assert isinstance(nu, NeutrinoBackground)


# --- T-23: T_ν(z=0) = (4/11)^{1/3} × 2.7255 K ------------------------------


def test_T23_T_nu_z0_kelvin(bg, neutrino):
    """T_ν(z=0) ≈ 1.9454 K (matches Kolb §5.5 numeric)."""
    c = default_constants()
    T_nu_z0 = neutrino.temperature(bg.eta_today)
    expected = (4.0 / 11.0) ** (1.0 / 3.0) * c.T_gamma_0_K
    assert T_nu_z0 == pytest.approx(expected, rel=1e-12)
    # Absolute sanity vs literature (1.9454 K quoted in Kolb §5.5).
    assert 1.94 < T_nu_z0 < 1.96


# --- Continuity form (parallel to T-05) ------------------------------------


def test_dot_rho_neutrino_continuity(bg, neutrino):
    """ρ̇_ν / (−4/3 × Θ × ρ_ν) = 1 (collisionless radiation)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 20)[1:]
    theta = bg.interp_Theta(eta_sample)
    rho = np.asarray(neutrino.rho_rest(eta_sample))
    dot = np.asarray(neutrino.dot_rho(eta_sample))
    expected = -(4.0 / 3.0) * theta * rho
    assert np.allclose(dot, expected, rtol=1e-12)


def test_neutrino_w_is_one_third(bg, neutrino):
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    w = neutrino.w(eta_sample)
    assert np.allclose(w, 1.0 / 3.0, atol=1e-15)


# --- Construction guards ----------------------------------------------------


def test_negative_Omega_nu_raises(bg):
    with pytest.raises(ValueError):
        NeutrinoBackground(bg, -1.0)


def test_nonpositive_Neff_raises(bg):
    c = default_constants()
    with pytest.raises(ValueError):
        NeutrinoBackground(bg, c.Omega_nu_0, N_eff=0.0)
    with pytest.raises(ValueError):
        NeutrinoBackground(bg, c.Omega_nu_0, N_eff=-3.044)
