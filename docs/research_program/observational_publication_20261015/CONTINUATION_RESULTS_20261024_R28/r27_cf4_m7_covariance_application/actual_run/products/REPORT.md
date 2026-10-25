# Actual CF4 M7 covariance application

Serialized binary64 inputs were lifted to exact dyadic rationals. Exact identities and ranks apply only to those frozen entries. Numerical eigenvalues and square roots are diagnostics, without a rigorous radius.

| Map | Exact rank | t_first (mag²) | t_match (mag²) | t_spec_match (mag²) |
|---|---:|---:|---:|---:|
| nominal | 5 | 0.09898491124139373 | 37.591353687848915 | 23.357381845966675 |
| witness_round_nearest | 5 | 0.09924026819591455 | 37.62069689233363 | 23.41709182135179 |
| witness_one_place_outer | 5 | 0.09956796335493294 | 37.65070507246403 | 23.502008617400005 |

The 28 exact coefficients preserve signed channel cross terms. The unit trace cap is an illustrative mag² normalization, not an observed bound. The common-shift fixture retains its exact binary residual. The full covariance candidate retains measurement-calibration, measurement-PV, calibration-PV and all transpose blocks. J_v, empirical Gamma, residual anchor correlations, total mean/covariance, bias set, law and physical response remain unresolved.

Physical confidence: HOLD_MISSING_TOTAL_MEAN_COVARIANCE_RESPONSE_ASSUMPTIONS. Physical x, F, Pi, Q and G_F remain HOLD. Historical R9 UNKNOWN, original 17/42 and alternative 18/42, 48-task and one-use allocations remain unchanged.
