# R23-Q: retained-score finite nuisance quotient

Owner: HTT. Scope: fixed selected-row A22 astrometry diagnostic, claim tier C1,
transfer source `none`. Source intake commit `a8e66da28461a415f5da3b3d609c482554d2dcd1`
is an ancestor of the execution checkout `855107f23fd4f25587ba242d8a5dfc1a8fc81876`.
The full and margin cached statistics match the packet's SHA-256 identities.
No catalogue rows were replayed.

## Actual retained-score calculation

The retained 102 columns comprise 18 E1/B1 signal coefficients in three
reported-redshift bins and 84 nuisance columns: 24 l2/l3 E/B, 42 selection
template responses, and 18 l4 E/B. For block Gram matrix
`G = [[A,J],[Jᵀ,C]]` and score `b`, the new estimator is
`ĝ = F⁻¹(b_D − J C⁻¹ b_U)`, where `F = A − J C⁻¹Jᵀ`.
Both observed blocks are positive definite. Its conditional covariance is
`F⁻¹`, assuming the supplied per-source Gaussian score covariance `G` and the
same selected sources. The estimator annihilates every fixed mean in the 84
retained nuisance columns: `M G[:,18:] = 0` in exact arithmetic. Direct
double-precision checks give maximum absolute residuals `5.26e-13` (full)
and `1.03e-12` (margin); the relative Frobenius residuals are `2.68e-15`
and `8.81e-15`.

| Cache | Selected sources | Augmented signal rank | Nuisance rank | Six estimable contrasts | Normalized estimability residuals |
|---|---:|---:|---:|---|---|
| Full | 755,850 | 18/18 | 84/84 | all six | 1.107e-15, 1.357e-15, 1.549e-15, 0.632e-15, 1.912e-15, 1.646e-15 |
| Known-cut margin | 558,407 | 18/18 | 84/84 | all six | 0.536e-15, 1.052e-15, 0.583e-15, 0.822e-15, 0.992e-15, 0.745e-15 |

Requested contrasts are low-minus-high E1 xyz followed by middle-minus-high
E1 xyz, in µas/yr. The conditional estimates are
`[-0.197762, 0.397668, -0.023668, -1.760388, -0.733158, 0.934701]`
for full and `[1.016783, 0.579450, 0.027934, -2.648140, -0.952970,
1.323308]` for margin. Their conditional covariance diagonals, in
`(µas/yr)²`, are `[0.747452, 0.613165, 0.654172, 0.681165, 0.552889,
0.591878]` for full and `[1.396254, 1.269815, 1.541185, 1.059998,
0.942859, 1.133994]` for margin. The **complete 6×6 conditional covariance**
matrices are in [full.json](full.json) and [margin.json](margin.json), under
`contrast_covariance`. An independent Cholesky block solve in
[score_controls.py](score_controls.py) reproduces them with maximum absolute
differences `2.11e-15` and `4.29e-14`. The complete 18×18 covariance appears
in [controls.json](controls.json).

## Previously failed whole-field controls with the new estimator

We reused 1,024 whole-field Gaussian **score-space** draws per control and
the original seed `230623`, fixed selected sources, tau-angular=30 µas/yr,
tau-template=30 µas/yr, l4 RMS=12 µas/yr, and template-mean injection
100 µas/yr. The 18 signal truth is zero. Each draw shares the same noise and
baseline nuisance realization across the two paired injections. Joint 18D
coverage uses the conditional `χ²₁₈` 95% cutoff. The old model's failures
remain the historical result; this is a different estimator and nuisance class.

| Control | Historical full Gaussian-grid fit | New full quotient | New margin quotient |
|---|---:|---:|---:|
| l4 E/B RMS 12 | 291/1024 = 0.28418 | 973/1024 = 0.95020 | 965/1024 = 0.94238 |
| Nonzero template mean 100 | 0/1024 = 0 | 973/1024 = 0.95020 | 965/1024 = 0.94238 |

Exact binomial 95% intervals for the two new full cases are
`[0.93503, 0.96270]`; for margin, `[0.92630, 0.95585]`.
Maximum paired estimator shifts caused by either injected nuisance are below
`2.9e-11` µas/yr. See [controls.json](controls.json) for all counts, intervals,
mean biases and numerical invariants, and [the figure](CONTROLS.png).

## Claim boundary and next input

These controls verify conditional robustness to fixed means *inside the
included 84-dimensional nuisance span* for a frozen selected sample.
They do not calibrate sourcewise proper-motion/classifier selection: changing
that law can change the source set, redshift-bin membership, design and score
distribution. Empirical correlated residual covariance and the sourcewise
selection law are still `UNKNOWN`. The old radial-cut `Q` cannot be used under
unrestricted fixed nuisance means. Out-of-span fields, measurement covariance,
redshift errors and same-congruence PM/NNR/clock physical response also remain
open. K03/K05 cosmic acceleration and physical-response admission remain
`HOLD`; this output is a conditional diagnostic, not empirical coverage.

Next scientific input: a sourcewise selection likelihood or a justified fixed
mean bound, plus residual spatial covariance calibration on the selected
catalogue. The independent physical response remains a separate K03/K05 input.
No native low-ell solver, ODE evolution, MIO posterior, or Bianchi family claim
was used.

## Execution and validation

The first two adapter calls ran with `/usr/bin/python` and NumPy 2.4.2.
They were preserved in [PRE_VENV_RECORD](PRE_VENV_RECORD). The final two
adapter calls ran with the repository `.venv/bin/python` and NumPy 2.5.4.
[Numerical comparison](NUMERICAL_COMPARISON.json) checks every output leaf
at absolute plus relative tolerance `1e-10` and finds no material change.
The largest absolute change is `1.52e-10` in a margin covariance entry;
large relative changes are confined to near-zero estimability residuals.
This is a numerically equivalent output across environments, not a source
identity mismatch. The controls and focused tests had already used `.venv`.

Run the two SHA-checked `stats` commands in `THEORY_AND_RESULTS.md` using
`.venv/bin/python`, then
`score_controls.py` and `plot_controls.py` from the repository root with
`.venv/bin/python`, the cache directory
`/mnt/extdrive/workdir/htt_open_data/a22_20261023/astrometry`, and this
directory as `--output-dir`. The actual
repository-root commands, exit codes, environment and output hashes are
recorded in [RAW_RECEIPT.json](RAW_RECEIPT.json). The focused quotient and
A22 model suites passed: `23 passed, 6 subtests passed`.
