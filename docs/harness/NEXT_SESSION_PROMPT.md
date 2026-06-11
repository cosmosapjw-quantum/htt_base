# Next Session Prompt

State current DAG node, blockers, required skills, commands to run, and next PR target.

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-020-harness-runner.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`

Current state:

- PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, and PR-020 are complete.
- Generated five-PR checkpoint artifact:
  `docs/generated/progress_checkpoints/checkpoint_005.md`.
- Checkpoint 005: 5/62 = 8.06% complete, dependency-weighted 7.69%,
  critical-path 14.29%, no blockers, no replan required.
- PR-020 added deterministic collect/smoke/fast/package runner commands in
  `scripts/codex_harness/run_subset.py`.
- Next policy-ordered PR is PR-010. PR-021 is also unblocked.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-identification claims before native low-ell
  morphology atlas plus null/mask/covariance/equivalence/rank/PPC gates.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
python scripts/codex_harness/run_subset.py --list
```
