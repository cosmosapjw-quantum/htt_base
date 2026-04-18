# Solver-Choice Decision — IMEX-ARK4 as mainline, RODAS5P-centered hybrid as backup

**Date**: 2026-04-18
**Status**: Authoritative. All prior solver-direction documents converge here or are reclassified (see §8).
**Scope**: Numerical-method foundation for bass_rs solver going forward (FLRW → Bianchi I → full Bianchi). Long-term reference — the selection standard for any future solver PR.

---

## §0. TL;DR

1. **Pure IMEX-ARK4 (Kennedy–Carpenter ARK4(3)6L[2]SA)** is the **mainline reference path** for Phase 2+ Bianchi scale-up.
2. **RODAS5P-centered partitioned hybrid** ([`rodas5p_hybrid_ablation_master_plan.md`](../rodas5p_hybrid_ablation_master_plan.md)) is a **frozen benchmark / backup branch**. Not abandoned; retained as rollback option if IMEX validation blocks.
3. **Both paths operate under the same baseline contract + ablation ladder** (the discipline from the hybrid plan's PR-00..PR-10 is solver-neutral and reused).
4. **Memory backend refactor** (`mats_flat` → callback-based stage assembly with sparse/structured linear algebra) is a **solver-independent prerequisite**. Must precede either solver choice at n > ~1000.
5. **Current Phase 1 (PSTF primary FLRW truth freeze) remains on Rodas5P**. This decision applies only to Phase 2+ scale-up, not to the present truth-engine phase.

---

## §1. Context

### 1.1 What prompted this decision

The user's architectural charter (`project/04_implementation_specs/TCA_UFA_RSA_대응안`) bans TCA/UFA/RSA as defaults for Bianchi physics integrity. This eliminates the speed advantage CAMB/CLASS extract from those approximations. The approximation-free regime has its own literature (SymBoltz.jl, ABCMB, DISCO-DJ) achieving ~3-10 s FLRW C_ℓ on a laptop — a plausible target for bass_rs.

At Phase 2+ DOF counts (500–2700 near/mid-term, with long-term Bianchi expansion possible), the question of **which implicit ODE integrator to use** becomes a first-order architectural decision. Two candidates were put on the table.

### 1.2 The two candidates

- **Candidate A — pure IMEX-ARK4 (Kennedy–Carpenter)**: single additive Runge-Kutta tableau with implicit stiff block (Thomson collision diagonal + ℓ≤2 dense small block) and explicit transport/streaming/metric/fluid block. Well-documented in SUNDIALS ARKODE and Dimarco–Pareschi 2012 (for Boltzmann kinetic equations). Supporting cost analysis in [`project/04_implementation_specs/solver_strategy_5566dof_v2.md`](../project/04_implementation_specs/solver_strategy_5566dof_v2.md) §2.
- **Candidate B — RODAS5P-centered partitioned hybrid**: Rodas5P macro-stepper with internal 3-way kernel split (core linearly implicit / mixed explicit predictor-corrector / tail integrating-factor). Full specification in [`rodas5p_hybrid_ablation_master_plan.md`](../rodas5p_hybrid_ablation_master_plan.md).

### 1.3 The critique that refined the decision

A detailed counter-critique of the first-pass "IMEX wins unconditionally" analysis is captured in [`note.md`](../note.md). It corrected six specific overclaims (see §3 below) and produced a more defensible version of the same structural conclusion.

---

## §2. Head-to-head comparison

| Dimension | Pure IMEX-ARK4 | RODAS5P-centered hybrid |
|---|---|---|
| Formal order conditions | **Guaranteed 4th (Kennedy–Carpenter)** | Not proven for current sketch; class-level high-order possible via exponential-integrator theory but not specified |
| Method class | Single additive tableau (ARK) | Partitioned / multirate / exponential-hybrid (bespoke exact recipe) |
| Literature support | SUNDIALS ARKODE, Dimarco–Pareschi 2012 (Boltzmann-specific), SymBoltz/ABCMB as validated deployments | ARKStep ≠ this sketch; ForcingStep/MRIStep/MRI-GARK and Hochbruck–Ostermann exponential integrators cover the class but not this exact coupling |
| Accept/reject | Single embedded Kennedy–Carpenter 3rd-order estimator (asymptotically sound) | Heterogeneous `e_C/e_M/e_T` weighted composite (consistency/order must be shown by experiment, not theory) |
| Split structure | Stiff = collision (diagonal at ℓ≥3, dense 2×2 at ℓ=2, cross at ℓ=1). Explicit = transport + metric + fluid | Core = Θ₀..Θ₃, E₂E₃, v_b. Mixed = Φ Ψ δ_b δ_c v_c N₀N₁N₂. Tail = ℓ≥4 |
| Memory at Phase 2 scale (N≈500–2700) | Callback-based stage assembly natural fit; no `mats_flat` required | `mats_flat`-compatible by default; needs separate refactor |
| Mode switching | None (single tableau, one accept/reject path) | `χ = h·max(κ̇)` hysteresis between tight/loose kernel modes — regime-boundary thrashing risk |
| Bianchi extension (m≠0) | Same tableau; split structure preserved because collision is m-independent | Core/Mixed/Tail split must be re-validated per m-mixing pattern |
| Code surface area | Smaller (single tableau + stiff implicit block); exact lines contingent on shared infrastructure | Larger (state views, core Jacobian, tail IF, mixed predictor, error control, hysteresis controller, plus same shared infrastructure) |
| Engineering risk profile | Well-known algorithm; main risk is split quality + small dense block tuning | Bespoke composition; must empirically verify order, stability, accept/reject at every ablation step |

**Conclusion**: IMEX-ARK4 wins on 7/10 axes. Hybrid wins on 0 strictly; ties on implementation timeline (which is speculative either way) and Bianchi structural compatibility is weaker for hybrid.

---

## §3. Corrections applied to the first-pass analysis

[`note.md`](../note.md) identified six specific overclaims. Each is acknowledged and the judgment stands on the corrected basis.

### 3.1 "5566 DOF → 124 GB memory disaster" — withdrawn

The 5566 figure is a long-term horizon, not current-phase target. Recomputed DOFs:

| State space | DOF | mats_flat at 500 snaps |
|---|---|---|
| Reduced M=2 (1st-order SVT-complete) | 531 | 1.1 GB |
| Reduced M=2 + massive-ν (130) | 661 | 1.6 GB |
| Reduced M=4 (2nd-order scope) | 901 | 3.0 GB |
| M=4 + massive-ν | 1031 | 4.0 GB |
| Current full all-m (L_γ=25, L_ν=15) | 2551 | 24 GB |
| full all-m + massive-ν | 2681 | 27 GB |
| Long-term horizon | 5566 | 124 GB |

Phase 2/3 target sits at 531–2681. At this scale `mats_flat` is "tight but possible", not fatal. **The categorical memory argument is withdrawn**; what remains is the architectural O(N_snap · n²) scaling critique, which is solver-neutral (see §4.3).

### 3.2 "Hybrid is literature-free" — refined

Correct statement: **the hybrid's exact recipe is bespoke**, but the method class has literature. SUNDIALS provides additive ARK (ARKStep) *and* multirate hierarchies (ForcingStep, MRIStep). Hochbruck–Ostermann 2010 Acta Numerica review (~100 pp) provides formal order theory for exponential integrators. MRI-GARK covers hierarchical kernel coupling.

Pure IMEX-ARK4 still has a **direct lineage to Boltzmann kinetic problems** (Dimarco–Pareschi 2012, SymBoltz/ABCMB/DISCO-DJ). That remains a genuine literature advantage, but weaker than "no literature exists."

### 3.3 "IMEX automatically solves memory" — withdrawn

The callback-based stage assembly is a **SUNDIALS/ARKODE design choice** that pairs naturally with IMEX, not a built-in property of "IMEX-ness." A poorly-written IMEX can still stage-buffer giant matrices. **Memory is a backend problem and is solver-neutral**. See §4.3 for the solver-independent backend refactor.

### 3.4 "Tail IF is 1st-order" — over-generalized

The claim applied to **the specific sketch** in the hybrid plan (frozen coefficient + low-order quadrature), not to the exponential-integrator class. High-order exponential integrators exist (Hochbruck–Ostermann B-series theory). The correct critique of the hybrid sketch is: **formal order conditions are not proven for the specific coupling as written**.

### 3.5 "Hysteresis = LSODA replay" — over-stated

LSODA switches solver families (Adams ↔ BDF). The hybrid's χ_on/χ_off changes kernel policy inside the same Rodas5P macro-step. Failure mode is analogous (regime-boundary thrashing), but not literally the same algorithmic class. The actual risk is **tuning burden and boundary oscillation**, not LSODA-identical pathology.

### 3.6 "4–8 weeks vs 3–6 months" — speculation, withdrawn

Line counts and calendar estimates depend on how much shared infrastructure (callback interface, adaptive controller, benchmark harness, validation scripts, Bianchi extension) is counted. The directional claim "single-tableau has smaller method surface area" is retained; the numeric specificity is withdrawn.

---

## §4. Final judgment (corrected)

### 4.1 Why IMEX-ARK4 remains mainline

Even after removing the overclaims above, the following **survive**:

1. **Formal order guarantee**: Kennedy–Carpenter 4th-order with proven embedded 3rd-order estimator. Adaptive integrator theory applies without adjustment. The hybrid sketch does not have an equivalent proof.

2. **Single accept/reject logic**: `e_embedded` has a well-defined asymptotic meaning. The hybrid's `‖e_C/W_C‖² + ‖e_M/W_M‖² + ‖e_T/W_T‖²` combines estimators of different analytic character — practical, but requires empirical justification every time the weights change.

3. **Literature defensibility for Einstein–Boltzmann specifically**: Dimarco–Pareschi 2012 is cited as the modern reference for IMEX applied to Boltzmann with easy-invertible collision operators. SymBoltz.jl and ABCMB operationalize this for cosmology. This is exactly the problem structure we have.

4. **m-extension preservation**: Thomson collision diagonal at ℓ≥3 is m-independent. The IMEX split boundary (stiff vs explicit) does not shift when we go from FLRW (m=0) to Bianchi (m∈{−2..+2}). The hybrid's Core/Mixed/Tail boundaries are physics-adjacent but need re-validation per m-mixing pattern.

5. **No mode switching**: a single tableau with one accept/reject path eliminates regime-boundary thrashing as a category of failure.

### 4.2 Why hybrid is not abandoned

1. **It is not inferior in principle**: the method class (partitioned / multirate / exponential) is legitimate and has literature for other problem domains.

2. **Ablation methodology is solver-neutral and valuable**: the discipline from PR-00..PR-10 (one variable per PR, baseline contract freeze, unified metrics) applies equally to IMEX development.

3. **Rollback option**: if IMEX validation encounters blockers (e.g. split quality fails at a specific regime, or small-block LU is more expensive than predicted), having a vetted hybrid branch allows a course correction without re-opening the solver question from scratch.

4. **A/B benchmark**: head-to-head timing and accuracy comparison at each ablation step is only possible if both branches are maintained under the same contract.

### 4.3 Solver-neutral prerequisite: memory backend refactor

Independent of solver choice, the current `integrate_linear_profile_rodas5p` / `LinearProfileDyn` / `mats_flat` interface is architecturally wrong at scale. Specifically:

- `mats_flat ∼ N_snap · n²` dense storage is O(N·n²) instead of the inherent O(N·nnz) of the problem structure.
- Even at reduced Phase 2 scale (n ~ 500–1000), 1–4 GB lower bound inflates 2–4× with stage buffers, multi-k batching, debug duplication.
- Long-term Bianchi expansion (n → 2551 → larger) hits physical memory limits directly.

The fix is **callback-based RHS + Jacobian assembly** with sparse / structured linear algebra. ARKODE's user-supplied `fe`/`fi`/`jac` callback interface is the natural shape. Rodas5P can be adapted to the same pattern; it is not IMEX-specific.

**This refactor must land before either solver can be scaled beyond current Phase 1 limits.** It is Phase 2.0 of the roadmap.

---

## §5. Consequences for ROADMAP_v3

[`docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md) Phase 2 is refined:

- **Phase 2.0 (new, solver-neutral prerequisite)**: callback-based stage assembly backend. Rodas5P retargeted to new interface, dropping `mats_flat` pre-materialization.
- **Phase 2.1–2.5 (original)**: m-major layout, analytical Jacobian extension (already done at a different layer via PR c5ae4f9), sparse Jacobian backend, adaptive ℓ_max + sponge, matrix LoS. Unchanged.
- **Phase 2.6 (new)**: Pure IMEX-ARK4 mainline implementation per §6 below.
- **Phase 2.6b (new, parallel track)**: RODAS5P-centered hybrid as frozen backup branch. Implemented only to the extent needed for A/B benchmarking at Phase 2.6 exit gate.

Phase 1 (FLRW truth freeze via PSTF primary) is **unchanged**. It stays on Rodas5P with the callback-based backend from Phase 2.0 (applied retroactively if convenient).

---

## §6. PR ladder for IMEX-ARK4 development

Borrowing the ablation discipline from `rodas5p_hybrid_ablation_master_plan.md` but applied to a single-tableau integrator.

| PR | Content | Merge gate |
|---|---|---|
| **IMEX-00** | Baseline contract freeze at current Phase 1 PSTF primary. Reference outputs snapshotted. Metrics logger (accept/reject, factorizations, wall, RSS). | Baseline outputs reproducible, metrics logged |
| **IMEX-01** | Kennedy–Carpenter ARK4(3)6L[2]SA tableau + scalar Van der Pol / Prothero–Robinson test. Standalone stepper; no coupling to solver infra yet. | Order of convergence = 4, embedded estimator monotone in h |
| **IMEX-02** | Operator split `A = A_stiff + A_stream` on current PSTF FLRW RHS: stiff = Thomson collision block, stream = everything else. Identity check: `A_stiff + A_stream ≡ pstf_full_rhs` to ULP | Split bit-equivalence verified |
| **IMEX-03** | Single-k FLRW PSTF primary solve via IMEX-ARK4 (layout 8,6,0). Diagonal implicit for ℓ≥3, dense 2×2 for ℓ=2 Θ–E block, dense 2×2 for ℓ=1 Θ₁–v_b block | D_ℓ agreement with Rodas5P baseline within 1e-6 relative |
| **IMEX-04** | Multi-k end-to-end: `compute_pstf_cl_track_a` IMEX variant. `BASS_IMEX=1` env toggle between Rodas5P (default) and IMEX | All flrw_cl_pipeline regression tests pass under IMEX toggle |
| **IMEX-05** | Callback-based stage assembly backend (solver-neutral prerequisite from §4.3). Applies to Rodas5P and IMEX equally. `mats_flat` retired for production path | Both solvers pass green; peak RSS drops visibly at any layout with n > 500 |
| **IMEX-06** | Polarization activation (L_pol = L_γ = 12). `Θ_2 ↔ E_2` recoupling goes through the dense 2×2 implicit block. EE spectrum generated | bass_py W7-02 4/3 amplification regression ported to Rust and passes |
| **IMEX-07** | Production truncation scale-up (L_γ=25, L_ν=15, L_pol=25). CAMB ±5% at ℓ≤300 | D_2 ∈ 1022 ± 50, D_220 ∈ 5733 ± 300; wall time recorded for comparison |
| **IMEX-08** | Bianchi I (m-major extension, m∈{−2..+2}). Split structure preserved (collision is m-independent). Small-shear σ→0 continuity | FLRW limit (σ=0) reproduces IMEX-07 output. Small σ linear in Σ² |
| **IMEX-09** | Massive-ν momentum bins (130 DOF). Integrated into the m-major layout. | Planck cosmology recovered with mass-eigenstate sum |

### §6.1 Backup branch (RODAS5P hybrid)

A matching ladder for the hybrid is maintained under `rodas5p_hybrid_ablation_master_plan.md` §8 (A0–A9), restricted to:

- A0 (baseline contract) — shared with IMEX-00
- A5 (unified full-state acceptance) — required for A/B comparison to be honest
- A8 (production scale-up) — only to the extent needed for head-to-head benchmark at IMEX-07 exit gate

Other ablation steps (A1, A2, A3, A4, A6) are **deferred indefinitely** unless IMEX mainline hits a blocker.

---

## §7. Measurement protocol (shared across both branches)

Both IMEX and hybrid branches log the same metrics at every PR merge:

- **Performance**: wall time, peak RSS, accepted / rejected steps, Jacobian rebuilds, factorizations, linear-solve total / mean time.
- **Numerical**: `‖y_candidate − y_baseline‖ / ‖y_baseline‖`, per-block drift, stage defect norms.
- **Physical**: TT/EE transfer differences, low-ℓ C_ℓ drift, D_2 drift, visibility-peak source drift.
- **Stability**: reject bursts, NaN/Inf/negative-state hits, κ̇→0 and large-κ̇ limit recovery.

Baseline for both branches: current Rodas5P / `mats_flat` / PSTF primary Phase 1 output, snapshotted at IMEX-00 / A0.

---

## §8. Document consolidation

This document is the single authoritative statement of solver direction. Existing documents are reclassified as follows.

### 8.1 Reclassified — backup / benchmark reference

- [`rodas5p_hybrid_ablation_master_plan.md`](../rodas5p_hybrid_ablation_master_plan.md): status changed from "proposed mainline" to **"frozen backup branch; benchmark-only. Superseded as mainline direction by IMEX_DECISION."** The ablation-ladder discipline is retained and borrowed by the IMEX PR ladder (§6). Move to `docs/` at §8.5 below.

### 8.2 Absorbed — critique material

- [`note.md`](../note.md): refined the first-pass IMEX-is-obviously-right analysis into the corrected version captured in §3 here. Kept as historical record; no further canonical role. Move to `docs/` at §8.5 below.

### 8.3 Supporting reference material (kept as-is)

- [`project/04_implementation_specs/solver_strategy_5566dof_v2.md`](../project/04_implementation_specs/solver_strategy_5566dof_v2.md): IMEX-ARK4 cost analysis, Kennedy–Carpenter tableau reference, Dimarco–Pareschi citation, SymBoltz benchmark numbers. This document is referenced by §2 and §6 here and **remains the primary cost-model reference** for the IMEX implementation.
- [`project/04_implementation_specs/TCA_UFA_RSA_대응안`](../project/04_implementation_specs/TCA_UFA_RSA_대응안): architectural charter banning TCA/UFA/RSA as defaults. Upstream of this decision.
- [`project/04_implementation_specs/R-P1-02_IMEX_ARK_benchmark_report.md`](../project/04_implementation_specs/R-P1-02_IMEX_ARK_benchmark_report.md): empirical IMEX benchmark report. Referenced for historical continuity.

### 8.4 Upstream — roadmap this decision updates

- [`docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md): Phase 2 refined per §5. This decision is an addendum to the roadmap, not a replacement.

### 8.5 Recommended file moves (follow-up PR)

For consistency with the rest of the documentation tree:

```
rodas5p_hybrid_ablation_master_plan.md → docs/RODAS5P_HYBRID_BACKUP_PLAN.md
note.md                                → docs/IMEX_DECISION_CRITIQUE_NOTES.md
```

These moves are **not** required for this decision to take effect; they are cosmetic cleanup. Perform them when convenient.

---

## §9. Open questions deferred to implementation

The following questions are **not** settled by this decision and must be answered empirically during IMEX PR ladder execution:

1. **Small dense block size for ℓ≤2**: at layouts with m∈{0,±1,±2} activated, the ℓ=2 Θ–E dense block grows from 2×2 to ~10×10. Cost of direct LU vs block-iterative solve at this size is to be benchmarked (IMEX-04 / IMEX-08).
2. **IMEX accept/reject controller PI gains**: Kennedy–Carpenter default vs cosmology-tuned values. Benchmark at IMEX-03.
3. **Jacobian reuse cadence**: SymBoltz reports LU factorization reuse across multiple steps when Newton convergence is healthy. Adapt to our linear case. IMEX-05.
4. **Explicit-stage stiffness at high m**: as Bianchi geometric coupling 𝒢 grows with σ, does the explicit part re-enter the stiff regime? If so, 𝒢 migrates to the implicit block. IMEX-08.
5. **Callback backend: Rust trait vs function pointer**: implementation choice in IMEX-05. Both are viable; pick based on compile-time overhead and inlining behavior.

Each of these goes into its own PR-level decision log, not into this document.

---

## §10. Change log for this decision

| Date | Change | Basis |
|---|---|---|
| 2026-04-18 | Initial decision recorded. Pure IMEX-ARK4 mainline, hybrid backup. | Session analysis + note.md critique + solver_strategy_5566dof_v2.md cost model |
| — | (future revisions recorded here) | |

---

*End of IMEX_DECISION_2026-04-18.md.*
*Next concrete action: Phase 2.0 (memory backend refactor) scoping + IMEX-00 baseline contract freeze.*
