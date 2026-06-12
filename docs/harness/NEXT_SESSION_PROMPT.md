# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-041.md`
- `docs/generated/progress_checkpoints/checkpoint_015.md`
- `docs/generated/status_snapshot.json`

Current state:

- PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020, PR-010,
  PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, and PR-041 are complete.
- Generated checkpoint artifacts:
  `docs/generated/progress_checkpoints/checkpoint_005.md`,
  `docs/generated/progress_checkpoints/checkpoint_010.md`, and
  `docs/generated/progress_checkpoints/checkpoint_015.md`.
- Progress after PR-041: 19/62 = 30.65% complete, dependency-weighted
  36.92%, critical-path 6/21 = 28.57%, no blockers, no checkpoint due until
  20 completed PRs.
- PR-010 added canonical owner/claim-tier/scope enums and HTT/MIO
  bundle-role firewall checks.
- PR-011 added `common.artifact_manifest`, `scripts/check_artifact_manifests.py`,
  and `docs/generated/quarantined_figures.md`.
- PR-012 added `common.status_snapshot`, generated
  `docs/generated/status_snapshot.json`, `docs/generated/claim_ledger.json`,
  and `docs/generated/status_matrix.md`, and converted old manual status
  surfaces into generated-authority indexes.
- PR-013 added the new HTT posterior bundle ingress guard and rejects MIO
  diagnostic payloads as HTT likelihood inputs.
- PR-014 added `common.transfer_registry.TransferFunctionSpec` and related
  validation for transfer-dependent results.
- PR-015 added `common.semantic_guards.no_overclaim` and
  `scripts/check_claim_language.py` as a COMMON hard-fail claim-language
  guard for active docs/manuscripts/reports.
- PR-022 added `scripts/codex_harness/new_pr_delta.py`,
  `docs/PR_DELTAS/TEMPLATE.md`, and `tests/contracts/test_pr_delta_template.py`.
- PR-040 added COMMON sky-support metadata, deterministic mask hashes, sky
  fractions, completeness status, sky-facing manifest validation, and
  spherical-mean direction guards.
- PR-070 added `htt.obsstat` as the OBSSTAT facade over the canonical COMMON
  `ObservableVector`.
- PR-050 added `mio.formalism` with `DepartureComponent`,
  `ComponentBreakdown`, and `DepartureBundle`. It validates signed `x_C`
  comparator projections from canonical `B_C` components using signs
  `(+1, -1, +1, +1)`, requires comparator/frame/units/config/input/caveat
  metadata, preserves negative values, exposes cancellation index, and requires
  PR-014 transfer metadata for transfer-derived bundles.
- PR-041 added `htt.zoa.selection_ladder` and
  `common.healpix_selection.source_mask_from_pixel_mask`. The ladder separates
  raw, ZoA-masked, angular-completeness, and mock-calibrated support summaries,
  records COMMON sky-support metadata, config/input hashes, caveats, and keeps
  all exported axes diagnostic/fail-closed with `production_allowed=False`.
  `production_mode=True` forbids uniform fallback and requires adequate
  mock-calibration weights, but it does not promote support to posterior
  evidence.
- Unblocked next candidates from the live progress report: `PR-023`,
  `PR-071`, `PR-080`, `PR-030`, `PR-113`, `PR-051`, and `PR-042`.
  Topological next is `PR-023`; `PR-051` is the current critical-path successor
  after PR-050, and `PR-042` is now unblocked by PR-041.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Reuse `TransferFunctionSpec` for transfer-dependent producers.
- Reuse `common.semantic_guards.no_overclaim` and
  `scripts/check_claim_language.py` for active claim-language scans.
- Keep `htt.zoa.selection_ladder` support summaries diagnostic-only until a
  later posterior-derived axis promotion gate exists with its own recorded
  tests and claim-tier review.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
python scripts/codex_harness/new_pr_delta.py PR-023 --dry-run
python scripts/check_claim_language.py docs docs/manuscript --dry-run
venv/bin/python -m pytest tests/htt/test_zoa_selection_ladder.py -q
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
