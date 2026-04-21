"""VER2 background evolution path built from the canonical S1 operators."""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.integrate import solve_ivp

from bass.background.constraints import (
    BackgroundConstraintResiduals,
    MatterNormalFrameState,
)
from bass.background.geometry import pstf_rank2
from bass.background.initial_conditions import (
    OrthogonalInitialConditions,
    TiltedInitialConditions,
)
from bass.background.rhs import assemble_background_rhs
from bass.background.weyl import build_weyl_diagnostics
from bass.species.barotropic_closures import (
    OrthogonalBarotropicClosure,
    OrthogonalSpeciesRegistryClosure,
    TiltedBarotropicClosure,
    TiltedSpeciesRegistryClosure,
)

__all__ = [
    "BackgroundEvolutionConfig",
    "BackgroundEvolutionResult",
    "BackgroundResidualSummary",
    "summarize_background_residuals",
    "solve_background_evolution",
]


C_KMS = 299792.458


_ORTHONORMAL_PSTF_BASIS = (
    np.diag([1.0, -1.0, 0.0]) / np.sqrt(2.0),
    np.diag([1.0, 1.0, -2.0]) / np.sqrt(6.0),
    np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float64)
    / np.sqrt(2.0),
    np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float64)
    / np.sqrt(2.0),
    np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    / np.sqrt(2.0),
)


def _sigma_to_coeffs(sigma_ab: np.ndarray) -> np.ndarray:
    sigma = pstf_rank2(sigma_ab)
    return np.array(
        [float(np.sum(sigma * basis)) for basis in _ORTHONORMAL_PSTF_BASIS],
        dtype=np.float64,
    )


def _sigma_from_coeffs(coeffs: np.ndarray) -> np.ndarray:
    sigma = np.zeros((3, 3), dtype=np.float64)
    for coeff, basis in zip(np.asarray(coeffs, dtype=np.float64), _ORTHONORMAL_PSTF_BASIS):
        sigma += float(coeff) * basis
    return pstf_rank2(sigma)


@dataclass(frozen=True)
class BackgroundEvolutionConfig:
    a_start: float = 1.0e-3
    a_end: float = 1.0
    n_steps: int = 256
    rtol: float = 1.0e-8
    atol: float = 1.0e-10
    solver_method: str = "DOP853"
    lambda_value: float = 0.0
    kappa: float = 1.0
    matter_model_override: (
        OrthogonalBarotropicClosure
        | TiltedBarotropicClosure
        | OrthogonalSpeciesRegistryClosure
        | TiltedSpeciesRegistryClosure
        | None
    ) = None
    eta_at_scale_factor: Callable[[float], float] | None = None


@dataclass(frozen=True)
class BackgroundEvolutionResult:
    branch: Literal["orthogonal", "tilted"]
    eta: np.ndarray
    N: np.ndarray
    a: np.ndarray
    H: np.ndarray
    sigma_tensor: np.ndarray
    rho: np.ndarray
    p: np.ndarray
    q: np.ndarray
    pi: np.ndarray
    residuals: tuple[BackgroundConstraintResiduals, ...]
    electric_weyl: np.ndarray
    magnetic_weyl: np.ndarray
    initial_conditions: OrthogonalInitialConditions | TiltedInitialConditions
    matter_model_tag: str


@dataclass(frozen=True)
class BackgroundResidualSummary:
    samples: int
    H_reference: float
    structure_reference: float
    gauss_max_abs: float
    gauss_max_over_H2_ref: float
    codazzi_max_norm: float
    codazzi_max_over_H2_ref: float
    jacobi_max_norm: float
    jacobi_max_over_structure_ref: float
    bianchi_max_norm: float
    bianchi_max_over_H2_ref: float


def summarize_background_residuals(
    result: BackgroundEvolutionResult,
) -> BackgroundResidualSummary:
    """Return a machine-readable normalized residual bundle for ver3 PR-05."""

    H_ref = max(float(np.max(np.abs(result.H))), 1.0e-30)
    H2_ref = H_ref * H_ref
    structure_ref = max(
        float(np.linalg.norm(result.initial_conditions.algebra.C)),
        1.0e-30,
    )
    gauss_max_abs = max(abs(res.gauss) for res in result.residuals)
    codazzi_max_norm = max(float(np.linalg.norm(res.codazzi)) for res in result.residuals)
    jacobi_max_norm = max(float(np.linalg.norm(res.jacobi)) for res in result.residuals)
    bianchi_max_norm = max(
        float(np.linalg.norm(res.twice_contracted_bianchi)) for res in result.residuals
    )
    return BackgroundResidualSummary(
        samples=len(result.residuals),
        H_reference=H_ref,
        structure_reference=structure_ref,
        gauss_max_abs=gauss_max_abs,
        gauss_max_over_H2_ref=gauss_max_abs / H2_ref,
        codazzi_max_norm=codazzi_max_norm,
        codazzi_max_over_H2_ref=codazzi_max_norm / H2_ref,
        jacobi_max_norm=jacobi_max_norm,
        jacobi_max_over_structure_ref=jacobi_max_norm / structure_ref,
        bianchi_max_norm=bianchi_max_norm,
        bianchi_max_over_H2_ref=bianchi_max_norm / H2_ref,
    )


def solve_background_evolution(
    initial_conditions: OrthogonalInitialConditions | TiltedInitialConditions,
    *,
    config: BackgroundEvolutionConfig | None = None,
) -> BackgroundEvolutionResult:
    """Integrate the VER2 S1 background using the canonical PSTF RHS."""

    cfg = BackgroundEvolutionConfig() if config is None else config
    if cfg.a_start <= 0.0 or cfg.a_end <= cfg.a_start:
        raise ValueError(
            f"Require 0 < a_start < a_end, got a_start={cfg.a_start!r}, a_end={cfg.a_end!r}"
        )

    branch = initial_conditions.metadata.branch
    if cfg.matter_model_override is not None:
        matter_model = cfg.matter_model_override
        if branch == "orthogonal":
            matter_model_tag = "orthogonal_species_registry_mixture"
        else:
            matter_model_tag = "tilted_species_registry_mixture"
    elif branch == "orthogonal":
        matter_model = OrthogonalBarotropicClosure.from_state(
            initial_conditions.matter,
            a_ref=cfg.a_start,
        )
        matter_model_tag = "orthogonal_barotropic"
    else:
        matter_model = TiltedBarotropicClosure.from_state(
            initial_conditions.matter,
            a_ref=cfg.a_start,
        )
        matter_model_tag = "tilted_barotropic_fixed_velocity"

    y0 = np.concatenate(
        ([float(initial_conditions.H)], _sigma_to_coeffs(initial_conditions.sigma_ab))
    )
    N_grid = np.linspace(math.log(cfg.a_start), math.log(cfg.a_end), cfg.n_steps)

    def rhs(N_val: float, y: np.ndarray) -> np.ndarray:
        a_val = float(np.exp(N_val))
        H_val = max(float(y[0]), 1.0e-30)
        sigma = _sigma_from_coeffs(y[1:])
        matter_state = matter_model.state_at_scale_factor(a_val)
        if isinstance(matter_state, MatterNormalFrameState):
            normal_frame = matter_state
        else:
            normal_frame = MatterNormalFrameState(
                rho=matter_state.rho,
                p=matter_state.p,
                q=matter_state.q,
                pi=matter_state.pi,
            )
        assembly = assemble_background_rhs(
            H=H_val,
            sigma_ab=sigma,
            matter=normal_frame,
            geometry=initial_conditions.geometry,
            lambda_value=cfg.lambda_value,
            kappa=cfg.kappa,
        )
        dH_dN = assembly.H_dot / H_val
        dsigma_dN = _sigma_to_coeffs(assembly.sigma_dot) / H_val
        return np.concatenate(([dH_dN], dsigma_dN))

    sol = solve_ivp(
        rhs,
        (N_grid[0], N_grid[-1]),
        y0,
        method=cfg.solver_method,
        t_eval=N_grid,
        rtol=cfg.rtol,
        atol=cfg.atol,
    )
    if not sol.success:
        raise RuntimeError(f"Background evolution failed: {sol.message}")

    a = np.exp(sol.t)
    H = np.asarray(sol.y[0], dtype=np.float64)
    sigma_history = np.stack(
        [_sigma_from_coeffs(sol.y[1:, i]) for i in range(sol.y.shape[1])],
        axis=0,
    )

    rho = np.zeros_like(H)
    p = np.zeros_like(H)
    q = np.zeros((H.size, 3), dtype=np.float64)
    pi = np.zeros((H.size, 3, 3), dtype=np.float64)
    residuals: list[BackgroundConstraintResiduals] = []
    electric = np.zeros((H.size, 3, 3), dtype=np.float64)
    magnetic = np.zeros((H.size, 3, 3), dtype=np.float64)

    for i, (a_i, H_i, sigma_i) in enumerate(zip(a, H, sigma_history)):
        matter_state = matter_model.state_at_scale_factor(float(a_i))
        if isinstance(matter_state, MatterNormalFrameState):
            normal_frame = matter_state
            rho[i] = matter_state.rho
            p[i] = matter_state.p
            q[i] = matter_state.q
            pi[i] = matter_state.pi
        else:
            normal_frame = MatterNormalFrameState(
                rho=matter_state.rho,
                p=matter_state.p,
                q=matter_state.q,
                pi=matter_state.pi,
            )
            rho[i] = matter_state.rho
            p[i] = matter_state.p
            q[i] = matter_state.q
            pi[i] = matter_state.pi
        assembly = assemble_background_rhs(
            H=float(H_i),
            sigma_ab=sigma_i,
            matter=normal_frame,
            geometry=initial_conditions.geometry,
            lambda_value=cfg.lambda_value,
            kappa=cfg.kappa,
        )
        residuals.append(assembly.residuals)
        weyl = build_weyl_diagnostics(
            sigma_ab=sigma_i,
            sigma_dot_ab=assembly.sigma_dot,
            H=float(H_i),
            geometry=initial_conditions.geometry,
            residuals=assembly.residuals,
            pi_ab=normal_frame.pi,
            kappa=cfg.kappa,
        )
        electric[i] = weyl.electric
        magnetic[i] = weyl.magnetic

    if cfg.eta_at_scale_factor is None:
        eta = np.zeros_like(H)
        integrand = C_KMS / np.maximum(a * H, 1.0e-30)
        dN = np.diff(sol.t)
        for i in range(1, eta.size):
            eta[i] = eta[i - 1] + 0.5 * (integrand[i - 1] + integrand[i]) * dN[i - 1]
    else:
        eta = np.array(
            [float(cfg.eta_at_scale_factor(float(a_i))) for a_i in a],
            dtype=np.float64,
        )

    return BackgroundEvolutionResult(
        branch=branch,
        eta=eta,
        N=np.asarray(sol.t, dtype=np.float64),
        a=a,
        H=H,
        sigma_tensor=sigma_history,
        rho=rho,
        p=p,
        q=q,
        pi=pi,
        residuals=tuple(residuals),
        electric_weyl=electric,
        magnetic_weyl=magnetic,
        initial_conditions=initial_conditions,
        matter_model_tag=matter_model_tag,
    )
