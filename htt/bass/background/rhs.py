"""VER2 1+3 PSTF background RHS skeletons for the BASS S1 lane."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bass.background.constraints import (
    BackgroundConstraintResiduals,
    MatterNormalFrameState,
    evaluate_background_constraints,
)
from bass.background.geometry import TetradGeometry, div_vector, pstf_rank2

__all__ = [
    "BackgroundRhsAssembly",
    "assemble_background_rhs",
]


@dataclass(frozen=True)
class BackgroundRhsAssembly:
    """Algebraic RHS block for one background state.

    This is a contract/skeleton surface, not the final production integrator.
    Later packets may enrich it with species-resolved evolution or evolved
    algebra variables without changing the equation ownership frozen here.
    """

    H_dot: float
    sigma_dot: np.ndarray
    rho_dot: float
    residuals: BackgroundConstraintResiduals


def assemble_background_rhs(
    *,
    H: float,
    sigma_ab: np.ndarray,
    matter: MatterNormalFrameState,
    geometry: TetradGeometry,
    lambda_value: float,
    kappa: float = 1.0,
    conservation_residual: np.ndarray | None = None,
) -> BackgroundRhsAssembly:
    """Assemble the 1+3 background RHS from geometry plus matter summaries."""
    sigma = pstf_rank2(sigma_ab)
    sigma_sq = 0.5 * float(np.sum(sigma * sigma))
    H_dot = -float(H) ** 2 - (2.0 / 3.0) * sigma_sq - (kappa / 6.0) * (
        float(matter.rho) + 3.0 * float(matter.p)
    ) + float(lambda_value) / 3.0
    sigma_dot = -3.0 * float(H) * sigma - geometry.ricci_pstf + kappa * matter.pi
    rho_dot = -3.0 * float(H) * (float(matter.rho) + float(matter.p)) - div_vector(
        matter.q, geometry.Gamma
    ) - float(np.sum(sigma * matter.pi))
    residuals = evaluate_background_constraints(
        algebra=geometry.algebra,
        geometry=geometry,
        H=H,
        sigma_ab=sigma,
        matter=matter,
        lambda_value=lambda_value,
        kappa=kappa,
        conservation_residual=conservation_residual,
    )
    return BackgroundRhsAssembly(
        H_dot=H_dot,
        sigma_dot=sigma_dot,
        rho_dot=rho_dot,
        residuals=residuals,
    )
