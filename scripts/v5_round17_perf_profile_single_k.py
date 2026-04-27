"""V5 Round-17 P3.5 perf profiling — cProfile of a single-k Tier-B call.

Profiles `compute_transfer_function_at_k` at k = 1e-2 Mpc⁻¹ (a typical
mid-range k that exercises both the IMEX integrator and LoS projector).
Single-process, single-threaded — no parallelism overhead, isolates the
per-k Python+numpy work itself.

Output:
- ``/tmp/v5_round17_profile_single_k.prof`` — pstats binary, browsable
  via ``snakeviz /tmp/v5_round17_profile_single_k.prof``
- Stdout: top-30 cumulative-time functions

Usage::

    cd /home/cosmosapjw/Dropbox/bianchi/htt_base
    venv/bin/python scripts/v5_round17_perf_profile_single_k.py

To open the interactive snakeviz view afterward::

    venv/bin/snakeviz /tmp/v5_round17_profile_single_k.prof
"""
from __future__ import annotations

import os

# Single-thread BLAS so the profile reflects pure Python+numpy work,
# not BLAS-contention noise (consistent with the production diagnostic
# scripts post-Round-17 P3.5 perf optimization).
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import cProfile
import pstats
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
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig,
    compute_transfer_function_at_k,
)


PROFILE_PATH = "/tmp/v5_round17_profile_single_k.prof"
K_MPC = 1.0e-2  # mid-range k that exercises both IMEX and LoS


def main() -> None:
    print("[t=0.0 s] building Planck 2018 species registry...")
    t_start = time.perf_counter()

    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )

    cfg = FLRWPipelineConfig(L_max_tower=8, ell_max_transfer=8)

    elapsed = time.perf_counter() - t_start
    print(f"[t={elapsed:.1f} s] species ready; warming up (single dry run)...")

    # Warm-up call to populate any per-process JIT/cache. Otherwise the
    # profile would attribute first-call overhead (numpy import, scipy
    # spline init, etc.) to the cold path.
    compute_transfer_function_at_k(
        species, K_MPC, config=cfg, bianchi_type="I",
    )

    elapsed = time.perf_counter() - t_start
    print(
        f"[t={elapsed:.1f} s] warmup done; running cProfile on the hot call..."
    )

    profiler = cProfile.Profile()
    t_call_start = time.perf_counter()
    profiler.enable()
    compute_transfer_function_at_k(
        species, K_MPC, config=cfg, bianchi_type="I",
    )
    profiler.disable()
    t_call = time.perf_counter() - t_call_start

    print(f"[profile] hot call wall time: {t_call:.2f} s")
    print(f"[profile] saving to: {PROFILE_PATH}")
    profiler.dump_stats(PROFILE_PATH)

    print()
    print("=" * 90)
    print("TOP-30 functions by cumulative time (excluding Python builtins)")
    print("=" * 90)
    stats = pstats.Stats(profiler).sort_stats("cumulative")
    stats.print_stats(30)

    print()
    print("=" * 90)
    print("TOP-30 functions by total (self) time")
    print("=" * 90)
    stats = pstats.Stats(profiler).sort_stats("tottime")
    stats.print_stats(30)

    print()
    print("=" * 90)
    print("Total hot-call time:", f"{t_call:.2f} s")
    print(f"Open the interactive view with: snakeviz {PROFILE_PATH}")
    print("=" * 90)


if __name__ == "__main__":
    main()
