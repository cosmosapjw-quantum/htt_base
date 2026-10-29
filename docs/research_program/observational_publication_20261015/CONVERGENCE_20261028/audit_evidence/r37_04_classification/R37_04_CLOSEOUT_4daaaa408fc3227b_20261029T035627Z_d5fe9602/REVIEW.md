# Physics/math audit verdict

SCOPED_PASS_TARGETED_CLOSEOUT for candidate sha256:b1a0eec816b5d922349d17aaa0afc3ce8b58c83154c8a2f7427f1965212d085a. The prior adequacy-figure defect is closed. Qualified product: physical_family_compatibility, solely as the declared finite conditional supplied-family method.

## Assumptions and conventions

Two retained instantaneous spatial-Ricci fixtures, each scaled by the same fixed amplitude a in [0,1], with independent proper SO(3) orientations. Oriented orthonormal hypersurface-normal frame; signature (-,+,+,+); epsilon123=+1. Tensor/noise/error units are u_star^2 and amplitude is dimensionless. Raw data have trace/sqrt(3), STF5 and calibration coordinates, isotropic sigma^2 I7 noise, one common trace-plus-calibration nuisance and one joint deterministic response-error radius. No observed curvature covariance or native sky transfer is supplied.

## Equation and definition audit

| Item | Status | Evidence |
|---|---|---|
| 7-to-6 nuisance quotient | PASS | Independent 6x7 map has orthonormal rows, rank 6 and annihilates the nuisance. Exact chi-square(6) CDF at the declared quantile is 0.95. |
| Actual raw-shift curve | PASS | All 200 captured points obey abs(s)/sqrt(2); horizontal line is tau=0.5258155191041224. |
| Witness and counterexample | PASS | Marker is (1,0.7071067811865475); s=0.6 gives 0.42426406871192845 and compatible set [II]. Raw-axis threshold is 0.7436154384232991. Checks immediately below/above threshold retain/reject II. |
| Sealed figure | PASS | Actual plot-only replay and sealed candidate PDF render to identical 640x420 RGB pixels; max channel difference 0. |
| 135 numerical rows | PASS | Byte-identical to preserved original; independent spectral-permutation evaluation yields max numeric difference 8.881784197001252e-16 and zero membership differences. |
| STF5 versus adequacy | PASS | 75 deterministic fixed-amplitude orientation comparisons preserve pairwise LR to 8.881784197001252e-16. Independently varying amplitudes produce 0.0390625 LR discrepancy when trace is omitted, agreeing with the explicit warning. |
| Common fixed amplitude | PASS | Domain and report explicitly condition on one shared amplitude; no independently fitted-amplitude separation certificate is asserted. |
| Spatial-Ricci origin | PASS | Text explicitly rejects inference of full FLRW. Retained flat control has extrinsic STF norm 0.12247448713915901. |
| Strong scalar baseline and fixed-Q radius | RETAINED | Frozen numerical fields unchanged; targeted local tests pass. Prior review remains the source for the unchanged broader mathematical checks. |

## Dimensional/sign/limit checks

A raw trace-coordinate shift s projects to abs(s)/sqrt(2). The seven-coordinate noise law projects orthogonally to six isotropic coordinates. The STF5 carrier preserves fixed-amplitude family likelihood ratios because the family trace means coincide; its discarded coordinate must remain for all-family adequacy. A=0 denotes coincident spatial-curvature images only. Spatial curvature scales as a^2; the positive-amplitude fixed-common-scale gap and source-qualified a=1 error radii remain unchanged.

## Claim-tier implications

Accept physical_family_compatibility only for the source-qualified finite geometry-response method and retained fixed-Q sign-radius example. This supplies no empirical CMB/Bianchi identification, full T/E/B atlas, native solver result, broad scalar-information impossibility claim, or additional information over the same joint law. Original42 acceptance is unchanged. This review is not a new four-axis CAS admission.

## Fatal blockers

None for this candidate and the frozen targeted closeout.

## Safe claims

The repaired adequacy plot now gives the same retention/rejection decision as the declared joint event. The finite supplied-family compatibility result retains common law, nuisance, amplitude, rotation, adequacy and approximation-error restrictions. Both spatial-Ricci origin overlap and equivalent flat presentations remain explicit.

## Required tests or artifacts

Independent closeout script: PASS. Existing four targeted tests: PASS. Nonfatal Matplotlib Axes3D import warning is preserved in raw logs; all required plots are 2D. Nine candidate artifact hashes and sizes, all six frozen input hashes, two historical review/repair receipt hashes, the original producer receipt, predecessor candidate seal and source status seal match. Only the five intended artifacts differ from the old manifest; the result JSON changes only script_sha256 and flrw_origin. No candidate, repository, STATE or Git writes; no old producer, Monte Carlo, solver, ODE or child-agent execution.

