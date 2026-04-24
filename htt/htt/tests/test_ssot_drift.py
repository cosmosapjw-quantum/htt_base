"""Anti-regression guard for SSOT T_CMB drift (SSOT-01 — closed 2026-04-24).

Freezes ``T_CMB = 2.72548 K`` (Fixsen 2009 post-WMAP recalibration; see
``docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md``) at every copy of the constant
across the htt, bass, and tsc packages. Any silent future change to any of
the copies fires a regression test.

Drift closure commit (2026-04-24): updated four production files plus ten
paired tests from the legacy ``2.7255`` to the canonical Fixsen central
value. Post-closure there are no ``T_CMB_K = 2.7255`` literals in any
production module; this guard traps re-introductions at unit-test time.
"""
from htt.core.ssot import C


# ─── htt side ─────────────────────────────────────────────────────────
def test_tcmb_ssot_frozen_fixsen2009():
    """C.T0_K must equal the Fixsen 2009 central value (2.72548 K) byte-exact."""
    assert C.T0_K == 2.72548


def test_tcmb_ssot_units_are_internally_consistent():
    """C.T0_uK must be the exact μK conversion of the frozen Fixsen 2009 value."""
    assert C.T0_uK == C.T0_K * 1e6


# ─── bass side (drift closure 2026-04-24) ────────────────────────────
def test_tcmb_bass_planck_mes_bounds_matches_htt():
    """bass.observational.planck_mes_bounds.T_CMB_K must equal C.T0_K bit-exact.

    Prior to the 2026-04-24 closure this held 2.7255; any re-introduction
    of the legacy value now fires here.
    """
    from bass.observational.planck_mes_bounds import T_CMB_K, T_CMB_MICROK
    assert T_CMB_K == C.T0_K
    assert T_CMB_MICROK == C.T0_uK


def test_tcmb_bass_off_diagonal_covariance_matches_htt():
    """bass.spectrum.off_diagonal_covariance._T_CMB_K must match the SSOT."""
    from bass.spectrum import off_diagonal_covariance
    assert off_diagonal_covariance._T_CMB_K == C.T0_K


# ─── tsc side (drift closure 2026-04-24) ──────────────────────────────
def test_tcmb_tsc_michaelis_menten_mirror_matches_htt():
    """tsc.charts.michaelis_menten_export.T_CMB_K_MIRROR must match the SSOT."""
    from tsc.charts.michaelis_menten_export import T_CMB_K_MIRROR
    assert T_CMB_K_MIRROR == C.T0_K
