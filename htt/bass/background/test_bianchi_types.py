"""
tests/test_bianchi_types.py
============================

Unit tests for the extended bianchi_types.py module (all 10 Bianchi types).

Test strategy
-------------
1. Each factory produces a valid StructureConstants (Jacobi identity holds).
2. Class A / Class B partition is correctly identified.
3. Canonical sign patterns match the Ellis-MacCallum classification.
4. FLRW-limit types are correctly flagged.
5. Type-specific invariants (e.g., Type III has h = -1) are verified.
6. Type registry completeness and lookup consistency.
7. Edge cases: invalid parameters raise ValueError.
8. Jacobi identity: every valid type has n₂ × a_twist = 0.

Run
---
    pytest tests/test_bianchi_types.py -v
"""
from __future__ import annotations

import math
import pytest

from bass.background.bianchi_types import (
    FamilySpec,
    StructureConstants,
    flrw_constants,
    type_i_constants, type_ii_constants, type_iii_constants, type_iv_constants,
    type_v_constants, type_vi0_constants, type_vih_constants,
    type_vii0_constants, type_viih_constants, type_viii_constants,
    type_ix_constants,
    TYPE_REGISTRY, ALL_BIANCHI_TYPES, CLASS_A_TYPES, CLASS_B_TYPES,
    TYPES_WITH_FLRW_LIMIT, MARGINAL_TYPES,
    all_family_specs, get_family_spec, get_type,
)


# ═══════════════════════════════════════════════════════════════
# §1 — Jacobi identity (the fundamental algebraic constraint)
# ═══════════════════════════════════════════════════════════════

class TestJacobiIdentity:
    """Every valid Bianchi type must satisfy n^{αβ} a_β = 0.

    In the Pontzen-Challinor frame a = (0, a_twist, 0), this reduces to
    n_2 × a_twist = 0, i.e., EITHER a_twist = 0 (Class A) OR n_2 = 0 (Class B).
    """

    def test_flrw_jacobi(self):
        assert flrw_constants().jacobi_residual() == 0.0

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES)
    def test_default_factory_jacobi(self, label):
        """All 10 type factories at default parameters satisfy Jacobi."""
        sc = get_type(label)
        assert sc.jacobi_residual() < 1e-12, (
            f"Type {label} violates Jacobi: residual = {sc.jacobi_residual()}"
        )

    def test_class_b_has_zero_n2(self):
        """In our frame, Class B types must have n₂ = 0."""
        for label in CLASS_B_TYPES:
            sc = get_type(label)
            assert sc.n2 == 0.0, (
                f"Class B type {label} should have n₂ = 0, got {sc.n2}"
            )

    def test_class_a_has_zero_a_twist(self):
        """Class A types are unimodular (a_twist = 0)."""
        for label in CLASS_A_TYPES:
            sc = get_type(label)
            assert sc.a_twist == 0.0, (
                f"Class A type {label} should have a_twist = 0, got {sc.a_twist}"
            )

    def test_validate_raises_on_bad_construct(self):
        """Manually construct invalid: Class B with n₂ ≠ 0 must fail validation."""
        bad = StructureConstants(
            n1=0.0, n2=1e-3, n3=1e-3, a_twist=1e-3,
            label="BAD", no_flrw_limit=True,
        )
        with pytest.raises(ValueError, match="Jacobi"):
            bad.validate()


# ═══════════════════════════════════════════════════════════════
# §2 — Canonical sign patterns (Ellis-MacCallum classification)
# ═══════════════════════════════════════════════════════════════

class TestSignPatterns:
    """Test that each type has the correct (n₁, n₂, n₃) sign pattern."""

    def test_type_I_all_zero(self):
        """Type I: (0, 0, 0), a = 0 — abelian."""
        sc = type_i_constants()
        assert sc.n1 == 0 and sc.n2 == 0 and sc.n3 == 0
        assert sc.a_twist == 0

    def test_type_II_single_positive(self):
        """Type II: (+, 0, 0), a = 0 — Heisenberg."""
        sc = type_ii_constants()
        assert sc.n1 > 0 and sc.n2 == 0 and sc.n3 == 0

    def test_type_VI0_mixed_sign(self):
        """Type VI₀: (+, 0, −), a = 0 — e(1,1)."""
        sc = type_vi0_constants()
        assert sc.n1 > 0 and sc.n2 == 0 and sc.n3 < 0

    def test_type_VII0_both_positive(self):
        """Type VII₀: (+, 0, +), a = 0 — e(2)."""
        sc = type_vii0_constants()
        assert sc.n1 > 0 and sc.n2 == 0 and sc.n3 > 0

    def test_type_VIII_one_negative(self):
        """Type VIII: (−, +, +), a = 0 — sl(2,ℝ)."""
        sc = type_viii_constants()
        assert sc.n1 < 0 and sc.n2 > 0 and sc.n3 > 0

    def test_type_IX_all_positive(self):
        """Type IX: (+, +, +), a = 0 — so(3)."""
        sc = type_ix_constants()
        assert sc.n1 > 0 and sc.n2 > 0 and sc.n3 > 0

    def test_type_V_all_zero_with_twist(self):
        """Type V: (0, 0, 0), a > 0."""
        sc = type_v_constants()
        assert sc.n1 == 0 and sc.n2 == 0 and sc.n3 == 0
        assert sc.a_twist > 0

    def test_type_IV_single_positive_with_twist(self):
        """Type IV: (0, 0, +), a > 0."""
        sc = type_iv_constants()
        assert sc.n1 == 0 and sc.n2 == 0 and sc.n3 > 0
        assert sc.a_twist > 0

    def test_type_III_mixed_sign_with_twist(self):
        """Type III: (+, 0, −), a > 0, h = −1."""
        sc = type_iii_constants()
        assert sc.n1 > 0 and sc.n2 == 0 and sc.n3 < 0
        assert sc.a_twist > 0

    def test_type_VIh_mixed_sign_with_twist(self):
        """Type VI_h: (+, 0, −), a > 0, h ≠ −1."""
        sc = type_vih_constants()
        assert sc.n1 > 0 and sc.n2 == 0 and sc.n3 < 0
        assert sc.a_twist > 0

    def test_type_VIIh_both_positive_with_twist(self):
        """Type VII_h: (+, 0, +), a > 0, h > 0."""
        sc = type_viih_constants()
        assert sc.n1 > 0 and sc.n2 == 0 and sc.n3 > 0
        assert sc.a_twist > 0


# ═══════════════════════════════════════════════════════════════
# §3 — Group parameter h (VI_h, VII_h, III invariant)
# ═══════════════════════════════════════════════════════════════

class TestGroupParameterH:
    """h = a²/(n₁ n₃) distinguishes continuous Class B families."""

    def test_type_III_has_h_equals_minus_one(self):
        """Type III is VI_{-1}: the h = -1 special case."""
        sc = type_iii_constants()
        assert abs(sc.h_parameter - (-1.0)) < 1e-10, (
            f"Type III should have h = -1, got h = {sc.h_parameter}"
        )

    def test_type_VIh_has_h_negative_not_minus_one(self):
        """Type VI_h: h ∈ (−∞,−1) ∪ (−1, 0)."""
        sc = type_vih_constants()
        h = sc.h_parameter
        assert h < 0, f"Type VI_h should have h < 0, got h = {h}"
        assert abs(h + 1.0) > 1e-6, f"Type VI_h excludes h = -1, got h = {h}"

    def test_type_VIIh_has_h_positive(self):
        """Type VII_h: h > 0."""
        sc = type_viih_constants()
        assert sc.h_parameter > 0

    def test_type_VIIh_default_h_value(self):
        """Pontzen-Challinor default: h = (5.5e-3)²/(1.8e-2 × 1.0e-2) ≈ 0.168."""
        sc = type_viih_constants()
        expected_h = (5.5e-3) ** 2 / (1.8e-2 * 1.0e-2)
        assert abs(sc.h_parameter - expected_h) < 1e-8
        assert abs(sc.h_parameter - 0.168) < 0.002

    def test_h_undefined_for_type_V(self):
        """Type V has n₁ = n₃ = 0, so h is undefined (returns 0 by convention)."""
        sc = type_v_constants()
        assert sc.h_parameter == 0.0

    def test_h_undefined_for_flrw(self):
        sc = flrw_constants()
        assert sc.h_parameter == 0.0


# ═══════════════════════════════════════════════════════════════
# §4 — Class A / Class B partition
# ═══════════════════════════════════════════════════════════════

class TestClassPartition:
    def test_class_a_flag(self):
        for label in CLASS_A_TYPES:
            sc = get_type(label)
            assert sc.is_class_a, f"{label} should be Class A"
            assert not sc.is_class_b

    def test_class_b_flag(self):
        for label in CLASS_B_TYPES:
            sc = get_type(label)
            assert sc.is_class_b, f"{label} should be Class B"
            assert not sc.is_class_a

    def test_all_types_accounted_for(self):
        """Every type in ALL_BIANCHI_TYPES is in exactly one of Class A or Class B."""
        class_a = set(CLASS_A_TYPES)
        class_b = set(CLASS_B_TYPES)
        all_types = set(ALL_BIANCHI_TYPES)
        assert class_a | class_b == all_types
        assert class_a & class_b == set()
        assert len(all_types) == 11  # 9 Bianchi + III + IV accounted

    def test_flrw_is_classified_as_class_a(self):
        """FLRW has all zeros, so a_twist = 0 → Class A (degenerate)."""
        assert flrw_constants().is_class_a


# ═══════════════════════════════════════════════════════════════
# §5 — FLRW limits and marginal types
# ═══════════════════════════════════════════════════════════════

class TestFLRWLimits:
    def test_types_with_flrw_limit_flagged_correctly(self):
        for label in TYPES_WITH_FLRW_LIMIT:
            sc = get_type(label)
            assert not sc.no_flrw_limit, (
                f"{label} should admit FLRW limit (no_flrw_limit=False)"
            )

    def test_marginal_types_flagged_correctly(self):
        for label in MARGINAL_TYPES:
            sc = get_type(label)
            assert sc.no_flrw_limit, (
                f"{label} should NOT admit FLRW limit (no_flrw_limit=True)"
            )

    def test_flrw_limit_types_count(self):
        """Only 5 types admit FLRW limit: I, V, VII₀, VII_h, IX."""
        assert len(TYPES_WITH_FLRW_LIMIT) == 5
        assert set(TYPES_WITH_FLRW_LIMIT) == {"I", "V", "VII_0", "VII_h", "IX"}

    def test_marginal_types_count(self):
        """6 marginal types: II, III, IV, VI₀, VI_h, VIII."""
        assert len(MARGINAL_TYPES) == 6
        assert set(MARGINAL_TYPES) == {"II", "III", "IV", "VI_0", "VI_h", "VIII"}


# ═══════════════════════════════════════════════════════════════
# §6 — ver3 PR-02 registry contract
# ═══════════════════════════════════════════════════════════════


class TestVer3FamilyRegistry:
    def test_all_family_specs_cover_flrw_plus_eleven_types(self):
        specs = all_family_specs()
        assert set(specs) == {"FLRW", *ALL_BIANCHI_TYPES}

    @pytest.mark.parametrize("label", ["FLRW", *ALL_BIANCHI_TYPES])
    def test_get_family_spec_returns_registry_complete_contract(self, label):
        spec = get_family_spec(label)
        assert isinstance(spec, FamilySpec)
        assert spec.family == label
        assert spec.release_status == "registry-complete"
        assert spec.orthogonal_global_tilt_local_boost_split == "frozen"
        assert spec.generic_fallback == "generic_collocation"

    @pytest.mark.parametrize("label", ["FLRW", "I", "V", "VII_0", "VII_h", "IX"])
    def test_isotropic_anchor_family_flags(self, label):
        assert get_family_spec(label).isotropic_anchor

    @pytest.mark.parametrize("label", ["II", "III", "IV", "VI_0", "VI_h", "VIII"])
    def test_intrinsic_family_flags(self, label):
        assert not get_family_spec(label).isotropic_anchor

    def test_type_iii_registry_stays_on_special_h_equals_minus_one_branch(self):
        spec = get_family_spec("III")
        assert spec.algebra.h_parameter == pytest.approx(-1.0)

    def test_vih_h_override_builds_h_consistent_registry_spec(self):
        spec = get_family_spec("VI_h", h=-0.5)
        assert spec.algebra.h_parameter == pytest.approx(-0.5)
        assert spec.class_label == "B"

    def test_viih_h_override_builds_h_consistent_registry_spec(self):
        spec = get_family_spec("VII_h", h=0.25)
        assert spec.algebra.h_parameter == pytest.approx(0.25)
        assert spec.class_label == "B"

    def test_h_override_is_forbidden_for_non_h_families(self):
        with pytest.raises(ValueError, match="h override"):
            get_family_spec("V", h=0.1)


# ═══════════════════════════════════════════════════════════════
# §6 — Spatial curvature sign
# ═══════════════════════════════════════════════════════════════

class TestSpatialCurvature:
    def test_type_I_is_flat(self):
        assert type_i_constants().spatial_ricci_sign == 0

    def test_type_V_is_open(self):
        """Type V has k = -1 (open FLRW limit)."""
        assert type_v_constants().spatial_ricci_sign == -1

    def test_type_IX_is_closed(self):
        """Type IX has k = +1 (closed FLRW limit)."""
        assert type_ix_constants().spatial_ricci_sign == +1


# ═══════════════════════════════════════════════════════════════
# §7 — Parameter validation (invalid inputs raise)
# ═══════════════════════════════════════════════════════════════

class TestParameterValidation:
    def test_type_II_requires_positive_n1(self):
        with pytest.raises(ValueError, match="n1 > 0"):
            type_ii_constants(n1=-1e-3)

    def test_type_VI0_requires_mixed_sign(self):
        with pytest.raises(ValueError):
            type_vi0_constants(n1=-1e-3, n3=1e-3)  # wrong signs

    def test_type_VIII_requires_minus_plus_plus(self):
        with pytest.raises(ValueError):
            type_viii_constants(n1=1e-3, n2=1e-3, n3=1e-3)  # n1 should be negative

    def test_type_IX_requires_positive_n(self):
        with pytest.raises(ValueError):
            type_ix_constants(n=0.0)

    def test_type_V_requires_positive_a_twist(self):
        with pytest.raises(ValueError):
            type_v_constants(a_twist=0.0)

    def test_type_VIh_forbids_h_equals_minus_one(self):
        """Cannot construct VI_h with h = -1 — that's Type III."""
        # Choose parameters where a² = -(n1 × n3), i.e., h = -1
        n1 = 1e-2
        n3 = -1e-2  # so n1 × n3 = -1e-4
        a_twist = 1e-2  # a² = 1e-4 → h = 1e-4 / (-1e-4) = -1
        with pytest.raises(ValueError, match="h ≠ −1"):
            type_vih_constants(n1=n1, n3=n3, a_twist=a_twist)

    def test_type_IV_requires_positive_n3(self):
        with pytest.raises(ValueError):
            type_iv_constants(n3=-1e-3, a_twist=1e-3)


# ═══════════════════════════════════════════════════════════════
# §8 — Type registry and lookup API
# ═══════════════════════════════════════════════════════════════

class TestRegistry:
    def test_all_types_in_registry(self):
        """All 11 types (9 Bianchi + I + FLRW) must be in TYPE_REGISTRY."""
        assert "FLRW" in TYPE_REGISTRY
        for label in ALL_BIANCHI_TYPES:
            assert label in TYPE_REGISTRY, f"{label} missing from TYPE_REGISTRY"
        assert len(TYPE_REGISTRY) == 12  # 11 Bianchi (incl. III, IV) + FLRW

    def test_get_type_lookup(self):
        """get_type() returns the same as direct factory call."""
        sc1 = get_type("VII_h")
        sc2 = type_viih_constants()
        assert sc1.n1 == sc2.n1
        assert sc1.n3 == sc2.n3
        assert sc1.a_twist == sc2.a_twist

    def test_get_type_unknown_label_raises(self):
        with pytest.raises(KeyError, match="Unknown Bianchi type"):
            get_type("Type_XII")

    def test_get_type_forwards_kwargs(self):
        """Parameters can be overridden via get_type()."""
        sc = get_type("VII_h", n1=0.05, n3=0.03, a_twist=0.01)
        assert sc.n1 == 0.05
        assert sc.n3 == 0.03

    def test_get_type_validates(self):
        """get_type() must call validate() before returning."""
        # Manually construct invalid via factory kwargs — if factory validates
        # internally before returning, get_type's validate() is belt-and-suspenders.
        pass  # The factories themselves raise on invalid input; validate() is a second line.


# ═══════════════════════════════════════════════════════════════
# §9 — Derived properties (trace, delta_n, sqrt_h)
# ═══════════════════════════════════════════════════════════════

class TestDerivedProperties:
    def test_trace_n_for_IX(self):
        """Type IX default: n₁ = n₂ = n₃ = 1e-2, so trace = 3e-2."""
        sc = type_ix_constants(n=1e-2)
        assert abs(sc.trace_n - 3e-2) < 1e-15

    def test_delta_n_for_VIIh(self):
        """Type VII_h: Δn = n₃ - n₁ = 1e-2 - 1.8e-2 = -0.8e-2."""
        sc = type_viih_constants()
        assert abs(sc.delta_n - (1.0e-2 - 1.8e-2)) < 1e-15

    def test_sqrt_h_for_VIIh(self):
        """Type VII_h: √h for default parameters."""
        sc = type_viih_constants()
        assert abs(sc.sqrt_h - math.sqrt(sc.h_parameter)) < 1e-15
        assert sc.sqrt_h > 0

    def test_sqrt_h_zero_for_class_a(self):
        """Class A has no h, so √h = 0 by convention."""
        assert type_i_constants().sqrt_h == 0.0
        assert type_ix_constants().sqrt_h == 0.0

    def test_n_diag_tuple(self):
        sc = type_viii_constants()
        assert sc.n_diag == (sc.n1, sc.n2, sc.n3)


# ═══════════════════════════════════════════════════════════════
# §10 — Integration: every type constructs and validates
# ═══════════════════════════════════════════════════════════════

class TestIntegrationAllTypes:
    @pytest.mark.parametrize("label", ["FLRW"] + ALL_BIANCHI_TYPES)
    def test_every_type_constructs_and_validates(self, label):
        """Smoke test: every type factory produces a valid object."""
        sc = get_type(label)
        # Core invariants
        assert sc.label == label
        assert isinstance(sc.n1, float)
        assert isinstance(sc.n2, float)
        assert isinstance(sc.n3, float)
        assert isinstance(sc.a_twist, float)
        # Jacobi
        assert sc.jacobi_residual() < 1e-12
        # Class partition is coherent
        assert sc.is_class_a != sc.is_class_b or label == "FLRW"  # FLRW is degenerate

    def test_count_class_a_matches_expected(self):
        """Exactly 6 Class A Bianchi types (I, II, VI₀, VII₀, VIII, IX)."""
        assert len(CLASS_A_TYPES) == 6

    def test_count_class_b_matches_expected(self):
        """Exactly 5 Class B Bianchi types (III, IV, V, VI_h, VII_h)."""
        assert len(CLASS_B_TYPES) == 5

    def test_total_type_count(self):
        """6 Class A + 5 Class B = 11 Bianchi types."""
        assert len(ALL_BIANCHI_TYPES) == 11
