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
