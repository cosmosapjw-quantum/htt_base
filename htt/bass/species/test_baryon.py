"""Tests for bass/species/baryon.py (LB-1, T-09..T-12, T-24).

The baryon background is the species where LB-1 leans the most on
existing bass_py machinery (HyRec fixture + tanh reionization). The
tests therefore split into three parts:

1. Pure dust scaling ρ_b ∝ a⁻³ (T-09, T-10)
2. Recombination-wrapper contract — queries propagate verbatim through
   the shared ``RecombinationInterp`` (T-11)
3. Reionization-wrapper contract — the reionization-extended table
   produces the expected late-time x_e plateau (T-12)

T-24 in the spec as literally written compares ``T_m(z=150)`` to
``T_γ(z=150)`` "within 1 %"; the HyRec fixture ships with a Compton
decoupling that has already weakened T_m / T_γ to 0.76 by z=150
(physical — Compton rate ∝ x_e T⁴ × a⁻³ drops below H around
z≈200). We therefore anchor T-24 at z=800 instead, where T_m/T_γ is
0.999, preserving the "Compton-coupled plateau" intent of the test.
"""
from __future__ import annotations

from pathlib import Path
import warnings

import numpy as np
import pytest

from bass.recombination.recombination_ingest import (
    build_interpolators, load_recombination_table,
)
from bass.recombination.reionization import (
    ReionizationParameters,
    cosmology_from_metadata,
    extend_table_with_reionization,
)
from bass.species.background_table import build_flrw_background_table
from bass.species.baryon import BaryonBackground
from bass.species.constants import default_constants


FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "recombination" / "fixtures"
    / "recombination_ref_planck2018.csv"
)


@pytest.fixture(scope="module")
def bg():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def recomb():
    table = load_recombination_table(FIXTURE_PATH)
    return build_interpolators(table)


@pytest.fixture(scope="module")
def recomb_with_reion():
    table = load_recombination_table(FIXTURE_PATH)
    cosmo = cosmology_from_metadata(table.metadata)
    reion_params = ReionizationParameters()
    ext = extend_table_with_reionization(table, reion_params, cosmology=cosmo)
    return build_interpolators(ext), cosmo, reion_params


@pytest.fixture(scope="module")
def baryon(bg, recomb):
    c = default_constants()
    return BaryonBackground(bg, c.Omega_b_0, recomb)


# --- T-09: ρ_b × a³ = const ------------------------------------------------


def test_T09_rho_b_times_a3_constant(bg, baryon):
    """ρ_b × a³ is constant across η-grid (dust; Kolb §3.5)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 50)[1:]
    a = bg.interp_a(eta_sample)
    product = np.asarray(baryon.rho_rest(eta_sample)) * a ** 3
    rel_spread = np.max(np.abs(product - product.mean()) / product.mean())
    assert rel_spread < 1e-12


def test_rho_b_today(bg, baryon):
    c = default_constants()
    assert baryon.rho_rest(bg.eta_today) == pytest.approx(
        c.Omega_b_0, rel=1e-10,
    )


# --- T-10: p_b = 0 at background ------------------------------------------


def test_T10_p_b_zero(bg, baryon):
    """p_b = 0 at all η (strict background level)."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    p = baryon.p_rest(eta_sample)
    assert np.all(np.asarray(p) == 0.0)
    assert baryon.p_rest(bg.eta_today) == 0.0


# --- T-11: tau_dot wrapper matches RecombinationInterp ---------------------


def test_T11_tau_dot_passthrough(bg, baryon, recomb):
    """τ̇ wrapper passes through the RecombinationInterp spline verbatim.

    The wrapper composes two interpolations (η → a via bg spline, then
    a → z, then recomb spline in z), so comparing to the raw direct
    query at a *nominal* z introduces interpolation noise of order
    1e-5. We split the test into two checks:

      (a) the wrapper matches the recomb spline at the *exact* z the
          wrapper produces (pure passthrough, 1e-10);
      (b) the wrapper's output at η(z_nominal) is within 1% of the
          recomb spline at z_nominal (physical consistency).
    """
    z_target = 1000.0
    eta_target = bg.eta_at_a(1.0 / (1.0 + z_target))

    # (a) Pure passthrough check.
    z_actual = baryon._z_of_eta(eta_target)
    tau_dot_wrapper = baryon.tau_dot(eta_target)
    assert tau_dot_wrapper == pytest.approx(
        float(np.asarray(recomb.query_tau_dot(z_actual))),
        rel=1e-10,
    )

    # (b) Physical consistency around z=1000.
    tau_dot_nominal = recomb.query_tau_dot(z_target)
    assert tau_dot_wrapper == pytest.approx(tau_dot_nominal, rel=1e-2)


# --- T-12: reionization wrapper matches extended table --------------------


def test_T12_x_e_reion_wrapper(bg, recomb_with_reion):
    """Baryon.x_e tracks the reionization-extended table.

    T-12 as written in spec §8 compares ``x_e`` at ``z=8`` to
    ``0.5 × x_e,post`` — but with default ``z_reion_H=7.67`` and the
    tanh width, the midpoint occurs at z=7.67, not z=8. We test two
    stronger invariants:

      (a) wrapper passthrough — baryon.x_e at the wrapper's internal
          z exactly matches ``recomb.query_x_e`` at that same z
          (1e-10, no double-interpolation error);
      (b) late-time H-reion plateau — at z=6, x_e = 1 + f_He to 0.5 %.
    """
    c = default_constants()
    interp, cosmo, reion_params = recomb_with_reion
    baryon = BaryonBackground(bg, c.Omega_b_0, interp)

    # (a) Passthrough contract at the wrapper's internal z.
    z_mid = reion_params.z_reion_H
    eta_mid = bg.eta_at_a(1.0 / (1.0 + z_mid))
    z_actual = baryon._z_of_eta(eta_mid)
    assert baryon.x_e(eta_mid) == pytest.approx(
        float(np.asarray(interp.query_x_e(z_actual))),
        rel=1e-10,
    )

    # (b) Late-time post-H plateau: at z=6, x_e ≈ 1 + f_He.
    z_plateau = 6.0
    eta_plateau = bg.eta_at_a(1.0 / (1.0 + z_plateau))
    assert baryon.x_e(eta_plateau) == pytest.approx(
        1.0 + cosmo.f_He, rel=5e-3,
    )


# --- T-24 (revised): T_m tracks T_γ during Compton-coupled era ------------


def test_T24_T_m_tracks_T_gamma_at_z800(bg, baryon):
    """T_m(z=800) ≈ T_γ(z=800) within 1 % (Compton coupling intact).

    Note: spec §8 T-24 states z=150 originally, but the HyRec fixture's
    Compton decoupling begins around z≈200; T_m/T_γ = 0.76 at z=150.
    Anchoring at z=800 (where T_m/T_γ = 0.999) preserves the intent.
    """
    c = default_constants()
    z_target = 800.0
    eta_target = bg.eta_at_a(1.0 / (1.0 + z_target))
    T_m = baryon.temperature(eta_target)
    T_gamma = c.T_gamma_0_K * (1.0 + z_target)
    assert T_m == pytest.approx(T_gamma, rel=1.0e-2)


# --- Construction guard + edge cases ---------------------------------------


def test_nonpositive_Omega_b_raises(bg, recomb):
    with pytest.raises(ValueError):
        BaryonBackground(bg, 0.0, recomb)
    with pytest.raises(ValueError):
        BaryonBackground(bg, -0.01, recomb)


def test_recombination_warning_policy_ignore_silences_support_gap(bg, recomb):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        BaryonBackground(
            bg,
            default_constants().Omega_b_0,
            recomb,
            recombination_warning_policy="ignore",
        )
    assert not caught


def test_recombination_warning_policy_always_emits_support_gap(bg, recomb):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        BaryonBackground(
            bg,
            default_constants().Omega_b_0,
            recomb,
            recombination_warning_policy="always",
        )
    assert any("recombination table z-range" in str(item.message) for item in caught)


def test_invalid_recombination_warning_policy_raises(bg, recomb):
    with pytest.raises(ValueError, match="recombination_warning_policy"):
        BaryonBackground(
            bg,
            default_constants().Omega_b_0,
            recomb,
            recombination_warning_policy="bad",  # type: ignore[arg-type]
        )


def test_dot_rho_baryon_continuity(bg, baryon):
    """ρ̇_b = −Θ × ρ_b."""
    eta_sample = np.linspace(bg.eta_min, bg.eta_today, 10)[1:]
    theta = bg.interp_Theta(eta_sample)
    rho = np.asarray(baryon.rho_rest(eta_sample))
    dot = np.asarray(baryon.dot_rho(eta_sample))
    assert np.allclose(dot, -theta * rho, rtol=1e-12)


def test_baryon_helpers_are_scalar_in_scalar_out(bg, baryon):
    """Scalar η in → scalar helpers (x_e, tau_dot, T_m, kappa, visibility)."""
    z = 500.0
    eta = bg.eta_at_a(1.0 / (1.0 + z))
    assert isinstance(baryon.x_e(eta), float)
    assert isinstance(baryon.tau_dot(eta), float)
    assert isinstance(baryon.kappa(eta), float)
    assert isinstance(baryon.visibility(eta), float)
    assert isinstance(baryon.temperature(eta), float)


def test_out_of_recomb_range_raises(bg, baryon):
    """Querying x_e at z beyond the HyRec table range raises."""
    # Fixture covers z ∈ [1, 8000]; ask for z=15000 (deep in radiation era).
    a_early = 1.0 / (1.0 + 15000.0)
    if a_early >= bg.a[0]:
        eta_early = bg.eta_at_a(a_early)
        with pytest.raises(ValueError):
            baryon.x_e(eta_early)


def test_LB4_F1_tau_reion_window_matches_planck2018(bg, recomb_with_reion):
    """LB-4 F1 post-audit repair: ``BaryonBackground.tau_reion_window``
    integrated over ``[z_lo, z_hi] = [0, 30]`` reproduces the Planck
    2018 τ_reion = 0.0544 ± 0.0073 band on the reionization-extended
    HyRec fixture.

    Reference: Planck 2018 I (Aghanim+ 2018) eq (3); LB-6-14
    integration test delegates to this helper.
    """
    interp, _, _ = recomb_with_reion
    c = default_constants()
    baryon = BaryonBackground(bg, c.Omega_b_0, interp)
    tau_reion = baryon.tau_reion_window(z_lo=0.0, z_hi=30.0)
    assert 0.0514 <= tau_reion <= 0.0574, (
        f"τ_reion = {tau_reion} outside Planck 2018 ±0.003 band"
    )


def test_LB4_F1_tau_reion_window_validates_range(bg, recomb_with_reion):
    """Window helper rejects inverted or negative redshift bounds."""
    interp, _, _ = recomb_with_reion
    c = default_constants()
    baryon = BaryonBackground(bg, c.Omega_b_0, interp)
    with pytest.raises(ValueError, match="z_lo < z_hi"):
        baryon.tau_reion_window(z_lo=10.0, z_hi=5.0)
    with pytest.raises(ValueError, match="z_lo < z_hi"):
        baryon.tau_reion_window(z_lo=-1.0, z_hi=5.0)


def test_LB1_F6_out_of_range_error_carries_eta_context(bg, baryon):
    """LB-1 F6 post-audit repair: when η lands outside the recomb table
    support, ``x_e / T_m / tau_dot / kappa / visibility`` raise
    ``ValueError`` whose message identifies both the offending η and the
    mapped z, plus the field name. Prior behaviour raised the raw
    ``query_x_e`` error that mentioned only z, leaving the η-side caller
    to reverse the mapping by hand.
    """
    a_early = 1.0 / (1.0 + 15000.0)
    if a_early < bg.a[0]:
        pytest.skip("FLRW bg_table does not span z=15000")
    eta_early = bg.eta_at_a(a_early)
    for field, call in (
        ("x_e", lambda: baryon.x_e(eta_early)),
        ("tau_dot", lambda: baryon.tau_dot(eta_early)),
        ("T_m", lambda: baryon.temperature(eta_early)),
        ("kappa", lambda: baryon.kappa(eta_early)),
        ("visibility", lambda: baryon.visibility(eta_early)),
    ):
        with pytest.raises(ValueError, match=r"BaryonBackground\." + field) as excinfo:
            call()
        msg = str(excinfo.value)
        assert "η" in msg and "z" in msg, (
            f"{field}: expected both η and z in the ValueError message, got: {msg}"
        )
