# Publication Claim Freeze

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:8d5153162f93f1c3224c797de0a9b656006d3229cdb7433ecac5fc6bdf149b88`
input_hashes:
- docs/audit_prompts/claim_firewall_review.md:sha256:8d10cb45fc88b4de2d3629c012096b4370cc6cd45c9b2ceefdd5a237f7ee7c77
- docs/audit_prompts/future_solver_interface_review.md:sha256:33b05ec5952e1434bd82b9a8aaacd1b540d897c2f3c40cf4a8b54771a1f18c0f
- docs/audit_prompts/local_global_review.md:sha256:5e78f85612fedb84bdf0aeef4b3e9f9baaa5368b563f2c602587af9896d96ae0
- docs/audit_prompts/manuscript_figure_review.md:sha256:bc34fe7364e8c69be10705ac560f551a07e841a4db51ae17a2dc292e19236bad
- docs/audit_prompts/transfer_provenance_review.md:sha256:1c7cca8dc358495c8004c1dcf3968377ded0735720631d445a64b3c3ceb31a95
- docs/generated/claim_ledger.json:sha256:d30fa4bdefeaeb966adfd58b6c4658c5284fcad43e86c3b7b4d0a036cd4371bf
- docs/generated/external_audit_package_manifest.json:sha256:149bc1ca6eda94e7fe5d5fa781f6aacd0b262ec9ea2442eef4e7ca284fd30f6e
- docs/generated/manuscript_figure_inventory.md:sha256:8c705f855f7d5edaa4823ef562942aac41d2b679ee58a2d8c49c9a3c4b5138c9
- docs/generated/missing_figure_references.md:sha256:23c204246fb00c57992983505502096c5834ecac297fa36fdb72d9129b9041b0
- docs/generated/result_pack_A.md:sha256:676f2150c2fe24503ab37ba52b0e3826a39c0bce6cf346c75e28b13336c07c7b
- docs/generated/result_pack_B.md:sha256:57c2ae21d774acf3c87fe51d6562dbb62c1ccced9f367a2b6cbfbb12a82181d1
- docs/generated/result_pack_C.md:sha256:2b37198072126ce63fc76376c84741bcb154c5c75e9544cfbf36061a8fb30c77
- docs/generated/status_matrix.md:sha256:ce2f01380331077c81c20250db6f6bb5baf6e9b86d5bcc1877b481792e326e13
- docs/generated/status_snapshot.json:sha256:2f987d0d3d736c52e657e455b9bf63a44b93aee5b5ad2b3e3b286cd068641ff8
- docs/generated/transfer_sensitivity_report.md:sha256:b2634c82ef783687cc2d304c50bb64487fa4556833bcc1a55464f7cae136903c
- scripts/check_publication_claim_freeze.py:sha256:1125a269c5e43a76b843b2cd15b99865366ad4469053cda6db30ef00f0c27092
- tests/contracts/test_publication_claim_freeze.py:sha256:cd02069bc0579037f4560752f0918f4b58b2b7bf06493bad1a82d052b7543571
caveats:
- Publication claim freeze controls public wording; it is not submission approval.
- Current transfer-dependent outputs remain transfer-conditional.
- MIO diagnostics remain separate from HTT inference.
- Native morphology atlas support is absent in this repository state.
- Missing or quarantined manuscript figures block final submission freeze.
generating_command: python scripts/check_publication_claim_freeze.py
git_commit_or_worktree_state: b5753e2+dirty
artifact_path: docs/generated/publication_claim_freeze.md

## Decision

- Submission decision: `blocked_internal_only`
- Native morphology atlas present: `False`
- Public claim count: `8`
- Failed gates: `none`

This freeze allows only caveated status, framework, transfer-provenance, diagnostic, and audit-package claims.
It blocks stronger geometry, native-validation, or family-ID wording until the missing native and manuscript gates are closed.

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
| `claim_ledger_included` | `True` |
| `external_audit_package_included` | `True` |
| `manuscript_blockers_recorded` | `True` |
| `no_c5_c6_family_id_claim` | `True` |
| `no_forbidden_claim_language` | `True` |
| `transfer_provenance_included` | `True` |

## Manuscript Blockers

| Metric | Value |
| --- | ---: |
| Includegraphics refs | 94 |
| Resolved refs | unknown |
| Missing refs | 22 |
| Quarantined refs | 72 |
| Text audit findings | 23 |
| Claim-risk findings | 13 |

## Frozen Public Claims

| Claim ID | Owner | Tier | Status | Allowed Phrase | Artifacts | Tests | Caveats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `framework.claim_tiered_observatory` | `COMMON` | `C1` | `allowed_with_caveats` | claim-tiered observational/statistical framework | `docs/generated/status_snapshot.json`<br>`docs/generated/claim_ledger.json`<br>`docs/generated/status_matrix.md` | `tests/contracts/test_status_snapshot.py`<br>`python -m common.status_snapshot --write docs/generated/status_snapshot.json` | DAG completion is project bookkeeping only.<br>Production validation remains false without native, null, mask, and covariance gates. |
| `transfer.current_external_paths` | `COMMON` | `C2` | `allowed_with_caveats` | transfer-conditional result | `docs/generated/transfer_sensitivity_report.md` | `tests/contracts/test_transfer_sensitivity_report.py`<br>`python scripts/generate_transfer_sensitivity_report.py --dry-run` | External/proxy transfer paths are not native validated artifacts.<br>Transfer metadata labels are provenance labels only. |
| `mio.certificates_diagnostic_only` | `MIO` | `C2` | `allowed_with_caveats` | diagnostic-only certificate | `docs/generated/result_pack_C.md` | `tests/result_packs/test_pack_C.py`<br>`tests/contracts/test_claim_language_lint.py` | MIO reports are not truth, posterior, or model-ranking objects.<br>HTT evidence traces remain HTT-owned and read-only to MIO reports. |
| `htt.local_global_candidate` | `HTT` | `C4` | `allowed_with_caveats` | local/global discrimination candidate | `docs/generated/result_pack_B.md` | `tests/result_packs/test_pack_B.py`<br>`tests/htt/test_local_global_mixture.py`<br>`tests/htt/test_posterior_pushforward.py` | Candidate wording is blocked when rank or FPR prerequisites fail.<br>MIO directional/depth rows are diagnostic cross-checks, not HTT evidence. |
| `obsstat.scalar_morphology_side_by_side` | `OBSSTAT` | `C3` | `allowed_with_caveats` | morphology compatibility remains unclaimed | `docs/generated/result_pack_A.md` | `tests/result_packs/test_pack_A.py`<br>`tests/contracts/test_claim_language_lint.py` | Scalar x/Q/Pi/F/G and low-ell feature summaries do not classify geometry.<br>Native morphology atlas support is absent. |
| `audit.external_package_disclosure` | `COMMON` | `C1` | `allowed_with_caveats` | external audit disclosure package | `docs/generated/external_audit_package.zip`<br>`docs/generated/external_audit_package_manifest.json` | `tests/contracts/test_audit_package_generator.py`<br>`python scripts/build_external_audit_package.py --check` | Audit packaging is not publication readiness.<br>Missing manuscript figure provenance remains visible inside the package. |
| `bass.future_native_interface_schema_only` | `BASS` | `C1` | `allowed_with_caveats` | future native solver interface schema | `htt/bass/transfer/native_schema.py`<br>`htt/bass/transfer/native_adapter.py`<br>`docs/generated/external_audit_package_manifest.json` | `tests/contracts/test_transfer_registry.py`<br>`tests/contracts/test_audit_package_generator.py` | The adapter stub must not return synthetic science values.<br>No native low-ell solver output is present in this repository state. |
| `manuscript.figure_inventory_blocks_submission` | `COMMON` | `C1` | `blocked_for_submission` | manuscript figure inventory blocks final freeze | `docs/generated/manuscript_figure_inventory.md`<br>`docs/generated/missing_figure_references.md`<br>`docs/generated/quarantined_figures.md` | `tests/contracts/test_manuscript_figure_audit.py`<br>`python scripts/audit_manuscript_figures.py --dry-run` | Missing or quarantined figures are blockers, not promoted figures.<br>Text audit findings are review findings, not scientific results. |

## Forbidden Promotions

- Do not label external/proxy transfer outputs as native validated artifacts.
- Do not merge MIO diagnostic reports into HTT evidence or posterior quantities.
- Do not use scalar x/Q/Pi/F/G, low-ell summaries, or directional coherence as geometry or family-ID evidence.
- Do not present audit packaging or DAG completion as publication readiness.
- Do not submit the manuscript while missing or quarantined figure references remain unresolved.
