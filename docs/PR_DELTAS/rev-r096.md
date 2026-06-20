# REV-R096 - Gate Prior Error Sensitivity

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R096 gate prior error sensitivity`
git_commit_or_worktree_state: pending_rev_r096_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 9)
- `scripts/make_current_manuscript_figures.py`
- `scripts/generate_revision_experiment_assets.py`
- `figures/current/fig_revision_prior_support_surface.manifest.json`,
  `fig_revision_sigma_beta_band.manifest.json`
- Web/literature: arXiv 0803.4089 supports prior sensitivity in Bayesian
  evidence; a sign flip across the prior grid blocks a single Jeffreys label.

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 9: replace proxy prior-support surfaces with an explicit
prior/error sensitivity gate record, and keep the prior-support and sigma-beta
figures display-only.

## Role Split

- Physics/statistics auditor steelman: ln B swings from +26.40 to -39.1 across
  the prior-floor grid, a sign flip; no single Jeffreys evidence label is
  admissible, and the rows are display proxies, not marginal-likelihood runs.
- Harness engineer steelman: pin the gate with a contract test on sign flips and
  the proxy-vs-marginal distinction; record boundary-mass and KL status as
  explicit placeholders.
- Claim-gate reviewer steelman: the figure manifests must stay display-only and
  point at the gate record.

## Changes

- `htt/htt/htt/infer/prior_error_sensitivity.py`: new module with
  `summarize_prior_error_grid(...)`. Detects sign flips across the
  prior/ceiling/sigma_beta grid, blocks `single_jeffreys_label_allowed` when a
  sign flip is present or the rows are display proxies, and reports robust range
  plus boundary-mass/KL placeholder status. `main()` writes the audited report.
- `docs/generated/prior_error_sensitivity_report.{json,md}`: the audited grid
  (sign flip -> blocked).
- `scripts/make_current_manuscript_figures.py`: the departure display contract
  now records the `prior_error_sensitivity` gate payload.
- `scripts/generate_revision_experiment_assets.py`: the prior-support and
  sigma-beta figure specs now carry display-only schematic caveats pointing at
  the gate record.
- Regenerated the current science payload, revision assets, and dependent
  surfaces. No figure PNG changed (manifests/caveats only).
- Test: `tests/htt/test_prior_error_sensitivity.py`.

## Artifact Metadata

- owner: HTT
- implementation_scope: htt
- claim_tier: blocked
- config_hash:
  - `htt/htt/htt/infer/prior_error_sensitivity.py:sha256:08cab3cf285364bf5f7b545f53c0742831ef628cee86f1db5d5912f1b5d92736`
  - `scripts/make_current_manuscript_figures.py:sha256:08b7d0e550f1eab6f30e99101980a5ed62379d4fa0484896b73231b6874a3cf1`
- input_hashes:
  - `scripts/generate_revision_experiment_assets.py:sha256:f660c313da8834bceee6bb7ec6f440575863240c22738d149f5e7cf2d53f19f1`
  - `docs/generated/prior_error_sensitivity_report.json:sha256:f140044d69c77bdf0da25ce81d94bf4938a6afb7ab64170360a9843d94cc175f`
  - `tests/htt/test_prior_error_sensitivity.py:sha256:4fbec5f15defa6e3760a8db1253f4f4675ed87d7af56d206df491194391cf37f`
  - `docs/generated/current_science_plot_payload.json:sha256:1204b955a23caafd66eb867194f0a9bc57a52c5e5e7dc23db35163d3c23ada1c`
- caveats:
  - boundary-mass and KL diagnostics are explicit placeholders, not computed;
  - the prior/error rows are display proxies, not marginal-likelihood runs;
  - no native low-ell solver output is introduced.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/htt/test_prior_error_sensitivity.py -q` initially failed with `ModuleNotFoundError`.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B htt/htt/htt/infer/prior_error_sensitivity.py` | PASS | Wrote the audited prior/error sensitivity report. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_current_manuscript_figures.py --check` | PASS | `current manuscript figure artifacts are current`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_revision_experiment_assets.py --check` | PASS | `revision experiment assets pass check`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_prior_error_sensitivity.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_revision_experiment_assets.py` | PASS | `15 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...module... report.md` | PASS | `No forbidden claim language detected.` |
