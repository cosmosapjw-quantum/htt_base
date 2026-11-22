"""R95 Step 3B (G07_BIANCHI / REC / REI): Source-qualified HyRec-2 recombination + tanh reionization + Bianchi shear Peebles bridge.

Replaces R94's constant-ionized assumption (n_e0=2e-7 cm^-3, x_e=1) with:
  1. Source-qualified HyRec-2 Planck 2018 recombination table (htt/bass/recombination/fixtures/recombination_ref_planck2018.csv)
  2. Planck 2018 tanh H+HeI+HeII reionization extension (z_rei_H=7.67, z_rei_HeII=3.5) via htt/bass/recombination/reionization.py
  3. Anisotropic Bianchi expansion H(z) = H_FLRW * sqrt(1 + Sigma^2(z)) Peebles cross-check via BASS bianchi/thermo/recombination.py
  4. Provenance lock to REC AxisymmetricBianchiIBackground & REI THOMSON_PAIR_RESULT.json (explicitly preserving
     REI_electron_history_qualified=False since REI provides a pair-difference envelope, not a full CMB z-history).
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

ROOT = Path(__file__).resolve().parents[2]
REC_SRC = Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi/src")
for p in (str(REC_SRC), str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bass.recombination.recombination_ingest import (
    build_interpolators,
    find_last_scattering_redshift,
    find_visibility_peak,
    load_recombination_table,
    validate_recombination_table,
)
from bass.recombination.reionization import (
    C_LIGHT,
    SEC_PER_MPC,
    SIGMA_T,
    ReionizationParameters,
    compute_reionization_tau,
    cosmology_from_metadata,
    extend_table_with_reionization,
)
from full_bianchi_hyrec.background.axisymmetric_bianchi_i import AxisymmetricBianchiIBackground

import subprocess

HYREC_CSV = ROOT / "htt/bass/recombination/fixtures/recombination_ref_planck2018.csv"
REI_PAIR = Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi/research/flrw_pair_observable_20261016/results/THOMSON_PAIR_RESULT.json")
REC_PR05B2 = Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi/data/pr05b2_source_history_v060.npz")
BASS_ROOT = Path("/home/cosmosapjw/bass")
BASS_PY = BASS_ROOT / ".venv/bin/python"
OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122/G07_BIANCHI_REC_REI_OPTICS.json"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _eval_bass_peebles_in_venv(cosmo_dict: dict, sigmas: tuple[float, ...]) -> dict:
    """Execute BASS bianchi.thermo.recombination (requires jax in BASS's own venv) cleanly read-only."""
    code = "\n".join([
        "import json, math, sys, numpy as np",
        "from bianchi.thermo.recombination import peebles_xe, optical_depth_and_visibility",
        "from bianchi.physical import units as U",
        "inp = json.load(sys.stdin)",
        "c = inp['cosmo']",
        "h = c['h']",
        "Obh2 = c['Omega_b'] * h * h",
        "Omh2 = c['Omega_m'] * h * h",
        "Om = c['Omega_m']",
        "Or = c['Omega_r']",
        "OL = c['Omega_Lambda']",
        "H0 = 100.0 * h / U.MPC_KM",
        "z_pb = np.linspace(1600.0, 200.0, 2801)",
        "out = {}",
        "z_flrw = None",
        "for s0 in inp['sigmas']:",
        "    # Bianchi I Friedmann shear density: Omega_sigma0 = Sigma_0^2 = (sigma_0/H_0)^2 / 6",
        "    s2 = (s0 * s0) / 6.0",
        "    Ha = lambda z, _s=s2: H0 * np.sqrt(Or * (1 + np.asarray(z)) ** 4 + Om * (1 + np.asarray(z)) ** 3 + OL + _s * (1 + np.asarray(z)) ** 6)",
        "    xe = peebles_xe(z_pb, Omega_b_h2=Obh2, Omega_m_h2=Omh2, h=h, T0_K=c['T_cmb'], H_of_z=Ha)",
        "    opt = optical_depth_and_visibility(z_pb, xe, Omega_b_h2=Obh2, h=h, Omega_m_h2=Omh2, T0_K=c['T_cmb'], H_of_z=Ha)",
        "    zs = float(opt['z_star'])",
        "    g_arr = np.asarray(opt['g'], float); z_arr = np.asarray(opt['z'], float)",
        "    kpk = int(np.argmax(g_arr))",
        "    if 0 < kpk < len(z_arr) - 1:",
        "        denom = (g_arr[kpk-1] - 2.0*g_arr[kpk] + g_arr[kpk+1])",
        "        zs_interp = float(z_arr[kpk] + 0.5 * (g_arr[kpk-1] - g_arr[kpk+1]) / denom * (z_arr[1] - z_arr[0])) if abs(denom) > 0 else zs",
        "    else:",
        "        zs_interp = zs",
        "    if z_flrw is None:",
        "        z_flrw = zs_interp",
        "    out[f'{s0:.0e}'] = {",
        "        'sigma0_over_H0': s0,",
        "        'omega_sigma0': s2,",
        "        'H_ratio_at_z1100': float(Ha(1100.0) / (H0 * math.sqrt(Or * 1101 ** 4 + Om * 1101 ** 3 + OL))),",
        "        'peebles_z_star_grid': zs,",
        "        'peebles_z_star_quadratic_peak': zs_interp,",
        "        'delta_z_star_vs_flrw': zs_interp - z_flrw,",
        "        'freezeout_xe_z200': float(xe[-1]),",
        "    }",
        "print(json.dumps(out))",
    ])
    proc = subprocess.run(
        [str(BASS_PY), "-B", "-c", code],
        input=json.dumps({"cosmo": cosmo_dict, "sigmas": list(sigmas)}),
        cwd=str(BASS_ROOT),
        env={"PATH": "/usr/bin:/bin", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "JAX_PLATFORMS": "cpu"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(proc.stdout)


def build_optics_profile() -> dict:
    t0 = time.perf_counter()
    # 1. HyRec-2 Planck 2018 source-qualified recombination table
    recomb = load_recombination_table(HYREC_CSV)
    errs = validate_recombination_table(recomb)
    if errs:
        raise RuntimeError(f"HyRec table validation failed: {errs}")
    cosmo = cosmology_from_metadata(recomb.metadata)

    # 2. Extend down to z=0 with Planck 2018 tanh reionization
    reion_params = ReionizationParameters(
        z_reion_H=7.67, delta_z_H=0.5, z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=True
    )
    full_tab = extend_table_with_reionization(
        recomb, reion_params, cosmology=cosmo, z_low=0.0, n_low_points=400
    )
    errs_full = validate_recombination_table(full_tab)
    if errs_full:
        raise RuntimeError(f"Extended table validation failed: {errs_full}")

    interp = build_interpolators(full_tab)
    z_star, g_star_Mpc = find_visibility_peak(interp, z_search_lo=800.0, z_search_hi=1400.0, n_samples=4000)
    z_kappa1 = find_last_scattering_redshift(interp, target_kappa=1.0)
    tau_reion = compute_reionization_tau(full_tab, z_high_cutoff=30.0)

    # Check conformal-time normalization: \int g(z) d\eta = \int [g(z)/H_Mpc(z)] dz == 1 - exp(-kappa_max)
    # Use log-spaced / dense grid through recombination + reionization for quadrature accuracy
    z_dense = np.unique(np.concatenate([
        np.linspace(0.0, 20.0, 800),
        np.linspace(20.0, 600.0, 600),
        np.linspace(600.0, 1600.0, 4000),
        np.linspace(1600.0, float(full_tab.z_max), 1000),
    ]))
    H_dense_Mpc = cosmo.H_of_z(z_dense) * SEC_PER_MPC
    g_dense = interp.query_visibility(z_dense)
    kappa_max = float(full_tab.kappa[-1])
    norm_integral = float(np.trapezoid(g_dense / H_dense_Mpc, z_dense))
    expected_norm = 1.0 - math.exp(-kappa_max)
    norm_err = abs(norm_integral - expected_norm)

    # Compute conformal time eta(z) from today eta(0) backwards / relative eta_0 - eta(z) = \int_0^z dz'/H_Mpc(z')
    inv_H = 1.0 / H_dense_Mpc
    chi_Mpc = np.concatenate([[0.0], np.cumsum(0.5 * (inv_H[1:] + inv_H[:-1]) * np.diff(z_dense))])
    eta_0_Mpc = float(chi_Mpc[-1])

    # 3. Cross-check anisotropic Bianchi expansion effect on Peebles recombination using BASS thermo/recombination.py
    cosmo_dict = {
        "h": float(cosmo.h), "T_cmb": float(cosmo.T_cmb), "Omega_b": float(cosmo.Omega_b),
        "Omega_m": float(cosmo.Omega_m), "Omega_r": float(cosmo.Omega_r), "Omega_Lambda": float(cosmo.Omega_Lambda),
    }
    shear_sensitivity = _eval_bass_peebles_in_venv(cosmo_dict, (0.0, 1.0e-5, 1.0e-4, 1.0e-3, 1.0e-2))

    # 4. REC positive-clock & REI envelope provenance bridge
    bg_rec_0 = AxisymmetricBianchiIBackground(q_ref=0.0, cells=1024)
    bg_rec_s = AxisymmetricBianchiIBackground(q_ref=1e-6, cells=1024)
    iv0 = bg_rec_0.interval(1.0 / 21.0, 0.2)
    ivs = bg_rec_s.interval(1.0 / 21.0, 0.2)
    rei_data = json.loads(REI_PAIR.read_text())
    with np.load(REC_PR05B2, allow_pickle=False) as pr5:
        rec_pr5_info = {"schema": str(pr5["schema"]), "completeness": str(pr5["completeness"]), "n_eta": int(len(pr5["eta"]))}

    out = {
        "schema": "htt.r95.bianchi_rec_rei_optics_bridge/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "sources_sha256": {
            "hyrec2_planck2018_csv": _sha(HYREC_CSV),
            "rei_thomson_pair_json": _sha(REI_PAIR),
            "rec_pr05b2_npz": _sha(REC_PR05B2),
        },
        "cosmology_planck2018": {
            "h": cosmo.h, "T_cmb_K": cosmo.T_cmb, "Omega_b": cosmo.Omega_b,
            "Y_He": cosmo.Y_He, "Omega_m": cosmo.Omega_m, "Omega_r": cosmo.Omega_r, "Omega_Lambda": cosmo.Omega_Lambda,
            "n_H0_per_m3": cosmo.n_H_today,
        },
        "hyrec2_plus_tanh_reionization": {
            "n_points": full_tab.n_points,
            "z_range": [full_tab.z_min, full_tab.z_max],
            "reion_params": {
                "z_reion_H": reion_params.z_reion_H, "delta_z_H": reion_params.delta_z_H,
                "z_reion_HeII": reion_params.z_reion_HeII, "include_HeII": reion_params.include_HeII,
            },
            "tau_reion_z0_to_30": tau_reion,
            "z_visibility_peak": z_star,
            "g_visibility_peak_Mpc_inv": g_star_Mpc,
            "z_kappa_eq_1": z_kappa1,
            "kappa_z_max": kappa_max,
            "conformal_visibility_integral": norm_integral,
            "expected_1_minus_exp_minus_kappa_max": expected_norm,
            "visibility_normalization_abs_error": norm_err,
            "comoving_distance_to_zmax_Mpc": eta_0_Mpc,
            "comoving_distance_to_zstar_Mpc": float(np.interp(z_star, z_dense, chi_Mpc)),
            "x_e_at_z0": float(full_tab.x_e[0]),
            "x_e_at_z1089": float(interp.query_x_e(1089.0)),
            "positivity_and_monotonicity_ok": True,
        },
        "r94_constant_xe_control_vs_physical": {
            "r94_assumed_tau_z20_to_z4": 0.18393,
            "physical_kappa_z20": float(interp.query_kappa(20.0)),
            "physical_tau_reion": tau_reion,
            "delta_z_kappa_20": "R94 used constant n_e0=2e-7 cm^-3, x_e=1; R95 replaces with HyRec-2 + Planck2018 tanh reionization",
        },
        "bianchi_anisotropic_peebles_sensitivity": shear_sensitivity,
        "rec_and_rei_provenance": {
            "rec_bianchi_i_source_sha256": bg_rec_0.source_sha256,
            "rec_delta_t_flrw_z20_to_z4_s": iv0.delta_t_s,
            "rec_delta_b_shear_q1e_6": ivs.delta_b,
            "rec_pr05b2": rec_pr5_info,
            "rei_thomson_pair_q_envelope": float(rei_data["optical_depth_envelope"]["q"]),
            "REI_full_cmb_electron_history_qualified": False,
            "anisotropic_reionization_modeled": False,
        },
    }
    if norm_err > 2e-3 or not (0.04 < tau_reion < 0.08) or not (1070 < z_star < 1110):
        raise RuntimeError(f"Physical visibility check failed: norm_err={norm_err}, tau={tau_reion}, z*={z_star}")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = build_optics_profile()
    h = res["hyrec2_plus_tanh_reionization"]
    print(json.dumps({
        "z_star": h["z_visibility_peak"],
        "tau_reion": h["tau_reion_z0_to_30"],
        "vis_norm": h["conformal_visibility_integral"],
        "norm_err": h["visibility_normalization_abs_error"],
        "runtime_s": res["elapsed_seconds"],
    }))
