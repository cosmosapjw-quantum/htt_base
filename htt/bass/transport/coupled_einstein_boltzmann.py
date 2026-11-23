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
from bass.collision.moving_thomson import covariant_thomson_four_force
from bass.transport.moving_collision_stage import MovingCollisionStage, initial_radiation_stokes
from bass.recombination.baryon_history import BaryonHistory
from bass.recombination.reionization import CosmologyForRecombination, ReionizationParameters, cosmology_from_metadata
from bass.recombination.recombination_ingest import load_recombination_table
from bass.recombination.tilted_hyrec import (
    HyRecAtomicTables,
    TiltedHyrecHistory,
    integrate_tilted_recombination,
    load_hyrec_atomic_tables,
)
from bass.transport.general_bianchi_transfer import gl_sphere_grid
from bass.transport.general_lie_stokes import (
    GeneralLieStokesOperator,
    LieGeometry,
    max_stokes_reality_error,
    vector_to_alm_dict,
    vector_to_stokes_maps,
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
    massless_neutrino_fraction: float = 0.0,
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

    f_nu = float(massless_neutrino_fraction)
    if not math.isfinite(f_nu) or not 0.0 <= f_nu < 1.0:
        raise ValueError("massless_neutrino_fraction must satisfy 0 <= rho_nu/rho_rad < 1")

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
    # Keep the legacy "radiation" key for the photon hierarchy. Ω_r is fixed;
    # its split has a shared initial velocity and an isotropic rest distribution.
    rho_gamma = (1.0 - f_nu) * rho_rad
    if rho_gamma/3 <= 0.0 or (f_nu and (f_nu*rho_rad)/3 <= 0.0):
        raise ValueError("massless radiation pressure underflows the represented density range")
    sp_rad = SpeciesFluidCongruence(species="radiation", eps_hat=rho_gamma, p_hat=rho_gamma/3, v_vec=v_rad_init)
    sp_nu = ([SpeciesFluidCongruence(species="neutrino", eps_hat=f_nu*rho_rad,
                                    p_hat=f_nu*rho_rad/3, v_vec=v_rad_init)]
             if f_nu else [])
    # Compensate geometric momentum divergence div(sigma) + q_rad smoothly into CDM tilt (exact relativistic boost inverse)
    q_rem = -exact_momentum_divergence(sigma, algebra.a, algebra.n, a_sign=1) - sum(sp.to_projected_state().q for sp in (sp_rad, *sp_nu))
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
        species=[sp_rad, sp_cdm, sp_bar, *sp_nu],
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
    massless_neutrino_fraction: float = 0.0
    # Store per-cell sky/fluid moment ratios and constraint residuals (diagnostic only).
    record_history: bool = False
    # R104: evaluate the moving-Thomson frame at SDIRK stage times (False keeps the
    # R103 cell-midpoint frozen baryon velocity for A/B diagnostics only).
    stage_velocity_collision: bool = True
    # R105: cap scalar conserved-anchor depth per scattering substep.
    max_substep_depth: float | None = 1.0
    # R106: evaluate the Thomson rate at the same SDIRK stage times as the electron
    # velocity (False keeps the R105 substep-average rate for A/B diagnostics only).
    stage_rate_collision: bool = True
    # R106: bisect photon substeps while |Delta ln(opacity rate)| exceeds this bound
    # (stage-rate path only; None disables).
    max_substep_log_rate: float | None = 0.25
    # R106: n_picard is the minimum sweep count; continue up to max_picard until the
    # largest per-node relative change of the radiation STF stress fed to the fluid
    # is <= picard_rtol (None restores exactly n_picard sweeps). A globally normalised
    # change hides unconverged late-time class-B stress.
    picard_rtol: float | None = 1e-6
    max_picard: int = 12


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
    neutrino_final_state: np.ndarray | None = None
    history: dict | None = None
    picard_iterations_used: int = 0
    picard_pi_local_rel_change: float = float("nan")


def sky_energy_momentum_ratios(state: np.ndarray, op: GeneralLieStokesOperator) -> np.ndarray:
    """Return the normal-frame radiation tensor T^{mu nu}/T^{00} carried by a Stokes state.

    The bolometric intensity on the outward sky is proportional to ``1 + 4 Theta(n)``
    and photon momentum points along ``-n``. Gauss-Legendre quadrature with
    ``n_gl_theta >= L + 4`` integrates these ell <= 2 moments exactly.
    """
    sky = vector_to_stokes_maps(np.asarray(state), op.idx, L=op.L, n_gl_theta=op.n_gl_theta)
    n = op._grid[2].reshape(-1, 3)
    weight = op._grid[3].ravel() * (1.0 + 4.0 * sky[..., 0].ravel())
    k4 = np.column_stack([np.ones(len(n)), -n])
    tensor = np.einsum("n,ni,nj->ij", weight, k4, k4)
    if not math.isfinite(tensor[0, 0]) or tensor[0, 0] <= 0.0:
        raise FloatingPointError("nonpositive sky radiation energy")
    return tensor / tensor[0, 0]


def _optical_substeps(opacity, start, stop, min_steps, max_depth, max_log_rate=None):
    """Refine physical-time intervals until their integrated scalar depth is bounded.

    Equal-N bisections retain the time midpoint and integrate each PCHIP piece
    exactly. The returned N edges and depths describe the same intervals.
    ``max_log_rate`` additionally bisects an interval while the anchor opacity rate
    changes by more than that bound in |ln r| between its ends (R106). Stage-time
    collision rates leave a tau_sub^2 * Delta(ln r) damping error that the depth
    cap alone does not control in visibility and transparent cells.
    """
    if isinstance(min_steps, (bool, np.bool_)) or not isinstance(min_steps,(int, np.integer)) or min_steps < 1:
        raise ValueError("min_steps must be a positive integer")
    if max_depth is not None and (not max_depth > 0 or not np.isfinite(max_depth)):
        raise ValueError("max_substep_depth must be finite and positive")
    if max_log_rate is not None and (not max_log_rate > 0 or not np.isfinite(max_log_rate)):
        raise ValueError("max_substep_log_rate must be finite and positive")
    edges = np.linspace(start,stop,min_steps+1)
    tol = 1.0 + 8*np.finfo(float).eps
    while True:
        dtau = opacity.cells(edges).delta_tau
        split = np.zeros(len(dtau), dtype=bool)
        if max_depth is not None:
            split |= dtau > max_depth*tol
        if max_log_rate is not None:
            rate = np.asarray(opacity.rate(edges), dtype=float)
            ra, rb = rate[:-1], rate[1:]
            both = (ra > 0.0) & (rb > 0.0)
            change = np.zeros(len(dtau))
            change[both] = np.abs(np.log(rb[both]/ra[both]))
            split |= both & (change > max_log_rate*tol)
        if not np.any(split):
            return (edges-start)/(stop-start), dtau
        lo, hi = edges[:-1][split], edges[1:][split]
        mid = lo + (hi-lo)/2
        if np.any(mid==lo) or np.any(mid==hi):
            raise FloatingPointError("optical resolution exceeds floating-point time resolution")
        edges = np.sort(np.r_[edges, mid])


def _stage_opacity_rate(opacity, n0, n_stop):
    """Anchor optical depth per unit cell coordinate u in [0, 1] for one e-fold cell.

    u = (N - n0)/(n_stop - n0), so d tau/du = (n_stop - n0) * d tau/dN with the same
    PCHIP rate that drives the fluid Thomson force. Stage abscissae are clamped to
    the cell, which absorbs the one-ulp overshoot of edges[j] + 1.0*h.
    """
    n0, n_stop = float(n0), float(n_stop)
    if not n_stop > n0:
        raise ValueError("cell must have positive e-fold width")
    dn = n_stop - n0

    def rate_at(u):
        return dn * float(opacity.rate(min(max(n0 + u * dn, n0), n_stop)))

    return rate_at


def _advance_moving_photon_cell(op, state, delta_N, geometry, shear_source, sub_depths,
                                baryon_velocity_at, *, sub_edges=None, opacity_rate_at=None):
    """SDIRK(2,2) photon cell with the electron velocity evaluated at each stage time.

    The source and Lie operator are expressed per unit cell coordinate u. Substep
    j spans [a,b] in that coordinate, carries its exact integrated anchor optical
    depth and uses the electron velocity at a+gamma*(b-a) and at b. The second
    stage is the step result. Omitted edges use a uniform time partition.

    Without ``opacity_rate_at`` both stages use the substep-average rate depth/h
    (R105). With ``opacity_rate_at(u)`` (anchor depth per unit u) the stages sample
    the rate at the same abscissae as the electron velocity and the pair is then
    rescaled so the SDIRK node quadrature h[(1-gamma) r1 + gamma r2] equals the exact
    substep depth (R106). Both forms are second order in the depth cap; on a
    tight-coupling ramp the stage-time shape lowers the error constant by roughly
    30x, and the rescaling keeps the applied depth exact in visibility and
    transparent cells. For a constant rate the two forms are identical.
    """
    gamma = 1.0 - 1.0 / math.sqrt(2.0)
    edges = np.linspace(0.,1.,len(sub_depths)+1) if sub_edges is None else np.asarray(sub_edges,dtype=float)
    if (edges.shape != (len(sub_depths)+1,) or edges[0] != 0. or edges[-1] != 1.
        or not np.isfinite(edges).all() or np.any(np.diff(edges) <= 0)):
        raise ValueError("sub_edges must cover [0,1] in increasing order and match sub_depths")
    m_total = delta_N * (op.base_operator(geometry) + op.bolometric_redshift_operator(geometry))
    y = np.array(state, dtype=np.complex128, copy=True)
    for j, depth in enumerate(sub_depths):
        h = edges[j+1]-edges[j]
        if opacity_rate_at is None:
            stage_rates = (float(depth) / h,) * 2
        else:
            stage_rates = tuple(float(opacity_rate_at(edges[j] + c * h)) for c in (gamma, 1.0))
            if not all(math.isfinite(r) and r >= 0.0 for r in stage_rates):
                raise ValueError("stage opacity rates must be finite and nonnegative")
            quad = h * ((1.0 - gamma) * stage_rates[0] + gamma * stage_rates[1])
            if quad > 0.0:
                stage_rates = tuple(r * float(depth) / quad for r in stage_rates)
            else:
                stage_rates = (float(depth) / h,) * 2
        stages = []
        for c, rate in zip((gamma, 1.0), stage_rates):
            v = np.asarray(baryon_velocity_at(edges[j] + c * h), dtype=np.float64)
            inc = gamma * h * shear_source
            if rate > 0.0 and np.any(v):
                moving = MovingCollisionStage(op, v)
                solve = moving.factor_sdirk_stage(m_total, gamma * h, rate)
                inc = inc + gamma * h * rate * moving.emission
            else:
                solve = op.factor_sdirk_stage(m_total, gamma * h, rate)
            stages.append((solve, inc))
        (solve1, inc1), (solve2, inc2) = stages
        y1 = solve1(y + inc1)
        y = solve2(y + ((1.0 - gamma) / gamma) * (y1 - y) + inc2)
    if not np.all(np.isfinite(y)):
        raise FloatingPointError("moving photon cell produced a non-finite state")
    return y


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


def _species_thomson_forces(photon_tensor, baryon_velocity, rate, count, photon_idx, baryon_idx):
    """In a common normal tetrad the only Thomson four-force pair is gamma-b."""
    forces = np.zeros((count, 4))
    forces[photon_idx] = rate * covariant_thomson_four_force(
        photon_tensor, baryon_velocity, clock="conserved_anchor")
    forces[baryon_idx] = -forces[photon_idx]
    return forces


def _stress_feedback_ratio(state, op, flux_ratio, velocity):
    """Additional STF pressure divided by the current normal energy density."""
    zero_mode = op.idx["T"].get((0, 0))
    monopole = state[zero_mode].real / math.sqrt(4*math.pi) if zero_mode is not None else 0.
    mean_intensity = 1.0 + 4.0*monopole
    if not math.isfinite(mean_intensity) or mean_intensity <= 0.0:
        raise FloatingPointError("nonpositive mean radiation intensity in stress feedback")
    pi_over_energy = extract_stf_pi_from_state(state, 1./mean_intensity, op)
    return pi_over_energy - pstf_rank2(np.outer(velocity, flux_ratio))


def solve_coupled_einstein_boltzmann(
    family: str,
    config: CoupledSolverConfig | None = None,
    *,
    tables: HyRecAtomicTables | None = None,
    lie_op: GeneralLieStokesOperator | None = None,
) -> CoupledSolverResult:
    """Run coupled N3 recombination + Bianchi Einstein-Euler + N1/N2 Boltzmann integration."""
    cfg = CoupledSolverConfig() if config is None else config
    if cfg.stage_rate_collision and cfg.include_moving_correction and cfg.max_substep_depth is None:
        # Unequal stage rates lose the L-stable damping bound unless the depth is capped.
        raise ValueError("stage_rate_collision requires a finite max_substep_depth")
    tbl = load_hyrec_atomic_tables() if tables is None else tables
    op_lie = GeneralLieStokesOperator(cfg.ell_max) if lie_op is None else lie_op

    init_state, cosmo, href_i = build_early_family_state(
        family,
        epsilon=cfg.epsilon,
        handedness=cfg.handedness,
        curvature=cfg.curvature,
        z_initial=cfg.z_initial,
        massless_neutrino_fraction=cfg.massless_neutrino_fraction,
    )
    N_start = -math.log1p(cfg.z_initial)
    N_end = 0.0
    kappa_grav = float(init_state.kappa)
    lam_val = float(init_state.lambda_value)
    congs = list(init_state.species_congruences)
    from bass.background.general_tilted_evolution import EvolvedSpeciesSpec
    from common.stf_metric_bridge import orthonormal_to_stf_matrix, stf_matrix_to_orthonormal

    species_specs = tuple(
        EvolvedSpeciesSpec(species=sp.species, K_eos=1/3 if sp.species in ("radiation", "neutrino") else 0.)
        for sp in congs
    )

    photon_idx = next(i for i, spec in enumerate(species_specs) if spec.species == "radiation")
    baryon_idx = next(i for i, spec in enumerate(species_specs) if spec.species == "baryon")
    radiation_indices = tuple(i for i, spec in enumerate(species_specs)
                              if spec.species in ("radiation", "neutrino"))
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

    initial_stokes = initial_radiation_stokes(op_lie, congs[photon_idx].v_vec)

    # Sample at (2 * n_cells + 1) exact ODE points so midpoint geometry lies ON exact Jacobi manifold!
    n_eval = 2 * int(cfg.n_cells) + 1
    N_eval = np.linspace(N_start, N_end, n_eval, dtype=np.float64)
    z_eval_recomb = np.expm1(-N_eval)

    # Zero-initialized radiation stress tensor pi_gamma_tab[k, 3, 3]
    pi_tab = np.zeros((len(radiation_indices), n_eval, 3, 3), dtype=np.float64)
    prev_pi_tab = None
    recomb_hist: TiltedHyrecHistory | None = None
    baryon_history = None
    delta = np.eye(3, dtype=np.float64)

    traj: TiltedEvolutionResult | None = None
    final_S = np.zeros(op_lie.dim, dtype=np.complex128)
    neutrino_final = None
    max_orthog_err = 0.0
    max_mom_sum_err = 0.0
    max_jac = 0.0
    max_ham = 0.0
    max_cod = 0.0
    picard_rel_change = 0.0
    history_iterations: list[dict] = []

    reion_par = (
        ReionizationParameters(z_reion_H=7.67, delta_z_H=0.5, z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=True)
        if cfg.reionization is None
        else cfg.reionization
    )

    n_picard_min = max(1, int(cfg.n_picard))
    if cfg.picard_rtol is not None and not (math.isfinite(cfg.picard_rtol) and cfg.picard_rtol > 0):
        raise ValueError("picard_rtol must be finite and positive")
    n_picard_max = n_picard_min if cfg.picard_rtol is None else max(n_picard_min, int(cfg.max_picard))
    picard_local_change = float("nan")
    picard_used = 0
    prev_ratio_tab = None
    for picard_idx in range(n_picard_max):
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
            H_n_fn=baryon_history.H if baryon_history else None,
            v_b_fn=baryon_history.beta if baryon_history else None,
            sigma_b_fn=baryon_history.shear if baryon_history else None,
            theta_b_fn=baryon_history.theta if baryon_history else None,
            hydrogen_factor_fn=baryon_history.hydrogen_factor if baryon_history else None,
            acceleration_b_over_c_fn=baryon_history.acceleration if baryon_history else None,
            tables=tbl,
            reionization=reion_par,
            mode="tilted_physical",
        )
        opacity = recomb_hist.opacity_history()
        cell_depths = opacity.cells(N_eval[::2]).delta_tau

        # Each massless component supplies its own correction to boosted-fluid
        # STF pressure, in the same normal frame as the conserved E and q.
        pi_splines = {}
        if picard_idx:
            for slot, species_idx in enumerate(radiation_indices):
                coeff = np.array([stf_matrix_to_orthonormal(p) for p in pi_tab[slot]])
                pi_splines[species_idx] = CubicSpline(N_eval, coeff)

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
                if T4_s[0, 0] <= 0.0:
                    raise FloatingPointError(f"{spec.species} normal energy underflow at N={N_val}")
                if idx in pi_splines:
                    T4_s = T4_s.copy()
                    T4_s[1:, 1:] += T4_s[0, 0] * orthonormal_to_stf_matrix(pi_splines[idx](N_val))
                T4_list.append(T4_s)
                eh_list.append(eh)
                vv_list.append(vv)
            T4_tot = sum(T4_list)
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

            op_val = float(opacity.rate(min(max(float(N_val), N_start), N_end)))
            coll_forces = _species_thomson_forces(T4_list[photon_idx], vv_list[baryon_idx], op_val,
                                                  len(species_specs), photon_idx, baryon_idx)

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
            dense_output=True,
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
        ham_grid = np.zeros(n_eval, dtype=np.float64)
        cod_grid = np.zeros(n_eval, dtype=np.float64)

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
            ham_grid[k] = ham_k
            cod_grid[k] = cod_k
            max_jac = max(max_jac, jac_k)
            max_ham = max(max_ham, ham_k)
            max_cod = max(max_cod, cod_k)
            max_trace = max(max_trace, abs(float(np.trace(sig))))

            op_k = float(recomb_hist.opacity_per_efold[k])
            force_grid = _species_thomson_forces(T4_list[photon_idx], vv_list[baryon_idx], op_k,
                                                len(species_specs), photon_idx, baryon_idx)
            F_rad, F_bar = force_grid[photon_idx], force_grid[baryon_idx]
            max_mom_sum_err = max(max_mom_sum_err, float(np.linalg.norm(F_rad + F_bar)))
            vb = vv_list[baryon_idx]
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
        if picard_idx + 1 < n_picard_max:
            baryon_history = BaryonHistory(N_eval, H_grid*href_i, sig_grid*href_i,
                                          a_grid*href_i, n_grid*href_i, v_grid["baryon"])

        # Step 3: Evolve N1+N2 all-m polarized Stokes state across cfg.n_cells (each cell has exact midpoint index 2*c + 1)
        # Initial normalized brightness is identical for common-velocity
        # thermal massless populations, independent of the absolute density.
        S_vec = initial_stokes.copy()
        nu_vec = initial_stokes.copy() if len(radiation_indices) == 2 else None
        # The boosted perfect-fluid pressure already contains STF(v_i q_j).
        # The prescribed IC matches that stress, so its initial correction is zero.
        new_pi_tab = np.zeros_like(pi_tab)
        stress_scale_tab = np.zeros(pi_tab.shape[:2])
        if cfg.record_history:
            n_rad, n_c = len(radiation_indices), int(cfg.n_cells)
            record = {
                "N_end": N_eval[2::2].copy(),
                "delta_tau": np.asarray(cell_depths[:n_c], dtype=np.float64).copy(),
                "photon_substeps": np.full(n_c,cfg.substeps_per_cell,dtype=int),
                "hamiltonian": ham_grid[2::2].copy(),
                "codazzi": cod_grid[2::2].copy(),
                "q_over_E_sky": np.zeros((n_rad, n_c, 3)),
                "q_over_E_fluid": np.zeros((n_rad, n_c, 3)),
                "pi_over_E_sky": np.zeros((n_rad, n_c, 3, 3)),
                "pi_over_E_fluid": np.zeros((n_rad, n_c, 3, 3)),
                "thomson_force_over_E_fluid": np.zeros((n_c, 4)),
                "thomson_force_over_E_sky": np.zeros((n_c, 4)),
            }

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
            dtau_cell = float(cell_depths[cell])

            vb_mid = v_grid["baryon"][i_mid]
            src_vec = op_lie.shear_source_vector(sigN_mid, amplitude=dN_cell)
            if nu_vec is not None:
                # The collisionless species receives gravitational brightness
                # forcing only; it has no polarization and no electron opacity.
                nu_vec = op_lie.advance_cell(nu_vec, dN_cell, geom, 0.0,
                                             source_increment=src_vec, substeps=cfg.substeps_per_cell,
                                             bolometric_redshift=True)
            if cfg.include_moving_correction and dtau_cell > 0.0 and cfg.stage_velocity_collision:
                # The baryon frame relaxes on the Thomson time inside opaque cells;
                # sample it from the dense Einstein-Euler solution at each stage.
                n0 = float(N_eval[i0])
                b_off = 16 + 4 * baryon_idx

                def _baryon_velocity_at(u, n0=n0, dn=dN_cell, b_off=b_off):
                    y_u = sol.sol(n0 + u * dn)
                    return primitive_from_energy_momentum_ratio(y_u[b_off], y_u[b_off + 1:b_off + 4], 0.0)[2]

                u_edges, sub_depths = _optical_substeps(
                    opacity, n0, float(N_eval[i1]), cfg.substeps_per_cell, cfg.max_substep_depth,
                    cfg.max_substep_log_rate if cfg.stage_rate_collision else None)
                S_vec = _advance_moving_photon_cell(
                    op_lie, S_vec, dN_cell, geom, src_vec, sub_depths, _baryon_velocity_at,
                    sub_edges=u_edges,
                    opacity_rate_at=(_stage_opacity_rate(opacity, n0, float(N_eval[i1]))
                                     if cfg.stage_rate_collision else None))
                if cfg.record_history:
                    record["photon_substeps"][cell] = len(sub_depths)
            else:
                moving = None
                if dtau_cell > 0.0 and np.any(vb_mid):
                    if cfg.include_moving_correction:
                        moving = MovingCollisionStage(op_lie, vb_mid)
                        src_vec += dtau_cell * moving.emission
                    else:
                        # Outward sky direction n is opposite photon momentum p in the Lie operator.
                        src_vec += op_lie.dipole_source_vector(-vb_mid, channel="T", amplitude=dtau_cell)
                S_vec = op_lie.advance_cell(
                    S_vec,
                    dN_cell,
                    geom,
                    dtau_cell,
                    source_increment=src_vec,
                    substeps=cfg.substeps_per_cell,
                    moving_collision=moving,
                    bolometric_redshift=True,
                )
            for slot, species_idx in enumerate(radiation_indices):
                spec_key = species_specs[species_idx].species
                angular_state = S_vec if species_idx == photon_idx else nu_vec
                offset = 16 + 4*species_idx
                new_pi_tab[slot, i1] = _stress_feedback_ratio(
                    angular_state, op_lie, sol.y[offset+1:offset+4, i1], v_grid[spec_key][i1])
                new_pi_tab[slot, i_mid] = .5*(new_pi_tab[slot, i0] + new_pi_tab[slot, i1])
                boosted = pstf_rank2(np.outer(v_grid[spec_key][i1], sol.y[offset+1:offset+4, i1]))
                stress_scale_tab[slot, i1] = float(np.linalg.norm(new_pi_tab[slot, i1] + boosted))
            if cfg.record_history:
                T4_end = _unpack(float(N_eval[i1]), sol.y[:, i1])[11]
                for slot, species_idx in enumerate(radiation_indices):
                    angular_state = S_vec if species_idx == photon_idx else nu_vec
                    sky_t = sky_energy_momentum_ratios(angular_state, op_lie)
                    fluid_t = T4_end[species_idx] / T4_end[species_idx][0, 0]
                    record["q_over_E_sky"][slot, cell] = sky_t[0, 1:]
                    record["q_over_E_fluid"][slot, cell] = fluid_t[0, 1:]
                    record["pi_over_E_sky"][slot, cell] = pstf_rank2(sky_t[1:, 1:])
                    record["pi_over_E_fluid"][slot, cell] = pstf_rank2(fluid_t[1:, 1:])
                    if species_idx == photon_idx:
                        rate = float(recomb_hist.opacity_per_efold[i1])
                        vb_end = v_grid["baryon"][i1]
                        record["thomson_force_over_E_fluid"][cell] = rate * covariant_thomson_four_force(
                            fluid_t, vb_end, clock="conserved_anchor")
                        record["thomson_force_over_E_sky"][cell] = rate * covariant_thomson_four_force(
                            sky_t, vb_end, clock="conserved_anchor")

        if cfg.record_history:
            history_iterations.append(record)
        neutrino_final = nu_vec
        final_S = S_vec
        # Interpolate the slowly varying pi/E, then restore the dimensional
        # pressure using the current stage energy. Preserve the historical
        # Picard error definition in units of dimensional normal pressure.
        energy_history = np.exp(sol.y[[16+4*i for i in radiation_indices]])
        physical_pi = energy_history[:, :, None, None] * new_pi_tab
        if prev_pi_tab is not None:
            denom = max(float(np.max(np.abs(physical_pi))), 1e-30)
            picard_rel_change = float(np.max(np.abs(physical_pi - prev_pi_tab)) / denom)
        prev_pi_tab = physical_pi
        if prev_ratio_tab is not None:
            ends = slice(2, None, 2)
            change = np.linalg.norm((new_pi_tab - prev_ratio_tab)[:, ends].reshape(len(radiation_indices), -1, 9), axis=2)
            scale = stress_scale_tab[:, ends]
            ratio = np.divide(change, scale, out=np.where(change > 0, np.inf, 0.0), where=scale > 0)
            picard_local_change = float(np.max(ratio)) if ratio.size else 0.0
        prev_ratio_tab = new_pi_tab.copy()
        pi_tab = new_pi_tab
        picard_used = picard_idx + 1
        if (cfg.picard_rtol is not None and picard_used >= n_picard_min and picard_idx > 0
                and picard_local_change <= cfg.picard_rtol):
            break

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
        picard_iterations_used=picard_used,
        picard_pi_local_rel_change=picard_local_change,
        total_optical_depth=float(recomb_hist.kappa[0]),
        neutrino_final_state=neutrino_final,
        history=({"radiation_species": [species_specs[i].species for i in radiation_indices],
                  "picard_iterations": history_iterations} if cfg.record_history else None),
    )
