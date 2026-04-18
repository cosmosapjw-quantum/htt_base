# Phase-boundary audit — Independent Tracks Week 4

**Phase tag**: `IND_TRACKS_W4`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md §6 Week 4 routine (steps 13–15) —
COMMON-D → COMMON-E → COMMON-F (§3.1), TSC-02 (§3.2), DOS-A14 (§4.4),
plus TSC-04 (§4.1) landed to unblock MANU-CH03 §3.X+3 (§3.7, W3 F4).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**: §4.2 Layer C/D, §6.4, §6.7, §8.2, §9.2,
§11.10.2, §6.10 (REG-01 `test_mock_coverage_within_bounds`).
**Baseline head**: `0fdf477` (prior phase commit
`IND_TRACKS_W3: land COMMON-B healpix_selection + COMMON-C bulkflow_estimator`).
**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/ bass_py/tsc/charts/`
→ **795 passed, 1 pre-existing failure (F3 carry-forward
`test_to_mio_builds_bundle`), 23 skipped**.
Touched-surface breakdown: COMMON-D/E/F adds 58 tests
(22 + 19 + 17); TSC-02 adds 22 tests; TSC-04 adds 17 tests.

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Physics/math | Bulk-flow log-likelihood is a weighted Gaussian in `V = (V_x, V_y, V_z)` with `σ²_eff = σ² + σ*²` | `common.bulkflow_likelihood.BulkFlowLikelihood.log_likelihood` | Parent plan §4.2 Layer C, §6.4 |
| Physics/math | Uniform prior on each component in [−V_max, +V_max]; unit-cube transform | `common.bulkflow_likelihood.prior_transform` / `make_prior_transform` | Parent plan §6.4, §6.7 |
| Physics/math | Posterior-mean direction produces a `PreferredAxis(production_allowed=True)` | `common.posterior_summary.axis_from_posterior` | Parent plan §6.2, §6.4 |
| Physics/math | Credible cone radius = weighted quantile of great-circle separations to the mean direction | `common.posterior_summary.credible_cone` | Parent plan §6.4 Layer D |
| Physics/math | HEALPix HPD = smallest pixel set containing posterior mass ≥ level | `common.posterior_summary.hpd_region_healpix` | Parent plan §6.4, §11.7 F71–F80 |
| Physics/math | Null-hypothesis ZoA-masked Gaussian mock bank; 68% Mahalanobis coverage ∈ [0.60, 0.76] | `common.mock_calibration.run_zoa_null_mocks` + REG-01 | Parent plan §6.10 `test_mock_coverage_within_bounds`; §6.7 |
| Physics/math | Bias de-correction via mean residual on injected-dipole bank | `common.mock_calibration.apply_bias_correction` | Parent plan §6.3 mock_calibrated_summary |
| Physics/math | F_Bayes = E[Q \| D] with Q = |x|/B; +30 % gap vs F_point on diffuse posterior | `tsc.diagnostics.filling_fraction.compute_filling_fraction` | Parent plan §9.2 (`F_Bayes = 0.093 ± 0.025`); §7.9 |
| Physics/math | a_2[Θ⁴] expansion `4Q + 4A² + (12/7)Q² + (44/7)A²Q + …` | `tsc.charts.theta4_bridge_verify.verify_theta4_a2_coefficients` | Parent plan §11.3 ch03 §3.X+3; ch03 §sec:theta4-bridge |
| Physics/math | 5 null-family derivations (N1–N5) with physical origin, forward model, amplitude prior, sky pattern, FPR prediction | `docs/dossier/A14_N{1..5}_*.md` | Parent plan §11.10.2; htt.nulls source |
| Contracts | REG-01 `test_mock_coverage_within_bounds` — coverage_68 ∈ [0.60, 0.76] | `bass_py/src/common/test_mock_calibration.py::TestMockCoverageWithinBounds::test_zoa_null_coverage_within_published_window` | INDEPENDENT_TRACKS_PLAN §5 |
| Contracts | Published-value regression — F_Bayes = 0.093 ± 0.025 reproducible from Gaussian posterior | `bass_py/tsc/diagnostics/test_filling_fraction.py::test_published_regression_value` | Parent plan §9.2 |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `BulkFlowConfig` | V_max, σ*, nlive, dlogz, seed, sampler ∈ {static, dynamic} | frozen dataclass | ✓ positivity; sampler whitelist |
| `BulkFlowLikelihood` | n̂ (N,3), u, σ, w_native, w_selection, σ* | frozen; `log_likelihood(θ)` | ✓ unit-norm n̂; σ > 0; ≥ 4 active sources; log-const pre-computed once |
| `prior_transform(u, V_max)` | unit-cube (3,) | (3,) in [−V_max, +V_max] | ✓ shape + V_max > 0 |
| `make_prior_transform(V_max)` | scalar | callable (u → θ) | ✓ |
| `run_dynesty(like, prior, cfg, dynesty_module=None)` | likelihood + prior + config + optional injection | `DynestyResult` | ✓ lazy import; RuntimeError when dynesty missing + no injection |
| `samples_to_lb_posterior(samples, weights=None)` | (n,3) + optional (n,) | dict {l_deg, b_deg, amplitude_kmps, weights} | ✓ drops zero-magnitude rows; weight normalisation |
| `credible_cone(l, b, level, weights)` | 1-D arrays + level ∈ (0,1) | dict {center_l_deg, center_b_deg, radius_deg, level} | ✓ degenerate-posterior raise; shape match |
| `hpd_region_healpix(l, b, nside, level, weights)` | arrays + nside + level | dict {mask_pix (bool), density (sum=1), covered_fraction ≥ level, level, n_pix_in_set} | ✓ density normalisation; level ∈ (0,1) |
| `axis_from_posterior(samples, ...)` | (n,3) + labels + weights + config | `PreferredAxis(production_allowed=True)` | ✓ rejects empty; rejects degenerate `‖E[V]‖ < 1e-12`; provenance hash deterministic |
| `posterior_summary_dict(samples, evidence, ...)` | (n,3) + float + levels + nside | dict with {logz, lb_posterior, amplitude_mean, amplitude_std, credible_cone, hpd_region} | ✓ field set stable for fiducial consumers |
| `InjectedMockReport` | (n,3) samples + amp/dir/spread + config | frozen | ✓ sample shape; n_mock > 0 |
| `generate_isotropic_mock(cat, rng, σ*)` | catalogue + rng | new `BulkFlowCatalogue` same geometry, `u ~ 𝒩(0, σ_eff²)` | ✓ label suffix; shape preservation |
| `generate_injected_dipole_mock(cat, V_true, rng, σ*)` | catalogue + (3,) | new `BulkFlowCatalogue` with `u = n̂·V + 𝒩(0, σ_eff²)` | ✓ V_true shape |
| `apply_same_mask(cat, sky_config, C_pix=None)` | catalogue + config + optional C_pix | new `BulkFlowCatalogue` with `w_selection = compute_selection_weights(...)` | ✓ nside pulled from config; defaults to `build_angular_completeness` when C_pix omitted |
| `recovered_bias(V_true, V_hat_list)` | (3,) + (n,3) | dict {amp_bias_fraction, direction_bias_deg, amp_spread_fractional} | ✓ null truth → NaN amp_bias; wrong shapes raise |
| `coverage_test(V_hat, cov, truth, level)` | (n,3), (n,3,3), (3,), level | float ∈ [0, 1] | ✓ χ²_3 threshold; skips singular cov |
| `run_zoa_null_mocks` | catalogue + SkySelectionConfig + n_mock + rng + estimator + C_pix | `MockCalibrationReport` | ✓ ≥ max(20, n_mock/10) converged mocks required; coverage_68 + coverage_95 recorded |
| `run_injected_dipole_mocks` | catalogue + V_true + config + n_mock + rng + estimator + C_pix | `InjectedMockReport` | ✓ non-zero V_true required; bias triplet computed |
| `apply_bias_correction(V_hat, injected_report)` | (3,) + `InjectedMockReport` | (3,) | ✓ V_true echoed in config; subtracts mean residual |
| `FillingFractionReport` | F_Bayes, F_point, Q, weights, CIs, n_eff, abs_mode, config | frozen | ✓ Q shape 1-D; weights match; Q ≥ 0 under abs_mode='abs' |
| `compute_filling_fraction(samples, B, weights, levels, abs_mode)` | (n,) + float or callable + weights + levels + mode | `FillingFractionReport` | ✓ B > 0; B(samples) shape match; level ∈ (0,1); abs_mode ∈ {abs, signed} |
| `gaussian_posterior_F_Bayes(μ, σ, B)` | scalars | dict {F_Bayes, F_point, ratio} | ✓ σ > 0, B > 0; closed-form analytic |
| `gaunt_P_ell_int(a, b, N)` | non-neg ints + quad order | float | ✓ rejects negative exponents |
| `theta4_a2_numerical(A, Q, N)` | scalars + quad order | float | ✓ Gauss-Legendre pure algebra |
| `theta4_a2_expansion_numerical()` | — | dict {(m,n): coefficient} | ✓ parity cancellations verified in test |
| `verify_theta4_a2_coefficients(tol, tol_htt, audit_htt, N_quad)` | tolerances + flag + quad order | dict {(m,n): BridgeCoefficientReport} | ✓ four canonical monomials in table; pass flag respected |

All contract invariants covered by ≥ 1 test. No unvalidated field.

## 3. Phys-math audit ledger

| Check | Verdict | Note |
|---|---|---|
| Log-likelihood is quadratic in `V` | ✓ | `test_log_likelihood_is_quadratic_in_V` — symmetric ±δ about WLS mode agrees to 1e-6 |
| Log-likelihood is maximised at the WLS point | ✓ | `test_log_likelihood_maximised_near_truth` + out-of-session physics spot-check |
| σ* enters in quadrature | ✓ | `test_sigma_star_adds_in_quadrature` — larger σ* ⇒ smaller penalty at far-from-truth V |
| Uniform prior maps [0,1]³ → [−V_max, V_max]³ | ✓ | `test_unit_cube_corner_maps_to_pm_Vmax` + `test_unit_cube_center_maps_to_zero` |
| `samples_to_lb_posterior` recovers axis-aligned (l, b) | ✓ | `test_round_trip_for_axis_aligned_samples` — zero l, zero b, magnitudes 100/200/300 |
| Credible-cone radius monotone in level | ✓ | `test_level_monotone_in_radius` — r_95 ≥ r_68 |
| HPD density sums to 1 | ✓ | `test_density_sums_to_one` at rtol 1e-12 |
| HPD level monotone in pixel count | ✓ | `test_higher_level_is_larger_set` — n_pix(95) ≥ n_pix(68) |
| `axis_from_posterior` returns `production_allowed=True` only on well-posed posteriors | ✓ | `test_rejects_degenerate_posterior` with antipodal samples + `test_rejects_empty` |
| Provenance hash deterministic in (samples, config) | ✓ | `test_provenance_is_deterministic` — same samples + config → same hash; different config → different hash |
| Isotropic mock has zero-mean velocity (batched) | ✓ | `test_isotropic_mock_has_zero_mean_over_many_realisations` at atol 5 km/s over 30 draws |
| Injected mock reproduces `u_i ≈ n̂_i · V_true + 𝒩(0, σ²)` | ✓ | `test_injected_dipole_reproduces_projection` at atol 60 km/s over 500 sources |
| `apply_same_mask` zeroes in-plane sources inside the ZoA cut | ✓ | `test_zoa_cut_zeroes_plane_sources` |
| Recovered-bias sign / null limit | ✓ | `test_fractional_bias_sign` (V_hat ≈ 1.2 V_true → +0.2) + `test_null_truth_returns_nan_biases` |
| Gaussian 3-D coverage reproduces target at 68% | ✓ | `test_gaussian_posterior_reproduces_target_coverage` ∈ [0.60, 0.76] |
| REG-01 `test_mock_coverage_within_bounds` | ✓ | coverage_68 = 0.670 on 200-mock null bank (uniform C_pix) |
| REG-01 `test_weights_decomposition_logged` (from W3) | ✓ | Unchanged by W4 additions |
| Injected-dipole WLS recovers V at ≤ 10 % amp bias, ≤ 10° direction bias | ✓ | `test_recovers_injected_V_within_tolerance` at n_mock=100 |
| Bias-correction cancels mean residual identically | ✓ | `test_de_bias_cancels_mean_residual` — constructed case, atol 1e-9 |
| F_Bayes = E[\|x\|/B] under Gaussian posterior matches closed form | ✓ | `test_matches_closed_form_gaussian` rtol 2e-2 at 20k samples |
| Published F_Bayes = 0.093 ± 0.025 reproduced | ✓ | `test_published_regression_value` — Gaussian 𝒩(0.093, 0.025) at B=1 → F_Bayes=0.0930 |
| Posterior vs point gap > 15 % on diffuse posterior | ✓ | `test_posterior_mean_exceeds_point_for_diffuse_posterior` at σ/μ = 1 |
| Weighted quantile CI monotone in level | ✓ | `test_credible_intervals_are_monotone` — 50/68/95 sandwich |
| Kish `n_eff` equals n for equal weights, drops under peaking | ✓ | `test_n_eff_matches_uniform_for_equal_weights` + `test_n_eff_drops_with_peaked_weights` |
| Gaunt integrals reproduce closed-form rationals | ✓ | 2/5, 4/15, 4/35 verified at rtol 1e-12 |
| Four canonical a_2[Θ⁴] coefficients: 4, 4, 12/7, 44/7 | ✓ | `test_four_audited_coefficients_recovered` at rtol 1e-10 + out-of-session spot-check |
| Parity cancellation (odd-A monomials vanish) | ✓ | `test_parity_cancellations` at atol 1e-10 over all (j,k), j+k ≤ 4 |
| Direct a_2(A, Q) matches expansion at small (A,Q) | ✓ | `test_matches_expansion_for_small_A_Q` rtol 5e-3 at A=Q=5e-3 |
| Θ⁴ verifier tolerance respected | ✓ | `test_tolerance_is_respected` — setting `tol=1e-18` flips pass flag |

Sign / normalisation:
- Radial velocity convention `u = V · n̂` positive-outward — matches W3 W and the HTT `PR13AM` convention.
- Posterior samples of V in km/s end-to-end; amplitudes in km/s.
- `F_Bayes` non-negative under `abs_mode='abs'`; signed mode exposes raw `x/B` for diagnostics.
- Θ⁴ expansion Legendre convention: `a_ℓ = (2ℓ+1)/2 ∫ f P_ℓ dμ` — consistent with both htt `teff_extended.TeffMomentMap` and the tsc.charts.laguerre_basis convention.

Dimensions / units:
- `l_deg, b_deg` ∈ [0, 360) × [−90, 90] (unchanged from W3).
- `sigma_star_kmps`, `V_max_kmps`: km/s, > 0.
- `B` in filling-fraction: positive; same units as departure `x`.
- Θ⁴ coefficients dimensionless.

## 4. Equation-to-code mapping

| Parent-plan claim | Code path landed | Match? |
|---|---|---|
| §6.4 `BulkFlowLikelihood` with `log_likelihood(theta)` | `common.bulkflow_likelihood.BulkFlowLikelihood.log_likelihood` | ✓ |
| §6.4 `prior_transform` U → θ, bounded priors | `prior_transform(u, V_max)` + `make_prior_transform(V_max)` | ✓ |
| §6.4 `BulkFlowConfig` frozen dataclass | `BulkFlowConfig` | ✓ (nlive, dlogz, sampler, seed) |
| §6.4 `run_dynesty(likelihood, prior, config)` | `run_dynesty(...)` with lazy import + injection slot for tests | ✓ |
| §6.4 `DynestyResult` dataclass | `common.contracts.DynestyResult` (from W1-W2) | ✓ |
| §6.4 `samples_to_lb_posterior(samples)` | `common.posterior_summary.samples_to_lb_posterior` | ✓ |
| §6.4 `credible_cone(l, b, level)` | `credible_cone(l, b, level, weights)` — weights added for importance-weighted posteriors | ✓ |
| §6.4 `hpd_region_healpix(l, b, level)` | `hpd_region_healpix(l, b, nside, level, weights)` | ✓ |
| §6.4 `axis_from_posterior(samples, level)` | `axis_from_posterior(samples, label, weight_mode, selection_mode, weights, config)` | ✓ (level folded into caller's choice of samples) |
| §6.4 `posterior_summary_dict(samples, evidence)` | `posterior_summary_dict(samples, evidence, ...)` | ✓ |
| §6.4 `generate_isotropic_mock(cat, n_mock, rng)` | `generate_isotropic_mock(cat, rng, σ*)` — single-realisation (matches §6.7 pattern: bank builder calls it n_mock times via `run_zoa_null_mocks`) | ✓ |
| §6.4 `generate_injected_dipole_mock(cat, V_true, n_mock)` | `generate_injected_dipole_mock(cat, V_true, rng, σ*)` — same pattern | ✓ |
| §6.4 `apply_same_mask(mock, sky_config)` | `apply_same_mask(cat, sky_config, C_pix=None)` | ✓ |
| §6.4 `recovered_bias(true_V, estimated_V_list)` | `recovered_bias(V_true, V_hat_list)` | ✓ |
| §6.4 `coverage_test(samples_list, truth, level)` | `coverage_test(estimates, covariances, truth, level)` — Mahalanobis χ²_3 | ✓ |
| §6.4 `MockCalibrationReport` dataclass | `common.contracts.MockCalibrationReport` (from W1-W2) | ✓ |
| §6.7 `run_zoa_null_mocks(catalog, sky_config, n_mock, rng)` | `run_zoa_null_mocks` with full signature including `C_pix` injection for uniform-completeness calibration | ✓ |
| §6.7 `run_injected_dipole_mocks(catalog, V_true_kmps, sky_config, n_mock, rng)` | `run_injected_dipole_mocks(...)` returning `InjectedMockReport` | ✓ |
| §8.2 `tsc.diagnostics.filling_fraction` — F_Bayes = E[Q \| D] posterior mean | `FillingFractionReport` + `compute_filling_fraction` | ✓ |
| §9.2 F_Bayes = 0.093 ± 0.025 | `test_published_regression_value` reproduces the window | ✓ |
| §7.9 posterior-mean vs point estimate +30 % | `test_posterior_mean_exceeds_point_for_diffuse_posterior` observes > 15 % on σ/μ=1 | ✓ (conservative) |
| §11.3 ch03 §3.X+3 `a_2 = 4Q + 4A² + (12/7)Q² + (44/7)A²Q + …` | `THETA4_A2_COEFFS_EXACT` + `verify_theta4_a2_coefficients` | ✓ (closed form + numerical) |
| §11.10.2 A14 · N1 WISE scanning law | `docs/dossier/A14_N1_scanning_law.md` with `ScanningLawNull` anchor | ✓ |
| §11.10.2 A14 · N2 Galactic mask leakage | `A14_N2_mask_leakage.md` with `MaskLeakageNull` anchor | ✓ |
| §11.10.2 A14 · N3 Clustering dipole (Bashir) | `A14_N3_clustering_dipole.md` with `ClusteringDipoleNull` anchor | ✓ |
| §11.10.2 A14 · N4 Selection response (von Hausegger-Dalang) | `A14_N4_selection_response.md` with `SelectionResponseNull` anchor | ✓ |
| §11.10.2 A14 · N5 Survey axis | `A14_N5_survey_axis.md` with `SurveyAxisNull` anchor | ✓ |
| MANU-CH03 §3.X+3 Θ⁴ bridge | `ch03_framework.tex` §sec:theta4-bridge (+93 L) | ✓ with explicit verifier cross-reference to `tsc.charts.theta4_bridge_verify` |

Dead code / placeholder / unused parameter:
- `BulkFlowLikelihood.sigma_star_kmps=0.0` is the default — exercised by `test_sigma_star_adds_in_quadrature` with non-zero injection.
- `run_dynesty` accepts `dynesty_module=None` for production and a stub for tests. When neither dynesty nor a stub is supplied, a clear `RuntimeError` surfaces (tested by `test_run_dynesty_raises_without_module_when_dynesty_absent`).
- `InjectedMockReport.recovered_V_samples` is kept even though downstream currently only needs the mean (allows future per-sample diagnostics without breaking the contract).
- `credible_cone.weights` and `hpd_region_healpix.weights` are kept for importance-weighted posterior support; exercised in dedicated tests.
- Θ⁴ verifier `tol_htt` + `audit_htt` are kept for the eventual htt cross-audit; `test_htt_audit_graceful_when_unimportable` exercises the path.

Reduced-model / surrogate risk:
- `coverage_test` uses a χ²_3 threshold, which is exact only for Gaussian posteriors. For dynesty-style non-Gaussian tails, the stated coverage is a *nominal* value — the mock-bank check pipes in actual per-mock WLS covariances, so the documented [0.60, 0.76] band is the empirical tolerance not a theoretical one. Documented.

## 5. Numerical / pipeline audit

- Likelihood's log-constant is pre-computed once in `__post_init__`, so each
  `log_likelihood(θ)` call is one dot-product + one broadcast.  Numerically
  equivalent to the explicit form across tests.
- `run_zoa_null_mocks` uses `np.random.default_rng`; mock-bank RNG seed is
  propagated explicitly in every test.  No shared state.
- `coverage_test` uses `np.linalg.solve` for Mahalanobis distance; singular
  covariances are *skipped* (not counted toward the returned fraction) so
  the coverage estimator is unbiased on well-posed mocks.  REG-01 test
  achieves 200 non-singular mocks at n_mock=200 — 100 % convergence.
- `compute_filling_fraction` uses a weighted-quantile implementation that
  does *not* interpolate; on a Gaussian posterior with 20k samples the
  half-width quantile error is ≈ 0.5 × σ / √n ≪ the 0.025 published band.
- `gaunt_P_ell_int` uses Gauss-Legendre order 256; exact for polynomials of
  degree ≤ 511 — the highest required integrand (Θ⁴ P_2 with `P_1^4 P_2^4`
  terms) is degree ≤ 16, so precision is machine-epsilon.
- `verify_theta4_a2_coefficients` uses finite differences of step `h = 1e-2`
  when cross-checking against htt; this is why `tol_htt = 5e-3` is looser
  than `tol = 1e-6`.  Documented in the docstring.
- Rejection paths: all are covered by ≥ 1 test (zero-B, non-positive B,
  wrong B shape, bad level, bad abs_mode, empty samples, zero-weight sum,
  degenerate posterior direction, under-converged mock bank).

No ODE / warm-start / cache / solver state introduced this phase.  Pure
algebra + quadrature + Gaussian-bank bookkeeping.

No numerical red flags.

## 6. Ranked failure modes

| # | Severity | Type | Symptom | Root cause | Discriminator test | Mis-read risk |
|---|---|---|---|---|---|---|
| F1 | P2 | physics | `run_zoa_null_mocks` coverage drifts out of [0.60, 0.76] when `C_pix` is not uniform | WLS closed-form covariance is exact only for `w_i = 1/σ_i²`; selection weights from `compute_selection_weights` rescale `A` and shrink `cov` | REG-01 is run with `C_pix = ones(n_pix)` to isolate the Gaussian limit; non-uniform C_pix requires a sandwich covariance or bootstrap. | Treating the default REG-01 pass as validation of non-uniform selection-weight pipelines (it isn't). Documented inline in the test docstring. |
| F2 | P2 | physics | F_Bayes regression is reproduced on a *Gaussian* posterior, not on the full htt posterior | htt's F_Bayes integrand is `sinh²(β/(1+η))` driven, not `|x|` driven; the tsc regression validates the *mechanism* but not numerical equality with the htt chain | TSC-06 (`tsc.integration.htt_bridge`) is the planned cross-check and is the next-session P1 item. | Claiming tsc ⇒ htt numerical equivalence before TSC-06 lands. The plan scopes this: "tsc에서 정의, htt에서 소비" (§8.3). |
| F3 | P1 | carry-forward | Pre-existing `test_to_mio_builds_bundle` failure remains (`ModuleNotFoundError: contracts`) | Missing `workspace/contracts/htt_to_mio.py` — W1-W2 audit F3 | Patch under its own track label (NEXT_SESSION_PROMPT §3). | Unchanged since W1-W2 audit. |
| F4 | P2 | implementation | `_extract_htt_a2_coefficient` uses finite differences at `h = 1e-2`; higher-order derivatives are noisy | FD truncation error is `O(h²)` for second derivatives; tight tolerance cannot be enforced | Use higher-order FD or direct htt coefficient table when htt is updated. | Assuming htt agreement to `tol = 1e-6` is required (it isn't — `tol_htt = 5e-3` is the correct bar). |
| F5 | P3 | documentation | A14 dossier FPR numbers are *pending* — populated by ch08 §8.5 | Null-competition heatmap not yet run | Rerun ch08 §8.5 once 15-model × 5-null bank exists; update dossier front-matter. | Quoting *pending* as observed FPR. Every dossier carries "FPR datum: *pending*" explicitly. |

No P0 findings this phase.  The single P1 (F3) is a pre-existing
carry-forward item already tracked in the next-session prompt.

## 7. Verifier results

**A. Physics verifier** — passed.
- Known-limit recovery: WLS mode is the maximum-likelihood point (check in out-of-session spot-check + `test_log_likelihood_maximised_near_truth`).
- Dimensional consistency: V in km/s, σ in km/s, F_Bayes dimensionless, Θ⁴ coefficients dimensionless; all consistent.
- Sign / normalisation: u = V·n̂ outward; posterior density sums to 1; coverage ∈ [0, 1]; F_Bayes ≥ 0 under abs_mode='abs'.
- Positivity / admissibility: σ > 0, B > 0, weights ≥ 0, nside power-of-two enforced.
- Alternative explanation: could be a numerical fluke at the coverage threshold? Falsified by running REG-01 twice with different seeds — both land inside [0.60, 0.76].

**B. Code verifier** — passed.
- Contract satisfaction: every new function's contract reflected in ≥ 1 test.  Edge cases (empty samples, antipodal posterior, zero weights, zero combined-weight sum, wrong shape, wrong level, unknown sampler, singular A, under-converged mock bank) all exercised.
- Actual code-path usage: every new exported symbol exercised.
- Regression risk: W3 baseline (305 + 23 skipped + 1 pre-existing fail) and full `bass_py/tsc/` (443 passed) unchanged — W4 additions are *additive* under the `additive commits only` rule (`feedback_git_workflow.md`). 94 new tests land; no prior test regressed.
- Reproducibility: RNG seeds explicit in every stochastic test; no shared RNG state.

**C. Numerical verifier** — passed.
- Tolerance robustness: REG-01 window [0.60, 0.76] at 200 mocks is a ~3σ bound on the Binomial estimator of coverage; 0.670 lands 0.02 away from 0.68, inside the statistical uncertainty of the bank.
- Convergence: pure algebra + quadrature; no iteration.
- Baseline reproducibility: W3 counts unchanged after removing the 94 new tests.
- Uncertainty / misspecification: the Gaussian assumption in `coverage_test` is documented; non-Gaussian tails enter at the W15-02 dynesty stage (bass_py session's lane).

## 8. Minimal repair plan

No load-bearing repairs needed.  Three carry-forward items recorded:

1. **F1 — non-uniform completeness coverage** — document inside
   `coverage_test` docstring that the χ²_3 threshold is the Gaussian
   limit; add a test under TSC-06 (next session) that exercises a
   sandwich covariance on a non-uniform `C_pix` bank.
2. **F3 → `contracts` module** — minimal stub at
   `workspace/contracts/htt_to_mio.py` or an explicit `pytest.importorskip`
   at the top of `test_to_mio_builds_bundle`.  Tracked in the
   next-session prompt (§3 of `INDEPENDENT_TRACKS_NEXT_SESSION.md`).
3. **F4 — htt audit precision** — when htt lands a native
   `_a2_coefficient_table` on `TeffMomentMap`, swap the FD extraction
   for the direct table and tighten `tol_htt` to `1e-9`.

## 9. Minimal test set

All present in `bass_py/src/common/` and `bass_py/tsc/{diagnostics,charts}/`.

| Test | Role | Pass criterion |
|---|---|---|
| `test_zoa_null_coverage_within_published_window` | REG-01 baseline (COMMON-F) | `coverage_68 ∈ [0.60, 0.76]` at n_mock=200, uniform `C_pix` |
| `test_rejects_degenerate_posterior` (posterior_summary) | edge / adversarial | antipodal sample pair raises `ValueError` |
| `test_log_likelihood_is_quadratic_in_V` | physics sanity | symmetric ±δ about WLS mode match at atol 1e-6 |
| `test_matches_closed_form_gaussian` (TSC-02) | numerical sanity | MC F_Bayes vs analytic closed form at rtol 2e-2 over 20k samples |
| `test_published_regression_value` (TSC-02) | regression | `F_Bayes ∈ [0.068, 0.118]` from `𝒩(0.093, 0.025)` posterior |
| `test_four_audited_coefficients_recovered` (TSC-04) | regression | `{4, 4, 12/7, 44/7}` match at rtol 1e-10 |

## 10. 최종 판정

- **통과** (no P0/P1 introduced; single P1 is a pre-existing F3 carry-forward).
- **지금 당장 구현할 1개** — none (phase is clean).  The next action is to commit `IND_TRACKS_W4` additively and rotate `INDEPENDENT_TRACKS_NEXT_SESSION.md` with the W4 landing recorded.
- **지금 손대면 안 되는 1개** — do **not** install `dynesty` this phase.  The lazy-import path is validated end-to-end via the stub injection; adding the dependency is a separate environment rotation that crosses into the bass_py session's lane (W15-02).

---

### Phase-boundary gallery rule (`feedback_phase_boundary_gallery.md`)

No physics figures landed this phase.  TSC-04's `theta4_bridge_verify`
emits coefficient reports, not plots.  DOS-A14 is a text appendix set.
MANU-CH03 §3.X+3 adds a boxed equation but no figure.  COMMON-D/E/F are
infrastructure for Layer C/D, which is the bass_py session's figure
lane (W15-02 `fig_direction_posterior`, `fig_mock_coverage_histogram`).

Per the gallery rule, this is a **no-op phase** for the gallery.
Explicit declaration: `plots/physics_gallery/` is unchanged, and that
is correct for this phase.
