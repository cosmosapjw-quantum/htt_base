"""
tsc/diagnostics/species_tangency.py  (Week 3 Day 4, merged v4.1)
=================================================================

Species-resolved batch tangency diagnostic for the cosmological species
stack {photon γ, neutrinos ν_e, ν_μ, ν_τ}.

Role in Paper I
---------------
Section §III of Paper I defines the tangency diagnostic D_{s, ≥ 2} per
species s. The single-species engine lives in `tangency.compute_D_diagnostic`.
This module layers a batch computation over the four cosmological species,
keeping per-species results accessible while also exposing aggregate
statistics needed by the runtime (`worst_species`, `total_D_sq`,
`all_tangent`, species-weighted on-manifold fraction).

Chart assignment (default)
--------------------------
Photon γ uses ONE_FIELD (Θ-only ansatz, Paper I §IV.A). Neutrinos ν_e, ν_μ,
ν_τ use TWO_FIELD (Θ and η fugacity, Paper I §IV.B). Callers can override
the chart assignment per species — e.g., to probe a one-field ν as a
sensitivity test.

Non-goals
---------
- No G_field construction: collision sources are the caller's responsibility
  (W4 collision modules will produce them).
- No runtime allow/block decision: this module is pure diagnostics. The
  consumer (`canonical_decision.source_Dge2_gate`) aggregates over species
  by taking the worst-species result or the total leakage, per its own policy.
- No TSC → BASS runtime coupling: that wiring is executed at the W3D5b
  freeze commit.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, Sequence

import numpy as np

# Current (pre-freeze) import; after W3D5b becomes tsc.diagnostics.tangency
from tsc.diagnostics.tangency import (
    TangentKind,
    TangencyResult,
    compute_D_diagnostic,
)


# ============================================================================
# Section 1 - Species enumeration
# ============================================================================

class CosmologicalSpecies(Enum):
    """Four species covered by this batch diagnostic.

    PHOTON : CMB photons (Bose-Einstein, ξ = +1). Standard chart: ONE_FIELD.
    NU_E, NU_MU, NU_TAU : Three neutrino flavors (Fermi-Dirac, ξ = -1).
        Standard chart: TWO_FIELD to carry independent η per flavor, which
        the Paper I framework needs to capture flavor-dependent chemical
        potential.
    """
    PHOTON = "photon"
    NU_E = "nu_e"
    NU_MU = "nu_mu"
    NU_TAU = "nu_tau"


NEUTRINO_FLAVORS: tuple = (
    CosmologicalSpecies.NU_E,
    CosmologicalSpecies.NU_MU,
    CosmologicalSpecies.NU_TAU,
)


# ============================================================================
# Section 2 - Per-species chart specification
# ============================================================================

@dataclass(frozen=True)
class SpeciesChart:
    """Per-species chart assignment for the Paper I tangency diagnostic.

    Attributes
    ----------
    species : CosmologicalSpecies
    xi : int
        Statistics parameter ∈ {-1, 0, +1}.
    kind : TangentKind
        ONE_FIELD (Θ-only) or TWO_FIELD (Θ + η).
    eta : float
        Fugacity at which the tangency diagnostic is evaluated. Must be ≤ 0
        for BE.
    """
    species: CosmologicalSpecies
    xi: int
    kind: TangentKind
    eta: float = 0.0

    def __post_init__(self) -> None:
        if self.xi not in (-1, 0, +1):
            raise ValueError(
                f"xi must be in {{-1, 0, +1}}, got {self.xi}"
            )
        if self.xi == +1 and self.eta > 1e-15:
            raise ValueError(
                f"BE requires eta ≤ 0, got eta={self.eta} for {self.species}"
            )


# Default chart set matching the standard cosmological picture
DEFAULT_SPECIES_CHARTS: tuple = (
    SpeciesChart(CosmologicalSpecies.PHOTON,
                 xi=+1, kind=TangentKind.ONE_FIELD, eta=0.0),
    SpeciesChart(CosmologicalSpecies.NU_E,
                 xi=-1, kind=TangentKind.TWO_FIELD, eta=0.0),
    SpeciesChart(CosmologicalSpecies.NU_MU,
                 xi=-1, kind=TangentKind.TWO_FIELD, eta=0.0),
    SpeciesChart(CosmologicalSpecies.NU_TAU,
                 xi=-1, kind=TangentKind.TWO_FIELD, eta=0.0),
)


# ============================================================================
# Section 3 - Aggregated result
# ============================================================================

@dataclass(frozen=True)
class SpeciesTangencyResult:
    """Aggregate tangency diagnostic across the species stack.

    Attributes
    ----------
    per_species : Mapping[CosmologicalSpecies, TangencyResult]
        Single-species result for each input species.
    species_order : tuple
        Deterministic iteration order used during aggregation.
    all_tangent : bool
        True iff every species has `is_tangent == True`.
    total_D_sq : float
        Sum over species of D_s². This is the natural additive quantity in
        the Paper I weighted inner product.
    total_norm_sq : float
        Sum over species of ‖G_s‖².
    max_relative_residual : float
        max_s D_s / ‖G_s‖. The "weakest link" diagnostic.
    worst_species : CosmologicalSpecies
        Species attaining `max_relative_residual`.
    weighted_fraction_on_manifold : float
        Σ_s tangent_norm_sq_s / Σ_s total_norm_sq_s. Equals 1 iff
        `all_tangent`; drops as any species leaks off-manifold weighted by
        its source magnitude.
    """
    per_species: Mapping[CosmologicalSpecies, TangencyResult]
    species_order: tuple
    all_tangent: bool
    total_D_sq: float
    total_norm_sq: float
    max_relative_residual: float
    worst_species: CosmologicalSpecies
    weighted_fraction_on_manifold: float


# ============================================================================
# Section 4 - Main computation
# ============================================================================

def compute_species_tangency(
    G_fields: Mapping[CosmologicalSpecies, Callable[[np.ndarray], np.ndarray]],
    charts: Sequence[SpeciesChart] = DEFAULT_SPECIES_CHARTS,
    alpha: float = 2.0,
) -> SpeciesTangencyResult:
    """Run the Paper I tangency diagnostic for each species.

    Parameters
    ----------
    G_fields : mapping
        Per-species collision source G_s(x). Every species listed in
        `charts` must have a G_field. Extra keys are ignored.
    charts : sequence of SpeciesChart
        Chart assignment. Defaults to `DEFAULT_SPECIES_CHARTS`
        (γ one-field BE, ν_{e,μ,τ} two-field FD).
    alpha : float
        Laguerre weight parameter passed through to `compute_D_diagnostic`.

    Returns
    -------
    SpeciesTangencyResult

    Raises
    ------
    ValueError
        If `G_fields` is missing an entry for any species in `charts`, or if
        `charts` contains duplicate species entries.
    """
    species_in_charts = [c.species for c in charts]
    if len(set(species_in_charts)) != len(species_in_charts):
        raise ValueError(
            f"charts contains duplicate species entries: {species_in_charts}"
        )

    missing = [s for s in species_in_charts if s not in G_fields]
    if missing:
        raise ValueError(
            f"G_fields is missing entries for: {[s.value for s in missing]}"
        )

    per_species: dict = {}
    species_order = tuple(species_in_charts)

    for chart in charts:
        G = G_fields[chart.species]
        result = compute_D_diagnostic(
            G_field=G,
            kind=chart.kind,
            xi=chart.xi,
            eta=chart.eta,
            alpha=alpha,
        )
        per_species[chart.species] = result

    return _aggregate(per_species, species_order)


# ============================================================================
# Section 5 - Aggregation helpers
# ============================================================================

def _aggregate(
    per_species: Mapping[CosmologicalSpecies, TangencyResult],
    species_order: tuple,
) -> SpeciesTangencyResult:
    """Combine per-species results into the aggregate container."""
    D_sq_list = [per_species[s].D_sq for s in species_order]
    total_norm_list = [per_species[s].total_norm_sq for s in species_order]
    tangent_norm_list = [
        per_species[s].tangent_norm_sq for s in species_order
    ]

    total_D_sq = float(sum(D_sq_list))
    total_norm_sq = float(sum(total_norm_list))
    total_tangent = float(sum(tangent_norm_list))

    # max relative residual picks the worst species
    rel_residuals = np.array(
        [per_species[s].relative_residual for s in species_order]
    )
    worst_idx = int(np.argmax(rel_residuals))
    worst_species = species_order[worst_idx]
    max_rel_residual = float(rel_residuals[worst_idx])

    all_tangent = bool(
        all(per_species[s].is_tangent for s in species_order)
    )

    if total_norm_sq > 0:
        weighted_fraction = total_tangent / total_norm_sq
    else:
        weighted_fraction = 1.0

    return SpeciesTangencyResult(
        per_species=dict(per_species),
        species_order=species_order,
        all_tangent=all_tangent,
        total_D_sq=total_D_sq,
        total_norm_sq=total_norm_sq,
        max_relative_residual=max_rel_residual,
        worst_species=worst_species,
        weighted_fraction_on_manifold=float(weighted_fraction),
    )


# ============================================================================
# Section 6 - Species selectors (convenience)
# ============================================================================

def tangent_species(
    result: SpeciesTangencyResult,
) -> tuple:
    """Return species that passed the is_tangent threshold, in stable order."""
    return tuple(
        s for s in result.species_order
        if result.per_species[s].is_tangent
    )


def off_manifold_species(
    result: SpeciesTangencyResult,
) -> tuple:
    """Return species that failed the is_tangent threshold, in stable order."""
    return tuple(
        s for s in result.species_order
        if not result.per_species[s].is_tangent
    )


def per_species_relative_residuals(
    result: SpeciesTangencyResult,
) -> dict:
    """Convenience view: {species: D_s / ‖G_s‖} mapping."""
    return {
        s: float(result.per_species[s].relative_residual)
        for s in result.species_order
    }


# ============================================================================
# Section 7 - Chart override helpers
# ============================================================================

def override_neutrino_chart_one_field(
    eta: float = 0.0,
) -> tuple:
    """Return a chart set that forces ν into ONE_FIELD (sensitivity probe).

    This is the Paper I §IV sensitivity configuration: when the chemistry
    closure demands a one-field ν, the batch diagnostic must still run. The
    default chart set keeps ν two-field.
    """
    return (
        SpeciesChart(CosmologicalSpecies.PHOTON,
                     xi=+1, kind=TangentKind.ONE_FIELD, eta=0.0),
        SpeciesChart(CosmologicalSpecies.NU_E,
                     xi=-1, kind=TangentKind.ONE_FIELD, eta=eta),
        SpeciesChart(CosmologicalSpecies.NU_MU,
                     xi=-1, kind=TangentKind.ONE_FIELD, eta=eta),
        SpeciesChart(CosmologicalSpecies.NU_TAU,
                     xi=-1, kind=TangentKind.ONE_FIELD, eta=eta),
    )


def photon_only_chart() -> tuple:
    """Return a chart set containing only the photon species.

    Useful for unit-testing or when neutrinos are treated separately.
    """
    return (
        SpeciesChart(CosmologicalSpecies.PHOTON,
                     xi=+1, kind=TangentKind.ONE_FIELD, eta=0.0),
    )
