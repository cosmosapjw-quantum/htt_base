# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-xqpi-fg-formalism/SKILL.md`
- `.agents/skills/htt-physics-math-audit/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-local-global-discrimination/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-055.md`
- `docs/generated/progress_checkpoints/checkpoint_040.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: 40/62 = 64.52%.
- Dependency-weighted completion: 69.74%.
- Critical path completion: 11/21 = 52.38%.
- Checkpoint 040 is current; the next checkpoint is due at 45 completed PRs.
- Latest unblocked candidates: `PR-076`, `PR-056`, and `PR-060`.
- The next topological node is `PR-076`.
- The progress harness reported no blockers and no replan requirement.

Important PR-055 boundary:

- `mio.formalism.isotropy_gap` is MIO-owned, diagnostic-only, and pre-solver.
- `log_g_F = log(max(F_comparison,floor))-log(max(F_reference,floor))`, and
  `G_F = exp(log_g_F)`.
- Payloads require explicit depth-bin metadata, covariance/null metadata,
  PR-040 sky/mask support fields, BudgetUse.DEPTH_GAP_REFERENCE, floor policy,
  sample-wise denominator-evolution split fields, config/input hashes,
  generating command, and git/worktree provenance.
- Optional transfer-derived records require PR-014 metadata, matching transfer
  source/spec IDs, and matching canonical transfer metadata hashes across
  compared bins.
- PR-055 does not calibrate p-values/FPR, create HTT posterior/evidence
  content, create MIO certificate content, validate transfer or native solver
  output, establish morphology compatibility, or support global-tilt,
  geometry, or family claims.

Immediate PR-076 target:

- Title: Null ensembles and look-elsewhere bookkeeping.
- Owner: OBSSTAT.
- Depends: `PR-072`, `PR-073`, `PR-074`, `PR-075`.
- Files: `htt/obsstat/null_ensembles.py`,
  `tests/obsstat/test_null_ensembles.py`.
- DoD: FLRW+mask+noise, local/systematic, and injected-template nulls can be
  represented; look-elsewhere metadata attaches to feature vectors.
- Kill switch: reject any p-value path without null ensemble provenance.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior or evidence semantics.
- Do not make geometry/family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Continue the per-PR loop with web/doc verification, role divergence,
  implementation, tests, adversarial review, status updates, and commit.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_null_ensembles.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_biposh_features.py tests/obsstat/test_template_fit.py tests/obsstat/test_morphology.py tests/obsstat/test_scalar_lowell.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke
```
