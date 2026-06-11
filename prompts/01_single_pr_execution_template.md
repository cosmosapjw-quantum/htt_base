# Single PR execution template

Run PR `<PR-ID>` from the DAG.

- Read the PR card and dependencies.
- Confirm all dependency PRs are complete in `pr_status.yaml`.
- Perform web/docs check if external/current behavior is involved.
- Spawn or simulate distinct subagents: code_cartographer, harness_engineer, physics_stat_auditor, claim_gate_reviewer, regression_tester.
- Steelman, object, converge.
- Implement meaningful code/test/docs changes.
- Run the PR tests and relevant smoke suite.
- Run `/review` or reviewer subagents.
- Fix findings.
- Update PR_DELTA and status.
- Commit as `<PR-ID>: <imperative summary>`.
