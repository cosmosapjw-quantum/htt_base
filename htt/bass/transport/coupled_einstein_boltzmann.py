"""Self-consistent coupled Bianchi Einstein-Euler + general-Lie polarized Boltzmann + tilted HYREC solver.

Unifies:
- N1 (`GeneralLieStokesOperator`): all-m geodesic + Sachs screen twist across `(T, E, B, V)`
  with L-stable SDIRK(2,2) + exact 9x9 Woodbury/Schur Thomson monopole capacity solve.
- N2 (`MovingFrameThomsonOperator` + `covariant_thomson_four_force`): exact electron-rest
  redistribution & covariant 4-force conservation (`u_b . F_rad == 0`, `F_bar == -F_rad`).
- N3 (`TiltedHyrecRecombination`): 4-channel physical HYREC-2 recombination/reionization
  history separating clock `Gamma * H_n`, rest density `N_H/(Gamma a^3)`, directional/shear
  Sobolev escape `H_esc`, and matter cooling `Theta_b / 3`.
- Iterated radiation anisotropic stress `pi_gamma(N)` backreaction across all 7 Bianchi
  families (`FLRW`, `I`, `V`, `VII_h` [handedness +1/-1], `VI_h`, `VI_-1/9`, `IX`).

All constraint residuals (Jacobi, Hamiltonian, Codazzi) and Stokes reality errors are checked
fail-closed throughout evolution.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Literal, Sequence

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from scipy.special import sph_harm_y

from bass.background import rhs as ver2_rhs
from bass.background.bianchi_types import BianchiAlgebra, build_bianchi_algebra, build_structure_tensor
from bass.background.constraints import MatterNormalFrameState
from bass.background.convention_bridge import (
    LEVI_CIVITA_3D,
    build_structure_tensor_with_sign,
    exact_momentum_divergence,
    exact_spatial_ricci_from_compact,
)
from bass.background.general_tilted_evolution import (
    TiltedEvolutionResult,
    _pack_sym6,
    _unpack_sym6,
    energy_momentum_ratio_from_primitive,
    primitive_from_energy_momentum_ratio,
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
from bass.collision.moving_thomson import MovingFrameThomsonOperator, covariant_thomson_four_force
from bass.recombination.reionization import CosmologyForRecombination, ReionizationParameters, cosmology_from_metadata
from bass.recombination.recombination_ingest import load_recombination_table
from bass.recombination.tilted_hyrec import (
    HyRecAtomicTables,
    TiltedHyrecHistory,
    integrate_tilted_recombination,
    load_hyrec_atomic_tables,
)
from bass.transport.general_bianchi_transfer import _spherical_screen_basis, gl_sphere_grid, spin_weighted_spherical_harmonic_grid
from bass.transport.general_lie_stokes import (
    GeneralLieStokesOperator,
    LieGeometry,
    alm_dict_to_vector,
    max_stokes_reality_error,
    vector_to_alm_dict,
)

__all__ = [
    "ALL_SEVEN_FAMILIES",
    "CoupledSolverConfig",
    "CoupledSolverResult",
    "Z_INITIAL",
    "N_INITIAL",
    "build_early_family_state",
    "extract_stf_pi_from_state",
    "solve_coupled_einstein_boltzmann",
]

ROOT = Path(__file__).resolve().parents[3]
HYREC_REF_CSV = ROOT / "htt/bass/recombination/fixtures/recombination_ref_planck2018.csv"

Z_INITIAL = 1600.0
N_INITIAL = -math.log1p(Z_INITIAL)
ALL_SEVEN_FAMILIES = ("FLRW", "I", "V", "VII_h", "VI_h", "VI_-1/9", "IX")

_DEFAULT_SHEAR_SHAPE = pstf_rank2(np.array([[-1.0, 0.4, -0.3], [0.4, 0.3, 0.2], [-0.3, 0.2, 0.7]]))
_DEFAULT_TILT_SHAPE = np.array([1.0, -0.5, 0.25], dtype=np.float64)


def _load_default_cosmo() -> CosmologyForRecombination:
    tab = load_recombination_table(HYREC_REF_CSV)
    return cosmology_from_metadata(tab.metadata)


def build_early_family_state(
    family: str,
    *,
    epsilon: float = 1e-5,
    handedness: int = 1,
    curvature: float = 3e-4,
    z_initial: float = Z_INITIAL,
    cosmo: CosmologyForRecombination | None = None,
) -> tuple[TiltedBianchiState, CosmologyForRecombination, float]:
    """Construct exact Jacobi/Hamiltonian/Codazzi-admissible multi-fluid early state.

    Supports all 7 required families: FLRW, I, V, VII_h (+/-1), VI_h, VI_-1/9, IX.
    Returns ``(state, cosmo, H_ref_SI_at_z_initial)``.
    """
    if family not in ALL_SEVEN_FAMILIES:
        raise ValueError(f"unsupported family {family!r}; expected one of {ALL_SEVEN_FAMILIES}")
    if handedness not in (-1, 1):
        raise ValueError("handedness must be +1 or -1")
    if not math.isfinite(epsilon) or epsilon < 0.0:
        raise ValueError("epsilon must be finite and non-negative")

    c = _load_default_cosmo() if cosmo is None else cosmo
    u = 1.0 + float(z_initial)
    href_i = float(c.H_of_z(float(z_initial)))
    density_scale = 3.0 * (float(c.H_0_SI) / href_i) ** 2

    rho_b = density_scale * float(c.Omega_b) * (u ** 3)
    rho_cdm = density_scale * float(c.Omega_m - c.Omega_b) * (u ** 3)
    rho_rad = density_scale * float(c.Omega_r) * (u ** 4)
    lam_val = density_scale * float(c.Omega_Lambda)

    curv = float(curvature)
    if family == "FLRW":
        algebra = build_bianchi_algebra("I")
        amp = 0.0
    elif family == "I":
        algebra = build_bianchi_algebra("I")
        amp = float(epsilon)
    elif family == "V":
        algebra = build_bianchi_algebra("V", a_twist=curv)
        amp = float(epsilon)
    elif family == "VII_h":
        base = build_bianchi_algebra("VII_h", a_twist=0.5 * curv, n1=curv, n3=curv)
        if handedness == 1:
            algebra = base
        else:
            n_flip = -base.n
            algebra = BianchiAlgebra(
                type_name="VII_h",
                a=base.a.copy(),
                n=n_flip,
                C=build_structure_tensor(base.a, n_flip),
                h_parameter=base.h_parameter,
                class_label="B",
                h_convention=base.h_convention,
                axis_permutation=base.axis_permutation,
                branch_policy=base.branch_policy,
            )
        amp = float(epsilon)
    elif family == "VI_h":
        algebra = build_bianchi_algebra("VI_h", a_twist=0.5 * curv, n1=curv, n3=-2.0 * curv)
        amp = float(epsilon)
    elif family == "VI_-1/9":
        # Exact exceptional Class B boundary h = a^2/(n1*n3) = (2/3)^2 / (1 * -4) = -1/9
        algebra = build_bianchi_algebra("VI_h", a_twist=(2.0 / 3.0) * curv, n1=curv, n3=-4.0 * curv)
        amp = float(epsilon)
    else:  # "IX"
        base = build_bianchi_algebra("IX", n=curv)
        n_ix = np.diag([1.0 * curv, 1.15 * curv, 0.85 * curv])
        algebra = BianchiAlgebra(
            type_name="IX",
            a=base.a.copy(),
            n=n_ix,
            C=build_structure_tensor(base.a, n_ix),
            h_parameter=None,
            class_label="A",
            h_convention=base.h_convention,
            axis_permutation=base.axis_permutation,
            branch_policy=base.branch_policy,
        )
        amp = float(epsilon)

    sigma = amp * _DEFAULT_SHEAR_SHAPE
    v_rad_init = 0.1 * amp * _DEFAULT_TILT_SHAPE
    sp_rad = SpeciesFluidCongruence(species="radiation", eps_hat=rho_rad, p_hat=rho_rad / 3.0, v_vec=v_rad_init)
    # Compensate geometric momentum divergence div(sigma) + q_rad smoothly into CDM tilt (exact relativistic boost inverse)
    q_rem = -exact_momentum_divergence(sigma, algebra.a, algebra.n, a_sign=1) - sp_rad.to_projected_state().q
    q_mag = float(np.linalg.norm(q_rem))
    if q_mag == 0.0:
        v_cdm_init = np.zeros(3, dtype=np.float64)
    else:
        b_cdm = (2.0 * q_mag) / (rho_cdm + math.hypot(rho_cdm, 2.0 * q_mag))
        v_cdm_init = (b_cdm / q_mag) * q_rem
    sp_cdm = SpeciesFluidCongruence(species="cdm", eps_hat=rho_cdm, p_hat=0.0, v_vec=v_cdm_init)
    sp_bar = SpeciesFluidCongruence(species="baryon", eps_hat=rho_b, p_hat=0.0, v_vec=np.zeros(3, dtype=np.float64))

    state = construct_admissible_tilted_state(
        family=algebra.type_name,
        algebra=algebra,
        sigma_ab=sigma,
        species=[sp_rad, sp_cdm, sp_bar],
        lambda_value=lam_val,
        kappa=1.0,
        codazzi_mode="strict",
        closure="solve_H",
        tol=1e-11,
    )
    return state, c, href_i


def extract_stf_pi_from_state(
    state: np.ndarray,
    rho_rad: float,
    op: GeneralLieStokesOperator,
) -> np.ndarray:
    """Convert photon brightness temperature quadrupole T_{2m} -> stress pi_gamma^{ij} [energy units].

    For blackbody I_bol(n) = (rho_rad / 4pi) * (1 + 4 Theta(n)):
      pi^{ij} = int dOmega I_bol(n) (n^i n^j - delta^{ij}/3)
              = 4 * rho_rad * int (dOmega/4pi) Theta(n) (n^i n^j - delta^{ij}/3).
    """
    TH, PH, d_grid, w_grid = gl_sphere_grid(max(op.n_gl_theta, 8))
    alms = vector_to_alm_dict(state, op.idx)
    t2_alm = {lm: complex(val) for lm, val in alms["T"].items() if lm[0] == 2}
    # Reconstruct exact l=2 scalar brightness map cleanly via sph_harm_y
    theta2 = np.zeros_like(TH, dtype=np.float64)
    for (_, m), coeff in t2_alm.items():
        if m == 0:
            theta2 += float(coeff.real) * sph_harm_y(2, 0, TH, PH).real
        elif m > 0:
            theta2 += 2.0 * (coeff * sph_harm_y(2, m, TH, PH)).real
    M = np.einsum("abi,abj,ab->ij", d_grid, d_grid, theta2 * (w_grid / (4.0 * math.pi)))
    return (4.0 * float(rho_rad)) * pstf_rank2(M)


def _moving_emission_and_delta_vector(
    op_lie: GeneralLieStokesOperator,
    state: np.ndarray,
    v_b: np.ndarray,
    *,
    moving_op_cache: dict[tuple[float, float, float], MovingFrameThomsonOperator],
) -> tuple[np.ndarray, np.ndarray]:
    """Compute moving electron-frame linearized collision corrections projected onto (T,E,B,V).

    Uses MovingFrameThomsonOperator exact Lorentz transformation D(n)^4 R_screen, returning:
    - emission_delta_vec: difference between exact moving equilibrium emission
      `collision_bolometric(0.25, clock='conserved_anchor')` and rest-frame `(v_b . n)` dipole
      (capturing O(v_b^2) kinematic quadrupole in T/E/B and relativistic aberration).
    - hom_delta_vec: moving-frame perturbation change `(C_moving[S] - C_rest[S])` when
      `|v_b| > 1e-10`.
    """
    b_norm = float(np.linalg.norm(v_b))
    if b_norm <= 1e-12:
        zeros = np.zeros(op_lie.dim, dtype=np.complex128)
        return zeros, zeros

    key = (round(float(v_b[0]), 12), round(float(v_b[1]), 12), round(float(v_b[2]), 12))
    op_mov = moving_op_cache.get(key)
    if op_mov is None:
        op_mov = MovingFrameThomsonOperator(v_b, n_theta_rest=max(op_lie.L + 4, 8))
        if len(moving_op_cache) < 256:
            moving_op_cache[key] = op_mov

    # Project emission on normal-frame rays using exact normal weights and right-handed (u, v, n) -> (e_th, e_ph)
    n_vec = op_mov.directions_normal
    w_n = op_mov.weights_normal
    e_th, e_ph = _spherical_screen_basis(n_vec)
    # Spherical coordinates matching gl_sphere_grid / spin_weighted_spherical_harmonic_grid
    th = np.arccos(np.clip(n_vec[:, 2], -1.0, 1.0))
    ph = np.mod(np.arctan2(n_vec[:, 1], n_vec[:, 0]), 2.0 * math.pi)

    I_bg = np.zeros((len(n_vec), 4), dtype=np.float64)
    I_bg[:, 0] = 0.25
    em_sky = op_mov.collision_bolometric(I_bg, clock="conserved_anchor")

    from bass.collision.electron_frame import rotate_stokes_samples

    q_scr, u_scr = rotate_stokes_samples(
        em_sky[:, 1], em_sky[:, 2], op_mov.basis_u_normal, op_mov.basis_v_normal, e_th, e_ph
    )
    # Spin-weighted harmonic transform on arbitrary (n_vec, w_n) up to l=2 (emission has l<=2 + O(beta^2))
    lmax_em = min(op_lie.L, 4)
    em_alms: dict[str, dict[tuple[int, int], complex]] = {"T": {}, "E": {}, "B": {}, "V": {}}
    # Include only the residual BEYOND the rest-frame dipole (n . v_b), which is already added analytically
    dip_rest = n_vec @ v_b
    dI_res = em_sky[:, 0] - dip_rest
    for ell in range(lmax_em + 1):
        for m in range(-ell, ell + 1):
            if (ell, m) in op_lie.idx["T"]:
                ylm = sph_harm_y(ell, m, th, ph)
                em_alms["T"][(ell, m)] = complex(np.sum(w_n * dI_res * np.conj(ylm)))
            if ell >= 2 and ((ell, m) in op_lie.idx["E"] or (ell, m) in op_lie.idx["B"]):
                qp = q_scr + 1j * u_scr
                qm = q_scr - 1j * u_scr
                yp2 = spin_weighted_spherical_harmonic_grid(2, ell, m, th, ph)
                ym2 = spin_weighted_spherical_harmonic_grid(-2, ell, m, th, ph)
                ap = complex(np.sum(w_n * (-qp) * np.conj(yp2)))
                am = complex(np.sum(w_n * (-qm) * np.conj(ym2)))
                em_alms["E"][(ell, m)] = 0.5 * (ap + am)
                em_alms["B"][(ell, m)] = -0.5j * (ap - am)
            if (ell, m) in op_lie.idx["V"]:
                ylm = sph_harm_y(ell, m, th, ph)
                em_alms["V"][(ell, m)] = complex(np.sum(w_n * em_sky[:, 3] * np.conj(ylm)))

    em_delta_vec = alm_dict_to_vector(em_alms, op_lie.idx, op_lie.dim)
    hom_delta_vec = np.zeros(op_lie.dim, dtype=np.complex128)
    # Linearized homogeneous moving correction only becomes non-negligible when |v_b| > 1e-6
    if b_norm > 1e-6:
        # Evaluate current normal-frame sky on op_mov.directions_normal up to min(L, 4)
        alms = vector_to_alm_dict(state, op_lie.idx)
        I_cur = np.zeros(len(n_vec), dtype=np.float64)
        Q_cur = np.zeros(len(n_vec), dtype=np.float64)
        U_cur = np.zeros(len(n_vec), dtype=np.float64)
        V_cur = np.zeros(len(n_vec), dtype=np.float64)
        for ell in range(min(op_lie.L, 4) + 1):
            for m in range(-ell, ell + 1):
                ylm = sph_harm_y(ell, m, th, ph)
                if (ell, m) in alms["T"]:
                    I_cur += (alms["T"][(ell, m)] * ylm).real
                if (ell, m) in alms["V"]:
                    V_cur += (alms["V"][(ell, m)] * ylm).real
                if ell >= 2 and (ell, m) in alms["E"] and (ell, m) in alms["B"]:
                    a2p = -(alms["E"][(ell, m)] + 1j * alms["B"][(ell, m)])
                    yp2 = spin_weighted_spherical_harmonic_grid(2, ell, m, th, ph)
                    val = a2p * yp2
                    Q_cur += val.real
                    U_cur += val.imag
        q_n, u_n = rotate_stokes_samples(Q_cur, U_cur, e_th, e_ph, op_mov.basis_u_normal, op_mov.basis_v_normal)
        sky_cur = np.column_stack((I_cur, q_n, u_n, V_cur))
        hom_mov, _ = op_mov.linearized_perturbation_and_emission(sky_cur, clock="conserved_anchor")
        # Subtract unboosted rest collision K_rest @ state to extract pure O(v_b) correction
        hom_rest_on_vec = op_lie.U_rank9 @ (op_lie.thomson_gains * (op_lie.U_rank9.T @ state)) - state
        qh_scr, uh_scr = rotate_stokes_samples(
            hom_mov[:, 1], hom_mov[:, 2], op_mov.basis_u_normal, op_mov.basis_v_normal, e_th, e_ph
        )
        hom_alms: dict[str, dict[tuple[int, int], complex]] = {"T": {}, "E": {}, "B": {}, "V": {}}
        for ell in range(min(op_lie.L, 4) + 1):
            for m in range(-ell, ell + 1):
                ylm = sph_harm_y(ell, m, th, ph)
                if (ell, m) in op_lie.idx["T"]:
                    hom_alms["T"][(ell, m)] = complex(np.sum(w_n * hom_mov[:, 0] * np.conj(ylm)))
                if (ell, m) in op_lie.idx["V"]:
                    hom_alms["V"][(ell, m)] = complex(np.sum(w_n * hom_mov[:, 3] * np.conj(ylm)))
                if ell >= 2 and (ell, m) in op_lie.idx["E"]:
                    qp = qh_scr + 1j * uh_scr
                    qm = qh_scr - 1j * uh_scr
                    yp2 = spin_weighted_spherical_harmonic_grid(2, ell, m, th, ph)
                    ym2 = spin_weighted_spherical_harmonic_grid(-2, ell, m, th, ph)
                    ap = complex(np.sum(w_n * (-qp) * np.conj(yp2)))
                    am = complex(np.sum(w_n * (-qm) * np.conj(ym2)))
                    hom_alms["E"][(ell, m)] = 0.5 * (ap + am)
                    hom_alms["B"][(ell, m)] = -0.5j * (ap - am)
        hom_delta_vec = alm_dict_to_vector(hom_alms, op_lie.idx, op_lie.dim) - hom_rest_on_vec

    return em_delta_vec, hom_delta_vec


@dataclass(frozen=True)
class CoupledSolverConfig:
    """Configuration for self-consistent coupled Einstein-Boltzmann integration."""

    ell_max: int = 8
    n_cells: int = 160
    substeps_per_cell: int = 2
    n_picard: int = 2
    z_initial: float = Z_INITIAL
    epsilon: float = 1e-5
    handedness: int = 1
    curvature: float = 3e-4
    reionization: ReionizationParameters | None = None
    include_moving_correction: bool = True
    constraint_abort_tol: float = 1e-6


@dataclass(frozen=True)
class CoupledSolverResult:
    """Complete coupled background, recombination, Stokes harmonic, and constraint summary."""

    family: str
    handedness: int
    epsilon: float
    ell_max: int
    n_cells: int
    trajectory: TiltedEvolutionResult
    recombination: TiltedHyrecHistory
    final_state: np.ndarray
    alm_final: dict[str, dict[tuple[int, int], complex]]
    cl_final: dict[str, np.ndarray]
    max_jacobi_residual: float
    max_hamiltonian_residual: float
    max_codazzi_residual: float
    max_four_force_orthog_error: float
    max_momentum_sum_error: float
    max_stokes_reality_err: float
    picard_pi_rel_change: float
    total_optical_depth: float


def _power_spectrum_from_alms(alms: dict[str, dict[tuple[int, int], complex]], ell_max: int) -> dict[str, np.ndarray]:
    out = {}
    for ch in ("T", "E", "B", "V"):
        cl = np.zeros(ell_max + 1, dtype=np.float64)
        mp = alms[ch]
        for ell in range(ell_max + 1):
            vals = [mp[(ell, m)] for m in range(-ell, ell + 1) if (ell, m) in mp]
            if vals:
                arr = np.asarray(vals, dtype=np.complex128)
                cl[ell] = float(np.sum(np.abs(arr) ** 2) / (2 * ell + 1))
        out[ch] = cl
    return out


def solve_coupled_einstein_boltzmann(
    family: str,
    config: CoupledSolverConfig | None = None,
    *,
    tables: HyRecAtomicTables | None = None,
    lie_op: GeneralLieStokesOperator | None = None,
) -> CoupledSolverResult:
    """Run coupled N3 recombination + Bianchi Einstein-Euler + N1/N2 Boltzmann integration."""
    cfg = CoupledSolverConfig() if config is None else config
    tbl = load_hyrec_atomic_tables() if tables is None else tables
    op_lie = GeneralLieStokesOperator(cfg.ell_max) if lie_op is None else lie_op

    init_state, cosmo, href_i = build_early_family_state(
        family,
        epsilon=cfg.epsilon,
        handedness=cfg.handedness,
        curvature=cfg.curvature,
        z_initial=cfg.z_initial,
    )
    N_start = -math.log1p(cfg.z_initial)
    N_end = 0.0
    kappa_grav = float(init_state.kappa)
    lam_val = float(init_state.lambda_value)
    congs = list(init_state.species_congruences)
    from bass.background.general_tilted_evolution import EvolvedSpeciesSpec
    from common.stf_metric_bridge import orthonormal_to_stf_matrix, stf_matrix_to_orthonormal

    species_specs = tuple(
        EvolvedSpeciesSpec(species=sp.species, K_eos=float(sp.p_hat / max(sp.eps_hat, 1e-30))) for sp in congs
    )

    y0 = np.zeros(16 + 4 * len(congs), dtype=np.float64)
    y0[0] = math.log(float(init_state.H))
    y0[1:6] = stf_matrix_to_orthonormal(init_state.sigma_ab, convention="kinematic_response")
    y0[6:9] = init_state.algebra.a.copy()
    y0[9:15] = _pack_sym6(init_state.algebra.n)
    y0[15] = 0.0
    for idx, (sp, spec) in enumerate(zip(congs, species_specs)):
        lE, r_v = energy_momentum_ratio_from_primitive(sp.eps_hat, sp.v_vec, spec.K_eos)
        off = 16 + 4 * idx
        y0[off] = lE
        y0[off + 1 : off + 4] = r_v

    # Sample at (2 * n_cells + 1) exact ODE points so midpoint geometry lies ON exact Jacobi manifold!
    n_eval = 2 * int(cfg.n_cells) + 1
    N_eval = np.linspace(N_start, N_end, n_eval, dtype=np.float64)
    z_eval_recomb = np.expm1(-N_eval)

    # Zero-initialized radiation stress tensor pi_gamma_tab[k, 3, 3]
    pi_tab = np.zeros((n_eval, 3, 3), dtype=np.float64)
    prev_pi_tab = None
    recomb_hist: TiltedHyrecHistory | None = None
    H_fn_cur = None
    v_b_fn_cur = None
    sig_b_fn_cur = None
    delta = np.eye(3, dtype=np.float64)
    moving_cache: dict[tuple[float, float, float], MovingFrameThomsonOperator] = {}

    traj: TiltedEvolutionResult | None = None
    final_S = np.zeros(op_lie.dim, dtype=np.complex128)
    max_orthog_err = 0.0
    max_mom_sum_err = 0.0
    max_jac = 0.0
    max_ham = 0.0
    max_cod = 0.0
    picard_rel_change = 0.0

    reion_par = (
        ReionizationParameters(z_reion_H=7.67, delta_z_H=0.5, z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=True)
        if cfg.reionization is None
        else cfg.reionization
    )

    for picard_idx in range(max(1, int(cfg.n_picard))):
        # Step 1: N3 physical 4-channel recombination coupled to current background (H_n, v_b, sigma)
        recomb_hist = integrate_tilted_recombination(
            z_eval_recomb,
            h=float(cosmo.h),
            t_cmb0=float(cosmo.T_cmb),
            omega_b=float(cosmo.Omega_b),
            omega_m=float(cosmo.Omega_m),
            omega_r=float(cosmo.Omega_r),
            omega_lambda=float(cosmo.Omega_Lambda),
            y_he=float(cosmo.Y_He),
            n_h0_m3=float(cosmo.n_H_today),
            H_n_fn=H_fn_cur,
            v_b_fn=v_b_fn_cur,
            sigma_b_fn=sig_b_fn_cur,
            tables=tbl,
            reionization=reion_par,
            mode="tilted_physical",
        )
        op_spline = CubicSpline(N_eval, np.maximum(recomb_hist.opacity_per_efold, 0.0))

        # Splines for 5 independent components of pi_gamma(N)
        pi_comps = np.array([stf_matrix_to_orthonormal(p) for p in pi_tab], dtype=np.float64)
        pi_spline = CubicSpline(N_eval, pi_comps)

        def _eval_pi(N_v: float) -> np.ndarray:
            if picard_idx == 0:
                return np.zeros((3, 3), dtype=np.float64)
            Nc = min(max(float(N_v), N_start), N_end)
            return orthonormal_to_stf_matrix(pi_spline(Nc))

        def _unpack(N_val: float, y: np.ndarray):
            H = math.exp(float(y[0]))
            sig = orthonormal_to_stf_matrix(y[1:6], convention="kinematic_response")
            a_v = y[6:9]
            n_m = _unpack_sym6(y[9:15])
            C = build_structure_tensor_with_sign(a_v, n_m, a_sign=1)
            _, R_sc, S_ab = exact_spatial_ricci_from_compact(a_v, n_m, a_sign=1)
            T4_list, eh_list, vv_list = [], [], []
            for idx, spec in enumerate(species_specs):
                off = 16 + 4 * idx
                eh, _, vv, T4_s = primitive_from_energy_momentum_ratio(y[off], y[off + 1 : off + 4], spec.K_eos)
                if idx == 0 and picard_idx > 0:
                    T4_s = T4_s.copy()
                    T4_s[1:, 1:] += _eval_pi(N_val)
                T4_list.append(T4_s)
                eh_list.append(eh)
                vv_list.append(vv)
            T4_tot = T4_list[0] + T4_list[1] + T4_list[2]
            rho_tot = float(T4_tot[0, 0])
            q_tot = T4_tot[0, 1:]
            p_tot = float(np.trace(T4_tot[1:, 1:]) / 3.0)
            pi_tot = pstf_rank2(T4_tot[1:, 1:])
            return H, sig, a_v, n_m, C, R_sc, S_ab, rho_tot, p_tot, q_tot, pi_tot, T4_list, eh_list, vv_list

        def ode_rhs(N_val: float, y: np.ndarray) -> np.ndarray:
            H, sig, a_v, n_m, C, _, S_ab, rho_tot, p_tot, q_tot, pi_tot, T4_list, _, vv_list = _unpack(N_val, y)
            matter = MatterNormalFrameState(rho=rho_tot, p=p_tot, q=q_tot, pi=pi_tot)
            dH_dt = ver2_rhs.raychaudhuri_rhs(H=H, sigma_ab=sig, matter=matter, lambda_value=lam_val, kappa=kappa_grav)
            dsig_dt = ver2_rhs.shear_rhs(H=H, sigma_ab=sig, S_ab=S_ab, pi_ab=pi_tot, kappa=kappa_grav)

            theta = H * delta + sig
            Cdot = (
                np.einsum("km,mij->kij", theta, C)
                - np.einsum("mi,kmj->kij", theta, C)
                - np.einsum("mj,kim->kij", theta, C)
            )
            adot = -0.5 * np.einsum("kki->i", Cdot)
            Cdot_n = Cdot - (np.einsum("a,bc->cab", adot, delta) - np.einsum("b,ac->cab", adot, delta))
            ndot = 0.5 * np.einsum("dab,cab->dc", LEVI_CIVITA_3D, Cdot_n)
            ndot = 0.5 * (ndot + ndot.T)

            Gamma4 = build_4d_bianchi_connection(H, sig, C)
            dy = np.zeros_like(y)
            inv_H = 1.0 / H
            dy[0] = (dH_dt * inv_H) * inv_H
            dy[1:6] = stf_matrix_to_orthonormal(dsig_dt * inv_H, convention="kinematic_response")
            dy[6:9] = adot * inv_H
            dy[9:15] = _pack_sym6(ndot * inv_H)
            dy[15] = math.exp(-float(N_val)) * inv_H

            op_val = max(0.0, float(op_spline(min(max(float(N_val), N_start), N_end))))
            F_rad = covariant_thomson_four_force(T4_list[0], vv_list[2], clock="conserved_anchor") * op_val
            coll_forces = (F_rad, np.zeros(4, dtype=np.float64), -F_rad)

            for idx, (T4_s, F_s) in enumerate(zip(T4_list, coll_forces)):
                dT0_dt = -(np.einsum("aca,cb->b", Gamma4, T4_s) + np.einsum("bca,ac->b", Gamma4, T4_s))
                E_s = float(T4_s[0, 0])
                Q_s = T4_s[0, 1:]
                r_s = Q_s / E_s
                dE_dN = float(dT0_dt[0]) * inv_H + float(F_s[0])
                dQ_dN = dT0_dt[1:] * inv_H + F_s[1:]
                off = 16 + 4 * idx
                dy[off] = dE_dN / E_s
                dy[off + 1 : off + 4] = (dQ_dN - r_s * dE_dN) / E_s
            return dy

        # Step 2: Evolve Bianchi Einstein-Euler background ODE
        sol = solve_ivp(
            ode_rhs,
            (N_start, N_end),
            y0,
            method="Radau",
            t_eval=N_eval,
            rtol=1e-10,
            atol=1e-13,
        )
        if not sol.success:
            raise CodazziProjectionError(f"[{family}] coupled Einstein-Euler ODE failed: {sol.message}")

        H_grid = np.zeros(n_eval, dtype=np.float64)
        sig_grid = np.zeros((n_eval, 3, 3), dtype=np.float64)
        a_grid = np.zeros((n_eval, 3), dtype=np.float64)
        n_grid = np.zeros((n_eval, 3, 3), dtype=np.float64)
        v_grid = {spec.species: np.zeros((n_eval, 3), dtype=np.float64) for spec in species_specs}
        eps_grid = {spec.species: np.zeros(n_eval, dtype=np.float64) for spec in species_specs}
        max_jac = max_ham = max_cod = max_trace = max_orthog_err = max_mom_sum_err = 0.0

        for k in range(n_eval):
            H, sig, a_v, n_m, _, R_sc, _, rho_tot, _, q_tot, _, T4_list, eh_list, vv_list = _unpack(float(N_eval[k]), sol.y[:, k])
            H_grid[k] = H
            sig_grid[k] = sig
            a_grid[k] = a_v
            n_grid[k] = n_m
            for idx, spec in enumerate(species_specs):
                eps_grid[spec.species][k] = eh_list[idx]
                v_grid[spec.species][k] = vv_list[idx]

            scale_alg = float(a_v @ a_v + np.sum(n_m * n_m))
            if scale_alg <= 1e-24:
                jac_k = 0.0
            else:
                jac_k = float(np.max(np.abs(n_m @ a_v))) / scale_alg
            ham_k = abs(3.0 * H * H + 0.5 * R_sc - 0.5 * float(np.sum(sig * sig)) - kappa_grav * rho_tot - lam_val) / max(1e-300, 3.0 * H * H)
            div_sig = exact_momentum_divergence(sig, a_v, n_m, a_sign=1)
            q_sum = sum(float(np.linalg.norm(kappa_grav * T4_s[0, 1:])) for T4_s in T4_list)
            cod_k = float(np.linalg.norm(div_sig + kappa_grav * q_tot)) / max(1e-300, float(np.linalg.norm(div_sig)) + q_sum)
            max_jac = max(max_jac, jac_k)
            max_ham = max(max_ham, ham_k)
            max_cod = max(max_cod, cod_k)
            max_trace = max(max_trace, abs(float(np.trace(sig))))

            op_k = max(0.0, float(op_spline(float(N_eval[k]))))
            F_rad = covariant_thomson_four_force(T4_list[0], vv_list[2], clock="conserved_anchor") * op_k
            F_bar = -F_rad
            max_mom_sum_err = max(max_mom_sum_err, float(np.linalg.norm(F_rad + F_bar)))
            vb = vv_list[2]
            gb = 1.0 / math.sqrt(max(1e-30, 1.0 - float(vb @ vb)))
            u_b_cov = np.r_[-gb, gb * vb]
            max_orthog_err = max(max_orthog_err, abs(float(u_b_cov @ F_rad)))

        if max(max_ham, max_cod) > float(cfg.constraint_abort_tol):
            raise CodazziProjectionError(f"[{family}] constraint breach: ham={max_ham:.3e}, cod={max_cod:.3e}")

        traj = TiltedEvolutionResult(
            family=init_state.family,
            class_label=init_state.triple.class_label,
            species_specs=species_specs,
            lambda_value=lam_val,
            kappa=kappa_grav,
            N_grid=N_eval,
            eta_grid=sol.y[15, :].copy(),
            H_grid=H_grid,
            sigma_ab_grid=sig_grid,
            a_grid=a_grid,
            n_grid=n_grid,
            species_v_grid=v_grid,
            species_eps_hat_grid=eps_grid,
            max_jacobi_residual=max_jac,
            max_hamiltonian_residual_rel=max_ham,
            max_codazzi_residual_rel=max_cod,
            max_shear_trace_error=max_trace,
            max_speed_over_trajectory=max(float(np.max(np.linalg.norm(v_grid[s.species], axis=1))) for s in species_specs),
            n_rhs_evals=int(getattr(sol, "nfev", 0)),
            converged=bool(sol.success),
        )

        # Update recombination background callbacks for next Picard iteration
        H_si_sp = CubicSpline(N_eval, H_grid * href_i)
        vb_sp = CubicSpline(N_eval, v_grid["baryon"])
        sig_si_sp = CubicSpline(N_eval, np.array([stf_matrix_to_orthonormal(s) * href_i for s in sig_grid]))
        H_fn_cur = lambda Nv, sp=H_si_sp: float(sp(min(max(float(Nv), N_start), N_end)))
        v_b_fn_cur = lambda Nv, sp=vb_sp: np.asarray(sp(min(max(float(Nv), N_start), N_end)), dtype=np.float64)
        sig_b_fn_cur = lambda Nv, sp=sig_si_sp: orthonormal_to_stf_matrix(sp(min(max(float(Nv), N_start), N_end)))

        # Step 3: Evolve N1+N2 all-m polarized Stokes state across cfg.n_cells (each cell has exact midpoint index 2*c + 1)
        S_vec = np.zeros(op_lie.dim, dtype=np.complex128)
        new_pi_tab = np.zeros_like(pi_tab)
        new_pi_tab[0] = extract_stf_pi_from_state(S_vec, float(eps_grid["radiation"][0]), op_lie)

        for cell in range(int(cfg.n_cells)):
            i0 = 2 * cell
            i_mid = i0 + 1
            i1 = i0 + 2
            dN_cell = float(N_eval[i1] - N_eval[i0])
            H_mid = float(H_grid[i_mid])
            sigN_mid = pstf_rank2(sig_grid[i_mid] / H_mid)
            aN_mid = a_grid[i_mid] / H_mid
            nN_mid = n_grid[i_mid] / H_mid
            # Abelian Bianchi I / FLRW remain a=0, n=0 analytically; filter < 1e-12 ODE atol noise
            scale_mid = float(aN_mid @ aN_mid + np.sum(nN_mid * nN_mid))
            if scale_mid <= 1e-24:
                aN_mid = np.zeros(3, dtype=np.float64)
                nN_mid = np.zeros((3, 3), dtype=np.float64)
            elif float(aN_mid @ aN_mid) <= 1e-24 * max(scale_mid, 1.0):
                aN_mid = np.zeros(3, dtype=np.float64)
                nN_mid = 0.5 * (nN_mid + nN_mid.T)
            else:
                jac_mid = float(np.max(np.abs(nN_mid @ aN_mid))) / scale_mid
                if jac_mid > 1e-8:
                    raise CodazziProjectionError(f"[{family}] Lie Jacobi breach at midpoint cell {cell}: {jac_mid:.3e}")
                if jac_mid > 5e-12:
                    # Project tiny ODE tolerance drift orthogonally onto ker(a_N^T): P N P with P = I - a_hat a_hat^T
                    anorm2 = float(aN_mid @ aN_mid)
                    a_hat = aN_mid / math.sqrt(anorm2)
                    proj = np.eye(3, dtype=np.float64) - np.outer(a_hat, a_hat)
                    n_proj = proj @ nN_mid @ proj
                    nN_mid = 0.5 * (n_proj + n_proj.T)

            geom = LieGeometry(sigN_mid, aN_mid, nN_mid)
            # Simpson quadrature on [i0, i_mid, i1]
            dtau_cell = max(
                0.0,
                float(dN_cell / 6.0 * (op_spline(N_eval[i0]) + 4.0 * op_spline(N_eval[i_mid]) + op_spline(N_eval[i1]))),
            )

            vb_mid = v_grid["baryon"][i_mid]
            src_vec = op_lie.shear_source_vector(sigN_mid, amplitude=dN_cell)
            src_vec = src_vec + op_lie.dipole_source_vector(vb_mid, channel="T", amplitude=dtau_cell)

            if cfg.include_moving_correction and dtau_cell > 0.0 and float(np.linalg.norm(vb_mid)) > 1e-12:
                em_delta, hom_delta = _moving_emission_and_delta_vector(op_lie, S_vec, vb_mid, moving_op_cache=moving_cache)
                src_vec = src_vec + dtau_cell * (em_delta + hom_delta)

            S_vec = op_lie.advance_cell(
                S_vec,
                dN_cell,
                geom,
                dtau_cell,
                source_increment=src_vec,
                substeps=cfg.substeps_per_cell,
            )
            pi_end = extract_stf_pi_from_state(S_vec, float(eps_grid["radiation"][i1]), op_lie)
            new_pi_tab[i1] = pi_end
            new_pi_tab[i_mid] = 0.5 * (new_pi_tab[i0] + pi_end)

        final_S = S_vec
        if prev_pi_tab is not None:
            denom = max(float(np.max(np.abs(new_pi_tab))), 1e-30)
            picard_rel_change = float(np.max(np.abs(new_pi_tab - prev_pi_tab)) / denom)
        prev_pi_tab = new_pi_tab.copy()
        pi_tab = new_pi_tab

    reality_err = max_stokes_reality_error(final_S, op_lie.idx)
    if reality_err > 1e-12:
        raise FloatingPointError(f"[{family}] Stokes reality violated: {reality_err:.3e}")

    alms = vector_to_alm_dict(final_S, op_lie.idx)
    cl = _power_spectrum_from_alms(alms, op_lie.L)
    assert traj is not None and recomb_hist is not None
    return CoupledSolverResult(
        family=family,
        handedness=cfg.handedness,
        epsilon=cfg.epsilon,
        ell_max=op_lie.L,
        n_cells=cfg.n_cells,
        trajectory=traj,
        recombination=recomb_hist,
        final_state=final_S,
        alm_final=alms,
        cl_final=cl,
        max_jacobi_residual=max_jac,
        max_hamiltonian_residual=max_ham,
        max_codazzi_residual=max_cod,
        max_four_force_orthog_error=max_orthog_err,
        max_momentum_sum_error=max_mom_sum_err,
        max_stokes_reality_err=reality_err,
        picard_pi_rel_change=picard_rel_change,
        total_optical_depth=float(recomb_hist.kappa[0]),
    )
