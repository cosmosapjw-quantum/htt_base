"""Invariant: `einstein_bianchi._PLANCK18` matches the species SSOT.

Post-audit (2026-04-18) guard that prevents parameter drift between
the Bianchi solver (`bass.background.einstein_bianchi`) and the
species-layer SSOT (`bass.species.constants.default_constants()`).
Pre-audit, ``_PLANCK18`` hardcoded ``Omega_m=0.3138, Omega_Lambda=
0.6862`` which summed to 1.000092 — a spurious Ω_k ≈ -9e-5 that
silently broke flat-closure regression tests in any future LB-5
code joining tetrad-state and species output.
"""
from __future__ import annotations

import pytest

from bass.background.einstein_bianchi import _PLANCK18, flrw_cosmology
from bass.species.constants import default_constants


def test_planck18_matches_species_ssot():
    """All four Ω / H_0 entries must match ``default_constants()`` exactly."""
    c = default_constants()
    assert _PLANCK18["H0"] == pytest.approx(c.H0_km_s_mpc, rel=1e-15)
    assert _PLANCK18["Omega_r"] == pytest.approx(c.Omega_r_0, rel=1e-15)
    assert _PLANCK18["Omega_m"] == pytest.approx(c.Omega_m_0, rel=1e-15)
    assert _PLANCK18["Omega_Lambda"] == pytest.approx(
        c.Omega_Lambda_0, rel=1e-15,
    )


def test_planck18_flat_closure():
    """Ω_r + Ω_m + Ω_Λ = 1 exactly (flat-ΛCDM)."""
    total = (
        _PLANCK18["Omega_r"]
        + _PLANCK18["Omega_m"]
        + _PLANCK18["Omega_Lambda"]
    )
    assert total == pytest.approx(1.0, abs=1e-14, rel=0.0)


def test_flrw_cosmology_uses_ssot():
    """``flrw_cosmology()`` BianchiCosmology reflects the SSOT constants."""
    c = default_constants()
    cos = flrw_cosmology()
    assert cos.H0 == pytest.approx(c.H0_km_s_mpc, rel=1e-15)
    assert cos.Omega_r == pytest.approx(c.Omega_r_0, rel=1e-15)
    assert cos.Omega_m == pytest.approx(c.Omega_m_0, rel=1e-15)
    assert cos.Omega_Lambda == pytest.approx(c.Omega_Lambda_0, rel=1e-15)
