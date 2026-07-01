# REV-R141 - EGS3 Axis C: kinematic deprojection of the observer-boost quadrupole

owner: OBSSTAT
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Critically accept the "Leaky Universe" toy test and upgrade the code: implement the two
formalism upgrades the rev-r140 note only specified, do the maximum analysis possible without
the native low-ell solver and without real data (still downloading), and reach a publishable,
non-toned-down novel result. Port with CRAG / metacognitive self-ask / CoVe / chain-of-code.

## Deliverable (refined research direction, anti-tone-down)

A closed-form kinematic deprojection `Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2` that
makes the low-ell shear reading PROVABLY IMMUNE to observer-boost contamination. The headline
is a proven ESTIMATOR PROPERTY + a validated false-positive rate + a covariance-inflation
model -- NOT a shear detection -- so it needs neither real data nor the solver, yet is a
strong, novel methods contribution. `Sigma^2` on the real sky stays `partial` until data
lands, at which point `Sigma_tilde^2` supplies a boost-immune shear reading.

## Changes

- **NEW `htt/obsstat/egs3_kinematic_deprojection.py`** (separate diagnostic surface):
  - `deprojection_alpha` = `(4/9) T0^2 N2 / (kappa_T^2 R_sigma)`, beta-independent; = 1 in the
    registered eps-normalisation, matching `doppler_boost.py:94` (`delta_eps2 ⊃ eps1^2`) and
    `boost_coefficients.py:135` (`a[2]=v^2`, Paper I Prop 5).
  - `projected_shear` (-> 0 on a pure-boost sky; = Sigma^2 when Omega_tilt=0),
    `coupled_fisher` / `response_correlation` / `covariance_inflation` (F_{Sigma2,Omega_tilt}
    ~ beta^2; inflation 1/(1-r^2) -> 1 as beta->0), `boost_tilt_identifiability`
    (Gram det 1-P2(cos t)^2; rank 2 generic, degenerate iff boost axis || shear axis),
    `injection_recovery_experiment` (deterministic moment-level; no map/solver/data),
    `injection_recovery_fullmap` (optional-healpy, figure only).
- **NEW gate `research_gates/egs3/tests/test_egs3_axis_c_boost_tilt.py`** (C1-C6, 19 tests):
  closed-form alpha (chain-of-code, recomputed two ways), projection zeroes-boost/preserves-shear,
  beta^2 off-diagonal + inflation formula/limit/monotonicity, identifiability generic-vs-aligned,
  injection-recovery FPR/coverage bounds, a CoVe adversarial beta/noise/axis sweep, and a
  bit-identity guard (x_C unchanged, response design unchanged, no registered statistic added).
  `make egs3-gates` now 48 tests.
- **NEW Wolfram `wolfram/egs3_boost_tilt_separation.wls`** (10/10 checks PASS) wired into the
  Makefile `egs3-wolfram` target -> `docs/generated/egs3_boost_tilt_separation_proof.json`.
- **`scripts/run_egs3_experiments.py`** += `axis_c()`; **`scripts/build_egs_results_table.py`**
  += EGS3-C1..C4 rows (results table now 21 rows, 12 proven_gate);
  **`scripts/make_egs2_egs3_theorem_figures.py`** += `fig_egs3_c_deprojection` + sidecars.
- **`docs/research_program/egs3/CLAIM_LEDGER.yaml`** += `egs3.kinematic_deprojection` (C4, DERIVED).
- **`docs/final_report/main.tex`**: §8 Axis-C subsection + gallery figure + four table rows;
  row count prose updated (21 rows / 18 proven). **`htt_local_global_formalism.tex`** §7 +
  Claim Envelope upgraded from "recommended" to "implemented + gate-validated + Wolfram-verified".

## Claim discipline

Diagnostic-only. Estimator property + synthetic FPR/coverage witness, not a detection. The
deprojection is a SEPARATE surface: the bit-identical comparator `x_C = tr(C M)`, the response
design, the canonical K1 GRF artifact, and the v2 frozen 6-statistic set are all byte-identical.
No family-ID, geometry, native-solver validation, MIO-as-odds, or global-tilt certificate. The
exact physical alpha awaits the covariant low-ell transfer (EGS3-B1); the ratio structure and
the deprojection/inflation/identifiability content are the robust, closed-form part.

## Validation

| Command | Status |
| --- | --- |
| `make egs3-gates` (Axis C + existing A/B/PSD) | 48 passed |
| `run_pr07_wolfram_proofs.py egs3_boost_tilt_separation.wls` | PASS (10/10 checks) |
| `build_egs_results_table.py` / `make_egs2_egs3_theorem_figures.py --check` | current |
| `pytest tests/obsstat tests/contracts` | pass (no new failures) |
| `claim_lint_research_surfaces.py` + `check_claim_language.py` | 0 hits |
| `latexmk` report + root note | exit 0; 24 pp / 5 pp; 0 undefined refs |
| audit packages rebuilt + `--check` | current |
