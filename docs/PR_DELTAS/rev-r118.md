# REV-R118 - Comprehensive report expansion + external-audit zip expansion (PR07)

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_observed_and_external_transfer_conditional
generating_command: `latexmk final_report/main.tex + build_pr04_research_audit_package.py + build_final_report_audit_package.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Expand the self-contained research report and the external-audit zip to
comprehensively cover **all** research results obtained in the repo so far
(including the PR07 audit-repair programme). Compile the report to PDF and verify.

## Changes

### Report (`docs/final_report/main.tex`, 14 -> 16 pages)
- Abstract: now names the external adversarial-audit hardening — theorem
  restatements under exact hypotheses, the independent chain-rule dynamics
  verifier, and the synthetic estimator-mechanics validations + xAct cross-check.
- PAPER-A: added the three PR07-004-closed theorems (A-radial-novortex no-go,
  A-shell-degeneracy rank 3 vs 6, A-temporal-rank `5·rank(T)`) with their gates.
- New paragraphs: **Independent dynamics verification** (1000-state conservation
  5.7e-14 / 5.1e-14; Gauss/Codazzi transport 5.6e-17 / 0; DOP853/Radau exact-dust
  9.6e-13 / 3.2e-14; RK4 4th-order) and **Symbolic and chain-of-verification gate
  surface** (Wolfram all-true, xAct 1.3.0; CoVe 13/13).
- New section **Synthetic estimator-mechanics validations**: K5 hierarchical
  coverage (0.51 -> 0.67 worst component; bias 15.0 -> 1.9 km/s; sigma_star 142.7),
  K6 curl-suppression no-go (projected vorticity 7.5e-17), K1 max-scan
  calibration (global p 0.0070 >= min-local 0.0015), plus a summary table.
- Standing blocks: added the PR08/PR10 registered blockers
  (BLOCKED_MISSING_PR4_E2E_ACCESS, _RELEASE_MOCK_OWNERSHIP, _FIELD_REALIZATIONS,
  AWAITING_NATIVE_LOWELL_SOLVER).
- Reproducibility: added the PR07 gate/symbolic/CoVe commands + the
  `docs/research_program/pr07/` registry pointer.

### External-audit packages
- `scripts/build_pr04_research_audit_package.py` (research surface): +PR07 symbolic/
  CoVe/capability records, +PR07 synthetic-mechanics jsons, +`paper_a_closure`/
  `verification`/`lowell_global_calibration` modules, +PR07 drivers + `wolfram/*.wls`,
  +`docs/research_program/pr07/` programme docs + blocked tickets, +PR07 gate
  tests, deltas r108..r117. **87 -> 126 entries** (~1.67 MB). README/prompt updated
  to PR04+LR-06+PR07.
- `scripts/build_final_report_audit_package.py`: +PR07 evidence (wolfram, CoVe,
  pr07 experiment jsons). 51 -> 58 files.

## Claim discipline

All additions are diagnostic-only, conditional-theorem, or explicitly synthetic
estimator-mechanics. Forbidden-token claim lint passes (0 failed / 0 warnings).
No family-ID, global tilt, native-solver result, or physical-vorticity detection.

## Validation

| Command | Status |
| --- | --- |
| `latexmk -pdf main.tex` | PASS; 16 pages; refs resolved |
| `pdf_claim_lint.py --pdf docs/final_report/main.pdf` | Failed 0, Warning 0 |
| `build_pr04_research_audit_package.py` + `--check` | 126 entries; byte-deterministic |
| `build_final_report_audit_package.py` + `--check` | 58 files; byte-deterministic |
| `pytest tests/contracts/test_{pr07_audit_repair,pr04_research_audit_package,final_report_audit_package}.py` | 17 passed |
