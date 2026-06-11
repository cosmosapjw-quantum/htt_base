---
name: htt-dag-orchestrator
description: Use when selecting the next PR, validating dependencies, updating PR status, computing progress percentages, or replanning the long-range DAG for htt_base.
---

# htt-dag-orchestrator


Follow the machine-readable DAG. Never choose a PR with incomplete dependencies unless the task is a formal replan PR. Use `validate_pr_dag.py` and `progress_report.py`. After every five completed PRs, force a checkpoint and close completed subagents.

Decision order:
1. Validate DAG.
2. Load status.
3. Find unblocked PRs.
4. Prefer the earliest topological PR unless a blocker report justifies a replan.
5. Record exact rationale in PR_DELTA.


## Required output when invoked

Return:

- evidence read,
- proposed changes,
- tests to run,
- risks and kill-switches,
- artifacts/status updates needed.
