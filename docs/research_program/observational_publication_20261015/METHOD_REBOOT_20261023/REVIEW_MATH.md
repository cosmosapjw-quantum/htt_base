# Independent mathematical and numerical review

Date: 2026-10-23. Scope: `THEOREMS.md` T1–T6, `analysis.py`, `K03_INPUT.json`, `RESULT.json`, `agent_selection.md`, and `agent_observables.md`, with the retained K03 source summary/report used to check extraction. This reviewer did not author the candidate and did not use earlier review verdicts. Requested runtime: Astra/xhigh; independently observed runtime identity: **UNKNOWN**. No nested agents, catalogue replay, ODE, or Boltzmann calculation was used. Only this review file was written; candidate outputs were not overwritten.

**Verdict: PASS for the stated conditional mathematical/method result; no blocking mathematical or numerical defect found.** This is not acceptance of the original physical targets, an empirical coverage calibration, or a novelty finding. Original acceptance remains 17/42; the separately labelled analytic-alternate count is unchanged.

## Actual independent checks

An independent in-memory Python calculation used the small input and retained source, rather than executing `analysis.py`'s output-writing main function.

| Check | Result |
|---|---:|
| Extracted history covariance equals retained `fit.covariance[:3,:3]` | Exact array equality |
| Extracted joint information equals retained `fit.F` | Exact array equality |
| Source SHA-256 and input SHA-256 | Both match recorded values |
| Inverse history covariance versus Schur information, maximum absolute residual | 1.3322676295501878e-15 |
| Full information inverse versus retained full covariance, maximum absolute residual | 6.661338147750939e-16 |
| Independent degree-four angular cubature: quadrupole norm residual | 3.469446951953614e-18 |
| Same cubature: reconstruction of all shear matrix entries | 1.1102230246251565e-16 |
| Momentum perturbation inequality: scalar-aligned saturating example | Exact within printed precision |
| Momentum perturbation inequality: 1,000 independent random cases | All pass; largest actual/bound ratio 0.8978638529689951 |
| Strict-tail intervals, endpoint ties and unknown completion | All 540 finite cases pass |
| Independent selection-odds event/mean endpoint LPs, including atoms and Gamma=1 | All 60 pass; maximum discrepancy 8.881784197001252e-16 |

The angular calculation used six coordinate-axis directions with weight 1/15 each and eight cube-vertex directions with weight 3/40 each. This differs from the candidate's Gauss–Legendre grid and integrates the required degree-four moments exactly. The selection LPs are this review's own check, not a claimed reproduction of the appendix's separate 180-LP run.

Reproduced covariance eigenvalues are `(0.6631896090691883, 0.6967907812958589, 0.8788988664685646)` in `(microarcsec/year)^2`.

| epsilon | Largest permitted amplitude (microarcsec/year) | d_max | Level-0.05 oracle power |
|---:|---:|---:|---:|
| 0.01 | 0.000019690591538992444 | 0.00002417908749302638 | 0.05000249377526175 |
| 0.1 | 0.00019690591538992446 | 0.0002417908749302638 | 0.05002494221604289 |
| 0.3 | 0.0005907177461697734 | 0.0007253726247907914 | 0.050074856411508 |

All three powers agree with `RESULT.json` within 1e-15.

## Findings by theorem

**T1 — valid.** In a smooth energy frame, the projected divergence of anisotropic stress contributes the additional `pi_ab a^b` term, so the acceleration matrix is indeed `epsilon I + P`, not merely `(epsilon+p)I`. Positive semidefinite P and positive epsilon imply the stated inverse-norm bound. With unit timelike u and proper-length differentiation, `a=A/c^2`; stress gradient divided by energy density has dimensions inverse length, giving acceleration after multiplication by `c^2`. The perturbation inequality follows from the resolvent identity and the lower singular/eigenvalue bound `m-eta`. A scalar-aligned perturbation `Delta M=-eta I` and an aligned positive `Delta g` saturate it, so the constants have the right direction. Requiring `q=0` in a neighbourhood matters: vanishing flux only at one point would not eliminate its derivative terms. The candidate explicitly makes the stronger assumption.

**T2 — valid with its declared local interpretation.** Contracting `-u_a a_b + (H/c)h_ab + sigma_ab/c + omega_ab/c` with `(u-n)^a(u-n)^b` gives `H/c - A.n/c^2 + sigma:nn/c`; the acceleration dipole sign is consistent with the sourceward n convention. The antisymmetric part vanishes. Fourth-moment contraction gives `mean(h2^2)=2 sigma:sigma/15`, hence the factor 5/4 and inversion factor 15/2. The nonlinear uncertainty bounds use the normalized `L2(dOmega/(4pi))` norm and the same joint event for H and h2. No independence assumption is needed. The same-G requirement, finite-redshift remainder, boost, and selected-sky qualifications are substantive and correctly retained. These identities alone do not determine the other signed terms of x_C.

**T3 — valid.** Compactness gives attainment, positive fixed irreducible weights make the representation orthogonal, and the quotient triangle inequality and two-argument Lipschitz inequality follow. Repeated eigenvalues and zero tensors cause no failure of this construction. The exactly aligned scaled example is a suitable check, but supplies no generic optimizer certificate; the candidate says so. The anisotropic-covariance warning is necessary: for the vector representation with squared norm matrix `diag(1,4,9)`, e1 and e2 belong to the same rotation orbit, yet their distances to zero are 1 and 2. Therefore a fixed anisotropic norm cannot define the stated metric on tensor orbits.

**T4 — valid.** Confidence-set images preserve coverage by event inclusion, with the same parameter/source and experiment throughout. This also yields simultaneous coverage of the entire threshold envelope, because the single input event implies all threshold inequalities. It does not mean that a distinct extremizing source completion can be used as one common completion at every threshold. For closed input intervals and strict exceedance, the upper indicator must indeed be `1[r_i>t]`; when `r_i=t`, exceedance is impossible. The sum of retained source weights must be `1-u`, as the appendix explicitly states. Undefined F cannot enter the floored comparison as zero. The ratio-of-bin-summary formula, the example `1` versus `13/9`, the box projection, and the Lipschitz coefficients `1/delta` and `1/delta^2` are correct. Production implementation provenance is distinct from this mathematical verification; the actual `IsotropyGap`/`F_Bayes` class source was not among the supplied review inputs.

**T5 — valid.** For `gamma <= alpha < 1`, the covered-set rejection event implies `p_true <= alpha-gamma`, and the union bound adds at most gamma. Dependence between the confidence set and p-values is harmless. `alpha<gamma` cannot reject; `alpha=1` is trivial. A grid maximum without an upper envelope is not a conservative supremum. The bounded-bias Gaussian interval and the split common-mode kernel argument are correct. These constructions require valid fixed-nuisance p-values/noise bounds for the actual selected experiment; they do not supply that validity from an invalid residual law.

**T6 — valid for exactly the fixed retained Gaussian mean experiment.** Maximizing `a_b^T C_bb^-1 a_b` over its Euclidean amplitude ball gives the claimed largest-eigenvalue result. The appropriate information is the Schur complement: its largest eigenvalue is 1.5078643970365244, whereas the largest eigenvalue of the fixed-local block `F_bb` is 3.1110711618848947. Replacing the former with the latter would change the nuisance treatment; the candidate uses the correct former value. For a specified shift a, the normalized likelihood-ratio contrast is standard normal under zero and has mean d under a, giving optimal power `Phi(Phi^-1(alpha)+d)`. Neyman–Pearson bounds every level-alpha test at that specified alternative, hence also at every alternative in the declared ball using d_max. The result is not a statement about a new covariance, richer observations, constrained/known local velocities, a non-Gaussian physical experiment, or independently enlarged data. The document retains these distinctions and does not identify epsilon with a full remainder certificate.

The selection appendix's density-ratio normalization, sharp event bounds, quantile-tail mean bounds with fractional atom allocation, exact transport-bias identity, and total-variation response bound are also algebraically consistent. The covariance-orthogonality identity is read conditionally on the stated design/training information; it does not make the quadratic residual diagnostic insensitive to misspecification.

## Nonblocking precision edits

1. Add `sum_i p_i=1-u` directly beside the T4 displayed strict-tail bounds. It already appears in the selection appendix; “retained normalized source weights” alone can be misread as renormalizing the retained subset to one.
2. In the T5 proof write `gamma <= alpha < 1`, then state that alpha=1 is trivial. The capped-p-value implication used in the proof does not literally hold at alpha=1, although the theorem remains valid there.
3. Keep the invariant norm as the actual T3 metric. If the covariance-transform alternative is developed, specify its joint state/action and invariant distance construction: transforming covariance under a common coordinate change alone does not prove that an anisotropic Mahalanobis minimization is a metric on tensor-only orbits.

These are clarification points, not counterexamples to the correctly scoped results. The report is ready to describe a conditional method audit and a reproducible retained-summary power calculation. It should continue to withhold physical acceptance, universal no-go claims, and literature-priority claims.

## Supplemental review: corrected full tuple and T7

This supplement reviews the corrected introduction and T7, plus the added numerical checks and the newly supplied `inputs/MODEL_TO_DATA.md`, `inputs/tensor_functionals.py`, `inputs/isotropy_gap.py`, `inputs/anchor_geometry.py`, and `inputs/depth_path.py`. **It supersedes any implication above that the legacy scalar tuple defines the complete research object.** The initial T4 review verified scalar projection mathematics; it did not establish the full tuple's definitions. The three earlier precision edits have now been applied and checked.

The pinned design explicitly gives x as sample-by-functional output, Q as an anchor gauge/margin, F as directional support, Pi as an explicit-law exceedance surface, and G_F as a structured depth path. Scalar x_C, its positive-normalizer ratio, and the floored bin ratio belong to a legacy projection report. The corrected introduction/T7 restore this distinction. In particular, the legacy `IsotropyGap.G_F` is not the complete `FunctionalDepthPath`.

**Supplemental verdict: PASS, with no blocking issue.** The following claims are correct under their displayed hypotheses:

- A single confidence event for the entire typed state, nuisance, response/remainder, and anchor variables implies simultaneous membership in all its deterministic functional images, including all directions and depths. This is event inclusion, not an extra independence assumption. Separate jet regions cannot be attached while retaining the old nominal coverage without a valid joint construction or error allocation.
- For a closed convex balanced anchor satisfying `rB subset A subset RB`, its gauge is a norm, is `1/r` Lipschitz in the state, and obeys the stated reversed-inclusion bounds under anchor perturbation. Combining those bounds gives the displayed state-plus-anchor interval. The equivariance statement rotates both anchor and state. These norm claims do not automatically extend to every nonbalanced/nonconvex/conditional anchor supported by an API.
- Compact convex sets satisfy the support/Hausdorff identity. The support ratio is well defined only with an eligible positive anchor denominator; it is not an occupancy probability. The finite-net correction requires the stated radius bound, with extra denominator control for a support ratio. Nonconvex strata cannot be reconstructed from support alone: the two-point set `{-1,1}` and the interval `[-1,1]` have identical support functions but Hausdorff distance 1.
- The fixed-contraction sphere-fibre support formula follows from the orthogonal minimum-norm solution and kernel decomposition. At norm-squared eta0=1 the fibre is a singleton; at eta0>1 it is empty. The supplied 3-by-7 numerical helper refuses uncertain q, rank ambiguity, and uncertified near-boundary outcomes. Its numeric support/witness status is not an outer confidence guarantee. A fitted q substituted into L does not represent the joint q/v inverse image.
- The explicit-law Pi surface preserves strict exceedance. A confidence region does not create a probability law, and a morphology result does not remove unknown physical mass.
- Retaining the initial depth block plus adjacent differences gives an invertible fixed transformation. Transforming the entire Gaussian covariance preserves the quadratic likelihood and Fisher information; dropping the initial block destroys common-mode information. The actual `DepthRepresentation` implementation also permits fixed general adjacent kernels and restores the original blocks recursively. Its covariance assembler returns unavailable for missing cross-blocks instead of assuming zeros. Fitted kernels require their joint law, as the source explicitly marks.

Direct source inspection confirms that `DepthBinFRecord.f_value` returns `filling_fraction.F_Bayes`, `effective_F_by_bin` floors each bin summary, and `IsotropyGap.G_F` exponentiates the difference of their logarithms. Thus the legacy ratio-of-floored-bin-summaries interpretation is verified in the supplied implementation. The internal mean formula of `F_Bayes` resides in the separate filling-fraction module and is not reverified from `isotropy_gap.py` alone. The full path remains the typed reporting target; this review does not certify that a complete production `FunctionalDepthPath` implementation has been delivered.

### Additional execution evidence

The exact numerical prefix of the revised `analysis.py` was executed in memory through construction of its output object. An AST-only truncation inserted a return before all output writes; the numerical statements were unchanged. **Every candidate assertion passed, every check entry matched the stored `RESULT.json` exactly, and every power row matched exactly.** Candidate outputs were not overwritten.

Independent calculations, using different random draws and dimensions, additionally produced:

| Supplemental check | Result |
|---|---:|
| Joint state/anisotropic-anchor perturbation bounds | All 300 cases pass |
| Gauge equivariance, maximum residual | 3.352873534367973e-14 |
| Full-row-rank 3-by-7 sphere-fibre support witnesses | All 200 cases pass |
| Largest fibre constraint residual | 1.3118495982947944e-14 |
| Largest fibre unit-norm residual | 3.3306690738754696e-16 |
| Largest fibre support residual | 1.5543122344752192e-15 |
| Four depth bins with two coordinates: likelihood quadratic residual | 1.7319479184152442e-14 |
| Same full-covariance experiment: Fisher residual | 2.930988785010413e-14 |

For independent unit-variance scalar bins, the independently computed adjacent-difference covariance has diagonal 2 and nearest off-diagonal -1; the difference operator annihilates the constant vector exactly. This explicitly tests the two depth-path failure modes, rather than only checking an invertible identity.

No empirical coverage, physical-target acceptance, literature novelty, or universal impossibility statement follows from these finite checks. The corrected report is ready for conditional mathematical closeout with the full tensor-functional object preserved.

### Final source-dependency clarification

The subsequently supplied pinned `inputs/filling_fraction.py` was inspected directly. Its `F_Bayes` property returns `math.fsum(self.f_samples) / self.sample_count`, confirming the unweighted arithmetic mean of samplewise fractions. This closes the previously unverified dependency note: together with `DepthBinFRecord.f_value` and `IsotropyGap.G_F`, the source confirms a ratio of floored bin means, not a mean of per-draw ratios. This remains a legacy scalar projection, distinct from the full tensor-functional depth path. The verdict is unchanged.
