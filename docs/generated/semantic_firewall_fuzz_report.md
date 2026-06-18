# Semantic Firewall Fuzz Report

artifact_id: semantic_firewall_fuzz_report
owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
production_status: diagnostic_only
schema_version: common.semantic_firewall_fuzz_report.v1
transfer_source: mixed_none_and_external_transfer_controls
sky_support_status: mixed_not_directional_and_masked_controls
null_mock_status: mixed_diagnostic_null_and_constructor_controls
covariance_status: mixed_diagnostic_covariance_and_constructor_controls
config_hash: sha256:ec8b875a573eecde46b3498b44c790045ca46d88ee433112cbe594e1816202b8
generating_command: `python scripts/generate_semantic_firewall_fuzz_report.py`
git_commit_or_worktree_state: 64a47c7+dirty

## Summary

- attack_count: 15
- blocked_count: 15
- smuggle_count: 0
- leakage_path_count: 0
- publication_ready: false
- science_claim_ceiling: diagnostic-only firewall coverage; not scientific validation

## Case Matrix

| Case | Family | Surface | Blocked | Blocker |
| --- | --- | --- | --- | --- |
| reserved_public_claim_prose | reserved_language | `common.semantic_guards.no_overclaim.scan_text` | true | scan_text |
| figure_label_owner_definition_mismatch | figure_label | `scripts.verify_formalism_figure_labels.validate_rows` | true | label_registry |
| q_family_metadata | q_metadata | `mio.formalism.normalized_score.build_normalized_score` | true | ValueError |
| f_sign_dirty_sample | f_semantics | `mio.formalism.filling_fraction.build_certified_filling_fraction` | true | ValueError |
| f_super_ceiling_no_clipping | f_semantics | `mio.formalism.filling_fraction.build_certified_filling_fraction` | true | ValueError |
| f_external_ceiling_not_certified | f_semantics | `mio.formalism.budget_spec.BudgetSpec` | true | ValueError |
| f_observational_ceiling_not_certified | f_semantics | `mio.formalism.budget_spec.BudgetSpec` | true | ValueError |
| pi_curve_only_selected_threshold_smuggle | pi_semantics | `mio.formalism.exceedance.build_exceedance_curve` | true | ValueError |
| pi_post_hoc_threshold_selection | pi_semantics | `mio.formalism.exceedance.build_exceedance_curve` | true | ValueError |
| g_f_reserved_claim_metadata | g_f_semantics | `mio.formalism.isotropy_gap.build_isotropy_gap` | true | ValueError |
| g_f_missing_covariance_status | rank_null_covariance | `mio.formalism.isotropy_gap.DepthBinMetadata` | true | ValueError |
| htt_likelihood_rejects_mio_payload | mio_htt_leakage | `workspace.contracts.htt_posterior.reject_mio_likelihood_inputs` | true | TypeError |
| htt_pushforward_rejects_mio_payload | mio_htt_leakage | `htt.departure.posterior_pushforward.reject_mio_pushforward_inputs` | true | TypeError |
| response_rank_deficiency_blocks_model_run | rank_null_covariance | `htt.departure.response_overlap.require_rank_audit_for_model_run` | true | RuntimeError |
| atlas_entry_rejects_external_as_native | transfer_provenance | `bass.atlas.AtlasEntryLite` | true | ValueError |

## Modules Exercised

- `bass.atlas`
- `bass.transfer.registry`
- `common.semantic_guards.no_overclaim`
- `htt.departure.posterior_pushforward`
- `htt.departure.response_overlap`
- `mio.formalism.budget_spec`
- `mio.formalism.exceedance`
- `mio.formalism.filling_fraction`
- `mio.formalism.isotropy_gap`
- `mio.formalism.normalized_score`
- `scripts.verify_formalism_figure_labels`
- `workspace.contracts.htt_posterior`

## Caveats

- This artifact tests hostile semantic paths against production guard surfaces.
- The report is diagnostic-only firewall coverage; not scientific validation.
- It does not validate a native low-ell solver, transfer calibration, or morphology atlas.
- It records sanitized case ids only; hostile prose payloads and exception text are intentionally omitted.
