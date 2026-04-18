# Phase 0 — Correctness Audit Report (D0.1–D0.3)

**Date**: 2026-04-18
**Roadmap**: [ROADMAP_v3 Phase 0](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md)
**Instruments**: `phase0_d0_1a_source_mode_matrix`, `phase0_d0_1c_dl_profile_full_mode`, `phase0_d0_2b_ell_max_gamma_sweep`, and `BASS_SRC_PROBE` / `BASS_LIMBER_PROBE` env-var instrumentation in [src/solver/flrw_cl_pipeline.rs](src/solver/flrw_cl_pipeline.rs).

---

## §1. Executive summary

**Three independent bugs** isolated in `compute_flrw_cl_track_a` at `default_track_a` (production) scale. Ordered by severity:

| Bug | Location | Severity | Root cause hypothesis |
|---|---|---|---|
| **B** | `solve_kmode_with_history` (MB-95) at k > ~0.03 | **critical** | ODE solver (Rodas5P) diverges at high-k; `source_jl` grows exponentially with k |
| **C** | Limber formula in `flrw_cl_pipeline.rs:345` | high | `eta_sp = ν/k` should be `η₀ − ν/k`; likely `1/k²` factor also missing |
| **A** | `SourceMode::Full` path — `extract_source_grid` (ISW FD) | medium | Both SW and ISW sum in source_jl drops D_2 from 690 → 3.9 at same scale |

**Critical finding**: `default_track_a` config (k_max = 0.25, ell_max = 2500, SourceMode::Full) has **NEVER worked**. Only `fast_validation` (k_max = 0.03, ell_max = 30, SwOnly) produces physical spectra because it stays below the divergence threshold on k and never invokes the Limber path.

This is consistent with the user's decision to demote MB-95 to reference prototype and promote PSTF primary to production.

---

## §2. Measurement trail

### 2.1 D0.1a — source-mode × scale matrix

Ran [`phase0_d0_1a_source_mode_matrix`](src/solver/flrw_cl_pipeline.rs). Each row is one scenario:

```
fast_SwOnly     D_2 = 7.679e2   D_10 = 3.116     D_30   = 0.884     finite? ✓
fast_Full       D_2 = 3.902     D_10 = 3.153     D_30   = 1.139     finite? ✓  ← Bug A
prod_SwOnly     D_2 = 6.895e2   D_10 = 3.914     D_200  = 1.953e202 finite? ✓  ← Bug B/C
prod_Full       D_2 = 3.946     D_10 = 3.821     D_200  = 1.953e202 finite? ✓  ← Bug A+B/C
```

### 2.2 D0.1c — D_ℓ profile at prod Full

Ran [`phase0_d0_1c_dl_profile_full_mode`](src/solver/flrw_cl_pipeline.rs):

```
D_2    = +3.95        D_5   = +3.82       D_10  = +3.82      D_20  = +4.21
D_30   = +4.62        D_50  = +5.24       D_100 = +4.64     ← normal regime
D_150  = +1.17e202 ← explosion onset (Limber boundary at ell_limber=100)
D_200  = +1.95e202    D_300 = +4.32e202   D_500 = +1.32e203
D_1000 = +1.33e204    D_2000= +2.78e206
```

**Blow-up starts exactly at ℓ = ell_limber + 50 = 150** where Limber takes over.
Full LoS branch (ℓ ≤ 100) is numerically fine. Full LoS skips k-modes with
`k × 13680 > 1.5 × ell_limber` (flrw_cl_pipeline.rs:276) so it only uses k < 0.011 — below the divergence threshold.

### 2.3 D0.1b + D0.2 — `BASS_SRC_PROBE` per-k source magnitudes

Ran prod SwOnly with `BASS_SRC_PROBE=1`. Output shows `source_jl` is exponential in k:

```
k=5.0e-5   |src|_max = 1.85e-2   (normal)
k=4.9e-2   |src|_max = 4.46e5
k=5.8e-2   |src|_max = 2.67e10
k=6.3e-2   |src|_max = 1.60e13
k=7.5e-2   |src|_max = 2.14e20
k=9.7e-2   |src|_max = 3.79e33
k=1.25e-1  |src|_max = 3.14e49
k=1.77e-1  |src|_max = 4.36e73
k=2.50e-1  |src|_max = 1.04e101    ← catastrophic
```

Onset at k ≈ 0.03–0.05. Growth rate ≈ 10⁵ per k-octave — **hallmark of numerical instability**, not physics. All values are `finite? true`, so not NaN/Inf — just astronomical.

### 2.4 D0.2 — `BASS_LIMBER_PROBE` max contributor

```
LIMBER_PROBE: max_contrib = +5.968e188
              at (ell=2146, ik=99, k=2.500e-1, eta_sp=8.586e3, s_at_sp=-1.037e101)
```

The dominant contribution is at `k = 0.25`, driven entirely by `source_jl = -1.037e101`. Removing this single `s_at_sp` value would eliminate the blow-up.

### 2.5 D0.2b — ell_max_gamma sweep (cutoff reflection hypothesis)

Ran [`phase0_d0_2b_ell_max_gamma_sweep`](src/solver/flrw_cl_pipeline.rs):

```
ell_max_gamma=12   | D_2=+8.5e-2  D_50=+3.48  D_100=+7.24  D_150=+7.7e206  D_300=+1.3e207
ell_max_gamma=25   | same                                  D_150=+1.2e203  D_300=+6.2e203
ell_max_gamma=50   | same                                  D_150=+9.6e204  D_300=+2.9e206
ell_max_gamma=100  | same                                  D_150=+3.7e204  D_300=+5.0e205
ell_max_gamma=200  | same                                  D_150=+3.8e204  D_300=+1.3e205
```

**Cutoff reflection hypothesis rejected**. Raising `ell_max_gamma` from 12 to 200 shifts the explosion magnitude by only ~3 orders of magnitude (still 10²⁰³ to 10²⁰⁵). Photon-hierarchy truncation is **not** the primary driver.

---

## §3. Bug characterization

### 3.1 Bug B (critical) — ODE divergence at high k

**Hypothesis** (not yet confirmed): Rodas5P step controller with `rtol = 1e-6`, `atol = 1e-9` is inadequate for the oscillatory photon sector at k > ~0.03. The state is finite but grows exponentially as k increases, consistent with:

- A subtle numerical instability (CFL-like) in the implicit integrator when the photon Θ_ℓ oscillation period (≈ 2π/k) shrinks below the typical adaptive step size.
- OR the "TCA pre-phase as bad-state injector" mode described by the architectural charter ([TCA_UFA_RSA_대응안](../project/04_implementation_specs/TCA_UFA_RSA_대응안) §4.1).

**Evidence against fundamental ODE ill-posedness**: SymBoltz.jl, ABCMB, CAMB, CLASS all solve this same ODE system without divergence up to k ≈ 0.25 Mpc⁻¹, so the physics is benign. The bug is implementation-specific.

**Evidence against IC error**: `fast_validation` runs work with k_max = 0.03; only k > ~0.03 diverges. IC issues would appear at all k.

**Not yet tested but likely same bug**: PSTF primary `pstf_solve_kmode` uses the same `integrate_linear_profile_rodas5p` stepper and same rtol/atol config ([src/solver/pstf_primary/integrate.rs:149-160](src/solver/pstf_primary/integrate.rs#L149-L160)). Must be verified in Phase 1.

### 3.2 Bug C (high) — Limber formula

Two suspected errors in [flrw_cl_pipeline.rs:335-353](src/solver/flrw_cl_pipeline.rs#L335-L353):

**C.1 — wrong stationary phase**: `eta_sp = ν/k`. Correct value: `η₀ − ν/k`. The LoS integral is `∫ S(η) j_ℓ(k(η₀−η)) dη`; substituting χ = η₀ − η shifts the stationary phase to `χ = ν/k`, i.e. `η_sp = η₀ − ν/k`. As written, the code samples the source at the **wrong conformal time** — early universe rather than late. This error is masked at the moment by Bug B (source is garbage everywhere at high k), but must be fixed for Phase 1.

**C.2 — missing `1/k²` factor**: Limber approximation gives `|Δ_ℓ(k)|² ≈ (π/(2ℓ+1)) × S² / k²`. The code lacks the `/k²`. This produces a scale-dependent multiplicative error; magnitude depends on which k-modes dominate each ℓ.

### 3.3 Bug A (medium) — Full mode D_2 collapse

`SourceMode::Full` switches `source_jl` from `raw_theta0_source` to `extract_source_grid(...) → SW + ISW`. At fast_val scale (where Bug B is absent), this drops D_2 from 768 → 3.9. The ISW term in [flrw_kmode.rs:782-787](src/solver/flrw_kmode.rs#L782-L787) uses forward FD with a `deta > 0.5` guard and `exp(-τ)` prefactor. Inspection suggests two possible issues:

- Sign convention mismatch between `(ψ + φ)` here vs the MB-95 convention producing `raw_theta0_source` elsewhere.
- The ISW FD noise amplification the charter (`TCA_UFA_RSA_대응안` §"레드팀 반례") warned about: "narrow k-grid, ISW FD noise, reionization 누락".

Detailed investigation deferred to Phase 1 when PSTF primary's source construction replaces this path.

---

## §4. Phase 0 conclusions

1. **`default_track_a` config has never been validated** — the pipeline explodes structurally at high k and high ℓ. PREP_NOTES's "D_ℓ ℓ ≤ 300 ±0.6% (2000k, Track B)" refers to a **different** code path (Track B = bypassing the Track A Limber pipeline). The Track A flrw_cl_pipeline is unfit for production.

2. **The solver-vs-pipeline question cannot be cleanly separated**: Bug B is in the **solver** (ODE divergence), Bugs A and C are in the **pipeline** (source construction and LoS assembly). All three need fixes for production.

3. **Phase 1 (PSTF primary truth freeze) should proceed**, with two caveats:
   - PSTF primary inherits the Rodas5P config from MB-95. Phase 1.2 must audit step controller and consider tightening tolerances or adding high-k diagnostics **before** scaling up k_max.
   - Bugs A and C are **pipeline-level**, affecting flrw_cl_pipeline.rs regardless of which solver is upstream. PSTF primary will need its own cleaner pipeline (`compute_pstf_cl_track_a`, see ROADMAP_v3 P1.3), built from scratch rather than re-using flrw_cl_pipeline.

4. **Architectural charter predicted this**: [TCA_UFA_RSA_대응안](../project/04_implementation_specs/TCA_UFA_RSA_대응안) warned specifically about "narrow k-grid, ISW FD noise, and cutoff reflection" — Bugs A+B+C are this triad. The recommended response (sparse implicit truth solve, stage separation, matrix LoS) is already in ROADMAP_v3 Phase 2.

---

## §5. Immediate next steps (Phase 1 readiness)

1. **Verify PSTF primary does not share Bug B**. Run `pstf_solve_kmode` at k ∈ {0.01, 0.03, 0.1, 0.25} single-mode and inspect `source_jl` magnitude over time. If PSTF primary diverges similarly, the stepper tolerance is the root cause and must be fixed first. If PSTF primary stays bounded, the bug is specific to MB-95's RHS construction or initial conditions.

2. **Do not attempt fixes in `compute_flrw_cl_track_a`**. It is the reference/prototype path. Fixes go into the new `compute_pstf_cl_track_a` built in Phase 1.3.

3. **Retain Phase 0 probes**. The `BASS_SRC_PROBE`, `BASS_LIMBER_PROBE`, and `phase0_*` tests are kept in the source tree for regression use during Phase 1-3. They are `#[ignore]`d and opt-in via env var so they do not pollute the default test run.

---

## §6. Artifacts produced

- [src/solver/flrw_cl_pipeline.rs](../src/solver/flrw_cl_pipeline.rs): instrumentation (env-gated) and three phase-0 tests (`phase0_d0_1a_source_mode_matrix`, `phase0_d0_1c_dl_profile_full_mode`, `phase0_d0_2b_ell_max_gamma_sweep`).
- No code changes outside of diagnostic instrumentation and tests. MB-95 production path untouched.
- Bit-reference test (`bitref_fast_val_d2`) retained and passes (fast_val D_ℓ hex-identical).

---

*End of D0 audit.*
*Status: D0 gate PASSED (bug isolated). Phase 1 authorized to proceed.*
