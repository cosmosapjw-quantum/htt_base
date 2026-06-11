# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-011-artifact-manifest-quarantine.md`
- `docs/generated/progress_checkpoints/checkpoint_010.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`

Current state:

- PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020, PR-010,
  PR-021, and PR-011 are complete.
- Generated checkpoint artifacts:
  `docs/generated/progress_checkpoints/checkpoint_005.md` and
  `docs/generated/progress_checkpoints/checkpoint_010.md`.
- Checkpoint 010: 10/62 = 16.13% complete, dependency-weighted 19.49%,
  critical-path 4/21 = 19.05%, no blockers, no replan required.
- PR-010 added canonical owner/claim-tier/scope enums and HTT/MIO
  bundle-role firewall checks. Canonical contract rows normalize legacy
  `TSC`/`tsc` inputs to `TSC_LEGACY` / `tsc_legacy`.
- PR-021 added a COMMON optional dependency registry and generated
  `docs/generated/optional_dependency_status.md` for machine-local
  skip/blocker attribution.
- PR-011 added `common.artifact_manifest`, `scripts/check_artifact_manifests.py`,
  and `docs/generated/quarantined_figures.md`. The quarantine report records
  96 existing figure/PDF assets without valid sidecar manifests, 0 manifested
  figures through the PR-011 checker, and 0 sidecar manifest issues.
- Progress after PR-011: 10/62 = 16.13%; dependency-weighted 19.49%;
  critical-path 4/21 = 19.05%.
- Unblocked next candidates from the live progress report: `PR-013`,
  `PR-014`, `PR-040`, `PR-012`, `PR-022`, and `PR-070`. Topological next is
  `PR-013`; `PR-014` is on the current critical path.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Do not promote quarantined figure/PDF assets without valid sidecar manifests.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
python scripts/check_artifact_manifests.py --dry-run
venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py -q
venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q
```
