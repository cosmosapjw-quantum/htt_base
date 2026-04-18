# AUDIT — LB P2/P3 carry-forward cleanup

**Date**: 2026-04-19 (immediately post-LB-6, pre-FB-0.1)
**Purpose**: clear all actionable P2/P3 items documented in
`AUDIT_PHASE_LB1_2026-04-18.md` through
`AUDIT_PHASE_LB6_2026-04-19.md` before Phase FB begins, so the FB
roadmap starts from a clean baseline.
**Baseline commit**: `c72dcba` (FB plan approved, post-LB-6).
**Baseline test count**: 2,558 passing + 1 skipped.
**Post-cleanup test count**: **2,565 passing + 1 skipped** (+7 new
cleanup-regression tests; no existing test regressed).
**Verdict**: **통과** — all items resolved, deferred with
investigation, or scoped into FB explicitly.

---

## 1. Scope — which carry-forwards does this cleanup address?

Scanned every `docs/audits/AUDIT_PHASE_LB*_*.md` for `P2` and `P3`
lines in §6 Failure modes + §Outstanding items. Each item was
triaged as **fix now**, **close with investigation**, or **defer to
FB**.

### Fix now (implemented in this commit)

| Source | ID | Type | Summary | Patch |
|---|---|---|---|---|
| LB-1 | F4 | doc (P2) | Spec §3 line 115 claimed `T_m ∝ a⁻²` onset at z~150; HyRec shows already decoupled there (T_m/T_γ ≈ 0.76). | `docs/lowell_bianchi/01_species_background_spec.md` §3 line 115 corrected to z~800 with post-audit footnote |
| LB-1 | F5 | code (P3) | External-code policy regex missed `import X; import Y` chains — could bypass the guard. | `bass/validation/test_external_code_policy.py::_scan_forbidden_imports` splits on `;` before matching; 3 new parametrised regression snippets added |
| LB-1 | F6 | code (P3) | `BaryonBackground.{x_e, tau_dot, T_m, kappa, visibility}(η)` raised raw `ValueError` mentioning only `z`; η-side caller had to reverse the mapping by hand. | `_query_with_eta_context` helper re-raises with η + z + field-name context; 1 new regression test |
| LB-2b | F2 | code (P2) | `proper_shear_at_eta` nearest-grid-point lookup → ~2 % quantisation error mid-grid. | `hierarchy_rhs.proper_shear_at_eta` uses `scipy.CubicSpline` (cached on tetrad_state); 1 new regression test confirms < 1e-3 rel at mid-grid |
| LB-3 | F2 | doc (P2) | Spec §8 narrative described the pre-LB-3 three-argument signature (`(state, L_ref, L_trunc)`) while the shipping API is two-argument. | `docs/lowell_bianchi/03_closure_truncation_spec.md` §8 realigned to `(state_reference, L_truncated)` with post-audit note |
| LB-4 | F1 | code (P2) | Integrated τ_reion match was deferred behind a "dedicated window integral" stub; LB-6-14 worked around it with an inline trapezoidal. | `BaryonBackground.tau_reion_window(z_lo, z_hi)` helper; LB-6-14 now calls it; 2 new direct tests (Planck match + input validation) |
| LB-6 | F2 | code (P2) | `detect_critical_events` exposed `eta_today` but not the CAMB-convention `eta_star` / `chi_star`; LB-6-09 / LB-6-20 recomputed them by hand. | `event_detection.find_eta_star / find_chi_star` + `detect_critical_events` returns both; LB-6-09 / LB-6-20 now consume the keys directly; 1 new key-set + physics-band regression test |

### Close with investigation (no patch needed)

| Source | ID | Investigation | Resolution |
|---|---|---|---|
| LB-6 | F1 | Prototyped three sub-grid z_* estimators (parabolic 3-pt fit; weighted-moment over top-N; Gaussian `curve_fit`). All three drift to z ~ 1088.5..1088.8 — **further from Planck 1089.94 than the integer argmax (1089.00)**. The skew of `g(z)` (sharper high-z tail than low-z) biases every symmetric fit downward. | Integer-argmax on Δz=1 HyRec fixture is the **correct** oracle. LB-6-08 tolerance (±1.0) was right. F1 closes here — the "sub-grid refinement" item would require a physics-informed asymmetric kernel, which is an FB-7 line-of-sight calibration item, not a LB-cleanup item. |
| LB-1 | F3 | Verified `scripts/make_physics_gallery.py::_bianchi_solve` — docstring reads `"Post-audit: reads Ω values from bass.species.default_constants() so the gallery's Bianchi shear plots use the same cosmology as the species background plots (flat closure Σ Ω = 1 exactly)."` Code implementation matches. | Already repaired in LB-1 post-audit patch (before this cleanup started). F3 closes. |
| LB-1 | F7 | Audit log noted F7 closed by LB-1 commit; verified `friedmann_residual` docstring now documents the three modes. | Already closed. |

### Deferred to FB phase (explicitly scoped into roadmap)

| Source | ID | Reason | FB home |
|---|---|---|---|
| LB-2a | F2 | 3^ell atol in pack/unpack round-trip — intentional; documented; machine-precision already. | No FB target — close as "documented". |
| LB-2a | F3/F4 | `L_MAX_CACHED = 8` docstring + `pstf_pack` silent STF projection — both intentional, already documented. | Cache bump tracked in FB-2.1 risk register. |
| LB-2b | F1 | `test_h25` forward-Euler cross-check — H-22 covers absolute coefficient; H-25 covers integration smoke. | No action; documented trade-off. |
| LB-2b | F3/F4 | Docstring / test-only Doppler operator — LB-4 migrated to real Thomson; resolved. | Already closed. |
| LB-3 | F1 | FreeStreamingClosure per-m lift is exact only at m=0. | **FB-4** (tilted sector revisits off-axis E/B mixing). |
| LB-3 | F3 | TCAClosure standalone `_always_allowing_tca_decision` bypass — LB-5 integrator path threads the real decision; standalone use (tests) keeps the bypass intentionally. | Already resolved where load-bearing. |
| LB-4 | F2 | `PolarizationHierarchyState` 0.8 % memory penalty from L≥2 zero slots. | Intentional design; no FB target. |
| LB-4 | F3 | `TiltedVisibility.__init__` try/except precompute — 2 ms/construction, not a hot path. | Revisit in **FB-4.1** if Layer B moves to inside the integrator loop. |
| LB-5 | F2 | `einstein_bianchi` `Σ × a = const` vs Ellis `Σ² × a⁴ = const`. | **FB-0.1** (next session, plan-locked). |
| LB-5 | F3 | LSODA stiffness at dynamically-huge Γ_T — not observed at LB-6's override regime. | **FB-3 / FB-4** tilted sector will stress-test; revisit then. |
| LB-6 | F3 | LB-6-18 unit-mismatch docstring retires Route B comparison. | **FB-7.1** line-of-sight projection phase. |

---

## 2. Detailed repair log

### LB-1 F4 (doc, P2)

- **File**: `docs/lowell_bianchi/01_species_background_spec.md` §3 line 115
- **Before**: `follows T_γ until Compton decoupling z ~ 150, then T_m ∝ a⁻²`
- **After**: `follows T_γ until Compton decoupling z ~ 800, then T_m ∝ a⁻²; LB-1 F4 post-audit correction — at z=150 the HyRec-2 Planck-2018 fixture shows T_m / T_γ ≈ 0.76, i.e. already in the decoupled regime`

### LB-1 F5 (code, P3)

- **File**: `bass_py/bass/validation/test_external_code_policy.py`
- **Change**: `_scan_forbidden_imports` now splits each line's code portion on `;` before matching; module docstring of `_IMPORT_RE` updated to document the LB-1 F5 repair.
- **New tests**: three parametrised snippets
  - `import os; import camb`
  - `import numpy as np; from camb.symbolic import bar`
  - `    import logging; import classy  # indented chain`

### LB-1 F6 (code, P3)

- **File**: `bass_py/bass/species/baryon.py`
- **Change**: Added `_query_with_eta_context(eta, query_fn, field_name)` helper. All five public methods (`x_e, tau_dot, T_m (via temperature), kappa, visibility`) dispatch through it. Raw `ValueError` from `RecombinationInterp.query_*` is caught and re-raised with:
  ```
  BaryonBackground.{field}(η) out of recomb table range: η ∈ [...] Mpc mapped to z ∈ [...]. Underlying error: ...
  ```
- **New test**: `test_LB1_F6_out_of_range_error_carries_eta_context` covers all five methods.

### LB-2b F2 (code, P2)

- **File**: `bass_py/bass/hierarchy/hierarchy_rhs.py`
- **Change**: `proper_shear_at_eta` uses a lazily-built `scipy.interpolate.CubicSpline` (`axis=0`, `natural` BC) cached on the tetrad_state instance via `_sigma_spline_cache`. Endpoint clamping preserves the prior nearest-neighbour extremal behaviour. Docstring updated with the LB-2b F2 note.
- **New test**: `test_LB2b_F2_proper_shear_spline_better_than_nearest_neighbour` constructs a fixture with a linearly-varying Σ_ab across 50 grid points and checks mid-grid recovery at < 1e-3 rel (prior nearest-neighbour would produce O(1) relative error halfway between points).

### LB-3 F2 (doc, P2)

- **File**: `docs/lowell_bianchi/03_closure_truncation_spec.md` §8
- **Change**: Code block in §8 updated from the three-argument `(hierarchy_state, L_reference, L_truncated)` form to the shipped `(state_reference, L_truncated, *, closure=None)` form, with a post-audit footnote explaining the pre-LB-3 rename.

### LB-4 F1 (code, P2)

- **File**: `bass_py/bass/species/baryon.py`
- **Added**: `BaryonBackground.tau_reion_window(z_lo=0.0, z_hi=30.0, *, n_samples=4096) -> float`. Returns the integrated optical depth `∫ τ̇(η) dη` over the reionization window, using `np.trapezoid` on a linear η-grid between `η(z_hi)` and `η(z_lo)`. Validates `0 ≤ z_lo < z_hi`.
- **Consumer change**: `bass/integration/test_lowell_bianchi.py::TestLBThermalHistory::test_LB_6_14_tau_reion` now calls the helper instead of inlining the trapezoid.
- **New tests**: `test_LB4_F1_tau_reion_window_matches_planck2018` (0.0514 ≤ τ ≤ 0.0574 band) + `test_LB4_F1_tau_reion_window_validates_range` (inverted / negative bounds raise).

### LB-6 F2 (code, P2)

- **File**: `bass_py/bass/hierarchy/event_detection.py`
- **Added**: `find_eta_star(species, bg_table, *, z_star=None) -> float` returning `η(z_*)` (conformal time at LSS, ~280 Mpc) and `find_chi_star(species, bg_table, *, z_star=None) -> float` returning `η_today − η(z_*)` (comoving distance to LSS, CAMB convention, ~13873 Mpc).
- **Change**: `detect_critical_events` now includes both keys. LB-6-09 / LB-6-20 simplified to consume `result.critical_events['chi_star']` directly.
- **Test updates**: `test_detect_critical_events_returns_all_four` → `test_detect_critical_events_returns_all_keys` (renamed, extended with key-set + physics-band assertions + `eta_star + chi_star = eta_today` round-trip). `test_integrator.py::test_integrator_publishes_critical_events` updated key-set.

### LB-6 F1 (investigation, no patch)

Ran three sub-grid z_* estimators against the shipped HyRec fixture
(z ∈ [900, 1300], Δz = 1):

| Method | Result | Distance to Planck 1089.94 |
|---|---|---|
| integer argmax of g | **1089.00** | **0.94** |
| parabolic fit on 3 points around argmax | 1088.79 | 1.15 |
| weighted-moment (top-10 pts) | 1088.43 | 1.51 |
| Gaussian `curve_fit` (n=10 window) | 1088.74 | 1.20 |
| Gaussian `curve_fit` (n=20) | 1088.57 | 1.37 |
| Gaussian `curve_fit` (n=40) | 1087.94 | 2.00 |

All sub-grid methods bias downward because `g(z)` is asymmetric —
the recombination side (high z) is steeper than the Silk-damping
side (low z). The integer argmax is closer to Planck than any
symmetric fit. F1 closes — the sub-grid item belongs in the FB-7
line-of-sight calibration phase where a physics-informed
asymmetric kernel can be developed with C_ℓ matching as the
criterion.

---

## 3. Regression summary

| Suite | Pre-cleanup | Post-cleanup | Δ |
|---|---|---|---|
| `bass/` + `tsc/` full | 2,558 passed + 1 skipped | **2,565 passed + 1 skipped** | **+7 new** |

New tests (all green):

- `bass/validation/test_external_code_policy.py` — 3 parametrised semicolon-chain snippets
- `bass/species/test_baryon.py::test_LB1_F6_out_of_range_error_carries_eta_context`
- `bass/species/test_baryon.py::test_LB4_F1_tau_reion_window_matches_planck2018`
- `bass/species/test_baryon.py::test_LB4_F1_tau_reion_window_validates_range`
- `bass/hierarchy/test_hierarchy_rhs.py::test_LB2b_F2_proper_shear_spline_better_than_nearest_neighbour`

Modified tests (key-set realignment after LB-6 F2 key additions):

- `bass/hierarchy/test_event_detection.py::test_detect_critical_events_returns_all_keys`
- `bass/hierarchy/test_integrator.py::test_integrator_publishes_critical_events`
- `bass/integration/test_lowell_bianchi.py::test_LB_6_09_eta_star_comoving_distance_to_LSS` (simplified)
- `bass/integration/test_lowell_bianchi.py::test_LB_6_20_eta_star_vs_camb` (simplified)
- `bass/integration/test_lowell_bianchi.py::test_LB_6_14_tau_reion` (delegates to helper)

---

## 4. Verifier results

| Verifier | Result |
|---|---|
| Physics | **PASSED** — τ_reion integrates to 0.0541 (Planck band); chi_star = 13867 Mpc (CAMB ±20); spline reproduces linear Σ_ab mid-grid at 1e-3; no physics target drifted |
| Code | **PASSED** — all seven new tests green; no existing test regressed; LB-6 integration tests simplified through new helpers |
| Numerical | **PASSED** — 2,565 / 2,566 green (1 deferred LB-6-11 z_drag remains skipped per prior spec amendment); wall time ~66 s unchanged |

---

## 5. Carry-forward tally (post-cleanup)

After this cleanup, the P2/P3 ledger reads:

- **Closed in this session**: LB-1 F4/F5/F6; LB-2b F2; LB-3 F2; LB-4 F1; LB-6 F1 (investigated); LB-6 F2.
- **Already closed in earlier sessions** (verified during this cleanup): LB-1 F3/F7; LB-2b F3/F4; LB-3 F3 (load-bearing path); LB-5 F1.
- **Intentional / documented, no repair target**: LB-2a F2/F3/F4; LB-2b F1; LB-4 F2; LB-6 F3.
- **FB-scoped (deferred with explicit FB home)**: LB-3 F1 → FB-4; LB-4 F3 → FB-4.1; LB-5 F2 → **FB-0.1** (next session); LB-5 F3 → FB-3/4.

---

## 6. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과**. No P0/P1 surfaced during cleanup. Seven P2/P3 items patched; one investigated and closed with rationale; remaining items either intentional or scoped into FB.
* **지금 당장 구현/수정한 1개**: the `tau_reion_window` helper (LB-4 F1). It consolidates four lines of inline trapezoidal integration from LB-6-14 into a first-class `BaryonBackground` method, with input validation and n-sample control. Any future τ-window regression (e.g., a Helium-reion comparison at z ∈ [3, 4]) now has a one-line call site rather than a copy-paste.
* **지금 손대면 안 되는 1개**: LB-6 F1 "sub-grid z_* detector". Three symmetric fit methods prototyped — all move us further from Planck 1089.94 than the integer argmax. Correcting this requires a physics-informed asymmetric kernel (the high-z recombination edge is steeper than the low-z Silk-damping side), which is an FB-7 line-of-sight calibration item, not LB-cleanup. The current ±1.0 tolerance is the honest width.

---

## 7. Next session

FB-0.1 — Ellis Σ-convention flip — remains the next session (prompt unchanged in `NEXT_SESSION_PROMPT.md §2`). This cleanup commit does not alter the FB roadmap; it only raises the starting baseline from 2,558 to 2,565 tests and removes 7 items from the carry-forward ledger before FB starts.
