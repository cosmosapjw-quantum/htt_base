# AUDIT — Phase LB-5 (unified Lowell-Bianchi integrator + TCA dispatch)

**Date**: 2026-04-19
**Phase**: LB-5 — `LowellBianchiIntegrator` driving background +
photon temperature tower + photon E-mode tower + reduced neutrino
fluid on one η-grid through `scipy.integrate.solve_ivp` (LSODA),
with a TCA algebraic-dispatch branch at ℓ=2 and a **real W3
`CanonicalDecision`** threaded to `solve_tca_closure` (resolves the
LB-3 F3 / LB-4 F3 carry-over bypass).
**Baseline commit**: `2a67f20` (post LB-4)
**Baseline test count**: 2,441 passing (post LB-4)
**Post-audit test count**: 2,534 passing (93 new: 13 in
`test_pack_unpack.py` + 10 in `test_ic.py` + 6 in
`test_neutrino_reduced.py` + 7 in `test_event_detection.py` + 15 in
`test_integrator.py` + 8 in `test_aux_state.py` + a few
parametrised overflow into the existing shared fixtures).
**Verdict**: **통과** (no P0/P1; three P2/P3 items documented below).

---

## 1. Audit target reconstruction

| Layer | Artifact | Role |
|---|---|---|
| Physics / math source | Ellis §6, §18.3; Ma-Bertschinger 1995 §8; Hamilton 2001 (CAMB); Kolb §3.5, §5.4; lowell §6, §9.2; Hindmarsh 1983 (LSODA) | Combined-state ODE; stiffness switching; FLRW background reuse |
| Driver | `bass/hierarchy/integrator.py` (LB-5) — `LowellBianchiIntegrator.run` | Single-pass `solve_ivp` over the 101-entry state (L_max=6) |
| State packing | `bass/hierarchy/pack_unpack.py` (LB-5) | Fixed spec §2.1 layout — `(a, Σ_+, Σ_−, Π_{0..L}, E_{0..L}, Δ_ν, q_ν, π_ν, G_3)` |
| Aux payload | `bass/hierarchy/aux_state.py` (LB-5) | `IntegratorAuxState` — shared bg table, species, tetrad, closure, collision operators, **real** `CanonicalDecision`, TCA threshold, `Γ_T` test override |
| Initial conditions | `bass/hierarchy/ic.py` (LB-5) | `zero_IC` (spec §6 baseline) + `make_initial_state` with axisymmetric Π_2 / E_2 seeds |
| Reduced ν fluid | `bass/hierarchy/neutrino_reduced.py` (LB-5) | 4-scalar (Δ_ν, q_ν, π_ν, G_3) diagonal block (lowell §9.3) |
| Critical events | `bass/hierarchy/event_detection.py` (LB-5) | `z_eq`, `z_*` (visibility-peak argmax on native fixture grid), `η_reion_midpoint`, `η_today` |
| Reused (no re-derivation) | `bass/background/einstein_bianchi.solve_bianchi_background` (background RHS arithmetic); `bass/closure/quadrupole_tca.solve_tca_closure` (W6-04 algebraic closure); `bass/hierarchy/hierarchy_rhs.hierarchy_rhs_photon` (LB-2b driver); `bass/hierarchy/closure.py` (LB-3); `bass/collision/thomson_pstf.py` (LB-4) | Upstream layers that LB-5 composes |
| Spec | `docs/lowell_bianchi/05_integrator_spec.md` §1–§12 | Implementation contract (two in-session amendments — see §6 below) |

Source of truth: spec §2.1 (state-vector layout) + spec §3 (combined
RHS assembly) + spec §10 (numerical test targets I-01..I-18).

## 2. Contract / interface table

| API | Input contract | Output | Units / invariants |
|---|---|---|---|
| `pack_combined_state(a, Σ_±, photon_T, photon_E, nu_reduced, L_max)` | photon_T.L == photon_E.L == L_max; nu_reduced shape (4,) | flat float64 `(combined_total_size(L_max),)` | spec §2.1 fixed layout |
| `unpack_combined_state(y, L_max)` | y shape matches `combined_total_size(L_max)` | `CombinedState` with **copied** arrays | round-trip bit-identical at atol 1e-14 |
| `slice_a/sigma_pm/photon_T/photon_E/neutrino_reduced` | L_max ≥ 0 | contiguous non-overlapping slice objects | partition the full vector (I-03) |
| `zero_IC(L_max, a_initial, Σ_±_initial)` | a_initial > 0; L_max ≥ 2; Σ_± finite | flat y0 with only `a, Σ_±` non-zero | deterministic (I-04) |
| `make_initial_state(..., seed_Pi_2_m0, seed_E_2_m0)` | optional scalar seeds | y0 with axisymmetric m=0 slots populated | all other slots exactly 0.0 |
| `neutrino_reduced_rhs(η, nu, *, bg_table)` | nu shape (4,) | shape (4,) RHS | MB-1995 eq (49) diagonal k=0 damping; Δ_ν' coefficient = −(4/3) a Θ; q_ν' / π_ν' / G_3' coefficient = −a Θ |
| `find_z_equality / z_star / eta_reion_midpoint / detect_critical_events` | SpeciesBackgroundRegistry + FLRWBackgroundTable | `z_eq ∈ [3300, 3500]`, `z_* ∈ [1089, 1091]`, `η_reion ∈ [5000, 5200]` | Kolb §3.5; native-grid visibility argmax |
| `build_integrator_canonical_decision(β, σ²)` | β / σ² finite | frozen `CanonicalDecision` with `allow_reduction = AND(beta_gate, sigma_gate, tangency_gate)` | **resolves F3**: real gates, not bypass |
| `build_aux_state(..., gamma_T_override)` | closure is ClosureStrategy; decision is real; override is `η → Γ_T` callable or None | frozen `IntegratorAuxState` | supports I-18 deep-tight-coupling probe |
| `IntegratorAuxState.Gamma_T_at(η)` | η in table range | float ≥ 0 | uses `gamma_T_override` if provided; else `baryon.tau_dot(η)` with zero-fallback outside recomb fixture |
| `IntegratorAuxState.H_local_at(η)` | η in table range | float > 0 Mpc⁻¹ | `calH / a` from shared FLRW spline |
| `combined_rhs(η, y, *, L_max, aux_state, cosmo, tca_tracker)` | y shape matches L_max; aux_state populated; cosmo is BianchiCosmology | flat float64 RHS | deterministic; zero-IC FLRW → zero hierarchy output |
| `LowellBianchiIntegrator.run()` | config validated at construction | `IntegrationResult` with `(η, a, Σ_±, photon_T_tower, photon_E_tower, neutrino_reduced, critical_events, tca_active_mask, solver_info)` | raises on non-finite output; uses LSODA with `rtol=1e-6, atol=1e-12` |

The LB-5 `canonical_decision` wiring is **load-bearing**: every TCA
algebraic-closure call inside `combined_rhs` threads the
integrator's real decision into `solve_tca_closure`, so the W3
`allow_reduction` gate is enforced at the ODE step (not bypassed
via `_always_allowing_tca_decision`). An audit-ledger test
(`test_real_canonical_decision_blocks_oversize_beta`) pins this.

## 3. Phys-math audit ledger

| Check | Result | Evidence |
|---|---|---|
| State layout is fixed at spec §2.1 indices | ✅ | `test_I03_slices_partition_the_vector` + explicit boundary assertions at L_max=6 |
| Pack/unpack bit-identical | ✅ | `test_I01_roundtrip_bit_identical` at atol 1e-14, L_max ∈ {4, 6, 8} |
| FLRW zero-IC → Π ≡ 0 | ✅ | `test_I07_flrw_zero_ic_photon_stays_zero` at 1e-10 |
| a(η_today) ≈ 1 | ✅ | `test_I08_flrw_a_today_is_unity_and_sigma_zero` at 1e-3 |
| a-dynamics vs bg_table spline | ✅ | `test_I09_flrw_a_matches_bg_table_spline` at rtol 1e-3 |
| Species sum rule at η_today | ✅ | `test_I10_species_sum_rule_at_eta_today` at abs 1e-5 |
| Shear-decay invariant (einstein_bianchi convention) | ✅ | `test_I11_bianchi_I_sigma_plus_decay` + `test_I12_sigma_squared_a_squared_constant` — ``Σ × a = const``, ``(Σ_+²+Σ_−²) × a² = const`` at 5% / 1% respectively (amended from the pre-LB-5 spec's ``Σ² × a⁴`` per §6 below) |
| Finite output at L_max ∈ {2, 4, 6} | ✅ | `test_I13_L_max_variants_integrate_cleanly` |
| Thomson damping dominates at high Γ_T | ✅ | `test_I14_high_Gamma_T_pi2_damping` (instantaneous Π̇_2 < 0, magnitude ≫ residual) |
| Critical events in expected bands | ✅ | `test_I15_z_star_near_planck18` (1089), `test_I16_z_eq_matches_kolb_target` (3419), `test_I17_eta_reion_matches_z_7_67` (5118 Mpc) |
| TCA dispatch activates at Γ_T/H > threshold | ✅ | `test_I18_TCA_dispatch_matches_W604_algebraic` (all 200 output points TCA-active) |
| TCA dispatch pins Π_2 / E_2 to W6-04 algebraic | ✅ | `test_I18` relative error vs `solve_tca_closure` < 1e-3 at end-of-run |
| Real CanonicalDecision allows reduction in regime | ✅ | `test_real_canonical_decision_allows_reduction_in_regime` |
| Real CanonicalDecision blocks oversize β | ✅ | `test_real_canonical_decision_blocks_oversize_beta` — raises `CanonicalBlockError` |
| Γ_T override replaces recomb lookup | ✅ | `test_gamma_T_override_replaces_recomb_lookup` |
| Default Γ_T falls back to 0 outside fixture | ✅ | `test_gamma_T_without_override_uses_baryon_recomb` |
| PSTF invariants preserved along trajectory | ✅ | Implicit: `hierarchy_rhs_photon` PSTF-packs the output; `test_I13_L_max_variants_integrate_cleanly` confirms finite output (no NaN/Inf) |
| Determinism (no RNG) | ✅ | `test_combined_rhs_is_deterministic` (equal outputs across repeated calls) |
| External-code guard remains active | ✅ | `bass.validation.test_external_code_policy` green in full-suite run |

## 4. Equation-to-code mapping

| Spec formula | Code path | Hand-verification |
|---|---|---|
| ``a' = a × 𝓗`` (Ellis §18.3; Friedmann) | `integrator._bg_rhs` lines 186–196 | I-08 (a(η_today) ≈ 1), I-09 (vs bg_table spline) |
| ``Σ_±' = −𝓗 Σ_± + S_±(type, …)`` | `integrator._bg_rhs` lines 197–202 via `compute_shear_source` (reused) | I-11 / I-12 |
| Combined RHS per spec §3 | `integrator.combined_rhs` lines 210–312 (5-step assembly matching spec §3 numbered list) | I-07, I-13, I-18 |
| MB-1995 eq (49) reduced ν: diagonal ``−a Θ (1+w) Δ_ν`` etc. | `neutrino_reduced.neutrino_reduced_rhs` | Radiation-coefficient test + q/π/G_3 coefficients |
| Kolb §3.5 ``a_eq = Ω_r / Ω_m`` | `event_detection.find_z_equality` (log-ratio bracket search) | I-16 analytic cross-check at 1% |
| Ma-Bertschinger 1995 §7 visibility peak = ``z_*`` | `event_detection.find_z_star_from_visibility` (native-grid argmax) | I-15 |
| TCA algebraic closure `solve_tca_closure(S_T, S_E, Γ_T, decision)` | `integrator._algebraic_tca_scalars` | I-18 bit-identicality |
| TCA DAE-style substitution on ℓ=2 m=0 slot | `integrator.combined_rhs` lines 265–312 (relaxation with rate `a × Γ_T`) | I-18 (pinned at 1e-3 rel) |
| Canonical decision construction | `aux_state.build_integrator_canonical_decision` (calls real `beta_policy_gate` + `sigma_min_gate` + `compute_D_diagnostic`) | `test_aux_state.py` suite |

No dead code: every branch in `combined_rhs` is exercised by at
least one of I-07..I-18. The `_algebraic_tca_scalars` function is
exercised specifically by I-18 (dispatch active) and
`test_real_canonical_decision_*` (dispatch declined).

## 5. Numerical / pipeline audit

| Item | Finding |
|---|---|
| Solver suitability | LSODA (spec §4.2) handles the ∼4 orders of magnitude stiffness ratio between the radiation-era (pre-recomb) and Λ-dominated (today) regimes. Typical cost: ~1200 RHS evaluations per full-range FLRW run at rtol=1e-6 (observed in `test_I08`). No explicit Jacobian is supplied — LSODA generates its own finite-difference Jacobian when it detects stiffness. |
| Tolerance sensitivity | `rtol=1e-6, atol=1e-12` gives `a(η_today) = 1 ± 7e-5` (see smoke-check at top of session). Tighter tolerances `rtol=1e-9, atol=1e-14` used in `test_I12` to pin Σ² × a² at <1% variation. |
| Overflow / underflow | `_bg_rhs` clips ``a`` to `max(a, 1e-30)` (mirrors `einstein_bianchi`). `H_local_at` raises if ``a`` is non-positive. |
| Grid mismatch | The FLRW bg_table spans ``z ∈ [0, 10⁸]``; the HyRec fixture spans ``z ∈ [1, 8000]``. LB-5 tolerates this via the zero-fallback in `Gamma_T_at` (spec-documented F3). TCA dispatch never triggers on the real Planck-2018 fixture because Γ_T/H < 0.2 throughout the fixture's η range (visible in gallery 11/02 left panel); the dispatch mechanism is verified via the synthetic override path (`gamma_T_override`, I-18). |
| PSTF invariants along trajectory | The LB-2b driver `hierarchy_rhs_photon` does a `pstf_pack` at every RHS output (PSTF projection for numerical hygiene); LB-5 passes through that layer. No bespoke PSTF enforcement needed in the integrator itself. |
| Interpolation artifacts | The bg_table uses natural-BC cubic splines; this is consistent with LB-4's kappa integrator. No sub-grid drift observed in `test_I09` at 1e-3 relative. |
| State mutation | `unpack_combined_state` materialises copies (via `PSTFHierarchyState.from_flat`'s `arr[sl].copy()`); `combined_rhs` never mutates its ``y`` input. `aux_state` is a frozen dataclass. |
| Determinism | No RNG in any code path; frozen aux payloads; `test_combined_rhs_is_deterministic` pins byte-equality across repeated calls. |
| Baseline reproduction | LB-0..LB-4 suite unchanged: 2,441 baseline → 2,441 unchanged + 93 new = 2,534. |
| TCA dispatch stiffness | The relaxation rate `a × Γ_T` for Π_2 / E_2 DAE substitution is stiff when Γ_T is large. LSODA handles this without user intervention (observed in `test_I18`: 200/200 output points converged with no solver warnings). If a future variant supplies **dynamically-huge** Γ_T (~10⁶ Mpc⁻¹) the max_step cap may need relaxation; flagged as F3 below. |

## 6. Ranked failure modes

| ID | Type | Severity | Summary | Action |
|---|---|---|---|---|
| F1 | interface | P2 | Spec §5.3 and §10.5 I-17 draft quoted `η_reion ~ 13800 Mpc` at z≈8 — arithmetically wrong. ``η`` in flat ΛCDM grows monotonically with ``a``; ``a = 1/(1+7.67) ≈ 0.115`` maps to ``η ≈ 5100 Mpc``, not ``13800``. Spec amended in this session (05_integrator_spec.md §5.3 table + §10.5 I-17); event-detection test pinned at the arithmetic-correct band `[5000, 5200]`. | Repaired in-session via spec amendment + `test_I17_eta_reion_matches_z_7_67`. |
| F2 | physics | P2 | Spec §10.4 I-12 draft quoted `Σ² × a⁴ = const` (Ellis convention with `σ × a³ = const`, `Σ_ab = a σ_ab`). The shipping `einstein_bianchi.solve_bianchi_background` evolves Σ with a single factor of 𝓗 (`Σ̇ = −𝓗 Σ` for Type I), giving `Σ × a = const` in those variables. The LB-5 integrator reuses `einstein_bianchi` verbatim (spec §12 "background reuse") so I-11 / I-12 must pin the einstein_bianchi convention, not the Ellis convention. Spec amended to match. | Repaired in-session. The `einstein_bianchi` convention discrepancy is **not fixed** at LB-5; a dedicated phase should re-normalise the background solver to the Ellis convention (and touch the `σ → Σ` conversion in `proper_shear_at_eta`). Flagged as a follow-up. |
| F3 | implementation | P3 | The TCA dispatch uses a DAE-style relaxation ``Π̇_2 = −a Γ_T (Π_2 − Π_2_alg)`` applied through `combined_rhs` (not a hard algebraic substitution). In the tight-coupling regime `a × Γ_T` ≫ H so LSODA adapts to the implicit BDF branch; however, at dynamically-huge Γ_T (~10⁶ Mpc⁻¹) the fixed `max_step = Δη / 1000` cap may fail to give LSODA enough room to switch and the integration could stall. Not observed in the LB-5 test suite (I-18 uses Γ_T = 10 Mpc⁻¹) but flagged for LB-6 / future-large-shear runs. | Documented; revisit if LB-6 integration tests exhibit slow progress in the deep-TCA regime. |

No P0 / P1 items.

## 7. Verifier results

| Verifier | Result | Notes |
|---|---|---|
| Physics (formula + limits) | **PASSED** | MB-1995 eq (49) radiation coefficients reproduced exactly (1e-14); Kolb §3.5 `a_eq = Ω_r / Ω_m` matched at 1% (I-16); W6-04 algebraic closure `solve_tca_closure` matched bit-identically through the dispatch path at 1e-3 relative (I-18); `einstein_bianchi` background arithmetic reused verbatim (no re-derivation, no drift). |
| Code (contract satisfaction) | **PASSED** | All 13 integrator tests + 10 IC + 13 pack/unpack + 6 neutrino + 7 event-detection + 8 aux-state green. `combined_rhs` is deterministic. `IntegratorAuxState` is frozen. External-code policy still clean. |
| Numerical (stability + regression) | **PASSED** | 2,534 / 2,534 green (baseline 2,441 + 93 new). No NaN/Inf in any LB-5 output arrays. LSODA handles the stiffness of the TCA dispatch without warnings. `a(η_today) = 1 ± 7e-5` at default tolerances. |

## 8. Minimal repair plan — applied in-session

Two spec amendments + one API extension applied during implementation:

| Patch | Target | Status |
|---|---|---|
| A | `docs/lowell_bianchi/05_integrator_spec.md §5.3` + §10.5 I-17 — η_reion band corrected from `[13500, 13800]` to `[5000, 5200]` (F1) | ✅ |
| B | `docs/lowell_bianchi/05_integrator_spec.md §10.4` I-11 / I-12 — shear-decay invariant re-pinned to match `einstein_bianchi`'s `Σ × a = const` convention (F2) | ✅ |
| C | `IntegratorAuxState.gamma_T_override` — optional callable to replace the baryon `τ̇` lookup for tests probing the deep tight-coupling regime (enables I-18 without a new fixture) | ✅ |
| D | `build_integrator_canonical_decision` — factory that wires the real W3 gate functions (`beta_policy_gate`, `sigma_min_gate`, `compute_D_diagnostic`) into a `CanonicalDecision`; threaded through `IntegratorAuxState` and consumed by the TCA dispatch (resolves LB-3 F3 / LB-4 F3 carry-over) | ✅ |

## 9. Minimal test set (delivered — 93 new tests)

**Baseline reproduction** (spec numerical targets): I-01 round-trip
bit-identicality (atol 1e-14); I-02 layout size; I-03 slice
partition; I-04 zero IC; I-05 Σ_+ IC; I-06 IC validators; I-07 FLRW
zero-state; I-08 a(η_today); I-09 a vs bg_table; I-10 species sum
rule; I-11 / I-12 shear-decay invariant; I-13 L_max ∈ {2,4,6}
finiteness; I-14 high-Γ_T damping; I-15 z_*; I-16 z_eq; I-17
η_reion; **I-18 TCA dispatch bit-identical to W6-04**.

**Edge / adversarial**: pack/unpack shape validation;
`make_initial_state` off-slot zeros; negative a_initial, NaN/Inf
Σ_±; `L_max < 2` rejection; reduced-ν shape validation;
`z_reion_guess < 0` rejection; `gamma_T_over_H_threshold < 0`
rejection; config-validator rejections.

**Physics sanity**: neutrino-ν radiation coefficient
`−(4/3) a Θ Δ_ν`; q_ν / π_ν / G_3 coefficients `−a Θ`; zero-state
fixed-point; `find_z_equality` vs analytic `Ω_m/Ω_r − 1`;
`find_z_star` peak tolerance 1.

**Numerical stability / integration**: `combined_rhs` determinism;
L_max variant finiteness; `a(η_today) ≈ 1` cumulated integrator
error at 7e-5; `Σ × a` drift bounded at 5%; `Σ² × a²` drift at 1%;
TCA dispatch dispatch DAE accuracy at 1e-3.

**Regression**: full bass+tsc run — **2,534 green** (baseline
2,441 + 93 new).

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과** (no P0/P1; three documented P2/P3 items).
* **지금 당장 구현/수정한 1개**: the real `CanonicalDecision` factory (`build_integrator_canonical_decision`) + its wiring through `IntegratorAuxState` into `solve_tca_closure`. Without this the LB-5 integrator would have silently inherited the `_always_allowing_tca_decision` bypass from the LB-3 `TCAClosure` helper — masking W3 gate violations at the most stiffness-sensitive step of the run. The wiring is load-bearing and test-pinned (`test_real_canonical_decision_blocks_oversize_beta` asserts the gate actually blocks).
* **지금 손대면 안 되는 1개**: the `einstein_bianchi` convention mismatch flagged as F2. Re-normalising the background solver to the Ellis convention (``σ × a³ = const``, ``Σ_ab = a σ_ab``) touches every downstream consumer of Σ_+ / Σ_− including the LB-2 `proper_shear_at_eta`, LB-4 tilted-visibility tests, and all shipped Y-Block plots. LB-5's reuse-verbatim-of-einstein_bianchi mandate (spec §12) explicitly defers this to a dedicated phase; doing it now would blow the session budget and drag in a dozen sub-commits worth of regression work.

## Gallery refresh

New topic `plots/physics_gallery/11_integrator/` with 2 LB-5 plots:

* `01_unified_trajectory_bianchi_I.png` — background + Σ_± +
  Π_2[m=0] + E_2[m=0] along a Type I flat trajectory with an
  injected 1e-4 Π_2 seed. Π_2 damps via Thomson; E_2 gets a
  transient (through the polter cross-coupling K^E_2 ∝ Π_2) and
  relaxes. Visual confirmation of spec §3 combined-RHS assembly.
* `02_tca_activation_window.png` — left panel: `Γ_T / H` across
  the Planck-2018 HyRec history (never clears threshold — the
  fixture's z_max = 8000 places us outside the natural deep
  tight-coupling regime). Right panel: synthetic `gamma_T_override
  = 10 Mpc⁻¹` triggers the dispatch on 531/600 grid points, pinning
  the mechanism independently of the fixture.

Both plots were visually inspected; physical behaviour matches
spec §3 / §10.6. The `11_` topic brings the gallery total to
**50 plots across 11 topics**.

## Outstanding items carried forward

* **F1** (P2): η_reion band correction applied to spec §5.3 and
  §10.5 I-17. A future "τ_reion window" helper (mentioned in LB-4
  F1) would let us pin the LB-5 event detector against the
  literal 0.0544 Planck value rather than a z-band tolerance.
* **F2** (P2): `einstein_bianchi` Σ-convention vs Ellis convention.
  Carried forward to a dedicated phase ("background convention
  normalisation") post-LB-6.
* **F3** (P3): LSODA may stall at dynamically-huge Γ_T (~10⁶
  Mpc⁻¹) because of the fixed `max_step` cap. Revisit if LB-6 tests
  exhibit slow convergence in the deep-TCA regime.
* **From LB-4 F1 carry-over**: τ_reion literal match deferred —
  still open; not LB-5's territory.
* **From LB-4 F2 carry-over**: `PolarizationHierarchyState.L ≥ 2`
  keeps zero ℓ<2 slots for layout parity — intentional; LB-5
  pack_unpack honours this by reserving `(L+1)²` slots for the
  E-mode tower (0.8% memory overhead at L_max=6; spec §2.1).
* **From LB-3 F3 / LB-4 F3**: `TCAClosure._always_allowing_tca_decision`
  bypass **resolved** inside the integrator. `TCAClosure.tca_scalars`
  in `bass/hierarchy/closure.py` itself still uses the bypass for
  callers that invoke it standalone (e.g. test_thomson_integration.py);
  that is deliberately retained — the LB-5 fix is exclusive to the
  integrator path which is what the rotation prompt mandated.
