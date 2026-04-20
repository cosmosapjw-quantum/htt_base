# VER2 Validation Campaigns

## Status

- Authority: `docs/ver2_upgrade/*`
- Packet owner: `SK-08V`
- Machine-readable registry: `htt/workspace/contracts/validation_registry.py`
- Current status model: `pass` / `warn` / `fail`

`warn` means the campaign exists and is tracked, but it does not promote any claim to `validated`.

## Campaign registry

| Campaign ID | Status | Blocking | Theorem refs | Categories | No-claim conditions |
|---|---|---|---|---|---|
| `validation.flrw_baseline` | `warn` | yes | `V8_isotropic_limit_recovery`, `V8_biposh_Lgt0_null_or_proxy_block` | `baseline_reproduction`, `regression` | `sparse_proxy_only`, `missing_biposh_basis` |
| `validation.false_promotion` | `warn` | yes | `V8_local_vs_global_discrimination`, `V8_tsc_no_overclaim` | `adversarial_edge`, `regression` | `missing_null_ensemble`, `posterior_correction_attempted` |
| `validation.mes_no_claim` | `warn` | yes | `V8_mes_rank_no_claim`, `V8_filling_requires_certification` | `physics_sanity`, `numerical_stability` | `response_rank_deficient`, `claim_gate_not_passed` |

## Null / injection manifests

### Null ensembles

| ID | Family | Basis | Status | No-claim conditions |
|---|---|---|---|---|
| `null.flrw_isotropic_gaussian_lowell` | `flrw_isotropic_gaussian` | `lowell_alm_features` | `warn` | `missing_scan_volume`, `missing_tail_calibration` |
| `null.local_boost_only` | `observer_local_boost_only` | `directional_power_and_coherence` | `warn` | `missing_null_identity`, `missing_false_promotion_check` |

### Injection campaigns

| ID | Hypothesis family | Target statistic | Status | Downgrade conditions |
|---|---|---|---|---|
| `validation.injection.template_amplitude` | `deterministic_template` | `template_amplitude_recovery` | `warn` | `missing_injection_grid`, `missing_recovery_tolerance` |
| `validation.injection.anisotropic_covariance` | `anisotropic_covariance` | `covariance_feature_recovery` | `warn` | `covariance_sampler_unavailable`, `proxy_mode_only` |

## Export rule

Manuscript export is blocked if any manuscript-blocking campaign reaches `fail`.

## Check command

```bash
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check
```
