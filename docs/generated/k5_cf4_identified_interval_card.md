# K5 CF4 Identified-Interval Diagnostic Card

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
artifact_mode: external_audit_conditioned
config_hash: `sha256:6419242c1eb6ce67f8442386b8d014e2ba8bf36e36f58561d24fbbecf091084a`
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
| W2_upper | `REGISTERED_MES_CEILING` |
| Omega_k_upper | `PLUGIN/BLOCKED` |
| K1_maxscan | `REAL_DIAGNOSTIC_INPUT_NOT_USED_AS_SIGMA2` |
| MES_coefficients | `REGISTERED_EXTERNAL_NOT_REDERIVED` |

## Branch Intervals

| Policy | Branch | Status | Interval | IM 95% CI |
| --- | --- | --- | --- | --- |
| `measurement_only` | `open_branch[0,Uk]` | `FEASIBLE` | [-9.235304e-07, 2.682811e-05] | [-1.128613e-05, 3.719071e-05] |
| `measurement_only` | `all_branch[-Uk,Uk]` | `FEASIBLE` | [-1.923530e-06, 2.682811e-05] | [-1.228613e-05, 3.719071e-05] |
| `cosmic_variance_inclusive` | `open_branch[0,Uk]` | `FEASIBLE` | [-1.308680e-06, 2.683960e-05] | [-1.167900e-05, 3.720992e-05] |
| `cosmic_variance_inclusive` | `all_branch[-Uk,Uk]` | `FEASIBLE` | [-2.308680e-06, 2.683960e-05] | [-1.267900e-05, 3.720992e-05] |

## Caveats

- Diagnostic pipeline-closure card only.
- W2 ceiling is the registered MES value (3/2)B_omega^2 from the ssot epsilons.
- Sigma2 and Omega_k placeholders still block observational promotion.
- No posterior odds, native low-ell solver output, or morphology-family promotion.
