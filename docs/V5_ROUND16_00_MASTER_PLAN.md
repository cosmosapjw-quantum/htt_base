# V5 Round-16 Master Plan — Audit-Driven Re-Architecture
_Last updated: 2026-04-26. Owner: BASS. Authority: this doc + V5_ROUND16_01..05._

## 0. Reading order

This plan replaces (does not duplicate) the prior `bianchi_design_pack_v5/` and `docs/ver3/` series for active development. v5/ver3 remain frozen reference; Round-16 is the live working set.

2026-05-01 status note: G4's default-owner portion is now closed in code.
`RuntimeControlBlock.tilt_background_owner` defaults to
`nonperturbative_tilt_rhs`, representative tilted Tier-B contracts use the
dynamic rapidity closure, and fixed velocity is explicit legacy diagnostic.
The remaining tilt work is generic off-axis tilted hierarchy transport and
runtime integration of full angular Stokes collision.

```
V5_ROUND16_00_MASTER_PLAN.md            ← (this) gap registry, sequencing, audit protocol
V5_ROUND16_01_PHYSICS_LAYER.md          ← background + geometry + Codazzi-consistent tilt
V5_ROUND16_02_SOLVER_LAYER.md           ← PSTF hierarchy with RHS k-mixing, off-axis, IC factories
V5_ROUND16_03_OBSERVABLES_LAYER.md      ← LoS propagators, maps, atlas, MES, statistics gate
V5_ROUND16_04_NUMERICS_AND_RUNTIME.md   ← IMEX-ARK4, sparse layout, fairness, profiling
V5_ROUND16_05_SHIP_GATES_AND_ADVERSARIAL_AUDIT.md
                                         ← gate ladder, per-step audit template, ship criteria
```

A new session can pick this directory up cold; no other input is required to start coding.

## 1. Origin: 2026-04-26 audit findings (verbatim, P0/P1 only)

| ID | Severity | Statement |
|----|----------|-----------|
| **G1** | P0 | Python-side `D_2 = 1002.086744 μK²` PSTF closure is **not** bit-identical with the Rust MB-95 anchor (PR-024c open). |
| **G2** | P0 | Hierarchy RHS has **no off-diagonal ℓ-ℓ' or m-m' coupling**; mode mixing only enters at IC and (FLRW) LoS. Without this, no Bianchi-induced spectrum is meaningful. |
| **G3** | P0 | "11-family support" headline is registry-true but mode-coverage-false: 8/11 (II, III, IV, VI₀, VI_h, VII₀, VII_h, VIII) are restricted to axis-aligned mode subsets. |
| **G4** | P1 | Default-owner portion closed 2026-05-01: supported tilted Tier-B background runs now use the King-Ellis dynamic rapidity owner by default. Remaining gap: generic off-axis tilted hierarchy transport and full angular Stokes runtime collision are not closed. |
| **G5** | P1 | B-mode tower has RHS but the FLRW Bessel projector returns identically zero; the `alm_B` archive column is structurally a phantom. |
| **G6** | P1 | No end-to-end output regression for any non-FLRW family beyond the Type-V→Type-I residual comparator. |
| **G7** | P1 | TCA conditional dispatch contradicts the headline "approximation-free truth engine"; the audit accepts the conditional-inline DAE-relaxation but a smoothness audit at the activation threshold was missing (now patched). |
| **G8** | P2 | No real-data Planck likelihood binding; inference whitelist is synthetic-only. |
| **G9** | P2 | Family-specific IC is metadata only ("template-card" status decorative); 11/11 families share one FLRW seed in production. |
| **G10** | P2 | `map_T/Q/U` typed pass-through has no producer (now flagged via `map_output_support` enforcement). |
| **G11** | P3 | No dedicated optimization-fairness benchmark (now patched via `test_optimization_fairness.py`). |

The 12-patch round (R15-AUDIT-PATCH) closed the visibility/enforcement debt for G7, G10, G11 and added explicit gates for G3, G5, G9. Round-16 closes the substantive physics debt for **G1, G2, G3 (mode-coverage closure), G4, G5, G6, G8, G9**.

## 2. Round-16 work-breakdown (audit-fix WBS)

The work decomposes into six tracks. Cross-cutting numerics + ship gates are tracks E and F.

| Track | Closes | Lead doc | Net new code |
|------|---------|----------|--------------|
| **A. Codazzi-tilt evolution** | G4 | 01 §3 | `bass/background/codazzi_tilt_rhs.py`, `tilted_initial_conditions.py` |
| **B. Hierarchy RHS k-mixing** | G2, G3 | 02 §2 | `bass/hierarchy/mode_mixing_blocks.py`; family-specific `A_mix` assembly |
| **C. Family IC factories** | G9 | 02 §4 | per-family `seed_factory()` in `bass/los/families/type_*.py` |
| **D. Bianchi LoS + B-mode** | G5, G6 | 03 §2 | `bass/los/bianchi_propagator/{type_v,type_ix,...}.py`, `bass/los/b_mode_projector.py` |
| **E. Numerics + IMEX-ARK4** | G1 (closure prerequisite) | 04 §1 | `bass/integration/imex_ark4.py`; mass-matrix freeze |
| **F. Real-data binding + statistics gate** | G8 | 03 §6 | `bass/inference/planck_likelihood.py`; promote `template_card_authorized` to fitting precondition |

PR closure path (sequenced):

```
PR-S1 Codazzi-tilt evolution (Track A)
PR-S2 IMEX-ARK4 mainline (Track E) ─────┐
PR-S3 RHS k-mixing scalar block (B-1)   │
PR-S4 RHS k-mixing tensor block (B-2)   │
PR-S5 Family IC factories (C)           │
PR-S6 Off-axis modes for class-A intrinsic (II, VIII; B-3)
PR-S7 Off-axis modes for class-B (III/IV/VI/VII; B-4)
PR-S8 Bianchi LoS — Type V hyperbolic   │
PR-S9 Bianchi LoS — Type IX Wigner-D    │
PR-S10 Bianchi LoS — solvable collocation (II, III, IV, VI, VII, VIII)
PR-S11 B-mode projector tensor source   │
PR-S12 Real-space map producer (T/Q/U via inverse SHT)
PR-S13 D_2 = 1002.086744 PSTF Python-side closure (G1)  ← unblocks all family fitting headlines
PR-S14 Real-data Planck likelihood scaffold (G8)
PR-S15 Production switch MB-95 → PSTF (Phase-1 closure)
```

Critical-path lengths:
- FLRW closure (PR-S2 → S5 → S13): 3 PRs in sequence, ~6–8 weeks at 1 PR/2-weeks.
- Bianchi anisotropy headline (PR-S2 → S3/S4 → S5 → S6/S7 → S8/S9/S10 → S11 → S13 → S14): 9–10 PRs critical, ~5 months.
- The two paths share PR-S2 (IMEX) and PR-S13 (D_2 closure).

## 3. Multi-agent debate: hard architectural choices

Three decisions with non-obvious answers were debated by independent agents (R16-Δ-A/B/C). Each consensus is recorded with the *minority dissent* preserved as a fallback path.

### 3.1 RHS k-mixing implementation (G2)

**Question.** Bianchi anisotropy couples ℓ-ℓ' and m-m' modes in the photon Boltzmann RHS via shear σ_ab and curvature anisotropy `S_AB`. There are three structurally distinct ways to encode this:

| Path | Description | When right |
|------|------------|------------|
| **α (block-sparse explicit)** | Build sparse matrices `A_mix` per η that pair (ℓ, m) with (ℓ±2, m±M), M ∈ {-2..+2}, with PSTF Wigner-3j coefficients C^{(7,8,9)}_{ℓmM} pre-computed. | Default. Maps to ver3 `02A §2` operator factory; portable to Rust verbatim. |
| **β (eigenfunction expansion)** | Expand state in family-specific spatial harmonics whose Laplacian is diagonal; mode-mixing is then a *background-coupled* drift in coefficient space. | Type V (hyperbolic Legendre), Type IX (Wigner-D); analytic spectra exist. |
| **γ (mode-by-mode independent k-grid)** | Solve scalar/vector/tensor sectors at each k as if independent, then post-hoc mix at LoS via path-ordered propagator 𝒢. | Diagnostic only; loses time-resolved coupling. Forbidden as production. |

**Consensus.** Path α as the default authority path for all 11 types; Path β engaged in parallel for V and IX as a diagonal cross-check (must give identical observables to Path α at machine precision). Path γ is permitted only as a `validation_only=True` diagnostic in `bass/los/families/test_*.py`, never as a production predictor.

**Why α**: The Wigner-3j coefficients are family-agnostic (depend only on shear-basis decomposition `σ_ab = Σ_M σ_{2M} Y^{2M}_{ab}` and PSTF tower indexing). Path α therefore produces a single shared C-matrix table that all 11 families consume — no per-family RHS branching. The C-coefficients are derived in Pontzen-Challinor 2007 §3, and re-derived in ver3 `01A_GEOMETRY_AND_WEYL_AUTHORITY_NOTE.md`. Concrete formulas in 02 §2.

### 3.2 Tilted-Bianchi background closure (G4)

**Question.** Should `β` (rapidity) be (a) integrated alongside `(a, σ_+, σ_-)` in a single ODE, (b) integrated separately via the King-Ellis 6-variable system and consumed by the main integrator, or (c) kept static as a parametric input?

**Consensus.** (a) — integrate β as a state variable in the unified background ODE so that Codazzi residuals can be enforced *dynamically*, not only checked post-hoc. The current `nonperturbative_tilt.py` 6-variable closure is now the default Tier-B tilted background owner through `tilt_background_owner = "nonperturbative_tilt_rhs"`, and fixed velocity survives only as an explicit legacy diagnostic owner with metadata marking it as non-production.

**Why (a) over (b)**: Two-ODE solutions risk inconsistent step sizes and Codazzi residual drift between the two integrators. Single ODE keeps `(a, σ_+, σ_-, β)` on the same adaptive controller and lets the gate enforce `||C_{Codazzi}||/H² ≤ 10⁻⁶` per step instead of post-integration.

**Why not (c)**: parametric β is *exactly* the failure mode that produced G4. It silently turns "tilted Bianchi" into "Bianchi with constant boost", losing the King-Ellis dynamics that distinguish whimper-singular from shear-dominant histories.

### 3.3 B-mode projector for Bianchi (G5)

**Question.** Three approaches to producing a non-zero `Δ_ℓ^B(k)`:

| Path | Description | Best when |
|------|------------|-----------|
| **A (lift FLRW Bessel to spin-2)** | Replace scalar j_ℓ with spin-2 P^B_ℓ projector (KKS97); keep B source from quadrupole shear-driven free-streaming. | FLRW + tensor perturbations. *Insufficient for Bianchi*: misses background-driven B production. |
| **B (Bianchi tensor projector via Wigner-D)** | Saadeh-Pontzen-McEwen 2016 (ABSolve) basis: spin-±2 spherical harmonics with Bianchi rotation matrices acting on (ℓ, m, ±2) channels. | All Bianchi types. Default. |
| **C (explicit shear-curvature B source via PSTF)** | Treat B as direct integral of σ_{ab} τ̇ along null geodesic, no spin-2 projector — geometry produces B before recombination. | Diagnostic for Type IX (compact spatial sections); produces correct deterministic B for known Bianchi VII_h templates. |

**Consensus.** Path B as the production default; Path C as a per-family analytic anchor for V, VII_h, IX. Path A is forbidden — it would silently zero B for Bianchi backgrounds.

**Why B**: ABSolve has been validated against Planck data (Saadeh+ 2016, PRL 117, 131302) and produces both the deterministic spin-2 morphology and the post-recombination free-streaming E→B mixing. The Wigner-D matrices are the same family of objects already used in Type IX (Wigner D^J=2_{MN}); Path B re-uses that machinery for all 11 types via the Bianchi rotation convention `D^J_{MN}(α, β, γ)` with Euler angles tied to the family's preferred chart.

## 4. Adversarial audit protocol (applied at every step)

Every PR in §2 must pass an **end-of-step adversarial audit** with the following probe set. The probes are concrete: each one is a code-checkable predicate, not a vibes check. The audit is run *by the implementer*, with results pasted into the PR description under "Adversarial Audit".

```
A1. Toy / naive approximation detection
   • grep for: "TODO", "FIXME", "approx", "naive", "toy", "mock", "fake"
   • For each hit: verdict in {removed, justified-with-cite, downgraded-with-flag}

A2. "Pretend perturbation as nonperturbative" detection
   • grep for: "linear", "small β", "small v", "small σ" in physics modules
   • For each hit: assert that the corresponding *non-linearization* is reachable
     via a runtime control (not a hidden default)

A3. "Temporary analytic model" detection
   • grep for: "placeholder", "fixture", "static", "frozen_diagnostic"
   • For each: verify the metadata flag is set in BoostArchive / SolverCoreOutput

A4. "Mock / surrogate / synthetic only" detection
   • For statistics layer: assert dataset.kind whitelist enforces explicit
     allow_surrogate=True if not real Planck binding

A5. "Tilt & anisotropy correction must be applied" detection
   • grep code path for the term "tilt_freeze=True" or any place that drops
     β from the RHS; assert each is either runtime-controlled or removed
   • assert that for every shear/curvature source S_AB used, the tilt-induced
     correction (γ_e, sinh β, v_e·n̂) is applied at the same code-block level
     (no asymmetric application)

A6. "Family-specific code path silently FLRW" detection
   • For each non-FLRW family: assert that its LoS bundle metadata carries
     family != "FLRW" AND the spatial spectrum is non-Bessel
   • assert that the seed_factory() returns a non-FLRW seed_pack
     (seed_mode != "isotropic_anchor_continuation" for II/III/IV/VI/VII/VIII)

A7. Convergence regression sweep
   • Re-run the production_cutoff_gate sweep at L_max ∈ {6, 10, 20, 40}
   • assert |D_2(L) - D_2(L+Δ)| ≤ 10⁻³ μK² for each pair

A8. Cross-code external reference
   • If the PR touches FLRW physics, run CAMB at the same parameters via
     test_flrw_external_camb; assert per-ℓ tolerance (1% for ℓ ∈ [2,30])

A9. Optimization fairness
   • If the PR touches any optimization (parallel, sparse, cache, batching),
     re-run test_optimization_fairness; assert bit-identity to ≤ 1e-12

A10. Gate-ladder regression
   • Run hard_gate_before_fitting on the prepared output_split_gate bundle;
     assert allowed=True iff all 14 upstream gates are open AND the relevant
     template_card / b_mode / map flags are set as expected
```

The full template lives in `V5_ROUND16_05_SHIP_GATES_AND_ADVERSARIAL_AUDIT.md §3`.

## 5. Adversarial audit of *this plan* (CoVe layer)

Before publishing, the master plan passes a self-CoVe with 12 verification questions. Answers are verifiable by code/file inspection.

| Q | Answer |
|---|--------|
| Q1. Does every G* gap have an owning PR? | Yes (§2 table). G1 → PR-S13; G2 → PR-S3,S4; G3 → PR-S6,S7; G4 → PR-S1; G5 → PR-S11; G6 → PR-S8..S10; G8 → PR-S14; G9 → PR-S5; G10/G11 → patched in R15-AUDIT-PATCH. |
| Q2. Does every PR have an end-of-step adversarial audit? | Yes (§4 protocol; mandatory per §2 ladder). |
| Q3. Is "approximation-free" preserved? | Conditional. TCA inline-relaxation explicitly permitted (CLAUDE.md §6 clarification 2026-04-26); FLRW-UFA + photon-RSA + TCA-pre-phase remain banned. Each appearance is grep-checkable in A2 + A3. |
| Q4. Is the tilt evolution actually wired? | Yes (G4 → PR-S1, default-on owner switch in §3.2). |
| Q5. Does every non-FLRW family produce non-trivial output? | Forced by gate `family_backend_gate` + IC factory contract (G9 → PR-S5) + audit probe A6. |
| Q6. Is `D_2 = 1002.086744 μK²` reachable on Python side? | Target of PR-S13. Until then: xfail in `test_d2_pstf_closure.py` (R15-AUDIT-PATCH P-01). |
| Q7. Are real-space maps producible? | Target of PR-S12; until then `map_output_support="not_implemented"` enforced (R15-AUDIT-PATCH P-08). |
| Q8. Is B-mode genuine? | Target of PR-S11; until then `b_mode_output_support="flrw_zero_only"` flag is the explicit honest envelope. |
| Q9. Does the gate ladder block fitting? | Yes (existing `hard_gate_before_fitting` + new `template_card_authorized` requirement; see 05 §1). |
| Q10. Are external references (CAMB, Saadeh ABSolve) usable? | CAMB harness is `pytest.importorskip` (R15-AUDIT-PATCH P-10); ABSolve is reference-only (no code import — formulas re-derived). |
| Q11. Is the document set self-contained for a new session? | Verified by hand-off check: drop into a new session, read 00 → 01 → 02 → 03 → 04 → 05 → start coding PR-S1. No external input expected. |
| Q12. Does the plan downclaim or fix? | Fix. Every G* has an owning PR with an end-state physics test. The R15-AUDIT-PATCH is the *visibility* layer; Round-16 is the *substance* layer. |

## 6. Definitions & nomenclature pinned for Round-16

These names are used throughout 01–05. Any divergence is a regression.

```
authority path        = production code path that produces user-visible output
template card         = per-family backend metadata: chart, seed_mode, normalization
                       residuals, must-not-do list
seed factory          = callable returning a SeedPack for one (family, branch, k_vec)
fitting gate          = the 15-stage ladder ending in 'fitting_gate'; hard-stops
                       any data-fit unless all upstream gates are open
ship tier             = Tier-A (FLRW closure), Tier-B (broad Bianchi), Tier-C (real-data)
adversarial audit     = end-of-step probe set (§4) attached to every PR
honest envelope       = the set of metadata flags that explicitly mark "what this run
                       is NOT" (e.g. b_mode_output_support, map_output_support,
                       template_card_authorized, tilt_evolution_status)
```

## 7. Tier-by-tier ship criteria (cross-reference: 05 §6)

| Tier | Sufficient PR set | Allowed claim | Forbidden claim |
|------|-------------------|---------------|------------------|
| **A — FLRW closure** | S1 + S2 + S5(FLRW only) + S13 + S15 | "PSTF Python-side D_2 closure at 1002.086744 μK² bit-identical to MB-95"; "FLRW + Type I + V + IX with full mode coverage" | "Bianchi anisotropy spectrum"; "data-fitted" |
| **B — Bianchi broad** | A + S3 + S4 + S6 + S7 + S8 + S9 + S10 + S11 + S12 | "11-family deterministic anisotropy spectrum"; "T/Q/U map predictions"; "B-mode prediction" | "Real-data fitted"; "Statistical Bianchi-tilt evidence" |
| **C — Statistics-grade** | B + S14 + ABSolve agreement at <5% | "Planck-likelihood-fitted Bianchi parameters"; "MES full-cov bound from data" | "Detection" (only in manuscript with explicit FPR + null-ensemble) |

Tier-A unblocks the manuscript's Phase-1 figures; Tier-B unblocks Bianchi anisotropy figures; Tier-C unblocks the data-fit table.

## 8. Document hand-off contract

When a new session opens `docs/V5_ROUND16_*.md`, it must be able to:

1. Read 00 (this) — get the gap registry, sequencing, audit protocol.
2. Pick a PR from §2 (default: PR-S1 if starting fresh).
3. Read the corresponding section in 01–05 — get the equations, skeleton, pseudocode, tests, audit checklist for that PR.
4. Implement against the skeleton; the pseudocode is detailed enough to translate to NumPy/SciPy idiomatically without further reference reads.
5. Run the corresponding tests; the test file path is given in each section.
6. Run the adversarial audit (§4); paste results into the PR description.
7. If the PR opens a new gate, update the gate ladder in 05 §1 and the relevant `forbidden_shortcut_checks` in `htt/bass/runtime/gate_fragments.py`.

This contract is the design's success criterion: a session that follows the contract produces a PR-S* deliverable in 1–2 weeks.

## 9. Out of scope for Round-16

These items are deferred to Round-17 with reason:

- **Backreaction (Buchert Q_D)** — no audit pressure; manuscript section 9 only discusses qualitatively.
- **Lensing potential** — requires independent LSS pipeline; manuscript section 12 is forward-only.
- **Massive-graviton / EFT modifications** — not in BASS scope.
- **Anisotropic-reionization full implementation** — design is in `reionization_design.md` §10–11; implementation is post-Tier-C.
- **MES dynamical bound `B^{dyn}`** — depends on backreaction; deferred.

These remain `out_of_scope` flags in `SolverCoreOutput.metadata` until Round-17 decides otherwise.

## 10. References (canonical for Round-16)

Tier 1 (must-read for any PR):
- Pontzen & Challinor 2007, *Class. Quantum Grav.* 24, 3185 — Bianchi B-mode tower, m-recoupling.
- Pereira, Pitrou & Uzan 2007, *JCAP* 09, 006 — scalar-vector-tensor seesaw, mode mixing in Bianchi I.
- Saadeh, Pontzen, McEwen et al. 2016, *PRL* 117, 131302 — ABSolve full Bianchi+polarization Planck constraints.
- Lesgourgues & Tram 2011, *JCAP* 09, 032 — non-cold relic momentum quadrature (CLASS IV).
- Challinor & Lasenby 2000, *Ann. Phys.* 282, 285 — 1+3 covariant CMB hierarchy I+II.
- Kennedy & Carpenter 2001, NASA/TM-2001-211038 — IMEX-ARK4(3)6L[2]SA tableau.
- Cyr-Racine & Sigurdson 2011, *PRD* 83, 103521 — algebraically-exact second-order TCA.

Tier 2 (per-PR reference):
- King & Ellis 1973, *Commun. Math. Phys.* 31, 209 — tilted homogeneous models.
- Hu & White 1997, *PRD* 56, 596 — total angular momentum method.
- Ali-Haïmoud & Hirata 2011, *PRD* 83, 043513 (HyRec) — recombination history.
- Lewis, Challinor & Lasenby 2000, *ApJ* 538, 473 — CAMB benchmark.

All Tier-1 entries are referenced by name in 01–05. Tier-2 are referenced where used.

---

**End of Master Plan.** Continue to `V5_ROUND16_01_PHYSICS_LAYER.md`.
