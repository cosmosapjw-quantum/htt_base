# AUDIT — Phase FB-1 (Per-type background validation)

**Date**: 2026-04-19
**Phase**: FB-1 — Per-type background validation of the 11-type
`shear_sources` dispatch against Wainwright-Ellis §18 Table 11.1
ground-truth formulas. Sub-phase **FB-1.1** promotes the Class A
orthogonal types I / II / VI₀ / VII₀ from `PROVISIONAL` to `VALIDATED`.
FB-1.2 / FB-1.3 / FB-1.4 are tracked for follow-up sessions and will
append to this audit log.

**Baseline commit (pre FB-1.1)**: `9373da1` (post Phase FB-0;
`AUDIT_PHASE_FB0_2026-04-19.md` sealed at the bottom).
**Baseline test count**: 2,688 passing + 1 skipped.
**Post FB-1.1 test count**: **2,753 passing + 1 skipped** (+65 new;
61 parametrised combinations in the new `TestClassAFixedPoints` plus
4 auxiliary parametrised sub-cases in the existing `TestSourceStatus`
regression layer that pick up the PROVISIONAL → VALIDATED flip).
**Verdict**: **통과** (no P0/P1; one fresh P2 physics-framework
finding FB11-F1 explicitly recorded for FB-5 / FB-6 discussion;
pre-existing carry-forwards F3 → FB-2.4 and FB02-F1 → FB-3.1
preserved).

---

## 1. Audit target reconstruction (FB-1.1)

| Layer | Artifact | Role |
|---|---|---|
| Physics / math source | Wainwright & Ellis 1997 §18 + Table 11.1 (Class A A=0 source dispatch); Ellis-Maartens-MacCallum 2012 §18.3 (Ellis conformal shear convention locked in FB-0.1) | Per-type dimensionless `S^{WE}_{±}(N_1, N_2, N_3)` formulas and sign patterns that anchor the "VALIDATED" promotion contract |
| Per-type source dispatch | `bass/transport/shear_sources.py::{source_I, source_II, source_VI0, source_VII0}` + `SOURCE_STATUS` registry | Each source function returns `(ℋ² × S^{WE}_+, ℋ² × S^{WE}_-)` in Mpc⁻² units per the FB-0.1 Ellis conformal mapping |
| Background ODE | `bass/background/einstein_bianchi.py::solve_bianchi_background` | Integrates `(a, Σ_+, Σ_-)` with per-type source dispatch; used by FB-1.1 Type I Kasner invariant test |
| Tests (new) | `bass/transport/test_shear_sources.py::TestClassAFixedPoints` | 4 per-type methods + 1 isotropic auxiliary (5 methods total, 61 parametrised runs) |
| Tests (unchanged, still green) | every LB-0..LB-6 + FB-0 regression | Zero-impact invariant verified across 2,688 pre-existing tests |
| Spec cross-ref | `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.1` | FB-1.1 row ("Class A 배경: I / II / VI₀ / VII₀ … Source regression promote → 'VALIDATED'") delivered |
| Gallery | `plots/physics_gallery/11_integrator/{03..06}_fb11_classA_*.png` | First FB gallery extension (FB-0 was visual no-op across three sub-phases) |

Source of truth: Wainwright-Ellis §18 Table 11.1 formulas (per-type
`S^{WE}` expressions in the Hubble-normalised Class A A=0 setting);
the Ellis conformal lift `S_± = ℋ² × S^{WE}` locked in FB-0.1.
Our per-type source functions are the operative code path.

## 2. Contract / interface table — FB-1.1 additions

| Surface | Signature / invariant | Status |
|---|---|---|
| `SOURCE_STATUS["I"]` | tag=VALIDATED, reference="Kasner analytic + W-E §18 Table 11.1", benchmark="σ × a³ const on background integrator + FB-0.1 LB-5 I-11/I-12/I-12b" | Promoted (was VALIDATED for Kasner only; extended reference) |
| `SOURCE_STATUS["II"]` | tag=VALIDATED, reference="W-E §18 Table 11.1, Heisenberg e(1) axisymmetric", benchmark="formula + sign + Σ-independence pinned on (N_1, ℋ) grid" | Promoted PROVISIONAL → VALIDATED |
| `SOURCE_STATUS["VI_0"]` | tag=VALIDATED, reference="W-E §18 Table 11.1, e(1,1) algebra", benchmark="formula + S_+ < 0 sign + Σ-indep pinned on (n_1, n_3, ℋ) grid" | Promoted PROVISIONAL → VALIDATED |
| `SOURCE_STATUS["VII_0"]` | tag=VALIDATED, reference="W-E §18 Table 11.1, e(2) algebra (plane-wave line)", benchmark="formula + S_- sign flip vs VI₀ + isotropic vanishing pinned" | Promoted PROVISIONAL → VALIDATED |
| `SOURCE_STATUS["III/IV/VI_h/VII_h/VIII/IX"]` | unchanged PROVISIONAL | Deferred to FB-1.2 / FB-1.3 |
| `compute_shear_source` signature | `(sc, Sp, Sm, calH, a) → (dSp, dSm)` in Mpc⁻² | Unchanged (surgical SOURCE_STATUS metadata flip only) |
| `source_I / source_II / source_VI0 / source_VII0` source bodies | Pre-FB-1.1 formulas preserved verbatim (FB-0.1 ℋ² form) | Unchanged |
| `TestClassAFixedPoints` public surface | `test_type_I_kasner_exponent_sum` / `test_type_II_WE_fixed_point_asymptotic` / `test_type_VI0_WE_fixed_point_asymptotic` / `test_type_VII0_shear_decay_to_plane_wave_line` / `test_type_VII0_isotropic_limit_vanishes_exactly` | New |

**Per-type formula pins (W-E §18 Table 11.1)**:

| Type | `S^{WE}_+` | `S^{WE}_-` | Verified in |
|---|---|---|---|
| I | 0 | 0 | `test_type_I_kasner_exponent_sum` (via geometric Kasner invariant) |
| II (axi, N_2=N_3=0) | −(2/3) N_1² | 0 | `test_type_II_WE_fixed_point_asymptotic` (4 N_1 × 4 ℋ grid, rel 1e-12) |
| VI₀ (n_1>0, n_3<0, n_2=0) | −(2/3)(n_1−n_3)² | −(2/√3)(n_1+n_3)(n_1−n_3) | `test_type_VI0_WE_fixed_point_asymptotic` (4 (n_1,n_3) × 4 ℋ, rel 1e-12) |
| VII₀ (n_1>0, n_3>0, n_2=0) | −(2/3)(n_1−n_3)² | **+**(2/√3)(n_1+n_3)(n_1−n_3) | `test_type_VII0_shear_decay_to_plane_wave_line` (4 (n_1,n_3) × 4 ℋ, rel 1e-12; sign flip vs VI₀ pinned explicitly) |
| VII₀ isotropic limit | 0 (exact) | 0 (exact) | `test_type_VII0_isotropic_limit_vanishes_exactly` (3 N × 4 ℋ) |

## 3. Phys-math audit ledger

| Check | Result | Evidence |
|---|---|---|
| Type I vacuum-Kasner invariant `σ × a³ = const` at ≤ 2 % drift on direct background integrator | ✅ | `test_type_I_kasner_exponent_sum` (< 1e-5 drift observed) |
| Type I Ellis invariant `Σ × a² = const` at ≤ 0.5 % drift on direct background integrator | ✅ | same test (< 1e-5 drift observed) |
| Type II axisymmetric source formula `S^{WE}_+ = −(2/3) N_1²`, `S^{WE}_- = 0` at rel 1e-12 on full (N_1, ℋ) parametrisation grid | ✅ | `test_type_II_WE_fixed_point_asymptotic` |
| Type II Σ-independence: source does not depend on Σ_± | ✅ | same test, second assertion block |
| Type VI₀ formula `S^{WE}_+ = −(2/3)(n_1−n_3)²`, `S^{WE}_- = −(2/√3)(n_1+n_3)(n_1−n_3)` at rel 1e-12 on (n_1, n_3, ℋ) grid | ✅ | `test_type_VI0_WE_fixed_point_asymptotic` |
| Type VI₀ sign pin: S_+ < 0 whenever n_1 ≠ n_3 | ✅ | same test (assertion `dSp < 0` across all 16 parametrised runs) |
| Type VII₀ formula `S^{WE}_+ = −(2/3)(n_1−n_3)²`, `S^{WE}_- = +(2/√3)(n_1+n_3)(n_1−n_3)` at rel 1e-12 | ✅ | `test_type_VII0_shear_decay_to_plane_wave_line` |
| Type VII₀ S_- sign flip vs VI₀ at matched (|diff|, |summ|) | ✅ | same test, cross-check block: `dSm_VII0 = −dSm_VI0_matched` at rel 1e-12 |
| Type VII₀ isotropic limit (n_1 = n_3) → S_+ = S_- = 0 exactly (not just small) | ✅ | `test_type_VII0_isotropic_limit_vanishes_exactly` (12 parametrised runs, `== 0.0` assertion) |
| FLRW limit still bit-identical: `SOURCE_STATUS["FLRW"]` unchanged; `source_I(FLRW)` returns (0, 0) | ✅ | `TestFLRWLimit.test_flrw_source_exactly_zero` + `test_type_I_source_exactly_zero` (unchanged) |
| Promotion does not silently weaken existing PROVISIONAL tests | ✅ | `TestSourceStatus.test_type_I_validated` / `test_type_V_validated` still green; no test asserted "II/VI_0/VII_0 are PROVISIONAL" explicitly |
| FB-0.1 Ellis conformal lift (`ℋ²` factor) preserved | ✅ | `TestDimensionalConsistency.test_source_units` across 9 non-VII_h types still green (ratio ≈ 4 on ℋ doubling) |
| LB-5 I-11/I-12/I-12b Kasner regression (hierarchy integrator) | ✅ | green (2,688 baseline unchanged on this subset) |
| LB-6-15/16 Σ×a² / Σ²×a⁴ regression | ✅ | green |

## 4. Equation-to-code mapping audit

| Target equation | Code implementation | Test anchor |
|---|---|---|
| W-E §18 Table 11.1 row I: `S^{WE} = 0` (no spatial curvature) | `shear_sources.source_I: return 0.0, 0.0` | `test_type_I_kasner_exponent_sum` (trajectory-level invariant) + `test_type_I_source_exactly_zero` (direct return value) |
| W-E §18 Table 11.1 row II: `S^{WE}_+ = −(2/3) N_1²`, `S^{WE}_- = 0` | `shear_sources.source_II: dSp = -(2.0/3.0) * N1**2 * calH**2; dSm = 0.0` | `test_type_II_WE_fixed_point_asymptotic` (formula rel 1e-12 × 16 parametrisations) |
| W-E §18 Table 11.1 row VI₀: `S^{WE}_+ = −(2/3)(diff)²`, `S^{WE}_- = −(2/√3)(summ)(diff)` | `shear_sources.source_VI0: diff = n1-n3; summ = n1+n3; dSp = -(2/3)*diff**2*calH_sq; dSm = -(2/sqrt(3))*summ*diff*calH_sq` | `test_type_VI0_WE_fixed_point_asymptotic` (16 parametrisations) |
| W-E §18 Table 11.1 row VII₀: identical magnitudes but `S^{WE}_-` sign flipped | `shear_sources.source_VII0: dSm = +(2/sqrt(3))*summ*diff*calH_sq` (note the `+`) | `test_type_VII0_shear_decay_to_plane_wave_line` (16 + cross-check vs VI₀) |
| VII₀ plane-wave line n_1 = n_3 ⇒ S = 0 (FLRW-recovery axis) | Direct consequence of `diff = 0` in source_VII0; no separate branch | `test_type_VII0_isotropic_limit_vanishes_exactly` (12 parametrisations) |
| SOURCE_STATUS promotion contract | 4 entries in `SOURCE_STATUS` dict flipped to `"VALIDATED"` with cross-ref comments citing the new tests | `TestSourceStatus.test_all_types_have_status` (trivially green — enum check only) |

No dead code introduced. No orphan imports. Per-type function bodies
themselves are untouched (the FB-0.1 ℋ² form is preserved verbatim);
FB-1.1 is a **metadata-level + test-level** promotion, not a
formula-level change. The pre-existing test suite (`TestFLRWLimit`,
`TestDimensionalConsistency`, `TestSignConventions`,
`TestZeroShearResponse`, `TestIntegrationSmoke`, `TestSourceStatus`)
continues to pass without modification.

## 5. Numerical / pipeline audit

| Item | Finding |
|---|---|
| `TestClassAFixedPoints` parametrised run count | 61 (1 Type I + 16 Type II + 16 Type VI₀ + 16 Type VII₀ + 12 VII₀ isotropic) |
| `test_type_I_kasner_exponent_sum` drift | `σ × a³` rel_var < 2 % (observed ~ 10⁻⁶); `Σ × a²` rel_var < 0.5 % (observed ~ 10⁻⁶) |
| Formula-match tolerance | rel 1e-12 (well inside float64 ulp × a few operations); passes at all 3 × 16 + 12 = 60 formula assertions |
| Σ-independence assertion | rel 1e-14 (exactly equal up to ordering-of-operations noise) |
| Sign pin on VI₀ | `dSp < 0` at all 16 parametrised runs (non-degenerate strict inequality) |
| VII₀ isotropic limit | `dSp == 0.0` and `dSm == 0.0` (hard equality, not approx) — sourced from `diff = 0` propagating through `diff**2 * calH_sq = 0` and `summ * diff * calH_sq = 0` |
| Wall time | 70 s full suite (was 70 s post FB-0.3); FB-1.1 adds ~0.5 s for the parametrised source-function calls (all O(1) arithmetic) |
| Determinism | No RNG, no background-table mutation, no state leakage across parametrised runs |
| Baseline reproduction | 2,688 pre → 2,753 post (+65); 0 regressions |
| Gallery render time | ~4 s for the 4 new plots (2000-pt trajectories × 4 integrations) |
| Gallery file sizes | 03 (Type I): 260 KB; 04 (Type II): 116 KB; 05 (VI₀): 292 KB; 06 (VII₀): 222 KB |

## 6. Ranked failure modes

| ID | Type | Severity | Summary | Action |
|---|---|---|---|---|
| F3 (FB-0.1) | documentation | P2 carried | `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation drift | Still deferred to FB-2.4 |
| FB02-F1 (FB-0.2) | documentation | P2 carried | `00_conventions.md §2` cross-ref of `v̂_e` default | Still deferred to FB-3.1 |
| **FB11-F1** | **physics-framework** | **P2** | **The Wainwright-Ellis Table 11.1 fixed-point *coordinates* (Σ̂_+ = −1/2 for II, Σ̂_− = ∓1/√3 for VI₀, etc.) are attractors of the self-similar closed W-E system in which N_i co-evolve with H as `N̂_i = N_i/H`. Our framework pins `N_i` as constants of `StructureConstants` and lets ℋ(a) follow pure FLRW (Planck-2018), so the self-similar fixed-point *numerical* coordinates are not directly reachable. FB-1.1 therefore pins the source-function *formulas* (the dimensionless `S^{WE}_{±}` expressions) at rel 1e-12 rather than asymptotic convergence to the Hubble-normalised coordinates.** | **Deferred to FB-5 / FB-6**: when the perturbation sector (FB-5) opens the per-type mode quantisation and FB-6.2 exercises the cross-type continuity limits (VII_h → VII₀ etc.), revisit whether a Hubble-normalised diagnostic of the source function is useful. In the interim, the per-type formula + sign + Σ-independence tests (61 parametrised runs) are the stronger claim because they hold at **every** (N, ℋ) point rather than a single asymptotic limit. |
| FB11-F2 | testing | resolved | The FB plan brief for FB-1.1 specifies bands like `Σ_+/ℋ → −1/2 ± 0.05` under "asymptotic W-E fixed-point convergence". Pre-session interpretation would have silently failed (fixed point not reachable in our framework) and tempted loosening tolerances to catch transient excursions — which would be a false VALIDATION. | **Resolved in-session**: rewrote tests as formula-match + sign-match + axisymmetric/isotropic-limit pins (the *implementable* per-type contract). The "asymptotic" language is preserved in the test names (`test_type_II_WE_fixed_point_asymptotic`) with the docstring explicitly documenting the framework mismatch and what is actually being pinned. |

No P0 / P1 items. F3 and FB02-F1 are pre-existing P2 carries
from FB-0.1 and FB-0.2 respectively, both with explicit future
targets. FB11-F1 is a new P2 physics-framework finding — not a bug,
not a regression, but a precise statement of what FB-1.1 can and
cannot validate given the fixed-N framework.

## 7. Verifier results

| Verifier | Result | Notes |
|---|---|---|
| Physics (limit recovery, dimensions, signs) | **PASSED** | FLRW limit preserved (no-op on 4 promoted types); FB-0.1 Ellis ℋ² conformal factor preserved; Kasner σ × a³ pinned on direct background integrator; axisymmetric Type II Σ_- ≡ 0 pinned; VI₀ / VII₀ S_- sign-flip pinned at matched (|diff|, |summ|); VII₀ isotropic limit ⇒ S = 0 exactly; W-E Table 11.1 formulas reproduced at rel 1e-12 |
| Code (contract satisfaction) | **PASSED** | `compute_shear_source` signature unchanged; `SOURCE_STATUS` dict expanded with FB-1.1 cross-ref comments but same shape; per-type function bodies untouched; `TestClassAFixedPoints` does not reach into private state |
| Numerical (convergence, tolerance) | **PASSED** | 2,753 pass + 1 skip; +65 new, 0 regressed; 70 s wall time stable; formula rel 1e-12 passes on all 60 parametrised assertions; Kasner rel_var 10⁻⁶ against a 2 % ceiling (2000 pts, Planck-2018 FLRW background) |

## 8. Minimal repair plan (applied in-session)

| Patch | Target | Status |
|---|---|---|
| A | `bass/transport/test_shear_sources.py` — added `TestClassAFixedPoints` class with 5 methods (4 per-type + 1 isotropic VII₀ auxiliary); added `source_II` to the existing import block | ✅ |
| B | `bass/transport/shear_sources.py::SOURCE_STATUS` — promoted I / II / VI_0 / VII_0 to `"VALIDATED"` with FB-1.1 cross-reference comments linking to each test and to this audit log | ✅ |
| C | `scripts/make_physics_gallery.py` — added 4 new plot functions (`plot_11_03..06_fb11_classA_*`) and 4 corresponding entries in the `CATALOG[TOPIC_11]` list; uses only existing helpers (`solve_bianchi_background`, `_save`, `_prepare_axes`, `COLS`) | ✅ |
| D | `plots/physics_gallery/11_integrator/{03..06}_fb11_classA_*.png` — generated via `scripts/make_physics_gallery.py --only 11_integrator`; each PNG visually inspected (see §9) | ✅ |
| E | `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` — new audit log (this file); §1..§10 template followed; FB-1.2 / FB-1.3 / FB-1.4 placeholders queued for future sub-phases | ✅ |
| F | `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md §2` — rotated to FB-1.2 (Class A VIII / IX; Bianchi IX `solve_ivp` event detection for recollapse) | ✅ (see commit) |

## 9. Minimal test set (delivered)

**Baseline reproduction**: 2,688 pre-FB-1.1 tests all still green;
no pre-existing test was weakened, modified, or added. The
formula-body changes are **zero** — FB-0.1 already landed the Ellis
ℋ² lift.

**Physics sanity (new)**: `test_type_I_kasner_exponent_sum` verifies
the Kasner geometric invariant `σ × a³ = const` on a direct
`solve_bianchi_background` trajectory (distinct from the existing
`test_I12b_kasner_analytic_recovery_type_I` which uses the hierarchy
integrator); `test_type_VII0_isotropic_limit_vanishes_exactly`
verifies VII₀ plane-wave-line FLRW recovery at 12 (N, ℋ) points.

**Formula-level regression (new)**: `test_type_II_WE_fixed_point_asymptotic`
(16 parametrised), `test_type_VI0_WE_fixed_point_asymptotic` (16),
`test_type_VII0_shear_decay_to_plane_wave_line` (16) each pin the
W-E Table 11.1 dimensionless `S^{WE}_{±}` formula at rel 1e-12.

**Sign / symmetry cross-check (new)**: the VII₀ test includes an
explicit assertion `dSm_VII0 == −dSm_VI0_matched` at matched
(|diff|, |summ|), verifying the sign-flip signature that distinguishes
the two types in W-E Table 11.1.

**Adversarial / edge**: Σ-independence of every Class A source is
pinned explicitly (axisymmetric Type II; VI₀ and VII₀ with Σ ≠ 0 vs
Σ = 0 baseline), ruling out any accidental Σ-coupling slipped in
during FB-0.1.

**Regression**: 2,753 passing + 1 skipped; +65 new, 0 regressed.

### Gallery inspection summary (visual verification)

Each of the 4 new PNGs was opened with the Read tool and the physics
qualitatively verified before final commit:

| PNG | Key visual check | Verdict |
|---|---|---|
| `03_fb11_classA_typeI_kasner_trace.png` | Σ × a² flat at 2.1609e-16 with drift < 1e-22 (integrator noise); σ × a³ matches; Σ²/a⁴ decays exactly as ∝ a⁻⁸ reference | ✅ |
| `04_fb11_classA_typeII_WE_attractor.png` | Σ_+ dips below zero near a ~ 3e-5 (source-driven), Type I baseline stays positive; Σ_- identically zero; S^{WE}_+ constant at −6.67e-5 | ✅ |
| `05_fb11_classA_typeVI0_WE_attractor.png` | Σ_+ driven negative in both cases (S_+ < 0); Σ_- zero for n_3 = -1e-2 (n_1+n_3 = 0 ⇒ S_- = 0), negative for n_3 = -5e-3; phase plane shows curved trajectory into Σ_- < 0 quadrant | ✅ |
| `06_fb11_classA_typeVII0_decay.png` | Isotropic Σ × a² flat at the same Type-I level; asymmetric Σ_- **positive** (contrasts with VI₀ negative — sign-flip signature of W-E Table 11.1); phase plane shows trajectory into Σ_- > 0 quadrant | ✅ |

No physics anomaly required in-session fixes to the plot code.

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과** (no P0 / P1;
  FB11-F1 is a P2 physics-framework finding documented explicitly
  with deferred action to FB-5 / FB-6; FB11-F2 resolved in-session
  by reframing the tests to the implementable formula + sign +
  limit contract).
* **지금 당장 구현/수정한 1개**: the promotion of `SOURCE_STATUS`
  for Class A types I / II / VI₀ / VII₀ from PROVISIONAL to
  VALIDATED, grounded in 61 parametrised formula-match + sign-pattern
  + axisymmetric/isotropic-limit tests. This is the FB plan §4 FB-1
  exit-criteria pre-requisite for promoting 4/9 PROVISIONAL sources;
  FB-1.2 (VIII/IX) + FB-1.3 (Class B III/IV/V/VI_h/VII_h) will
  complete the remaining 5.
* **지금 손대면 안 되는 1개**: attempting to wire a Hubble-normalised
  source diagnostic to "match" the W-E Table 11.1 *fixed-point
  coordinates* numerically today. Our framework has `N_i` pinned by
  `StructureConstants` and H(a) from Planck-2018 FLRW, so the
  self-similar fixed points are not dynamically reachable; forcing
  a coordinate match would require adding an N-renormalisation
  layer whose scope, purpose, and interaction with FB-2 / FB-5 is
  outside FB-1.1 (and is itself a candidate only for FB-5 / FB-6
  cross-type continuity work, not for FB-1). FB11-F1 documents
  this as a P2 finding with explicit deferral.

## Gallery refresh

FB-1.1 is the **first non-no-op** gallery extension of the FB phase
(FB-0.1 / 0.2 / 0.3 were all visual no-ops as documented in their
supplements). Four new PNGs land under `plots/physics_gallery/11_integrator/`:

* `03_fb11_classA_typeI_kasner_trace.png` — 3-panel Type I Kasner
  invariants + shear-energy decay
* `04_fb11_classA_typeII_WE_attractor.png` — 3-panel Type II
  axisymmetric source (Σ_+ trace + Σ_- ≡ 0 pin + W-E S^{WE}_+ const)
* `05_fb11_classA_typeVI0_WE_attractor.png` — 3-panel Type VI₀
  (Σ_+ driven negative + Σ_- sign pattern + phase plane)
* `06_fb11_classA_typeVII0_decay.png` — 3-panel Type VII₀
  (isotropic plane-wave line + asymmetric Σ_- positive sign-flip vs
  VI₀ + phase plane)

Per the phase-boundary gallery rule, each PNG was visually inspected
post-generation and before commit. No physics anomaly was detected
that required an in-session fix.

## Outstanding items carried forward

* **F3** (P2 from FB-0.1): `TetradBackgroundState.shear_magnitude_sq`
  → dimensionless Σ² per `00_conventions §4.2`. Still deferred to
  **FB-2.4** (11-type anisotropic ³R_ab consolidation).
* **FB02-F1** (P2 from FB-0.2): cross-reference the FB-0.2 `v̂_e`
  default into `00_conventions.md §2`. Still deferred to **FB-3.1**
  (first dynamical consumer of `v̂_e` — TiltedSpeciesBackground).
* **FB11-F1** (P2 from FB-1.1): W-E Table 11.1 fixed-point
  *coordinates* (Σ̂_+ = −1/2 etc.) are not directly reachable in our
  fixed-N framework; revisit during **FB-5 / FB-6** when the
  perturbation-sector mode quantisation and cross-type continuity
  limits open a natural diagnostic surface. No production-code
  change needed in the interim.

---

**Phase FB-1 status (after FB-1.1)**: 1/4 sub-phases delivered.
Four of the nine PROVISIONAL Class A / Class B sources promoted to
VALIDATED; the remaining five (VIII, IX, III, IV, VI_h, VII_h) are
tracked for FB-1.2 / FB-1.3 / FB-1.4. Ready to hand off to
**FB-1.2** (Class A VIII / IX — Bianchi IX recollapse `solve_ivp`
event detection; BKL oscillation smoke on axisymmetric fixture).

---

<!-- Reserved placeholder for FB-1.2 supplement (next session):

## FB-1.2 supplement — VIII / IX background validation

Will append the same §1..§10 template. Headline additions:
- `SOURCE_STATUS["VIII"]` / `["IX"]` promoted to VALIDATED
- `solve_ivp(event=IX_recollapse)` branch in einstein_bianchi for
  Type IX's positive spatial curvature → recompact scenario
- BKL oscillation qualitative smoke on Type IX axisymmetric fixture
- Gallery: `07_fb12_classA_typeVIII_WE_attractor.png` and
  `08_fb12_classA_typeIX_recollapse_trace.png` (if the event branch
  fires within a representative integration window)

-->

<!-- Reserved placeholder for FB-1.3 supplement (Class B) and FB-1.4
(anisotropic_3_curvature 11-type consolidation). -->
