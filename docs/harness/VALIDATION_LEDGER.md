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
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --write-mermaid docs/codex_handoff/pr_dag.mmd` | repo root | PASS | Wrote Mermaid graph after the DAG command returned OK. |
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

## PR-002 - pytest taxonomy and optional dependency skip gates

Date: 2026-06-12

Changed files: `pytest.ini`, `htt/pytest.ini`, `htt/pyproject.toml`,
`htt/conftest.py`, `htt/bass/validation/test_d2_regression_anchor.py`,
`htt/bass/forward/test_map_producer.py`,
`htt/bass/inference/test_fb113_bayes_factor_skeleton.py`,
`htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py`,
`scripts/codex_harness/test_pytest_taxonomy.py`,
`docs/PR_DELTAS/pr-002-test-taxonomy.md`,
`docs/codex_handoff/pr_status.yaml`, `machine_readable/pr_status.yaml`,
`docs/harness/VALIDATION_LEDGER.md`.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` before implementation | repo root | FAIL | Red phase: five expected marker/config/optional-gate failures. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `8 passed`; direct hook test covers monkeypatched missing optional deps. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6815 deselected`; L0 reachability only. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6762/6821 tests collected (59 deselected)` under default `not slow` addopts. |
| `venv/bin/python -m pytest -m "fast and not slow" -q` | repo root | PASS | `6 passed, 6815 deselected`. |
| `venv/bin/python -m pytest -m "requires_healpy or requires_dynesty" --collect-only -q` | repo root | PASS | `23/6821 tests collected (6798 deselected)`. |
| `cd htt && ../venv/bin/python -m pytest -m smoke -q` | `htt/` | PASS | `6 passed, 6781 deselected`. |
| `python -m pytest -m smoke -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; host interpreter lacks pytest. |
| `python -m pytest --collect-only -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; host interpreter lacks pytest. |

Numerical/scientific impact: none; test taxonomy and optional dependency
collection behavior only.

Artifact/claim-tier impact: COMMON L0 harness metadata. Smoke and collect-only
evidence is not solver, transfer, posterior/evidence, MIO diagnostic, null,
morphology, or family-identification evidence.

## PR-004 - Repo-scoped Codex assets and install checks

Date: 2026-06-12

Changed files: `.gitignore`, `.codex/agents/*.toml`,
`.codex/rules/default.rules`, `.agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py`,
`.agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py`,
`.agents/skills/htt-family-identification-gate/SKILL.md`,
`.agents/skills/htt-solver-handoff-readiness-audit/SKILL.md`,
`docs/codex_handoff/00_Codex_global_rules.md`,
`docs/codex_handoff/07_repo_skill_installation_guide.md`,
`docs/codex_handoff/08_skill_trigger_matrix.md`,
`docs/codex_handoff/INSTALL.md`, `scripts/codex_harness/test_codex_assets.py`,
`scripts/codex_harness/validate_codex_config_shape.py`,
`scripts/install_codex_handoff.sh`, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest scripts/codex_harness/test_codex_assets.py -q` before implementation | repo root | FAIL | Red phase: broken execpolicy examples and missing install doc. |
| `venv/bin/python -m pytest scripts/codex_harness/test_codex_assets.py -q` | repo root | PASS | `10 passed`. |
| `codex execpolicy check --pretty --rules .codex/rules/default.rules -- python -m pytest -q` | repo root | PASS | Decision `allow`; check does not execute pytest. |
| `codex execpolicy check --pretty --rules .codex/rules/default.rules -- python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | Decision `allow`. |
| `codex execpolicy check --pretty --rules .codex/rules/default.rules -- rm -rf /tmp/foo` | repo root | PASS | Decision `forbidden`. |
| `python scripts/codex_harness/verify_skill_layout.py .` | repo root | PASS | `18 skills OK`. |
| `python scripts/codex_harness/validate_codex_config_shape.py .` | repo root | PASS | No project-local `.codex/config.toml`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| Explicit PR-004 `check_forbidden_claims.py` scan over claim-sensitive asset/docs paths | repo root | PASS | No forbidden claim patterns detected. |
| Explicit PR-004 `check_claim_status.py` scan over claim-sensitive asset/docs paths | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` | repo root | PASS | `Completed 5/62 = 8.06%`; checkpoint due. |

Numerical/scientific impact: none; Codex orchestration, install, rule, skill,
and claim-scanner guardrails only.

Artifact/claim-tier impact: COMMON L0. No native solver, transfer calibration,
HTT posterior/evidence, MIO diagnostic certificate, null calibration,
morphology compatibility, or family-identification evidence was generated.

## PR-005 - Five-PR checkpoint and adaptive replan protocol

Date: 2026-06-12

Changed files: `scripts/codex_harness/progress_report.py`,
`scripts/codex_harness/test_pr_dag_harness.py`,
`docs/codex_handoff/checkpoint_protocol.md`,
`docs/generated/progress_checkpoints/README.md`,
`docs/generated/progress_checkpoints/checkpoint_005.md`, status and handoff
docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` before implementation | repo root | FAIL | Red phase: `--write-checkpoint-dir` was not implemented. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` | repo root | PASS | `11 passed`; covers checkpoint writer due/not-due, no-progress, JSON, malformed metadata, and existing DAG harness behavior. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints` | repo root | PASS | Generated `docs/generated/progress_checkpoints/checkpoint_005.md`; `5/62 = 8.06%`; no replan required. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir /tmp/htt_progress_json_check --json` | repo root | PASS | Output parsed as JSON and included `checkpoint_artifact` plus `replan_required: false`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-005 complete: `6/62 = 9.68%`; checkpoint not due; next checkpoint at 10. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-005 docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-005 docs>` before wording fix | repo root | FAIL | Flagged family-identification caveats without nearby status markers and an older DAG-status ledger phrase. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-005 docs>` | repo root | PASS | No unmarked strong claims detected after wording fixes. |

Numerical/scientific impact: none; progress and checkpoint harness only.

Artifact/claim-tier impact: COMMON L1 DAG bookkeeping. The generated checkpoint
artifact is not native solver, transfer calibration, HTT posterior/evidence,
MIO diagnostic, null calibration, morphology compatibility, or
family-identification evidence.

## PR-020 - Harness runner for pytest subsets

Date: 2026-06-12

Changed files: `scripts/codex_harness/run_subset.py`, `pytest.ini`,
`tests/contracts/test_harness_runner.py`,
`docs/codex_handoff/test_harness.md`, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_harness_runner.py -q` before implementation | repo root | FAIL | Red phase: six expected failures for old subsets, missing `--python`, ambient interpreter use, and unknown-subset message. |
| `venv/bin/python -m pytest tests/contracts/test_harness_runner.py -q` before root collection fix | repo root | FAIL | Red phase: top-level `tests` was absent from root `pytest.ini` `testpaths`, so the contract suite was not covered by `collect`. |
| `venv/bin/python -m pytest tests/contracts/test_harness_runner.py -q` | repo root | PASS | `8 passed`; covers list, dry-run, package target, unknown subset, failure propagation, venv default, no hidden `PYTHONPATH`, docs, and root collect visibility. |
| `python scripts/codex_harness/run_subset.py --list` | repo root | PASS | Lists `collect`, `fast`, `package`, and `smoke` with exact commands. |
| `python scripts/codex_harness/run_subset.py collect --dry-run` | repo root | PASS | Prints venv-backed collection command. |
| `python scripts/codex_harness/run_subset.py smoke --dry-run` | repo root | PASS | Prints venv-backed smoke command without running it. |
| `python scripts/codex_harness/run_subset.py fast --dry-run` | repo root | PASS | Prints venv-backed fast marker command. |
| `python scripts/codex_harness/run_subset.py package --dry-run` | repo root | PASS | Prints `htt/test_packaging_imports.py` package smoke command. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `8 passed`; marker taxonomy remains compatible with runner commands. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `env -u PYTHONPATH venv/bin/python -m py_compile scripts/codex_harness/run_subset.py` | repo root | PASS | Runner compiles with no `PYTHONPATH`. |
| `env -u PYTHONPATH venv/bin/python -m pytest --collect-only tests/contracts/test_harness_runner.py scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `16 tests collected`. |
| `env -u PYTHONPATH venv/bin/python -m pytest tests/contracts/test_harness_runner.py scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `16 passed`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6785/6844 tests collected (59 deselected)`; includes top-level contract tests. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6838 deselected`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py fast` | repo root | PASS | `6 passed, 6838 deselected`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py not-a-subset` | repo root | EXPECTED FAIL | Exit `2`; prints `unknown subset: not-a-subset` and does not run pytest. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py smoke --python /bin/false` | repo root | EXPECTED FAIL | Exit `1`; child return code propagates. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-020 complete: `7/62 = 11.29%`; checkpoint not due; unblocked next `PR-010`, `PR-021`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-020 docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-020 docs>` before wording fix | repo root | FAIL | Flagged a quoted overclaim term in the PR delta. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-020 docs>` | repo root | PASS | No unmarked strong claims detected after wording fix. |

Numerical/scientific impact: none; harness runner only.

Artifact/claim-tier impact: COMMON L1 harness metadata. These subset commands
provide deterministic pytest dispatch and failure propagation only. They do not
validate native solver behavior, transfer calibration, HTT posterior/evidence,
MIO diagnostics, null/mask/covariance adequacy, morphology compatibility, rank
sufficiency, equivalence-class separation, or family-identification evidence.
