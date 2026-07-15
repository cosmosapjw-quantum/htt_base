# Publication Claim Freeze

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:6da6661c346898a0fbd86c84c2e0ee741c6eb34e1e6cb6d21b8d29de1ea6a958`
cf4_p0_quarantine_report_hash: `sha256:b6322139c0ada95749cde60f7c4cea849737687e890c3e3ea3282f779508229e`
input_hashes:
- docs/audit_prompts/claim_firewall_review.md:sha256:8d10cb45fc88b4de2d3629c012096b4370cc6cd45c9b2ceefdd5a237f7ee7c77
- docs/audit_prompts/future_solver_interface_review.md:sha256:33b05ec5952e1434bd82b9a8aaacd1b540d897c2f3c40cf4a8b54771a1f18c0f
- docs/audit_prompts/local_global_review.md:sha256:5e78f85612fedb84bdf0aeef4b3e9f9baaa5368b563f2c602587af9896d96ae0
- docs/audit_prompts/manuscript_figure_review.md:sha256:bc34fe7364e8c69be10705ac560f551a07e841a4db51ae17a2dc292e19236bad
- docs/audit_prompts/transfer_provenance_review.md:sha256:1c7cca8dc358495c8004c1dcf3968377ded0735720631d445a64b3c3ceb31a95
- docs/generated/claim_ledger.json:sha256:8582133082a68d13f2fe145db2419bee3ad02a4d3ce4bdba3ed6914d38aa9495
- docs/generated/manuscript_figure_inventory.md:sha256:62a06c0bc438899203311c8db7441063523e6350ae393d40905fbba068c15592
- docs/generated/missing_figure_references.md:sha256:cac9ef89be04835e6ef59cdcfb1c18513daf7e4fbb7c764603254eefa9bb2486
- docs/generated/pdf_claim_lint_report.md:sha256:f779110274f5f76c47ac84b3079faf62a1a8716001600e9c6aca92d590382d99
- docs/generated/result_pack_A.md:sha256:ff6616ee58976624cfd89692dfc117da435fde9b6f5a79f8cd5ab4d0b94081c2
- docs/generated/result_pack_B.md:sha256:766ee58d61feb2072d6ce97fcdfa007ac7f248d7836876fb866fd9e1ed54e46c
- docs/generated/result_pack_C.md:sha256:a8335933b110bae061ff527f91aef424996311396cc52881eec05e583577e2fe
- docs/generated/status_matrix.md:sha256:c06a88227365b4b1d7a42c291cfc0d42669c8b478d4fadd71b9346a04b562a81
- docs/generated/status_snapshot.json:sha256:3b3d5a726232ed97ed5cb3125b49d9cc2bf04c5f38febd9baa622664a55e842a
- docs/generated/transfer_sensitivity_report.md:sha256:b2634c82ef783687cc2d304c50bb64487fa4556833bcc1a55464f7cae136903c
- scripts/check_publication_claim_freeze.py:sha256:b8e52a894d9b4734d11bbd4a5cdf604fd911ffe08ba54c87bee89d1090eb173f
- tests/contracts/test_publication_claim_freeze.py:sha256:dad2dffac0732eb75e886c189fa35bd56623204bf0f727aa00def7ae6c00c3ce
caveats:
- Publication claim freeze controls public wording; it is not submission approval.
- Current transfer-dependent outputs remain transfer-conditional.
- MIO diagnostics remain separate from HTT inference.
- Native morphology atlas support is absent in this repository state.
- No current manuscript PDF exists at the active path, so PDF claim lint remains blocked rather than passed.
- CF4 P0 source quarantine keeps retained chapter, bibliography, and generated TeX sources in immutable historical lanes with public_use false.
generating_command: python scripts/check_publication_claim_freeze.py
git_commit_or_worktree_state: e6da367+dirty
artifact_path: docs/generated/publication_claim_freeze.md

## Decision

- Submission decision: `blocked_cf4_p0_manuscript_quarantine`
- Native morphology atlas present: `False`
- Public claim count: `8`
- Failed gates: `pdf_claim_lint_passed`

This freeze allows only caveated status, framework, transfer-provenance, diagnostic, and audit-package claims.
It blocks current manuscript publication while the CF4 P0 source quarantine, absent current PDF, and PDF claim-lint gate remain open.

## Required Assertions

| Assertion | Status |
| --- | --- |
| `all_claim_artifacts_exist` | `True` |
| `all_claims_have_artifacts` | `True` |
| `all_claims_have_caveats` | `True` |
| `all_claims_have_manifest_refs` | `True` |
| `all_claims_have_owner` | `True` |
| `all_claims_have_tests` | `True` |
| `all_manifest_refs_exist` | `True` |
| `cf4_p0_quarantine_clean` | `True` |
| `claim_ledger_included` | `True` |
| `external_audit_package_included` | `True` |
| `manuscript_blockers_recorded` | `True` |
| `manuscript_source_quarantine_enforced` | `True` |
| `no_c5_c6_family_id_claim` | `True` |
| `no_current_manuscript_pdf_recorded` | `True` |
| `no_forbidden_claim_language` | `True` |
| `pdf_claim_lint_passed` | `False` |
| `transfer_provenance_included` | `True` |

## Manuscript Blockers

| Metric | Value |
| --- | --- |
| Current manuscript PDF present | False |
| CF4 P0 source quarantine enforced | True |
| PDF claim lint | blocked, not passed |
| Figure inventory | 126 / 126 refs resolved |
| Text audit findings | 5 |
| Claim-risk findings | 5 |

## Frozen Public Claims

| Claim ID | Owner | Tier | Status | Allowed Phrase | Artifacts | Tests | Caveats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `framework.claim_tiered_observatory` | `COMMON` | `C1` | `allowed_with_caveats` | claim-tiered observational/statistical framework | `docs/generated/status_snapshot.json`<br>`docs/generated/claim_ledger.json`<br>`docs/generated/status_matrix.md` | `tests/contracts/test_status_snapshot.py`<br>`python -m common.status_snapshot --write docs/generated/status_snapshot.json` | DAG completion is project bookkeeping only.<br>Production validation remains false without native, null, mask, and covariance gates. |
| `transfer.current_external_paths` | `COMMON` | `C2` | `allowed_with_caveats` | transfer-conditional result | `docs/generated/transfer_sensitivity_report.md` | `tests/contracts/test_transfer_sensitivity_report.py`<br>`python scripts/generate_transfer_sensitivity_report.py --dry-run` | External/proxy transfer paths are not native validated artifacts.<br>Transfer metadata labels are provenance labels only. |
| `mio.certificates_diagnostic_only` | `MIO` | `C2` | `allowed_with_caveats` | diagnostic-only certificate | `docs/generated/result_pack_C.md` | `tests/result_packs/test_pack_C.py`<br>`tests/contracts/test_claim_language_lint.py` | MIO reports are not truth, posterior, or model-ranking objects.<br>HTT evidence traces remain HTT-owned and read-only to MIO reports. |
| `htt.local_global_candidate` | `HTT` | `C4` | `allowed_with_caveats` | local/global discrimination candidate | `docs/generated/result_pack_B.md` | `tests/result_packs/test_pack_B.py`<br>`tests/htt/test_local_global_mixture.py`<br>`tests/htt/test_posterior_pushforward.py` | Candidate wording is blocked when rank or FPR prerequisites fail.<br>MIO directional/depth rows are diagnostic cross-checks, not HTT evidence. |
| `obsstat.scalar_morphology_side_by_side` | `OBSSTAT` | `C3` | `allowed_with_caveats` | morphology compatibility remains unclaimed | `docs/generated/result_pack_A.md` | `tests/result_packs/test_pack_A.py`<br>`tests/contracts/test_claim_language_lint.py` | Scalar x/Q/Pi/F/G and low-ell feature summaries do not classify geometry.<br>Native morphology atlas support is absent. |
| `audit.external_package_disclosure` | `COMMON` | `C1` | `allowed_with_caveats` | external audit disclosure package | `docs/generated/external_audit_package.zip`<br>`docs/generated/external_audit_package_manifest.json` | `tests/contracts/test_audit_package_generator.py`<br>`python scripts/build_external_audit_package.py --check` | Audit packaging is not publication readiness.<br>The CF4 P0 manuscript-source quarantine and absent current PDF remain visible inside the package. |
| `bass.future_native_interface_schema_only` | `BASS` | `C1` | `allowed_with_caveats` | future native solver interface schema | `htt/bass/transfer/native_schema.py`<br>`htt/bass/transfer/native_adapter.py`<br>`docs/generated/external_audit_package_manifest.json` | `tests/contracts/test_transfer_registry.py`<br>`tests/contracts/test_audit_package_generator.py` | The adapter stub must not return synthetic science values.<br>No native low-ell solver output is present in this repository state. |
| `manuscript.cf4_p0_source_quarantine_blocks_submission` | `COMMON` | `C1` | `blocked_for_submission` | current manuscript publication source remains quarantined | `docs/manuscript/main.tex`<br>`docs/generated/cf4_p0_quarantine_block.json`<br>`docs/generated/pdf_claim_lint_report.md` | `tests/contracts/test_manuscript_cf4_quarantine.py`<br>`tests/contracts/test_pdf_claim_lint.py` | No current manuscript PDF exists at the active path.<br>Retained chapter, bibliography, and generated TeX sources are immutable historical evidence with public_use false. |

## Forbidden Promotions

- Do not label external/proxy transfer outputs as native validated artifacts.
- Do not merge MIO diagnostic reports into HTT evidence or posterior quantities.
- Do not use scalar x/Q/Pi/F/G, low-ell summaries, or directional coherence as geometry or family-ID evidence.
- Do not present audit packaging or DAG completion as publication readiness.
- Do not build or submit a current manuscript while the CF4 P0 source quarantine or PDF claim-lint gate is open.
