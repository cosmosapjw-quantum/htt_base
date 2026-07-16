# Publication Claim Freeze

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:6b4619dc65d0c61d851050359cc4145a866076c90e50df555fd74b6ed40d518d`
cf4_p0_quarantine_report_hash: `sha256:fb56e2cc718ef984c3a564ba1d3eb5c6889e966143b207b2103372363fe12620`
input_hashes:
- docs/audit_prompts/claim_firewall_review.md:sha256:8d10cb45fc88b4de2d3629c012096b4370cc6cd45c9b2ceefdd5a237f7ee7c77
- docs/audit_prompts/future_solver_interface_review.md:sha256:33b05ec5952e1434bd82b9a8aaacd1b540d897c2f3c40cf4a8b54771a1f18c0f
- docs/audit_prompts/local_global_review.md:sha256:5e78f85612fedb84bdf0aeef4b3e9f9baaa5368b563f2c602587af9896d96ae0
- docs/audit_prompts/manuscript_figure_review.md:sha256:bc34fe7364e8c69be10705ac560f551a07e841a4db51ae17a2dc292e19236bad
- docs/audit_prompts/transfer_provenance_review.md:sha256:1c7cca8dc358495c8004c1dcf3968377ded0735720631d445a64b3c3ceb31a95
- docs/generated/claim_ledger.json:sha256:92c098221b43e491a97a0c82818876012ef68b620de5c8c60ea54f7c22fa94ab
- docs/generated/manuscript_figure_inventory.md:sha256:62a06c0bc438899203311c8db7441063523e6350ae393d40905fbba068c15592
- docs/generated/missing_figure_references.md:sha256:cac9ef89be04835e6ef59cdcfb1c18513daf7e4fbb7c764603254eefa9bb2486
- docs/generated/pdf_claim_lint_report.md:sha256:6778ba89ead477eacac4e07aca8a5336dea4f545dee8ffb48231aee3da44af6e
- docs/generated/pr122_artifact_manifest.json:sha256:93113facac0af83de12dac28f0423e2eba0aea9b9b8c3b4ba3750ca8170bcb81
- docs/generated/pr122_claim_closure_report.json:sha256:b29a2129cbad22cdac9cd27df1fa2a1303cb1e8763f8b5e89f39c97085fe7c06
- docs/generated/pr122_claim_closure_report.md:sha256:6a55b2f2725ba0f65902f6e6c577abd79a63d169485e8cb99ef1cd27c2387025
- docs/generated/pr122_claim_evidence_graph.json:sha256:aba2a4285105e85720dc560e08ccbc7f9f6a384f9ffc23e4aa6872d8674e45d6
- docs/generated/pr122_mes_successor_scan.json:sha256:5dc04616e9b435ec1f8e5248e19377bae22fd26ffdc65de705104d0c3d8f8350
- docs/generated/pr122_parent_receipt.json:sha256:f141796fe04f5840bfea256174632d62a72875ea7c62cd4fcf1206dfed2db424
- docs/generated/pr122_release_receipt.json:sha256:3c40f202e6e9c46853bea1e03ffffa9881cdffaa210ed480cb2c7be45ec65012
- docs/generated/pr122_test_execution.json:sha256:0628a9a23c84c8d26e500c05749c6f3d94c5d19c9f9a7f63b1438405229ea554
- docs/generated/result_pack_A.md:sha256:ff6616ee58976624cfd89692dfc117da435fde9b6f5a79f8cd5ab4d0b94081c2
- docs/generated/result_pack_B.md:sha256:766ee58d61feb2072d6ce97fcdfa007ac7f248d7836876fb866fd9e1ed54e46c
- docs/generated/result_pack_C.md:sha256:a8335933b110bae061ff527f91aef424996311396cc52881eec05e583577e2fe
- docs/generated/status_matrix.md:sha256:731b3240871567331de395b75fc42acffbf5c7c1985318bf122f69e388bfcedd
- docs/generated/status_snapshot.json:sha256:26f1bbf5983fda5046817b510446f76addaa0ef8da2d59aa24eac9fd2ecfc25d
- docs/generated/transfer_sensitivity_report.md:sha256:b2634c82ef783687cc2d304c50bb64487fa4556833bcc1a55464f7cae136903c
- docs/research_program/long_horizon_rescue/pr122_active_mes_consumers.yaml:sha256:d8a477e1b7a02132b75a61c9ce273bfb0a20c63d4e2d3b971ce364155de13d71
- docs/research_program/long_horizon_rescue/pr122_authority_snapshot.yaml:sha256:7841941e66ea1ef2de88855c512ceef8235041066cbe3aa2f36c84d1c07f57cc
- docs/research_program/long_horizon_rescue/pr122_spec.yaml:sha256:15ae65cba4e7e5572a827723daca179731ba470da75870f0e1215f43fc6218d9
- htt/src/common/pytest_execution_evidence.py:sha256:7bd592b08f918bbfd1d44d20cbc74a6fe883d57a6314b28b2f96a51a50077247
- htt/src/common/release_evidence_binding.py:sha256:927bf019090796c4544f7a6c9b47db77b7e5da1b9de127d0de55e38acfd2cffb
- htt/src/common/release_evidence_pin.py:sha256:ca8b004feb23db6d80d80c1f957ff6c0fcbad0531c40520033749e4fc5de6815
- scripts/check_publication_claim_freeze.py:sha256:57e8bd7febce6ae299f9c395d9afb868ab9a15e514d899e65327cf41b00a7175
- scripts/codex_harness/build_claim_evidence_graph.py:sha256:1a64facbb10a6ba999121835d9a8806d58d2056cca7dd16ff500cb491193ba4a
- scripts/codex_harness/run_pr122_source_only.sh:sha256:72bed4818b6799cb872f877397877199455888904a777bc4efa13231a59cd982
- tests/contracts/test_publication_claim_freeze.py:sha256:be37c9afad75257c5c3e0230e011f4cbec9603b115f8f12a2e8b406422d45a30
caveats:
- Publication claim freeze controls public wording; it is not submission approval.
- Current transfer-dependent outputs remain transfer-conditional.
- MIO diagnostics remain separate from HTT inference.
- Native morphology atlas support is absent in this repository state.
- No current manuscript PDF exists at the active path, so PDF claim lint remains blocked rather than passed.
- CF4 P0 source quarantine keeps retained chapter, bibliography, and generated TeX sources in immutable historical lanes with public_use false.
generating_command: scripts/codex_harness/run_pr122_source_only.sh scripts/check_publication_claim_freeze.py
git_commit_or_worktree_state: 461fe4c+dirty
artifact_path: docs/generated/publication_claim_freeze.md

## Decision

- Submission decision: `blocked_cf4_p0_manuscript_quarantine`
- Native morphology atlas present: `False`
- Public claim count: `8`
- Failed gates: `pdf_claim_lint_passed`
- BLOCKED audit-disclosure evidence receipt: `eda4df392574c5e08a54269b3caea4b1c2f03fba358582636fe2907e9f1bc628`
- Claim release from that receipt: `blocked`; audit disclosure only.

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
| `claim_release_blocked_by_evidence_graph` | `True` |
| `exact_claim_evidence_receipt_consumed` | `True` |
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

| Claim ID | Owner | Scientific level | Status | Allowed Phrase | Artifacts | Tests | Caveats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `framework.claim_tiered_observatory` | `COMMON` | `C1` | `allowed_with_caveats` | claim-tiered observational/statistical framework | `docs/generated/status_snapshot.json`<br>`docs/generated/claim_ledger.json`<br>`docs/generated/status_matrix.md` | `tests/contracts/test_status_snapshot.py`<br>`python -m common.status_snapshot --write docs/generated/status_snapshot.json` | DAG completion is project bookkeeping only.<br>Production validation remains false without native, null, mask, and covariance gates. |
| `transfer.current_external_paths` | `COMMON` | `C2` | `allowed_with_caveats` | transfer-conditional result | `docs/generated/transfer_sensitivity_report.md` | `tests/contracts/test_transfer_sensitivity_report.py`<br>`python scripts/generate_transfer_sensitivity_report.py --dry-run` | External/proxy transfer paths are not native validated artifacts.<br>Transfer metadata labels are provenance labels only. |
| `mio.certificates_diagnostic_only` | `MIO` | `C2` | `allowed_with_caveats` | diagnostic-only certificate | `docs/generated/result_pack_C.md` | `tests/result_packs/test_pack_C.py`<br>`tests/contracts/test_claim_language_lint.py` | MIO reports are not truth, posterior, or model-ranking objects.<br>HTT evidence traces remain HTT-owned and read-only to MIO reports. |
| `htt.local_global_candidate` | `HTT` | `C4` | `allowed_with_caveats` | local/global discrimination candidate | `docs/generated/result_pack_B.md` | `tests/result_packs/test_pack_B.py`<br>`tests/htt/test_local_global_mixture.py`<br>`tests/htt/test_posterior_pushforward.py` | Candidate wording is blocked when rank or FPR prerequisites fail.<br>MIO directional/depth rows are diagnostic cross-checks, not HTT evidence. |
| `obsstat.scalar_morphology_side_by_side` | `OBSSTAT` | `C3` | `allowed_with_caveats` | morphology compatibility remains unclaimed | `docs/generated/result_pack_A.md` | `tests/result_packs/test_pack_A.py`<br>`tests/contracts/test_claim_language_lint.py` | Scalar x/Q/Pi/F/G and low-ell feature summaries do not classify geometry.<br>Native morphology atlas support is absent. |
| `audit.external_package_disclosure` | `COMMON` | `C1` | `allowed_with_caveats` | external audit disclosure package | `docs/generated/external_audit_package.zip`<br>`docs/generated/external_audit_package_manifest.json` | `tests/contracts/test_audit_package_generator.py`<br>`scripts/codex_harness/run_pr122_source_only.sh scripts/build_external_audit_package.py --check` | Audit packaging is not publication readiness.<br>The CF4 P0 manuscript-source quarantine and absent current PDF remain visible inside the package. |
| `bass.future_native_interface_schema_only` | `BASS` | `C1` | `allowed_with_caveats` | future native solver interface schema | `htt/bass/transfer/native_schema.py`<br>`htt/bass/transfer/native_adapter.py`<br>`docs/generated/external_audit_package_manifest.json` | `tests/contracts/test_transfer_registry.py`<br>`tests/contracts/test_audit_package_generator.py` | The adapter stub must not return synthetic science values.<br>No native low-ell solver output is present in this repository state. |
| `manuscript.cf4_p0_source_quarantine_blocks_submission` | `COMMON` | `C1` | `blocked_for_submission` | current manuscript publication source remains quarantined | `docs/manuscript/main.tex`<br>`docs/generated/cf4_p0_quarantine_block.json`<br>`docs/generated/pdf_claim_lint_report.md` | `tests/contracts/test_manuscript_cf4_quarantine.py`<br>`tests/contracts/test_pdf_claim_lint.py` | No current manuscript PDF exists at the active path.<br>Retained chapter, bibliography, and generated TeX sources are immutable historical evidence with public_use false. |

## Forbidden Promotions

- Do not label external/proxy transfer outputs as native validated artifacts.
- Do not merge MIO diagnostic reports into HTT evidence or posterior quantities.
- Do not use scalar x/Q/Pi/F/G, low-ell summaries, or directional coherence as geometry or family-ID evidence.
- Do not present audit packaging or DAG completion as publication readiness.
- Do not build or submit a current manuscript while the CF4 P0 source quarantine or PDF claim-lint gate is open.
