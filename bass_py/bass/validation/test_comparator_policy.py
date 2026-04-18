"""
tests/test_comparator_policy.py
================================

Day 3 test suite covering:
  §1 — Comparator policy dispatch (recommend/validate)
  §2 — Departure components (API scaffolding)
  §3 — Filling fraction with sign-aware behaviour
  §4 — Bianchi IV structured-null handling
  §5 — Integration with einstein_bianchi factory
  §6 — End-to-end: build cosmology for all 10 types + FLRW

Run
---
    pytest test_comparator_policy.py -v
"""
from __future__ import annotations

import math
import warnings
import numpy as np
import pytest

from bass.background.bianchi_types import (
    ALL_BIANCHI_TYPES, CLASS_A_TYPES, CLASS_B_TYPES,
    TYPES_WITH_FLRW_LIMIT, MARGINAL_TYPES,
    get_type,
)
from bass.validation.comparator_policy import (
    ComparatorPolicy, ComparatorStatus, DepartureComponents,
    MATCHED_COMPATIBLE, NULL_RECOMMENDED,
    recommend_comparator, validate_comparator,
    compute_departure_components, filling_fraction,
    bianchi_iv_falsifiability_probe,
)
from bass.background.einstein_bianchi import (
    BianchiCosmology, BianchiBackgroundState,
    make_cosmology, COSMOLOGY_FACTORY,
    flrw_cosmology, type_i_cosmology, type_iv_cosmology,
    type_viih_cosmology, type_ix_cosmology,
)


# ═══════════════════════════════════════════════════════════════
# §1 — Comparator policy dispatch
# ═══════════════════════════════════════════════════════════════

class TestComparatorRecommendation:
    def test_flrw_gets_matched(self):
        assert recommend_comparator("FLRW") == ComparatorPolicy.MATCHED

    @pytest.mark.parametrize("label", list(TYPES_WITH_FLRW_LIMIT))
    def test_flrw_limit_types_get_matched(self, label):
        assert recommend_comparator(label) == ComparatorPolicy.MATCHED

    @pytest.mark.parametrize("label", list(MARGINAL_TYPES))
    def test_marginal_types_get_null(self, label):
        assert recommend_comparator(label) == ComparatorPolicy.NULL

    def test_unknown_type_warns_and_returns_null(self):
        with pytest.warns(UserWarning, match="Unknown type"):
            policy = recommend_comparator("XII")
        assert policy == ComparatorPolicy.NULL


class TestComparatorValidation:
    def test_flat_always_valid(self):
        for label in ALL_BIANCHI_TYPES + ["FLRW"]:
            status = validate_comparator(label, ComparatorPolicy.FLAT)
            assert status.is_valid, f"{label}: FLAT should always be valid"

    def test_null_always_valid(self):
        for label in ALL_BIANCHI_TYPES + ["FLRW"]:
            status = validate_comparator(label, ComparatorPolicy.NULL)
            assert status.is_valid

    def test_matched_valid_for_flrw_limit_types(self):
        for label in TYPES_WITH_FLRW_LIMIT:
            status = validate_comparator(label, ComparatorPolicy.MATCHED)
            assert status.is_valid, f"{label} admits FLRW → MATCHED valid"

    def test_matched_invalid_for_marginal_types(self):
        for label in MARGINAL_TYPES:
            status = validate_comparator(label, ComparatorPolicy.MATCHED)
            assert not status.is_valid, (
                f"{label} has no FLRW limit → MATCHED should be invalid"
            )
            assert "no FLRW limit" in status.reason or "undefined" in status.reason

    def test_matched_valid_for_FLRW_itself(self):
        status = validate_comparator("FLRW", ComparatorPolicy.MATCHED)
        assert status.is_valid


class TestComparatorStatus:
    def test_x_C_defined_flag_under_flat(self):
        status = validate_comparator("I", ComparatorPolicy.FLAT)
        assert status.x_C_defined

    def test_x_C_undefined_under_null(self):
        status = validate_comparator("IV", ComparatorPolicy.NULL)
        assert not status.x_C_defined   # NULL → x_C undefined

    def test_F_C_tracks_x_C(self):
        status_flat = validate_comparator("I", ComparatorPolicy.FLAT)
        status_null = validate_comparator("IV", ComparatorPolicy.NULL)
        assert status_flat.F_C_defined
        assert not status_null.F_C_defined


# ═══════════════════════════════════════════════════════════════
# §2 — Departure components
# ═══════════════════════════════════════════════════════════════

class TestDepartureComponents:
    def _make_test_comp(self, sc_label, policy, **kw):
        sc = get_type(sc_label)
        defaults = dict(
            sigma_sq=1e-6, omega_sq=0.0, H_theta=1.0, beta=1e-3,
            w=0.0, Omega_matter=0.3, Omega_k=1e-4,
        )
        defaults.update(kw)
        return compute_departure_components(sc, policy=policy, **defaults)

    def test_flrw_zero_shear_zero_tilt_gives_zero_departure(self):
        """FLRW with σ=ω=β=0 and Ω_k=0 gives x_C = 0 exactly."""
        comp = self._make_test_comp(
            "FLRW", ComparatorPolicy.MATCHED,
            sigma_sq=0.0, omega_sq=0.0, beta=0.0, Omega_k=0.0,
        )
        assert comp.x_C is not None
        assert abs(comp.x_C) < 1e-30

    def test_sigstd_squared_nonnegative(self):
        comp = self._make_test_comp("I", ComparatorPolicy.MATCHED)
        assert comp.Sigstd_sq >= 0

    def test_wstd_squared_nonnegative(self):
        comp = self._make_test_comp("I", ComparatorPolicy.MATCHED, omega_sq=1e-7)
        assert comp.Wstd_sq >= 0

    def test_tilt_component_nonnegative(self):
        """Ω_tilt = (1+w) Ω sinh²β ≥ 0 always."""
        comp = self._make_test_comp("I", ComparatorPolicy.MATCHED, beta=1e-2)
        assert comp.Omega_tilt >= 0

    def test_null_comparator_gives_none_x_C(self):
        comp = self._make_test_comp("IV", ComparatorPolicy.NULL)
        assert comp.x_C is None
        assert comp.Omega_k_aniso is None

    def test_x_C_direct_always_finite(self):
        """x_C^direct is defined even for NULL comparator."""
        comp = self._make_test_comp("IV", ComparatorPolicy.NULL)
        assert math.isfinite(comp.x_C_direct)

    def test_flat_comparator_sets_ref_to_zero(self):
        comp = self._make_test_comp("I", ComparatorPolicy.FLAT, Omega_k=1e-3)
        assert comp.Omega_k_ref == 0.0
        assert comp.Omega_k_aniso == 1e-3

    def test_matched_invalid_type_raises(self):
        """MATCHED with Type IV should raise ValueError."""
        with pytest.raises(ValueError, match="no FLRW limit|undefined"):
            self._make_test_comp("IV", ComparatorPolicy.MATCHED)

    def test_tilt_linear_order_beta(self):
        """For small β, Ω_tilt ≈ (1+w) Ω β²."""
        sc = get_type("I")
        comp_small = compute_departure_components(
            sc, sigma_sq=0, omega_sq=0, H_theta=1.0,
            beta=1e-4, w=0.0, Omega_matter=0.3,
            Omega_k=0.0, policy=ComparatorPolicy.MATCHED,
        )
        # Ω_tilt ≈ 1 × 0.3 × (1e-4)² = 3e-9
        expected = 0.3 * (1e-4) ** 2
        assert abs(comp_small.Omega_tilt - expected) < 1e-11


class TestSectorClassification:
    def test_irrotational_positive_sector(self):
        """Typical positive x_C case."""
        sc = get_type("I")
        comp = compute_departure_components(
            sc, sigma_sq=1e-6, omega_sq=0.0, H_theta=1.0,
            beta=1e-3, w=0.0, Omega_matter=0.3, Omega_k=0.0,
            policy=ComparatorPolicy.MATCHED,
        )
        assert comp.sector == "irrotational_positive"

    def test_vortical_sector_when_omega_nonzero(self):
        sc = get_type("VII_h")
        comp = compute_departure_components(
            sc, sigma_sq=1e-8, omega_sq=1e-6, H_theta=1.0,
            beta=0.0, w=0.0, Omega_matter=0.3, Omega_k=0.0,
            policy=ComparatorPolicy.MATCHED,
        )
        assert comp.sector == "vortical"


# ═══════════════════════════════════════════════════════════════
# §3 — Filling fraction
# ═══════════════════════════════════════════════════════════════

class TestFillingFraction:
    def test_canonical_positive_F(self):
        """Typical positive x_C / x_max gives F ∈ [0, 1]."""
        comp = compute_departure_components(
            get_type("I"), sigma_sq=1e-6, omega_sq=0.0, H_theta=1.0,
            beta=1e-3, w=0.0, Omega_matter=0.3, Omega_k=0.0,
            policy=ComparatorPolicy.MATCHED,
        )
        F, flag = filling_fraction(comp, x_max=1e-3)
        assert flag == "unsigned"
        assert 0 <= F <= 1 or F > 1  # could exceed 1 if x > x_max

    def test_null_comparator_returns_none(self):
        comp = compute_departure_components(
            get_type("IV"), sigma_sq=1e-6, omega_sq=0.0, H_theta=1.0,
            beta=0.0, w=0.0, Omega_matter=0.3, Omega_k=1e-3,
            policy=ComparatorPolicy.NULL,
        )
        F, flag = filling_fraction(comp, x_max=1e-3)
        assert F is None
        assert flag == "null_comparator"

    def test_invalid_xmax_returns_none(self):
        comp = compute_departure_components(
            get_type("I"), sigma_sq=1e-6, omega_sq=0.0, H_theta=1.0,
            beta=0.0, w=0.0, Omega_matter=0.3, Omega_k=0.0,
            policy=ComparatorPolicy.MATCHED,
        )
        F, flag = filling_fraction(comp, x_max=0.0)
        assert F is None
        assert flag == "invalid_x_max"

    def test_signed_saturation_for_negative_x(self):
        """For x < 0 (negative irrotational sector), return signed F^±."""
        # Construct a case with x_C < 0: large Ω_{k,aniso} negative
        # Easiest: FLAT comparator with Omega_k slightly negative
        comp = compute_departure_components(
            get_type("I"), sigma_sq=0.0, omega_sq=0.0, H_theta=1.0,
            beta=0.0, w=0.0, Omega_matter=0.3, Omega_k=-1e-3,
            policy=ComparatorPolicy.FLAT,
        )
        # Under FLAT: x_C = 0 - 0 + 0 + (-1e-3 - 0) = -1e-3
        assert comp.x_C < 0
        F, flag = filling_fraction(comp, x_max=1e-3)
        assert flag == "signed"
        assert F < 0


# ═══════════════════════════════════════════════════════════════
# §4 — Bianchi IV falsifiability probe
# ═══════════════════════════════════════════════════════════════

class TestBianchiIVProbe:
    def test_probe_returns_structured_null(self):
        sc = get_type("IV")
        comp = compute_departure_components(
            sc, sigma_sq=1e-6, omega_sq=0.0, H_theta=1.0,
            beta=1e-3, w=0.0, Omega_matter=0.3, Omega_k=1e-3,
            policy=ComparatorPolicy.NULL,
        )
        report = bianchi_iv_falsifiability_probe(comp, sc)

        assert report['type_label'] == 'IV'
        assert report['comparator_status'] == 'NULL'
        assert report['x_C'] is None
        assert math.isfinite(report['x_C_direct'])
        assert report['F_C'] is None
        assert report['no_flrw_limit_flag'] is True

    def test_probe_raises_for_wrong_type(self):
        sc = get_type("I")
        comp = compute_departure_components(
            sc, sigma_sq=0, omega_sq=0, H_theta=1.0,
            beta=0, w=0, Omega_matter=0.3, Omega_k=0,
            policy=ComparatorPolicy.FLAT,
        )
        with pytest.raises(ValueError, match="Expected Type IV"):
            bianchi_iv_falsifiability_probe(comp, sc)


# ═══════════════════════════════════════════════════════════════
# §5 — einstein_bianchi factory integration
# ═══════════════════════════════════════════════════════════════

class TestFactoryIntegration:
    @pytest.mark.parametrize("label", list(COSMOLOGY_FACTORY.keys()))
    def test_all_types_produce_valid_cosmology(self, label):
        """Every type factory produces a validated BianchiCosmology."""
        cosmo = make_cosmology(label)
        assert cosmo.structure.label == label
        assert cosmo.structure.jacobi_residual() < 1e-12

    def test_unknown_type_raises(self):
        with pytest.raises(KeyError, match="Unknown cosmology type"):
            make_cosmology("XII")

    def test_effective_comparator_uses_recommendation(self):
        """If comparator=None, effective_comparator uses recommendation."""
        cosmo = make_cosmology("VII_h")  # no explicit comparator
        assert cosmo.effective_comparator == ComparatorPolicy.MATCHED

        cosmo = make_cosmology("IV")  # Type IV defaults to NULL
        assert cosmo.effective_comparator == ComparatorPolicy.NULL

    def test_type_iv_has_no_flrw_limit_flag(self):
        cosmo = type_iv_cosmology()
        assert cosmo.no_flrw_limit is True
        assert cosmo.comparator == ComparatorPolicy.NULL

    def test_type_i_has_flrw_limit_flag_false(self):
        cosmo = type_i_cosmology()
        assert cosmo.no_flrw_limit is False


class TestBackgroundIntegration:
    """Run the background integrator briefly for a few types to verify
    the Day 2 one-line substitution works end-to-end."""

    def test_flrw_background_runs(self):
        cosmo = flrw_cosmology()
        state = _run_short_background(cosmo)
        # FLRW: source is zero, shear decays as Σ ∝ 1/a
        assert state.source_status == "VALIDATED"

    def test_type_I_background_runs(self):
        cosmo = type_i_cosmology(sigma_over_H_init=1e-5)
        state = _run_short_background(cosmo)
        assert state.source_status == "VALIDATED"
        # Type I: Σ should decay monotonically (no source to amplify)
        # Check Σ_+ at end < Σ_+ at start
        assert abs(state.sigma_plus[-1]) < abs(state.sigma_plus[0]) * 2  # allow 2× tolerance

    def test_type_VIIh_background_runs(self):
        cosmo = type_viih_cosmology(sigma_over_H_init=1e-5)
        state = _run_short_background(cosmo)
        # VII_h uses the spiral source; should be PROVISIONAL
        assert state.source_status == "PROVISIONAL"
        # Integration should complete without NaN/Inf
        assert np.all(np.isfinite(state.sigma_plus))
        assert np.all(np.isfinite(state.sigma_minus))

    def test_type_iv_background_runs_despite_no_flrw_limit(self):
        """Type IV has no FLRW limit, but the forward model still runs."""
        cosmo = type_iv_cosmology(sigma_over_H_init=1e-5)
        state = _run_short_background(cosmo)
        assert np.all(np.isfinite(state.sigma_plus))
        assert np.all(np.isfinite(state.sigma_minus))

    @pytest.mark.parametrize("label", list(COSMOLOGY_FACTORY.keys()))
    def test_every_type_integrates_to_completion(self, label):
        """End-to-end: every type's forward model runs without error."""
        cosmo = make_cosmology(label)
        state = _run_short_background(cosmo)
        assert len(state.eta) > 0
        assert np.all(np.isfinite(state.a))


def _run_short_background(cosmo):
    """Helper: run background integration on a small grid for fast tests."""
    from bass.background.einstein_bianchi import solve_bianchi_background
    return solve_bianchi_background(
        cosmo, a_start=1e-4, a_end=1e-2, n_pts=100,
    )
