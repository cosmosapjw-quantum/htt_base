#!/usr/bin/env python3
"""C3: REI bass_ionization join for all five AX08 cases with --recombination matched --recombination-stop-eta."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from scripts.r111.c1_visibility_hyrec import NH0_AX08_MP, NH0_HYREC, cosmology_anchors, load_rec_csv, sha256_file, write_hyrec_tsv
from scripts.r111.c2_rei_join import AX08_COMMIT, AX08_GZ, CASES, REI_BIN, REI_REPO, piecewise_tau_for_table
from scripts.r111.c3_long_highl_atlas import COMMON_SHEAR, FAMILIES_LIE

ROOT = Path(__file__).resolve().parents[2]
BASS_BIN = Path("/home/cosmosapjw/Downloads/htt_r114/bin/homogeneous_sky_r114")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r114/c3_rei_matched")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C3_REI_MATCHED_JOIN.json"
)
F_NU = (0.227107317660239 * 3.03821934419124) / (1.0 + 0.227107317660239 * 3.03821934419124)


def run_viih_rei(
    out_dir: Path,
    lie_file: Path,
    tsv_path: Path,
    anc: dict[str, float],
    t_unit_k: float,
    route: str,
    matched: bool,
    stop_eta: float | None,
    steps: int = 2000,
) -> dict:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    args = [
        str(BASS_BIN),
        "--out", str(out_dir),
        "--lie-ic", str(lie_file),
        "--duration", repr(anc["duration"]),
        "--steps", str(steps),
        "--feedback", "recoil",
        "--collision", "sdirk2",
        "--lie-update", "congruence",
        "--omega-lambda", repr(anc["omega_lambda_emit"]),
        "--dust-fraction", repr(anc["dust_fraction"]),
        "--baryon-fraction", "0.157",
        "--neutrino-fraction", repr(F_NU),
        "--ionization", str(tsv_path),
        "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
        "--h-emit-s", repr(anc["h_emit_s"]),
        "--observer-frame", "host",
        "--lmax", "4",
        "--los-lmax", "32",
        "--los-ntheta", "48",
        "--los-nphi", "96",
    ]
    if route == "harmonic":
        args += ["--route", "harmonic", "--harmonic-lmax", "16", "--nmu", "8", "--nphi", "16"]
    else:
        args += ["--route", "rays", "--nmu", "12", "--nphi", "28"]
    if matched:
        args += ["--recombination", "matched", "--t-unit-k", repr(t_unit_k)]
        if stop_eta is not None:
            args += ["--recombination-stop-eta", repr(stop_eta)]
    env = os.environ.copy()
    env["RAYON_NUM_THREADS"] = "4"
    t0 = time.monotonic()
    subprocess.run(args, check=True, capture_output=True, text=True, env=env)
    wall = time.monotonic() - t0
    with (out_dir / "diagnostics.tsv").open() as f:
        dhead = f.readline().split()
        drows = np.loadtxt(f)
    dcol = {k: i for i, k in enumerate(dhead)}
    cl = np.loadtxt(out_dir / "los_cl.tsv", skiprows=1)
    rtxt = dict(line.split("=", 1) for line in (out_dir / "run.txt").read_text().splitlines() if "=" in line)
    rec = {
        "wall_seconds": wall,
        "proper_depth_0": float(drows[-1, dcol["proper_depth"]]),
        "max_abs_gauss": float(np.max(np.abs(drows[:, dcol["gauss"]]))),
        "min_screen": float(np.min(drows[:, dcol["min_screen_eigenvalue"]])),
        "delta_xe_final": float(rtxt["delta_xe_final"]),
        "los_cl": {int(cl[l, 0]): [float(cl[l, 1]), float(cl[l, 4]), float(cl[l, 6])] for l in range(2, 11)},
        "diagnostics_sha256": sha256_file(out_dir / "diagnostics.tsv"),
        "los_modes_sha256": sha256_file(out_dir / "los_modes.tsv"),
    }
    rec_tsv = out_dir / "recombination.tsv"
    if rec_tsv.exists() and stop_eta is not None:
        with rec_tsv.open() as f:
            rhead = f.readline().split()
            rrows = np.loadtxt(f)
        rcol = {k: i for i, k in enumerate(rhead)}
        etas = rrows[:, rcol["eta"]]
        dxe = rrows[:, rcol["delta_xe"]]
        # Verify stop_eta boundary: last index with eta <= stop_eta + tol
        active_idx = np.where(etas <= stop_eta + 1e-12)[0]
        last_active = int(active_idx[-1])
        post_diff = float(np.max(np.abs(dxe[last_active:] - dxe[last_active]))) if last_active < len(dxe) else 0.0
        rec["recombination"] = {
            "stop_eta": stop_eta,
            "last_active_step": last_active,
            "last_active_eta": float(etas[last_active]),
            "last_active_z": 1601.0 * math.exp(-float(etas[last_active])) - 1.0,
            "first_frozen_next_eta": float(etas[last_active + 1]) if last_active + 1 < len(etas) else None,
            "held_delta_xe": float(dxe[last_active]),
            "delta_xe_peak": float(dxe[int(np.argmax(np.abs(dxe)))]),
            "max_post_stop_drift": post_diff,
            "recombination_sha256": sha256_file(rec_tsv),
        }
    elif rec_tsv.exists():
        with rec_tsv.open() as f:
            rhead = f.readline().split()
            rrows = np.loadtxt(f)
        rcol = {k: i for i, k in enumerate(rhead)}
        dxe = rrows[:, rcol["delta_xe"]]
        rec["recombination"] = {
            "stop_eta": None,
            "delta_xe_peak": float(dxe[int(np.argmax(np.abs(dxe)))]),
            "delta_xe_final": float(dxe[-1]),
            "recombination_sha256": sha256_file(rec_tsv),
        }
    return rec


def main() -> None:
    if RAW_ROOT.exists():
        shutil.rmtree(RAW_ROOT)
    RAW_ROOT.mkdir(parents=True)

    rows, rec_sha = load_rec_csv()
    c1_tsv = RAW_ROOT / "hyrec_xe_1600.tsv"
    write_hyrec_tsv(rows, 1600, c1_tsv)
    anc = cosmology_anchors(1600)
    t_unit = 2.72548 * 1601.0
    stop_eta_z20 = math.log(1601.0 / 21.0)

    n6, a3, _, _ = FAMILIES_LIE["VIIh"]
    viih_lie = RAW_ROOT / "viih_small.lie"
    viih_lie.write_text(f"shear {COMMON_SHEAR}\nn {n6}\na {a3}\n", encoding="utf-8")

    gz_bytes = subprocess.check_output(["git", "-C", str(REI_REPO), "show", f"{AX08_COMMIT}:{AX08_GZ}"])
    ax08_gz_sha = hashlib.sha256(gz_bytes).hexdigest()
    ax08_csv = RAW_ROOT / "five_case_abundances.csv"
    ax08_csv.write_bytes(gzip.decompress(gz_bytes))

    merged_paths = {}
    rei_meta = {}
    tau_info = {}
    for case in CASES:
        merged_tsv = RAW_ROOT / f"merged_{case}_1600.tsv"
        proc = subprocess.run(
            [str(REI_BIN), str(c1_tsv), str(ax08_csv), case, "--z-emit", "1600"],
            check=True,
            capture_output=True,
            text=True,
        )
        merged_tsv.write_text(proc.stdout, encoding="utf-8")
        rep = json.loads(proc.stderr.strip())
        arr = np.loadtxt(merged_tsv, skiprows=1)
        assert arr[0, 0] == 0.0 and np.all(np.diff(arr[:, 0]) > 0.0)
        merged_paths[case] = merged_tsv
        rei_meta[case] = {"report": rep, "merged_tsv_sha256": sha256_file(merged_tsv)}
        tau_info[case] = {
            "hyrec_mH": piecewise_tau_for_table(merged_tsv, 1600, NH0_HYREC),
            "ax08_mp": piecewise_tau_for_table(merged_tsv, 1600, NH0_AX08_MP),
        }

    jobs = []
    for case in CASES:
        jobs.append((case, "table", "harmonic", None, False))
        jobs.append((case, "matched_stop", "harmonic", stop_eta_z20, True))
    jobs.append(("ZERO", "matched_nostop", "harmonic", None, True))
    jobs.append(("ZERO", "matched_stop_rays", "rays", stop_eta_z20, True))

    job_results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [
            (
                (case, label),
                ex.submit(
                    run_viih_rei,
                    RAW_ROOT / f"{case}_{label}",
                    viih_lie,
                    merged_paths[case],
                    anc,
                    t_unit,
                    route,
                    matched,
                    stop_eta,
                ),
            )
            for case, label, route, stop_eta, matched in jobs
        ]
        for key, fut in futs:
            job_results[key] = fut.result()

    cases_out = {}
    for case in CASES:
        tab = job_results[(case, "table")]
        mat = job_results[(case, "matched_stop")]
        ee_rel = {
            str(l): (mat["los_cl"][l][1] - tab["los_cl"][l][1]) / tab["los_cl"][l][1]
            for l in range(2, 11)
        }
        tt_rel = {
            str(l): (mat["los_cl"][l][0] - tab["los_cl"][l][0]) / tab["los_cl"][l][0]
            for l in range(2, 11)
        }
        bb_rel = {
            str(l): (mat["los_cl"][l][2] - tab["los_cl"][l][2]) / tab["los_cl"][l][2]
            for l in range(2, 11)
        }
        cases_out[case] = {
            "rei_report": rei_meta[case]["report"],
            "merged_tsv_sha256": rei_meta[case]["merged_tsv_sha256"],
            "tau_quadrature": tau_info[case],
            "table_harmonic16": tab,
            "matched_stop_harmonic16": mat,
            "cl_rel_change_matched_vs_table_l2_10": {
                "EE": ee_rel,
                "TT": tt_rel,
                "BB": bb_rel,
                "max_abs_EE_rel_l2_10": max(abs(v) for v in ee_rel.values()),
            },
        }
    out = {
        "schema": "htt.r114.c3_rei_matched_join/1",
        "claim_ceiling": "deterministic single-history native outputs; z<4 remains conditional T3 continuation placeholder; zero R78 promotions",
        "bass_binary_sha256": sha256_file(BASS_BIN),
        "rei_binary_sha256": sha256_file(REI_BIN),
        "ax08_gz_sha256": ax08_gz_sha,
        "rec_source_sha256": rec_sha,
        "stop_eta_z20": stop_eta_z20,
        "neutrino_fraction_hyrec": F_NU,
        "cases": cases_out,
        "zero_controls": {
            "matched_nostop_harmonic16": job_results[("ZERO", "matched_nostop")],
            "matched_stop_rays": job_results[("ZERO", "matched_stop_rays")],
        },
        "acceptance": {
            "all_5_cases_offset_held_exact_after_stop": all(
                cases_out[c]["matched_stop_harmonic16"]["recombination"]["max_post_stop_drift"] == 0.0
                for c in CASES
            ),
            "all_5_cases_last_active_eta_le_stop_eta": all(
                cases_out[c]["matched_stop_harmonic16"]["recombination"]["last_active_eta"] <= stop_eta_z20 + 1e-12
                for c in CASES
            ),
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("C3 COMPLETE:", json.dumps(out["acceptance"], indent=2))


if __name__ == "__main__":
    main()
