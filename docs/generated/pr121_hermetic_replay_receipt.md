# PR-121 Hermetic Replay Receipt

- owner: `COMMON`
- implementation_scope: `common`
- artifact_mode: `governance_diagnostic`
- allowed_use: `internal_reproducibility_mechanics_only`
- claim_tier: `diagnostic_only`
- transfer_source: `none`
- config_hash: `7e37e757775b02e20d6ed418a7162e6c7d8fe10745c8f49a8ecfaa64aa85cdb5`
- sky_support_status: `not_directional`
- null_mock_status: `not_statistical`
- source_authority_id: `sha256:4fceed77501fd8f155920a0a4938c2633da785abb9468f4f44833641b1105c7d`
- worktree_state: `declared_git_index_bound`
- generated_on: `2000-01-01T00:00:00+00:00`
- generating_command: `venv/bin/python scripts/codex_harness/hermetic_replay.py --write`
- receipt_content_hash: `db8fde00acec732b3779661e023697942b1557be1cbc429030735de0266993bf`
- overall_status: `pass`
- source_tree_hash: `ae905d7df7600c381f5c4484c5577a44a675427827ef7d5fcc24250e559657d9`
- dependency_layer_hash: `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210`

Clean-install/replay success is implementation mechanics only, not scientific validation.

## Input hashes

| path | sha256 | size |
| --- | --- | ---: |
| `docs/codex_handoff/artifact_gate_outputs.yaml` | `66fe6f798fe4e02b7240e7916dced3ab3116b68081775fe96e79c81490674836` | 8448 |
| `docs/codex_handoff/pr_backlog.yaml` | `03ec8869094d65ceda007661949cb0513c42f7620529d4b963190c183a803e71` | 159143 |
| `docs/codex_handoff/pr_status.yaml` | `ea0a59098b064b4daadcfe3df7c370a10db34eb53954eec99b3d92aeb01c63f3` | 42209 |
| `docs/research_program/long_horizon_rescue/pr121_spec.yaml` | `7e37e757775b02e20d6ed418a7162e6c7d8fe10745c8f49a8ecfaa64aa85cdb5` | 8107 |
| `htt/htt/pyproject.toml` | `5df329753ae1306d42643949b06287a51acb60a20cbace9b342e5788f1e25ad5` | 330 |
| `htt/pyproject.toml` | `b62eca1237103fd5ae0bfb083883d11de915c83967ddff1ea07498f4f563e945` | 2371 |
| `scripts/codex_harness/hermetic_replay.py` | `1d2eb42ae8e0b39dbe39cd0ccae17053d8a88d918d613a5faf687b3eecdb44da` | 106940 |
| `tests/pr_cards/test_pr_121_hermetic_install_owner_namespace_detached_replay.py` | `9f1f9faf800d90420db3241025cc6a040583c2795e1216326b8c27d675e554f3` | 37514 |

## Caveats

- Clean install and detached replay success are not scientific validation.
- Distribution ownership does not transfer scientific ownership between COMMON, HTT, MIO, OBSSTAT, BASS, and TSC_LEGACY.
- The teff top-level is packaged only as a TSC_LEGACY compatibility and frozen-reproduction surface; historical TEFF-labelled payload metadata cannot authorize new work.
- Optional dependency absence is an explicit skip or blocker and never a pass.
- No native solver, transfer validation, posterior, evidence, morphology-family, or geometry claim is created.
- Unhashed generated __pycache__ bytecode rows are excluded from the dependency layer; every copied regular RECORD row is hash/size verified.

## Dependency layer seal

- physical_read_only: `True`
- mode_policy: `files=0444_or_0555;directories=0555`
- file_count: `6721`
- directory_count: `695`
- build_guard_unchanged: `True`
- verified_cell_guard_count: `6`

### Phase evidence

| scope | phase | content/mode hash | files | directories | writable |
| --- | --- | --- | ---: | ---: | ---: |
| `receipt` | `receipt:baseline` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `build` | `build:before` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `build` | `build:after` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `direct_main_then_compat` | `direct_main_then_compat:before` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `direct_main_then_compat` | `direct_main_then_compat:after` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `direct_compat_then_main` | `direct_compat_then_main:before` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `direct_compat_then_main` | `direct_compat_then_main:after` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `sdist_main_then_compat` | `sdist_main_then_compat:before` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `sdist_main_then_compat` | `sdist_main_then_compat:after` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `sdist_compat_then_main` | `sdist_compat_then_main:before` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `sdist_compat_then_main` | `sdist_compat_then_main:after` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `editable_main_then_compat` | `editable_main_then_compat:before` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `editable_main_then_compat` | `editable_main_then_compat:after` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `editable_compat_then_main` | `editable_compat_then_main:before` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |
| `editable_compat_then_main` | `editable_compat_then_main:after` | `97cd195062171afc0c30d900ed80c1fa1fb538bfb854f9eb8fd8856381249210` | 6721 | 695 | 0 |

## Installed generator replay

- status: `pass`
- execution_path: `python -I -m common.status_snapshot --write plus installed parser check`
- cell_count: `6`
- structured_hash: `75ca91bc4b7805fae55b9da1cd679afdd87418a05443a2d116f5b9a83009b935`
- fixed_generated_on: `2000-01-01T00:00:00+00:00`
- fixed_source_commit: `PR121_INDEX_SNAPSHOT`
- check.canonical_json_companions: `True`
- check.claim_status_artifact_identity: `True`
- check.cli_module: `common.status_snapshot`
- check.generated_on_normalized_to_policy: `True`
- check.status_matrix_excludes_generated_on: `True`
- check.status_matrix_matches_snapshot: `True`
- check.status_matrix_parser: `validate_status_matrix_matches_snapshot`

## Install matrix

| cell | status | tests executed | tests skipped | structured hash |
| --- | --- | ---: | ---: | --- |
| `direct_main_then_compat` | `pass` | 46 | 0 | `75ca91bc4b7805fae55b9da1cd679afdd87418a05443a2d116f5b9a83009b935` |
| `direct_compat_then_main` | `pass` | 6 | 0 | `75ca91bc4b7805fae55b9da1cd679afdd87418a05443a2d116f5b9a83009b935` |
| `sdist_main_then_compat` | `pass` | 6 | 0 | `75ca91bc4b7805fae55b9da1cd679afdd87418a05443a2d116f5b9a83009b935` |
| `sdist_compat_then_main` | `pass` | 6 | 0 | `75ca91bc4b7805fae55b9da1cd679afdd87418a05443a2d116f5b9a83009b935` |
| `editable_main_then_compat` | `pass` | 6 | 0 | `75ca91bc4b7805fae55b9da1cd679afdd87418a05443a2d116f5b9a83009b935` |
| `editable_compat_then_main` | `pass` | 6 | 0 | `75ca91bc4b7805fae55b9da1cd679afdd87418a05443a2d116f5b9a83009b935` |

## Optional dependencies

- `astropy`: `missing_documented_blocker` (excluded from pass count)
- `camb`: `missing_documented_blocker` (excluded from pass count)
- `dynesty`: `missing_skip` (excluded from pass count)
- `healpy`: `missing_skip` (excluded from pass count)

## PR4 scope firewall

PR4 download, intake, reduction, and analysis were skipped by explicit user scope.
