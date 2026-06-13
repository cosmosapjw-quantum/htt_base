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
- `docs/PR_DELTAS/pr-083.md`
- `docs/generated/progress_checkpoints/checkpoint_035.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: 37/62 = 59.68%.
- Dependency-weighted completion: 64.62%.
- Critical path completion: 9/21 = 42.86%.
- Checkpoint 035 is current; next checkpoint is due at 40 completed PRs.
- Latest unblocked candidates: `PR-054` and `PR-075`.
- The next topological node is `PR-054`.
- The progress harness reported no blockers and no replan requirement.

Important PR-083 boundary:

- `bass.atlas.budget_ceiling_optimizer` is BASS-owned, diagnostic-only, and
  pre-solver.
- It emits positive finite `U_C` ceiling policy results only with explicit
  transfer source/spec, valid range, prior, admissible set, rank metadata,
  rejected-candidate provenance, depth-gap metadata, config/input hashes,
  generating command, and worktree state.
- It lets MIO reference `ceiling_policy_id` and `ceiling_result_hash` through
  compact payloads and PR-051 `BudgetSpec` conversion.
- External/proxy ceilings remain transfer-conditional and non-certifying for
  F; depth-gap references require bin, covariance, null, and denominator
  evolution metadata.
- It does not run or fake a native solver, validate external transfer as
  native, create HTT posterior/evidence content, create a MIO certificate,
  provide morphology compatibility, or provide geometry/family-identification
  evidence.

Immediate PR-054 target:

- Title: Pi exceedance curve and threshold discipline.
- Owner: MIO.
- Depends: `PR-052`, `PR-053`.
- Files: `htt/mio/formalism/exceedance.py`,
  `tests/mio/test_exceedance.py`.
- DoD: Pi is an exceedance curve, not a truth probability; threshold choice is
  metadata/pre-registered or the output remains curve-only.
- Kill switch: reject any wording or payload that describes Pi as the
  probability that anisotropy is true.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior or evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Continue the per-PR loop with web/doc verification, role divergence,
  implementation, tests, adversarial review, status updates, and commit.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_normalized_score.py tests/mio/test_filling_fraction.py tests/mio/test_budget_spec.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke
```
