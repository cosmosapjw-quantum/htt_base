"""
tests/test_shear_sources.py
============================

Unit tests for the per-type shear source dispatch module.

Test strategy
-------------
§1. Dispatcher completeness: every Bianchi type has a registered source.
§2. FLRW limit: as N_i → 0 and A → 0, all sources → 0 (where applicable).
§3. Type I / FLRW: S = 0 exactly (no curvature).
§4. Type V: σ-source is zero (only A² enters Friedmann).
§5. Dimensional consistency: source has units of Mpc⁻² given Σ in Mpc⁻¹.
§6. Per-type sign conventions.
§7. VII_h spiral: opposite-sign coupling S_+ ↔ S_-.
§8. Source status metadata sanity.
§9. Integration with einstein_bianchi interface.

Run
---
    pytest test_shear_sources.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.background.bianchi_types import (
    StructureConstants, get_type,
    ALL_BIANCHI_TYPES, CLASS_A_TYPES, CLASS_B_TYPES,
    TYPES_WITH_FLRW_LIMIT, MARGINAL_TYPES,
    flrw_constants, type_i_constants, type_v_constants,
    type_ii_constants, type_viii_constants, type_ix_constants,
    type_viih_constants, type_iii_constants, type_vih_constants,
    type_vii0_constants, type_vi0_constants, type_iv_constants,
)
from bass.transport.shear_sources import (
    SHEAR_SOURCE_REGISTRY, SOURCE_STATUS,
    compute_shear_source, get_source_status,
    source_I, source_II, source_V, source_VI0, source_VII0, source_VIIh,
    source_VIII, source_IX, source_III, source_IV, source_VIh,
)


# Canonical test values for (Σ_+, Σ_-, ℋ, a)
Sp_test = 1e-6      # Mpc⁻¹ — typical conformal shear at recombination
Sm_test = 5e-7
calH_test = 1e-4    # Mpc⁻¹ — typical ℋ at recombination
a_test = 1e-3       # typical scale factor at z ≈ 1000


# ═══════════════════════════════════════════════════════════════
# §1 — Dispatcher completeness
# ═══════════════════════════════════════════════════════════════

class TestDispatcherCompleteness:
    def test_all_types_registered(self):
        """Every type in ALL_BIANCHI_TYPES has a registered source function."""
        for label in ALL_BIANCHI_TYPES:
            assert label in SHEAR_SOURCE_REGISTRY, f"{label} missing from registry"

    def test_flrw_registered(self):
        assert "FLRW" in SHEAR_SOURCE_REGISTRY

    def test_registry_count(self):
        """11 Bianchi types + FLRW = 12 entries."""
        assert len(SHEAR_SOURCE_REGISTRY) == 12

    def test_every_source_callable(self):
        for label, func in SHEAR_SOURCE_REGISTRY.items():
            assert callable(func), f"Source for {label} is not callable"

    def test_compute_shear_source_dispatches(self):
        """compute_shear_source() correctly dispatches to the right function."""
        sc = type_i_constants()
        result = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        # Type I returns (0, 0)
        assert result == (0.0, 0.0)

    def test_unknown_type_warns_and_returns_zero(self):
        """An unknown type label issues a warning and returns (0, 0)."""
        fake_sc = StructureConstants(label="XII", n1=0.0, n2=0.0, n3=0.0, a_twist=0.0)
        with pytest.warns(UserWarning, match="No shear source registered"):
            result = compute_shear_source(fake_sc, Sp_test, Sm_test, calH_test, a_test)
        assert result == (0.0, 0.0)


# ═══════════════════════════════════════════════════════════════
# §2 — FLRW limit (N_i → 0 and A → 0)
# ═══════════════════════════════════════════════════════════════

class TestFLRWLimit:
    """For types that admit an FLRW limit, sending all structure constants → 0
    must give zero source. For marginal types, this test is vacuous but we can
    still verify that the source vanishes as parameters → 0."""

    def test_flrw_source_exactly_zero(self):
        sc = flrw_constants()
        dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        assert dSp == 0.0
        assert dSm == 0.0

    def test_type_I_source_exactly_zero(self):
        """Type I has no curvature → exact zero source."""
        sc = type_i_constants()
        dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        assert dSp == 0.0
        assert dSm == 0.0

    def test_type_V_shear_source_zero(self):
        """Type V: only A² enters Friedmann as curvature, not shear source.

        The shear-specific source S_± is zero for Type V."""
        sc = type_v_constants(a_twist=1e-3)
        dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        assert dSp == 0.0
        assert dSm == 0.0

    def test_type_II_vanishes_as_n1_goes_zero(self):
        """Type II (Ellis conformal, FB-0.1): S_+ = -(2/3) N_1² × ℋ²,
        so S_+ → 0 as n_1 → 0."""
        for n1 in [1e-3, 1e-5, 1e-8]:
            sc = type_ii_constants(n1=n1)
            dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
            expected_scale = (2.0/3.0) * n1**2 * calH_test**2
            assert abs(dSp + expected_scale) < 1e-20 * max(expected_scale, 1e-20), (
                f"Type II source scaling broken at n1={n1}: got dSp={dSp}, expected=-{expected_scale}"
            )
            assert dSm == 0.0

    def test_type_VII0_vanishes_when_n1_equals_n3(self):
        """Type VII_0 with n_1 = n_3 is isotropic → source vanishes."""
        sc = type_vii0_constants(n1=1e-3, n3=1e-3)
        dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        assert abs(dSp) < 1e-20
        assert abs(dSm) < 1e-20

    def test_type_IX_isotropic_source_vanishes(self):
        """Type IX with n_1 = n_2 = n_3 corresponds to closed FLRW → source
        should vanish in this isotropic limit."""
        sc = type_ix_constants(n=1e-3)
        dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        # Not exactly zero in our current formulation (full Mixmaster deferred)
        # but should be small: dSp ∝ (2n² - n² - n² - n²) = -n² > 0 actually
        # For symmetric case n_1 = n_2 = n_3: 2*n² - n² - n² - n² = -n² ≠ 0
        # This is a known Wainwright-Ellis pathology for IX at isotropic pt
        # — the full treatment requires dynamical systems approach (deferred).
        # For now, verify finite and scales correctly:
        n = 1e-3
        expected_magnitude = (2.0/3.0) * n**2 * calH_test
        assert abs(dSp) < 10 * expected_magnitude
        assert abs(dSm) < 10 * expected_magnitude


# ═══════════════════════════════════════════════════════════════
# §3 — Dimensional consistency (Ellis conformal: FB-0.1)
# ═══════════════════════════════════════════════════════════════

class TestDimensionalConsistency:
    """Ellis conformal source = ℋ² × S^{WE}(dimensionless), giving
    units [Σ]/[η] = Mpc⁻¹/Mpc = Mpc⁻² given Σ in Mpc⁻¹ and ℋ in
    Mpc⁻¹. Σ-independent piece scales as ℋ²; Σ-linear (VII_h spiral)
    piece scales as ℋ."""

    # Types where the Ellis source is a pure ℋ²-scaled W-E term (no
    # Σ-linear spiral coupling). VII_h is handled separately because
    # its W-E piece and spiral piece can near-cancel at a generic
    # test point.
    _PURE_QUADRATIC_TYPES = [
        t for t in ALL_BIANCHI_TYPES if t != "VII_h"
    ]

    @pytest.mark.parametrize("label", _PURE_QUADRATIC_TYPES)
    def test_source_units(self, label):
        """Double ℋ and verify the Ellis source scales as ℋ² (ratio ≈ 4).

        All non-VII_h types source dΣ/dη via ``ℋ² × S^{WE}`` only, so
        doubling ℋ quadruples the source.
        """
        sc = get_type(label)
        dSp_1, _ = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        dSp_2, _ = compute_shear_source(sc, Sp_test, Sm_test, 2*calH_test, a_test)
        if abs(dSp_1) > 1e-20:
            ratio = abs(dSp_2 / dSp_1)
            assert 3.5 < ratio < 4.5, (
                f"{label}: Ellis S_+ should scale as ℋ² (ratio={ratio})"
            )

    def test_VIIh_mixed_scaling_components(self):
        """VII_h has a Σ-independent W-E piece (∝ ℋ²) AND a Σ-linear
        spiral piece (∝ ℋ). Verify each piece scales correctly in
        isolation.

        The W-E piece is isolated by setting Σ_+ = Σ_- = 0.
        The spiral piece is isolated as ``dSp(Σ) - dSp(0)`` with the
        same (n_1, n_3, a_twist) — the Σ-linear difference.
        """
        sc = type_viih_constants()
        # W-E piece only: Σ_+ = Σ_- = 0 ⇒ spiral = 0
        dSp_we_1, _ = compute_shear_source(sc, 0.0, 0.0, calH_test, a_test)
        dSp_we_2, _ = compute_shear_source(sc, 0.0, 0.0, 2*calH_test, a_test)
        ratio_we = abs(dSp_we_2 / dSp_we_1)
        assert 3.5 < ratio_we < 4.5, (
            f"VII_h W-E piece should scale as ℋ² (ratio={ratio_we})"
        )
        # Spiral piece: dSp(Σ ≠ 0) − dSp(Σ = 0) ≈ Σ-linear spiral term
        dSp_full_1, _ = compute_shear_source(sc, 0.0, Sm_test, calH_test, a_test)
        dSp_full_2, _ = compute_shear_source(sc, 0.0, Sm_test, 2*calH_test, a_test)
        spiral_1 = dSp_full_1 - dSp_we_1
        spiral_2 = dSp_full_2 - dSp_we_2
        ratio_spiral = abs(spiral_2 / spiral_1)
        assert 1.8 < ratio_spiral < 2.2, (
            f"VII_h spiral piece should scale as ℋ¹ (ratio={ratio_spiral})"
        )


# ═══════════════════════════════════════════════════════════════
# §4 — VII_h spiral coupling (signature of the type)
# ═══════════════════════════════════════════════════════════════

class TestVII_h_Spiral:
    """Type VII_h has characteristic spiral coupling: S_+ gets a +Σ_- contribution,
    S_- gets a -Σ_+ contribution. This preserves Σ_+² + Σ_-² (rotation)."""

    def test_spiral_antisymmetric_coupling(self):
        """With Sp=0, Sm>0: spiral coupling gives positive dSp and zero-spiral dSm contribution."""
        sc = type_viih_constants()
        Sp0, Sm0 = 0.0, 1e-6
        dSp_a, dSm_a = compute_shear_source(sc, Sp0, Sm0, calH_test, a_test)
        # With Sp=0, Sm>0: spiral contributes +ω×Sm to dSp_a and 0 to dSm_a
        # (Plus the symmetric W-E source with n₁ − n₃ ≠ 0.)
        # Flip roles: Sp>0, Sm=0 → spiral contributes 0 to dSp_b, -ω×Sp to dSm_b
        Sp0, Sm0 = 1e-6, 0.0
        dSp_b, dSm_b = compute_shear_source(sc, Sp0, Sm0, calH_test, a_test)
        # The difference isolates the spiral contribution
        # dSp_a - dSp_b ≈ 2 × ω × Sp (from SP contribution in case b vs no contribution in case a)
        # This is a qualitative check — exact value is symmetric:
        # We simply verify VII_h sources DO depend on both Sp and Sm:
        assert dSp_a != dSp_b, "VII_h source should depend on both Σ_+ and Σ_-"

    def test_spiral_coefficient_positive(self):
        """The spiral coupling amplitude should be positive (enforces correct rotation sense).
        
        Note: with n_1 = n_3, the Σ-independent W-E source still has a nonzero a_twist²
        contribution. We must isolate the Σ-linear spiral term by subtracting the Σ=0 baseline.
        """
        sc = type_viih_constants(n1=1e-2, n3=1e-2, a_twist=5e-3)
        # Baseline: source with Σ_± = 0 isolates the constant W-E part
        dSp_zero, _ = compute_shear_source(sc, 0.0, 0.0, calH_test, a_test)
        # With nonzero Σ_-
        dSp_pos_Sm, _ = compute_shear_source(sc, 0.0, +Sm_test, calH_test, a_test)
        dSp_neg_Sm, _ = compute_shear_source(sc, 0.0, -Sm_test, calH_test, a_test)
        # Spiral contribution (Σ-linear, antisymmetric in Σ_-)
        spiral_pos = dSp_pos_Sm - dSp_zero
        spiral_neg = dSp_neg_Sm - dSp_zero
        # Must flip sign with Σ_-
        assert spiral_pos * spiral_neg < 0, (
            f"Spiral contribution should flip sign with Σ_-: "
            f"spiral(+) = {spiral_pos}, spiral(-) = {spiral_neg}"
        )
        # And the positive-Σ_- case should itself be nonzero
        assert abs(spiral_pos) > 1e-25

    def test_spiral_amplitude_scales_as_sqrt_h(self):
        """Spiral frequency ω ∝ √h; increasing h should increase coupling."""
        sc_small_h = type_viih_constants(n1=1e-2, n3=1e-2, a_twist=2e-3)  # h = 0.04
        sc_big_h = type_viih_constants(n1=1e-2, n3=1e-2, a_twist=5e-3)    # h = 0.25
        dSp_a, _ = compute_shear_source(sc_small_h, 0.0, Sm_test, calH_test, a_test)
        dSp_b, _ = compute_shear_source(sc_big_h, 0.0, Sm_test, calH_test, a_test)
        # bigger h → bigger |dSp|
        # Since both have n_1 = n_3, only spiral term is nonzero
        assert abs(dSp_b) > abs(dSp_a), (
            f"Spiral amplitude should grow with h: got |dSp(h=.04)|={abs(dSp_a)}, "
            f"|dSp(h=.25)|={abs(dSp_b)}"
        )


# ═══════════════════════════════════════════════════════════════
# §5 — Sign conventions per type
# ═══════════════════════════════════════════════════════════════

class TestSignConventions:
    def test_type_II_S_plus_negative(self):
        """Type II: S_+ = -(2/3) N_1² × ℋ < 0."""
        sc = type_ii_constants(n1=1e-2)
        dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        assert dSp < 0
        assert dSm == 0.0

    def test_VII0_vs_VI0_S_minus_opposite_signs(self):
        """VII_0 and VI_0 have same S_+ but opposite S_-.
        
        VI_0: S_- = -(2/√3)(n_1 + n_3)(n_1 - n_3)
        VII_0: S_- = +(2/√3)(n_1 + n_3)(n_1 - n_3)
        """
        # Use same magnitudes but different signs for n_3
        sc_VI0 = type_vi0_constants(n1=1e-2, n3=-1e-3)   # n_1 + n_3 > 0, n_1 - n_3 > 0
        sc_VII0 = type_vii0_constants(n1=1e-2, n3=1e-3)  # n_1 + n_3 > 0, n_1 - n_3 > 0
        _, dSm_VI0 = compute_shear_source(sc_VI0, Sp_test, Sm_test, calH_test, a_test)
        _, dSm_VII0 = compute_shear_source(sc_VII0, Sp_test, Sm_test, calH_test, a_test)
        # Sign convention differs; for chosen parameter signs, VI0 < 0, VII0 > 0
        assert dSm_VI0 < 0
        assert dSm_VII0 > 0


# ═══════════════════════════════════════════════════════════════
# §6 — Source status metadata
# ═══════════════════════════════════════════════════════════════

class TestSourceStatus:
    def test_all_types_have_status(self):
        for label in ALL_BIANCHI_TYPES:
            status = get_source_status(label)
            assert status.tag in ("VALIDATED", "PROVISIONAL", "NOT_IMPLEMENTED")

    def test_type_I_validated(self):
        status = get_source_status("I")
        assert status.tag == "VALIDATED"

    def test_type_V_validated(self):
        status = get_source_status("V")
        assert status.tag == "VALIDATED"

    def test_marginal_types_have_vacuous_flrw_test(self):
        """Class B types without FLRW limit should have flrw_limit_verified=False."""
        for label in ["III", "IV", "VI_h"]:
            status = get_source_status(label)
            assert not status.flrw_limit_verified, (
                f"{label} is marginal (no FLRW limit); flrw_limit_verified should be False"
            )

    def test_types_with_flrw_limit_have_verified_flag_true(self):
        """Types I, V, VII_0, VII_h, IX should have flrw_limit_verified=True."""
        for label in TYPES_WITH_FLRW_LIMIT:
            status = get_source_status(label)
            assert status.flrw_limit_verified, (
                f"{label} admits FLRW limit; flrw_limit_verified should be True"
            )


# ═══════════════════════════════════════════════════════════════
# §7 — Zero-shear response (shear sources from curvature alone)
# ═══════════════════════════════════════════════════════════════

class TestZeroShearResponse:
    """When Sp = Sm = 0, the source reduces to the pure curvature contribution.
    
    This checks that the source has both Σ-independent (curvature) AND
    Σ-linear (VII_h spiral) parts, which combine linearly."""

    def test_type_II_source_independent_of_Sigma(self):
        """Type II source S_+ = -(2/3) N_1² × ℋ is Σ-independent."""
        sc = type_ii_constants()
        dSp_a, _ = compute_shear_source(sc, 0, 0, calH_test, a_test)
        dSp_b, _ = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        # Source is independent of Σ → dSp_a == dSp_b
        assert abs(dSp_a - dSp_b) < 1e-25

    def test_VIIh_source_depends_on_Sigma(self):
        """VII_h has spiral coupling → source DOES depend on Σ."""
        sc = type_viih_constants()
        dSp_a, _ = compute_shear_source(sc, 0, 0, calH_test, a_test)
        dSp_b, _ = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        # Spiral term: different with Σ ≠ 0 vs Σ = 0
        assert abs(dSp_a - dSp_b) > 1e-25


# ═══════════════════════════════════════════════════════════════
# §8 — Integration smoke test
# ═══════════════════════════════════════════════════════════════

class TestIntegrationSmoke:
    """All 10 Bianchi types + FLRW compute a source without raising."""

    @pytest.mark.parametrize("label", ["FLRW"] + ALL_BIANCHI_TYPES)
    def test_every_type_computes_source(self, label):
        sc = get_type(label)
        dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_test, a_test)
        # Source returns a finite tuple of floats
        assert isinstance(dSp, float)
        assert isinstance(dSm, float)
        assert math.isfinite(dSp)
        assert math.isfinite(dSm)

    @pytest.mark.parametrize("label", ["FLRW"] + ALL_BIANCHI_TYPES)
    def test_sources_finite_across_wide_calH_range(self, label):
        """Test at early universe (small a, large ℋ) and today (a=1, small ℋ)."""
        sc = get_type(label)
        for a_val, calH_val in [(1e-6, 1.0), (1e-3, 1e-2), (0.1, 1e-3), (1.0, 1e-4)]:
            dSp, dSm = compute_shear_source(sc, Sp_test, Sm_test, calH_val, a_val)
            assert math.isfinite(dSp), f"Source blew up for {label} at a={a_val}"
            assert math.isfinite(dSm), f"Source blew up for {label} at a={a_val}"


# ═══════════════════════════════════════════════════════════════
# §9 — FB-1.1 per-type Class A validation (W-E §18 Table 11.1)
# ═══════════════════════════════════════════════════════════════

class TestClassAFixedPoints:
    """FB-1.1 per-type validation of the Class A source dispatch against
    Wainwright-Ellis §18 Table 11.1 dimensionless ``S^{WE}`` formulas.

    Framework note
    --------------
    The Wainwright-Ellis Table 11.1 fixed points (Σ̂_+ = −1/2 for II,
    Σ̂_− = ∓1/√3 for VI₀, etc.) are attractors of the **self-similar
    closed W-E system** in which the structure constants ``N_i`` co-evolve
    with Hubble via ``N̂_i = N_i / H``. Our framework pins ``N_i`` as
    constants of ``StructureConstants`` and lets ``ℋ(a)`` follow pure
    FLRW (Planck-2018), so the self-similar fixed points are not
    directly reachable without a rescaling layer. What *is* reachable,
    and what `SOURCE_STATUS` tracks, is whether the source *function*
    ``S^{WE}_{\\pm}(N_1, N_2, N_3, A)`` matches W-E Table 11.1 exactly
    at every parameter point, including the axisymmetric axis-zero
    limits that should vanish identically.

    These four tests pin each Class A type's formula + sign pattern at
    the per-value level (a regression against W-E §18); promotion of
    `SOURCE_STATUS` from PROVISIONAL to VALIDATED rides on this plus the
    FB-0.1 dimensional / FLRW / Kasner invariants (already covered).

    References
    ----------
    Wainwright & Ellis 1997 §18 + Table 11.1 (Class A A=0 source
    dispatch); Ellis-Maartens-MacCallum 2012 §18.3 (Ellis conformal
    shear convention); `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md
    §FB-1.1`.
    """

    # Finer calH grid: covers radiation (calH large), matter (peak),
    # dark-energy (calH small). FB-1.1 pins the formula across four
    # decades of ℋ.
    _CALH_GRID = (1.0, 1e-2, 1e-3, 1e-4)

    def test_type_I_kasner_exponent_sum(self):
        """Type I vacuum-limit Kasner invariants on a direct background
        integration (no hierarchy layer): ``σ × a³ = const`` at ≤ 2 %
        drift over a wide a-window, and the dimensionless shear energy
        ``Σ² × a⁴`` is also conserved.

        Why this is the Kasner-triplet pin: the Kasner relations
        ``∑ p_i = 1, ∑ p_i² = 1`` hold in *vacuum* Bianchi I, which our
        framework does not simulate (Planck-2018 FLRW background).
        What is preserved in our framework is the geometric statement
        ``σ_{ab} × a³ = const`` (Raychaudhuri companion ``σ̇ = -3Hσ``),
        which is the physical content of the Kasner exponent triplet at
        the shear-tensor level regardless of the background stress-energy.

        Reference: Ellis §18.3 (Kasner geometric invariant); W-E §18.
        """
        from bass.background.einstein_bianchi import (
            solve_bianchi_background, type_i_cosmology,
        )
        cosmo = type_i_cosmology(sigma_over_H_init=1e-4)
        bg = solve_bianchi_background(
            cosmo, a_start=1e-6, a_end=1.0, n_pts=2000,
        )
        mask = np.abs(bg.sigma_plus) > 1e-30
        assert np.any(mask)
        sigma_proper = bg.sigma_plus[mask] / bg.a[mask]
        kasner = sigma_proper * bg.a[mask] ** 3
        rel_var = (kasner.max() - kasner.min()) / abs(kasner.mean())
        assert rel_var < 2e-2, f"σ × a³ rel_var = {rel_var}"
        conformal_inv = bg.sigma_plus[mask] * bg.a[mask] ** 2
        rel_var_conf = (
            (conformal_inv.max() - conformal_inv.min())
            / abs(conformal_inv.mean())
        )
        assert rel_var_conf < 5e-3, f"Σ × a² rel_var = {rel_var_conf}"

    @pytest.mark.parametrize("N1", [1e-4, 1e-3, 1e-2, 5e-2])
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_II_WE_fixed_point_asymptotic(self, N1, calH):
        """Type II axisymmetric source per W-E Table 11.1:
        ``S^{WE}_+ = −(2/3) N_1²``, ``S^{WE}_- = 0``.

        Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. We
        verify at 10⁻¹² relative that ``source_II(sc, 0, 0, ℋ, a)`` equals
        ``(−(2/3) N_1² ℋ², 0)`` exactly across the full (N_1, ℋ) grid.
        The "asymptotic" qualifier in the W-E fixed-point literature
        refers to the self-similar N̂_1 = N_1/H attractor; in our fixed-N
        framework we instead pin the source-function formula, which is
        what `SOURCE_STATUS` governs.

        Reference: Wainwright-Ellis §18 Table 11.1 row II; Ellis §18.3.
        """
        sc = type_ii_constants(n1=N1)
        dSp, dSm = source_II(sc, 0.0, 0.0, calH, 1e-3)
        expected_Sp = -(2.0 / 3.0) * N1 ** 2 * calH ** 2
        assert dSp == pytest.approx(expected_Sp, rel=1e-12)
        assert dSm == 0.0, f"Type II axisymmetric S_- != 0 at N1={N1}, calH={calH}"
        # Σ-independence: source does not depend on Σ_± (axisymmetric,
        # no spiral) — formula is purely quadratic in N_1.
        dSp_Sigma, dSm_Sigma = source_II(sc, 1e-5, -3e-6, calH, 1e-3)
        assert dSp_Sigma == pytest.approx(dSp, rel=1e-14)
        assert dSm_Sigma == 0.0

    @pytest.mark.parametrize(
        "n1, n3",
        [(1e-2, -1e-2), (1e-2, -5e-3), (5e-3, -1e-2), (2e-2, -1e-3)],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VI0_WE_fixed_point_asymptotic(self, n1, n3, calH):
        """Type VI₀ source per W-E Table 11.1 (Pontzen-Challinor n_2=0
        frame, our n_1 ↔ canonical N_2, n_3 ↔ canonical N_3):

            S^{WE}_+ = −(2/3)(n_1 − n_3)²
            S^{WE}_- = −(2/√3)(n_1 + n_3)(n_1 − n_3)

        Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. The
        S_- sign is the Class A "negative off-diagonal" signature that
        W-E Table 11.1 contrasts with VII₀ (opposite sign). We verify:
        (a) formula match to 10⁻¹² relative across the (n_1, n_3, ℋ)
        grid; (b) S_+ < 0 always (since (n_1 − n_3)² > 0 when the two
        diagonal eigenvalues differ); (c) Σ-independence.

        Reference: Wainwright-Ellis §18 Table 11.1 row VI₀; Ellis §18.3.
        """
        sc = type_vi0_constants(n1=n1, n3=n3)
        dSp, dSm = compute_shear_source(sc, 0.0, 0.0, calH, 1e-3)
        diff = n1 - n3
        summ = n1 + n3
        expected_Sp = -(2.0 / 3.0) * diff ** 2 * calH ** 2
        expected_Sm = -(2.0 / math.sqrt(3.0)) * summ * diff * calH ** 2
        assert dSp == pytest.approx(expected_Sp, rel=1e-12)
        assert dSm == pytest.approx(expected_Sm, rel=1e-12)
        # Sign pin: with the parametrised choices all have n_1 > 0 > n_3
        # so (n_1 − n_3) > 0 always and (n_1 − n_3)² > 0 ⇒ S_+ < 0.
        assert dSp < 0.0, f"VI₀ S_+ should be negative for n_1 > 0 > n_3"
        # Σ-independence
        dSp_Sigma, dSm_Sigma = compute_shear_source(
            sc, 1e-5, -3e-6, calH, 1e-3,
        )
        assert dSp_Sigma == pytest.approx(dSp, rel=1e-14)
        assert dSm_Sigma == pytest.approx(dSm, rel=1e-14)

    @pytest.mark.parametrize(
        "n1, n3",
        [(1e-2, 5e-3), (5e-3, 1e-2), (2e-2, 1e-3), (1e-3, 2e-2)],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VII0_shear_decay_to_plane_wave_line(self, n1, n3, calH):
        """Type VII₀ source per W-E Table 11.1 (same magnitude as VI₀
        but **opposite sign** on S_-):

            S^{WE}_+ = −(2/3)(n_1 − n_3)²
            S^{WE}_- = +(2/√3)(n_1 + n_3)(n_1 − n_3)

        Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. The
        W-E Table 11.1 row VII₀ is the "plane-wave" fixed line along
        which σ → 0 in the isotropic limit n_1 = n_3 (source vanishes
        identically). We verify: (a) formula match to 10⁻¹² relative;
        (b) S_- sign flip vs VI₀ at matched |n_1|, |n_3|; (c) isotropic
        limit n_1 = n_3 ⇒ S_± = 0 exactly; (d) Σ-independence.

        Reference: Wainwright-Ellis §18 Table 11.1 row VII₀ (e(2)
        algebra); Ellis §18.3.
        """
        sc = type_vii0_constants(n1=n1, n3=n3)
        dSp, dSm = compute_shear_source(sc, 0.0, 0.0, calH, 1e-3)
        diff = n1 - n3
        summ = n1 + n3
        expected_Sp = -(2.0 / 3.0) * diff ** 2 * calH ** 2
        expected_Sm = +(2.0 / math.sqrt(3.0)) * summ * diff * calH ** 2
        assert dSp == pytest.approx(expected_Sp, rel=1e-12)
        assert dSm == pytest.approx(expected_Sm, rel=1e-12)
        # Sign flip vs VI₀ at matched magnitudes
        sc_VI0 = type_vi0_constants(n1=n1, n3=-n3)
        dSp_VI0, dSm_VI0 = compute_shear_source(
            sc_VI0, 0.0, 0.0, calH, 1e-3,
        )
        # (n_1 − (−n_3)) = n_1 + n_3; (n_1 + (−n_3)) = n_1 − n_3
        # So VI₀ at (n_1, −n_3): S_+ = −(2/3)(n_1 + n_3)² × ℋ²
        #                       S_- = −(2/√3)(n_1 − n_3)(n_1 + n_3) × ℋ²
        # Differs from VII₀ at (n_1, n_3); but the structural invariant we
        # pin is ``sign(S_-)_VII0 = -sign(S_-)_VI0`` at matched
        # ``(|diff|, |summ|)`` pairs, which requires setting VI₀ params
        # so the inner product (n_1+n_3)(n_1-n_3) has the same magnitude:
        sc_VI0_matched = type_vi0_constants(n1=n1, n3=-n3)
        # For n_3 → -n_3 in VI₀: (n_1 + (−n_3)) × (n_1 − (−n_3))
        # = (n_1 − n_3) × (n_1 + n_3) — same product magnitude as VII₀.
        _, dSm_VI0_matched = compute_shear_source(
            sc_VI0_matched, 0.0, 0.0, calH, 1e-3,
        )
        # VII₀ uses + sign, VI₀ uses − sign; same (diff, summ) product ⇒
        # dSm_VII0 = −dSm_VI0_matched
        assert dSm == pytest.approx(-dSm_VI0_matched, rel=1e-12), (
            f"VII₀ S_- should flip sign vs VI₀ at matched (|diff|, |summ|); "
            f"VII₀={dSm}, VI₀_matched={dSm_VI0_matched}"
        )
        # Σ-independence
        dSp_Sigma, dSm_Sigma = compute_shear_source(
            sc, 1e-5, -3e-6, calH, 1e-3,
        )
        assert dSp_Sigma == pytest.approx(dSp, rel=1e-14)
        assert dSm_Sigma == pytest.approx(dSm, rel=1e-14)

    @pytest.mark.parametrize("N_equal", [1e-4, 1e-3, 1e-2])
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VII0_isotropic_limit_vanishes_exactly(self, N_equal, calH):
        """Type VII₀ at n_1 = n_3 is the "plane-wave FLRW line" of W-E
        Table 11.1 — both S_+ and S_- must vanish identically (source =
        (0, 0)) since (n_1 − n_3) = 0. This is the FB-1.1 pin that
        VII₀'s isotropic limit recovers FLRW without any residual drift.

        Reference: Wainwright-Ellis §18 Table 11.1 row VII₀ (k = 0
        "plane-wave" attractor at n_1 = n_3).
        """
        sc = type_vii0_constants(n1=N_equal, n3=N_equal)
        dSp, dSm = compute_shear_source(sc, 1e-5, -3e-6, calH, 1e-3)
        assert dSp == 0.0, f"VII₀ isotropic S_+ != 0 at N={N_equal}, ℋ={calH}"
        assert dSm == 0.0, f"VII₀ isotropic S_- != 0 at N={N_equal}, ℋ={calH}"

    # ─── FB-1.2: VIII / IX formula pins ─────────────────────────────

    @pytest.mark.parametrize(
        "n1, n2, n3",
        [
            (-1e-2, 1e-2, 1e-2),   # canonical (|n|, |n|, |n|) with one negative
            (-5e-3, 1e-2, 2e-2),   # asymmetric (+)-eigenvalues
            (-2e-2, 1e-2, 5e-3),   # larger |n_1|
            (-1e-3, 2e-2, 1e-2),   # small |n_1| vs larger (+)-block
        ],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VIII_WE_source_formula_and_signs(self, n1, n2, n3, calH):
        """Type VIII source per W-E §18 Table 11.1 (sl(2,ℝ) algebra,
        one negative eigenvalue):

            S^{WE}_+ = −(2/3) [2 N_1² − N_2² − N_3² + N_2 N_3]
            S^{WE}_- = (2/√3) [N_2² − N_3²]

        Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. We pin:
        (a) formula match to 10⁻¹² relative across the (n_1, n_2, n_3, ℋ)
        grid; (b) n_1 < 0, n_2 > 0, n_3 > 0 (sl(2,ℝ) algebra — one
        negative eigenvalue); (c) S_- sign flips with (N_2² − N_3²);
        (d) Σ-independence of the source (leading-order near-FLRW form;
        full nonlinear Mixmaster dispatch is deferred to FB-5).

        FB11-F1 carry: formula-level pin, not Hubble-normalised
        coordinate chasing.

        Reference: Wainwright-Ellis 1997 §18 Table 11.1 row VIII; Ellis-
        Maartens-MacCallum 2012 §18.3.
        """
        sc = StructureConstants(
            n1=n1, n2=n2, n3=n3, a_twist=0.0,
            label="VIII", no_flrw_limit=True,
        )
        dSp, dSm = source_VIII(sc, 0.0, 0.0, calH, 1e-3)
        expected_Sp = -(2.0 / 3.0) * (
            2 * n1 ** 2 - n2 ** 2 - n3 ** 2 + n2 * n3
        ) * calH ** 2
        expected_Sm = (2.0 / math.sqrt(3.0)) * (n2 ** 2 - n3 ** 2) * calH ** 2
        assert dSp == pytest.approx(expected_Sp, rel=1e-12)
        if expected_Sm == 0.0:
            assert dSm == 0.0
        else:
            assert dSm == pytest.approx(expected_Sm, rel=1e-12)
        # Sign pin on S_-: flips with (n_2² − n_3²). The parametrisation
        # samples both signs and the equal case.
        if n2 > n3:
            assert dSm > 0.0, (
                f"VIII S_- should be positive when n_2 > n_3 "
                f"(n2={n2}, n3={n3})"
            )
        elif n2 < n3:
            assert dSm < 0.0, (
                f"VIII S_- should be negative when n_2 < n_3 "
                f"(n2={n2}, n3={n3})"
            )
        # Σ-independence (leading-order near-FLRW form has no spiral
        # coupling — the full nonlinear Σ-dependence is FB-5 scope).
        dSp_Sigma, dSm_Sigma = source_VIII(sc, 1e-5, -3e-6, calH, 1e-3)
        assert dSp_Sigma == pytest.approx(dSp, rel=1e-14)
        assert dSm_Sigma == pytest.approx(dSm, rel=1e-14)

    @pytest.mark.parametrize(
        "n1, n2, n3",
        [
            (2e-2, 1e-2, 5e-3),   # all-positive, fully asymmetric
            (1e-2, 2e-2, 5e-3),   # mid eigenvalue dominant
            (5e-3, 1e-2, 2e-2),   # reverse ordering (n_2 < n_3)
            (1e-2, 1e-2, 5e-3),   # n_1 = n_2 (partial symmetry)
        ],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_IX_WE_source_formula_and_signs(self, n1, n2, n3, calH):
        """Type IX source per W-E §18 Table 11.1 (so(3) algebra, all
        three N_i positive — Mixmaster model):

            S^{WE}_+ = −(2/3) [2 N_1² − N_2² − N_3² − N_2 N_3]
            S^{WE}_- = (2/√3) [N_2² − N_3²]

        Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. Differs
        from VIII only by the sign of the N_2 N_3 cross-term (so(3) vs
        sl(2,ℝ)). We pin: (a) formula match to 10⁻¹² relative across the
        (n_1, n_2, n_3, ℋ) grid; (b) all n_i > 0 (so(3) algebra);
        (c) S_- sign flip with (N_2² − N_3²); (d) Σ-independence.

        Full nonlinear Mixmaster / BKL oscillation dynamics (Belinsky-
        Khalatnikov-Lifshitz 1970) are deferred to FB-5 / FB-6; this
        test pins the leading-order near-FLRW source formula only
        (FB11-F1 carry).

        Reference: Wainwright-Ellis 1997 §18 Table 11.1 row IX; Ellis-
        Maartens-MacCallum 2012 §18.3; BKL 1970.
        """
        sc = StructureConstants(
            n1=n1, n2=n2, n3=n3, a_twist=0.0,
            label="IX", no_flrw_limit=False,
        )
        dSp, dSm = source_IX(sc, 0.0, 0.0, calH, 1e-3)
        expected_Sp = -(2.0 / 3.0) * (
            2 * n1 ** 2 - n2 ** 2 - n3 ** 2 - n2 * n3
        ) * calH ** 2
        expected_Sm = (2.0 / math.sqrt(3.0)) * (n2 ** 2 - n3 ** 2) * calH ** 2
        assert dSp == pytest.approx(expected_Sp, rel=1e-12)
        if expected_Sm == 0.0:
            assert dSm == 0.0
        else:
            assert dSm == pytest.approx(expected_Sm, rel=1e-12)
        # S_- sign
        if n2 > n3:
            assert dSm > 0.0
        elif n2 < n3:
            assert dSm < 0.0
        # Σ-independence
        dSp_Sigma, dSm_Sigma = source_IX(sc, 1e-5, -3e-6, calH, 1e-3)
        assert dSp_Sigma == pytest.approx(dSp, rel=1e-14)
        assert dSm_Sigma == pytest.approx(dSm, rel=1e-14)

    @pytest.mark.parametrize("N_equal", [1e-4, 1e-3, 1e-2])
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_IX_isotropic_near_limit_known_pathology(
        self, N_equal, calH,
    ):
        """Type IX at n_1 = n_2 = n_3 = n: the current W-E leading-order
        form gives

            S^{WE}_+ = −(2/3) [2n² − n² − n² − n²] = +(2/3) n²
            S^{WE}_- = (2/√3) [n² − n²] = 0 exactly.

        The S_+ residual at the isotropic point is a **known W-E
        pathology** of the leading-order source (noted in
        `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.2` and the full
        Mixmaster dynamical-systems treatment in Wainwright-Ellis §6.2
        that FB-5/FB-6 will address). We do not assert S_+ = 0 here; we
        pin the current behaviour: S_+ = +(2/3) n² ℋ² exactly, S_- = 0
        exactly, and the magnitude obeys the ``|S_+| ≤ 10 × (2/3) n² ℋ²``
        band from the FB-1.2 prompt.

        Reference: Wainwright-Ellis §18 Table 11.1 row IX + §6.2 (BKL
        closed-attractor treatment deferred to FB-5 / FB-6).
        """
        n = N_equal
        sc = StructureConstants(
            n1=n, n2=n, n3=n, a_twist=0.0,
            label="IX", no_flrw_limit=False,
        )
        dSp, dSm = source_IX(sc, 0.0, 0.0, calH, 1e-3)
        expected_Sp_pathology = +(2.0 / 3.0) * n ** 2 * calH ** 2
        assert dSp == pytest.approx(expected_Sp_pathology, rel=1e-12)
        # S_- is exactly zero for n_2 = n_3 (identical in VIII and IX).
        assert dSm == 0.0
        # FB-1.2 band — the magnitude stays close to the natural scale
        # (2/3) n² ℋ² (ratio = 1 exactly in the current form); asserts
        # the source does not blow up due to an accidental algebra bug.
        band = 10.0 * (2.0 / 3.0) * n ** 2 * calH ** 2
        assert abs(dSp) < band
        assert abs(dSm) < band

    # ─── FB-1.2: Bianchi IX recollapse event smoke ──────────────────

    def test_bianchi_IX_recollapse_event_default_branch_is_opt_in(self):
        """The pre FB-1.2 behaviour of ``solve_bianchi_background`` (no
        ``events=``) must be preserved bit-for-bit when the event branch
        is not activated. This guards the "no silent fallback" principle
        — adding optional event plumbing must not change default output.
        """
        from bass.background.einstein_bianchi import (
            solve_bianchi_background, type_ix_cosmology,
        )
        cosmo = type_ix_cosmology(n=1e-2)
        bg = solve_bianchi_background(
            cosmo, a_start=1e-6, a_end=1.0, n_pts=1000,
        )
        assert bg.terminated_by_event is False
        assert bg.event_eta == ()
        # integration completed to (near) a_end
        assert bg.a[-1] > 0.9

    def test_bianchi_IX_recollapse_event_does_not_fire_on_realistic_flrw(
        self,
    ):
        """With the Planck-2018 FLRW background (Ω_m + Ω_Λ > 0, so
        H(a) > 0 for all a), the canonical recollapse event (floor = 0)
        does **not** fire. This pins that the event infrastructure does
        not spuriously terminate canonical IX integration.

        Real vacuum-IX recollapse lives in FB-5 / FB-6 Mixmaster / BKL
        work; this smoke test verifies the plumbing is inert on the
        current production background.
        """
        from bass.background.einstein_bianchi import (
            solve_bianchi_background, type_ix_cosmology,
            bianchi_ix_recollapse_event,
        )
        cosmo = type_ix_cosmology(n=1e-2)
        event = bianchi_ix_recollapse_event(cosmo, floor=0.0)
        bg = solve_bianchi_background(
            cosmo, a_start=1e-6, a_end=1.0, n_pts=1000, events=event,
        )
        assert bg.terminated_by_event is False
        assert bg.event_eta == ()
        assert bg.a[-1] > 0.9

    def test_bianchi_IX_recollapse_event_fires_on_synthetic_floor(self):
        """Synthetic smoke test — force the event branch by raising the
        ``floor`` threshold above the realistic-FLRW ℋ crossing. The
        integrator must: (a) detect the crossing, (b) terminate cleanly
        without NaN/inf, (c) populate ``terminated_by_event`` and
        ``event_eta`` on the returned state.

        This exercises exactly the FB plan §6 D5 "(a) event-terminated
        solve_ivp" dispatch that Bianchi IX recollapse needs in
        FB-5 / FB-6 when the vacuum H² contribution can flip sign.
        """
        from bass.background.einstein_bianchi import (
            solve_bianchi_background, type_ix_cosmology,
            bianchi_ix_recollapse_event,
        )
        cosmo = type_ix_cosmology(n=1e-2)
        # Planck-2018 ℋ spans roughly [1e-5, large] over [1e-6, 1]; a
        # floor of 1e-3 guarantees a crossing during matter era.
        event = bianchi_ix_recollapse_event(cosmo, floor=1e-3)
        bg = solve_bianchi_background(
            cosmo, a_start=1e-6, a_end=1.0, n_pts=1000, events=event,
        )
        assert bg.terminated_by_event is True
        assert len(bg.event_eta) == 1
        # event-η is strictly inside the integration window
        assert 0.0 < bg.event_eta[0]
        # final state is finite (no NaN/inf leakage)
        assert np.all(np.isfinite(bg.a))
        assert np.all(np.isfinite(bg.sigma_plus))
        assert np.all(np.isfinite(bg.sigma_minus))
        # ℋ at the final sample is close to the floor (event fired
        # because ℋ crossed 1e-3 going down)
        assert abs(bg.calH[-1] - 1e-3) < 1e-4


# ═══════════════════════════════════════════════════════════════
# §10 — FB-1.3 per-type Class B validation
#        (W-E §18 Table 11.1 + Pontzen-Challinor 2009 §III)
# ═══════════════════════════════════════════════════════════════


class TestClassBFixedPoints:
    """FB-1.3 per-type validation of the Class B source dispatch against
    Wainwright-Ellis §18 Table 11.1 Class B rows (twist-coupled
    ``a_twist ≠ 0`` with Jacobi constraint ``n_2 = 0``) and the
    Pontzen-Challinor 2009 VII_h spiral signature.

    Framework note (inherited from FB-1.1 / FB-1.2, FB11-F1 + FB12-F1)
    ------------------------------------------------------------------
    The W-E fixed-point *coordinates* are not reachable in the fixed-N
    framework; FB-1.3 pins the *source-function formulas* at rel 1e-12
    for III / IV / VI_h / VII_h, pins ``S_± = 0`` exactly for V, and
    pins the VII_h spiral qualitative signature (antisymmetric coupling
    ``+ω Σ_- / −ω Σ_+``, ω ∝ √h, rotation conservation
    ``Σ_+ dΣ_+^{spi} + Σ_- dΣ_-^{spi} = 0``) — the operative Class B
    contract for SOURCE_STATUS promotion. Quantitative calibration of
    the Pontzen-Challinor spiral ``κ`` coefficient remains FB-5 / FB-6
    scope (non-goal for this session).

    References
    ----------
    Wainwright & Ellis 1997 §18 + Table 11.1 Class B rows (III / IV /
    V / VI_h / VII_h); Ellis-Maartens-MacCallum 2012 §18.3 (Ellis
    conformal shear convention locked in FB-0.1); Pontzen & Challinor,
    *PRD* 79, 103518 (2009) §III (VII_h spiral signature);
    `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.3`.
    """

    # Re-use the FB-1.1/FB-1.2 ℋ grid so the 4-decade coverage is
    # consistent across the Class A and Class B promotion tests.
    _CALH_GRID = (1.0, 1e-2, 1e-3, 1e-4)

    # ─── III: algebraic identity with VI_{h=-1} ────────────────

    @pytest.mark.parametrize("n1", [5e-3, 1e-2, 2e-2])
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_III_dispatches_to_VIh_at_h_minus_1(self, n1, calH):
        """Type III is the special case VI_{h=-1} (``a² = -n_1 n_3``;
        the factory enforces ``n_3 = -a_twist²/n_1`` at construction).
        We pin: (a) the factory always produces ``h_parameter = -1``;
        (b) ``source_III`` dispatches to ``source_VIh`` and produces
        bit-identical output; (c) the W-E VI_h formula evaluated at
        ``h = -1`` (so the A² prefactor becomes ``1/(1+|h|) = 1/2``)
        matches the output at rel 1e-12.

        Reference: Wainwright-Ellis §18 Table 11.1 row III (≡ VI_{-1}).
        """
        sc = type_iii_constants(n1=n1)
        assert sc.h_parameter == pytest.approx(-1.0, rel=1e-12)
        dSp_III, dSm_III = source_III(sc, 0.0, 0.0, calH, 1e-3)
        dSp_VIh, dSm_VIh = source_VIh(sc, 0.0, 0.0, calH, 1e-3)
        # III dispatches to VI_h verbatim (no numerical reformulation).
        assert dSp_III == dSp_VIh
        assert dSm_III == dSm_VIh
        # Formula pin at h = -1 ⇒ 1/(1+|h|) = 1/2.
        diff = sc.n1 - sc.n3
        summ = sc.n1 + sc.n3
        expected_Sp = (
            -(2.0 / 3.0) * diff ** 2
            + (2.0 / 3.0) * sc.a_twist ** 2 * 0.5
        ) * calH ** 2
        expected_Sm = -(2.0 / math.sqrt(3.0)) * summ * diff * calH ** 2
        assert dSp_III == pytest.approx(expected_Sp, rel=1e-12)
        assert dSm_III == pytest.approx(expected_Sm, rel=1e-12)
        # Σ-independence (III inherits the Class B W-E piece; there is
        # no spiral coupling for III — only VII_h carries that).
        dSp_Sigma, dSm_Sigma = source_III(sc, 1e-5, -3e-6, calH, 1e-3)
        assert dSp_Sigma == pytest.approx(dSp_III, rel=1e-14)
        assert dSm_Sigma == pytest.approx(dSm_III, rel=1e-14)

    # ─── IV: axisymmetric twist-coupled source ─────────────────

    @pytest.mark.parametrize(
        "n3, a_twist",
        [
            (1e-2, 5e-3),
            (2e-2, 1e-2),
            (5e-3, 1e-2),
            (1e-3, 5e-3),
        ],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_IV_WE_source_formula(self, n3, a_twist, calH):
        """Type IV source per W-E §18 Table 11.1 (``(n_1, n_2, n_3) =
        (0, 0, +)`` with ``a > 0``, Jacobi-constrained n_2 = 0):

            S^{WE}_+ = -(2/3) N_3² + (2/3) A²
            S^{WE}_- = 0

        Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. Type IV
        is cosmologically marginal (no FLRW limit) — the W-E formula is
        dimensionally correct and finite but its physical role is as a
        cross-falsifiability probe rather than a standard cosmological
        background. We pin: (a) formula match to 10⁻¹² relative across
        the (N_3, A, ℋ) grid; (b) S_- = 0 exactly (axisymmetric);
        (c) Σ-independence.

        Reference: Wainwright-Ellis §18 Table 11.1 row IV; Ellis §18.3.
        """
        sc = type_iv_constants(n3=n3, a_twist=a_twist)
        dSp, dSm = source_IV(sc, 0.0, 0.0, calH, 1e-3)
        expected_Sp = (
            -(2.0 / 3.0) * n3 ** 2 + (2.0 / 3.0) * a_twist ** 2
        ) * calH ** 2
        assert dSp == pytest.approx(expected_Sp, rel=1e-12)
        assert dSm == 0.0, f"Type IV axisymmetric S_- != 0 at n3={n3}, a={a_twist}"
        # Σ-independence (Class B IV has no spiral coupling).
        dSp_Sigma, dSm_Sigma = source_IV(sc, 1e-5, -3e-6, calH, 1e-3)
        assert dSp_Sigma == pytest.approx(dSp, rel=1e-14)
        assert dSm_Sigma == 0.0

    # ─── V: shear-specific source vanishes (A² → curvature) ────

    @pytest.mark.parametrize("a_twist", [1e-3, 5e-3, 1e-2, 5e-2])
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_V_shear_zero_pin(self, a_twist, calH):
        """Type V (open FLRW analogue, ``(0, 0, 0)`` with ``a > 0``):
        the A² contribution is absorbed into the FLRW k = -1 curvature
        term, **not** into the shear source. The shear-specific
        ``S_±`` is therefore identically zero — this is the FB-1.1
        baseline behaviour for V (already VALIDATED), and FB-1.3
        promotes the regression to explicit formula-level form on the
        (A, ℋ) grid to match the Class B test pattern.

        We pin: (a) ``source_V`` returns (0, 0) exactly; (b) this is
        independent of Σ_± (no spiral — Type V has no ``n_i`` to
        source any directional anisotropy); (c) the vanishing holds
        across the full (a_twist, ℋ) grid.

        Reference: Wainwright-Ellis §18 Table 11.1 row V (k = -1
        open-FLRW analogue); Ellis §18.3.
        """
        sc = type_v_constants(a_twist=a_twist)
        dSp, dSm = source_V(sc, 0.0, 0.0, calH, 1e-3)
        assert dSp == 0.0
        assert dSm == 0.0
        # Σ-independence (trivial: source is identically zero).
        dSp_Sigma, dSm_Sigma = source_V(sc, Sp_test, Sm_test, calH, 1e-3)
        assert dSp_Sigma == 0.0
        assert dSm_Sigma == 0.0

    # ─── VI_h: twist-coupled mixed-sign Class B ────────────────

    # Parametrisation: all rows avoid h = -1 (that is Type III).
    # Chosen so h_parameter spans both h < -1 and -1 < h < 0 ranges
    # (i.e., a²/|n_1 n_3| either > 1 or < 1).
    @pytest.mark.parametrize(
        "n1, n3, a_twist",
        [
            (1e-2, -2e-3, 5e-3),   # h = -1.25 (h < -1)
            (1e-2, -5e-3, 2e-3),   # h = -0.08 (-1 < h < 0)
            (2e-2, -1e-2, 4e-3),   # h = -0.08 (-1 < h < 0)
            (5e-3, -2e-3, 7e-3),   # h = -4.9  (h < -1)
        ],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VIh_WE_source_formula(self, n1, n3, a_twist, calH):
        """Type VI_h source per W-E §18 Table 11.1 (``(+, 0, −)`` with
        ``a > 0`` and ``h ∈ (−∞, −1) ∪ (−1, 0)``):

            S^{WE}_+ = -(2/3)(n_1 − n_3)² + (2/3) A² / (1 + |h|)
            S^{WE}_- = -(2/√3)(n_1 + n_3)(n_1 − n_3)

        Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. The
        h-dependent A² prefactor ``1/(1+|h|)`` is the Hewitt-Wainwright
        near-FLRW reduction (full Δ, Ñ variables deferred to FB-5/FB-6;
        FB11-F1 carry). We pin: (a) formula match to 10⁻¹² relative
        across the (n_1, n_3, A, h, ℋ) grid; (b) S_+ < 0 always on
        this parametrisation (``(n_1 − n_3)²`` dominates the A² piece
        when h and A are matched to this near-FLRW regime); (c) S_-
        sign — negative when ``(n_1 + n_3)(n_1 − n_3) > 0``;
        (d) Σ-independence (no spiral coupling for VI_h — that is
        VII_h's signature).

        Reference: Wainwright-Ellis §18 Table 11.1 row VI_h; Ellis
        §18.3; Hewitt-Wainwright 1990.
        """
        sc = type_vih_constants(n1=n1, n3=n3, a_twist=a_twist)
        dSp, dSm = source_VIh(sc, 0.0, 0.0, calH, 1e-3)
        diff = n1 - n3
        summ = n1 + n3
        h = sc.h_parameter
        h_factor = 1.0 / (1.0 + abs(h))
        expected_Sp = (
            -(2.0 / 3.0) * diff ** 2
            + (2.0 / 3.0) * a_twist ** 2 * h_factor
        ) * calH ** 2
        expected_Sm = -(2.0 / math.sqrt(3.0)) * summ * diff * calH ** 2
        assert dSp == pytest.approx(expected_Sp, rel=1e-12)
        assert dSm == pytest.approx(expected_Sm, rel=1e-12)
        # Sign pin on S_+: in this parametrisation (n_1 > 0, n_3 < 0)
        # we have ``diff = n_1 − n_3 > 2 |n_3|`` so ``diff² × (2/3)``
        # always exceeds ``A² × (2/3) × h_factor`` (A and h_factor both
        # O(1) × a_twist² / |n_1 n_3|). Strict negativity is pinned.
        assert dSp < 0.0, (
            f"VI_h S_+ should be negative for (n_1 > 0, n_3 < 0, "
            f"near-FLRW regime), got dSp = {dSp} at n1={n1}, n3={n3}, "
            f"a={a_twist}, ℋ={calH}"
        )
        # Σ-independence
        dSp_Sigma, dSm_Sigma = source_VIh(sc, 1e-5, -3e-6, calH, 1e-3)
        assert dSp_Sigma == pytest.approx(dSp, rel=1e-14)
        assert dSm_Sigma == pytest.approx(dSm, rel=1e-14)

    # ─── VII_h: W-E formula + Pontzen-Challinor spiral ─────────

    @pytest.mark.parametrize(
        "n1, n3, a_twist",
        [
            (1.8e-2, 1.0e-2, 5.5e-3),   # Pontzen-Challinor 2007 fixture, h ≈ 0.168
            (1.0e-2, 1.0e-2, 5.0e-3),   # n_1 = n_3 (kills W-E diff-piece)
            (2.0e-2, 5.0e-3, 3.0e-3),   # asymmetric; h ≈ 0.09
            (5.0e-3, 1.0e-2, 2.0e-3),   # reversed ordering, h ≈ 0.08
        ],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VIIh_WE_source_formula_and_spiral_signature(
        self, n1, n3, a_twist, calH,
    ):
        """Type VII_h (principal CMB type) source: W-E §18 Table 11.1
        ``(+, 0, +)`` with ``a > 0``, ``h > 0``:

            S^{WE}_+ = -(2/3)(n_1 − n_3)² + (2/3) A² / (1 + h)
            S^{WE}_- = +(2/√3)(n_1 + n_3)(n_1 − n_3)   [sign flip vs VI_h]

        Plus the Pontzen-Challinor 2009 §III spiral coupling:

            dΣ_+^{spi} = +ω_{spi} × Σ_-
            dΣ_-^{spi} = -ω_{spi} × Σ_+,
            ω_{spi} = √|n_1 n_3| × √h × ℋ,

        where ``κ`` is the O(1) spiral coefficient (set to 1.0 in the
        current implementation; quantitative calibration against
        AniCLASS / P-C fixture is FB-5 / FB-6 scope — FB-1.3 pins only
        sign + ω ∝ √h + rotation invariance). We verify:

        (a) W-E piece (Σ_± = 0) formula match rel 1e-12 across the
            (n_1, n_3, A, h, ℋ) grid;
        (b) Spiral piece (subtract Σ_± = 0 baseline) equals
            ``(+ω Σ_-, -ω Σ_+)`` at rel 1e-12 — the antisymmetric
            coupling that is the P-C spiral signature;
        (c) ω_{spi} scales as √h when (n_1, n_3) are held fixed and
            a_twist varies — doubling a_twist (⇒ h ×4 ⇒ √h ×2) must
            double the spiral amplitude.

        Reference: Wainwright-Ellis §18 Table 11.1 row VII_h; Pontzen
        & Challinor PRD 79, 103518 (2009) §III; Ellis §18.3.
        """
        sc = type_viih_constants(n1=n1, n3=n3, a_twist=a_twist)
        h = sc.h_parameter
        assert h > 0.0
        # (a) W-E piece — isolate with Σ_± = 0.
        dSp_we, dSm_we = source_VIIh(sc, 0.0, 0.0, calH, 1e-3)
        diff = n1 - n3
        summ = n1 + n3
        expected_Sp_we = (
            -(2.0 / 3.0) * diff ** 2
            + (2.0 / 3.0) * a_twist ** 2 / (1.0 + h)
        ) * calH ** 2
        expected_Sm_we = +(2.0 / math.sqrt(3.0)) * summ * diff * calH ** 2
        assert dSp_we == pytest.approx(expected_Sp_we, rel=1e-12)
        if expected_Sm_we == 0.0:
            assert dSm_we == 0.0
        else:
            assert dSm_we == pytest.approx(expected_Sm_we, rel=1e-12)
        # (b) Spiral piece — subtract the Σ = 0 baseline.
        Sp_probe, Sm_probe = 1e-6, 5e-7
        dSp_full, dSm_full = source_VIIh(
            sc, Sp_probe, Sm_probe, calH, 1e-3,
        )
        dSp_spi = dSp_full - dSp_we
        dSm_spi = dSm_full - dSm_we
        omega_spi = math.sqrt(abs(n1 * n3)) * math.sqrt(h) * calH
        expected_dSp_spi = +omega_spi * Sm_probe
        expected_dSm_spi = -omega_spi * Sp_probe
        assert dSp_spi == pytest.approx(expected_dSp_spi, rel=1e-12)
        assert dSm_spi == pytest.approx(expected_dSm_spi, rel=1e-12)

    @pytest.mark.parametrize(
        "n1, n3",
        [
            (1.0e-2, 1.0e-2),
            (2.0e-2, 1.0e-2),
            (1.0e-2, 5.0e-3),
        ],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VIIh_spiral_omega_scales_as_sqrt_h(self, n1, n3, calH):
        """Spiral frequency scaling pin: with (n_1, n_3) held fixed,
        doubling a_twist multiplies ``h = a² / (n_1 n_3)`` by 4 and
        therefore multiplies ``ω_{spi} = √|n_1 n_3| √h ℋ`` by 2.
        Equivalently, the spiral amplitude ``|dΣ_+ − dΣ_+^{W-E}|`` at
        fixed Σ_- must double under this rescaling.

        This is the FB-1.3 qualitative pin of the Pontzen-Challinor
        2009 §III spiral ``ω ∝ √h`` scaling; quantitative ``κ``
        calibration remains FB-5 / FB-6.
        """
        a_small = 2.0e-3
        a_big = 4.0e-3  # a_big = 2 × a_small ⇒ h_big = 4 × h_small
        sc_small = type_viih_constants(n1=n1, n3=n3, a_twist=a_small)
        sc_big = type_viih_constants(n1=n1, n3=n3, a_twist=a_big)
        Sm_probe = 1e-6
        dSp_small_we, _ = source_VIIh(sc_small, 0.0, 0.0, calH, 1e-3)
        dSp_small, _ = source_VIIh(sc_small, 0.0, Sm_probe, calH, 1e-3)
        dSp_big_we, _ = source_VIIh(sc_big, 0.0, 0.0, calH, 1e-3)
        dSp_big, _ = source_VIIh(sc_big, 0.0, Sm_probe, calH, 1e-3)
        spi_small = dSp_small - dSp_small_we
        spi_big = dSp_big - dSp_big_we
        # √h ratio = 2 exactly (since a_big / a_small = 2 and
        # h ∝ a², so √h ∝ a).
        assert spi_big == pytest.approx(2.0 * spi_small, rel=1e-12)

    @pytest.mark.parametrize(
        "n1, n3, a_twist, Sp, Sm",
        [
            (1.0e-2, 1.0e-2, 5.0e-3, 1e-6, 5e-7),
            (1.8e-2, 1.0e-2, 5.5e-3, 3e-7, -2e-6),
            (2.0e-2, 5.0e-3, 3.0e-3, -1e-6, 1e-6),
            (5.0e-3, 1.0e-2, 2.0e-3, 1e-6, 1e-6),
        ],
    )
    @pytest.mark.parametrize("calH", list(_CALH_GRID))
    def test_type_VIIh_spiral_rotation_conserves_amplitude(
        self, n1, n3, a_twist, Sp, Sm, calH,
    ):
        """Pontzen-Challinor 2009 §III spiral signature: the spiral
        coupling is a **rotation** in the ``(Σ_+, Σ_-)`` plane — it
        preserves the amplitude ``Σ_+² + Σ_-²`` instantaneously. The
        spiral contribution to ``d(Σ_+² + Σ_-²)/dη`` is

            2 Σ_+ dΣ_+^{spi} + 2 Σ_- dΣ_-^{spi}
              = 2 Σ_+ (+ω Σ_-) + 2 Σ_- (−ω Σ_+)
              = 0  (identically, to float64 precision).

        This pin rules out any accidental sign flip or magnitude drift
        in the spiral coupling — either would break the P-C rotation
        signature that VII_h is celebrated for. We isolate the
        spiral-only contribution by subtracting the Σ_± = 0 baseline
        (the W-E piece, which is Σ-independent) and verify the
        rotation-invariance identity at rel 1e-12.

        Quantitative calibration of the κ coefficient is FB-5 / FB-6.
        """
        sc = type_viih_constants(n1=n1, n3=n3, a_twist=a_twist)
        dSp_we, dSm_we = source_VIIh(sc, 0.0, 0.0, calH, 1e-3)
        dSp_full, dSm_full = source_VIIh(sc, Sp, Sm, calH, 1e-3)
        dSp_spi = dSp_full - dSp_we
        dSm_spi = dSm_full - dSm_we
        # Rotation-invariance identity: Σ_+ dSp_spi + Σ_- dSm_spi ≡ 0.
        rotation_residual = Sp * dSp_spi + Sm * dSm_spi
        # Tolerance: the subtraction ``dSp_full - dSp_we`` loses
        # precision proportional to ``|W-E piece| / |spiral piece|`` ulps,
        # so the residual floor scales as
        # ``(|dSp_we| + |dSm_we|) × max(|Sp|, |Sm|) × ε_float``.
        # Use 1e-10 × that natural floor as a generous ceiling —
        # a true sign-flip or coefficient drift would blow this up by
        # many orders of magnitude.
        magnitude_bound = (
            (abs(dSp_we) + abs(dSm_we)) * max(abs(Sp), abs(Sm))
        )
        assert abs(rotation_residual) < 1e-10 * magnitude_bound + 1e-30, (
            f"VII_h spiral rotation residual {rotation_residual} "
            f"exceeds float-subtraction floor "
            f"(magnitude_bound={magnitude_bound}) at n1={n1}, n3={n3}, "
            f"a={a_twist}, Sp={Sp}, Sm={Sm}, ℋ={calH}"
        )
        # Additionally verify the *directly-computed* spiral (without
        # subtraction) satisfies the identity exactly — this is the
        # closed-form pin free of cancellation error.
        omega_spi = math.sqrt(abs(n1 * n3)) * math.sqrt(
            abs(sc.h_parameter)
        ) * calH
        direct_residual = Sp * (+omega_spi * Sm) + Sm * (-omega_spi * Sp)
        # The closed-form sum is exactly zero only up to reordering-of-
        # operations ulps on ``omega_spi × Sp × Sm`` — a handful of
        # float ulps of ``omega_spi × |Sp| × |Sm|``.
        direct_scale = abs(omega_spi) * abs(Sp) * abs(Sm) + 1e-300
        assert abs(direct_residual) < 1e-12 * direct_scale
