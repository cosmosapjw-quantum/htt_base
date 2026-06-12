# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-xqpi-fg-formalism/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-032.md`
- `docs/generated/progress_checkpoints/checkpoint_030.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, PR-051,
  PR-042, PR-072, PR-081, PR-031, PR-052, PR-043, PR-073, PR-082, and PR-032.
- Latest progress after PR-032: 34/62 = 54.84% complete;
  dependency-weighted completion = 59.49%; critical path = 8/21 = 38.1%.
- Checkpoint 030 is current. The next checkpoint is due at 35 completed PRs.
- Latest unblocked candidates: `PR-053`, `PR-074`, and `PR-083`.
- The next topological node is `PR-053`:
  `Pi filling-fraction curve and exceedance report`.
- Checkpoint is not due and the harness does not require a replan.

Important PR-032 boundary:

- `docs/generated/theorem_to_test_map_legacy_tsc.json` is COMMON-owned audit
  metadata derived from `tsc.validation.theorem_map`.
- Rows are validation obligations and historical witness links only.
- The map records `TSC_LEGACY` provenance but does not revive TSC/Teff as an
  active science owner.
- It is not production validation, HTT evidence, a MIO certificate, transfer
  validation, native solver validation, morphology compatibility, or
  geometry/family-identification evidence.
- Witness pytest nodes are collected by
  `tests/contracts/test_theorem_to_test_map.py`.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- After one more completed PR, rerun the checkpoint procedure with
  `--checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints`.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio -q
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
