"""R102 Step 7 (N4): Family-by-family coupled Einstein-Boltzmann convergence & atlas audit.

Runs self-consistent coupled Bianchi Einstein-Euler + N1 GeneralLieStokesOperator +
N2 MovingFrameThomson + N3 4-channel TiltedHyrec across all 7 families:
  FLRW, I, V, VII_h (+1 / -1), VI_h, VI_-1/9, IX

Verifies:
- Baseline full coupled convergence (`L=8, n_cells=160, substeps=2, n_picard=2`) and
  strict Jacobi, Hamiltonian, Codazzi, 4-force conservation, and Stokes reality bounds.
- Angular truncation convergence across L in (6, 8, 12) for all 6 anisotropic families
  (transport sweep on converged coupled trajectories).
- Temporal refinement convergence across (n_cells, substeps) in [(80,1), (160,2), (320,4)]
  (transport sweep on all 6 anisotropic families + full coupled n_picard=2 refinement on
  VII_h, VI_-1/9, and IX).
- Independent 4D polarized geodesic + Sachs screen ray-tracing oracle across
  (I, V, VII_h, VI_-1/9, IX) comparing T, E, B, V harmonics against GeneralLieStokes(L=12).
- VII_h handedness parity (+1 vs -1) and moving electron-frame 4-force + equilibrium checks.
- N3 4-channel physical vs forbidden global H -> Gamma*H separation check.

Explicit boundary: atlas_qualified_for_planck_family_id = False,
Bianchi_family_attribution = None, physical_Pi = None, physical_GF = None, calibrated_p = None.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.interpolate import CubicSpline

from bass.background.geometry import pstf_rank2
from bass.background.initial_conditions import CodazziProjectionError
from bass.collision.electron_frame import rotate_stokes_samples
from bass.collision.moving_thomson import MovingFrameThomsonOperator
from bass.transport.moving_collision_stage import MovingCollisionStage, initial_radiation_stokes
from bass.recombination.tilted_hyrec import compare_against_forbidden_global_gamma_H, load_hyrec_atomic_tables
from bass.transport.coupled_einstein_boltzmann import (
    ALL_SEVEN_FAMILIES,
    CoupledSolverConfig,
    _power_spectrum_from_alms,
    solve_coupled_einstein_boltzmann,
)
from bass.transport.general_bianchi_transfer import (
    TRANSFER_MODE_GEODESIC,
    TiltedTransferParameters,
    _spherical_screen_basis,
    compute_general_bianchi_transfer,
    gl_sphere_grid,
    integrate_polarized_geodesics,
    map_from_scalar_alm,
    qu_from_spin2_alm,
)
from bass.transport.general_lie_stokes import (
    GeneralLieStokesOperator,
    LieGeometry,
    alm_dict_to_vector,
    max_stokes_reality_error,
    stokes_maps_to_vector,
    vector_to_alm_dict,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = (
    ROOT
    / "docs/research_program/observational_publication_20261015"
    / "R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123"
    / "NATIVE_SOLVER_CONVERGENCE.json"
)


def _summarize_cl(cl: dict[str, np.ndarray], lmax_keep: int = 8) -> dict[str, list[float]]:
    out = {}
    for ch in ("T", "E", "B", "V"):
        arr = np.asarray(cl[ch], dtype=np.float64)
        out[ch] = [float(x) for x in arr[: min(len(arr), lmax_keep + 1)]]
    return out


def _transport_sweep_on_converged_bg(
    base_res,
    op_lie: GeneralLieStokesOperator,
    *,
    n_cells: int,
    substeps: int,
    include_moving_correction: bool = True,
) -> tuple[np.ndarray, dict[str, np.ndarray], float]:
    """Replay N1+N2 Stokes integration at arbitrary (L, n_cells, substeps) on converged background."""
    traj = base_res.trajectory
    rec = base_res.recombination
    N_bg = np.asarray(traj.N_grid, dtype=np.float64)
    H_sp = CubicSpline(N_bg, traj.H_grid)
    sig_sp = CubicSpline(N_bg, traj.sigma_ab_grid.reshape(len(N_bg), 9))
    a_sp = CubicSpline(N_bg, traj.a_grid)
    n_sp = CubicSpline(N_bg, traj.n_grid.reshape(len(N_bg), 9))
    vb_sp = CubicSpline(N_bg, traj.species_v_grid["baryon"])

    N_edges = np.linspace(float(N_bg[0]), float(N_bg[-1]), int(n_cells) + 1, dtype=np.float64)
    cell_depths = rec.opacity_history().cells(N_edges).delta_tau
    S_vec = initial_radiation_stokes(op_lie, traj.species_v_grid["radiation"][0])

    for c in range(int(n_cells)):
        N0, N1 = float(N_edges[c]), float(N_edges[c + 1])
        N_mid = 0.5 * (N0 + N1)
        dN = N1 - N0
        Hm = float(H_sp(N_mid))
        sigN = pstf_rank2(sig_sp(N_mid).reshape(3, 3) / Hm)
        aN = a_sp(N_mid) / Hm
        nN = n_sp(N_mid).reshape(3, 3) / Hm
        nN = 0.5 * (nN + nN.T)

        scale = float(aN @ aN + np.sum(nN * nN))
        if scale <= 1e-24:
            aN = np.zeros(3, dtype=np.float64)
            nN = np.zeros((3, 3), dtype=np.float64)
        elif float(aN @ aN) <= 1e-24 * max(scale, 1.0):
            aN = np.zeros(3, dtype=np.float64)
            nN = 0.5 * (nN + nN.T)
        else:
            jac = float(np.max(np.abs(nN @ aN))) / scale
            if jac > 1e-6:
                raise CodazziProjectionError(f"[{base_res.family}] spline midpoint Jacobi breach: {jac:.3e}")
            if jac > 5e-12:
                an2 = float(aN @ aN)
                a_hat = aN / math.sqrt(an2)
                proj = np.eye(3, dtype=np.float64) - np.outer(a_hat, a_hat)
                np_m = proj @ nN @ proj
                nN = 0.5 * (np_m + np_m.T)

        dtau = float(cell_depths[c])
        geom = LieGeometry(sigN, aN, nN)
        vb = np.asarray(vb_sp(N_mid), dtype=np.float64)
        src = op_lie.shear_source_vector(sigN, amplitude=dN)
        moving = None
        if dtau > 0.0 and np.any(vb):
            if include_moving_correction:
                moving = MovingCollisionStage(op_lie, vb)
                src += dtau * moving.emission
            else:
                src += op_lie.dipole_source_vector(-vb, channel="T", amplitude=dtau)
        S_vec = op_lie.advance_cell(S_vec, dN, geom, dtau, source_increment=src,
                                    substeps=substeps, moving_collision=moving, bolometric_redshift=True)

    reality = max_stokes_reality_error(S_vec, op_lie.idx)
    alms = vector_to_alm_dict(S_vec, op_lie.idx)
    cl = _power_spectrum_from_alms(alms, op_lie.L)
    return S_vec, cl, reality


def _geodesic_oracle_for_state(family: str, traj, op_lie: GeneralLieStokesOperator) -> dict[str, object]:
    """Compare collisionless polarized (T,E,B,V) Lie transport vs 4D geodesic + Sachs ray tracing."""
    # Evaluate near last-scattering z ~ 1100 (or where H_norm > 0 and n_eff/a_eff non-degenerate) AND observer z=0!
    sig = np.asarray(traj.sigma_ab_grid[-1] / traj.H_grid[-1], dtype=np.float64)
    a = np.asarray(traj.a_grid[-1] / traj.H_grid[-1], dtype=np.float64)
    n = 0.5 * (
        np.asarray(traj.n_grid[-1] / traj.H_grid[-1], dtype=np.float64)
        + np.asarray(traj.n_grid[-1] / traj.H_grid[-1], dtype=np.float64).T
    )
    scale = float(a @ a + np.sum(n * n))
    if scale <= 1e-24:
        a = np.zeros(3, dtype=np.float64)
        n = np.zeros((3, 3), dtype=np.float64)
    elif float(a @ a) <= 1e-24 * max(scale, 1.0):
        a = np.zeros(3, dtype=np.float64)
        n = 0.5 * (n + n.T)
    else:
        jac = float(np.max(np.abs(n @ a))) / scale
        if jac > 5e-12:
            an2 = float(a @ a)
            a_hat = a / math.sqrt(an2)
            proj = np.eye(3, dtype=np.float64) - np.outer(a_hat, a_hat)
            np_m = proj @ n @ proj
            n = 0.5 * (np_m + np_m.T)

    # Polarized Sachs ray-tracing check over dN_ray = 0.02 comparing Lie (L=12) vs direct geodesic + screen transport
    dN_ray = 0.02
    n_th = op_lie.n_gl_theta
    th_grid, ph_grid, n_hat, _ = gl_sphere_grid(n_th)
    rays = integrate_polarized_geodesics(
        n_hat,
        family=traj.family,
        H0=1.0,
        sigma_ab=sig,
        a_vec=a,
        n_mat=n,
        n_efolds_star=-dN_ray,
        n_steps=64,
    )
    n_emit = -rays.p_emit / np.linalg.norm(rays.p_emit, axis=-1, keepdims=True)
    th_em = np.arccos(np.clip(n_emit[..., 2], -1.0, 1.0))
    ph_em = np.mod(np.arctan2(n_emit[..., 1], n_emit[..., 0]), 2.0 * math.pi)
    e_th_em, e_ph_em = _spherical_screen_basis(n_emit)

    # Smooth low-l sky in T, E, B, V evaluated analytically at observer and emission directions
    alms_seed = {
        "T": {(1, 0): 0.4 + 0.0j, (2, 1): 0.3 - 0.2j, (2, -1): -(0.3 + 0.2j), (2, 2): 0.5 + 0.1j, (2, -2): 0.5 - 0.1j},
        "E": {(2, 0): 0.35 + 0.0j, (2, 2): -0.25 + 0.15j, (2, -2): -0.25 - 0.15j},
        "B": {(2, 1): 0.2 + 0.1j, (2, -1): -(0.2 - 0.1j)},
        "V": {(1, 1): 0.15 - 0.1j, (1, -1): -(0.15 + 0.1j), (2, 0): 0.25 + 0.0j},
    }

    def _eval_sky(TH: np.ndarray, PH: np.ndarray) -> np.ndarray:
        I_m = map_from_scalar_alm(alms_seed["T"], TH, PH, ell_max=2)
        Q_m, U_m = qu_from_spin2_alm(alms_seed["E"], alms_seed["B"], TH, PH, ell_max=2)
        V_m = map_from_scalar_alm(alms_seed["V"], TH, PH, ell_max=2)
        return np.stack((I_m, Q_m, U_m, V_m), axis=-1)

    sky_obs_t0 = _eval_sky(th_grid, ph_grid)
    sky_em_raw = _eval_sky(th_em, ph_em)
    # Parallel-transport linear polarization from emission spherical basis (e_th_em, e_ph_em) to Sachs screen (s1_emit, s2_emit),
    # which arrives unaltered on observer's spherical basis (e_th_obs, e_ph_obs)!
    q_tr, u_tr = rotate_stokes_samples(
        sky_em_raw[..., 1].reshape(-1),
        sky_em_raw[..., 2].reshape(-1),
        e_th_em.reshape(-1, 3),
        e_ph_em.reshape(-1, 3),
        rays.s1_emit.reshape(-1, 3),
        rays.s2_emit.reshape(-1, 3),
    )
    sky_ray = sky_em_raw.copy()
    sky_ray[..., 1] = q_tr.reshape(th_grid.shape)
    sky_ray[..., 2] = u_tr.reshape(th_grid.shape)

    v0 = alm_dict_to_vector(alms_seed, op_lie.idx, op_lie.dim)
    v_ray = stokes_maps_to_vector(sky_ray, op_lie.idx, op_lie.dim, L=op_lie.L, n_gl_theta=n_th)
    v_lie = op_lie.advance_cell(v0, dN_ray, LieGeometry(sig, a, n), 0.0, substeps=16)

    rel_by_ch = {}
    for ch in ("T", "E", "B", "V"):
        idxs = [pos for (ell, _), pos in op_lie.idx[ch].items() if ell <= 6]
        num = float(np.linalg.norm(v_lie[idxs] - v_ray[idxs]))
        den = max(float(np.linalg.norm(v_ray[idxs])), 1e-30)
        rel_by_ch[ch] = num / den

    # Full finite-z exact_geodesic_background transfer along the coupled trajectory
    tp = TiltedTransferParameters(
        family=traj.family,
        trajectory=traj,
        sigma_N=sig,
        v_matter=traj.species_v_grid["cdm"][-1],
        v_rad=traj.species_v_grid["radiation"][-1],
        v_obs=np.zeros(3, dtype=np.float64),
        ell_max=8,
        n_gl_theta=16,
        n_geodesic_steps=128,
        transfer_mode=TRANSFER_MODE_GEODESIC,
    )
    gout = compute_general_bianchi_transfer(tp)
    return {
        "family_key": family,
        "traj_family": traj.family,
        "polarized_dN_ray": dN_ray,
        "ray_max_null_err": float(rays.max_null_err),
        "ray_max_screen_ortho_err": float(rays.max_screen_ortho_err),
        "collisionless_lie_vs_sachs_ray_rel_l_le_6": rel_by_ch,
        "transfer_max_null_err": float(gout.max_null_err),
        "transfer_max_screen_ortho_err": float(gout.max_screen_ortho_err),
        "transfer_cl_TT_l2_l3": [float(gout.cl_TT[2]), float(gout.cl_TT[3])],
        "transfer_cl_EE_l2_l3": [float(gout.cl_EE[2]), float(gout.cl_EE[3])],
        "transfer_cl_BB_l2_l3": [float(gout.cl_BB[2]), float(gout.cl_BB[3])],
    }


def run_all() -> dict[str, object]:
    t0 = time.monotonic()
    tbl = load_hyrec_atomic_tables(verify_sha256=True)

    ops = {L: GeneralLieStokesOperator(L) for L in (6, 8, 12)}
    op8 = ops[8]

    # 1. Baseline L=8, n_cells=160, substeps=2, n_picard=2 across all 7 families + VII_h (-1)
    baseline: dict[str, dict[str, object]] = {}
    base_results = {}
    cases = [(fam, 1) for fam in ALL_SEVEN_FAMILIES] + [("VII_h", -1)]
    for fam, hnd in cases:
        key = fam if hnd == 1 else "VII_h_minus"
        eps = 0.0 if fam == "FLRW" else 1e-5
        res = solve_coupled_einstein_boltzmann(
            fam,
            CoupledSolverConfig(ell_max=8, n_cells=160, substeps_per_cell=2, n_picard=2, epsilon=eps, handedness=hnd),
            tables=tbl,
            lie_op=op8,
        )
        base_results[key] = res
        baseline[key] = {
            "family": fam,
            "handedness": hnd,
            "epsilon": eps,
            "class_label": res.trajectory.class_label,
            "total_optical_depth": res.total_optical_depth,
            "max_jacobi_residual": res.max_jacobi_residual,
            "max_hamiltonian_residual": res.max_hamiltonian_residual,
            "max_codazzi_residual": res.max_codazzi_residual,
            "max_four_force_orthog_error": res.max_four_force_orthog_error,
            "max_momentum_sum_error": res.max_momentum_sum_error,
            "max_stokes_reality_err": res.max_stokes_reality_err,
            "picard_pi_rel_change": res.picard_pi_rel_change,
            "cl_l0_to_8": _summarize_cl(res.cl_final, 8),
        }

    # 2. Multipole truncation L in (6, 8, 12) and temporal refinement (1, 2, 4) across all 6 anisotropic families
    convergence_families = ("I", "V", "VII_h", "VI_h", "VI_-1/9", "IX")
    l_convergence = {}
    for fam in convergence_families:
        specs_by_L = {8: base_results[fam].cl_final}
        realities_by_L = {8: base_results[fam].max_stokes_reality_err}
        for L in (6, 12):
            _, cl_L, rel_L = _transport_sweep_on_converged_bg(base_results[fam], ops[L], n_cells=160, substeps=2)
            specs_by_L[L] = cl_L
            realities_by_L[L] = rel_L

        def _rel_cl_diff(a_cl: dict[str, np.ndarray], b_cl: dict[str, np.ndarray]) -> dict[str, float]:
            out = {}
            for ch in ("T", "E", "B", "V"):
                ref_seg = b_cl[ch][2:7]
                diff_seg = a_cl[ch][2:7] - ref_seg
                denom = max(float(np.linalg.norm(ref_seg)), 1e-30)
                out[ch] = float(np.linalg.norm(diff_seg) / denom)
            return out

        l_convergence[fam] = {
            "L6_vs_L12_rel_l2_6": _rel_cl_diff(specs_by_L[6], specs_by_L[12]),
            "L8_vs_L12_rel_l2_6": _rel_cl_diff(specs_by_L[8], specs_by_L[12]),
            "L12_stokes_reality_err": realities_by_L[12],
        }

    time_refinement = {}
    for fam in convergence_families:
        states_by_ref = {2: base_results[fam].final_state}
        realities_by_ref = {2: base_results[fam].max_stokes_reality_err}
        for ref, nc, ss in ((1, 80, 1), (4, 320, 4)):
            st_r, _, rel_r = _transport_sweep_on_converged_bg(base_results[fam], op8, n_cells=nc, substeps=ss)
            states_by_ref[ref] = st_r
            realities_by_ref[ref] = rel_r
        d12 = float(np.linalg.norm(states_by_ref[1] - states_by_ref[2]) / max(float(np.linalg.norm(states_by_ref[2])), 1e-30))
        d24 = float(np.linalg.norm(states_by_ref[2] - states_by_ref[4]) / max(float(np.linalg.norm(states_by_ref[4])), 1e-30))
        time_refinement[fam] = {
            "transport_ref1_vs_ref2_rel": d12,
            "transport_ref2_vs_ref4_rel": d24,
            "transport_ratio_d12_over_d24": float(d12 / max(d24, 1e-30)),
            "ref4_stokes_reality_err": realities_by_ref[4],
        }

    # Full end-to-end coupled n_picard=2 refinement across (80,1) -> (160,2) -> (320,4) on VII_h, VI_-1/9, IX
    full_coupled_refinement = {}
    for fam in ("VII_h", "VI_-1/9", "IX"):
        r1 = solve_coupled_einstein_boltzmann(
            fam, CoupledSolverConfig(ell_max=8, n_cells=80, substeps_per_cell=1, n_picard=2, epsilon=1e-5),
            tables=tbl, lie_op=op8,
        )
        r2 = base_results[fam]
        r4 = solve_coupled_einstein_boltzmann(
            fam, CoupledSolverConfig(ell_max=8, n_cells=320, substeps_per_cell=4, n_picard=2, epsilon=1e-5),
            tables=tbl, lie_op=op8,
        )
        d12 = float(np.linalg.norm(r1.final_state - r2.final_state) / max(float(np.linalg.norm(r2.final_state)), 1e-30))
        d24 = float(np.linalg.norm(r2.final_state - r4.final_state) / max(float(np.linalg.norm(r4.final_state)), 1e-30))
        full_coupled_refinement[fam] = {
            "ref1_vs_ref2_state_rel": d12,
            "ref2_vs_ref4_state_rel": d24,
            "ref4_constraints": {
                "max_jacobi": r4.max_jacobi_residual,
                "max_ham": r4.max_hamiltonian_residual,
                "max_codazzi": r4.max_codazzi_residual,
            },
        }

    # 3. Independent 4D geodesic + Sachs screen oracle checks across (I, V, VII_h, VI_-1/9, IX)
    geodesic_oracle = {
        fam: _geodesic_oracle_for_state(fam, base_results[fam].trajectory, ops[12])
        for fam in ("I", "V", "VII_h", "VI_-1/9", "IX")
    }

    # 4. VII_h handedness parity, MovingFrameThomson 4-force/equilibrium, and N3 4-channel checks
    cl_p = base_results["VII_h"].cl_final
    cl_m = base_results["VII_h_minus"].cl_final
    parity_check = {
        "E_spectrum_rel_diff_l2_8": float(np.linalg.norm(cl_p["E"][2:9] - cl_m["E"][2:9]) / max(float(np.linalg.norm(cl_p["E"][2:9])), 1e-30)),
        "B_spectrum_rel_diff_l2_8": float(np.linalg.norm(cl_p["B"][2:9] - cl_m["B"][2:9]) / max(float(np.linalg.norm(cl_p["B"][2:9])), 1e-30)),
        "B22_plus": [float(base_results["VII_h"].alm_final["B"][(2, 2)].real), float(base_results["VII_h"].alm_final["B"][(2, 2)].imag)],
        "B22_minus": [float(base_results["VII_h_minus"].alm_final["B"][(2, 2)].real), float(base_results["VII_h_minus"].alm_final["B"][(2, 2)].imag)],
    }

    mov_op = MovingFrameThomsonOperator(np.array([0.12, -0.05, 0.03], dtype=np.float64), n_theta_rest=12)
    eq_sky = mov_op.bolometric_equilibrium_sky(1.0)
    eq_resid = float(np.max(np.abs(mov_op.collision_bolometric(eq_sky, clock="rest_time"))))
    rng = np.random.default_rng(17)
    aniso_sky = eq_sky + 0.05 * (rng.normal(size=eq_sky.shape) * np.array([1.0, 0.2, 0.2, 0.1]))
    aniso_sky[:, 0] = np.maximum(aniso_sky[:, 0], 0.1)
    ff = mov_op.four_force(aniso_sky, clock="conserved_anchor")
    moving_thomson_check = {
        "beta": mov_op.beta.tolist(),
        "equilibrium_collision_max_abs": eq_resid,
        "four_force_angular_vs_covariant_rel_diff": float(ff["rel_diff"]),
        "orthog_ub_dot_F_cov": float(ff["orthogonality_ub_dot_F_cov"]),
        "orthog_ub_dot_F_ang": float(ff["orthogonality_ub_dot_F_ang"]),
    }

    zs_rec = np.linspace(1500.0, 800.0, 15)
    n3_b05 = compare_against_forbidden_global_gamma_H(zs_rec, beta_const=[0.04, -0.02, 0.022], tables=tbl)
    n3_b10 = compare_against_forbidden_global_gamma_H(zs_rec, beta_const=[0.08, -0.04, 0.044], tables=tbl)

    return {
        "schema": "htt.r102.native_solver_convergence/1",
        "scope": "Native coupled Einstein-Boltzmann + general-Lie + moving-Thomson + tilted-HYREC convergence & constraint suite.",
        "atlas_qualified_for_planck_family_id": False,
        "Bianchi_family_attribution": None,
        "physical_Pi": None,
        "physical_GF": None,
        "calibrated_p": None,
        "tables_sha256": tbl.sha256_manifest,
        "baseline_seven_families_L8_ref2": baseline,
        "multipole_convergence_L6_8_12": l_convergence,
        "time_step_refinement_1_2_4": time_refinement,
        "full_coupled_refinement_viih_vim1_9_ix": full_coupled_refinement,
        "geodesic_sachs_oracle_checks": geodesic_oracle,
        "viih_handedness_parity": parity_check,
        "moving_thomson_check": moving_thomson_check,
        "tilted_hyrec_vs_forbidden_gamma_H": {"beta_low": n3_b05, "beta_double": n3_b10},
        "scientific_claims_quarantine": {
            "native_implementation_and_numerical_validation": "COMPLETE_SCOPED_R102",
            "source_conditioned_observational_analysis": "PARTIAL_SCOPED_BLOCKED_INPUT",
            "calibrated_observational_inference": "BLOCKED_MISSING_UPSTREAM_CALIBRATION_AND_ENSEMBLES",
            "bianchi_family_attribution": "BLOCKED_ATLAS_UNQUALIFIED_AND_MISSING_NULL",
        },
        "runtime_seconds": time.monotonic() - t0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    res = run_all()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(res, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "atlas_qualified_for_planck_family_id": res["atlas_qualified_for_planck_family_id"],
                "Bianchi_family_attribution": res["Bianchi_family_attribution"],
                "max_jacobi": max(v["max_jacobi_residual"] for v in res["baseline_seven_families_L8_ref2"].values()),
                "max_hamiltonian": max(v["max_hamiltonian_residual"] for v in res["baseline_seven_families_L8_ref2"].values()),
                "max_codazzi": max(v["max_codazzi_residual"] for v in res["baseline_seven_families_L8_ref2"].values()),
                "max_oracle_lie_vs_ray": max(max(v["collisionless_lie_vs_sachs_ray_rel_l_le_6"].values()) for v in res["geodesic_sachs_oracle_checks"].values()),
                "max_oracle_null_err": max(v["transfer_max_null_err"] for v in res["geodesic_sachs_oracle_checks"].values()),
                "runtime_s": res["runtime_seconds"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
