# Missing and Quarantined Manuscript Figure References

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `c00fb8c8890bd4e3937afddbd77ed8f1b3c1132189f5518332b380b69ec3ac78`
input_hashes:
- docs/manuscript/appendices.tex: `aa73795f125332cda27e624c8af6c96393253a35cf47b08664f9dd7c5f96dad7`
- docs/manuscript/ch01_introduction.tex: `4d35ab4527fb2082f5bfd90bfdc4867309833c249675294b3617e833780a5d68`
- docs/manuscript/ch02_dipole_anomaly.tex: `d93dce82d3fd2f50aa114079c1d90609c4626d2fe8da981b5c67fdc83e947abe`
- docs/manuscript/ch03_framework.tex: `194b0cdfb7f586ec2a439f6f4c4a26d8c4769589d0a11e89217e960811e828b9`
- docs/manuscript/ch04_bianchi_bounds.tex: `3741a8145e9372fc8d39dcaebaa1e8ad72769729a05cb4ad750535be2c590109`
- docs/manuscript/ch05_teff_corrections.tex: `496689f4677e61d15d9925ec5ad5a130e12329b598d764bb5a48037d77b743ad`
- docs/manuscript/ch06_pipeline.tex: `b7b50ba5d0bf9d3fa0916fed36be5e377ccaf410fc067f5280816c24ed4b3012`
- docs/manuscript/ch07_results.tex: `a55792b2d2136daf0ebfd99acc4e30eef4bccfd437b8e2ee0502c1f99a6422e1`
- docs/manuscript/ch08_robustness.tex: `8340e736fcb944d9f49489302b03b243c9ff6f88cef250482fba8398311708e3`
- docs/manuscript/ch09_discussion.tex: `2b3742085ae4d24ebe04f5f68580927f9804927a6349d25dad2c344bd64d173e`
- docs/manuscript/ch10_future.tex: `91c05153af626c8bd8858a062da574e9a1d4a74645beaa1ac76e34d0b44e2ab1`
- docs/manuscript/ch11_error_hierarchy.tex: `5016cb571b519a6dcd84f9ae078027e108d5f25a53d45c525b13fe4c71f7ce4d`
- docs/manuscript/generated/conditioned_legacy_figure_gallery.tex: `002b0d0a1d4c817e825e7fcf11584bf2eda611768f5dee495901c7738dd5d33b`
- docs/manuscript/generated/current_figures_framework.tex: `9c960a9ba56ccbcf5e8365e3f3399d9a80df9781547fd925b4443bc289ca1bcf`
- docs/manuscript/generated/current_figures_governance.tex: `ad89fd0c612fb355039b312db057be1ccb6b25c2edeba51f80ece2266591bd29`
- docs/manuscript/generated/current_figures_pipeline.tex: `195f8ae9ec189206325edb2ca0411f6031b8985b0f0ef6b981c05d5cd93750b8`
- docs/manuscript/generated/current_figures_results.tex: `839c04959f0f8d9a6836893dc45a2d7857a78991ad9153c54fa355de51f6dbae`
- docs/manuscript/generated/current_figures_ver2_exports.tex: `c63f1348b3762a812cfd391fe96ba1c20e5092f354818d6079c21a3216e140de`
- docs/manuscript/generated/observed_figures_pipeline.tex: `b2b1579f259b14df683c913aaf7171721a8477e93a23aff55a07bad5aaddad93`
- docs/manuscript/generated/observed_figures_results.tex: `23c45f3e2b05992b79ab1f9e0e695e01fbc7ca72815ae8c1b0155838729b169a`
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
- docs/manuscript/main.tex: `89e34c2a3927457f48855f3e8c9cc523c71c01708fe9c3fa4beb3d77e6f7ef0b`
- docs/generated/quarantined_figures.md: `bf0fb77b3fb9a02c35e1e3db7b0871b35cae29b363a2416c2b865291312e89f2`
caveats:
- Manuscript figure inventory only; this report does not promote figures.
- Missing or quarantined figure references block final manuscript freeze until explained.
- Text audit findings are audit findings, not scientific results.
generating_command: python scripts/audit_manuscript_figures.py
git_commit: 367039e
worktree_state: dirty
output_path: docs/generated/missing_figure_references.md

## Summary

- Missing refs: 0
- Quarantined refs: 0
- Forbidden-claim findings: 0
- Claim-risk findings: 0
- Manual/status-number findings: 10

## Missing Figure References

| Source | Include | Status | Resolved path | Manifest | Reason |
| --- | --- | --- | --- | --- | --- |
| none | none | none | none | none | none |

## Quarantined Figure References

| Source | Include | Status | Resolved path | Manifest | Reason |
| --- | --- | --- | --- | --- | --- |
| none | none | none | none | none | none |

## Text Audit Findings

| Source | Type | Rule | Text SHA256 |
| --- | --- | --- | --- |
| `docs/manuscript/ch01_introduction.tex:213` | `manual_status_number` | `test_count` | `e32a6d21ae06c5b615a551513563e6090472c86841809725d82acf67dc7433ea` |
| `docs/manuscript/ch07_results.tex:374` | `manual_status_number` | `pytest_count` | `601ed839ce5d071ab204402b8f39b977a73d97431ab47a688eefac2c7d99874d` |
| `docs/manuscript/ch07_results.tex:375` | `manual_status_number` | `pytest_count` | `98cf9b71fef68526360f8ba79f335ada0528bcbdb985400a057673962f8f6d59` |
| `docs/manuscript/generated/ver2_artifact_export_policy.tex:10` | `manual_status_number` | `manifest_ready_count` | `f74def9b1a8fce0337c980c9c3822ba1ebba16f3ef2199281982474ff0a7ffd5` |
| `docs/manuscript/generated/ver2_figure_manifest_status.tex:3` | `manual_status_number` | `manifest_ready_count` | `3641b120e10eb08823c36f8f1fc7fc0b87ea74f1a4522c00b118b3026ab70228` |
| `docs/manuscript/generated/ver2_figure_manifest_status.tex:4` | `manual_status_number` | `blocked_figure_count` | `e56b6bc57773d52f482a03e2f636fac2fda4c299ce0eb879b9c633bfae6e4594` |
| `docs/manuscript/generated/ver2_status_snapshot.tex:3` | `manual_status_number` | `status_counter` | `7a25a3f4520d145b61d2bc5708bccc841924cde35517c6fa26310a01d49a6123` |
| `docs/manuscript/generated/ver2_status_snapshot.tex:4` | `manual_status_number` | `status_counter` | `7a5e5d551bec3f9ce300a8bc20ba2157e9ea9680e7657cf3c3400e490b722360` |
| `docs/manuscript/generated/ver2_titlepage_status.tex:3` | `manual_status_number` | `status_counter` | `04e3b582a4306c367f198a1cfc4285c7aa39df3eabd08b281fc1938e72bff655` |
| `docs/manuscript/generated/ver2_titlepage_status.tex:4` | `manual_status_number` | `status_counter` | `016ea54b99b0d22e7b3acf8aa8f741325a108e647146b0d9dc9934ab03869037` |
