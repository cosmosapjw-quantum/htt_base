# CF4++ lnB Provenance Report

owner: HTT
implementation_scope: cf4pp_lnb_provenance_gate
claim_tier: blocked
transfer_source: legacy_external_transfer_or_unbound
status: quarantined_untraceable
config_hash: sha256:631afa3b429192879cf643ca02440f626f991413bac133311b6cf7f595c1d86d
input_hash_count: 12
sky_support_status: not_directional
covariance_status: not_bound_for_cf4pp_legacy_sensitivity
null_mock_status: not_bound
generating_command: `venv/bin/python scripts/reproduce_cf4pp_lnb.py --write`
git_commit_or_worktree_state: pending_rev_r077_commit

input_hashes:
- dl_pipeline/assets/obs_meta/INDEX.json=sha256:97d3c8d69b77552ff6592fc1a46132043c89774ccc185a7824612b1425eb3198
- docs/audits/external_research_inputs_2026-06-20/input_inventory.json=sha256:dde5ca448d4d20323e57bc061449326bbe5e88c01c40ec039a417ac5144bdf73
- docs/generated/current_manuscript_figure_curation.json=sha256:1bff29c98803b711203a90c988ecdbabdf241d2daf13666a314faa7673ec49f8
- docs/generated/current_science_plot_payload.json=sha256:54267178062c635f30779f0b31323c46dd607c695ff994e7b6b727b80a000c76
- docs/generated/expanded_manuscript_figure_suite.json=sha256:396ea931859590d70e81631e3f4cdccca3d66508b04bef27cabfab7e35c405b4
- docs/generated/observational_data_inventory.json=sha256:7c7b8684ff47394d90a858e37d8452e92611dc4d43114e6eb2a45d30400b325b
- docs/generated/observed_longrun_analysis.json=sha256:deb1cd2f10a49f9d4803b57c8c2414c03d04e7baf5939c48a8c9251295a2e5ec
- docs/generated/revision_experiment_assets.json=sha256:3523968bfb14620c19bb3fc74e8134948d34201bf3455f17b12b1a12975aac44
- figures/conditioned_legacy/root__fig_cf4pp_sensitivity.manifest.json=sha256:1bf7bf1971ea689a94541fd21325f350d4399c8d40ff1e27b282a2b3558df7bb
- htt/workspace/data/obs_defaults.json=sha256:8c05bad58f2a85d23d5baae55e373421d84737456ca3dfd8b2538c9e70763d1a
- htt/workspace/results/integrated_pipeline_results.json=sha256:f8a86e3b527af99eb2f5ef8f7ae2efb9485e7b55b24d74cc43766b3d8b13af5d
- htt/workspace/results/mio_directional_coherence.json=sha256:3f41a2bdf2b6f056c271d892d8ddfbb60734dd78dd74aceef60e0628376bc6c9

## Decision

The CF4++ legacy sensitivity value is quarantined: repo-local canonical JSON payloads did not bind it to config and input hashes.

## Accepted Source

- none

## Rejected Candidates

- `dl_pipeline/assets/obs_meta/INDEX.json` /scalars/obs_defaults.courtois2025: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, missing_transfer_source
- `docs/audits/external_research_inputs_2026-06-20/input_inventory.json` /response_actions/2: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, missing_transfer_source
- `docs/generated/expanded_manuscript_figure_suite.json` /aggressive/figures/20: target_lnb_absent, missing_bound_config_or_input_hashes, missing_generating_command, missing_claim_tier, unsupported_transfer_source
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

