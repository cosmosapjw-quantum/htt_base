#!/usr/bin/env python3
"""C5: Project C3 high-l atlas (l<=128) and F3 Part-A (l<=32) via R108 Commander kernel."""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import json
import shutil
import tarfile
import time
from pathlib import Path

import numpy as np

from scripts.r109.commander_native import FAMILIES, modes as parse_modes, project, sha

ROOT = Path(__file__).resolve().parents[2]
KERNEL_PATH = Path("/home/cosmosapjw/Downloads/htt_r108/s6/kernel.npz")
R108_S6_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R108_LOS_ATLAS_DATA_20261124/SOLVER/S6_B03_TEMPLATES.json"
)
R109_PROJ_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R109_NATIVE_RUST_BIANCHI_20261124/COMMANDER_NATIVE_PROJECTION.json"
)
R109_ARCHIVE = Path(
    "/home/cosmosapjw/worktrees/bass-r109-native-20261124/research/r109_native_sky/ATLAS_MODES.tar.gz"
)
C3_TAR = Path("/home/cosmosapjw/Downloads/htt_r111/c3_atlas/C3_HIGHL_ATLAS_MODES.tar.gz")
F3_TAR = Path("/home/cosmosapjw/Downloads/htt_r111/f3_r111_raw/HIGHL_ATLAS_MODES_REBUILD.tar.gz")

RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r111/c5_commander")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R111_LOCAL_HIGHL_NATIVE_20261124/C5_COMMANDER_LEAKAGE.json"
)


def harmonic_high_l_fraction(tar_path: Path, modes_name: str, l_cut: int = 4) -> dict[str, dict]:
    out = {}
    with tarfile.open(tar_path, "r:gz") as tf:
        for fam in FAMILIES:
            raw = tf.extractfile(f"recoil_{fam}/{modes_name}").read()
            lmax, alm = parse_modes(raw)
            # alm shape: (3, n_alm); m=0 once, m>0 twice in full sky C_l weight (2l+1)
            import healpy as hp

            ls, ms = hp.Alm.getlm(lmax)
            w_m = np.where(ms == 0, 1.0, 2.0)
            fam_d = {"lmax": int(lmax)}
            for ch_idx, ch in enumerate("TEB"):
                p_all = np.zeros(lmax + 1, dtype=np.float64)
                for l in range(1, lmax + 1):
                    ml = ls == l
                    p_all[l] = float(np.sum(w_m[ml] * (np.abs(alm[ch_idx, ml]) ** 2)))
                tot = float(np.sum(p_all[1:]))
                high = float(np.sum(p_all[l_cut + 1 :])) if lmax > l_cut else 0.0
                gt2 = float(np.sum(p_all[3:])) if lmax > 2 else 0.0
                fam_d[ch] = {
                    "power_l_ge_1": tot,
                    "frac_l_gt_2": gt2 / tot if tot > 0 else 0.0,
                    f"frac_l_gt_{l_cut}": high / tot if tot > 0 else 0.0,
                }
            out[fam] = fam_d
    return out


def run_proj(archive: Path, modes_name: str, out_dir: Path) -> tuple[float, dict, dict[str, np.ndarray]]:
    json_path = out_dir / "COMMANDER_NATIVE_PROJECTION.json"
    npz_path = out_dir / "COMMANDER_NATIVE_COEFFICIENTS.npz"
    if json_path.exists() and npz_path.exists():
        meta = json.loads(json_path.read_text())
        if meta.get("atlas_sha256") == sha(archive) and meta.get("modes_name", "modes.tsv") == modes_name:
            return 0.0, meta, dict(np.load(npz_path))
    if out_dir.exists():
        shutil.rmtree(out_dir)
    t0 = time.perf_counter()
    project(KERNEL_PATH, archive, out_dir, modes_name=modes_name, member_prefix="recoil_")
    wall = time.perf_counter() - t0
    meta = json.loads(json_path.read_text())
    arrs = dict(np.load(npz_path))
    return wall, meta, arrs


def compare_coeff_pairs(
    hi_meta: dict,
    hi_arr: dict[str, np.ndarray],
    lo_meta: dict,
    lo_arr: dict[str, np.ndarray],
) -> dict[str, dict]:
    out = {}
    for i, fam in enumerate(FAMILIES):
        hi_cut = hi_arr["masked"][i]    # (384, 3, 5)
        hi_full = hi_arr["fullsky"][i]
        lo_cut = lo_arr["masked"][i]
        lo_full = lo_arr["fullsky"][i]
        per_ch = {}
        for c_idx, ch in enumerate("TEB"):
            hc = hi_cut[:, c_idx, :]
            hf = hi_full[:, c_idx, :]
            lc = lo_cut[:, c_idx, :]
            lf = lo_full[:, c_idx, :]
            n_hf = np.linalg.norm(hf, axis=1)
            n_hc = np.linalg.norm(hc, axis=1)
            # 1) Mask leakage (masked - fullsky)/fullsky across 384 orientations
            hi_leak = np.linalg.norm(hc - hf, axis=1) / np.maximum(n_hf, 1e-30)
            lo_leak = np.linalg.norm(lc - lf, axis=1) / np.maximum(np.linalg.norm(lf, axis=1), 1e-30)
            # 2) High-l projection leakage onto l<=4 masked/fullsky Commander coefficients:
            #    ||(c_hi - c_lo)|| / ||c_hi||
            d_mask = np.linalg.norm(hc - lc, axis=1) / np.maximum(n_hc, 1e-30)
            d_full = np.linalg.norm(hf - lf, axis=1) / np.maximum(n_hf, 1e-30)
            per_ch[ch] = {
                "hi_masked_vs_full_max_rel": float(np.max(hi_leak)),
                "hi_masked_vs_full_median_rel": float(np.median(hi_leak)),
                "lo_masked_vs_full_max_rel": float(np.max(lo_leak)),
                "highl_into_masked_max_rel": float(np.max(d_mask)),
                "highl_into_masked_median_rel": float(np.median(d_mask)),
                "highl_into_fullsky_max_rel": float(np.max(d_full)),
                "highl_max_coeff_abs_uK": float(np.max(np.abs(hc))),
            }
        out[fam] = per_ch
    return out


def main() -> None:
    if not KERNEL_PATH.exists():
        raise FileNotFoundError(f"Missing R108 kernel: {KERNEL_PATH}")
    reg_sha = json.loads(R108_S6_JSON.read_text())["kernel"]["kernel_sha256"]
    kern_sha = sha(KERNEL_PATH)
    assert kern_sha == reg_sha, f"Kernel sha mismatch {kern_sha} != {reg_sha}"
    with np.load(KERNEL_PATH) as npz:
        kernel_lmax = int(npz["lmax"])
        kernel_nside = int(npz["nside"])
    assert kernel_lmax >= 128

    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    # 1. C3 z_emit=1600 atlas: LoS (l<=128) vs forward Lagrangian modes.tsv (l<=4)
    w_c3_los, meta_c3_los, arr_c3_los = run_proj(C3_TAR, "los_modes.tsv", RAW_ROOT / "c3_los_l128")
    w_c3_lag, meta_c3_lag, arr_c3_lag = run_proj(C3_TAR, "modes.tsv", RAW_ROOT / "c3_lag_l4")
    c3_comp = compare_coeff_pairs(meta_c3_los, arr_c3_los, meta_c3_lag, arr_c3_lag)
    c3_pwr = harmonic_high_l_fraction(C3_TAR, "los_modes.tsv", l_cut=4)

    # 2. Exact R109 ATLAS_MODES.tar.gz baseline check (< 1e-12) and R110 Part A (l<=32) vs R109 l<=4
    r109_meta = json.loads(R109_PROJ_JSON.read_text())
    r109_by_fam = {s["family"]: s["cut_minus_full_relative_max_T_E_B"] for s in r109_meta["summaries"]}
    w_r109_repro, meta_r109_repro, _ = run_proj(R109_ARCHIVE, "modes.tsv", RAW_ROOT / "r109_exact_repro")
    r109_exact_repro_max_diff = max(
        abs(s["cut_minus_full_relative_max_T_E_B"][c] - r109_by_fam[s["family"]][c])
        for s in meta_r109_repro["summaries"]
        for c in range(3)
    )
    r109_exact_sha_equal = meta_r109_repro["output_sha256"] == r109_meta["output_sha256"]
    assert r109_exact_repro_max_diff < 1e-12 and r109_exact_sha_equal

    w_r110_los, meta_r110_los, arr_r110_los = run_proj(F3_TAR, "los_modes.tsv", RAW_ROOT / "r110_partA_los_l32")
    w_r110_lag, meta_r110_lag, arr_r110_lag = run_proj(F3_TAR, "modes.tsv", RAW_ROOT / "r110_partA_lag_l4")
    r110_comp = compare_coeff_pairs(meta_r110_los, arr_r110_los, meta_r110_lag, arr_r110_lag)
    # Note: R110 Part A used SDIRK2 + congruence whereas R109 baseline used Backward-Euler + additive.
    r110_vs_r109_integrator_diff = max(
        abs(s["cut_minus_full_relative_max_T_E_B"][c] - r109_by_fam[s["family"]][c])
        for s in meta_r110_lag["summaries"]
        for c in range(3)
    )

    prev_c5 = json.loads(OUT_JSON.read_text()) if OUT_JSON.exists() else {}
    if w_c3_los == 0.0:
        w_c3_los = float(prev_c5.get("c3_z1600_l128_vs_l4", {}).get("wall_seconds_los_l128", 0.0))
    if w_c3_lag == 0.0:
        w_c3_lag = float(prev_c5.get("c3_z1600_l128_vs_l4", {}).get("wall_seconds_lag_l4", 0.0))
    if w_r110_los == 0.0:
        w_r110_los = float(prev_c5.get("r110_partA_l32_vs_r109_l4", {}).get("wall_seconds_los_l32", 0.0))
    if w_r110_lag == 0.0:
        w_r110_lag = float(prev_c5.get("r110_partA_l32_vs_r109_l4", {}).get("wall_seconds_lag_l4", 0.0))

    out = {
        "schema": "htt.r111.c5_commander_leakage/1",
        "claim_ceiling": "linear projection only; deterministic single-history templates without CMB data or noise covariance",
        "kernel": {
            "path": str(KERNEL_PATH),
            "sha256": kern_sha,
            "lmax": kernel_lmax,
            "nside": kernel_nside,
            "covers_c3_lmax_128": kernel_lmax >= 128,
        },
        "r109_exact_archive_repro": {
            "archive": str(R109_ARCHIVE),
            "wall_seconds": w_r109_repro,
            "output_sha256_equal": r109_exact_sha_equal,
            "max_diff_vs_r109_json": r109_exact_repro_max_diff,
        },
        "c3_z1600_l128_vs_l4": {
            "wall_seconds_los_l128": w_c3_los,
            "wall_seconds_lag_l4": w_c3_lag,
            "truncated_vs_padded_max_relative_los": meta_c3_los["truncated_vs_padded_max_relative"],
            "per_family_leakage": c3_comp,
            "per_family_sky_high_l_power": c3_pwr,
        },
        "r110_partA_l32_vs_r109_l4": {
            "wall_seconds_los_l32": w_r110_los,
            "wall_seconds_lag_l4": w_r110_lag,
            "r110_sdirk2_congruence_vs_r109_be_additive_max_diff": r110_vs_r109_integrator_diff,
            "per_family_leakage": r110_comp,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT_JSON} (C3 l128 proj={w_c3_los:.2f}s, R109 exact repro diff={r109_exact_repro_max_diff:.2e}, "
        f"sha_eq={r109_exact_sha_equal}, R110-vs-R109 integrator diff={r110_vs_r109_integrator_diff:.2e})"
    )
    for fam in FAMILIES:
        d = c3_comp[fam]
        print(
            f"  C3 {fam:6s}: T(mask-full={d['T']['hi_masked_vs_full_max_rel']:.4f}, hi-l4={d['T']['highl_into_masked_max_rel']:.3e}), "
            f"E(mask-full={d['E']['hi_masked_vs_full_max_rel']:.4f}, hi-l4={d['E']['highl_into_masked_max_rel']:.3e}), "
            f"B(mask-full={d['B']['hi_masked_vs_full_max_rel']:.4f}, hi-l4={d['B']['highl_into_masked_max_rel']:.3e})"
        )


if __name__ == "__main__":
    main()
