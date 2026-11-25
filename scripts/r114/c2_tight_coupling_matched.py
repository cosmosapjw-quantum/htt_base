#!/usr/bin/env python3
"""C2: Tight-coupling start from z_emit >= 1600 (1600 & 1800) with --recombination matched."""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from scripts.r111.c1_visibility_hyrec import cosmology_anchors, load_rec_csv, sha256_file, write_hyrec_tsv
from scripts.r111.c3_long_highl_atlas import COMMON_SHEAR, FAMILIES_LIE

ROOT = Path(__file__).resolve().parents[2]
BASS_BIN = Path("/home/cosmosapjw/Downloads/htt_r114/bin/homogeneous_sky_r114")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r114/c2_tight_coupling")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C2_TIGHT_COUPLING_MATCHED.json"
)
F_NU = (0.227107317660239 * 3.03821934419124) / (1.0 + 0.227107317660239 * 3.03821934419124)


def run_job(out_dir: Path, args: list[str], rayon_threads: int = 4) -> dict:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    env = os.environ.copy()
    env["RAYON_NUM_THREADS"] = str(rayon_threads)
    t0 = time.monotonic()
    subprocess.run([str(BASS_BIN), "--out", str(out_dir), *args], check=True, capture_output=True, text=True, env=env)
    wall = time.monotonic() - t0
    with (out_dir / "diagnostics.tsv").open() as f:
        dhead = f.readline().split()
        drows = np.loadtxt(f)
    dcol = {k: i for i, k in enumerate(dhead)}
    rtxt = dict(line.split("=", 1) for line in (out_dir / "run.txt").read_text().splitlines() if "=" in line)
    out = {
        "wall_seconds": wall,
        "final_proper_depth": float(drows[-1, dcol["proper_depth"]]),
        "final_hubble_ratio": float(drows[-1, dcol["hubble_ratio"]]),
        "max_abs_gauss": float(np.max(np.abs(drows[:, dcol["gauss"]]))),
        "max_abs_codazzi": float(
            np.max(np.sqrt(drows[:, dcol["codazzi_x"]] ** 2 + drows[:, dcol["codazzi_y"]] ** 2 + drows[:, dcol["codazzi_z"]] ** 2))
        ),
        "min_screen": float(np.min(drows[:, dcol["min_screen_eigenvalue"]])),
        "delta_xe_final": float(rtxt["delta_xe_final"]),
        "diagnostics_sha256": sha256_file(out_dir / "diagnostics.tsv"),
        "modes_sha256": sha256_file(out_dir / "modes.tsv"),
    }
    rec_tsv = out_dir / "recombination.tsv"
    if rec_tsv.exists():
        with rec_tsv.open() as f:
            rhead = f.readline().split()
            rrows = np.loadtxt(f)
        rcol = {k: i for i, k in enumerate(rhead)}
        etas = rrows[:, rcol["eta"]]
        xet = rrows[:, rcol["xe_table"]]
        dxe = rrows[:, rcol["delta_xe"]]
        idx_peak = int(np.argmax(np.abs(dxe)))
        early = np.where(etas <= 1.0)[0]
        idx_early = int(early[np.argmax(np.abs(dxe[early]))]) if len(early) else idx_peak
        gt1 = xet >= 1.0 - 1e-12
        out["recombination"] = {
            "n_rows": int(len(rrows)),
            "n_xe_ge_1_rows": int(np.sum(gt1)),
            "max_abs_delta_xe_where_xe_ge_1": float(np.max(np.abs(dxe[gt1]))) if np.any(gt1) else None,
            "first_nonzero_delta_xe_eta": float(etas[np.argmax(dxe != 0.0)]) if np.any(dxe != 0.0) else None,
            "delta_xe_peak": {
                "eta": float(etas[idx_peak]),
                "xe_table": float(xet[idx_peak]),
                "delta_xe": float(dxe[idx_peak]),
                "relative": float(dxe[idx_peak] / xet[idx_peak]),
            },
            "delta_xe_peak_eta_le_1": {
                "eta": float(etas[idx_early]),
                "xe_table": float(xet[idx_early]),
                "delta_xe": float(dxe[idx_early]),
                "relative": float(dxe[idx_early] / xet[idx_early]),
            },
            "delta_xe_final": float(dxe[-1]),
            "recombination_sha256": sha256_file(rec_tsv),
        }
    if (out_dir / "los_cl.tsv").exists():
        cl = np.loadtxt(out_dir / "los_cl.tsv", skiprows=1)
        out["los_cl_l2_4_TT_EE_BB"] = {
            str(int(cl[l, 0])): [float(cl[l, 1]), float(cl[l, 4]), float(cl[l, 6])] for l in range(2, min(5, len(cl)))
        }
    return out


def base_args(tsv: Path, anc: dict[str, float], steps: int, route: str, matched: bool, t_unit_k: float) -> list[str]:
    args = [
        "--duration", repr(anc["duration"]),
        "--steps", str(steps),
        "--feedback", "recoil",
        "--collision", "sdirk2",
        "--lie-update", "congruence",
        "--omega-lambda", repr(anc["omega_lambda_emit"]),
        "--dust-fraction", repr(anc["dust_fraction"]),
        "--baryon-fraction", "0.157",
        "--neutrino-fraction", repr(F_NU),
        "--ionization", str(tsv),
        "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
        "--h-emit-s", repr(anc["h_emit_s"]),
        "--observer-frame", "host",
        "--lmax", "4",
    ]
    if route == "harmonic":
        args += ["--route", "harmonic", "--harmonic-lmax", "16", "--nmu", "8", "--nphi", "16"]
    else:
        args += ["--route", "rays", "--nmu", "12", "--nphi", "28"]
    if matched:
        args += ["--recombination", "matched", "--t-unit-k", repr(t_unit_k)]
    return args


def main() -> None:
    if RAW_ROOT.exists():
        shutil.rmtree(RAW_ROOT)
    RAW_ROOT.mkdir(parents=True)
    rows, rec_sha = load_rec_csv()

    tables = {}
    anchors = {}
    for z_emit in (1600, 1800):
        tsv = RAW_ROOT / f"hyrec_xe_{z_emit}.tsv"
        write_hyrec_tsv(rows, z_emit, tsv)
        tables[z_emit] = tsv
        anchors[z_emit] = cosmology_anchors(z_emit)

    # Lie file for VIIh small data
    n6, a3, _, _ = FAMILIES_LIE["VIIh"]
    viih_lie = RAW_ROOT / "viih_small.lie"
    viih_lie.write_text(f"shear {COMMON_SHEAR}\nn {n6}\na {a3}\n", encoding="utf-8")

    # 1. FLRW step-halving 2nd-order test at z_emit=1600 and z_emit=1800 (rays & harmonic)
    flrw_tasks = []
    for z_emit in (1600, 1800):
        anc = anchors[z_emit]
        t_unit = 2.72548 * (1.0 + z_emit)
        for route in ("rays", "harmonic"):
            for steps in (512, 1024, 2048, 4096):
                name = f"flrw_z{z_emit}_{route}_s{steps}"
                args = ["--family", "FLRW", "--shear", "0.0", *base_args(tables[z_emit], anc, steps, route, True, t_unit)]
                flrw_tasks.append((z_emit, route, steps, name, args))

    flrw_out: dict[int, dict[str, dict[int, dict]]] = {1600: {"rays": {}, "harmonic": {}}, 1800: {"rays": {}, "harmonic": {}}}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [(item, ex.submit(run_job, RAW_ROOT / item[3], item[4], 4)) for item in flrw_tasks]
        for (z_emit, route, steps, name, _), fut in futs:
            flrw_out[z_emit][route][steps] = fut.result()

    flrw_orders = {}
    for z_emit in (1600, 1800):
        flrw_orders[str(z_emit)] = {}
        for route in ("rays", "harmonic"):
            by_s = flrw_out[z_emit][route]
            vals = [abs(by_s[s]["delta_xe_final"]) for s in (512, 1024, 2048, 4096)]
            peaks = [abs(by_s[s]["recombination"]["delta_xe_peak"]["delta_xe"]) for s in (512, 1024, 2048, 4096)]
            flrw_orders[str(z_emit)][route] = {
                "steps": [512, 1024, 2048, 4096],
                "abs_delta_xe_final": vals,
                "final_halving_ratios": [vals[i] / vals[i + 1] if vals[i + 1] > 0 else None for i in range(3)],
                "abs_delta_xe_peak": peaks,
                "peak_halving_ratios": [peaks[i] / peaks[i + 1] if peaks[i + 1] > 0 else None for i in range(3)],
                "runs": {str(s): by_s[s] for s in (512, 1024, 2048, 4096)},
            }

    # 2. Tilted anisotropic tight-coupling histories (I tilted 1e-3,0,0 & VIIh small) at z_emit=1600 & 1800
    aniso_specs = []
    for z_emit in (1600, 1800):
        anc = anchors[z_emit]
        t_unit = 2.72548 * (1.0 + z_emit)
        # Type I tilted
        for route in ("rays", "harmonic"):
            for matched in (False, True):
                mode = "matched" if matched else "table"
                tag = f"I_tilt_z{z_emit}_{route}_{mode}"
                args = [
                    "--family", "I", "--shear", "0.0", "--dust-beta", "1e-3,0,0",
                    "--los-lmax", "16", "--los-ntheta", "24", "--los-nphi", "48",
                    *base_args(tables[z_emit], anc, 2048, route, matched, t_unit),
                ]
                aniso_specs.append((tag, args))
        # VIIh small Lie
        for route in ("rays", "harmonic"):
            for matched in (False, True):
                mode = "matched" if matched else "table"
                tag = f"VIIh_small_z{z_emit}_{route}_{mode}"
                args = [
                    "--lie-ic", str(viih_lie),
                    "--los-lmax", "32", "--los-ntheta", "48", "--los-nphi", "96",
                    *base_args(tables[z_emit], anc, 2048, route, matched, t_unit),
                ]
                aniso_specs.append((tag, args))

    aniso_runs = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [(tag, ex.submit(run_job, RAW_ROOT / tag, args, 4)) for tag, args in aniso_specs]
        for tag, fut in futs:
            aniso_runs[tag] = fut.result()

    # Check acceptance summaries
    ratios_ok = all(
        all(3.5 <= r <= 4.5 for r in flrw_orders[str(z)][rt]["final_halving_ratios"])
        for z in (1600, 1800)
        for rt in ("rays", "harmonic")
    )
    xe_gt1_zero_ok = all(
        aniso_runs[tag]["recombination"]["max_abs_delta_xe_where_xe_ge_1"] == 0.0
        for tag in aniso_runs
        if "_z1800_" in tag and tag.endswith("_matched")
    ) and all(
        flrw_out[1800][rt][s]["recombination"]["max_abs_delta_xe_where_xe_ge_1"] == 0.0
        for rt in ("rays", "harmonic")
        for s in (512, 1024, 2048, 4096)
    )

    out = {
        "schema": "htt.r114.c2_tight_coupling_matched/1",
        "claim_ceiling": "deterministic single-history native outputs; zero R78 DAG node promotions",
        "binary_sha256": sha256_file(BASS_BIN),
        "rec_source_csv_sha256": rec_sha,
        "neutrino_fraction_hyrec": F_NU,
        "tables": {
            str(z): {
                "path": str(tables[z]),
                "sha256": sha256_file(tables[z]),
                "xe_at_z_emit": rows[z],
                "t_unit_k": 2.72548 * (1.0 + z),
                "cosmology_anchors": anchors[z],
            }
            for z in (1600, 1800)
        },
        "flrw_second_order_convergence": flrw_orders,
        "anisotropic_histories": aniso_runs,
        "acceptance": {
            "flrw_delta_xe_second_order_ratios_in_3p5_to_4p5": ratios_ok,
            "z1800_xe_gt_1_strictly_zero_hydrogen_response": xe_gt1_zero_ok,
            "all_runs_min_screen_positive": all(r["min_screen"] > 0.0 for r in aniso_runs.values()),
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("C2 COMPLETE:", json.dumps(out["acceptance"], indent=2))


if __name__ == "__main__":
    main()
