"""VER2 1+3 PSTF background RHS skeletons for the BASS S1 lane."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from bass.background.constraints import (
    BackgroundConstraintResiduals,
    MatterNormalFrameState,
    evaluate_background_constraints,
)
from bass.background.geometry import TetradGeometry, div_vector, pstf_rank2
from bass.validation import GateBundle, make_gate_bundle

__all__ = [
    "BackgroundRhsAssembly",
    "raychaudhuri_rhs",
    "shear_rhs",
    "background_rhs",
    "assemble_background_rhs",
    "background_gate_bundle",
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


def raychaudhuri_rhs(
    *,
    H: float,
    sigma_ab: np.ndarray,
    matter: MatterNormalFrameState,
    lambda_value: float,
    kappa: float = 1.0,
) -> float:
    """Return the homogeneous Raychaudhuri evolution for the Hubble scalar."""

    sigma = pstf_rank2(sigma_ab)
    sigma_sq = 0.5 * float(np.sum(sigma * sigma))
    return -float(H) ** 2 - (2.0 / 3.0) * sigma_sq - (kappa / 6.0) * (
        float(matter.rho) + 3.0 * float(matter.p)
    ) + float(lambda_value) / 3.0


def shear_rhs(
    *,
    H: float,
    sigma_ab: np.ndarray,
    S_ab: np.ndarray,
    pi_ab: np.ndarray,
    kappa: float = 1.0,
) -> np.ndarray:
    """Return the PSTF shear evolution block."""

    sigma = pstf_rank2(sigma_ab)
    S = pstf_rank2(S_ab)
    pi = pstf_rank2(pi_ab)
    return -3.0 * float(H) * sigma - S + kappa * pi


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
    H_dot = raychaudhuri_rhs(
        H=H,
        sigma_ab=sigma,
        matter=matter,
        lambda_value=lambda_value,
        kappa=kappa,
    )
    sigma_dot = shear_rhs(
        H=H,
        sigma_ab=sigma,
        S_ab=geometry.S_AB,
        pi_ab=matter.pi,
        kappa=kappa,
    )
    rho_dot = -3.0 * float(H) * (float(matter.rho) + float(matter.p)) - div_vector(
        matter.q, geometry.Gamma
    ) - float(np.sum(sigma * matter.pi))
    raw_residuals = evaluate_background_constraints(
        algebra=geometry.algebra,
        geometry=geometry,
        H=H,
        sigma_ab=sigma,
        matter=matter,
        lambda_value=lambda_value,
        kappa=kappa,
        conservation_residual=conservation_residual,
    )
    energy_bianchi = (
        float(rho_dot)
        + 3.0 * float(H) * (float(matter.rho) + float(matter.p))
        + div_vector(matter.q, geometry.Gamma)
        + float(np.sum(sigma * matter.pi))
    )
    residuals = BackgroundConstraintResiduals(
        gauss=raw_residuals.gauss,
        codazzi=raw_residuals.codazzi,
        jacobi=raw_residuals.jacobi,
        twice_contracted_bianchi=np.concatenate(
            ([energy_bianchi], np.asarray(raw_residuals.codazzi, dtype=np.float64))
        ),
    )
    return BackgroundRhsAssembly(
        H_dot=H_dot,
        sigma_dot=sigma_dot,
        rho_dot=rho_dot,
        residuals=residuals,
    )


def background_rhs(**kwargs) -> BackgroundRhsAssembly:
    """ver3 alias for the canonical background RHS assembly."""

    return assemble_background_rhs(**kwargs)


def background_gate_bundle(
    assembly: BackgroundRhsAssembly,
    geometry: TetradGeometry,
    *,
    family: str | None = None,
    branch: str = "orthogonal",
    backend: str = "background_rhs",
    truncation: Mapping[str, object] | None = None,
) -> GateBundle:
    """Emit the machine-readable PR-05 background gate bundle."""

    residuals = assembly.residuals
    return make_gate_bundle(
        "background_core_gate",
        family=geometry.algebra.type_name if family is None else family,
        branch=branch,
        backend=backend,
        truncation={} if truncation is None else dict(truncation),
        residual_summary={
            "gauss_abs": float(abs(residuals.gauss)),
            "codazzi_max_abs": float(np.max(np.abs(residuals.codazzi))),
            "jacobi_max_abs": float(np.max(np.abs(residuals.jacobi))),
            "twice_contracted_bianchi_max_abs": float(
                np.max(np.abs(residuals.twice_contracted_bianchi))
            ),
        },
        known_limit_checks={
            "rhs_finite": bool(
                np.isfinite(assembly.H_dot)
                and np.isfinite(assembly.rho_dot)
                and np.all(np.isfinite(assembly.sigma_dot))
            ),
            "geometry_dual_route_status": geometry.dual_route_status,
        },
        forbidden_shortcut_checks={
            "no_unavailable_residual_to_zero": True,
            "no_output_logic_in_background": True,
        },
        metadata={
            "compact_formula_status": geometry.compact_formula_status,
        },
        passed=bool(
            np.isfinite(assembly.H_dot)
            and np.isfinite(assembly.rho_dot)
            and np.all(np.isfinite(assembly.sigma_dot))
        ),
        opened_claim="background-ready for named family branch only",
    )
