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
