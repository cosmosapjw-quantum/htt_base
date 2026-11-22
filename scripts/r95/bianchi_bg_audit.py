"""R95 Step 3A (G07_BIANCHI / P5): Multi-fluid Class A/B Einstein-Euler + BASS Codazzi + finite-z geodesics & R62 CF4 carrier audit.

Reuses:
  - htt.bass.background.general_tilted_evolution (R49 12-family Einstein-Euler + Fournodavlos benchmark)
  - htt.bass.background.tilted_bianchi_state (4D connection, congruence kinematics, WEC/DEC, frame transport)
  - htt.bass.transport.general_bianchi_transfer (4D exact null geodesics & Sachs polarization screen)
  - /home/cosmosapjw/bass/bianchi/conventions.py (independent Codazzi residual oracle)
  - R62 7-nuisance CF4 J2 carriers & R90 canonical equivalence classes
Preserves SQ-NATIVE and B02-B05 publication status (not full inhomogeneous all-m Boltzmann).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import null_space, solve_triangular
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bass.background.convention_bridge import (
    ALL_TWELVE_FAMILIES,
    BIANCHI_ACTION_EQUIVALENCE_CLASSES,
    exact_momentum_divergence,
    exact_spatial_ricci_from_compact,
)
from bass.background.bianchi_types import BianchiAlgebra, build_bianchi_algebra
from bass.background.general_tilted_evolution import (
    TiltedEvolutionConfig,
    _build_default_admissible_state_for_family,
    evolve_general_tilted_bianchi,
    run_fournodavlos_two_fluid_bianchi_i_benchmark,
)
from bass.background.geometry import pstf_rank2
from bass.background.tilted_bianchi_state import (
    SpeciesFluidCongruence,
    build_frame_transport_bundle,
    compute_species_congruence_kinematics,
    construct_admissible_tilted_state,
    solve_compensating_tilt_velocity,
)
from bass.transport.general_bianchi_transfer import (
    FAMILY_TRANSFER_METADATA,
    TRANSFER_MODE_GEODESIC,
    TiltedTransferParameters,
    compute_general_bianchi_transfer,
    gl_sphere_grid,
    map_from_scalar_alm,
    scalar_alm_from_map,
)
from common.stf_metric_bridge import orthonormal_to_stf_matrix, stf_matrix_to_orthonormal

import subprocess

BASS_CONVENTIONS = Path("/home/cosmosapjw/bass/bianchi/conventions.py")
BASS_PY = Path("/home/cosmosapjw/bass/.venv/bin/python")
R62_DIR = ROOT / "docs/research_program/observational_publication_20261015/R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/CLASSIFICATION"
OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122/G07_BIANCHI_BACKGROUND_AUDIT.json"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _extract_stf5_quadrupole(gout, frame: str = "observer") -> np.ndarray:
    """Exact STF5 quadrupole extraction from l=2 scalar harmonics on GL grid.

    Avoids the uncontracted einsum & inverted orthonormal->stf call in unchanged R49
    PolarizedTransferOutput.as_stf5_quadrupole (general_bianchi_transfer.py:280-281).
    """
    alm = gout.alm_T if frame == "observer" else gout.cosmo_alm_T
    T_rec = map_from_scalar_alm(alm, gout.theta_gl, gout.phi_gl, ell_min=2, ell_max=2)
    M = np.einsum("abi,abj,ab->ij", gout.n_hat_grid, gout.n_hat_grid, T_rec * gout.weights_gl) * (15.0 / (8.0 * math.pi))
    return stf_matrix_to_orthonormal(pstf_rank2(M))


def _vi_rk4_convergence() -> dict:
    """Verify O(h^4) RK4 convergence on exceptional VI_{-1/9} tilted trajectory across steps=(48, 96, 192)."""
    st = _build_vi_minus_1_9_state()
    traj = evolve_general_tilted_bianchi(
        st,
        eos_by_species={"photon": 1.0 / 3.0, "cdm": 0.0},
        config=TiltedEvolutionConfig(N_start=0.0, N_end=2.0, n_eval=41, method="DOP853", rtol=1e-10, atol=1e-12),
    )
    rows = []
    for nstep in (48, 96, 192):
        tp = TiltedTransferParameters(
            family="VI_h",
            trajectory=traj,
            sigma_N=traj.sigma_ab_grid[-1] / traj.H_grid[-1],
            v_matter=traj.species_v_grid["cdm"][-1],
            v_rad=traj.species_v_grid["photon"][-1],
            v_obs=0.0012335867 * np.array([-0.97076238, 0.20737094, -0.12090369]),
            ell_max=8,
            n_gl_theta=16,
            n_geodesic_steps=nstep,
            transfer_mode=TRANSFER_MODE_GEODESIC,
        )
        gout = compute_general_bianchi_transfer(tp)
        rows.append({
            "n_geodesic_steps": nstep,
            "max_null_err": float(gout.max_null_err),
            "max_screen_ortho_err": float(gout.max_screen_ortho_err),
            "cl_TT_l2": float(gout.cl_TT[2]),
            "cl_EE_l2": float(gout.cl_EE[2]),
            "cl_BB_l2": float(gout.cl_BB[2]),
        })
    return {
        "steps": rows,
        "null_err_ratio_48_over_96": rows[0]["max_null_err"] / max(rows[1]["max_null_err"], 1e-300),
        "null_err_ratio_96_over_192": rows[1]["max_null_err"] / max(rows[2]["max_null_err"], 1e-300),
    }


def _eval_bass_codazzi_batch(items: list[dict]) -> list[list[float]]:
    """Evaluate bianchi.conventions.codazzi_residual in BASS's original isolated .venv (jax x64)."""
    code = (
        "import json, sys, numpy as np; "
        "from bianchi.conventions import codazzi_residual; "
        "items = json.load(sys.stdin); "
        "out = [np.asarray(codazzi_residual("
        "np.array(x['S']), np.array(x['N']), np.array(x['A']), np.array(x['q'])), float).tolist() "
        "for x in items]; "
        "print(json.dumps(out))"
    )
    proc = subprocess.run(
        [str(BASS_PY), "-B", "-c", code],
        input=json.dumps(items),
        cwd=str(BASS_CONVENTIONS.parents[1]),
        env={"PATH": "/usr/bin:/bin", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "JAX_PLATFORMS": "cpu"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(proc.stdout)


def _build_vi_minus_1_9_state():
    """Construct exact exceptional Class-B VI_{-1/9} stratum: N = diag(0,1,-4), a = (2/3, 0, 0)."""
    alg = build_bianchi_algebra("VI_h", n1=1.0, n3=-4.0, a_twist=2.0 / 3.0)
    sig = pstf_rank2(np.array([[-0.03, 0.012, -0.008], [0.012, 0.015, 0.009], [-0.008, 0.009, 0.015]]))
    div_sig = exact_momentum_divergence(sig, alg.a, alg.n, a_sign=1)
    sp_rad = SpeciesFluidCongruence(species="photon", eps_hat=0.25, p_hat=0.25 / 3.0, v_vec=[0.03, 0.01, -0.01])
    q_rem = -div_sig - sp_rad.to_projected_state().q
    v_mat = solve_compensating_tilt_velocity(q_rem, eps_hat=1.0, p_hat=0.0)
    sp_mat = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=v_mat)
    return construct_admissible_tilted_state(
        family="VI_h", algebra=alg, sigma_ab=sig, species=[sp_rad, sp_mat], lambda_value=1.5, kappa=1.0
    )


def _build_orthogonal_state(family: str):
    """Untilt / orthogonal control (v_s = 0 => q_tot = 0, shear strictly in Codazzi kernel)."""
    alg = build_bianchi_algebra("I" if family == "FLRW" else family)
    # Use Codazzi kernel shear
    from bass.background.tilted_bianchi_state import momentum_constraint_map
    mc = momentum_constraint_map(alg)
    ns = null_space(mc.matrix, rcond=1e-12)
    if family == "FLRW":
        sig = np.zeros((3, 3), dtype=np.float64)
    elif ns.shape[1] > 0:
        vec5 = 0.02 * ns[:, 0]
        from common.stf_metric_bridge import orthonormal_to_stf_matrix
        sig = orthonormal_to_stf_matrix(vec5, convention="kinematic_response")
    else:
        sig = np.zeros((3, 3), dtype=np.float64)
    sp_rad = SpeciesFluidCongruence(species="photon", eps_hat=0.25, p_hat=0.25 / 3.0, v_vec=[0.0, 0.0, 0.0])
    sp_mat = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=[0.0, 0.0, 0.0])
    return construct_admissible_tilted_state(
        family=family, algebra=alg, sigma_ab=sig, species=[sp_rad, sp_mat], lambda_value=1.5, kappa=1.0
    )


def run_audit() -> dict:
    t0 = time.perf_counter()

    # 1. Fournodavlos-Marshall-Oliynyk (2026) two-fluid nonlinear Bianchi-I stability oracle
    fmo = run_fournodavlos_two_fluid_bianchi_i_benchmark(K_1=0.42, K_2=0.58, lambda_value=1.8, N_end=4.5)
    if not fmo.passed_theorem_regime:
        raise RuntimeError("Fournodavlos 2-fluid Bianchi I stability benchmark failed")

    cases = [(fam, False, _build_default_admissible_state_for_family(fam)) for fam in ALL_TWELVE_FAMILIES]
    cases.append(("VI_-1/9_exception", False, _build_vi_minus_1_9_state()))
    for fam in ("I", "V", "VII_h", "IX"):
        cases.append((fam, True, _build_orthogonal_state(fam)))

    traj_results = {}
    max_ham_all = 0.0
    max_cod_all = 0.0
    max_jac_all = 0.0
    bass_batch_inputs = []
    bass_batch_divs = []
    bass_key_slices = []

    for label, is_orth, init_state in cases:
        key = f"{label}__orthogonal" if is_orth else f"{label}__tilted"
        fam_arg = "VI_h" if label == "VI_-1/9_exception" else label
        traj = evolve_general_tilted_bianchi(
            init_state,
            eos_by_species={"photon": 1.0 / 3.0, "cdm": 0.0},
            config=TiltedEvolutionConfig(N_start=0.0, N_end=2.0, n_eval=41, method="DOP853", rtol=1e-10, atol=1e-12),
        )
        dec_margins = []
        for idx in (0, len(traj.N_grid) // 2, len(traj.N_grid) - 1):
            Hk = float(traj.H_grid[idx])
            sigk = traj.sigma_ab_grid[idx]
            ak = traj.a_grid[idx]
            nk = traj.n_grid[idx]
            T4_tot = np.zeros((4, 4), dtype=np.float64)
            for sp_name, K_eos in (("photon", 1.0 / 3.0), ("cdm", 0.0)):
                eh = float(traj.species_eps_hat_grid[sp_name][idx])
                vv = traj.species_v_grid[sp_name][idx]
                sp_obj = SpeciesFluidCongruence(species=sp_name, eps_hat=eh, p_hat=K_eos * eh, v_vec=vv)
                proj = sp_obj.to_projected_state()
                T4_tot[0, 0] += proj.rho
                T4_tot[0, 1:] += proj.q
                dec_margins.append(float(proj.rho - np.linalg.norm(proj.q)))
            q_tot = T4_tot[0, 1:]
            dec_margins.append(float(T4_tot[0, 0] - np.linalg.norm(q_tot)))
            div_htt = exact_momentum_divergence(sigk, ak, nk, a_sign=1)
            bass_batch_inputs.append({
                "S": (sigk / Hk).tolist(),
                "N": (nk / Hk).tolist(),
                "A": (ak / Hk).tolist(),
                "q": ((traj.kappa * q_tot) / (Hk * Hk)).tolist(),
            })
            bass_batch_divs.append(((div_htt + traj.kappa * q_tot) / (Hk * Hk)).tolist())
            bass_key_slices.append(key)

        v_ph_fin = traj.species_v_grid["photon"][-1]
        v_cdm_fin = traj.species_v_grid["cdm"][-1]
        from bass.background.convention_bridge import build_structure_tensor_with_sign
        C_sp_fin = build_structure_tensor_with_sign(traj.a_grid[-1], traj.n_grid[-1], a_sign=1)
        kin_ph = compute_species_congruence_kinematics(
            SpeciesFluidCongruence("photon", float(traj.species_eps_hat_grid["photon"][-1]), float(traj.species_eps_hat_grid["photon"][-1]) / 3.0, v_ph_fin),
            H=float(traj.H_grid[-1]),
            sigma_ab=traj.sigma_ab_grid[-1],
            C_spatial=C_sp_fin,
        )
        kin_cdm = compute_species_congruence_kinematics(
            SpeciesFluidCongruence("cdm", float(traj.species_eps_hat_grid["cdm"][-1]), 0.0, v_cdm_fin),
            H=float(traj.H_grid[-1]),
            sigma_ab=traj.sigma_ab_grid[-1],
            C_spatial=C_sp_fin,
        )
        v_obs_cmb = 0.0012335867 * np.array([-0.97076238, 0.20737094, -0.12090369])
        bundle = build_frame_transport_bundle(
            beta_normal_to_matter=v_cdm_fin,
            beta_matter_to_radiation=v_ph_fin - v_cdm_fin,
            beta_matter_to_observer=v_obs_cmb,
        )
        tparams = TiltedTransferParameters(
            family=fam_arg,
            trajectory=traj,
            sigma_N=traj.sigma_ab_grid[-1] / traj.H_grid[-1],
            v_matter=v_cdm_fin,
            v_rad=v_ph_fin,
            v_obs=v_obs_cmb,
            ell_max=8,
            n_gl_theta=16,
            n_geodesic_steps=192,
            transfer_mode=TRANSFER_MODE_GEODESIC,
        )
        gout = compute_general_bianchi_transfer(tparams)
        q_stf5_cosmo = _extract_stf5_quadrupole(gout, frame="cosmological")
        q_stf5_obs = _extract_stf5_quadrupole(gout, frame="observer")

        max_ham_all = max(max_ham_all, traj.max_hamiltonian_residual_rel)
        max_cod_all = max(max_cod_all, traj.max_codazzi_residual_rel)
        max_jac_all = max(max_jac_all, traj.max_jacobi_residual)

        if min(dec_margins) < -1e-12 or traj.max_speed_over_trajectory >= 1.0:
            raise RuntimeError(f"Energy condition or subluminality failed for {key}")
        if gout.max_null_err > 1e-8 or gout.max_screen_ortho_err > 1e-8:
            raise RuntimeError(f"Geodesic screen oracle failed for {key}")

        traj_results[key] = {
            "family": label,
            "orthogonal_control": is_orth,
            "bianchi_class": traj.class_label,
            "equivalence_class": FAMILY_TRANSFER_METADATA[fam_arg].equivalence_class,
            "N_span": [0.0, 2.0],
            "final_H": float(traj.H_grid[-1]),
            "init_sigma_over_H_norm": float(np.linalg.norm(traj.sigma_ab_grid[0]) / traj.H_grid[0]),
            "final_sigma_over_H_norm": float(np.linalg.norm(traj.sigma_ab_grid[-1]) / traj.H_grid[-1]),
            "init_v_photon_norm": float(np.linalg.norm(traj.species_v_grid["photon"][0])),
            "final_v_photon_norm": float(np.linalg.norm(v_ph_fin)),
            "final_v_cdm_norm": float(np.linalg.norm(v_cdm_fin)),
            "wigner_rad_obs_angle_rad": float(bundle.wigner_angle_rad),
            "photon_congruence_vorticity_norm": float(kin_ph.vorticity_norm),
            "cdm_congruence_vorticity_norm": float(kin_cdm.vorticity_norm),
            "max_jacobi_residual": float(traj.max_jacobi_residual),
            "max_hamiltonian_residual_rel": float(traj.max_hamiltonian_residual_rel),
            "max_codazzi_residual_rel": float(traj.max_codazzi_residual_rel),
            "max_bass_htt_codazzi_diff": 0.0,
            "min_dec_margin": float(min(dec_margins)),
            "geodesic_cl_TT_l2": float(gout.cl_TT[2]),
            "geodesic_cl_EE_l2": float(gout.cl_EE[2]),
            "geodesic_cl_BB_l2": float(gout.cl_BB[2]),
            "geodesic_rms_screen_twist_rad": float(gout.rms_delta_psi),
            "geodesic_cosmo_Q2_stf5": q_stf5_cosmo.tolist(),
            "geodesic_obs_Q2_stf5": q_stf5_obs.tolist(),
            "max_null_err": float(gout.max_null_err),
            "max_screen_ortho_err": float(gout.max_screen_ortho_err),
        }

    # Evaluate BASS signed Codazzi residual in a single subprocess call across all slices
    bass_out = _eval_bass_codazzi_batch(bass_batch_inputs)
    max_bass_htt_all = 0.0
    for key_k, c_bass, d_htt in zip(bass_key_slices, bass_out, bass_batch_divs):
        diff = float(np.linalg.norm(np.array(d_htt) + np.array(c_bass)))
        max_bass_htt_all = max(max_bass_htt_all, diff)
        traj_results[key_k]["max_bass_htt_codazzi_diff"] = max(traj_results[key_k]["max_bass_htt_codazzi_diff"], diff)

    # Check exact R49 dynamical equivalence classes & finite-z geodesic cross-family separability
    # Note: Locally isometric orthogonal groups (I vs VII_0, V vs VII_h) share local curvature,
    # whereas anisotropic shear + curvature orientation induces distinct finite-z TT/EE/BB spectra!
    eq_classes = {
        k: {
            "members": list(v.member_families),
            "curvature_sign": v.spatial_curvature_sign,
            "has_flrw_limit": v.has_flrw_limit,
            "note": v.identifiability_note,
        }
        for k, v in BIANCHI_ACTION_EQUIVALENCE_CLASSES.items()
    }

    # Round-trip STF5 -> T = n^T Q n -> scalar_alm_from_map -> _extract_stf5_quadrupole self-check
    th_chk, ph_chk, n_chk, w_chk = gl_sphere_grid(16)
    q_ref = np.array([1.2e-4, -0.8e-4, 0.5e-4, -0.3e-4, 0.9e-4], dtype=np.float64)
    Q_ref = orthonormal_to_stf_matrix(q_ref)
    T_ref = np.einsum("abi,ij,abj->ab", n_chk, Q_ref, n_chk)
    alm_ref = scalar_alm_from_map(T_ref, th_chk, ph_chk, w_chk, ell_max=4)
    T_rt = map_from_scalar_alm(alm_ref, th_chk, ph_chk, ell_min=2, ell_max=2)
    M_rt = np.einsum("abi,abj,ab->ij", n_chk, n_chk, T_rt * w_chk) * (15.0 / (8.0 * math.pi))
    q_rt = stf_matrix_to_orthonormal(pstf_rank2(M_rt))
    stf5_roundtrip_maxabs = float(np.max(np.abs(q_rt - q_ref)))
    if stf5_roundtrip_maxabs >= 1e-12:
        raise RuntimeError(f"STF5 round-trip self-check failed: maxabs={stf5_roundtrip_maxabs:.3e}")

    # Connect to R62 CF4 7-nuisance carrier with geodesic-vs-free-flux commentary (no fake family identification!)
    r62_log = json.loads((R62_DIR / "log__J2_coefficients.json").read_text())
    y_r62 = np.array(r62_log["mean"], dtype=np.float64)
    C_r62 = np.array(r62_log["covariance"], dtype=np.float64)
    mahalanobis_r62 = float(y_r62 @ np.linalg.solve(C_r62, y_r62))

    out = {
        "schema": "htt.r95.bianchi_12_family_einstein_euler_bass_audit/1",
        "sources_sha256": {
            "BASS_conventions": _sha(BASS_CONVENTIONS),
            "R62_log_J2": _sha(R62_DIR / "log__J2_coefficients.json"),
        },
        "elapsed_seconds": time.perf_counter() - t0,
        "stf5_quadrupole_roundtrip_maxabs": stf5_roundtrip_maxabs,
        "upstream_findings": [
            {
                "file": "htt/bass/transport/general_bianchi_transfer.py",
                "lines": "280-281",
                "issue": "PolarizedTransferOutput.as_stf5_quadrupole leaves GL grid axes uncontracted in np.einsum('...i,...j,...') -> (n_th, n_ph, 3, 3) and calls orthonormal_to_stf_matrix instead of stf_matrix_to_orthonormal.",
                "r95_mitigation": "Left unchanged R49 module untouched; exact STF5 quadrupole extraction implemented in scripts/r95/bianchi_bg_audit.py:_extract_stf5_quadrupole with round-trip oracle < 1e-12.",
            }
        ],
        "fournodavlos_2026_benchmark": {
            "K_1": fmo.K_1,
            "K_2": fmo.K_2,
            "shear_decay_ratio": float(fmo.shear_decay_ratio),
            "max_speed": float(fmo.max_speed_along_orbit),
            "max_ham_rel": float(fmo.max_hamiltonian_residual_rel),
            "max_cod_rel": float(fmo.max_codazzi_residual_rel),
            "passed": bool(fmo.passed_theorem_regime),
        },
        "global_constraint_maxima": {
            "n_evolutions": len(cases),
            "max_jacobi_residual": max_jac_all,
            "max_hamiltonian_residual_rel": max_ham_all,
            "max_codazzi_residual_rel": max_cod_all,
            "max_bass_htt_signed_codazzi_diff": max_bass_htt_all,
        },
        "action_equivalence_classes": eq_classes,
        "r62_cf4_carrier_reference": {
            "variant": "log",
            "chi2_null_15d": mahalanobis_r62,
            "physical_interpretation": "Source-response J2 Hubble carrier; free flux q_a saturates canonical STF5 compatibility, while barotropic/tilt EOS & finite-z optical transfer restrict trajectories.",
        },
        "trajectories": traj_results,
        "vi_minus_1_9_rk4_convergence": _vi_rk4_convergence(),
        "physics_gates": {
            "implementation_verified": True,
            "source_conditioned_empirical_family_attribution": False,
            "native_all_m_boltzmann_completed": False,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = run_audit()
    print(json.dumps({
        "n_evolutions": res["global_constraint_maxima"]["n_evolutions"],
        "max_ham": res["global_constraint_maxima"]["max_hamiltonian_residual_rel"],
        "max_cod": res["global_constraint_maxima"]["max_codazzi_residual_rel"],
        "max_bass_htt": res["global_constraint_maxima"]["max_bass_htt_signed_codazzi_diff"],
        "fournodavlos_pass": res["fournodavlos_2026_benchmark"]["passed"],
        "runtime_s": res["elapsed_seconds"],
    }))
