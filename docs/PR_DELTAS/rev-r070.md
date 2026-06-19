# REV-R070 Delta: Legacy VER2 Readiness Normalization

owner: COMMON
implementation_scope: formalism_audit_revision
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: mixed_not_directional_and_pending_directional_support
null_mock_status: mixed_diagnostic_unmatched_forecast_and_not_applicable
generating_command: manual Codex REV-R070 implementation
git_commit_or_worktree_state: 3225e56+dirty before REV-R070 commit

## Evidence Read

- `docs/superpowers/plans/2026-06-19-formalism-audit-originality-program.md`
- `docs/PR_DELTAS/rev-r069.md`
- `scripts/ver2_artifact_export.py`
- `scripts/result_packs/generate_pack_A_scalar_to_morphology.py`
- `scripts/result_packs/generate_pack_B_local_global.py`
- `scripts/result_packs/generate_pack_C_mio_certificates.py`
- `scripts/build_external_audit_package.py`
- `scripts/build_research_only_audit_package.py`
- `scripts/build_statistical_formalism_audit_package.py`
- `scripts/check_publication_claim_freeze.py`
- `scripts/make_current_manuscript_figures.py`
- `scripts/test_ver2_artifact_export.py`
- `tests/result_packs/test_pack_A.py`
- `tests/result_packs/test_pack_B.py`
- `tests/result_packs/test_pack_C.py`
- `tests/contracts/test_audit_package_generator.py`
- `tests/contracts/test_statistical_formalism_audit_package.py`
- Official Python `json`, `pathlib`, and `argparse` documentation was checked before relying on stdlib JSON ordering/serialization, path-relative handling, and CLI mode behavior.

## Role Synthesis

- Code cartographer: raw legacy readiness labels entered current public outputs through `ver2_artifact_export.py` and the newer Pack A/B/C generators that quote VER2 JSON; package builders only copied those reports.
- Harness engineer: add regression tests at the generator and zip-content layers, because a figure-manifest-only guard misses report text and audit-package payloads.
- Physics/statistics auditor: legacy readiness is provenance, not validation; current public surfaces must not imply native morphology atlas support, HTT evidence, MIO posterior semantics, or family identification.
- Claim-gate reviewer: expose `diagnostic_only`, `legacy_not_current`, and `native_morphology_atlas_status=unavailable_pre_native_solver` on public surfaces; preserve historical context only as prior-context references.
- Regression tester: use the actual MIO test path `htt/mio/tests/test_ver2_manifest_status.py`, and separate broad audit-package freshness from targeted VER2 readiness normalization.

## Changes

- Added a public-readiness sanitizer in `scripts/ver2_artifact_export.py`.
- VER2 artifact records now normalize public/generated manifests and payloads to `diagnostic_only`, `legacy_not_current`, and `native_morphology_atlas_status=unavailable_pre_native_solver`.
- The sanitizer is idempotent for already-normalized generated manifests, so `scripts/ver2_artifact_export.py --check` stabilizes after regeneration.
- VER2 result-pack index, pack Markdown/TeX, gallery maps, figure manifests, and artifact JSON now use current-public readiness language instead of stale legacy promotion labels.
- Pack A/B/C legacy VER2 context loaders now expose current public readiness and legacy readiness status rather than raw source gate labels.
- Pack C renamed public readiness scenario fields and certificate tables away from production-grade language.
- Added report-content regression tests for full external-audit and statistical-formalism audit zips.
- Added full-archive allowlist tests for full external, research-only, and statistical-formalism audit packages so stale readiness vocabulary is allowed only inside historical PR/status namespaces or explicit false status-schema fields.
- Added package README caveats explaining that archived PR/status records may preserve historical readiness vocabulary as provenance while current result reports use diagnostic-only public readiness and legacy-not-current caveats.
- Updated `docs/generated/formalism_audit_originality_response_matrix.md` row A6 to mark this finding implemented/test-covered.
- Regenerated VER2 generated artifacts, Pack A/B/C, current manuscript payloads, publication claim freeze, full external audit package, research-only audit package, and statistical-formalism audit package.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider scripts/test_ver2_artifact_export.py::test_public_ver2_text_outputs_normalize_legacy_readiness_labels scripts/test_ver2_artifact_export.py::test_ver2_pack_payload_carries_legacy_not_current_readiness tests/result_packs/test_pack_A.py::test_pack_a_payload_compares_scalar_and_morphology_surfaces tests/result_packs/test_pack_A.py::test_pack_a_markdown_has_manifest_and_caveated_comparison tests/result_packs/test_pack_B.py::test_pack_b_payload_includes_required_surfaces_and_manifest tests/result_packs/test_pack_B.py::test_pack_b_markdown_is_conditional_at_most_and_caveated tests/result_packs/test_pack_C.py::test_pack_c_status_scenarios_make_diagnostic_and_production_grade_explicit tests/result_packs/test_pack_C.py::test_pack_c_markdown_lists_statuses_caveats_and_no_ranking tests/contracts/test_audit_package_generator.py::test_packaged_result_reports_do_not_surface_legacy_readiness_tokens tests/contracts/test_statistical_formalism_audit_package.py::test_statistical_formalism_package_reports_normalize_legacy_readiness -q` -> failed before implementation with 10 expected stale-label failures; passed after implementation with `10 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile scripts/ver2_artifact_export.py scripts/result_packs/generate_pack_A_scalar_to_morphology.py scripts/result_packs/generate_pack_B_local_global.py scripts/result_packs/generate_pack_C_mio_certificates.py` -> pass
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/ver2_artifact_export.py` -> regenerated 45 files; 5 figure bases scanned; 5 manifest-ready figures
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/ver2_artifact_export.py --check` -> initially failed on artifact-manifest hash drift; fixed sanitizer idempotence; final run reports up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/result_packs/generate_pack_A_scalar_to_morphology.py` -> regenerated Pack A
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/result_packs/generate_pack_B_local_global.py` -> regenerated Pack B
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/result_packs/generate_pack_C_mio_certificates.py` -> regenerated Pack C
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/make_current_manuscript_figures.py` -> regenerated current payload, figures, snippets, and current plot list after result-pack and claim-freeze updates
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py` -> regenerated publication claim freeze and hostile review response matrix
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_external_audit_package.py` -> regenerated full external audit zip and manifest
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_research_only_audit_package.py` -> regenerated research-only audit zip, manifest, and prompt
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_statistical_formalism_audit_package.py` -> regenerated statistical-formalism audit zip, manifest, prompt, and readiness checklist
- Final regression reviewer found a policy gap: audit zips still contained historical/status vocabulary in archived PR deltas and status ledgers. This was not current-report leakage, but the allowlist was implicit.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_audit_package_generator.py::test_full_audit_package_legacy_readiness_tokens_are_archival_only tests/contracts/test_research_only_audit_package.py::test_research_only_package_legacy_readiness_tokens_are_archival_only tests/contracts/test_statistical_formalism_audit_package.py::test_statistical_formalism_legacy_readiness_tokens_are_archival_only -q` -> `3 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider scripts/test_ver2_artifact_export.py tests/result_packs/test_pack_A.py tests/result_packs/test_pack_B.py tests/result_packs/test_pack_C.py tests/contracts/test_audit_package_generator.py tests/contracts/test_research_only_audit_package.py tests/contracts/test_statistical_formalism_audit_package.py htt/mio/tests/test_ver2_manifest_status.py -q` -> `64 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/make_current_manuscript_figures.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_external_audit_package.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_research_only_audit_package.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_statistical_formalism_audit_package.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -m smoke -q` -> `6 passed, 7490 deselected`
- `rg -n -S "atlas_available\s*[:=]\s*true|atlas_available.*true|atlas_ready|production-grade|production grade|production_candidate|public_grade=production-grade" docs/ver2_upgrade/generated docs/generated figures/paper/ver2_generated docs/manuscript/generated` -> no matches
- Full zip token probe with explicit archival/status allowlist -> zero offenders; remaining allowed hits are archived PR deltas, status/backlog files, and `production_validated` false-schema fields.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_claim_language.py --dry-run --format text` -> no forbidden claim language detected; `manuscripts` path skipped because absent
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` -> DAG valid
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` -> 62/62 completed, checkpoint due false
- `git diff --check` -> clean

## Residual Risks

- Raw historical readiness labels still exist in internal code paths, archived PR deltas, and status ledgers where they define history or schema fields; REV-R070 blocks current report/manuscript/generated leakage and documents the archive allowlist.
- Current VER2 and Pack A/B/C readiness is diagnostic public packaging status, not native solver validation.
- MIO certificates remain diagnostic reports, not truth certificates, posteriors, or model-ranking outputs.
- No native low-ell morphology atlas, matched observed null/covariance stack, PPC, LOOCV, or family-equivalence gate was added.

## Next Candidate

- `REV-R071: Reframe Manuscript as Methods/Framework Contribution`
