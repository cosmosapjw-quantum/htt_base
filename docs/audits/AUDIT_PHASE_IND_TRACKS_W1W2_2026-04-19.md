# Phase-boundary audit — Independent Tracks Week 1–2

**Phase tag**: `IND_TRACKS_W1W2`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md §6 Week 1–2 routine (steps 1–10)
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.

Baseline test count before phase: 123 htt tests (1 pre-existing failure) +
existing tsc ≥ 400.
After phase: **263 passed, 1 pre-existing failure, 23 skipped**
(all skips tied to missing external data / optional matplotlib deps).

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Physics/math | T_CMB = 2.72548 K (Fixsen 2009) | `htt.core.ssot.C.T0_K` | Fixsen ApJ 707, 916 (2009) |
| Physics/math | Production inference must refuse all-zero directional weights | `PR13AM._direction_weight_status` | Parent plan §6.1/§6.8 |
| Physics/math | a_{ℓm} restoration must require production-grade axis | `PR13AJ.restore_full_a2m` + `PreferredAxis(production_allowed)` | Parent plan §6.2 |
| Physics/math | Directional summary must be split into four semantically disjoint channels | `PR13AH.reintegrate_observables` | Parent plan §6.3 |
| Math | Axisymmetric Θ(μ) admissibility (Paper I Prop 14/15) | `tsc/admissibility/realizability.py` + 50 tests | Paper I + ch03 |
| Math/geometry | Sphere-correct resultant-vector mean | `common.sky_geometry.spherical_mean` | Bingham-style circular statistics |
| Contracts | SkySelectionConfig invariant: `production_mode ⇒ !allow_uniform_fallback ∧ require_mock_calibration` | `common.contracts.SkySelectionConfig.__post_init__` | Parent plan §6.6 |
| Hygiene | No `zoa20_mean` / `FLRW_tilt_zoa20` in production path | `htt/core/constants.py` + `test_zoa20_sweep.py` | INDEPENDENT_TRACKS_PLAN §2.5 |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `_direction_weight_status(npz, prefix, production_mode)` | mapping w/ `'{prefix}_dir_w'`, bool | `{weights, fallback_status, production_allowed}` | ✓ all-zero + production → RuntimeError |
| `PreferredAxis` (frozen) | l_deg, b_deg, label, source, weight_mode, selection_mode, production_allowed, provenance_hash | — | ✓ source / weight_mode / selection_mode whitelisted |
| `restore_full_a2m(axis, a20)` | PreferredAxis, complex | Dict[int, complex] | ✓ production_allowed=False → RuntimeError (body itself NotImplemented — explicit) |
| `reintegrate_observables(cat, cfg)` | cat{'l','b','w'}, cfg{'zoa_half_angle_deg'} | dict of 4 ChannelSummary | ✓ 4 disjoint selection_mode labels; mock_calibrated carries `calibration_pending=True` |
| `SkySelectionConfig` | 9 fields | — | ✓ production↔uniform-fallback mutually exclusive; nside power-of-two |
| `DynestyResult` | samples, logwt, logz, ncall, config | — | ✓ shape consistency; ncall ≥ 0 |
| `MockCalibrationReport` | 5 fields | — | ✓ coverage_68 ∈ [0,1]; n_mock > 0; radius ≥ 0 |
| `spherical_mean(l,b,w)` | arrays | {l_deg, b_deg, resultant_R ∈ [0,1]} | ✓ degenerate R < 1e-12 → NaN longitude; ValueError on mismatched shape / non-positive wsum |
| `normalize_weights(w, allow_uniform_fallback)` | array, bool | (w_norm, status) | ✓ all-zero + not allowed → ValueError; non-positive sum → ValueError |

All contract invariants are covered by at least one test. No unvalidated field.

## 3. Phys-math audit ledger

| Check | Verdict | Note |
|---|---|---|
| Fixsen 2009 central value = 2.72548 | ✓ | bass side uses rounded 2.7255 → recorded in audit; deferred to bass_py session |
| Internal htt `T0_uK = T0_K × 1e6` identity | ✗ (documented) | audit + guard test captures the drift; intentional non-fix per §2.1 |
| ZoA half-angle convention (20° ↔ Kogut 1993) | ✓ | 3-tier split lands without touching numerical default |
| Axisymmetric Θ(μ) positivity | ✓ | 40 existing + 10 new tests; quadrature cross-check passes |
| Resultant-vector mean degenerate case (antipodal cancellation) | ✓ | R < 1e-12 threshold catches FP-noise antipodal zeros |
| PR13AH spherical mean uses placeholder (naive) | partial — **intended** | Plan §2.4 explicitly defers to COMMON-A-ready replacement; documented P2 below |

Sign / normalization: N/A for this phase (no equations with sign conventions land).
Dimensions / units: `T_CMB` in K and μK both handled; `ZoA_half_angle` degrees; `spherical_mean` returns degrees. Consistent across contracts.

## 4. Equation-to-code mapping

| Parent-plan claim | Code path landed | Match? |
|---|---|---|
| §6.1 `_direction_weight_status` signature | `htt/PR13AM_te_sign_d1d3_bridge.py::_direction_weight_status` | ✓ bit-equivalent to §6.8 |
| §6.2 `PreferredAxis` frozen dataclass with 8 fields | `htt/PR13AJ_full_a2m_restoration.py::PreferredAxis` + `common/contracts.py::PreferredAxis` | ✓ (two copies — see P2 below) |
| §6.2 `restore_full_a2m` gate | gate present; rotation body NotImplementedError | ✓ **explicit**: plan says "gate only" |
| §6.3 four-summary dict with four named keys | ✓ keys match: raw / zoa_masked / selection_aware / mock_calibrated | ✓ |
| §6.6 SkySelectionConfig invariants | `common/contracts.py::SkySelectionConfig.__post_init__` | ✓ literal match to spec |
| §6.6 `normalize_weights` signature | `common/sky_geometry.py::normalize_weights` | ✓ |
| §6.10 REG-01 test enumeration (7 tests) | 6/7 present: 1/2/3/4/5/6 of the table. The 7th (`test_weights_decomposition_logged`) depends on COMMON-C which is not in this phase. | partial — deferred to COMMON-C |

## 5. Numerical / pipeline audit

- Spherical quadrature cross-check: `test_isotropic_admissible_consistent_with_quadrature` passes; Lebedev order 7 grid agrees with `check_field_admissible` to 1e-6 on admissible fields.
- Antipodal cancellation FP: threshold `R < 1e-12` is conservative (≈ 30× double-precision noise at equator).
- Self-dot product clip: `arccos(clip(dot, -1, 1))` under the ~1e-6-degree residual. Tests tolerate 1e-4 deg.
- No solver / ODE introduced in this phase — all operations are pure algebra on numpy arrays or dict-level scaffolds.
- Reproducibility: three tests use `np.random.default_rng(seed=0)` for synthetic catalogues. No caches / warm starts involved.

No numerical red flags.

## 6. Ranked failure modes

| # | Type | Severity | Symptom | Root cause | Cheapest discriminator |
|---|---|---|---|---|---|
| F1 | implementation | P2 | PR13AH uses naive weighted (l, b) mean, not spherical_mean | Plan §2.4 defers the replacement to post-COMMON-A; both modules now exist in the same commit, so the defer is resolvable. | swap `_placeholder_mean` → `common.sky_geometry.spherical_mean`; re-run 7 AH tests |
| F2 | interface | P2 | Two copies of `PreferredAxis` (htt.PR13AJ and common.contracts) | Intentional per plan (HTT-P0-AJ atomicity); later track collapses the duplication | none now; track in NEXT_SESSION_PROMPT |
| F3 | implementation | P1 | `htt.integration.to_mio.test_to_mio_builds_bundle` still fails (pre-existing) | Missing `workspace/contracts` module sibling | not in scope this phase; carry forward |
| F4 | testing | P3 | 21 figures skip with external-dep filter | Figures depend on `/mnt/project`, `plot_style`, etc. | not a sys.path leak (the scripts parse cleanly); leave as skip |
| F5 | physics | P2 | htt-internal `T0_uK = 2.7255e6` inconsistent with `T0_K = 2.72548` | Historical drift; documented but not fixed | swap to `T0_K * 1e6` with regression check on `eps_ell` / `D_ell_from_eps` tolerance |
| F6 | interface | P3 | `bass.observational.planck_mes_bounds.T_CMB_K = 2.7255` drifts from htt's 2.72548 | Documented in SSOT audit; requires coordinated bass-side commit | defer to bass_py session (§2.1) |

No P0 failures. F1 is the largest-confidence P0-adjacent item but is bound by explicit plan language.

## 7. Verifier filter

| Verifier | Result |
|---|---|
| Physics — known-limit recovery (FLRW/small-shear/boost preservation) | ✓ all TSC `TestKnownLimits` PASS |
| Physics — positivity / admissibility | ✓ 10 extras tests PASS |
| Code — contract satisfaction | ✓ all invariants enforced in `__post_init__` |
| Code — actual code-path usage | partial — new PR13A* modules have **no upstream consumer yet**; they are gates waiting to be wired. This is plan-intended but worth an explicit flag. |
| Code — reproducibility | ✓ seeded RNGs; no hidden state |
| Numerical — tolerance robustness | ✓ (all thresholds conservative) |
| Numerical — baseline reproducibility | N/A (no numerical baseline lands; Phase H responsibility) |

## 8. Minimal repair plan (≤ 3 patches)

| # | Patch | Load-bearing reason | Failure mode addressed | New test | Regression impact |
|---|---|---|---|---|---|
| R1 | **Swap PR13AH placeholder mean → `common.sky_geometry.spherical_mean`** | Both modules ship in the same commit set, so the plan's "AH decoupled, wire later" justification no longer applies | F1 | Add a PR13AH test asserting that raw_summary's (l_deg, b_deg) equals `spherical_mean(l, b, 1)` to within 1e-10 | Seven AH tests may shift; keep the resultant_R invariants unchanged |
| R2 | **Record F2 / F3 / F5 / F6 in NEXT_SESSION_PROMPT §3 as Phase-H carry-forwards** | Avoids memory-only tracking; makes them discoverable in the next session | F2, F3, F5, F6 | none (documentation) | none |
| R3 | (optional) Expose a `htt.PreferredAxis = common.contracts.PreferredAxis` alias so the duplication in F2 collapses immediately | Single-point-of-truth for the axis contract | F2 | import-equivalence test | Any existing htt consumer (none yet) would not see a behaviour change |

I will implement **R1 + R2** inside this session as `AUDIT(IND_TRACKS_W1W2):` commits per the audit rule; R3 deferred to keep the two PR13AJ tests atomic.

## 9. Minimal test set (all live; no new test files required beyond R1)

| Slot | Existing test | Pass/fail criterion |
|---|---|---|
| Baseline | `test_tcmb_ssot_frozen_fixsen2009` | `C.T0_K == 2.72548` bit-exact |
| Edge / adversarial | `test_production_mode_rejects_uniform_fallback` | all-zero → RuntimeError |
| Physics sanity | `test_isotropic_admissible_consistent_with_quadrature` | field check ↔ Lebedev probe agreement |
| Numerical sensitivity | `test_antipodal_points_cancel` | R < 1e-12, NaN l_deg |
| Regression | `test_no_forbidden_zoa20_tokens_in_htt_production` | 0 hits in non-test non-constants code |

## 10. Final judgment

- **Verdict**: 통과 (R1 in-session fix before commit).
- **지금 당장 구현할 1개**: R1 — PR13AH → spherical_mean swap (eliminates a silent FP-wrap wrongness the moment COMMON-A consumers start appearing).
- **지금 손대면 안 되는 1개**: F5 (T0_uK fix) — requires numerical regression sweep over `eps_ell`/`D_ell_from_eps` consumers; out of scope for an audit-triggered session, needs its own thorough commit.
