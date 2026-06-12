# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-080.md`
- `docs/generated/progress_checkpoints/checkpoint_020.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020, PR-010,
  PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, and PR-080 are complete.
- Generated checkpoint artifacts:
  `docs/generated/progress_checkpoints/checkpoint_005.md`,
  `checkpoint_010.md`, `checkpoint_015.md`, and `checkpoint_020.md`.
- Latest progress scoreboard:
  `docs/generated/progress_checkpoints/progress_scoreboard.md`.
- Progress after PR-080: 22/62 = 35.48% complete, dependency-weighted
  42.05%, critical-path 6/21 = 28.57%, no blockers, no checkpoint due until
  25 completed PRs.
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
- PR-023 extended `scripts/codex_harness/progress_report.py` with explicit
  skipped-PR accounting, `skipped`/`skipped_count` JSON fields,
  skipped/completed/blocked/in-progress overlap rejection, skipped exclusion
  from dependency satisfaction and `unblocked_next`, `--write-scoreboard`, and
  checkpoint markdown that lists skipped PRs. Checkpoint 020 was generated and
  no replan is required because progress advanced by 5 since checkpoint 015.
- PR-071 added `htt.obsstat.alm_conventions` with scalar and spin-2 harmonic
  convention metadata, channel-local OBSSTAT alm export gates, coordinate-frame
  matching against `SkySupport`, healpy-style coefficient-shape checks,
  deterministic NumPy-aware coefficient hashing, and no E/B sign export claim.
- PR-080 added `bass.transfer` under the live `htt/bass/transfer` package root.
  It wraps current AniCLASS-calibrated and empirical-proxy legacy transfer
  callables with PR-014 metadata, callable provenance, callable input domains,
  `claim_tier="conditional"`, `production_status="diagnostic_only"`,
  `transfer_conditional=True`, and `native_solver_result=False`.
- PR-040 added COMMON sky-support metadata, deterministic mask hashes, sky
  fractions, completeness status, sky-facing manifest validation, and
  spherical-mean direction guards.
- PR-070 added `htt.obsstat` as the OBSSTAT facade over the canonical COMMON
  `ObservableVector`.
- PR-050 added `mio.formalism` with signed `x_C` comparator projection
  metadata and PR-014 transfer metadata validation.
- PR-041 added `htt.zoa.selection_ladder` and
  `common.healpix_selection.source_mask_from_pixel_mask`, with diagnostic-only
  raw, ZoA-masked, angular-completeness, and mock-calibrated support summaries.
- Unblocked next candidates from the live progress report: `PR-030`,
  `PR-113`, `PR-051`, `PR-042`, `PR-072`, and `PR-081`.
  Topological next is `PR-030`; `PR-051` is the current critical-path successor
  after PR-050.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Reuse `TransferFunctionSpec` for transfer-dependent producers.
- Reuse `common.semantic_guards.no_overclaim` and
  `scripts/check_claim_language.py` for active claim-language scans.
- Keep OBSSTAT as feature extraction only: harmonic convention metadata is not
  HTT inference evidence or MIO certification.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
python scripts/codex_harness/new_pr_delta.py PR-030 --dry-run
python scripts/check_claim_language.py docs docs/manuscript --dry-run
venv/bin/python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
