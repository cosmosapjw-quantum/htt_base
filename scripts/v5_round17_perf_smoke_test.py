"""V5 Round-17 P3.5 perf smoke test — single-anchor V0d at η_init=261.

This is a quick benchmark of the post-optimization pipeline, used to
verify the cumulative speedup of:
  1. n_workers=None (auto-detect = 24 on the user's Ryzen 9 5900X) vs
     legacy hard-coded 4
  2. FLRWPipelineConfig.{rtol, atol, max_step_factor} diagnostic relaxation
  3. The Round-15 P0 / Round-16 / pre1+pre2+pre3 stack (already landed)

Pre-optimization V0d wall time at η_init=261:
  ~31 min (1 sweep of 65 k-points × bias-subtraction at 4 workers)

Target wall time post-optimization:
  ~2-5 min (24 workers × ~3× from looser tolerances + max_step_factor=100)

Compares the result D_2 against V0e's bit-zero reference (6.43) to
verify the relaxed-tolerance approximation hasn't introduced a
> 1 % deviation.

Usage::

    cd /home/cosmosapjw/Dropbox/bianchi/htt_base
    venv/bin/python scripts/v5_round17_perf_smoke_test.py
"""
from __future__ import annotations

import os

# Round-17 P3.5 perf fix: limit BLAS thread count to 1 BEFORE numpy is
# imported. Without this, each ProcessPoolExecutor worker spawns its own
# OpenBLAS thread pool (default MAX_THREADS=64); 24 workers × ~12 BLAS
# threads = ~288 threads on 24 cores → context-switching kills
# throughput. With per-worker BLAS=1, workers do single-threaded numerics
# and parallelism scales with worker count.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import sys
import time
from pathlib import Path

_HTT_ROOT = Path(__file__).resolve().parents[1] / "htt"
_HTT_SRC = _HTT_ROOT / "src"
if _HTT_SRC.is_dir() and str(_HTT_SRC) not in sys.path:
    sys.path.insert(0, str(_HTT_SRC))
if str(_HTT_ROOT) not in sys.path:
    sys.path.insert(0, str(_HTT_ROOT))

import numpy as np

from bass.species.registry import SpeciesBackgroundRegistry
from bass.spectrum.cl_assembly import CLAssemblyConfig
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig,
    compute_flrw_d_ell_linear_probe,
)


D2_ANCHOR_UK2 = 1002.086744


def main() -> None:
    print("=" * 78)
    print("V5 Round-17 P3.5 perf smoke test — single anchor V0d at η_init=261")
    print("=" * 78)
    print(f"detected logical CPUs: {os.cpu_count()}")
    print()

    t_start = time.perf_counter()
    print(f"[t=0.0 min] building Planck 2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )

    k_grid = np.logspace(-4.0, -1.5, 65)
    # Bisect bottom: PRODUCTION tolerances + max_step_factor. Sole change
    # vs original V0d: n_workers=None (24 vs 4) + BLAS thread cap. Tests
    # whether parallelization alone gives meaningful speedup, with
    # accuracy bit-identical to the V0d post-pre1 reference.
    pipeline_cfg = FLRWPipelineConfig(
        L_max_tower=8,
        ell_max_transfer=8,
        rtol=1e-6,
        atol=1e-9,
        max_step_factor=1000,
    )
    assembly_cfg = CLAssemblyConfig(
        ell_max=8, k_grid=k_grid, quadrature="simpson",
    )

    elapsed_min = (time.perf_counter() - t_start) / 60.0
    print(
        f"[t={elapsed_min:.2f} min] launching compute_flrw_d_ell_linear_probe"
    )
    print(
        f"               (probe_b_k_sq=1.0, N_k={k_grid.size}, "
        f"n_workers=None (auto), rtol=1e-4, atol=1e-7, max_step_factor=100)"
    )
    bundle = compute_flrw_d_ell_linear_probe(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        assembly_config=assembly_cfg,
        probe_b_k_sq=1.0,
        n_workers=None,  # auto-detect = 24 on Ryzen 9 5900X
    )
    elapsed_min = (time.perf_counter() - t_start) / 60.0
    d_tt = bundle["d_tt"]
    d2 = float(d_tt[2])
    rel_err = abs(d2 - D2_ANCHOR_UK2) / D2_ANCHOR_UK2
    ratio_to_anchor = d2 / D2_ANCHOR_UK2

    print()
    print("=" * 78)
    print("RESULT")
    print("=" * 78)
    print(f"  Wall time: {elapsed_min:.2f} min")
    print(f"  D_2 (Python linear-probe): {d2:.6e} μK²")
    print(f"  D_2 (Rust MB-95 anchor):   {D2_ANCHOR_UK2:.6f} μK²")
    print(f"  D_2 / anchor:              {ratio_to_anchor:.4f}")
    print(f"  Reference (post-pre1, η_init=261): 6.4554 (V0d) / 6.4395 (V0e)")
    print(f"  Relative deviation from post-pre1 reference: "
          f"{abs(ratio_to_anchor - 6.455) / 6.455 * 100:.2f}%")
    print()
    print("Pre-optimization wall time at this anchor:  ~31 min (4 workers,")
    print("                                             rtol=1e-6, atol=1e-9,")
    print("                                             max_step_factor=1000).")
    print(f"Speedup ratio (this run / 31 min): {31.0 / elapsed_min:.1f}×")
    print()


if __name__ == "__main__":
    main()
