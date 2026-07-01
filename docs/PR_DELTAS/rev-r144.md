# REV-R144 - Long-form final report refreshed; all pre-solver analyses re-run

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: ffp10_component_separation (SMICA/Commander); cf4 (peculiar velocities)
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Update the existing long-form research OUTPUT report (not the plan document). Run and review
every analysis performable at the current point in time, and organise the results.

## Analyses run + verified (all pass / current)

- Gates: `make egs3-gates` (61), `make egs2-gates`.
- Wolfram: `egs3_bracket_constants`, `egs3_psd_cone`, `egs3_boost_tilt_separation` -> all PASS.
- Experiments: `run_egs3_experiments.py`; `run_egs2_experiments.py` (refreshed `egs2_experiments.json`
  to its current generator output -- new c_up provenance / nondegeneracy fields).
- Results table (25 rows) + theorem figures `--check` current.
- Real-data scripts `--check` current, headline numbers: K1 morphology p=0.097 (SMICA)/0.121
  (Commander); K5 |B|=340.7+/-101.9 km/s (38049 groups); K6 vorticity/shear<=0.55% (no-go);
  D3 SMICA BipoSH p=0.68/0.65 (500 GRF nulls); D1 CF4 Woodbury |B|=340.7 (K5-consistent), 9 JWST
  anchors (+4% Omega_tilt precision gain); PR08-006 data rank 2.

## Report edits (`docs/final_report/main.tex`)

- Retitled + expanded the real-data section to the six solver-free channels; added a D3 paragraph
  (off-diagonal BipoSH SI on real SMICA/Commander) and a D1 paragraph (feasible correlated-covariance
  CF4 tilt via Woodbury + JWST-anchored precision forecast + degeneracy break).
- Updated the abstract envelope (boost-immune shear estimator with validated FPR; feasible bulk-flow
  covariance reproducing the CF4 amplitude + JWST forecast; SMICA BipoSH SI consistent with isotropy)
  and the blocker-status note (E2E + theory-g sectors only).

## Claim discipline

Diagnostic-only. Sigma^2 stays partial; theory-g CMB fail-closed (never fabricated); JWST prior is a
labelled forecast; SMICA BipoSH is a real measurement consistent with isotropy. No family/geometry/
native-solver/posterior claim.

## Validation

| Check | Status |
| --- | --- |
| `latexmk` report | exit 0; 28 pages; 0 undefined refs (2-pass) |
| research-surface + claim-language linters | 0 hits |
| `make egs3-gates` / `egs2-gates` | pass |
| egs3 Wolfram proofs (x3) | PASS |
| `pytest tests/contracts` | 355 passed |
| audit packages rebuilt + `--check` | current |
