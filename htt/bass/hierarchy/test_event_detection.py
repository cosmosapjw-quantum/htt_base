"""Tests for bass/hierarchy/event_detection.py (LB-5 I-15..I-17).

The three locators are pinned directly against the spec's Kolb /
Planck-2018 targets. The LB-6 integration-regression suite consumes
the same locators via ``IntegrationResult.critical_events``.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.event_detection import (
    detect_critical_events,
    find_eta_reion_midpoint,
    find_z_equality,
    find_z_star_from_visibility,
)
from bass.species.registry import SpeciesBackgroundRegistry


@pytest.fixture(scope="module")
def species():
    return SpeciesBackgroundRegistry.from_planck2018()


# ════════════════════════════════════════════════════════════════════
# I-16 z_eq ≈ 3400
# ════════════════════════════════════════════════════════════════════

def test_I16_z_eq_matches_kolb_target(species) -> None:
    """``z_eq`` lies in the spec §10.5 band [3300, 3500].

    Kolb §3.5 quotes ``z_eq ≈ 3400`` for Planck-2018; the exact value
    depends on ``Ω_m / Ω_r`` and is pinned here as a regression anchor.
    """
    z_eq = find_z_equality(species, species.bg_table)
    assert 3300.0 <= z_eq <= 3500.0, f"z_eq={z_eq} outside [3300, 3500]"
    # Kolb-Turner "analytic" estimate: a_eq = Ω_r/Ω_m → z_eq = Ω_m/Ω_r − 1.
    c = species.bg_table.constants
    z_eq_analytic = c.Omega_m_0 / c.Omega_r_0 - 1.0
    assert z_eq == pytest.approx(z_eq_analytic, rel=1e-2)


# ════════════════════════════════════════════════════════════════════
# I-15 z_* ∈ [1089, 1091]
# ════════════════════════════════════════════════════════════════════

def test_I15_z_star_near_planck18(species) -> None:
    """``z_*`` (peak of visibility) matches the Planck-2018 value 1089.94
    within the spec §10.5 I-15 tolerance of 1.
    """
    z_star = find_z_star_from_visibility(species, species.bg_table)
    assert 1089.0 <= z_star <= 1091.0, f"z_star={z_star}"
    assert abs(z_star - 1089.94) <= 1.0


# ════════════════════════════════════════════════════════════════════
# I-17 eta_reion ≈ 5100 Mpc
# ════════════════════════════════════════════════════════════════════

def test_I17_eta_reion_matches_z_7_67(species) -> None:
    """``eta_reion_midpoint`` evaluated at ``z = 7.67`` lands inside
    the spec §10.5 I-17 band [5000, 5200] (Planck-2018 reion midpoint).
    """
    eta_reion = find_eta_reion_midpoint(
        species, species.bg_table, z_reion_guess=7.67,
    )
    assert 5000.0 <= eta_reion <= 5200.0, (
        f"eta_reion_midpoint={eta_reion} outside [5000, 5200] Mpc"
    )


# ════════════════════════════════════════════════════════════════════
#   detect_critical_events aggregate
# ════════════════════════════════════════════════════════════════════

def test_detect_critical_events_returns_all_keys(species) -> None:
    """``detect_critical_events`` returns the full dict with finite
    values in the expected bands. LB-6 F2 post-audit: ``eta_star`` and
    ``chi_star`` keys added.
    """
    events = detect_critical_events(species, species.bg_table)
    assert set(events) == {
        "z_eq", "z_star",
        "eta_star", "chi_star",
        "eta_reion_midpoint", "eta_today",
    }
    for key, val in events.items():
        assert np.isfinite(val), f"{key} = {val} is not finite"
    assert events["eta_today"] == pytest.approx(
        species.bg_table.eta_today, rel=1e-14,
    )
    # eta_star + chi_star = eta_today by construction
    assert events["eta_star"] + events["chi_star"] == pytest.approx(
        events["eta_today"], rel=1e-12,
    )
    # Planck-2018 ballpark
    assert 270.0 <= events["eta_star"] <= 290.0, (
        f"eta_star = {events['eta_star']} outside [270, 290] Mpc"
    )
    assert 13850.0 <= events["chi_star"] <= 13900.0, (
        f"chi_star = {events['chi_star']} outside [13850, 13900] Mpc"
    )


def test_find_eta_reion_rejects_bad_z() -> None:
    """Non-positive ``z_reion_guess`` raises immediately."""
    sp = SpeciesBackgroundRegistry.from_planck2018()
    with pytest.raises(ValueError, match="z_reion_guess"):
        find_eta_reion_midpoint(sp, sp.bg_table, z_reion_guess=-1.0)
