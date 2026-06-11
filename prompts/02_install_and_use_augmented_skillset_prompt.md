# Prompt: install and use augmented skillset

You are working in the `htt_base` repository. First read `AGENTS.md`, then inspect `.agents/skills`, `.codex/agents`, `.codex/rules`, `docs/codex_handoff/02_long_range_PR_backlog.md`, and `docs/codex_handoff/08_skill_trigger_matrix.md`.

Before editing code, run:

```bash
python scripts/codex_harness/verify_skill_layout.py .
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml
```

For each PR:

1. Select the next unblocked DAG node.
2. Invoke the required skills from `docs/codex_handoff/08_skill_trigger_matrix.md`.
3. Brainstorm using distinct subagents: mapper, physics/stat auditor, harness engineer, claim reviewer, regression tester, convergence director.
4. Implement meaningful changes toward the PR goal; do not stop at cosmetic gates if core evidence plumbing is missing.
5. Run validation appropriate to changed files.
6. Run `/review`-style self-audit with `$htt-adversarial-review-loop` and any relevant domain skill.
7. Fix concrete findings.
8. Update `docs/harness` ledgers and PR status.
9. Every five PRs, run progress report and replan if percent complete has not advanced.

Never claim native Bianchi family identification before the external/native low-ell solver outputs have been integrated through the transfer/atlas/obsstat gates.
