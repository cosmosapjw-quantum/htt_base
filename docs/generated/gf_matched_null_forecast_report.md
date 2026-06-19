# G_F Matched-Null Forecast Report

owner: HTT
implementation_scope: htt
claim_tier: blocked
artifact_mode: forecast_only
allowed_use: external_audit
transfer_source: none
sky_support_status: not_directional
null_mock_status: forecast_matched_null_blocked
config_hash: sha256:629ff58959ab40d41a9329fcc951774082c987e871d986cf37b649dc19c86353
input_hashes:
- sha256:ab84fb754a284b1a7eaf9cc0ee6793f691dfc1bcbf03b4c8243d9aa279bad974
- sha256:bf1cccdc07a712c5032b6f7bc9b6d483795dcf0e52b757d311bc646a4e823a58
- sha256:629ff58959ab40d41a9329fcc951774082c987e871d986cf37b649dc19c86353
caveats:
- Forecast-only matched-null diagnostic.
- Does not promote observed-data evidence, global-tilt wording, native solver validation, geometry detection, or family identification.
generating_command: python scripts/make_current_manuscript_figures.py
git_commit_or_worktree_state: 3225e56+dirty
artifact_path: docs/generated/gf_matched_null_forecast_report.json

## Status

- matched_null_status: `forecast_matched_null_blocked`
- local_global_separation_status: `blocked_existing_null_bank_insufficient`
- observed_data_evidence: `False`
- global_tilt_wording_allowed: `False`
- retuning_after_failure: `False`
- forecast_source_kind: `deterministic_current_code_fixture`
- forecast_source_description: Deterministic current-code synthetic demonstration fixture; not production mocks and not observed-data evidence.
- FPR statement: 91/192 forecast false-positive crossings; Wilson upper bound 0.510035 at z=1.
