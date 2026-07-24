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
config_hash: `sha256:ac227dfb5bb66f66a34128a956bd1b6f0433a58468558bee8026e632e5cbe1db`
input_hashes:
- `scripts/generate_transfer_sensitivity_report.py:5dedf6db87a5bb3e0e95c418f4e7e4bd37c9b02cfec2f589c20b9487b4867d87`
- `htt/src/common/transfer_registry.py:7c08a18c14a4833411e0139e2362886e8353eb5c67a28a24df6fe1e57b455265`
- `htt/bass/transfer/registry.py:c1065aa3e2fc0a1d83fb9ace26073b674f66eac627d83eedb4344dd8e15983a0`
- `htt/bass/transfer/aniclass_adapter.py:962d30a4d32bd7263fd52d9db95fc459fbae38daf8296bada99fafb493d242dc`
- `htt/bass/atlas/atlas_entry.py:7012a5a06f819b62c194975c7f025142388621f5dc06668d4b008a222eee14db`
- `htt/bass/atlas/budget_ceiling_optimizer.py:fec33e6fcd768abc809563731ac3828764324a4bd278afb3b5eb0be0ae0c2953`
- `htt/mio/formalism/budget_spec.py:25213b00a1f0e6c373e17960e15de567240ce6f22d914a54e6cad8047a4d727e`
- `htt/mio/reports/departure_report.py:636530f1c4acc6e3f7f051a8b58d82eb08e85948a2a6dc84d1ade4b3c525f464`
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
git_commit_or_worktree_state: c80e35c9+dirty

## Current Transfer Dependencies

| transfer_id | source | claim_tier | conditional | non_native | observable | calibration | callable | input_domain | caveat_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| aniclass.lowell.f2_tensor.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f2_tensor | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.f2_vector.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f2_vector | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.f3_tensor.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f3_tensor | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.f3_vector.v1 | AniCLASS_external | conditional | True | True | scalar_summary | external_calibrated | htt.core.evidence_models_R03a:f3_vector | {"x_h_max": 1000.0, "x_h_min": 0.001} | 6 |
| aniclass.lowell.shear_to_D2.v1 | AniCLASS_external | conditional | True | True | temperature | external_calibrated | htt.core.evidence_models_R03a:shear_to_D2 | {"Sigma2_max": 1e-20, "Sigma2_min": 1e-24, "Sigma2_note": "legacy Saadeh-linear-regime external calibration window", "x_h_max": 1000.0, "x_h_min": 0.001, "x_h_note": "explicit x_h values use the AniCLASS interpolation domain"} | 6 |
| aniclass.lowell.shear_to_D3.v1 | AniCLASS_external | conditional | True | True | temperature | external_calibrated | htt.core.evidence_models_R03a:shear_to_D3 | {"Sigma2_max": 1e-20, "Sigma2_min": 1e-24, "Sigma2_note": "legacy Saadeh-linear-regime external calibration window", "x_h_max": 1000.0, "x_h_min": 0.001, "x_h_note": "explicit x_h values use the AniCLASS interpolation domain"} | 6 |
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
