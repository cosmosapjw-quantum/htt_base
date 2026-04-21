"""Barotropic matter closures for the VER2 S1 background solver."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bass.background.constraints import MatterNormalFrameState
from bass.tilt.species_tilt import (
    TiltedMatterState,
    TiltedSpeciesDecomposition,
    TiltedSpeciesParams,
    assemble_tilted_matter_state,
    decompose_tilted_species,
)

__all__ = [
    "OrthogonalBarotropicClosure",
    "TiltedBarotropicClosure",
]


@dataclass(frozen=True)
class OrthogonalBarotropicClosure:
    rho_ref: float
    w: float
    a_ref: float

    @classmethod
    def from_state(
        cls,
        state: MatterNormalFrameState,
        *,
        a_ref: float,
    ) -> "OrthogonalBarotropicClosure":
        rho_ref = float(state.rho)
        w = 0.0 if abs(rho_ref) < 1.0e-30 else float(state.p) / rho_ref
        return cls(rho_ref=rho_ref, w=w, a_ref=float(a_ref))

    def state_at_scale_factor(self, a: float) -> MatterNormalFrameState:
        factor = (float(self.a_ref) / float(a)) ** (3.0 * (1.0 + float(self.w)))
        rho = float(self.rho_ref) * factor
        return MatterNormalFrameState(rho=rho, p=float(self.w) * rho)


@dataclass(frozen=True)
class TiltedBarotropicClosure:
    species: tuple[TiltedSpeciesDecomposition, ...]
    a_ref: float

    @classmethod
    def from_state(
        cls,
        state: TiltedMatterState,
        *,
        a_ref: float,
    ) -> "TiltedBarotropicClosure":
        return cls(species=tuple(state.species), a_ref=float(a_ref))

    def state_at_scale_factor(self, a: float) -> TiltedMatterState:
        scale = float(self.a_ref) / float(a)
        evolved: list[TiltedSpeciesDecomposition] = []
        for piece in self.species:
            rho_hat_ref = float(piece.params.rho_hat)
            w = 0.0 if abs(rho_hat_ref) < 1.0e-30 else float(piece.params.p_hat) / rho_hat_ref
            rho_hat = rho_hat_ref * scale ** (3.0 * (1.0 + w))
            params = TiltedSpeciesParams(
                rho_hat=rho_hat,
                p_hat=w * rho_hat,
                v=np.asarray(piece.params.v, dtype=np.float64),
                label=piece.params.label,
            )
            evolved.append(decompose_tilted_species(params))
        return assemble_tilted_matter_state(tuple(evolved))
