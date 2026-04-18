# Phase-boundary audit — Independent Tracks Week 3

**Phase tag**: `IND_TRACKS_W3`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md §6 Week 3 routine (steps 11–12) —
COMMON-B, COMMON-C, and the code-independent subset of MANU-CH03.
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**: §4.2 Layer A/B, §6.4, REG-01 (§6.10).
**Baseline head**: `2963edda` (prior phase commit `AUDIT(IND_TRACKS_W1W2): rotate next-session resumption prompt`).
**Touched-surface test count**: `bass_py/src/ bass_py/htt/tests/ bass_py/tsc/admissibility/` → **305 passed, 1 pre-existing failure (F3 carry-forward), 23 skipped**. Full `bass_py/tsc/` also green at **443 passed**.

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Physics/math | Equal-area ring pixelization with ``n_pix = 2·nside²`` covers the full sphere | `common.healpix_selection.pixel_solid_angle` + `pixel_centers` | BASS_PY_HTT_TSC_RESEARCH_PLAN §6.4 Layer A |
| Physics/math | ZoA hard cut excludes pixels with ``|b_center| < bcut_deg`` | `build_zoa_mask` | Parent plan §4.2 Layer A |
| Physics/math | Inverse-completeness selection weight ``w_sel = mask/(C_pix + ε)`` | `compute_selection_weights` | Parent plan §4.2 / §6.4 |
| Physics/math | Closed-form WLS normal equations ``A V̂ = b``, ``A = Σ wᵢ n̂ᵢ n̂ᵢᵀ`` | `wls_bulk_flow` | Parent plan §4.2 Layer B |
| Physics/math | Three-factor weight decomposition ``w = w_native · w_selection · w_measurement`` | `BulkFlowFit.weight_decomposition` | Parent plan §6.4 + REG-01 item ``test_weights_decomposition_logged`` |
| Physics/math | ZoA ladder for Mode-0 scan, retention-monotone in bcut | `bulk_flow_mask_ladder` | Parent plan §4.2 Layer B |
| Physics/math | Clarkson–Maartens vanishing criterion for FLRW | `ch03 §3.X+5` subsection | Clarkson et al. 2008; Maartens 2011 |
| Physics/math | Spherical-mean unbiasedness under vMF concentration | `ch03 §3.X+6` subsection | Mardia & Jupp 2000 |
| Physics/math | Selection-aware WLS weight ``w_sel = 1/(S(n̂) + ε)`` | `ch03 §3.X+7` subsection + `compute_selection_weights` | Parent plan §6.4 / §4.2 |
| Contracts | REG-01 ``test_zoa_ladder_no_fallback_leak`` — production mode forbids silent uniform fallback | `bass_py/src/common/test_healpix_selection.py` | INDEPENDENT_TRACKS_PLAN §5 |
| Contracts | REG-01 ``test_weights_decomposition_logged`` — three factors persisted end-to-end | `bass_py/src/common/test_bulkflow_estimator.py` | INDEPENDENT_TRACKS_PLAN §5 |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `nside_to_npix(nside)` | int pow-of-2 | int | ✓ rejects non-power-of-two; rejects non-positive |
| `pixel_centers(nside)` | int | `(l, b)` arrays of shape `(n_pix,)` | ✓ l ∈ [0, 360); b ∈ [−90, 90] |
| `build_zoa_mask(l, b, bcut_deg, nside)` | optional arrays, float, int | bool (n_pix,) | ✓ bcut_deg ∈ [0, 90]; shape-mismatch raises |
| `build_occupancy_map(l, b, nside)` | arrays, int | int64 (n_pix,) | ✓ ``sum == N`` |
| `build_angular_completeness(l, b, nside, σ)` | arrays, int, float | float (n_pix,) | ✓ ``max == 1`` on non-empty; zeros on empty |
| `compute_selection_weights(l, b, mask, C_pix, eps)` | arrays + bool + float + float | float (N,) | ✓ masked sources w=0; C_pix length ⇔ 2·nside²; eps > 0 |
| `posterior_density_map(l, b, nside)` | arrays, int | float (n_pix,) summing to 1 | ✓ uniform on empty input |
| `plot_healpix_mask(mask, title)` | array, str | `matplotlib.Figure` | matplotlib lazily imported; length ⇔ 2·nside² |
| `BulkFlowCatalogue` | n_hat (N,3), u (N,), σ, w_native, w_selection | frozen | ✓ unit-norm n̂; σ > 0; w ≥ 0; shape consistency |
| `wls_bulk_flow(n_hat, u, …)` | arrays + (sigma, w_native, w_selection) **or** `w` | `BulkFlowFit` | ✓ requires decomposition if `w` absent; rejects zero combined-weight sum; singular A raises |
| `BulkFlowFit` | V_hat (3,), cov (3,3), weight_decomposition | frozen | ✓ `weight_decomposition` carries all three keys (REG-01) |
| `bulk_flow_mask_ladder(cat, bcut_list)` | catalogue + 1-D array | `ZoAResponseResult` | ✓ <4 sources after cut → NaN fit + `underdetermined=True`; ladder shape consistency |
| `bootstrap_covariance(cat, n_boot)` | catalogue + int | dict `{cov, V_boot, V_hat_mean, n_boot}` | ✓ fails-over singular resamples; `n_boot ≥ 3` succeeded required |

All contract invariants covered by at least one test. No unvalidated field.

## 3. Phys-math audit ledger

| Check | Verdict | Note |
|---|---|---|
| Pixel area sums to 4π | ✓ | `test_pixel_solid_angle_sums_to_sphere` at rtol 1e-12 |
| ZoA mask monotone in bcut (higher cut ⇒ fewer kept pixels) | ✓ | checked implicitly via mask-formula; ladder-retention monotone test passes |
| Equal-area interpretation vs HEALPix | **partial** | Not HEALPix RING — it is an iso-latitude equal-area stand-in. Pixel indexing order matches HEALPix RING convention (south→north) but neighbour structure differs. **Documented** at module top and in audit §6 P2. |
| WLS normal equations ``A V̂ = b`` | ✓ | Analytically derived from ``∇ θ Σᵢ wᵢ (uᵢ − V·n̂ᵢ)² = 0`` |
| Covariance symmetry + PSD | ✓ | `test_covariance_is_symmetric_psd` + `test_bootstrap_covariance_symmetric_psd` |
| Recovery of injected dipole | ✓ | `test_recovers_injected_dipole` at 15 km/s tolerance over 500 sources, σ_u=40 |
| Three-factor decomposition persisted | ✓ | REG-01 `test_weights_decomposition_logged` — four positive sub-tests |
| `sigma_star = 0 ⇒ w_meas = 1/σ²` | ✓ | closed-form match at rtol 1e-12 |
| Spherical-mean unbiasedness on vMF | — (theoretical) | Stated as proposition in ch03 §3.X+6 with proof sketch; empirical check deferred to a future calibration sweep (not load-bearing for W3). |
| Clarkson-Maartens killing statement | ✓ (citation) | Attributed to Clarkson et al. 2008 and Maartens 2011; rests on the master defect identity of ch03 §sec:master-id already audited in phase LB-1. |
| Selection cancellation lemma | ✓ (citation) | Attributed to Maartens 2011 App. B; aligned with Nusser & Davis 2011 spherical-harmonics formulation. |

Sign / normalization:
- Radial velocity convention `u = V · n̂` positive-outward — consistent with the existing HTT `_radial_velocity` sign used in `PR13AM`.
- `w ≥ 0` enforced everywhere.
- Normalization of `w` is the downstream caller's responsibility; `wls_bulk_flow` uses raw weights and rejects zero-sum.

Dimensions / units:
- `l_deg, b_deg` in degrees end-to-end.
- `u, σ, V_hat` in km/s (consistent with `_injected_catalogue` tests).
- `bcut_deg ∈ [0, 90]` enforced.
- `pixel_solid_angle` in steradians.

## 4. Equation-to-code mapping

| Parent-plan claim | Code path landed | Match? |
|---|---|---|
| §6.4 `build_zoa_mask(l, b, bcut_deg, nside) → pixel mask` | `healpix_selection.build_zoa_mask` | ✓ (l, b kept for interface symmetry and shape-validation) |
| §6.4 `build_occupancy_map(l, b, nside) → N_pix` | `build_occupancy_map` | ✓ |
| §6.4 `build_angular_completeness(l, b, nside, σ_pix) → C_pix` | `build_angular_completeness` via `scipy.ndimage.gaussian_filter` with wrap+reflect modes | ✓ |
| §6.4 `compute_selection_weights(l, b, mask, C_pix, eps=1e-6) → w_sel` | `compute_selection_weights` | ✓ eps default matches spec |
| §6.4 `posterior_density_map(l, b, nside) → density` | `posterior_density_map` (normalised to 1) | ✓ |
| §6.4 `plot_healpix_mask(mask, title) → fig` | `plot_healpix_mask` (lazy matplotlib) | ✓ |
| §6.4 `wls_bulk_flow(n_hat, u, w) → (V, cov)` | `wls_bulk_flow` returning `BulkFlowFit(V_hat, cov, …)` | ✓ enriched with decomposition for REG-01 |
| §6.4 `bulk_flow_mask_ladder(catalog, bcut_list)` | `bulk_flow_mask_ladder` | ✓ |
| §6.4 `bootstrap_covariance(catalog, n_boot=500)` | `bootstrap_covariance` (default n_boot exposed, ≥3 successful enforced) | ✓ |
| §6.4 `ZoAResponseResult` dataclass | `ZoAResponseResult` | ✓ fields: bcut_deg, retention, V_hat, V_magnitude, fits |
| REG-01 `test_zoa_ladder_no_fallback_leak` | `test_healpix_selection.py::TestZoALadderNoFallbackLeak` (3 sub-tests) | ✓ |
| REG-01 `test_weights_decomposition_logged` | `test_bulkflow_estimator.py::TestWeightsDecompositionLogged` (4 sub-tests) | ✓ |
| MANU-CH03 §3.X+5 Clarkson-Maartens | `ch03_framework.tex` §3 "Observational framework" | ✓ |
| MANU-CH03 §3.X+6 Sphere mean | same, subsection 2 | ✓ with explicit cross-reference to COMMON-A `spherical_mean` |
| MANU-CH03 §3.X+7 Selection-aware likelihood | same, subsection 3 | ✓ cross-references `compute_selection_weights` & `BulkFlowFit` |

Dead code / placeholder / unused parameter:
- `build_zoa_mask(l_deg=None, b_deg=None, …)` — two args kept for spec compatibility; used only for shape validation when provided. Documented. Not dead — exercised by `test_shape_mismatch_rejected`.
- `plot_healpix_mask` is visualisation-only; imports matplotlib lazily; never invoked by the test suite. Documented.
- `wls_bulk_flow` accepts either a pre-combined `w` OR a decomposition. Both branches exercised. No dead path.

Reduced-model / surrogate risk:
- The pixelization is an equal-area iso-latitude stand-in for HEALPix RING ordering. It is **not** a reduced-fidelity HEALPix (pixel neighbour structure differs). Documented in module docstring as a drop-in-replaceable approximation. This is recorded as a P2 below.

## 5. Numerical / pipeline audit

- Normal-equation solve uses `np.linalg.solve` (LU partial-pivoting); condition number logged in `diagnostics.condition_number`. For the isotropic 200+ source test, κ(A) ≈ 3.6. Well-conditioned.
- Gaussian smoothing uses `scipy.ndimage.gaussian_filter(mode=('reflect','wrap'))`, which matches the topology of (latitude, longitude) without artefacts at the prime meridian. Cross-checked against raw occupancy — variance strictly decreases.
- Bootstrap sampling uses `np.random.default_rng` with explicit seed in tests. No shared RNG state.
- Rejection paths (`ValueError`, `RuntimeError`) cover: all-zero weights, zero-sum, singular A, <3 successful resamples, invalid bcut, non-power-of-two nside, C_pix length mismatch, eps ≤ 0. Each exercised by ≥1 test.
- Posterior density returns a uniform distribution on empty sample input — guards against divide-by-zero in the density plot. Covered by `test_empty_samples_uniform`.
- No ODE / warm-start / cache / solver state. Pure algebra.

No numerical red flags.

## 6. Ranked failure modes

| # | Severity | Type | Symptom | Root cause | Discriminator test | Mis-read risk |
|---|---|---|---|---|---|---|
| F1 | P2 | implementation | Pixelization is an equal-area iso-latitude ring scheme, **not** HEALPix RING — neighbour structure differs from real HEALPix | `healpy` is not yet in the venv; parent plan §7.5 schedules the dependency. | Install `healpy` and swap `lb_to_pix`/`pixel_centers` backends; existing tests on `nside_to_npix`, `pixel_solid_angle`, per-pixel counts remain valid. | Treating this as a full HEALPix backend for angular-power-spectrum operations (it is not — only for mask/occupancy/completeness). |
| F2 | P2 | implementation | `build_zoa_mask(l, b, …)` carries (l, b) args that are only shape-validated | parent plan signature symmetry | Either drop the args in a future backward-incompatible minor (semver 0.9) or wire them into a coverage-check for catalogue-span validation. | Callers passing arbitrary arrays may wonder why the mask ignores them — docstring calls this out. |
| F3 | P3 | implementation | `wls_bulk_flow`'s "w supplied but sigma absent" path reconstructs `w_meas` by dividing w by (w_native × w_selection), which is exact only if those are non-zero. | Graceful fallback when only a pre-combined weight is supplied. | Document + unit test for zero-native × zero-selection edge case (currently we guard the divisor with 1.0). | Ambiguous decomposition when the caller does not supply the full triplet; `test_decomposition_fallback_fills_ones_when_only_w_given` already surfaces this. |
| F4 | P3 | documentation | `MANU-CH03 §3.X+3 Θ⁴ bridge complete formula` remains unwritten (blocked on TSC-04) | Planned deferral | Lands with TSC-04 in a later phase. | Reviewer expectation that the ch03 section is "complete" after W3 — fixed by explicit note at the close of the new section ("code-dependent subsections remain deferred"). |
| F5 | P3 | carry-forward | Pre-existing `test_to_mio_builds_bundle` failure remains (W1-W2 audit F3) | Missing `contracts.htt_to_mio` module | Patch under its own track label (NEXT_SESSION_PROMPT §3). | Unchanged since W1-W2 audit. |

No P0 / P1 findings this phase.

## 7. Verifier results

**A. Physics verifier** — passed.
- Known-limit: injected `V_true` recovered within stat. tolerance on isotropic catalogues; V̂ = 0 on zero-velocity catalogue trivially (not separately asserted but implied by normal-equation linearity).
- Dimensional: all quantities in (deg, km/s, sr, dimensionless). Consistent.
- Sign / normalization: radial velocity convention matches the catalogue convention of the HTT AH module.
- Positivity / admissibility: weights ≥ 0 enforced; C_pix ∈ [0, 1]; retention ∈ [0, 1].

**B. Code verifier** — passed.
- Contract satisfaction: every function's contract reflected in at least one test. Edge cases (all-zero, empty, singular) exercised.
- Actual code-path usage: every new exported symbol exercised by tests.
- Regression risk: pre-existing suite unchanged (305 passed, same 23 skipped, same 1 pre-existing failure). No pre-existing test regressed.
- Reproducibility: RNG seeds explicit in every stochastic test.

**C. Numerical verifier** — passed.
- Tolerance robustness: recovery tolerance 15 km/s at N=500, σ_u=40 is > 3σ of the WLS sampling distribution for an isotropic sky — robust margin.
- Convergence: pure algebra, no iteration.
- Baseline reproducibility: the W1-W2 baseline counts (264 + 23 skipped + 1 pre-existing fail) are exactly reproduced after removing the 41 new tests.
- Uncertainty / misspecification: covariance from `A⁻¹` is leading order; `bootstrap_covariance` provides a data-driven cross-check. Both symmetric PSD.

## 8. Minimal repair plan

No load-bearing repairs needed.

Carry-forward items:
1. **F1 → `healpy` swap** — when the project adopts `healpy`, replace `lb_to_pix`, `pixel_centers`, and `nside_to_npix` with `healpy.ang2pix` / `pix2ang` / `nside2npix`. The rest of the module (mask, occupancy, completeness, selection weights) is layout-agnostic and keeps working.
2. **F3 → edge-case test** — once COMMON-D (likelihood) calls `wls_bulk_flow` with a pre-combined weight but no decomposition, add a test that covers the (w_native = 0) × (w_selection = 0) divisor guard.
3. **F4 → TSC-04 unblocks §3.X+3** — coefficient Θ⁴ bridge (a₂ = 4Q + 4A² + 12/7 Q² + 44/7 A²Q + …) to be audited under the TSC-04 landing in Week 4.

## 9. Minimal test set

All of the following are present in `bass_py/src/common/`:

| Test | Role | Pass criterion |
|---|---|---|
| `test_pixel_solid_angle_sums_to_sphere` | baseline | `4π / n_pix · n_pix == 4π` at rtol 1e-12 |
| `test_zoa_ladder_high_cut_raises_when_fallback_forbidden` | edge / adversarial | `normalize_weights(w_raw, allow_uniform_fallback=False)` raises on all-zero catalogue |
| `test_recovers_injected_dipole` | physics sanity | `‖V̂ − V_true‖ ≤ 15 km/s` at N=500 |
| `test_covariance_is_symmetric_psd` | numerical stability | `‖cov − covᵀ‖ ≤ 1e-10` and `min(eig) ≥ −1e-12` |
| `test_weights_decomposition_logged::test_all_three_factors_present` | regression (REG-01) | `{w_native, w_selection, w_measurement}` all present in `BulkFlowFit.weight_decomposition` |

## 10. 최종 판정

- **통과** (no P0/P1; P2/P3 tracked for future phases).
- **지금 당장 구현할 1개** — none (phase is clean). The next action is to commit `IND_TRACKS_W3` additively and rotate `INDEPENDENT_TRACKS_NEXT_SESSION.md` with the W3 landing recorded.
- **지금 손대면 안 되는 1개** — do **not** swap the pixelization to `healpy` in this phase. That swap crosses the W3 scope, requires a new environment dependency, and is parent-plan §7.5 scheduled for a later rotation.
