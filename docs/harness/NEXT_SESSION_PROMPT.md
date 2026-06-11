# Next Session Prompt

State current DAG node, blockers, required skills, commands to run, and next PR target.

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-010-ownership-firewall.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`

Current state:

- PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020, PR-010, and PR-021
  are complete.
- Generated five-PR checkpoint artifact:
  `docs/generated/progress_checkpoints/checkpoint_005.md`.
- Checkpoint 005: 5/62 = 8.06% complete, dependency-weighted 7.69%,
  critical-path 14.29%, no blockers, no replan required.
- PR-020 added deterministic collect/smoke/fast/package runner commands in
  `scripts/codex_harness/run_subset.py`.
- PR-010 added canonical owner/claim-tier/scope enums and HTT/MIO
  bundle-role firewall checks. Canonical contract rows now normalize legacy
  `TSC`/`tsc` inputs to `TSC_LEGACY` / `tsc_legacy`.
- PR-021 added a COMMON optional dependency registry and generated
  `docs/generated/optional_dependency_status.md` for machine-local
  skip/blocker attribution. This is diagnostic harness provenance only.
- Progress after PR-021: 9/62 = 14.52%; dependency-weighted 15.90%;
  critical-path 4/21 = 19.05%; checkpoint not due until 10 completed PRs.
- Unblocked next candidates from the live progress report: `PR-011`, `PR-013`,
  `PR-014`, and `PR-040`. Topological next is `PR-011`; `PR-014` is on the
  current critical path.

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
venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q
venv/bin/python -m pytest tests/contracts/test_optional_dependencies.py -q
```
