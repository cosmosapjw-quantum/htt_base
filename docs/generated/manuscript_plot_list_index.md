# Manuscript Plot List Index

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_observed_current_and_conditioned_legacy
sky_support_status: mixed_not_directional_and_recorded_sky_support
null_mock_status: mixed_not_statistical_jackknife_bootstrap_and_legacy_conditioned
config_hash: `sha256:cedbdfc6311d0fcfa95f5f2f181f7bda35a21f16ae61a7e84ca3cb844c7eb05e`
input_hashes:
- `docs/generated/current_manuscript_plot_list.md:sha256:f8ec3a8b30b22d2441bf93d961c575a3fb00dcb9e70b2691f0df17e17d0fc6a8`
- `docs/generated/observed_current_plot_list.md:sha256:bf92b7cfbaeec044a575889c43d1fdfd519b24a2f5b509817a226e9a1096d1f6`
- `docs/generated/expanded_manuscript_plot_list.md:sha256:f2b25fca25ac67801f688b3464bfd1f528c1aacf0578acb478219a21322c8fae`
caveats:
- This is an index over generated plot-list documents, not a new science result.
- Observed-data entries are descriptive or diagnostic-only unless matched-null status is explicit.
- Conditioned legacy entries remain appendix-only and assumption-conditioned.
- No entry claims native low-ell solver output, geometry detection, or Bianchi family-ID.
generating_command: `scripts/make_observed_data_manuscript_figures.py`
git_commit_or_worktree_state: `6649e04+dirty`
artifact_path: docs/generated/manuscript_plot_list_index.md

## Summary

- Current-code core figures: `10`
- Observed-data figures added in this deck: `11`
- Current-code VER2 diagnostic figures: `5`
- Conditioned legacy appendix figures: `88`
- Total manuscript figure references after observed-data extension: `114`

## Manuscript Flow

| Report flow | Plot deck | Count | Source list | Claim ceiling |
| --- | --- | ---: | --- | --- |
| Framework and repository status | Current-code core | 10 | `docs/generated/current_manuscript_plot_list.md` | diagnostic-only framework reporting |
| Observational pipeline and observed-data results | Observed-data deck | 11 | `docs/generated/observed_current_plot_list.md` | observed-data diagnostics only |
| Results and robustness | Current-code VER2 packs | 5 | `docs/generated/expanded_manuscript_plot_list.md` | current-code diagnostics only |
| Appendix context | Conditioned legacy appendix deck | 88 | `docs/generated/expanded_manuscript_plot_list.md` | appendix-only conditioned context |

## Observed-Data Figure Order

| Flow slot | Figure | Manuscript snippet |
| --- | --- | --- |
| Observed-data pipeline | `figures/observed_current/fig_observed_inventory_matrix.png` | `docs/manuscript/generated/observed_figures_pipeline.tex` |
| Observed CMB spectra | `figures/observed_current/fig_observed_planck_pr3_spectra.png` | `docs/manuscript/generated/observed_figures_pipeline.tex` |
| Observed low-l statistics | `figures/observed_current/fig_observed_planck_lowell_residual.png` | `docs/manuscript/generated/observed_figures_results.tex` |
| Observed CMB maps | `figures/observed_current/fig_observed_planck_map_mask.png` | `docs/manuscript/generated/observed_figures_pipeline.tex` |
| Observed lensing products | `figures/observed_current/fig_observed_planck_lensing_bandpowers.png` | `docs/manuscript/generated/observed_figures_results.tex` |
| Observed high-l and polarization products | `figures/observed_current/fig_observed_high_ell_experiment_summary.png` | `docs/manuscript/generated/observed_figures_pipeline.tex` |
| Observed LSS catalog | `figures/observed_current/fig_observed_desi_footprint_depth.png` | `docs/manuscript/generated/observed_figures_pipeline.tex` |
| Observed LSS systematics | `figures/observed_current/fig_observed_desi_selection_weights.png` | `docs/manuscript/generated/observed_figures_results.tex` |
| Observed peculiar-velocity reconstruction | `figures/observed_current/fig_observed_cf4_velocity_density.png` | `docs/manuscript/generated/observed_figures_results.tex` |
| Observed peculiar-velocity reconstruction | `figures/observed_current/fig_observed_cf4_depth_response.png` | `docs/manuscript/generated/observed_figures_results.tex` |
| Observed long-run diagnostics | `figures/observed_current/fig_observed_longrun_jackknife_bootstrap.png` | `docs/manuscript/generated/observed_figures_results.tex` |

## Boundary

- MIO certificates and HTT evidence are not merged into this observed-data deck.
- External or conditioned transfer products are not labeled native.
- Scalar, depth, and direction summaries do not assign a Bianchi family.
git_commit: `6649e04`
