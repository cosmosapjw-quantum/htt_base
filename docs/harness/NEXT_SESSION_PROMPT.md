# Next Session Prompt

State current DAG node, blockers, required skills, commands to run, and next PR target.

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-004-codex-assets.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`

Current state:

- PR-000, PR-001, PR-002, PR-003, and PR-004 are complete.
- Five-PR checkpoint after PR-004: 5/62 = 8.06% complete,
  dependency-weighted 7.69%, critical-path 14.29%, no blockers.
- Next policy-ordered PR is PR-005.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-identification claims before native low-ell
  morphology atlas plus null/mask/covariance/equivalence/rank/PPC gates.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
```
