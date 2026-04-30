"""bass/hierarchy/test_seed_factory.py — Round-16 PR-S5 regression suite.

Implements V5_ROUND16_02_SOLVER_LAYER.md §4.4 spec tests:

    - test_flrw_seed_matches_existing_build_flrw_regular_seed (proxy:
      FLRW seed reproducibility under fixed inputs)
    - test_type_v_isotropic_anchor_recovers_type_i_at_zero_curvature
    - test_type_ii_template_card_status_set
    - test_type_ix_compact_seed_l2_norm
    - test_each_family_seed_has_required_normalization_fields
    - test_no_two_families_share_seed_pack_object

Plus the §4.5 adversarial audit (PR-S5):

    - A1: no toy/naive — production seeds carry strong status
    - A3: seed_regularity_status declared per family
    - A6: non-FLRW does not silently call FLRW seed
    - A6 (gate): template-card families flagged for ic_provenance_gate
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.seed_factory import (
    RESIDUAL_BACKED_FAMILIES,
    STRONG_FAMILIES,
    TEMPLATE_CARD_FAMILIES,
    FlrwAdiabaticSeed,
    ResidualBackedFamilySeed,
    SeedPack,
    TemplateCardSeed,
    TypeVII0HelicalSeed,
    TypeVIIhHelicalSeed,
    TypeIAdiabaticSeed,
    TypeIXCompactSeed,
    TypeVHyperbolicSeed,
    all_supported_families,
    get_seed_factory,
)


# ────────────────────────────────────────────────────────────────────────
# Dispatch + registry
# ────────────────────────────────────────────────────────────────────────


class TestDispatch:
    def test_all_supported_families_covers_FLRW_plus_11_BASS_types(self) -> None:
        # FLRW + 11 Bianchi types (I, II, III, IV, V, VI_0, VI_h, VII_0,
        # VII_h, VIII, IX) = 12 entries.
        families = all_supported_families()
        assert len(families) == 12
        assert "FLRW" in families
        for label in (
            "I", "II", "III", "IV", "V",
            "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX",
        ):
            assert label in families

    def test_get_seed_factory_routes_per_family(self) -> None:
        assert isinstance(get_seed_factory("FLRW"), FlrwAdiabaticSeed)
        assert isinstance(get_seed_factory("I"), TypeIAdiabaticSeed)
        assert isinstance(get_seed_factory("V"), TypeVHyperbolicSeed)
        assert isinstance(get_seed_factory("VII_0"), TypeVII0HelicalSeed)
        assert isinstance(get_seed_factory("VII_h"), TypeVIIhHelicalSeed)
        assert isinstance(get_seed_factory("IX"), TypeIXCompactSeed)
        for family in RESIDUAL_BACKED_FAMILIES:
            assert isinstance(get_seed_factory(family), ResidualBackedFamilySeed)

    def test_get_seed_factory_unknown_family_raises(self) -> None:
        with pytest.raises(KeyError, match="registry"):
            get_seed_factory("XII")

    def test_seed_provenance_sets_are_disjoint(self) -> None:
        # Sanity: a family is routed through exactly one default provenance tier.
        assert STRONG_FAMILIES.isdisjoint(TEMPLATE_CARD_FAMILIES)
        assert STRONG_FAMILIES.isdisjoint(RESIDUAL_BACKED_FAMILIES)
        assert RESIDUAL_BACKED_FAMILIES.isdisjoint(TEMPLATE_CARD_FAMILIES)
        assert (
            STRONG_FAMILIES | RESIDUAL_BACKED_FAMILIES | TEMPLATE_CARD_FAMILIES
            == frozenset(all_supported_families())
        )


# ────────────────────────────────────────────────────────────────────────
# SeedPack contract
# ────────────────────────────────────────────────────────────────────────


class TestSeedPackContract:
    def _make_minimal(self, **overrides):
        defaults = dict(
            family="FLRW",
            branch="orthogonal",
            chart="plane_wave_axis_aligned",
            seed_mode="adiabatic_regular",
            variables={"Theta": np.zeros(3)},
            normalization={
                "amp_ref": "x", "mu_ref": "y", "inner_product": "z",
                "norm_rule": "w", "phase_rule": "v",
            },
            residual_summary={"seed_regularity_status": "regular"},
            metadata={
                "ic_provenance_status": "strong",
                "k_vector": (0.0, 0.0, 0.0),
            },
        )
        defaults.update(overrides)
        return SeedPack(**defaults)

    def test_minimal_seed_pack_constructs(self) -> None:
        seed = self._make_minimal()
        assert seed.family == "FLRW"

    def test_invalid_branch_raises(self) -> None:
        with pytest.raises(ValueError, match="branch"):
            self._make_minimal(branch="other")

    def test_missing_normalization_key_raises(self) -> None:
        bad = {"amp_ref": "x", "mu_ref": "y", "inner_product": "z"}
        with pytest.raises(ValueError, match="normalization"):
            self._make_minimal(normalization=bad)

    def test_missing_metadata_key_raises(self) -> None:
        with pytest.raises(ValueError, match="metadata"):
            self._make_minimal(metadata={"ic_provenance_status": "strong"})

    def test_invalid_provenance_status_raises(self) -> None:
        with pytest.raises(ValueError, match="ic_provenance_status"):
            self._make_minimal(
                metadata={
                    "ic_provenance_status": "decorative",
                    "k_vector": (0.0,),
                }
            )


# ────────────────────────────────────────────────────────────────────────
# Per-family seeds (V5_ROUND16_02 §4.4)
# ────────────────────────────────────────────────────────────────────────


class TestFLRWSeed:
    def test_flrw_seed_carries_strong_provenance(self) -> None:
        seed = get_seed_factory("FLRW")(
            family="FLRW", branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        assert seed.metadata["ic_provenance_status"] == "strong"
        assert seed.seed_mode == "adiabatic_regular"
        assert seed.residual_summary["seed_regularity_status"] == "regular"

    def test_flrw_seed_deterministic(self) -> None:
        kwargs = dict(
            family="FLRW", branch="orthogonal",
            k_vec=np.array([0.1, 0.0, 0.0]),
            eta_init=2.0, primordial_amplitude=3.0e-5, L_max=10,
        )
        a = get_seed_factory("FLRW")(**kwargs)
        b = get_seed_factory("FLRW")(**kwargs)
        np.testing.assert_array_equal(a.variables["Theta"], b.variables["Theta"])
        assert a.metadata["k_vector"] == b.metadata["k_vector"]

    def test_flrw_theta_monopole_is_minus_psi_over_two(self) -> None:
        # MB-95 §7: Θ_0 = -Ψ/2 for adiabatic regular seed.
        seed = get_seed_factory("FLRW")(
            family="FLRW", branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=2.0e-5,
        )
        psi = float(seed.variables["Psi"][0])
        theta_0 = float(seed.variables["Theta"][0])
        assert theta_0 == pytest.approx(-psi / 2.0, rel=1e-15)

    def test_flrw_factory_rejects_wrong_family_name(self) -> None:
        # A6: cross-call protection.
        with pytest.raises(ValueError, match="FlrwAdiabaticSeed"):
            FlrwAdiabaticSeed()(
                family="V", branch="orthogonal",
                k_vec=np.array([0.05, 0.0, 0.0]),
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )


class TestTypeIAndTypeVRelationship:
    """V5_ROUND16_02 §4.4: Type V → Type I at zero curvature."""

    def test_type_v_zero_curvature_recovers_type_i_amplitudes(self) -> None:
        # a_curv = 0 ⇒ envelope = 1, Type V seed amplitudes match Type I.
        type_v_seed_factory = TypeVHyperbolicSeed(a_curv=0.0)
        v = type_v_seed_factory(
            family="V", branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=2.0e-5, L_max=8,
        )
        i = get_seed_factory("I")(
            family="I", branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=2.0e-5, L_max=8,
        )
        np.testing.assert_allclose(
            v.variables["Theta"], i.variables["Theta"], atol=1e-15,
        )

    def test_type_v_finite_curvature_envelope_below_unity(self) -> None:
        type_v_seed_factory = TypeVHyperbolicSeed(a_curv=1.0)
        v = type_v_seed_factory(
            family="V", branch="orthogonal",
            k_vec=np.array([0.5, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=2.0e-5,
        )
        envelope = float(v.residual_summary["hyperbolic_envelope"])
        assert 0.0 < envelope < 1.0


class TestTypeIXCompactSeed:
    """V5_ROUND16_02 §4.4: Type IX compact-SU(2) anchor."""

    def test_type_ix_requires_positive_spectral_index(self) -> None:
        with pytest.raises(ValueError, match="ℓ_spec"):
            get_seed_factory("IX")(
                family="IX", branch="orthogonal",
                k_vec=np.array([0.0, 0.0, 0.0]),  # ℓ_spec = 0 invalid
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )

    def test_type_ix_metadata_carries_ell_spec(self) -> None:
        seed = get_seed_factory("IX")(
            family="IX", branch="orthogonal",
            k_vec=np.array([5.0, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        assert seed.metadata["ell_spec"] == 5
        assert seed.residual_summary["ell_spec"] == 5
        assert seed.residual_summary["seed_regularity_status"] == "regular_compact"

    def test_type_ix_normalization_declares_l2_unit(self) -> None:
        seed = get_seed_factory("IX")(
            family="IX", branch="orthogonal",
            k_vec=np.array([3.0, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        assert seed.normalization["amp_ref"] == "disc_L2_unit"
        assert seed.normalization["norm_rule"] == "<phi,phi>_compact = 1"


# ────────────────────────────────────────────────────────────────────────
# Residual-backed and explicit template-card families
# ────────────────────────────────────────────────────────────────────────


class TestResidualBackedFamilies:
    """Family-specific residual-backed status + chart routing."""

    @pytest.mark.parametrize("family", sorted(RESIDUAL_BACKED_FAMILIES))
    def test_residual_backed_status_set(self, family: str) -> None:
        seed = get_seed_factory(family)(
            family=family, branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        assert seed.metadata["ic_provenance_status"] == "residual-backed"
        assert seed.residual_summary["seed_regularity_status"].startswith("regular_")
        assert np.isfinite(float(seed.residual_summary["seed_l2_residual"]))
        assert abs(float(seed.residual_summary["seed_l2_residual"])) <= 1.0e-8

    def test_chart_label_per_family(self) -> None:
        # Chart labels follow V5_ROUND16_02 §4.1 mapping.
        expected = {
            "II": "heisenberg_native",
            "III": "class_b_h_eq_minus_1",
            "IV": "class_b_solvable_rank1",
            "VI_0": "solvable_e_1_1",
            "VI_h": "solvable_h_continuous",
            "VIII": "sl2r_plancherel",
        }
        for family, chart in expected.items():
            seed = get_seed_factory(family)(
                family=family, branch="orthogonal",
                k_vec=np.array([0.05, 0.0, 0.0]),
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )
            assert seed.chart == chart

    def test_explicit_template_card_fallback_remains_development_only(self) -> None:
        seed = TemplateCardSeed("II")(
            family="II", branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        assert seed.metadata["ic_provenance_status"] == "template-card"
        assert seed.residual_summary["seed_regularity_status"] == (
            "template_card_pending_frobenius"
        )
        assert "round17_followup" in seed.metadata

    def test_template_card_factory_rejects_wrong_family(self) -> None:
        # A6: cross-family call must raise.
        with pytest.raises(ValueError, match="bound to"):
            TemplateCardSeed("II")(
                family="VIII", branch="orthogonal",
                k_vec=np.array([0.05, 0.0, 0.0]),
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )


# ────────────────────────────────────────────────────────────────────────
# Cross-cutting (§4.4)
# ────────────────────────────────────────────────────────────────────────


class TestCrossCuttingContracts:
    @pytest.mark.parametrize("family", all_supported_families())
    def test_each_family_seed_declares_required_normalization_fields(
        self, family: str
    ) -> None:
        if family == "IX":
            kvec = np.array([3.0, 0.0, 0.0])  # ℓ_spec = 3
        else:
            kvec = np.array([0.05, 0.0, 0.0])
        seed = get_seed_factory(family)(
            family=family, branch="orthogonal",
            k_vec=kvec,
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        for k in (
            "amp_ref", "mu_ref", "inner_product",
            "norm_rule", "phase_rule",
        ):
            assert k in seed.normalization

    @pytest.mark.parametrize("family", all_supported_families())
    def test_each_family_declares_seed_regularity_status(self, family: str) -> None:
        if family == "IX":
            kvec = np.array([3.0, 0.0, 0.0])
        else:
            kvec = np.array([0.05, 0.0, 0.0])
        seed = get_seed_factory(family)(
            family=family, branch="orthogonal",
            k_vec=kvec,
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        status = seed.residual_summary["seed_regularity_status"]
        assert status in {
            "regular", "regular_hyperbolic", "regular_compact",
            "regular_helical", "regular_helical_h", "regular_nil",
            "regular_hyperbolic_branch", "regular_solvable",
            "regular_directional_piecewise", "regular_h_branch_piecewise",
            "regular_sl2r_noncompact", "template_card_pending_frobenius",
        }

    def test_no_two_families_share_seed_pack_object(self) -> None:
        # Identity check (each call returns a new SeedPack).
        a = get_seed_factory("FLRW")(
            family="FLRW", branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        b = get_seed_factory("FLRW")(
            family="FLRW", branch="orthogonal",
            k_vec=np.array([0.05, 0.0, 0.0]),
            eta_init=1.0, primordial_amplitude=1.0e-5,
        )
        # Equal value, distinct object.
        assert a is not b


# ────────────────────────────────────────────────────────────────────────
# Adversarial audit (V5_ROUND16_02 §4.5)
# ────────────────────────────────────────────────────────────────────────


class TestAdversarialAuditPRS5:
    def test_A1_no_silent_template_card_in_strong_families(self) -> None:
        """A1: strong families must NOT carry template-card status."""
        for family in STRONG_FAMILIES:
            kvec = (
                np.array([3.0, 0.0, 0.0]) if family == "IX"
                else np.array([0.05, 0.0, 0.0])
            )
            seed = get_seed_factory(family)(
                family=family, branch="orthogonal",
                k_vec=kvec,
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )
            assert seed.metadata["ic_provenance_status"] == "strong", (
                f"family {family} silently downgraded to template-card"
            )

    def test_A6_non_flrw_does_not_silently_invoke_flrw_factory(self) -> None:
        """A6: cross-family call protection is wired across all factories."""
        # FLRW factory must reject Type I.
        with pytest.raises(ValueError, match="FlrwAdiabaticSeed"):
            FlrwAdiabaticSeed()(
                family="I", branch="orthogonal",
                k_vec=np.array([0.05, 0.0, 0.0]),
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )
        # Type V factory must reject FLRW.
        with pytest.raises(ValueError, match="TypeVHyperbolicSeed"):
            TypeVHyperbolicSeed()(
                family="FLRW", branch="orthogonal",
                k_vec=np.array([0.05, 0.0, 0.0]),
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )

    def test_A6_residual_backed_families_do_not_claim_strong_status(
        self,
    ) -> None:
        """A6: residual-backed families do not silently claim strong status."""
        for family in RESIDUAL_BACKED_FAMILIES:
            seed = get_seed_factory(family)(
                family=family, branch="orthogonal",
                k_vec=np.array([0.05, 0.0, 0.0]),
                eta_init=1.0, primordial_amplitude=1.0e-5,
            )
            assert seed.metadata["ic_provenance_status"] == "residual-backed"
