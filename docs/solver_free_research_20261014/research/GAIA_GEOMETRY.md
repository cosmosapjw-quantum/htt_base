# Fixed-cohort Gaia operator geometry

Owner: HTT. Claim tier: DESCRIPTIVE_CONDITIONAL. Artifact mode: exploratory numerical operator application. Transfer source: not applicable. Allowed use: conditional sensitivity and confidence geometry for the saved six-parameter linear estimator. Forbidden use: physical Gaia coverage, a physical systematic-bias bound, Bianchi identification, or CAS07/Jacobi/MES admission. The covariance is the upstream block-independent proxy; the only new null experiment is a synthetic known Gaussian law.

The application is new to this fixed operator packet; the convex support, ellipsoid image, and Gaussian chi-square identities used below are standard mathematics. This packet supplies a reusable implementation, analytical witnesses, a tangent-basis invariance check, and a six-dimensional simultaneous confidence construction. It does not establish a new theorem or resolve the upstream observational limitations.

## Assumptions and input identities

The exact upstream repository identity is `89621f4c9a6f63449813587a0fadeb13287f8e10`. The frozen operator packet SHA256 is `d5384f57138f4e8ea7b986153bf0133f846e9f7806bdf82b2cb7ac4d6a676c9f`; the baseline result SHA256 is `7af1f6b3508826b69f7170891146536398104779962de76d9d4355c8b9e4415d`. The code requires these explicit identities unless the caller supplies replacement expected hashes. No repository module, upstream archive, fitted observations, solver, or ODE is imported.

For the saved selected cohort of 4,756 sources, write

\[
\widehat\beta=\beta+Mb+K\epsilon,\qquad
M=[M_1\cdots M_N],\quad M_i\in\mathbb R^{6\times2},
\quad K\in\mathbb R^{6\times2N},\quad V=KK^\top\succ0.
\]

Here each `M_i` maps a raw proper-motion tangent vector to spin/glide coefficients. The tangent coordinates are pmRAstar and pmDEC, with no additional cosine of declination. Raw biases and coefficients have units mas/year, `M` is dimensionless, and `K` has units mas/year because its input is a dimensionless whitened vector. `V` has units mas²/year². Values in the tables and figures are multiplied by 1,000 to display microas/year. Parameter order is spin x/y/z followed by glide x/y/z. No relativistic metric or transfer convention enters this finite observation-operator calculation.

The sampling assertion needed for the confidence construction is **conditionally on treating this selected cohort and its operator as fixed**, `epsilon ~ N(0,I_(2N))`. The saved per-source marginal covariance blocks do not supply cross-source covariance. The fitted cohort was selected using outcomes upstream. Neither the fixed-design treatment nor a numerical Gaussian stress check validates this sampling law after selection.

## Per-source physical disk, exact support, and witness

Let

\[
\mathcal B_{\rm disk}(\bar b)=\{b:\|b_i\|_2\le\bar b\ \text{for every source}\}.
\]

For any parameter direction `u`, independent maximization over blocks and Cauchy–Schwarz give

\[
h_{M\mathcal B_{\rm disk}}(u)
=\sup_{b\in\mathcal B_{\rm disk}}u^\top Mb
=\bar b\sum_i\|M_i^\top u\|_2.
\]

This is attained by `b_i = bbar M_i^T u / ||M_i^T u||` when the denominator is nonzero, and by zero for a zero block. Each witness respects the per-source disk constraint; the collection generally depends on `u`. The six reported coordinate supports are six different extremal directions, not one bias realizing every component maximum simultaneously.

Under arbitrary independent orthogonal tangent changes `R_i`, use `M_i' = M_i R_i` and `b_i' = R_i^T b_i`. Then `M_i' b_i' = M_i b_i` and `||M_i'^T u|| = ||M_i^T u||`. The physical disk and its support are therefore invariant under each source's tangent-basis rotation. The implemented check draws 4,756 independent rotations, checks 134 parameter directions, and also rotates an attaining witness.

A raw coordinate box `|b_ia| <= bbar` has support `bbar sum_ia |(M_i^T u)_a|`. A disk at the same numeric budget is a different physical set, contained in that box. Indeed, `disk(bbar) subset box(bbar) subset disk(sqrt(2) bbar)`. Thus the observed smaller disk values do not improve an estimate under identical physical assumptions. The box changes when its coordinate axes change unless its defining physical set is transformed too.

At a per-source disk budget of 10 microas/year:

| Direction | Disk support | Chosen coordinate-box support | Disk / box |
|---|---:|---:|---:|
| spin x | 12.7749 | 16.0821 | 0.7944 |
| spin y | 11.5432 | 13.9264 | 0.8289 |
| spin z | 13.1219 | 15.9274 | 0.8239 |
| glide x | 12.5970 | 15.6091 | 0.8070 |
| glide y | 11.6854 | 14.9711 | 0.7805 |
| glide z | 12.4345 | 14.8981 | 0.8346 |

Supports are microas/year. The budget is hypothetical; the fit does not certify it.

## Exact whitened-bias image and simultaneous Gaussian region

A separate bias model bounds one **total** whitened observation vector: `||z||_2 <= rho`. This is not a per-source, RMS, or raw-tangent disk budget. Its exact parameter-space image is

\[
K\{z:\|z\|_2\le\rho\}
=\{\delta:\delta^\top V^{-1}\delta\le\rho^2\}.
\]

To see both inclusions, `A=V^(-1/2)K` has `AA^T=I_6`; hence `||A z|| <= ||z||`. Conversely, for any desired `delta` inside the displayed ellipsoid, the minimum-norm preimage

\[
z_* = K^\top V^{-1}\delta
\]

satisfies `K z_* = delta` and `||z_*||² = delta^T V^-1 delta`. Arbitrary preimages differ by a kernel vector orthogonal to this minimum-norm preimage, which cannot reduce the norm.

Under the stated Gaussian law, `K epsilon ~ N(0,V)` and its Mahalanobis norm squared is chi-square with six degrees of freedom. Let

\[
q=\sqrt{\chi^2_6(0.95)}=3.54846265920102.
\]

The central noise ellipsoid `E_q` has exact 95% Gaussian-reference probability. The Minkowski sum of noise and admissible bias ellipsoids is exactly `E_q + E_rho = E_(q+rho)` because both become concentric Euclidean balls in the same whitened parameter metric. The constructive decomposition of any point in the larger ball allocates fractions `q/(q+rho)` and `rho/(q+rho)` to the two smaller balls. Aligned boundary points attain the sum radius, so no smaller concentric ball contains this Minkowski sum.

Therefore

\[
\mathcal C_\rho(\widehat\beta)
=\left\{\beta:
(\widehat\beta-\beta)^\top V^{-1}(\widehat\beta-\beta)
\le(q+\rho)^2\right\}
\]

has coverage at least 95% uniformly over admissible fixed biases **under that Gaussian reference law**. It has exact 95% coverage at zero budget; for positive budget it is generally conservative. The scalar direction projection halfwidth is `(q+rho) sqrt(u^T V u)`. Coordinate projections therefore have halfwidths `(q+rho) sqrt(V_jj)`, not the marginal `1.96 sqrt(V_jj)`. This region supplies simultaneous six-parameter geometry. Its projections are consequences of one joint ellipsoid; the enclosing rectangular box is not that ellipsoid and loses its correlations.

At `rho=0`, the component projection halfwidths are `[12.1133,11.0193,13.0129,12.3156,10.8559,11.6868]` microas/year. They are 1.81047 times the exact marginal Gaussian 95% widths. This is a joint-versus-marginal comparison, not newly discovered data uncertainty.

The saved fitted vector has Mahalanobis radius `1.89966054605245`, below `q`. Zero is contained in the simultaneous region even at `rho=0`, hence throughout the tested nonnegative budget grid. This is a conditional zero-containment statement for the saved Gaussian proxy. It is neither a physical Gaia p-value nor empirical coverage.

## Numerical validation and synthetic stress

The final run finds `||KK^T-V||/||V|| = 2.01e-15`. Across the 134 parameter directions, disk witness support error is at most `3.82e-17` mas/year and source-budget excess is at most `3.47e-18` mas/year. Independent tangent rotations change disk supports by at most `3.47e-18` mas/year; rotated witness shifts agree to `6.94e-18` mas/year. The same chosen-coordinate box changes by up to `1.0204` microas/year, exposing its coordinate dependence. Minimum-norm ellipsoid witnesses reproduce arbitrary boundary shifts to `1.22e-17` mas/year and their norms to `1.78e-15`.

The optional 20,000-replicate synthetic stress uses six independent standard normals and known fixed whitened-parameter shifts of norms 0, 1, 2, and 4. Reference central-region coverage is respectively `0.94760, 0.90320, 0.73030, 0.13320`; expanded-region coverage is `0.94760, 0.99235, 0.99775, 0.99905`. At zero shift, Monte Carlo error is approximately `0.00158`; the slight numerical deficit from 0.95 is ordinary simulation error. These simulations stress the stated known law and illustrate conservatism; the analytical geometry is the coverage warrant. The run does not assert measured Gaia coverage.

The portable unit suite has seven passing tests: witness attainment and feasible-point bounds, independent rotations and disk/box containments, minimum-norm ellipsoid preimages, simultaneous Minkowski containment and a sharp aligned boundary, covariance/shape/nonfinite rejection, a known-bias coverage sanity check, and a synthetic input CLI-style run with explicit hash rejection. Non-SPD inputs are rejected without regularization or eigenvalue flooring. Source IDs must be distinct and aligned. Seeds and source identities are present in `result.json`.

## Physics/math audit verdict

Assumptions and units are explicit. Directions with zero operator blocks use a zero witness; zero budgets recover zero support. Rank deficiency is rejected by positive-definite `V` together with `KK^T` parity. Disk symmetry makes positive/negative directional bounds equal. Gaussian stochastic variation and deterministic bias supports remain separate.

| Item | Status | Issue | Required fix |
|---|---|---|---|
| Disk support and tangent invariance | derived and numerically tested | budget is hypothetical | retain budget caveat |
| Exact total-whitened bias image | derived and numerically tested | requires SPD `V=KK^T` | reject failing inputs |
| Six-parameter simultaneous coverage | conditional standard Gaussian result | selection and covariance law unvalidated | retain fixed-cohort proxy language |
| Native solver / CAS07 / physical geometry | not supplied | requisite inputs unavailable | no admission or promotion |

There is no fatal blocker for this conditional operator application. Missing cross-source covariance, outcome-based cohort selection, direction-error modeling, and calibrated physical budgets block an observational coverage claim. Independent review is still required before any publication admission by the parent writer.

## Reproduction

Numerical dependencies: Python 3 and NumPy; Matplotlib is used for SVG/PNG output and can be skipped with `--no-plots`. The authoritative primary run used Python 3.12.3 and NumPy 2.4.2; the machine-readable result records the actual interpreter versions if those differ.

```bash
OPENBLAS_NUM_THREADS=1 /usr/bin/python3 scripts/run_solver_free_gaia_geometry.py \
  --input docs/observational_reboot_20261014/results/gaia_bias_sensitivity_v1/influence_blocks.npz \
  --baseline docs/observational_reboot_20261014/results/gaia_bias_sensitivity_v1/result.json \
  --output /tmp/htt-gaia-geometry-replay \
  --bbar-microas 10 --seed 20261014 --mc-reps 20000
PYTHONPATH=scripts /usr/bin/python3 -m pytest -q tests/htt/test_solver_free_gaia_geometry.py
```

Fresh output directories are required. The output consists of `result.json`, `operator_geometry.svg/png`, and `directional_support.svg/png`. SVG is suitable for repository publication and PNG is a preview. The authoritative integrated result is `docs/solver_free_research_20261014/results/gaia_geometry/result.json`. Worker scratch candidates are not delivery sources.
