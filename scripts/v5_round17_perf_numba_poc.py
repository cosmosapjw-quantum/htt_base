"""V5 Round-17 P3.5 Tier 3 prep — numba toolchain POC.

Verifies the venv has a working numba + LLVM backend by JIT-compiling
a small numerical helper, AOT-caching it, and asserting bit-equality
against pure-NumPy across 1000 random inputs.

Pass criterion: 1000 random inputs produce bit-equal results between
``@njit``-compiled and pure-NumPy implementations.

Usage::

    cd /home/cosmosapjw/Dropbox/bianchi/htt_base
    venv/bin/python scripts/v5_round17_perf_numba_poc.py
"""
from __future__ import annotations

import os

# Match the BLAS thread cap pattern used by all v5_round17 perf scripts.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import time

import numpy as np
from numba import njit


@njit(cache=True)
def thomson_diagonal_damping_jit(
    inv_source: np.ndarray,
    coeff: float,
) -> np.ndarray:
    """JIT version: ``inv_source * coeff`` (used as ``-np.diag(...)``
    contribution in the Thomson source-block damping at
    ``ver3_layout_protocol.py:2447`` style operations).
    """
    n = inv_source.shape[0]
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        out[i] = inv_source[i] * coeff
    return out


def thomson_diagonal_damping_numpy(
    inv_source: np.ndarray,
    coeff: float,
) -> np.ndarray:
    """Pure-NumPy reference."""
    return inv_source * coeff


def main() -> None:
    print("=" * 78)
    print("V5 Round-17 Tier 3 prep — numba toolchain POC")
    print("=" * 78)

    rng = np.random.default_rng(42)

    # Warmup compile (first call triggers JIT). Time it separately.
    t_compile_start = time.perf_counter()
    inv0 = rng.standard_normal(8)
    c0 = float(rng.standard_normal())
    _ = thomson_diagonal_damping_jit(inv0, c0)
    compile_time = time.perf_counter() - t_compile_start
    print(f"\nFirst-call (JIT compile) wall: {compile_time * 1000:.1f} ms")
    print("(Subsequent runs of this script use the AOT cache; "
          "compile time should drop to < 5 ms.)")

    # Bit-equal validation across 1000 random inputs.
    n_pass = 0
    t_validate_start = time.perf_counter()
    for trial in range(1000):
        size = int(rng.integers(low=1, high=64))
        inv = rng.standard_normal(size)
        coeff = float(rng.standard_normal())
        np_result = thomson_diagonal_damping_numpy(inv, coeff)
        nb_result = thomson_diagonal_damping_jit(inv, coeff)
        if np.array_equal(np_result, nb_result):
            n_pass += 1
        else:
            print(
                f"  trial {trial}: MISMATCH at size={size}, coeff={coeff:.6e}"
            )
            print(f"    numpy={np_result}")
            print(f"    numba={nb_result}")
    validate_time = time.perf_counter() - t_validate_start
    print(
        f"\nBit-equality validation: {n_pass}/1000 PASS in "
        f"{validate_time * 1000:.1f} ms"
    )

    # Per-call timing (small input).
    inv = rng.standard_normal(8)
    coeff = float(rng.standard_normal())
    n_iter = 100_000
    t_jit_start = time.perf_counter()
    for _ in range(n_iter):
        thomson_diagonal_damping_jit(inv, coeff)
    t_jit = time.perf_counter() - t_jit_start
    t_np_start = time.perf_counter()
    for _ in range(n_iter):
        thomson_diagonal_damping_numpy(inv, coeff)
    t_np = time.perf_counter() - t_np_start
    print(
        f"\nPer-call timing (size=8, n_iter={n_iter}):"
    )
    print(
        f"  numba @njit:  {t_jit / n_iter * 1e6:.2f} µs/call"
    )
    print(
        f"  pure NumPy:   {t_np / n_iter * 1e6:.2f} µs/call"
    )
    speedup = t_np / t_jit if t_jit > 0 else float("inf")
    print(f"  speedup: {speedup:.2f}× (numba over numpy)")

    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    if n_pass == 1000:
        print("✅ numba toolchain WORKING. JIT compiled, cached, bit-equal output.")
        print("   Ready for Tier 3 implementation per "
              "PERF_TIER3_NUMBA_JIT_PREP.md roadmap.")
    else:
        print(f"❌ {1000 - n_pass} mismatches detected. Investigate before "
              "proceeding to Tier 3 implementation.")


if __name__ == "__main__":
    main()
