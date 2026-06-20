# REV-R080: add observational data binding contracts

owner: COMMON
implementation_scope: data_readiness_contracts
claim_tier: diagnostic_only
transfer_source: mixed_none_and_external_reference
config_hash: sha256:68848e33466617d73386e6abe514b1f24ebb0c68fc5e33d8bf9c0f04d8af53f7
sky_support_status: mixed_not_directional_and_catalog_recorded
null_mock_status: not_statistical
generating_command: `venv/bin/python scripts/inventory_observational_data.py --write`
git_commit_or_worktree_state: pending_rev_r080_commit
caveats:
- COMMON data-readiness contract PR only.
- D0/D1 rows are diagnostic-only data bindings, not analysis-ready evidence.
- Present compact DESI/CF4 data do not satisfy spectroscopic production or matched-mock promotion gates.
- No HTT posterior, MIO certificate, native solver validation, or Bianchi family-identification claim is created.

## Input Hashes

- `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`: `sha256:c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a`
- `.gitignore`: `sha256:fffde9ca036c7a416357878582b5d70b46dfa4aecb311f3384f3b01d1f5fac3b`
- `htt/src/common/data_contracts.py`: `sha256:c327270cbcf9e15e130fc3ad4cc3c86b14a72efb295a1a7018f9718d77faef08`
- `scripts/inventory_observational_data.py`: `sha256:9d88d150e13239900fb16c06b1af0c768b5b7eb1da5f9c099d73f68e62e132d0`
- `scripts/make_observed_data_manuscript_figures.py`: `sha256:f64c6903aa2e59bf11dff076470c2b3ddf93441fca15241800dda0fe012935a6`
- `tests/contracts/test_data_contracts.py`: `sha256:092d02b3bd841eedeee329ad2c12d9cf306fca8ebe8da2d328a8da76ba23f04a`
- `tests/contracts/test_observed_data_figures.py`: `sha256:f7a935048b69ab183bb9b6a7b5153af720deab48d6d83feb0eb939115273b899`
- `htt/test_packaging_imports.py`: `sha256:1ba2f82451c679826597c2a02298310605d822c00282ebe2938f4cd48bfdb416`
- `docs/generated/observational_data_inventory.json`: `sha256:025b666eb5813b3397eef285f9feef68283d54bc328b7756ada03f62f462e328`
- `docs/generated/observational_data_inventory.md`: `sha256:4c73e8b01af9c8aa690341fb7dab9852304ec8407c262286172f3f55d23a19c3`
- `docs/generated/data_binding_gap_report.md`: `sha256:618ef519e6ef3d00a81261846c01395af6e7baf41ce743055708c1a606ac2c94`
- `docs/generated/observed_current_plot_list.md`: `sha256:940927ce616ae28c60f36daba3a9b54760bae398367dc80aaf3c204a3aea994d`
- `docs/generated/revision_experiment_assets.json`: `sha256:7091d112392857cb2ba848d6601b685afdc4fb873cfe6ab569cc07a39aa42280`
- `docs/generated/revision_experiment_assets.md`: `sha256:99817e25ab62f60ee4cd6e2e6ea704285b93ded74f8f4528168c7c903685c7ee`
- `docs/generated/cf4pp_lnb_provenance_report.json`: `sha256:ed2592a8ed3bd6e8991879a9da5c017d906ea1b11ad6321a3a43f40570b3dcad`
- `docs/generated/cf4pp_lnb_provenance_report.md`: `sha256:4873dc4e0bd8f959af561e7c89290a56581afc19916d7c55d31cda21527313d4`

## Evidence Gathering

- Read Task 7 of `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`.
- Read `scripts/inventory_observational_data.py`, `tests/contracts/test_observed_data_figures.py`, `htt/src/common/contracts.py`, `htt/src/common/artifact_manifest.py`, and `htt/test_packaging_imports.py`.
- Web/docs check: verified Python stdlib `dataclasses`, `enum.StrEnum`, and `hashlib.sha256` behavior from official Python docs:
  - https://docs.python.org/3/library/dataclasses.html
  - https://docs.python.org/3/library/enum.html#enum.StrEnum
  - https://docs.python.org/3/library/hashlib.html#hashlib.sha256

## Divergence And Selection

- Code cartographer steelman: keep data readiness in `common.data_contracts` and wire inventory rows to it. Attack: do not put cross-survey data-binding policy under OBSSTAT feature extraction.
- Harness engineer steelman: add importable contracts plus generated inventory/gap `--check`. Attack: do not leave output metadata path-dependent or generated reports out of sync.
- Physics/statistics auditor steelman: D0/D1 are useful pre-analysis bindings. Attack: present catalog rows, row counts, direction vectors, or weights must not imply spectroscopic production readiness.
- Claim-gate reviewer steelman: use data-readiness/gap-status wording. Attack: avoid validation/evidence/native/family wording except as negated caveats.
- Regression tester steelman: focused contract, inventory, artifact-manifest, adjacent generated-asset, and packaging tests cover the PR. Attack: audit-package and manuscript-PDF refresh are later package/report PRs.

## Changes

- Added `common.data_contracts` with canonical data roles, allowed-use lanes, D0/D1/D2/D3 readiness levels, frozen `SurveySupport`, fail-closed readiness decisions, and support-parity blockers.
- Hardened D2/D3 semantics with explicit allowlists for selection certification, covariance/null mock status, support parity, companion checksums, provenance refs, and HTT rank/PPC/LOOCV gate refs.
- Updated observational inventory rows with canonical data role, preserved legacy role, survey support metadata, readiness decisions, allowed use, binding gap reasons, spectroscopic blockers, and matched-mock promotion blockers.
- Added path-aware `--write` and deterministic `--check` behavior to `scripts/inventory_observational_data.py`, including absolute-output smoke coverage.
- Generated `docs/generated/data_binding_gap_report.md` with owner/scope/tier/transfer/config/input hashes/caveats/command/git state.
- Updated `scripts/make_observed_data_manuscript_figures.py` so observed-figure regeneration writes the inventory JSON, inventory Markdown, and gap report together.
- Refreshed observed figure manifests/plot lists, revision experiment assets, and CF4++ provenance reports to consume the new inventory hash.
- Added `common.data_contracts` to package import-surface tests.
- Ignored root-level external audit/revision input drops whose curated copies already live under `docs/audits/`.

## Review Loop

- Loop 1 subagents returned concrete blockers across harness, physics/statistics, claim gate, regression, and cartography; all must-fix findings were patched.
- Loop 2 subagents were spawned but errored due account usage limits before returning findings. Completed the loop locally with the same five review roles and recorded this tool-capacity fallback instead of opening more threads.
- Local `/review` residual risk accepted: audit-package and manuscript-PDF manifests still need a downstream refresh PR, not this data-binding contract PR.

## Verification

- `venv/bin/python -B -m py_compile htt/src/common/data_contracts.py scripts/inventory_observational_data.py scripts/make_observed_data_manuscript_figures.py scripts/generate_revision_experiment_assets.py scripts/reproduce_cf4pp_lnb.py tests/contracts/test_data_contracts.py tests/contracts/test_observed_data_figures.py htt/test_packaging_imports.py`
  - result: passed.
- `venv/bin/python -B scripts/inventory_observational_data.py --write`
  - result: regenerated observational inventory JSON/Markdown and data-binding gap report.
- `venv/bin/python -B scripts/inventory_observational_data.py --check`
  - result: observational data inventory outputs pass check.
- `tmpdir=$(mktemp -d); venv/bin/python -B scripts/inventory_observational_data.py --write --output-json "$tmpdir/inventory.json" --output-md "$tmpdir/inventory.md" --gap-md "$tmpdir/gap.md"; venv/bin/python -B scripts/inventory_observational_data.py --check --output-json "$tmpdir/inventory.json" --output-md "$tmpdir/inventory.md" --gap-md "$tmpdir/gap.md"`
  - result: absolute-output write/check passed.
- `venv/bin/python -B scripts/make_observed_data_manuscript_figures.py`
  - result: regenerated 11 observed-current figures and plot indices.
- `venv/bin/python -B scripts/generate_revision_experiment_assets.py --write`
  - result: refreshed revision experiment assets and five revision figure manifests.
- `venv/bin/python -B scripts/generate_revision_experiment_assets.py --check`
  - result: revision experiment assets pass check.
- `venv/bin/python -B scripts/reproduce_cf4pp_lnb.py --write && venv/bin/python -B scripts/reproduce_cf4pp_lnb.py --check`
  - result: CF4++ lnB provenance report is current.
- `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_data_contracts.py tests/contracts/test_observed_data_figures.py tests/contracts/test_artifact_manifest.py tests/contracts/test_revision_experiment_assets.py tests/contracts/test_audit_package_generator.py htt/test_packaging_imports.py`
  - result: 56 passed.
- `venv/bin/python -B scripts/check_claim_language.py --dry-run ...`
  - result: no forbidden claim language detected.
- `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml`
  - result: OK, 62 PRs DAG valid.
- `git diff --check`
  - result: passed.
- Stale-hash search for previous observational inventory hashes under generated figure/provenance outputs, excluding audit-package and manuscript-PDF package manifests.
  - result: no matches.

## Current Generated Summary

- Dataset candidates: 52.
- Present: 40.
- Missing: 12.
- Data readiness counts: D0=15, D1=25, blocked=12.
- Canonical data roles: raw_catalog=15, harmonic_product=32, map=2, mask=2, covariance=1.
- Rows with binding gaps: 23.
- Spectroscopic dipole blocked rows: 12.

## Known Residuals

- D2/D3 promotion still requires future matched random/mask, covariance, null/mock, rank, PPC, and LOOCV artifacts. This PR records blockers and does not synthesize those artifacts.
- Research-only audit package, general external-audit package, and manuscript-PDF manifests remain stale after generated report changes and are expected to be refreshed in the downstream packaging/report PR.
