#!/usr/bin/env python3
"""C2: Run REI bass_ionization for all five AX08 cases on the C1 z_emit=1600 table."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

from scripts.r111.c1_visibility_hyrec import (
    BASS_BIN,
    C_SIGMA_T,
    NH0_AX08_MP,
    NH0_HYREC,
    cosmology_anchors,
    hubble_s,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[2]
REI_REPO = Path("/home/cosmosapjw/worktrees/rei-htt-thomson-20261124")
REI_BIN = REI_REPO / "rust/rei_microphysics/target/release/examples/bass_ionization"
AX08_COMMIT = "56dc609ea9b801c88d3364aed3eee140b3a20d46"
AX08_GZ = (
    "research/rei_igm_sync_20261116/approximation_validity/"
    "incremental_fifth/results_five/five_case_abundances.csv.gz"
)
CASES = ("ZERO", "SHEAR_PLUS", "SHEAR_MINUS", "SHEAR_HALF_PLUS", "SHEAR_HALF_MINUS")

C1_TSV = Path("/home/cosmosapjw/Downloads/htt_r111/c1_hyrec_1600/hyrec_xe_1600.tsv")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r111/c2_rei_join")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R111_LOCAL_HIGHL_NATIVE_20261124/C2_REI_JOIN.json"
)


def piecewise_tau_for_table(tsv_path: Path, z_emit: int, nh0_m3: float) -> dict[str, float]:
    arr = np.loadtxt(tsv_path, skiprows=1)
    etas, xes = arr[:, 0], arr[:, 1]
    n_h_emit = nh0_m3 * ((1.0 + z_emit) ** 3)
    eta_20 = math.log((1.0 + z_emit) / 21.0)
    eta_4 = math.log((1.0 + z_emit) / 5.0)
    gl_x, gl_w = np.polynomial.legendre.leggauss(12)

    def seg_int(a: float, b: float) -> float:
        mid, half = 0.5 * (a + b), 0.5 * (b - a)
        pts = mid + half * gl_x
        vals = np.empty_like(pts)
        for k, p in enumerate(pts):
            z = (1.0 + z_emit) * math.exp(-float(p)) - 1.0
            xe = float(np.interp(p, etas, xes))
            nh = n_h_emit * math.exp(-3.0 * float(p))
            vals[k] = C_SIGMA_T * nh * xe / hubble_s(z)
        return float(half * np.sum(gl_w * vals))

    tau_tot = 0.0
    tau_reio_le20 = 0.0
    tau_rei_4_to_20 = 0.0
    tau_cont_lt4 = 0.0
    for i in range(len(etas) - 1):
        a, b = float(etas[i]), float(etas[i + 1])
        s = seg_int(a, b)
        tau_tot += s
        # Split cleanly at boundaries if an edge crosses eta_20 or eta_4
        if b <= eta_20 + 1e-13:
            continue
        if a < eta_20 < b:
            tau_reio_le20 += seg_int(eta_20, b)
            if b <= eta_4 + 1e-13:
                tau_rei_4_to_20 += seg_int(eta_20, b)
        elif b <= eta_4 + 1e-13:
            tau_reio_le20 += s
            tau_rei_4_to_20 += s
        elif a < eta_4 < b:
            tau_reio_le20 += s
            tau_rei_4_to_20 += seg_int(a, eta_4)
            tau_cont_lt4 += seg_int(eta_4, b)
        else:
            tau_reio_le20 += s
            tau_cont_lt4 += s

    return {
        "tau_1600_to_0": tau_tot,
        "tau_reio_z_le_20": tau_reio_le20,
        "tau_rei_4_to_20": tau_rei_4_to_20,
        "tau_cont_0_to_4": tau_cont_lt4,
    }


def main() -> None:
    if not C1_TSV.exists():
        raise FileNotFoundError(f"Run C1 first; missing {C1_TSV}")
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    gz_bytes = subprocess.check_output(["git", "-C", str(REI_REPO), "show", f"{AX08_COMMIT}:{AX08_GZ}"])
    ax08_gz_sha = hashlib.sha256(gz_bytes).hexdigest()
    ax08_csv = RAW_ROOT / "five_case_abundances.csv"
    ax08_csv.write_bytes(gzip.decompress(gz_bytes))

    # Extract raw AX08 lookup (case, zbar) -> xe_per_H
    ax08_rows: dict[tuple[str, float], float] = {}
    with ax08_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ax08_rows[(row["case"], float(row["zbar"]))] = float(row["xe_per_H"])

    rec_arr = np.loadtxt(C1_TSV, skiprows=1)
    anc = cosmology_anchors(1600)
    eta_end_expected = anc["duration"]

    results = {}
    for case in CASES:
        merged_tsv = RAW_ROOT / f"merged_{case}_1600.tsv"
        t0 = time.perf_counter()
        proc = subprocess.run(
            [str(REI_BIN), str(C1_TSV), str(ax08_csv), case, "--z-emit", "1600"],
            check=True,
            capture_output=True,
            text=True,
        )
        rei_wall = time.perf_counter() - t0
        merged_tsv.write_text(proc.stdout, encoding="utf-8")
        rep = json.loads(proc.stderr.strip())

        arr = np.loadtxt(merged_tsv, skiprows=1)
        etas, xes = arr[:, 0], arr[:, 1]
        assert etas[0] == 0.0
        assert np.all(np.diff(etas) > 0.0)
        assert abs(etas[-1] - eta_end_expected) < 1e-12
        zs = 1601.0 * np.exp(-etas) - 1.0
        # Verify single owner per interval without overlap:
        n_gt20 = int(np.sum(zs > float(rep["z_high"]) + 1e-9))
        n_4_20 = int(np.sum((zs >= float(rep["z_low"]) - 1e-9) & (zs <= float(rep["z_high"]) + 1e-9)))
        n_lt4 = int(np.sum(zs < float(rep["z_low"]) - 1e-9))
        assert n_gt20 == rep["rec_knots"]
        assert n_4_20 == rep["rei_knots"]
        assert n_lt4 == rep["continuation_knots"]

        eta_20 = math.log(1601.0 / (1.0 + float(rep["z_high"])))
        xe_rec_at_20 = float(np.interp(eta_20, rec_arr[:, 0], rec_arr[:, 1]))
        xe_rei_at_20 = ax08_rows[(case, float(rep["z_high"]))]
        xe_rei_at_4 = ax08_rows[(case, float(rep["z_low"]))]

        tau_hyrec_nh0 = piecewise_tau_for_table(merged_tsv, 1600, NH0_HYREC)
        tau_ax08_nh0 = piecewise_tau_for_table(merged_tsv, 1600, NH0_AX08_MP)

        # Verify in BASS FLRW (4096 steps SDIRK2)
        bass_flrw_dir = RAW_ROOT / f"bass_flrw_{case}"
        if bass_flrw_dir.exists():
            shutil.rmtree(bass_flrw_dir)
        t_b = time.perf_counter()
        subprocess.run(
            [
                str(BASS_BIN), "--out", str(bass_flrw_dir),
                "--family", "I", "--shear", "0.0",
                "--duration", repr(anc["duration"]), "--steps", "4096",
                "--nmu", "6", "--nphi", "12", "--lmax", "2",
                "--feedback", "recoil", "--collision", "sdirk2",
                "--lie-update", "congruence",
                "--omega-lambda", repr(anc["omega_lambda_emit"]),
                "--dust-fraction", repr(anc["dust_fraction"]),
                "--ionization", str(merged_tsv),
                "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
                "--h-emit-s", repr(anc["h_emit_s"]),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        bass_wall = time.perf_counter() - t_b
        diag = np.loadtxt(bass_flrw_dir / "diagnostics.tsv", skiprows=1)
        depth_bass = float(diag[-1, 16])

        results[case] = {
            "rei_seconds": rei_wall,
            "merged_tsv": str(merged_tsv),
            "merged_tsv_sha256": sha256_file(merged_tsv),
            "rei_report": rep,
            "single_owner_partition_verified": True,
            "strictly_increasing_eta_verified": True,
            "xe_rec_interp_at_z_high": xe_rec_at_20,
            "xe_rei_at_z_high": xe_rei_at_20,
            "jump_rec_minus_rei_at_z_high": xe_rec_at_20 - xe_rei_at_20,
            "xe_rei_at_z_low": xe_rei_at_4,
            "xe_at_z0": float(xes[-1]),
            "tau_with_hyrec_nh0": tau_hyrec_nh0,
            "tau_with_ax08_mp_nh0": tau_ax08_nh0,
            "nh0_convention_delta_tau_reio": tau_ax08_nh0["tau_reio_z_le_20"] - tau_hyrec_nh0["tau_reio_z_le_20"],
            "bass_flrw_4096": {
                "wall_seconds": bass_wall,
                "proper_depth": depth_bass,
                "abs_err_vs_hyrec_nh0_quad": abs(depth_bass - tau_hyrec_nh0["tau_1600_to_0"]),
                "rel_err_vs_hyrec_nh0_quad": abs(depth_bass - tau_hyrec_nh0["tau_1600_to_0"]) / tau_hyrec_nh0["tau_1600_to_0"],
                "max_abs_gauss": float(np.max(np.abs(diag[:, 4]))),
                "diagnostics_sha256": sha256_file(bass_flrw_dir / "diagnostics.tsv"),
            },
        }

    # Demonstration VIIh run on ZERO merged table with SDIRK2 + LoS l<=32 to measure reionization polarization
    viih_zero_dir = RAW_ROOT / "bass_viih_ZERO_sdirk2"
    if viih_zero_dir.exists():
        shutil.rmtree(viih_zero_dir)
    lie_path = RAW_ROOT / "viih_demo.lie"
    lie_path.write_text("shear 0.0003 0.0002 -0.0005 0.00015 0.0001 0.00012\nn 0 0.01 0.01 0 0 0\na 0.005 0 0\n")
    t_demo = time.perf_counter()
    subprocess.run(
        [
            str(BASS_BIN), "--out", str(viih_zero_dir),
            "--lie-ic", str(lie_path), "--feedback", "recoil",
            "--dust-fraction", repr(anc["dust_fraction"]),
            "--omega-lambda", repr(anc["omega_lambda_emit"]),
            "--ionization", str(RAW_ROOT / "merged_ZERO_1600.tsv"),
            "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
            "--h-emit-s", repr(anc["h_emit_s"]),
            "--duration", repr(anc["duration"]), "--steps", "4000",
            "--nmu", "12", "--nphi", "28", "--lmax", "4", "--los-lmax", "32",
            "--collision", "sdirk2", "--lie-update", "congruence",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    demo_wall = time.perf_counter() - t_demo
    demo_cl = np.loadtxt(viih_zero_dir / "los_cl.tsv", skiprows=1)
    demo_diag = np.loadtxt(viih_zero_dir / "diagnostics.tsv", skiprows=1)
    demo_rtxt = dict(
        line.split("=", 1) for line in (viih_zero_dir / "run.txt").read_text().splitlines() if "=" in line
    )

    out = {
        "schema": "htt.r111.c2_rei_join/1",
        "claim_ceiling": "deterministic single-history join; z < 4 continuation is a conditional placeholder pending M1-M6 physics",
        "rei_binary": str(REI_BIN),
        "rei_binary_sha256": sha256_file(REI_BIN),
        "bass_binary_sha256": sha256_file(BASS_BIN),
        "ax08_source": {
            "repo": str(REI_REPO),
            "commit": AX08_COMMIT,
            "file": AX08_GZ,
            "gz_sha256": ax08_gz_sha,
            "csv_sha256": sha256_file(ax08_csv),
        },
        "rec_input_sha256": sha256_file(C1_TSV),
        "nh0_anchors": {
            "hyrec_mH_m3": NH0_HYREC,
            "ax08_mp_m3": NH0_AX08_MP,
            "relative_shift_mp_vs_mH": (NH0_AX08_MP / NH0_HYREC) - 1.0,
        },
        "cases": results,
        "viih_zero_reionization_demo": {
            "wall_seconds": demo_wall,
            "proper_depth": float(demo_diag[-1, 16]),
            "max_abs_gauss": float(np.max(np.abs(demo_diag[:, 4]))),
            "min_screen_eigenvalue": float(np.min(demo_diag[:, 14])),
            "los_max_landing_error": float(demo_rtxt["los_max_landing_error"]),
            "los_modes_sha256": sha256_file(viih_zero_dir / "los_modes.tsv"),
            "cl_ell_2_to_10": [
                {
                    "ell": int(row[0]),
                    "TT": float(row[1]),
                    "EE": float(row[4]),
                    "BB": float(row[6]),
                }
                for row in demo_cl[2:11]
            ],
        },
        "acceptance": {
            "all_five_cases_single_owner_per_interval": all(r["single_owner_partition_verified"] for r in results.values()),
            "all_five_cases_strictly_increasing_eta": all(r["strictly_increasing_eta_verified"] for r in results.values()),
            "all_five_cases_jump_at_z20_reported": all(math.isfinite(r["rei_report"]["jump_at_z_high"]) for r in results.values()),
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    for k, v in results.items():
        print(
            f"  {k:16s}: jump_z20={v['rei_report']['jump_at_z_high']:+.6e}, "
            f"tau_reio(mH)={v['tau_with_hyrec_nh0']['tau_reio_z_le_20']:.6f}, "
            f"tau_reio(mp)={v['tau_with_ax08_mp_nh0']['tau_reio_z_le_20']:.6f}"
        )


if __name__ == "__main__":
    main()
