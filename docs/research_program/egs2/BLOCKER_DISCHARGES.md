# EGS2 Blocker Discharges (public data + published methods)

Three of the report's four standing blocks are dischargeable now without the
native low-ℓ solver. Each discharge is implemented as runnable *mechanics* in the
repo; the real-input run keeps its registered blocker code until the input is owned.

| Block | Discharge | Repo mechanics | Real-input gate (still blocked) |
|---|---|---|---|
| `BLOCKED_MISSING_PR4_E2E_ACCESS` (K1 global p) | run the frozen max-scan on the **public** Planck FFP10 (999 CMB + 300 noise MC/method) + PR4/NPIPE (~300 E2E) sims; +1-corrected global rank p | `obsstat/lowell_global_calibration.py:e2e_maxscan_from_summaries` | swap the synthetic stand-in for healpy reads of the PLA maps → global p + pipeline-config hash |
| `BLOCKED_MISSING_FIELD_REALIZATIONS` (K6 vorticity) | **Hoffman–Ribak** constrained realizations: the CR ensemble is the curl posterior the WF mean suppresses (mean ~0 ± prior width) | `obsstat/constrained_realizations.py:curl_posterior` | the 3D CF4 WF/CR ensemble (Hoffman et al. 2024) → realization-conditioned posterior |
| `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` (K5 cosmic variance) | the same CF4 WF/CR Bias-Gaussianization machinery generates release-matched forward mocks; GLS estimator per mock → cosmic-variance-inclusive coverage | reuse `obsstat/bulkflow_mle.py:hierarchical_coverage_experiment` + the CR ensemble | ticket `tickets/K5_release_matched_mocks.yaml` |
| `AWAITING_NATIVE_LOWELL_SOLVER` | **interim** semi-native shear→quadrupole calculator: covariant 1+3 PSTF hierarchy (Gebbie–Ellis), single shear-sourced mode, modest ℓ_max, with a **real** CAMB/CLASS recombination visibility — replaces the toy `r_ℓ` of NT2-A1 with a physically sourced response | ticket `tickets/semi_native_shear_to_quadrupole.yaml` | not the full 11-family atlas; PR10 remains the native project |

## Priority order

1. **K1** (public FFP10/NPIPE) — highest leverage, smallest effort: turns the
   low-ℓ features into a defensible *global* p-value.
2. **K6/K5** (CF4 WF/CR + forward mocks) — velocity descriptors → posteriors with
   cosmic-variance-inclusive coverage.
3. **Semi-native shear→quadrupole calculator** — replaces toy responses with real
   low-ℓ transfer; the bridge toward the native solver. Feeds NT2-A1/B1 real
   coefficients.
4. **NT2-A1/B1 with real coefficients** — quote the Fisher floor and the two-sided
   bracket on real Planck `a₂,a₃,f_sky` once (3) lands.
