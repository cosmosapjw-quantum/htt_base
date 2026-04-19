"""Tests for bass/species/photon.py (LB-1, T-01..T-05)."""
from __future__ import annotations

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.constants import default_constants
from bass.species.photon import PhotonBackground


@pytest.fixture(scope="module")
def bg():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def photon(bg):
    c = default_constants()
    return PhotonBackground(bg, c.Omega_gamma_0)


# --- T-01: ρ_γ(1) = Ω_γ,0 ------------------------------------------------


def test_T01_rho_gamma_at_a_eq_1(bg, photon):
    """ρ_γ(η_today) = Ω_γ,0  (tolerance 1e-10 rel)."""
    c = default_constants()
    assert photon.rho_rest(bg.eta_today) == pytest.approx(
        c.Omega_gamma_0, rel=1e-10,
    )


# --- T-02: p_γ / ρ_γ = 1/3 --------------------------------------------------


def test_T02_photon_w_is_one_third(bg, photon):
    """w = p/ρ = 1/3 everywhere on the η-grid (tolerance 1e-15 abs)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 20)[1:]  # skip eta=0
    w = photon.w(eta_sample)
    assert np.allclose(w, 1.0 / 3.0, atol=1e-15, rtol=0.0)


# --- T-03: ρ_γ(a) × a⁴ = const ---------------------------------------------


def test_T03_rho_gamma_times_a4_constant(bg, photon):
    """ρ_γ × a⁴ is constant across the η-grid (tolerance 1e-12 rel)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 50)[1:]
    a = bg.interp_a(eta_sample)
    product = np.asarray(photon.rho_rest(eta_sample)) * a ** 4
    assert np.max(np.abs(product - product.mean()) / product.mean()) < 1e-12


# --- T-04: T_γ(z=0) = T_γ,0 (SSOT) -----------------------------------------


def test_T04_temperature_today(bg, photon):
    """T_γ at z=0 equals the Fixsen 2009 SSOT value exactly."""
    c = default_constants()
    T = photon.temperature(bg.eta_today)
    assert T == pytest.approx(c.T_gamma_0_K, rel=1e-10)


def test_T04b_temperature_scales_as_inverse_a(bg, photon):
    """T_γ(η) × a(η) = T_γ,0 across the grid."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 30)[1:]
    a = bg.interp_a(eta_sample)
    T = np.asarray(photon.temperature(eta_sample))
    c = default_constants()
    assert np.allclose(T * a, c.T_gamma_0_K, rtol=1e-12)


# --- T-05: dot_rho = -(4/3) Θ ρ_γ ------------------------------------------


def test_T05_dot_rho_photon_continuity(bg, photon):
    """ρ̇_γ / (−4/3 × Θ × ρ_γ) = 1 along the η-grid (tolerance 1e-12)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 30)[1:]
    theta = bg.interp_Theta(eta_sample)
    rho = np.asarray(photon.rho_rest(eta_sample))
    dot = np.asarray(photon.dot_rho(eta_sample))
    expected = -(4.0 / 3.0) * theta * rho
    assert np.allclose(dot, expected, rtol=1e-12, atol=0.0)


# --- Broadcasting / scalar-vs-array contract (§3.2) -------------------------


def test_scalar_input_returns_scalar(bg, photon):
    out = photon.rho_rest(bg.eta_today)
    assert isinstance(out, float)


def test_array_input_preserves_shape(bg, photon):
    eta_arr = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    out = photon.rho_rest(eta_arr)
    assert isinstance(out, np.ndarray)
    assert out.shape == eta_arr.shape


# --- Out-of-range behaviour (§7 edge case 3; T-19) -------------------------


def test_out_of_range_eta_raises(bg, photon):
    """Queries outside the FLRW table domain raise ValueError."""
    with pytest.raises(ValueError):
        photon.rho_rest(bg.eta_today + 1e6)
    with pytest.raises(ValueError):
        photon.rho_rest(bg.eta_min - 1e6)


# --- Construction guard -----------------------------------------------------


def test_nonpositive_Omega_gamma_raises(bg):
    with pytest.raises(ValueError):
        PhotonBackground(bg, 0.0)
    with pytest.raises(ValueError):
        PhotonBackground(bg, -1e-5)
