#!/usr/bin/env python3
"""C4: Open-dust VII_h (Omega0 in {0.3,0.5,0.7}, x in {0.62,1.0}) on --route harmonic through R108 S4 comparator."""
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
from scripts.r111.c1_visibility_hyrec import sha256_file
from scripts.r111.c4_bjs_highl import CASES, GRID_NSIDE, LMAX_LOS, N_STARTS, NSIDE, SIGMA0, Z_E, unpack_g14

ROOT = Path(__file__).resolve().parents[2]
BASS_BIN = Path("/home/cosmosapjw/Downloads/htt_r114/bin/homogeneous_sky_r114")
R111_C4_ROOT = Path("/home/cosmosapjw/Downloads/htt_r111/c4_bjs_highl")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r114/c4_bjs_harmonic")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C4_BJS_HARMONIC_HIGHL.json"
)


def max_mode_rel(raw_a: bytes, raw_b: bytes) -> float:
    la, a = parse_modes(raw_a)
    lb, b = parse_modes(raw_b)
    assert la == lb
    scale = float(np.max(np.abs(a)))
    return float(np.max(np.abs(a - b)) / scale)


def run_case(args: tuple[float, float, int]) -> dict:
    omega0, x, harm_lmax = args
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    tag = f"O{omega0:.1f}_x{x:.2f}_L{harm_lmax}"
    cdir = RAW_ROOT / tag
    cdir.mkdir(parents=True, exist_ok=True)

    N_E = -math.log1p(Z_E)
    st, _ = s4.build_bjs_state(omega0, x, SIGMA0)
    geo, _ = s4.evolve_background(st, omega0, x, N_E, M=1400, rtol=1e-12, atol=1e-16)
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
            "--route", "harmonic",
            "--harmonic-lmax", str(harm_lmax),
            "--nmu", "8", "--nphi", "16", "--lmax", "4",
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

    with (bass_dir / "diagnostics.tsv").open() as f:
        dhead = f.readline().split()
        diag = np.loadtxt(f)
    dcol = {k: i for i, k in enumerate(dhead)}
    rtxt = dict(line.split("=", 1) for line in (bass_dir / "run.txt").read_text().splitlines() if "=" in line)

    raw_modes = (bass_dir / "los_modes.tsv").read_bytes()
    ell_out, alm_arr = parse_modes(raw_modes)
    assert ell_out == LMAX_LOS
    y_bass = hp.alm2map(alm_arr[0], nside=NSIDE, lmax=LMAX_LOS, pol=False)
    y_protocol = y_bass - y_bass.mean()

    dirs = s4.healpix_directions(NSIDE)
    nE = None
    for k_step, n_k, _delta_k, _chi in s4.trace_rays(
        dirs, np.array([N_E - 1e-3, N_E, 0.0]), geo["geometry_N"], geo["geometry14"], max_step=0.05
    ):
        if k_step == 1:
            nE = n_k
    v0_bass = np.asarray(diag[-1, dcol["host_beta_x"] : dcol["host_beta_z"] + 1], dtype=np.float64)
    vE_bass = np.asarray(diag[0, dcol["host_beta_x"] : dcol["host_beta_z"] + 1], dtype=np.float64)
    g0 = 1.0 / math.sqrt(1.0 - float(v0_bass @ v0_bass))
    gE = 1.0 / math.sqrt(1.0 - float(vE_bass @ vE_bass))
    fac_doppler = g0 * (1.0 + dirs @ v0_bass) * (1.0 + y_bass) / (gE * (1.0 + nE @ vE_bass))
    y_doppler = fac_doppler - fac_doppler.mean()

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
            "--duration", repr(duration),
            "--steps", "2800",
            "--route", "harmonic",
            "--harmonic-lmax", str(harm_lmax),
            "--nmu", "8", "--nphi", "16", "--lmax", "4",
            "--los-lmax", str(LMAX_LOS),
            "--los-ntheta", "128",
            "--los-nphi", "256",
            "--lie-update", "congruence",
            "--observer-beta", f"{v0_bass[0]:.17e},{v0_bass[1]:.17e},{v0_bass[2]:.17e}",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    _, alm_obs = parse_modes((bass_obs_dir / "los_modes.tsv").read_bytes())
    y_obs = hp.alm2map(alm_obs[0], nside=NSIDE, lmax=LMAX_LOS, pol=False)
    y_obs -= y_obs.mean()
    y_obs_ref = g0 * (1.0 + dirs @ v0_bass) * (1.0 + y_bass) - 1.0
    y_obs_ref -= y_obs_ref.mean()
    obs_boost_rel = float(np.linalg.norm(y_obs - y_obs_ref) / np.linalg.norm(y_obs_ref))

    coarse_nside = max(NSIDE // 2, 8)
    dirs_c = s4.healpix_directions(coarse_nside)
    fits = {}
    for variant in s4.VARIANTS:
        tmpl = s4.TemplateSky(omega0, x, variant, z_emission=Z_E)
        for mname, mmap in (("protocol", y_protocol), ("doppler", y_doppler)):
            yc = hp.ud_grade(mmap, nside_out=coarse_nside, order_in="RING", order_out="RING")
            for kappa in s4.HANDEDNESS:
                r = s4.fit_rotation(
                    tmpl, kappa, dirs, mmap,
                    grid_nside=GRID_NSIDE, n_starts=N_STARTS,
                    dirs_coarse=dirs_c, y_coarse=yc,
                )
                r["variant"] = variant
                r["map"] = mname
                fits[f"{mname}|{variant}|{kappa:+d}"] = r

    ray_ref_path = R111_C4_ROOT / f"O{omega0:.1f}_x{x:.2f}" / "bass_normal/los_modes.tsv"
    harm_vs_r111_rays = max_mode_rel(raw_modes, ray_ref_path.read_bytes()) if ray_ref_path.exists() else None

    return {
        "omega0": omega0,
        "x": x,
        "harmonic_lmax": harm_lmax,
        "bass_seconds": bass_wall,
        "lie_type": [rtxt["lie_type_initial"], rtxt["lie_type_final"]],
        "lie_h": [rtxt.get("lie_h_initial"), rtxt.get("lie_h_final")],
        "max_abs_gauss": float(np.max(np.abs(diag[:, dcol["gauss"]]))),
        "max_abs_codazzi": float(
            np.max(np.sqrt(diag[:, dcol["codazzi_x"]] ** 2 + diag[:, dcol["codazzi_y"]] ** 2 + diag[:, dcol["codazzi_z"]] ** 2))
        ),
        "min_screen": float(np.min(diag[:, dcol["min_screen_eigenvalue"]])),
        "los_max_landing_error": float(rtxt["los_max_landing_error"]),
        "observer_boost_check_rel_diff": obs_boost_rel,
        "harm_vs_r111_rays_los_max_rel": harm_vs_r111_rays,
        "fits": fits,
        "los_modes_sha256": sha256_file(bass_dir / "los_modes.tsv"),
    }


def main() -> None:
    if RAW_ROOT.exists():
        shutil.rmtree(RAW_ROOT)
    RAW_ROOT.mkdir(parents=True)
    jobs = [(om, xv, 32) for om, xv in CASES] + [(0.3, 0.62, 48)]
    t0 = time.monotonic()
    with ProcessPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(run_case, jobs))
    wall = time.monotonic() - t0
    l32 = [r for r in results if r["harmonic_lmax"] == 32]
    l48 = next(r for r in results if r["harmonic_lmax"] == 48)
    min_proto = min(r["fits"]["protocol|mcewen2006|+1"]["corr"] for r in l32)
    min_dopp = min(r["fits"]["doppler|mcewen2006|+1"]["corr"] for r in l32)
    out = {
        "schema": "htt.r114.c4_bjs_harmonic_highl/1",
        "claim_ceiling": "deterministic single-history native harmonic templates vs BJS S4 comparator; zero tuning",
        "binary_sha256": sha256_file(BASS_BIN),
        "total_wall_seconds": wall,
        "cases_l32": l32,
        "check_o0p3_x0p62_l48": l48,
        "acceptance": {
            "min_protocol_corr_mcewen2006": min_proto,
            "min_doppler_corr_mcewen2006": min_dopp,
            "all_cases_ge_0p999": min_proto >= 0.999 and min_dopp >= 0.999,
            "all_types_preserved": all(r["lie_type"][0] == r["lie_type"][1] for r in results),
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("C4 COMPLETE:", json.dumps(out["acceptance"], indent=2))


if __name__ == "__main__":
    main()
