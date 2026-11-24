#!/usr/bin/env python3
"""C4: Open-dust VII_h (Omega0 in {0.3,0.5,0.7}, x in {0.62,1.0}) through R108 S4 comparator at l<=64."""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import json
import math
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import healpy as hp
import numpy as np

from scripts.r108 import s4_bjs_comparator as s4
from scripts.r109.commander_native import modes as parse_modes
from scripts.r111.c1_visibility_hyrec import BASS_BIN, sha256_file

ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r111/c4_bjs_highl")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R111_LOCAL_HIGHL_NATIVE_20261124/C4_BJS_HIGHL.json"
)

CASES = [
    (0.3, 0.62),
    (0.3, 1.0),
    (0.5, 0.62),
    (0.5, 1.0),
    (0.7, 0.62),
    (0.7, 1.0),
]
Z_E = 1100.0
SIGMA0 = 1e-8
NSIDE = 64
LMAX_LOS = 64
GRID_NSIDE = 16
N_STARTS = 8


def unpack_g14(g14: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    s11, s22, s12, s13, s23 = g14[0], g14[1], g14[2], g14[3], g14[4]
    s33 = -(s11 + s22)
    sig6 = np.array([s11, s22, s33, s12, s13, s23], dtype=np.float64)
    a3 = np.array([g14[5], g14[6], g14[7]], dtype=np.float64)
    n6 = np.array([g14[8], g14[9], g14[10], g14[11], g14[12], g14[13]], dtype=np.float64)
    return sig6, a3, n6


def run_single_case(args: tuple[float, float]) -> dict:
    omega0, x = args
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    tag = f"O{omega0:.1f}_x{x:.2f}"
    cdir = RAW_ROOT / tag
    cdir.mkdir(parents=True, exist_ok=True)

    N_E = -math.log1p(Z_E)
    st, st_info = s4.build_bjs_state(omega0, x, SIGMA0)
    geo, bg = s4.evolve_background(st, omega0, x, N_E, M=1400, rtol=1e-12, atol=1e-16)
    idx_E = int(np.argmin(np.abs(geo["geometry_N"] - N_E)))
    assert abs(float(geo["geometry_N"][idx_E]) - N_E) < 1e-12
    sig6, a3, n6 = unpack_g14(geo["geometry14"][idx_E])

    lie_path = cdir / "bjs_init.lie"
    lie_path.write_text(
        "shear " + " ".join(f"{v:.17e}" for v in sig6) + "\n"
        + "n " + " ".join(f"{v:.17e}" for v in n6) + "\n"
        + "a " + " ".join(f"{v:.17e}" for v in a3) + "\n",
        encoding="utf-8",
    )

    bass_dir = cdir / "bass_normal"
    if bass_dir.exists():
        shutil.rmtree(bass_dir)
    duration = math.log1p(Z_E)
    env = dict(os.environ)
    env["RAYON_NUM_THREADS"] = "4"
    t0 = time.perf_counter()
    subprocess.run(
        [
            str(BASS_BIN), "--out", str(bass_dir),
            "--lie-ic", str(lie_path),
            "--feedback", "active",
            "--dust-fraction", "0.9999",
            "--tau", "0.0",
            "--duration", repr(duration),
            "--steps", "2800",
            "--nmu", "12", "--nphi", "28", "--lmax", "4",
            "--los-lmax", str(LMAX_LOS),
            "--los-ntheta", "128",
            "--los-nphi", "256",
            "--lie-update", "congruence",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    bass_wall = time.perf_counter() - t0

    diag = np.loadtxt(bass_dir / "diagnostics.tsv", skiprows=1)
    rtxt = dict(
        line.split("=", 1) for line in (bass_dir / "run.txt").read_text().splitlines() if "=" in line
    )
    raw_modes = (bass_dir / "los_modes.tsv").read_bytes()
    ell_out, alm_arr = parse_modes(raw_modes)
    assert ell_out == LMAX_LOS
    y_bass = hp.alm2map(alm_arr[0], nside=NSIDE, lmax=LMAX_LOS, pol=False)
    y_protocol = y_bass - y_bass.mean()

    # Ray-traced emitter directions nE on geo to form exact Doppler-corrected BASS map,
    # using BASS's own host_beta today & at emission!
    dirs = s4.healpix_directions(NSIDE)
    nE = None
    for k_step, n_k, _delta_k, _chi in s4.trace_rays(
        dirs, np.array([N_E - 1e-3, N_E, 0.0]), geo["geometry_N"], geo["geometry14"], max_step=0.05
    ):
        if k_step == 1:
            nE = n_k
    v0_bass = np.asarray(diag[-1, 18:21], dtype=np.float64)
    vE_bass = np.asarray(diag[0, 18:21], dtype=np.float64)
    g0 = 1.0 / math.sqrt(1.0 - float(v0_bass @ v0_bass))
    gE = 1.0 / math.sqrt(1.0 - float(vE_bass @ vE_bass))
    fac_doppler = g0 * (1.0 + dirs @ v0_bass) * (1.0 + y_bass) / (gE * (1.0 + nE @ vE_bass))
    y_doppler = fac_doppler - fac_doppler.mean()

    # Verify BASS --observer-beta flag reproduces observer Doppler boost directly
    bass_obs_dir = cdir / "bass_obs_boost"
    if bass_obs_dir.exists():
        shutil.rmtree(bass_obs_dir)
    subprocess.run(
        [
            str(BASS_BIN), "--out", str(bass_obs_dir),
            "--lie-ic", str(lie_path),
            "--feedback", "active",
            "--dust-fraction", "0.9999",
            "--tau", "0.0",
            "--observer-beta", f"{v0_bass[0]:.17e},{v0_bass[1]:.17e},{v0_bass[2]:.17e}",
            "--duration", repr(duration),
            "--steps", "2800",
            "--nmu", "12", "--nphi", "28", "--lmax", "4",
            "--los-lmax", str(LMAX_LOS),
            "--los-ntheta", "128",
            "--los-nphi", "256",
            "--lie-update", "congruence",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    _, alm_obs = parse_modes((bass_obs_dir / "los_modes.tsv").read_bytes())
    y_bass_obs = hp.alm2map(alm_obs[0], nside=NSIDE, lmax=LMAX_LOS, pol=False)
    y_bass_obs -= y_bass_obs.mean()
    y_analytic_obs = (1.0 + dirs @ v0_bass) * (1.0 + y_bass) - 1.0
    y_analytic_obs -= y_analytic_obs.mean()
    obs_boost_rel_diff = float(np.linalg.norm(y_bass_obs - y_analytic_obs) / np.linalg.norm(y_analytic_obs))

    # Run S4 comparator fits (mcewen2006 & kogut1997, kappa=+1 and -1, on both protocol & doppler)
    coarse_nside = max(NSIDE // 2, 8)
    dirs_c = s4.healpix_directions(coarse_nside)
    fit_maps = (("protocol", y_protocol), ("doppler", y_doppler))
    fits = {}
    for variant in s4.VARIANTS:
        tmpl = s4.TemplateSky(omega0, x, variant, z_emission=Z_E)
        for map_label, ymap in fit_maps:
            yc = hp.ud_grade(ymap, coarse_nside, order_in="RING", order_out="RING")
            for kappa in s4.HANDEDNESS:
                r = s4.fit_rotation(
                    tmpl, kappa, dirs, ymap,
                    grid_nside=GRID_NSIDE, n_starts=N_STARTS,
                    dirs_coarse=dirs_c, y_coarse=yc,
                )
                d = np.asarray(r["axis"])
                r["variant"] = variant
                r["map"] = map_label
                r["amp_over_sigma_perp"] = r["amp"] / SIGMA0
                r["amp_over_sigma_perp_times_sqrt2"] = r["amp"] * math.sqrt(2.0) / SIGMA0
                r["template_axis_angle_to_plus_z_deg"] = s4.angle_deg(d, [0, 0, 1])
                r["template_axis_angle_to_minus_z_deg"] = s4.angle_deg(d, [0, 0, -1])
                fits[f"{map_label}|{variant}|{kappa:+d}"] = r

    return {
        "omega0": omega0,
        "x": x,
        "z_E": Z_E,
        "sigma0": SIGMA0,
        "nside": NSIDE,
        "los_lmax": LMAX_LOS,
        "bass_seconds": bass_wall,
        "bass_diagnostics": {
            "max_abs_gauss": float(np.max(np.abs(diag[:, 4]))),
            "max_abs_codazzi": float(np.max(np.abs(diag[:, 5:8]))),
            "max_abs_jacobi": float(np.max(np.abs(diag[:, 8]))),
            "lie_type_initial": rtxt["lie_type_initial"],
            "lie_type_final": rtxt["lie_type_final"],
            "lie_kappa_inverse_h_initial": rtxt["lie_kappa_inverse_h_initial"],
            "lie_kappa_inverse_h_final": rtxt["lie_kappa_inverse_h_final"],
            "los_max_landing_error": float(rtxt["los_max_landing_error"]),
            "initial_host_beta_bass": vE_bass.tolist(),
            "initial_v_E_bjs": np.asarray(geo["v_E"]).tolist(),
            "final_host_beta_bass": v0_bass.tolist(),
            "final_v_today_bjs": np.asarray(geo["v_today"]).tolist(),
            "los_modes_sha256": sha256_file(bass_dir / "los_modes.tsv"),
        },
        "observer_boost_check_rel_diff": obs_boost_rel_diff,
        "protocol_rms": float(np.std(y_protocol)),
        "doppler_rms": float(np.std(y_doppler)),
        "fits": fits,
    }


def main() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()
    with ProcessPoolExecutor(max_workers=6) as ex:
        case_list = list(ex.map(run_single_case, CASES))
    total_wall = time.perf_counter() - t_all

    summary_rows = []
    min_corr_protocol_mcewen = 1.0
    min_corr_protocol_kogut = 1.0
    min_corr_doppler_mcewen = 1.0
    for c in case_list:
        f = c["fits"]
        pm = f["protocol|mcewen2006|+1"]
        pk = f["protocol|kogut1997|+1"]
        dm = f["doppler|mcewen2006|+1"]
        dk = f["doppler|kogut1997|+1"]
        pm_neg = f["protocol|mcewen2006|-1"]
        min_corr_protocol_mcewen = min(min_corr_protocol_mcewen, pm["corr"])
        min_corr_protocol_kogut = min(min_corr_protocol_kogut, pk["corr"])
        min_corr_doppler_mcewen = min(min_corr_doppler_mcewen, dm["corr"])
        summary_rows.append({
            "omega0": c["omega0"],
            "x": c["x"],
            "protocol_mcewen_plus_corr": pm["corr"],
            "protocol_mcewen_minus_corr": pm_neg["corr"],
            "protocol_mcewen_resid_rms": pm["residual_rms"],
            "protocol_mcewen_resid_rel": pm["residual_rms_relative"],
            "protocol_kogut_plus_corr": pk["corr"],
            "doppler_mcewen_plus_corr": dm["corr"],
            "doppler_mcewen_resid_rms": dm["residual_rms"],
            "doppler_mcewen_resid_rel": dm["residual_rms_relative"],
            "doppler_kogut_plus_corr": dk["corr"],
            "doppler_kogut_resid_rel": dk["residual_rms_relative"],
            "observer_boost_check_rel_diff": c["observer_boost_check_rel_diff"],
        })

    assert min_corr_protocol_mcewen >= 0.999
    assert min_corr_doppler_mcewen >= 0.999

    out = {
        "schema": "htt.r111.c4_bjs_highl/1",
        "claim_ceiling": "deterministic single-history open-dust VII_h vs BJS template check; no ensemble p-value or family claim",
        "bass_binary_sha256": sha256_file(BASS_BIN),
        "total_wall_seconds": total_wall,
        "summary_table": summary_rows,
        "cases": case_list,
        "acceptance": {
            "min_corr_protocol_mcewen2006": min_corr_protocol_mcewen,
            "min_corr_protocol_kogut1997": min_corr_protocol_kogut,
            "min_corr_doppler_mcewen2006": min_corr_doppler_mcewen,
            "all_cases_ge_0p999_mcewen2006": bool(min_corr_protocol_mcewen >= 0.999 and min_corr_doppler_mcewen >= 0.999),
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON} in {total_wall:.1f}s")
    for r in summary_rows:
        print(
            f"  O={r['omega0']:.1f} x={r['x']:.2f}: proto(mc+)={r['protocol_mcewen_plus_corr']:.6f} "
            f"resid_rel={r['protocol_mcewen_resid_rel']:.3e} | dopp(mc+)={r['doppler_mcewen_plus_corr']:.6f} "
            f"resid_rel={r['doppler_mcewen_resid_rel']:.3e}"
        )


if __name__ == "__main__":
    main()
