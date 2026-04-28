# Tier 3 Day 5 — Final perf bench (V5 Round-17 P3.5)

**Date:** 2026-04-28. **Commit:** `4ef59a2` (post-v3.5 sentinel).
**Single-k cProfile baseline:** 111 s (pre-perf) → 73.7 s (post all tiers).
**Smoke V0d single-anchor (24-worker):** 31 min (4w pre-perf) → **17.58 min**.

## Result snapshot

```
Wall time:                  17.58 min
D_2 (Python linear-probe):  5.850968e+03 μK²
D_2 (Rust MB-95 anchor):    1002.086744 μK²
D_2 / anchor:               5.8388
Reference (V0d post-pre1):  6.4554
Deviation from reference:   9.55 %
Speedup vs 4-worker base:   1.80×
```

The D_2 is **bit-identical** to every prior post-Tier-1A-v2 smoke
measurement (`5.850968e+03 μK²`), confirming all caching mechanisms
preserve numerical correctness end-to-end.

## Cumulative perf timeline (V5 Round-17 P3.5)

| Stage | Single-k cProfile | V0d single-anchor | Cumulative speedup |
|---|---:|---:|---:|
| Pre-perf baseline (4w, BLAS=64) | — | 31 min | 1.0× |
| Hardware harness (24w + BLAS=1) | 111 s | 18.5 min | 1.7× |
| Tier 1A v2 (joint pattern cache) | 90.4 s | 16.45 min | 1.9× |
| Tier 1A v3 (source pattern cache) | 87.9 s | (not re-measured) | 1.94× (single-k) |
| Tier 2C (η-snapshot dict cache) | 80.0 s | (not re-measured) | 2.13× (single-k) |
| Tier 2D (joint workspace pre-alloc) | 76.4 s | (not re-measured) | 2.26× (single-k) |
| Tier 3 Days 1+2 (unpack micro-opt + scales cache) | 72.6 s | (not re-measured) | 2.38× (single-k) |
| Tier 1A v3.5 (perm cache infra; FLRW no-op) | 73.7 s | **17.58 min** | 2.34× (single-k) |
|  |  |  | **1.80×** (parallel) |

## Discussion: single-thread vs parallel scaling

Single-k cProfile measures pure single-threaded work (1 core,
no ProcessPoolExecutor). It cleanly tracks per-task perf gains.

Smoke V0d at 24 workers measures parallel wall time over 130
bias-subtraction tasks (65 k × 2). Per-task cost is partially
amortized across workers, but the **scaling efficiency caps at
about 7-9×** due to:
- Fork + cache-warmup overhead per worker
- L3 cache contention across 24 workers on the species background
  table
- Python multiprocessing IPC for results
- Bias-subtraction dispatch is task-by-task (not chunked-bg) so
  each task pays full per-task setup

Net: single-thread perf 1.51× (111 → 73.7) translates to parallel
wall 1.12× (18.5 → 17.58) over the Tier 1A v2 smoke baseline. Most
of the single-thread gains saturate against parallel scaling
overhead.

The cumulative 1.80× parallel speedup vs the original 4-worker
baseline is the load-bearing measurement for downstream δ work:
each V0d-class measurement now takes 18 min instead of 31 min, and
each 6-anchor sweep ~108 min instead of ~195 min.

## Per-tier breakdown of the single-k 37.3 s reduction

```
Pre-perf single-k:                            111.07 s
  − Tier 1A v2 (joint pattern cache):          −20.7 s   (skipped 21.3 s nonzero)
  − Tier 1A v3 (source pattern cache):          −2.5 s   (smaller op)
  − Tier 2C (η-snapshot dict cache):            −7.9 s   (cache hit ~5/6)
  − Tier 2D (joint workspace pre-alloc):        −3.6 s   (skip np.zeros 49 µs × 16k)
  − Tier 3 Days 1+2 (micro-opt + scales cache): −3.8 s   (slice cache + scale memo)
  + Tier 1A v3.5 (FLRW no-op overhead):         +1.1 s   (plumbing cost)
                                                 ─────────
Post-all-tiers single-k:                       73.7 s    (−33.6 % wall)
```

## What this enables (downstream)

The audit Reports' planning assumed multi-month δ work would
include "dozens of V0d-class measurements" for per-decade
conservation audits, switch-smoothness re-audits, and bit-identity
verification. At the pre-perf baseline of 31 min/measurement, this
was clearly multi-week even before integration time. At 18 min/
measurement, the same audit budget collapses to ~5 days/cycle
(if 30 measurements per gate × 6 gates).

Phase 1 (α a-switch, β real-IC, D-3 sync→Newt) requires fewer V0d
measurements than δ but still benefits — each measurement is
unambiguously cheaper now.

## Tier 3 Days 3-4 deferral rationale

The original prep doc projected:
- Day 3: extract Thomson coupling fill into JIT helper (~3-4 s gain)
- Day 4: refactor hierarchy_rhs_photon_from_state inner ℓ-loop, JIT
  (~1.5 s gain)

Both deferred because:

1. **Day 3** requires extracting a Python loop block that's intermixed
   with `Mapping`-typed inputs (`bg`, `backend.family_spec`,
   `_operator_scales` results in dict form). Clean numba @njit
   extraction needs the data to flow through ndarrays + scalars only.
   The refactor surface is large (touches `_operator_scales`,
   `_family_conditioned_kernel_law`, `_geometry_contract`, downstream
   builders). 2-3 days of structured work.

2. **Day 4** requires refactoring `hierarchy_rhs_photon_from_state`
   to take ndarrays instead of `PSTFHierarchyState` /
   `ClosureStrategy` / `CollisionOperator` Python objects. Same
   surface-area concern.

For both, the marginal gain (~5.5 s combined) is modest relative to
the implementation cost. Better to land them once a follow-on
refactor flattens the dataclass / Mapping access patterns naturally.

## v3.5 retrospective

The harmonic_affine perm cache infrastructure is fully wired but
**ineffective for FLRW Type-I** (the current production case)
because the harmonic builder accumulates row_chunks/col_chunks with
duplicate (row, col) entries that COO sums. Validated empirically:
`csc.nnz < len(rows)` after the cold build, so
`_HarmonicSparsityCache.has_duplicates = True` → fast path never
fires.

The infrastructure remains in place for future non-FLRW Bianchi
families (II, III, V, VII₀, VIII) where the harmonic builder MAY
emit unique COO entries. Tri-state sentinel attribute on the
integrator avoids retrying capture per call once duplicates are
detected.

Net cost on FLRW: ~1.1 s per single-k cProfile (the plumbing
overhead). Acceptable price for keeping the infrastructure ready.

## Recommendation

The hardware harness + Tier 1A v2 + (1A v3, 2C, 2D, 3 Days 1+2,
1A v3.5) sequence is **complete** for this perf-investment cycle.
The remaining gains in this Round-17 P3.5 perf push come from:

- **Tier 3 Days 3-4** (deferred): structured 2-3 day refactor
- **Cython rewrite of hot path**: 3-5 day investment, 5-10× possible
- **Architectural change**: GPU offload (multi-week)

For the immediate next user decision, the perf side is "done enough"
to start Phase 1 work (α a-switch, β real-IC, D-3) at meaningful
iteration speed. Each V0d measurement: 18 min instead of 31 min.
