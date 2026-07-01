# REV-R142 - EGS3 Axis D: BASS-Extended joint PV+CMB analysis (pre-solver)

owner: OBSSTAT
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: ffp10_component_separation (SMICA/Commander maps); cf4 (peculiar velocities)
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Critically evaluate the proposed BASS-Extended joint likelihood and port everything honestly
runnable before the native low-ell solver, expanding scope to: (i) a JWST data-acquisition
pipeline, (ii) extracting/estimating the off-diagonal `C_{lm,l'm'}` from real Planck SMICA,
(iii) a feasible `invert_matrix(C_PV)`.

## Critical evaluation (as landed)

- The theory `C_{lm,l'm'}(g)` IS the blocked native solver (already fail-closed at
  `cl_assembly.py:921`); ported as a fail-closed interface stub, never fabricated.
- A single sky cannot give a covariance, but the off-diagonal signal IS a real single-sky
  observable as BipoSH `A^{LM}_{ll'}` -> measured on real SMICA, null-calibrated.
- The dense N x N `C_PV` inversion is infeasible at CF4 scale -> diagonal + low-rank Woodbury.
- JWST anchors are real but small/nearby -> a labelled forecast; the modest global-tilt gain is
  reported honestly, not inflated.

## Changes

- **NEW `htt/obsstat/pv_covariance.py`** - Woodbury `C_PV = diag + U Lambda U^T`
  (`woodbury_solve`/`woodbury_logdet` verified == dense; `velocity_field_modes` bulk+shear basis;
  `pv_tilt_gls` correlated-covariance GLS; `traceless_symmetric_basis`).
- **NEW `htt/obsstat/biposh_smica.py`** - exact `wigner_3j`/`clebsch_gordan` +
  `compute_biposh_from_alm` (D^L_{l1l2}, L=1 aberration / L=2 SI) reusing `SparseBiPoSHCoefficient`.
- **NEW `htt/obsstat/joint_pv_cmb_forecast.py`** - `jwst_anchor_forecast`, `joint_fisher_forecast`
  (coupled-Fisher degeneracy break), `anisotropic_cmb_covariance`/`anisotropic_cmb_loglike`
  (fail-closed `OutOfScopeError`, `AWAITING_NATIVE_LOWELL_SOLVER`), `evaluate_joint_loglike`
  (real PV + real BipoSH + fail-closed theory; never a fabricated total).
- **NEW gate** `research_gates/egs3/tests/test_egs3_axis_d_joint_forecast.py` (D1-D8, 13 tests);
  `make egs3-gates` now 61. **Wolfram** `egs3_boost_tilt_separation.wls` +=
  `prior_precision_reduces_inflation` (11/11 PASS).
- **NEW JWST acquisition** `dl_pipeline/scripts/download_jwst_anchors.py` + cited seed
  `dl_pipeline/data/jwst_distances_seed.csv` + `scripts/jwst_cf4_crossmatch.py`
  (-> `docs/generated/jwst_cf4_anchors.json`, 9/12 matched).
- **NEW real-data scripts** `scripts/k1_biposh_smica.py` (real SMICA/Commander BipoSH, p=0.68/0.65)
  + `scripts/bass_extended_joint_forecast.py` (real CF4, |B|=340.7+/-5.0 K5-consistent, JWST forecast).
- **Edits**: `run_egs3_experiments.py` (axis_d), `build_egs_results_table.py` (EGS3-D1..D4; 25 rows),
  `make_egs2_egs3_theorem_figures.py` (2 figures), `CLAIM_LEDGER.yaml`, `BLOCKERS.md`,
  `docs/final_report/main.tex` (Axis-D subsection + 2 figures + 4 rows), CHANGELOG, CLAUDE.md.

## Claim discipline

Diagnostic-only. PV tilt + SMICA BipoSH are REAL measurements (measured / measured_partial); the
JWST prior is a labelled FORECAST; the theory-g CMB likelihood is fail-closed (never fabricated).
Sigma^2 stays partial; no family/geometry/native-solver/MIO-as-odds claim. Canonical K1 GRF
artifact, K5 measured row, v2 frozen statistics, and the bit-identical x_C all byte-identical.
Raw JWST/CF4 downloads stay under workdir/raw (gitignored); only compact anchors/manifests + the
cited seed are committed.

## Validation

| Command | Status |
| --- | --- |
| `make egs3-gates` | 61 passed |
| `run_pr07_wolfram_proofs.py egs3_boost_tilt_separation.wls` | PASS (11/11) |
| `scripts/k1_biposh_smica.py` + `bass_extended_joint_forecast.py` + `jwst_cf4_crossmatch.py` `--check` | current |
| `build_egs_results_table.py` / `make_egs2_egs3_theorem_figures.py` `--check` | current |
| `pytest tests/obsstat tests/contracts` | pass (no new failures) |
| claim linters | 0 hits |
| `latexmk` report | exit 0; 0 undefined refs |
| audit packages rebuilt + `--check` | current |
