---
name: htt-dag-orchestrator
description: Use when selecting htt_base DAG work, updating PR status, checking dependencies or replanning blocked work.
---

# htt-dag-orchestrator

Use canonical `docs/codex_handoff/pr_backlog.yaml` and `pr_status.yaml`;
`machine_readable/` is a compatibility mirror. Inspect only the relevant node and
dependents. Run `validate_pr_dag.py`; update mirrors with `sync_pr_dag_mirrors.py`.
An explicitly authorized runtime repair may proceed without pretending a science
node passed. Preserve active R9, historical failed tasks and cumulative usage.

Before execution use the existing native router and repo-root default
in `docs/harness/CURRENT_CODEX_RUNTIME.md`. Soft budgets trigger replanning, not
termination. Do not reopen a finished experiment or allocate another one-use run.
After five completed DAG PRs run the progress report. Keep measured scientific
progress separate from harness/PR counts. Record one executable next action and
stop repeated process-only expansion.

For the owner-authorized continuous solver-free campaign, use
`docs/harness/CONTINUOUS_RESEARCH_CONTROLLER.md`: actually dispatch, acknowledge,
record, independently review and request the next packet. Empty fixed-task READY
is not research exhaustion. Opt-in adaptive discovery may propose genuinely new
conditional methods/sources/assumptions or retain an exact evidence-scoped hold.
Planning checkpoints never qualify scientific products or original acceptance.
Preserve prior task IDs, packets, one-use runs and consumed escalation allowances.
