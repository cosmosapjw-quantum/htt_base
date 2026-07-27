"""Regression anchors for legacy bounds and ``htt.core.tilted_flrw``.

These two modules are the pure-algebra core of the MES-bound hierarchy
(`fig_MES_three_bounds`, `fig_sigma_omega_contour`, `fig_sigma_accel_contour`)
and the tilted-FLRW observable dictionary (`fig_tilted_dictionary`,
`fig_peculiar_jeans`, `fig_q0_pushforward`, `fig_v_pushforward`,
`fig_q_decomposition`). No existing test references them directly — a
silent coefficient drift could change every "data-independent" manuscript
figure without any regression flagging it.

Values measured bit-identical on 2026-04-24 against the current HTT
SSOT (`htt.core.ssot.C`).
"""
from __future__ import annotations

import pytest

from tsc_legacy.htt_core_bounds import (
    A2_max_MES,
    B_accel,
    B_omega,
    B_sigma,
    B_sigma_corrected,
    Omega_tilt as bounds_Omega_tilt,
    Sig2_BV,
    Sig2_max_MES,
    W2_max_MES,
    beta_safe,
    eps1_from_beta,
    filling_fraction,
    frame_bias,
    nonlinear_R_omega,
    nonlinear_R_sigma,
    x_defect,
)
from htt.core.tilted_flrw import (
    Delta_q,
    Omega_tilt as tilted_Omega_tilt,
    beta_from_colin,
    matter_acceleration,
    matter_vorticity,
    peculiar_jeans,
    q_matter,
    tilted_H_ratio,
    velocity_growth,
)


# ─── Canonical scenario parameters ────────────────────────────────────
_S1_EPS1   = 1.233e-3    # Kinematic dipole (Ferreira-Quartin)
_S2A_EPS1  = 1.476e-3    # CatWISE 2020
_S2C_EPS1  = 3.296e-3    # Radio NVSS+RACS
_BETA_ANCHOR = 1.360e-3  # CLAUDE.md §5 production anchor


# ═══════════════════════════════════════════════════════════════════════
# Part 1 — bounds.py three-bound hierarchy
# ═══════════════════════════════════════════════════════════════════════

_BOUND_ANCHORS = {
    # eps1 → (B_sigma, B_omega, B_accel, B_sigma_corrected, Sig2_max_MES)
    _S1_EPS1: (
        2.068278297429e-03, 9.336021982857e-04, 9.296093342143e-04,
        2.075138300837e-03, 6.459298451402e-06,
    ),
    _S2A_EPS1: (
        2.473278297429e-03, 1.115852198286e-03, 1.111859334214e-03,
        2.483098300512e-03, 9.248665755007e-06,
    ),
    _S2C_EPS1: (
        5.506611630762e-03, 2.480852198286e-03, 2.476859334214e-03,
        5.555434571067e-03, 4.629427991011e-05,
    ),
}


@pytest.mark.parametrize("eps1,expected", _BOUND_ANCHORS.items())
def test_B_sigma_pinned(eps1, expected):
    """B_σ(ε₁) at canonical scenarios — pinned bit-identical."""
    assert B_sigma(eps1) == pytest.approx(expected[0], abs=1e-15)


@pytest.mark.parametrize("eps1,expected", _BOUND_ANCHORS.items())
def test_B_omega_pinned(eps1, expected):
    """B_ω(ε₁) at canonical scenarios — pinned bit-identical."""
    assert B_omega(eps1) == pytest.approx(expected[1], abs=1e-15)


@pytest.mark.parametrize("eps1,expected", _BOUND_ANCHORS.items())
def test_B_accel_pinned(eps1, expected):
    """B_u̇(ε₁) at canonical scenarios — pinned bit-identical."""
    assert B_accel(eps1) == pytest.approx(expected[2], abs=1e-15)


@pytest.mark.parametrize("eps1,expected", _BOUND_ANCHORS.items())
def test_B_sigma_corrected_pinned(eps1, expected):
    """Frame-corrected B_σ (VT-07 correction) — pinned bit-identical."""
    assert B_sigma_corrected(eps1) == pytest.approx(expected[3], abs=1e-15)


@pytest.mark.parametrize("eps1,expected", _BOUND_ANCHORS.items())
def test_Sig2_max_MES_pinned(eps1, expected):
    """MES ceiling Σ²_max = (3/2)[B_σ^corr]² — pinned bit-identical."""
    assert Sig2_max_MES(eps1) == pytest.approx(expected[4], abs=1e-18)


def test_three_bound_hierarchy_B_sigma_gt_B_omega_gt_B_accel():
    """MES three-bound strict ordering B_σ > B_ω > B_u̇ at every scenario.

    Plan §4.3 D6 anchor. Protects against a sign flip / factor bug that
    would leave one of the three curves crossing another.
    """
    for eps1 in (_S1_EPS1, _S2A_EPS1, _S2C_EPS1):
        Bs = B_sigma(eps1)
        Bw = B_omega(eps1)
        Ba = B_accel(eps1)
        assert Bs > Bw > Ba, (
            f"three-bound ordering violated at eps1={eps1!r}: "
            f"B_sigma={Bs!r}, B_omega={Bw!r}, B_accel={Ba!r}"
        )


def test_W2_max_MES_matches_B_omega_squared():
    """W²_max = (3/2)[B_ω]² (Corollary 3.2)."""
    for eps1 in (_S1_EPS1, _S2A_EPS1, _S2C_EPS1):
        Bw = B_omega(eps1)
        assert W2_max_MES(eps1) == pytest.approx(1.5 * Bw * Bw, rel=1e-12)


def test_A2_max_MES_matches_B_accel_squared():
    """A²_max = (3/2)[B_u̇]² (Corollary 3.3)."""
    for eps1 in (_S1_EPS1, _S2A_EPS1, _S2C_EPS1):
        Ba = B_accel(eps1)
        assert A2_max_MES(eps1) == pytest.approx(1.5 * Ba * Ba, rel=1e-12)


# ═══════════════════════════════════════════════════════════════════════
# Part 2 — tilt primitives (eps1 ↔ beta, frame bias)
# ═══════════════════════════════════════════════════════════════════════

def test_eps1_from_beta_at_anchor():
    """eps1 = (1 + η_u̇) β at β_anchor=1.360e-3."""
    assert eps1_from_beta(_BETA_ANCHOR) == pytest.approx(
        1.473333333333e-03, abs=1e-14
    )


def test_beta_safe_inverse_of_eps1_from_beta():
    """beta_safe(ε₁) = ε₁/(1+η_u̇); round-trip with eps1_from_beta."""
    for eps1 in (_S1_EPS1, _S2A_EPS1, _S2C_EPS1):
        beta = beta_safe(eps1)
        # Round-trip through eps1_from_beta
        assert eps1_from_beta(beta) == pytest.approx(eps1, rel=1e-14)


def test_beta_safe_pinned_at_S1():
    assert beta_safe(_S1_EPS1) == pytest.approx(1.138153846154e-03, abs=1e-15)


def test_frame_bias_pinned_at_S1():
    """frame_bias at S1 is O(ε₁²) ≈ 6.86e-6."""
    assert frame_bias(_S1_EPS1) == pytest.approx(6.860003408563e-06, abs=1e-15)


# ═══════════════════════════════════════════════════════════════════════
# Part 3 — defect variable + filling fraction algebra
# ═══════════════════════════════════════════════════════════════════════

def test_Omega_tilt_bounds_pinned_at_anchor():
    """Ω_tilt(β=1.360e-3) ≈ 5.83e-7 (bounds.py definition)."""
    assert bounds_Omega_tilt(_BETA_ANCHOR) == pytest.approx(
        5.831792395493e-07, abs=1e-18
    )


def test_Omega_tilt_bounds_matches_tilted_flrw():
    """bounds.Omega_tilt and tilted_flrw.Omega_tilt must agree bit-identical.

    Two independent implementations of the same physics — a drift on
    either side must fire this test. Corollary 2.15.
    """
    for beta in (0.0, _BETA_ANCHOR, 2e-3, 5e-3):
        assert bounds_Omega_tilt(beta) == pytest.approx(
            tilted_Omega_tilt(beta), rel=1e-14
        ), f"Omega_tilt mismatch at beta={beta!r}"


def test_x_defect_no_contributions_returns_Sig2():
    """x = Σ² when Ω_tilt, Ω_k, W² all zero."""
    assert x_defect(1e-8) == pytest.approx(1e-8, abs=1e-20)


def test_x_defect_accumulates_contributions():
    """x = Σ² − W² + Ω_tilt + Ω_k_aniso (master departure identity §1.2)."""
    Sig2 = 1e-8
    Om_tilt = 3e-7
    Om_k = 5e-8
    W2 = 2e-9
    expected = Sig2 - W2 + Om_tilt + Om_k
    assert x_defect(Sig2, Omega_tilt=Om_tilt, Omega_k_aniso=Om_k, W2=W2) == \
        pytest.approx(expected, rel=1e-14)


def test_filling_fraction_pinned_at_S1():
    """Point-estimate filling fraction at S1 fiducial."""
    xmax = Sig2_max_MES(_S1_EPS1)
    assert filling_fraction(1e-8, xmax) == pytest.approx(
        1.548155744039e-03, abs=1e-14
    )


def test_Sig2_BV_pinned_at_anchor_with_Planck_Ok():
    """Σ²_BV(β=1.360e-3, Ω_K=7e-4) — pinned bit-identical."""
    assert Sig2_BV(_BETA_ANCHOR, 7e-4) == pytest.approx(
        6.567010745143e-05, abs=1e-16
    )


# ═══════════════════════════════════════════════════════════════════════
# Part 4 — nonlinear R corrections
# ═══════════════════════════════════════════════════════════════════════

def test_nonlinear_R_sigma_pinned_at_small_sigma():
    """R_σ ≈ 1 + O(σ/H)² for small σ/H."""
    assert nonlinear_R_sigma(1e-4) == pytest.approx(
        1.000000060000e+00, abs=1e-15
    )


def test_nonlinear_R_omega_pinned():
    """R_ω ≈ 1 + O(σ/H × ω/H) — near-unity at small fluctuations."""
    assert nonlinear_R_omega(1e-11, 1e-4) == pytest.approx(
        1.000000040000e+00, abs=1e-15
    )


# ═══════════════════════════════════════════════════════════════════════
# Part 5 — tilted_flrw observables dictionary (D26 anchor)
# ═══════════════════════════════════════════════════════════════════════

def test_tilted_H_ratio_pinned_at_anchor():
    """H_tilt / H_isotropic at β_anchor — cosh(β) ≈ 1 + O(β²)."""
    assert tilted_H_ratio(_BETA_ANCHOR) == pytest.approx(
        1.0000018496011402, abs=1e-14
    )


def test_Delta_q_pinned_at_100_Mpc():
    """Δq at d=100 Mpc, β_anchor — pinned bit-identical."""
    assert Delta_q(_BETA_ANCHOR, 100.0) == pytest.approx(
        1.332147371628e+01, abs=1e-10
    )


def test_q_matter_pinned():
    """Deceleration parameter q_m = Ω_m/2 − Ω_Λ (FLRW flat)."""
    assert q_matter() == pytest.approx(1.576500000000e-01, abs=1e-14)


def test_peculiar_jeans_returns_pair_pinned():
    """peculiar_jeans returns (λ_J, f_J). Both pinned at β_anchor."""
    lam_J, f_J = peculiar_jeans(_BETA_ANCHOR, q_matter())
    assert lam_J == pytest.approx(438.8196826844135, abs=1e-9)
    assert f_J   == pytest.approx(0.09859785674001878, abs=1e-14)


def test_matter_vorticity_pinned():
    """ω_matter(β=1.360e-3, Σ²=1e-8) ≈ 3.42e-20 (tiny — quadratic in β)."""
    assert float(matter_vorticity(_BETA_ANCHOR, 1e-8)) == pytest.approx(
        3.421018050829379e-20, rel=1e-12
    )


def test_matter_acceleration_pinned():
    """u̇(β=1.360e-3) ≈ 2.14e-9."""
    assert float(matter_acceleration(_BETA_ANCHOR)) == pytest.approx(
        2.1407420605790912e-09, rel=1e-12
    )


def test_velocity_growth_GR_min_pinned():
    """GR minimal-growth model at z=0.1, β₀=β_anchor."""
    assert velocity_growth(0.1, _BETA_ANCHOR, model="GR_min") == pytest.approx(
        0.0011788264739763686, abs=1e-14
    )


def test_velocity_growth_rejects_unknown_model():
    """Unknown model name raises ValueError with the registered alternatives."""
    with pytest.raises(ValueError, match="Unknown model"):
        velocity_growth(0.1, _BETA_ANCHOR, model="nonsense_model")


# ═══════════════════════════════════════════════════════════════════════
# Part 6 — beta_from_colin translation (D27 anchor)
# ═══════════════════════════════════════════════════════════════════════

_BETA_COLIN_ANCHORS = {
    # z_ref → beta_SNe (Colin 2019 / Tsagas translation, q_d=−8.03, S=0.0262)
    0.03: 6.209234487247e-04,
    0.05: 1.339867350703e-03,
    0.10: 1.589811112754e-03,
}


@pytest.mark.parametrize("z_ref,expected", _BETA_COLIN_ANCHORS.items())
def test_beta_from_colin_pinned(z_ref, expected):
    """β_SNe translation at Colin reference z values — pinned bit-identical."""
    assert beta_from_colin(z_ref) == pytest.approx(expected, abs=1e-15)


def test_beta_from_colin_does_not_authorize_cf4_cross_consistency():
    """A derived SNe translation cannot restore the quarantined CF4 input."""
    from htt.core.cf4_observational_input import CF4InputQuarantined
    from htt.core.evidence_models_R03a import ObsData

    assert beta_from_colin(0.05) == pytest.approx(_BETA_COLIN_ANCHORS[0.05])
    with pytest.raises(CF4InputQuarantined, match="N-DATA-CF4-DOWNSTREAM"):
        _ = ObsData().b_CF4
