# Tier 3 — Numba JIT preparation (Phase B perf)

**Date:** 2026-04-28. **Profile baseline:** post-Tier-2D single-k cProfile,
total 76.0 s wall (down from 111 s pre-perf).

This document is the **preparation** deliverable for Tier 3
(JIT compilation of hot pure-numerical paths). Full implementation is
multi-day work; this prep:

1. Surveys the post-2D single-k profile to identify JIT candidates.
2. Assesses each candidate's feasibility (pure-numerical vs
   Python-state-coupled).
3. Provides expected gain estimates.
4. Records a numba toolchain POC that validates the install + workflow.
5. Lays out an implementation roadmap.

## Toolchain installation

Both numba and cython are now in the venv:

```
numba 0.65.1
llvmlite 0.47.0   (numba's LLVM backend)
cython 3.2.4
```

Numba is preferred for hot-path JIT because:
- No separate compile step (JIT at first call, cached on disk).
- Decorator-based: ``@njit`` annotates a Python function in place, the
  source stays readable. Preserves the "transparent baseline" goal.
- Integrates with NumPy seamlessly; supports ndarrays + scalars + tuples.

Cython is a fallback for cases numba can't handle (typed memoryviews,
custom C extensions, etc.).

## Top self-time functions (post-Tier-2D, 76 s baseline)

```
ncalls    tottime  cumtime  function
─────────────────────────────────────────────────────────────────────
16069     7.033    25.842   build_reduced_joint_affine_operator (ver3)
64269     4.765     4.765   scipy.sparse.linalg._dsolve._superlu.gstrf
1072871   4.220     4.220   numpy.zeros
16069     3.708     8.409   build_reduced_harmonic_affine_operator
128536    2.570     3.101   hierarchy_rhs_photon_from_state
417803    2.317     3.802   scipy.sparse._sputils.get_index_dtype
1371869   2.249     2.249   numpy.ufunc.reduce (mostly inside scipy.sparse)
449876    2.086     4.675   _unpack_hierarchy_view
15839344  1.752     1.752   numpy.asarray
16132     1.602     1.602   ndarray.fill (Tier 2D's workspace-zero call)
4048884   1.342     2.040   _make_pstf_tensor_view
112494    1.309     3.516   _operator_scales
1         1.153    74.677   _solve_segment_imex (driver, 1 call)
289231    1.112    13.101   scipy.sparse._compressed.__init__
16067     1.089     6.629   _orthogonal_implicit_step
64269     1.022     1.022   SuperLU.solve
112469    0.797     5.768   _unpack_radiation_state
369578    0.766     1.798   scipy.sparse._compressed.prune
304478    0.753     0.776   pstf_tensor.as_flat
899875    0.685     0.685   numpy.getlimits.__init__
```

## JIT feasibility assessment

| Function | Self time | Calls | JIT feasibility | Why |
|---|---:|---:|:---:|---|
| `build_reduced_joint_affine_operator` | 7.0 s | 16k | 🟡 partial | Top-level has Mapping access, dict lookups, dataclass attribute access — not direct `@njit`. **Inner numerical loops** can be extracted into a separate `@njit` helper. |
| `gstrf` (SuperLU) | 4.8 s | 64k | ❌ no | Already a C extension. Cannot JIT around it; only avoidable by switching to dense LU (Tier 1A v1 was 2× slower) or precomputed factor caching. |
| `numpy.zeros` | 4.2 s | 1.07M | ❌ no | System-level allocator. Tier 2D already addressed the largest joint-level allocation. Remaining 4.2 s is many small allocations across builders. |
| `build_reduced_harmonic_affine_operator` | 3.7 s | 16k | 🟡 partial | Same shape as joint: top-level Python orchestration is hard to JIT, but the inner harmonic-coupling fill loops are clean numerical. |
| `hierarchy_rhs_photon_from_state` | 2.6 s | 128k | 🟡 partial | Takes `PSTFHierarchyState`, `ClosureStrategy`, `CollisionOperator` — all custom Python objects. **Refactor to ndarray-only inner helper** to JIT. |
| `_make_pstf_tensor_view` | 1.3 s | 4M | 🟢 good | Pure ndarray operation; high call frequency makes per-call dispatch overhead the dominant cost. Excellent JIT target. |
| `_operator_scales` | 1.3 s | 112k | 🟢 good | Returns a dict of scalars from a Mapping — refactor to return tuple/ndarray, JIT-able. |
| `_unpack_hierarchy_view` | 2.1 s | 450k | 🟢 good | View extraction; ndarray-in, ndarray-out. JIT-able. |
| `_orthogonal_implicit_step` | 1.1 s | 16k | 🔴 hard | Calls scipy.sparse + Python control flow. Limited JIT scope. |

**Realistic Tier 3 targets** (in implementation priority):

1. **`_make_pstf_tensor_view`** + **`_unpack_hierarchy_view`** + **`_unpack_radiation_state`**: 5 s combined self time across 5M calls. JIT removes the Python dispatch overhead per call. Estimated 4-5× per-call speedup → save ~3-4 s.

2. **`_operator_scales`**: 1.3 s. Refactor to return a frozen `np.ndarray` of scalars (or a NamedTuple) instead of a dict. JIT the value-computation loop. Estimated save ~1 s.

3. **Inner Thomson-coupling fill loop in `build_reduced_joint_affine_operator`**: extract lines 2419-2515 into a `@njit` helper that takes structural arrays (residual_count, gamma_t, scales, ...) and writes to a pre-allocated joint dense ndarray. Estimated save ~3-4 s of the 7 s self time.

4. **`hierarchy_rhs_photon_from_state` inner numerical core**: refactor to take ndarray inputs only (extract the dataclass unpacking outside). The inner ℓ-loop is pure tensor algebra. Estimated save ~1.5 s.

**Total realistic Tier 3 gain**: ~9-12 s of the 76 s baseline → 64-67 s
single-k. **+13-15 % wall improvement**, ~1.15× additional speedup.
Combined with prior tiers: 31 min original / (76 / 12.7) = ~2.6×
total. Smoke V0d projection: ~12 min single-anchor / ~70 min full sweep.

## POC: numba toolchain validation

A minimal POC verifies the install works and produces bit-identical
output. Test function: a small ndarray operation representative of the
inner fill loops we'd JIT.

```python
# scripts/v5_round17_perf_numba_poc.py (this file)
import numpy as np
from numba import njit

@njit(cache=True)
def thomson_diagonal_damping(
    inv_source: np.ndarray,
    coeff: float,
) -> np.ndarray:
    """numpy-equivalent: inv_source * coeff (then used as -np.diag(...))."""
    n = inv_source.shape[0]
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        out[i] = inv_source[i] * coeff
    return out

# Validation: numba == pure-numpy bit-equal across 1000 random inputs
rng = np.random.default_rng(42)
for _ in range(1000):
    inv = rng.standard_normal(8)
    c = float(rng.standard_normal())
    np_result = inv * c
    nb_result = thomson_diagonal_damping(inv, c)
    assert np.array_equal(np_result, nb_result)
```

Expected output:
- First call: ~200 ms compile time (cached)
- Subsequent calls: < 1 µs / element

The POC is intentionally trivial. The point is to verify the venv,
LLVM linker, and AOT cache infrastructure all work end-to-end before
investing in larger refactors.

## Implementation roadmap (multi-day, post-prep)

**Day 1 — extraction**:
- Refactor `_make_pstf_tensor_view`, `_unpack_hierarchy_view`,
  `_unpack_radiation_state` to take ndarray-only inputs and return
  ndarrays. Verify bit-equality against the current dataclass-based
  versions.
- Add `@njit(cache=True)` decorators.

**Day 2 — operator scales**:
- Refactor `_operator_scales` to return a NamedTuple or struct-of-arrays
  instead of a dict.
- JIT the scalar-computation block.

**Day 3 — joint inner-fill loop**:
- Extract the Thomson coupling fill (lines 2407-2515 of ver3) into a
  helper function `_fill_joint_thomson_couplings(joint, ..., gamma_t,
  ...)` that takes structural arrays.
- JIT it. Verify bit-equality with the current dense-fill code.

**Day 4 — hierarchy RHS**:
- Same approach for `hierarchy_rhs_photon_from_state`. Extract the
  inner ℓ-loop into a JIT helper that takes flat ndarrays.

**Day 5 — validation + bench**:
- Run V0e (bias-floor reprobe at b_k_sq=0) for D_2 = 0 verification.
- Run V0d single-anchor smoke and verify D_2 = 5.85 bit-identical to
  the post-Tier-2D baseline.
- Update CHANGELOG with measured speedups.

## What this prep deliverable provides

- **Confirmed**: numba 0.65.1 + llvmlite 0.47.0 installed and importable.
- **Documented**: top-20 self-time functions + JIT feasibility assessment.
- **Identified**: 4 priority targets for Tier 3 implementation.
- **Estimated**: 9-12 s additional speedup (~15 % wall) realistic from
  full Tier 3 implementation.
- **POC script**: `scripts/v5_round17_perf_numba_poc.py` verifies the
  toolchain works end-to-end.

The user's strategic argument ("multi-day investment now saves
multi-week downstream") still holds: Tier 3 implementation
(~5 days) buys a 1.15× additional speedup, bringing cumulative
~2.6× over the 4-worker baseline. For δ work that may issue dozens of
V0d-class measurements, this is meaningful.

For the next session, the implementation roadmap above is ready to
follow. The key prerequisite — toolchain available + targets
identified — is now satisfied.
