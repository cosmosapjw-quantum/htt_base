# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-transfer-provenance/SKILL.md`
- `.agents/skills/htt-xqpi-fg-formalism/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-074.md`
- `docs/generated/progress_checkpoints/checkpoint_035.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: 36/62 = 58.06%.
- Dependency-weighted completion: 63.59%.
- Critical path completion: 9/21 = 42.86%.
- Checkpoint 035 is current; next checkpoint is due at 40 completed PRs.
- Latest unblocked candidates: `PR-083`, `PR-054`, and `PR-075`.
- The next topological node is `PR-083`.
- The progress harness reported no blockers and no replan requirement.

Important PR-074 boundary:

- `htt.obsstat.template_fit` is OBSSTAT-owned diagnostic feature extraction.
- It emits amplitude, DeltaChi2, orientation scan volume/hash, covariance
  weighting metadata, and separate template-mean and covariance branches.
- It rejects covariance anomaly collapse, inconsistent chi-square aliases,
  invalid vectors, non-positive weights, non-positive-definite full
  covariance, missing scan metadata, and overclaim text.
- It does not create HTT posterior or evidence content, MIO reports, transfer
  validation, native solver output, morphology compatibility, or Bianchi
  geometry/family-identification evidence.

Immediate PR-083 target:

- Title: Budget ceiling optimizer policy interface.
- Owner: BASS_PY.
- Depends: `PR-051`, `PR-082`.
- Files: `htt/bass/atlas/budget_ceiling_optimizer.py`,
  `tests/bass/test_budget_ceiling_optimizer.py`.
- DoD: ceiling policies output `U_C` with provenance and valid range; MIO
  F/G can reference the ceiling policy explicitly.
- Kill switch: reject any policy that hides transfer source, prior, or
  admissible set.

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
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_budget_ceiling_optimizer.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_filling_fraction.py tests/mio/test_budget_spec.py tests/mio/test_global_tilt_budget.py -q
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
