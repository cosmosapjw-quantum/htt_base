# AUDIT — Phase FB-0 (Convention & dispatch SSOT for full Bianchi coverage)

**Date**: 2026-04-19
**Phase**: FB-0 — Full Bianchi Coverage bootstrap. Sub-phase **FB-0.1**
normalises the Bianchi background shear convention to Ellis
(`Σ_ab ≡ a σ_ab`) across `einstein_bianchi`, `shear_sources`, and the
LB-5 integrator. FB-0.2 / FB-0.3 are tracked for follow-up sessions and
will append to this same audit log.

**Baseline commit (pre FB-0.1)**: `a257c76` (post LB-6, post-LB P2/P3
cleanup, plus downstream W7/W8 work on MANU / MIO / HTT-STAB that
doesn't touch the Bianchi bedrock).
**Baseline test count**: 2,681 passing + 1 skipped.
**Post FB-0.1 test count**: **2,682 passing + 1 skipped** (+1 Kasner
analytic-recovery test; the four existing shear-decay tests are
retained but with Ellis-convention invariants).
**Verdict**: **통과** (no P0/P1; LB-5 F2 carry-forward resolved;
FB-0.2 / FB-0.3 queued explicitly).

---

## 1. Audit target reconstruction

| Layer | Artifact | Role |
|---|---|---|
| Physics / math source | Ellis, Maartens & MacCallum 2012 §18.3 (shear propagation); Wainwright & Ellis 1997 §18 (per-type N–A source); Pontzen-Challinor 2009 (VII_h spiral) | Defines the Ellis conformal-shear relation ``Σ_ab ≡ a σ_ab`` and the Hubble-normalised W-E source dispatch |
| Background ODE | `bass/background/einstein_bianchi.py::solve_bianchi_background` | Integrates ``(a, Σ_+, Σ_-)`` in conformal time |
| Per-type source dispatch | `bass/transport/shear_sources.py` (11 type functions + registry) | Returns ``ℋ² × S^{WE}(type)`` |
| LB-5 re-use path | `bass/hierarchy/integrator.py::_bg_rhs` | Calls `compute_shear_source` through the combined RHS; LB-5 I-11 / I-12 tests pinned its convention |
| Downstream consumer | `bass/hierarchy/hierarchy_rhs.py::proper_shear_at_eta` | Divides stored Σ by ``a`` to obtain proper-time σ — already assumes Ellis (this was the LB-5 F2 trigger) |
| Tests (flipped) | `bass/hierarchy/test_integrator.py` I-11/I-12; `bass/integration/test_lowell_bianchi.py` LB-6-15/16 | Rewrote invariants ``Σ×a → Σ×a²`` and ``Σ²×a² → Σ²×a⁴`` |
| Tests (new) | `bass/hierarchy/test_integrator.py::test_I12b_kasner_analytic_recovery_type_I` | Direct ``σ × a³ = const`` invariant |
| Tests (updated dimensional) | `bass/transport/test_shear_sources.py::TestDimensionalConsistency` | ``ℋ² × S^{WE}`` scaling (ratio ~4 on ℋ doubling); new split W-E vs spiral for VII_h |
| Spec SSOT | `docs/lowell_bianchi/00_conventions.md §4` (rewritten) | Locks FB plan §6 D2 default to the Ellis convention |
| External-code guard | `bass/validation/test_external_code_policy.py` (unchanged) | Still green |

Source of truth: Ellis §18.3 equations for ``σ̇ + Θ σ = S_proper``;
Wainwright-Ellis §18 Hubble-normalised source; `00_conventions.md §4`
as the repo-internal SSOT pointing at those references.

## 2. Contract / interface table — convention flip map

Derivation of the Ellis ODE from the proper-time companion (starting
``dσ/dt = -3 H σ + S_proper`` and using ``Σ = a σ``, ``𝓗 = aH``,
``η`` with ``d/dη = a d/dt``):

```
dΣ/dη = (da/dη) σ + a (dσ/dη)
      = 𝓗 a σ + a · a (dσ/dt)
      = 𝓗 Σ + a² (-3 H σ + S_proper)
      = 𝓗 Σ - 3 𝓗 Σ + a² S_proper
      = -2 𝓗 Σ + a² S_proper
```

Wainwright-Ellis dimensionless form ``Σ̂ = σ/H``, ``τ = H t`` defines
``S^{WE}(N, A)``; translating back gives ``S_proper = H² × S^{WE}``.
Hence ``a² × S_proper = a²H² × S^{WE} = 𝓗² × S^{WE}``.

**The flip**:

| Site | Pre-FB-0.1 | Post-FB-0.1 (Ellis) |
|---|---|---|
| `einstein_bianchi.solve_bianchi_background` decay | ``-ℋ × Σ`` | ``-2 ℋ × Σ`` |
| `hierarchy.integrator._bg_rhs` decay | ``-ℋ × Σ`` | ``-2 ℋ × Σ`` |
| `shear_sources.source_II` | ``-(2/3) N₁² × ℋ`` | ``-(2/3) N₁² × ℋ²`` |
| `shear_sources.source_VI0 / VII0` | ``S^{WE} × ℋ`` | ``S^{WE} × ℋ²`` |
| `shear_sources.source_VIII / IX` | ``S^{WE} × ℋ`` | ``S^{WE} × ℋ²`` |
| `shear_sources.source_IV / VIh` | ``S^{WE} × ℋ`` | ``S^{WE} × ℋ²`` |
| `shear_sources.source_VIIh` (W-E piece) | ``S^{WE} × ℋ`` | ``S^{WE} × ℋ²`` |
| `shear_sources.source_VIIh` (spiral) | ``kappa × ω_spiral × Σ_⊥`` | ``kappa × ω_spiral × Σ_⊥`` (unchanged — rotation rate, convention-invariant) |
| `source_I / source_V / source_FLRW` | ``(0, 0)`` | ``(0, 0)`` (unchanged) |
| `hierarchy_rhs.proper_shear_at_eta` (``σ = Σ/a``) | Ellis already | unchanged ✓ |
| IC ``Σ_0 = sigma_over_H_init × 𝓗_0`` | = ``a_0 × σ_0`` | unchanged ✓ (already Ellis at instant 0) |

**Type I Kasner check (analytical sanity)**: under the Ellis ODE
``dΣ/dη = -2 𝓗 Σ`` (Type I: no source), for any ``Σ_0 = a_0 σ_0``:

- ``Σ(a) ∝ 1/a²`` ⇒ ``Σ × a² = const``
- ``σ(a) = Σ/a ∝ 1/a³`` ⇒ ``σ × a³ = const`` (Kasner) ✓

## 3. Phys-math audit ledger

| Check | Result | Evidence |
|---|---|---|
| Ellis conformal-shear identification ``Σ_ab = a σ_ab`` derived correctly | ✅ | §2 above; initial condition ``Σ_0 = sigma_over_H_init × 𝓗_0 = a_0 σ_0`` already satisfies this at instant 0, so flipping only the evolution (not the IC) is consistent |
| Proper-time decay ``σ̇ = -3Hσ`` translates to conformal ``dΣ/dη = -2𝓗 Σ`` | ✅ | Algebraic derivation §2; Kasner test `test_I12b_kasner_analytic_recovery_type_I` passes at 2 % |
| W-E Hubble-normalised source ⇒ Ellis conformal source = ``ℋ² × S^{WE}`` | ✅ | dimensional: ``[S_proper] = Mpc⁻² = [H²][S^{WE}]`` with ``S^{WE}`` dimensionless; units check |
| FLRW limit: ``σ ≡ 0`` ⇒ flip is a no-op | ✅ | FLRW and Type I regression (I-07..I-10, LB-6-01..06) all green; shear term vanishes both sides of the flip |
| Type I Kasner ``σ × a³ = const`` recovered | ✅ | new test I-12b passes at 2 % |
| Type V ``σ_source`` remains zero | ✅ | `source_V` unchanged; `test_type_V_shear_source_zero` green |
| VII_h spiral coupling unchanged (rotation rate is convention-invariant) | ✅ | spiral coupling ``ω_spiral × Σ_⊥`` retains its linear-in-ℋ structure (verified by `test_VIIh_mixed_scaling_components`) |
| Σ-independent W-E piece scales as ℋ² (new Ellis invariant) | ✅ | `TestDimensionalConsistency.test_source_units` ratio ≈ 4 across 9 non-VII_h types |
| VII_h mixed scaling decomposition | ✅ | `test_VIIh_mixed_scaling_components` — W-E part ratio ≈ 4, spiral part ratio ≈ 2 |
| Per-type sign conventions preserved | ✅ | `TestSignConventions.test_VII0_vs_VI0_S_minus_opposite_signs` still green; sign structure doesn't touch ℋ power |
| Bianchi I shear invariants ``Σ × a² = const``, ``Σ² × a⁴ = const`` | ✅ | LB-5 I-11/I-12; LB-6-15/16 — drifts < 5 % and < 1 % respectively |
| Sigma² = 0 in FLRW preserved bit-identically | ✅ | LB-6-03 green; FLRW trajectory untouched |
| Friedmann-backbone residual at 1e-4 (LB-6-17) unchanged | ✅ | independent of convention (drops the shear term) |

## 4. Equation-to-code mapping audit

| Target | Test(s) | Implementation path |
|---|---|---|
| Ellis ``dΣ/dη = -2 ℋ Σ + ℋ² S^{WE}`` | `test_I11_bianchi_I_sigma_plus_decay` (Σ × a²) | `einstein_bianchi.solve_bianchi_background` RHS lines 200..211; `hierarchy.integrator._bg_rhs` lines 224..253 |
| ``Σ² × a⁴ = const`` | `test_I12_sigma_squared_a_fourth_constant`; `test_LB_6_16_Sigma_squared_times_a_fourth_conserved` | integrated Σ_± squared × a⁴ along Type I trajectory |
| Kasner ``σ × a³ = const`` (physical) | `test_I12b_kasner_analytic_recovery_type_I` (new) | post-process ``σ = Σ/a`` then check ``σ × a³`` |
| ``Σ × a² = const`` | `test_LB_6_15_Sigma_times_a_squared_conserved` | integrated Σ_+ × a² along Type I trajectory |
| ``ℋ²`` scaling of the Ellis source | `TestDimensionalConsistency::test_source_units[*non-VII_h*]` | ratio ``dSp(2ℋ) / dSp(ℋ) ≈ 4`` |
| Mixed scaling for VII_h (W-E ℋ² + spiral ℋ) | `TestDimensionalConsistency::test_VIIh_mixed_scaling_components` (new) | isolate W-E via Σ = 0; isolate spiral via Σ-difference |
| SSOT `00_conventions.md §4` — Ellis + Pontzen-Challinor | doc-level invariant (read by every downstream session prompt) | §4.1 lists the Ellis identification + evolution; §4.2 keeps the Pontzen-Challinor scalar Σ²; §4.3 bans pre-FB-0.1 ``Σ × a = const`` |
| Source status table unchanged | `TestSourceStatus.*` | `SOURCE_STATUS` preserved — I/V still VALIDATED; 9 types still PROVISIONAL (FB-1 promotes) |

No dead code introduced. No orphan imports. `compute_shear_source`
signature unchanged (positional params reused). `IntegratorConfig`,
`IntegrationResult`, `BianchiCosmology` layouts all unchanged.

## 5. Numerical / pipeline audit

| Item | Finding |
|---|---|
| Bianchi I convergence of ``Σ × a² = const`` at `rtol=1e-6, atol=1e-12` | drift < 5 % over η ∈ [1, 1000] Mpc and ∈ [1, 500] Mpc trajectories — matches the old `Σ × a` drift budget (same ODE stiffness, same integrator) |
| Bianchi I convergence of ``Σ² × a⁴ = const`` at `rtol=1e-9, atol=1e-14` | drift < 1 % — matches the old `Σ² × a²` drift budget |
| Kasner `σ × a³` drift at `rtol=1e-9, atol=1e-14` | < 2 % at the same η window; this is a new, tighter probe and it passes |
| VII_h source near-cancellation (W-E ℋ² vs spiral ℋ) at nominal test params | discovered during FB-0.1 implementation: at `n1=1.8e-2, n3=1.0e-2, a_t=5.5e-3, calH=1e-4, Σ=1e-6` the Ellis source is ~2e-14 from a cancellation of two ~2.5e-13 pieces; this is not a physics bug (spiral is supposed to be Σ-linear and therefore scale as ℋ not ℋ²) but means the old generic "double ℋ → ratio ~2" test would mis-fire for VII_h. Split the test into W-E piece + spiral piece each in isolation (same file). |
| Spiral coupling coefficient `kappa_spiral = 1.0` | still PROVISIONAL — FB-1.3 will calibrate against the Pontzen-Challinor fixture. FB-0.1 preserves the factor verbatim. |
| FLRW regression bit-identicality | σ = 0 everywhere → all flip changes are no-ops; `test_LB_6_03_sigma_stays_zero_in_flrw` confirms Σ_± = 0 to 1e-12 |
| Wall time | 67 s (flat vs 66 s baseline; +1 test added) |
| Determinism | every test reads session-scoped `species` registries; no RNG anywhere |
| Baseline reproduction | 2,681 pre → 2,682 post (+1); 0 regressions |

## 6. Ranked failure modes

| ID | Type | Severity | Summary | Action |
|---|---|---|---|---|
| F1 | carry-forward | resolved | LB-5 F2 (einstein_bianchi Σ-convention mismatch with Ellis) | **Resolved** in this session. |
| F2 | testing | P2 | `TestDimensionalConsistency.test_source_units` parametrised over ALL_BIANCHI_TYPES was too coarse for VII_h because its W-E and spiral pieces near-cancel at the generic test operating point. | **Split in-session** into two tests: `test_source_units` over `_PURE_QUADRATIC_TYPES` (9 types, ratio ≈ 4) and `test_VIIh_mixed_scaling_components` (isolates each piece). No ongoing risk. |
| F3 | documentation | P2 | `shear_magnitude_sq` on `TetradBackgroundState` computes ``Σ_ab Σ^ab / 6`` but the §4.2 dimensionless Σ² requires ``/(6 H²)``. The two formulas differ by a factor of ``𝓗²``. Downstream consumers (`comparator_policy`, `htt.core.bounds`) use the dimensionless form. | Carry forward — this is a pre-existing P2 (independent of FB-0.1) and should be addressed at the FB-2 sigma² normalisation pass, not here. Flagged for FB-2.4. |
| F4 | spec | P2 | FB plan §6 D1 (Class-B frame convention) is locked to Pontzen-Challinor (2 / n₂=0). FB-0.1 doesn't touch frame convention — stays locked. | No action; explicit note preserved in `00_conventions.md §4.4`. |

No P0 / P1 items. The audit confirms FB-0.1 is a surgical convention
flip with no silent behaviour changes outside the Ellis mapping.

## 7. Verifier results

| Verifier | Result | Notes |
|---|---|---|
| Physics (limit recovery, dimensions, signs) | **PASSED** | Kasner recovery `σ × a³ = const` now tested explicitly (new I-12b); FLRW no-op preserved; W-E dimensions carry correctly through ``𝓗²`` factor; sign conventions unchanged. |
| Code (contract satisfaction) | **PASSED** | `compute_shear_source` signature unchanged; `IntegratorConfig` / `IntegrationResult` layouts unchanged; `proper_shear_at_eta`'s ``σ = Σ/a`` conversion already matched Ellis and now matches the evolving Σ as well. |
| Numerical (convergence, tolerance) | **PASSED** | Σ × a² drift < 5 %, Σ² × a⁴ drift < 1 %, Kasner drift < 2 % — all within existing LSODA budget. 2,682 pass + 1 skip. |

## 8. Minimal repair plan (applied in-session)

| Patch | Target | Status |
|---|---|---|
| A | `bass/background/einstein_bianchi.py::solve_bianchi_background` — decay ``-ℋ Σ`` → ``-2ℋ Σ``; module docstring expanded with Ellis derivation + history note | ✅ |
| B | `bass/transport/shear_sources.py` — all 9 non-trivial source functions multiply the W-E dimensionless piece by ``calH**2``; VII_h spiral ``ω × Σ_⊥`` structure preserved | ✅ |
| C | `bass/hierarchy/integrator.py::_bg_rhs` — decay ``-ℋ Σ`` → ``-2ℋ Σ``; docstring cites FB-0.1 audit | ✅ |
| D | `bass/hierarchy/test_integrator.py::test_I11 / test_I12` — invariants Σ×a² and Σ²×a⁴; new `test_I12b_kasner_analytic_recovery_type_I` | ✅ |
| E | `bass/integration/test_lowell_bianchi.py::TestLBBianchiI` — LB-6-15/16 invariants flipped to Σ×a² / Σ²×a⁴ | ✅ |
| F | `bass/transport/test_shear_sources.py` — II scaling test updated (× calH²); dimensional test parametrised over non-VII_h types, new `test_VIIh_mixed_scaling_components` | ✅ |
| G | `docs/lowell_bianchi/00_conventions.md §4` rewritten into §4.1 (Ellis SSOT), §4.2 (Pontzen-Challinor dimensionless Σ²), §4.3 (conventions to avoid), §4.4 (FB-D2 lock) | ✅ |

## 9. Minimal test set (delivered)

**Baseline reproduction**: 2,681 pre-FB-0.1 tests all still green. No
pre-existing test needed to be weakened; four tests had their
invariant formula updated (I-11, I-12, LB-6-15, LB-6-16) — all still
pass.

**Physics sanity (new)**: `test_I12b_kasner_analytic_recovery_type_I`
verifies ``σ × a³ = const`` at 2 % directly from the integrated
trajectory, which cannot be tautologically satisfied by the integrator
state vector alone (it requires the Σ/a conversion + the a³ product to
match Kasner independently).

**Dimensional sanity (split)**: `TestDimensionalConsistency` — 9
non-VII_h types ratio ≈ 4 (ℋ² scaling); VII_h split-piece test
verifies W-E ratio ≈ 4 and spiral ratio ≈ 2 separately.

**Adversarial / edge**: FLRW regression (`test_I07..I-10`,
`test_LB_6_01..06`) verifies the no-op path — σ ≡ 0 absorbs the
convention flip invisibly.

**Regression**: 2,682 passing + 1 skipped; +1 new, 0 regressed.

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과** (no P0 / P1;
  F2 absorbed in-session; F3 pre-existing P2 deferred to FB-2.4;
  F4 is a no-op doc cross-reference).
* **지금 당장 구현/수정한 1개**: the LB-5 F2 carry-forward resolution
  — flipping the einstein_bianchi + integrator + shear_sources trio
  all at once so that `proper_shear_at_eta`'s ``σ = Σ/a`` (which
  already assumed Ellis) no longer sits astride a convention
  mismatch. This unblocks every subsequent FB phase (FB-1 per-type
  validation, FB-2 hierarchy T4–T7 wire-up, FB-3 tilted sector) from
  the convention question.
* **지금 손대면 안 되는 1개**: `TetradBackgroundState.shear_magnitude_sq`
  (missing ``/𝓗²`` for dimensionless Σ²). Touching this today would
  ripple into `comparator_policy`, `htt.core.bounds`,
  `spectrum.cl_assembly` Route-B, and at least three tests currently
  checking the raw ``Σ_ab Σ^ab / 6`` value — all outside FB-0.1 scope
  and better addressed at FB-2.4 when the 11-type ³R_ab^{aniso}
  implementation consolidates the dimensionless-Σ² surface area.

## Gallery refresh

FB-0.1 is a convention flip with visual no-op on the physics gallery:
Type I shear-decay plots continue to show monotonic decay; the
numerical axis values for ``Σ × a²`` are identical to (the old
``Σ × a``) × a, which at the integration's ``a_start ≈ 1e-6``,
``a_end = 1`` window is an ~10⁶× relabel but the qualitative shape
and physics unchanged. The `plots/physics_gallery/11_integrator/` tree
will get an axis-label pass at the FB-1 boundary when per-type
background traces are added to the gallery; FB-0.1 does not emit new
plots.

## Outstanding items carried forward

* **F3** (P2): `TetradBackgroundState.shear_magnitude_sq` → dimensionless
  Σ² per §4.2. Deferred to FB-2.4.
* **FB-0.2** (next session): `BianchiCosmology(structure, beta=0,
  v_hat_e=(1,0,0))` field expansion + `make_cosmology(type_label,
  beta=..., v_hat_e=...)` factory + `IntegratorConfig` tilt-parameter
  exposure. β=0 maintains LB-5 / LB-6 regression bit-for-bit.
* **FB-0.3** (second-next session): LB-6 F2 carry-forward
  (`detect_critical_events` exposes `eta_star` / `chi_star` as
  first-class keys); LB-6 test-helper cleanup to stop recomputing the
  comoving distance to LSS manually.

---

**Phase FB-0 status (after FB-0.1)**: LB-5 F2 resolved; Ellis
convention locked in the `00_conventions.md` SSOT; all 22
configurations of the future FB-6 regression matrix will now inherit
a single, physically motivated shear convention. Ready to hand off to
**FB-0.2** (tilt field exposure).
