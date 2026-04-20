"""VER2 initial-condition builder interfaces for the BASS S1 lane.

These builders are intentionally lightweight. `SK-01S1` freezes the contracts,
constraint bookkeeping, and branch metadata so later packets can replace the
internals with full solver logic without changing the public skeleton surface.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal

import numpy as np

from bass.background.bianchi_types import BianchiAlgebra
from bass.background.constraints import (
    BackgroundConstraintResiduals,
    MatterNormalFrameState,
    evaluate_background_constraints,
)
from bass.background.geometry import TetradGeometry, build_geometry, pstf_rank2
from bass.tilt.species_tilt import TiltedMatterState, TiltedSpeciesDecomposition, assemble_tilted_matter_state

__all__ = [
    "OrthogonalInitialConditions",
    "TiltedInitialConditions",
    "solve_expanding_H",
    "project_trace_free_shear",
    "build_orthogonal_initial_conditions",
    "build_tilted_initial_conditions",
]


@dataclass(frozen=True)
class OrthogonalInitialConditions:
    algebra: BianchiAlgebra
    geometry: TetradGeometry
    H: float
    sigma_ab: np.ndarray
    matter: MatterNormalFrameState
    residuals: BackgroundConstraintResiduals
    closure: str


@dataclass(frozen=True)
class TiltedInitialConditions:
    algebra: BianchiAlgebra
    geometry: TetradGeometry
    H: float
    sigma_ab: np.ndarray
    matter: TiltedMatterState
    residuals: BackgroundConstraintResiduals
    closure: str


def project_trace_free_shear(sigma_ab: np.ndarray) -> np.ndarray:
    """Project an arbitrary spatial shear guess onto the PSTF surface."""
    return pstf_rank2(np.asarray(sigma_ab, dtype=np.float64))


def solve_expanding_H(
    *,
    rho: float,
    sigma_ab: np.ndarray,
    ricci_scalar: float,
    lambda_value: float,
    kappa: float = 1.0,
) -> float:
    """Solve the expanding-branch Gauss constraint for `H`."""
    sigma = np.asarray(sigma_ab, dtype=np.float64)
    sigma_sq = 0.5 * float(np.sum(sigma * sigma))
    radicand = (kappa * float(rho) + float(lambda_value) + sigma_sq - 0.5 * float(ricci_scalar)) / 3.0
    if radicand < 0.0:
        raise ValueError(
            f"Expanding-branch Gauss solve requires a non-negative radicand; got {radicand!r}"
        )
    return math.sqrt(radicand)


def _resolve_H(
    *,
    H: float | None,
    matter: MatterNormalFrameState,
    sigma_ab: np.ndarray,
    geometry: TetradGeometry,
    lambda_value: float,
    closure: Literal["solve_H", "hold_H"],
    kappa: float,
) -> float:
    if closure == "solve_H":
        return solve_expanding_H(
            rho=matter.rho,
            sigma_ab=sigma_ab,
            ricci_scalar=geometry.ricci_scalar,
            lambda_value=lambda_value,
            kappa=kappa,
        )
    if closure == "hold_H":
        if H is None:
            raise ValueError("closure='hold_H' requires an explicit H value")
        return float(H)
    raise ValueError(f"Unknown closure policy {closure!r}")


def build_orthogonal_initial_conditions(
    *,
    algebra: BianchiAlgebra,
    rho: float,
    p: float,
    sigma_ab: np.ndarray | None = None,
    lambda_value: float = 0.0,
    H: float | None = None,
    closure: Literal["solve_H", "hold_H"] = "solve_H",
    kappa: float = 1.0,
) -> OrthogonalInitialConditions:
    """Build an orthogonal-branch IC bundle plus machine-readable residuals."""
    geometry = build_geometry(algebra)
    sigma = project_trace_free_shear(np.zeros((3, 3)) if sigma_ab is None else sigma_ab)
    matter = MatterNormalFrameState(rho=float(rho), p=float(p))
    H_value = _resolve_H(
        H=H,
        matter=matter,
        sigma_ab=sigma,
        geometry=geometry,
        lambda_value=lambda_value,
        closure=closure,
        kappa=kappa,
    )
    residuals = evaluate_background_constraints(
        algebra=algebra,
        geometry=geometry,
        H=H_value,
        sigma_ab=sigma,
        matter=matter,
        lambda_value=lambda_value,
        kappa=kappa,
    )
    return OrthogonalInitialConditions(
        algebra=algebra,
        geometry=geometry,
        H=H_value,
        sigma_ab=sigma,
        matter=matter,
        residuals=residuals,
        closure=closure,
    )


def build_tilted_initial_conditions(
    *,
    algebra: BianchiAlgebra,
    species: Iterable[TiltedSpeciesDecomposition],
    sigma_ab: np.ndarray | None = None,
    lambda_value: float = 0.0,
    H: float | None = None,
    closure: Literal["solve_H", "hold_H"] = "solve_H",
    kappa: float = 1.0,
) -> TiltedInitialConditions:
    """Build a tilted-branch IC bundle plus machine-readable residuals."""
    geometry = build_geometry(algebra)
    sigma = project_trace_free_shear(np.zeros((3, 3)) if sigma_ab is None else sigma_ab)
    matter = assemble_tilted_matter_state(tuple(species))
    normal_frame = MatterNormalFrameState(rho=matter.rho, p=matter.p, q=matter.q, pi=matter.pi)
    H_value = _resolve_H(
        H=H,
        matter=normal_frame,
        sigma_ab=sigma,
        geometry=geometry,
        lambda_value=lambda_value,
        closure=closure,
        kappa=kappa,
    )
    residuals = evaluate_background_constraints(
        algebra=algebra,
        geometry=geometry,
        H=H_value,
        sigma_ab=sigma,
        matter=normal_frame,
        lambda_value=lambda_value,
        kappa=kappa,
    )
    return TiltedInitialConditions(
        algebra=algebra,
        geometry=geometry,
        H=H_value,
        sigma_ab=sigma,
        matter=matter,
        residuals=residuals,
        closure=closure,
    )
