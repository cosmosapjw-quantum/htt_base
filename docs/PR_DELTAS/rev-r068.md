# REV-R068 Delta: Comparator-Multiverse and Pi Policy Reporting

owner: COMMON
implementation_scope: formalism_audit_revision
claim_tier: diagnostic_only
transfer_source: mixed_none_and_external_transfer_conditioned
sky_support_status: mixed_not_directional_and_diagnostic_sky_support
null_mock_status: mixed_not_statistical_and_current_code_diagnostic_null_banks
generating_command: manual Codex REV-R068 implementation
git_commit_or_worktree_state: 8706cdd+dirty before REV-R068 commit

## Evidence Read

- `htt/mio/formalism/normalized_score.py`
- `htt/mio/formalism/exceedance.py`
- `scripts/make_current_manuscript_figures.py`
- `scripts/verify_formalism_figure_labels.py`
- `tests/mio/test_normalized_score.py`
- `tests/mio/test_exceedance.py`
- `tests/contracts/test_formalism_figure_labels.py`
- `docs/generated/formalism_audit_originality_response_matrix.md`
- Official Python dataclasses/argparse docs and pytest parametrization docs were checked for current API behavior.

## Role Synthesis

- Code cartographer: primary production path is `scripts/make_current_manuscript_figures.py`; canonical Q/Pi contracts already existed but lacked display-level comparator/Pi policy metadata.
- Harness engineer: add RED tests in MIO unit tests and figure-label contracts before implementation; verify checked-in generated payload, not constructors only.
- Physics/statistics auditor: comparator spread is specification-curve sensitivity only, not uncertainty, evidence, family rank, or geometry support; Pi is exceedance metadata, not a p-value.
- Claim-gate reviewer: keep proxy lanes relabeled; do not label external transfer as native or promote scalar `x/Q/Pi/F/G_F` to family identification.
- Regression tester: run focused MIO, contract, claim-language, figure, package, and manifest gates after regeneration.

## Changes

- Added `NormalizedScore.display_metadata` and `ComparatorMultiverseSummary`.
- Added `ExceedanceCurve.look_elsewhere_trials`, `threshold_registration_status`, and `display_metadata`.
- Extended `scripts/verify_formalism_figure_labels.py` so `x/Q` rows require comparator display metadata and canonical `Pi` rows require measure-kind, threshold, and look-elsewhere metadata.
- Extended the verifier to dereference `transfer_sensitivity.q_comparator_multiverse`, compare Q row metadata against the summary, validate the noncanonical `Pi_policy_display_contract`, and enforce `Q-spread` as comparator specification-curve sensitivity.
- Regenerated `docs/generated/current_science_plot_payload.json`, current manuscript figure sidecars/snippets, and `docs/generated/current_manuscript_plot_list.md`.
- Regenerated `docs/generated/statistical_formalism_audit_package.zip` and manifest.
- Updated `docs/generated/formalism_audit_originality_response_matrix.md` and the REV-R068 plan checkboxes.
- Removed the schema-only `atlas_quantile` numeric denominator row from current transfer-sensitivity plotting.
- Added `scripts/make_current_manuscript_figures.py --check` as a generated-artifact freshness gate.
- Down-labeled the generated Pi material to `Pi_policy_display_contract` / `noncanonical_pi_policy_metadata_summary`; no canonical Pi curve is exported in the current semantic split.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_normalized_score.py -q` -> `14 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_exceedance.py -q` -> `18 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/mio/test_normalized_score.py tests/mio/test_exceedance.py tests/contracts/test_formalism_figure_labels.py -q` -> `41 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json` -> pass
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_claim_language.py --dry-run --format text ...` -> no forbidden claim language detected
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_claim_language_lint.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_statistical_formalism_audit_package.py -q` -> `20 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_statistical_formalism_audit_package.py --check` failed before regeneration with stale manifest, then package was regenerated.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/make_current_manuscript_figures.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/generate_semantic_firewall_fuzz_report.py --check` -> current after regeneration
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/build_statistical_formalism_audit_package.py --check` -> up-to-date after regeneration
- `git diff --check` -> clean

## Residual Risks

- Archived external verifier still treats absent canonical `Pi/F/G_F` rows as mismatches; current production policy accepts relabeled proxy lanes until true formal rows are plotted.
- Comparator spread is diagnostic specification-curve sensitivity only.
- Pi policy summary is noncanonical curve-policy/sample-distribution metadata and is not a calibrated p-value or HTT inference input.
- Comparator spread is generated from explicit current-code comparator-conditioned samples, not native morphology atlas support.
- Native low-ell morphology atlas and family-equivalence gates remain absent.

## Next Candidate

- `REV-R069: G_F Floor, Denominator Split, and Matched-Null Forecast Path`
