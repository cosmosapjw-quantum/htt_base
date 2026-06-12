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
- `docs/PR_DELTAS/pr-081.md`
- `docs/generated/progress_checkpoints/checkpoint_025.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, PR-051,
  PR-042, PR-072, and PR-081.
- Latest progress after PR-081: 28/62 = 45.16% complete;
  dependency-weighted completion = 50.77%; critical path = 7/21 = 33.33%.
- Checkpoint 025 remains the latest checkpoint; the next checkpoint is due at
  30 completed PRs.
- Latest unblocked candidates: `PR-031`, `PR-052`, `PR-043`, `PR-073`, and
  `PR-082`.

Important PR-081 boundary:

- `bass.transfer.native_schema` and `bass.transfer.native_adapter` are
  schema-only, fail-closed BASS_PY handoff surfaces for a future low-ell solver
  artifact.
- The live BASS package root is `htt/bass/transfer`; stale backlog references
  to `htt/src/bass/...` were corrected across YAML, JSON, and long-range
  markdown mirrors.
- Native schema specs carry `schema_only_no_solver_output`,
  `native_solver_result=false`, `returns_values=false`,
  `outputs_available=false`, and `consumable_as_result=false`.
- `FutureNativeLowEllAdapterStub.evaluate()`, `solve()`,
  `load_solver_output()`, and `__call__()` all raise `NotImplementedError`;
  the PR does not return zero-filled, proxy, synthetic, or native science
  values.
- `common.transfer_registry.validate_transfer_dependent_result()` rejects
  schema-only, non-consumable, or no-value transfer metadata as result
  provenance.
- PR-081 does not validate native transfer, relabel external transfer as
  native, create HTT evidence, create MIO output, or support morphology,
  geometry, or family-ID claims.

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
