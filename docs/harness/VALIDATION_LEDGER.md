# Validation Ledger

Record commands actually run. Never mark skipped checks as passed.

## PR-001 - Editable install and import-path stabilization

Date: 2026-06-12

Changed files: `htt/pyproject.toml`, `htt/__init__.py`, `htt/htt/__init__.py`,
`htt/test_packaging_imports.py`, `docs/PR_DELTAS/pr-001-packaging.md`,
`docs/codex_handoff/pr_status.yaml`, `docs/harness/VALIDATION_LEDGER.md`.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `python -m pip install -e './htt[dev]'` | repo root | FAIL | `/usr/bin/python` is PEP 668 externally managed. |
| `python -m pip install --break-system-packages --dry-run -e './htt[dev]'` | repo root | PASS | Dry-run only; no persistent override used. |
| `venv/bin/python -m pytest htt/test_packaging_imports.py -q` | repo root | PASS | `5 passed`. |
| `venv/bin/python -m pip install -e './htt[dev]'` | repo root | PASS | Editable `bass-py-0.8.2+w8.2` built. |
| `venv/bin/python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | repo root | PASS | `1541 tests collected`. |
| `venv/bin/python -m pip check` | repo root | PASS | No broken requirements found. |
| Clean venv PR-card commands with venv `python` first on `PATH` | repo root | PASS | Editable install and collect-only both passed; temp-dir imports passed with no `PYTHONPATH`. |
| `python .agents/skills/htt-scientific-code-validation/scripts/check_no_mock_results.py` | repo root | FAIL | Pre-existing legacy/audit `calibration_factor` and mock-result mentions outside the PR-001 packaging diff. |
| `git diff --check -- <PR-001 files>` | repo root | PASS | No whitespace errors. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | repo root | PASS | `Completed 2/62 = 3.23%`; checkpoint not due. |

Numerical/scientific impact: none; packaging/import infrastructure only.

Artifact/claim-tier impact: L0 infrastructure. No result artifact, transfer
output, posterior/evidence bundle, MIO diagnostic certificate, null calibration,
or family-identification claim was generated.

## PR-003 - PR DAG machine-readable manifest and progress engine

Date: 2026-06-12

Changed files: `scripts/codex_harness/validate_pr_dag.py`,
`scripts/codex_harness/progress_report.py`,
`scripts/codex_harness/test_pr_dag_harness.py`,
`docs/codex_handoff/pr_dag.mmd`, `docs/codex_handoff/pr_status.yaml`,
`machine_readable/pr_status.yaml`, `docs/PR_DELTAS/pr-003-dag-progress.md`,
`docs/harness/VALIDATION_LEDGER.md`.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` before implementation | repo root | FAIL | Red phase: four expected harness failures. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` after reviewer edge-case tests | repo root | FAIL | Red phase: two expected harness failures. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` | repo root | PASS | `6 passed`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --write-mermaid docs/codex_handoff/pr_dag.mmd` | repo root | PASS | Generated Mermaid graph from validated DAG. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | repo root | PASS | `Completed 3/62 = 4.84%`; checkpoint not due. |
| `python scripts/codex_harness/progress_report.py machine_readable/pr_backlog.yaml machine_readable/pr_status.yaml --json` | repo root | PASS | Same metrics as docs status. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; echo status_cmp=$?` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6813 tests collected`; existing unknown marker warnings remain for PR-002 taxonomy. |
| Scoped forbidden-claim `rg` over PR-003 files | repo root | PASS | No forbidden-risk phrases in changed PR-003 files. |

Numerical/scientific impact: none; DAG/progress harness only.

Artifact/claim-tier impact: COMMON L0 bookkeeping. Percent complete counts DAG
cards only and is not solver, transfer, inference, MIO, null, morphology, or
family-identification evidence.
