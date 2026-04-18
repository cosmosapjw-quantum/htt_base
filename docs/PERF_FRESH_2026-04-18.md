# BASS Performance — Fresh Analysis (2026-04-18)

> Re-analysis performed from scratch, **ignoring legacy PERF_NOTES.md**.
> All numbers below are from `perf record` / `hyperfine` on the live codebase.
> Machine: AMD Ryzen 9 5900X (24T / 12C), 64 GB RAM, Ubuntu 24.04, rustc 1.94.1.

---

## §1. Baseline measurements

### 1.1 Two workloads

| Config | ell_max | n_k | ell_max_γ / ν | n_vis | SourceMode | Wall (median of N) |
|---|---|---|---|---|---|---|
| `fast_validation` | 30 | 30 | 15 / 8 | 1500 | SwOnly | **5.129 ± 0.135 s** (5 runs) |
| `default_track_a` | 2500 | 100 | 25 / 15 | 5000 | Full | **11.119 ± 0.358 s** (3 runs) |

Both are parallel over k-modes via rayon. Observed parallelism on this machine:
- fast_val: user/wall = 53.3 / 5.1 = **10.5×**
- prod:     user/wall = 178.6 / 11.1 = **16.1×** (near the 24T limit)

### 1.2 Phase timer attribution (printed by pipeline)

```
[fast_val]  PROFILE: vis=19.4ms kgrid=0.0ms ksolve=4983.3ms bessel=34.7ms
            (0.4%)            (0.0%)      (91.1%)          (0.6%)

[prod]      PROFILE: vis=19.4ms kgrid=0.0ms ksolve=10063.9ms bessel=698.7ms
            (0.2%)            (0.0%)      (93.3%)           (6.5%)
```

**ksolve (ODE integration over k-grid) dominates at 91–93%** in both workloads.

### 1.3 Memory

`maxRSS` during production run: **5.2 GB**. This is a concern for low-spec
targets with limited RAM — per-k-mode history arrays are the culprit
(100 k-modes × full ODE trajectory).

---

## §2. Function-level CPU attribution (`perf record -F 497`, prod run)

| Rank | Function | Self % | File:line |
|---|---|---|---|
| 1 | `lu_solve_factored_flat_into` | **26.3** | [core/lu.rs:133](src/core/lu.rs#L133) |
| 2 | `linear_profile_rhs_only_into` | **23.0** | [solver/rodas5p.rs:103](src/solver/rodas5p.rs#L103) |
| 3 | `step_linear_profile_rodas5p_into` | **20.1** | [solver/rodas5p.rs:237](src/solver/rodas5p.rs#L237) |
| 4 | `lu_factor_in_place_flat_into` | **17.7** | [core/lu.rs:62](src/core/lu.rs#L62) |
| 5 | `linear_profile_rhs_jac_flat_into` | **5.8** | [solver/rodas5p.rs:123](src/solver/rodas5p.rs#L123) |
| 6 | `memmove` (libc) | 1.7 | — |
| 7 | `memset` (libc) | 0.7 | — |
| **Σ** | **(top 7 ≈ 95%)** | | |

Fast_validation shows the same distribution (LU solve 30.0%, RHS 22.5%, step 21.1%, LU factor 15.1%). **Bottleneck structure is workload-independent.**

### 2.1 The legacy doc's "Bessel 57.7%" claim is wrong

Legacy [PERF_NOTES.md](PERF_NOTES.md) claims LoS_Bessel is the dominant cost.
This is not true for either `flrw_cl_pipeline` workload. Bessel is 0.6% at fast
scale and 6.5% at production scale. Either the legacy measurement used a
different code path (e.g. the Python-facing `solve_stacked_native_rodas5p` direct
call, without LoS), or the code has since evolved past that bottleneck.

**Trust these numbers, not the legacy doc.**

---

## §3. Flops-per-second sanity check

Rough estimate for the production run:
- d ≈ 50–70 (state dim), ~500 Rodas5P steps per k-mode, 100 k-modes
- Per step: 1× LU factor (d³/3 ≈ 50 kflop) + 8× LU solve (2d² ≈ 7 kflop each = 56 kflop) + 9× matvec (2d² ≈ 7 kflop each = 63 kflop) ≈ **170 kflop/step**
- Total: 100 × 500 × 170 k ≈ **8.5 Gflop**
- Wall (single core equivalent): 178 s → **~48 MFlop/s per core**

AVX2 FMA on Zen3 ceiling for f64 is **≈ 25 GFlop/s/core**. We are at **~0.2%
of peak**. The code is **overwhelmingly memory-bound or instruction-bound**,
not flop-bound. This means:

- There is huge headroom for micro-optimization
- The biggest wins will come from **reducing memory traffic** (cache blocking,
  avoiding redundant matrix materialization) and **eliminating control overhead**
  (unrolling small LU, removing per-stage re-sampling)
- Adding more arithmetic (e.g. higher-order stepper) is essentially free
  compared to memory access

---

## §4. Target & gap analysis

User's target: **10–15 s single-run on low-spec hardware**. Reference:
CAMB ≈ 5 s, CLASS ≈ 7 s.

Current on this machine (Ryzen 9 5900X, 24T): **11.1 s**. But we are getting
~16× parallelism. On a **4-core / 8-thread** low-spec: estimated ~**25 s**.
On an **8-core / 16-thread** low-spec: estimated ~**14 s**.

**Gap to close**: ~2× on 4-core class, ~1.1× on 8-core class. Plus memory
(5.2 GB RSS is too high for 8 GB laptops when combined with OS + Python).

---

## §5. Optimization plan — measurement-driven

Each step must preserve the D_2 = 1002.086744 μK² regression guard
bit-identically. Ordering is by **(expected impact) × (reverse of risk)**.

### Phase 0 — Build profile tuning (ZERO code change)

**§5.0.1** Add `[profile.release]` to Cargo.toml: `lto = "fat"`,
`codegen-units = 1`, `panic = "abort"`, `debug = "line-tables-only"`.
**Status**: applied; impact measured below in §6.

**§5.0.2** Skip `target-cpu=native` by default. Legacy doc reported regression
and we can't validate on low-spec silicon from this machine. Defer to
per-deployment `.cargo/config.toml` overlay.

**Expected gain**: 5–15%. Bit-identical (LTO reorders but does not alter math).

### Phase 1 — Structural wins in the Rodas5P inner loop

Target: **rodas5p.rs self-time 42% (RHS matvec + step logic + RHS+Jac)**.

**§5.1.1 Stage-level matrix reconstruction via Taylor**
`linear_profile_rhs_only_into` calls `sample_matrix_only_into_hint` 8 times
per Rodas5P step ([solver/rodas5p.rs:107](src/solver/rodas5p.rs#L107) inside the
8-stage loop). But we already have both `a_buf` and `da_buf` from the
combined `sample_into_hint` call at step start ([solver/rodas5p.rs:127](src/solver/rodas5p.rs#L127)). Within a step, the matrix is linear in τ by construction (the
profile is linearly interpolated between adjacent η samples). So
`a_stage = a_buf + Δτ · da_buf` computes the same value without re-doing the
binary search + bracket interpolation.

**Caveat**: boundary case when a stage's η crosses a sample interval.
Handle by detecting and falling back to full re-sample for those steps.

**Expected gain**: 8× → 1× sampling per step. Roughly **−8 to −12% wall**.
Bit-identical within interior intervals; requires boundary guard to preserve
identicity at sample crossings.

**§5.1.2 Fused `W = I/(γh) − J` with Jacobian output**
[solver/rodas5p.rs:242-248](src/solver/rodas5p.rs#L242-L248) loops over `d×d`
copying `-J` into `W` then adds `1/(γh)` on the diagonal. The Jacobian is
already written into `scratch.j0` by `linear_profile_rhs_jac_flat_into`. We
can have the RHS function write negated Jacobian directly, or fuse the
assembly into the same loop that fills `j0`. Saves one full `d²` pass plus
cache miss of `j0`.

**Expected gain**: 3–5% wall. Bit-identical.

**§5.1.3 Pre-allocate LoS scratch**
[solver/flrw_cl_pipeline.rs:282-284](src/solver/flrw_cl_pipeline.rs#L282-L284)
allocates `delta_ell` and `jl_buf` on every k-mode iteration. Move outside
the loop or reuse via a `Vec<ScratchLoS>` indexed by thread.

**Expected gain**: 0.5–1% wall on production. Bit-identical.

### Phase 2 — LU kernel specialization

Target: **44% (lu_solve 26% + lu_factor 18%)**.

**§5.2.1 Const-generic small-d LU** (d ≤ 64)
For d in this range, full loop unrolling and fixed-size SIMD give large wins
vs generic d LU. Options in decreasing preference:

1. `nalgebra` fixed-size `MatrixN<f64, Const<D>>` — already a crate dep.
   Its LU uses stack allocation and inline unrolling.
2. `faer` — newer, explicitly tuned for small-d LU with AVX2 microkernels.
   Would require adding a dep.
3. Hand-written `lu_factor_small<const D: usize>` — most work, least gain.

**Caveat**: FMA reordering may shift rounding by ULPs. Bit-identicity check
needs FP-strict mode or a separate test with a tolerance. If bit-identical is
required, we'd need to match the exact arithmetic pattern of the current
iter/zip LU, which mostly negates the SIMD win.

**Expected gain**: 10–25% wall. **Bit-identicity risk — must gate on test**.

**§5.2.2 Avoid redundant `is_finite` + `abs()` in pivot search hot loop**
[core/lu.rs:77](src/core/lu.rs#L77) checks `is_finite` on `piv_abs` but only
once per column. Low impact — mostly confirms this is not the issue.

### Phase 3 — Memory pressure reduction

Target: **maxRSS 5.2 GB** (blocks parallel use on RAM-limited hardware).

**§5.3.1 Streaming k-mode history**
Per-k-mode history arrays are retained in memory until all k-modes finish
before LoS aggregation starts. Instead, feed each k-mode's source grid into
the Bessel accumulator as soon as it's available, and drop the full history.
Concretely: restructure so each worker computes `delta_ell` for its k-mode
and only returns `delta_ell` (sized `ell_limber+1`) rather than the full
`eta_grid + source` (sized `n_vis ≈ 5000`).

**Expected gain**: ~60–70% RSS reduction (5.2 GB → ~1.5 GB). Wall
change: 0 to slightly positive (better cache behavior).

### Phase 4 — Parallel determinism & scaling

**§5.4.1 Reduction order is already deterministic**
Checked: `par_iter().collect::<Vec<_>>()` preserves source order,
and the C_ℓ accumulation loop iterates `ik in 0..n_k` sequentially. Bit-identical
under rayon. ✓ No action needed.

**§5.4.2 Thread-local scratch via `rayon::iter::map_init`**
Replace per-closure fresh allocations with `map_init(ScratchLoS::new, |s, k| …)`.
Net: fewer allocations under parallel, warmer caches.

**Expected gain**: 1–3% wall on many-core; memory halved.

### Phase 5 — PGO (last, once structural changes settle)

`cargo-pgo` is installed. Workflow: instrument → run representative workload →
re-compile with profile data. Typical wins: 5–15% for branch-heavy code.

Do this **last** because PGO data becomes stale as soon as code changes.

**Expected gain**: 5–15% wall. Bit-identical (no math change).

---

## §6. Measured impact log

Record actual wallclock after each change. Format: `(mean ± σ, n runs)`.

| Step | fast_val | prod | Note |
|---|---|---|---|
| Baseline (default release) | 5.129 ± 0.135 s (5) | 11.119 ± 0.358 s (3) | commit HEAD |
| LTO=fat + cgu=1            | 5.363 ± 0.074 s (5) | _n/a_ | **+4.6% regression** (i-cache pressure) |
| LTO=thin, cgu=16           | 5.204 ± 0.186 s (5) | 10.554 ± 0.755 s (3) | fast: within noise; prod: **−5.1%** (borderline) |
| Phase 1.1 fused matvec     | _n/a_ | 11.256 ± 0.559 s (5) | **REVERTED** — A/B vs fallback Δ=0.3σ, no gain |
| Phase 1.1 reverted (HEAD)  | _n/a_ | 10.735 ± 0.310 s (5) | back to thin-LTO baseline, bit-identical confirmed |
| Phase 1.2 (fused W)        | — | — | |
| Phase 1.3 (LoS scratch)    | — | — | |
| Phase 2.1 (small-d LU)     | — | — | |
| Phase 3.1 (streaming hist) | — | — | RSS also tracked |
| Phase 5   (PGO)            | — | — | final step |

**Phase 0 conclusion**: Keep `lto = "thin"` in Cargo.toml. Compile time goes
32s → 42s (+10s), prod wallclock improves ~5% (within noise — needs more
runs to confirm). Do **NOT** use `lto = "fat"` + `codegen-units = 1`; regresses
fast_val by measurable 4.6%. The bulk of wins must come from Phase 1–3.

### Phase 1.1 result — NEGATIVE (reverted)

Implemented as designed: fused interp+matvec for stages within the step-start
bracket, preserving the exact `v0 + w*(v1-v0)` arithmetic for bit-identicity.

**Bit-identicity gate passed** — all 9 reference D_ℓ values (5 at fast_val +
4 at prod) matched to hex precision. Measurement infrastructure is in
[src/solver/flrw_cl_pipeline.rs](src/solver/flrw_cl_pipeline.rs) (bitref_fast_val_d2
and `BITREF <hex>` output in perf_probe).

**Diagnostic counter** showed 96.8% fast-path hit rate at prod scale (only
3.2% bracket crossings). So the path was actually exercised.

**But wallclock A/B (same binary, BASS_P11_OFF toggle)**:

| Path | prod wall (n=5) |
|---|---|
| Fused ON  | 11.256 ± 0.559 s |
| Fused OFF | 11.162 ± 0.358 s |
| **Δ**     | **+0.094 s, within noise (Δ/SE = 0.3σ)** |

**Root cause of the null result**:

1. `mats_flat` at prod scale = 5.76 MB (L3-resident, not L1).
2. Two-pass form reads base0 then base1 in **separate linear sweeps** —
   hardware prefetcher handles this perfectly.
3. Fused form reads base0+k and base1+k alternately (offset by n_state²)
   on every inner iteration — prefetcher less effective for interleaved streams.
4. The saved `a_buf` materialization writes+reads are L1-local; near-free.
5. Net: fused has same total memory traffic but worse access pattern.

**Hypothesis that was wrong**: "eliminating a_buf saves 50% of sample+matvec
memory traffic → visible wallclock gain." The 50% traffic reduction is
accurate in an L1-disconnected model, but in practice base0/base1 are L3-
resident so the real savings are in the L1 transfer layer which was already
cheap.

**Action**: reverted all Phase 1.1 code ([src/solver/rodas5p.rs](src/solver/rodas5p.rs)
back to pre-change). Retained the bitref tests — they're reusable for any
future phase.

**Lesson for future phases**: the bottleneck is not "redundant memory
materialization." Likely it's the LU kernels (44% combined) or the intrinsic
matvec+LU flop count. Phase 1.2 (fused W assembly) is likely to be similarly
null since j0 is also L1-resident. Skipping straight to **Phase 2 (LU
specialization)** or **Phase 3 (memory-focused — streaming history)** may
have better return.

---

## §7. Validation protocol

Every step must pass this gate before the next one begins:

1. `cargo test --lib --release solver::flrw_cl_pipeline::tests::test_cl04a_ -- --nocapture`
   (6 tests must remain green; 1 known-failing `test_cl04a_diagnostic_d2` is
   physics-not-perf and pre-existing)
2. `cargo test --lib --release solver::sync_gauge_camb::dump_dl_spectrum_sparse -- --ignored --nocapture`
   must emit `D_2 = 1002.086744 μK²` bit-identically
3. `hyperfine --warmup 1 --runs 5 "<test_bin> fast_validation"` — regression
   check, must not increase
4. `hyperfine --warmup 1 --runs 3 "<test_bin> perf_probe_default_track_a"`
   — same for prod

---

## §8. Things NOT to do (anti-plan)

Based on what the data says, these paths are **not worth pursuing**:

- **Bessel microopt** — only 0.6–6.5% of wall. Chasing it is a waste.
- **BLAS link** — already tried (`feature = "blas"`), confirmed killed for d<100.
- **Replacing Rodas5P with BDF** — Rodas5P is already L-stable and appropriate.
  Stiffness handling isn't the bottleneck.
- **target-cpu=native in the default profile** — regresses due to i-cache.
  Good as an opt-in for deployment, not default.
- **`unsafe get_unchecked` spraying** — 2–5% estimated, high risk of UB, low
  reward relative to the structural wins above.
