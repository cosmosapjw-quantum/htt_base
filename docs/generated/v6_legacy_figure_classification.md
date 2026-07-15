# V6 Legacy Figure Classification

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:e34dfbc36d8773d393790ccd5272845076472b9036b9611dc0f4d37c3c25262d`
caveats:
- Old root/parallel/validation figures are discarded from current claim lanes.
- Manifest-backed conditioned_legacy copies are the only retained legacy figure lane.
- This file classifies figures; it does not promote or reinterpret them.
generating_command: python scripts/build_v6_no_download_research_cards.py
git_commit_or_worktree_state: content-addressed

## Summary

- Classified old figures: 84
- Missing conditioned replacement manifests: 0

## By Kind

| Kind | Count |
| --- | ---: |
| `old_parallel_track_figure` | 8 |
| `old_root_result_figure` | 72 |
| `old_validation_figure` | 4 |

## By Response Class

| Class | Count |
| --- | ---: |
| `directional_style_only_no_geometry_claim` | 6 |
| `legacy_ranking_or_posterior_removed` | 8 |
| `legacy_response_label_only` | 55 |
| `method_or_denominator_context_only` | 8 |
| `observed_or_validation_style_only` | 7 |

## Classified Figures

| Path | Disposition | Response class | Replacement |
| --- | --- | --- | --- |
| `figures/quarantined_legacy/root_sources/fig_3D_constraint_volume.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_3D_constraint_volume.png` |
| `figures/quarantined_legacy/root_sources/fig_4D_projection_atlas.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_4D_projection_atlas.png` |
| `figures/quarantined_legacy/root_sources/fig_BV_exclusion_restyled.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_BV_exclusion_restyled.png` |
| `figures/quarantined_legacy/root_sources/fig_DCP_defect_mapping.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_DCP_defect_mapping.png` |
| `figures/quarantined_legacy/root_sources/fig_MES_three_bounds.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/root__fig_MES_three_bounds.png` |
| `figures/quarantined_legacy/root_sources/fig_NL_heatmap.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_NL_heatmap.png` |
| `figures/quarantined_legacy/root_sources/fig_activation_map.png` | `discarded_from_current_claim_lane` | `observed_or_validation_style_only` | `figures/conditioned_legacy/root__fig_activation_map.png` |
| `figures/quarantined_legacy/root_sources/fig_anomaly_atlas_skymap.png` | `discarded_from_current_claim_lane` | `directional_style_only_no_geometry_claim` | `figures/conditioned_legacy/root__fig_anomaly_atlas_skymap.png` |
| `figures/quarantined_legacy/root_sources/fig_anomaly_direction_sky.png` | `discarded_from_current_claim_lane` | `directional_style_only_no_geometry_claim` | `figures/conditioned_legacy/root__fig_anomaly_direction_sky.png` |
| `figures/quarantined_legacy/root_sources/fig_anomaly_overlap_matrix.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_anomaly_overlap_matrix.png` |
| `figures/quarantined_legacy/root_sources/fig_beta_posteriors_R03.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_beta_posteriors_R03.png` |
| `figures/quarantined_legacy/root_sources/fig_catwise_sensitivity.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_catwise_sensitivity.png` |
| `figures/quarantined_legacy/root_sources/fig_cf4pp_sensitivity.png` | `discarded_from_current_claim_lane` | `observed_or_validation_style_only` | `figures/conditioned_legacy/root__fig_cf4pp_sensitivity.png` |
| `figures/quarantined_legacy/root_sources/fig_channel_ablation_heatmap.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_channel_ablation_heatmap.png` |
| `figures/quarantined_legacy/root_sources/fig_channel_coherence_heatmap.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_channel_coherence_heatmap.png` |
| `figures/quarantined_legacy/root_sources/fig_colin_beta.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_colin_beta.png` |
| `figures/quarantined_legacy/root_sources/fig_contrastive_summary.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_contrastive_summary.png` |
| `figures/quarantined_legacy/root_sources/fig_coverage_sbc.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_coverage_sbc.png` |
| `figures/quarantined_legacy/root_sources/fig_d2_sigma2_scaling.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/root__fig_d2_sigma2_scaling.png` |
| `figures/quarantined_legacy/root_sources/fig_data_decomposition.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_data_decomposition.png` |
| `figures/quarantined_legacy/root_sources/fig_defect_identity_schematic.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_defect_identity_schematic.png` |
| `figures/quarantined_legacy/root_sources/fig_departure_summary.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_departure_summary.png` |
| `figures/quarantined_legacy/root_sources/fig_dipole_sky_overlay_all_surveys.png` | `discarded_from_current_claim_lane` | `directional_style_only_no_geometry_claim` | `figures/conditioned_legacy/root__fig_dipole_sky_overlay_all_surveys.png` |
| `figures/quarantined_legacy/root_sources/fig_direction_alignment_matrix.png` | `discarded_from_current_claim_lane` | `directional_style_only_no_geometry_claim` | `figures/conditioned_legacy/root__fig_direction_alignment_matrix.png` |
| `figures/quarantined_legacy/root_sources/fig_direction_posterior.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_direction_posterior.png` |
| `figures/quarantined_legacy/root_sources/fig_ell_mixing_comparison.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_ell_mixing_comparison.png` |
| `figures/quarantined_legacy/root_sources/fig_equiv_class_evidence.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_equiv_class_evidence.png` |
| `figures/quarantined_legacy/root_sources/fig_evidence_decomposition.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_evidence_decomposition.png` |
| `figures/quarantined_legacy/root_sources/fig_evidence_grand_bar.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_evidence_grand_bar.png` |
| `figures/quarantined_legacy/root_sources/fig_experiment_timeline.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_experiment_timeline.png` |
| `figures/quarantined_legacy/root_sources/fig_external_integration.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_external_integration.png` |
| `figures/quarantined_legacy/root_sources/fig_f2_transfer_function.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_f2_transfer_function.png` |
| `figures/quarantined_legacy/root_sources/fig_filling_fraction_posterior.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_filling_fraction_posterior.png` |
| `figures/quarantined_legacy/root_sources/fig_filling_z_evolution.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/root__fig_filling_z_evolution.png` |
| `figures/quarantined_legacy/root_sources/fig_fisher_ellipses_future_surveys.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_fisher_ellipses_future_surveys.png` |
| `figures/quarantined_legacy/root_sources/fig_frame_problem.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_frame_problem.png` |
| `figures/quarantined_legacy/root_sources/fig_growing_mode.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_growing_mode.png` |
| `figures/quarantined_legacy/root_sources/fig_hemispherical_power_asymmetry_bianchi.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_hemispherical_power_asymmetry_bianchi.png` |
| `figures/quarantined_legacy/root_sources/fig_htt_mio_cross_check_table.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_htt_mio_cross_check_table.png` |
| `figures/quarantined_legacy/root_sources/fig_injection_recovery.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_injection_recovery.png` |
| `figures/quarantined_legacy/root_sources/fig_isotropy_pvalue_per_combination.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_isotropy_pvalue_per_combination.png` |
| `figures/quarantined_legacy/root_sources/fig_jeffreys_categorization.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_jeffreys_categorization.png` |
| `figures/quarantined_legacy/root_sources/fig_leave_one_out.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_leave_one_out.png` |
| `figures/quarantined_legacy/root_sources/fig_nonlinear_corrections.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_nonlinear_corrections.png` |
| `figures/quarantined_legacy/root_sources/fig_null_competition_production.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_null_competition_production.png` |
| `figures/quarantined_legacy/root_sources/fig_orientation_diagnostics.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_orientation_diagnostics.png` |
| `figures/quarantined_legacy/root_sources/fig_pairwise_bf_matrix.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_pairwise_bf_matrix.png` |
| `figures/quarantined_legacy/root_sources/fig_pairwise_separations_matrix.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_pairwise_separations_matrix.png` |
| `figures/quarantined_legacy/root_sources/fig_parity_asymmetry_per_model.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_parity_asymmetry_per_model.png` |
| `figures/quarantined_legacy/root_sources/fig_peculiar_jeans.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_peculiar_jeans.png` |
| `figures/quarantined_legacy/root_sources/fig_prior_sensitivity.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_prior_sensitivity.png` |
| `figures/quarantined_legacy/root_sources/fig_q0_pushforward.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_q0_pushforward.png` |
| `figures/quarantined_legacy/root_sources/fig_q_decomposition.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/root__fig_q_decomposition.png` |
| `figures/quarantined_legacy/root_sources/fig_reduced_los_physics_payoff.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_reduced_los_physics_payoff.png` |
| `figures/quarantined_legacy/root_sources/fig_resultant_vector_5probes.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_resultant_vector_5probes.png` |
| `figures/quarantined_legacy/root_sources/fig_rho_sweep.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_rho_sweep.png` |
| `figures/quarantined_legacy/root_sources/fig_route_b_mm_curve.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_route_b_mm_curve.png` |
| `figures/quarantined_legacy/root_sources/fig_s1m_shadow.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_s1m_shadow.png` |
| `figures/quarantined_legacy/root_sources/fig_scale_hierarchy.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_scale_hierarchy.png` |
| `figures/quarantined_legacy/root_sources/fig_scenarios_comprehensive.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_scenarios_comprehensive.png` |
| `figures/quarantined_legacy/root_sources/fig_sigma_accel_contour.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/root__fig_sigma_accel_contour.png` |
| `figures/quarantined_legacy/root_sources/fig_sigma_omega_contour.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/root__fig_sigma_omega_contour.png` |
| `figures/quarantined_legacy/root_sources/fig_source_decomposition.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_source_decomposition.png` |
| `figures/quarantined_legacy/root_sources/fig_source_discrimination.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_source_discrimination.png` |
| `figures/quarantined_legacy/root_sources/fig_teff_moment_map.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_teff_moment_map.png` |
| `figures/quarantined_legacy/root_sources/fig_tension_resolution_timeline.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_tension_resolution_timeline.png` |
| `figures/quarantined_legacy/root_sources/fig_tilted_H0_depth.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_tilted_H0_depth.png` |
| `figures/quarantined_legacy/root_sources/fig_triangle_BI_R03.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_triangle_BI_R03.png` |
| `figures/quarantined_legacy/root_sources/fig_triangle_BVIIh_grow_R03.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_triangle_BVIIh_grow_R03.png` |
| `figures/quarantined_legacy/root_sources/fig_type_by_type_summary.png` | `discarded_from_current_claim_lane` | `legacy_ranking_or_posterior_removed` | `figures/conditioned_legacy/root__fig_type_by_type_summary.png` |
| `figures/quarantined_legacy/root_sources/fig_v_pushforward.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/root__fig_v_pushforward.png` |
| `figures/quarantined_legacy/root_sources/fig_vorticity_hierarchy.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/root__fig_vorticity_hierarchy.png` |
| `figures/parallel_track/fig_01_mes_three_bounds.png` | `discarded_from_current_claim_lane` | `method_or_denominator_context_only` | `figures/conditioned_legacy/parallel-track__fig_01_mes_three_bounds.png` |
| `figures/parallel_track/fig_05_filling_fraction_scenarios.png` | `discarded_from_current_claim_lane` | `observed_or_validation_style_only` | `figures/conditioned_legacy/parallel-track__fig_05_filling_fraction_scenarios.png` |
| `figures/parallel_track/fig_06_directional_probes_mollweide.png` | `discarded_from_current_claim_lane` | `directional_style_only_no_geometry_claim` | `figures/conditioned_legacy/parallel-track__fig_06_directional_probes_mollweide.png` |
| `figures/parallel_track/fig_07_planck_pr3_tt.png` | `discarded_from_current_claim_lane` | `observed_or_validation_style_only` | `figures/conditioned_legacy/parallel-track__fig_07_planck_pr3_tt.png` |
| `figures/parallel_track/fig_08_planck_pr3_tt_te_ee.png` | `discarded_from_current_claim_lane` | `observed_or_validation_style_only` | `figures/conditioned_legacy/parallel-track__fig_08_planck_pr3_tt_te_ee.png` |
| `figures/parallel_track/fig_09_planck_lowell_envelope.png` | `discarded_from_current_claim_lane` | `observed_or_validation_style_only` | `figures/conditioned_legacy/parallel-track__fig_09_planck_lowell_envelope.png` |
| `figures/parallel_track/fig_11_dipole_direction_comparison.png` | `discarded_from_current_claim_lane` | `directional_style_only_no_geometry_claim` | `figures/conditioned_legacy/parallel-track__fig_11_dipole_direction_comparison.png` |
| `figures/parallel_track/fig_12_planck_act_dr4_combined.png` | `discarded_from_current_claim_lane` | `observed_or_validation_style_only` | `figures/conditioned_legacy/parallel-track__fig_12_planck_act_dr4_combined.png` |
| `figures/validation/flrw_lowell_cell_camb_bass_lmax30.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/validation__flrw_lowell_cell_camb_bass_lmax30.png` |
| `figures/validation/flrw_lowell_cell_camb_bass_lmax8.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/validation__flrw_lowell_cell_camb_bass_lmax8.png` |
| `figures/validation/flrw_lowell_dell_camb_bass_lmax30.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/validation__flrw_lowell_dell_camb_bass_lmax30.png` |
| `figures/validation/flrw_lowell_dell_camb_bass_lmax8.png` | `discarded_from_current_claim_lane` | `legacy_response_label_only` | `figures/conditioned_legacy/validation__flrw_lowell_dell_camb_bass_lmax8.png` |
