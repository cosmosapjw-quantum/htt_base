# AUDIT — Phase post-LB-1 + tilted-visibility-spec + physics-gallery

**Date**: 2026-04-18
**Phase**: LB-0 (external-code guard) + LB-1 (species backgrounds) +
LB-4 spec rotation (lowell §11.3 tilted visibility) + physics plot gallery
**Baseline commit**: `701f4c1` (pre-audit)
**Baseline test count**: 2,136 passing
**Post-audit test count**: 2,141 passing
**Verdict**: **부분 통과** (critical-severity drift/tautology fixed in-session)

---

## 1. Audit target reconstruction

| Layer | Artifact | Role |
|---|---|---|
| Physics/math source | Kolb §3.3-3.5, §5.5; Ellis §5.3; lowell §11.1-3 | Textbook truth |
| Constants SSOT | `htt.htt.core.ssot.C` | Planck-2018 parameter dict |
| Species implementation | `bass/species/*` | ρ_s(η), H, η, T_m |
| Legacy Bianchi solver | `bass/background/einstein_bianchi.py` | ODE-based shear history |
| Guard | `bass/validation/test_external_code_policy.py` | LB-0 §11 enforcement |
| Diagnostic | `scripts/make_physics_gallery.py` + 37 PNGs | Gallery reconstruction |

## 2. Contract / interface table (excerpt)

See audit prompt in session transcript; key invariants:

* `Σ_s Ω_{s,0} = 1` exactly (flat closure)
* `dot_rho(η)` = proper-time ρ̇ = −Θ(1+w)ρ (ABC docstring verified matches)
* `friedmann_residual(η)` contract: must actually probe `bg_table.H_mpc`

## 3–5. Audit ledger summary

Full ledger: see session transcript §3–§5.

## 6. Ranked failure modes (found)

| ID | Type | Severity | Summary |
|---|---|---|---|
| **F1** | impl/physics | **P1** | `einstein_bianchi._PLANCK18` hardcoded Ω_m=0.3138 Ω_Λ=0.6862, sum=1.000092 (non-flat). Drift vs species SSOT (Ω_m=0.3153) |
| **F2** | testing/numerical | **P1** | `friedmann_residual(η)` default mode tautological — evaluated both sides analytically from constants; doesn't probe `bg_table.H_mpc`. Verified by array tamper test |
| **F3** | impl | **P2** | Gallery `_bianchi_solve` hardcoded the same non-flat Ω values |
| **F4** | doc | **P2** | Spec §8 T-24 claims `T_m(z=150) ≈ T_γ` within 1%; HyRec-2 shows 24% off at z=150, correct value is z=800 |
| **F5** | impl | **P3** | LB-0 guard regex misses `import X; import Y` semicolon chains |
| **F6** | testing | **P3** | BaryonBackground domain errors raise from deep inside RecombinationInterp |
| **F7** | doc | **P3** | `friedmann_residual` docstring didn't document the three modes |

## 7. Verifier results

| Verifier | Pre-audit | Post-audit |
|---|---|---|
| Physics (Kolb/Ellis limits) | PARTIAL (F1 flat-closure break) | PASSED |
| Code (contract satisfaction) | PARTIAL (F2 tautology, F1 drift) | PASSED |
| Numerical (baseline + stability) | PARTIAL | PASSED |

## 8. Minimal repair plan — applied in-session

| Patch | Target | Status |
|---|---|---|
| A | `einstein_bianchi._PLANCK18` now reads from `default_constants()` via `_planck18_from_species_ssot()` helper | ✅ |
| B | `friedmann_residual(η)` default `source="table"` actually queries `bg.interp_calH/interp_a`; `source="analytic"` kept as explicit self-check | ✅ |
| C | Added `bass/background/test_planck18_ssot.py` invariant test (3 assertions); spec §8 T-24 footnote added documenting z=150 → z=800 shift | ✅ |

## 9. Minimal test set added

| ID | Test | Pass criterion |
|---|---|---|
| T18 | `test_T18_friedmann_residual_zero` (retained) | on-grid, explicit H, |res| < 1e-10 |
| T18b | `test_T18b_friedmann_residual_table_probes_bg` (new) | injected 10% H error → |res| > 0.1 × ρ_tot |
| T18c | `test_T18c_analytic_mode_is_tautological` (new) | |res| < 1e-12 × ρ_scale under analytic mode |
| T18d | `test_T18d_invalid_source_raises` (new) | `source='bogus'` raises ValueError |
| planck18 | `test_planck18_matches_species_ssot` + 2 siblings (new) | `_PLANCK18` fields == `default_constants()` fields bit-exact |

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **부분 통과**
  (P1 findings F1+F2 fixed in-session; regression 2,141 green)
* **지금 당장 구현/수정한 1개**: F1 `_PLANCK18` SSOT drift — blocked flat-closure in every Bianchi-solver-producing pipeline
* **지금 손대면 안 되는 1개**: F5 LB-0 guard semicolon regex — P3, architectural scope, defer to post-LB-6

## Outstanding items carried forward

* **F5** (P3): document semicolon bypass in guard docstring; add to LB-5 prerequisites
* **F6** (P3): wrap `BaryonBackground.x_e/tau_dot/T_m` with domain-aware ValueError re-raise; roll into LB-4 implementation
* **F7** (P3): close by this commit (added to `friedmann_residual` docstring)

## Gallery refresh

37 PNGs regenerated after Patch A propagated to `_PLANCK18`. Bianchi
shear plots now use the flat-closure constants (Σ Ω = 1 exact), so
the gallery is internally consistent with the species-side plots.
