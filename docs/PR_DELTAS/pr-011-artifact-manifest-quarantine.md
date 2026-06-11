# PR-011 PR delta: artifact manifest validation and figure quarantine

## Goal

Add COMMON L2 artifact-manifest validation helpers and a deterministic
quarantine checker for existing figure/PDF assets that lack valid manifest
sidecars. The generated quarantine inventory is diagnostic-only: it accounts
for pre-existing assets and blocks claim-bearing promotion until provenance is
added.

This PR does not regenerate figures, inspect image content, reinterpret
figures, implement a native low-ell solver, validate transfer calibration,
produce HTT posterior/evidence, promote MIO diagnostics beyond diagnostic-only
scope, or make family-ID claims.

The existing `docs/PR_DELTAS/pr-011-subtrack-1.md` is stale material from an
older numbering scheme and was not used as the active PR delta for this DAG PR.

## Evidence read

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-011 card
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `htt/src/common/contracts.py`
- `htt/src/common/test_contracts.py`
- `tests/contracts/test_ownership_firewall.py`
- `scripts/ver2_artifact_export.py`
- `scripts/test_ver2_artifact_export.py`
- `docs/generated/repo_inventory.json`
- `docs/generated/optional_dependency_status.md`
- `docs/generated/progress_checkpoints/checkpoint_005.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-manuscript-figure-audit/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`

## Web/doc checks

- WEB_CHECK_STATUS: done
- Python `pathlib` documentation checked for object-oriented filesystem path
  traversal and path semantics.
  URL: https://docs.python.org/3/library/pathlib.html
- Python `dataclasses` documentation checked for dataclass field introspection
  and generated dataclass behavior.
  URL: https://docs.python.org/3/library/dataclasses.html
- Python `hashlib` documentation checked for SHA-256 hashing behavior.
  URL: https://docs.python.org/3/library/hashlib.html
- Python `json` documentation checked for JSON encoding/decoding and
  deterministic sorted-key output behavior.
  URL: https://docs.python.org/3/library/json.html

## Subagent divergence

- code_cartographer:
  - Steelman: add `common.artifact_manifest` as a facade around the canonical
    `common.contracts.ArtifactManifest`; use sidecar manifests and quarantine
    old assets rather than generating new figures.
  - Attack: do not duplicate the manifest schema, do not run the VER2 exporter
    as a checker, and do not retrofit provenance for 88 legacy PNG assets.
- harness_engineer:
  - Steelman: deterministic CLI with `--dry-run`, `--repo-root`,
    repeatable `--scan-root`, `--output`, manifest validation, and generated
    Markdown metadata.
  - Attack: a sidecar must prove it describes the scanned file; custom CLI
    invocations must record replayable command metadata.
- physics_stat_auditor:
  - Steelman: missing provenance makes artifacts non-claim-bearing by default.
  - Attack: free-text caveats alone are too weak; missing transfer, sky/mask,
    null/covariance, or native provenance gates must keep outputs blocked from
    stronger claims.
- claim_gate_reviewer:
  - Steelman: require owner/scope/claim tier/config/input/caveats plus
    transfer source, sky support status, null mock status, command, and git or
    worktree state.
  - Attack: morphology-atlas readiness must not satisfy native-transfer
    validation; native transfer provenance requires explicit native transfer
    or native solver validation.
- regression_tester:
  - Steelman: use `venv/bin/python` for pytest and include adjacent ownership,
    exporter, package, smoke, and collect checks.
  - Attack: PR-card tests alone would miss import compatibility and stale
    figure-check behavior.

## Chosen plan

1. Add failing PR-011 tests under `tests/contracts/test_artifact_manifest.py`.
2. Add `htt/src/common/artifact_manifest.py` as a facade around the canonical
   `ArtifactManifest`, with validation helpers for PR-011 artifact/provenance
   metadata.
3. Add `scripts/check_artifact_manifests.py` with deterministic scan, dry-run,
   write, and nonzero exit on malformed or invalid sidecar manifests.
4. Generate `docs/generated/quarantined_figures.md` from current disk state.
5. Record PR-011 completion in both status files and materialize checkpoint
   010 because the completed PR count reached 10.

## Files changed

- `htt/src/common/artifact_manifest.py`
- `scripts/check_artifact_manifests.py`
- `tests/contracts/test_artifact_manifest.py`
- `docs/generated/quarantined_figures.md`
- `docs/generated/progress_checkpoints/checkpoint_010.md`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-011-artifact-manifest-quarantine.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/PR_PROGRESS.md`
- `docs/harness/CLAIM_LEDGER.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | ---: | --- |
| `venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py -q` before implementation | repo root | FAIL | Red phase: missing `common.artifact_manifest`. |
| `venv/bin/python scripts/check_artifact_manifests.py --dry-run` before implementation | repo root | FAIL | Red phase: checker script absent. |
| `venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py -q` after first implementation | repo root | FAIL | Expected additional canonical dataclass issue after missing `input_hashes`; test tightened to require both field-level and dataclass diagnostics. |
| `venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py -q` after reviewer fixes | repo root | PASS | `11 passed`; covers required metadata, native-transfer gate, sidecar path match, dry-run, write, and invalid sidecar JSON exit. |
| `python scripts/check_artifact_manifests.py --dry-run` | repo root | PASS | Exit 0; dry-run reports 96 quarantined assets, 0 manifested figures, 0 manifest issues, and writes nothing. |
| `venv/bin/python scripts/check_artifact_manifests.py` | repo root | PASS | Wrote `docs/generated/quarantined_figures.md`; report records 96 quarantined assets and no manifest issues. |
| `venv/bin/python -m py_compile htt/src/common/artifact_manifest.py scripts/check_artifact_manifests.py` | repo root | PASS | Touched Python modules compile. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py htt/src/common/test_contracts.py htt/src/common/test_ver2_contract_layer.py -q` | repo root | PASS | `41 passed`; common ownership and manifest compatibility preserved. |
| `venv/bin/python -m pytest scripts/test_ver2_artifact_export.py::test_scan_figures_blocks_missing_manifest_and_accepts_generated_override scripts/test_ver2_artifact_export.py::test_caption_claim_violation_blocks_stronger_terms -q` | repo root | PASS | `2 passed`; older VER2 figure scanner behavior still intact. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6863 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6810/6869 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints` | repo root | PASS | After status update: `10/62 = 16.13%`; dependency-weighted `19.49%`; critical path `4/21 = 19.05%`; generated `checkpoint_010.md`; no replan required. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-011 files> && python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-011 files>` | repo root | PASS | No forbidden claim patterns or unmarked strong claims detected. |
| `git diff --check -- <PR-011 files>` | repo root | PASS | No whitespace errors in scoped PR-011 diff. |

## Review findings and fixes

- Finding: sidecar manifests were initially accepted without proving their
  `artifact_path` matched the scanned figure path. Fix: `validate_manifest_payload`
  accepts `expected_artifact_path`; figure scans now quarantine mismatched
  sidecars with `artifact_path_mismatch`, and a regression test covers it.
- Finding: CLI report metadata initially hard-coded the default command and
  omitted custom `--repo-root`, `--scan-root`, and `--output` arguments. Fix:
  the checker records the actual invocation arguments with shell quoting; tests
  cover replayable custom metadata.
- Finding: `native_morphology_atlas` was initially accepted as a native
  transfer-provenance gate. Fix: native transfer sources now require
  `native_transfer_validated` or `native_solver_validation`; morphology atlas
  support remains separate downstream evidence.
- Finding: exact forbidden phrases appeared in negative tests as literal
  assertions. Fix: tests compose the strings to avoid creating scanner hits in
  source.

## Claim hygiene and scientific scope

Numerical/scientific impact: none; manifest validation and generated
quarantine inventory only.

Artifact/claim-tier impact: COMMON L2 contract/checker metadata and one
COMMON diagnostic-only generated report. `docs/generated/quarantined_figures.md`
records current disk state: 96 existing figure/PDF assets are quarantined for
missing manifests, 0 are manifest-ready through this checker, and 0 sidecar
manifest issues were found. The report is not solver, transfer, posterior,
MIO diagnostic, null/mock/covariance, sky-support, morphology, or family-ID
evidence.

## Residual risks

- The checker validates JSON sidecar manifests for figure/PDF assets only; it
  does not yet validate every generated JSON result pack or manuscript table.
  That broader artifact ledger remains staged for downstream PRs.
- The committed quarantine report records the current dirty worktree state
  because unrelated local files were dirty before PR-011.
- Existing legacy figures remain in place and unmodified. They are inventoried
  as quarantined, not deleted or reinterpreted.
