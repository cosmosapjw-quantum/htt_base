# Phase B Dynamic Profiling — single-k cProfile

**Run:** 2026-04-27 (post Round-17 P3.5 perf-revert commit `d6c18d4`).
**Script:** `scripts/v5_round17_perf_profile_single_k.py`. **Hot-call wall:** 111.07 s.
**Profile artifact:** `/tmp/v5_round17_profile_single_k.prof`.

## Setup

Single-process, single-threaded (`OPENBLAS_NUM_THREADS=1`) cProfile of
`compute_transfer_function_at_k(species, k=1e-2 Mpc⁻¹, config=L_max_tower=8)`.
Warmup call first (90 s, mostly numpy/scipy import + species build), then
profiled hot call (111 s).

## Major finding 1: production path is NOT LSODA, it's a custom sparse-IMEX

The audit Reports (Round-17 external audit) traced the production path
through `LowellBianchiIntegrator.run` → `solve_ivp(method="LSODA")`. The
profile reveals this is **wrong** — the actual production path is:

```
compute_transfer_function_at_k
  → execute_tier_b_solver (bass/runtime/ver2_execution.py:2017)
  → _run_tier_b_runtime_request
  → _execute_prepared_tier_b_runtime
  → ver2_native_integrator.run (bass/hierarchy/ver2_native_integrator.py:5051)
    → _solve_segment_imex (line 4550; 109 s of 111 s = 98 %)
      → _orthogonal_residual_joint_ros2_step (line 2279; 69 s = 62 %)
        → _build_residual_joint_affine_operator (line 2120; 51.7 s = 47 %)
          → backend.build_reduced_joint_affine_operator
            → ver3_layout_protocol.build_reduced_joint_affine_operator
              → scipy.sparse._coo.__init__ + _compressed.__init__
              → numpy.ndarray.nonzero (21.3 s = 19 % self time)
```

`LowellBianchiIntegrator` is a **legacy compatibility path** (per the
docstring at `ver2_execution.py:2032`: *"the Lowell integrator only as
a retained compatibility path outside the production route"*). The
audit's "LSODA" findings (Reports 1 and 2 §3.1, §3.2, R-1) were
*structurally accurate for the legacy path* but didn't apply to the
actual production path the BF-01B-HCORE rewrite installed.

The real production path is a **custom Rosenbrock-2 (ROS2) IMEX
integrator** with sparse-matrix affine operators built from scratch
at every step. There is **no** `solve_ivp` call on the hot path.

## Major finding 2: 58 % of the wall time is sparse-matrix infrastructure, not physics

Top-30 cumulative-time decomposition of the 111 s hot call:

| Bucket | Time | % | What |
|---|---:|---:|---|
| **Sparse matrix construction** (`scipy.sparse._coo.__init__` + `_compressed.__init__`) | **64.6 s** | **58 %** | `__init__`, `prune`, `check_format`, `get_index_dtype` per step |
| **`numpy.ndarray.nonzero`** (called *inside* sparse construction) | 21.3 s | 19 % | 64,275 calls = 4 per ROS2 step |
| **`Gamma_T` Python wrapper chain** (`_resolved_gamma_t` → `Gamma_T` → `tilted_visibility.Gamma_T`) | 10.4 s | 9.4 % | 112,540 calls |
| **`numpy.zeros` allocation** | 6.9 s | 6.2 % | 1,153,206 calls = **72 zero-allocations per ROS2 step** |
| **Sparse LU + solve** (`gstrf` + `solve` + `splu`) | 5.8 s | 5.2 % | actual numerical work |
| **`hierarchy_rhs_photon_from_state`** (the actual physics RHS) | 2.5 s | **2.3 %** | 128,536 calls |
| `_unpack_hierarchy_view` | 2.1 s | 1.9 % | 449,876 calls |
| `tau_dot` (recombination spline) | 7.3 s | 6.5 % | 116,540 calls |
| Everything else | ~5 s | ~5 % | scipy interpolate, ufunc.reduce, etc. |

**The "JIT the RHS" intuition is wrong for this path.** The actual
physics RHS evaluation is only 2.3 % of total time. Numba JIT of the
RHS would give at most ~1.02× total speedup (Amdahl's law).

The dominant cost is **sparse matrix re-construction at every IMEX
step**. The integrator runs 16,069 ROS2 steps, each one constructing
~24 sparse matrices from scratch.

## Major finding 3: per-step waste is architectural

Per ROS2 step (16,069 steps total):
- 24 sparse matrix `__init__` calls (CSR + COO)
- 4 `numpy.ndarray.nonzero` calls
- 7 `Gamma_T` queries (through 3-layer Python wrapper)
- 72 `numpy.zeros` allocations
- 1 sparse LU factorization (small, 5 ms)

The sparsity pattern of the joint affine operator **does not change
across IMEX steps** — only the values do. The current implementation
rebuilds the entire CSR/COO structure every step, including:
- Dtype inference (`get_index_dtype`)
- Pattern validation (`check_format`)
- Pattern pruning (`prune`)
- Buffer allocation (`__init__`)

All of these are O(nnz) Python+scipy calls at every step. Setup
overhead dominates the small numerical work (matvec + LU).

## Implications for optimization plan

The original Phase C plan was "Numba JIT of the hot RHS path." That
plan **does not match the bottleneck**. Revised priorities:

### Tier 1 (highest ROI, 2-3 days)

**(A) Sparse pattern reuse across IMEX steps.** Build the CSR
indices/indptr once at the start of integration; per step, only
update `.data` and re-factor the LU. Eliminates `__init__`,
`nonzero`, `get_index_dtype`, `prune`, `check_format` calls.

- Estimated savings: 64.6 + 21.3 = **85 s of 111 s** if all sparse
  setup is amortized (assumes pattern is genuinely static).
- Realistic savings (some pattern changes between explicit/implicit
  stages): 50-70 s ≈ **2.5-3× speedup**.
- Affected files: `bass/hierarchy/ver3_layout_protocol.py`
  (build_reduced_joint_affine_operator),
  `bass/los/family_backend_protocol.py` (build_reduced_joint_affine_operator),
  `bass/hierarchy/ver2_native_integrator.py` (caller-side caching).

**(B) Dense matrices for small problems.** For L_max ≤ 8, the joint
affine operator is at most ~250×250 (0.5 MB dense vs the current
sparse infrastructure's ~64 s of bookkeeping per step). Dense LU via
`scipy.linalg.lu_factor`/`lu_solve` is sub-millisecond for matrices
this size.

- Estimated speedup: 5-10× if we can switch entirely. Possibly
  conflicts with Bianchi family kernel sparsity (off-axis modes have
  larger but still-sparse blocks); FLRW path is the easy target.
- Migration cost: moderate; needs a flag to dispatch dense-vs-sparse
  by problem size.

### Tier 2 (medium ROI, 1-2 days)

**(C) `Gamma_T` lookup in-lining.** 112,540 calls × ~92 μs/call
through 3-layer Python wrapper = 10.4 s. Caching the resolved
`Γ_T(η)` lookup or in-lining the wrapper chain saves 7-9 s
(~7 % speedup).

**(D) `numpy.zeros` allocation reduction.** 72 zero-allocations
per step is suspicious. Likely many small workspace arrays being
re-allocated. Pre-allocate once, reuse. Saves 5-6 s (~5 % speedup).

**(E) PCHIP migration of `build_interpolators`.** Already on the
agenda from the pre2 revert. Decoupled from perf but unlocks deep-z
default. Doesn't change per-step cost meaningfully.

### Tier 3 (lower priority)

**(F) Numba JIT of the RHS.** 2.5 s self-time gain (~2 %). Only
attractive after Tier 1 + 2 land and the dominant overheads are
eliminated.

**(G) Cython for sparse matrix workspace.** If sparse pattern reuse
(A) doesn't fully eliminate the per-step rebuild cost (because some
parts of the pattern genuinely change), Cython could rewrite the
critical reconstruct path. Keep as fallback.

## Revised Phase C plan (post-profile)

```
Day 1: Sparse pattern reuse (Tier 1A)
  - Read build_reduced_joint_affine_operator: identify what changes
    between IMEX steps (block values vs pattern).
  - Implement a CachedSparseOperator that holds CSR indices once
    and updates only .data per step.
  - Side-by-side regression: cached vs rebuild bit-equal at all η.

Day 2-3: Dense vs sparse dispatch (Tier 1B)
  - Add a problem-size threshold: < 500 dofs → dense, ≥ 500 → sparse.
  - Implement a DenseJointAffineOperator with the same interface.
  - Validate on FLRW + Bianchi-I.

Day 3-4: Gamma_T inline + zeros pre-allocation (Tier 2C, 2D)
  - Cache _resolved_gamma_t per (η, direction) call site.
  - Identify the 72 zeros calls/step; pre-allocate workspace.

Day 4-5: PCHIP migration + final benchmark (Tier 2E)
  - build_interpolators → PCHIP / clamped CubicSpline.
  - Re-run V0d post-perf single-anchor benchmark.
  - Target: 18 min → < 5 min per anchor (≈ 4× speedup).

Out-of-scope this round:
  - Numba JIT of RHS (Tier 3F): only worthwhile after Tier 1+2.
  - Full Cython rewrite (Tier 3G): keep as escape hatch.
```

## Reproduction

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
venv/bin/python scripts/v5_round17_perf_profile_single_k.py
# Output: /tmp/v5_round17_profile_single_k.prof + stdout top-30

# Interactive view:
venv/bin/snakeviz /tmp/v5_round17_profile_single_k.prof
# Opens browser at http://127.0.0.1:8080/snakeviz/...
```

---

## Tier 1A v1 attempt (2026-04-28) — REVERTED

The first Tier 1A attempt converted the joint affine operator from
`csc_matrix` to `np.ndarray` at the boundary of
`build_reduced_joint_affine_operator`, eliminating the per-step
`numpy.ndarray.nonzero` scan (21 s of the 111 s baseline) and the
matching scipy.sparse COO/CSR `__init__` calls. The implicit IMEX
solve was dispatched to LAPACK `lu_factor` / `lu_solve` for the
ndarray path while leaving `splu` for genuinely-sparse callers.

**Result: 2× slower (111 s → 229 s).** Re-profile decomposition:

| Metric | Pre-Tier-1A-v1 | Post-Tier-1A-v1 | Δ |
|---|---:|---:|---:|
| Hot-call wall | 111.07 s | **229.55 s** | **+118.5 s** |
| `lu_factor` (LAPACK dgetrf) | n/a | **131.4 s (57 %)** | new dominant |
| `splu` + `solve` (SuperLU) | 5.8 s | gone | −5.8 s |
| `numpy.ndarray.nonzero` | 21.3 s | reduced | savings ~17 s |
| `_compressed.__init__` | 36.8 s | 11.8 s | savings ~25 s |
| `_coo.__init__` | 27.8 s | 5.7 s | savings ~22 s |
| Net sparse savings | — | — | **−69 s** |
| Net dense LU cost | — | — | **+131 s** |
| **Net change** | — | — | **+62 s** |

The 250×250 joint operator is structurally sparse — most entries are
zero except diagonal blocks (free-streaming, Thomson damping) plus a
handful of cross-couplings. `splu` skips the zero entries entirely
and runs in O(nnz) ~ tens of microseconds. `lu_factor` runs full
O(n³) ~ 4 ms regardless. With 32,178 calls per integration, the
factor-1000× per-call gap of `splu` over `lu_factor` overwhelms the
sparse-construction savings.

**Lesson: Sparse splu is not the inefficiency; the dense→sparse
*conversion* boundary at the function return is.** The right Tier 1A
is CSR-pattern caching, not dense conversion.

## Tier 1A v2 plan (CSR-pattern caching) — queued

The sparsity *pattern* of the joint operator is determined by:
- `layout.mode_labels` and `residual_mode_labels` (fixed at integrator init)
- `backend.family_spec.family` (fixed)
- `int(layout.ell_max)` (fixed)
- The structure-from-physics couplings (Thomson cross-couplings to
  baryon-dipole, source-quadrupole — all fixed across η)

The pattern does NOT depend on:
- η (the integration variable)
- The state vector (photon T/E/B, neutrino, baryon, source values)
- `Γ_T`, `H`, `a` background quantities (only multiply existing entries)

So the (rows, cols, indptr) tuple can be built **once** at integrator
init. Per-step build then becomes:
1. Compute the per-step values.
2. Write them into the cached `data` array at the pre-allocated indices.
3. Pass the cached CSR (rows/indptr static; data new) to `splu`.

Estimated savings: eliminate the ~64 s of `_compressed.__init__` +
`_coo.__init__` + `nonzero` per integration. New per-call cost:
~47 s (down from 111 s). **2.4× single-thread speedup.**

Combined with the existing 24-worker parallelism (which only gives
1.7× due to per-task contention), the wall-time projection for a
single-anchor V0d sweep is ~18 min × (47 / 111) = **7.6 min** (down
from 18 min). Full 6-anchor V0d ~46 min (down from 108 min).

**Implementation approach** (next session):
1. Refactor `build_reduced_joint_affine_operator` to expose a "pattern"
   builder + "data filler" pair.
2. Cache the pattern at `ver2_native_integrator.__init__` (one-shot).
3. Per-step caller fills data; constructs CSR via direct buffer write
   (avoids COO→CSR conversion).
4. `splu` continues to factorize the cached-pattern CSR.
5. Validate via existing baseline tests + smoke test (D_2 should be
   bit-equal to pre-cache result).

**Files to refactor**:
- `bass/hierarchy/ver3_layout_protocol.py:build_reduced_joint_affine_operator`
  + helpers (`build_reduced_local_affine_operator`, `build_reduced_harmonic_affine_operator`)
- `bass/hierarchy/ver2_native_integrator.py:_build_residual_joint_affine_operator`
  (caching layer)
- New unit tests pinning pattern stability across η.
