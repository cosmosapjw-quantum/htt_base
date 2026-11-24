"""VER2 initial-condition builders for the BASS S1 lane.

`IM-01S1` promotes the S1 contracts from report-only skeletons into the
constraint-satisfying implementation anchor for the VER2 background path.
The builders now perform explicit Codazzi projection, expose machine-readable
closure metadata, and fail controlledly when the chosen branch cannot satisfy
the momentum constraint.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal

import numpy as np

from bass.background.bianchi_types import (
    BianchiAlgebra,
    rescale_bianchi_algebra,
)
from bass.background.constraints import (
    BackgroundConstraintResiduals,
    MatterNormalFrameState,
    evaluate_background_constraints,
)
from bass.background.geometry import TetradGeometry, build_geometry, pstf_rank2
from bass.background.matter_projection import (
    SpeciesProjectedState,
    SpeciesRestFrameState,
    total_matter_projection,
)
from bass.background.rhs import assemble_background_rhs
from bass.tilt.species_tilt import (
    TiltedMatterState,
    TiltedSpeciesDecomposition,
    assemble_tilted_matter_state,
)

__all__ = [
    "CodazziProjectionError",
    "CodazziProjectionMetadata",
    "InitialConditionMetadata",
    "OrthogonalInitialConditions",
    "TiltedInitialConditions",
    "solve_expanding_H",
    "project_shear_to_codazzi",
    "project_tilted_codazzi",
    "project_trace_free_shear",
    "build_orthogonal_initial_conditions",
    "build_tilted_initial_conditions",
]


_CODAZZI_SVD_RCOND = 1.0e-6


class CodazziProjectionError(ValueError):
    """Raised when the requested branch cannot satisfy the Codazzi surface."""


@dataclass(frozen=True)
class CodazziProjectionMetadata:
    policy: str
    applied: bool
    rank: int
    residual_norm_before: float
    residual_norm_after: float
    target_q: np.ndarray

    def __post_init__(self) -> None:
        target_q = np.asarray(self.target_q, dtype=np.float64)
        if target_q.shape != (3,):
            raise ValueError(
                f"CodazziProjectionMetadata.target_q must have shape (3,), got {target_q.shape}"
            )
        object.__setattr__(self, "target_q", target_q)


@dataclass(frozen=True)
class InitialConditionMetadata:
    branch: Literal["orthogonal", "tilted"]
    constraint_policy_required: str
    codazzi_policy: str
    hamiltonian_closure: str
    jacobi_ok: bool
    gauss_admissible: bool
    codazzi_satisfied: bool
    algebra_scale_factor: float = 1.0
    shear_amplitude_scale: float = 1.0
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class OrthogonalInitialConditions:
    algebra: BianchiAlgebra
    geometry: TetradGeometry
    H: float
    sigma_ab: np.ndarray
    matter: MatterNormalFrameState
    residuals: BackgroundConstraintResiduals
    closure: str
    projection: CodazziProjectionMetadata
    metadata: InitialConditionMetadata


@dataclass(frozen=True)
class TiltedInitialConditions:
    algebra: BianchiAlgebra
    geometry: TetradGeometry
    H: float
    sigma_ab: np.ndarray
    matter: TiltedMatterState
    residuals: BackgroundConstraintResiduals
    closure: str
    projection: CodazziProjectionMetadata
    metadata: InitialConditionMetadata


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


def _sigma_to_basis_coefficients(sigma_ab: np.ndarray) -> np.ndarray:
    sigma = project_trace_free_shear(sigma_ab)
    return np.array(
        [float(np.sum(sigma * basis)) for basis in _ORTHONORMAL_PSTF_BASIS],
        dtype=np.float64,
    )


def _sigma_from_basis_coefficients(coeffs: np.ndarray) -> np.ndarray:
    sigma = np.zeros((3, 3), dtype=np.float64)
    for coeff, basis in zip(np.asarray(coeffs, dtype=np.float64), _ORTHONORMAL_PSTF_BASIS):
        sigma += float(coeff) * basis
    return project_trace_free_shear(sigma)


def _codazzi_operator_matrix(geometry: TetradGeometry) -> np.ndarray:
    return np.column_stack(
        [
            evaluate_background_constraints(
                algebra=geometry.algebra,
                geometry=geometry,
                H=1.0,
                sigma_ab=basis,
                matter=MatterNormalFrameState(rho=0.0, p=0.0),
                lambda_value=0.0,
            ).codazzi
            for basis in _ORTHONORMAL_PSTF_BASIS
        ]
    )


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
    radicand = (
        kappa * float(rho) + float(lambda_value) + sigma_sq - 0.5 * float(ricci_scalar)
    ) / 3.0
    if radicand < 0.0:
        raise ValueError(
            f"Expanding-branch Gauss solve requires a non-negative radicand; got {radicand!r}"
        )
    return math.sqrt(radicand)


def project_shear_to_codazzi(
    *,
    sigma_ab: np.ndarray,
    geometry: TetradGeometry,
    target_q: np.ndarray,
    kappa: float = 1.0,
    policy: str = "least_squares_project",
    atol: float = 1.0e-10,
    rtol: float = 1.0e-12,
) -> tuple[np.ndarray, CodazziProjectionMetadata]:
    """Find the nearest PSTF shear with `div σ = -κ target_q` for physical normal flux."""

    if policy not in {"least_squares_project", "solve_shear_offdiag"}:
        raise ValueError(f"Unsupported Codazzi policy {policy!r}")

    sigma0 = project_trace_free_shear(sigma_ab)
    q = np.asarray(target_q, dtype=np.float64)
    if q.shape != (3,):
        raise ValueError(f"target_q must have shape (3,), got {q.shape}")

    A = _codazzi_operator_matrix(geometry)
    x0 = _sigma_to_basis_coefficients(sigma0)
    target = -kappa * q
    before = A @ x0 - target
    # Preserve the old Gram pseudoinverse cutoff, 1e-12 in squared
    # singular values, while solving directly on the divergence operator.
    delta, _, rank, _ = np.linalg.lstsq(A, -before, rcond=_CODAZZI_SVD_RCOND)
    x_proj = x0 + delta
    sigma_proj = _sigma_from_basis_coefficients(x_proj)
    after = evaluate_background_constraints(
        algebra=geometry.algebra,
        geometry=geometry,
        H=1.0,
        sigma_ab=sigma_proj,
        matter=MatterNormalFrameState(
            rho=0.0,
            p=0.0,
            q=q,
        ),
        lambda_value=0.0,
        kappa=kappa,
    ).codazzi
    meta = CodazziProjectionMetadata(
        policy=policy,
        applied=bool(np.linalg.norm(delta) > 0.0),
        rank=int(rank),
        residual_norm_before=float(np.linalg.norm(before)),
        residual_norm_after=float(np.linalg.norm(after)),
        target_q=q,
    )
    effective_tol = max(
        float(atol),
        float(rtol) * max(float(np.linalg.norm(target)), 1.0),
    )
    if meta.residual_norm_after > effective_tol:
        raise CodazziProjectionError(
            f"Codazzi projection failed for {geometry.algebra.type_name}: "
            f"policy={policy}, residual={meta.residual_norm_after:.3e}, "
            f"tol={effective_tol:.3e}, "
            f"required={geometry.algebra.branch_policy.constraint_policy_required}"
        )
    return sigma_proj, meta


def project_tilted_codazzi(
    *,
    sigma_ab: np.ndarray,
    matter: TiltedMatterState,
    geometry: TetradGeometry,
    kappa: float = 1.0,
    policy: str = "least_squares_project",
    atol: float = 1.0e-10,
    rtol: float = 1.0e-12,
) -> tuple[np.ndarray, TiltedMatterState, CodazziProjectionMetadata]:
    sigma_proj, meta = project_shear_to_codazzi(
        sigma_ab=sigma_ab,
        geometry=geometry,
        target_q=matter.q,
        kappa=kappa,
        policy=policy,
        atol=atol,
        rtol=rtol,
    )
    return sigma_proj, matter, meta


def _nearest_curvature_scale(ricci: float, linear: float, forced_sq: float) -> float:
    """Positive u nearest one in log scale for R u^4 + B u² − ||x_parallel||² = 0."""
    if not all(math.isfinite(v) for v in (ricci, linear, forced_sq)) or forced_sq <= 0.0:
        raise ValueError("non-finite or unrepresentable curvature closure coefficients")
    # Normalize B and sqrt(|R| U) at their common scale before squaring.
    # Compute u directly from square-root ratios; u can be representable
    # even when y=u² or a ratio of the original coefficients overflows.
    forced_norm = math.sqrt(forced_sq)
    if ricci == 0.0:
        candidates = [forced_norm / math.sqrt(linear)] if linear > 0.0 else []
    else:
        sqrt_r = math.sqrt(abs(ricci))
        geometric_mean = sqrt_r * forced_norm
        scale = max(abs(linear), geometric_mean)
        b = linear / scale
        cross = 2.0 * (geometric_mean / scale)
        if ricci > 0.0:
            root_disc = math.hypot(b, cross)
        else:
            # Both roots have the same sign. The factorization retains
            # the splitting near a double root.
            gap = b - cross
            if b <= 0.0 or gap < -16.0 * np.finfo(float).eps * max(b, cross):
                raise ValueError("no positive curvature scale satisfies Gauss and Codazzi")
            root_disc = math.sqrt(max(0.0, gap)) * math.sqrt(b + cross)
        stable = -0.5 * (b + math.copysign(root_disc, linear))
        sqrt_stable = math.sqrt(abs(stable))
        sqrt_scale = math.sqrt(scale)
        candidates = []
        if (stable > 0.0) == (ricci > 0.0):
            candidates.append((sqrt_stable * sqrt_scale) / sqrt_r)
        if stable < 0.0:
            candidates.append(forced_norm / (sqrt_scale * sqrt_stable))
    scales = [u for u in candidates if math.isfinite(u) and u > 0.0]
    if not scales:
        raise ValueError("no finite positive curvature scale satisfies Gauss and Codazzi")
    if len(scales) == 1:
        return scales[0]
    # The two positive solutions straddle the fold u_*=(U/|R|)^(1/4),
    # their geometric mean. Choose the root on the side of u_* containing
    # u=1 (minimum |ln u|), taking the larger root on an exact tie.
    return min(scales) if forced_sq > abs(ricci) else max(scales)


def _joint_tilted_rescaling(
    *, H: float, matter: MatterNormalFrameState, sigma: np.ndarray,
    geometry: TetradGeometry, lambda_value: float, closure: str, kappa: float,
) -> tuple[float, BianchiAlgebra, TetradGeometry, np.ndarray, float, float]:
    x = _sigma_to_basis_coefficients(sigma)
    A = _codazzi_operator_matrix(geometry)
    left, singular, right = np.linalg.svd(A, full_matrices=True)
    rank = int(np.count_nonzero(singular > singular[0] * _CODAZZI_SVD_RCOND))
    if rank == 0:
        raise CodazziProjectionError("nonzero tilted momentum has zero divergence range")
    target = -kappa * matter.q
    forced = right[:rank].T @ ((left[:, :rank].T @ target) / singular[:rank])
    free = right[rank:].T @ (right[rank:] @ x)
    forced_sq = float(forced @ forced)
    free_sq = float(free @ free)
    # Twice the Gauss energy after subtracting matter and Lambda.
    expansion = 6.0 * H * H
    density = 2.0 * kappa * matter.rho
    vacuum = 2.0 * lambda_value
    twice_energy = math.fsum([expansion, -density, -vacuum])
    ricci = geometry.ricci_scalar
    u = 1.0
    algebra = geometry.algebra
    if closure == "project_shear_amplitude":
        # Only the kernel radius is free on this affine Codazzi surface.
        radius_sq = math.fsum([twice_energy, ricci, -forced_sq])
        roundoff = 32.0 * np.finfo(float).eps * max(
            abs(v) for v in (expansion, density, vacuum, ricci, forced_sq)
        )
        if radius_sq < -roundoff:
            raise ValueError("target shear norm is below the minimum required by tilted Codazzi")
        if abs(radius_sq) <= roundoff:
            result = forced
        else:
            free_norm = math.sqrt(free_sq)
            if free_norm <= 64.0 * np.finfo(float).eps * math.hypot(*x):
                raise ValueError("positive remaining shear norm requires an input Codazzi-null shear direction")
            result = forced + math.sqrt(radius_sq) * (free / free_norm)
    else:
        u = _nearest_curvature_scale(ricci, math.fsum([twice_energy, -free_sq]), forced_sq)
        result = forced / u + free
        algebra = rescale_bianchi_algebra(algebra, u)
        geometry = build_geometry(algebra)
    xnorm = math.hypot(*x)
    if xnorm == 0.0 or not np.all(np.isfinite(result)):
        raise ValueError("nonfinite or unrepresented constrained shear")
    return H, algebra, geometry, _sigma_from_basis_coefficients(result), u, math.hypot(*result) / xnorm


def _resolve_hamiltonian_closure(
    *,
    H: float | None,
    matter: MatterNormalFrameState,
    sigma_ab: np.ndarray,
    algebra: BianchiAlgebra,
    geometry: TetradGeometry,
    lambda_value: float,
    closure: Literal["solve_H", "hold_H", "solve_curvature_scale", "project_shear_amplitude"],
    kappa: float,
    atol: float = 1.0e-12,
) -> tuple[float, BianchiAlgebra, TetradGeometry, np.ndarray, float, float]:
    sigma = project_trace_free_shear(sigma_ab)
    if closure == "solve_H":
        H_value = solve_expanding_H(
            rho=matter.rho,
            sigma_ab=sigma,
            ricci_scalar=geometry.ricci_scalar,
            lambda_value=lambda_value,
            kappa=kappa,
        )
        return H_value, algebra, geometry, sigma, 1.0, 1.0
    if closure == "hold_H":
        if H is None:
            raise ValueError("closure='hold_H' requires an explicit H value")
        return float(H), algebra, geometry, sigma, 1.0, 1.0
    if closure in {"solve_curvature_scale", "project_shear_amplitude"} and np.any(kappa * matter.q):
        if H is None or not math.isfinite(H):
            raise ValueError(f"closure={closure!r} requires a finite explicit H value")
        return _joint_tilted_rescaling(H=float(H), matter=matter, sigma=sigma, geometry=geometry,
                                       lambda_value=lambda_value, closure=closure, kappa=kappa)
    if closure == "solve_curvature_scale":
        if H is None:
            raise ValueError("closure='solve_curvature_scale' requires an explicit H value")
        if abs(geometry.ricci_scalar) < atol:
            raise ValueError(
                "closure='solve_curvature_scale' requires a non-zero spatial Ricci scalar"
            )
        sigma_sq = 0.5 * float(np.sum(sigma * sigma))
        numerator = 2.0 * (
            kappa * float(matter.rho) + float(lambda_value) + sigma_sq - 3.0 * float(H) ** 2
        )
        scale_sq = numerator / float(geometry.ricci_scalar)
        if scale_sq < 0.0:
            raise ValueError(
                "closure='solve_curvature_scale' requires a non-negative algebra scale; "
                f"got {scale_sq!r}"
            )
        scale = math.sqrt(scale_sq)
        algebra_scaled = rescale_bianchi_algebra(algebra, scale)
        geometry_scaled = build_geometry(algebra_scaled)
        return float(H), algebra_scaled, geometry_scaled, sigma, scale, 1.0
    if closure == "project_shear_amplitude":
        if H is None:
            raise ValueError("closure='project_shear_amplitude' requires an explicit H value")
        sigma_sq = 0.5 * float(np.sum(sigma * sigma))
        target_sigma_sq = (
            3.0 * float(H) ** 2
            - kappa * float(matter.rho)
            - float(lambda_value)
            + 0.5 * float(geometry.ricci_scalar)
        )
        if target_sigma_sq < -atol:
            raise ValueError(
                "closure='project_shear_amplitude' requires a non-negative target shear norm; "
                f"got {target_sigma_sq!r}"
            )
        if sigma_sq <= atol:
            if abs(target_sigma_sq) <= atol:
                return float(H), algebra, geometry, sigma, 1.0, 1.0
            raise ValueError(
                "closure='project_shear_amplitude' needs a non-zero shear shape when the target "
                "shear norm is positive"
            )
        amplitude = math.sqrt(max(target_sigma_sq, 0.0) / sigma_sq)
        return float(H), algebra, geometry, sigma * amplitude, 1.0, amplitude
    raise ValueError(f"Unknown closure policy {closure!r}")


def build_orthogonal_initial_conditions(
    *,
    algebra: BianchiAlgebra,
    rho: float,
    p: float,
    sigma_ab: np.ndarray | None = None,
    lambda_value: float = 0.0,
    H: float | None = None,
    closure: Literal[
        "solve_H",
        "hold_H",
        "solve_curvature_scale",
        "project_shear_amplitude",
    ] = "solve_H",
    codazzi_policy: Literal["least_squares_project", "solve_shear_offdiag"] = "least_squares_project",
    kappa: float = 1.0,
) -> OrthogonalInitialConditions:
    """Build a constraint-satisfying orthogonal IC bundle."""

    geometry = build_geometry(algebra)
    sigma_guess = project_trace_free_shear(np.zeros((3, 3)) if sigma_ab is None else sigma_ab)
    matter = MatterNormalFrameState(rho=float(rho), p=float(p))
    sigma, projection = project_shear_to_codazzi(
        sigma_ab=sigma_guess,
        geometry=geometry,
        target_q=np.zeros(3, dtype=np.float64),
        kappa=kappa,
        policy=codazzi_policy,
    )
    H_value, algebra_eff, geometry_eff, sigma_eff, algebra_scale, shear_scale = _resolve_hamiltonian_closure(
        H=H,
        matter=matter,
        sigma_ab=sigma,
        algebra=algebra,
        geometry=geometry,
        lambda_value=lambda_value,
        closure=closure,
        kappa=kappa,
    )
    residuals = assemble_background_rhs(
        H=H_value,
        sigma_ab=sigma_eff,
        matter=matter,
        geometry=geometry_eff,
        lambda_value=lambda_value,
        kappa=kappa,
    ).residuals
    return OrthogonalInitialConditions(
        algebra=algebra_eff,
        geometry=geometry_eff,
        H=H_value,
        sigma_ab=sigma_eff,
        matter=matter,
        residuals=residuals,
        closure=closure,
        projection=projection,
        metadata=InitialConditionMetadata(
            branch="orthogonal",
            constraint_policy_required=algebra_eff.branch_policy.constraint_policy_required,
            codazzi_policy=codazzi_policy,
            hamiltonian_closure=closure,
            jacobi_ok=algebra_eff.jacobi_residual_norm < 1.0e-12,
            gauss_admissible=abs(residuals.gauss) < 1.0e-10,
            codazzi_satisfied=float(np.linalg.norm(residuals.codazzi)) < 1.0e-10,
            algebra_scale_factor=algebra_scale,
            shear_amplitude_scale=shear_scale,
        ),
    )


def build_tilted_initial_conditions(
    *,
    algebra: BianchiAlgebra,
    species: Iterable[TiltedSpeciesDecomposition],
    sigma_ab: np.ndarray | None = None,
    lambda_value: float = 0.0,
    H: float | None = None,
    closure: Literal[
        "solve_H",
        "hold_H",
        "solve_curvature_scale",
        "project_shear_amplitude",
    ] = "solve_H",
    codazzi_policy: Literal["least_squares_project", "solve_shear_offdiag"] = "least_squares_project",
    kappa: float = 1.0,
) -> TiltedInitialConditions:
    """Build a constraint-satisfying tilted IC bundle or fail controlledly."""

    geometry = build_geometry(algebra)
    sigma_guess = project_trace_free_shear(np.zeros((3, 3)) if sigma_ab is None else sigma_ab)
    species = tuple(species)
    matter = assemble_tilted_matter_state(species)
    projected_species = tuple(
        SpeciesProjectedState(
            label=piece.params.label,
            rho=piece.mu,
            p=piece.p,
            q=piece.q,
            pi=piece.pi,
            tilt_contravariant=np.asarray(piece.params.v, dtype=np.float64),
            tilt_covariant=np.asarray(piece.params.v, dtype=np.float64),
            gamma_lorentz=piece.params.gamma,
            rest_frame=SpeciesRestFrameState(
                rho_hat=float(piece.params.rho_hat),
                p_hat=float(piece.params.p_hat),
                label=piece.params.label,
            ),
        )
        for piece in species
    )
    normal_frame = total_matter_projection(projected_species)
    sigma, matter, projection = project_tilted_codazzi(
        sigma_ab=sigma_guess,
        matter=matter,
        geometry=geometry,
        kappa=kappa,
        policy=codazzi_policy,
    )
    H_value, algebra_eff, geometry_eff, sigma_eff, algebra_scale, shear_scale = _resolve_hamiltonian_closure(
        H=H,
        matter=normal_frame,
        sigma_ab=sigma,
        algebra=algebra,
        geometry=geometry,
        lambda_value=lambda_value,
        closure=closure,
        kappa=kappa,
    )
    residuals = assemble_background_rhs(
        H=H_value,
        sigma_ab=sigma_eff,
        matter=normal_frame,
        geometry=geometry_eff,
        lambda_value=lambda_value,
        kappa=kappa,
    ).residuals
    gauss_ok = abs(residuals.gauss) < 1.0e-10
    codazzi_ok = float(np.linalg.norm(residuals.codazzi)) < 1.0e-10
    notes = ()
    if closure in {"solve_curvature_scale", "project_shear_amplitude"} and np.any(kappa * normal_frame.q):
        # Verify the actual rescaled connection and reconstructed tensor. Near
        # a singular structure map the divergence contraction may cancel.
        eps = np.finfo(float).eps
        shear_norm = math.hypot(*sigma_eff.flat)
        gauss_scale = max(3.0 * H_value**2, abs(kappa * normal_frame.rho), abs(lambda_value),
                          0.5 * shear_norm**2, 0.5 * abs(geometry_eff.ricci_scalar))
        flux_norm = math.hypot(*(kappa * normal_frame.q))
        contraction_scale = math.hypot(*geometry_eff.Gamma.flat) * shear_norm
        gauss_ok = math.isfinite(residuals.gauss) and abs(residuals.gauss) <= 256.0 * eps * gauss_scale
        codazzi_ok = math.hypot(*residuals.codazzi) <= 1e-10 * flux_norm + 256.0 * eps * contraction_scale
        if not (gauss_ok and codazzi_ok):
            raise CodazziProjectionError(f"joint {closure} failed: Gauss={residuals.gauss:.3e}, "
                                         f"Codazzi={np.linalg.norm(residuals.codazzi):.3e}")
        notes = ("shear_amplitude_scale is the final/initial projected Frobenius norm ratio",
                 "fixed Codazzi forcing; shear kernel radius adjusted" if closure == "project_shear_amplitude"
                 else "Codazzi row-space shear inversely scaled; kernel component preserved")
    return TiltedInitialConditions(
        algebra=algebra_eff,
        geometry=geometry_eff,
        H=H_value,
        sigma_ab=sigma_eff,
        matter=matter,
        residuals=residuals,
        closure=closure,
        projection=projection,
        metadata=InitialConditionMetadata(
            branch="tilted",
            constraint_policy_required=algebra_eff.branch_policy.constraint_policy_required,
            codazzi_policy=codazzi_policy,
            hamiltonian_closure=closure,
            jacobi_ok=algebra_eff.jacobi_residual_norm < 1.0e-12,
            gauss_admissible=gauss_ok,
            codazzi_satisfied=codazzi_ok,
            algebra_scale_factor=algebra_scale,
            shear_amplitude_scale=shear_scale,
            notes=notes,
        ),
    )
