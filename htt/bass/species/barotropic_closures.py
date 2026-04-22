"""Barotropic matter closures for the VER2 S1 background solver."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from bass.background.constraints import MatterNormalFrameState
from bass.species.base import CANONICAL_ORDER, SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
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
    "OrthogonalSpeciesRegistryClosure",
    "TiltedSpeciesRegistryClosure",
    "DynamicTiltedSpeciesRegistryClosure",
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


@dataclass(frozen=True)
class OrthogonalSpeciesRegistryClosure:
    """Species-backed orthogonal matter closure over the shared FLRW table.

    This keeps the S1 background path aligned with the live LB-1 species
    mixture instead of freezing a single effective ``w`` at ``a_ref``.
    """

    registry: SpeciesBackgroundRegistry
    include_lambda: bool = False

    def state_at_scale_factor(self, a: float) -> MatterNormalFrameState:
        eta = float(self.registry.bg_table.eta_at_a(float(a)))
        rho = 0.0
        p = 0.0
        for label in CANONICAL_ORDER:
            if not self.include_lambda and label is SpeciesLabel.LAMBDA:
                continue
            rho += float(self.registry[label].rho_rest(eta))
            p += float(self.registry[label].p_rest(eta))
        return MatterNormalFrameState(rho=rho, p=p)


@dataclass(frozen=True)
class TiltedSpeciesRegistryClosure:
    """Species-backed tilted matter closure with fixed velocity direction."""

    registry: SpeciesBackgroundRegistry
    velocity: np.ndarray
    label_formatter: Callable[[SpeciesLabel], str] = str

    def __post_init__(self) -> None:
        velocity = np.asarray(self.velocity, dtype=np.float64)
        if velocity.shape != (3,):
            raise ValueError(
                f"TiltedSpeciesRegistryClosure.velocity must have shape (3,), got {velocity.shape}"
            )
        object.__setattr__(self, "velocity", velocity)

    def state_at_scale_factor(self, a: float) -> TiltedMatterState:
        eta = float(self.registry.bg_table.eta_at_a(float(a)))
        pieces: list[TiltedSpeciesDecomposition] = []
        for label in CANONICAL_ORDER:
            if label is SpeciesLabel.LAMBDA:
                continue
            pieces.append(
                decompose_tilted_species(
                    TiltedSpeciesParams(
                        rho_hat=float(self.registry[label].rho_rest(eta)),
                        p_hat=float(self.registry[label].p_rest(eta)),
                        v=self.velocity,
                        label=self.label_formatter(label),
                    )
                )
            )
        return assemble_tilted_matter_state(tuple(pieces))


@dataclass(frozen=True)
class DynamicTiltedSpeciesRegistryClosure:
    """Species-backed tilted matter closure with dynamic rapidity magnitude."""

    registry: SpeciesBackgroundRegistry
    tilt_direction: np.ndarray
    rapidity_at_scale_factor: Callable[[float], float]
    label_formatter: Callable[[SpeciesLabel], str] = str

    def __post_init__(self) -> None:
        direction = np.asarray(self.tilt_direction, dtype=np.float64)
        if direction.shape != (3,):
            raise ValueError(
                "DynamicTiltedSpeciesRegistryClosure.tilt_direction must have "
                f"shape (3,), got {direction.shape}"
            )
        norm = float(np.linalg.norm(direction))
        if norm <= 0.0:
            raise ValueError("tilt_direction must be non-zero")
        object.__setattr__(self, "tilt_direction", direction / norm)

    def state_at_scale_factor(self, a: float) -> TiltedMatterState:
        eta = float(self.registry.bg_table.eta_at_a(float(a)))
        rapidity = float(self.rapidity_at_scale_factor(float(a)))
        beta = float(np.tanh(max(rapidity, 0.0)))
        velocity = beta * np.asarray(self.tilt_direction, dtype=np.float64)
        pieces: list[TiltedSpeciesDecomposition] = []
        for label in CANONICAL_ORDER:
            if label is SpeciesLabel.LAMBDA:
                continue
            pieces.append(
                decompose_tilted_species(
                    TiltedSpeciesParams(
                        rho_hat=float(self.registry[label].rho_rest(eta)),
                        p_hat=float(self.registry[label].p_rest(eta)),
                        v=velocity,
                        label=self.label_formatter(label),
                    )
                )
            )
        return assemble_tilted_matter_state(tuple(pieces))
