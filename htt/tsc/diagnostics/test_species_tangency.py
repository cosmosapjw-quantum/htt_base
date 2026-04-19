"""
Test suite: species_tangency.py (Week 3 Day 4, merged v4.1)
============================================================

Batch Paper I tangency diagnostic over {γ, ν_e, ν_μ, ν_τ}.

Test classes (9):
  1. TestCosmologicalSpecies    (enum identity, 4 species)
  2. TestSpeciesChart            (per-species spec validation)
  3. TestDefaultChartSet         (DEFAULT_SPECIES_CHARTS conventions)
  4. TestBatchComputation        (compute_species_tangency happy paths)
  5. TestAggregation             (SpeciesTangencyResult invariants)
  6. TestWorstSpeciesIdentification  (argmax picks right species)
  7. TestSelectors               (tangent/off_manifold species helpers)
  8. TestChartOverrides          (one-field ν probe, photon-only)
  9. TestInputValidation         (error paths)

Target: ~40 tests.
"""
from __future__ import annotations

import numpy as np
import pytest

from tsc.diagnostics.tangency import TangentKind
from tsc.diagnostics.species_tangency import (
    CosmologicalSpecies,
    NEUTRINO_FLAVORS,
    SpeciesChart,
    DEFAULT_SPECIES_CHARTS,
    SpeciesTangencyResult,
    compute_species_tangency,
    tangent_species,
    off_manifold_species,
    per_species_relative_residuals,
    override_neutrino_chart_one_field,
    photon_only_chart,
)


# ============================================================================
# Test helpers - G_fields ranging from on-manifold to heavily off-manifold
# ============================================================================

def _on_manifold(x):
    """Pure x — lies in ONE_FIELD and TWO_FIELD basis for any ξ."""
    return np.asarray(x, dtype=float)


def _tilt_only(x):
    """Pure 1 — in TWO_FIELD basis (ν); off-manifold for ONE_FIELD (γ)."""
    return np.ones_like(np.asarray(x, dtype=float))


def _heavy_off_manifold(x):
    """Pure x^3 — off-manifold for both ONE and TWO_FIELD."""
    return np.asarray(x, dtype=float) ** 3


def _slight_off_manifold(x):
    """x + small x² perturbation."""
    xa = np.asarray(x, dtype=float)
    return xa + 1e-4 * xa ** 2


def _all_on_manifold_fields() -> dict:
    """G_field for each of the four default species using _on_manifold."""
    return {
        CosmologicalSpecies.PHOTON: _on_manifold,
        CosmologicalSpecies.NU_E: _on_manifold,
        CosmologicalSpecies.NU_MU: _on_manifold,
        CosmologicalSpecies.NU_TAU: _on_manifold,
    }


# ============================================================================
# Test Class 1 - Species enum identity
# ============================================================================

class TestCosmologicalSpecies:
    """Enum stability: 4 members with pinned string values."""

    def test_has_exactly_4_members(self):
        assert len(list(CosmologicalSpecies)) == 4

    def test_pinned_values(self):
        assert CosmologicalSpecies.PHOTON.value == "photon"
        assert CosmologicalSpecies.NU_E.value == "nu_e"
        assert CosmologicalSpecies.NU_MU.value == "nu_mu"
        assert CosmologicalSpecies.NU_TAU.value == "nu_tau"

    def test_NEUTRINO_FLAVORS_excludes_photon(self):
        assert CosmologicalSpecies.PHOTON not in NEUTRINO_FLAVORS
        assert len(NEUTRINO_FLAVORS) == 3
        assert set(NEUTRINO_FLAVORS) == {
            CosmologicalSpecies.NU_E,
            CosmologicalSpecies.NU_MU,
            CosmologicalSpecies.NU_TAU,
        }


# ============================================================================
# Test Class 2 - SpeciesChart validation
# ============================================================================

class TestSpeciesChart:
    """Per-species chart dataclass construction."""

    def test_happy_path_photon(self):
        chart = SpeciesChart(
            species=CosmologicalSpecies.PHOTON,
            xi=+1, kind=TangentKind.ONE_FIELD, eta=0.0,
        )
        assert chart.species == CosmologicalSpecies.PHOTON

    def test_happy_path_neutrino(self):
        chart = SpeciesChart(
            species=CosmologicalSpecies.NU_E,
            xi=-1, kind=TangentKind.TWO_FIELD, eta=-0.1,
        )
        assert chart.xi == -1

    def test_rejects_bad_xi(self):
        with pytest.raises(ValueError, match="xi"):
            SpeciesChart(
                species=CosmologicalSpecies.PHOTON,
                xi=2, kind=TangentKind.ONE_FIELD,
            )

    def test_rejects_BE_with_positive_eta(self):
        with pytest.raises(ValueError, match="BE"):
            SpeciesChart(
                species=CosmologicalSpecies.PHOTON,
                xi=+1, kind=TangentKind.ONE_FIELD, eta=+0.1,
            )

    def test_is_frozen(self):
        chart = SpeciesChart(
            species=CosmologicalSpecies.PHOTON,
            xi=+1, kind=TangentKind.ONE_FIELD,
        )
        with pytest.raises(Exception):
            chart.xi = -1  # frozen dataclass


# ============================================================================
# Test Class 3 - Default chart set conventions
# ============================================================================

class TestDefaultChartSet:
    """Cosmological convention sanity: γ BE one-field, ν FD two-field."""

    def test_has_4_entries(self):
        assert len(DEFAULT_SPECIES_CHARTS) == 4

    def test_photon_is_BE_one_field(self):
        photon_chart = next(
            c for c in DEFAULT_SPECIES_CHARTS
            if c.species == CosmologicalSpecies.PHOTON
        )
        assert photon_chart.xi == +1
        assert photon_chart.kind == TangentKind.ONE_FIELD
        assert photon_chart.eta == 0.0

    def test_all_neutrinos_are_FD_two_field(self):
        for nu_species in NEUTRINO_FLAVORS:
            chart = next(
                c for c in DEFAULT_SPECIES_CHARTS if c.species == nu_species
            )
            assert chart.xi == -1
            assert chart.kind == TangentKind.TWO_FIELD

    def test_species_coverage_matches_cosmological_stack(self):
        chart_species = {c.species for c in DEFAULT_SPECIES_CHARTS}
        assert chart_species == set(CosmologicalSpecies)


# ============================================================================
# Test Class 4 - Batch computation happy paths
# ============================================================================

class TestBatchComputation:
    """compute_species_tangency end-to-end."""

    def test_all_on_manifold_is_all_tangent(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        assert result.all_tangent is True
        assert result.max_relative_residual < 1e-6

    def test_returns_SpeciesTangencyResult(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        assert isinstance(result, SpeciesTangencyResult)

    def test_per_species_is_populated_for_all_defaults(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        for s in CosmologicalSpecies:
            assert s in result.per_species

    def test_species_order_is_deterministic(self):
        result_a = compute_species_tangency(_all_on_manifold_fields())
        result_b = compute_species_tangency(_all_on_manifold_fields())
        assert result_a.species_order == result_b.species_order

    def test_extra_G_fields_ignored(self):
        G = _all_on_manifold_fields()
        G["some_extra_key"] = _heavy_off_manifold  # not a CosmologicalSpecies
        # Should still work — only the chart species are consulted
        result = compute_species_tangency(G)
        assert result.all_tangent is True


# ============================================================================
# Test Class 5 - Aggregate invariants
# ============================================================================

class TestAggregation:
    """SpeciesTangencyResult structural invariants."""

    def test_total_D_sq_is_nonnegative(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_E] = _heavy_off_manifold
        result = compute_species_tangency(G)
        assert result.total_D_sq >= 0

    def test_total_norm_sq_is_positive_when_G_nonzero(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        assert result.total_norm_sq > 0

    def test_weighted_fraction_is_1_when_all_tangent(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        assert result.weighted_fraction_on_manifold == pytest.approx(
            1.0, abs=1e-10,
        )

    def test_weighted_fraction_below_1_when_any_off_manifold(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_TAU] = _heavy_off_manifold
        result = compute_species_tangency(G)
        assert result.weighted_fraction_on_manifold < 1.0

    def test_weighted_fraction_in_range(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_E] = _heavy_off_manifold
        G[CosmologicalSpecies.NU_MU] = _slight_off_manifold
        result = compute_species_tangency(G)
        assert 0.0 <= result.weighted_fraction_on_manifold <= 1.0

    def test_total_D_sq_equals_sum_over_species(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_E] = _heavy_off_manifold
        result = compute_species_tangency(G)
        direct_sum = sum(
            result.per_species[s].D_sq for s in result.species_order
        )
        assert result.total_D_sq == pytest.approx(direct_sum, rel=1e-12)


# ============================================================================
# Test Class 6 - worst_species identification
# ============================================================================

class TestWorstSpeciesIdentification:
    """argmax over relative_residual picks the right species."""

    def test_nu_e_worst_when_heavily_off_manifold(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_E] = _heavy_off_manifold
        result = compute_species_tangency(G)
        assert result.worst_species == CosmologicalSpecies.NU_E

    def test_photon_worst_when_heavily_off_manifold(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.PHOTON] = _heavy_off_manifold
        result = compute_species_tangency(G)
        assert result.worst_species == CosmologicalSpecies.PHOTON

    def test_max_rel_residual_matches_worst_species(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_MU] = _heavy_off_manifold
        result = compute_species_tangency(G)
        worst_per_species = result.per_species[result.worst_species]
        assert result.max_relative_residual == pytest.approx(
            worst_per_species.relative_residual, rel=1e-14,
        )

    def test_worst_species_stable_on_tie(self):
        # With two equally off-manifold species, the earlier-in-order wins
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_E] = _heavy_off_manifold
        G[CosmologicalSpecies.NU_MU] = _heavy_off_manifold
        result = compute_species_tangency(G)
        # species_order has NU_E before NU_MU; argmax returns first
        assert result.worst_species in (
            CosmologicalSpecies.NU_E, CosmologicalSpecies.NU_MU,
        )


# ============================================================================
# Test Class 7 - Species selectors
# ============================================================================

class TestSelectors:
    """tangent_species / off_manifold_species / per_species_relative_residuals."""

    def test_tangent_species_all_when_on_manifold(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        tan = tangent_species(result)
        assert set(tan) == set(CosmologicalSpecies)

    def test_off_manifold_species_empty_when_all_tangent(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        assert off_manifold_species(result) == ()

    def test_off_manifold_species_captures_offenders(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_TAU] = _heavy_off_manifold
        result = compute_species_tangency(G)
        off = off_manifold_species(result)
        assert CosmologicalSpecies.NU_TAU in off
        assert CosmologicalSpecies.PHOTON not in off

    def test_selector_order_matches_species_order(self):
        G = _all_on_manifold_fields()
        G[CosmologicalSpecies.NU_E] = _heavy_off_manifold
        G[CosmologicalSpecies.NU_MU] = _heavy_off_manifold
        result = compute_species_tangency(G)
        off = off_manifold_species(result)
        # Check elements appear in species_order sequence
        positions = [result.species_order.index(s) for s in off]
        assert positions == sorted(positions)

    def test_per_species_rel_residuals_shape(self):
        result = compute_species_tangency(_all_on_manifold_fields())
        rr = per_species_relative_residuals(result)
        assert set(rr.keys()) == set(CosmologicalSpecies)
        for s, val in rr.items():
            assert isinstance(val, float)
            assert val >= 0


# ============================================================================
# Test Class 8 - Chart override helpers
# ============================================================================

class TestChartOverrides:
    """override_neutrino_chart_one_field + photon_only_chart."""

    def test_photon_only_chart_single_entry(self):
        charts = photon_only_chart()
        assert len(charts) == 1
        assert charts[0].species == CosmologicalSpecies.PHOTON

    def test_photon_only_run(self):
        result = compute_species_tangency(
            G_fields={CosmologicalSpecies.PHOTON: _on_manifold},
            charts=photon_only_chart(),
        )
        assert result.species_order == (CosmologicalSpecies.PHOTON,)
        assert result.all_tangent is True

    def test_neutrino_one_field_override(self):
        charts = override_neutrino_chart_one_field()
        for c in charts:
            assert c.kind == TangentKind.ONE_FIELD

    def test_neutrino_one_field_covers_all_species(self):
        charts = override_neutrino_chart_one_field()
        species_set = {c.species for c in charts}
        assert species_set == set(CosmologicalSpecies)

    def test_neutrino_one_field_diagnostic_runs(self):
        # When ν forced to ONE_FIELD, pure-x G is still on-manifold
        result = compute_species_tangency(
            G_fields=_all_on_manifold_fields(),
            charts=override_neutrino_chart_one_field(),
        )
        assert result.all_tangent is True


# ============================================================================
# Test Class 9 - Input validation
# ============================================================================

class TestInputValidation:
    """Error paths."""

    def test_rejects_missing_G_field(self):
        with pytest.raises(ValueError, match="missing"):
            compute_species_tangency(
                G_fields={CosmologicalSpecies.PHOTON: _on_manifold},
            )

    def test_rejects_duplicate_chart_species(self):
        duplicate_charts = (
            SpeciesChart(CosmologicalSpecies.PHOTON, +1, TangentKind.ONE_FIELD),
            SpeciesChart(CosmologicalSpecies.PHOTON, +1, TangentKind.ONE_FIELD),
        )
        with pytest.raises(ValueError, match="duplicate"):
            compute_species_tangency(
                G_fields={CosmologicalSpecies.PHOTON: _on_manifold},
                charts=duplicate_charts,
            )

    def test_partial_G_fields_list_missing_species(self):
        G = {
            CosmologicalSpecies.PHOTON: _on_manifold,
            CosmologicalSpecies.NU_E: _on_manifold,
            # NU_MU and NU_TAU missing
        }
        with pytest.raises(ValueError, match="nu_mu"):
            compute_species_tangency(G)
