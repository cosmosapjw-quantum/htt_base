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
- `docs/PR_DELTAS/pr-042.md`
- `docs/generated/progress_checkpoints/checkpoint_025.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, PR-051, and
  PR-042.
- Latest progress after PR-042: 26/62 = 41.94% complete;
  dependency-weighted completion = 48.72%; critical path = 7/21 = 33.33%.
- Checkpoint 025 remains the latest checkpoint; the next checkpoint is due at
  30 completed PRs.
- Latest unblocked candidates: `PR-072`, `PR-081`, `PR-031`, `PR-052`,
  `PR-043`, and `PR-073`.

Important PR-042 boundary:

- `common.contracts.PreferredAxis` remains canonical and defaults
  `production_allowed=False`.
- `htt.direction.preferred_axis` is only an HTT helper over the COMMON axis
  contract; do not create `htt/src/htt` as a second HTT package root.
- `htt.zoa.axis_promotion` is the downstream harmonic synthesis lock. It wraps
  the existing basic axis gate and additionally requires finite coordinates,
  stable axis provenance, explicit PR-040 `SkySupport`, sha256
  sky-support/mask/scan-volume hashes, adequate mock coverage, and a matching
  `AxisPromotionRecord` with `lineage_status="self_attested_pre_solver"`.
- `restore_full_a2m` now requires that lock before reaching its rotation stub;
  diagnostic ZoA axes and hand-flipped production flags cannot rotate
  `a_lm`/`a_2m`.
- `AxisPromotionRecord` only matches axis/sky/mask/mock metadata in PR-042.
  Posterior/config/input hashes are carried forward for future upstream bundle
  wiring and are not proof of native or publication-grade lineage.
- PR-042 is gate metadata only. It does not create a production axis, native
  solver result, transfer validation, HTT posterior evidence, MIO certificate,
  blocked morphology-compatibility claim, or blocked geometry/family
  identification evidence.

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
