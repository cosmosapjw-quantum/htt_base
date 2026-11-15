"""R49 general tilted Bianchi Class A / Class B dynamical Einstein-Euler evolution.

Implements `GBI-03`:
- Evolves the full non-perturbative Einstein + multi-fluid Euler system in e-fold
  time `N = ln a` across `FLRW` and all 11 Bianchi types (`I`..`IX`) using the
  Fermi-Walker synchronous tetrad `(H, Sigma_5, a_alpha, n^{alpha beta}, eta)`
  and per-species logarithmic energy & velocity ratios `(ln T_s^{00}, r_s^alpha)`.
- Integrates exact `nabla_a T_s^{ab} = 0` via the 4D Bianchi connection `Gamma4`,
  exact Jacobi-preserving commutator evolution `dC^k_{ij}/dt`, Raychaudhuri, and
  trace-free shear evolution `dsigma/dt = -3 H sigma - R_<ab> + kappa pi_<ab>`
  with zero algebraic constraint-replacement shortcuts.
- Monitors Jacobi, Hamiltonian, Codazzi (`D_j sigma^j_i + kappa q_i = 0`), and
  subluminal velocity bounds along the trajectory and fails closed via
  `CodazziProjectionError` on threshold breach.
- Includes the Fournodavlos, Marshall & Oliynyk (2026) two-fluid tilted Bianchi-I
  nonlinear stability benchmark (`Lambda > 0`, `1/3 < K_1 <= K_2 < 5/7`) and
  step-refinement convergence suite across Class A and Class B representatives.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal, Sequence

import numpy as np
from scipy.integrate import solve_ivp

from bass.background import rhs as ver2_rhs
from bass.background.bianchi_types import BianchiAlgebra, build_bianchi_algebra
from bass.background.constraints import MatterNormalFrameState
from bass.background.convention_bridge import (
    ALL_TWELVE_FAMILIES,
    LEVI_CIVITA_3D,
    build_structure_tensor_with_sign,
    exact_momentum_divergence,
    exact_spatial_ricci_from_compact,
)
from bass.background.geometry import pstf_rank2
from bass.background.initial_conditions import CodazziProjectionError
from bass.background.tilted_bianchi_state import (
    SpeciesFluidCongruence,
    TiltedBianchiState,
    build_4d_bianchi_connection,
    construct_admissible_tilted_state,
    solve_compensating_tilt_velocity,
)
from common.relativistic_kinematics import lorentz_boost
from common.stf_metric_bridge import (
    orthonormal_to_stf_matrix,
    stf_matrix_to_orthonormal,
)

__all__ = [
    "EvolvedSpeciesSpec",
    "TiltedEvolutionConfig",
    "TiltedTrajectoryPoint",
    "TiltedEvolutionResult",
    "FournodavlosStabilityBenchmarkResult",
    "primitive_from_energy_momentum_ratio",
    "energy_momentum_ratio_from_primitive",
    "evolve_general_tilted_bianchi",
    "run_fournodavlos_two_fluid_bianchi_i_benchmark",
    "verify_all_families_evolution_convergence",
]


@dataclass(frozen=True)
class EvolvedSpeciesSpec:
    """Constant-EOS relativistic tilted fluid species descriptor."""

    species: str
    K_eos: float


@dataclass(frozen=True)
class TiltedEvolutionConfig:
    """Configuration for general tilted-Bianchi e-fold integration."""

    N_start: float = 0.0
    N_end: float = 2.0
    n_eval: int = 81
    method: Literal["DOP853", "RK45", "BDF", "Radau"] = "DOP853"
    rtol: float = 1.0e-10
    atol: float = 1.0e-12
    constraint_abort_tol: float = 1.0e-6
    eta_start: float = 0.0


@dataclass(frozen=True)
class TiltedTrajectoryPoint:
    """Single e-fold snapshot along a general tilted-Bianchi trajectory."""

    N: float
    scale_factor: float
    eta: float
    H: float
    sigma_ab: np.ndarray
    a_vec: np.ndarray
    n_mat: np.ndarray
    species_eps_hat: dict[str, float]
    species_v_vec: dict[str, np.ndarray]
    jacobi_residual: float
    hamiltonian_residual_rel: float
    codazzi_residual_rel: float


@dataclass(frozen=True)
class TiltedEvolutionResult:
    """Complete evolved general tilted-Bianchi trajectory and constraint audit."""

    family: str
    class_label: Literal["A", "B"]
    species_specs: tuple[EvolvedSpeciesSpec, ...]
    lambda_value: float
    kappa: float
    N_grid: np.ndarray
    eta_grid: np.ndarray
    H_grid: np.ndarray
    sigma_ab_grid: np.ndarray
    a_grid: np.ndarray
    n_grid: np.ndarray
    species_v_grid: dict[str, np.ndarray]
    species_eps_hat_grid: dict[str, np.ndarray]
    max_jacobi_residual: float
    max_hamiltonian_residual_rel: float
    max_codazzi_residual_rel: float
    max_shear_trace_error: float
    max_speed_over_trajectory: float
    n_rhs_evals: int
    converged: bool


@dataclass(frozen=True)
class FournodavlosStabilityBenchmarkResult:
    """Verification of Fournodavlos, Marshall & Oliynyk (2026) two-fluid Bianchi-I stability."""

    K_1: float
    K_2: float
    lambda_value: float
    initial_shear_over_H: float
    final_shear_over_H: float
    shear_decay_ratio: float
    initial_speed_1: float
    final_speed_1: float
    initial_speed_2: float
    final_speed_2: float
    max_speed_along_orbit: float
    max_hamiltonian_residual_rel: float
    max_codazzi_residual_rel: float
    passed_theorem_regime: bool


def _pack_sym6(n_mat: np.ndarray) -> np.ndarray:
    S = 0.5 * (n_mat + n_mat.T)
    return np.array([S[0, 0], S[1, 1], S[2, 2], S[0, 1], S[0, 2], S[1, 2]], dtype=np.float64)


def _unpack_sym6(v6: np.ndarray) -> np.ndarray:
    return np.array(
        [
            [v6[0], v6[3], v6[4]],
            [v6[3], v6[1], v6[5]],
            [v6[4], v6[5], v6[2]],
        ],
        dtype=np.float64,
    )


def energy_momentum_ratio_from_primitive(
    eps_hat: float,
    v_vec: Sequence[float] | np.ndarray,
    K_eos: float,
) -> tuple[float, np.ndarray]:
    """Convert primitive `(eps_hat, v_vec)` with `p_hat = K * eps_hat` to `(ln T^{00}, T^{0i}/T^{00})`."""
    v = np.asarray(v_vec, dtype=np.float64)
    b2 = float(v @ v)
    if b2 >= 1.0:
        raise CodazziProjectionError(f"Superluminal velocity |v|^2 = {b2} >= 1")
    E = float(eps_hat) * (1.0 + float(K_eos) * b2) / (1.0 - b2)
    if E <= 0.0:
        raise ValueError(f"Energy density T^00 must be strictly positive, got {E}")
    r = ((1.0 + float(K_eos)) / (1.0 + float(K_eos) * b2)) * v
    return math.log(E), r


def primitive_from_energy_momentum_ratio(
    log_E: float,
    r_vec: np.ndarray,
    K_eos: float,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Recover `(eps_hat, p_hat, v_vec, T4)` stably across all `K in (-1, 1]` and `|v| < 1`."""
    E = math.exp(float(log_E))
    rv = np.asarray(r_vec, dtype=np.float64)
    r_norm = float(np.linalg.norm(rv))
    K = float(K_eos)
    if r_norm == 0.0:
        v = np.zeros(3, dtype=np.float64)
        eps_hat = E
    else:
        disc = (1.0 + K) ** 2 - 4.0 * K * (r_norm ** 2)
        if disc <= 0.0:
            raise CodazziProjectionError(
                f"Invalid conserved momentum ratio |r|={r_norm:.6f} for K={K:.4f} (disc={disc:.3e})"
            )
        beta = (2.0 * r_norm) / ((1.0 + K) + math.sqrt(disc))
        if beta >= 1.0:
            raise CodazziProjectionError(f"Recovered speed beta={beta:.6f} >= 1")
        v = (beta / r_norm) * rv
        b2 = beta * beta
        eps_hat = E * (1.0 - b2) / (1.0 + K * b2)
    p_hat = K * eps_hat
    L = lorentz_boost(v)
    T4 = L @ np.diag([eps_hat, p_hat, p_hat, p_hat]) @ L.T
    return float(eps_hat), float(p_hat), v, T4


def evolve_general_tilted_bianchi(
    initial_state: TiltedBianchiState,
    *,
    eos_by_species: dict[str, float] | None = None,
    config: TiltedEvolutionConfig | None = None,
) -> TiltedEvolutionResult:
    """Evolve a certified `TiltedBianchiState` forward/backward in e-fold `N = ln a`.

    Zero algebraic constraint replacement: evolves `(ln H, sigma_5, a, n_sym6, eta)`
    and per-species `(ln E_s, r_s)` directly from Einstein + 4D Euler equations,
    failing closed if Jacobi, Hamiltonian, or Codazzi residuals breach
    `config.constraint_abort_tol`.
    """
    cfg = TiltedEvolutionConfig() if config is None else config
    active_congs = [sp for sp in initial_state.species_congruences if sp.species != "lambda"]
    if not active_congs:
        raise ValueError("Need at least one non-Lambda dynamic species to evolve")

    eos_map = {} if eos_by_species is None else dict(eos_by_species)
    specs: list[EvolvedSpeciesSpec] = []
    for sp in active_congs:
        if sp.species in eos_map:
            K = float(eos_map[sp.species])
        elif abs(sp.eps_hat) > 0.0:
            K = float(sp.p_hat / sp.eps_hat)
        else:
            K = 0.0
        specs.append(EvolvedSpeciesSpec(species=sp.species, K_eos=K))

    Lam = float(initial_state.lambda_value)
    # Include static vacuum species if present separately in initial_state.species_congruences
    for sp in initial_state.species_congruences:
        if sp.species == "lambda":
            Lam += float(initial_state.kappa) * float(sp.eps_hat)

    kappa = float(initial_state.kappa)
    n_sp = len(active_congs)

    # Initial packed state: [ln_H (1), sigma_5 (5), a (3), n_sym6 (6), eta (1), species (4 * n_sp)]
    y0 = np.zeros(16 + 4 * n_sp, dtype=np.float64)
    y0[0] = math.log(float(initial_state.H))
    y0[1:6] = stf_matrix_to_orthonormal(initial_state.sigma_ab, convention="kinematic_response")
    y0[6:9] = initial_state.algebra.a.copy()
    y0[9:15] = _pack_sym6(initial_state.algebra.n)
    y0[15] = float(cfg.eta_start)
    for idx, (sp, spec) in enumerate(zip(active_congs, specs)):
        lE, r_v = energy_momentum_ratio_from_primitive(sp.eps_hat, sp.v_vec, spec.K_eos)
        off = 16 + 4 * idx
        y0[off] = lE
        y0[off + 1 : off + 4] = r_v

    def _unpack_and_eval_sources(N_val: float, y: np.ndarray):
        H = math.exp(float(y[0]))
        sig = orthonormal_to_stf_matrix(y[1:6], convention="kinematic_response")
        a_v = y[6:9]
        n_m = _unpack_sym6(y[9:15])
        C = build_structure_tensor_with_sign(a_v, n_m, a_sign=1)
        _, R_sc, S_ab = exact_spatial_ricci_from_compact(a_v, n_m, a_sign=1)

        T4_tot = np.zeros((4, 4), dtype=np.float64)
        T4_list = []
        eps_hat_list = []
        v_list = []
        for idx, spec in enumerate(specs):
            off = 16 + 4 * idx
            eh, _, vv, T4_s = primitive_from_energy_momentum_ratio(y[off], y[off + 1 : off + 4], spec.K_eos)
            T4_tot += T4_s
            T4_list.append(T4_s)
            eps_hat_list.append(eh)
            v_list.append(vv)

        rho_tot = float(T4_tot[0, 0])
        q_tot = T4_tot[0, 1:]
        p_tot = float(np.trace(T4_tot[1:, 1:]) / 3.0)
        pi_tot = pstf_rank2(T4_tot[1:, 1:])
        return H, sig, a_v, n_m, C, R_sc, S_ab, rho_tot, p_tot, q_tot, pi_tot, T4_list, eps_hat_list, v_list

    def ode_rhs(N_val: float, y: np.ndarray) -> np.ndarray:
        H, sig, a_v, n_m, C, _, S_ab, rho_tot, p_tot, q_tot, pi_tot, T4_list, _, _ = _unpack_and_eval_sources(N_val, y)
        matter = MatterNormalFrameState(rho=rho_tot, p=p_tot, q=q_tot, pi=pi_tot)
        dH_dt = ver2_rhs.raychaudhuri_rhs(H=H, sigma_ab=sig, matter=matter, lambda_value=Lam, kappa=kappa)
        dsig_dt = ver2_rhs.shear_rhs(H=H, sigma_ab=sig, S_ab=S_ab, pi_ab=pi_tot, kappa=kappa)

        theta = H * np.eye(3, dtype=np.float64) + sig
        Cdot = (
            np.einsum("km,mij->kij", theta, C)
            - np.einsum("mi,kmj->kij", theta, C)
            - np.einsum("mj,kim->kij", theta, C)
        )
        adot = -0.5 * np.einsum("kki->i", Cdot)
        delta = np.eye(3, dtype=np.float64)
        Cdot_n = Cdot - (np.einsum("a,bc->cab", adot, delta) - np.einsum("b,ac->cab", adot, delta))
        ndot = 0.5 * np.einsum("dab,cab->dc", LEVI_CIVITA_3D, Cdot_n)
        ndot = 0.5 * (ndot + ndot.T)

        Gamma4 = build_4d_bianchi_connection(H, sig, C)
        dy = np.zeros_like(y)
        inv_H = 1.0 / H
        dy[0] = (dH_dt * inv_H) * inv_H  # d(ln H)/dN = dH/(H^2 dt)
        dy[1:6] = stf_matrix_to_orthonormal(dsig_dt * inv_H, convention="kinematic_response")
        dy[6:9] = adot * inv_H
        dy[9:15] = _pack_sym6(ndot * inv_H)
        dy[15] = math.exp(-float(N_val)) * inv_H  # d(eta)/dN = 1 / (a * H)

        for idx, T4_s in enumerate(T4_list):
            dT0_dt = -(np.einsum("aca,cb->b", Gamma4, T4_s) + np.einsum("bca,ac->b", Gamma4, T4_s))
            E_s = T4_s[0, 0]
            Q_s = T4_s[0, 1:]
            r_s = Q_s / E_s
            dE_dN = dT0_dt[0] * inv_H
            dQ_dN = dT0_dt[1:] * inv_H
            off = 16 + 4 * idx
            dy[off] = dE_dN / E_s
            dy[off + 1 : off + 4] = (dQ_dN - r_s * dE_dN) / E_s
        return dy

    N_eval = np.linspace(float(cfg.N_start), float(cfg.N_end), int(cfg.n_eval), dtype=np.float64)
    sol = solve_ivp(
        ode_rhs,
        (float(cfg.N_start), float(cfg.N_end)),
        y0,
        method=cfg.method,
        t_eval=N_eval,
        rtol=float(cfg.rtol),
        atol=float(cfg.atol),
    )
    if not sol.success:
        raise CodazziProjectionError(f"[{initial_state.family}] ODE integration failed: {sol.message}")

    M_steps = sol.y.shape[1]
    H_grid = np.zeros(M_steps, dtype=np.float64)
    eta_grid = sol.y[15, :].copy()
    sig_grid = np.zeros((M_steps, 3, 3), dtype=np.float64)
    a_grid = np.zeros((M_steps, 3), dtype=np.float64)
    n_grid = np.zeros((M_steps, 3, 3), dtype=np.float64)
    v_grid = {spec.species: np.zeros((M_steps, 3), dtype=np.float64) for spec in specs}
    eps_grid = {spec.species: np.zeros(M_steps, dtype=np.float64) for spec in specs}

    max_jac = 0.0
    max_ham_rel = 0.0
    max_cod_rel = 0.0
    max_trace = 0.0
    max_speed = 0.0

    for k in range(M_steps):
        yk = sol.y[:, k]
        (
            H, sig, a_v, n_m, _, R_sc, _, rho_tot, _, q_tot, _, T4_list, eh_list, vv_list
        ) = _unpack_and_eval_sources(float(N_eval[k]), yk)
        H_grid[k] = H
        sig_grid[k] = sig
        a_grid[k] = a_v
        n_grid[k] = n_m
        for idx, spec in enumerate(specs):
            eps_grid[spec.species][k] = eh_list[idx]
            v_grid[spec.species][k] = vv_list[idx]
            max_speed = max(max_speed, float(np.linalg.norm(vv_list[idx])))

        jac = float(np.linalg.norm(n_m @ a_v)) / max(1.0, float(np.linalg.norm(a_v) * np.linalg.norm(n_m)))
        sigma_sq = 0.5 * float(np.sum(sig * sig))
        ham_scale = max(1.0, 3.0 * H * H + abs(kappa * rho_tot) + abs(Lam) + abs(0.5 * R_sc))
        ham_rel = abs(3.0 * H * H + 0.5 * R_sc - sigma_sq - kappa * rho_tot - Lam) / ham_scale

        div_sig = exact_momentum_divergence(sig, a_v, n_m, a_sign=1)
        q_species_sum = sum(float(np.linalg.norm(kappa * T4_s[0, 1:])) for T4_s in T4_list)
        cod_scale = max(
            1.0e-12,
            float(np.linalg.norm(div_sig)) + q_species_sum + H * float(np.linalg.norm(sig)),
        )
        cod_rel = float(np.linalg.norm(div_sig + kappa * q_tot)) / cod_scale

        max_jac = max(max_jac, jac)
        max_ham_rel = max(max_ham_rel, ham_rel)
        max_cod_rel = max(max_cod_rel, cod_rel)
        max_trace = max(max_trace, abs(float(np.trace(sig))))

    if max(max_jac, max_ham_rel, max_cod_rel) > float(cfg.constraint_abort_tol):
        raise CodazziProjectionError(
            f"[{initial_state.family}] Dynamic constraint breach: "
            f"jac={max_jac:.3e}, ham_rel={max_ham_rel:.3e}, cod_rel={max_cod_rel:.3e}"
        )

    return TiltedEvolutionResult(
        family=initial_state.family,
        class_label=initial_state.triple.class_label,
        species_specs=tuple(specs),
        lambda_value=Lam,
        kappa=kappa,
        N_grid=N_eval,
        eta_grid=eta_grid,
        H_grid=H_grid,
        sigma_ab_grid=sig_grid,
        a_grid=a_grid,
        n_grid=n_grid,
        species_v_grid=v_grid,
        species_eps_hat_grid=eps_grid,
        max_jacobi_residual=max_jac,
        max_hamiltonian_residual_rel=max_ham_rel,
        max_codazzi_residual_rel=max_cod_rel,
        max_shear_trace_error=max_trace,
        max_speed_over_trajectory=max_speed,
        n_rhs_evals=int(sol.nfev),
        converged=True,
    )


def run_fournodavlos_two_fluid_bianchi_i_benchmark(
    *,
    K_1: float = 0.42,
    K_2: float = 0.58,
    lambda_value: float = 1.8,
    N_end: float = 4.5,
) -> FournodavlosStabilityBenchmarkResult:
    """Reproduce Fournodavlos, Marshall & Oliynyk (2026) two-fluid tilted Bianchi-I nonlinear stability.

    For Bianchi I with Lambda > 0 and two barotropic fluids satisfying 1/3 < K_1 <= K_2 < 5/7
    and balanced initial momenta q_1 + q_2 == 0, Einstein-Euler solutions stay future-stable,
    subluminal, and shear-damped (sigma / H -> 0).
    """
    if not (1.0 / 3.0 < K_1 <= K_2 < 5.0 / 7.0) or lambda_value <= 0.0:
        raise ValueError("Inputs outside Fournodavlos-Marshall-Oliynyk theorem window")

    sp1 = SpeciesFluidCongruence(
        species="fluid_1",
        eps_hat=0.6,
        p_hat=float(K_1) * 0.6,
        v_vec=np.array([0.18, -0.07, 0.05], dtype=np.float64),
    )
    q1 = sp1.to_projected_state().q
    v2_req = solve_compensating_tilt_velocity(-q1, eps_hat=0.9, p_hat=float(K_2) * 0.9)
    sp2 = SpeciesFluidCongruence(
        species="fluid_2",
        eps_hat=0.9,
        p_hat=float(K_2) * 0.9,
        v_vec=v2_req,
    )
    sig0 = pstf_rank2(np.array([[-0.18, 0.06, -0.04], [0.06, 0.09, 0.05], [-0.04, 0.05, 0.09]]))
    init = construct_admissible_tilted_state(
        family="I",
        sigma_ab=sig0,
        species=[sp1, sp2],
        lambda_value=lambda_value,
        kappa=1.0,
    )
    res = evolve_general_tilted_bianchi(
        init,
        eos_by_species={"fluid_1": K_1, "fluid_2": K_2},
        config=TiltedEvolutionConfig(N_start=0.0, N_end=N_end, n_eval=91, rtol=1.0e-11, atol=1.0e-13),
    )
    sig_init = float(np.linalg.norm(res.sigma_ab_grid[0]) / res.H_grid[0])
    sig_fin = float(np.linalg.norm(res.sigma_ab_grid[-1]) / res.H_grid[-1])
    v1_0 = float(np.linalg.norm(res.species_v_grid["fluid_1"][0]))
    v1_f = float(np.linalg.norm(res.species_v_grid["fluid_1"][-1]))
    v2_0 = float(np.linalg.norm(res.species_v_grid["fluid_2"][0]))
    v2_f = float(np.linalg.norm(res.species_v_grid["fluid_2"][-1]))

    passed = (
        res.max_speed_over_trajectory < 1.0
        and res.max_hamiltonian_residual_rel < 1.0e-9
        and res.max_codazzi_residual_rel < 1.0e-10
        and sig_fin < 1.0e-3 * sig_init
    )
    return FournodavlosStabilityBenchmarkResult(
        K_1=float(K_1),
        K_2=float(K_2),
        lambda_value=float(lambda_value),
        initial_shear_over_H=sig_init,
        final_shear_over_H=sig_fin,
        shear_decay_ratio=sig_fin / max(sig_init, 1.0e-30),
        initial_speed_1=v1_0,
        final_speed_1=v1_f,
        initial_speed_2=v2_0,
        final_speed_2=v2_f,
        max_speed_along_orbit=res.max_speed_over_trajectory,
        max_hamiltonian_residual_rel=res.max_hamiltonian_residual_rel,
        max_codazzi_residual_rel=res.max_codazzi_residual_rel,
        passed_theorem_regime=passed,
    )


def _build_default_admissible_state_for_family(family: str) -> TiltedBianchiState:
    alg = build_bianchi_algebra("I" if family == "FLRW" else family)
    if family in ("FLRW", "I", "IX"):
        sig = np.zeros((3, 3), dtype=np.float64) if family == "FLRW" else pstf_rank2(np.diag([-0.03, 0.015, 0.015]))
        sp_rad = SpeciesFluidCongruence(species="photon", eps_hat=0.25, p_hat=0.25 / 3.0, v_vec=[0.04, -0.02, 0.01])
        v_mat = solve_compensating_tilt_velocity(-sp_rad.to_projected_state().q, eps_hat=1.0, p_hat=0.0)
        sp_mat = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=v_mat)
        species = [sp_rad, sp_mat]
    else:
        sig = pstf_rank2(
            np.array([[-0.03, 0.012, -0.008], [0.012, 0.015, 0.009], [-0.008, 0.009, 0.015]])
        )
        div_sig = exact_momentum_divergence(sig, alg.a, alg.n, a_sign=1)
        sp_rad = SpeciesFluidCongruence(species="photon", eps_hat=0.25, p_hat=0.25 / 3.0, v_vec=[0.03, 0.01, -0.01])
        q_rem = -div_sig - sp_rad.to_projected_state().q
        v_mat = solve_compensating_tilt_velocity(q_rem, eps_hat=1.0, p_hat=0.0)
        sp_mat = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=v_mat)
        species = [sp_rad, sp_mat]
    return construct_admissible_tilted_state(
        family=family,
        algebra=alg,
        sigma_ab=sig,
        species=species,
        lambda_value=1.5,
        kappa=1.0,
    )


def verify_all_families_evolution_convergence() -> dict[str, Any]:
    """Run all 12 families through coarse-vs-fine convergence & constraint checks."""
    fournodavlos = run_fournodavlos_two_fluid_bianchi_i_benchmark()
    families_summary: dict[str, Any] = {}
    all_passed = fournodavlos.passed_theorem_regime

    for fam in ALL_TWELVE_FAMILIES:
        init = _build_default_admissible_state_for_family(fam)
        res_coarse = evolve_general_tilted_bianchi(
            init,
            eos_by_species={"photon": 1.0 / 3.0, "cdm": 0.0},
            config=TiltedEvolutionConfig(N_start=0.0, N_end=1.5, n_eval=31, method="RK45", rtol=1.0e-7, atol=1.0e-9),
        )
        res_fine = evolve_general_tilted_bianchi(
            init,
            eos_by_species={"photon": 1.0 / 3.0, "cdm": 0.0},
            config=TiltedEvolutionConfig(N_start=0.0, N_end=1.5, n_eval=31, method="DOP853", rtol=1.0e-11, atol=1.0e-13),
        )
        refinement_diff_H = float(np.max(np.abs(res_coarse.H_grid - res_fine.H_grid)))
        refinement_diff_sig = float(np.max(np.abs(res_coarse.sigma_ab_grid - res_fine.sigma_ab_grid)))
        refinement_diff_v = float(np.max(np.abs(res_coarse.species_v_grid["photon"] - res_fine.species_v_grid["photon"])))
        fam_ok = (
            res_fine.max_jacobi_residual < 1.0e-13
            and res_fine.max_hamiltonian_residual_rel < 1.0e-9
            and res_fine.max_codazzi_residual_rel < 1.0e-9
            and refinement_diff_H < 1.0e-6
            and refinement_diff_sig < 1.0e-6
            and refinement_diff_v < 1.0e-6
        )
        all_passed = all_passed and fam_ok
        families_summary[fam] = {
            "class_label": res_fine.class_label,
            "passed": fam_ok,
            "max_jacobi_residual": res_fine.max_jacobi_residual,
            "max_hamiltonian_residual_rel": res_fine.max_hamiltonian_residual_rel,
            "max_codazzi_residual_rel": res_fine.max_codazzi_residual_rel,
            "max_shear_trace_error": res_fine.max_shear_trace_error,
            "refinement_diff_H": refinement_diff_H,
            "refinement_diff_sigma": refinement_diff_sig,
            "refinement_diff_v_photon": refinement_diff_v,
            "final_H": float(res_fine.H_grid[-1]),
            "final_v_photon": res_fine.species_v_grid["photon"][-1].tolist(),
            "final_v_cdm": res_fine.species_v_grid["cdm"][-1].tolist(),
        }

    return {
        "schema_version": "r49_gbi03_evolution_convergence_v1",
        "all_passed": all_passed,
        "fournodavlos_2026_two_fluid_bianchi_i": fournodavlos.__dict__,
        "families": families_summary,
    }
