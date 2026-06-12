# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-xqpi-fg-formalism/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-052.md`
- `docs/generated/progress_checkpoints/checkpoint_030.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, PR-051,
  PR-042, PR-072, PR-081, PR-031, and PR-052.
- Latest progress after PR-052: 30/62 = 48.39% complete;
  dependency-weighted completion = 53.85%; critical path = 8/21 = 38.1%.
- Checkpoint 030 is current. The next checkpoint is due at 35 completed PRs.
- Latest unblocked candidates: `PR-043`, `PR-073`, `PR-082`, `PR-032`, and
  `PR-053`.
- Progress advanced by five PRs since checkpoint 025; the harness did not
  require a replan.

Important PR-052 boundary:

- `mio.formalism.normalized_score.NormalizedScore` composes PR-050
  `DepartureBundle` and PR-051 `BudgetSpec`.
- Q is a MIO-owned, diagnostic-only policy-normalized score over `x_C`.
- Q carries explicit `numerator_policy`, `denominator_policy`, and selected
  denominator use `signed_projection_normalization`.
- Q payloads preserve separate departure/budget transfer provenance and
  inherit sky/covariance/null status from the budget.
- Q does not implement certified F, Pi, G_F, HTT posterior pushforward, HTT
  evidence, MIO certificates, native solver output, transfer validation,
  morphology compatibility, or geometry/family-identification evidence.
- Q artifact labels, caveats, and metadata reject certified-F, inference,
  class-label, and solver-result wording.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- PR-053 owns certified F and must not back-propagate F semantics into Q.
- After five more completed PRs, rerun the checkpoint procedure with
  `--checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints`.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
