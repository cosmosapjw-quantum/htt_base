# Revision Experiment Assets

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: mixed_not_statistical_current_null_bank_and_jackknife_bootstrap_diagnostic
config_hash: `sha256:cc6e2520973432a222fead2c0006a370fac2ebed531348e4511cdd55f9d45ae0`
generating_command: `venv/bin/python scripts/generate_revision_experiment_assets.py --write`
git_commit_or_worktree_state: `content-addressed`
input_hashes:
- docs/generated/observational_data_inventory.json:sha256:7c7b8684ff47394d90a858e37d8452e92611dc4d43114e6eb2a45d30400b325b
- docs/generated/observed_longrun_analysis.json:sha256:deb1cd2f10a49f9d4803b57c8c2414c03d04e7baf5939c48a8c9251295a2e5ec
- docs/generated/current_science_plot_payload.json:sha256:dbe57bffa28b9c11f88491ff2c31d3c2bb8e41efabbf2bb7a070da1e0c2faa48

These generated assets are diagnostic-only and conditioned on repo-local inputs or deterministic scaffolds.
They are not native transfer outputs and do not support geometry or family claims.

## Assets

| Asset | Input mode | Lane | Figure | Manifest |
|---|---|---|---|---|
| `E1_prior_support_surface` | `repo_observed_input` | `display_only_prior_sensitivity_schematic` / `paper_appendix` | `figures/current/fig_revision_prior_support_surface.png` | `figures/current/fig_revision_prior_support_surface.manifest.json` |
| `E2_sigma_beta_band` | `repo_observed_input` | `display_only_error_budget_schematic` / `paper_appendix` | `figures/current/fig_revision_sigma_beta_band.png` | `figures/current/fig_revision_sigma_beta_band.manifest.json` |
| `FPR_rule_of_three` | `repo_observed_input` | `external_audit_conditioned` / `external_audit` | `figures/current/fig_revision_rule_of_three_fpr.png` | `figures/current/fig_revision_rule_of_three_fpr.manifest.json` |
| `E3_per_channel_occupancy` | `repo_observed_input` | `paper_appendix_conditioned` / `paper_appendix` | `figures/current/fig_revision_per_channel_occupancy.png` | `figures/current/fig_revision_per_channel_occupancy.manifest.json` |
| `E5_tomographic_forecast` | `repo_observed_input` | `methods_negative_result` / `paper_appendix_blocked_degeneracy` | `figures/current/fig_revision_tomographic_forecast.png` | `figures/current/fig_revision_tomographic_forecast.manifest.json` |

## Caveats

- not native transfer
- not family identification
- does not promote geometry or family claims
- paper-main use requires the lane recorded in this manifest
- Native solver validation is absent.
- Native morphology atlas validation is absent.
- Matched publication-grade null and covariance gates remain promotion blockers.
