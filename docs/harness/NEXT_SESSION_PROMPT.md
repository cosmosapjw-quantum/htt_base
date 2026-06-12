# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-transfer-provenance/SKILL.md`
- `.agents/skills/htt-observable-statistics/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-072.md`
- `docs/generated/progress_checkpoints/checkpoint_025.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, PR-051,
  PR-042, and PR-072.
- Latest progress after PR-072: 27/62 = 43.55% complete;
  dependency-weighted completion = 49.74%; critical path = 7/21 = 33.33%.
- Checkpoint 025 remains the latest checkpoint; the next checkpoint is due at
  30 completed PRs.
- Latest unblocked candidates: `PR-081`, `PR-031`, `PR-052`, `PR-043`, and
  `PR-073`.

Important PR-072 boundary:

- `htt.obsstat.scalar_lowell` is OBSSTAT feature extraction only. It computes
  `C_l`, `S_1/2`, parity, and input-frame planarity with explicit definitions.
- `a_lm` inputs must use dense full storage with every `m=-l..l` mode present.
  Packed real-map or healpy-style positive-`m` storage needs a future explicit
  adapter and must not be silently interpreted here.
- Supplying both `C_l` and `a_lm` requires matching overlapping `C_l` values.
- Low-ell scalar payloads are `feature_only` unless an explicit
  `LowEllNullCalibration` is attached. Null-calibrated p-values require null
  ensemble, look-elsewhere, tail, mask, covariance, scan-volume, and mock-count
  metadata.
- Top-level `obsstat.scalar_lowell` and `htt.obsstat.scalar_lowell` are aliased
  to the same module object to preserve class identity.
- PR-072 does not create HTT model inputs, MIO outputs, native solver outputs,
  transfer outputs, morphology outputs, geometry claims, or family-ID support.

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
