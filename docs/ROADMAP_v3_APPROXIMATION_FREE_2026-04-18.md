# BASS Rust Roadmap — v3 (approximation-free Bianchi production)

**Date**: 2026-04-18
**Supersedes**: MASTER_PROMPT_LIST_v4.0 (2026-04-11) for solver-side direction
**Status**: user-approved plan, 2026-04-18
**Companion**: `BASS_PY_FAST_TRACK_2026-04-18.md` (side-track for preliminary plots)

> This document is the single reference for the Rust production solver's
> architectural direction going forward. It supersedes v4.0's assumption
> that `sync_gauge_camb.rs` would become the truth engine. User's decision
> (2026-04-18): **PSTF primary → production path; MB-95 → reference prototype**.

---

## §1. Where we are (measured, 2026-04-18)

### 1.1 Measured baseline on desktop (Ryzen 9 5900X, 24T)

| Workload | bass_rs wall | D_2 | Status |
|---|---|---|---|
| `fast_validation` (ℓ_max=30, n_k=30, SwOnly) | 5.08 ± 0.18 s | 768 μK² | order-of-magnitude OK |
| `default_track_a` (ℓ_max=2500, n_k=100, Full) | 10.42 ± 0.54 s | **3.95 μK²** | ❌ **Full mode broken** (D_200 = 10²⁰⁰) |

Reference (same machine):

| System | Wall | D_2 | Notes |
|---|---|---|---|
| CAMB default (24T) | 0.096 s | 1022.4 | TCA+UFA+RSA all ON |
| CAMB single-thread | 0.934 s | 1022.4 | same approximations |
| **SymBoltz.jl (approximation-free)** | 3.1 s | 1022 | i7-12800H laptop, ℓ_max=16, Julia |
| CLASS TCA only | 8.7 s | 1022 | same machine as SymBoltz |
| CLASS all approximations | 1.6 s | 1022 | same |

### 1.2 CPU attribution (perf record, production scale)

| Function | Self % | Location |
|---|---|---|
| `lu_solve_factored_flat_into` | 26.3 | `src/core/lu.rs:133` |
| `linear_profile_rhs_only_into` | 23.0 | `src/solver/rodas5p.rs:103` |
| `step_linear_profile_rodas5p_into` | 20.1 | `src/solver/rodas5p.rs:237` |
| `lu_factor_in_place_flat_into` | 17.7 | `src/core/lu.rs:62` |
| `linear_profile_rhs_jac_flat_into` | 5.8 | `src/solver/rodas5p.rs:123` |
| memmove/memset (libc) | 2.4 | — |
| **Σ top 5** | **92.9** | ODE inner loop |

**Bessel evaluation = 6.5%** at prod. The legacy PERF_NOTES.md claim of
"57.7% Bessel" is empirically wrong on the current pipeline.

### 1.3 Flops/s reality check

- 8.5 GFLOP estimated arithmetic at prod scale
- 178 core-sec CPU → ~48 MFLOP/s/core = **0.2% of Zen3 AVX2 FMA ceiling**
- Code is overwhelmingly **memory-bound / instruction-overhead-bound**, not flop-bound
- Huge headroom for (structural, not micro) optimization

---

## §2. Target recalibration

### 2.1 What NOT to chase

- **CAMB 0.1s is unreachable** — that speed is bought with TCA/UFA/RSA
  approximation stack which this project's architectural charter
  (`project/04_implementation_specs/TCA_UFA_RSA_대응안`) forbids as defaults
  for Bianchi work. Chasing it would invalidate the whole anisotropy
  detection methodology.
- **Micro-optimization ≤10% gains** — irrelevant at 100× gap-to-CAMB scale.
  Phase 1.1 (fused interp+matvec) was tested and produced 0% wallclock
  improvement despite bit-identical output (see §2.3 log).

### 2.2 What IS the target

- **Approximation-free FLRW limit**: SymBoltz-equivalent (3-10 s on this
  desktop for ℓ_max=2500).
- **Bianchi (ℓ,m) production**: 30-60 s range per
  `project/03_physics_notes/nonlinear_boltzmann_feasibility_v2.md`
  (~10⁴ CPU-sec ≈ ~10 min single-thread ≈ 30-60 s parallel at 24T).
- **Correctness first**: D_2 = 1022 ± 50, D_220 = 5733 ± 300 (v4.0 ENTRY-02
  gate). CAMB ±5% at ℓ ≤ 300 (v4.0 ACC-06r).

### 2.3 Already-tried null results (do not re-try)

| Attempt | Result |
|---|---|
| `lto = "fat"` + `codegen-units = 1` | **+4.6% regression** (i-cache pressure) |
| `lto = "thin"` | prod −5.1% borderline, fast_val within noise |
| Phase 1.1 fused interp+matvec (bit-identical) | A/B within same binary: Δ = 0.3σ. **Zero wallclock gain.** |
| `target-cpu = native` (per legacy PERF_NOTES) | regression at MB-95 code circa PR-PERF-05 |

Retained config: `[profile.release] lto = "thin"` in Cargo.toml (neutral
baseline, ~5% borderline win). Everything else reverted.

---

## §3. Hard architectural constraints (non-negotiable)

Source: `project/04_implementation_specs/TCA_UFA_RSA_대응안` (2368 L).

### 3.1 BANNED as defaults

- **TCA as pre-phase IC generator** — the "reduced solve → reconstruct → full solve" pattern is banned.
- **Standard FLRW UFA** — default OFF. Only neutrino-UFA allowed, with residual monitor, Bianchi-disabled.
- **Photon RSA** — banned outright. Eats the low-ℓ / ISW / reionization / directional signals.
- **FLRW-specific closure formulas** copied into Bianchi — banned. Closures must be in operator-norm terms.

### 3.2 MANDATED design principles

- **One equation set, many numerical strategies, zero hidden physics switches.** Solver switches allowed; equation switches forbidden.
- **Operator decomposition**: RHS = 𝒞 (collision) + ℱ (free-stream) + 𝒢 (Bianchi geometry) + ℳ (metric/matter) + s.
- **Sparse Jacobian is the real battle**, not integrator choice.
- **(m)-major state ordering**, not species-first. Bianchi coupling is ℓ→ℓ±1, m→m, m±1, m±2.
- **Matrix line-of-sight** as primary projector; scalar FLRW LoS as special case.

### 3.3 Recommended solver stack

- **Engine-T (truth)**: sparse BDF2/NDF OR stiffly-accurate ESDIRK (Kvaerno4/5) OR Rosenbrock-W.
- **Engine-P (production)**: KenCarp4/5 IMEX, Rosenbrock-W (Rodas5P current), or Kvaerno5.
- **Engine-D (diagnostic)**: Implicit Euler / TR-BDF2 / Rosenbrock23 — slow, robust, debugging only.
- BDF order ≥ 3 is not A-stable (Dahlquist barrier). BDF1/2 for stiff-dominant phases only.

### 3.4 High-ℓ tail strategy (replaces UFA)

Priority: (1) adaptive ℓ_max on tail-energy ratio, (2) sponge/absorbing top-ℓ layer,
(3) asymptotic closure diagnostic, (4) neutrino-UFA last-resort.

---

## §4. Execution plan — 5 phases

Each phase has a validation gate. Failure halts the chain and forces replay.

### Phase 0 — Correctness audit (1 week)

**Blocker if not resolved**: `default_track_a` produces D_2 = 3.95 instead of ~1022.

- **D0.1** Run MB-95 `solve_stacked_native_rodas5p` directly (not via `compute_flrw_cl_track_a`). Per PREP notes the 2000-k Track B 2000k reproduces D_ℓ ±0.6% at ℓ≤300. If that still holds today, the bug is in `flrw_cl_pipeline.rs` (source extraction + LoS), not in the solver itself.
- **D0.2** Trace the `SourceMode::Full` path in `src/solver/flrw_cl_pipeline.rs`. Check the `extract_source_grid` call at prod scale. D_200 = 10²⁰⁰ strongly suggests unphysical amplification in ISW or polter_ddot reconstruction.
- **D0.3** Cross-check PSTF primary's `pstf_solve_kmode_adiabatic` single-mode output against MB-95 at matching k. Confirms PSTF primary solver is numerically sound.

**Phase 0 gate**: bug isolated (solver / pipeline / source). If solver is sound, proceed. If solver bug, fix before Phase 1.

### Phase 1 — FLRW truth freeze via PSTF primary (4-6 weeks)

Ports v4.0 ENTRY track to PSTF primary as the new production target.

- **P1.1 ApproximationConfig + ResidualMonitor trait** (v4.0 P1-00r ported). Default-constructed struct has all flags OFF = truth mode. Every approximation gates on residual.
- **P1.2 PSTF primary production config activation**. `src/solver/pstf_primary/full_rhs.rs`: `lmax_pol = 12`, massive-ν GL 10 bins, full E-mode path.
- **P1.3 PSTF primary end-to-end C_ℓ pipeline**. New: `compute_pstf_cl_track_a(params, config) -> FlrwClResult`. MB-95 currently the only path in `flrw_cl_pipeline.rs`.
- **P1.4 FLRW validation**. D_2 = 1022 ± 50, D_220 = 5733 ± 300, CAMB ±5% at ℓ ≤ 300.
- **P1.5 Source contract closure**. Track A (PSTF source) vs CAMB source RMS < 10% at all k ∈ [0.001, 0.1]. Port v4.0 ENTRY-03.

**Phase 1 gate**: D_2 = 1022 ± 50 on FLRW limit via PSTF primary, CAMB ±5% at ℓ ≤ 300.

### Phase 2 — Bianchi-ready infrastructure (6-8 weeks)

Implements TCA_UFA_RSA document §3-10 (sparse Jacobian, m-major, matrix LoS).

- **P2.1 (ℓ,m) m-major layout formalization**. `src/solver/pstf_primary/layout.rs`: `PstfFlrwLayout` → full `LmLayout` with m ∈ {−m_max..+m_max}. m=0 remains special case.
- **P2.2 Analytical Jacobian full-sector extension**. `src/solver/pstf_primary/jacobian.rs`: current scope = free-stream + collision only. Extend to metric + fluid + Clebsch-Gordan κ-factor for m ≠ 0. σ = 0 → m ≠ 0 entries zero (preserves FLRW).
- **P2.3 Sparse Jacobian backend**. Choose `faer-sparse` (preferred; active maintenance, AVX2 microkernels) or `sprs`. Exact sparsity pattern pre-computed. LU factorization reuse policy.
- **P2.4 Adaptive ℓ_max + sponge boundary**. `R_ℓmax = tail-energy / total` monitor. Top-ℓ shell damping layer (gentle profile to avoid low-ℓ backreaction).
- **P2.5 Matrix LoS projector**. Current `src/los/` is scalar. Introduce `G_{Aa}(η, k)` matrix kernel; FLRW LoS becomes the A=a=0 case.

**Phase 2 gate**: FLRW limit (m=0 only) reproduces Phase 1 D_ℓ. Jacobian
sparsity pattern matches expected band structure. Small-shear Σ² ≪ 1
continuity check.

### Phase 3 — Production throughput tuning (3-4 weeks)

- **P3.1 Solver backend A/B**. Current Rodas5P vs Kvaerno5 (ESDIRK, Julia/`diffsol`) vs KenCarp4 (IMEX). SymBoltz paper directly recommends this comparison.
- **P3.2 Jacobian reuse + LU cache**. SymBoltz's core trick: reuse factorization across many steps when Newton convergence is healthy.
- **P3.3 k-mode parallelism retained**. Already implemented (`rayon par_iter` in `flrw_cl_pipeline.rs:188`). Deterministic reduction order already verified bit-identical-safe.
- **P3.4 Measured target**: FLRW 5566 DOF < 10 s wallclock (SymBoltz's 3 s × 3× Bianchi-ready overhead); Bianchi full (ℓ, m) < 60 s on 24T.

**Phase 3 gate**: wallclock targets met, all Phase 2 tests still green.

### Phase 4 — bass_py bridge (2-3 weeks)

Closes the `bass_rs ↔ bass_py` interface that
`BASS_PY_HTT_TSC_RESEARCH_PLAN.md §2.4` lists as "bass_rs 측 미구현".

- **P4.1 `BianchiTransferFunctions(k)` JSON/CSV producer**. Rust-side module emitting transfer functions per (type, Σ², β, x_h) grid point. Schema pinned in `docs/BASS_PY_BRIDGE_SPEC.md` (new).
- **P4.2 Atlas HDF5 generator**. Pre-computes `(type × Σ² × β × x_h)` grid for HTT consumption (`post_bass_programme_v1.md HI-01`).
- **P4.3 Route B anti-regression guard**. Already complete — just maintain.

**Phase 4 gate**: bass_py round-trip integration test green.

### Phase 5 — Bianchi extension proper (12-18 months, spans beyond this roadmap)

Per `project/03_physics_notes/nonlinear_boltzmann_feasibility_v2.md`. Not
planned in detail here; listed for sequencing.

- P5.1 Bianchi type I σ² > 0 background (partial code exists in `src/bianchi/`)
- P5.2 Tilt dynamics (ω_a ≠ 0) — V-tilt sector
- P5.3 Θ⁴ quadratic sources (`Quadratic_Source_Coefficients_for_Second-Order_Bianchi_I_Boltzmann_Theory.md`)
- P5.4 Bianchi VIIh, IX extensions
- P5.5 Nonlinear Σ regime (Σ² > 10⁻⁴)

---

## §5. Success metrics (measurable gates)

| Phase | Pass condition | Instrument |
|---|---|---|
| 0 | Bug localized (solver / pipeline / source) | diagnostic log |
| 1 | PSTF FLRW D_2 = 1022 ± 50, D_220 = 5733 ± 300 | CAMB comparison |
| 1 | CAMB ±5% at ℓ ≤ 300 | per-ℓ rel_err |
| 1 | wall ≤ 20 s (ℓ_max=2500 FLRW, 24T) | hyperfine n=5 |
| 2 | (ℓ,m) m-major sparsity pattern correct | Jacobian nnz count + band metadata |
| 2 | FLRW limit (m=0 only) matches Phase 1 | regression (relax bit-identical → 1e-10 rtol) |
| 3 | wall ≤ 10 s (ℓ_max=2500 FLRW, 24T) | hyperfine n=5 |
| 3 | wall ≤ 60 s (Bianchi I full, 24T) | hyperfine n=3 |
| 4 | bass_py ↔ bass_rs round-trip | integration test |

---

## §6. Killed directions (write once, remember forever)

These are empirically confirmed dead ends on this codebase/hardware.
Do not re-attempt without new measurement.

- `lto = "fat"` + `codegen-units = 1` (regresses).
- Phase 1.1 fused interp+matvec preserving bit-identical (zero gain, confirmed by same-binary A/B).
- Micro-optimization targeting top 5% of profile (structural wins required).
- "Port CAMB's TCA" (banned by architectural charter).
- "Use UFA/RSA" (banned).
- `target-cpu = native` as default release profile (regresses on MB-95; untested on PSTF primary but low expected gain).

---

## §7. Parallel side-track

While this roadmap runs on the Rust side, the **bass_py fast-track**
runs in parallel and is documented separately in
[`docs/BASS_PY_FAST_TRACK_2026-04-18.md`](BASS_PY_FAST_TRACK_2026-04-18.md).

bass_py is a Python low-ℓ (ℓ ≤ 30) special-purpose solver already at
14/24 prompts (1,637 tests passing). It produces direction-dependent
likelihoods for dipole + 15-model Bianchi evidence independently of
bass_rs. The side-track is optimized for **preliminary plots first**,
not full coverage.

The two tracks have a formal interface (`BianchiTransferFunctions(k)`,
atlas HDF5) activated at Phase 4 of this roadmap.

---

## §8. Persisted session learnings (memory)

See `/home/cosmosapjw/.claude/projects/-home-cosmosapjw-Dropbox-bianchi-bass-phase1-snapshot-2026-04-18-bass-phase1-snapshot/memory/` for Claude's durable notes:

- `project_bass_phase1.md` — Bianchi+tilt design law
- `project_perf_targets.md` — recalibrated per above
- `project_solver_infra.md` — Rodas5P + nonlinear + diffsol; mimalloc
- `project_measured_bottleneck.md` — fresh perf, supersedes PERF_NOTES.md
- `project_arch_constraints.md` — TCA/UFA/RSA bans + operator decomposition mandate

---

*End of ROADMAP_v3.*
*Next concrete action: Phase 0 correctness audit (D0.1–D0.3).*
