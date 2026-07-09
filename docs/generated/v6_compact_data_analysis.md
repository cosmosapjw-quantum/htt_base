# V6 Compact Data Analysis

owner: COMMON/OBSSTAT/DL_PIPELINE
implementation_scope: external_data_acquisition_and_obsstat_diagnostics
claim_tier: diagnostic_only
transfer_source: external_public_data_and_external_reference
sky_support_status: mixed_dataset_bound
null_mock_status: not_promoted_to_inference_null
config_hash: `sha256:7aaca026dc82cc42e69fb7c28b618a995e3b10b189ba9e4cd25cecd5c5bbf718`
caveats:
- Acquisition and compact-product diagnostics only.
- No native low-ell solver output, evidence, posterior odds, p-value, or family-identification claim is made.
- DESI random/mask support remains separate unless explicit support files are locally bound.
- ACT DR6 lensing status: `acquired`.
generating_command: python scripts/build_v6_compact_data_analysis.py
git_commit_or_worktree_state: content-addressed

## Summary

- Compact product rows: 19
- Present compact products: 19
- Missing compact products: 0
- Acceptance checks: 8/8 passed

## Download Inventory

| Inventory | Known additional GB | Unknown sizes | Status summary |
| --- | ---: | ---: | --- |
| `existing_compact` | 0.000 | 6 | `{'present': 16, 'size_unknown': 6}` |
| `approval_compact` | 0.000 | 0 | `{'present': 4}` |

## Compact Products

| Label | Present | Size MB | Key summary |
| --- | ---: | ---: | --- |
| `planck_tt_binned` | `True` | 0.00 | bandpowers n=83, ell=47.0..2499.0 |
| `planck_lensing` | `True` | 0.95 | arrays=40 |
| `camb_lensing_reference` | `True` | 0.28 | arrays=8 |
| `act_dr4_compact` | `True` | 1.12 | arrays=11 |
| `spt3g_y1_compact` | `True` | 34.61 | arrays=59 |
| `bicep_keck_2018_bb` | `True` | 57.12 | arrays=27 |
| `act_dr6_tt` | `True` | 0.00 | bandpowers n=57, ell=63.5..7525.5 |
| `act_dr6_te` | `True` | 0.00 | bandpowers n=57, ell=63.5..7525.5 |
| `act_dr6_ee` | `True` | 0.00 | bandpowers n=57, ell=63.5..7525.5 |
| `desi_bgs_ngc` | `True` | 210.18 | catalog rows=4081227, z_median=0.22725433111190796 |
| `desi_bgs_sgc` | `True` | 74.22 | catalog rows=1441126, z_median=0.22840336710214615 |
| `desi_lrg_ngc` | `True` | 76.02 | catalog rows=1476135, z_median=0.7546951770782471 |
| `desi_lrg_sgc` | `True` | 34.12 | catalog rows=662492, z_median=0.7508252263069153 |
| `desi_qso_ngc` | `True` | 40.85 | catalog rows=793219, z_median=1.7429596185684204 |
| `desi_qso_sgc` | `True` | 22.16 | catalog rows=430172, z_median=1.739847719669342 |
| `cf4_query_batch` | `True` | 19.99 | arrays=10 |
| `cf4_full_groups` | `True` | 4.94 | arrays=17 |
| `act_dr6_lensing_likelihood_archive` | `True` | 344.57 | archive sample_members=20 |
| `act_dr6_lensing_maps_archive` | `True` | 1307.94 | archive sample_members=20 |

## Acceptance Checks

| Check | Passed | Evidence |
| --- | ---: | --- |
| `no_download_cards_complete` | `True` | `["component_source_matrix", "denominator_sensitivity_table", "depth_gap_card", "exceedance_calibration_card", "identified_set_card", "optical_ansatz_readiness", "response_class_...` |
| `no_download_meta_figures_quarantined` | `True` | `"not_report_facing_internal_meta_quarantine"` |
| `existing_compact_inventory_has_no_known_new_bytes` | `True` | `0.0` |
| `approval_compact_inventory_within_3gb_cap` | `True` | `{"known_additional_gb": 0.0, "within_cap_for_known_sizes": true}` |
| `act_dr6_bandpowers_extracted` | `True` | `["act_dr6_ee", "act_dr6_te", "act_dr6_tt"]` |
| `act_dr6_acquisition_manifest_present` | `True` | `"workdir/raw/act_data/act_dr6_02_acquisition_manifest.json"` |
| `act_dr6_lensing_acquired_or_deferred_cleanly` | `True` | `{"inventory_item_ids": ["act_dr6_lensing_likelihood", "act_dr6_lensing_maps"], "local_download_files": ["workdir/downloads/act_dr6_lensing/ACT_dr6_likelihood_v1.2.tgz", "workdir...` |
| `report_data_pack_contains_compact_figures` | `True` | `["fig_data_planck_tt_binned_residual.png", "fig_data_planck_smica_masked_temperature.png", "fig_data_cf4_catalog_sky_velocity.png", "fig_data_cf4_depth_velocity_profile.png", "f...` |
