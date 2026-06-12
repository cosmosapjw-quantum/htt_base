# Missing and Quarantined Manuscript Figure References

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `563e43204fb0a909e4c08c98ed9ecd2ad76e71f4f0a7e42ae50f881ab5f67295`
input_hashes:
- docs/manuscript/appendices.tex: `b84450743f0a06f0fc954d04aab578f7df8523cd234ac87689bdb18404214366`
- docs/manuscript/ch01_introduction.tex: `166c08cb98b4d89a7055d2bf1e0bec037d7f72bb54f29e91e7c8ff475adf7b1c`
- docs/manuscript/ch02_dipole_anomaly.tex: `04c903c4a4c9616bbf18706428edc0ebb12e6504aca7968fcd0368bcee75f4fe`
- docs/manuscript/ch03_framework.tex: `8397a22e3750187db3d94dc304a481a4e8a589946c95e7249406ebfce9eae55b`
- docs/manuscript/ch04_bianchi_bounds.tex: `1aab34feee83c94087dd617bd1942701d75ba10984529ebd689f18c814158bc0`
- docs/manuscript/ch05_teff_corrections.tex: `6ed81ffbce2812324707f3d1162e48fbcacc841ae87a91600f024be653a0392d`
- docs/manuscript/ch06_pipeline.tex: `199b349648ef023ef47c916e66b0b1cce571e82ecf3427b42999f65f4bd84b43`
- docs/manuscript/ch07_results.tex: `ea7d3eda2940634bf416c24dfa625cadbbb7141f45f03ea78eaf291e977fe34c`
- docs/manuscript/ch08_robustness.tex: `eedf78488dd699b6799d6f68ad5882e5fb972ee8e9c5a0c321a3367a0fdf5daf`
- docs/manuscript/ch09_discussion.tex: `9011007ec829362bafa0fea73c652de8d19784de1b900c04d37851e801e587b8`
- docs/manuscript/ch10_future.tex: `2c9959ecef6b3156d31ea72a48f1b145b302cbcc68024c87ae70f327de809520`
- docs/manuscript/ch11_error_hierarchy.tex: `f997ed0711bbb3062bbdead0bbb1f06fcf5cbeea7f9d07f033f305389232e522`
- docs/manuscript/generated/ver2_artifact_export_policy.tex: `6cef67bdb8fea2e4166c6a7be1fd0c036c3f2f06010ce9f787ce4aefcf688150`
- docs/manuscript/generated/ver2_channel_responsibility.tex: `0a1c264f31035558a31a2b1f487cca8ab6a69f7a7f08e4c5469a371425f8d4ae`
- docs/manuscript/generated/ver2_claim_ledger.tex: `c5ab0fc11fb5884c86268af3eacd473b840e9f3b983d788342568821c732b907`
- docs/manuscript/generated/ver2_figure_manifest_status.tex: `255a65e2a34fd1228b133acae4a7f39ac21131e9400cd815a89ab030a68639d6`
- docs/manuscript/generated/ver2_result_pack_summary.tex: `23e72c5ff41ae5630b172573cbd8194ee5c13c5fed5cfb4c5b217e50d5f7801b`
- docs/manuscript/generated/ver2_source_vs_propagation.tex: `6c597700528fa7a63e620500ab8a6b375d81ae861278b874263eb541fb77b736`
- docs/manuscript/generated/ver2_status_snapshot.tex: `29743c2ce4fb943ea8470beff21d8e60f049abbdf76a425190437d8c3332adb3`
- docs/manuscript/generated/ver2_titlepage_status.tex: `2c637e034d699052e267fa9415e85a7e6cd29ef7543ae4198297e83848891d35`
- docs/manuscript/generated/ver2_tsc_scope_boundary.tex: `79690e0baa64e291bad85081dd88a85da71c36abe6b0c0710c84e8362ef4de80`
- docs/manuscript/generated/ver2_validation_status.tex: `469bb99fb4a90d5fb680214a45f42f378c99667ea5643b769e122ed7418ab144`
- docs/manuscript/main.tex: `fd57f16d95dc0d1cdf9afd93d69d109a41b0c358ae6c58d593e7b35e3fd2f416`
- docs/generated/quarantined_figures.md: `bffd8a4306f9767966e29842ed84a9e83fe659d55ecd22c2271c25825e9cb857`
caveats:
- Manuscript figure inventory only; this report does not promote figures.
- Missing or quarantined figure references block final manuscript freeze until explained.
- Text audit findings are audit findings, not scientific results.
generating_command: python scripts/audit_manuscript_figures.py
git_commit: 93fa283
worktree_state: dirty
output_path: docs/generated/missing_figure_references.md

## Summary

- Missing refs: 22
- Quarantined refs: 72
- Forbidden-claim findings: 0
- Claim-risk findings: 13
- Manual/status-number findings: 10

## Missing Figure References

| Source | Include | Status | Resolved path | Manifest | Reason |
| --- | --- | --- | --- | --- | --- |
| `docs/manuscript/appendices.tex:344` | `paper/ver2_generated/fig_ver2b_local_global_discrimination_matrix` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/appendices.tex:354` | `paper/ver2_generated/fig_ver2c_departure_card_summary` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/appendices.tex:364` | `paper/ver2_generated/fig_ver2e_validation_campaign_matrix` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch02_dipole_anomaly.tex:407` | `figures/physics_gallery/14_observer_frame/04_discriminator_coverage.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch03_framework.tex:3579` | `figures/physics_gallery/17_perturbation_k_modes/01_harmonic_modes_per_type.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch03_framework.tex:3590` | `figures/physics_gallery/17_perturbation_k_modes/02_adiabatic_seed_ic.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch03_framework.tex:3592` | `figures/physics_gallery/17_perturbation_k_modes/05_Dl_TT_vs_camb_per_k.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch05_teff_corrections.tex:2185` | `figures/physics_gallery/10_collision_and_visibility/04_thomson_beta_sweep_Dl.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch05_teff_corrections.tex:2223` | `figures/physics_gallery/10_collision_and_visibility/05_bb_from_tilted_lens_e.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch05_teff_corrections.tex:2259` | `figures/physics_gallery/10_collision_and_visibility/06_doppler_second_order_residual.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch06_pipeline.tex:335` | `figures/physics_gallery/19_htt_likelihood/plot_19_01_los_propagator_heatmap.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch06_pipeline.tex:377` | `figures/physics_gallery/19_htt_likelihood/plot_19_04_direction_likelihood_contours.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:360` | `figures/physics_gallery/17_perturbation_k_modes/03_k_zero_limit_recovery.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:362` | `figures/physics_gallery/17_perturbation_k_modes/05_Dl_TT_vs_camb_per_k.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:404` | `figures/physics_gallery/18_22_config_regression/plot_18_01_22_config_sigma2_decay.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:469` | `figures/physics_gallery/18_22_config_regression/plot_18_02_cross_type_limits_grid.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:513` | `figures/physics_gallery/18_22_config_regression/plot_18_03_Dl_TT_11_types_vs_camb.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:522` | `figures/physics_gallery/18_22_config_regression/plot_18_04_pontzen_challinor_shape_match.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:621` | `figures/physics_gallery/19_htt_likelihood/plot_19_05_lnB_11types_vs_FLRW.png` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:659` | `paper/ver2_generated/fig_ver2a_scalar_to_morphology_summary` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch07_results.tex:668` | `paper/ver2_generated/fig_ver2d_mio_predictive_residuals` | `missing` | `none` | `none` | `no_candidate_found` |
| `docs/manuscript/ch11_error_hierarchy.tex:588` | `../../figures/physics_gallery/15_massive_neutrino/02_rho_p_NR_transition.png` | `missing` | `none` | `none` | `no_candidate_found` |

## Quarantined Figure References

| Source | Include | Status | Resolved path | Manifest | Reason |
| --- | --- | --- | --- | --- | --- |
| `docs/manuscript/appendices.tex:383` | `fig_equiv_class_evidence` | `quarantined` | `figures/fig_equiv_class_evidence.png` | `none` | `missing_manifest` |
| `docs/manuscript/appendices.tex:395` | `fig_cf4pp_sensitivity` | `quarantined` | `figures/fig_cf4pp_sensitivity.png` | `none` | `missing_manifest` |
| `docs/manuscript/appendices.tex:406` | `fig_sigma_omega_contour` | `quarantined` | `figures/fig_sigma_omega_contour.png` | `none` | `missing_manifest` |
| `docs/manuscript/appendices.tex:416` | `fig_sigma_accel_contour` | `quarantined` | `figures/fig_sigma_accel_contour.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch03_framework.tex:3614` | `fig_defect_identity_schematic` | `quarantined` | `figures/fig_defect_identity_schematic.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch03_framework.tex:3625` | `fig_frame_problem` | `quarantined` | `figures/fig_frame_problem.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch03_framework.tex:3636` | `fig_scale_hierarchy` | `quarantined` | `figures/fig_scale_hierarchy.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch03_framework.tex:3647` | `fig_defect_identity_schematic` | `quarantined` | `figures/fig_defect_identity_schematic.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch03_framework.tex:3658` | `fig_frame_problem` | `quarantined` | `figures/fig_frame_problem.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch03_framework.tex:3669` | `fig_scale_hierarchy` | `quarantined` | `figures/fig_scale_hierarchy.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch03_framework.tex:3680` | `fig_4D_projection_atlas` | `quarantined` | `figures/fig_4D_projection_atlas.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch04_bianchi_bounds.tex:1223` | `fig_MES_three_bounds` | `quarantined` | `figures/fig_MES_three_bounds.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch04_bianchi_bounds.tex:1238` | `fig_type_by_type_summary` | `quarantined` | `figures/fig_type_by_type_summary.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch04_bianchi_bounds.tex:1249` | `fig_vorticity_hierarchy` | `quarantined` | `figures/fig_vorticity_hierarchy.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch05_teff_corrections.tex:2559` | `fig_NL_heatmap` | `quarantined` | `figures/fig_NL_heatmap.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch05_teff_corrections.tex:2572` | `fig_nonlinear_corrections` | `quarantined` | `figures/fig_nonlinear_corrections.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch05_teff_corrections.tex:2584` | `fig_ell_mixing_comparison` | `quarantined` | `figures/fig_ell_mixing_comparison.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch05_teff_corrections.tex:2596` | `fig_teff_moment_map` | `quarantined` | `figures/fig_teff_moment_map.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch06_pipeline.tex:852` | `fig_experiment_timeline` | `quarantined` | `figures/fig_experiment_timeline.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch06_pipeline.tex:863` | `fig_activation_map` | `quarantined` | `figures/fig_activation_map.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch06_pipeline.tex:875` | `fig_reduced_los_physics_payoff` | `quarantined` | `figures/fig_reduced_los_physics_payoff.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch06_pipeline.tex:887` | `fig_s1m_shadow` | `quarantined` | `figures/fig_s1m_shadow.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch06_pipeline.tex:898` | `fig_coverage_sbc` | `quarantined` | `figures/fig_coverage_sbc.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch06_pipeline.tex:909` | `fig_external_integration` | `quarantined` | `figures/fig_external_integration.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1468` | `fig_scenarios_comprehensive` | `quarantined` | `figures/fig_scenarios_comprehensive.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1493` | `fig_filling_fraction_posterior` | `quarantined` | `figures/fig_filling_fraction_posterior.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1500` | `fig_filling_z_evolution` | `quarantined` | `figures/fig_filling_z_evolution.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1507` | `fig_growing_mode` | `quarantined` | `figures/fig_growing_mode.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1514` | `fig_evidence_grand_bar` | `quarantined` | `figures/fig_evidence_grand_bar.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1545` | `fig_data_decomposition` | `quarantined` | `figures/fig_data_decomposition.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1569` | `fig_BV_exclusion_restyled` | `quarantined` | `figures/fig_BV_exclusion_restyled.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1576` | `fig_f2_transfer_function` | `quarantined` | `figures/fig_f2_transfer_function.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1601` | `fig_beta_posteriors_R03` | `quarantined` | `figures/fig_beta_posteriors_R03.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1608` | `fig_triangle_BI_R03` | `quarantined` | `figures/fig_triangle_BI_R03.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1615` | `fig_triangle_BVIIh_grow_R03` | `quarantined` | `figures/fig_triangle_BVIIh_grow_R03.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1622` | `fig_prior_sensitivity` | `quarantined` | `figures/fig_prior_sensitivity.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1629` | `fig_evidence_decomposition` | `quarantined` | `figures/fig_evidence_decomposition.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1650` | `fig_catwise_sensitivity` | `quarantined` | `figures/fig_catwise_sensitivity.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1683` | `fig_channel_coherence_heatmap` | `quarantined` | `figures/fig_channel_coherence_heatmap.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch07_results.tex:1710` | `fig_direction_alignment_matrix` | `quarantined` | `figures/fig_direction_alignment_matrix.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:957` | `fig_departure_summary` | `quarantined` | `figures/fig_departure_summary.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:974` | `fig_q0_pushforward` | `quarantined` | `figures/fig_q0_pushforward.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:988` | `fig_rho_sweep` | `quarantined` | `figures/fig_rho_sweep.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1002` | `fig_channel_ablation_heatmap` | `quarantined` | `figures/fig_channel_ablation_heatmap.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1014` | `fig_direction_posterior` | `quarantined` | `figures/fig_direction_posterior.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1028` | `fig_v_pushforward` | `quarantined` | `figures/fig_v_pushforward.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1125` | `fig_injection_recovery` | `quarantined` | `figures/fig_injection_recovery.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1140` | `fig_leave_one_out` | `quarantined` | `figures/fig_leave_one_out.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1153` | `fig_null_competition_production` | `quarantined` | `figures/fig_null_competition_production.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1164` | `fig_orientation_diagnostics` | `quarantined` | `figures/fig_orientation_diagnostics.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1179` | `fig_source_decomposition` | `quarantined` | `figures/fig_source_decomposition.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1193` | `fig_source_discrimination` | `quarantined` | `figures/fig_source_discrimination.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1232` | `fig_hemispherical_power_asymmetry_bianchi` | `quarantined` | `figures/fig_hemispherical_power_asymmetry_bianchi.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1257` | `fig_parity_asymmetry_per_model` | `quarantined` | `figures/fig_parity_asymmetry_per_model.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch08_robustness.tex:1283` | `fig_anomaly_overlap_matrix` | `quarantined` | `figures/fig_anomaly_overlap_matrix.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch09_discussion.tex:1914` | `fig_tilted_H0_depth` | `quarantined` | `figures/fig_tilted_H0_depth.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch09_discussion.tex:1921` | `fig_contrastive_summary` | `quarantined` | `figures/fig_contrastive_summary.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch09_discussion.tex:1933` | `fig_DCP_defect_mapping` | `quarantined` | `figures/fig_DCP_defect_mapping.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch09_discussion.tex:1945` | `fig_anomaly_direction_sky` | `quarantined` | `figures/fig_anomaly_direction_sky.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch09_discussion.tex:1959` | `fig_colin_beta` | `quarantined` | `figures/fig_colin_beta.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch09_discussion.tex:1992` | `fig_dipole_sky_overlay_all_surveys` | `quarantined` | `figures/fig_dipole_sky_overlay_all_surveys.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch09_discussion.tex:2021` | `fig_anomaly_atlas_skymap` | `quarantined` | `figures/fig_anomaly_atlas_skymap.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1015` | `fig_experiment_timeline` | `quarantined` | `figures/fig_experiment_timeline.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1049` | `fig_activation_map` | `quarantined` | `figures/fig_activation_map.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1064` | `fig_reduced_los_physics_payoff` | `quarantined` | `figures/fig_reduced_los_physics_payoff.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1078` | `fig_s1m_shadow` | `quarantined` | `figures/fig_s1m_shadow.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1093` | `fig_external_integration` | `quarantined` | `figures/fig_external_integration.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1106` | `fig_peculiar_jeans` | `quarantined` | `figures/fig_peculiar_jeans.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1120` | `fig_peculiar_jeans` | `quarantined` | `figures/fig_peculiar_jeans.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1134` | `fig_q_decomposition` | `quarantined` | `figures/fig_q_decomposition.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1172` | `fig_fisher_ellipses_future_surveys` | `quarantined` | `figures/fig_fisher_ellipses_future_surveys.png` | `none` | `missing_manifest` |
| `docs/manuscript/ch10_future.tex:1196` | `fig_tension_resolution_timeline` | `quarantined` | `figures/fig_tension_resolution_timeline.png` | `none` | `missing_manifest` |

## Text Audit Findings

| Source | Type | Rule | Text SHA256 |
| --- | --- | --- | --- |
| `docs/manuscript/appendices.tex:175` | `claim_risk_phrase` | `production_value` | `875192a7ba352c0f97db329bfaf92c1d95e47ac55af3acde6e6a5931b05cc09a` |
| `docs/manuscript/appendices.tex:222` | `claim_risk_phrase` | `production_value` | `9d75e69fd63f0212836791bfdf04fbc9a0d575ae8c3fa7ac6f9c001dfec86332` |
| `docs/manuscript/ch01_introduction.tex:213` | `manual_status_number` | `test_count` | `872e95f0a0bb091bf6436aa9a71ecc412df5b25581b9c27cca5fd7b193feb499` |
| `docs/manuscript/ch05_teff_corrections.tex:1028` | `claim_risk_phrase` | `overstrong_validation_wording` | `1671716a4a8999772ee95519e02d171158e88c19cb759ca72c2e8a4aa6d2d615` |
| `docs/manuscript/ch05_teff_corrections.tex:1041` | `claim_risk_phrase` | `premature_family_identification` | `914d29ffba2ae8152f9ba803753afc945d98abeddf889d0be977fc6c32789c3e` |
| `docs/manuscript/ch05_teff_corrections.tex:1700` | `claim_risk_phrase` | `production_value` | `0645c9c969fc09ca61ab41f73ffe7becbb2ce5eb8cc817ff5d1fc7188cf9e2be` |
| `docs/manuscript/ch06_pipeline.tex:574` | `claim_risk_phrase` | `production_value` | `704f00687b45213498b6df4ca7335148d6460731566319a022ff7a145ca42938` |
| `docs/manuscript/ch07_results.tex:1438` | `claim_risk_phrase` | `solver_validated_transfer` | `39977ea400f082c3f83230f7df3b58125c8787dc7bdcbf702b338e25b851389e` |
| `docs/manuscript/ch07_results.tex:1439` | `claim_risk_phrase` | `solver_validated_transfer` | `6100a2fe5295c10aa3651c77a6ddde492951797bbc67a63ef1c211d84bd8f64b` |
| `docs/manuscript/ch07_results.tex:1455` | `claim_risk_phrase` | `solver_validated_transfer` | `0e080a0a509accc3a65ef2dbe4e357c323a754bd760ea107471003239e784d08` |
| `docs/manuscript/ch07_results.tex:386` | `manual_status_number` | `pytest_count` | `601ed839ce5d071ab204402b8f39b977a73d97431ab47a688eefac2c7d99874d` |
| `docs/manuscript/ch07_results.tex:387` | `manual_status_number` | `pytest_count` | `98cf9b71fef68526360f8ba79f335ada0528bcbdb985400a057673962f8f6d59` |
| `docs/manuscript/ch08_robustness.tex:928` | `claim_risk_phrase` | `solver_validated_transfer` | `7ae74b4bb96c7b6bab598a2d5e6a1bf7a27e2d819293ead363fa4bd56ed03d69` |
| `docs/manuscript/ch08_robustness.tex:929` | `claim_risk_phrase` | `solver_validated_transfer` | `3c70a3c76fa8dbcc41602386da51306d18d89cf0f1f8ebf527bc36af0e605c40` |
| `docs/manuscript/ch09_discussion.tex:500` | `claim_risk_phrase` | `production_value` | `e0f53d03801a62b9f6440f5f2846dde407b6128f0ac8484f40bfacfec283320d` |
| `docs/manuscript/ch09_discussion.tex:851` | `claim_risk_phrase` | `production_value` | `f099596fa9124a4853988b3255b66f8adc55ff1b5ab490b699380af5a0eda956` |
| `docs/manuscript/generated/ver2_artifact_export_policy.tex:10` | `manual_status_number` | `manifest_ready_count` | `f74def9b1a8fce0337c980c9c3822ba1ebba16f3ef2199281982474ff0a7ffd5` |
| `docs/manuscript/generated/ver2_figure_manifest_status.tex:3` | `manual_status_number` | `manifest_ready_count` | `3641b120e10eb08823c36f8f1fc7fc0b87ea74f1a4522c00b118b3026ab70228` |
| `docs/manuscript/generated/ver2_figure_manifest_status.tex:4` | `manual_status_number` | `blocked_figure_count` | `e56b6bc57773d52f482a03e2f636fac2fda4c299ce0eb879b9c633bfae6e4594` |
| `docs/manuscript/generated/ver2_status_snapshot.tex:3` | `manual_status_number` | `status_counter` | `7a25a3f4520d145b61d2bc5708bccc841924cde35517c6fa26310a01d49a6123` |
| `docs/manuscript/generated/ver2_status_snapshot.tex:4` | `manual_status_number` | `status_counter` | `7a5e5d551bec3f9ce300a8bc20ba2157e9ea9680e7657cf3c3400e490b722360` |
| `docs/manuscript/generated/ver2_titlepage_status.tex:3` | `manual_status_number` | `status_counter` | `04e3b582a4306c367f198a1cfc4285c7aa39df3eabd08b281fc1938e72bff655` |
| `docs/manuscript/generated/ver2_titlepage_status.tex:4` | `manual_status_number` | `status_counter` | `016ea54b99b0d22e7b3acf8aa8f741325a108e647146b0d9dc9934ab03869037` |
