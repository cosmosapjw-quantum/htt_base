# BASS Rust solver — performance optimization release notes

This branch consolidates the equation-independent numerical-kernel
optimizations. All changes are math-identical syntactic rewrites;
production D_ℓ is bit-exact at every ℓ on the mini 50k Rodas5P reference
run (D_2 = 967.4, D_10 = 958.2, D_30 = 543.8, D_100 = 1561.9, D_200 =
9209.2).

## Commit sequence

```
d06f4b7  PR-PERF-07: LU pivot row block swap + atomic counter plumbing
00c1dab  PR-PERF-05: iter/zip rewrite of LU + matvec hot loops
1440844  PR-IMEX-04: k-heuristic routing + production wiring complete
f707f7c  PR-PERF-03: Miller branch tuning (base 32→16, slope 0.5→0.4)
5dbd1c2  profiling: pprof-rs + phase timer + Bessel branch counters
428e229  WIP PR-IMEX-03: production wiring scaffold
```

## PR-PERF-05 — the measurable win

`src/core/lu.rs` and `src/solver/rodas5p.rs`: LU factor, LU solve, and
matvec inner loops rewritten using `iter().zip()`, `split_at_mut`,
`chunks_exact_mut`. The prior index-arithmetic form (`a[i*n+j] -= fac *
a[k*n+j]`) used a single `&mut [f64]` for both reads and writes in the
axpy inner loop, forcing the compiler to emit aliasing checks that
blocked any reduction to vectorized code. Splitting rows into disjoint
slices gives LLVM non-aliased iterator pairs.

Primary 200k Rodas5P parallel, 3-run median: **35.6 s → 34.2 s (-4%)**.

Module shift at primary scale (500 Hz sampling, serial):
| module         | before | after  |
|----------------|--------|--------|
| ODE_LU         | 21.7%  | 18.2%  |
| ODE_Rodas5P    | 18.6%  | 19.3%  |
| LoS_Bessel     | 57.7%  | 59.5%  |

Function-level, primary scale:
| function               | before | after  | relative |
|------------------------|--------|--------|----------|
| lu_factor_in_place     | 10.8%  | 7.7%   | -29%     |
| linear_profile_rhs_only| 11.3%  | 9.6%   | -15%     |
| lu_solve_factored_flat | 10.9%  | 10.4%  | -5%      |

Phase timer (serial primary):
|                 | before  | after   | Δ       |
|-----------------|---------|---------|---------|
| ODE solve       | 19.4 s  | 18.5 s  | -4.6%   |
| LoS integration | 17.6 s  | 16.3 s  | -7.4%   |
| total           | 37.1 s  | 34.8 s  | -6.2%   |

Three new correctness tests in `src/core/lu.rs` enforce bit-identical
output vs a scalar reference implementation:
 - `lu_factor_matches_reference_random_24x24` (max |Δ| = 0)
 - `lu_solve_bit_exact_24x24` (residual < 1e-10)
 - `lu_solve_3x3_exact` (hand-computed case)

## PR-PERF-07 — block pivot swap + counter plumbing

Pivot row exchange replaced with contiguous slice swap:

```rust
let (lo, hi) = a.split_at_mut(piv_row * n);
lo[k*n..(k+1)*n].swap_with_slice(&mut hi[..n]);
```

Single pair of memcpy-backed swaps instead of N scalar element swaps.
No measurable wall-clock change in sandbox (variance-level difference
only); retained for code clarity and because the memcpy form is
the objectively correct primitive for row exchange.

Also adds `BASS_LU_PROF=1` counter plumbing (`LU_FACTOR_CALLS`,
`LU_PIVOT_SWAPS`) behind `OnceLock` gating, parallel to the existing
`bessel_prof_*` infrastructure. Zero overhead when disabled.

## Experiments that did not ship

**`target-cpu=x86-64-v3`** (AVX2+FMA auto-vectorization): +5–8%
regression in sandbox. Hot loops (Miller Bessel recurrence, LU
factor/solve, matvec reductions) carry sequential data dependencies
that block auto-vectorization; the wider AVX2 code path increased
i-cache pressure without benefit. Reverted; `.cargo/config.toml`
intentionally not committed. May be worth revisiting on bare-metal
after further scalar-level restructuring.

**Bessel Miller two-phase split**: restructured the downward recurrence
into separate `n > lmax` (no-write) and `n ≤ lmax` (write) loops to
eliminate per-iteration bound checks. Passed all three Bessel accuracy
tests bit-exact, but primary 200k showed no measurable wall-clock
change (34.21 s → 34.57 s, variance-level). The `if n <= lmax` check is
a monotonic predicate the branch predictor handles at ~0 cost, and the
Phase-1 iterations are only ~13% of the total ladder at primary scale.
Reverted; code complexity was not justified by sandbox measurements.

## Build

`target-cpu` left at Rust default (x86-64 baseline) so the binary runs
on any amd64 deployment. Release profile unchanged from upstream Cargo
defaults; no `.cargo/config.toml` required.

```
cargo build --release
cargo test --release --lib
```

## Known pending items

 - Pivot-swap frequency on CAMB matrices is not yet measured. The
   atomic counter plumbing (PR-PERF-07-B) is in place; driving it from
   a dedicated test would settle whether Rodas5P sees pivoting at all.
 - `unsafe { get_unchecked }` in the iter/zip inner loops could
   eliminate residual bounds checks (estimated 2–5% additional).
 - `LinearProfileDyn::sample_matrix_only_into_hint` (matrix
   interpolation, called once per ODE step) has not been audited for
   algorithmic simplification.
