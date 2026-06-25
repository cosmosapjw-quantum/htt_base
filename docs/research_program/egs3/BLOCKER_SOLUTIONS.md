# EGS3 Blocker Solutions

| Blocker | Concrete solution | Mechanics (landed) | Real-input ticket |
|---|---|---|---|
| BLOCKED_MISSING_PR4_E2E_ACCESS | run the frozen K1 max-scan on the public PLA FFP10 (999 CMB + 300 noise MC/method) + NPIPE (~300 E2E) sims; +1-corrected global p | `lowell_global_calibration.e2e_maxscan_from_summaries` | `tickets/k1_ffp10_npipe.yaml` |
| BLOCKED_MISSING_FIELD_REALIZATIONS | Hoffman-Ribak CR ensemble on the 3D CF4 WF field; CR spread = vorticity posterior | `constrained_realizations.curl_posterior` | `tickets/cf4_wfcr.yaml` |
| BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP | CF4 Bias-Gaussianization WF/CR forward mocks; GLS per mock -> cosmic-variance coverage | `bulkflow_mle.hierarchical_coverage_experiment` + CR ensemble | `tickets/cf4_wfcr.yaml` |
| AWAITING_NATIVE_LOWELL_SOLVER | interim semi-native shear->quadrupole transfer (B1, single mode, real visibility); PR10 native remains the full atlas | `bass/transfer/shear_quadrupole_seminative.py` | `../egs2/tickets/semi_native_shear_to_quadrupole.yaml` |

Priority: K1 (highest leverage, public sims) -> CF4 WF/CR (posteriors) ->
real CAMB visibility into B1 -> NT2-A1/B1 quoted on real Planck a2,a3,f_sky.
None requires the native solver to make real progress.
