# Publication Claim Freeze

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:c78bac5fdbae0c4ac78d08bf58397e8fa531947b5540007f40d89b4f41e2f0ba`
input_hashes:
- docs/audit_prompts/claim_firewall_review.md:sha256:8d10cb45fc88b4de2d3629c012096b4370cc6cd45c9b2ceefdd5a237f7ee7c77
- docs/audit_prompts/future_solver_interface_review.md:sha256:33b05ec5952e1434bd82b9a8aaacd1b540d897c2f3c40cf4a8b54771a1f18c0f
- docs/audit_prompts/local_global_review.md:sha256:5e78f85612fedb84bdf0aeef4b3e9f9baaa5368b563f2c602587af9896d96ae0
- docs/audit_prompts/manuscript_figure_review.md:sha256:bc34fe7364e8c69be10705ac560f551a07e841a4db51ae17a2dc292e19236bad
- docs/audit_prompts/transfer_provenance_review.md:sha256:1c7cca8dc358495c8004c1dcf3968377ded0735720631d445a64b3c3ceb31a95
- docs/generated/claim_ledger.json:sha256:b49828ebc36e0542bd1162a6b2b90e0320883fc7e964d72a38424910ecfb68e2
- docs/generated/manuscript_figure_inventory.md:sha256:645c403f2d73bf3c3d798e1eb9d0b850b4ca3087c5b9c07f59fb5c4ae6513641
- docs/generated/missing_figure_references.md:sha256:3a2bd5b0319caee1ab86c3fa6093707c7400528ebd3b1f6af7d920d3005c8487
- docs/generated/pdf_claim_lint_report.md:sha256:39396efeeab03ea1c084002c7b5ab34c1998d791e395829a5970ffa83a1480e0
- docs/generated/result_pack_A.md:sha256:676f2150c2fe24503ab37ba52b0e3826a39c0bce6cf346c75e28b13336c07c7b
- docs/generated/result_pack_B.md:sha256:57c2ae21d774acf3c87fe51d6562dbb62c1ccced9f367a2b6cbfbb12a82181d1
- docs/generated/result_pack_C.md:sha256:2b37198072126ce63fc76376c84741bcb154c5c75e9544cfbf36061a8fb30c77
- docs/generated/status_matrix.md:sha256:515dc625f1260ab6c8921dd93e611163cfd349059e8e687b51f3cf2dc18b212b
- docs/generated/status_snapshot.json:sha256:da0dbc84e54addf1c927361d1e1620aad45a7cf55188c82b6d8996ebb8a7982d
- docs/generated/transfer_sensitivity_report.md:sha256:b2634c82ef783687cc2d304c50bb64487fa4556833bcc1a55464f7cae136903c
- scripts/check_publication_claim_freeze.py:sha256:3dae9096d4b7241b65fd1649c37e27aeb9e25459768a48d576debeb8c1f9580a
- tests/contracts/test_publication_claim_freeze.py:sha256:ecc6f44ef087438a411e2e6fdaadd128510d11a2eb0e5aec6ea091de07e81537
caveats:
- Publication claim freeze controls public wording; it is not submission approval.
- Current transfer-dependent outputs remain transfer-conditional.
- MIO diagnostics remain separate from HTT inference.
- Native morphology atlas support is absent in this repository state.
- Missing or quarantined manuscript figures block final submission freeze.
generating_command: python scripts/check_publication_claim_freeze.py
git_commit_or_worktree_state: 9d520cc+dirty
artifact_path: docs/generated/publication_claim_freeze.md

## Decision

- Submission decision: `claim_freeze_only_not_submission_approval`
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
| `pdf_claim_lint_passed` | `True` |
| `transfer_provenance_included` | `True` |

## Manuscript Blockers

| Metric | Value |
| --- | ---: |
| Includegraphics refs | 118 |
| Resolved refs | 118 |
| Missing refs | 0 |
| Quarantined refs | 0 |
| Text audit findings | 10 |
| Claim-risk findings | 0 |

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
