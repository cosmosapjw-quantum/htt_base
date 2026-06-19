# REV-R069 Delta: G_F Floor and Matched-Null Forecast Gate

owner: COMMON
implementation_scope: formalism_audit_revision
claim_tier: diagnostic_only
transfer_source: none_for_forecast_report_and_mixed_current_generated_context
sky_support_status: mixed_not_directional_and_mask_weighted_directional_support
null_mock_status: forecast_matched_null_blocked
generating_command: manual Codex REV-R069 implementation
git_commit_or_worktree_state: c81e79c+dirty before REV-R069 commit

## Evidence Read

- `htt/mio/formalism/isotropy_gap.py`
- `htt/htt/htt/infer/matched_complexity.py`
- `htt/htt/htt/infer/null_competition.py`
- `scripts/make_current_manuscript_figures.py`
- `scripts/verify_formalism_figure_labels.py`
- `scripts/result_packs/generate_pack_B_local_global.py`
- `scripts/build_statistical_formalism_audit_package.py`
- `tests/mio/test_isotropy_gap.py`
- `tests/htt/test_matched_nulls.py`
- `tests/contracts/test_formalism_figure_labels.py`
- `tests/contracts/test_current_manuscript_figures.py`
- Official Python dataclasses docs, pytest `tmp_path` docs, statsmodels multiple-testing docs, and SciPy FDR-control docs were checked before relying on current API behavior.

## Role Synthesis

- Code cartographer: canonical `IsotropyGap` already exposed `floor_applied_by_bin` and `denominator_evolution_split`, but current generated report surfaces did not bind or lint those fields.
- Harness engineer: add checked-in-payload tests and verifier rules, not constructor-only tests, so stale generated figures and payloads fail.
- Physics/statistics auditor: `G_F` displays must show floor value/label/reason, raw/effective `F`, floor application by bin, depth-bin metadata, and denominator split; matched-null output is forecast-only design sensitivity.
- Claim-gate reviewer: MIO owns the diagnostic `G_F` display contract; HTT owns matched-null forecast gating. Neither surface authorizes observed-data evidence, global-tilt wording, native solver validation, or family identification.
- Regression tester: run focused MIO/HTT/contract/Pack B tests plus generated-artifact freshness, claim-language, manifest, manuscript-figure, smoke, and DAG/progress gates.

## Changes

- Added `ArtifactMode.FORECAST_ONLY`.
- Added `GFMatchedNullForecastReport` and `build_gf_matched_null_forecast_report()` to HTT null competition.
- The forecast wrapper always exports `forecast_only=true`, `observed_data_evidence=false`, `authorization_scope=design_sensitivity_only`, `global_tilt_wording_allowed=false`, and Wilson count-based FPR wording.
- The forecast wrapper labels its counts as a deterministic current-code synthetic demonstration fixture, not production mocks or observed-data evidence.
- The forecast wrapper prefers dirty worktree provenance in `git_commit_or_worktree_state` and manifest `code_version` when both a clean commit and `+dirty` state are available.
- Passing forecast matched nulls remain `diagnostic_only`; failing forecast matched nulls are `blocked` and preserve `retuning_after_failure=false`.
- Added a generated `docs/generated/gf_matched_null_forecast_report.json` and Markdown companion.
- Extended the current science payload with `/semantic_and_vectors/g_f_display_contract` and `/semantic_and_vectors/g_f_matched_null_forecast`.
- The `G_F` display contract now binds floor value/label/reason, `floor_applied_by_bin`, raw/effective `F` by bin, depth-bin metadata, denominator-evolution split, matched-null forecast status, and blocked-use codes.
- Extended `scripts/verify_formalism_figure_labels.py` so canonical `G_F` rows and checked-in payloads fail without floor/split/depth-bin/forecast-block metadata.
- Updated current manuscript figure specs and captions so the depth-residual figure requires the matched-null forecast report and names the canonical MIO floor/split contract.
- Updated Pack B to reference the canonical `G_F` display contract and forecast-only matched-null report without creating a current-payload hash cycle.
- Added the matched-null forecast report and HTT null-competition code/tests to the statistical-formalism audit package.
- Fixed claim-gate self-review findings by carrying fixture source labels into the JSON and Markdown report, adding regression tests for dirty-provenance display, and stabilizing generated artifacts with the order `current figures -> Pack B -> publication freeze -> current figures -> audit package`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_matched_nulls.py::test_gf_matched_null_forecast_blocks_failed_fpr_without_retuning tests/htt/test_matched_nulls.py::test_gf_matched_null_forecast_pass_still_blocks_observed_claims -q` -> `2 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_matched_nulls.py::test_gf_matched_null_forecast_labels_fixture_source_and_dirty_worktree -q` -> failed before implementation with missing `forecast_source_kind`, then `1 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_formalism_figure_labels.py::test_gf_rows_require_floor_split_and_forecast_block_metadata -q` -> `1 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/src/common/contracts.py htt/htt/htt/infer/null_competition.py htt/htt/htt/infer/__init__.py scripts/verify_formalism_figure_labels.py scripts/make_current_manuscript_figures.py` -> pass
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/make_current_manuscript_figures.py` -> regenerated current figures, manifests, snippets, payloads, and `G_F` forecast report
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/result_packs/generate_pack_B_local_global.py` -> regenerated Pack B
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_statistical_formalism_audit_package.py` -> regenerated audit package and manifest
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_isotropy_gap.py tests/htt/test_matched_nulls.py tests/contracts/test_formalism_figure_labels.py tests/contracts/test_current_manuscript_figures.py tests/result_packs/test_pack_B.py tests/contracts/test_publication_claim_freeze.py -q` -> `64 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider htt/src/common/test_contracts.py htt/src/common/test_ver2_contract_layer.py tests/contracts/test_artifact_manifest.py tests/contracts/test_status_snapshot.py tests/htt/test_local_boost_nulls.py tests/mio/test_mio_evidence_anatomy_no_merge.py tests/htt/test_posterior_pushforward.py -q` -> `75 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json` -> pass
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/result_packs/generate_pack_B_local_global.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/make_current_manuscript_figures.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_statistical_formalism_audit_package.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/htt/test_matched_nulls.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_formalism_figure_labels.py tests/result_packs/test_pack_B.py -q` -> `36 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_artifact_manifests.py --scan-root docs/generated --scan-root figures/current --dry-run` -> 0 manifest issues, 0 quarantined figures
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/audit_manuscript_figures.py --dry-run` -> 118 includegraphics resolved, 0 missing, 0 quarantined; 10 text findings remain manual/status-number findings
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` -> DAG valid
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` -> 62/62 completed, checkpoint due false
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -m smoke -q` -> `6 passed, 7481 deselected`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_claim_language.py --dry-run --format text` -> no forbidden claim language detected; `manuscripts` path skipped because absent
- `git diff --check` -> clean

## Residual Risks

- The matched-null report is a forecast-only deterministic current-code fixture, not observed-data evidence.
- Current null banks remain insufficient for observed-data local/global separation.
- `G_F` mean numerator and denominator deltas are provenance summaries and do not decompose the reported ratio.
- The depth-residual figure still includes current-code noncanonical proxy lanes; the canonical `G_F` contract is exposed in payload metadata and linted, not promoted to family identification.
- Native low-ell morphology atlas, covariance-bound observed matched nulls, PPC, LOOCV, prior sweeps, and family-equivalence gates remain absent.

## Next Candidate

- `REV-R070: Normalize Legacy VER2 Readiness Labels`
