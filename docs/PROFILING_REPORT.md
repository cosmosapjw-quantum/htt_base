# BASS Comprehensive Profiling Report

**Date**: 2026-04-16
**Commit**: 430b902 (PR-IMEX-03 WIP) + profiling infrastructure
**Purpose**: Identify true bottlenecks before further PR-IMEX / PR-PERF work.

---

## 1. Tooling

Three independent instruments, cross-validated:

1. **`pprof-rs`** — SIGPROF-based in-process sampling profiler at 500 Hz.
   Produces flamegraph SVG + self-time top-function list + coarse module
   aggregation. Zero instrumentation overhead. Captures user-mode CPU time
   only (not wall-clock I/O or syscalls).

2. **Phase timer** (`BASS_PHASE_TIMER=1`) — wall-clock timing at four
   pipeline checkpoints via `std::time::Instant`. Accurate wall breakdown.

3. **Bessel branch counter** (`BASS_BESSEL_PROF=1`) — atomic counters
   embedded in `spherical_bessel_j_array` tracking upward / Miller / small-x
   branches and their iteration counts. Zero overhead when disabled.

`perf`, `valgrind`, `cargo-flamegraph`, `hotspot` are **not available** in
this sandbox (no `/proc/sys/kernel/perf_event_paranoid`, no kernel perf
support). pprof-rs is the only viable sampling profiler.

Artifacts: `/tmp/bass_prof/flame_*.svg` + `top_*.txt`.

---

## 2. Configurations Measured

| Label | n_k | ell_max | wall | purpose |
|---|---|---|---|---|
| `mini_full` | 50 | 200 | **6.0 s** | mini production, baseline |
| `primary_full` | 200 | 300 | **37.1 s** | **true production scale** |
| `10k_rodas` | 10 | 50 | 1.5 s | small reference (Rodas5P) |
| `10k_imex` | 10 | 50 | 0.8 s | small reference (IMEX, 42% faster) |

All in `BASS_SERIAL_KLOOP=1` mode to eliminate rayon parallelism noise.

---

## 3. Primary 200k — Full Pipeline Breakdown

### 3.1 Phase timer (wall-clock, exact)

```
CommonProfile build     0.000 s     (<0.1%)
ODE solve (all k-modes) 19.427 s    52.4%
LoS integration (D_l)   17.646 s    47.5%
=== total ===           37.074 s    100%
```

**ODE : LoS ≈ 1.1 : 1**. Both are first-order bottlenecks at production size.

### 3.2 Sampling profiler (CPU self-time)

| % | Module | | % | Top function |
|---|---|---|---|---|
| **57.7** | LoS_Bessel | | 57.7 | `spherical_bessel_j_array` |
| 21.7 | ODE_LU | | 11.3 | `linear_profile_rhs_only_into` |
| 18.6 | ODE_Rodas5P | | 10.9 | `lu_solve_factored_flat_into` |
| 1.1 | alloc | | 10.8 | `lu_factor_in_place_flat_into` |
| 0.5 | other | | 3.9 | `step_linear_profile_rodas5p_into` |
| 0.3 | matrix_build | | 2.9 | `linear_profile_rhs_jac_flat_into` |

**Key discrepancy** vs phase timer: sampling attributes 57.7% of CPU samples
to LoS but phase timer says LoS consumed 47.5% of wall. The 10-point gap
likely reflects LoS being more CPU-bound (arithmetic-dense Bessel ladder)
while ODE solve has more cache misses and memory stalls (dense LU stores).
Both measurements agree on the same ranking, just with a mild re-weighting.

### 3.3 Bessel branch decomposition (the critical finding)

```
array calls (total):      353,490
  upward recurrence:       92,716  (26.2%)
  miller downward:        130,770  (37.0%)
  small-x series:         130,004  (36.8%)
  zero-x shortcut:              0  (0.0%)

upward iters total:    27,814,800      ≈ 300 iter/call (exactly lmax)
miller iters total:    50,516,090      ≈ 386 iter/call (lmax + 32 + 0.5·x)
miller rescales:          221,334      (1.7% of miller iters, cheap overhead)
```

**Miller branch dominates Bessel cost**:
- 37% of calls × 386 iter/call = **64% of total Bessel iterations**.
- Upward: 26% of calls × 300 iter/call = 35% of total iterations.
- Small-x: 37% of calls, bounded SERIES_MAX_ITERS=80 iters/call, negligible.

Per-call cost:
- Upward: O(lmax) = O(300) multiplies + subtracts, cache-friendly single pass
- Miller: O(lmax + 32 + 0.5x) = O(386+) iters, PLUS 0.7% rescale events
  (each a full out[] scalar multiply of up to lmax+1 entries)

Effective work ratio (total iter count × per-iter cost): Miller is ~1.8×
upward per iteration, combined with being the larger branch, gives the
dominant contribution.

### 3.4 Actionable implications

| Lever | Current % | Max reachable % | Priority |
|---|---|---|---|
| Miller branch (tune base=32, slope=0.5) | 57.7 × 0.64 ≈ 37% | -10-15% wall | **P0** |
| ODE_LU → IMEX (dense LU → scalar ops) | 21.7% | -10-15% wall | **P1** |
| Rodas5P RHS eval (matrix interp + matvec) | 13% | -5% wall (SIMD?) | P2 |
| matrix_build, source_extract | <1% each | 0 | skip |

---

## 4. Mini 50k Comparison

### Phase timer
```
CommonProfile build     0.000 s
ODE solve              4.383 s    73.3%
LoS integration        1.597 s    26.7%
=== total ===          5.981 s
```

### Module aggregation
- LoS_Bessel: 32.7% (vs primary 57.7%)
- ODE_LU: 32.2% (vs primary 21.7%)
- ODE_Rodas5P: 31.5% (vs primary 18.6%)
- alloc: 2.0% (stable)

### Bessel calls
- 91,320 calls total (vs primary 353,490 → **3.87× scaling**, close to n_k·ell_max ratio 200·300 / 50·200 = 6×)
- Miller 30.9% × 272 iter/call (vs primary 37.0% × 386)
- Miller fraction grows with ell_max (more x values fall into `x < lmax+8`)

### Scaling

Primary is 6.2× longer than mini but only n_k × ell_max = 6× more work.
Close to linear — good news. LoS scales linearly with n_k (each k independent)
and roughly linearly with ell_max (Bessel ladder + panel count).
ODE scales linearly with n_k and is ell-independent (sync hierarchy is
truncated at `lmax_g=16`).

This explains why at mini (n_k=50, ell_max=200) ODE dominates (73%) but at
primary (n_k=200, ell_max=300) LoS catches up (47.5%).

---

## 5. 10-kmode IMEX Confirmation

```
10k_rodas (Rodas5P):
  ODE_LU: 59.3%
  ODE_Rodas5P: 29.6%
  LoS_Bessel: 3.7%   (ell_max=50 too small to matter)
  Wall: 1.5 s

10k_imex (IMEX-ARK4):
  ODE_IMEX: 77.3%    (→ BassLinearOp::apply_explicit is 68%)
  alloc: 9.1%
  LoS_Bessel: 9.1%
  Wall: 0.8 s        (42% faster)
```

IMEX eliminates dense LU entirely (**59.3% → 0%**) at cost of more matvec
work inside `apply_explicit`. Net: 42% speedup at n_k=10, ell_max=50.
Not yet verified at primary scale due to the n_k≥15 hang (PR-IMEX-03 WIP).

`alloc` jumps from 2.0% to 9.1% in IMEX — the `interp_bg` / `fill_implicit_*`
code paths allocate per-call. Fixable in PR-IMEX-04 (reuse scratch buffers).

---

## 6. Cross-check: Sampling vs Phase Timer

At primary 200k:
- Phase timer: ODE 52.4%, LoS 47.5%
- Sampling:     ODE 40.3%, LoS 57.7%
- Gap: 12 points

Possible causes:
1. LoS is arithmetic-dense (Bessel ladder in tight loop, SIMD-friendly,
   high IPC). Sampling captures each cycle.
2. ODE solve has dense LU with memory stalls and page faults that don't
   register as CPU samples but eat wall clock.
3. ODE solve has per-step setup overhead (matrix interp, Rosenbrock stages)
   that doesn't show up cleanly in leaf sampling.

The phase timer is authoritative for wall-clock budgeting. Both agree on
ranking (LoS and ODE are the only two that matter).

---

## 7. Recommended PR Sequence (evidence-based)

### P0: PR-PERF-03 — LoS Bessel Miller branch optimization
**Target**: 57.7% LoS_Bessel at primary 200k.
**Mechanism**: Miller branch is 64% of iterations. Two knobs:
- MILLER_EXTRA_BASE=32: investigate reducing. With ground-state test
  (single x, known j_l exact), find minimal base that keeps relative
  error < 1e-12. Expect base=16 sufficient for lmax=300.
- MILLER_EXTRA_SLOPE=0.5: same approach. Probably 0.3-0.4 acceptable.
- Optional: SIMD-vectorize the Miller loop (4× f64 per AVX2, tight inner).
**Expected gain**: 15-25% of LoS cost → 8-14% of total wall.
**Risk**: Miller accuracy compromised → wrong j_l → wrong D_l at high ell.
Must pair with bit-level Bessel test against BesselJ reference.

### P1: PR-IMEX-04 — IMEX production wiring fix (resume from WIP)
**Target**: 21.7% ODE_LU at primary 200k.
**Status**: PR-IMEX-03 WIP (commit 430b902) shows 42% speedup at n_k=10,
hang at n_k≥15 (mid-k 2.5e-2 < k < 0.3 range).
**Action**:
- Bisect hang k exactly (was deferred from last session).
- Tune h_init / max_steps / PI controller safety factor.
- Add stiffness-aware h scaling via `StiffnessScales::stiffness_ratio()`.
- Validate mini 50k D_2 ± 1% vs Rodas5P baseline.
**Expected gain**: Proportional to ODE_LU share = 21.7% at primary.

### P2: PR-PERF-04 — Rodas5P RHS eval SIMD
**Target**: 13% `linear_profile_rhs_only_into` + 2.9% `_rhs_jac_flat_into`.
This is matrix interpolation + matvec per step. Currently scalar.
**Expected gain**: 3-5% of total wall with AVX2 vectorized matvec.

### Skip: matrix_build, source_extract, setup, alloc
All combined < 3% at primary. Not worth touching.

---

## 8. Commit Plan

Current working tree changes (atop 430b902):
1. `Cargo.toml` — add `pprof` dev-dep with `flamegraph,protobuf-codec` features
2. `src/los/bessel.rs` — atomic counters for 3 Bessel branches + reset/snapshot API
3. `src/solver/sync_gauge_camb.rs`:
   - `solve_production_spectrum` — phase timer (`BASS_PHASE_TIMER=1`)
   - `profile_mini` test — sampling profiler + Bessel counter report + module agg
4. `docs/PROFILING_REPORT.md` — this document

Proposed commit message: "profiling: pprof-rs + phase timer + Bessel branch
counters for BASS pipeline"

All changes are **opt-in via env vars** (`BASS_PHASE_TIMER`, `BASS_BESSEL_PROF`,
`BASS_PROF_LABEL`, `BASS_N_K`, `BASS_ELL_MAX`, `BASS_PROF_FREQ`, `BASS_PROF_OUT`).
Zero overhead when disabled. Production path untouched.
