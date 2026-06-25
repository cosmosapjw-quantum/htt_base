# REV-R114 - Final-results report update: PR04 theorems + CF4 K5/K6 measurements

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
generating_command: `latexmk final_report/main.tex + build_final_report_audit_package.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Update the new-version self-contained research report (the credible-claim
distillation, `docs/final_report/`) with this branch's progress.

## Changes

`docs/final_report/main.tex` (9 -> 13 pages):

- Abstract: now names both conditional-theorem suites (EGS-type + multicomponent /
  restricted Bianchi-I) and the new CF4 measurements + exact dust-FLRW oracle.
- New section "Multicomponent identifiability and restricted Bianchi-I dynamics"
  (PAPER-A/B): the seven Wolfram-verified analytic cores - A-rank, A-flrw,
  A-wigner (identifiability + congruence/Wigner kinematics); B-nonsuff, B-psd,
  B-dust (exact FLRW oracle + constraint transport), B-shear (shear memory) -
  with four figures (rank ladder, Wigner, non-sufficiency, dust+shear).
- New measurement subsections K5 (CF4 full-release minimum-variance bulk flow
  ~345 km/s toward (293,21), forward-mock coverage ~0.68) and K6 (CF4 affine
  velocity-gradient decomposition; vorticity reconstruction-conditioned,
  curl-injection recovery 3e-16), each with a figure. Intro updated "two -> four".
- Reproducibility list extended with the PAPER-A/B, K5, and K6 commands.

`scripts/build_final_report_audit_package.py`: `FIGURE_STEMS` extended to the
twelve report figures; `EVIDENCE_FILES` adds the PR04 proof record and the K5/K6
reports. Package rebuilt.

## Claim discipline

All additions are diagnostic-only / conditional-theorem. The K5/K6 prose carries
the explicit "no global-tilt or Bianchi-geometry claim from CF4 distances"
boundary; vorticity is reconstruction-conditioned; the bulk-flow covariance is
the inverse Fisher matrix. No family-ID, geometry, native-solver, posterior, or
model-ranking claim is introduced.

## Validation

| Command | Status |
| --- | --- |
| `latexmk -pdf main.tex` | PASS; 13 pages; all refs resolved; 12 figures embedded |
| `pdf_claim_lint.py --pdf docs/final_report/main.pdf` | Failed 0, Warning 0 |
| `build_final_report_audit_package.py` + `--check` | rebuilt; byte-deterministic |
| `pytest tests/contracts/test_final_report_audit_package.py` | 6 passed |
