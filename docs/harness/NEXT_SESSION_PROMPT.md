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
- `docs/PR_DELTAS/pr-053.md`
- `docs/generated/progress_checkpoints/checkpoint_035.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: 35/62 = 56.45%.
- Dependency-weighted completion: 61.54%.
- Critical path completion: 9/21 = 42.86%.
- Checkpoint 035 is current; next checkpoint is due at 40 completed PRs.
- Latest unblocked candidates: `PR-074`, `PR-083`, and `PR-054`.
- The next topological node is `PR-074`, the next OBSSTAT wave item after
  PR-073.
- The progress harness reported no blockers and no replan requirement.

Important PR-053 boundary:

- `mio.formalism.CertifiedFillingFraction` is MIO-owned and diagnostic-only.
- F is computed sample-wise as signed sign-clean `x_C / U` under an
  admissible certified ceiling.
- `F_Bayes` is the mean of sample-wise F values, not a ratio of means.
- Invalid sectors, bad ceilings, and over-ceiling values fail closed without
  clipping.
- F payloads require generating command and git or worktree provenance.
- PR-053 does not add HTT evidence/posterior content, MIO certificates,
  native solver validation, transfer validation, morphology compatibility, or
  geometry/family-identification evidence.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Continue the per-PR loop with web/doc verification, role divergence,
  implementation, tests, adversarial review, status updates, and commit.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_filling_fraction.py tests/mio/test_budget_spec.py tests/mio/test_normalized_score.py tests/mio/test_departure_bundle.py -q
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
