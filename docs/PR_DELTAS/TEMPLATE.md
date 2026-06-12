# $pr_id - $title

## Goal

- Owner: $owner
- Depends: $depends
- Level: $level
- Scope: $scope
- Risk: $risk

## Evidence read

- PR card in `docs/codex_handoff/pr_backlog.yaml`
- Current `docs/codex_handoff/pr_status.yaml`
- Prior relevant PR deltas and touched-file tests

## Web/doc checks

- WEB_CHECK_STATUS: $web_check_status
- Record official documentation or web verification used before relying on
  external APIs, package behavior, or Codex mechanics. If unavailable, record
  that explicitly and continue with repository-local evidence.

## Subagent divergence

- code_cartographer:
  - Steelman:
  - Attack:
- harness_engineer:
  - Steelman:
  - Attack:
- physics_stat_auditor:
  - Steelman:
  - Attack:
- claim_gate_reviewer:
  - Steelman:
  - Attack:
- regression_tester:
  - Steelman:
  - Attack:

## Chosen plan

- Explain the selected patch and why alternatives were rejected.

## Files changed

$files

## Tests run

$tests

## Review findings and fixes

- Finding:
  - Fix:

## Claim-tier impact

This PR delta is project-review metadata and diagnostic harness provenance only;
it is not scientific readiness evidence, native solver validation, transfer
validation, posterior evidence, MIO diagnostic certificate evidence, morphology
compatibility, or family-identification evidence. It carries no C5/C6 science
claim.

- owner: $owner
- implementation_scope: $implementation_scope
- pr_scope: $scope
- claim_tier: diagnostic_only
- transfer_source: none
- sky_support_status: not_directional
- null_mock_status: not_statistical
- covariance_status: not_statistical
- ppc_status: not_applicable
- loocv_status: not_applicable

## Risk log

- DoD:
$dod
- Kill switch: $kill
- Residual risks:

## Status and artifacts

- Status files updated:
- Generated artifacts updated:
- Subagents closed:

## Commit

- Commit:
