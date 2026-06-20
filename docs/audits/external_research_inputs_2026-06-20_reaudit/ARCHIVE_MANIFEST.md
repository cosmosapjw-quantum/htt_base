# External Research Re-Audit Input Archive Manifest

owner: COMMON
implementation_scope: external_research_input_intake
claim_tier: diagnostic_only
transfer_source: none
config_hash: sha256:4e7afaf16c97c5d1aeb174238c7ac9ef3cd19038fb0a0fb7a7730353cf4fd163
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R088 archive copy and response matrix`
git_commit_or_worktree_state: working-tree input snapshot hash-bound during REV-R088

## Boundary

This folder preserves the latest external research re-audit inputs and the repo-authored execution plan that translates them into a supplemental revision DAG. These files are external-input or planning evidence only. They are not publication evidence, native low-ell output, transfer validation, HTT evidence, MIO certification, morphology compatibility, or Bianchi family support.

## Files

| File | Role | SHA256 | Size bytes | Status |
| --- | --- | --- | ---: | --- |
| `docs/audits/external_research_inputs_2026-06-20_reaudit/audit_ver2.md` | `strict_external_reaudit` | `4c7cda3a41ea58c15d6382be7a523c57c2a2b0314250a2c78beada7bff515ddb` | 41634 | `raw_external_or_plan_input_hash_preserved` |
| `docs/audits/external_research_inputs_2026-06-20_reaudit/RESEARCH_AUDIT_REPORT.md` | `near_pass_external_reaudit` | `08c30c1df76a7808bfcbc31959d33660f10a45aaba2735935ed4ee1daa665b2d` | 14420 | `raw_external_or_plan_input_hash_preserved` |
| `docs/audits/external_research_inputs_2026-06-20_reaudit/2026-06-20-audit-ver2-research-hardening.md` | `repo_authored_execution_plan` | `18f1b0b3886af572ea3ad4282a4197d9735fc37360455cba289d6c0baa1298c1` | 43523 | `raw_external_or_plan_input_hash_preserved` |

## Priority Rule

When the two external reviews disagree, `audit_ver2.md` controls the revision path because it identifies source-identification, frame-identity, denominator-admissibility, and prior/error-budget blockers. The near-pass report is still retained for quick wording and hygiene fixes.

## Caveats

- diagnostic/proposed intake only
- not publication evidence
- no native low-ell solver output or validation is present
- no Bianchi family support
- no geometry support or evidence promotion
