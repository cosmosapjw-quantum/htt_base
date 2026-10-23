# Selection, transport, and partial identification for the solver-free HTT branches

Prepared 2026-10-23. Research-only note; no repository mutation, native Boltzmann solver, ODE integration, or author contact. Primary literature was located through Exa and SciSpace and checked against primary publisher, author, or arXiv pages. The calculations below are mathematical derivations and a small synthetic optimization check, not new fits to the scientific data.

> **Full-tuple scope clarification added by the coordinating author:** the notation below concerns the legacy scalar projection supplied to this subtask. The full tensor-functional/set/path definitions in `THEOREMS.md` T7, the July tensor plan and R9 revision 2 are primary. In particular Q may be an anchor gauge, F separates support/pushforward/occupancy, and the full G_F is a FunctionalDepthPath. This appendix does not redefine that richer framework.

## Status that must remain unchanged

The new 628-target / 274-distance conditional-likelihood candidate **failed its observed residual diagnostic**: `T = 4.5553218238`, `p = 0.0009763241396`. The `3890/4096` mock pass count does not repair that failure. A narrower estimand or sensitivity interval would be a separately labelled result with its own assumptions, not a retrospective acceptance of this candidate. No additional peculiar-velocity or calibration variance should be added when those components are already in the supplied errors/covariance.

The original full-source requirements remain unfulfilled where the named source law is unavailable. The useful change is to register a weaker, explicit scientific claim for which less information is sufficient. No theorem here establishes that its assumptions hold for these data.

## Registered objects and notation discipline

The root supplied the current definitions: `x_C = Sigma_G^2 - W_G^2 + Omega_tilt + DeltaOmega_k`; the shear, vorticity, and `H = Theta/3` are evaluated on the same congruence. `Q = x_C/U_sigma`, with `U_sigma = (3/2) B_sigma^2 > 0`, is a registered SHEAR-sector MES normalizer, not a total bound. `F` is a samplewise normalized sign-clean sector fraction, defined only when the positive ceiling and amplitude-bound requirements are admissible; it is not a volume occupation fraction. `Pi_Q(t)` uses normalized joint-source weights and strict exceedance `Q_i > t`, plus unknown completion. `G_F = max(F_comparison, delta)/max(F_reference, delta)` uses a predeclared positive floor and matched bins, sky, selection, normalization, and covariance.

The exact tensor carrier itself was not supplied to this subtask. Nothing below assigns new meanings to its components. Once its observation map is specified, the results apply to its registered measurable outputs `(x, F, Pi, Q, G_F)` and to explicitly declared subfunctionals. Statistical selection weights below are **not** the physical joint-source weights `p_i`, and do not make physical unknown mass disappear. The root checked that production `G_F` is formed from the bin records' `f_value` summaries: the joint inputs to its bound below must be those production summaries. A per-draw ratio and an expectation of ratios are distinct estimands and must not replace the production ratio of bin summaries.

## What the primary literature actually permits

| Literature result | Exact useful reduction and conditions | Limit in this project |
|---|---|---|
| Mandel, Farr & Gair, selected population likelihood [R1] | For observed data selected by a known data rule, the selected likelihood is normalized by the model probability of detection. A latent detection factor cannot simply be multiplied into a numerator while ignoring dependence on the observed data. | Conditioning on observed target properties removes their marginal law only if the remaining response law, including response-dependent quality cuts, is justified. |
| Fithian, Sun & Taylor, selective inference [R2] | Control error conditional on the actual selection event; exponential-family conditioning can remove sufficient nuisance statistics. | Conditioning is useful information reduction, not a proof that an unknown catalogue selection event is ignorable. |
| Aronow & Lee, bounded inclusion probabilities [R3] | Sharp bounds on a Hájek mean over a posited range of finite-population inclusion probabilities. | Requires a defensible range and sampling framework; arbitrary catalogue weights are not inclusion probabilities. |
| Zhao, Small & Bhattacharya [R4]; Dorn & Guo [R5] | Marginal selection-odds sensitivity gives optimization-based bounds; conditional normalization/quantile constraints can tighten them to sharp identification bounds. Their inference results have stated regularity and overlap assumptions. | A chosen sensitivity parameter is an assumption. Bootstrap and quantile regression cannot certify an unobserved physical response kernel. |
| Tudball et al. [R6] | Population moments, response rates, and other justified constraints restrict a partial-identification optimization. Estimated constraints need a confidence relaxation; their Theorem 1 allocates separate errors to constraint containment and objective inference. | Do not impose uncertain catalogue summaries as exact constraints or borrow moments from an unmatched frame. |
| Imbens & Manski [R7] | Distinguish confidence coverage of one true parameter from simultaneous coverage of its entire identified set; naive endpoint procedures can fail uniformity near point identification. | A reported outer interval must say which coverage claim it makes. |
| Berger & Boos [R8] | Maximize a valid nuisance-specific p-value over a confidence set for the nuisance, and add the confidence-set error. | Requires valid p-values at each nuisance value; taking a supremum of invalid model p-values is not a repair. |
| Josey et al. [R9]; Chernozhukov et al. [R10] | Covariate balancing, orthogonal scores, and cross-fitting can avoid reconstructing the entire selection law when suitable outcome exchangeability and overlap hold. | Double robustness concerns nuisance estimation, not unmeasured optical-to-kinematic nonexchangeability. |
| Efron & Petrosian [R11] | A specified truncation region and the relevant independence null support a conditional/rank test without fitting a full bivariate density. | An undocumented multilayer targeting/quality/group selection law is not automatically a known truncation region. |
| White [R12] | Under misspecification, quasi-likelihood can estimate a well-defined limiting target with appropriate covariance methods. | The limiting target need not be the physical parameter; sandwich errors do not validate a rejected residual law. |

## Result 1 — Sharp selection sensitivity without a full joint source law

**Status:** standard density-ratio/partial-identification mathematics, derived explicitly here for a useful HTT output. Related literature: [R3–R6]. The application and notation are new to this note; methodological novelty is not established.

Let `S` indicate response availability, `Z` be recorded frame covariates, and `Y` be a **specified observable output**, not automatically physical `Q`. At a fixed `Z=z`, write

\[
e=P(S=1\mid Z=z),\quad P_1=\mathcal L(Y\mid Z=z,S=1),\quad
s(y)=P(S=1\mid Y=y,Z=z).
\]

Assume `0 < e < 1`, finite first moment, common support, and the sensitivity restriction

\[
\Gamma^{-1}\leq\frac{s(y)/(1-s(y))}{e/(1-e)}\leq\Gamma,\qquad\Gamma\geq1.
\tag{1}
\]

Bayes' rule gives the equivalence

\[
r(y)=\frac{dP_0}{dP_1}(y)=\frac{e[1-s(y)]}{(1-e)s(y)},\qquad
\Gamma^{-1}\leq r\leq\Gamma,\quad E_1r=1.
\tag{2}
\]

Conversely, any normalized `r` in (2) defines `P_0=rP_1` and `s=e/[e+(1-e)r]`, satisfying (1). Thus the feasible set is exact, not just a necessary relaxation.

For any event `A`, including a **strict** exceedance, put `q_1=P_1(A)`. Then

\[
\boxed{\max\{q_1/\Gamma,\;1-\Gamma(1-q_1)\}
\leq q_0\leq
\min\{\Gamma q_1,\;1-(1-q_1)/\Gamma\}.}
\tag{3}
\]

Both bounds are sharp. Proof: on `A`, bounds on `r` give `q_1/Gamma <= q_0 <= Gamma q_1`; on its complement, normalization gives the second pair. A density ratio constant on each of `A` and its complement attains every feasible endpoint (with the evident treatment of zero-probability sets). The target event probability is `e q_1 + (1-e) q_0`, so (3) directly gives its sharp interval. With covariates, apply (3) conditionally and integrate over a justified target distribution of `Z`; do not integrate over the selected covariate distribution unless that is the estimand.

For a real output with selected mean `mu_1` and generalized quantile `H_1^{-1}`, let `tau=Gamma/(1+Gamma)`. The sharp unobserved conditional-mean endpoints are

\[
\mu_0^+=\frac{\mu_1}{\Gamma}+
 (\Gamma-\Gamma^{-1})\int_{\tau}^{1}H_1^{-1}(v)\,dv,
\qquad
\mu_0^-=\frac{\mu_1}{\Gamma}+
 (\Gamma-\Gamma^{-1})\int_{0}^{1-\tau}H_1^{-1}(v)\,dv.
\tag{4}
\]

Proof: maximization places `r=Gamma` on the largest `1/(Gamma+1)` selected probability mass and `r=1/Gamma` elsewhere; if the cutoff is an atom, split its weight to preserve `E_1 r=1`. A swapping argument shows that allocating more weight to a smaller value cannot improve the maximum. Reversing the order gives the minimum. `Gamma=1` gives equality to the selected mean. Formula (4) handles atoms and ties; naive empirical quantile thresholding without fractional cutoff mass need not.

**A bound requiring even less.** For a fixed 628-target frame and a bounded response `0 <= Y_i <= 1`, if the 274 observed responses are known exactly and the other 354 are unobserved, the deterministic full-frame mean lies in

\[
\left[\frac{1}{628}\sum_{i:S_i=1}Y_i,
\quad\frac{1}{628}\sum_{i:S_i=1}Y_i+\frac{354}{628}\right].
\tag{5}
\]

Its width is `0.5636942675`; this reflects actual missing information. Equation (5) needs no random selection law. With measurement uncertainty, replace observed values by a simultaneous confidence set as in Result 2. Here `274/628=0.4363057325` is a frame fraction, **not** an individually calibrated propensity, and certainly not physical normalized source mass. The bounded `Y` assumption is natural for an admissible fraction or an event indicator; it does not bound `x` or `Q` without their own justified domain.

**Inference distinction.** Equations (3–4) are population identification bounds. Estimated `e`, distributions, target moments, or kernel constraints add uncertainty. Use simultaneous uncertainty sets and projection, or the specific asymptotic procedures whose assumptions are verified [R4–R7]. A plug-in sensitivity range is not automatically a confidence interval.

## Result 2 — Observable identification and finite outer coverage

**Status:** elementary identified-function and confidence-set projection results, specialized here to the registered outputs. Literature context: [R6–R8]. No novelty claim.

### 2A. Only the relevant pushforward must be identified

Let a candidate source law `P` and a specified observation kernel produce observed law `O(P)`. Define the observational equivalence class

\[
\mathcal E(\nu)=\{P:O(P)=\nu\}.
\]

A functional `theta(P)` is identified by the observed law exactly when it is constant on each equivalence class. If not, its identified set is `{theta(P):P in E(nu)}`. For a statistic `T`, a source-model generator is unnecessary **if** a known null law of `T` (or a known valid stochastic envelope) is proved valid across the entire registered null collection of admissible source laws, e.g. by an analytic pivot or justified conditional exchangeability. Invariance merely within one observational equivalence class is automatic and is not sufficient to supply a known null distribution. This is a condition to establish, not permission to assume a catalogue bootstrap is that null law.

Proof: if two source laws have the same observed law but different functionals, no observed-data procedure can distinguish their functional values. If the functional is constant, define it directly on the observed-law class. Similarly, every test has the same rejection probability under two observationally equivalent laws; a source null and alternative sharing such a law cannot be distinguished with nontrivial power beyond size. Conversely, a common valid statistic law supplies a test without identifying all latent coordinates.

For H02, this gives a precise alternative: register an **observable/conditional null**, prove the statistic law or envelope, and label the resulting test accordingly. It cannot establish the original full-population source null when the source property varies within `E(nu)`. A physical unknown mass of one can coexist with useful conditional optical inference.

### 2B. A simultaneous set gives finite outer coverage without a sampling selection law

Let `v` contain the finite-frame latent outputs and shared nuisance quantities. Suppose an observed-data set `C(D)` satisfies

\[
\inf_{v\in\mathcal V}P_v\{v\in C(D)\}\geq1-\alpha.
\tag{6}
\]

For any preregistered measurable functional `h`, define

\[
I_h(D)=\left[\inf_{v\in C(D)}h(v),\ \sup_{v\in C(D)}h(v)\right].
\tag{7}
\]

Then `P_v{h(v) in I_h(D)} >= 1-alpha` uniformly, since `v in C` implies `h(v) in I_h`. No stochastic sampling model for the finite list is used in this proof. No independence across galaxies or groups is used. Independent marginal intervals are unnecessary: a joint covariance ellipsoid, calibrated non-Gaussian set, or Bonferroni rectangle can be used if (6) is valid. Bonferroni allocation `sum alpha_i <= alpha` works with arbitrary dependence but can be wide.

**Selection caveat:** (6) must hold for the declared experiment. Ordinary unconditional measurement intervals can lose coverage after selection on the same noisy measurements. One valid route is simultaneous coverage on a prespecified parent frame before selecting a subset; another is genuinely selection-conditional coverage. An undocumented optical-to-kinematic kernel prevents one from asserting (6) for physical quantities merely because optical intervals exist.

For physical `Pi_Q(t)`, suppose joint source IDs and nonnegative weights are retained, `sum_known p_i = 1-u`, and the admissible physical completion is otherwise unrestricted. If all known `Q_i` are exact,

\[
\Pi_Q(t)\in\left[\sum_{known}p_i\mathbf1\{Q_i>t\},
\quad\sum_{known}p_i\mathbf1\{Q_i>t\}+u\right].
\tag{8}
\]

For simultaneous closed bounds `ell_i <= Q_i <= r_i`, a conservative outer interval is

\[
\boxed{\left[\sum_i p_i\mathbf1\{\ell_i>t\},
\quad u+\sum_i p_i\mathbf1\{r_i>t\}\right].}
\tag{9}
\]

Strict ties are preserved: `ell_i=t` does not guarantee exceedance, and `r_i=t` does not permit it. Projection over a joint `C` retains stronger coupling and can tighten (9). Rectangular endpoint optimization is sharp only if those endpoint choices are jointly admissible. If normalization weights are uncertain, optimize jointly over them as well; do not move the weights after inspecting threshold labels. If `u=1`, the physical interval remains `[0,1]`.

For production `G_F`, let `f_c` and `f_r` denote the exact comparison/reference bin-summary functionals used as `DepthBinFRecord.f_value`, not individual samplewise fractions or an average of samplewise ratios. Propagate the joint source/measurement set through those summary functionals, then project the resulting **joint** set:

\[
\left[\inf_{(f_c,f_r)\in C_F}
\frac{\max(f_c,\delta)}{\max(f_r,\delta)},
\quad\sup_{(f_c,f_r)\in C_F}
\frac{\max(f_c,\delta)}{\max(f_r,\delta)}\right].
\tag{10}
\]

If only a containing rectangle `[a,b] x [c,d]` is available, the conservative interval is

\[
\left[\frac{\max(a,\delta)}{\max(d,\delta)},
\quad\frac{\max(b,\delta)}{\max(c,\delta)}\right].
\tag{11}
\]

Its endpoints need not be attainable under shared errors, bins, or source coupling. Do not independently resample the numerator and denominator. If a different analysis explicitly registers a per-draw ratio, the same projection theorem applies to that different map, but it is not the production `G_F`. A fixed positive floor makes this map continuous; for admissible fraction summaries in `[0,1]` and `0<delta<=1`,

\[
|g(a,b)-g(a',b')|\leq |a-a'|/\delta+|b-b'|/\delta^2.
\tag{12}
\]

This follows from the 1-Lipschitz maximum map and `|1/v-1/v'| <= |v-v'|/delta^2`. It quantifies why a very small floor can greatly magnify uncertainty. Undefined `F` values must remain undefined or explicitly part of the unknown completion; flooring a valid `F` is not a rule for imputing inadmissible `F`.

For a nuisance-dependent null, if `C_beta(D)` covers the true nuisance with probability at least `1-beta`, and every `p_eta(D)` is a valid p-value under its own null, then [R8]

\[
p_{BB}=\min\{1,\sup_{\eta\in C_\beta(D)}p_\eta(D)+\beta\}
\tag{13}
\]

is valid. Proof: for `alpha>=beta`, rejection on the event `eta_true in C_beta` implies `p_eta_true <= alpha-beta`; add the at-most-`beta` failure probability. Independence between the set and p-values is not needed. Numerical optimization must provide an upper bound for the supremum; a coarse grid without a certified envelope can understate it. This does not validate the currently failed conditional likelihood.

## Result 3 — Transport bias, orthogonality, and the exact limit of covariance repair

**Status:** a standard doubly robust identity and matrix derivative, combined for this application; literature foundations [R9–R10,R12]. Novelty unestablished.

Let `P_s` denote a selected source sample, `P_t` a specified target frame/distribution, `Z` recorded covariates, and `Y` a declared output measured in the selected source. Assume target support is contained in source support, with density ratio `r_0=dP_t^Z/dP_s^Z`. Write

\[
\mu_s(z)=E_s(Y\mid Z=z),\qquad
\mu_t(z)=\mu_s(z)+b(z),\qquad\theta_t=E_t\mu_t(Z).
\]

For candidate functions `m` and `r`, define the two-sample augmented mean

\[
\Psi(m,r)=E_t m(Z)+E_s[r(Z)\{Y-m(Z)\}].
\]

Then the exact error identity is

\[
\boxed{\Psi(m,r)-\theta_t
=E_s[(r_0-r)(m-\mu_s)]-E_t b.}
\tag{14}
\]

Proof: replace `Y` by its conditional mean, express `E_t` as `E_s r_0`, and collect terms. If `b=0`, either a correct response regression or a correct density ratio makes the bias zero; the first derivative in either nuisance at `(mu_s,r_0)` is zero. More generally,

\[
|\Psi-\theta_t|\leq\|r-r_0\|_{L^2(P_s)}\|m-\mu_s\|_{L^2(P_s)}+E_t|b|.
\tag{15}
\]

Cross-fitting makes empirical counterparts usable under appropriate independent-unit/independent-cluster sampling, overlap, moments, and nuisance convergence; a familiar sufficient product-rate condition is `||rhat-r0||_2 ||mhat-mus||_2 = o_p(n^-1/2)` with both nuisances consistent and controlled empirical variance. Split at the independent group level, not at individual rows when groups share noise. This is asymptotic inference, not automatic finite-sample coverage. Covariate balancing may replace full `r` estimation for a restricted outcome function class [R9].

The `b` term is the key S02/K04 limit. If an optical response is transported to a kinematic physical output, its unknown response bias is not removed by fitting selection weights. If a justified bound `|b(z)|<=B(z)` exists, enlarge the result by `E_t B`; if no such bound exists, report the optical estimand without a physical relabelling. For event responses, a justified joint-kernel sensitivity assumption `TV(K_true(z),K_ref(z))<=epsilon(z)` implies

\[
|P_t(Y\in A)-P_t^{ref}(Y\in A)|\leq E_t\epsilon(Z).
\tag{16}
\]

For an output in `[a,b]`, replace the right side by `(b-a) E_t epsilon`. This follows directly by integrating the event/expectation definition of total variation. The assumption concerns the relevant response kernel; it is not estimated from optical-only values merely by having 2048 IDs. The kernel must be joint when the output couples sources, sectors, or numerator/denominator quantities.

There is a separate, restricted covariance orthogonality. For residual vector `R=Y-m(theta_0,Z)` with `E(R|Z,training)=0`, deterministic/cross-fitted design `D(Z)`, and positive-definite weight matrix `C(Z,training)`, consider

\[
\psi_C=D^T C^{-1}R.
\]

Its conditional mean is zero for every such `C`, and in direction `H`,

\[
\partial_C E\psi_C[H]=-D^T C^{-1}HC^{-1}E R=0.
\tag{17}
\]

Thus a suitable mean-parameter estimating equation can be insensitive at first order to covariance estimation. Valid standard errors still require the correct sandwich/group structure and suitable regularity. In contrast, for fixed covariance weighting (or conditionally on independent training, with conditional moments), a quadratic residual diagnostic satisfies

\[
E[R^T\widetilde C^{-1}R]
=\operatorname{tr}(\widetilde C^{-1}C_0)
 +b_R^T\widetilde C^{-1}b_R,
\tag{18}
\]

where `b_R=E R` and `C_0=Cov(R)`. It is sensitive to covariance mismatch and mean misspecification, and is not made orthogonal by (17). Consequently neither a sandwich covariance nor extra already-counted PV/calibration variance repairs the reported failed residual test. A revised model must explain the failure and face an appropriately fresh or selection-adjusted validation claim.

## Concrete branch transitions, without changing original acceptance status

| Blocker | A genuinely weaker result that can be attempted | Evidence still required |
|---|---|---|
| CF4 targeting / quality / PGC / group / method law unknown | A named fixed-frame or selected-catalogue estimand; bounded missing-output interval (5); or a registered `Gamma` sensitivity curve (3–4) if its setup is justified. | Frame definition, target response, record linkage, group covariance, and measurement coverage. For point transport, relevant target covariates and exchangeability/overlap; the 628/274 count alone is insufficient. |
| H02 full population source null and generator missing | Observable-statistic or conditional-null test whose pushforward law/envelope is proved, optionally using (13). | Proof of pivot/exchangeability/envelope for that null. It must be labelled different from the original source null; rejected current residual law cannot be reused as a valid pivot. |
| S02 optical-to-kinematic joint kernel unknown for 2048 IDs | Finite optical functional with retained joint IDs; physical partial identification only through a justified joint response set or explicit kernel-sensitivity parameter (16). | Response calibration/structural bound in the same frame; otherwise physical unknown mass remains. No independent rematching or fabricated optical–kinematic coupling. |
| S04 selected likelihood unavailable | A separately named finite-frame outer confidence interval via (6–11), with its precise coverage target recorded. | Simultaneous measurement coverage for the actual selection experiment and admissible physical map. This can unblock a narrower deliverable without passing the original selected-likelihood criterion. |
| K04 same-frame optical response missing | Matched optical contrast or transported output with explicit `b` sensitivity; joint `G_F` interval (10). | Same frame, bins, sky, selection, normalizer, floor, and covariance; response-bias bounds if used physically. |

Recommended implementation order: (i) freeze estimand, frame, group structure, and undefined-value rules; (ii) record which constraints are physical and which are statistical sensitivity assumptions; (iii) produce the unconditional finite-frame outer bound first; (iv) tighten only with independently justified moment, selection-odds, or response constraints; (v) project jointly to `Pi_Q` and `G_F`; (vi) report both identification width and statistical uncertainty. Register any model changes after the residual failure explicitly and separate exploratory fit improvement from confirmatory validation.

## Small computational check

Synthetic verification only, seed `20261023`: 180 discrete-distribution cases, support sizes 3, 7, 23 and `Gamma` in `{1, 1.1, 1.5, 2, 5, 20}`. Formula (4) was checked against exact finite-dimensional linear programming with constraints `sum p_j r_j=1`, `1/Gamma<=r_j<=Gamma`; (3) was checked against its two-cell LP. Largest absolute discrepancy: `9.325873406851315e-15`. This verifies algebra and atom handling numerically; it provides no evidence for a scientific selection assumption, physical model, or original acceptance condition.

## Primary references

- **R1.** Mandel, I., Farr, W. M., & Gair, J. R. (2019), “Extracting distribution parameters from multiple uncertain observations with selection biases,” *MNRAS*. DOI: [10.1093/mnras/stz896](https://doi.org/10.1093/mnras/stz896). [Primary manuscript](https://arxiv.org/abs/1809.02063); [full text](https://ar5iv.labs.arxiv.org/html/1809.02063).
- **R2.** Fithian, W., Sun, D., & Taylor, J. (2014; revised 2017), “Optimal Inference After Model Selection.” [Primary manuscript](https://arxiv.org/abs/1410.2597), DOI: [10.48550/arXiv.1410.2597](https://doi.org/10.48550/arXiv.1410.2597).
- **R3.** Aronow, P. M., & Lee, D. K. K. (2013), “Interval estimation of population means under unknown but bounded probabilities of sample selection,” *Biometrika* 100, 235–240. DOI: [10.1093/biomet/ass064](https://doi.org/10.1093/biomet/ass064). [Publisher](https://academic.oup.com/biomet/article/100/1/235/193266).
- **R4.** Zhao, Q., Small, D. S., & Bhattacharya, B. B. (2019), “Sensitivity Analysis for Inverse Probability Weighting Estimators via the Percentile Bootstrap,” *JRSS B* 81, 735–761. DOI: [10.1111/rssb.12327](https://doi.org/10.1111/rssb.12327). [Author page](https://www.statslab.cam.ac.uk/~qz280/publication/sensitivity-ipw/).
- **R5.** Dorn, J., & Guo, K. (online 2022), “Sharp Sensitivity Analysis for Inverse Propensity Weighting via Quantile Balancing,” *JASA*. DOI: [10.1080/01621459.2022.2069572](https://doi.org/10.1080/01621459.2022.2069572). [Primary manuscript](https://arxiv.org/abs/2102.04543); [author PDF](https://jacobdorn.info/files/QuantileBalancing.pdf). Marginal odds model: equation (2); normalization and sharpness are central, not optional weight constraints.
- **R6.** Tudball, M. J., Hughes, R. A., Tilling, K., Bowden, J., & Zhao, Q. (2023), “Sample-constrained partial identification with application to selection bias,” *Biometrika* 110, 485–498. DOI: [10.1093/biomet/asac042](https://doi.org/10.1093/biomet/asac042). [Primary full text](https://academic.oup.com/biomet/article/110/2/485/6649721). Theorem 1 requires its stated assumptions 1–6 and a relaxed constraint set containing the population set with the allocated asymptotic confidence; it is not an unconditional finite-sample theorem.
- **R7.** Imbens, G. W., & Manski, C. F. (2004), “Confidence Intervals for Partially Identified Parameters,” *Econometrica* 72, 1845–1857. DOI: [10.1111/j.1468-0262.2004.00555.x](https://doi.org/10.1111/j.1468-0262.2004.00555.x). [Author PDF](https://scholar.harvard.edu/files/imbens/files/confidence_intervals_for_partially_identified_parameters.pdf). Section 3 treats bounded missing outcomes; uniformity near point identification is substantive.
- **R8.** Berger, R. L., & Boos, D. D. (1994), “P Values Maximized Over a Confidence Set for the Nuisance Parameter,” *JASA*. DOI: [10.1080/01621459.1994.10476836](https://doi.org/10.1080/01621459.1994.10476836); [JSTOR DOI](https://doi.org/10.2307/2290928).
- **R9.** Josey, K. P., Berkowitz, S. A., Ghosh, D., & Raghavan, S. (2021), “Transporting Experimental Results with Entropy Balancing,” *Statistics in Medicine* 40, 4310–4326. DOI: [10.1002/sim.9031](https://doi.org/10.1002/sim.9031). [Primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC8487904/). Their treatment-effect transport theorem uses exchangeability, sampling positivity, and treatment-assignment conditions plus stated model assumptions; it is cited as methodology, not transplanted literally to galaxy data.
- **R10.** Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018), “Double/debiased machine learning for treatment and structural parameters,” *The Econometrics Journal* 21, C1–C68. DOI: [10.1111/ectj.12097](https://doi.org/10.1111/ectj.12097). [Primary full text](https://academic.oup.com/ectj/article/21/1/C1/5056401).
- **R11.** Efron, B., & Petrosian, V. (1992), “A simple test of independence for truncated data with applications to redshift surveys,” *ApJ*. DOI: [10.1086/171931](https://doi.org/10.1086/171931). [Primary institutional report](https://statistics.stanford.edu/technical-reports/permutation-tests-independence-truncated-data-applications-redshift-surveys-0).
- **R12.** White, H. (1982), “Maximum Likelihood Estimation of Misspecified Models,” *Econometrica* 50, 1–25. DOI: [10.2307/1912526](https://doi.org/10.2307/1912526). [Publisher page](https://www.econometricsociety.org/publications/econometrica/1982/01/01/maximum-likelihood-estimation-misspecified-models).

**Novelty/acceptance ledger:** Literature results are attributed above. Equations (3–18) are explicit elementary derivations/adaptations for the stated assumptions; no priority or methodological novelty is asserted. Scientific applicability remains conditional. Original CF4/H02/S02/S04/K04 acceptances are not marked passed, and the new 628/274 conditional likelihood remains failed.
