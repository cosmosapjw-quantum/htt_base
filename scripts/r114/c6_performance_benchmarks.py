#!/usr/bin/env python3
"""C6: Performance benchmarks — matched-step cost vs N_dir, harmonic L=16..64 cost, LoS l=256 on harmonic."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from scripts.r111.c1_visibility_hyrec import cosmology_anchors, load_rec_csv, sha256_file, write_hyrec_tsv
from scripts.r111.c3_long_highl_atlas import COMMON_SHEAR, FAMILIES_LIE

ROOT = Path(__file__).resolve().parents[2]
BASS_BIN = Path("/home/cosmosapjw/Downloads/htt_r114/bin/homogeneous_sky_r114")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r114/c6_perf")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C6_PERFORMANCE_BENCHMARKS.json"
)
F_NU = (0.227107317660239 * 3.03821934419124) / (1.0 + 0.227107317660239 * 3.03821934419124)


def run_timed(out_dir: Path, args: list[str], threads: int) -> dict:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    env = dict(os.environ)
    env["RAYON_NUM_THREADS"] = str(threads)
    cmd = ["/usr/bin/time", "-v", str(BASS_BIN), "--out", str(out_dir), *args]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    wall = time.perf_counter() - t0
    m_rss = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", proc.stderr)
    rss_kb = int(m_rss.group(1)) if m_rss else -1
    rtxt = dict(line.split("=", 1) for line in (out_dir / "run.txt").read_text().splitlines() if "=" in line)
    rec = {
        "rayon_threads_requested": threads,
        "wall_seconds": wall,
        "max_rss_kbytes": rss_kb,
        "max_rss_mib": rss_kb / 1024.0 if rss_kb >= 0 else None,
        "delta_xe_final": rtxt.get("delta_xe_final"),
        "route": rtxt.get("route"),
    }
    if "los_seconds" in rtxt:
        m_grid = re.match(r"gauss_legendre_(\d+)_x_uniform_phi_(\d+)", rtxt["los_grid"])
        nt, np_ = (int(m_grid.group(1)), int(m_grid.group(2))) if m_grid else (0, 0)
        rec.update({
            "rayon_threads_reported": int(rtxt["los_threads"]),
            "los_seconds": float(rtxt["los_seconds"]),
            "forward_plus_io_seconds": wall - float(rtxt["los_seconds"]),
            "los_lmax": int(rtxt["los_lmax"]),
            "los_ntheta": nt,
            "los_nphi": np_,
            "n_rays": nt * np_,
            "los_max_landing_error": float(rtxt["los_max_landing_error"]),
            "los_modes_sha256": sha256_file(out_dir / "los_modes.tsv"),
        })
    return rec


def main() -> None:
    if RAW_ROOT.exists():
        shutil.rmtree(RAW_ROOT)
    RAW_ROOT.mkdir(parents=True)

    rows, _ = load_rec_csv()
    tsv_1600 = RAW_ROOT / "hyrec_xe_1600.tsv"
    write_hyrec_tsv(rows, 1600, tsv_1600)
    anc = cosmology_anchors(1600)
    t_unit = 2.72548 * 1601.0

    n6, a3, _, _ = FAMILIES_LIE["VIIh"]
    viih_lie = RAW_ROOT / "viih_small.lie"
    viih_lie.write_text(f"shear {COMMON_SHEAR}\nn {n6}\na {a3}\n", encoding="utf-8")

    # 1. Matched-step cost per step vs direction count (steps=64 on z=1600 recombination window eta in [0, 0.3])
    matched_scaling = []
    common_m = [
        "--family", "I", "--shear", "0.01", "--dust-beta", "1e-3,0,0",
        "--duration", "0.3", "--steps", "64", "--feedback", "recoil",
        "--collision", "sdirk2", "--lie-update", "congruence",
        "--omega-lambda", repr(anc["omega_lambda_emit"]),
        "--dust-fraction", repr(anc["dust_fraction"]), "--baryon-fraction", "0.157",
        "--neutrino-fraction", repr(F_NU),
        "--ionization", str(tsv_1600), "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
        "--h-emit-s", repr(anc["h_emit_s"]), "--observer-frame", "host", "--lmax", "4",
    ]
    grid_configs = [
        ("rays", 8, 16, []),
        ("rays", 12, 24, []),
        ("rays", 16, 36, []),
        ("rays", 24, 48, []),
        ("rays", 32, 64, []),
        ("harmonic_L16", 19, 38, ["--route", "harmonic", "--harmonic-lmax", "16"]),
        ("harmonic_L24", 27, 54, ["--route", "harmonic", "--harmonic-lmax", "24"]),
    ]
    for label, nt, np_, extra in grid_configs:
        n_dir = nt * np_
        if label == "rays":
            grid_args = ["--route", "rays", "--nmu", str(nt), "--nphi", str(np_)]
        else:
            grid_args = [*extra, "--nmu", "8", "--nphi", "16", "--harmonic-ntheta", str(nt), "--harmonic-nphi", str(np_)]
        tab = run_timed(RAW_ROOT / f"ms_{label}_{n_dir}_tab", common_m + grid_args, 1)
        mat = run_timed(
            RAW_ROOT / f"ms_{label}_{n_dir}_mat",
            common_m + grid_args + ["--recombination", "matched", "--t-unit-k", repr(t_unit)],
            1,
        )
        matched_scaling.append({
            "label": label,
            "n_theta": nt,
            "n_phi": np_,
            "n_directions": n_dir,
            "steps": 64,
            "table_wall_seconds": tab["wall_seconds"],
            "matched_wall_seconds": mat["wall_seconds"],
            "table_ms_per_step": 1000.0 * tab["wall_seconds"] / 64.0,
            "matched_ms_per_step": 1000.0 * mat["wall_seconds"] / 64.0,
            "matched_minus_table_ms_per_step": 1000.0 * (mat["wall_seconds"] - tab["wall_seconds"]) / 64.0,
            "overhead_ratio": mat["wall_seconds"] / tab["wall_seconds"],
            "table_rss_mib": tab["max_rss_mib"],
            "matched_rss_mib": mat["max_rss_mib"],
        })
        print("C6 matched", label, n_dir, f"tab={tab['wall_seconds']:.2f}s mat={mat['wall_seconds']:.2f}s", flush=True)

    # 2. Harmonic cost for L = 16, 24, 32, 48, 64 (steps=64, 1t & 24t)
    harm_cost = []
    for L in (16, 24, 32, 48, 64):
        args_L = [
            "--lie-ic", str(viih_lie), "--duration", "0.3", "--steps", "64",
            "--feedback", "recoil", "--collision", "sdirk2", "--lie-update", "congruence",
            "--omega-lambda", repr(anc["omega_lambda_emit"]),
            "--dust-fraction", repr(anc["dust_fraction"]), "--baryon-fraction", "0.157",
            "--neutrino-fraction", repr(F_NU),
            "--ionization", str(tsv_1600), "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
            "--h-emit-s", repr(anc["h_emit_s"]),
            "--route", "harmonic", "--harmonic-lmax", str(L),
            "--nmu", "8", "--nphi", "16", "--lmax", "4", "--observer-frame", "host",
        ]
        r1 = run_timed(RAW_ROOT / f"harm_L{L}_t1", args_L, 1)
        r24 = run_timed(RAW_ROOT / f"harm_L{L}_t24", args_L, 24)
        harm_cost.append({
            "harmonic_lmax": L,
            "steps": 64,
            "collision_grid": [L + 3, 2 * L + 6],
            "threads_1": {"wall_seconds": r1["wall_seconds"], "ms_per_step": 1000.0 * r1["wall_seconds"] / 64.0, "max_rss_mib": r1["max_rss_mib"]},
            "threads_24": {"wall_seconds": r24["wall_seconds"], "ms_per_step": 1000.0 * r24["wall_seconds"] / 64.0, "max_rss_mib": r24["max_rss_mib"]},
        })
        print(f"C6 harm L={L}: 1t={r1['wall_seconds']:.2f}s (rss={r1['max_rss_mib']:.1f}MiB) 24t={r24['wall_seconds']:.2f}s", flush=True)

    # 3. LoS l=256 on --route harmonic --harmonic-lmax 32
    los_short_args = [
        "--family", "VIIh", "--shear", "0.18", "--duration", "0.35", "--steps", "36",
        "--route", "harmonic", "--harmonic-lmax", "32",
        "--nmu", "8", "--nphi", "16", "--lmax", "4",
        "--feedback", "recoil", "--tau", "0.22", "--dust-fraction", "0.22", "--baryon-fraction", "0.157",
        "--dust-beta", "0.16,-0.08,0.04", "--observer-beta", "0.1,0.035,-0.025",
        "--los-lmax", "256", "--collision", "sdirk2", "--lie-update", "congruence",
    ]
    los_scaling = {str(th): run_timed(RAW_ROOT / f"los256_h32_short_t{th}", los_short_args, th) for th in (1, 6, 12, 24)}

    long_los_args = [
        "--lie-ic", str(viih_lie), "--duration", repr(anc["duration"]), "--steps", "2000",
        "--feedback", "recoil", "--collision", "sdirk2", "--lie-update", "congruence",
        "--omega-lambda", repr(anc["omega_lambda_emit"]),
        "--dust-fraction", repr(anc["dust_fraction"]), "--baryon-fraction", "0.157",
        "--neutrino-fraction", repr(F_NU),
        "--ionization", str(tsv_1600), "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
        "--h-emit-s", repr(anc["h_emit_s"]),
        "--route", "harmonic", "--harmonic-lmax", "32",
        "--nmu", "8", "--nphi", "16", "--lmax", "4", "--observer-frame", "host",
        "--los-lmax", "256",
    ]
    los_long = run_timed(RAW_ROOT / "los256_h32_long_t24", long_los_args, 24)
    print(f"C6 long LoS l=256 (harm32, 2000s, 24t): wall={los_long['wall_seconds']:.2f}s los={los_long['los_seconds']:.2f}s rss={los_long['max_rss_mib']:.1f}MiB err={los_long['los_max_landing_error']:.2e}")

    out = {
        "schema": "htt.r114.c6_performance_benchmarks/1",
        "binary_sha256": sha256_file(BASS_BIN),
        "matched_step_cost_vs_directions_1t": matched_scaling,
        "harmonic_cost_l16_to_64": harm_cost,
        "los256_harmonic32_short_36step_scaling": los_scaling,
        "los256_harmonic32_long_z1600_2000step_24t": los_long,
        "los256_thread_speedup_1_to_24": los_scaling["1"]["los_seconds"] / los_scaling["24"]["los_seconds"],
    }
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
