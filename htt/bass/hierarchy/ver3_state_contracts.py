"""ver3 hierarchy state split contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from bass.collision.polarization import PolarizationHierarchyState
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, pack_hierarchy, unpack_hierarchy
from bass.hierarchy.ver3_layout_protocol import HierarchyLayout, flatten

__all__ = [
    "CanonicalLayoutProjection",
    "HierarchyState",
    "project_runtime_native_state",
]


@dataclass(frozen=True)
class HierarchyState:
    """Document-level hierarchy split frozen by the ver3 numerical SSOT."""

    matter_block: Mapping[str, object]
    photon_intensity_block: np.ndarray
    photon_polarization_block: Mapping[str, np.ndarray]
    neutrino_block: np.ndarray
    source_history_block: Mapping[str, object]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        photon_intensity = np.asarray(self.photon_intensity_block, dtype=np.float64)
        neutrino = np.asarray(self.neutrino_block, dtype=np.float64)
        polarization = {
            key: np.asarray(value, dtype=np.float64)
            for key, value in dict(self.photon_polarization_block).items()
        }
        object.__setattr__(self, "matter_block", dict(self.matter_block))
        object.__setattr__(self, "photon_intensity_block", photon_intensity)
        object.__setattr__(self, "photon_polarization_block", polarization)
        object.__setattr__(self, "neutrino_block", neutrino)
        object.__setattr__(self, "source_history_block", dict(self.source_history_block))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class CanonicalLayoutProjection:
    """Live runtime projection into the ver3 canonical hierarchy layout."""

    layout_manifest: Mapping[str, object]
    hierarchy_state: HierarchyState
    state_vector: np.ndarray
    sector_status: Mapping[str, str]
    covered_mode_labels: tuple[str, ...]
    zero_filled_mode_labels: tuple[str, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "layout_manifest", dict(self.layout_manifest))
        object.__setattr__(self, "hierarchy_state", self.hierarchy_state)
        object.__setattr__(self, "state_vector", np.asarray(self.state_vector, dtype=np.float64))
        object.__setattr__(self, "sector_status", dict(self.sector_status))
        object.__setattr__(self, "covered_mode_labels", tuple(self.covered_mode_labels))
        object.__setattr__(self, "zero_filled_mode_labels", tuple(self.zero_filled_mode_labels))
        object.__setattr__(self, "metadata", dict(self.metadata))


def _coerce_hierarchy_state(
    value: PSTFHierarchyState | np.ndarray,
    *,
    L: int,
) -> PSTFHierarchyState:
    if isinstance(value, PSTFHierarchyState):
        return value
    return unpack_hierarchy(np.asarray(value, dtype=np.float64), L)


def _coerce_polarization_state(
    value: PolarizationHierarchyState | PSTFHierarchyState | np.ndarray,
    *,
    L: int,
) -> PolarizationHierarchyState:
    if isinstance(value, PolarizationHierarchyState):
        return value
    if isinstance(value, PSTFHierarchyState):
        return PolarizationHierarchyState(E=value)
    return PolarizationHierarchyState(E=unpack_hierarchy(np.asarray(value, dtype=np.float64), L))


def _extract_local_sector(layout: HierarchyLayout, vector: np.ndarray, *, mu: str, sector: str) -> np.ndarray:
    width = int(layout.sector_local_dofs[sector])
    return np.array(
        [
            float(vector[flatten(layout, mu, sector, None, None, local_dof=i)])
            for i in range(width)
        ],
        dtype=np.float64,
    )


def project_runtime_native_state(
    *,
    layout: HierarchyLayout,
    layout_manifest: Mapping[str, object],
    photon_T: PSTFHierarchyState | np.ndarray,
    photon_E: PolarizationHierarchyState | PSTFHierarchyState | np.ndarray,
    neutrino_tower: PSTFHierarchyState | np.ndarray,
    source_template: np.ndarray,
    covered_mode_label: str | None = None,
) -> CanonicalLayoutProjection:
    """Embed the live Tier-B harmonic towers into the ver3 canonical sector order.

    Current native Tier-B evolves one effective harmonic bundle. This helper
    projects that bundle onto one canonical mode label and zero-fills the
    remaining mode labels and non-evolved local sectors while preserving the
    ver3 source-history block from ``ModeOps.source_template``.
    """

    if not layout.mode_labels:
        raise ValueError("layout.mode_labels must be non-empty")
    covered = layout.mode_labels[0] if covered_mode_label is None else str(covered_mode_label)
    if covered not in layout.mode_labels:
        raise ValueError(f"covered_mode_label {covered!r} not present in layout.mode_labels")

    L = int(layout.ell_max)
    photon_T_state = _coerce_hierarchy_state(photon_T, L=L)
    photon_E_state = _coerce_polarization_state(photon_E, L=L)
    neutrino_state = _coerce_hierarchy_state(neutrino_tower, L=L)
    source = np.asarray(source_template, dtype=np.float64)
    if source.shape != (layout.size,):
        raise ValueError(
            f"source_template shape {source.shape} does not match layout size {layout.size}"
        )

    vector = np.zeros(layout.size, dtype=np.float64)
    for mu in layout.mode_labels:
        for local_dof in range(layout.sector_local_dofs["src"]):
            idx = flatten(layout, mu, "src", None, None, local_dof=local_dof)
            vector[idx] = float(source[idx])

    tower_T = np.asarray(pack_hierarchy(photon_T_state), dtype=np.float64)
    tower_E = np.asarray(pack_hierarchy(photon_E_state.E), dtype=np.float64)
    tower_nu = np.asarray(pack_hierarchy(neutrino_state), dtype=np.float64)
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            slot = sum(2 * l + 1 for l in range(ell)) + (m + ell)
            vector[flatten(layout, covered, "ph_I", ell, m)] = float(tower_T[slot])
            vector[flatten(layout, covered, "ph_E", ell, m)] = float(tower_E[slot])
            vector[flatten(layout, covered, "nu_I", ell, m)] = float(tower_nu[slot])

    hierarchy_state = HierarchyState(
        matter_block={
            "baryon": _extract_local_sector(layout, vector, mu=covered, sector="baryon"),
            "cdm": _extract_local_sector(layout, vector, mu=covered, sector="cdm"),
        },
        photon_intensity_block=tower_T,
        photon_polarization_block={
            "E": tower_E,
            "B": np.zeros_like(tower_E),
        },
        neutrino_block=tower_nu,
        source_history_block={
            "src": _extract_local_sector(layout, vector, mu=covered, sector="src"),
        },
        metadata={
            "covered_mode_label": covered,
            "zero_filled_mode_labels": [mu for mu in layout.mode_labels if mu != covered],
            "sector_status": {
                "ph_I": "live_runtime_projection",
                "ph_E": "live_runtime_projection",
                "ph_B": "zero_filled_not_evolved",
                "nu_I": "live_runtime_projection",
                "baryon": "zero_filled_local_sector_not_evolved",
                "cdm": "zero_filled_local_sector_not_evolved",
                "src": "mode_ops_source_template",
            },
        },
    )
    zero_filled = tuple(mu for mu in layout.mode_labels if mu != covered)
    sector_status = dict(hierarchy_state.metadata["sector_status"])
    source_block = np.asarray(hierarchy_state.source_history_block["src"], dtype=np.float64)
    return CanonicalLayoutProjection(
        layout_manifest=dict(layout_manifest),
        hierarchy_state=hierarchy_state,
        state_vector=vector,
        sector_status=sector_status,
        covered_mode_labels=(covered,),
        zero_filled_mode_labels=zero_filled,
        metadata={
            "projection_mode": "single_live_mode_label_with_zero_filled_residual_layout",
            "state_norm": float(np.linalg.norm(vector)),
            "source_block_norm": float(np.linalg.norm(source_block)),
            "source_block_nonzero": bool(np.any(np.abs(source_block) > 0.0)),
            "source_block_owner": str(sector_status["src"]),
        },
    )
