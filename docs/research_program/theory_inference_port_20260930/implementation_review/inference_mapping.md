# Pre-data HTT inference mapping — 2026-09-30

Scope: read-only source mapping for the theory/pre-data implementation port. No catalogue fitting, scientific suite, inference run, empirical classification, model-metadata inference, or production writes were performed. This document is the sole output of this mapping task.

## Source quality and authority

The parent reports current main `efbd6d39b1167afcf40f3d07af0b5552747f3611` (DATA-01), and a source subset at `htt_port_20260930/work` whose 1,505 required tracked files were verified against parent Git blobs plus 13 DATA-01 deltas. This is a verified subset, not a complete checkout. Initial reads used `code_upgrade_20260929/sources`; the DATA-01 adapter, CLI, and tests were subsequently read from the current subset. Repository-relative paths below refer to these inspected sources. Runtime execution is not proved merely by the presence of a producer or test.

Read authority: root `AGENTS.md`, `htt/htt/AGENTS.md`, `htt/src/common/AGENTS.md`, and repository skills `htt-statistical-hardening`, `htt-local-global-discrimination`, `htt-claim-firewall`. The survey also applied `keystone:context-survey`. Their relevant rules are HTT ownership of inference, OBSSTAT ownership of extraction, rank before posterior, model/systematics separation, retained CF4 quarantine, and no conversion of MIO diagnostics into likelihood inputs. No nested agents were dispatched.

Theory input: `tilt_boost_loop_20260930/REPORT_KO.md` and `CLAIMS.json`. TBO-02/03 require a free distance-zero intercept and actual area-distance slope; TBO-06 distinguishes area distance from the endpoint invariant; TBO-10 assumes an already sound joint confidence set. TBO-11 is HOLD, I2 remains DEFENDED_CONDITIONAL, I3 HOLD_INPUT_INCOMPLETE, BIC-07 open. These are conditional theoretical inputs, not an executed observational inverse problem.

## Existing callable surfaces and consumers

| Surface | What the inspected source actually implements | Consequence for this port |
|---|---|---|
| `htt/htt/htt/core/pipeline.py` | Quarantined legacy entry point; `main()` only invokes `require_cf4_observational_input`. | Do not revive or route new work through it. The docstring mentions a separate production pipeline; that pipeline was not located in this subset. |
| `htt/htt/htt/core/departure_posteriors.py` | Legacy downstream transformation of posterior samples into HTT diagnostic quantities. | It neither constructs the new observation law nor reconstructs a geometric normal. Do not insert new endpoint coefficients into its older tilt model. |
| `htt/htt/htt/infer/dipole_vector_likelihood.py` | Concrete older amplitude/direction audit; CatWISE/radio amplitudes, a bivariate scalar law and angular penalties; excludes CF4 channel `c`. Imported by `infer/__init__.py`, `shared_cause.py`, `null_competition.py`. | This is not a catalogue distance/intercept likelihood or a general dense-vector law. Reuse neither its fixed sky directions nor its physical parameter labels for the new module. |
| `htt/htt/htt/departure/response_overlap.py` | Concrete full-covariance response-rank prerequisite, with manifest/transfer bindings. | Relevant later to physical local/global response separation; does not itself supply the required physical responses. |
| `htt/htt/htt/departure/local_global_mixture.py` | Explicitly a gated mixture skeleton. Once supplied rank, local-null and survey-null gates pass, evaluates a normalized Gaussian on separately supplied local/global/systematic/noise response blocks. | Do not call the proposed endpoint fit a ready global-tilt mixture. Existing builder needs evidence and responses absent from the theory-only port. |
| `htt/htt/htt/departure/posterior_pushforward.py` | Downstream HTT posterior diagnostic report with explicit prerequisite statuses and MIO-input rejection. | A regression estimate is not a posterior sample bundle, and neither produces an empirical geometry label. |
| `htt/htt/htt/infer/joint_survey_hierarchy.py` | Schema-only fail-closed cross-survey contract requiring cross covariance, mask/selection, calibration, shared LSS covariance and held-out prediction. `obsstat/catalogs/cf4.py` and `spectroscopic_dipole.py` reference it by name. | A combined inventory is not an independence assertion or joint likelihood. |
| `htt/htt/htt/infer/r7_gaussian_law.py` | Implemented normalized Gaussian density, PSD support decomposition, explicit unresolved-rank handling, and `JointObservationLaw` with ordered identities, domain, selection law, covariance source and bound callable/specification identity. | Best existing likelihood primitive for the pre-data route. No estimated-covariance calibration is supplied automatically. |
| `htt/htt/htt/infer/r7_joint_experiment.py` | Supplied full joint covariance, duplicate-measurement checks, unknown cross-dependence preservation, nuisance-projected response analysis and fixed observation-space comparisons. | Reuse once there is an actual bound observation law. It must not invent cross-probe covariance. |
| `htt/htt/htt/infer/r7_confidence.py` | Fixed known-Gaussian acceptance inversion and joint-set projection. It retains rank(C) residual degrees of freedom and distinguishes unresolved numerics from rejection. | Compatible future conditional joint-set consumer; do not subtract fitted parameters from its acceptance rank or substitute an optimizer's extrema for certified outer bounds. |
| `scripts/observed_runs/run_tensor_joint_r7.py` | Concrete consumers: `joint()` and `model_comparison()` call R7 joint/comparison helpers; campaign source lists bind Gaussian, confidence and catalogue modules. Its public entry point is stated as `run_r7_campaign.py`. | These are existing callable campaign paths. They were not executed here and should not be dispatched for this port. |
| `htt/obsstat/directional_cosmography.py` and `scripts/codex_harness/run_pr179_directional_cosmography.py` | Real producer: `build_generation()` calls `analyze_directional_cosmography()`. Frozen CF4 group relation uses `vcmb/c`, redshift cuts, distance-modulus response, diagonal sigma, fixed folds and null calibration. Docstring explicitly says H_cat/q_cat are catalogue coefficients, not physical fields or HTT likelihood products. | Its nuisance intercept is not the full angular zero-distance redshift intercept. Do not relabel its results as TBO-02/03 or run it as part of this port. |

## Current owned-data lanes

`scripts/analyze_owned_observations.py` imports OBSSTAT implementations and dispatches:

| Lane | Actual dispatch | Status semantics in source |
|---|---|---|
| DATA-01 | `owned_data_adapter.load_matrix`, `bind_owned_products`, `binding_report` | Exactly 52 inventory rows; paths, sizes, hashes and bounded schemas. Does not establish a sampling law. |
| DATA-02 | `spectral_residual_analysis` | Available spectrum diagnostics; theory alignment; missing/invalid products skipped. |
| DATA-03 | `owned_lowell_analysis.analyze_nside16_map` | Available Planck NSIDE16 map/mask extraction. |
| DATA-04 | `catalogs.owned_desi_analysis.summarize_desi` | Available NPZ catalogue summaries. |
| DATA-05 | `owned_cf4_query_analysis.summarize_cf4_queries` | Query-batch depth summaries, not raw independent distance/redshift inference. |
| DATA-06 | No call | `NOT_REQUESTED_NO_COMPLETE_LIKELIHOOD_LAW`. |
| DATA-07 | No call | `NOT_REQUESTED_NO_PHYSICAL_RESPONSE_OR_JOINT_BODY`. |

`owned_data_adapter._availability()` sets covariance `AVAILABLE` from a field name containing `cov`; this is discovery metadata, not validation of matrix shape, row order, frame, sampling law or cross-probe covariance. An additive likelihood must perform its own numerical/semantic checks. `tests/contracts/test_owned_analysis_cli.py` covers an executable synthetic DATA-02 CLI fixture; it does not certify empirical inference. Preserve `cross_survey_combination=NOT_PERFORMED`, `scientific_claim_promotion=False`, and the unrequested DATA-06/07 lanes unless a later specifically authorized integration actually supplies the missing law. Do not add an automatic real-catalogue dispatch for this pre-data task.

## Smallest compatible implementation recommendation

Add one HTT-owned module, e.g. `htt/htt/htt/infer/endpoint_cosmography.py`, and focused synthetic tests. It should be callable from explicit arrays/configuration and have no data discovery, catalogue loading, plotting or production artifact side effects. A short integration note can name the future owned-data consumer without pretending it is wired today.

Use the declared observation model

`1 + z_i = zeta_0 + zeta_vector · n_i + (d_A_i / c) * (h_0 + h_1 · n_i + q : n_i n_i) + r_i`,

with symmetric trace-free `q`. This is four free intercept plus nine slope coefficients, hence 13 columns before extra nuisances. The existing Cartesian STF basis is `(nx²−nz², ny²−nz², 2nxny, 2nxnz, 2nynz)`. Explicitly distinguish a statistical unrestricted intercept estimate from the physical unit-hyperboloid condition `zeta_0²−|zeta|²=1`, `zeta_0>=1`. Noise means that a point estimate need not satisfy this condition; do not silently renormalize it into a physical velocity. A constrained physical branch, if supplied, must constrain the joint law/domain and preserve its uncertainty.

Input contract should require:

- Finite unit sourceward directions; physical distance units; explicit speed-of-light units; `d_A` distance kind. Luminosity distance conversion is `d_L/(1+z)^2` under reciprocity, whereas the endpoint invariant is `d_L/(1+z)`; they must not share a field name. A nontrivial conversion with noisy redshift/distance changes their joint error law.
- Named observed redshift frame and correction history, direction tetrad/frame, source material component/congruence, observer reference and direction convention. Missing history cannot become an implicit CMB-rest correction. Coordinates such as Galactic are distinct from velocity/redshift reference frames.
- Ordered unique row IDs and covariance row IDs, full dense covariance, and explicit fixed boolean support selection. Select `C[np.ix_(indices, indices)]` in the same order as every observable/design row. Neither a precision submatrix nor discarded off-diagonals gives the selected marginal covariance.
- Explicit law/conditioning scope. The smallest implemented branch may condition on fixed, exact `d_A`/directions and a known Gaussian redshift law. It must state this limitation. Real distance errors, calibration zero points, outcome-dependent selection or cross-probe dependence require a supplied joint/latent law; they are not covered by declaring a covariance identity.
- Explicit finite-distance/extrapolation remainder treatment. A caller-supplied zero remainder is an exact truncated-model assumption, not an empirical finding. Nonzero deterministic bounds are nuisance sets or bound propagation, not Gaussian variance; no automatically estimated bound. Missing/unbounded remainder should leave the physical distance-zero interpretation unresolved. Cosmological smoothing across the virial region belongs to this applicability contract.

Reuse `r7_gaussian_law.gaussian_loglik` or `JointObservationLaw` for normalization and covariance semantics, and `r7_confidence` only if the exact declared conditional law/domain warrants its existing coverage theorem. For an SPD-only regression MVP, reject singular/near-unresolved covariance rather than add jitter. Use whitened SVD/QR with rank and scale-aware conditioning checks, report all coefficient covariance including intercept–slope cross terms, and fail closed on aliased designs. `nuisance_rank.nuisance_projected_rank` is a useful existing diagnostic, but it symmetrizes its covariance and has an absolute scale floor; validate covariance independently and avoid importing its thresholds as a universal numerical rule.

OBSSTAT `mes_directional_moments.estimate_joint_fit_directional_moments()` already binds frame/mask identities and the nine-column angular basis, but takes scalar weights and an exact ell<=2 field. Its public estimator is not the 13-column dense joint fit. `obsstat.cf4_current_stack.build_cf4_affine_design()` has a different nine-column radial-flow interpretation, also not a replacement. Reuse conventions and tested numerical patterns; do not call private helpers as public API or turn an OBSSTAT extractor into the HTT likelihood owner. A broad shared-contract refactor is unnecessary for this single new consumer.

Output should preserve `endpoint/source U relative to observer O` separately from `matter U relative to homogeneous normal N`. With only this law, the latter is unavailable. The Hubble lift must remain conditional on geodesic U and a unique future timelike eigenline; arbitrary acceleration or an unresolved/degenerate line blocks that interpretation. A point eigenvector is not finite-error eigenline coverage. No vorticity follows from the symmetric Hubble contraction. Keep full vector/STF content rather than reducing immediately to an amplitude or MES percentage.

## Focused validation recommendation

1. Recover nonzero free monopole/dipole intercept and all nine slope coefficients from a full-rank synthetic angular/depth design; show forced-zero intercept changes the slope, so this test catches the actual historical failure mode.
2. Use a dense correlated covariance oracle. Check normalized log density and recovered coefficient covariance against direct small linear algebra, retaining off-diagonals and intercept–slope covariance.
3. Permute rows and matching covariance IDs; result is invariant. Mismatched IDs fail. Apply a nontrivial mask and compare with independently selected rows/covariance, catching precision-submatrix mistakes.
4. Check rank failure for one distance shell: intercept angular columns alias corresponding slope angular columns. Check insufficient/degenerate angular support and ill conditioning; no minimum-norm physical solution should escape as identified.
5. Reject invalid covariance, nonunit/nonfinite directions, mismatched shapes, wrong distance kind or unresolved frame/correction history. Test zero/bounded/unavailable remainder statuses and confirm no unknown bound silently becomes zero.
6. Keep endpoint-versus-normal output tags distinct; missing N never yields eta_UN or an empirical tilt/Bianchi label. Test noisy intercept incompatibility is reported rather than projected silently onto the unit hyperboloid.
7. If theory helpers are connected, check intercept sign convention, Lorentz-boosted geodesic Hubble tensor, timelike degeneracy, and the difference between `d_A` and endpoint-invariant distance. These are synthetic algebraic tests, not observation coverage tests.

Relevant existing narrow regressions: `tests/r7/test_gaussian_law.py`, `tests/r7/test_catalogue_laws.py`, `tests/r7/test_joint_experiment.py`, `tests/htt/test_nuisance_rank.py`, and the new test module. Run only those touched by actual imports/changes; none were run during this mapping. Avoid `scripts/analyze_owned_observations.py`, PR-179 producers and full campaign runners in the present task.

## Decision and remaining uncertainty

Recommend implementation of the isolated HTT conditional law/regression surface; do not couple it into the owned-data dispatcher yet. Confidence is high for ownership and source-level reuse, medium for whole-repository routing because the inspected material is a verified subset and no production execution receipt was audited. The remaining observational inputs are frame/correction history, actual independent distances and shared source/calibration covariance, selection law, finite-distance remainder, and independent geometric-normal reconstruction. Their absence is a scientific limitation, not a reason to fabricate model metadata or classify current catalogues.
