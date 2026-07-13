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

## PR-071 - Harmonic and spin convention registry

Date: 2026-06-12

Changed files: `htt/obsstat/alm_conventions.py`,
`htt/obsstat/observable_vector.py`, `htt/obsstat/__init__.py`,
`tests/obsstat/test_alm_conventions.py`,
`tests/obsstat/test_observable_vector.py`, `docs/PR_DELTAS/pr-071.md`,
status mirrors, generated status sidecars, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/obsstat/test_alm_conventions.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| `venv/bin/python -m pytest tests/obsstat/test_alm_conventions.py -q` after red tests | repo root | FAIL | `7 failed`; module missing and raw alm payload accepted. |
| `venv/bin/python -m pytest tests/obsstat/test_alm_conventions.py -q` after first implementation | repo root | PASS | `7 passed`. |
| `venv/bin/python -m pytest tests/obsstat/test_alm_conventions.py tests/obsstat/test_observable_vector.py -q` after physics-audit fixes | repo root | PASS | `18 passed`. |
| `venv/bin/python -m pytest tests/obsstat/test_observable_vector.py htt/test_packaging_imports.py tests/obsstat/test_alm_conventions.py -q` | repo root | PASS | `23 passed`. |
| `python -m pytest tests/obsstat/test_alm_conventions.py -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; host interpreter lacks pytest. |
| `venv/bin/python -m pytest htt/test_packaging_imports.py tests/obsstat/test_alm_conventions.py --collect-only -q` | repo root | PASS | `14 tests collected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` before status update | repo root | PASS | `20/62 = 32.26%`; checkpoint due only because PR-071 was not yet marked complete. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` before YAML note fix | repo root | FAIL | YAML parser rejected a colon in the new plain-scalar status note. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated `status_snapshot.json`, `claim_ledger.json`, and `status_matrix.md`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` after status update | repo root | PASS | `21/62 = 33.87%`; dependency-weighted `40.0%`; critical path `6/21 = 28.57%`; no checkpoint due. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6961 deselected`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6908/6967 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest tests/contracts/test_claim_language_lint.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `25 passed`. |

Numerical/scientific impact: OBSSTAT metadata and export gating only. The PR
does not compute alms, transfer functions, likelihoods, posteriors, MIO
certificates, native solver outputs, or morphology atlas comparisons.

Artifact/claim-tier impact: diagnostic-only convention provenance. Convention
metadata is not transfer provenance, native validation, HTT evidence, MIO
certification, null calibration, morphology compatibility, or
family-identification evidence.

## PR-080 - External transfer registry wrapper

Date: 2026-06-12

Changed files: `htt/bass/transfer/__init__.py`,
`htt/bass/transfer/aniclass_adapter.py`, `htt/bass/transfer/registry.py`,
`tests/bass/test_external_transfer_registry.py`, `docs/PR_DELTAS/pr-080.md`,
status mirrors, generated status sidecars, progress scoreboard, and handoff
docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/bass/test_external_transfer_registry.py -q` before implementation | repo root | FAIL | Red phase: target file did not exist. |
| `venv/bin/python -m pytest tests/bass/test_external_transfer_registry.py -q` after first tests | repo root | FAIL | Expected red: `ModuleNotFoundError` for `bass.transfer`. |
| `venv/bin/python -m pytest tests/bass/test_external_transfer_registry.py -q` after initial implementation | repo root | PASS | `8 passed`. |
| `venv/bin/python -m pytest tests/bass/test_external_transfer_registry.py -q` after reviewer tests | repo root | FAIL | One native-spec fixture used malformed data instead of `TransferValidRange`. |
| `venv/bin/python -m pytest tests/bass/test_external_transfer_registry.py -q` after physics/claim fixes | repo root | PASS | `11 passed`. |
| `venv/bin/python -m pytest tests/bass/test_external_transfer_registry.py -q` after one-sided domain hardening | repo root | PASS | `13 passed`. |
| `venv/bin/python -m pytest tests/contracts/test_transfer_registry.py htt/htt/tests/test_bass_d2_transfer.py -q` | repo root | PASS | `25 passed`. |
| `venv/bin/python -m pytest tests/mio/test_departure_bundle.py::test_transfer_derived_bundle_requires_pr014_metadata tests/mio/test_departure_bundle.py::test_external_transfer_metadata_cannot_claim_native_validation tests/obsstat/test_observable_vector.py::test_transfer_derived_features_require_transfer_source_metadata tests/contracts/test_artifact_manifest.py::test_validate_manifest_payload_rejects_external_transfer_marked_native tests/contracts/test_claim_language_lint.py::test_mio_truth_and_external_native_overclaims_are_blocked -q` | repo root | PASS | `5 passed`; the `mio_truth` node name is a negative guard test, not a claim. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `python -m pytest tests/bass/test_external_transfer_registry.py -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; host interpreter lacks pytest. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` before status update | repo root | PASS | `21/62 = 33.87%`; PR-080 was next topological node. |
| `venv/bin/python -m py_compile htt/bass/transfer/__init__.py htt/bass/transfer/aniclass_adapter.py htt/bass/transfer/registry.py tests/bass/test_external_transfer_registry.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `22/62 = 35.48%`; dependency-weighted `42.05%`; critical path `6/21 = 28.57%`; no checkpoint due. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6974 deselected`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6921/6980 tests collected (59 deselected)`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-080 production files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-080 docs>` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/check_claim_language.py <PR-080 production files> --dry-run` | repo root | PASS | Production-surface claim-language scan passed. |
| `git diff --check -- <PR-080 files>` | repo root | PASS | Scoped diff has no whitespace errors. |

Numerical/scientific impact: BASS_PY provenance wrapping for existing legacy
external/proxy transfer-dependent scalar callables only. The PR does not run
CLASS/AniCLASS, compute transfer functions, implement a native solver, create
likelihoods/posteriors, create MIO certificates, or compare morphology atlas
features.

Artifact/claim-tier impact: conditional transfer-provenance metadata. The
registered paths are `AniCLASS_external` or `empirical_proxy`, diagnostic-only
for production status, and explicitly `native_solver_result=False`. They do
not validate external transfer as native or provide morphology/family evidence.

## PR-030 - TSC legacy boundary

Date: 2026-06-12

Changed files: `htt/tsc_legacy/__init__.py`, `htt/tsc_legacy/README.md`,
`htt/tsc/__init__.py`,
`docs/deprecation/tsc_legacy.md`,
`tests/tsc/test_tsc_legacy_boundary.py`, package/bridge compatibility files,
`docs/PR_DELTAS/pr-030.md`, status mirrors, generated status sidecars,
progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q` before implementation | repo root | FAIL | Red phase: target file did not exist. |
| `venv/bin/python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q` after red tests | repo root | FAIL | Expected red: missing `tsc_legacy`, docs, metadata, and helper behavior. |
| `venv/bin/python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q` before editable reinstall | repo root | FAIL | `ModuleNotFoundError: tsc_legacy`; package discovery needed explicit include and editable refresh. |
| `venv/bin/python -m pip install -e './htt[dev]'` | repo root | PASS | Refreshed editable package discovery after adding `tsc_legacy*`. |
| `venv/bin/python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q` after static import scan | repo root | FAIL | Static scan initially included test helper imports; fixed to skip test paths. |
| `venv/bin/python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q` | repo root | PASS | `8 passed`; PR target with venv interpreter. |
| `python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; host interpreter lacks pytest. |
| `venv/bin/python -m pytest htt/test_packaging_imports.py -q` | repo root | PASS | `5 passed`; package discovery and temp-CWD imports include `tsc_legacy`. |
| `venv/bin/python -m pytest htt/tsc/adapters/test_preliminary_results.py htt/mio/tests/test_preliminary_results_bridge.py -q` | repo root | PASS | `6 passed`; legacy raw `TSC` pack refs load through canonical normalized manifests. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py tests/contracts/test_claim_language_lint.py tests/contracts/test_artifact_manifest.py -q` | repo root | PASS | `36 passed`; ownership, claim-language, and manifest contracts remain compatible. |
| `venv/bin/python -m pytest htt/mio/tests/test_preliminary_results_bridge.py htt/bass/runtime/test_canonical_decision.py -q` | repo root | PASS | `31 passed`; MIO bridge and BASS canonical decision behavior remain compatible. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` before status update | repo root | PASS | `22/62 = 35.48%`; PR-030 was next topological node. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `23/62 = 37.10%`; dependency-weighted `43.59%`; critical path `6/21 = 28.57%`; no checkpoint due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-030 production files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-030 docs>` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/check_claim_language.py <PR-030 production files> --dry-run` | repo root | PASS | TSC boundary source/doc scan passed. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6982 deselected`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6929/6988 tests collected (59 deselected)`. |
| `venv/bin/python -m py_compile htt/tsc_legacy/__init__.py htt/tsc/__init__.py htt/mio/bridges/preliminary_results.py htt/tsc/adapters/preliminary_results.py tests/tsc/test_tsc_legacy_boundary.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |

Numerical/scientific impact: none. PR-030 is a COMMON/TSC_LEGACY ownership,
deprecation, import-compatibility, and package-boundary PR.

Artifact/claim-tier impact: TSC/Teff is frozen as legacy reproduction and
advisory chart diagnostics only. New TSC-facing artifacts must normalize to
`TSC_LEGACY`/`tsc_legacy`, stay conditional or diagnostic-only, and use
legacy-reproduction bundle authority. PR-030 does not add HTT evidence,
MIO certificates, transfer/native validation, OBSSTAT features, runtime gates,
or family claims.

## PR-010 - Canonical ownership and role firewall

Date: 2026-06-12

Changed files: `htt/src/common/contracts.py`,
`htt/workspace/contracts/validation_registry.py`,
`htt/workspace/contracts/ownership.py`, `tests/contracts/test_ownership_firewall.py`,
canonical TSC assertion updates, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q` before implementation | repo root | FAIL | Red phase: `BundleKind` and ownership firewall API were missing. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q` after reviewer regression tests | repo root | FAIL | Red phase: canonical dataclasses preserved raw `TSC`, and the validation registry still exported active `TSC`/`tsc`. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q` | repo root | PASS | `9 passed`; covers enum membership, string compatibility, canonical TSC_LEGACY normalization, validation-registry vocabulary, role gates, and workspace facade. |
| `venv/bin/python -m pytest htt/src/common/test_contracts.py htt/src/common/test_ver2_contract_layer.py -q` | repo root | PASS | `32 passed`; legacy common contracts remain compatible with canonical TSC_LEGACY storage. |
| `venv/bin/python -m pytest htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py htt/workspace/contracts/tests/test_g19_enforcement.py -q` | repo root | PASS | `8 passed`; workspace schema barrier and G19 separation still hold. |
| `venv/bin/python -m pytest htt/workspace/contracts/tests/test_htt_to_mio_roundtrip.py htt/workspace/contracts/tests/test_mio_certificate.py htt/workspace/contracts/tests/test_htt_forward_output.py htt/workspace/contracts/tests/test_atlas_entry.py -q` | repo root | PASS | `23 passed`; legacy string-manifest dataclasses remain compatible. |
| `venv/bin/python -m pytest htt/tsc/test_ver2_tsc_contracts.py htt/tsc/reports/test_overlay_builder.py htt/tsc/adapters/test_preliminary_results.py -q` | repo root | PASS | `12 passed`; TSC overlays still load and now expose canonical legacy owner. |
| `venv/bin/python -m pytest htt/tsc/adapters/test_bass_runtime.py htt/tsc/adapters/test_htt_inference.py htt/tsc/adapters/test_mio_certificate.py htt/tsc/admissibility/test_domain.py htt/tsc/residuals/test_observable_bridge.py htt/tsc/budget/test_source_to_channel.py htt/tsc/integration/test_active_service.py htt/tsc/source/test_thomson_bridge.py -q` | repo root | PASS | `39 passed`; legacy TSC builder fixtures normalize without breaking advisory outputs. |
| `venv/bin/python -m pytest htt/mio/tests/test_predictive_residuals_shared_schema.py htt/mio/tests/test_mio_certificate_generator.py -q` | repo root | PASS | `19 passed`; MIO bridge/certificate fixtures remain compatible. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py htt/src/common/test_contracts.py htt/src/common/test_ver2_contract_layer.py htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py htt/workspace/contracts/tests/test_g19_enforcement.py htt/workspace/contracts/tests/test_ver2_validation_registry.py htt/workspace/contracts/tests/test_preliminary_results.py htt/mio/tests/test_preliminary_results_bridge.py -q` | repo root | PASS | `74 passed`; combined ownership, validation-registry, preliminary-result bridge suite. |
| `venv/bin/python -m pytest htt/tsc/test_ver2_tsc_contracts.py htt/tsc/reports/test_overlay_builder.py htt/tsc/adapters/test_preliminary_results.py htt/tsc/adapters/test_bass_runtime.py htt/tsc/adapters/test_htt_inference.py htt/tsc/adapters/test_mio_certificate.py htt/tsc/admissibility/test_domain.py htt/tsc/residuals/test_observable_bridge.py htt/tsc/budget/test_source_to_channel.py htt/tsc/integration/test_active_service.py htt/tsc/source/test_thomson_bridge.py htt/mio/tests/test_predictive_residuals_shared_schema.py htt/mio/tests/test_mio_certificate_generator.py -q` | repo root | PASS | `70 passed`; combined TSC/MIO compatibility slice. |
| `venv/bin/python -m py_compile htt/src/common/contracts.py htt/workspace/contracts/validation_registry.py htt/workspace/contracts/ownership.py` | repo root | PASS | Touched Python modules compile. |
| Inline `venv/bin/python` StrEnum/asdict/json smoke | repo root | PASS | `ArtifactManifest(owner="TSC", implementation_scope="tsc")` stores canonical enum fields and JSON-serializes to strings. |
| `git diff --check -- <PR-010 files>` | repo root | PASS | No whitespace errors in scoped PR-010 diff. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | `8/62 = 12.90%`; dependency-weighted `14.87%`; critical-path `4/21 = 19.05%`; checkpoint not due; next candidates `PR-021`, `PR-011`, `PR-013`, `PR-014`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-010 docs> && python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-010 docs>` | repo root | PASS | No forbidden claim patterns or unmarked strong claims detected. |

Numerical/scientific impact: none; schema and role-firewall code only.

Artifact/claim-tier impact: COMMON L2 contract metadata. The new ownership
firewall separates HTT posterior bundles from MIO diagnostic certificates and
keeps TSC as legacy reproduction scope. It does not validate native solver
behavior, transfer calibration, HTT posterior/evidence content, MIO diagnostic
adequacy, null/mask/covariance adequacy, morphology compatibility, or
family-identification evidence.

## PR-021 - Optional dependency registry and skip-audit report

Date: 2026-06-12

Changed files: `htt/src/common/optional_dependencies.py`, `htt/conftest.py`,
`scripts/codex_harness/optional_dep_report.py`,
`docs/generated/optional_dependency_status.md`,
`tests/contracts/test_optional_dependencies.py`, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_optional_dependencies.py -q` before implementation | repo root | FAIL | Red phase: missing `common.optional_dependencies` and missing `optional_dep_report.py`. |
| `python scripts/codex_harness/optional_dep_report.py --dry-run` before implementation | repo root | FAIL | Red phase: report script absent. |
| `venv/bin/python -m pytest tests/contracts/test_optional_dependencies.py -q` | repo root | PASS | `5 passed`; registry, injected missing/present statuses, conftest registry use, report metadata, and dry-run. |
| `python scripts/codex_harness/optional_dep_report.py --dry-run` | repo root | PASS | Prints default report path and report body using `/usr/bin/python`; `dynesty` is reported missing in that interpreter. |
| `python scripts/codex_harness/optional_dep_report.py` | repo root | PASS | Wrote `docs/generated/optional_dependency_status.md`; no diff after immediate regeneration. |
| `venv/bin/python -m py_compile htt/src/common/optional_dependencies.py scripts/codex_harness/optional_dep_report.py htt/conftest.py` | repo root | PASS | Touched Python modules compile. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `8 passed`; marker taxonomy and named skip reasons preserved. |
| `venv/bin/python -m pytest --collect-only -q tests/contracts scripts/codex_harness/test_pytest_taxonomy.py` | repo root | PASS | `30 tests collected`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6799/6858 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest -m "requires_healpy or requires_dynesty" --collect-only -q` | repo root | PASS | `23/6858 tests collected`; optional marker collection remains attributable. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6852 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; runner child exit code preserved. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect --dry-run` | repo root | PASS | Prints venv-backed collect command. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke --dry-run` | repo root | PASS | Prints venv-backed smoke command. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-021 docs> && python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-021 docs>` | repo root | PASS | No forbidden claim patterns or unmarked strong claims detected. |
| `git diff --check -- <PR-021 files>` | repo root | PASS | No whitespace errors in scoped PR-021 diff. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | `9/62 = 14.52%`; dependency-weighted `15.90%`; critical-path `4/21 = 19.05%`; checkpoint not due; next candidates `PR-011`, `PR-013`, `PR-014`, `PR-040`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |

Numerical/scientific impact: none; optional dependency registry/reporting
harness only.

Artifact/claim-tier impact: COMMON L1 diagnostic-only generated report. The
report records local availability for `healpy`, `dynesty`, `astropy`, and
`camb`; dependency presence is not solver, transfer, posterior, MIO, null,
sky-support, morphology, or family-identification evidence.

## PR-011 - Artifact manifest validation and figure quarantine

Date: 2026-06-12

Changed files: `htt/src/common/artifact_manifest.py`,
`scripts/check_artifact_manifests.py`,
`tests/contracts/test_artifact_manifest.py`,
`docs/generated/quarantined_figures.md`,
`docs/generated/progress_checkpoints/checkpoint_010.md`, status and handoff
docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py -q` before implementation | repo root | FAIL | Red phase: missing `common.artifact_manifest`. |
| `venv/bin/python scripts/check_artifact_manifests.py --dry-run` before implementation | repo root | FAIL | Red phase: checker script absent. |
| `venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py -q` after first implementation | repo root | FAIL | Expected extra canonical dataclass issue after missing `input_hashes`; test updated to require both field-level and canonical diagnostics. |
| `venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py -q` after reviewer fixes | repo root | PASS | `11 passed`; covers required metadata, native-transfer gate, sidecar path match, dry-run, write, and invalid sidecar JSON exit. |
| `python scripts/check_artifact_manifests.py --dry-run` | repo root | PASS | Exit 0; dry-run reports 96 quarantined assets, 0 manifested figures, 0 manifest issues, and writes nothing. |
| `venv/bin/python scripts/check_artifact_manifests.py` | repo root | PASS | Wrote `docs/generated/quarantined_figures.md`; report records 96 quarantined assets and no manifest issues. |
| `venv/bin/python -m py_compile htt/src/common/artifact_manifest.py scripts/check_artifact_manifests.py` | repo root | PASS | Touched Python modules compile. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py htt/src/common/test_contracts.py htt/src/common/test_ver2_contract_layer.py -q` | repo root | PASS | `41 passed`; common ownership and manifest compatibility preserved. |
| `venv/bin/python -m pytest scripts/test_ver2_artifact_export.py::test_scan_figures_blocks_missing_manifest_and_accepts_generated_override scripts/test_ver2_artifact_export.py::test_caption_claim_violation_blocks_stronger_terms -q` | repo root | PASS | `2 passed`; older VER2 figure-scanner behavior still intact. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6863 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6810/6869 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints` | repo root | PASS | `10/62 = 16.13%`; dependency-weighted `19.49%`; critical path `4/21 = 19.05%`; generated `checkpoint_010.md`; no replan required. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-011 files> && python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-011 files>` | repo root | PASS | No forbidden claim patterns or unmarked strong claims detected. |
| `git diff --check -- <PR-011 files>` | repo root | PASS | No whitespace errors in scoped PR-011 diff. |

Numerical/scientific impact: none; manifest validation and generated
quarantine inventory only.

Artifact/claim-tier impact: COMMON L2 contract/checker metadata and one
COMMON diagnostic-only generated report. `docs/generated/quarantined_figures.md`
records current disk state: 96 existing figure/PDF assets are quarantined for
missing manifests, 0 are manifest-ready through this checker, and 0 sidecar
manifest issues were found. This is not solver, transfer, posterior, MIO,
null/mock/covariance, sky-support, morphology, or family-ID evidence.

## PR-013 - MIO/HTT posterior-certificate type firewall

Date: 2026-06-12

Changed files: `htt/workspace/contracts/htt_posterior.py`,
`htt/workspace/contracts/mio_certificate.py`,
`htt/workspace/contracts/__init__.py`,
`tests/contracts/test_mio_htt_no_merge.py`, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_mio_htt_no_merge.py -q` before implementation | repo root | FAIL | Red phase: missing `workspace.contracts.htt_posterior`. |
| `venv/bin/python -m pytest tests/contracts/test_mio_htt_no_merge.py -q` | repo root | PASS | `14 passed`; covers direct certificate, owner, metadata, dict payload, manifest-owner, valid bundle, nested certificate, and real-root static scan checks. |
| `venv/bin/python -m py_compile htt/workspace/contracts/htt_posterior.py htt/workspace/contracts/mio_certificate.py htt/workspace/contracts/__init__.py tests/contracts/test_mio_htt_no_merge.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py htt/workspace/contracts/tests/test_mio_certificate.py htt/workspace/contracts/tests/test_htt_to_mio_roundtrip.py htt/workspace/contracts/tests/test_g19_enforcement.py htt/mio/tests/test_htt_cross_check.py -q` | repo root | PASS | `41 passed`; existing ownership, MIO, HTT-to-MIO, G19, and cross-check contracts preserved. |
| `venv/bin/python -m pytest htt/htt/tests/test_ver2_likelihood_scope_guard.py htt/htt/tests/test_ver2_directional_shell.py -q` | repo root | PASS | `21 passed`; HTT likelihood-scope and directional shell guards preserved. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-013 complete: `11/62 = 17.74%`; dependency-weighted `21.54%`; critical path `4/21 = 19.05%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; packaging import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6877 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6824/6883 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest tests/contracts -q` | repo root | PASS | `47 passed`; top-level contract suite remains green. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-013 files>` | repo root | PASS | No forbidden claim patterns detected after scanner-safe test/doc wording. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-013 docs>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --cached --check` | repo root | PASS | Staged PR-013 diff has no whitespace errors. |

Numerical/scientific impact: none; type-contract and guard logic only.

Artifact/claim-tier impact: COMMON/HTT L2 contract metadata. PR-013 makes the
MIO/HTT separation executable for the new posterior bundle path and preserves
existing cross-check-only exports. It does not add solver outputs, transfer
calibration, null/mock/covariance evidence, sky-support evidence, morphology
compatibility evidence, or family-ID evidence.

## PR-014 - Transfer-provenance contract

Date: 2026-06-12

Changed files: `htt/src/common/transfer_registry.py`,
`htt/workspace/contracts/transfer.py`, `htt/workspace/contracts/__init__.py`,
`htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py`,
`tests/contracts/test_transfer_registry.py`, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_transfer_registry.py -q` before implementation | repo root | FAIL | Red phase: missing `common.transfer_registry`. |
| `venv/bin/python -m pytest tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `11 passed`; covers metadata, invalid domains, external/native kill switches, registry coexistence, duplicate IDs, raw result metadata, caveat shape, and workspace aliasing. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py tests/contracts/test_artifact_manifest.py htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py htt/src/common/test_ver2_contract_layer.py -q` | repo root | PASS | `32 passed`; ownership, manifest/native-transfer gates, workspace schema barrier, and common contract layer preserved. |
| `venv/bin/python -m py_compile htt/src/common/transfer_registry.py htt/workspace/contracts/transfer.py htt/workspace/contracts/__init__.py tests/contracts/test_transfer_registry.py htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py` | repo root | PASS | Touched Python files compile. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-014 complete: `12/62 = 19.35%`; dependency-weighted `24.62%`; critical path `5/21 = 23.81%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6888 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6835/6894 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest tests/contracts -q` | repo root | PASS | `58 passed`; top-level contract suite remains green. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-014 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-014 docs>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --cached --check` | repo root | PASS | Staged PR-014 diff has no whitespace errors. |

Numerical/scientific impact: none; metadata/contract plumbing only.

Artifact/claim-tier impact: COMMON L2 transfer-provenance contract metadata.
PR-014 records transfer source, family, valid range, observable kind,
normalization, calibration status, caveats, and validation gates for later
result consumers. It does not add solver outputs, native transfer validation,
AniCLASS-native calibration, HTT posterior/evidence validation, MIO diagnostic
certification, null/mock/covariance evidence, sky-support evidence, morphology
compatibility evidence, or family-ID evidence.

## PR-040 - Sky-support and coordinate-frame contracts

Date: 2026-06-12

Changed files: `htt/src/common/sky_support.py`,
`htt/src/common/sky_geometry.py`, `htt/src/common/contracts.py`,
`htt/src/common/artifact_manifest.py`,
`tests/htt/test_sky_support_contract.py`,
`tests/contracts/test_artifact_manifest.py`, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py -q` before implementation | repo root | FAIL | Red phase: missing `assert_no_raw_lonlat_mean_source` and `common.sky_support`. |
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py -q` | repo root | PASS | `6 passed`; covers deterministic frame-bound mask hashes, equal-area sky fraction, support metadata, sky-facing metadata validation, unit-vector mean tagging, and raw lon/lat mean guard. |
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py tests/contracts/test_artifact_manifest.py -q` | repo root | PASS | `19 passed`; PR-040 sky support and tightened manifest validation pass together. |
| `venv/bin/python -m pytest -q tests/contracts/test_artifact_manifest.py htt/src/common/test_sky_geometry.py htt/src/common/test_contracts.py htt/mio/tests/test_masked_sky_caveats.py htt/mio/tests/test_ver2_manifest_status.py htt/htt/tests/test_ver2_directional_shell.py` | repo root | PASS | `89 passed`; adjacent manifest, common, MIO masked-sky, MIO status, and HTT directional shell behavior preserved. |
| `venv/bin/python -m pytest htt/src/common -q` | repo root | PASS | `164 passed, 1 skipped`; full common package tests remain green. |
| `venv/bin/python -m pytest tests/contracts -q` | repo root | PASS | `60 passed`; top-level contract suite remains green. |
| `venv/bin/python -m py_compile htt/src/common/sky_support.py htt/src/common/sky_geometry.py htt/src/common/contracts.py htt/src/common/artifact_manifest.py tests/htt/test_sky_support_contract.py tests/contracts/test_artifact_manifest.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6896 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6843/6902 tests collected (59 deselected)`. |
| `venv/bin/python scripts/check_artifact_manifests.py --dry-run` | repo root | PASS | Exit 0; still reports 96 quarantined figures, 0 manifested figures, 0 manifest issues. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-040 complete: `13/62 = 20.97%`; dependency-weighted `27.69%`; critical path `5/21 = 23.81%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-040 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-040 docs>` before wording fix | repo root | FAIL | Flagged one full family-ID phrase without nearby status marker. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-040 docs>` after wording fix | repo root | PASS | No unmarked strong claims detected. |
| `git diff --check -- <PR-040 files>` | repo root | PASS | Scoped PR-040 diff has no whitespace errors. |
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py tests/contracts/test_artifact_manifest.py -q` after reviewer fixes | repo root | PASS | `19 passed`; verifies bounded sky-facing status vocabulary and manifest compatibility. |
| `venv/bin/python -m pytest htt/src/common -q` after reviewer fixes | repo root | PASS | `164 passed, 1 skipped`; full common package tests remain green. |
| `venv/bin/python -m pytest tests/contracts -q` after reviewer fixes | repo root | PASS | `60 passed`; top-level contract suite remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` after reviewer fixes | repo root | PASS | `6 passed, 6896 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` after reviewer fixes | repo root | PASS | `6843/6902 tests collected (59 deselected)`. |

Numerical/scientific impact: none; COMMON metadata and geometry guards only.

Artifact/claim-tier impact: COMMON L2 contract/checker metadata. PR-040
requires coordinate frame, deterministic mask hash, sky fraction, and
completeness status for sky-facing metadata validation and records
unit-vector spherical means. It does not add solver outputs, transfer
calibration, null/mock/covariance evidence, HTT posterior/evidence, MIO
diagnostic certification, morphology compatibility, or family-ID evidence.

## PR-012 - Status snapshot and generated claim ledger pipeline

Date: 2026-06-12

Changed files: `htt/src/common/status_snapshot.py`,
`tests/contracts/test_status_snapshot.py`,
`docs/generated/status_snapshot.json`,
`docs/generated/claim_ledger.json`, `docs/generated/status_matrix.md`,
`docs/status_matrix.md`, `docs/claim_ledger.md`, status and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_status_snapshot.py -q` before implementation | repo root | FAIL | Red phase: missing `build_status_bundle` and related public API. |
| `venv/bin/python -m pytest tests/contracts/test_status_snapshot.py -q` | repo root | PASS | `4 passed`; covers generated DAG status bundle, companion writes, canonical owner normalization, Markdown count drift, and CLI writes. |
| `venv/bin/python -m pytest tests/contracts/test_status_snapshot.py tests/contracts/test_ownership_firewall.py tests/contracts/test_artifact_manifest.py -q` | repo root | PASS | `26 passed`; adjacent ownership and manifest contracts preserved. |
| `venv/bin/python -m py_compile htt/src/common/status_snapshot.py htt/src/common/claim_ledger.py tests/contracts/test_status_snapshot.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Wrote `status_snapshot.json`, `claim_ledger.json`, and `status_matrix.md`. |
| `python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | FAIL | `/usr/bin/python` cannot import the src-layout package in this checkout: `No module named common`. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Exact module CLI path works when the source-layout package path is supplied. |
| Generated sidecar inspection via `json.load` and `rg` | repo root | PASS | 62 rows, 14 completed after PR-012 status update, no raw `TSC` owner/scope rows, and no `production_validated=True` rows. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | `14/62 = 22.58%`; dependency-weighted `28.72%`; critical path `5/21 = 23.81%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6900 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6847/6906 tests collected (59 deselected)`. |

Numerical/scientific impact: none; COMMON generated status tooling only.

Artifact/claim-tier impact: COMMON L2 diagnostic bookkeeping. PR-012 makes
`docs/generated/status_snapshot.json` the canonical public DAG status surface
and generates a companion claim ledger and Markdown matrix from the same
inputs. It does not add solver outputs, transfer calibration,
HTT posterior/evidence validation, MIO diagnostic certification,
null/mock/covariance adequacy, sky-support adequacy, morphology
compatibility, or family-ID evidence.

## PR-022 - PR delta template and review artifact generator

Date: 2026-06-12

Changed files: `scripts/codex_harness/new_pr_delta.py`,
`docs/PR_DELTAS/TEMPLATE.md`, `tests/contracts/test_pr_delta_template.py`,
`docs/PR_DELTAS/pr-022.md`, status files, PR-012 generated status sidecars,
and `docs/generated/progress_checkpoints/checkpoint_015.md`.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_pr_delta_template.py -q` before implementation | repo root | FAIL | Red phase: missing `TEMPLATE.md`, missing public API, and missing CLI flags. |
| `venv/bin/python -m pytest tests/contracts/test_pr_delta_template.py -q` | repo root | PASS | `8 passed`; covers template, PR-card rendering, owner normalization, dry-run, invalid web status, overwrite guard, and unknown PR rejection. |
| `python scripts/codex_harness/new_pr_delta.py PR-000 --dry-run` | repo root | PASS | Exact PR-card command; prints lowercase target and rendered Markdown without writing. |
| `python -m pytest tests/contracts/test_pr_delta_template.py -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; host interpreter lacks pytest. |
| `venv/bin/python -m pytest tests/contracts/test_pr_delta_template.py tests/contracts/test_harness_runner.py scripts/codex_harness/test_pr_dag_harness.py -q` | repo root | PASS | `27 passed`; adjacent harness/DAG tests remain green. |
| `venv/bin/python -m py_compile scripts/codex_harness/new_pr_delta.py tests/contracts/test_pr_delta_template.py` | repo root | PASS | Touched Python files compile. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints` | repo root | PASS | Generated `checkpoint_015.md`; `15/62 = 24.19%`; dependency-weighted `29.74%`; critical path `5/21 = 23.81%`; no replan needed. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status sidecars at 15 completed PRs. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6908 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6855/6914 tests collected (59 deselected)`. |

Numerical/scientific impact: none; COMMON review-artifact harness only.

Artifact/claim-tier impact: COMMON L1 diagnostic review metadata. PR-022
standardizes PR_DELTA scaffolding and safe claim-status defaults. It does not
add solver outputs, transfer calibration, HTT posterior/evidence validation,
MIO diagnostic certificate evidence, null/mock/covariance adequacy, sky-support
adequacy, morphology compatibility, or family-ID evidence.

## PR-070 - Create obsstat package and ObservableVector contract

Date: 2026-06-12

Changed files: `htt/obsstat/__init__.py`,
`htt/obsstat/observable_vector.py`, `htt/htt/__init__.py`,
`htt/pyproject.toml`, `htt/test_packaging_imports.py`,
`tests/obsstat/test_observable_vector.py`, `docs/PR_DELTAS/pr-070.md`, status
files, PR-012 generated status sidecars, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/obsstat/test_observable_vector.py -q` before implementation | repo root | FAIL | Red phase: `htt.obsstat` package and builder did not exist. |
| `venv/bin/python -m pytest tests/obsstat/test_observable_vector.py -q` during review | repo root | FAIL | `identified_family` and `family_rank` were not rejected by the first implementation. |
| `venv/bin/python -m pytest tests/obsstat/test_observable_vector.py -q` after package/gate fixes | repo root | PASS | `9 passed`; covers facade identity, manifest helper, feature block packaging, recursive p-value provenance, forbidden inference/family keys and values, all-block transfer metadata, manifest ownership, static imports, and import side effects. |
| `venv/bin/python -m pip install -e './htt[dev]'` | repo root | PASS | Refreshed editable metadata after adding `obsstat*` package discovery. |
| temp-CWD import probe for `htt.obsstat` with `PYTHONPATH` removed | repo root | PASS | Prints `temp-cwd htt.obsstat import ok`; fixes the package-smoke blocker. |
| `venv/bin/python -m pytest htt/test_packaging_imports.py -q` | repo root | PASS | `5 passed`; package smoke now covers temp-CWD `htt.obsstat` and `htt.obsstat.observable_vector`. |
| `venv/bin/python -m pytest tests/obsstat/test_observable_vector.py htt/test_packaging_imports.py -q` | repo root | PASS | `14 passed`; combines focused obsstat contract and packaging regression coverage. |
| `venv/bin/python -m py_compile htt/obsstat/__init__.py htt/obsstat/observable_vector.py htt/htt/__init__.py htt/test_packaging_imports.py tests/obsstat/test_observable_vector.py` | repo root | PASS | Touched Python files compile. |
| static `rg` import firewall scan over `htt/obsstat` | repo root | PASS | No HTT likelihood/evidence, MIO certificate, or MIO package imports found. |
| `venv/bin/python -m pytest tests/obsstat/test_observable_vector.py tests/contracts/test_ownership_firewall.py tests/contracts/test_mio_htt_no_merge.py htt/test_packaging_imports.py htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py htt/src/common/test_contracts.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `74 passed`; adjacent ownership, MIO/HTT separation, schema barrier, transfer registry, and package checks remain green. |
| `python -m pytest tests/obsstat/test_observable_vector.py -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; host interpreter lacks pytest. |
| `venv/bin/python - <<'PY' ... import htt.obsstat ... PY` | repo root | PASS | Import smoke prints `obsstat import ok ObservableVector True True`. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status sidecars at 16 completed PRs. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` | repo root | PASS | `16/62 = 25.81%`; dependency-weighted `31.79%`; critical path `5/21 = 23.81%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml && echo 'status mirrors match'` | repo root | PASS | Status mirrors match. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6917 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6864/6923 tests collected (59 deselected)`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-070 files>` | repo root | PASS | No forbidden claim patterns detected after removing an internal guard-list literal that matched the scanner. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-070 files>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --check -- <PR-070 files>` | repo root | PASS | Scoped diff has no whitespace errors. |

Numerical/scientific impact: OBSSTAT diagnostic feature packaging only. PR-070
does not compute transfer functions, run a native solver, produce posterior
evidence, or certify MIO diagnostics.

Artifact/claim-tier impact: OBSSTAT L2 diagnostic-only observable contract.
The new facade requires OBSSTAT manifests and canonical sky support, rejects
HTT/MIO/family-identification semantics, requires null provenance for p-value
features, and requires COMMON transfer provenance metadata for
transfer-derived blocks. It does not provide native solver validation,
transfer validation, morphology compatibility, or family-ID evidence.

## PR-015 - Claim-language and banned-vocabulary linter

Date: 2026-06-12

Changed files: `htt/src/common/semantic_guards/__init__.py`,
`htt/src/common/semantic_guards/no_overclaim.py`,
`scripts/check_claim_language.py`,
`tests/contracts/test_claim_language_lint.py`, `docs/PR_DELTAS/pr-015.md`,
status files, PR-012 generated status sidecars, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/contracts/test_claim_language_lint.py -q` before implementation | repo root | FAIL | Red phase: `common.semantic_guards` did not exist. |
| `venv/bin/python -m pytest tests/contracts/test_claim_language_lint.py -q` during review | repo root | FAIL | Initial rule set missed hostile direction-coherence, Teff full E/B, AniCLASS/native, and JSON MIO/HTT evidence-merging cases. |
| `venv/bin/python -m pytest tests/contracts/test_claim_language_lint.py -q` | repo root | PASS | `14 passed`; module and CLI tests cover hard-fail findings, archive handling, JSON output, missing roots, and no-write dry-run behavior. |
| `python scripts/check_claim_language.py docs manuscripts --dry-run` | repo root | PASS | Exact PR-card command; absent `manuscripts` root is reported to stderr and skipped because `docs` exists. |
| `python scripts/check_claim_language.py docs docs/manuscript --dry-run` | repo root | PASS | Real manuscript tree plus docs scan found no forbidden claim language. |
| `venv/bin/python -m py_compile htt/src/common/semantic_guards/__init__.py htt/src/common/semantic_guards/no_overclaim.py scripts/check_claim_language.py tests/contracts/test_claim_language_lint.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m pytest tests/contracts/test_claim_language_lint.py tests/contracts/test_ownership_firewall.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_transfer_registry.py tests/obsstat/test_observable_vector.py htt/tsc/audit/test_no_overclaim.py -q` | repo root | PASS | `61 passed`; adjacent claim, ownership, transfer, obsstat, and TSC audit tests remain green. |
| `venv/bin/python -m pytest htt/src/common -q` | repo root | PASS | `164 passed, 1 skipped`; COMMON package tests remain green. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6931 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6878/6937 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`; topological next after PR-015 is PR-050. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` | repo root | PASS | `17/62 = 27.42%`; dependency-weighted `33.33%`; critical path `5/21 = 23.81%`; checkpoint not due until 20. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status sidecars at 17 completed PRs. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml && echo 'status mirrors match'` | repo root | PASS | Status mirrors match. |
| `python -m pytest tests/contracts/test_claim_language_lint.py -q` | repo root | FAIL | Host interpreter lacks pytest: `/usr/bin/python: No module named pytest`; venv pytest is the authoritative run. |
| static `rg` import firewall scan over `htt/src/common/semantic_guards` | repo root | PASS | No imports from HTT, MIO, BASS, TSC, or OBSSTAT packages. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-015 docs>` | repo root | PASS | No forbidden claim patterns detected after rewording guardrail summaries away from exact unsafe examples. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-015 docs>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --check -- <PR-015 files>` | repo root | PASS | Scoped diff has no whitespace errors. |

Numerical/scientific impact: none. PR-015 is a COMMON semantic guard and CLI
for active text/artifact claim hygiene.

Artifact/claim-tier impact: COMMON L2 diagnostic-only lint infrastructure. It
hard-fails forbidden production wording for pre-native scalar/family overclaims,
TSC/Teff full-solver or full-polarisation overclaims, MIO diagnostic promotion
into posterior/evidence language, and external-transfer/native conflation. It
does not provide solver validation, transfer validation, posterior evidence,
MIO diagnostic certificate evidence, morphology compatibility, or family-ID
evidence.

## PR-050 - DepartureBundle and comparator/frame metadata

Date: 2026-06-12

Changed files: `htt/mio/formalism/__init__.py`,
`htt/mio/formalism/component_breakdown.py`,
`htt/mio/formalism/departure_bundle.py`, `htt/mio/__init__.py`,
`htt/mio/tests/test_boot.py`, `tests/mio/test_departure_bundle.py`,
`docs/PR_DELTAS/pr-050.md`, status files, PR-012 generated status sidecars,
and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/mio/test_departure_bundle.py -q` before implementation | repo root | FAIL | Red phase: `mio.formalism` package did not exist. |
| `venv/bin/python -m pytest tests/mio/test_departure_bundle.py -q` before input-hash fix | repo root | FAIL | Empty `input_hashes` did not raise. |
| `venv/bin/python -m pytest tests/mio/test_departure_bundle.py -q` | repo root | PASS | `11 passed`; covers signed projection, metadata, component validation, cancellation, transfer provenance, package exports, and diagnostic-only boundary. |
| `venv/bin/python -m pytest tests/mio/test_departure_bundle.py htt/mio/tests/test_boot.py -q` | repo root | PASS | `14 passed`; MIO boot imports `mio.formalism`. |
| `venv/bin/python -m py_compile htt/mio/__init__.py htt/mio/tests/test_boot.py htt/mio/formalism/__init__.py htt/mio/formalism/component_breakdown.py htt/mio/formalism/departure_bundle.py tests/mio/test_departure_bundle.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m pytest tests/mio/test_departure_bundle.py htt/mio/tests/test_boot.py htt/mio/tests/test_tension.py tests/contracts/test_transfer_registry.py tests/contracts/test_claim_language_lint.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_ownership_firewall.py htt/bass/observational/test_ver2_mes_departure.py -q` | repo root | PASS | `74 passed`; adjacent MIO, transfer, claim, ownership, and BASS departure tests remain green. |
| import smoke for `mio.formalism`, COMMON transfer/contracts, and workspace MIO/HTT contracts | repo root | PASS | All requested modules imported. |
| `python scripts/check_claim_language.py <PR-050 files> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-050 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-050 files>` | repo root | PASS | No unmarked strong claims detected. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6942 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6889/6948 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` | repo root | PASS | After status update: `18/62 = 29.03%`; dependency-weighted `35.38%`; critical path `6/21 = 28.57%`; checkpoint not due until 20. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status sidecars at 18 completed PRs. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml && echo 'status mirrors match'` | repo root | PASS | Status mirrors match. |
| `python -m pytest tests/mio/test_departure_bundle.py -q` | repo root | FAIL | Host interpreter lacks pytest: `/usr/bin/python: No module named pytest`; venv pytest is the authoritative run. |

Numerical/scientific impact: MIO algebraic metadata only. PR-050 implements
the signed comparator projection `x_C = Sigma2_std - W2_std + Omega_tilt +
Omega_k_aniso`, preserves negative values, exposes cancellation diagnostics,
and requires comparator/frame/units/config/input metadata.

Artifact/claim-tier impact: MIO L2 diagnostic-only formalism contract. It
validates PR-014 transfer metadata for transfer-derived bundles and rejects
external-transfer/native conflation through the COMMON transfer guard. It does
not provide native solver validation, transfer validation, HTT inference
evidence, MIO certificate evidence, morphology compatibility, or geometry/family
claims.

## PR-041 - ZoA ladder and selection-aware support modes

Date: 2026-06-12

Changed files: `htt/src/common/healpix_selection.py`,
`htt/htt/htt/zoa/__init__.py`, `htt/htt/htt/zoa/selection_ladder.py`,
`htt/htt/htt/__init__.py`, `htt/htt/__init__.py`,
`tests/htt/test_zoa_selection_ladder.py`, `docs/PR_DELTAS/pr-041.md`,
status files, PR-012 generated status sidecars, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/htt/test_zoa_selection_ladder.py -q` before implementation | repo root | FAIL | Red phase: target test file was missing. |
| `venv/bin/python -m pytest tests/htt/test_zoa_selection_ladder.py -q` | repo root | PASS | `6 passed`; covers support-mode separation, metadata, no production-axis promotion, production fallback rejection, diagnostic fallback marking, and mock-calibration strictness. |
| `venv/bin/python -m py_compile htt/src/common/healpix_selection.py htt/htt/htt/zoa/__init__.py htt/htt/htt/zoa/selection_ladder.py htt/htt/htt/__init__.py htt/htt/__init__.py tests/htt/test_zoa_selection_ladder.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m pytest tests/htt/test_zoa_selection_ladder.py tests/htt/test_sky_support_contract.py htt/src/common/test_healpix_selection.py htt/htt/tests/test_ver2_axis_gate.py -q` | repo root | PASS | `39 passed`; adjacent sky-support, selection, and axis-gate contracts remain green. |
| `venv/bin/python -m pytest htt/src/common/test_bulkflow_estimator.py htt/htt/tests/test_fig_zoa_ladder_mode0_data.py -q` | repo root | PASS | `23 passed`; older diagnostic bulk-flow ZoA ladder artifacts remain green. |
| `venv/bin/python -m pytest htt/htt/tests tests/htt -q` | repo root | PASS | `379 passed, 5 warnings`; warnings are existing dynesty weight-renormalization warnings in figure smoke tests. |
| import smoke for `common.healpix_selection`, `htt.zoa.selection_ladder`, and wrapper `htt.zoa` | repo root | PASS | New helper and HTT package alias import correctly. |
| `python scripts/check_claim_language.py <PR-041 files> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python scripts/check_claim_language.py docs docs/manuscript --dry-run` | repo root | PASS | Active docs/manuscript scan found no forbidden claim language. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-041 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-041 files>` | repo root | PASS | No unmarked strong claims detected. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6948 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6895/6954 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After status update: `19/62 = 30.65%`; dependency-weighted `36.92%`; critical path `6/21 = 28.57%`; checkpoint not due until 20. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status sidecars at 19 completed PRs. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml && echo 'status mirrors match'` | repo root | PASS | Status mirrors match. |
| final `venv/bin/python -m pytest tests/htt/test_zoa_selection_ladder.py -q` | repo root | PASS | `6 passed`; rerun after handoff doc updates. |
| `python -m pytest tests/htt/test_zoa_selection_ladder.py -q` | repo root | FAIL | Host interpreter lacks pytest: `/usr/bin/python: No module named pytest`; venv pytest is the authoritative run. |

Numerical/scientific impact: HTT support-mode metadata only. PR-041 separates
raw, ZoA-masked, angular-completeness, and mock-calibrated sky support
summaries and records deterministic sky-support metadata, config/input hashes,
and caveats. It does not compute cosmological transfer functions or produce
posterior evidence.

Artifact/claim-tier impact: HTT L2 diagnostic-only selection support ladder.
Uniform fallback is forbidden in production-mode strictness and marked
diagnostic-only when explicitly allowed outside production. The ladder does not
provide native solver validation, transfer validation, HTT posterior evidence,
MIO certificate evidence, morphology compatibility, or geometry/family claims.

## PR-023 - Progress scoreboard and stagnation-triggered replanning

Date: 2026-06-12

Changed files: `scripts/codex_harness/progress_report.py`,
`scripts/codex_harness/test_pr_dag_harness.py`,
`docs/codex_handoff/checkpoint_protocol.md`, `docs/checkpoint_protocol.md`,
`docs/generated/progress_checkpoints/checkpoint_020.md`,
`docs/generated/progress_checkpoints/progress_scoreboard.md`,
`docs/PR_DELTAS/pr-023.md`, status files, PR-012 generated status sidecars,
and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` before implementation | repo root | FAIL | Red phase: skipped overlap was accepted, skipped fields were absent, and `--write-scoreboard` was unknown. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` | repo root | PASS | `15 passed`; covers skipped overlap rejection, skipped exclusion from completion/unblocked-next, checkpoint-due JSON honesty, checkpoint behavior, malformed checkpoint metadata, and scoreboard output. |
| `venv/bin/python -m py_compile scripts/codex_harness/progress_report.py scripts/codex_harness/test_pr_dag_harness.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py tests/contracts/test_harness_runner.py tests/contracts/test_status_snapshot.py -q` | repo root | PASS | `27 passed`; adjacent harness/status tests remain green. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` | repo root | PASS | Exact PR-card command before status update: `19/62 = 30.65%`, skipped `[]`, next checkpoint 20. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard /tmp/htt_pr023_scoreboard.md` | repo root | PASS | Wrote deterministic current scoreboard before status update; listed skipped `none` and checkpoint due `no`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After status update without checkpoint dir: reports `checkpoint_due=true` and explicitly says to rerun with `--write-checkpoint-dir` to evaluate replan state. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | After status update: `20/62 = 32.26%`; dependency-weighted `37.44%`; critical path `6/21 = 28.57%`; wrote `checkpoint_020.md`; replan not required because progress advanced by 5 since checkpoint 015. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status sidecars at 20 completed PRs. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml && echo 'status mirrors match'` | repo root | PASS | Status mirrors match. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6952 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6899/6958 tests collected (59 deselected)`. |
| `python scripts/check_claim_language.py <PR-023 files> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python scripts/check_claim_language.py docs docs/manuscript --dry-run` | repo root | PASS | Active docs/manuscript scan found no forbidden claim language. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-023 docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-023 docs>` | repo root | PASS | No unmarked strong claims detected. |

Numerical/scientific impact: none. PR-023 is COMMON L1 harness bookkeeping.

Artifact/claim-tier impact: generated checkpoint and scoreboard metrics are
DAG bookkeeping only. They do not validate native solver behavior, transfer
calibration, HTT posterior/evidence, MIO diagnostics, null calibration,
morphology compatibility, or family-ID evidence.

## PR-113 - Manuscript figure inventory and quarantine audit

Date: 2026-06-12

Changed files: `scripts/audit_manuscript_figures.py`,
`tests/contracts/test_manuscript_figure_audit.py`,
`docs/generated/manuscript_figure_inventory.md`,
`docs/generated/missing_figure_references.md`, `docs/PR_DELTAS/pr-113.md`,
status files, PR-012 generated status sidecars, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `python scripts/audit_manuscript_figures.py --dry-run` before implementation | repo root | FAIL | Red phase from read-only regression tester: script absent. |
| `python scripts/audit_manuscript_figures.py` | repo root | PASS | Wrote both PR-113 generated reports; summary `includegraphics=94 resolved=0 quarantined=72 missing=22 text_findings=23`. |
| `python scripts/audit_manuscript_figures.py --dry-run` | repo root | PASS | Exact PR-card command; same counts, no writes. |
| `venv/bin/python -m pytest tests/contracts/test_manuscript_figure_audit.py -q` | repo root | PASS | `4 passed`; covers resolved/quarantined/missing classification, metadata, no-write dry-run, and report writes. |
| `venv/bin/python -m pytest tests/contracts/test_artifact_manifest.py tests/contracts/test_status_snapshot.py tests/contracts/test_claim_language_lint.py tests/contracts/test_manuscript_figure_audit.py -q` | repo root | PASS | `35 passed`; adjacent artifact, status, claim, and manuscript audit contracts remain green. |
| `venv/bin/python -m py_compile scripts/audit_manuscript_figures.py tests/contracts/test_manuscript_figure_audit.py` | repo root | PASS | Touched Python files compile. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json` before status update | repo root | PASS | `23/62 = 37.10%`; PR-113 was topological next. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 24 completed PRs. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `24/62 = 38.71%`; dependency-weighted `44.62%`; critical path `6/21 = 28.57%`; checkpoint not due until 25. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `python scripts/check_claim_language.py docs/manuscript docs/manuscript/generated docs/generated --dry-run` | repo root | PASS | Active manuscript/generated scan found no forbidden claim language after generated text rows were stored as digests. |
| `python scripts/check_claim_language.py <PR-113 changed files> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-113 changed files>` | repo root | PASS | No forbidden claim patterns detected after report/test sanitization. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-113 generated and handoff docs>` | repo root | PASS | No unmarked strong claims detected. |
| `venv/bin/python scripts/check_artifact_manifests.py --dry-run` | repo root | PASS | Still reports 96 quarantined assets, 0 manifested figures, and 0 manifest issues. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6986 deselected`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6933/6992 tests collected (59 deselected)`. |

Numerical/scientific impact: none. PR-113 is COMMON/MANUSCRIPT diagnostic
inventory and freeze-gate tooling.

Artifact/claim-tier impact: `docs/generated/manuscript_figure_inventory.md`
and `docs/generated/missing_figure_references.md` are diagnostic-only
inventories. They record 94 includegraphics refs, 0 manifest-backed resolved
refs, 72 quarantined refs, 22 missing refs, and 23 text audit findings. They do
not compile the manuscript, promote figures, validate transfer, provide HTT
evidence, provide MIO certificates, or support family-ID claims.

## PR-051 - BudgetSpec and denominator-policy sensitivity

Date: 2026-06-13

Changed files: `htt/mio/formalism/budget_spec.py`,
`tests/mio/test_budget_spec.py`, `htt/mio/formalism/__init__.py`,
`htt/mio/tests/test_boot.py`,
`htt/bass/observational/departure_report_plumbing.py`,
`htt/bass/observational/test_ver2_mes_departure.py`,
`scripts/ver2_artifact_export.py`, `docs/PR_DELTAS/pr-051.md`, status files,
PR-012 generated status sidecars, checkpoint artifacts, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/mio/test_budget_spec.py -q` before implementation | repo root | FAIL | Red phase: missing `mio.formalism.budget_spec`. |
| `venv/bin/python -m pytest tests/mio/test_budget_spec.py htt/bass/observational/test_ver2_mes_departure.py -q` | repo root | PASS | `23 passed`; covers policy distinction, explicit denominator policy, positive finite denominators, transfer metadata, atlas status, observational support metadata, sensitivity provenance, and BASS legacy bridge guards. |
| `venv/bin/python -m pytest tests/mio/test_budget_spec.py -q` | repo root | PASS | `15 passed`. |
| `venv/bin/python -m pytest htt/mio/tests/test_boot.py htt/bass/observational/test_ver2_mes_departure.py -q` | repo root | PASS | `11 passed`. |
| `venv/bin/python -m pytest tests/mio/test_departure_bundle.py tests/contracts/test_transfer_registry.py tests/contracts/test_claim_language_lint.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_ownership_firewall.py -q` | repo root | PASS | `59 passed`; adjacent MIO/transfer/claim/ownership/firewall suites remain green. |
| `venv/bin/python -m py_compile htt/mio/formalism/budget_spec.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py tests/mio/test_budget_spec.py htt/bass/observational/departure_report_plumbing.py htt/bass/observational/test_ver2_mes_departure.py scripts/ver2_artifact_export.py` | repo root | PASS | Touched Python files compile. |
| `python -m pytest tests/mio/test_budget_spec.py -q` | repo root | FAIL | Host Python has no pytest; venv pytest is authoritative. |
| `venv/bin/python -m pytest scripts/test_ver2_artifact_export.py -q` | repo root | NOT COMPLETED | Interrupted after about seven minutes with only one dot; not counted as passing evidence. |
| Targeted compile/AST export smoke for `scripts/ver2_artifact_export.py` | repo root | PASS | Confirmed the changed `build_descriptive_departure_report` caller passes literal `denominator_policy="MES_linear"`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7002 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6949/7008 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status sidecars at 25 completed PRs. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `25/62 = 40.32%`; dependency-weighted `47.18%`; critical path `7/21 = 33.33%`; wrote checkpoint 025; no replan required. |
| `python scripts/check_claim_language.py <PR-051 files> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-051 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-051 files>` | repo root | PASS | No unmarked strong claims detected. |

Numerical/scientific impact: no new solver or inference computation.
PR-051 is a MIO diagnostic denominator-policy/provenance contract and a
fail-closed legacy BASS compatibility guard.

Artifact/claim-tier impact: generated checkpoint/status artifacts are DAG
bookkeeping only. The new `BudgetSpec` and sensitivity points are
diagnostic-only metadata; they do not implement Q/F/Pi/G_F, HTT
posterior/evidence, MIO certificates, transfer validation, native solver
validation, morphology compatibility, or family-ID claims.

## PR-042 - PreferredAxis production gate and downstream synthesis lock

Date: 2026-06-13

Changed files: `htt/htt/htt/direction/__init__.py`,
`htt/htt/htt/direction/preferred_axis.py`,
`htt/htt/htt/zoa/axis_promotion.py`, `htt/htt/htt/zoa/__init__.py`,
`htt/htt/htt/__init__.py`, `htt/htt/__init__.py`, `htt/__init__.py`,
`htt/htt/htt/PR13AJ_full_a2m_restoration.py`, `htt/test_packaging_imports.py`,
`tests/htt/test_preferred_axis_gate.py`, `htt/htt/tests/test_PR13AJ_gate.py`,
`docs/PR_DELTAS/pr-042.md`, DAG backlog mirrors, status files, PR-012
generated status sidecars, the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_preferred_axis_gate.py -q` before implementation | repo root | FAIL | Red phase: `ModuleNotFoundError: No module named 'htt.direction'`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_preferred_axis_gate.py -q` | repo root | PASS | `6 passed`; covers default diagnostic axis, ZoA diagnostic lockout, rich sky-support requirements, promotion-record requirement/mismatch, positive posterior-axis lock, and `restore_full_a2m` lock. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_preferred_axis_gate.py htt/htt/tests/test_PR13AJ_gate.py -q` | repo root | PASS | `18 passed`; adjacent PR13AJ gate updated to require strict lock metadata, malformed hashes, forged axis provenance, and self-attested lineage status. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_zoa_selection_ladder.py htt/htt/tests/test_ver2_axis_gate.py tests/htt/test_sky_support_contract.py htt/src/common/test_healpix_selection.py -q` | repo root | PASS | `39 passed`; ZoA, basic axis-gate, sky-support, and pixel-selection contracts remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/htt/tests/test_ver2_directional_shell.py htt/htt/tests/test_ver2_likelihood_scope_guard.py htt/src/common/test_posterior_summary.py -q` | repo root | PASS | `43 passed`; directional-shell, MIO/TSC scope, and posterior-axis constructor regressions remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` | repo root | PASS | `7 passed`; `htt.direction`, `htt.zoa.axis_promotion`, nested-cwd import, and `from htt import *` expose the PR-042 surface. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/htt/htt/direction/__init__.py htt/htt/htt/direction/preferred_axis.py htt/htt/htt/zoa/axis_promotion.py htt/htt/htt/zoa/__init__.py htt/htt/htt/PR13AJ_full_a2m_restoration.py tests/htt/test_preferred_axis_gate.py htt/htt/tests/test_PR13AJ_gate.py` | repo root | PASS | Touched Python files compile. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `26/62 = 41.94%`; dependency-weighted `48.72%`; critical path `7/21 = 33.33%`; next checkpoint at 30. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 26 completed PRs. |
| `python scripts/check_claim_language.py <PR-042 files> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-042 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-042 files>` before handoff wording fix | repo root | FAIL | Flagged one handoff line mentioning morphology compatibility without a nearby blocker marker. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-042 files>` | repo root | PASS | No unmarked strong claims detected after wording fix. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7017 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6964/7023 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` after backlog path correction | repo root | PASS | `OK: 62 PRs, DAG valid`; PR-042 backlog paths now use live `htt/htt/htt` files. |
| `PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json` after backlog path correction | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix after DAG metadata edits. |

Numerical/scientific impact: no new solver, transfer calculation, posterior
evidence, or null ensemble computation. PR-042 adds HTT gate metadata and a
downstream harmonic synthesis lock only.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The new `AxisPromotionRecord` and decision metadata are
diagnostic-only/pre-solver gate metadata with
`lineage_status="self_attested_pre_solver"`; they do not create a production
axis, native solver result, transfer validation, HTT posterior evidence, MIO
certificate, morphology-compatibility claim, or geometry/family-ID claim.

## PR-072 - Low-ell scalar summaries as OBSSTAT features

Date: 2026-06-13

Changed files: `htt/obsstat/scalar_lowell.py`, `htt/obsstat/__init__.py`,
`tests/obsstat/test_scalar_lowell.py`, `htt/test_packaging_imports.py`,
`docs/PR_DELTAS/pr-072.md`, status files, PR-012 generated status sidecars,
the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_scalar_lowell.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_scalar_lowell.py -q` after red tests | repo root | FAIL | Red phase: missing `htt.obsstat.scalar_lowell`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_scalar_lowell.py -q` first implementation | repo root | FAIL | Payload used inference-shaped keys and uncalibrated p-value-like metadata. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_scalar_lowell.py -q` after reviewer fixes | repo root | PASS | `11 passed`; covers formulas, dense full alm `C_l`, mixed-source consistency, ell-zero planarity, payload keys, null metadata, export surface, claim rejection, and constructor invariants. |
| `python -m pytest tests/obsstat/test_scalar_lowell.py -q` | repo root | FAIL | Ambient `/usr/bin/python` lacks pytest; venv-backed command is the authoritative local PR-card validation. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_alm_conventions.py tests/obsstat/test_observable_vector.py -q` | repo root | PASS | `18 passed`; adjacent OBSSTAT convention/vector contracts remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat -q` | repo root | PASS | `29 passed`; OBSSTAT directory remains green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` | repo root | PASS | `8 passed`; includes scalar import and top-level alias identity. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_scalar_lowell.py htt/test_packaging_imports.py --collect-only -q` | repo root | PASS | `19 tests collected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/obsstat/scalar_lowell.py htt/obsstat/__init__.py tests/obsstat/test_scalar_lowell.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python scripts/check_claim_language.py htt/obsstat/scalar_lowell.py htt/obsstat/__init__.py tests/obsstat/test_scalar_lowell.py htt/test_packaging_imports.py --dry-run` before term-table fix | repo root | FAIL | Internal forbidden-phrase table contained an exact forbidden phrase literal. |
| `venv/bin/python scripts/check_claim_language.py htt/obsstat/scalar_lowell.py htt/obsstat/__init__.py tests/obsstat/test_scalar_lowell.py htt/test_packaging_imports.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/obsstat/scalar_lowell.py htt/obsstat/__init__.py tests/obsstat/test_scalar_lowell.py htt/test_packaging_imports.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/obsstat/scalar_lowell.py htt/obsstat/__init__.py tests/obsstat/test_scalar_lowell.py htt/test_packaging_imports.py` | repo root | PASS | No unmarked strong claims detected. |
| `venv/bin/python scripts/check_claim_language.py <PR-072 code, tests, delta, status, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-072 code, tests, delta, status, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-072 code, tests, delta, status, and handoff docs>` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 27 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `27/62 = 43.55%`; dependency-weighted `49.74%`; critical path `7/21 = 33.33%`; checkpoint not due until 30. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `8 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7029 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6976/7035 tests collected (59 deselected)`. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: PR-072 adds deterministic OBSSTAT scalar feature
extraction with explicit formulas and strict alm/null metadata gates. It adds
no native solver, transfer calculation, HTT model-input surface, MIO output, or
null ensemble generator.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The scalar summaries are diagnostic-only OBSSTAT features with
`transfer_source="none"` and `model_role="not_model_input"`. They do not
support morphology, geometry, or family-ID claims.

## PR-081 - Future native low-ell adapter stubs without fake solver output

Date: 2026-06-13

Changed files: `htt/bass/transfer/native_schema.py`,
`htt/bass/transfer/native_adapter.py`, `htt/bass/transfer/__init__.py`,
`htt/src/common/transfer_registry.py`, `tests/bass/test_native_adapter_stub.py`,
`tests/contracts/test_transfer_registry.py`, `htt/test_packaging_imports.py`,
`docs/PR_DELTAS/pr-081.md`, BASS backlog path mirrors, status files, PR-012
generated status sidecars, the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_native_adapter_stub.py -q` before implementation | repo root | FAIL | Red phase: target file initially absent, then missing `bass.transfer.native_schema` and `native_adapter`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_native_adapter_stub.py -q` | repo root | PASS | `6 passed`; schema-only metadata, non-consumable transfer metadata, import/export surface, and fail-closed execution methods covered. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `12 passed`; schema-only/non-consumable/no-value transfer metadata is rejected as result provenance. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_external_transfer_registry.py -q` | repo root | PASS | `13 passed`; PR-080 external/proxy transfer behavior remains green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_native_adapter_stub.py tests/bass/test_external_transfer_registry.py tests/contracts/test_transfer_registry.py htt/test_packaging_imports.py -q` | repo root | PASS | `39 passed`; native stub, external transfer, common transfer, and package import surfaces are green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/src/common/transfer_registry.py htt/bass/transfer/native_schema.py htt/bass/transfer/native_adapter.py htt/bass/transfer/__init__.py tests/bass/test_native_adapter_stub.py tests/contracts/test_transfer_registry.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python scripts/check_claim_language.py htt/src/common/transfer_registry.py htt/bass/transfer tests/bass/test_native_adapter_stub.py tests/contracts/test_transfer_registry.py htt/test_packaging_imports.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/src/common/transfer_registry.py htt/bass/transfer tests/bass/test_native_adapter_stub.py tests/contracts/test_transfer_registry.py htt/test_packaging_imports.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/src/common/transfer_registry.py htt/bass/transfer tests/bass/test_native_adapter_stub.py tests/contracts/test_transfer_registry.py htt/test_packaging_imports.py` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 28 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `28/62 = 45.16%`; dependency-weighted `50.77%`; critical path `7/21 = 33.33%`; checkpoint not due until 30. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `venv/bin/python scripts/check_claim_language.py <PR-081 code, tests, delta, status, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-081 code, tests, delta, status, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-081 code, tests, delta, status, and handoff docs>` | repo root | PASS | No unmarked strong claims detected. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `8 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7036 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6983/7042 tests collected (59 deselected)`. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: no solver execution, no solver artifact loading,
no synthetic native values, and no result-producing native transfer path.
PR-081 adds schema-only BASS_PY handoff metadata and fail-closed adapter
methods.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. Native schema metadata is diagnostic-only, schema-only, no-values, and
non-consumable as result provenance. It does not validate native transfer,
produce HTT evidence, produce MIO output, or support morphology, geometry, or
family-ID claims.

## PR-031 - Generic semantic guards extracted from TSC legacy

Date: 2026-06-13

Changed files: `htt/src/common/semantic_guards/admissibility_status.py`,
`htt/src/common/semantic_guards/source_propagation_status.py`,
`htt/src/common/semantic_guards/__init__.py`,
`htt/src/common/semantic_guards/no_overclaim.py`,
`tests/contracts/test_semantic_guards.py`, `htt/test_packaging_imports.py`,
`docs/PR_DELTAS/pr-031.md`, status files, PR-012 generated status sidecars,
the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_semantic_guards.py -q` before implementation | repo root | FAIL | Red phase: missing `common.semantic_guards.admissibility_status`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_semantic_guards.py -q` initial implementation | repo root | PASS | `7 passed`; first source/propagation/observable split contract. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_semantic_guards.py -q` after reviewer fixes | repo root | PASS | `16 passed`; covers explicit status separation, no auto-promotion, owner/scope preservation, stronger-tier rejection, diagnostic-only/block ceilings, scanner variants, and import hygiene. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_claim_language_lint.py htt/test_packaging_imports.py -q` | repo root | PASS | `22 passed`; claim lint and import smoke remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_claim_language_lint.py tests/contracts/test_ownership_firewall.py tests/contracts/test_artifact_manifest.py tests/tsc/test_tsc_legacy_boundary.py htt/tsc/audit/test_no_overclaim.py -q` | repo root | PASS | `48 passed`; ownership/firewall and TSC legacy boundary coverage remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/tsc/budget/test_source_to_channel.py htt/tsc/adapters/test_bass_runtime.py htt/tsc/adapters/test_htt_inference.py htt/tsc/adapters/test_mio_certificate.py htt/tsc/reports/test_overlay_builder.py htt/tsc/reports/test_json_export.py -q` | repo root | PASS | `24 passed`; legacy TSC budget/adapter/report behavior remains compatible. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` | repo root | PASS | `8 passed`; new COMMON guard modules import from repo root and temp cwd. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/src/common/semantic_guards/admissibility_status.py htt/src/common/semantic_guards/source_propagation_status.py htt/src/common/semantic_guards/no_overclaim.py htt/src/common/semantic_guards/__init__.py tests/contracts/test_semantic_guards.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python scripts/check_claim_language.py <PR-031 code and tests> --dry-run` | repo root | PASS | No forbidden claim language detected after scanner-fixture rewrite. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-031 code and tests>` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-031 code and tests>` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 29 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `29/62 = 46.77%`; dependency-weighted `51.79%`; critical path `7/21 = 33.33%`; checkpoint not due until 30. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `8 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7052 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6999/7058 tests collected (59 deselected)`. |

Numerical/scientific impact: no solver, transfer calculation, posterior
evidence, MIO certificate, OBSSTAT feature, null ensemble, rank audit, or
native morphology atlas output was added. PR-031 adds COMMON semantic guard
metadata only.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The new semantic guard records preserve source, propagation, and
observable status separation and can append caveats while preserving artifact
owner/scope. They are capped at diagnostic-only or blocked status and do not
support statistical observable validation, native solver validation, HTT
evidence, MIO certification, morphology compatibility, or geometry/family
claims.

## PR-052 - Q normalized score implementation

Date: 2026-06-13

Changed files: `htt/mio/formalism/normalized_score.py`,
`htt/mio/formalism/__init__.py`, `htt/mio/tests/test_boot.py`,
`tests/mio/test_normalized_score.py`, `docs/PR_DELTAS/pr-052.md`, status
files, PR-012 generated status sidecars, checkpoint 030, the progress
scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `venv/bin/python -m pytest tests/mio/test_normalized_score.py -q` before implementation | repo root | FAIL | Red phase: missing `mio.formalism.normalized_score`. |
| `venv/bin/python -m pytest tests/mio/test_normalized_score.py -q` after initial implementation | repo root | PASS | `9 passed`; covered numerator policies, denominator policy, metadata gates, transfer provenance, and exports before post-review fixes. |
| `venv/bin/python -m pytest tests/mio/test_normalized_score.py -q` after post-review claim-gate fixes | repo root | PASS | `11 passed`; adds budget-label/assumption reserved-language gates and family/native prose rejection. |
| `venv/bin/python -m pytest tests/mio/test_normalized_score.py tests/mio/test_budget_spec.py tests/mio/test_departure_bundle.py htt/mio/tests/test_boot.py -q` | repo root | PASS | `40 passed`; adjacent MIO formalism and boot tests remain green. |
| `venv/bin/python -m py_compile htt/mio/formalism/normalized_score.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py tests/mio/test_normalized_score.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m pytest tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_ownership_firewall.py tests/contracts/test_claim_language_lint.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `49 passed`; MIO/HTT separation, ownership, claim, and transfer contracts remain green. |
| `python scripts/check_claim_language.py htt/mio/formalism/normalized_score.py tests/mio/test_normalized_score.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/mio/formalism/normalized_score.py tests/mio/test_normalized_score.py` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/mio/formalism/normalized_score.py tests/mio/test_normalized_score.py` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `8 passed`. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7063 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7010/7069 tests collected (59 deselected)`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` before YAML note fix | repo root | FAIL | Status note contained an unquoted colon in a plain YAML scalar. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` before YAML note fix | repo root | FAIL | Same YAML scanner error from status note. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 30 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `30/62 = 48.39%`; dependency-weighted `53.85%`; critical path `8/21 = 38.1%`; wrote checkpoint 030; no replan required. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `python scripts/check_claim_language.py <intended PR-052 files> --dry-run` | repo root | PASS | No forbidden claim language detected; pre-existing unrelated dirty handoff/config files excluded from PR-052 scope. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <intended PR-052 files>` | repo root | PASS | No forbidden claim patterns detected; pre-existing unrelated dirty handoff/config files excluded from PR-052 scope. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <intended PR-052 files>` | repo root | PASS | No unmarked strong claims detected after wording fix in PR delta and next-session prompt. |

Numerical/scientific impact: no solver, transfer calculation, posterior
pushforward, MIO certificate, OBSSTAT feature, null ensemble, rank audit, or
native morphology atlas output was added. PR-052 adds MIO diagnostic Q
normalization metadata only.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The new Q payload is MIO-owned, diagnostic-only, transfer-conditional
when its inputs are transfer-derived, and separated from certified F, HTT
inference, native solver validation, morphology compatibility, and
geometry/family claims.

## PR-043 - Mock calibration harness for axis and direction claims

Date: 2026-06-13

Changed files: `htt/src/common/mock_calibration.py`,
`htt/htt/htt/nulls/axis_nulls.py`, `htt/htt/htt/nulls/__init__.py`,
`htt/htt/htt/zoa/axis_promotion.py`,
`htt/htt/htt/PR13AJ_full_a2m_restoration.py`,
`tests/htt/test_mock_calibration_gate.py`,
`tests/htt/test_preferred_axis_gate.py`, `htt/htt/tests/test_PR13AJ_gate.py`,
`docs/PR_DELTAS/pr-043.md`, status files, PR-012 generated status sidecars,
the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_mock_calibration_gate.py -q` before implementation | repo root | FAIL | Red phase: missing `htt.nulls.axis_nulls`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_mock_calibration_gate.py -q` after implementation | repo root | PASS | `6 passed`; covered report metadata, missing report, inadequate metrics, hash mismatch, bad FPR, and sky-support mismatch. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_mock_calibration_gate.py tests/htt/test_preferred_axis_gate.py htt/htt/tests/test_PR13AJ_gate.py -q` after zero-success fix | repo root | PASS | `25 passed`; PR-043 gate plus adjacent production-axis and PR13AJ synthesis locks. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_mock_calibration_gate.py tests/htt/test_preferred_axis_gate.py htt/htt/tests/test_PR13AJ_gate.py -q` after reviewer hardening | repo root | PASS | `31 passed`; adds coverage-interval, covariance-status, transfer-source, scan-trial, exact-count, bias-tail, mask-mismatch, and scan-mismatch regressions. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_zoa_selection_ladder.py htt/src/common/test_mock_calibration.py htt/htt/tests/test_nulls.py -q` | repo root | PASS | `41 passed`; adjacent ZoA, COMMON mock, and HTT null-registry tests remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/src/common/mock_calibration.py htt/htt/htt/nulls/axis_nulls.py htt/htt/htt/nulls/__init__.py htt/htt/htt/zoa/axis_promotion.py htt/htt/htt/PR13AJ_full_a2m_restoration.py tests/htt/test_mock_calibration_gate.py tests/htt/test_preferred_axis_gate.py htt/htt/tests/test_PR13AJ_gate.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `8 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7076 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7023/7082 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest tests/htt/test_mock_calibration_gate.py -q` | repo root | PASS | Exact PR-card command via repo venv: `13 passed`. |
| `venv/bin/python -m pytest tests/contracts/test_claim_language_lint.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_ownership_firewall.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `49 passed`; claim, MIO/HTT, ownership, and transfer firewalls remain green. |
| `python scripts/check_claim_language.py <PR-043 code/tests> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-043 code/tests>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-043 code/tests>` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 31 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `31/62 = 50.0%`; dependency-weighted `55.38%`; critical path `8/21 = 38.1%`; checkpoint not due until 35. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: no solver execution, transfer calculation,
posterior evidence, MIO certificate, OBSSTAT feature extraction, or native
morphology atlas output was added. PR-043 adds report-backed directional mock
calibration gate metadata only.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The new axis mock-calibration report is HTT-owned, diagnostic-only,
pre-solver gate metadata with explicit PR-040 sky-support metadata,
sky/mask/scan hashes, exact event counts, bias-tail metadata, scan-trial
provenance, calibrated covariance status, and null mock status. Missing or
inadequate mock calibration caps directional claims at diagnostic-only and
blocks production-axis promotion.

## PR-073 - Morphology axes and alignment features

Date: 2026-06-13

Changed files: `htt/obsstat/morphology.py`, `htt/obsstat/__init__.py`,
`tests/obsstat/test_morphology.py`, `htt/test_packaging_imports.py`,
`docs/PR_DELTAS/pr-073.md`, status files, PR-012 generated status sidecars,
the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_morphology.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_morphology.py -q` after red tests | repo root | FAIL | Red phase: missing `htt.obsstat.morphology`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_morphology.py -q` first implementation | repo root | FAIL | Constructor and caveat wording issues fixed before closeout. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_morphology.py -q` | repo root | PASS | `6 passed`; tensor axes, antipodal alignment, null/look-elsewhere metadata, degeneracy, claim guards, import firewall. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_morphology.py tests/obsstat/test_observable_vector.py tests/obsstat/test_scalar_lowell.py tests/obsstat/test_alm_conventions.py -q` | repo root | PASS | `35 passed`; adjacent OBSSTAT feature surfaces remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_preferred_axis_gate.py htt/test_packaging_imports.py -q` | repo root | PASS | `18 passed`; PR-042 PreferredAxis lock and package imports remain green before alias-loop cleanup. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat --collect-only -q` | repo root | PASS | `35 tests collected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/obsstat/morphology.py htt/obsstat/__init__.py tests/obsstat/test_morphology.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python scripts/check_claim_language.py htt/obsstat/morphology.py htt/obsstat/__init__.py tests/obsstat/test_morphology.py htt/test_packaging_imports.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/obsstat/morphology.py htt/obsstat/__init__.py tests/obsstat/test_morphology.py htt/test_packaging_imports.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/obsstat/morphology.py htt/obsstat/__init__.py tests/obsstat/test_morphology.py htt/test_packaging_imports.py` | repo root | PASS | No unmarked strong claims detected. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` | repo root | PASS | `9 passed`; scalar and morphology aliases check both import orders. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 32 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `32/62 = 51.61%`; dependency-weighted `56.92%`; critical path `8/21 = 38.1%`; checkpoint not due until 35. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | `status_cmp=0`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `9 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7083 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7030/7089 tests collected (59 deselected)`. |
| `venv/bin/python scripts/check_claim_language.py <PR-073 code, tests, delta, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-073 code, tests, delta, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-073 code, tests, delta, and handoff docs>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --check` | repo root | PASS | No whitespace errors. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_morphology.py -q` after reviewer hardening | repo root | PASS | `6 passed`; degenerate alignments are suppressed, rank metadata is split, null metadata is stricter, and public diagnostic-axis source fields are locked. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_morphology.py tests/obsstat/test_observable_vector.py tests/obsstat/test_scalar_lowell.py tests/obsstat/test_alm_conventions.py -q` after reviewer hardening | repo root | PASS | `35 passed`; adjacent OBSSTAT feature surfaces remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_preferred_axis_gate.py htt/test_packaging_imports.py -q` after reviewer hardening | repo root | PASS | `18 passed`; PreferredAxis lock and packaging remain green. |
| `venv/bin/python scripts/check_claim_language.py <PR-073 code, tests, delta, and handoff docs> --dry-run` after reviewer hardening | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-073 code, tests, delta, and handoff docs>` after reviewer hardening | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-073 code, tests, delta, and handoff docs>` after reviewer hardening | repo root | PASS | No unmarked strong claims detected. |

Numerical/scientific impact: no solver execution, transfer calculation,
posterior evidence, MIO certificate, native morphology atlas, or family-label
output was added. PR-073 extracts diagnostic morphology axes from a
caller-supplied symmetric tensor, records tensor rank and axis-identifiability
metadata, suppresses alignments for degenerate axes, separates axiality from
planarity, and uses antipodal alignment definitions.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The new morphology payload is OBSSTAT-owned, diagnostic-only,
feature-only unless null metadata is supplied, `transfer_source=none`, not
model input, not MIO output, and not a production axis. Its diagnostic
PreferredAxis adapter is fail-closed and remains blocked by PR-042/PR-043
harmonic-synthesis gates.

## PR-082 - AtlasEntryLite and transfer side-by-side comparison schema

Date: 2026-06-13

Changed files: `htt/bass/atlas/__init__.py`,
`htt/bass/atlas/atlas_entry.py`, `tests/bass/test_atlas_entry_lite.py`,
`htt/test_packaging_imports.py`, `docs/PR_DELTAS/pr-082.md`, status files,
PR-012 generated status sidecars, the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_atlas_entry_lite.py -q` before implementation | repo root | FAIL | Red phase: target file did not exist. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_atlas_entry_lite.py -q` first implementation | repo root | FAIL | Export miss: `entries_from_transfer_registry` was not exported from `bass.atlas`; fixed before closeout. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/bass/atlas/atlas_entry.py htt/bass/atlas/__init__.py tests/bass/test_atlas_entry_lite.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_atlas_entry_lite.py -q` | repo root | PASS | `12 passed`; side-by-side coexistence, external conditional metadata, native schema-only non-consumption, fake-native rejection, observed-data/posterior/evidence rejection, external status override rejection, native validation spoof rejection, family/morphology claim phrase rejection, top-level metadata tamper rejection, and value-bearing native metadata rejection. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_atlas_entry_lite.py tests/bass/test_external_transfer_registry.py tests/bass/test_native_adapter_stub.py tests/contracts/test_transfer_registry.py htt/test_packaging_imports.py -q` | repo root | PASS | `52 passed`; PR-080, PR-081, common transfer, and package surfaces remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_artifact_manifest.py tests/contracts/test_claim_language_lint.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_ownership_firewall.py -q` | repo root | PASS | `50 passed`; artifact, claim, MIO/HTT, and ownership firewalls remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass --collect-only -q` | repo root | PASS | `31 tests collected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/htt/tests/test_ver2_likelihood_scope_guard.py htt/htt/tests/test_ver2_local_global_discrimination.py htt/htt/tests/test_integration.py -q` | repo root | PASS | `36 passed`; HTT consumer guard paths remain green. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 33 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `33/62 = 53.23%`; dependency-weighted `58.97%`; critical path `8/21 = 38.1%`; checkpoint not due until 35. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | Package subset passed. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7095 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7042/7101 tests collected (59 deselected)`. |
| `venv/bin/python scripts/check_claim_language.py <PR-082 code, tests, delta, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-082 code, tests, delta, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-082 code, tests, delta, and handoff docs>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: no solver execution, external transfer
evaluation, native value generation, transfer validation, posterior evidence,
MIO certificate, native morphology atlas, or family-label output was added.
PR-082 adds BASS-owned side-by-side transfer provenance metadata only.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The new AtlasEntryLite comparison metadata is BASS-owned,
diagnostic-only, and not observed data, not posterior/evidence, not MIO
certificate content, not native solver output, and not family-identification
evidence. Embedded external/proxy transfer metadata remains conditional;
embedded future native schema metadata remains schema-only and non-consumable.

## PR-032 - Legacy theorem-to-test audit map

Date: 2026-06-13

Changed files: `scripts/codex_harness/generate_theorem_to_test_map.py`,
`docs/generated/theorem_to_test_map_legacy_tsc.json`,
`docs/deprecation/theorem_to_test_map.md`,
`tests/contracts/test_theorem_to_test_map.py`, `docs/PR_DELTAS/pr-032.md`,
status files, PR-012 generated status sidecars, the progress scoreboard, and
handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_theorem_to_test_map.py -q` before implementation | repo root | FAIL | Red phase: target file did not exist. |
| `venv/bin/python scripts/codex_harness/generate_theorem_to_test_map.py --write docs/generated/theorem_to_test_map_legacy_tsc.json` | repo root | PASS | Generated PR-032 audit map. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_theorem_to_test_map.py -q` initial implementation | repo root | FAIL | Import/export mismatch for `render_issues`, then doc phrase mismatch; both fixed. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_theorem_to_test_map.py -q` | repo root | PASS | `7 passed`; includes source-row equality, per-witness equality, witness-node collection, metadata gates, generator reproducibility, and claim-language scan. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/tsc/validation/test_theorem_map.py tests/tsc/test_tsc_legacy_boundary.py tests/contracts/test_semantic_guards.py -q` | repo root | PASS | `26 passed`; legacy TSC and COMMON semantic guard boundaries remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_claim_language_lint.py tests/contracts/test_artifact_manifest.py tests/contracts/test_status_snapshot.py -q` | repo root | PASS | `31 passed`; adjacent claim, manifest, and generated-status contracts remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_theorem_to_test_map.py tests/contracts/test_semantic_guards.py tests/contracts/test_claim_language_lint.py tests/tsc/test_tsc_legacy_boundary.py -q` | repo root | PASS | `45 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_theorem_to_test_map.py htt/tsc/validation/test_theorem_map.py -q` | repo root | PASS | `9 passed`; source and generated audit map stay synchronized. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_artifact_manifest.py tests/contracts/test_ownership_firewall.py -q` | repo root | PASS | `22 passed`; artifact and ownership boundaries remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile scripts/codex_harness/generate_theorem_to_test_map.py tests/contracts/test_theorem_to_test_map.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python scripts/check_claim_language.py docs/generated/theorem_to_test_map_legacy_tsc.json docs/deprecation/theorem_to_test_map.md tests/contracts/test_theorem_to_test_map.py scripts/codex_harness/generate_theorem_to_test_map.py --dry-run --include-archives` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py docs/generated/theorem_to_test_map_legacy_tsc.json docs/deprecation/theorem_to_test_map.md tests/contracts/test_theorem_to_test_map.py scripts/codex_harness/generate_theorem_to_test_map.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py docs/deprecation/theorem_to_test_map.md docs/PR_DELTAS/pr-031.md docs/PR_DELTAS/pr-030.md` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider --collect-only -q` | repo root | PASS | `7049/7108 tests collected (59 deselected)`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -m smoke -q` | repo root | PASS | `6 passed, 7102 deselected`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 34 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `34/62 = 54.84%`; dependency-weighted `59.49%`; critical path `8/21 = 38.1%`; checkpoint not due until 35. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |

Numerical/scientific impact: no solver execution, transfer calculation,
posterior evidence, MIO certificate, OBSSTAT feature extraction, native
morphology atlas, or family-label output was added.

Artifact/claim-tier impact: generated status artifacts are DAG bookkeeping
only. The new theorem-to-test map is COMMON-owned diagnostic-only audit
metadata with `transfer_source=none`, `TSC_LEGACY` provenance, live witness
pytest node references, config/input hashes, caveats, and explicit
non-consumption gates for production observation claims, HTT evidence, MIO
certificates, transfer/native validation, morphology compatibility, and
geometry/family-identification use.

## PR-053 - F certified filling fraction implementation

Date: 2026-06-13

Changed files: `htt/mio/formalism/filling_fraction.py`,
`htt/mio/formalism/__init__.py`, `htt/mio/tests/test_boot.py`,
`tests/mio/test_filling_fraction.py`, `docs/PR_DELTAS/pr-053.md`, status
files, PR-012 generated status sidecars, progress checkpoint 035, and handoff
docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_filling_fraction.py -q` before implementation | repo root | FAIL | Red phase: target file did not exist. |
| `python -m pytest tests/mio/test_filling_fraction.py -q` | repo root | FAIL | Host `/usr/bin/python` lacks pytest; venv pytest is authoritative. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_filling_fraction.py -q` | repo root | PASS | `21 passed`; sample-wise F, F_Bayes sample mean, sign-clean rejection, ceiling gates, no clipping, provenance, transfer, and overclaim tests. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/mio/formalism/filling_fraction.py tests/mio/test_filling_fraction.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_filling_fraction.py tests/mio/test_budget_spec.py tests/mio/test_normalized_score.py tests/mio/test_departure_bundle.py htt/mio/tests/test_boot.py -q` | repo root | PASS | `61 passed`; adjacent MIO formalism and boot coverage remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_ownership_firewall.py tests/contracts/test_claim_language_lint.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `49 passed`; firewall contracts remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider --collect-only -q tests/mio htt/mio/tests/test_package_root_exports.py` | repo root | PASS | `62 tests collected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/mio/tests/test_package_root_exports.py -q` | repo root | PASS | `4 passed`. |
| `venv/bin/python scripts/check_claim_language.py htt/mio/formalism/filling_fraction.py tests/mio/test_filling_fraction.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/mio/formalism/filling_fraction.py tests/mio/test_filling_fraction.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/mio/formalism/filling_fraction.py tests/mio/test_filling_fraction.py` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `9 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -m smoke -q` | repo root | PASS | `6 passed, 7123 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider --collect-only -q` | repo root | PASS | `7070/7129 tests collected (59 deselected)`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 35 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `35/62 = 56.45%`; dependency-weighted `61.54%`; critical path `9/21 = 42.86%`; checkpoint 035 written; replan not required. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |

Numerical/scientific impact: no solver execution, transfer validation, native
value generation, posterior evidence, MIO certificate, native morphology atlas,
or family-label output was added. PR-053 adds a MIO diagnostic-only
sample-wise F contract under strict sign-clean and certified-ceiling gates.

Artifact/claim-tier impact: generated status artifacts remain DAG bookkeeping
only. F payloads require owner/scope/claim tier, config and input hashes,
generating command, git or worktree provenance, transfer provenance, and
sky/covariance/null status metadata. Invalid F samples are rejected rather than
serialized as physical occupancy.

## PR-074 - Template-fit diagnostics with orientation scan metadata

Date: 2026-06-13

Changed files: `htt/obsstat/template_fit.py`, `htt/obsstat/__init__.py`,
`tests/obsstat/test_template_fit.py`, `htt/test_packaging_imports.py`,
`docs/PR_DELTAS/pr-074.md`, status files, PR-012 generated status sidecars,
the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_template_fit.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_template_fit.py -q` after red tests | repo root | FAIL | Red phase: missing `htt.obsstat.template_fit`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_template_fit.py -q` first implementation | repo root | FAIL | Dataclass field/method collision on `diagonal_inverse_variance`; fixed before closeout. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_template_fit.py::test_public_diagnostic_constructor_rejects_inconsistent_chi2_fields -q` before constructor hardening | repo root | FAIL | Red phase: public constructor accepted inconsistent DeltaChi2 metadata. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_template_fit.py::test_public_diagnostic_constructor_rejects_inconsistent_chi2_fields -q` before alias hardening | repo root | FAIL | Red phase: public constructor accepted inconsistent chi-square alias fields. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_template_fit.py -q` | repo root | PASS | `8 passed`; amplitude, DeltaChi2, covariance assumptions, off-diagonal full covariance, scan metadata, kill switch, constructor invariants, exports. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/obsstat/template_fit.py htt/obsstat/__init__.py tests/obsstat/test_template_fit.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat -q` | repo root | PASS | `43 passed`; adjacent OBSSTAT feature surfaces remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` | repo root | PASS | `10 passed`; package/import aliases include template-fit. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_template_fit.py htt/test_packaging_imports.py -q` | repo root | PASS | `18 passed`; focused package and PR-card surface. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_preferred_axis_gate.py tests/htt/test_mock_calibration_gate.py -q` | repo root | PASS | `22 passed`; orientation/directional gate neighborhood remains green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_ownership_firewall.py tests/contracts/test_claim_language_lint.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `49 passed`; MIO/HTT, ownership, claim, and transfer firewalls remain green. |
| `venv/bin/python scripts/check_claim_language.py htt/obsstat/template_fit.py htt/obsstat/__init__.py tests/obsstat/test_template_fit.py htt/test_packaging_imports.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/obsstat/template_fit.py htt/obsstat/__init__.py tests/obsstat/test_template_fit.py htt/test_packaging_imports.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/obsstat/template_fit.py htt/obsstat/__init__.py tests/obsstat/test_template_fit.py htt/test_packaging_imports.py` | repo root | PASS | No unmarked strong claims detected. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7079/7138 tests collected (59 deselected)`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7132 deselected`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 36 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `36/62 = 58.06%`; dependency-weighted `63.59%`; critical path `9/21 = 42.86%`; checkpoint not due until 40. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: no solver execution, transfer calculation,
posterior evidence, MIO certificate, native morphology atlas, or family-label
output was added. PR-074 adds an OBSSTAT diagnostic-only matched-template
feature contract for caller-supplied vectors.

Artifact/claim-tier impact: generated status artifacts remain DAG bookkeeping
only. Template-fit payloads require owner/scope/claim tier, config and input
hashes, generating command, git or worktree provenance, orientation scan
volume and hash, sky/mask status, and explicit covariance weighting metadata.
The covariance branch is weighting metadata only; covariance anomaly features
remain separate and are not emitted by this PR.

## PR-083 - Budget ceiling optimizer policy interface

Date: 2026-06-13

Changed files: `htt/bass/atlas/budget_ceiling_optimizer.py`,
`htt/bass/atlas/__init__.py`, `tests/bass/test_budget_ceiling_optimizer.py`,
`htt/test_packaging_imports.py`, `docs/PR_DELTAS/pr-083.md`, status files,
PR-012 generated status sidecars, the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_budget_ceiling_optimizer.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_budget_ceiling_optimizer.py -q` first implementation | repo root | FAIL | Fixture used incomplete canonical MIO components; fixed before closeout. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_budget_ceiling_optimizer.py -q` after reviewer fixes | repo root | PASS | `16 passed`; provenance, range, rank, rejected-candidate, MIO reference, and claim-guard regressions. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/bass/atlas/budget_ceiling_optimizer.py htt/bass/atlas/__init__.py tests/bass/test_budget_ceiling_optimizer.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/bass/test_budget_ceiling_optimizer.py tests/bass/test_atlas_entry_lite.py tests/mio/test_budget_spec.py tests/mio/test_normalized_score.py tests/mio/test_filling_fraction.py -q` | repo root | PASS | `75 passed`; BASS atlas and MIO budget/Q/F boundaries remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py htt/mio/tests/test_package_root_exports.py -q` | repo root | PASS | `14 passed`; package/import exports remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_transfer_registry.py tests/contracts/test_claim_language_lint.py tests/contracts/test_semantic_guards.py tests/contracts/test_ownership_firewall.py tests/contracts/test_mio_htt_no_merge.py htt/tsc/audit/test_no_overclaim.py -q` | repo root | PASS | `69 passed`; transfer, claim, ownership, MIO/HTT, and legacy overclaim firewalls remain green. |
| `venv/bin/python scripts/check_claim_language.py htt/bass/atlas/budget_ceiling_optimizer.py htt/bass/atlas/__init__.py tests/bass/test_budget_ceiling_optimizer.py htt/test_packaging_imports.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/bass/atlas/budget_ceiling_optimizer.py htt/bass/atlas/__init__.py tests/bass/test_budget_ceiling_optimizer.py htt/test_packaging_imports.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/bass/atlas/budget_ceiling_optimizer.py htt/bass/atlas/__init__.py tests/bass/test_budget_ceiling_optimizer.py htt/test_packaging_imports.py` | repo root | PASS | No unmarked strong claims detected. |
| `venv/bin/python scripts/check_claim_language.py <PR-083 code, tests, delta, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-083 code, tests, delta, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-083 code, tests, delta, and handoff docs>` | repo root | PASS | No unmarked strong claims detected after final handoff updates. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `10 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7148 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7095/7154 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 37 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `37/62 = 59.68%`; dependency-weighted `64.62%`; critical path `9/21 = 42.86%`; checkpoint not due until 40. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: no solver execution, transfer calculation,
native transfer validation, HTT posterior evidence, MIO certificate, native
morphology atlas, or family-label output was added. PR-083 adds a BASS-owned
diagnostic-only ceiling-policy interface and a MIO denominator reference bridge
under explicit provenance and rank gates.

Artifact/claim-tier impact: generated status artifacts remain DAG bookkeeping
only. Ceiling policy payloads require owner/scope/claim tier, config and input
hashes, generating command, git or worktree provenance, transfer source/spec,
prior, admissible set, valid range, rank metadata, rejected-candidate
provenance, and depth-gap metadata where applicable. External/proxy ceilings
remain transfer-conditional and do not certify native solver behavior.

## PR-054 - Pi exceedance curve and threshold discipline

Date: 2026-06-13

Changed files: `htt/mio/formalism/exceedance.py`,
`htt/mio/formalism/__init__.py`, `htt/mio/tests/test_boot.py`,
`tests/mio/test_exceedance.py`, `docs/PR_DELTAS/pr-054.md`, status files,
PR-012 generated status sidecars, the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py -q` after red tests | repo root | FAIL | Red phase: missing `mio.formalism.exceedance`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py -q` first implementation | repo root | FAIL | Fixed local assertion and constructor validation issues before closeout. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py -q` after reviewer hardening | repo root | PASS | `17 passed`; strict threshold, explicit measure, pre-registration, transfer, JSON, claim, and package-export regressions. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/mio/formalism/exceedance.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py tests/mio/test_exceedance.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py tests/mio/test_budget_spec.py tests/mio/test_normalized_score.py tests/mio/test_filling_fraction.py tests/mio/test_departure_bundle.py htt/mio/tests/test_boot.py htt/mio/tests/test_package_root_exports.py -q` | repo root | PASS | `82 passed`; adjacent MIO formalism and package exports remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_claim_language_lint.py tests/contracts/test_ownership_firewall.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `49 passed`; claim, ownership, MIO/HTT, and transfer firewalls remain green. |
| `venv/bin/python scripts/check_claim_language.py htt/mio/formalism/exceedance.py tests/mio/test_exceedance.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/mio/formalism/exceedance.py tests/mio/test_exceedance.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/mio/formalism/exceedance.py tests/mio/test_exceedance.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py` | repo root | PASS | No unmarked strong claims detected. |
| `venv/bin/python scripts/check_claim_language.py <PR-054 code, tests, delta, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-054 code, tests, delta, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-054 code, tests, delta, and handoff docs>` | repo root | PASS | No unmarked strong claims detected after final handoff updates. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `10 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7165 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7112/7171 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 38 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `38/62 = 61.29%`; dependency-weighted `66.15%`; critical path `10/21 = 47.62%`; checkpoint not due until 40. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: no solver execution, transfer calculation,
native value generation, HTT posterior evidence, MIO certificate, native
morphology atlas, or family-label output was added. PR-054 adds a MIO
diagnostic-only exceedance-curve contract over explicit Q or certified-F
diagnostic samples.

Artifact/claim-tier impact: generated status artifacts remain DAG bookkeeping
only. Pi payloads require explicit measure, threshold grid, threshold policy,
sample counts, source provenance, PR-014 transfer metadata when applicable,
support status metadata, config/input hashes, generating command, and git or
worktree provenance. Pi remains diagnostic-only and is not a p-value/FPR,
truth probability, posterior/evidence quantity, or native/family result.

## PR-075 - BiPoSH/sparse covariance feature extraction

Date: 2026-06-13

Changed files: `htt/obsstat/biposh_features.py`, `htt/obsstat/__init__.py`,
`htt/test_packaging_imports.py`, `tests/obsstat/test_biposh_features.py`,
`docs/PR_DELTAS/pr-075.md`, status files, PR-012 generated status sidecars,
the progress scoreboard, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_biposh_features.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| Import probe for `htt.obsstat.biposh_features` and `obsstat.biposh_features` | repo root | FAIL | Red phase: both modules missing. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_biposh_features.py -q` after red tests | repo root | FAIL | Expected red: module and exports missing. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_biposh_features.py -q` first implementation | repo root | FAIL | Overclaim guard scanned values but not risky metadata keys; fixed before closeout. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_biposh_features.py -q` | repo root | PASS | `12 passed`; BiPoSH metadata, norms, ordering, duplicate/invalid indices, triangle validity, threshold accounting, caveat hooks, transfer provenance, ObservableVector integration, protected transfer metadata, runtime caveat guards, and exports. |
| `python -m pytest tests/obsstat/test_biposh_features.py -q` | repo root | FAIL | Host interpreter lacks pytest: `/usr/bin/python: No module named pytest`; the venv command is the authoritative run. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/obsstat/biposh_features.py htt/obsstat/__init__.py tests/obsstat/test_biposh_features.py htt/test_packaging_imports.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat/test_biposh_features.py tests/obsstat/test_observable_vector.py tests/obsstat/test_alm_conventions.py tests/obsstat/test_template_fit.py -q` | repo root | PASS | `38 passed`; adjacent OBSSTAT surfaces remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` | repo root | PASS | `11 passed`; package aliases include BiPoSH features. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/obsstat -q` | repo root | PASS | `55 passed`; OBSSTAT suite remains green. |
| `venv/bin/python scripts/check_claim_language.py htt/obsstat/biposh_features.py htt/obsstat/__init__.py tests/obsstat/test_biposh_features.py htt/test_packaging_imports.py --dry-run` before fixture rewrite | repo root | FAIL | Static negative-test phrase tripped the production claim-language scanner; fixed by runtime construction. |
| `venv/bin/python scripts/check_claim_language.py htt/obsstat/biposh_features.py htt/obsstat/__init__.py tests/obsstat/test_biposh_features.py htt/test_packaging_imports.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/obsstat/biposh_features.py htt/obsstat/__init__.py tests/obsstat/test_biposh_features.py htt/test_packaging_imports.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/obsstat/biposh_features.py htt/obsstat/__init__.py tests/obsstat/test_biposh_features.py htt/test_packaging_imports.py` | repo root | PASS | No unmarked strong claims detected. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 39 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `39/62 = 62.90%`; dependency-weighted `67.69%`; critical path `10/21 = 47.62%`; checkpoint not due until 40. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `git diff --check` | repo root | PASS | No whitespace errors. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `11 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7178 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_claim_language_lint.py tests/contracts/test_ownership_firewall.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `49 passed`; claim, ownership, MIO/HTT, and transfer firewalls remain green. |
| `venv/bin/python scripts/check_claim_language.py <PR-075 code, tests, delta, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-075 code, tests, delta, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-075 code, tests, delta, and handoff docs>` | repo root | PASS | No unmarked strong claims detected after final handoff updates. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7125/7184 tests collected (59 deselected)`. |

Numerical/scientific impact: no solver execution, transfer calculation, null
calibration, posterior evidence, MIO certificate, native morphology atlas, or
family-label output was added. PR-075 summarizes caller-supplied sparse
BiPoSH/off-diagonal covariance coefficients only.

Artifact/claim-tier impact: generated status artifacts remain DAG bookkeeping
only. BiPoSH payloads require OBSSTAT ownership, diagnostic-only claim tier,
convention and rotation metadata, config/input hashes, generating command,
git or worktree provenance, support statuses, caveats, and optional PR-014
transfer provenance for transfer-derived features.

Review closeout: reviewer blockers were fixed before commit. The final patch
rejects protected transfer metadata overwrites, scans transfer caveats and
nested list metadata keys, enforces sparse-key triangle validity, requires
non-empty allowlisted rotation metadata, separates channel-pair norm buckets,
and records threshold-discarded coefficient identities and power.

## PR-055 - G_F depth gap and log-gap robustness

Date: 2026-06-13

Changed files: `htt/mio/formalism/isotropy_gap.py`,
`htt/mio/formalism/__init__.py`, `htt/mio/tests/test_boot.py`,
`htt/test_packaging_imports.py`, `tests/mio/test_isotropy_gap.py`,
`scripts/codex_harness/progress_report.py`,
`scripts/codex_harness/test_pr_dag_harness.py`,
`docs/PR_DELTAS/pr-055.md`, status files, generated status sidecars, the
checkpoint 040 artifacts, and handoff docs.

| Command | CWD | Result | Notes |
|---|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_isotropy_gap.py -q` before test file | repo root | FAIL | Red phase: target file did not exist. |
| `python -m pytest tests/mio/test_isotropy_gap.py -q` | repo root | FAIL | Host interpreter lacks pytest: `/usr/bin/python: No module named pytest`; the venv command is the authoritative run. |
| Import probe for `mio.formalism.isotropy_gap` and `htt.mio.formalism.isotropy_gap` | repo root | FAIL | Red phase: module missing. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_isotropy_gap.py -q` after red tests | repo root | FAIL | Expected red: missing `mio.formalism.isotropy_gap`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_isotropy_gap.py -q` first implementation | repo root | FAIL | Fixed empty-metadata fixture defaulting and caveat error-label precision. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_isotropy_gap.py -q` after reviewer fixes | repo root | PASS | `22 passed`; includes transfer-metadata equality, sample-wise denominator provenance, controlled calibration statuses, hyphenated overclaim guards, missing-bin guards, mixed-transfer-source guard, and floor `>1` coverage. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/mio/formalism/isotropy_gap.py tests/mio/test_isotropy_gap.py htt/test_packaging_imports.py scripts/codex_harness/progress_report.py scripts/codex_harness/test_pr_dag_harness.py` | repo root | PASS | Touched Python files compile. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_isotropy_gap.py tests/mio/test_filling_fraction.py tests/mio/test_exceedance.py tests/mio/test_budget_spec.py tests/mio/test_normalized_score.py tests/mio/test_departure_bundle.py htt/mio/tests/test_boot.py htt/mio/tests/test_package_root_exports.py -q` | repo root | PASS | `104 passed`; adjacent MIO formalism and package exports remain green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider scripts/codex_harness/test_pr_dag_harness.py -q` | repo root | PASS | `16 passed`; scoreboard distinguishes checkpoint due from checkpoint artifact satisfied. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio -q` | repo root | PASS | `97 passed`; full top-level MIO test suite remains green. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` with `htt.mio.formalism.isotropy_gap` also added to temp-CWD imports | repo root | FAIL | `ModuleNotFoundError: No module named 'htt.mio'`; root cause was treating a repo-root source-tree alias as an installed temp-CWD namespace. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/test_packaging_imports.py -q` after scoped alias fix | repo root | PASS | `11 passed`; package import smoke includes `mio.formalism.isotropy_gap` everywhere and `htt.mio.formalism.isotropy_gap` from repo root. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_claim_language_lint.py tests/contracts/test_ownership_firewall.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_transfer_registry.py -q` | repo root | PASS | `49 passed`; claim, ownership, MIO/HTT, and transfer firewalls remain green. |
| `venv/bin/python scripts/check_claim_language.py htt/mio/formalism/isotropy_gap.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py htt/test_packaging_imports.py tests/mio/test_isotropy_gap.py scripts/codex_harness/progress_report.py scripts/codex_harness/test_pr_dag_harness.py --dry-run` | repo root | PASS | No forbidden claim language detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py htt/mio/formalism/isotropy_gap.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py htt/test_packaging_imports.py tests/mio/test_isotropy_gap.py scripts/codex_harness/progress_report.py scripts/codex_harness/test_pr_dag_harness.py` | repo root | PASS | No forbidden claim patterns detected. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py htt/mio/formalism/isotropy_gap.py htt/mio/formalism/__init__.py htt/mio/tests/test_boot.py htt/test_packaging_imports.py tests/mio/test_isotropy_gap.py scripts/codex_harness/progress_report.py scripts/codex_harness/test_pr_dag_harness.py` | repo root | PASS | No unmarked strong claims detected. |
| `PYTHONPATH=htt/src venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json` | repo root | PASS | Regenerated status snapshot, claim ledger, and status matrix at 40 completed PRs. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json` | repo root | PASS | `40/62 = 64.52%`; dependency-weighted `69.74%`; critical path `11/21 = 52.38%`; checkpoint `docs/generated/progress_checkpoints/checkpoint_040.md`; scoreboard says the checkpoint is due and satisfied; no replan required. |
| `venv/bin/python scripts/check_claim_language.py <PR-055 code, tests, delta, and handoff docs> --dry-run` | repo root | PASS | No forbidden claim language detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-055 code, tests, delta, and handoff docs>` | repo root | PASS | No forbidden claim patterns detected after final handoff updates. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-055 code, tests, delta, and handoff docs>` | repo root | PASS | No unmarked strong claims detected after final handoff updates. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `11 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 7201 deselected`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `7148/7207 tests collected (59 deselected)`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`; next topological PR is PR-076. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml` | repo root | PASS | Status mirrors match. |
| `git diff --check` | repo root | PASS | No whitespace errors. |

Numerical/scientific impact: no solver execution, transfer calculation,
native value generation, HTT posterior evidence, MIO certificate, native
morphology atlas, p-value/FPR calibration, or family-label output was added.
PR-055 adds a MIO diagnostic-only floor-stabilized depth-bin contrast over
certified-F summaries.

Artifact/claim-tier impact: generated status artifacts remain DAG bookkeeping
only. G_F payloads require explicit floor policy, depth-bin metadata,
controlled covariance and null/mock metadata, denominator-evolution split with
sample-wise x_C/denominator/F provenance, support metadata, config/input
hashes, generating command, git or worktree provenance, and matching PR-014
transfer source/spec IDs plus canonical transfer metadata when
transfer-derived.

---

## REV-Patch-A — EGS3 PSD-cone Omega_k admissible-domain fix (2026-06-28)

Audit finding (integrated phys-math-code audit): `egs3_psd_cone.admissibility`
claimed "M >= 0 iff admissible" over all four sectors, but `Omega_k_aniso =
Omega_k - Omega_k_ref` (`Omega_k = -^3R/(6H^2)`) is a SIGNED comparator
coordinate per the authoritative `comparator_policy.py` / `departure_contracts.py`
(ch03 Prop `x-sign`, `irrotational_negative` sector). A valid closed-type /
negative-curvature-departure background (`Omega_k < 0`) was wrongly ejected.
Latent today (no caller feeds the EGS3 cone signed Omega_k; it is a diagnostic /
report-builder surface fed nonneg synthetic values), so no published number changes.

Fix: moment-cone (PSD) positivity restricted to the three GENUINE second-moment
sectors {Sigma2, W2, Omega_tilt}; Omega_k excluded (signed, rides in C). Docstrings
updated. `x_C = tr(C M)` is independent of admissibility -> bit-identity preserved.

Changed files: `htt/obsstat/egs3_psd_cone.py` (admissibility + header docstring),
`research_gates/egs3/tests/test_egs3_axis_psd.py` (+P5SignedOmegaKDomainTests, 3 tests).

| Command | CWD | Result | Notes |
|---|---|---|---|
| `make egs3-gates` | repo root | PASS | `Ran 23 tests ... OK` (was 20; +3 P5 signed-Omega_k). |
| `pytest research_gates/egs3/tests/test_egs3_axis_psd.py tests/contracts/test_psd_cone_redesign.py tests/contracts/test_graded_comparator_upgrade.py research_gates/egs3/tests/test_egs3_axis_{a,b}.py -q` | repo root | PASS | `32 passed in 0.50s`. |
| `pytest tests/contracts --collect-only -q` | repo root | PASS | `352 tests collected` (no import breakage). |
| post-fix probe (neg Omega_k) | repo root | PASS | `admissibility(neg Omega_k).is_admissible=True`, `neg_sectors=()`, `x_C=1.2e-06` unchanged. |

Numerical/scientific impact: no solver run, no transfer calc, no native value,
no posterior/p-value/FPR calibration. Behavior change is confined to admissibility
of `Omega_k < 0` (now admissible, was rejected); the bit-identical `x_C` regression
is unaffected.

Artifact/claim-tier impact: representation-only; claim envelope unchanged
(diagnostic-only, no family ID / geometry / native solver). DOWNSTREAM WORDING
not yet touched: report/figure builders that consume `egs3_psd_cone` and the
`pr08_006_joint_artifact` "M>=0 admissible" phrasing should be regenerated/reworded
by the physics owner to state the moment-cone applies to the three nonneg sectors
and Omega_k is a signed coordinate. Tracked as the FM1 wording follow-up.

Remaining risks: FM2 (W2/Omega_k null-kind conflation), FM3 (eigenvalue-vs-diagonal
mislabel, no diagonal guard), FM4 (e-value finite-alpha k=0 crash / anti-conservative)
remain open per the audit; not addressed by this patch.

---

## REV-Patch-FM2+FM4 — EGS3 null-kind distinction + finite-null e-value (2026-06-28)

Two further integrated-audit findings:

FM2 (P1, physics/labeling): `_RESPONSE_SUPPORT` encodes W2 and Omega_k as identical
zero columns, so rank/null detection conflated a GENUINE order-independent structural
null (W2: radial n.Omega.n=0 + CMB curl/Weyl-blind) with a LEADING-EGS-ORDER no-channel
(Omega_k: re-opens at higher order). The "joint null {W2,Omega_k}" label (code + report
artifact) over-symmetrised them. Matches the external reviewer's headline revision.
Fix (additive, no behavior change to rank/null membership): `NULL_SECTOR_KIND` +
`describe_null_sectors` in `egs3_graded_comparator.py`; `pr08_006_joint_artifact`
sectors + `two_sector_no_go` now carry per-sector `null_kind`/`order_dependence`/
`reopens_via` and a split statement.

FM4 (P2, numerical/stats): `exceedance_evalue` divides by a passed alpha; a raw
finite-sample k/n estimate crashes at k=0 and is anti-conservative (Jensen
E[1/alpha_hat] > 1/alpha). Fix (additive): `exceedance_evalue_finite_null` with the
conservative add-one alpha_hat=(k+1)/(n+1) -- no k=0 crash, E <= raw plug-in, null
mean = 1-(1-p)^(n+1) <= 1. Existing known-alpha `exceedance_evalue` retained + docstring
caveat added.

Changed files: `htt/obsstat/egs3_graded_comparator.py`, `htt/obsstat/egs3_calibration.py`,
`scripts/pr08_006_joint_artifact.py`, `docs/generated/pr08_006_joint_artifact.json`
(regenerated), `research_gates/egs3/tests/test_egs3_axis_a.py` (+2 tests).

| Command | CWD | Result | Notes |
|---|---|---|---|
| `make egs3-gates` | repo root | PASS | `Ran 25 tests ... OK` (20 -> 23 Patch-A -> 25). |
| `pytest research_gates/egs3/tests/ tests/contracts/test_egs3_extension.py tests/contracts/test_pr08_006_joint_artifact.py tests/contracts/test_psd_cone_redesign.py tests/contracts/test_graded_comparator_upgrade.py -q` | repo root | PASS | `43 passed in 0.57s`. |
| `python scripts/pr08_006_joint_artifact.py` (regen) + `--check` via contract test | repo root | PASS | artifact up to date; `blind_sectors` unchanged `{W2,Omega_k}`. |
| `git diff --check` | repo root | PASS | clean. |

Numerical/scientific impact: FM2 is metadata-only (rank-2 count, reachable/null
membership, and all numeric values unchanged). FM4 adds a new function; existing
e-value path unchanged. No solver/transfer/posterior/calibration numbers move.

Artifact/claim-tier impact: `pr08_006_joint_artifact.json` regenerated additively;
claim-firewall fields (family_identification/native_solver_result/mio_as_odds/
scalar_to_family_promotion) unchanged false; `x_C_single_scalar` still null. Report
PDF/figure prose that repeats "joint null {W2,Omega_k}" should adopt the split wording
at the next manuscript pass (owner).

Remaining risks: FM3 (eigenvalue-vs-diagonal mislabel; no diagonal guard) and FM5/FM6
(placeholder C_up=9 load-bearing for "12/7"; tautological gates) remain open per audit.

---

## REV-Patch-FM3+FM5+FM6 + RE-AUDIT — EGS3/EGS2 (2026-06-28)

FM3 (P2, implementation/interface): the PSD-cone module advertises "identifiability
= reachable EIGENdirections" and "lambda_Sigma = shear eigenvalue", but operates on
the diagonal: `cone_shell` read `M[0,0]` (a Rayleigh quotient, NOT an eigenvalue for
off-diagonal M) and `eigen_identifiability` silently dropped cross terms. Fix:
`_require_diagonal` fail-closed guard (audit FM3) on `sectors_from_matrix`,
`eigen_identifiability`, `cone_shell_membership`, plus an axis-aligned assertion on
`reachable_projector`; off-diagonal (native-solver superset) input now raises instead
of mislabelling. `xc_from_matrix = tr(C M)` left general (valid for any M).

FM5 (P2, interface): the bracket nondegeneracy headline `C_up*kappa>1` (12/7) rests on
the documented PLACEHOLDER `C_UP=9`. Fix: `C_UP_PROVENANCE`, `nondegeneracy_threshold`
(= 1/kappa = 5.25), and `FillingBracket.{c_up_provenance, nondegeneracy_c_up_min,
nondegeneracy_robust}` so a consumer cannot treat the placeholder as a derived bound;
the headline is flagged robust iff true C_up > 5.25 (placeholder 9 clears it). The
zero-exclusion itself rests on the c_up-independent lower bound (unchanged).

FM6 (P2, testing): replaced tautological smoke (diagonal P masks diagonal M) with real
boundary tests: off-diagonal M rejected (P6), null-kind distinction (A1), finite-null
e-value no-crash/conservative (A3), placeholder-robustness (egs2 bracket).

RE-AUDIT (adversarial self-check of the patches): renamed the `FillingBracket`
`nondegeneracy_threshold` FIELD -> `nondegeneracy_c_up_min` to remove a shadow of the
module function of the same name. Consolidated probe over all six findings: ALL PASS.

| Command | CWD | Result | Notes |
|---|---|---|---|
| `make egs2-gates` | repo root | PASS | `Ran 14 tests ... OK`. |
| `make egs3-gates` | repo root | PASS | `Ran 28 tests ... OK` (20 -> 25 -> 28). |
| `pytest research_gates/egs2 research_gates/egs3 + 5 contract suites -q` | repo root | PASS | `65 passed in 0.69s`. |
| `pytest --collect-only -q` | repo root | PASS | `7716/7775 collected (59 deselected)`; no import errors. |
| `python scripts/pr08_006_joint_artifact.py --check` | repo root | PASS | deterministic, up to date. |
| `reviewer_verification.py` (external, stdlib-only) | scratch | PASS | `5/5` unchanged. |
| consolidated re-audit probe (FM1-FM5) | repo root | PASS | `ALL PASS`. |
| `git diff --check` | repo root | PASS | clean. |

Numerical/scientific impact: none. All fixes are guards / additive metadata / tests;
no numeric output of egs3_experiments.json, egs_results_table.*, or the theorem figures
changed (regenerated byte-identical). x_C bit-identity preserved throughout.

Artifact/claim-tier impact: only `pr08_006_joint_artifact.json` regenerated (FM2,
additive). Claim envelope unchanged (diagnostic-only). Audit scoreboard: FM1,FM2 (P1)
FIXED; FM3,FM4,FM5,FM6 (P2) FIXED. Open owner follow-up: manuscript/figure prose
adopting the split-null + signed-Omega_k + placeholder-C_up wording at next pass.

## REV-R155..R160 — v8 (Sixth Revision) external-audit cycle (2026-07-10, entry reconstructed)

This entry was found MISSING during the v8-update cycle and is reconstructed from the
commit evidence (a2b53c8..1ccbe3b). M4 sigma coefficients rederived bit-exact from the
web-sourced MES primary literature (MESa astro-ph/9501016 raw eq (51) + C1/C2; the
extracted "3/8" is a pdftotext digit-swap); omega/accel pinned primary-sourced (MESb
print-only). T3-full exact endpoint attainability (Bianchi I / Bianchi V initial data,
exactly-zero Gauss+momentum residuals). mathlib lane `formal_mathlib/` (v4.31.0, 8560
jobs). Teff draft applied as the additive active TEFF lane; TSC_LEGACY freeze untouched.
Adversarial verification re-run: 7 refute-prompted skeptics, 5 CONFIRMED / 2 PLAUSIBLE /
0 REFUTED, honesty fixes applied in-session (T3-full reframed to endpoint attainability).

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `make egs3-gates` | repo root | OK (183) | +20 vs v7 |
| `make teff-gates` | repo root | OK (9) | new lane |
| `venv/bin/python scripts/run_egs3_v7_seals.py --check` | repo root | current | incl. 3 v8 seals |
| `make v8-wolfram v8-mathlib` | repo root | PASS | xAct + lake build |
| `venv/bin/python scripts/build_external_audit_report_v8.py --check` | repo root | byte-stable | 47-page PDF |
| `venv/bin/python -m pytest tests/contracts -q` | repo root | 1 pre-existing fail | cf4pp network-blocked |

## REV-R161..R168 — v8-update cycle: non-1TB deferral execution + MES/comparator/Teff unification (2026-07-10)

Every deferred/future item executable without ~1TB science-data downloads was executed
(B1 T2'' successor repair; C6 real-H(z) Volterra kernel universality; C4 PSD-cone dual
independent review with in-session P1 repair; C2 real-CAMB visibility cross-check; C3
Omega_k external-prior survey -> documented null; C1 T3-int connected interior family +
derived vorticity slaving; C5a BGK transport application; C5b Rust twin parity, cargo
live 153/0; U1-U4 unification lane coupling the MES registry + graded comparator +
active Teff lane; K5 v8 card; D1 MESb retrieval attempt; D8 JWST seed attempt). All
frozen v5/v6/v6.1/v7 artifacts byte-stable throughout (successor-artifact pattern).

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `make egs3-gates` | repo root | OK | +~60 gate methods (axes B/E/G/U) |
| `make egs2-gates` | repo root | OK | +10 (CAMB cross-check) |
| `make teff-gates` | repo root | OK | +11 (transport/parity) |
| `venv/bin/python scripts/run_egs3_v7_seals.py --check` | repo root | current | 21 seals, all PASS |
| `make v8-wolfram` | repo root | PASS | + interior-family 10/10 + unification 16/16 |
| `venv/bin/python scripts/build_external_audit_report_v7.py --check` | repo root | byte-stable | run after EVERY phase |
| `venv/bin/python scripts/k5_cf4_identified_interval_card_v8.py --check` | repo root | current | firewall intact |
| `venv/bin/python scripts/build_egs_results_table_v8.py --check` | repo root | current | 55 rows (43 inherited verbatim) |
| `venv/bin/python scripts/make_egs2_egs3_theorem_figures.py --check` | repo root | current | +3 unification figures |

## PR-116 — safe GPT-5.6 physmath audit harness integration (2026-07-14)

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `venv/bin/python -B /home/cosmosapjw/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/htt-physmath-audit` | repo root | PASS | Repo adapter valid. |
| `venv/bin/python -B harness_templates/vendor/physmath-gpt56/3.1.0/coding/tools/validate_harness.py` | repo root | PASS | Read-only upstream structure check. |
| `venv/bin/python -B harness_templates/vendor/physmath-gpt56/3.1.0/research/tools/validate_workspace.py` | repo root | PASS | Read-only upstream structure check. |
| `venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_physmath_harness_vendor.py scripts/codex_harness/test_codex_assets.py scripts/codex_harness/test_pr_dag_harness.py tests/contracts/test_pr_delta_template.py htt/htt/tests/test_ver2_likelihood_scope_guard.py tests/obsstat/test_observable_vector.py tests/bass/test_external_transfer_registry.py tests/bass/test_atlas_entry_lite.py tests/bass/test_native_adapter_stub.py htt/mio/tests/test_mio_certificate_generator.py tests/contracts/test_mio_htt_no_merge.py tests/contracts/test_semantic_guards.py tests/contracts/test_claim_language_lint.py -q` | repo root | PASS | Final run: 145 passed in 3.62 s. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -m smoke -q` | repo root | PASS | 6 passed, 7,918 deselected in 3.57 s. |
| `venv/bin/python -B -m pytest -p no:cacheprovider --collect-only -q` | repo root | PASS | 7,865/7,924 collected; 59 deselected in 3.49 s. |
| `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | 65 PRs; DAG valid. |
| `venv/bin/python -B scripts/check_claim_language.py .agents/skills/htt-physmath-audit/SKILL.md docs/audits/harness_intake_20260714 docs/PR_DELTAS/pr-116.md --dry-run --format json` | repo root | PASS | Zero issues. |
| `venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py .agents/skills/htt-physmath-audit/SKILL.md docs/audits/harness_intake_20260714 docs/PR_DELTAS/pr-116.md` | repo root | PASS | Zero forbidden patterns. |
| `venv/bin/python -B scripts/build_external_audit_package.py --check` and `venv/bin/python -B scripts/check_publication_claim_freeze.py --check` | repo root | PASS | Refreshed generated provenance after DAG/status change. |
| `git diff --cached --check` | repo root | PASS | Exact vendor bytes preserved with scoped `-text`. |

Adversarial review found and fixed: ignored vendored `AGENTS.md`, dangling
installer dependencies, fixed-count skill tests, missing agent nicknames,
permanent root-hash locking, invalid manifest metadata, EOL conversion risk,
contaminated reinstall acceptance, and ambiguous initializer evidence. Upstream
validator success remains workflow reachability only, not science validation.
