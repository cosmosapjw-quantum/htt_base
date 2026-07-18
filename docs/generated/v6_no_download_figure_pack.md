# V6 No-Download Figure Pack

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_and_external_transfer_conditioned
sky_support_status: not_directional
null_mock_status: mixed_diagnostic_and_blocked
config_hash: `sha256:d3b1ebdf87248fed86d1eb965f1cb4969be8d871238c5b4add9d6cbc238d6253`
caveats:
- Existing v6 no-download cards are the only science input.
- This pack is quarantined internal meta material, not a report figure lane.
- K5/K6 commands are exported separately and are not executed here.
- Figure use is internal-only unless the user explicitly asks for an internal audit appendix.
generating_command: python scripts/make_v6_no_download_figures.py
git_commit_or_worktree_state: content-addressed

## Figures

| Figure | Source card | Manifest |
| --- | --- | --- |
| `figures/quarantined_meta/v6_no_download/fig_v6_component_source_matrix.png` | `component_source_matrix` | `figures/quarantined_meta/v6_no_download/fig_v6_component_source_matrix.manifest.json` |
| `figures/quarantined_meta/v6_no_download/fig_v6_denominator_sensitivity.png` | `denominator_sensitivity_table` | `figures/quarantined_meta/v6_no_download/fig_v6_denominator_sensitivity.manifest.json` |
| `figures/quarantined_meta/v6_no_download/fig_v6_response_class_ledger.png` | `response_class_ledger` | `figures/quarantined_meta/v6_no_download/fig_v6_response_class_ledger.manifest.json` |
| `figures/quarantined_meta/v6_no_download/fig_v6_optical_ansatz_readiness.png` | `optical_ansatz_readiness` | `figures/quarantined_meta/v6_no_download/fig_v6_optical_ansatz_readiness.manifest.json` |
| `figures/quarantined_meta/v6_no_download/fig_v6_depth_gap_and_readiness.png` | `depth_gap_card` | `figures/quarantined_meta/v6_no_download/fig_v6_depth_gap_and_readiness.manifest.json` |

## K5/K6

- command artifact: `docs/generated/v6_k5_k6_user_commands.json`
- execution policy: `commands_exported_for_user_not_run_by_generator`
