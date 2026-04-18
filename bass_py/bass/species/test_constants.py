"""Tests for bass/species/constants.py (LB-1, T-25 + SSOT bit-match)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.species import constants as c
from bass.species.constants import default_constants


# --- SSOT bit-exact mirror -----------------------------------------------


def test_ssot_T0_K_bit_exact():
    """``C.T0_K`` (Fixsen 2009) is re-exported verbatim."""
    from htt.htt.core import ssot
    assert c.T_GAMMA_0_K == ssot.C.T0_K


def test_ssot_Omega_m_bit_exact():
    from htt.htt.core import ssot
    assert c.OMEGA_M_0 == ssot.C.Omega_m


def test_ssot_h_bit_exact():
    from htt.htt.core import ssot
    assert c.H_DIMLESS == ssot.C.h
    assert c.H0_KM_S_MPC == ssot.C.h * 100.0


def test_c_kms_matches_flrw_boltzmann():
    """Speed-of-light SSOT is shared with ``bass.spectrum.flrw_boltzmann``."""
    from bass.background.einstein_bianchi import C_KMS as bg_ckms
    assert c.C_KMS == bg_ckms


# --- Derived fractions physical sanity (T-25 + §4 cross-check) ----------


def test_Omega_gamma_0_blackbody_formula():
    """T-25: Ω_γ,0 derived from CODATA + T_γ,0 matches blackbody formula.

    Direct recomputation with an independent path:

        u_γ = 4 σ_SB T⁴ / c          (Stefan-Boltzmann, J/m³)
        σ_SB = π² k_B⁴ / (60 ℏ³ c²)

    This yields the same Ω_γ,0 as the (π²/15)(kT)⁴/(ℏc)³ formula used in
    ``constants._omega_gamma_0_from_T_and_cosmo`` to within 1e-12.
    """
    T = c.T_GAMMA_0_K
    # Stefan-Boltzmann constant from first principles.
    sigma_SB = (
        math.pi ** 2 * c.K_B_SI ** 4
        / (60.0 * c.HBAR_SI ** 3 * c.C_LIGHT_SI ** 2)
    )
    u_gamma = 4.0 * sigma_SB * T ** 4 / c.C_LIGHT_SI   # J/m³
    rho_gamma = u_gamma / c.C_LIGHT_SI ** 2            # kg/m³
    H0_SI = c.H_DIMLESS * 100.0 * 1000.0 / c.MPC_M
    rho_crit_0 = 3.0 * H0_SI ** 2 / (8.0 * math.pi * c.G_NEWTON_SI)
    Omega_gamma_alt = rho_gamma / rho_crit_0

    assert c.OMEGA_GAMMA_0 == pytest.approx(Omega_gamma_alt, rel=1e-12)


def test_Omega_gamma_0_within_Planck_range():
    """Ω_γ,0 is within the Planck 2018 published range ~5.4e-5."""
    assert 5.2e-5 < c.OMEGA_GAMMA_0 < 5.6e-5


def test_Omega_nu_over_Omega_gamma_Kolb_eq_5_17():
    """Ω_ν / Ω_γ = (7/8)(4/11)^{4/3} N_eff  (Kolb eq 5.17 exactly)."""
    expected_ratio = (7.0 / 8.0) * (4.0 / 11.0) ** (4.0 / 3.0) * c.N_EFF
    assert c.OMEGA_NU_0 / c.OMEGA_GAMMA_0 == pytest.approx(
        expected_ratio, rel=1e-14,
    )


def test_T_nu_over_T_gamma_cube_ratio():
    """(T_ν/T_γ)³ = 4/11 to machine precision (Kolb eq 5.14)."""
    assert c.T_NU_OVER_T_GAMMA ** 3 == pytest.approx(4.0 / 11.0, rel=1e-15)


def test_flat_closure_sums_to_one():
    """Ω_γ + Ω_ν + Ω_b + Ω_c + Ω_Λ = 1 exactly (flat ΛCDM)."""
    total = (
        c.OMEGA_GAMMA_0 + c.OMEGA_NU_0 + c.OMEGA_B_0 + c.OMEGA_C_0
        + c.OMEGA_LAMBDA_0
    )
    assert total == pytest.approx(1.0, rel=0.0, abs=1e-14)


def test_Omega_b_from_omega_b_h2():
    """Ω_b = ω_b / h² (Planck 2018 convention)."""
    assert c.OMEGA_B_0 == pytest.approx(
        c.OMEGA_B_H2 / c.H_DIMLESS ** 2, rel=1e-15,
    )


def test_Omega_c_equals_Omega_m_minus_Omega_b():
    """Ω_c = Ω_m − Ω_b."""
    assert c.OMEGA_C_0 == pytest.approx(
        c.OMEGA_M_0 - c.OMEGA_B_0, rel=1e-15,
    )


# --- SpeciesConstants dataclass -----------------------------------------


def test_default_constants_bundles_all_fractions():
    bundle = default_constants()
    assert bundle.Omega_gamma_0 == c.OMEGA_GAMMA_0
    assert bundle.Omega_nu_0 == c.OMEGA_NU_0
    assert bundle.Omega_b_0 == c.OMEGA_B_0
    assert bundle.Omega_c_0 == c.OMEGA_C_0
    assert bundle.Omega_Lambda_0 == c.OMEGA_LAMBDA_0
    assert bundle.Omega_r_0 == pytest.approx(
        c.OMEGA_GAMMA_0 + c.OMEGA_NU_0, rel=1e-15,
    )
    assert bundle.Omega_m_0 == pytest.approx(
        c.OMEGA_B_0 + c.OMEGA_C_0, rel=1e-15,
    )


def test_default_constants_is_immutable():
    bundle = default_constants()
    with pytest.raises((AttributeError, Exception)):
        bundle.Omega_gamma_0 = 0.0  # type: ignore[misc]


def test_H0_mpc_equals_H0_over_c():
    bundle = default_constants()
    expected = c.H0_KM_S_MPC / c.C_KMS
    assert bundle.H0_mpc == pytest.approx(expected, rel=1e-15)
