# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-observable-statistics/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-054.md`
- `docs/generated/progress_checkpoints/checkpoint_035.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: 38/62 = 61.29%.
- Dependency-weighted completion: 66.15%.
- Critical path completion: 10/21 = 47.62%.
- Checkpoint 035 is current; next checkpoint is due at 40 completed PRs.
- Latest unblocked candidates: `PR-075` and `PR-055`.
- The next topological node is `PR-075`.
- The progress harness reported no blockers and no replan requirement.

Important PR-054 boundary:

- `mio.formalism.exceedance` is MIO-owned, diagnostic-only, and pre-solver.
- Pi is an exceedance curve over explicit Q or certified-F diagnostic samples,
  using strict `sample_value > threshold` counting under explicit
  `measure_kind` and threshold-policy metadata.
- Selected thresholds require pre-registered metadata; otherwise outputs remain
  curve-only.
- Direct or bridged transfer-labelled inputs require PR-014 metadata and remain
  transfer-conditional.
- Mock/null measures require non-default covariance and null/mock support
  status metadata.
- PR-054 does not create truth probabilities, HTT posterior/evidence content,
  MIO certificates, p-values/FPR claims, native solver validation, transfer
  validation, morphology compatibility, or geometry/family-identification
  evidence.

Immediate PR-075 target:

- Title: BiPoSH/sparse covariance feature extraction.
- Owner: OBSSTAT.
- Depends: `PR-071`, `PR-074`.
- Files: `htt/obsstat/biposh_features.py`,
  `tests/obsstat/test_biposh_features.py`.
- DoD: BiPoSH norms are rotation-aware and convention-tagged; mask, beam, and
  systematic caveat hooks exist.
- Kill switch: reject any path where nonzero BiPoSH directly maps to a Bianchi
  geometry claim.

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
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_biposh_features.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_alm_conventions.py tests/obsstat/test_template_fit.py tests/obsstat/test_observable_vector.py -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke
```
