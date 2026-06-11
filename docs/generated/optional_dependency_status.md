# Optional Dependency Status

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `7c80fe1aec4824e64a5c5ac056a31d585906636a5176ed01b4bd384d061241b3`
input_hashes:
- scripts/codex_harness/optional_dep_report.py: `7432803668a5581df98efa8cf48ae243c43800b0724fa16029106c1ae8f30696`
- htt/src/common/optional_dependencies.py: `a830d85d5cec24473537caf0d4f57a7a432a69fa97aee59e620cdc9d590a4fd0`
- htt/conftest.py: `8095c409f76fd063ce54e69063291a56d199575367235384ba994d0029da6fac`
- pytest.ini: `a3f9fc9415c7eef1e0031c8b37b2201d8c78d0ec414a0d0227763e099d25fce4`
- htt/pytest.ini: `cf5111aad6bad6cc2de26951c0fefa36fbcc2aa85edc2dd994661d898b57edc3`
- htt/pyproject.toml: `016b0c1373f3482fdf7bb5aec5f1635b47c7e34e5d7018f8177b895d6ddf9f4d`
caveats:
- Machine-local availability records harness provenance only.
- Missing optional dependencies are skip causes or documented blockers, not passes.
- This report is not scientific readiness evidence.
generating_command: python scripts/codex_harness/optional_dep_report.py
python_executable: /usr/bin/python
git_commit: 26d0e55
worktree_state: dirty

## Dependency Registry

| key | import | status | policy | pytest marker | owner | attribution | explanation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| healpy | healpy | available | skip | requires_healpy | BASS | htt/bass/forward/test_map_producer.py | installed in the current Python environment |
| dynesty | dynesty | missing_skip | skip | requires_dynesty | HTT | htt/bass/inference/test_fb113_bayes_factor_skeleton.py | optional dependency 'dynesty' not installed; install it to run tests marked requires_dynesty |
| astropy | astropy | available | documented_blocker | none | COMMON | dl_pipeline/scripts/dl_fits_utils.py<br>dl_pipeline/scripts/extract_htt_data.py | installed in the current Python environment |
| camb | camb | available | documented_blocker | none | BASS | htt/bass/spectrum/test_flrw_external_camb.py<br>htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py | installed in the current Python environment |

## Skip Attribution

- `requires_healpy` maps to `healpy` through the COMMON optional dependency registry.
- `requires_dynesty` maps to `dynesty` through the COMMON optional dependency registry.
- Registered skip markers use dependency-named reasons during pytest collection.
- Existing `pytest.importorskip` gates remain the local test-level attribution for optional modules.
