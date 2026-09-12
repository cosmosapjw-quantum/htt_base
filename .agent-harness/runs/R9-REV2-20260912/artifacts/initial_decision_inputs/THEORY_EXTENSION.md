# R9 revision 2: dependent paths and tensor confidence images

Owner: HTT/common for laws and confidence sets; MIO for diagnostic views. Status: **directly derived research**, supported by bounded reference experiments and blind derivations. Not four-axis CAS admission, production validation, observational inference, or a novelty claim. Mathematical statements below are scoped results; standard Gaussian linear algebra is not presented as newly discovered statistics.

Seed: the compendium at `d514eabdbd6a464a92ff6e51e1aba91399a054db`, §§9.3, 13.2, 18–23, 26–28. The source `depth_path.py` is separately pinned to `6bafca66285ef071081453313bb7d2d6b261599c`; it is not assumed merged into this branch. R9's existing response/law and alpha contracts remain controlling. Observable temperature Q/O and physical shear/vorticity are different state spaces.

## D1. The whole depth law, including cross-step blocks

Let ordered, fixed feature vectors be \(Y_j\in\mathbb R^{d_j}\), with joint law \(Y\sim N(\mu,C)\), \(C\succeq0\). Let fixed \(K_j:\mathbb R^{d_j}\to\mathbb R^{d_{j+1}}\) transport features. Define \(r_j=Y_{j+1}-K_jY_j\) and the block difference matrix H. Then

\[
r=HY,\quad E[r]=H\mu,\quad V=HCH^T,
\]
\[
V_{jk}=C_{j+1,k+1}-C_{j+1,k}K_k^T-K_jC_{j,k+1}+K_jC_{jk}K_k^T.
\]

This follows by linearity of Gaussian maps and bilinearity of covariance. PSD follows from \(a^TVa=(H^Ta)^TC(H^Ta)\ge0\). The familiar two missing within-edge terms are only the diagonal blocks of this formula. Even independent original blocks have adjacent residual covariance \(-C_{j+1,j+1}K_{j+1}^T\).

For three independent unit scalar inputs and K=1,

\[
V=\begin{pmatrix}2&-1\\-1&2\end{pmatrix}.
\]

Deleting its off-diagonal terms gives a quadratic with law \(\tfrac12 Z_1^2+\tfrac32 Z_2^2\), not \(\chi^2_2\). Its expectation is still 2; matching the mean cannot validate a tail. The exact 5% nominal rejection probability is 0.0595427643. Our 100,000-draw reference run gives 0.05854; using V gives 0.04995. This is a synthetic counterexample, not an estimated survey failure rate.

In the donor, lines 1108–1111 add only marginal covariance terms; lines 1149–1170 average cell scores. Those operations support a restricted/descriptive interpretation. The revision specifies the general law but does not patch an unmerged production module by silently changing its API. Consumer: R9-24–27.

## D2. Singular support comes before a quadratic

For a fixed candidate mean, put \(z=r-H\mu(\theta)\), \(s=\operatorname{rank}V\). Require \(z\in\operatorname{Im}V\). On that support,

\[
z^TV^+z\sim\chi^2_s.
\]

Diagonalize on the positive eigenspace to obtain s independent standard normals. Outside support the candidate law is incompatible regardless of the pseudoinverse quadratic. If s=0, equality of r and Hμ is deterministic and a score divided by s is undefined. A numerical tolerance is an approximation policy, not a proof of an exact nullspace. The reference code uses explicit small-matrix tolerances and does not certify rank under measurement or numerical error.

For three copies of the same random variable, C is all ones and V=0. A nonzero contrast is impossible; a bare pseudoinverse would incorrectly give zero quadratic. No jitter may turn this known constraint into artificial noise. An unavailable covariance is a different state from a known zero covariance.

If covariance, transport, mean fit, selection, or nuisance projection is estimated using the same data, the fixed-law chi-square assertion does not automatically apply. If support changes with the candidate, pseudodeterminant likelihood values on different support measures cannot be compared without a common measure/model specification. The existing candidatewise inversion can still be defined through each candidate's own valid test.

## D3. Contrasts can erase the signal; preserving the initial block fixes the representation

The kernel of H is

\[
\{(a,K_0a,K_1K_0a,\ldots):a\in\mathbb R^{d_0}\}.
\]

All compatible contrast vectors are attainable by recursion, so H has full row rank and this kernel has dimension d0. The transform

\[
T:Y\longmapsto(Y_0,HY)
\]

is square block lower triangular with identity diagonal; det T=1, even when K is rectangular or singular. Its inverse is \(Y_{j+1}=r_j+K_jY_j\). Retaining the **full** \(TCT^T\), mean and support preserves the experiment. Retaining only marginal errors does not.

For \(Y\sim N(\theta\mathbf1,I_3)\), contrasts have no θ dependence, while the full and initial-block-plus-contrast observations have information 3. Here \(\hat\theta=Y_0+(2r_0+r_1)/3\), variance 1/3. This proves why a depth-coherence score alone cannot replace a common-state likelihood.

This is not a claim that every noninjective representation loses information about every parameter: for fixed SPD C and mean derivative a, equality in
\(a^TH^T(HCH^T)^{-1}Ha\le a^TC^{-1}a\)
holds precisely when \(C^{-1}a\in\operatorname{Im}H^T\). Singular laws can occupy a subspace on which H is injective. Data processing and a scientific target must be considered together.

## D4. A geometric transport is not automatically an innovation

Under a fully specified joint Gaussian law, conditioning on **the entire past** gives

\[
e_j=Y_j-\mu_j-C_{j,<j}C_{<j,<j}^{+}(Y_{<j}-\mu_{<j}),\qquad
S_j=C_{jj}-C_{j,<j}C_{<j,<j}^{+}C_{<j,j}.
\]

PSD block consistency makes the conditional mean well-defined on past support. Each e_j is uncorrelated with the full past and therefore independent of it under joint Gaussianity. Merely using the previous block requires an additional Markov property. For unit variances and all pairwise correlations 1/2, adjacent regression residuals with coefficient 1/2 have covariance −1/8. Thus nested sky metadata does not establish independent innovations or a martingale.

A fitted \(\hat K(Y)\) is also a different experiment: taking \(\hat K=Y_1/Y_0\) makes one residual identically zero, although a fixed-K variance formula would be positive. Fit/selection steps must be repeated inside every null replicate, or justified through an explicit conditional/training law. Estimated covariance needs its own sampling model; Sellentin–Heavens derives a modified t likelihood under its Gaussian simulation/Wishart and covariance-marginalization assumptions, not a universal frequentist coverage replacement ([primary paper, §§2–4](https://arxiv.org/html/1511.05969v2)).

## F1. One confidence event can support many tensor functionals

Let ξ contain the physical state, shared nuisance and every unknown population anchor used in a target. Suppose a measurable region C(Y) satisfies \(P_\xi\{\xi\in C(Y)\}\ge1-\alpha\). For a family of defined measurable functions \(f_t\), choose certified outer images \(I_t(Y)\supseteq f_t(C(Y))\). Then

\[
P_\xi\{f_t(\xi)\in I_t(Y)\text{ for all }t\}\ge1-\alpha.
\]

Proof: the common inclusion event implies every displayed inclusion. For uncountable families require measurable simultaneous events or use outer probability. No further alpha charge is incurred merely by displaying images of the **same** already valid set. This does not license selecting fresh tests, refitting a different region, or treating pointwise posterior quantiles as simultaneous confidence bounds. A valid image and a p-value are different outputs.

For coverage of an **entire identified set**, pointwise coverage is insufficient. With 20 observationally indistinguishable states, randomly excluding one gives each state 95% coverage but never covers all states. If ψ is the reduced identifiable law parameter, a valid D(Y) for ψ can instead be lifted as \(\bigcup_{\psi\in D(Y)}\Theta(\psi)\); on the event ψ0∈D this contains the complete \(\Theta(\psi_0)\). Declare which target is intended.

## F2. Anchors and quotients must stay on the same joint set

For \(f(\xi)=N(\xi)/D(\xi)\), optimize over the same ξ and its defined domain. A population anchor is an unknown parameter; a plug-in anchor computed from Y is a statistic, and a posterior or predictive anchor has a probability law. These are not interchangeable inferential targets. Data-dependent MES restrictions may exclude truth; intersecting them with a valid confidence set preserves coverage only with the required joint inclusion guarantee.

The two allowed tuples (N,D)=(1,1),(2,2) give ratio {1}; independent marginal recombination yields [1/2,2]. If D can vanish, retain the undefined branch. A numerator fixed at 1 and a denominator approaching 0 from above gives an unbounded ratio; N=D instead gives {1} on the nonzero domain. Touching zero alone does not prove unboundedness. Never clip a physical denominator to a small epsilon.

For an asymmetric anchor B, use its actual directional support h_B(u)>0. A symmetric two-sided profile using max{h_I(u),h_I(−u)} over one denominator is a chosen convention, not the opposite-direction physical ratio. Signed profiles, unavailable anchors, infeasible states and unbounded directions must retain separate statuses.

## F3. Exact linear support over a contraction fibre

The inherited companion notes fix a unit STF2 q and use full Frobenius products. Let \(L_qo=o:q\), \(M_q=I+6q^2/5\), \(R_q=B_qM_q^{-1}\), \(P_N=I-R_qL_q\), \(\eta_v=3v^TM_q^{-1}v\). The source fibre is

\[
\mathcal F_q(v)=R_qv+\sqrt{1-\eta_v}\,S(\ker L_q),\quad\eta_v\le1.
\]

For an STF3 linear representer a,

\[
\boxed{h_{\mathcal F_q(v)}(a)=a:R_qv+\sqrt{1-\eta_v}\,\|P_Na\|_F},
\qquad
\|P_Na\|_F^2=\|a\|_F^2-3(L_qa)^TM_q^{-1}(L_qa).
\]

Orthogonal decomposition reduces the supremum to a sphere in the four-dimensional kernel; Cauchy–Schwarz gives the expression, attained along P_Na when nonzero. At η=1 the fibre is a singleton; η>1 is infeasible. Both upper and lower endpoints follow from h(a) and −h(−a). This is a useful extension for a functional-image consumer, not proof that support summaries reconstruct the complete fibre: the support function also describes its convex hull, which includes points violating norm-one equality.

For uncertain contraction v in a valid D, optimize this expression over \(v\in D\cap\{\eta_v\le1\}\). Local sampled maximizers are lower witnesses, not certified upper bounds. Uncertain q must remain in the joint inverse image with its moving kernel; freezing its estimate loses the stated guarantee. Near η=1 the square-root term makes ordinary linear error propagation nonregular. The source result \(d_H=\sqrt{2t}\) for \(v_t=(1-t)v_*\) is reproduced numerically, not claimed as new here.

## How earlier exploration enters this revision

The prior R9 extension proposed target-specific robust support, stochastic CMB information and physical distinguishability. These remain useful but conditional. For the fixed ideal Gaussian Q/O pair, \(I_{ij}=(C_2-C_3)^2\operatorname{tr}(B_i^TB_j)/(C_2C_3)\); this derives from the covariance Fisher trace and does not cover masks, high multipoles, fitted covariance or arbitrary intrinsic octupoles. For whitened compact convex mean sets, their distance δ gives a separating minimax Gaussian test with maximum error Φ(−δ/2); rank alone supplies no precision threshold. Actual nuisance/noise/response laws are required before either guides an observed claim.

The historical generic NT2-A2 tail counterexample and signed fractional-box counterexample remain source-specific warnings. The compendium already reports a maintained convergent-tail branch and a replacement T2G. They are not labelled newly found failures in the current maintained formulations. All 172 proposal sections remain source/version roles, not independent or proved new theorems.

Evidence: `validate_revision2.py`, `evidence/research_checks.json`, the preserved Wolfram input/output and registered blind result envelopes. The exact scientific conclusion is that complete dependency laws and joint-set images are necessary interfaces for this research program; the current actual-data providers have not been admitted by these experiments.
