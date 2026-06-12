# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-observable-statistics/SKILL.md`
- `.agents/skills/htt-family-identification-gate/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-073.md`
- `docs/generated/progress_checkpoints/checkpoint_030.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, PR-051,
  PR-042, PR-072, PR-081, PR-031, PR-052, PR-043, and PR-073.
- Latest progress after PR-073: 32/62 = 51.61% complete;
  dependency-weighted completion = 56.92%; critical path = 8/21 = 38.1%.
- Checkpoint 030 is current. The next checkpoint is due at 35 completed PRs.
- Latest unblocked candidates: `PR-082`, `PR-032`, `PR-053`, and `PR-074`.
- Checkpoint is not due and the harness does not require a replan.

Important PR-073 boundary:

- `htt.obsstat.morphology` adds OBSSTAT-owned diagnostic morphology-axis and
  alignment feature extraction from a caller-supplied finite symmetric 3x3
  tensor.
- The payload records antipodal axis convention, principal and plane-normal
  diagnostic axes, eigenvalues, eigenvalue gaps, degeneracy tolerance,
  response rank, effective rank, null-space dimension, condition metadata,
  planarity descriptors, alignment descriptors, config/input hashes, caveats,
  and optional null/look-elsewhere metadata.
- `DiagnosticMorphologyAxis.to_preferred_axis()` is a fail-closed adapter only:
  it returns a COMMON `PreferredAxis` with `production_allowed=False`,
  `source="raw_diagnostic"`, `weight_mode="uniform_fallback"`, and
  `selection_mode="none"`.
- PR-073 morphology axes remain non-production and cannot seed harmonic
  synthesis without PR-042/PR-043 gates.
- PR-073 does not add HTT posterior evidence, MIO certificates, native solver
  validation, transfer validation, morphology compatibility, or
  geometry/family-identification evidence.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- After three more completed PRs, rerun the checkpoint procedure with
  `--checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints`.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
