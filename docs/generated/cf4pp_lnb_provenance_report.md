# CF4++ lnB Provenance Report

owner: HTT
implementation_scope: cf4pp_lnb_provenance_gate
claim_tier: blocked
transfer_source: legacy_external_transfer_or_unbound
status: quarantined_untraceable
config_hash: sha256:0d14443ef93204a140b7be7607854244b31afb413d817803f017f5c9134b6ae8
input_hash_count: 12
sky_support_status: not_directional
covariance_status: not_bound_for_cf4pp_legacy_sensitivity
null_mock_status: not_bound
generating_command: `venv/bin/python scripts/reproduce_cf4pp_lnb.py --write`
git_commit_or_worktree_state: pending_rev_r077_commit

input_hashes:
- dl_pipeline/assets/obs_meta/INDEX.json=sha256:97d3c8d69b77552ff6592fc1a46132043c89774ccc185a7824612b1425eb3198
- docs/audits/external_research_inputs_2026-06-20/input_inventory.json=sha256:640ac04449c73b405c8703a6b6ecee68e8d072d588531d485a688681bd3af0dc
- docs/generated/current_manuscript_figure_curation.json=sha256:1bff29c98803b711203a90c988ecdbabdf241d2daf13666a314faa7673ec49f8
- docs/generated/current_science_plot_payload.json=sha256:e347ed2997e2fc21101dcb4e692ec57f485c8f03c8dd3d971ff471ff8f9fe88f
- docs/generated/expanded_manuscript_figure_suite.json=sha256:f35e4a37b9d209a2e4492c06b8d8a3745da12743103427b7ad1397cbce5fee18
- docs/generated/observational_data_inventory.json=sha256:025b666eb5813b3397eef285f9feef68283d54bc328b7756ada03f62f462e328
- docs/generated/observed_longrun_analysis.json=sha256:deb1cd2f10a49f9d4803b57c8c2414c03d04e7baf5939c48a8c9251295a2e5ec
- docs/generated/revision_experiment_assets.json=sha256:7091d112392857cb2ba848d6601b685afdc4fb873cfe6ab569cc07a39aa42280
- figures/conditioned_legacy/root__fig_cf4pp_sensitivity.manifest.json=sha256:1efd7b8a65f0c7d8b1747e146b25609dbc624e5a82b6d8fe3dcbd4e7fedbe62d
- htt/workspace/data/obs_defaults.json=sha256:c305be5b42ea3c0a9f8d919f0314ac6befc5155424d6b8a00d92f4f9349ac1df
- htt/workspace/results/integrated_pipeline_results.json=sha256:f8a86e3b527af99eb2f5ef8f7ae2efb9485e7b55b24d74cc43766b3d8b13af5d
- htt/workspace/results/mio_directional_coherence.json=sha256:3f41a2bdf2b6f056c271d892d8ddfbb60734dd78dd74aceef60e0628376bc6c9

## Decision

The CF4++ legacy sensitivity value is quarantined: repo-local canonical JSON payloads did not bind it to config and input hashes.

## Accepted Source

- none

## Rejected Candidates

- `dl_pipeline/assets/obs_meta/INDEX.json` /scalars/obs_defaults.courtois2025: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, missing_transfer_source
- `docs/audits/external_research_inputs_2026-06-20/input_inventory.json` /response_actions/2: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, missing_transfer_source
- `docs/generated/expanded_manuscript_figure_suite.json` /aggressive/figures/12: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, unsupported_transfer_source
- `figures/conditioned_legacy/root__fig_cf4pp_sensitivity.manifest.json` /: target_lnb_absent, unsupported_claim_tier, unsupported_transfer_source
- `figures/conditioned_legacy/root__fig_cf4pp_sensitivity.manifest.json` /statistics_definitions: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, missing_transfer_source
- `htt/workspace/results/mio_directional_coherence.json` /certificate: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, missing_transfer_source
- `htt/workspace/results/mio_directional_coherence.json` /probes/3: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, missing_transfer_source

## Manuscript Action

Remove the +44/+105.8 values from headline/result prose and keep CF4++/Watkins rows as unbound, quarantined sensitivity entries pending a dedicated rerun.

## Caveats

- not used in manuscript headline
- dedicated rerun required
- canonical JSON search did not bind the CF4++ lnB value
- not native transfer
- not a family or geometry claim

## Search Summary

- canonical JSON files scanned: 12
- CF4++ candidate records: 7
- bound input hashes for target value: 0

