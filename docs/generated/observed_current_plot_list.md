# Observed Current Plot List

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: mixed_none_and_external_reference
sky_support_status: mixed_not_directional_and_recorded_sky_support
null_mock_status: mixed_not_statistical_and_jackknife_bootstrap_diagnostic
config_hash: `sha256:d08a270ee70c39346dcd894ea7b7aee36de4cc16619caaefe821be8d6282092a`
input_hashes:
- `data/camb_ref_planck2018.npz:sha256:6a51719d224dad50a3e85aa79ec126dab03ea4fbb8996699b11a8d8d4c91c942`
- `docs/generated/observational_data_inventory.json:sha256:025b666eb5813b3397eef285f9feef68283d54bc328b7756ada03f62f462e328`
- `docs/generated/observed_longrun_analysis.json:sha256:deb1cd2f10a49f9d4803b57c8c2414c03d04e7baf5939c48a8c9251295a2e5ec`
- `workdir/compact_products/cf4/query_batch.npz:sha256:5fb994ca076235fb30db644d3d1a3672d092ed31f8ef4737bcabe2da87491909`
- `workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz:sha256:ea52cb7e0bbfa3ef69db396dab4a68ee95b409d8e237451d74a924e4e3cca21d`
- `workdir/compact_products/desi/BGS_ANY_SGC_clustering_extended.npz:sha256:e6c858efb2b3fc22ce36443f1393772f62d2e714efbfefde76c1404386ffc05d`
- `workdir/compact_products/desi/LRG_NGC_clustering_extended.npz:sha256:62a7308c21b79e3ef6dc9553e02e8ff5b72dcad4ff657c788270d9d913aee5e9`
- `workdir/compact_products/desi/LRG_SGC_clustering_extended.npz:sha256:596cc08cd5fcc29563e43fdd2d23421a8b6afe678aae7423716a573453ef2798`
- `workdir/compact_products/desi/QSO_NGC_clustering_extended.npz:sha256:548b54767cbbd16dc595b9b08ced074081416a43a83674fbfd317ae220160562`
- `workdir/compact_products/desi/QSO_SGC_clustering_extended.npz:sha256:a8a0f41daed139c7d30129a2b60b1689a3a3e4b1b03b698c4b15146fda8d89b2`
- `workdir/obs_bundle/cmb/lensing/planck_pr3_lensing.npz:sha256:60cd3973a942cf6b95475d8280d17be4845f1ed3b599462bf6ccbdc8835d7368`
- `workdir/obs_bundle/cmb/maps/smica_nside16.npz:sha256:90780c4c42c6c4d371ea17d98de3db01d104a016bae2af58e8d9a6c304f88867`
- `workdir/obs_bundle/cmb/masks/temp_nside16.npz:sha256:3217b51b4c6d88a6df71375c98b3922e1a175f657aece8f67d673b0bd4146e6a`
- `workdir/obs_bundle/cmb/powerspectra/act_dr4.npz:sha256:d1d049253f000f048eac6ce8eee80450122cf59fdc0de951aee8f288dae0c2ca`
- `workdir/obs_bundle/cmb/powerspectra/bicep_keck_2018_bb.npz:sha256:6b85a60cae5b0bca3230ff412f5018a5307f04a25829e731e40cee72aa4ec8cc`
- `workdir/obs_bundle/cmb/powerspectra/planck_pr3_ee_full.npz:sha256:3d5a2920d28a6bd61e67f1d35c151ad1f34a4f5be85b686fe54b3d7108c690cd`
- `workdir/obs_bundle/cmb/powerspectra/planck_pr3_te_full.npz:sha256:b1e6b49aaac76c7d1ddc02fcb2575db9f04f0c9020f58441d1c673a03c0b9b37`
- `workdir/obs_bundle/cmb/powerspectra/planck_pr3_tt_full.npz:sha256:a3ba1178d2afc915d12dd2bf79dc4027aa48e5e263dc1f3bfe8e3a6762e13421`
- `workdir/obs_bundle/cmb/powerspectra/spt3g_y1.npz:sha256:625e55f5a7a2d66013e080520a87bf4922e44509ae347668ee44b3944f9c5ae5`
- `workdir/obs_bundle/cmb/theory/camb_planck2018_lensing_refs.npz:sha256:9eff1778acd345d8564f5057cf2fae94af9370176927203f28237349c698801e`
- `workdir/obs_bundle/cmb/theory/planck_pr3_bestfit.npz:sha256:3031ec210a9d5b4f7f042894bd9d310ca2dd099025b7702afefadbdfb98622fc`
caveats:
- Observed-data plots are diagnostic unless separately calibrated by matched nulls and covariance metadata.
- No plot claims native low-ell solver output, geometry detection, or Bianchi family-ID.
- Packed upstream likelihood products are displayed only as provenance diagnostics.
generating_command: `scripts/make_observed_data_manuscript_figures.py`
git_commit_or_worktree_state: `765fd97+dirty`
artifact_path: docs/generated/observed_current_plot_list.md

## Current Observed-Data Plot Sequence

- Manifest-backed observed-data plot count: `11`
- Long-run plots use jackknife/bootstrap summaries only; no p-value is introduced.

| Flow slot | Figure | Source artifacts | Claim tier | Artifact mode | Allowed use | Caveat |
| --- | --- | --- | --- | --- | --- | --- |
| Observed-data pipeline | `figures/observed_current/fig_observed_inventory_matrix.png` | `docs/generated/observational_data_inventory.json` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed CMB spectra | `figures/observed_current/fig_observed_planck_pr3_spectra.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/obs_bundle/cmb/powerspectra/planck_pr3_tt_full.npz`<br>`workdir/obs_bundle/cmb/powerspectra/planck_pr3_te_full.npz`<br>`workdir/obs_bundle/cmb/powerspectra/planck_pr3_ee_full.npz`<br>`workdir/obs_bundle/cmb/theory/planck_pr3_bestfit.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed low-l statistics | `figures/observed_current/fig_observed_planck_lowell_residual.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/obs_bundle/cmb/powerspectra/planck_pr3_tt_full.npz`<br>`workdir/obs_bundle/cmb/theory/planck_pr3_bestfit.npz`<br>`data/camb_ref_planck2018.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed CMB maps | `figures/observed_current/fig_observed_planck_map_mask.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/obs_bundle/cmb/maps/smica_nside16.npz`<br>`workdir/obs_bundle/cmb/masks/temp_nside16.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed lensing products | `figures/observed_current/fig_observed_planck_lensing_bandpowers.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/obs_bundle/cmb/lensing/planck_pr3_lensing.npz`<br>`workdir/obs_bundle/cmb/theory/camb_planck2018_lensing_refs.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed high-l and polarization products | `figures/observed_current/fig_observed_high_ell_experiment_summary.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/obs_bundle/cmb/powerspectra/act_dr4.npz`<br>`workdir/obs_bundle/cmb/powerspectra/spt3g_y1.npz`<br>`workdir/obs_bundle/cmb/powerspectra/bicep_keck_2018_bb.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed LSS catalog | `figures/observed_current/fig_observed_desi_footprint_depth.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz`<br>`workdir/compact_products/desi/BGS_ANY_SGC_clustering_extended.npz`<br>`workdir/compact_products/desi/LRG_NGC_clustering_extended.npz`<br>`workdir/compact_products/desi/LRG_SGC_clustering_extended.npz`<br>`workdir/compact_products/desi/QSO_NGC_clustering_extended.npz`<br>`workdir/compact_products/desi/QSO_SGC_clustering_extended.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed LSS systematics | `figures/observed_current/fig_observed_desi_selection_weights.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz`<br>`workdir/compact_products/desi/BGS_ANY_SGC_clustering_extended.npz`<br>`workdir/compact_products/desi/LRG_NGC_clustering_extended.npz`<br>`workdir/compact_products/desi/LRG_SGC_clustering_extended.npz`<br>`workdir/compact_products/desi/QSO_NGC_clustering_extended.npz`<br>`workdir/compact_products/desi/QSO_SGC_clustering_extended.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed peculiar-velocity reconstruction | `figures/observed_current/fig_observed_cf4_velocity_density.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/compact_products/cf4/query_batch.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed peculiar-velocity reconstruction | `figures/observed_current/fig_observed_cf4_depth_response.png` | `docs/generated/observational_data_inventory.json`<br>`workdir/compact_products/cf4/query_batch.npz` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |
| Observed long-run diagnostics | `figures/observed_current/fig_observed_longrun_jackknife_bootstrap.png` | `docs/generated/observational_data_inventory.json`<br>`docs/generated/observed_longrun_analysis.json` | `diagnostic_only` | `paper_appendix_conditioned` | `paper_appendix` | Observed-data diagnostic figure; not inference evidence. |

## Claim Boundary

- These figures support only observed-data diagnostic reporting.
- Directional and sky-support plots record masks or coordinate frames but do not establish a global anisotropy cause.
- DESI and CF4 diagnostics remain separate from HTT posterior/evidence and MIO certificates.
- Scalar, depth, and direction summaries do not identify a Bianchi family.
git_commit: `765fd97`
