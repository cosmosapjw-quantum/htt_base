# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-xqpi-fg-formalism/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-051.md`
- `docs/generated/progress_checkpoints/checkpoint_025.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, and PR-051.
- Latest progress after PR-051: 25/62 = 40.32% complete;
  dependency-weighted completion = 47.18%; critical path = 7/21 = 33.33%.
- Checkpoint 025 was generated and no replan is required because progress
  advanced by 5 since checkpoint 020.
- Latest unblocked candidates: `PR-042`, `PR-072`, `PR-081`, `PR-031`, and
  `PR-052`.

Important PR-051 boundary:

- `mio.formalism.BudgetSpec` is the strict MIO denominator-policy contract.
- It separates `MES_linear`, `external_transfer`, `atlas_quantile`, and
  `observational` policies.
- `external_transfer` budgets and sensitivity points require PR-014 metadata
  and are transfer-conditional only.
- `atlas_quantile` is pre-solver schema scaffolding only and does not identify
  a Bianchi family.
- The legacy COMMON/BASS departure report bridge is restricted to explicit
  `MES_linear`/`linear_MES`; do not relabel legacy budgets as external transfer
  or atlas/observational policies.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Q/F/Pi/G_F PRs must consume the PR-051 MIO contract directly.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
