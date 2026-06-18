# Revision Claim Lanes

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
caveats:
- external/proxy transfer is not native transfer
- family identification remains blocked until native morphology atlas support exists
- scaffold package outputs are not publication evidence


| Lane | Allowed use | Forbidden use |
| --- | --- | --- |
| `blocked/governance_diagnostic/internal_only` | gate failure reports | evidence, odds-based inference claims, paper claims |
| `diagnostic_only/external_audit_conditioned/external_audit` | external audit diagnostics | paper-main inference or family use |
| `diagnostic_only/paper_appendix_conditioned/paper_appendix` | caveated diagnostic plots | validated evidence wording |
| `conditional/paper_appendix_conditioned/paper_appendix` | transfer-conditional summaries | native or geometry wording |
| `conditional/paper_main_candidate/paper_main` | caveat-box framework or forecast figures | claim without premise/null/covariance status |
| `validated/paper_main_validated/paper_main` | future native-validated results | unavailable in current repo state |

Caption rule: every promoted figure states claim lane, transfer source, null status, and forbidden-use sentence.
Supplemental DAG rule: `docs/codex_handoff/pr_dag_revision.yaml` is proposed only and must not overwrite `docs/codex_handoff/pr_status.yaml`.
