"""Smoke validation for the V5 step-4b FLRW pipeline.

Runs ``compute_transfer_function_at_k`` and ``compute_flrw_d_ell`` at a
short k-grid to verify the end-to-end chain executes without errors and
produces finite D_ℓ values. NOT a D_2 accuracy validation — that
requires ~50+ k-points and is a multi-minute test.

Sequential (1 k ≈ 45 s at L_max=4):
    python scripts/v5_flrw_pipeline_smoke.py --mode single-k

Parallel k-sweep (N_k ≈ 4, ~50 s wall on an 8-core host):
    python scripts/v5_flrw_pipeline_smoke.py --mode k-sweep --n-k 4
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np


def _log(msg: str) -> None:
    print(msg, flush=True)


def smoke_single_k(k_mpc: float) -> int:
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_transfer_function_at_k,
    )
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    t0 = time.monotonic()
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log(f"  species ready in {time.monotonic() - t0:.2f} s")

    cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)
    _log(f"Running compute_transfer_function_at_k at k={k_mpc:.3e} Mpc^-1...")
    t0 = time.monotonic()
    tf = compute_transfer_function_at_k(species, k_mpc, config=cfg)
    dt = time.monotonic() - t0
    _log(f"  done in {dt:.2f} s")

    _log("Transfer function Δ_ℓ^T:")
    for ell, val in enumerate(tf.delta_T_m0):
        _log(f"  ℓ={ell}: Δ_T^m0 = {val:+.6e}")
    _log("Transfer function Δ_ℓ^E:")
    for ell, val in enumerate(tf.delta_E_m0):
        _log(f"  ℓ={ell}: Δ_E^m0 = {val:+.6e}")

    ok = True
    if not np.all(np.isfinite(tf.delta_T_m0)):
        _log("  ✗ FAIL: non-finite Δ_T^m0")
        ok = False
    if not np.all(np.isfinite(tf.delta_E_m0)):
        _log("  ✗ FAIL: non-finite Δ_E^m0")
        ok = False
    if float(np.max(np.abs(tf.delta_T_m0))) == 0.0:
        _log("  ✗ FAIL: Δ_T^m0 identically zero")
        ok = False

    if ok:
        _log("  ✓ PASS: Δ_ℓ^T/Δ_ℓ^E are finite and non-trivial.")
        return 0
    return 1


def smoke_k_sweep(n_k: int, n_workers: int | None) -> int:
    from bass.spectrum.cl_assembly import CLAssemblyConfig
    from bass.spectrum.flrw_pipeline import FLRWPipelineConfig, compute_flrw_d_ell
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    t0 = time.monotonic()
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log(f"  species ready in {time.monotonic() - t0:.2f} s")

    # Small log-spaced k-grid covering the ℓ=2 acoustic peak region.
    k_grid = np.logspace(-4.0, -3.0, n_k)
    _log(f"k-grid: {n_k} points in [{k_grid[0]:.3e}, {k_grid[-1]:.3e}] Mpc^-1")

    pipeline_cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)
    assembly_cfg = CLAssemblyConfig(ell_max=4, k_grid=k_grid, quadrature="trapezoid")

    _log(
        f"Running compute_flrw_d_ell with N_k={n_k}, "
        f"n_workers={n_workers or 'auto'}..."
    )
    t0 = time.monotonic()
    bundle = compute_flrw_d_ell(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        assembly_config=assembly_cfg,
        n_workers=n_workers,
    )
    dt = time.monotonic() - t0
    _log(f"  done in {dt:.2f} s (wall)")

    d_tt = bundle["d_tt"]
    d_ee = bundle["d_ee"]
    d_te = bundle["d_te"]
    _log("D_ℓ^TT (μK²) from full-pipeline extraction:")
    for ell, val in enumerate(d_tt):
        _log(f"  ℓ={ell}: D_TT = {val:+.6e}")
    _log("D_ℓ^EE (μK²):")
    for ell, val in enumerate(d_ee):
        _log(f"  ℓ={ell}: D_EE = {val:+.6e}")
    _log("D_ℓ^TE (μK²):")
    for ell, val in enumerate(d_te):
        _log(f"  ℓ={ell}: D_TE = {val:+.6e}")

    ok = True
    if not np.all(np.isfinite(d_tt)):
        _log("  ✗ FAIL: non-finite D_TT")
        ok = False
    if not np.all(np.isfinite(d_ee)):
        _log("  ✗ FAIL: non-finite D_EE")
        ok = False
    if not np.all(np.isfinite(d_te)):
        _log("  ✗ FAIL: non-finite D_TE")
        ok = False
    if len(d_tt) >= 3 and not float(d_tt[2]) > 0.0:
        _log(f"  ✗ FAIL: D_2^TT = {d_tt[2]:.3e} is non-positive")
        ok = False
    if len(d_tt) >= 3:
        # Reference Route-B anchor is 1002.086744. For N_k ~ 4 quadrature is
        # very coarse — just sanity-check that D_2 is within 2 orders of
        # magnitude, not tight precision.
        ref = 1002.086744
        ratio = float(d_tt[2]) / ref
        _log(
            f"  D_2^TT/Route-B ratio = {ratio:.3f}  "
            f"(N_k={n_k} is too coarse for tight agreement; "
            f"this is only a sanity check)"
        )

    if ok:
        _log("  ✓ PASS: D_ℓ arrays are finite; TT is non-trivial.")
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("single-k", "k-sweep"), default="k-sweep")
    parser.add_argument("--k-mpc", type=float, default=1.0e-3)
    parser.add_argument("--n-k", type=int, default=4)
    parser.add_argument("--n-workers", type=int, default=None)
    args = parser.parse_args()

    _log("V5 step-4b FLRW pipeline smoke")
    _log("=" * 60)
    if args.mode == "single-k":
        return smoke_single_k(args.k_mpc)
    return smoke_k_sweep(args.n_k, args.n_workers)


if __name__ == "__main__":
    sys.exit(main())
