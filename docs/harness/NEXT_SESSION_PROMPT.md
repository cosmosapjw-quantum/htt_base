# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-022.md`
- `docs/generated/progress_checkpoints/checkpoint_015.md`
- `docs/generated/status_snapshot.json`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`

Current state:

- PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020, PR-010,
  PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, and PR-022 are complete.
- Generated checkpoint artifacts:
  `docs/generated/progress_checkpoints/checkpoint_005.md` and
  `docs/generated/progress_checkpoints/checkpoint_010.md` and
  `docs/generated/progress_checkpoints/checkpoint_015.md`.
- Checkpoint 010: 10/62 = 16.13% complete, dependency-weighted 19.49%,
  critical-path 4/21 = 19.05%, no blockers, no replan required.
- Progress after PR-022: 15/62 = 24.19% complete, dependency-weighted
  29.74%, critical-path 5/21 = 23.81%, no blockers, no checkpoint due until
  20 completed PRs.
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
- PR-013 added `workspace.contracts.htt_posterior`, exported the new
  `HTTPosteriorBundle` and `HttLikelihoodTerm`, and extended `MioCertificate`
  with diagnostic-only query/raise helpers. The PR-013 guard rejects direct
  certificates, MIO-shaped payloads, MIO cross-check reports, and MIO
  diagnostic scalar keys as HTT likelihood inputs.
- PR-014 added `common.transfer_registry.TransferFunctionSpec`,
  `TransferRegistry`, and `workspace.contracts.transfer`. Transfer-dependent
  results now have a canonical metadata shape for source, family, valid range,
  observable kind, normalization, calibration status, caveats, and validation
  gates. External/AniCLASS paths cannot claim native validation.
- PR-040 added `common.sky_support`, richer `common.contracts.SkySupport`
  fields, sky-facing manifest validation, deterministic mask hashes, sky
  fractions, completeness status, and an AST guard against raw
  longitude/latitude arithmetic means in production summaries.
- PR-012 added `common.status_snapshot`, generated
  `docs/generated/status_snapshot.json`, `docs/generated/claim_ledger.json`,
  and `docs/generated/status_matrix.md`, and converted old manual
  `docs/status_matrix.md` / `docs/claim_ledger.md` surfaces into
  generated-authority indexes. The generated rows are diagnostic-only DAG
  bookkeeping and keep `production_validated` false.
- PR-022 added `scripts/codex_harness/new_pr_delta.py`,
  `docs/PR_DELTAS/TEMPLATE.md`, and `tests/contracts/test_pr_delta_template.py`
  so PR_DELTA/review artifacts are generated from active DAG cards with
  overwrite protection, owner normalization, web-check status, and structured
  safe-default claim metadata.
- Unblocked next candidates from the live progress report: `PR-070`,
  `PR-015`, `PR-050`, `PR-041`, and `PR-023`. Topological next is `PR-070`;
  `PR-050` is on the current critical path.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Do not promote quarantined figure/PDF assets without valid sidecar manifests.
- Reuse `reject_mio_likelihood_inputs` for downstream HTT likelihood ingress
  rather than creating parallel MIO/HTT merge guards.
- Reuse `TransferFunctionSpec` for downstream transfer-dependent producers
  rather than creating local transfer metadata dictionaries.
- Reuse `common.sky_support.validate_sky_facing_artifact_metadata` for
  directional artifact metadata and `common.sky_geometry.spherical_mean` for
  directional summaries.
- Reuse `common.status_snapshot` for public DAG status counts; do not restore
  manual status or claim-ledger SSoTs.
- Reuse `scripts/codex_harness/new_pr_delta.py` and
  `docs/PR_DELTAS/TEMPLATE.md` for future PR_DELTA scaffolds; do not restore
  ad hoc PR-delta formats.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python -m pytest tests/contracts/test_pr_delta_template.py -q
python scripts/codex_harness/new_pr_delta.py PR-070 --dry-run
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
