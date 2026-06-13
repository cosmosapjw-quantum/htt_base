# Transfer Sensitivity Report

This COMMON diagnostic report inventories current transfer-conditional result surfaces and records which downstream report-card fields inherit external/proxy transfer provenance.

## Artifact Metadata

artifact_id: common.transfer_sensitivity_report
artifact_path: docs/generated/transfer_sensitivity_report.md
owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
production_status: diagnostic_only
transfer_source: none
report_subject_transfer_sources: AniCLASS_external, empirical_proxy, external_transfer
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:53af2631d2c59ae5ce7547a32bda978688498e6645867ae9913f26938c2fd7e5`
input_hashes:
- `scripts/generate_transfer_sensitivity_report.py:5dedf6db87a5bb3e0e95c418f4e7e4bd37c9b02cfec2f589c20b9487b4867d87`
- `htt/src/common/transfer_registry.py:d22beea71bc0e9ffe308c2ae1c9424017c2274aedc7c791d8b432042f5175554`
- `htt/bass/transfer/registry.py:3891053f5d9c91de3cc37a228817c1d98a0aebb3a5cff3d726318f1271621415`
- `htt/bass/transfer/aniclass_adapter.py:685cc43faf3024df1563c66f49444e98a053bba2407896db0a07f58f4fb3e1b3`
- `htt/bass/atlas/atlas_entry.py:07164104137bcc008548c254d179841661de14226ff449ee641537809ab93cc4`
- `htt/bass/atlas/budget_ceiling_optimizer.py:af3ea2eb6817ce56cbf1d870de6f53a7814ea949902ba43a1ab0612842967cae`
- `htt/mio/formalism/budget_spec.py:e836268d37323288d4b9e6bc3442f8eab2b3928ac6ebc91b7caef46d6210166a`
- `htt/mio/reports/departure_report.py:2e28a9523f06d4c05966d2819e3823eeb8f4449c5e4934509bee8fdffcbe982a`
- `docs/PR_DELTAS/pr-080.md:b36fd653e635da8ab6ca3646c1def17c1c0ba5e96f7e739a28aa8b5d5220e717`
- `docs/PR_DELTAS/pr-082.md:403a9b5529e5db701430b4dffcc0b2ff012429db2f33e9fc472833ad43afacec`
- `docs/PR_DELTAS/pr-083.md:1c09331231e734c71e1754a4110a298ee6accbd8f4129cd4c51b2c8aea56e98b`
- `docs/PR_DELTAS/pr-056.md:ca22c09c8a1822c1894fd775e2991932e9a6c28ba55ec9876a137e6000bf4207`
caveats:
- This COMMON report inventories transfer dependence only.
- External/proxy transfer paths remain transfer-conditional result surfaces.
- Future native low-ell solver adapters are schema-only until solver artifacts and validation gates exist.
- Family labels in transfer metadata are provenance labels, not morphology or classification claims.
- This report is not HTT evidence, not a MIO certificate, and not a transfer calibration result.
generating_command: python scripts/generate_transfer_sensitivity_report.py
git_commit_or_worktree_state: e208cd9+dirty

## Current Transfer Dependencies

| transfer_id | source | claim_tier | conditional | non_native | observable | calibration | callable | input_domain | caveat_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| aniclass.lowell.f2_tensor.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f2_tensor | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.f2_vector.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f2_vector | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.f3_tensor.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f3_tensor | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.f3_vector.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f3_vector | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.shear_to_D2.v1 | AniCLASS_external | conditional | True | True | temperature | external_calibrated | htt.core.evidence_models_R03a:shear_to_D2 | {"Sigma2_max": 1e-20, "Sigma2_min": 1e-24, "Sigma2_note": "legacy Saadeh-linear-regime external calibration window"} | 6 |
| aniclass.lowell.shear_to_D3.v1 | AniCLASS_external | conditional | True | True | temperature | external_calibrated | htt.core.evidence_models_R03a:shear_to_D3 | {"Sigma2_max": 1e-20, "Sigma2_min": 1e-24, "Sigma2_note": "legacy Saadeh-linear-regime external calibration window"} | 6 |
| bass.empirical_proxy.shear_to_D2.v1 | empirical_proxy | conditional | True | True | temperature | empirical_proxy | htt.core.evidence_models_R03a:bass_shear_to_D2 | {"Sigma2_max": 0.001, "Sigma2_min": 1e-11} | 6 |

Family labels above are provenance labels only; they are not classification claims.
Current external/proxy paths have no passed native validation gates in this report.

## Downstream Result-Card Status

| row_id | owner | scope | claim_tier | result_card | transfer_source | transfer_status | sky_support | null_mock | boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mio.departure_report.sections | MIO | mio | diagnostic_only | DepartureReport x_C/Q/Pi/F/G_F sections | per_section | section_inherits_external_or_proxy_transfer_metadata | per_section | per_section | diagnostic_only_no_posterior_no_classification |
| mio.budget_spec.external_transfer | MIO | mio | diagnostic_only | BudgetSpec external_transfer denominator policy | external_or_proxy_when_policy_external_transfer | requires_transfer_spec_id_and_validated_transfer_metadata | explicit_field | explicit_field | denominator_sensitivity_not_certified_filling_for_external_transfer |
| bass.budget_ceiling_policy_result | BASS | bass_py | diagnostic_only | BudgetCeilingPolicyResult and MIO reference payload | candidate_transfer_source | external_or_proxy_candidate_remains_pre_solver_metadata | not_directional_or_depth_metadata | not_statistical_or_depth_metadata | ceiling_policy_metadata_not_evidence |
| bass.atlas_entry_lite.current_external_proxy | BASS | bass_py | diagnostic_only | AtlasEntryLite external/proxy transfer metadata | AniCLASS_external_or_empirical_proxy | metadata_only_not_observed_data | not_directional | not_statistical | side_by_side_metadata_not_classification |
| bass.native_schema.future_only | BASS | bass_py | blocked | future native adapter schema | BASS_native_provisional | schema_only_non_consumable_no_values | not_directional | not_statistical | not_current_transfer_result |

## Claim Boundary

- This report may support the claim that current listed outputs are transfer-conditional under explicit external/proxy provenance.
- This report does not validate transfer calibration, does not produce HTT evidence, and does not create a MIO certificate.
- Future native adapter rows remain schema-only and non-consumable until external solver artifacts and validation gates exist.
- Scalar diagnostics, report-card rows, and transfer metadata do not classify a Bianchi family.
