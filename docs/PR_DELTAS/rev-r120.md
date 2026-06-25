# REV-R120 - PR-N/PR-B: EGS2 extension theorems + blocker-discharge mechanics

owner: COMMON
implementation_scope: common
claim_tier: program_theorem_and_synthetic_mechanics
transfer_source: none
generating_command: `make egs2-gates && make egs2-experiments`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Continue the EGS2 extension audit by implementing the proposed NT2-* theorems and
the concrete public-data blocker discharges, sequentially, as runnable modules +
gates + a driver in the canonical repo.

## Changes (modules under htt/obsstat/)

- `egs2_fisher.py` (**NT2-A1 flagship**, NT2-A2): the genuine multi-multipole
  Fisher-Cramer-Rao floor on F_shear, `I = sum_l (2l+1)/2 f_sky r_l^2`,
  `sigma(F)/F >= I^{-1/2}` -- strictly below the single-l `sqrt(2/5)=0.632`
  (0.632->0.474->0.424 at L=2,5,20), decreasing with L, raised by sky cuts; a
  Monte-Carlo multi-l MLE achieves the floor (ratio ~1). NT2-A2: the Fisher
  information saturates (floor change <1% from L=40->80; convergent tail). This
  is the genuine floor the report's NT-A3 label asserted but did not prove.
- `egs2_shear_bracket.py` (**NT2-B1 flagship**): two-sided quadrupole+octupole
  bracket `a2 kappa/(1+R_EGS) <= Sigma <= C_up a2` under H3 (`R_EGS=a3/a2<=R*`),
  so `F_shear` is bracketed away from zero -- a nonzero quadrupole *excludes* a
  vanishing shear-filling (the strong lower-bound content; `F_lo>0`).
- `egs2_transport.py` (NT2-B2, NT2-B3): the GR shear-memory transport
  `sigma'=-3H sigma+3H^2 Pi(z)` GR-*sources* the depth gap `G_F(z)` (steady Pi ->
  flat; growing Pi -> spread 2.45); and the vorticity joint blind-sector no-go
  (CMB-T sensitivity 0 + radial projection `n^a Omega_ab n^b=0` exactly).
- `constrained_realizations.py` (**BLOCK-K6 discharge**): Hoffman-Ribak
  constrained-realization curl posterior `s_CR=s_WF+(s_rand-WF[s_rand])`; the WF
  mean is curl-suppressed (~0) but the CR ensemble carries the posterior
  (mean ~0 +- 0.59) -- upgrades K6 from "non-identifiable" to a prior-width bar.
- `lowell_global_calibration.py`: `e2e_maxscan_from_summaries` (**BLOCK-K1
  discharge**) ingests one row per public Planck FFP10/NPIPE E2E sim and returns
  the +1-corrected global rank p-value (global p >= min local p).

## Harness

- `research_gates/egs2/tests/test_egs2_{fisher_bracket,transport,blocker_discharges}.py`
  (13 gates, all pass).
- `scripts/run_egs2_experiments.py` -> `docs/generated/egs2_experiments.json`.
- `Makefile`: `egs2-gates`, `egs2-experiments` targets.

## Claim discipline

Conditional EGS-type theorems + synthetic mechanics only. The toy Fisher response
`r_l` and scalarized shear hierarchy are documented constructs: the *shapes*
(floor < 0.632, exclusion of zero, sourced transport, joint blind sector) are
robust; the exact numbers need the covariant l=2/l=3 coefficients and real low-l
transfer (semi-native calculator ticket). The K1/K6 discharges are *mechanics*;
the real public-map / 3D CF4 WF-CR runs keep their registered blocker codes
(`BLOCKED_MISSING_PR4_E2E_ACCESS`, `BLOCKED_MISSING_FIELD_REALIZATIONS`). No
detection, family/geometry, or native-solver claim.

## Validation

| Command | Status |
| --- | --- |
| `make egs2-gates` | 13/13 |
| `make egs2-experiments` | wrote egs2_experiments.json |
| floor monotonicity / MC ratio / bracket exclusion / B2 spread / B3 zero | all hold |
