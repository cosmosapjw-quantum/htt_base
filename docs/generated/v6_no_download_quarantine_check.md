# Quarantined Figure Inventory

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `f4b35450a88e477beadd6a6b24b1844acef95d7c66edee7be3c1e4d0b7e1cd7a`
input_hashes:
- figures/v6_no_download/fig_v6_component_source_matrix.png: `c1d2a984f8ac18a6c8a474be900139a55e6937273ecca2951f75da0d322bfa12`
- figures/v6_no_download/fig_v6_component_source_matrix.manifest.json: `6137a1d68bc4e74e49c752fb68205b62e0dc08082525c5189eb7d10b866a938a`
- figures/v6_no_download/fig_v6_denominator_sensitivity.png: `775764bd5fe9786b2eb71a3f43eaa9d01e544ccb67e638257b63559542338bfc`
- figures/v6_no_download/fig_v6_denominator_sensitivity.manifest.json: `6d999a00138f292cd90ae9607a579d4ba6d8c4efeb873374ec2fab9ecb8a5f8c`
- figures/v6_no_download/fig_v6_depth_gap_and_readiness.png: `a3b45ecf6d37b517e41feae3498593b71ab772df6e26ae556a686a866e675012`
- figures/v6_no_download/fig_v6_depth_gap_and_readiness.manifest.json: `c7f9932659889f4fbd25fabefa685d4e64c952c237ef57b34bedf73ddf979f8e`
- figures/v6_no_download/fig_v6_optical_ansatz_readiness.png: `04622ea133c9d476fc540f13771ce0230ae70605885b28b9104cd0b626628a36`
- figures/v6_no_download/fig_v6_optical_ansatz_readiness.manifest.json: `263296b25b6990c22b9cce57ef040194e4681c82fb5fdb49b6804f89e7454177`
- figures/v6_no_download/fig_v6_response_class_ledger.png: `5d8a552077127d18a4a41fcfd8d562c3e79fa752bd3706710fa5311d986535f0`
- figures/v6_no_download/fig_v6_response_class_ledger.manifest.json: `3ac31700b62773109cb2ec8ce1e4eff6309faccf816cd385011002f033ead6a1`
caveats:
- Quarantine inventory only; listed artifacts are not promoted by this report.
- Missing or invalid manifests block claim-bearing use until provenance is added.
- The checker does not regenerate figures, inspect pixels, or infer scientific meaning.
generating_command: python scripts/check_artifact_manifests.py --scan-root figures/v6_no_download --output docs/generated/v6_no_download_quarantine_check.md
git_commit: 8280b8f
worktree_state: dirty
output_path: docs/generated/v6_no_download_quarantine_check.md

## Summary

- Scan roots: figures/v6_no_download
- Manifested figures: 5
- Quarantined figures: 0
- Manifest issues: 0

## Quarantined Figures

| Path | Reason | Manifest |
| --- | --- | --- |
| none | none | none |

## Manifested Figures

| Path | Reason | Manifest |
| --- | --- | --- |
| `figures/v6_no_download/fig_v6_component_source_matrix.png` | `valid_manifest` | `figures/v6_no_download/fig_v6_component_source_matrix.manifest.json` |
| `figures/v6_no_download/fig_v6_denominator_sensitivity.png` | `valid_manifest` | `figures/v6_no_download/fig_v6_denominator_sensitivity.manifest.json` |
| `figures/v6_no_download/fig_v6_depth_gap_and_readiness.png` | `valid_manifest` | `figures/v6_no_download/fig_v6_depth_gap_and_readiness.manifest.json` |
| `figures/v6_no_download/fig_v6_optical_ansatz_readiness.png` | `valid_manifest` | `figures/v6_no_download/fig_v6_optical_ansatz_readiness.manifest.json` |
| `figures/v6_no_download/fig_v6_response_class_ledger.png` | `valid_manifest` | `figures/v6_no_download/fig_v6_response_class_ledger.manifest.json` |

## Manifest Issues

| Manifest | Issue | Detail |
| --- | --- | --- |
| none | none | none |
