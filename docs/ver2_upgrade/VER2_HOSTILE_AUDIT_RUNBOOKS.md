# VER2 Hostile Audit Runbooks

## Purpose

These runbooks are no longer prose-only buckets. Each bucket now resolves to campaign-linked check IDs, and every quarantine reason must be backed by a campaign or manifest downgrade rule.

Required hostile-audit categories:

- baseline reproduction
- adversarial edge
- physics sanity
- numerical stability
- regression

## Runbooks

### `runbook.bass_native_runtime`

- campaigns: `validation.bass_native_runtime_bridge`
- theorems: `V8_bass_native_runtime_bridge`
- baseline: `type_i_observable_null_recovery`
- adversarial: `native_seed_projection_survives_without_startup`
- physics: `tier_a_tier_b_type_i_bridge_matches`
- numerical: `tier_b_cutoff_campaign_stays_bounded`
- regression: `tier_b_runtime_consumes_live_hooks_and_exact_type_i_propagator`
- quarantine: `tier_a_validation_bridge_only`, `non_type_i_exact_propagator_missing`, `startup_manifold_disabled`, `seed_projection_not_ready`

### `runbook.observable_promotion`

- campaigns: `validation.observable_null_proxy`, `validation.mes_claim_gates`
- theorems: `V8_isotropic_limit_recovery`, `V8_biposh_Lgt0_null_or_proxy_block`, `V8_mes_rank_no_claim`, `V8_filling_requires_certification`
- baseline: `flrw_limit_zero_offdiag`, `mes_covariance_bound_live`
- adversarial: `rotating_types_activate_offdiag_blocks`, `mes_rank_failure_returns_no_claim`
- physics: `proxy_mode_records_no_claim`, `uncertified_f_downgrades_to_proxy`
- numerical: `anisotropic_te_is_finite`, `mock_coverage_within_published_window`
- regression: `type_i_observable_marks_isotropic_null_proxy`, `full_cov_contract_rejects_negative_rank`
- quarantine: `sparse_proxy_only`, `missing_biposh_basis`, `response_rank_deficient`, `claim_gate_not_passed`

### `runbook.semantic_firewall`

- campaigns: `validation.synthetic_injection`, `validation.semantic_firewall`
- theorems: `V8_template_injection_recovery`, `V8_local_vs_global_discrimination`, `V8_tsc_no_overclaim`
- baseline: `null_mock_zero_mean`, `directional_manifest_not_posterior`
- adversarial: `injected_dipole_projection_recovered`, `policy_rejects_tsc_posterior_correction`
- physics: `local_boost_and_global_tilt_are_not_merged`, `response_library_keeps_local_and_global_distinct`
- numerical: `synthetic_injection_coverage_reaches_nominal_band`, `axis_gate_requires_adequate_mock_coverage`
- regression: `tier_b_runtime_consumes_live_hooks`, `tsc_quarantine_flags_emitted`
- quarantine: `missing_injection_campaign`, `missing_null_ensemble`, `posterior_correction_attempted`, `missing_tsc_overlay`

## Check command

```bash
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_hostile_audit.py --check
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --check
```
