# Revision Experiment Assets

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: mixed_not_statistical_current_null_bank_and_jackknife_bootstrap_diagnostic
config_hash: `sha256:cc6e2520973432a222fead2c0006a370fac2ebed531348e4511cdd55f9d45ae0`
generating_command: `venv/bin/python scripts/generate_revision_experiment_assets.py --write`
git_commit_or_worktree_state: `c1bb2b1+dirty`
input_hashes:
- docs/generated/observational_data_inventory.json:sha256:39b0ccb29b293cc19b5f61f726dad70c8b4917e1241a912f9c6ea5f3bc8ab513
- docs/generated/observed_longrun_analysis.json:sha256:98596af03a7130bba55b007a122677eb25adc755bb454133cfe3597a423b6047
- docs/generated/current_science_plot_payload.json:sha256:e347ed2997e2fc21101dcb4e692ec57f485c8f03c8dd3d971ff471ff8f9fe88f

These generated assets are diagnostic-only and conditioned on repo-local inputs or deterministic scaffolds.
They are not native transfer outputs and do not support geometry or family claims.

## Assets

| Asset | Input mode | Lane | Figure | Manifest |
|---|---|---|---|---|
| `E1_prior_support_surface` | `repo_observed_input` | `paper_appendix_conditioned` / `paper_appendix` | `figures/current/fig_revision_prior_support_surface.png` | `figures/current/fig_revision_prior_support_surface.manifest.json` |
| `E2_sigma_beta_band` | `repo_observed_input` | `paper_appendix_conditioned` / `paper_appendix` | `figures/current/fig_revision_sigma_beta_band.png` | `figures/current/fig_revision_sigma_beta_band.manifest.json` |
| `FPR_rule_of_three` | `repo_observed_input` | `external_audit_conditioned` / `external_audit` | `figures/current/fig_revision_rule_of_three_fpr.png` | `figures/current/fig_revision_rule_of_three_fpr.manifest.json` |
| `E3_per_channel_occupancy` | `repo_observed_input` | `paper_appendix_conditioned` / `paper_appendix` | `figures/current/fig_revision_per_channel_occupancy.png` | `figures/current/fig_revision_per_channel_occupancy.manifest.json` |
| `E5_tomographic_forecast` | `repo_observed_input` | `paper_main_candidate` / `paper_main` | `figures/current/fig_revision_tomographic_forecast.png` | `figures/current/fig_revision_tomographic_forecast.manifest.json` |

## Caveats

- not native transfer
- not family identification
- does not promote geometry or family claims
- paper-main use requires the lane recorded in this manifest
- Native solver validation is absent.
- Native morphology atlas validation is absent.
- Matched publication-grade null and covariance gates remain promotion blockers.
