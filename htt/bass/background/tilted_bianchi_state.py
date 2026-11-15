"""R49 general multi-congruence vector-tilted Bianchi state, kinematics, and constraints.

Implements `GBI-02`:
- Metric signature `(-, +, +, +)` with unit hypersurface normal `n^a` (`n_a n^a = -1`),
  distinct tilted fluid congruences `u_s^a = gamma_s (n^a + v_s^a)` (`s` in
  `baryon`, `cdm`, `photon`, `neutrino`, `lambda`, `effective_total`), distinct
  radiation rest frame, and distinct observer frame.
- 3-vector species tilt `v_s in R^3` (`|v_s| < 1`), never collapsed to scalar speed.
- Dual-verified 4D stress-energy projection (`Lambda(v) @ T_rest @ Lambda(v)^T`)
  matching closed-form King-Ellis `(epsilon, p, q^alpha, pi^{alpha beta})`.
- Exact 4D synchronous Bianchi tetrad connection `Gamma4` for nonlinear species
  congruence kinematics `(Theta_s, sigma_s, omega_s, a_s)`.
- Exact special-relativistic boost composition and Wigner rotation on 3-vectors,
  STF-5 tensors, and spin-2 Stokes polarization `(Q, U)` via
  `common.relativistic_velocity_closure`.
- `FamilyAdmissibilityRegistry` and fail-closed `construct_admissible_tilted_state`
  across `FLRW` and all 11 Bianchi types, explicitly rejecting uncompensated single
  perfect-fluid (`eps + p > 0`, `v != 0`) Bianchi-I or Bianchi-IX tilt with
  `CodazziProjectionError`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from bass.background.bianchi_types import (
    ALL_BIANCHI_TYPES,
    BianchiAlgebra,
    TYPES_WITH_FLRW_LIMIT,
    build_bianchi_algebra,
    get_type,
)
from bass.background.constraints import (
    BackgroundConstraintResiduals,
    MatterNormalFrameState,
    evaluate_background_constraints,
)
from bass.background.convention_bridge import (
    ALL_TWELVE_FAMILIES,
    StructureTriple,
    action_equivalence_for_family,
    algebra_to_triple,
    exact_momentum_divergence,
    exact_spatial_ricci_from_compact,
    structure_constants_to_triple,
)
from bass.background.geometry import (
    TetradGeometry,
    build_geometry,
    connection_from_commutators,
    pstf_rank2,
    spatial_ricci_from_connection,
)
from bass.background.initial_conditions import CodazziProjectionError
from bass.background.matter_projection import (
    SpeciesProjectedState,
    SpeciesRestFrameState,
    project_species_to_normal_frame,
    total_matter_projection,
)
from common.kinematic_response import BetaTruncationError, KinematicsError
from common.relativistic_kinematics import lorentz_boost
from common.relativistic_velocity_closure import (
    VelocityClosureResult,
    compose_and_close_velocities,
)
from common.stf_metric_bridge import (
    G_STF5,
    G_STF5_INV,
    stf_matrix_to_orthonormal,
    orthonormal_to_stf_matrix,
)

__all__ = [
    "CONGRUENCE_SPECIES_NAMES",
    "FamilyAdmissibilitySpec",
    "FAMILY_ADMISSIBILITY_REGISTRY",
    "SpeciesFluidCongruence",
    "SpeciesCongruenceKinematics",
    "StressTensor4DOracleResult",
    "FrameTransportBundle",
    "TiltedConstraintReport",
    "TiltedBianchiState",
    "project_stress_tensor_4d_oracle",
    "build_4d_bianchi_connection",
    "compute_species_congruence_kinematics",
    "wigner_rotate_stf5_on",
    "aberrate_direction_and_stokes",
    "aberrate_directions_and_stokes_batch",
    "build_frame_transport_bundle",
    "evaluate_tilted_constraints",
    "solve_compensating_tilt_velocity",
    "construct_admissible_tilted_state",
]

CONGRUENCE_SPECIES_NAMES: tuple[str, ...] = (
    "baryon",
    "cdm",
    "photon",
    "neutrino",
    "lambda",
    "effective_total",
)

_ETA4: np.ndarray = np.diag([-1.0, 1.0, 1.0, 1.0])


@dataclass(frozen=True)
class FamilyAdmissibilitySpec:
    """Constraint fibre specification for one Bianchi/FLRW family."""

    family: str
    class_label: Literal["A", "B"]
    has_flrw_limit: bool
    equivalence_id: str
    divergence_rank_on_stf5: int
    allows_uncompensated_single_perfect_fluid_tilt: bool
    class_a_curl_coupling: bool
    class_b_a_sigma_coupling: bool
    supports_general_vector_tilt: bool
    summary: str


def _build_family_admissibility_registry() -> dict[str, FamilyAdmissibilitySpec]:
    specs: dict[str, FamilyAdmissibilitySpec] = {}
    for fam in ALL_TWELVE_FAMILIES:
        sc = get_type("I") if fam == "FLRW" else get_type(fam)
        eq = action_equivalence_for_family(fam)
        class_lbl: Literal["A", "B"] = "B" if abs(sc.a_twist) > 0.0 else "A"
        # Compute exact numerical rank of sigma -> D_j sigma^j_i map on 5D STF space
        alg = build_bianchi_algebra("I" if fam == "FLRW" else fam)
        basis_cols = []
        for idx in range(5):
            e_vec = np.zeros(5, dtype=np.float64)
            e_vec[idx] = 1.0
            S = orthonormal_to_stf_matrix(e_vec, convention="kinematic_response")
            basis_cols.append(exact_momentum_divergence(S, alg.a, alg.n, a_sign=1))
        M_div = np.column_stack(basis_cols)
        rank = int(np.linalg.matrix_rank(M_div, tol=1.0e-12))
        uncomp_single_allowed = rank > 0
        if fam in ("FLRW", "I"):
            summary = (
                "D_j sigma^j_i == 0 identically (rank 0); single perfect fluid (eps+p>0) "
                "must have v == 0; multi-fluid tilt requires vector sum_s q_s == 0."
            )
        elif fam == "IX":
            summary = (
                "n proportional to I => D_j sigma^j_i == 0 (rank 0) on diagonalized S^3; "
                "uncompensated single perfect-fluid tilt forbidden by Codazzi (requires sum_s q_s == 0)."
            )
        elif class_lbl == "A":
            summary = (
                f"Class A rank-{rank} Codazzi fibre eps_ijk n_jl sigma_lk == kappa q_i; "
                "non-zero off-diagonal shear sources/requires transverse total momentum."
            )
        else:
            summary = (
                f"Class B rank-{rank} Codazzi fibre -(eps_ijk sigma_jl n_lk + 3 a_j sigma_ji) == kappa q_i; "
                "non-zero a @ sigma forces non-zero total momentum flux along a or transverse plane."
            )
        specs[fam] = FamilyAdmissibilitySpec(
            family=fam,
            class_label=class_lbl,
            has_flrw_limit=(fam in TYPES_WITH_FLRW_LIMIT or fam == "FLRW"),
            equivalence_id=eq.equivalence_id,
            divergence_rank_on_stf5=rank,
            allows_uncompensated_single_perfect_fluid_tilt=uncomp_single_allowed,
            class_a_curl_coupling=(rank > 0 and np.linalg.norm(alg.n - (np.trace(alg.n) / 3.0) * np.eye(3)) > 1.0e-12),
            class_b_a_sigma_coupling=(class_lbl == "B"),
            supports_general_vector_tilt=True,
            summary=summary,
        )
    return specs


FAMILY_ADMISSIBILITY_REGISTRY: dict[str, FamilyAdmissibilitySpec] = (
    _build_family_admissibility_registry()
)


@dataclass(frozen=True)
class SpeciesFluidCongruence:
    """Typed relativistic fluid congruence state relative to slice normal `n^a`."""

    species: str
    eps_hat: float
    p_hat: float
    v_vec: np.ndarray
    v_dot: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    q_hat: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    pi_hat: np.ndarray = field(default_factory=lambda: np.zeros((3, 3), dtype=np.float64))

    def __post_init__(self) -> None:
        if not self.species:
            raise ValueError("species label must be non-empty")
        v = np.asarray(self.v_vec, dtype=np.float64)
        vd = np.asarray(self.v_dot, dtype=np.float64)
        qh = np.asarray(self.q_hat, dtype=np.float64)
        ph = pstf_rank2(np.asarray(self.pi_hat, dtype=np.float64))
        if v.shape != (3,) or vd.shape != (3,) or qh.shape != (3,) or ph.shape != (3, 3):
            raise ValueError("Invalid vector/tensor shapes in SpeciesFluidCongruence")
        if not (np.all(np.isfinite(v)) and np.all(np.isfinite(vd)) and math.isfinite(self.eps_hat) and math.isfinite(self.p_hat)):
            raise ValueError("Non-finite physical inputs in SpeciesFluidCongruence")
        v_sq = float(v @ v)
        if v_sq >= 1.0:
            raise BetaTruncationError(f"[{self.species}] |v| >= 1 ({math.sqrt(v_sq):.6f}) violates subluminality")
        # Vacuum energy has Lorentz-invariant T_ab = -rho g_ab
        if self.species == "lambda" and abs(self.eps_hat + self.p_hat) < 1.0e-12:
            v = np.zeros(3, dtype=np.float64)
            vd = np.zeros(3, dtype=np.float64)
        object.__setattr__(self, "eps_hat", float(self.eps_hat))
        object.__setattr__(self, "p_hat", float(self.p_hat))
        object.__setattr__(self, "v_vec", v)
        object.__setattr__(self, "v_dot", vd)
        object.__setattr__(self, "q_hat", qh)
        object.__setattr__(self, "pi_hat", ph)

    @property
    def enthalpy_hat(self) -> float:
        return self.eps_hat + self.p_hat

    @property
    def speed(self) -> float:
        return float(np.linalg.norm(self.v_vec))

    @property
    def gamma(self) -> float:
        return 1.0 / math.sqrt(1.0 - float(self.v_vec @ self.v_vec))

    @property
    def u_four_velocity(self) -> np.ndarray:
        g = self.gamma
        return np.array([g, g * self.v_vec[0], g * self.v_vec[1], g * self.v_vec[2]], dtype=np.float64)

    def to_projected_state(self) -> SpeciesProjectedState:
        """Project species to normal frame reusing `matter_projection` SSOT plus anisotropic `(q_hat, pi_hat)` if any."""
        base_proj = project_species_to_normal_frame(
            SpeciesRestFrameState(rho_hat=self.eps_hat, p_hat=self.p_hat, label=self.species),
            self.v_vec,
        )
        if np.linalg.norm(self.q_hat) == 0.0 and np.linalg.norm(self.pi_hat) == 0.0:
            return base_proj
        oracle = project_stress_tensor_4d_oracle(
            self.eps_hat, self.p_hat, self.v_vec, q_hat=self.q_hat, pi_hat=self.pi_hat
        )
        return SpeciesProjectedState(
            label=self.species,
            rho=oracle.eps_normal,
            p=oracle.p_normal,
            q=oracle.q_normal,
            pi=oracle.pi_normal,
            tilt_contravariant=self.v_vec.copy(),
            tilt_covariant=self.v_vec.copy(),
            gamma_lorentz=self.gamma,
            rest_frame=base_proj.rest_frame,
        )


@dataclass(frozen=True)
class StressTensor4DOracleResult:
    """Comparison of 4D Lorentz-boosted `T^{ab}` against closed-form King-Ellis formulas."""

    T_rest_4d: np.ndarray
    T_normal_4d: np.ndarray
    eps_normal: float
    p_normal: float
    q_normal: np.ndarray
    pi_normal: np.ndarray
    analytic_vs_4d_max_abs_error: float


def project_stress_tensor_4d_oracle(
    eps_hat: float,
    p_hat: float,
    v_vec: Sequence[float] | np.ndarray,
    *,
    q_hat: Sequence[float] | np.ndarray | None = None,
    pi_hat: np.ndarray | None = None,
) -> StressTensor4DOracleResult:
    """Compute normal-frame stress tensor via exact 4D Lorentz matrix and verify King-Ellis formulas."""
    v = np.asarray(v_vec, dtype=np.float64)
    v_sq = float(v @ v)
    if v_sq >= 1.0:
        raise BetaTruncationError(f"|v| >= 1 in 4D oracle: {v_sq}")

    T_rest = np.zeros((4, 4), dtype=np.float64)
    T_rest[0, 0] = float(eps_hat)
    T_rest[1:, 1:] = float(p_hat) * np.eye(3, dtype=np.float64)
    qh = np.zeros(3, dtype=np.float64) if q_hat is None else np.asarray(q_hat, dtype=np.float64)
    ph = np.zeros((3, 3), dtype=np.float64) if pi_hat is None else pstf_rank2(np.asarray(pi_hat, dtype=np.float64))
    T_rest[0, 1:] = qh
    T_rest[1:, 0] = qh
    T_rest[1:, 1:] += ph

    Lambda = lorentz_boost(v)
    T_norm = Lambda @ T_rest @ Lambda.T

    eps_n = float(T_norm[0, 0])
    q_n = T_norm[0, 1:].copy()
    S_spatial = T_norm[1:, 1:]
    p_n = float(np.trace(S_spatial) / 3.0)
    pi_n = pstf_rank2(S_spatial)

    if np.linalg.norm(qh) == 0.0 and np.linalg.norm(ph) == 0.0:
        gamma_sq = 1.0 / (1.0 - v_sq)
        w = float(eps_hat + p_hat)
        eps_ana = gamma_sq * w - float(p_hat)
        p_ana = float(p_hat) + (1.0 / 3.0) * gamma_sq * v_sq * w
        q_ana = gamma_sq * w * v
        pi_ana = gamma_sq * w * pstf_rank2(np.outer(v, v))
        err = max(
            abs(eps_n - eps_ana),
            abs(p_n - p_ana),
            float(np.max(np.abs(q_n - q_ana))),
            float(np.max(np.abs(pi_n - pi_ana))),
        )
    else:
        # Symmetrized T_norm consistency check
        err = float(np.max(np.abs(T_norm - T_norm.T)))

    return StressTensor4DOracleResult(
        T_rest_4d=T_rest,
        T_normal_4d=T_norm,
        eps_normal=eps_n,
        p_normal=p_n,
        q_normal=q_n,
        pi_normal=pi_n,
        analytic_vs_4d_max_abs_error=err,
    )


@dataclass(frozen=True)
class SpeciesCongruenceKinematics:
    """Nonlinear 4D kinematic decomposition `(Theta, sigma, omega, a)` of a tilted congruence `u^a`."""

    species: str
    theta_tilde: float
    sigma_tilde_4d: np.ndarray
    omega_tilde_4d: np.ndarray
    omega_vec_3d: np.ndarray
    vorticity_norm: float
    acceleration_tilde_4d: np.ndarray
    expansion_scalar_diff_from_3H: float
    u_orthogonality_max_err: float


def build_4d_bianchi_connection(
    H: float,
    sigma_ab: np.ndarray,
    C_spatial: np.ndarray,
) -> np.ndarray:
    """Build exact torsion-free metric-compatible 4D connection `Gamma4[d, b, a]` on synchronous tetrad.

    Satisfies `(nabla_{e_a} e_b)^d = Gamma4[d, b, a]` with Fermi-Walker spatial triad
    `nabla_{e_0} e_i = 0`, `[e_0, e_i] = -(H delta_ij + sigma_ij) e_j`, and `[e_i, e_j] = C^k_{ij} e_k`.
    """
    theta = float(H) * np.eye(3, dtype=np.float64) + pstf_rank2(np.asarray(sigma_ab, dtype=np.float64))
    C4 = np.zeros((4, 4, 4), dtype=np.float64)
    C4[1:, 1:, 1:] = np.asarray(C_spatial, dtype=np.float64)
    C4[1:, 0, 1:] = -theta
    C4[1:, 1:, 0] = +theta
    C_low = np.einsum("cd,dab->cab", _ETA4, C4)
    Gamma4 = np.zeros((4, 4, 4), dtype=np.float64)
    for a in range(4):
        for b in range(4):
            for c in range(4):
                val = 0.5 * (C_low[c, a, b] - C_low[a, b, c] + C_low[b, c, a])
                Gamma4[c, b, a] = _ETA4[c, c] * val
    return Gamma4


def compute_species_congruence_kinematics(
    congruence: SpeciesFluidCongruence,
    *,
    H: float,
    sigma_ab: np.ndarray,
    C_spatial: np.ndarray,
) -> SpeciesCongruenceKinematics:
    """Compute full 4D `(Theta_tilde, sigma_tilde, omega_tilde, a_tilde)` for `u^a = gamma (n^a + v^a)`."""
    Gamma4 = build_4d_bianchi_connection(H, sigma_ab, C_spatial)
    v = congruence.v_vec
    vd = congruence.v_dot
    g = congruence.gamma
    u_up = np.array([g, g * v[0], g * v[1], g * v[2]], dtype=np.float64)
    u_low = _ETA4 @ u_up

    g_dot = (g ** 3) * float(v @ vd)
    du_low_dt = np.array(
        [-g_dot, g_dot * v[0] + g * vd[0], g_dot * v[1] + g * vd[1], g_dot * v[2] + g * vd[2]],
        dtype=np.float64,
    )
    partial_u_low = np.zeros((4, 4), dtype=np.float64)
    partial_u_low[0, :] = du_low_dt

    # nabla_a u_b = e_a(u_b) - Gamma^c_{ba} u_c
    grad_u = partial_u_low - np.einsum("cba,c->ab", Gamma4, u_low)
    h_u = _ETA4 + np.outer(u_low, u_low)  # covariant projector h^{(u)}_{ab}
    # Mixed projector h^c_a = eta^{cd} h_{da}
    h_mix = _ETA4 @ h_u

    accel_4 = np.einsum("a,ab->b", u_up, grad_u)
    proj_grad = h_mix.T @ grad_u @ h_mix  # h_a^c h_b^d nabla_c u_d
    sym_grad = 0.5 * (proj_grad + proj_grad.T)
    omega_4 = 0.5 * (proj_grad - proj_grad.T)
    theta_tilde = float(np.sum(_ETA4 * proj_grad))  # eta^{ab} proj_grad_{ab}
    sigma_tilde = sym_grad - (theta_tilde / 3.0) * h_u

    # Dual spatial vorticity pseudovector omega_k = 1/2 eps_{kij} omega_{ij}
    omega_vec = 0.5 * np.array(
        [
            omega_4[1 + 1, 1 + 2] - omega_4[1 + 2, 1 + 1],
            omega_4[1 + 2, 1 + 0] - omega_4[1 + 0, 1 + 2],
            omega_4[1 + 0, 1 + 1] - omega_4[1 + 1, 1 + 0],
        ],
        dtype=np.float64,
    )
    # Use Levi-Civita index order omega^i = -1/2 eps^{ijk} omega_{jk} -> magnitude invariant
    u_ortho_err = max(
        abs(float(u_up @ accel_4)),
        float(np.max(np.abs(u_up @ omega_4))),
        float(np.max(np.abs(u_up @ sigma_tilde))),
        abs(float(np.sum(_ETA4 * sigma_tilde))),
    )
    vort_norm = math.sqrt(max(0.5 * float(np.sum((_ETA4 @ omega_4 @ _ETA4) * omega_4)), 0.0))

    return SpeciesCongruenceKinematics(
        species=congruence.species,
        theta_tilde=theta_tilde,
        sigma_tilde_4d=sigma_tilde,
        omega_tilde_4d=omega_4,
        omega_vec_3d=omega_vec,
        vorticity_norm=vort_norm,
        acceleration_tilde_4d=accel_4,
        expansion_scalar_diff_from_3H=theta_tilde - 3.0 * float(H),
        u_orthogonality_max_err=u_ortho_err,
    )


def wigner_rotate_stf5_on(
    stf5_on: np.ndarray,
    R_w: np.ndarray,
    *,
    convention: Literal["kinematic_response", "explicit_szz", "astrophysical"] = "kinematic_response",
) -> np.ndarray:
    """Apply `SO(3)` Wigner rotation `R_W` exactly to a Frobenius-orthonormal STF-5 vector."""
    S = orthonormal_to_stf_matrix(np.asarray(stf5_on, dtype=np.float64), convention=convention)
    R = np.asarray(R_w, dtype=np.float64)
    S_rot = R @ S @ R.T
    return stf_matrix_to_orthonormal(S_rot, convention=convention)


def _polarization_screen_basis(n_hat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Orthonormal spherical screen `(e_theta, e_phi)` for unit incoming photon direction `n_hat`."""
    n = np.asarray(n_hat, dtype=np.float64)
    n = n / np.linalg.norm(n)
    z = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    e_phi = np.cross(z, n)
    if float(np.linalg.norm(e_phi)) < 1.0e-12:
        e_theta = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        e_phi = np.cross(n, e_theta)
    else:
        e_phi = e_phi / float(np.linalg.norm(e_phi))
        e_theta = np.cross(e_phi, n)
        e_theta = e_theta / float(np.linalg.norm(e_theta))
    return e_theta, e_phi


def aberrate_direction_and_stokes(
    n_hat: np.ndarray,
    stokes_q_frac: float,
    stokes_u_frac: float,
    beta: np.ndarray,
    *,
    wigner_R: np.ndarray | None = None,
) -> tuple[np.ndarray, float, float, float]:
    """Lorentz-aberrate direction `n_hat` and spin-2 transform fractional Stokes `(q, u)`.

    Returns `(n_hat_obs, q_obs, u_obs, spin2_rotation_angle_rad)`, preserving
    fractional linear polarization degree `q^2 + u^2` identically.
    """
    n = np.asarray(n_hat, dtype=np.float64)
    n = n / float(np.linalg.norm(n))
    b = np.asarray(beta, dtype=np.float64)
    b_sq = float(b @ b)
    if b_sq >= 1.0:
        raise BetaTruncationError(f"|beta| >= 1 in aberration: {b_sq}")

    R = np.eye(3, dtype=np.float64) if wigner_R is None else np.asarray(wigner_R, dtype=np.float64)
    if b_sq == 0.0 and np.allclose(R, np.eye(3), atol=1.0e-15):
        return n.copy(), float(stokes_q_frac), float(stokes_u_frac), 0.0

    # Screen basis at n_hat; rotate first by Wigner R, then boost photon 4-momentum (-1, n) or (+1, n)
    e1, e2 = _polarization_screen_basis(n)
    # Apply Wigner rotation R before boost B(beta) as in L = B(beta_comp) @ R_4:
    n_rot = R @ n
    e1_rot = R @ e1
    e2_rot = R @ e2

    # Relativistic Doppler & aberration for incoming line-of-sight vector n_hat (direction k_hat = -n_hat):
    g = 1.0 / math.sqrt(1.0 - b_sq)
    dot_bn = float(b @ n_rot)
    denom = g * (1.0 + dot_bn)
    if denom <= 0.0:
        raise KinematicsError("Non-positive Doppler denominator in aberration")
    par_factor = (g / (g + 1.0)) * dot_bn
    n_obs = (n_rot + (g + par_factor) * b) / denom
    n_obs = n_obs / float(np.linalg.norm(n_obs))

    # Fermi-Walker / null screen transport of spatial polarization 4-vector eps^a = (0, eps)
    # Project spatially boosted polarization vectors orthogonal to n_obs:
    L = lorentz_boost(-b)
    def _transport_screen_vec(e_vec: np.ndarray) -> np.ndarray:
        k4 = np.array([1.0, n_rot[0], n_rot[1], n_rot[2]], dtype=np.float64)
        e4 = np.array([0.0, e_vec[0], e_vec[1], e_vec[2]], dtype=np.float64)
        k4_p = L @ k4
        e4_p = L @ e4
        # Gauge shift along photon 4-momentum k4_p so temporal component e_0' == 0 in obs frame
        alpha = -e4_p[0] / k4_p[0]
        e_spatial = (e4_p + alpha * k4_p)[1:]
        # Enforce orthogonality to n_obs
        e_spatial = e_spatial - float(e_spatial @ n_obs) * n_obs
        return e_spatial / float(np.linalg.norm(e_spatial))

    e1_p = _transport_screen_vec(e1_rot)
    e1_obs, e2_obs = _polarization_screen_basis(n_obs)
    cos_chi = float(np.clip(e1_p @ e1_obs, -1.0, 1.0))
    sin_chi = float(e1_p @ e2_obs)
    chi = math.atan2(sin_chi, cos_chi)

    qu_in = complex(float(stokes_q_frac), float(stokes_u_frac))
    qu_out = qu_in * complex(math.cos(2.0 * chi), -math.sin(2.0 * chi))
    return n_obs, float(qu_out.real), float(qu_out.imag), chi


def _polarization_screen_basis_batch(n_hats: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized spherical screen `(e_theta, e_phi)` for `(..., 3)` unit vectors."""
    n = np.asarray(n_hats, dtype=np.float64)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    nx = n[..., 0]
    ny = n[..., 1]
    nz = n[..., 2]
    # z x n = (-ny, nx, 0)
    phi_norm = np.hypot(nx, ny)
    deg = phi_norm < 1.0e-12
    safe_phi = np.where(deg, 1.0, phi_norm)
    e_phi_non = np.stack([-ny / safe_phi, nx / safe_phi, np.zeros_like(nx)], axis=-1)
    # e_theta = e_phi x n = (e_phi_y * nz, -e_phi_x * nz, e_phi_x * ny - e_phi_y * nx)
    e_th_non = np.stack(
        [
            e_phi_non[..., 1] * nz,
            -e_phi_non[..., 0] * nz,
            e_phi_non[..., 0] * ny - e_phi_non[..., 1] * nx,
        ],
        axis=-1,
    )
    e_th_non = e_th_non / np.linalg.norm(e_th_non, axis=-1, keepdims=True)
    # Degenerate pole n = +- z: e_theta = (1, 0, 0), e_phi = n x (1,0,0) = (0, nz, -ny)
    e_th_deg = np.zeros_like(n)
    e_th_deg[..., 0] = 1.0
    e_phi_deg = np.stack([np.zeros_like(nx), nz, -ny], axis=-1)
    e_theta = np.where(deg[..., None], e_th_deg, e_th_non)
    e_phi = np.where(deg[..., None], e_phi_deg, e_phi_non)
    return e_theta, e_phi


def aberrate_directions_and_stokes_batch(
    n_hats: np.ndarray,
    stokes_q_frac: np.ndarray,
    stokes_u_frac: np.ndarray,
    beta: np.ndarray,
    *,
    wigner_R: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized Lorentz aberration + spin-2 Stokes transport over `(N, 3)` directions."""
    n = np.asarray(n_hats, dtype=np.float64)
    orig_shape = n.shape[:-1]
    n_flat = n.reshape(-1, 3)
    n_flat = n_flat / np.linalg.norm(n_flat, axis=-1, keepdims=True)
    q_arr = np.asarray(stokes_q_frac, dtype=np.float64).reshape(-1)
    u_arr = np.asarray(stokes_u_frac, dtype=np.float64).reshape(-1)

    b = np.asarray(beta, dtype=np.float64)
    b_sq = float(b @ b)
    if b_sq >= 1.0:
        raise BetaTruncationError(f"|beta| >= 1 in aberration: {b_sq}")

    R = np.eye(3, dtype=np.float64) if wigner_R is None else np.asarray(wigner_R, dtype=np.float64)
    if b_sq == 0.0 and np.allclose(R, np.eye(3), atol=1.0e-15):
        return (
            n_flat.reshape(*orig_shape, 3).copy(),
            q_arr.reshape(orig_shape).copy(),
            u_arr.reshape(orig_shape).copy(),
            np.zeros(orig_shape, dtype=np.float64),
        )

    e1, _ = _polarization_screen_basis_batch(n_flat)
    n_rot = n_flat @ R.T
    e1_rot = e1 @ R.T

    g = 1.0 / math.sqrt(1.0 - b_sq)
    dot_bn = n_rot @ b
    denom = g * (1.0 + dot_bn)
    if np.any(denom <= 0.0):
        raise KinematicsError("Non-positive Doppler denominator in aberration")
    par_factor = (g / (g + 1.0)) * dot_bn
    n_obs = (n_rot + (g + par_factor)[:, None] * b) / denom[:, None]
    n_obs = n_obs / np.linalg.norm(n_obs, axis=-1, keepdims=True)

    L = lorentz_boost(-b)
    ones = np.ones((n_rot.shape[0], 1), dtype=np.float64)
    zeros = np.zeros((n_rot.shape[0], 1), dtype=np.float64)
    k4 = np.hstack([ones, n_rot])
    e4 = np.hstack([zeros, e1_rot])
    k4_p = k4 @ L.T
    e4_p = e4 @ L.T
    alpha = -e4_p[:, 0] / k4_p[:, 0]
    e_spatial = e4_p[:, 1:] + alpha[:, None] * k4_p[:, 1:]
    e_spatial = e_spatial - np.sum(e_spatial * n_obs, axis=-1, keepdims=True) * n_obs
    e1_p = e_spatial / np.linalg.norm(e_spatial, axis=-1, keepdims=True)

    e1_obs, e2_obs = _polarization_screen_basis_batch(n_obs)
    cos_chi = np.clip(np.sum(e1_p * e1_obs, axis=-1), -1.0, 1.0)
    sin_chi = np.sum(e1_p * e2_obs, axis=-1)
    chi = np.arctan2(sin_chi, cos_chi)

    c2 = np.cos(2.0 * chi)
    s2 = np.sin(2.0 * chi)
    q_out = q_arr * c2 + u_arr * s2
    u_out = u_arr * c2 - q_arr * s2
    return (
        n_obs.reshape(*orig_shape, 3),
        q_out.reshape(orig_shape),
        u_out.reshape(orig_shape),
        chi.reshape(orig_shape),
    )


@dataclass(frozen=True)
class FrameTransportBundle:
    """Exact boost + Wigner rotation connecting slice normal, radiation, matter, and observer."""

    beta_normal_to_matter: np.ndarray
    beta_matter_to_radiation: np.ndarray
    beta_matter_to_observer: np.ndarray
    beta_radiation_to_observer: np.ndarray
    closure_rad_obs: VelocityClosureResult
    wigner_matrix: np.ndarray
    wigner_angle_rad: float
    wigner_axis: np.ndarray

    def transport_vector(self, vec: np.ndarray) -> np.ndarray:
        return self.wigner_matrix @ np.asarray(vec, dtype=np.float64)

    def transport_stf5_on(self, stf5_on: np.ndarray) -> np.ndarray:
        return wigner_rotate_stf5_on(stf5_on, self.wigner_matrix)


def build_frame_transport_bundle(
    *,
    beta_normal_to_matter: Sequence[float] | np.ndarray,
    beta_matter_to_radiation: Sequence[float] | np.ndarray,
    beta_matter_to_observer: Sequence[float] | np.ndarray,
) -> FrameTransportBundle:
    """Build exact multi-frame SR boost + Wigner bundle using `relativistic_velocity_closure`."""
    b_nm = np.asarray(beta_normal_to_matter, dtype=np.float64)
    b_mr = np.asarray(beta_matter_to_radiation, dtype=np.float64)
    b_mo = np.asarray(beta_matter_to_observer, dtype=np.float64)
    closure = compose_and_close_velocities(-b_mr, b_mo)
    return FrameTransportBundle(
        beta_normal_to_matter=b_nm.copy(),
        beta_matter_to_radiation=b_mr.copy(),
        beta_matter_to_observer=b_mo.copy(),
        beta_radiation_to_observer=closure.beta_RO.copy(),
        closure_rad_obs=closure,
        wigner_matrix=closure.wigner_rotation_matrix.copy(),
        wigner_angle_rad=closure.wigner_angle_rad,
        wigner_axis=closure.wigner_axis.copy(),
    )


@dataclass(frozen=True)
class TiltedConstraintReport:
    """Unified Jacobi, Hamiltonian, Codazzi/Momentum, and shear-trace residuals."""

    family: str
    jacobi_residual: float
    hamiltonian_residual: float
    codazzi_residual_vec: np.ndarray
    codazzi_residual_norm: float
    shear_trace_error: float
    shear_asymmetry_error: float
    ricci_dual_route_error: float
    codazzi_source_kappa_q: np.ndarray
    codazzi_div_sigma: np.ndarray
    is_admissible: bool
    tolerance: float


@dataclass(frozen=True)
class TiltedBianchiState:
    """Complete general tilted-Bianchi multi-congruence background slice state."""

    family: str
    algebra: BianchiAlgebra
    triple: StructureTriple
    geometry: TetradGeometry
    H: float
    lambda_value: float
    kappa: float
    sigma_ab: np.ndarray
    species_congruences: tuple[SpeciesFluidCongruence, ...]
    projected_species: tuple[SpeciesProjectedState, ...]
    total_matter: MatterNormalFrameState
    radiation_tilt_vec: np.ndarray
    observer_tilt_vec: np.ndarray
    frame_transport: FrameTransportBundle
    constraints: TiltedConstraintReport
    kinematics_by_species: dict[str, SpeciesCongruenceKinematics]


def evaluate_tilted_constraints(
    *,
    family: str,
    algebra: BianchiAlgebra,
    geometry: TetradGeometry,
    H: float,
    sigma_ab: np.ndarray,
    total_matter: MatterNormalFrameState,
    lambda_value: float = 0.0,
    kappa: float = 1.0,
    tol: float = 1.0e-11,
) -> TiltedConstraintReport:
    """Evaluate all Bianchi/Euler normal-frame constraint equations using exact R49 Class-B Ricci."""
    triple = algebra_to_triple(algebra)
    jac_res = triple.jacobi_residual()
    R_exact, ricci_scalar_exact, _ = exact_spatial_ricci_from_compact(algebra.a, algebra.n, a_sign=1)
    ricci_dual_err = float(np.max(np.abs(geometry.ricci_tensor - R_exact)))

    sigma = 0.5 * (np.asarray(sigma_ab, dtype=np.float64) + np.asarray(sigma_ab, dtype=np.float64).T)
    shear_trace_err = abs(float(np.trace(sigma)))
    shear_asym_err = float(np.max(np.abs(np.asarray(sigma_ab, dtype=np.float64) - np.asarray(sigma_ab, dtype=np.float64).T)))

    sigma_sq = 0.5 * float(np.sum(sigma * sigma))
    # 3 H^2 + R/2 - sigma^2 - kappa * rho - Lambda == 0
    ham_res = (
        3.0 * (float(H) ** 2)
        + 0.5 * float(ricci_scalar_exact)
        - sigma_sq
        - float(kappa) * float(total_matter.rho)
        - float(lambda_value)
    )
    div_sig = exact_momentum_divergence(sigma, algebra.a, algebra.n, a_sign=1)
    kq = float(kappa) * total_matter.q
    # Exact 4D Einstein constraint in synchronous (-,+,+,+) tetrad:
    # G^{0i} = -D_j sigma^j_i == kappa T^{0i} = +kappa q^i  =>  D_j sigma^j_i + kappa q_i = 0.
    cod_vec = div_sig + kq
    cod_norm = float(np.linalg.norm(cod_vec))

    admissible = (
        jac_res <= tol
        and ricci_dual_err <= tol
        and abs(ham_res) <= tol * max(1.0, 3.0 * H * H)
        and cod_norm <= tol * max(1.0, float(np.linalg.norm(div_sig)) + float(np.linalg.norm(kq)))
        and shear_trace_err <= tol
        and shear_asym_err <= tol
    )
    return TiltedConstraintReport(
        family=family,
        jacobi_residual=jac_res,
        hamiltonian_residual=float(ham_res),
        codazzi_residual_vec=cod_vec,
        codazzi_residual_norm=cod_norm,
        shear_trace_error=float(shear_trace_err),
        shear_asymmetry_error=float(shear_asym_err),
        ricci_dual_route_error=ricci_dual_err,
        codazzi_source_kappa_q=kq,
        codazzi_div_sigma=div_sig,
        is_admissible=admissible,
        tolerance=tol,
    )


def solve_compensating_tilt_velocity(
    target_q_vec: np.ndarray,
    *,
    eps_hat: float,
    p_hat: float,
) -> np.ndarray:
    """Invert exact SR momentum equation `gamma^2 (eps_hat + p_hat) v = target_q_vec`.

    Note: setting |q| = W * v / (1 - v^2) gives a quadratic in v^2:
        q^2 * (1 - v^2)^2 = W^2 * v^2  with unique subluminal root v < 1.
    """
    q = np.asarray(target_q_vec, dtype=np.float64)
    q_norm = float(np.linalg.norm(q))
    if q_norm == 0.0:
        return np.zeros(3, dtype=np.float64)
    w = float(eps_hat + p_hat)
    if w <= 0.0:
        raise CodazziProjectionError(
            f"Cannot source non-zero momentum q={q.tolist()} from species with enthalpy eps+p={w} <= 0"
        )
    # Solve (1 - v^2) / v = w / q_norm = r  =>  v^2 + r v - 1 = 0 => v = (-r + sqrt(r^2 + 4))/2
    r = w / q_norm
    v_mag = 0.5 * (-r + math.sqrt(r * r + 4.0))
    if not (0.0 <= v_mag < 1.0):
        raise BetaTruncationError(f"Solved speed invalid: v_mag={v_mag}")
    return (v_mag / q_norm) * q


def _non_lambda_tilted_species(species: Sequence[SpeciesFluidCongruence]) -> list[SpeciesFluidCongruence]:
    out = []
    for sp in species:
        if abs(sp.enthalpy_hat) > 1.0e-12 and sp.speed > 1.0e-12:
            out.append(sp)
    return out


def construct_admissible_tilted_state(
    *,
    family: str,
    H: float | None = None,
    sigma_ab: np.ndarray | None = None,
    species: Sequence[SpeciesFluidCongruence],
    lambda_value: float = 0.0,
    kappa: float = 1.0,
    observer_tilt_vec: Sequence[float] | np.ndarray = (0.0, 0.0, 0.0),
    algebra: BianchiAlgebra | None = None,
    codazzi_mode: Literal["strict", "project_shear_to_codazzi"] = "strict",
    closure: Literal["solve_H", "hold_H"] = "solve_H",
    tol: float = 1.0e-11,
) -> TiltedBianchiState:
    """Construct and certify a general tilted-Bianchi initial state across all 12 families.

    Fail-closed rules:
    1. All families evaluate Jacobi, exact Class-B Ricci, Hamiltonian, and Codazzi.
    2. For Bianchi `I` and `FLRW` (and `IX` with diagonal `n` where `div sigma == 0`),
       a single perfect fluid with `eps + p > 0` and non-zero `v` yields non-zero `q`
       while `div sigma == 0`, so `strict` (and shear projection into `ker(div)`!)
       rejects the state with `CodazziProjectionError`.
    3. Multi-fluid opposing tilts (e.g. photon vs matter with `q_1 + q_2 == 0`) ARE
       admitted because `q_tot == 0` satisfies Codazzi while preserving vector drifts!
    """
    if family not in ALL_TWELVE_FAMILIES:
        raise KeyError(f"Unsupported Bianchi/FLRW family {family!r}")
    if len(species) == 0:
        raise ValueError("At least one fluid congruence is required")

    alg = build_bianchi_algebra("I" if family == "FLRW" else family) if algebra is None else algebra
    geom = build_geometry(alg)
    triple = algebra_to_triple(alg)
    spec = FAMILY_ADMISSIBILITY_REGISTRY[family]

    sig = np.zeros((3, 3), dtype=np.float64) if sigma_ab is None else pstf_rank2(np.asarray(sigma_ab, dtype=np.float64))

    proj_list = tuple(sp.to_projected_state() for sp in species)
    tot = total_matter_projection(proj_list)

    active_tilts = _non_lambda_tilted_species(species)
    if len(active_tilts) == 1 and not spec.allows_uncompensated_single_perfect_fluid_tilt:
        if float(np.linalg.norm(tot.q)) > tol:
            raise CodazziProjectionError(
                f"[{family}] Codazzi momentum constraint forbids an uncompensated single "
                f"perfect-fluid tilt (|q|={np.linalg.norm(tot.q):.3e} while D_j sigma^j_i == 0 identically). "
                "Add a compensating second species or set v == 0."
            )

    if codazzi_mode == "project_shear_to_codazzi":
        # Project shear onto divergence equation M_div @ s5 == kappa * tot.q
        basis_cols = []
        for idx in range(5):
            e_vec = np.zeros(5, dtype=np.float64)
            e_vec[idx] = 1.0
            S_basis = orthonormal_to_stf_matrix(e_vec, convention="kinematic_response")
            basis_cols.append(exact_momentum_divergence(S_basis, alg.a, alg.n, a_sign=1))
        M_div = np.column_stack(basis_cols)
        target_div = -float(kappa) * tot.q
        s5_sol, _, _, _ = np.linalg.lstsq(M_div, target_div, rcond=1.0e-12)
        res_proj = float(np.linalg.norm(M_div @ s5_sol - target_div))
        if res_proj > tol * max(1.0, float(np.linalg.norm(target_div))):
            raise CodazziProjectionError(
                f"[{family}] Target momentum q={tot.q.tolist()} lies outside range of D_j sigma^j_i "
                f"(residual={res_proj:.3e})"
            )
        # Keep projection component in ker(M_div) close to input `sigma_ab`
        s5_in = stf_matrix_to_orthonormal(sig, convention="kinematic_response")
        # Minimum-norm correction ds5 solving M_div (s5_in + ds5) = target_div
        ds5, _, _, _ = np.linalg.lstsq(M_div, target_div - M_div @ s5_in, rcond=1.0e-12)
        sig = orthonormal_to_stf_matrix(s5_in + ds5, convention="kinematic_response")

    _, ricci_scalar_exact, _ = exact_spatial_ricci_from_compact(alg.a, alg.n, a_sign=1)
    sigma_sq = 0.5 * float(np.sum(sig * sig))
    if closure == "solve_H":
        three_h2 = float(kappa) * float(tot.rho) + float(lambda_value) + sigma_sq - 0.5 * float(ricci_scalar_exact)
        if three_h2 <= 0.0:
            raise CodazziProjectionError(
                f"[{family}] Cannot close expanding Hamiltonian constraint: 3 H^2 = {three_h2:.6e} <= 0"
            )
        H_val = math.sqrt(three_h2 / 3.0)
    elif closure == "hold_H":
        if H is None or float(H) <= 0.0:
            raise ValueError("closure='hold_H' requires positive H")
        H_val = float(H)
    else:
        raise ValueError(f"Unknown closure {closure!r}")

    constraints = evaluate_tilted_constraints(
        family=family,
        algebra=alg,
        geometry=geom,
        H=H_val,
        sigma_ab=sig,
        total_matter=tot,
        lambda_value=lambda_value,
        kappa=kappa,
        tol=tol,
    )
    if not constraints.is_admissible:
        raise CodazziProjectionError(
            f"[{family}] Constraints violated: H_res={constraints.hamiltonian_residual:.3e}, "
            f"Codazzi_res={constraints.codazzi_residual_norm:.3e}, Jacobi_res={constraints.jacobi_residual:.3e}"
        )

    kin_map = {
        sp.species: compute_species_congruence_kinematics(sp, H=H_val, sigma_ab=sig, C_spatial=alg.C)
        for sp in species
    }

    # Separate matter (baryon+cdm weighted), radiation (photon), and observer frames
    matter_species = [sp for sp in species if sp.species in ("baryon", "cdm", "matter")]
    rad_species = [sp for sp in species if sp.species == "photon"]
    if matter_species:
        num = sum((sp.enthalpy_hat * (sp.gamma ** 2)) * sp.v_vec for sp in matter_species)
        den = sum(sp.enthalpy_hat * (sp.gamma ** 2) for sp in matter_species)
        v_matter = num / den if den > 0.0 else np.zeros(3, dtype=np.float64)
    else:
        v_matter = np.zeros(3, dtype=np.float64)
    v_rad = rad_species[0].v_vec.copy() if rad_species else np.zeros(3, dtype=np.float64)
    v_obs = np.asarray(observer_tilt_vec, dtype=np.float64)
    # Matter-to-radiation and matter-to-observer via exact SR velocity composition
    b_mr = compose_and_close_velocities(-v_matter, v_rad).beta_RO
    b_mo = compose_and_close_velocities(-v_matter, v_obs).beta_RO
    ft_bundle = build_frame_transport_bundle(
        beta_normal_to_matter=v_matter,
        beta_matter_to_radiation=b_mr,
        beta_matter_to_observer=b_mo,
    )

    return TiltedBianchiState(
        family=family,
        algebra=alg,
        triple=triple,
        geometry=geom,
        H=H_val,
        lambda_value=float(lambda_value),
        kappa=float(kappa),
        sigma_ab=sig,
        species_congruences=tuple(species),
        projected_species=proj_list,
        total_matter=tot,
        radiation_tilt_vec=v_rad,
        observer_tilt_vec=v_obs,
        frame_transport=ft_bundle,
        constraints=constraints,
        kinematics_by_species=kin_map,
    )
