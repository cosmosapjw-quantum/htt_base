# Statistical foundations and the strongest comparison methods

Date: 28 October 2026. Scope: primary-source R2/R3 comparison under PhysMath Research Loop 1.3.0. The original physical target is retained: observed morphology, a qualified radiation/optical response, constraints on kinematics, and comparison with an FLRW or anisotropic physical family. This lane does not fit Gaia rows, run a solver, change a repository, or adjudicate the numerical Gaia experiment.

## Assessment

The five objects $(x,F,Q,\Pi,G_F)$ can organize a physically interpretable inference method, but their joint notation is not itself a new statistical theory. The strongest comparison is nuisance-hardened score/GLS compression, augmented with the modes required for alternative models and lack-of-fit. Two primary papers particularly sharpen the proposed experiment: **Heavens, Sellentin and Jaffe (2020), MOPED-PC**, explicitly preserves extra modes for new physics; **Heavens et al. (2023)** studies combined compression for model comparison. Both are closer to the intended purpose than a comparison only with scalar power.

The useful possible contribution is an explicit physical construction: derive which radiation/optical response directions and finite remainders must survive compression; propagate one common observation event to several kinematic targets; and demonstrate calibrated physical discrimination on the same saved law used by the optimal baseline. That contribution can survive exact equality with GLS at fixed linear Gaussian assumptions. An information gain over GLS under identical assumptions cannot.

## Verified prior-art map

| Primary source | What is already available | Consequence for the HTT comparison |
|---|---|---|
| [Heavens, Jimenez and Lahav 2000](https://arxiv.org/abs/astro-ph/9911102), MNRAS 317, 965 | MOPED linear combinations retain Fisher information when the covariance is fixed and the response is evaluated at the relevant parameter point. | “Fewer coordinates” need not mean “less information”. |
| [Alsing and Wandelt 2018](https://arxiv.org/abs/1712.00012), MNRAS Letters 476, L60 | Score compression, with linear and quadratic Gaussian terms; section 3, equation (17). | Use score compression as an optimal comparator. General score preservation is local in parameter space; the affine Gaussian case is stronger. |
| [Alsing and Wandelt 2019](https://arxiv.org/html/1903.01473v1), MNRAS 488, 5093 | Equation (11) gives nuisance-hardened scores from a local/Laplace construction, with leading-order nuisance insensitivity. | Hardening does not recover information in the discarded nuisance tangent directions. Distinguish this approximation from an exact fixed-design projection. |
| [Pollard, arXiv:1107.3797v2](https://arxiv.org/pdf/1107.3797) | Theorem 7 gives conditional-expectation scores under differentiability in quadratic mean and the criterion for Fisher preservation. | The conditional-score covariance identity is established. Fisher preservation alone need not imply global sufficiency. |
| [Heavens, Sellentin and Jaffe 2020](https://arxiv.org/abs/2006.06706), MNRAS 498, 3440 | MOPED-PC augments baseline-model compression with additional generalized principal-component modes to retain sensitivity to new physics. | The motivation “preserve information for later alternatives” already has direct prior art. |
| [Heavens, Mootoovaloo, Trotta and Sellentin 2023](https://arxiv.org/html/2306.15998v2), JCAP 11, 048 | Section 2 combines model-specific MOPED summaries and their covariance for Bayesian comparison; exact linear Gaussian cases and nonlinear examples are considered. | The common-family carrier is a useful specialization, not a first general compression theorem. Affine offsets and shared probability laws must be explicit. |
| [Pyne, Joachimi, Gordon and Lin 2026](https://arxiv.org/pdf/2609.04829) | A guide comparing Fisher-, mutual-information- and MSE-based methods; sections 3–6 and appendices. | The quoted reference is real: submitted 4 September 2026, 18 pages, 14 figures, submitted to RASTI. Its comparisons use specified weak-lensing designs, not a universal ranking of methods. |
| [Hall 2019](https://arxiv.org/abs/1811.05454), MNRAS 486, 145 | Spin-weighted harmonic formalism and likelihood-derived optimal estimators for extragalactic proper motions, including correlated transverse velocities. | A full signed vector/likelihood baseline is already physically motivated. |
| [Makarov 2025](https://arxiv.org/abs/2507.01798), Nature Astronomy | Redshift-binned global VSH fits through degree 3; the paper also identifies hidden astrometric systematics as a possible explanation of differences. | Redshift-dependent VSH morphology is not unprecedented and is not automatically a cosmological detection. |
| [Gaia Collaboration 2022](https://arxiv.org/abs/2204.12574), A&A 667, A148 | CRF3 construction and large-angle proper-motion systematics; the abstract reports approximately 12 microarcseconds/year on scales above 15 degrees. | A released per-source or saved working covariance does not by itself establish the cross-source systematic law. |

Exa and SciSpace were used for discovery; claims were checked against author/publisher/arXiv sources. Direct web-tool access to some arXiv/OUP pages failed, but Exa retrieved the relevant primary material. The 2026 guide was read from its arXiv PDF, rather than accepted solely from aggregator metadata. No exhaustive absence-of-prior-art claim is made.

## Three preservation claims that should not be conflated

**Local Fisher preservation.** For a parameter-independent statistic $T$ in a regular model, its score is $s_T=E(s_Y\mid T)$. The law of total covariance gives

$$I_Y-I_T=E[\operatorname{Cov}(s_Y\mid T)]\succeq0.$$

Equality means that the score is recoverable from $T$, almost surely at the parameter point under consideration. Pollard's Theorem 7 supplies a DQM formulation and explicitly separates this criterion from global sufficiency. It would be incorrect to describe the identity as a new HTT theorem, or to infer preservation of every alternative-model likelihood ratio from equality of Fisher matrices at one fiducial point.

**Exact fixed-design Gaussian preservation.** With $y=m_0+J\theta+N\eta+\epsilon$, known fixed $C>0$, and unrestricted deterministic nuisance $\eta$, let

$$P=I-P_{C^{-1/2}N},\quad r=PC^{-1/2}(y-m_0),\quad H=PC^{-1/2}J.$$

Then the profiled log likelihood is $-\|r-H\theta\|^2/2$ plus a common constant. The score-like vector $H^Tr$ and information $H^TH$ preserve its complete parameter-dependent part, not merely a local quadratic approximation. Rank deficiency identifies only the range of $H$. A proper Gaussian nuisance prior generally changes the covariance rather than producing this same projection. Different nuisance spaces, parameter-dependent covariance and nonlinear responses require a new derivation.

**Fidelity of the physical target.** A statistic can be sufficient for an incorrectly specified response model. Statistical optimality does not turn a quasar centroid into a matter worldline, turn a measured E-mode into positive bolometric brightness, or supply a transport derivative. These are response/source requirements. The HTT construction is valuable when it makes them mathematically operational and uses them to define a better target or a controlled uncertainty class.

For parameter-dependent Gaussian covariance, the score contains both

$$\mu_{,i}^{T}C^{-1}(y-\mu)
+\tfrac12(y-\mu)^TC^{-1}C_{,i}C^{-1}(y-\mu)
-\tfrac12\operatorname{tr}(C^{-1}C_{,i}).$$

Mean-only linear compression is not generally sufficient in this case. A nonlinear physical normalization also does not remove this requirement.

## Common response families and the residual needed for new physics

For finitely many fixed-covariance affine families, project the same common nuisance and retain the span of all projected mean differences:

$$\mathcal S=\operatorname{span}\{PC^{-1/2}(\mu_k(\theta)-m_0):k,\theta\}.$$

If every family has common baseline $m_0$, this is the column span of the projected $J_k$. Otherwise include the projected offsets $m_{0k}-m_0$ as well. Let $U$ be an orthonormal basis. The factorization

$$\|r-h_k(\theta)\|^2
=\|U^Tr-U^Th_k(\theta)\|^2+\|(I-UU^T)r\|^2$$

shows exact preservation of pairwise profiled likelihood ratios. With proper priors and compatible treatment of the common nuisance, the common factor also cancels from Bayes factors. A profile likelihood alone does not specify such priors or a Bayesian evidence.

The rank of this span is the minimum number of **linear** coordinates needed to preserve the full affine family's likelihood ratios. Do not describe it as a minimum over arbitrary pathological measurable encodings. Combined score compression for competing models has close prior art in Heavens et al. (2023).

An explicit offset control is recorded in `sources/literature/affine_offset_fixture.json`. For $C=I_3$, $\mu_0=(\theta,0,0)$ and $\mu_1=(0,\phi,1)$, the derivative span contains only the first two axes. Independent unit Gaussian parameter priors give full log Bayes factors $+0.5$ and $-0.5$ at $(0,0,0)$ and $(0,0,1)$, while the two-coordinate compression gives zero for both. This does not refute the user's common-$m_0$ result; it fixes the condition for extending it to distinct physical families.

For the question “beyond FLRW?”, keeping model ratios is not enough. The discarded residual

$$q_\perp=\|(I-UU^T)r\|^2$$

is an omnibus lack-of-fit diagnostic under the declared law. An unlisted physical signal entirely in this complement is invisible to $U^Tr$ but changes $q_\perp$. The scalar residual detects excess size but does not retain the direction required to classify a newly proposed family. Store additional physically motivated residual modes, or the residual vector when inexpensive. MOPED-PC (2020) is the direct comparator for this design choice.

## A concrete physical extension worth testing

Suppose a retained response has an omitted whitened, nuisance-projected mean $\delta_k\perp\mathcal S$, with a physically justified bound $\|\delta_k\|\le\epsilon_k$. The exact omitted term in the log likelihood ratio between two candidates is

$$\Delta\log\Lambda_{k\ell}
=r_\perp^T(\delta_k-\delta_\ell)
-\tfrac12(\|\delta_k\|^2-\|\delta_\ell\|^2),$$

and consequently

$$|\Delta\log\Lambda_{k\ell}|
\le\|r_\perp\|(\epsilon_k+\epsilon_\ell)
+\tfrac12(\epsilon_k^2+\epsilon_\ell^2).$$

This elementary certificate follows from orthogonal decomposition and Cauchy–Schwarz. Its prospective contribution is obtaining useful $\epsilon_k$ from MES/radiation moments, optical finite-distance remainders or an instrumental response, then demonstrating a smaller retained carrier at a prescribed inference tolerance. It is not claimed here as a new general statistical inequality. The bound is a likelihood-error statement; frequentist coverage additionally requires a correctly calibrated joint observation event and treatment of any estimated radius.

## How to interpret the Gaia comparison

1. The scientifically strong null comparison is **C = joint GLS/efficient score** versus **D = an invertible tensor representation plus physical set/functionals on the same carrier**. Under identical response and covariance they must give the same likelihood, information, coverage and power for the same test. This is an equivalence benchmark, not a disappointing result.
2. Scalar power/norm is a valid reduced observation with its own generally non-Gaussian law. For a centered Gaussian shift, an even statistic has the same distribution at $\theta$ and $-\theta$. At the signed null its first-order Fisher information is zero, although it can retain information about noncentral amplitude at higher order. Do not use a Gaussian likelihood for a squared norm merely to make the comparator fail.
3. An independent-bin analysis is explicitly a covariance-misspecified control. Signed bin estimates with their correct joint law may already be equivalent to the joint carrier, depending on the estimator row space. Tensor notation alone does not restore correlations discarded elsewhere.
4. Verify what the reported 1.58485% means. A trace information ratio can depend on parameter scaling. Prefer directional retained fractions or generalized eigenvalues of $(I_{\rm eff},I_{\rm raw})$ on their identifiable support; distinguish these from rank, determinant and confidence-volume ratios.
5. Evaluate common physical functionals on one confidence event. Reusing that event for many displayed targets preserves its simultaneous implication; multiplying dependent probabilities derived from the same $x$ does not. These are standard confidence-image principles. A useful HTT advance must show the physical response/finite error construction and a concrete decision improved by it.

The extra factors $F,Q,\Pi,G_F$ should therefore be explicitly typed functionals or operators, with one underlying probability law. If they are deterministic functions of $x$, they add interpretation and decision structure but no new sampling information. A componentwise MES scale is a reference metric, not a probability density. If estimated from the same sky, its randomness and correlations must be propagated; if parameter-dependent, likelihood transformations require the relevant Jacobian or direct pushforward law.

## Publication strategy and present conclusion

The defensible methods claim is **response-qualified, tolerance-controlled physical inference with calibrated comparisons**, supported by exact equality with optimal inference in its valid domain and an advantage over specified information-losing or misspecified alternatives. The most promising distinctive experiments connect an actual MES/optical response remainder to the compression certificate, retain out-of-family diagnostics for an FLRW null, and propagate the same event to several physical families without multiplying correlated summaries.

The statements that tensorization universally outperforms scalar coordinates, that five factors define a novel likelihood, or that nuisance hardening recovers discarded physical information should not be made. This leaves substantial room for original applied mathematics and cosmological methodology, but that room is narrower and more concrete than a new general information geometry. The Gaia saved-law test establishes statistical behavior; source-qualified radiation and astrometric maps establish the physical extension.
