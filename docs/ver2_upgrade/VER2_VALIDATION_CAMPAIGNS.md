# VER2 Validation Campaigns

## Status

- Authority: `docs/ver2_upgrade/*`
- Packet owner: `IM-08V`
- Machine-readable registry: `htt/workspace/contracts/validation_registry.py`
- Current status model: `pass` / `warn` / `fail`
- Current phase state: executable minimal campaign set active; every campaign now resolves to live test entrypoints and covers all five required categories.

`warn` means the campaign is executable and checked, but it still does not promote any scientific claim to `validated` by itself. `pass` is allowed only for bounded executable evidence that is explicitly narrower than the remaining science-claim surface.

## Campaign registry

| Campaign ID | Status | Blocking | Theorem refs | Null / injection refs | Runbook refs | Categories | No-claim conditions |
|---|---|---|---|---|---|---|---|
| `validation.bass_native_runtime_bridge` | `pass` | no | `V8_bass_native_runtime_bridge` | `null.bass.type_i_native_runtime`, `validation.injection.native_seed_startup` | `runbook.bass_native_runtime` | all five required categories | `tier_a_validation_bridge_only`, `non_type_i_exact_propagator_missing` |
| `validation.observable_null_proxy` | `warn` | yes | `V8_isotropic_limit_recovery`, `V8_biposh_Lgt0_null_or_proxy_block` | `null.flrw_isotropic_gaussian_lowell`, `validation.injection.anisotropic_covariance` | `runbook.observable_promotion` | all five required categories | `sparse_proxy_only`, `missing_biposh_basis` |
| `validation.synthetic_injection` | `warn` | yes | `V8_template_injection_recovery`, `V8_local_vs_global_discrimination` | `null.flrw_isotropic_gaussian_lowell`, `null.local_boost_only`, `validation.injection.template_amplitude` | `runbook.semantic_firewall` | all five required categories | `missing_injection_campaign`, `missing_null_ensemble`, `missing_scan_volume` |
| `validation.mes_claim_gates` | `warn` | yes | `V8_mes_rank_no_claim`, `V8_filling_requires_certification` | `null.flrw_isotropic_gaussian_lowell` | `runbook.observable_promotion` | all five required categories | `response_rank_deficient`, `claim_gate_not_passed`, `occupancy_not_certified` |
| `validation.semantic_firewall` | `warn` | yes | `V8_local_vs_global_discrimination`, `V8_tsc_no_overclaim` | `null.local_boost_only`, `validation.injection.anisotropic_covariance` | `runbook.semantic_firewall` | all five required categories | `posterior_correction_attempted`, `missing_tsc_overlay`, `missing_response_library` |

## Category coverage

| Campaign ID | Baseline reproduction | Edge / adversarial | Physics sanity | Numerical stability | Regression |
|---|---|---|---|---|---|
| `validation.bass_native_runtime_bridge` | `type_i_observable_null_recovery` | `native_seed_projection_survives_without_startup` | `tier_a_tier_b_type_i_bridge_matches` | `tier_b_cutoff_campaign_stays_bounded` | `tier_b_runtime_consumes_live_hooks_and_exact_type_i_propagator` |
| `validation.observable_null_proxy` | `flrw_limit_zero_offdiag` | `rotating_types_activate_offdiag_blocks` | `proxy_mode_records_no_claim` | `anisotropic_te_is_finite` | `type_i_observable_marks_isotropic_null_proxy` |
| `validation.synthetic_injection` | `null_mock_zero_mean` | `injected_dipole_projection_recovered` | `local_boost_and_global_tilt_are_not_merged` | `synthetic_injection_coverage_reaches_nominal_band` | `tier_b_runtime_consumes_live_hooks` |
| `validation.mes_claim_gates` | `mes_covariance_bound_live` | `mes_rank_failure_returns_no_claim` | `uncertified_f_downgrades_to_proxy` | `mock_coverage_within_published_window` | `full_cov_contract_rejects_negative_rank` |
| `validation.semantic_firewall` | `directional_manifest_not_posterior` | `policy_rejects_tsc_posterior_correction` | `response_library_keeps_local_and_global_distinct` | `axis_gate_requires_adequate_mock_coverage` | `tsc_quarantine_flags_emitted` |

## Null / injection manifests

### Null ensembles

| ID | Family | Basis | Status | Theorem refs | Campaign refs | No-claim conditions |
|---|---|---|---|---|---|---|
| `null.bass.type_i_native_runtime` | `type_i_native_runtime_null` | `ver2_native_pstf_sphere_reconstruction` | `pass` | `V8_bass_native_runtime_bridge` | `validation.bass_native_runtime_bridge` | `tier_a_validation_bridge_only`, `non_type_i_exact_propagator_missing` |
| `null.flrw_isotropic_gaussian_lowell` | `flrw_isotropic_gaussian` | `lowell_alm_features` | `warn` | `V8_isotropic_limit_recovery`, `V8_template_injection_recovery`, `V8_filling_requires_certification` | `validation.observable_null_proxy`, `validation.synthetic_injection`, `validation.mes_claim_gates` | `missing_scan_volume`, `missing_tail_calibration` |
| `null.local_boost_only` | `observer_local_boost_only` | `directional_power_and_coherence` | `warn` | `V8_local_vs_global_discrimination` | `validation.synthetic_injection`, `validation.semantic_firewall` | `missing_null_identity`, `missing_false_promotion_check` |

### Injection campaigns

| ID | Hypothesis family | Target statistic | Status | Required null refs | Campaign refs | Downgrade conditions |
|---|---|---|---|---|---|---|
| `validation.injection.native_seed_startup` | `native_seed_startup` | `seeded_quadrupole_recovery` | `pass` | `null.bass.type_i_native_runtime` | `validation.bass_native_runtime_bridge` | `startup_manifold_disabled`, `seed_projection_not_ready` |
| `validation.injection.template_amplitude` | `deterministic_template` | `template_amplitude_recovery` | `warn` | `null.flrw_isotropic_gaussian_lowell` | `validation.synthetic_injection` | `missing_injection_grid`, `missing_recovery_tolerance` |
| `validation.injection.anisotropic_covariance` | `anisotropic_covariance` | `covariance_feature_recovery` | `warn` | `null.flrw_isotropic_gaussian_lowell`, `null.local_boost_only` | `validation.observable_null_proxy`, `validation.semantic_firewall` | `covariance_sampler_unavailable`, `proxy_mode_only` |

## Export rule

Manuscript export is blocked if any manuscript-blocking campaign reaches `fail`. A `warn` campaign remains explicitly no-claim.

`validation.bass_native_runtime_bridge` is intentionally not manuscript-blocking. It is a bounded BF-05 runtime-evidence campaign for the shipped Type-I native route, not a promotion of the remaining morphology/likelihood/inference science claims.

## Check commands

```bash
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_hostile_audit.py --check
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --check
```
