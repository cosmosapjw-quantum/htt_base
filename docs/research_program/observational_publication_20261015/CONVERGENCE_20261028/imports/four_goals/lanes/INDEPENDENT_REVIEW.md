# Independent bounded scientific review

28 October 2026. One coherent independent review of the four original goals, fibre information experiment, and common physical remainder. This review follows the binding PhysMath 1.3 excerpts in WORK_PACKET.md. It adds selected exact algebra and independent finite controls, not a second production programme, recursive review, catalogue fit, ODE, repository push or acceptance promotion.

**Scientific status:** the inspected derivations support a conditional physical-response and inference framework. They do not yet constitute measurements of cosmological shear/vorticity, identification of a Bianchi geometry from an observed sky, or separation of geometric distance from unconstrained grey transmission. The most substantive application additions are the joint Thomson/shear carrier and omission-bias map, detector/frame-qualified inversion, physical-error-compatible family classifier, and opacity-qualified Hubble/curvature images. The Gaussian inverse and confidence identities themselves are established mathematics. No independent priority claim is made.

## 1. Independent calculations and their scope

`code/review_checks.py` imports no production script. It uses exact rational angular moments and Gaussian elimination for ranks, a different finite angular design for spatial response, independent three-dimensional Hermitian jets for optical algebra, and a different four-target Gaussian fixture for the bias bound. `INDEPENDENT_REVIEW.json` is its machine-readable receipt.

| Claim checked independently | Result |
|---|---:|
| Exact common Thomson-gain/shear carrier rank | 23 |
| Exact common carrier with no circular component | 20 |
| Exact intensity-to-shear rank / gain rank | 15 / 9 |
| Positive-sky degree-4 difference, operator norm | 0.5744626566564194 |
| Difference from production quadrature value | 2.71e-14 |
| Spatial radial / transverse / joint response ranks | 6 / 8 / 9 |
| Helicity analyzer with phase-only / calibrated SU(2) paths | 1 / 2 |
| Fixed-Q sharp chirality radius | 0.5773502691896256 |
| Attaining zero-chirality residual | at most 9.87e-18 |
| Matrix CBL decomposition, 50 independent 3×3 jets | relative residual at most 8.66e-15 |
| Scalar opacity cancellation | exact zero polynomial |
| Worst Fisher-bias bound attained by singular vector | error 1.11e-16 |
| Noncentral Gaussian ball, five error budgets | minimum exact coverage 0.95 |

The exact angular calculation represents intensity degrees 0,2,4 by the fifteen homogeneous quartic monomials restricted to the sphere. Adding five projected real screen-STF modes and three screen-supported imaginary antisymmetric modes produces a 24×23 rational response of exact rank 23. This checks the actual combined physical map rather than relying only on a floating-point rank threshold. Positivity permits these independent local perturbations around a strictly positive screen state; it does not guarantee that all twenty-three components are observed by a given instrument.

The code initially failed because SymPy is absent; one diagnostic call with the primary interpreter confirmed the same condition. The substantive repair replaced that dependency with sparse exact Fraction polynomials and exact Gaussian elimination. The repaired check exits 0. The failed operations and repair are retained in the JSON receipt; no tolerance was weakened.

## 2. Concrete risks, effects, and smallest repairs

| Location and provenance | Defect or risky inference | Scientific effect | Smallest repair and readback |
|---|---|---|---|
| Pasted proposal / extracted text, **not rendered MF02** Eq. (1.6.8) | Additive `f0 I + epsilon(n.e)sigma3`, with only `|epsilon|<1` | Does not guarantee positivity or an integrable spectral perturbation | Use `f0(E)[I+epsilon(n.e)sigma3]`, already printed in the original PDF and used in the production experiment |
| Proposed distance reconstruction, not MF02 §4.6 | Infer absolute W or grey loss from traceless Xi | Removes a physically unobserved scalar transmission direction | Retain grey `g,g',g''` as calibrated/bounded nuisance; GOAL4 does this |
| Proposed channel interpretation | Treat Choi rank 1 as unitarity without TP | A one-Kraus attenuation filter would be misclassified as lossless | Require a justified TP normalization and equal input/output dimension; GOAL4 supplies a counterexample and the corrected condition |
| Ideal matrix K inversion | Identify supplied H/Q response fields directly with redshift/proper-motion observables or geometric vorticity | Hidden source/history/detector/frame kernels are omitted | Keep the explicit measurement adapter and common frame-spin nullspace; GOAL2 reports the resulting 36→33 rank loss |
| Proposed multipath information gain | Treat pure helicity connection phases as arbitrary SU(2) conversion | Claims an extra measured helicity direction that the physical phase channel cannot generate | Distinguish phase-only rank 1 from calibrated-converter rank 2; independently verified here |
| GOAL2 draft convention | Use `ell=-u+n` beside physical `u.u=-c²` | Mixes normalized and physical velocity units | Root corrected to `bar u=u/c`, `ell=-u/c+n`; retain this translation wherever physical acceleration is displayed |
| FIBRE sign test implementation | Counted `LLR=0` as incorrect for both equal-prior classes | Slightly understated a realizable classifier's accuracy; obscured tie handling | Repaired with an exact integer statistic and independent fair tie decisions. The dedicated sign-only rerun gives 98.086% accuracy, SE 0.0433 percentage points, with 155 ties in 100,000 draws |

**Source-provenance correction:** the reviewer initially attributed the additive expression to MF02 after reading `sources/fibre.txt`. Direct inspection of `sources/fibre_info_p17.png` showed the printed multiplicative brackets. That initial attribution is withdrawn. No original-PDF positivity defect is established. MF02 §4.6 also already states the grey ambiguity, the scalar-vs-matrix response distinction, and the conditional nature of the CBL decomposition. Those cautions should not be presented as repairs to the original PDF.

## 3. Conditions that must remain attached to the results

**Morphology and radiation-to-shear.** The nine-dimensional Thomson statement concerns the cold-electron rest-frame gain, not the full gain-minus-loss collision operator or the directly observed sky. The joint 23/20-dimensional carrier preserves that gain and the instantaneous intensity-to-shear operator only. The derivative residual, rate, bolometric completion and frame conversion remain physical inputs. The polarized omission-bias equation has the correct sign for the stated source equation; its inverse bound requires a strictly positive lower eigenvalue after operator uncertainty. Shear has inverse-time units, brightness moments share one spectral/energy convention, and gamma has inverse-time units.

**Kinematic inversion.** The six-axis inverse requires common-fibre matrix H and Q fields at one event. In the stated velocity-first index convention, Wn=n×Omega. With physical u normalized to -c², past and future null conventions use `-u/c+n` and `u/c+n`; the acceleration sign follows that choice. A physical source/detector law must identify any observable with the ideal fields. A common unconstrained frame spin removes the geometric antisymmetric identity sector. A trace-free internal decomposition must be specified before the trace of a matrix gradient is called geometric K.

The matrix-log distinction is correct and consequential: for the displayed positive matrix and analyzer, the scalar channel log derivative is 1/3, whereas the detector pairing with the matrix-log derivative is log(2)/2. Gauge invariance requires conjugating state, channel and effect together. Rotating the source relative to a fixed calibrated analyzer is a different physical experiment.

**Classification.** The Gauss adapter is for a hypersurface-normal congruence with vanishing vorticity and a declared Riemann convention. Its density is energy density and kappa=8πG/c⁴; H/c and Sigma/c have inverse-length units. A shear estimate alone does not supply the electric Weyl tensor or anisotropic stress. The finite separation certificate follows directly from disjoint metric tubes around supplied response families. Fixed known covariance, common nuisance projection, parameter domains, and full-family response-error bounds are required. The six-dimensional covering event includes the one-dimensional adequacy residual; dropping it while preserving pairwise likelihood ratios would not preserve an open-ended model check.

Eigenvalue distance solves the single symmetric-tensor rotation problem in the isotropic Frobenius metric. It does not eliminate relative orientation for joint tensors or anisotropic detector covariance. Ricci spectra may distinguish the two supplied witnesses, but do not generally determine a Bianchi presentation. The sharp sign-radius formula is correct for fixed simple-spectrum Q, an ambient Frobenius ball in O, and nonzero chirality. Uncertain Q or a fixed-norm O sphere is another domain.

**Optics and CBL.** The Jordan diagnostic is Hermitian and covariant under the given anti-Hermitian connection, but it is not a new metric field equation. Its decomposition separates terms algebraically conditional on W; it does not estimate both terms from one unknown transfer. Xi is a relative-transmission statistic; normalized Choi shape carries different channel information. The distance scale interval is attained under the stated CP rescaling and transmission inequalities. Q_in=A*(I) and Q_out=A(I) have different normalization roles. Inverse-square-root/log perturbation bounds need a common positive spectral lower bound. Redshift derivatives need their own regularity/error control.

The scalar opacity identity cancels the squared first-derivative term exactly. The lower-derivative curvature relation has the correct positive sign `kappa'=2d' C/d³`. The displayed opacity box is an outer interval, not a guarantee of an opacity function attaining all pointwise extremes. CBL needs its qualified independent H and geometric distance assumptions; an arbitrary direction-dependent fit is not automatically that H. The local Hubble bound separately retains finite-distance and opacity errors.

**Statistics and the common physical remainder.** In the fixed Gaussian experiment with known C, fixed design/nuisance and supplied deterministic ellipsoid, the joint Gram is an error image, not a covariance. The singular-value parameter-bias bound and noncentral-chi-square uniform radius are correct. Exact normality of the standardized estimator is conditional on these assumptions. Estimated covariance, adaptive model selection or a data-derived physical bound requires additional justification. Rank-deficient directions remain a kernel/cylinder; a pseudoinverse does not set their physical value to zero.

For the fibre experiment, conditionally on each informative count n_k, the retained count is Binomial(n_k,p_k). Each two-sided Clopper–Pearson interval has at least its allocated coverage, including `[0,1]` for n_k=0. The union bound across six intervals gives a common event of at least 95%, without requiring independence for that guarantee. Averaging over random n_k preserves it. Its projected physical image therefore inherits coverage. The Wald ellipsoids and their slightly subnominal simulated coverage are explicitly approximate; they must not be substituted for this exact event. The deterministic channel/coarse-graining comparisons do not manufacture independent data or a second likelihood.

## 4. Remaining scientific obligations

1. Supply a physically qualified observation adapter and calibration/derivative budget for one chosen target, then push the joint event through it. This is a concrete next experiment; it is not a need to rebuild all kinetic evolution.
2. Compare any claimed gain with the same acquired observations, nuisance assumptions, physical error class and full-law/GLS baseline. Extra analyzers, paths or photons must be counted as additional design resources when they are genuinely added.
3. Keep geometric, internal-channel and morphology labels separate until a matter/transport response connects them. Preserve nonconvex family labels alongside supports.
4. Keep the identified grey/frame/source directions visible until an independent calibrated response constrains them. Do not convert a convenient convention into a measurement.
5. Retain source-appropriate attribution: MF02/main identities and existing R36 outputs are reused; the present application combinations and finite controls are derived/computed here; empirical detection and broad classification remain unperformed.

## 5. Targeted closure readback

The assembled report's new opening synthesis and final continuation/reproducibility sections were read directly. They preserve the conditional scientific scope, distinguish the four original goals, and make no additional empirical or priority claim. GOAL2 now explicitly uses physical u and normalized u/c. The final fibre note distinguishes phase-only helicity transport from calibrated conversion, physical analyzer reversal from outcome relabeling, the six-dimensional finite natural-parameter span from a local score, and approximate Wald coverage from the exact common event.

The sign-only repair uses the integer statistic `(2K_+z-n_+z)-(2K_-z-n_-z)`; its coefficient in the log likelihood ratio is positive for the stated alternative. Exact zeros receive independent equal-probability class predictions. The recorded 98,086 successes, 155 ties and 98,012 strict successes in 100,000 draws are mutually consistent; the half-tie expectation is 98.0895%. This targeted repair changes no coverage/power/current calculation. Its old result and exact seeds remain in `sources/fibre_info_SIGN_REPAIR.json`. The assembled report should use the revised lane paragraph.

**Bounded review closed: no unresolved scientific defect identified within the inspected finite constructions.** The result remains conditional on the physical and statistical inputs in §3, with the concrete empirical obligations in §4. This conclusion does not change any prior formal acceptance state and does not certify all historical claims.
