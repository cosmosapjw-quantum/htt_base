# K5 CF4 Identified-Interval Diagnostic Card

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
artifact_mode: external_audit_conditioned
config_hash: `sha256:32779452961391487d6273a47043a3876d2d42049c57e4541c3165f2d1090aca`
generating_command: `venv/bin/python scripts/k5_cf4_identified_interval_card.py`
observational_claim_allowed: false

## Component Modes

| Component | Input mode |
| --- | --- |
| CF4_bulk_amplitude | `REAL` |
| Omega_m | `DECLARED_OBS_DEFAULT` |
| Omega_tilt_formula | `DERIVED_FROM_PARENT_IDENTITY_SEAL` |
| Sigma2_hat | `PLUGIN/BLOCKED` |
| Sigma2_error | `PLUGIN/BLOCKED` |
| W2_upper | `PLUGIN/BLOCKED` |
| Omega_k_upper | `PLUGIN/BLOCKED` |
| K1_maxscan | `REAL_DIAGNOSTIC_INPUT_NOT_USED_AS_SIGMA2` |
| MES_coefficients | `REGISTERED_EXTERNAL_NOT_REDERIVED` |

## Branch Intervals

| Policy | Branch | Status | Interval | IM 95% CI |
| --- | --- | --- | --- | --- |
| `measurement_only` | `open_branch[0,Uk]` | `FEASIBLE` | [-5.108123e-07, 2.682811e-05] | [-1.087341e-05, 3.719071e-05] |
| `measurement_only` | `all_branch[-Uk,Uk]` | `FEASIBLE` | [-1.510812e-06, 2.682811e-05] | [-1.187341e-05, 3.719071e-05] |
| `cosmic_variance_inclusive` | `open_branch[0,Uk]` | `FEASIBLE` | [-8.959622e-07, 2.683960e-05] | [-1.126628e-05, 3.720992e-05] |
| `cosmic_variance_inclusive` | `all_branch[-Uk,Uk]` | `FEASIBLE` | [-1.895962e-06, 2.683960e-05] | [-1.226628e-05, 3.720992e-05] |

## Caveats

- Diagnostic pipeline-closure card only.
- Sigma2, W2, and Omega_k placeholders block observational promotion.
- No posterior odds, native low-ell solver output, or morphology-family promotion.
