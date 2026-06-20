# External Research Re-Audit Input Inventory

owner: COMMON
implementation_scope: external_research_input_intake
claim_tier: diagnostic_only
transfer_source: none
config_hash: sha256:4e7afaf16c97c5d1aeb174238c7ac9ef3cd19038fb0a0fb7a7730353cf4fd163
sky_support_status: not_directional
null_mock_status: not_statistical
archive_directory: `docs/audits/external_research_inputs_2026-06-20_reaudit`
archive_manifest: `docs/audits/external_research_inputs_2026-06-20_reaudit/ARCHIVE_MANIFEST.md`
generating_command: `Codex REV-R088 archive copy and response matrix`
git_commit_or_worktree_state: working-tree input snapshot hash-bound during REV-R088

## Input Status

The archive contains two external research re-audit reports and one repo-authored execution plan. It is used to drive supplemental `REV-R088+` tasks and does not change canonical PR DAG completion.

## Inputs

| Input | Role | SHA256 | Size bytes | Archive copy | Supersession | Top-level summary |
| --- | --- | --- | ---: | --- | --- | --- |
| `audit_ver2.md` | `strict_external_reaudit` | `4c7cda3a41ea58c15d6382be7a523c57c2a2b0314250a2c78beada7bff515ddb` | 41634 | `docs/audits/external_research_inputs_2026-06-20_reaudit/audit_ver2.md` | controls when conflicts arise | Reject/not-ready; blocks positive Bayes-factor, source-identification, scalar occupancy, frame-vorticity, and prior/error-budget claims until hardening gates exist. |
| `RESEARCH_AUDIT_REPORT.md` | `near_pass_external_reaudit` | `08c30c1df76a7808bfcbc31959d33660f10a45aaba2735935ed4ee1daa665b2d` | 14420 | `docs/audits/external_research_inputs_2026-06-20_reaudit/RESEARCH_AUDIT_REPORT.md` | subordinate to strict audit on conflicts | Near-pass; useful for discovery wording, Pi/F namespace, manual count, and matched-null forecast quick fixes. |
| `2026-06-20-audit-ver2-research-hardening.md` | `repo_authored_execution_plan` | `18f1b0b3886af572ea3ad4282a4197d9735fc37360455cba289d6c0baa1298c1` | 43523 | `docs/audits/external_research_inputs_2026-06-20_reaudit/2026-06-20-audit-ver2-research-hardening.md` | execution source for supplemental REV slice | Staged `REV-R088` through `REV-R101` plan with downclaim, formalism repair, statistical hardening, and package refresh tasks. |

## Canonical Decision

The supplemental revision slice starts at `REV-R088`. Canonical `PR-*` status remains complete at `62/62`; this intake does not rewrite `docs/codex_handoff/pr_status.yaml`.

## Caveats

- diagnostic/proposed intake only
- not publication evidence
- no native low-ell solver output or validation is present
- no Bianchi family support
- no geometry support or evidence promotion
