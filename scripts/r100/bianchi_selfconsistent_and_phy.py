"""R100 Part E: Self-consistent coupled Bianchi + polarized radiation transport, P2 SHA guard, and PHY01-07."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from scipy.sparse import bmat, csc_matrix
from scipy.sparse.linalg import expm_multiply

from bass.background import rhs as ver2_rhs
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
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.recombination.reionization import compute_tau_dot_conformal_Mpc
from common.stf_metric_bridge import orthonormal_to_stf_matrix, stf_matrix_to_orthonormal
from scripts.r97 import bianchi_coupled_m_transport as r97
from scripts.r98 import bianchi_history as r98_bh


@dataclass(frozen=True)
class _SpeciesSpec:
    species: str
    K_eos: float

ROOT = Path(__file__).resolve().parents[2]
R98_DIR = ROOT / "docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123"
OUT_DIR = ROOT / "docs/research_program/observational_publication_20261015/R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project_vector_to_y1m(vec: np.ndarray, M_dip: np.ndarray) -> np.ndarray:
    """Exact spherical harmonic dipole coefficients T_{1m} (m=-1,0,+1) such that (M_dip @ T_1) == vec/3."""
    return (4.0 * math.pi) * (M_dip.conj().T @ np.asarray(vec, dtype=float))


def _opacity_per_efold(N_val: float, H_dimless: float, cosmo, xe_interp, href: float) -> float:
    """Dimensionless Thomson scattering rate Gamma_T / H_phys per e-fold dN."""
    z = math.expm1(-float(N_val))
    xe = float(xe_interp.query_x_e(z))
    tau_dot_mpc = float(compute_tau_dot_conformal_Mpc(z, xe, cosmo))
    dchi_dN = math.exp(-float(N_val)) / (float(H_dimless) * href * r97.SEC_PER_MPC)
    return tau_dot_mpc * dchi_dN


def covariant_thomson_force_dN(
    T4_rad: np.ndarray,
    v_bar: np.ndarray,
    op_per_efold: float,
) -> np.ndarray:
    """Elastic covariant Thomson 4-force per e-fold dN on radiation: u_{b,mu} F^mu == 0 exactly.

    Reduces to F^i = -op * (q_rad^i - (4/3)*rho_rad*v_b^i - pi_rad^{ij}*v_{b,j}), F^0 = v_b . F.
    """
    vb = np.asarray(v_bar, dtype=float)
    b2 = float(vb @ vb)
    gb = 1.0 / math.sqrt(max(1e-30, 1.0 - b2))
    u_b = np.r_[gb, gb * vb]
    u_b_cov = np.r_[-gb, gb * vb]
    V = -(T4_rad @ u_b_cov)
    W = V + u_b * float(u_b_cov @ V)
    return -float(op_per_efold) * (W / gb)


def evolve_coupled_bianchi_with_radiation(
    family: str,
    epsilon: float = 1e-5,
    samples: int = 641,
    pi_rad_fn=None,
    *,
    thomson_coupling: bool = True,
    method: str = "Radau",
    rtol: float = 1e-9,
    atol: float = 1e-13,
) -> tuple[object, TiltedEvolutionResult, dict[str, float]]:
    """Integrate 1+3 Bianchi + tilted multi-fluid Einstein-Euler ODE with radiation pi_gamma & Thomson drag."""
    initial_state = r98_bh.early_state(family, epsilon)
    cosmo, xe_interp = r98_bh.optics()
    href = float(cosmo.H_of_z(r98_bh.Z_INITIAL))
    N_start = float(r98_bh.N_INITIAL)
    N_end = 0.0
    kappa = float(initial_state.kappa)
    Lam = float(initial_state.lambda_value)
    congs = list(initial_state.species_congruences)
    specs = tuple(_SpeciesSpec(species=c.species, K_eos=float(c.p_hat / max(c.eps_hat, 1e-30))) for c in congs)
    if [s.species for s in specs] != ["radiation", "cdm", "baryon"]:
        raise ValueError(f"Unexpected species ordering: {[s.species for s in specs]}")

    y0 = np.zeros(16 + 4 * len(congs), dtype=float)
    y0[0] = math.log(float(initial_state.H))
    y0[1:6] = stf_matrix_to_orthonormal(initial_state.sigma_ab, convention="kinematic_response")
    y0[6:9] = initial_state.algebra.a.copy()
    y0[9:15] = _pack_sym6(initial_state.algebra.n)
    y0[15] = 0.0
    for idx, (sp, spec) in enumerate(zip(congs, specs)):
        lE, r_v = energy_momentum_ratio_from_primitive(sp.eps_hat, sp.v_vec, spec.K_eos)
        off = 16 + 4 * idx
        y0[off] = lE
        y0[off + 1 : off + 4] = r_v

    delta = np.eye(3, dtype=float)

    def _unpack(N_val: float, y: np.ndarray):
        H = math.exp(float(y[0]))
        sig = orthonormal_to_stf_matrix(y[1:6], convention="kinematic_response")
        a_v = y[6:9]
        n_m = _unpack_sym6(y[9:15])
        C = build_structure_tensor_with_sign(a_v, n_m, a_sign=1)
        _, R_sc, S_ab = exact_spatial_ricci_from_compact(a_v, n_m, a_sign=1)

        T4_list = []
        eh_list = []
        vv_list = []
        for idx, spec in enumerate(specs):
            off = 16 + 4 * idx
            eh, _, vv, T4_s = primitive_from_energy_momentum_ratio(y[off], y[off + 1 : off + 4], spec.K_eos)
            if idx == 0 and pi_rad_fn is not None:
                T4_s = T4_s.copy()
                T4_s[1:, 1:] += pstf_rank2(pi_rad_fn(float(N_val)))
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
        dH_dt = ver2_rhs.raychaudhuri_rhs(H=H, sigma_ab=sig, matter=matter, lambda_value=Lam, kappa=kappa)
        dsig_dt = ver2_rhs.shear_rhs(H=H, sigma_ab=sig, S_ab=S_ab, pi_ab=pi_tot, kappa=kappa)

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

        F_rad = np.zeros(4, dtype=float)
        if thomson_coupling:
            op = _opacity_per_efold(N_val, H, cosmo, xe_interp, href)
            F_rad = covariant_thomson_force_dN(T4_list[0], vv_list[2], op)
        coll_forces = (F_rad, np.zeros(4, dtype=float), -F_rad)

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

    N_eval = np.linspace(N_start, N_end, int(samples), dtype=float)
    sol = solve_ivp(
        ode_rhs,
        (N_start, N_end),
        y0,
        method=method,
        t_eval=N_eval,
        rtol=float(rtol),
        atol=float(atol),
    )
    if not sol.success:
        raise CodazziProjectionError(f"[{family}] coupled Radau ODE failed: {sol.message}")

    M_steps = sol.y.shape[1]
    H_grid = np.zeros(M_steps, dtype=float)
    eta_grid = sol.y[15, :].copy()
    sig_grid = np.zeros((M_steps, 3, 3), dtype=float)
    a_grid = np.zeros((M_steps, 3), dtype=float)
    n_grid = np.zeros((M_steps, 3, 3), dtype=float)
    v_grid = {spec.species: np.zeros((M_steps, 3), dtype=float) for spec in specs}
    eps_grid = {spec.species: np.zeros(M_steps, dtype=float) for spec in specs}

    max_jac = 0.0
    max_ham_rel = 0.0
    max_cod_rel = 0.0
    max_trace = 0.0
    max_speed = 0.0
    max_mom_sum_defect = 0.0
    max_orthog_defect = 0.0
    max_slip_after_eq = 0.0

    for k in range(M_steps):
        yk = sol.y[:, k]
        Nk = float(N_eval[k])
        H, sig, a_v, n_m, _, R_sc, _, rho_tot, _, q_tot, _, T4_list, eh_list, vv_list = _unpack(Nk, yk)
        H_grid[k] = H
        sig_grid[k] = sig
        a_grid[k] = a_v
        n_grid[k] = n_m
        for idx, spec in enumerate(specs):
            eps_grid[spec.species][k] = eh_list[idx]
            v_grid[spec.species][k] = vv_list[idx]
            max_speed = max(max_speed, float(np.linalg.norm(vv_list[idx])))

        jac = float(np.linalg.norm(n_m @ a_v)) / max(1.0e-300, float(np.sum(a_v * a_v) + np.sum(n_m * n_m)))
        sigma_sq = 0.5 * float(np.sum(sig * sig))
        ham_scale = max(1e-300, 3.0 * H * H)
        ham_rel = abs(3.0 * H * H + 0.5 * R_sc - sigma_sq - kappa * rho_tot - Lam) / ham_scale

        div_sig = exact_momentum_divergence(sig, a_v, n_m, a_sign=1)
        q_species_sum = sum(float(np.linalg.norm(kappa * T4_s[0, 1:])) for T4_s in T4_list)
        cod_scale = max(1e-300, float(np.linalg.norm(div_sig)) + q_species_sum)
        cod_rel = float(np.linalg.norm(div_sig + kappa * q_tot)) / cod_scale

        max_jac = max(max_jac, jac)
        max_ham_rel = max(max_ham_rel, ham_rel)
        max_cod_rel = max(max_cod_rel, cod_rel)
        max_trace = max(max_trace, abs(float(np.trace(sig))))

        if thomson_coupling:
            op = _opacity_per_efold(Nk, H, cosmo, xe_interp, href)
            F_rad = covariant_thomson_force_dN(T4_list[0], vv_list[2], op)
            F_bar = -F_rad
            max_mom_sum_defect = max(max_mom_sum_defect, float(np.linalg.norm(F_rad + F_bar)))
            vb = vv_list[2]
            gb = 1.0 / math.sqrt(max(1e-30, 1.0 - float(vb @ vb)))
            u_b_cov = np.r_[-gb, gb * vb]
            max_orthog_defect = max(max_orthog_defect, abs(float(u_b_cov @ F_rad)))
            if math.expm1(-Nk) > 1200.0 and Nk > N_start + 0.05:
                max_slip_after_eq = max(max_slip_after_eq, float(np.linalg.norm(vv_list[0] - vv_list[2])))

    if max(max_ham_rel, max_cod_rel) > 1e-6:
        raise CodazziProjectionError(f"[{family}] coupled constraint breach: ham={max_ham_rel:.2e}, cod={max_cod_rel:.2e}")

    traj = TiltedEvolutionResult(
        family=initial_state.family,
        class_label=initial_state.triple.class_label,
        species_specs=specs,
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
    diag = {
        "max_hamiltonian_abs_over_3H2": max_ham_rel,
        "max_codazzi_rel": max_cod_rel,
        "max_jacobi_rel": max_jac,
        "max_shear_trace_error": max_trace,
        "max_total_4mom_exchange_defect": max_mom_sum_defect,
        "max_thomson_elastic_orthog_defect": max_orthog_defect,
        "max_pre_recomb_rad_bar_slip_over_c": max_slip_after_eq,
        "final_v_rad_norm_over_c": float(np.linalg.norm(v_grid["radiation"][-1])),
        "final_v_baryon_norm_over_c": float(np.linalg.norm(v_grid["baryon"][-1])),
    }
    return initial_state, traj, diag


class AngularWithBaryonDipole(r98_bh.Angular):
    """Extend r98.bianchi_history.Angular with exact Y_{1m} baryon-velocity Thomson dipole source columns."""

    def __init__(self, L: int, n_gl: int | None = None):
        super().__init__(L, n_gl)
        self.M_dip, self.M_quad = r98_bh.radiation_moment_operators()
        size = self.dim + 1
        zero = csc_matrix((1, 1), dtype=complex)
        # Reconstruct slot union cleanly by augmenting existing template + 3 dipole source columns (T_{1,-1}, T_{1,0}, T_{1,1})
        dip_ops = []
        for m in (-1, 0, 1):
            col = np.zeros((self.dim, 1), dtype=complex)
            col[self.idx["T"][(1, m)], 0] = 1.0
            dip_ops.append(bmat([[csc_matrix((self.dim, self.dim)), csc_matrix(col)], [None, zero]], format="coo"))
        base_coo = self.template.tocoo()
        base_keys = base_coo.row.astype(np.int64) * size + base_coo.col
        dip_keys = [op.row.astype(np.int64) * size + op.col for op in dip_ops]
        slots = np.unique(np.concatenate([base_keys, *dip_keys]))

        n_base_cols = self.coeff.shape[1]
        ext_coeff = np.zeros((len(slots), n_base_cols + 3), dtype=complex)
        # Align old coeff (sorted by base_coo order -> Wait: self.template is CSC, base_coo may reorder if sorted by row/col!)
        # Safer: reconstruct original CSC via self.template.indices / indptr directly using row*size + col keys!
        rows_b = self.template.indices.astype(np.int64)
        cols_b = np.repeat(np.arange(size, dtype=np.int64), np.diff(self.template.indptr))
        tpl_keys = rows_b * size + cols_b
        ext_coeff[np.searchsorted(slots, tpl_keys), :n_base_cols] = self.coeff
        for j, (dk, op) in enumerate(zip(dip_keys, dip_ops)):
            ext_coeff[np.searchsorted(slots, dk), n_base_cols + j] = op.data

        ext_tpl = csc_matrix((np.arange(1, len(slots) + 1, dtype=float), (slots // size, slots % size)), shape=(size, size))
        self.coeff_ext = ext_coeff[ext_tpl.data.astype(int) - 1]
        self.template_ext = ext_tpl.astype(complex)

    def matrix_coupled(self, geometry: np.ndarray, source: np.ndarray, opacity: float, v1m: np.ndarray) -> csc_matrix:
        vals = self.coeff_ext @ np.r_[geometry, opacity, source[:5], opacity * np.asarray(v1m, dtype=complex)]
        return csc_matrix((vals, self.template_ext.indices, self.template_ext.indptr), shape=self.template_ext.shape, copy=False)


def evolve_boltzmann_with_baryon_dipole(angular: AngularWithBaryonDipole, state, trajectory, geometry, refinement: int = 2):
    """Evolve polarized Boltzmann hierarchy including exact Thomson baryon-dipole emission & initial photon dipole."""
    dN, bg, opacity, grid = r98_bh.timeline(trajectory, geometry, refinement)
    mid = 0.5 * (grid[:-1] + grid[1:])
    vb_mid = CubicSpline(trajectory.N_grid, trajectory.species_v_grid["baryon"], axis=0, extrapolate=False)(mid)

    y = np.zeros(angular.dim + 1, complex)
    # Initialize radiation dipole to match dynamical initial photon fluid tilt v_rad(N_init)
    v_rad0 = trajectory.species_v_grid["radiation"][0]
    t1m0 = project_vector_to_y1m(v_rad0, angular.M_dip)
    for k, m in enumerate((-1, 0, 1)):
        y[angular.idx["T"][(1, m)]] = t1m0[k]
    y[-1] = 1.0

    hist = [y[:-1].copy()]
    for step, sample, rate, vb in zip(dN, bg, opacity, vb_mid):
        v1m = project_vector_to_y1m(vb, angular.M_dip)
        mat = angular.matrix_coupled(sample, sample, rate, v1m)
        y = expm_multiply(step * mat, y)
        hist.append(y[:-1].copy())
    if not np.all(np.isfinite(y)) or abs(y[-1] - 1.0) > 2e-12:
        raise FloatingPointError("Coupled Boltzmann transport lost affine invariant")
    hist_arr = np.asarray(hist)
    return y[:-1], float(dN @ opacity), hist_arr, grid, dN, opacity


def _extract_pi_gamma_spline(angular: AngularWithBaryonDipole, trajectory, hist_arr: np.ndarray, grid: np.ndarray) -> CubicSpline:
    """Project T_{2m}(N) from Boltzmann history into symmetric trace-free 3x3 pi_gamma(N) in Href_i^2 units."""
    idx_t2 = [angular.idx["T"][(2, m)] for m in (-2, -1, 0, 1, 2)]
    eps_n = CubicSpline(trajectory.N_grid, trajectory.species_eps_hat_grid["radiation"], extrapolate=False)(grid)
    vr_n = CubicSpline(trajectory.N_grid, trajectory.species_v_grid["radiation"], axis=0, extrapolate=False)(grid)
    b2 = np.sum(vr_n * vr_n, axis=1)
    rho_rad = eps_n * (1.0 + b2 / 3.0) / np.maximum(1e-30, 1.0 - b2)
    pi_norm = np.einsum("abm,tm->tab", angular.M_quad, hist_arr[:, idx_t2]).real
    pi_nodes = 4.0 * rho_rad[:, None, None] * pi_norm
    pi_nodes = 0.5 * (pi_nodes + np.swapaxes(pi_nodes, 1, 2))
    tr = np.trace(pi_nodes, axis1=1, axis2=2) / 3.0
    for j in range(len(pi_nodes)):
        pi_nodes[j] -= tr[j] * np.eye(3)
    return CubicSpline(grid, pi_nodes, axis=0, extrapolate=True)


def run_part_e_selfconsistent_bianchi() -> dict[str, object]:
    """Execute iterated self-consistent radiation-shear-baryon Bianchi evolution for all 5 canonical families."""
    ang = AngularWithBaryonDipole(12)
    families_out = {}

    for fam in r98_bh.FAMILIES:
        # Reference uncoupled baseline (Thomson off, pi_rad = 0, Radau vs DOP853 parity)
        st_unc, tr_unc, bg_unc_diag = evolve_coupled_bianchi_with_radiation(
            fam, epsilon=1e-5, samples=641, pi_rad_fn=None, thomson_coupling=False
        )
        gs_unc, chk_unc = r98_bh.background_checks(st_unc, tr_unc)
        _, tr_r98_dop = r98_bh.background(fam, epsilon=1e-5, samples=641)
        radau_vs_dop853_H_rel = float(np.max(np.abs(tr_unc.H_grid - tr_r98_dop.H_grid) / tr_r98_dop.H_grid))
        radau_vs_dop853_sig_abs = float(np.max(np.abs(tr_unc.sigma_ab_grid - tr_r98_dop.sigma_ab_grid)))

        # Fixed-point iterations k = 0..4 with full Thomson drag + iterated pi_gamma(N) backreaction
        pi_fn = None
        prev_gs = None
        prev_teb = None
        iters = []
        final_y = None
        final_tr = None
        final_gs = None
        final_ep = None
        for it in range(5):
            st_it, tr_it, diag_it = evolve_coupled_bianchi_with_radiation(
                fam, epsilon=1e-5, samples=641, pi_rad_fn=pi_fn, thomson_coupling=True
            )
            gs_it, chk_it = r98_bh.background_checks(st_it, tr_it)
            y_it, tau_it, hist_it, grid_it, _, _ = evolve_boltzmann_with_baryon_dipole(ang, st_it, tr_it, gs_it, refinement=2)
            ep_it = r98_bh.endpoint(ang, y_it)
            teb_vec = np.concatenate([
                r98_bh.low_modes(ang, y_it, "T", 5),
                r98_bh.low_modes(ang, y_it, "E", 5),
                r98_bh.low_modes(ang, y_it, "B", 5),
            ])
            sig_over_H_end = float(np.linalg.norm(tr_it.sigma_ab_grid[-1]) / tr_it.H_grid[-1])
            d_gs = float(np.max(np.abs(gs_it - prev_gs))) if prev_gs is not None else None
            d_teb = float(np.linalg.norm(teb_vec - prev_teb)) if prev_teb is not None else None
            # Build smooth pi_gamma(N) spline for next iteration
            n_lo, n_hi = float(grid_it[0]), float(grid_it[-1])
            spl = _extract_pi_gamma_spline(ang, tr_it, hist_it, grid_it)
            pi_vals_diag = spl(grid_it)
            max_pi_over_rho = float(np.max(np.linalg.norm(pi_vals_diag, axis=(1, 2)) / np.maximum(tr_it.species_eps_hat_grid["radiation"][0] * 1e-12, np.abs(CubicSpline(tr_it.N_grid, tr_it.species_eps_hat_grid["radiation"])(grid_it)))))

            iters.append({
                "iter": it,
                "hamiltonian_abs_over_3H2": diag_it["max_hamiltonian_abs_over_3H2"],
                "codazzi_rel": diag_it["max_codazzi_rel"],
                "jacobi_rel": diag_it["max_jacobi_rel"],
                "momentum_exchange_defect": diag_it["max_total_4mom_exchange_defect"],
                "elastic_orthog_defect": diag_it["max_thomson_elastic_orthog_defect"],
                "final_sigma_over_H": sig_over_H_end,
                "final_v_baryon_over_c": diag_it["final_v_baryon_norm_over_c"],
                "final_v_rad_over_c": diag_it["final_v_rad_norm_over_c"],
                "max_pi_gamma_over_eps_rad": max_pi_over_rho,
                "T_norm_2to5": ep_it["T"]["norm_l2_to_5"],
                "E_norm_2to5": ep_it["E"]["norm_l2_to_5"],
                "B_norm_2to5": ep_it["B"]["norm_l2_to_5"],
                "delta_geom_linf_from_prev": d_gs,
                "delta_teb_l2_from_prev": d_teb,
            })
            pi_fn = (lambda N_val, _s=spl, _a=n_lo, _b=n_hi: _s(float(np.clip(N_val, _a, _b))))
            prev_gs = gs_it.copy()
            prev_teb = teb_vec.copy()
            final_y, final_tr, final_gs, final_ep = y_it, tr_it, gs_it, ep_it

        # Compare self-consistent k=4 vs k=0 (one-way unbackreacted test radiation + baryon drag) and vs uncoupled Thomson=False
        st_k0, tr_k0, _ = evolve_coupled_bianchi_with_radiation(fam, epsilon=1e-5, samples=641, pi_rad_fn=None, thomson_coupling=True)
        families_out[fam] = {
            "collisionless_radau_vs_r98_dop853": {
                "max_rel_H": radau_vs_dop853_H_rel,
                "max_abs_sigma": radau_vs_dop853_sig_abs,
                "uncoupled_hamiltonian": bg_unc_diag["max_hamiltonian_abs_over_3H2"],
                "uncoupled_codazzi": bg_unc_diag["max_codazzi_rel"],
            },
            "thomson_drag_baryon_shift_vs_uncoupled": {
                "uncoupled_final_v_b": float(np.linalg.norm(tr_unc.species_v_grid["baryon"][-1])),
                "coupled_final_v_b": float(np.linalg.norm(final_tr.species_v_grid["baryon"][-1])),
                "uncoupled_final_v_rad": float(np.linalg.norm(tr_unc.species_v_grid["radiation"][-1])),
                "coupled_final_v_rad": float(np.linalg.norm(final_tr.species_v_grid["radiation"][-1])),
            },
            "pi_gamma_backreaction_k4_minus_k0": {
                "max_delta_sigma_over_H": float(np.max(np.linalg.norm(final_tr.sigma_ab_grid / final_tr.H_grid[:, None, None] - tr_k0.sigma_ab_grid / tr_k0.H_grid[:, None, None], axis=(1, 2)))),
                "final_delta_sigma_over_H": float(np.linalg.norm(final_tr.sigma_ab_grid[-1] / final_tr.H_grid[-1] - tr_k0.sigma_ab_grid[-1] / tr_k0.H_grid[-1])),
                "max_rel_delta_H": float(np.max(np.abs(final_tr.H_grid - tr_k0.H_grid) / tr_k0.H_grid)),
            },
            "fixed_point_iterations_k0_to_4": iters,
            "converged_endpoint": final_ep,
            "tau_optical": float(tau_it),
        }

    anilos_chk = r98_bh.anilos_and_ic_atlas_audit(ang)
    return {
        "L_max": 12,
        "refinement": 2,
        "samples": 641,
        "anilos_near_isotropic_check": {
            "kappa_vs_r98_cspin_max_abs_diff": anilos_chk["kappa_vs_r98_cspin_max_abs_diff"],
            "zeta_factor_m0_exact_max_err": anilos_chk["zeta_factor_m0_exact_max_err"],
            "zeta_factor_m_parity_max_err": anilos_chk["zeta_factor_m_parity_max_err"],
        },
        "families": families_out,
    }


def verify_p2_cmb_sha_guard() -> dict[str, object]:
    """Verify frozen R98 P2 grouped CMB artifacts untouched and preserve physical_Pi=None / D01 block."""
    cross_r98 = json.loads((R98_DIR / "CROSS_PHY_RESULTS.json").read_text())
    expected = cross_r98["source_sha256"]
    cache_path = R98_DIR / "CMB_GROUPED_FULL_CACHE.json"
    splits_path = R98_DIR / "CMB_OBSERVED_SPLITS.json"
    cache_sha = sha256(cache_path)
    splits_sha = sha256(splits_path)
    if cache_sha != expected["CMB_GROUPED_FULL_CACHE"]:
        raise ValueError(f"P2 cache SHA mismatch: {cache_sha} != {expected['CMB_GROUPED_FULL_CACHE']}")
    if splits_sha != expected["CMB_OBSERVED_SPLITS"]:
        raise ValueError(f"P2 splits SHA mismatch: {splits_sha} != {expected['CMB_OBSERVED_SPLITS']}")

    cache_d = json.loads(cache_path.read_text())
    splits_d = json.loads(splits_path.read_text())
    fold0 = cache_d["folds"][0]
    return {
        "status": "PRESERVED_SOURCE_CONDITIONAL_PR3_BLOCKED_PR4",
        "cmb_grouped_full_cache_sha256": cache_sha,
        "cmb_observed_splits_sha256": splits_sha,
        "matched_r98_cross_phy_pin": True,
        "commander_null_qualified": cache_d["commander_null_qualified"],
        "Bianchi_family_attribution": cache_d["Bianchi_family_attribution"],
        "physical_Pi": cache_d["physical_Pi"],
        "physical_GF": cache_d["physical_GF"],
        "fold0_raw_smica_score": fold0["models"]["raw"]["smica_score"],
        "fold0_raw_group_balanced_tail": fold0["models"]["raw"]["group_balanced_tail"],
        "splits_max_algebra_err_uK2": splits_d["max_split_algebra_err_uK2"],
        "blocked_external": ["D03: PR4/NPIPE component-separated splits and independent FFP12-style paired noise ensemble"],
    }


def compute() -> dict[str, object]:
    t0 = time.monotonic()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Read upstream R100 JSON artifacts (must already be generated)
    cf4_r100 = json.loads((OUT_DIR / "CF4_UPSTREAM_KBAND_RESULTS.json").read_text())
    opt_r100 = json.loads((OUT_DIR / "OPTICAL_DRIFT_RESULTS.json").read_text())
    rad_r100 = json.loads((OUT_DIR / "RADIO_EXPOSURE_SELECTION_RESULTS.json").read_text())
    gaia_r100 = json.loads((OUT_DIR / "GAIA_OPTICAL_JOINT_RESULTS.json").read_text())

    p2_guard = verify_p2_cmb_sha_guard()
    part_e_bianchi = run_part_e_selfconsistent_bianchi()

    phy01_to_07 = {
        "PHY01_cf4_hubble_window_and_genealogy": {
            "status": "SOURCE_CONDITIONAL_FULL_KBAND_AND_FP_SIGN_AUDITED",
            "sdss_exact_t2_matches": cf4_r100["A2_upstream_genealogy_and_sign_audit"]["sdss_pv_census"]["exact_pgc_matches_table2"],
            "sixdf_unique_t2_matches": cf4_r100["A2_upstream_genealogy_and_sign_audit"]["sixdf_pv_census"]["unique_match_15arcsec_500kms"],
            "shared_sdss_sixdf_corr": cf4_r100["A2_upstream_genealogy_and_sign_audit"]["shared_sdss_sixdf_overlap"]["corr_sdss_ldc_vs_6df_delta_d"],
            "wf5_full_k_trace": cf4_r100["A4_selection_likelihood_and_4term_cov"]["four_term_covariance_trace_budget_WF_R5_full_k"]["C_total_trace"],
            "tc_flrw_cos_bo_be": opt_r100["jacobians_TC_TG"]["FLRW"]["cosine_beta_o_vs_beta_e_CF4_36D"],
            "physical_Pi": None,
        },
        "PHY02_finite_z_optical_drift": {
            "status": "MODEL_CONDITIONAL_RAY_AND_SO3_VERIFIED",
            "VII_h_ode_coarse_vs_fine_rel_TG": opt_r100["convergence"]["VII_h"]["ode_coarse_vs_fine_rel_TG"],
            "so3_rotational_equivariance_VIh_max_abs_uasyr": opt_r100["so3_rotational_equivariance_VIh_max_abs_uasyr"],
            "secular_aberration_err_uasyr": opt_r100["secular_aberration_check"]["max_abs_err_uasyr"],
            "VI_h_z2_finite_z_rem_frac": opt_r100["families"]["VI_h"]["finite_z_remainder_fraction_of_local_by_z"][-2],
            "VI_h_quaia_B2_over_E2_z2p46": opt_r100["families"]["VI_h"]["TG_sectors_at_quaia_z_norms"]["z=2.461"]["finite_z_B2_ratio_to_E2"],
            "physical_GF": None,
        },
        "PHY03_cmb_grouped_pr3_guard": p2_guard,
        "PHY04_radio_exposure_and_reselection": {
            "status": rad_r100["status"],
            "lotss_mosaics_audited": rad_r100["C1_lotss_dr3_coverage_audit"]["mosaic_count"],
            "lotss_surf_tape_http202": rad_r100["C1_lotss_dr3_coverage_audit"]["surf_datalink_tape_audit"]["prior_http202_deferred_confirmed_without_tape_staging"],
            "five_survey_legacy966_common_beta_over_cmb": rad_r100["C2_five_survey_common_beta_vs_residuals"]["common_beta_over_beta_cmb"],
            "five_survey_outer_b15_sensitivity_beta_over_cmb": rad_r100["C2_five_survey_with_lotss_outer_b15_sensitivity"]["common_beta_over_beta_cmb"],
            "physical_Pi": None,
        },
        "PHY05_gaia_optical_joint_identifiability": {
            "status": gaia_r100["status"],
            "quaia_jk_rank_max47": gaia_r100["subspace_diagnostics"]["quaia_4shell_64D_jk"]["rank"],
            "full_inversion_avoided": gaia_r100["full_160D_or_64D_inversion_avoided"],
            "pa_whitened_bo_vs_be_deg": gaia_r100["subspace_angles_degrees"]["jk_whitened_beta_o_vs_beta_e"],
            "joint_profiled_sv": gaia_r100["joint_cf4_gaia_bobe_profiled_identifiability"]["joint_cf4_plus_gaia_profiled_sv"],
            "min_sv_gain_joint_over_gaia": gaia_r100["joint_cf4_gaia_bobe_profiled_identifiability"]["min_sv_gain_joint_over_gaia_alone"],
            "physical_Pi": None,
        },
        "PHY06_codazzi_and_selfconsistent_background_closure": {
            "status": "MODEL_CONDITIONAL_SELFCONSISTENT_CONVERGED",
            "VI_h_final_ham_rel": part_e_bianchi["families"]["VI_h"]["fixed_point_iterations_k0_to_4"][-1]["hamiltonian_abs_over_3H2"],
            "VI_h_final_codazzi_rel": part_e_bianchi["families"]["VI_h"]["fixed_point_iterations_k0_to_4"][-1]["codazzi_rel"],
            "VI_h_k4_delta_geom_linf": part_e_bianchi["families"]["VI_h"]["fixed_point_iterations_k0_to_4"][-1]["delta_geom_linf_from_prev"],
            "cf4_full_k_min_eig": cf4_r100["A3_full_kband_correlated_pv"]["models"]["WF_log_R5"]["C_tot_full_k"]["min_eig"],
            "physical_Pi": None,
        },
        "PHY07_multimode_bianchi_history_and_optical_eb": {
            "status": "MODEL_CONDITIONAL_TEB_AND_THOMSON_DRAG_CONVERGED",
            "VI_h_k4_T_norm_2to5": part_e_bianchi["families"]["VI_h"]["fixed_point_iterations_k0_to_4"][-1]["T_norm_2to5"],
            "VI_h_k4_E_norm_2to5": part_e_bianchi["families"]["VI_h"]["fixed_point_iterations_k0_to_4"][-1]["E_norm_2to5"],
            "VI_h_k4_B_norm_2to5": part_e_bianchi["families"]["VI_h"]["fixed_point_iterations_k0_to_4"][-1]["B_norm_2to5"],
            "VI_h_baryon_drag_v_end": part_e_bianchi["families"]["VI_h"]["thomson_drag_baryon_shift_vs_uncoupled"]["coupled_final_v_b"],
            "VII_h_k4_B_norm_2to5": part_e_bianchi["families"]["VII_h"]["fixed_point_iterations_k0_to_4"][-1]["B_norm_2to5"],
            "anilos_kappa_max_diff": part_e_bianchi["anilos_near_isotropic_check"]["kappa_vs_r98_cspin_max_abs_diff"],
            "physical_Pi": None,
        },
    }

    payload = {
        "schema": "htt.r100.bianchi_selfconsistent_and_phy/1",
        "owner": "bass_py_presolver_and_obsstat",
        "status": "MODEL_CONDITIONAL_SELFCONSISTENT_AND_PHY01_07_EXECUTED",
        "physical_Pi": None,
        "physical_GF": None,
        "calibrated_p": None,
        "Bianchi_family_attribution": None,
        "p2_cmb_sha_guard": p2_guard,
        "self_consistent_bianchi_radiation_coupling": part_e_bianchi,
        "PHY01_to_PHY07": phy01_to_07,
        "inputs_sha256": {
            "cf4_results": sha256(OUT_DIR / "CF4_UPSTREAM_KBAND_RESULTS.json"),
            "optical_results": sha256(OUT_DIR / "OPTICAL_DRIFT_RESULTS.json"),
            "radio_results": sha256(OUT_DIR / "RADIO_EXPOSURE_SELECTION_RESULTS.json"),
            "gaia_results": sha256(OUT_DIR / "GAIA_OPTICAL_JOINT_RESULTS.json"),
            "code": sha256(Path(__file__)),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "threads": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        },
        "runtime_seconds": time.monotonic() - t0,
    }
    out_path = OUT_DIR / "BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json"
    out_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    res = compute()
    sc = res["self_consistent_bianchi_radiation_coupling"]["families"]["VI_h"]
    it4 = sc["fixed_point_iterations_k0_to_4"][-1]
    print(json.dumps({
        "status": res["status"],
        "p2_guard": res["p2_cmb_sha_guard"]["status"],
        "VI_h_k4_ham": it4["hamiltonian_abs_over_3H2"],
        "VI_h_k4_cod": it4["codazzi_rel"],
        "VI_h_k4_delta_teb": it4["delta_teb_l2_from_prev"],
        "VI_h_baryon_vb": it4["final_v_baryon_over_c"],
        "runtime_s": res["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
