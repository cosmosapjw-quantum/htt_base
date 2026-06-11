# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-013-mio-htt-type-firewall.md`
- `docs/generated/progress_checkpoints/checkpoint_010.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`

Current state:

- PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020, PR-010,
  PR-021, PR-011, and PR-013 are complete.
- Generated checkpoint artifacts:
  `docs/generated/progress_checkpoints/checkpoint_005.md` and
  `docs/generated/progress_checkpoints/checkpoint_010.md`.
- Checkpoint 010: 10/62 = 16.13% complete, dependency-weighted 19.49%,
  critical-path 4/21 = 19.05%, no blockers, no replan required.
- Progress after PR-013: 11/62 = 17.74% complete, dependency-weighted
  21.54%, critical-path 4/21 = 19.05%, no blockers, no checkpoint due until
  15 completed PRs.
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
- Unblocked next candidates from the live progress report: `PR-014`,
  `PR-040`, `PR-012`, `PR-022`, and `PR-070`. Topological next is `PR-014`;
  `PR-014` is on the current critical path.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Do not promote quarantined figure/PDF assets without valid sidecar manifests.
- Reuse `reject_mio_likelihood_inputs` for downstream HTT likelihood ingress
  rather than creating parallel MIO/HTT merge guards.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python -m pytest tests/contracts/test_mio_htt_no_merge.py -q
venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py htt/workspace/contracts/tests/test_g19_enforcement.py -q
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
