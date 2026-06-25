# REV-R117 - PR07 audit-repair: governance surface + tickets + PAPER map closure

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
generating_command: `n/a (documentation + ticket registry)`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Land the in-repo governance surface for the PR07 audit-repair programme: the
step-by-step PR list, the CoVe-lane→agent/skill map, blocker matrix, claim
gates, dependency schedule, literature/novelty ledger, machine-readable PR
registry + blocked tickets, the PAPER-A/B freeze exit notes, and the
PAPER_THEOREM_MAP corollary-closure update. Plus CHANGELOG + CLAUDE.md.

## Deliverables

`docs/research_program/pr07/`:
- `README.md`, `PR_LIST.md` (P0..P3 with landed/blocked status).
- `AGENT_SKILL_MAP.md` — 10 CoVe lanes → `.claude` agents + `htt-*` skills +
  the concise chain-of-checks schema (folded, no new agents).
- `BLOCKER_RESOLUTION_MATRIX.md`, `CLAIM_GATES.md`, `DEPENDENCY_SCHEDULE.md`.
- `PAPER_FREEZE_PR07_007_008.md` — PR07-007/008 freeze gates.
- `PR08-005_2MRS_CROSS_RECONSTRUCTION_CONTRACT.md` — independent cross-check spec.
- `WEB_CRAG_LEDGER.md` + `web_sources.json` — literature + novelty boundaries.
- `pr_registry.yaml` + `tickets/{PR08-001,PR08-003,PR08-004,PR08-006,PR10-solver}.yaml`
  (each blocked ticket terminates in its registered blocker code).

`docs/research_program/pr04/PAPER_THEOREM_MAP.md`: the three former
`BLOCKED_PROOF_REVIEW` PAPER-A corollaries (radial-vorticity no-go, single-shell
degeneracy, temporal-tensor rank) marked **closed PR07-004** with their PR07
gate tests; A-Wigner split into A-boost + A-first-jet; duplicate-block
full-column-rank qualifier added.

`CHANGELOG.md` (Unreleased) + `CLAUDE.md` (§ header date + §3 latest-entry) updated.

## Claim discipline

Documentation/registry only; no code or claim-tier change. Blocked tickets carry
`BLOCKED_MISSING_PR4_E2E_ACCESS`, `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP`,
`BLOCKED_MISSING_FIELD_REALIZATIONS`, `BLOCKED_UPSTREAM`, `AWAITING_NATIVE_LOWELL_SOLVER`.
PAPER-C/D remain blocked behind the PR10 solver gates.

## Validation

| Command | Status |
| --- | --- |
| `pytest tests/contracts/test_pr07_audit_repair.py` | 6 passed (re-verified) |
| `python -c "import yaml; yaml.safe_load_all(...)"` over `pr_registry.yaml` + tickets | parses |
| forbidden-token scan over `docs/final_report/main.tex` | 0 |
