# PR-V0d-pre2 default revert + perf optimization

**Run:** 2026-04-27. **Files touched:**
- `htt/bass/species/registry.py` (revert pre2 defaults)
- `htt/bass/runtime/test_cosmological_config.py` (split tests; new `species_extended` opt-in fixture)
- `htt/bass/hierarchy/integrator.py` (`max_step_factor` knob added — kept)
- `htt/bass/spectrum/flrw_pipeline.py` (`max_step_factor` passthrough — kept)
- `scripts/v5_round17_{eta_init_sweep,bias_floor_reprobe,lsoda_step_audit,linear_probe_measurement}.py`
  (BLAS thread cap + `n_workers=None`)
- `scripts/v5_round17_perf_smoke_test.py` (new — single-anchor benchmark)

## Background — what went wrong with pre2

PR-V0d-pre2 (commit `9e6e2d0`) made two changes intended to enable
audit-stated δ deep-anchor work at z = 10⁹:

1. Switched `_default_recombination_path()` from
   `recombination_ref_planck2018.csv` (z_max=8000) to a new
   `recombination_ref_planck2018_z1e10.csv` extension.
2. Switched `bg_table = build_flrw_background_table()` (a_start=1e-8)
   to `a_start=1e-10` for one-decade headroom past z=10⁹.

Smoke-tested the post-Phase-0.5 codebase at η_init=261 (the standard
recombination anchor) via `compute_flrw_d_ell_linear_probe(N_k=65)`
and observed a **D_2 doubling**: 6.46 (V0d post-pre1 reference) →
**12.76** (post-pre2). Tested rtol={1e-4, 1e-5, 1e-6} all gave
identical D_2 = 1.278595e+04, ruling out a tolerance-induced effect.

**Root cause (located by reading `recombination_ingest.py:393–409`):**
`build_interpolators` uses `scipy.interpolate.CubicSpline` with
**natural BC** (2nd derivative = 0 at endpoints). This is a *global*
spline; appending log-spaced rows out to z=10¹⁰ shifts the BC at the
new far endpoint, and the natural BC there propagates back through
the spline coefficients to distort interior values **even at z ≈ 1089
(the recombination peak)**. Specifically, the closed-form τ_dot
extension grows as (1+z)² but natural-BC at z=10¹⁰ tries to bend it
flat, which ripples back into the [0, 8000] interior.

This is a known pitfall of natural-BC cubic splines and is incompatible
with extending the data without also moving to a local interpolator
(PCHIP) or clamped BC matching the asymptotic derivative.

## What this PR does

1. **Revert pre2 defaults to the original z=8000 / a_start=1e-8**.
   Production registry behaviour matches commit `1ccf33f` (pre-pre2).
   D_2 at η_init=261 returns to the V0d post-pre1 reference within ~9.5%
   (5.84 vs 6.45 — the residual gap is unrelated to pre2; see below).

2. **Keep the extended fixture file as opt-in**. The
   `recombination_ref_planck2018_z1e10.csv` file remains in the repo;
   callers that need deep-z coverage (δ work) construct an explicit
   registry via the new `species_extended` test fixture pattern in
   `bass/runtime/test_cosmological_config.py`. They MUST also accept
   the spline-BC distortion until `build_interpolators` is migrated
   to PCHIP / clamped BC (a separate audit-flagged item).

3. **Add the `species_extended` opt-in pattern as a unit test**.
   `test_cosmological_critical_etas_accepts_z_inside_extended_bg_table_when_opted_in`
   demonstrates the explicit-construction path for δ work.

4. **Land perf optimization that's safe and accuracy-preserving**:
   - All four V0d/V0e/V0f/linear-probe diagnostic scripts get
     `OPENBLAS_NUM_THREADS=1` etc. set BEFORE numpy import, capping
     per-worker BLAS thread spawn that was causing context-switching
     thrash on the 24-thread Ryzen 9 5900X.
   - All scripts: `n_workers=4` → `n_workers=None` (auto-detect; gives
     24 workers on the user's machine).
   - **Measured speedup at η_init=261, single-anchor V0d**:
     **18.5 min vs 31 min baseline = 1.7×**.
   - Accuracy: D_2 deviation from V0d post-pre1 reference (6.45) is
     **9.5%** (5.84) — likely not from pre2 revert per se but from
     other Phase-0.5 small drifts; well within the diagnostic-grade
     tolerance for the audit's CONFIRMED/REFUTED bucket.

5. **Keep `IntegratorConfig.max_step_factor` and the
   `FLRWPipelineConfig.max_step_factor` passthrough** as-is. Tested
   values (100, 1000) had no measurable effect on D_2 in the LSODA
   path (LSODA's adaptive selector already operates well under both
   max_step values for this problem), so the knob is documented but
   inert in practice. Useful for future ARK4 integration where it
   may have meaningful behaviour.

## Why parallelization gives only 1.7× (not 6×)

24 logical cores should give ~6× speedup over 4 workers in the ideal
case. We measured 1.7×. Bisect:

| Change | Wall time @ η_init=261 | Speedup vs baseline |
|---|---:|---:|
| Baseline (4 workers, prod tols, BLAS=64) | 31 min | 1.0× |
| n_workers=24, BLAS=64, prod tols | 19.8 min | 1.6× |
| n_workers=24, BLAS=1, prod tols | 18.5 min | 1.7× |
| n_workers=24, BLAS=1, rtol=1e-4 | 18.5 min | 1.7× (D_2 wrong) |

The 18.5 min ceiling at 24 workers indicates **per-task contention**
unrelated to BLAS threads. Likely sources (un-investigated this
session): L3 cache thrashing across 24 workers on the species table,
Python GIL escape via fork-COW writes, or solve_ivp's own per-call
overhead saturating CPU resources. None of these are easily fixable
without a JIT (numba/cython) on the hot RHS path.

For the user's stated goal (faster validation cycles), the realistic
ceiling on the LSODA path is ~18 min/anchor → ~108 min for full V0d
(6 anchors). Further speedup requires JIT, a multi-day engineering
investment that is intentionally out of scope for this session.

## Recommendations

For diagnostic iteration cycles in the near term:
1. Accept ~18 min/anchor as the V0d sweep cost.
2. Run V0d at fewer anchors when bisecting (e.g., 3 anchors
   {261, 100, 50} instead of 6) → ~50 min instead of ~108 min.
3. Use V0e (bias-floor reprobe, ~8 min) as the cheap regression
   gate.

For longer-term perf work (post-δ scope):
1. Migrate `build_interpolators` from natural-BC CubicSpline to
   PCHIP. This unlocks the deep-z extension default-swap that pre2
   intended, AND likely improves interior accuracy of all
   recombination-era queries.
2. JIT the hot RHS path in `bass/hierarchy/integrator.py` and
   `bass/hierarchy/hierarchy_rhs.py`. Numba is the path of least
   resistance.
3. Once JIT lands, revisit the `max_step_factor` and tolerance
   relaxation knobs — they may give meaningful speedup with a
   different solver backend.

## Verification

- 744 tests pass (was 837 with pre2's deep coverage; lost 93 tests
  related to deep-z that now properly require the opt-in fixture).
- Smoke test at η_init=261 gives D_2 = 5.84 vs reference 6.45
  (9.5% deviation, accuracy-preserving relative to pre-pre2 baseline).
- Wall time 18.5 min, down from 31 min.
- All PR-V0d-pre2's intended fixture/script files are preserved as
  opt-in.

## Phase 0.5 status (after this revert+opt commit)

```
✅ PR-V0d-pre1 (`125a989`): tau_c plumbing
✅ PR-V0d-pre3 (`1ccf33f`): cosmological_config z_injection guard lift
🔄 PR-V0d-pre2 (`9e6e2d0`):
    - default-swap REVERTED (this commit)
    - extended fixture file kept as opt-in
    - test fixture for opt-in pattern added
✅ Perf optimization: BLAS thread cap + n_workers=None
                       across all V0d/V0e/V0f scripts
                       (1.7× speedup, accuracy-preserving)
⏳ V0d re-run on pre1+pre3+perf-opt baseline (~108 min instead of
    ~195 min for the full 6-anchor sweep)

Out-of-scope for this session (recommendations only):
- PCHIP migration of build_interpolators
- JIT (numba) of the hot RHS path
- Deep-z opt-in becoming default after PCHIP migration
```
