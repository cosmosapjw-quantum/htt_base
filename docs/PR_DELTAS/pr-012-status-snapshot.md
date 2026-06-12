# PR-012 - Status snapshot and generated claim ledger pipeline

Date: 2026-06-12

## PR card

- ID: `PR-012`
- Title: StatusSnapshot and generated claim ledger pipeline
- Owner: COMMON
- Dependencies: `PR-010`, `PR-011`
- Required tests:
  - `python -m pytest tests/contracts/test_status_snapshot.py -q`
  - `python -m common.status_snapshot --write docs/generated/status_snapshot.json`
- DoD:
  - Manual test/module/status counts are prohibited in manuscript-facing docs.
  - Snapshot is canonical for public status.
- Kill switch: generated and manuscript/status counts must not disagree.

## Evidence gathering

Repository evidence read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `htt/src/common/contracts.py`
- `htt/src/common/status_snapshot.py`
- `htt/src/common/claim_ledger.py`
- `scripts/ver2_artifact_export.py`
- `docs/claim_ledger.md`
- `docs/status_matrix.md`

Documentation/web verification:

- Python `json` documentation confirms deterministic JSON serialization
  support such as `sort_keys` and indentation:
  https://docs.python.org/3/library/json.html
- Python `dataclasses` documentation confirms `asdict`/frozen dataclass
  behavior for the canonical row contracts:
  https://docs.python.org/3/library/dataclasses.html
- Python `argparse` documentation confirms package CLI parsing behavior for
  `python -m common.status_snapshot`:
  https://docs.python.org/3/library/argparse.html

## Divergence and role review

- Code cartographer:
  - Steelman: implement PR-012 in `common.status_snapshot`, using
    `StatusSnapshotEntry` and `ClaimLedgerEntry`; derive rows from the
    DAG/status files.
  - Attack: reusing `scripts/ver2_artifact_export.py` would write the wrong
    namespace and conflate VER2 artifact status with DAG status.
- Harness engineer:
  - Steelman: keep the red `tests/contracts/test_status_snapshot.py` contract
    and add a CLI/write path that fails if files cannot be written.
  - Attack: writing JSON only would leave manual Markdown counts as drift
    surfaces.
- Physics/statistics auditor:
  - Steelman: all PR-DAG rows should be diagnostic-only bookkeeping with
    `production_validated=False`.
  - Attack: `smoke_tested=True` or `completed=True` must not imply native
    solver validation, null/mock adequacy, transfer validation, posterior
    evidence, or morphology compatibility.
- Claim-gate reviewer:
  - Steelman: generated allowed claims may state only DAG status.
  - Attack: stale `docs/claim_ledger.md` rows claiming hand-maintained SSoT
    and stronger solver/family language violate the PR-012 kill switch.
- Regression tester:
  - Steelman: focused contract tests plus DAG/progress/smoke/collect checks
    cover this PR's blast radius.
  - Attack: generated artifacts record the worktree state at generation time;
    reviewers must not treat a source commit string as a scientific validation
    gate.

Subagents were closed after their PR-012 findings were recorded.

## Implementation

Changed files:

- `htt/src/common/status_snapshot.py`
- `tests/contracts/test_status_snapshot.py`
- `docs/generated/status_snapshot.json`
- `docs/generated/claim_ledger.json`
- `docs/generated/status_matrix.md`
- `docs/status_matrix.md`
- `docs/claim_ledger.md`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-012-status-snapshot.md`
- harness handoff/status docs

Key changes:

- Added `StatusBundle` and `StatusArtifactPaths`.
- Added `build_status_bundle`, `render_status_matrix`,
  `validate_status_matrix_matches_snapshot`, and `write_status_artifacts`.
- Added `python -m common.status_snapshot --write ...` CLI support.
- Generated DAG status rows from `pr_backlog.yaml` and `pr_status.yaml`.
- Generated companion claim-ledger rows whose allowed claims only report DAG
  state and whose forbidden claims block scientific-readiness interpretations.
- Normalized PR-card owner aliases:
  - `BASS_PY` -> canonical owner `BASS`, implementation scope `bass_py`;
  - `MANUSCRIPT` -> canonical owner `COMMON`;
  - legacy `TSC` -> canonical owner/scope `TSC_LEGACY`/`tsc_legacy`.
- Replaced old manual `docs/status_matrix.md` and `docs/claim_ledger.md`
  content with generated-authority indexes pointing to `docs/generated/*`.

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | ---: | --- |
| `venv/bin/python -m pytest tests/contracts/test_status_snapshot.py -q` before implementation | repo root | FAIL | Red phase: missing `build_status_bundle` and related public API. |
| `venv/bin/python -m pytest tests/contracts/test_status_snapshot.py -q` | repo root | PASS | `4 passed`; covers DAG/status generation, metadata, canonical owner normalization, companion writes, Markdown count-drift rejection, and CLI writes. |
| `venv/bin/python -m pytest tests/contracts/test_status_snapshot.py tests/contracts/test_ownership_firewall.py tests/contracts/test_artifact_manifest.py -q` | repo root | PASS | `26 passed`; adjacent ownership and manifest contracts preserved. |
| `venv/bin/python -m py_compile htt/src/common/status_snapshot.py htt/src/common/claim_ledger.py tests/contracts/test_status_snapshot.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Wrote status snapshot, claim ledger, and status matrix sidecars. |
| `python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | FAIL | `/usr/bin/python` cannot import the src-layout package (`No module named common`) in this checkout. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Exact module CLI path works when the src-layout package path is supplied. |
| Generated sidecar inspection via `json.load` and `rg` | repo root | PASS | 62 rows, 14 completed after PR-012 status update, no raw `TSC` owner/scope rows, no `production_validated=True` rows, no forbidden public phrases found. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-012 complete: `14/62 = 22.58%`; dependency-weighted `28.72%`; critical path `5/21 = 23.81%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6900 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6847/6906 tests collected (59 deselected)`. |

## Review findings and fixes

- Finding: the real backlog uses `BASS_PY` and `MANUSCRIPT` card owners,
  which are not canonical `Owner` enum values.
  - Fix: added a generator-boundary owner adapter that emits canonical rows.
- Finding: a legacy `TSC` owner could leak into public generated status.
  - Fix: tests now cover legacy `TSC` normalization and generated rows emit
    only `TSC_LEGACY` if such a card appears.
- Finding: stale manual `docs/claim_ledger.md` described itself as an SSoT
  and carried stronger legacy rows.
  - Fix: replaced it with a generated-authority index pointing to
    `docs/generated/claim_ledger.json`.
- Finding: old `docs/status_matrix.md` was a stub/manual surface.
  - Fix: replaced it with a generated-authority index pointing to
    `docs/generated/status_matrix.md`.
- Finding: bare `/usr/bin/python` cannot import `common` in this src-layout
  checkout.
  - Fix: recorded the failure and reran the module command with
    `PYTHONPATH=htt/src` plus the repository venv. PR-001 remains the package
    install/import authority for this environment.

## Claim hygiene and scientific scope

Numerical/scientific impact: none; COMMON status-generation tooling only.

Artifact/claim-tier impact: COMMON L2 diagnostic bookkeeping. PR-012 creates a
canonical generated public status surface for DAG completion and claim-ledger
bookkeeping. It does not add native solver outputs, transfer calibration,
HTT posterior/evidence validation, MIO diagnostic certification,
null/mock/covariance adequacy, sky-support adequacy, morphology compatibility,
or family-ID evidence.

## Residual risks

- Generated sidecars record the generation-time worktree state. Because a
  committed artifact cannot contain its own final commit hash without a
  follow-up regeneration, treat `source_commit` as provenance for the generator
  run, not as a scientific validation key.
- The older VER2 exporter still owns VER2 manuscript generated snippets. PR-012
  does not migrate all manuscript includes to the new DAG-status sidecars.
- Full VER2 artifact-export tests are higher-cost gates and were not used as
  the fast PR-012 acceptance suite.
