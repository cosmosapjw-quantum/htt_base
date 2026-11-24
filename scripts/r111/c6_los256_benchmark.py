#!/usr/bin/env python3
"""C6: Benchmark LoS l=256 (rayon) runtime, peak RSS, and landing error."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from scripts.r111.c1_visibility_hyrec import BASS_BIN, cosmology_anchors, sha256_file

ROOT = Path(__file__).resolve().parents[2]
C1_TSV = Path("/home/cosmosapjw/Downloads/htt_r111/c1_hyrec_1600/hyrec_xe_1600.tsv")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r111/c6_perf")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R111_LOCAL_HIGHL_NATIVE_20261124/C6_LOS256_PERFORMANCE.json"
)


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
    rtxt = dict(
        line.split("=", 1) for line in (out_dir / "run.txt").read_text().splitlines() if "=" in line
    )
    m_grid = re.match(r"gauss_legendre_(\d+)_x_uniform_phi_(\d+)", rtxt["los_grid"])
    if not m_grid:
        raise ValueError(f"unexpected los_grid format: {rtxt['los_grid']}")
    los_ntheta, los_nphi = int(m_grid.group(1)), int(m_grid.group(2))
    return {
        "rayon_threads_requested": threads,
        "rayon_threads_reported": int(rtxt["los_threads"]),
        "wall_seconds": wall,
        "los_seconds": float(rtxt["los_seconds"]),
        "forward_plus_io_seconds": wall - float(rtxt["los_seconds"]),
        "max_rss_kbytes": rss_kb,
        "max_rss_mib": rss_kb / 1024.0 if rss_kb >= 0 else None,
        "los_lmax": int(rtxt["los_lmax"]),
        "los_ntheta": los_ntheta,
        "los_nphi": los_nphi,
        "n_rays": los_ntheta * los_nphi,
        "los_max_landing_error": float(rtxt["los_max_landing_error"]),
        "los_modes_sha256": sha256_file(out_dir / "los_modes.tsv"),
    }


def main() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    # 1. R109-epoch VIIh 36-step l=256 thread scaling (1, 6, 12, 24 threads) to isolate LoS scaling
    r109_args = [
        "--family", "VIIh", "--shear", "0.18", "--duration", "0.35",
        "--steps", "36", "--nmu", "10", "--nphi", "24", "--lmax", "4",
        "--feedback", "recoil", "--tau", "0.22", "--dust-fraction", "0.22",
        "--dust-beta", "0.16,-0.08,0.04", "--observer-beta", "0.1,0.035,-0.025",
        "--los-lmax", "256", "--collision", "sdirk2", "--lie-update", "congruence",
    ]
    scaling = {}
    for th in (1, 6, 12, 24):
        rec = run_timed(RAW_ROOT / f"viih_r109_l256_t{th}", r109_args, th)
        scaling[str(th)] = rec
        print(
            f"R109 VIIh l=256 threads={th:2d}: wall={rec['wall_seconds']:.2f}s "
            f"los={rec['los_seconds']:.2f}s rss={rec['max_rss_mib']:.1f}MiB "
            f"landing={rec['los_max_landing_error']:.2e}",
            flush=True,
        )

    # 2. Long-epoch z_emit=1600 VIIh 4000-step l=256 at 24 cores (production scale)
    anc = cosmology_anchors(1600)
    lie_path = RAW_ROOT / "viih_c3.lie"
    lie_path.write_text("shear 0.0003 0.0002 -0.0005 0.00015 0.0001 0.00012\nn 0 0.01 0.01 0 0 0\na 0.005 0 0\n")
    long_args = [
        "--lie-ic", str(lie_path), "--feedback", "recoil",
        "--dust-fraction", repr(anc["dust_fraction"]),
        "--omega-lambda", repr(anc["omega_lambda_emit"]),
        "--ionization", str(C1_TSV),
        "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
        "--h-emit-s", repr(anc["h_emit_s"]),
        "--duration", repr(anc["duration"]), "--steps", "4000",
        "--nmu", "14", "--nphi", "36", "--lmax", "4", "--los-lmax", "256",
        "--collision", "sdirk2", "--lie-update", "congruence",
    ]
    long_24 = run_timed(RAW_ROOT / "viih_long_4000_l256_t24", long_args, 24)
    print(
        f"Long-epoch VIIh 4000 steps l=256 (24t): wall={long_24['wall_seconds']:.2f}s "
        f"los={long_24['los_seconds']:.2f}s rss={long_24['max_rss_mib']:.1f}MiB "
        f"landing={long_24['los_max_landing_error']:.2e}"
    )

    out = {
        "schema": "htt.r111.c6_los256_performance/1",
        "binary_sha256": sha256_file(BASS_BIN),
        "r109_36step_scaling": scaling,
        "long_epoch_z1600_4000step_24t": long_24,
        "thread_speedup_los_1_to_24": scaling["1"]["los_seconds"] / scaling["24"]["los_seconds"],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
