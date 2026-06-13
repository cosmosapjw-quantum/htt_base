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
- `docs/PR_DELTAS/pr-075.md`
- `docs/generated/progress_checkpoints/checkpoint_035.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: 39/62 = 62.90%.
- Dependency-weighted completion: 67.69%.
- Critical path completion: 10/21 = 47.62%.
- Checkpoint 035 is current; the next completed PR triggers checkpoint 040.
- Latest unblocked candidates: `PR-055` and `PR-076`.
- The next topological node is `PR-055`.
- The progress harness reported no blockers and no replan requirement.

Important PR-075 boundary:

- `htt.obsstat.biposh_features` is OBSSTAT-owned, diagnostic-only, and
  pre-solver.
- BiPoSH/sparse covariance payloads summarize caller-supplied sparse
  coefficients only.
- Payloads require harmonic convention metadata, rotation metadata,
  deterministic sparse hashes, duplicate-key rejection, threshold accounting,
  sky/mask/beam/systematic/covariance/null statuses, config/input hashes,
  generating command, and git/worktree provenance.
- Optional transfer-derived payloads require PR-014 metadata and remain
  transfer-conditional.
- PR-075 does not estimate coefficients from maps, run or fake a native
  solver, calibrate null tails, create HTT posterior/evidence content, create
  MIO certificate content, validate transfer, provide morphology compatibility,
  or support geometry/family evidence.

Immediate PR-055 target:

- Title: G_F depth gap and log-gap robustness.
- Owner: MIO.
- Depends: `PR-053`, `PR-054`, `PR-040`.
- Files: `htt/mio/formalism/isotropy_gap.py`,
  `tests/mio/test_isotropy_gap.py`.
- DoD: `G_F` and `log g_F` handle floors, bin covariance metadata, and
  denominator-evolution split; `G` cannot be exported without depth-bin
  metadata.
- Kill switch: reject any path where `G_F` alone triggers a global tilt claim.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior or evidence semantics.
- Do not make geometry/family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Continue the per-PR loop with web/doc verification, role divergence,
  implementation, tests, adversarial review, status updates, and commit.
- After PR-055, run the required 40-PR checkpoint command and update checkpoint
  artifacts.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_isotropy_gap.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py tests/mio/test_filling_fraction.py tests/mio/test_budget_spec.py tests/mio/test_normalized_score.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke
```
