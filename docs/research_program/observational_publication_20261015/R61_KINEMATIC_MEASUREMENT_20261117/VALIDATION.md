# R61 validation and evidence map

Baseline commit: `fb6ae9f21585e194ef29dabc91d79a529e0ac57e`. Runtime: existing repository `.venv`, Python 3.12.3, NumPy 2.5.4 and SciPy 1.18.1, one BLAS thread. No new environment or catalog-sized covariance computation was created.

## Actual execution

| Check or calculation | Observed result | Evidence |
|---|---|---|
| Original R61 image and mixed tests | 24 passed; process exit0 | RESULTS/TESTS_EXECUTION.log; RESULTS/BATCH_EXECUTION.json |
| Actual kinematic images | exit0; 7 variants, 2 covariance settings, 4 calibration settings | RESULTS/IMAGES/KINEMATIC_IMAGES.json |
| Actual depth response | exit0; rank16; nested Wald/LR identity; source/operator parity | RESULTS/DEPTH_CORRECTED/KINEMATIC_DEPTH.json |
| Actual mixed invariant | exit0; 28 cases; maximum endpoint gap 9.9974e-11 | RESULTS/MIXED/R61_MIXED_INVARIANT_RESULT.json |
| Added box-extremum mathematical tests | 10 passed; process exit0 | RESULTS/BOX_TESTS_EXECUTION.log; RESULTS/BOX_EXECUTION.json |
| Actual coordinate-box comparison | exit0; same 28 existing mixed endpoints reused | RESULTS/BOX_COMPARISON/R61_BOX_COMPARISON_RESULT.json |
| Final current-tree tests | 34 passed; process exit0 | RESULTS/FINAL_CURRENT_TESTS.log; DAG_VALIDATION.json |
| Canonical and publication DAG gates | all six structural commands exit0; 285 cards, original42 nodes preserved | DAG_VALIDATION.json |
| Saved-result table generation | completed without refitting | RESULTS/NUMERICAL_SUMMARY.json; RESULTS/NUMERICAL_TABLES.md |
| Figures | all four primary figures and revised constraints figure visually inspected | RESULTS/FIGURES/FIGURE_MANIFEST.json; ARTIFACT_MANIFEST.json |
| Independent final review | PASS WITH MINOR REVISIONS; required finding R61-F1 closed by targeted evidence | REVIEW/final_review.md; REVIEW/R61_F1_CLOSURE.json |

The original 24 and 10 tests remain separate historical runs. The final current-tree run independently reports **34 passed** in RESULTS/FINAL_CURRENT_TESTS.log (exit0, 19.37 seconds). These are the same 34 cases, not 68 independent checks. The original images test run separately reported 13 passed after correcting the independent oracle scaling; it is not counted again.

## Mathematics and numerical checks

`r61_kinematic_images.py` handles interior, boundary and hard-case trust-region solutions. Feasible witnesses are paired with a global quadratic dual bound and numerical gap. Hand extrema, an independent scaled Cartesian SLSQP oracle, rotation covariance, calibration normalization, invalid input and random-point enclosure checks are recorded by the tests. Exact-arithmetic characterization and float64 implementation are distinguished.

`r61_mixed_invariant.py` projects the original 11D ellipsoid to beta/kappa with the original cutoff, conditionally removes kappa, and includes the analytic calibration support. Branch upper bounds and feasible witnesses, not a multistart optimum alone, establish the reported numerical enclosure. Rotation, conditional lift, direct 8D point checks, local-box bound falsification checks and input rejection are recorded in RESULTS/ISOLATED_MIXED_VALIDATION.json. Random samples are checks, not the mathematical proof of an upper bound.

`r61_box_comparison.py` enumerates 32 kappa corners and 27 beta-box faces per endpoint. Tests cover indefinite and PSD forms, nonzero box centers, consistent/inconsistent singular stationary sets, collapsed intervals, one-dimensional analytic cases and ambiguous numerical rank. In the actual 28 comparisons no singular face was encountered. The largest retained condition number was about 11976.7 and the maximum numerical guard was 2.522e-18. The finite-face characterization is complete in exact arithmetic; its float64 guard is not a formal interval certificate.

The depth runner verifies the reused raw/source operators, full rank, covariance, Wald/LR identity, common-calibration injection invariance, nonlinear fit agreement from two starts, inactive numerical bounds and all-sky positivity of the fitted angular factor. The finite-depth physical bridge and general-spacetime remainder remain assumptions; implementation checks do not supply missing physical transfer.

Wolfram symbolic outputs for the STF norm, calibration support and hard-case minimum are transcribed in RESULTS/SYMBOLIC_CHECKS.json. Explicit warnings are preserved. Hand derivations and numerical checks support the accepted expressions; no formal proof-assistant result is claimed.

## Preserved failures and classification

- **Independent numerical oracle:** first unscaled SLSQP check failed its line search near the optimum. Objective and constraint were normalized; strict feasibility and objective agreement remained required. Production solver unchanged. See DEVELOPMENT_TESTS.log and ORACLE_DIAGNOSTIC.json.
- **Numerical optimization limit:** deliberately degenerate isotropic mixed-function stress hit its node cap at rho=.01 with remaining gap. That stress remains in ISOTROPIC_STRESS.json and is not marked converged. The 28 actual source cases are a separate successful calculation.
- **Local runtime:** scratch Python lacked pytest. Local pytest was not claimed to pass; native repository pytest supplied actual evidence.
- **Transport:** one initial remote start_process request failed with connection error and no execution PID/log. Device status and log existence were inspected, and the later successful native run is recorded. This was not a physics or test failure.
- **Interpretation correction:** original cubic absolute component bound combined coordinate-box replacement with additional triangle slack. Actual-box comparison was added so the effects are separately quantified. The original loose enclosure is retained with its correct label.

## Claim boundary

Results are conditional on the fixed Gaussian likelihood, chosen mean response, covariance family and calibration body. No release-matched survey coverage, independently measured calibration bound, absolute H/Theta, vorticity, general local shear history, occupancy measure or Bianchi identification is supplied. A 5D marginal interval, 11D joint image and 16D depth image have different confidence objects. Seven source variants are not independent likelihood factors.

Actual-box comparison quantifies replacing the entire joint domain by its coordinate-support box. It neither isolates covariance off-diagonal contributions nor demonstrates information gain over a full GLS likelihood.

## Review and final release

One fresh independent R9/C9 review applies to final scientific code, source/results, theory and report. R61-F1 restricted depth-dependent calibration budgets to the fitted affine-z STF subspace or the actual estimator-induced bias. The corrected runner releases a 5x32 contrast-bias operator and reproduces the endpoint-zero counterexample. The affected depth component alone was run into DEPTH_CORRECTED with exit0. All 6159 pre-existing numeric leaves compared equal (runtime/implementation metadata excluded), and every original response array had identical dtype, shape and bytes. The original DEPTH result and executed runner snapshot remain historical evidence. No second full review was required. Final release also validates canonical PR DAG and compatibility mirrors while preserving 42 original scientific node states. Structural validation does not certify scientific submission readiness.


Release formatting check: the first staged diff check found an extra EOF blank line in the review text and independent oracle file. Only trailing newline bytes were normalized; the manifest records old/new hashes. The subsequent staged diff check passed.
