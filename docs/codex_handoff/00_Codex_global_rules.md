# Codex global rules for this repo

Use these rules with `AGENTS.md`.

## PR execution policy

- Execute the PR DAG in topological order unless a blocker requires a small replan PR.
- A PR is complete only when code, tests, docs, PR_DELTA, and status updates are done.
- Do not open result-pack PRs before manifest, claim-tier, transfer-provenance, sky support, null, and MIO/HTT firewall gates are green.

## Subagent policy

Each PR must use distinct viewpoints:

- `code_cartographer`: map affected code paths.
- `harness_engineer`: design tests, commands, and artifacts.
- `physics_stat_auditor`: check physical/statistical assumptions.
- `claim_gate_reviewer`: enforce claim-tier and no-overclaim language.
- `regression_tester`: run or design failure-reproduction tests.

For large PRs add `docs_citation_auditor`. Add `security_dependency_auditor`
only if its project-local agent profile exists.

## Web/documentation policy

Before implementation, verify any external or current API/tool behavior through web/docs when available. If web access is unavailable, write `WEB_CHECK_SKIPPED` in the PR_DELTA with a reason and avoid inventing API behavior.

## No local-minimum rule

Do not repeatedly add only wrappers, gates, or placeholder TODOs. A wrapper/gate PR must unlock a named downstream PR and include tests that prove the gate blocks a real failure mode.

## Serial stacked-PR recovery execution

- `AUTO_STACKED_PR` permits one active implementation PR and never permits an
  automatic merge. `AUTO_MERGE` must fail closed.
- Advance lifecycle states only in this order: `PLANNED`, `ACTIVE`,
  `IMPLEMENTED`, `VALIDATED`, `REVIEWED`, `SEALED`, `PUSHED`, `PR_OPEN`.
- Activate a successor only when the predecessor is `PR_OPEN` and the branch
  base equals the recorded predecessor `SEALED_HEAD` exactly.
- Treat future work as `INELIGIBLE/DEFERRED` with zero retry and assurance
  budget. Do not treat it as a failed review.
- Deduplicate salvage by stable patch ID. Never transplant a historical branch
  tip or a complete historical worktree.
- Key substantive evidence by production and relevant dependency hashes.
  Presentation-only drift must not consume substantive assurance budget; a
  post-seal production mutation invalidates the seal.
- Publication stops at `PR_OPEN`. Merge is human-only.
