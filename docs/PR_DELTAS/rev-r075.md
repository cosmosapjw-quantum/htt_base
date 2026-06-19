# REV-R075: repair manuscript audit findings

owner: COMMON
implementation_scope: manuscript_audit_repair
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
config_hash: sha256:manual-rev-r075
input_hashes:
- docs/audits/external_research_inputs_2026-06-20/RESEARCH_AUDIT_REPORT.md
- docs/generated/manuscript_audit_repair_matrix.md
- docs/manuscript/ch01_introduction.tex
- docs/manuscript/ch02_dipole_anomaly.tex
- docs/manuscript/ch03_framework.tex
- docs/manuscript/ch05_teff_corrections.tex
- docs/manuscript/ch07_results.tex
- docs/manuscript/ch08_robustness.tex
- docs/manuscript/ch09_discussion.tex
sky_support_status: mixed_not_applicable_and_manifest_bound
null_mock_status: mixed_blocked_and_not_applicable
generating_command: manual manuscript repair plus pytest/claim checks
git_commit_or_worktree_state: pending_rev_r075_commit
caveats:
- not native transfer
- no family identification
- no geometry-detection claim
- CF4++ and Watkins sensitivity values remain quarantined until rerun with bound inputs
- HTT posterior exceedance is not MIO diagnostic exceedance

## Intent

Close the immediate external manuscript-audit findings from
`RESEARCH_AUDIT_REPORT.md` without promoting any legacy
transfer-dependent result beyond its current claim lane.

## Changes

- Reconciled the intro/dipole-anomaly departure-number prose by splitting
  the legacy HTT posterior mean `Q` summary from the S3 filling-fraction
  `FF` values.
- Renamed the manuscript posterior exceedance curve to `Pi_HTT` and
  distinguished it from the empirical MIO diagnostic exceedance curve
  `Pi_MIO`.
- Replaced no-FLRW-limit Bayes-factor table entries with
  `N/A (no FLRW limit)`.
- Downgraded growing-mode wording from detection language to sensitivity
  language.
- Quarantined CF4++ and Watkins sensitivity `ln B` values as non-canonical
  and pending dedicated rerun with bound config/input hashes.
- Downgraded neutrino dominance wording from discovery/solver-validation
  language to legacy external/proxy transfer-path contribution bookkeeping.
- Added `docs/generated/manuscript_audit_repair_matrix.md` and
  `tests/contracts/test_manuscript_audit_repair_matrix.py`.

## Subagent Review

- Code cartographer mapped the audit findings to manuscript, generated,
  and existing lint/check harness surfaces.
- Harness engineer steelmanned the focused repair-matrix test, then
  attacked brittle global text bans; the final test uses local quarantine
  checks and targeted blocked phrase regressions.
- Claim-gate reviewer found and verified fixes for Watkins `+106` quarantine
  and test coverage gaps.
- Physics/statistics auditor found and verified fixes for remaining solver
  validation wording in Chapter 5 and Chapter 9.
- Regression tester identified the broader manuscript/figure/formalism suite
  used below.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/contracts/test_manuscript_audit_repair_matrix.py`
  - result: `6 passed`
- `venv/bin/python scripts/check_claim_language.py docs/generated/manuscript_audit_repair_matrix.md docs/manuscript/ch01_introduction.tex docs/manuscript/ch02_dipole_anomaly.tex docs/manuscript/ch03_framework.tex docs/manuscript/ch05_teff_corrections.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/manuscript/ch09_discussion.tex`
  - result: `No forbidden claim language detected.`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/contracts/test_manuscript_audit_repair_matrix.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_publication_claim_freeze.py tests/contracts/test_manuscript_figure_audit.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_expanded_manuscript_figure_suite.py tests/contracts/test_observed_data_figures.py tests/contracts/test_formalism_figure_labels.py`
  - result: `52 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/pdf_claim_lint.py --check`
  - result: up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py --check`
  - result: up-to-date
- `git diff --check`
  - result: pass

## Residual Risk

The compiled PDF and PDF claim-lint report are still based on the last
manuscript PDF build. The source-level repair is covered here; a later
manuscript/PDF refresh PR should rebuild the PDF and refresh PDF-derived
reports before external redistribution.
