#!/usr/bin/env python3
"""C5: Project R114 C1 harmonic L=32 atlas (los_modes.tsv l<=128) through R108 Commander kernel (lmax=256)."""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import json
import shutil
import tarfile
from pathlib import Path

import healpy as hp
import numpy as np

from scripts.r109.commander_native import FAMILIES, modes as parse_modes, sha
from scripts.r111.c5_commander_leakage import (
    KERNEL_PATH,
    R108_S6_JSON,
    compare_coeff_pairs,
    harmonic_high_l_fraction,
    run_proj,
)

ROOT = Path(__file__).resolve().parents[2]
C1_TAR = Path("/home/cosmosapjw/Downloads/htt_r114/c1_atlas/C1_HARMONIC_L32_MODES.tar.gz")
R111_C5_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R111_LOCAL_HIGHL_NATIVE_20261124/C5_COMMANDER_LEAKAGE.json"
)
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r114/c5_commander")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C5_COMMANDER_LEAKAGE.json"
)


def main() -> None:
    if not KERNEL_PATH.exists():
        raise FileNotFoundError(f"Missing R108 kernel: {KERNEL_PATH}")
    if not C1_TAR.exists():
        raise FileNotFoundError(f"Run C1 first; missing {C1_TAR}")
    reg_sha = json.loads(R108_S6_JSON.read_text())["kernel"]["kernel_sha256"]
    kern_sha = sha(KERNEL_PATH)
    assert kern_sha == reg_sha, f"Kernel sha mismatch {kern_sha} != {reg_sha}"
    with np.load(KERNEL_PATH) as npz:
        k_lmax = int(npz["lmax"])
        k_nside = int(npz["nside"])
    if k_lmax < 128:
        raise ValueError(f"Commander kernel lmax={k_lmax} does not cover C1 template lmax=128")

    if RAW_ROOT.exists():
        shutil.rmtree(RAW_ROOT)
    RAW_ROOT.mkdir(parents=True)

    wall_hi, meta_hi, arr_hi = run_proj(C1_TAR, "los_modes.tsv", RAW_ROOT / "c1_harm32_los_l128")
    wall_lo, meta_lo, arr_lo = run_proj(C1_TAR, "modes.tsv", RAW_ROOT / "c1_harm32_direct_l4")

    leakage = compare_coeff_pairs(meta_hi, arr_hi, meta_lo, arr_lo)
    hi_power = harmonic_high_l_fraction(C1_TAR, "los_modes.tsv", l_cut=4)

    # Check FLRW control member power (excluded from 12-family FAMILIES tuple in commander_native)
    with tarfile.open(C1_TAR, "r:gz") as tf:
        flrw_lmax, flrw_alm = parse_modes(tf.extractfile("recoil_FLRW/los_modes.tsv").read())
    ls, _ = hp.Alm.getlm(flrw_lmax)
    flrw_max_l_ge_1 = float(np.max(np.abs(flrw_alm[:, ls >= 1])))

    r111_diff = {}
    if R111_C5_JSON.exists():
        r111 = json.loads(R111_C5_JSON.read_text())["c3_z1600_l128_vs_l4"]["per_family_leakage"]
        for fam in FAMILIES:
            r111_diff[fam] = {
                ch: abs(leakage[fam][ch]["highl_into_masked_max_rel"] - r111[fam][ch]["highl_into_masked_max_rel"])
                for ch in "TEB"
            }

    out = {
        "schema": "htt.r114.c5_commander_leakage/1",
        "claim_ceiling": "linear projection only; no observed data, noise score, prior or family claim; zero R78 promotions",
        "kernel": {
            "path": str(KERNEL_PATH),
            "sha256": kern_sha,
            "lmax": k_lmax,
            "nside": k_nside,
            "covers_c1_lmax_128": k_lmax >= 128,
        },
        "c1_archive_sha256": sha(C1_TAR),
        "wall_seconds_los_l128": wall_hi,
        "wall_seconds_direct_l4": wall_lo,
        "truncated_vs_padded_max_relative_los": meta_hi["truncated_vs_padded_max_relative"],
        "flrw_control_max_abs_alm_l_ge_1": flrw_max_l_ge_1,
        "per_family_leakage": leakage,
        "per_family_sky_high_l_power": hi_power,
        "abs_diff_vs_r111_c5_ray_leakage": r111_diff,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"C5 COMPLETE in {wall_hi:.2f}s (los) + {wall_lo:.2f}s (direct), FLRW max|a_lm(l>=1)|={flrw_max_l_ge_1:.3e}")


if __name__ == "__main__":
    main()
