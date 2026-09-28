# Proposed R9 extensions: experiment information and robust resolution

Status: **derived under stated assumptions**, with a bounded **numerically checked** synthetic fixture. These are proposals for revising the research plan, not a full research loop, production implementation, formal theorem admission, physical detection, or novelty claim. Inputs read: `research_review/r9/THEORY.md` (T1–T4) and `research_review/r9/CMB_RESEARCH.md` (C1–C3). The d=1 skew-adjoint boost premise is inherited from C3; this note does not independently qualify a production boost operator.

## 1. A local experiment-information discriminator extending C3

Let \(X\sim N(\mu(\vartheta),\Sigma(\vartheta))\), with \(\Sigma\succ0\), a differentiable fixed experiment, and parameter-independent support. Write \(a_i=\partial_i\mu\), \(S_i=\partial_i\Sigma\). The score is

\[
s_i=a_i^T\Sigma^{-1}(X-\mu)
+\tfrac12\{(X-\mu)^T\Sigma^{-1}S_i\Sigma^{-1}(X-\mu)
-\operatorname{tr}(\Sigma^{-1}S_i)\}.
\]

Gaussian odd centred moments vanish; the fourth-moment identity gives

\[
F_{ij}=a_i^T\Sigma^{-1}a_j+	frac12
\operatorname{tr}(\Sigma^{-1}S_i\Sigma^{-1}S_j).
\tag{1}
\]

Thus a singular-value calculation of a deterministic mean design omits covariance information and does not by itself describe the actual experiment.

For physical parameters \(\theta\) and nuisance \(\eta\), projection of physical scores off the nuisance-score span yields

\[
F_{\mathrm{eff}}=F_{\theta\theta}
-F_{\theta\eta}F_{\eta\eta}^{+}F_{\eta\theta}.
\tag{2}
\]

The pseudoinverse is appropriate for a redundant nuisance tangent because these blocks form a Gram matrix. Formula (2) is a local tangent statement. Neither its positive definiteness nor its singularity alone proves global identifiability/nonidentifiability; higher-order dependence and physical domain restrictions require separate treatment. Infinite-dimensional or nonsmooth nuisance models need their own tangent-space analysis.

### Two-block ideal Q/O law

Adopt C3's real orthonormal coordinates, centred independent \(q\in\mathbb R^5\), \(o\in\mathbb R^7\), and

\[
\Sigma_0=\begin{pmatrix}C_2I_5&0\\0&C_3I_7\end{pmatrix},\qquad C_2,C_3>0,
\quad
G_i=\begin{pmatrix}0&-B_i^T\\B_i&0\end{pmatrix},\quad B_i\in\mathbb R^{7\times5}.
\]

Here \(\beta=v/c\) is dimensionless. The multipoles must use the same temperature convention, so \(C_2,C_3\) have the same squared-temperature units and \(B_i\) is dimensionless. Deterministic monopole/dipole means and other multipole blocks are excluded from this bounded pair experiment. At \(\beta=0\),

\[
S_i=G_i\Sigma_0+\Sigma_0G_i^T
=(C_2-C_3)\begin{pmatrix}0&B_i^T\\B_i&0\end{pmatrix}.
\]

Putting this in (1), the two diagonal trace contributions are equal; the factor \(1/2\) cancels their factor two:

\[
\boxed{F_{ij}^{(2,3)}=\frac{(C_2-C_3)^2}{C_2C_3}
\operatorname{tr}(B_i^TB_j).}
\tag{3}
\]

All entries are dimensionless inverse squared-\(\beta\) units. Equation (3) describes expected local information in the stochastic pair, not a realized velocity uncertainty.

An independent route uses the conditional experiment. At \(\beta=0\),

\[
\partial_iE[o_{\rm obs}\mid q_{\rm obs}=q]
=\frac{C_2-C_3}{C_2}B_iq,\qquad
\operatorname{Cov}(o_{\rm obs}\mid q_{\rm obs})=C_3I_7+O(\beta^2).
\]

The conditional covariance has zero first derivative here. The conditional mean information is therefore

\[
F_{ij}(q)=\frac{(C_2-C_3)^2}{C_2^2C_3}
q^TB_i^TB_jq.
\]

Using \(E[qq^T]=C_2I_5\) reproduces (3). In contrast, the fixed-source mean experiment \(o=\sum_i\beta_iB_iQ+\epsilon\), with known \(Q\) and \(\epsilon\sim N(0,\sigma_3^2I)\), has \(F=B_Q^TB_Q/\sigma_3^2\). Its full column rank is a property of a different admitted likelihood.

Consequences and boundary cases:

* \(C_2=C_3\) makes (3) zero despite deterministic rank three. In a closed two-block model \(\Sigma_0=C I_{12}\) and \(R=\exp(\sum_i\beta_iG_i)\), the invariance \(R\Sigma_0R^T=\Sigma_0\) is exact to all orders. The physical full multipole law need not have this invariance: adjacent powers, means, or a different response may retain information.
* \(C_2\to0\) or \(C_3\to0\) crosses a singular-law boundary. The apparent divergent prefactor does not justify applying the regular Fisher argument at zero power.
* Unknown scalar \(C_2,C_3\) give block-diagonal covariance tangents. Their score inner products with the off-diagonal \(S_i\) vanish in this ideal pair at \(\beta=0\), so profiling these two powers does not reduce (3) locally. A covariance nuisance with tangent in the span of \(S_i\) does reduce information; an exact matching tangent erases that first-order direction.
* A mean-only nuisance is orthogonal to a covariance-only physical score in the centred Gaussian tangent metric. This local orthogonality is not a guarantee about nonlinear finite-sample inference.

### Processing and the actual law

For a fixed linear processor \(P\) and independent parameter-free Gaussian noise \(n\sim N(0,N)\),

\[
Y=PX+n,\quad \Sigma_Y=P\Sigma_0P^T+N\succ0,\quad
S_{Y,i}=PS_iP^T.
\tag{4}
\]

Use (1)–(2) with (4), after composing all relevant source/noise/foreground blocks. In this parameter-free processing experiment the processed score is the conditional expectation of the original score given \(Y\); hence \(F_Y\preceq F_X\) by conditional-variance decomposition. A zero derivative cannot be restored by this processing. For a nonsquare processor, the ideal orthogonality between power nuisance and boost tangents can be lost, so (2) must be recomputed. Data-dependent masks/cleaning, parameter-dependent noise, or omitted multipoles are changes to the experiment and require their own likelihood.

**Suggested deliverable in the revised plan:** one response-law table per product containing its random variable, fixed conditioning variables, mean/covariance derivatives, nuisance tangents, \(F_{\rm eff}\), and explicit zero-information controls. This is a qualification experiment before interpreting \(B_Q\)'s rank or a fit as a physical velocity constraint. It does not settle the separate same-state map from fitted observer/source coefficients to global matter tilt.

## 2. A robust resolution discriminator extending T2–T3

Retain T2's justified common whitening and fixed model

\[
Z=A\theta+N\eta+b+\epsilon,\qquad \epsilon\sim N(0,I),\quad b\in\mathcal B.
\]

First join all products with scientifically shared nuisance variables as in T3. Then choose \(U\) spanning \(\operatorname{col}(N)^\perp\), and set \(D=U^TA\), \(\mathcal B'=U^T\mathcal B\). With unrestricted \(\eta\), the attainable projected mean set for a fixed physical state is

\[
\mathcal M_\theta=D\theta+\mathcal B'.
\]

For two candidate physical states, define

\[
\delta(\theta_0,\theta_1)=
\inf_{b_0',b_1'\in\mathcal B'}
\|D(\theta_1-\theta_0)+b_1'-b_0'\|
=\operatorname{dist}\bigl(D(\theta_1-\theta_0),\mathcal B'-\mathcal B'\bigr).
\tag{5}
\]

The equality uses symmetry of the difference set. This is a whitened signal-to-noise separation. It is independent of observed data for a declared experiment and bounds; it is not a posterior odds or a measured detection statistic.

For compact \(\mathcal B'\), \(\delta=0\) is exactly overlap of attainable mean sets. The two states then admit identical Gaussian sampling laws for at least one pair of permitted discrepancies. No uniform test can separate that pair, regardless of full column rank of \(D\). For a merely nonclosed set, zero distance need not mean actual intersection; state the distinction.

For \(\mathcal B'\) compact and convex, suppose the sets have \(\delta>0\), and let nearest means be \(m_0^*,m_1^*\). Put \(v=(m_1^*-m_0^*)/\delta\). Convex nearest-point optimality yields

\[
\sup_{m\in\mathcal M_0}v^Tm\le v^Tm_0^*,\qquad
\inf_{m\in\mathcal M_1}v^Tm\ge v^Tm_1^*.
\]

The midpoint threshold on \(v^TU^TZ\) has worst-case errors at most \(\Phi(-\delta/2)\) on either state. The nearest simple Gaussian pair attains this bound, so it is also the minimax maximal error. At a one-sided type-I allocation \(\alpha\), the separating threshold \(v^Tm_0^*+z_{1-\alpha}\) guarantees type-II error at most \(\Phi(z_{1-\alpha}-\delta)\). Thus a sufficient uniform resolution requirement for type-II target \(\gamma\) is

\[
\boxed{\delta\ge z_{1-\alpha}+z_{1-\gamma}.}
\tag{6}
\]

For nonconvex sets, (5) still identifies overlap and closest simple pairs, but positive distance alone does not yield this separating linear test or its exact minimax formula. For state-dependent covariance, a distance between means alone is insufficient. These distinctions should be fixed in the plan before optimizing a physical discriminator.

### Exact rank-full counterexample

Take one whitened observation

\[
Y=0.01\theta+b+\epsilon,\quad \epsilon\sim N(0,1),\quad b\in[-\rho,\rho],\quad
\theta_0=0,\ \theta_1=1.
\]

The design has rank one and \(\ker D=\{0\}\). Yet

\[
\delta=\max(0.01-2\rho,0).
\]

At \(\rho=0\), the optimal balanced error is \(\Phi(-0.005)=0.4980052969\): structural identification is compatible with practically negligible one-observation resolution. At \(\rho=0.006\), the mean intervals overlap; the exact common mean \(0.005\) is attained by \((\theta,b)=(0,0.005)\) and \((1,-0.005)\). The uniform balanced minimax error is then \(1/2\).

This does not contradict T2's finite-target theorem. Its kernel condition determines whether a target is unbounded under arbitrary parameter translations. Equations (5)–(6) determine whether *specified finite changes* survive bounded discrepancy and finite noise at a stated error rate. Compact physical domains, sample repetition, or better depth/angular leverage change these questions in different ways. Systematic discrepancy does not automatically average down with sample size.

For a Euclidean discrepancy ball of radius \(\rho\), (5) reduces to \((\|D\Delta\theta\|-2\rho)_+\). For an ellipsoid, retain orientation and solve distance to its difference ellipsoid; do not replace it with a largest-eigenvalue radius unless explicitly choosing a conservative bound. If a proposed response must be tested against calibration-only or alternative physical models, use the corresponding two full attainable mean sets, with all declared nuisance/discrepancy variables, rather than testing a single column of \(D\).

**Suggested deliverable in the revised plan:** selected physical contrasts \(\Delta\theta\), response coefficients and domains, common-nuisance justification, discrepancy origin and orientation, attainable-set witnesses/certified separation, and a predeclared error-rate resolution target. If the actual processing law is unqualified, report the distance as a scenario calculation only. A feasible overlap witness establishes ambiguity; failure of an optimizer to find overlap does not certify separation.

## 3. Bounded check evidence

`check_extensions.py` uses a fixed seed and three arbitrary integer \(7\times5\) blocks, not the production boost matrix. Actual execution: Python 3 environment with NumPy 2.3.5; process exit 0. `check_results.json` preserves the numbers.

* Joint trace Fisher vs (3): maximum difference \(7.11\times10^{-15}\).
* Equal-power covariance derivatives: exactly zero in the synthetic arithmetic.
* Ideal power-nuisance cross information: zero; after a fixed noisy projection: maximum absolute entry 0.242799.
* Eigenvalues of \(F_X-F_Y\): 30.69996, 45.91817, 56.74481, consistent with information contraction.
* Eigenvalues of profiled-information decrement: \(-4.32\times10^{-16}\), 0.189673, 0.750729; the tiny negative value is floating-point roundoff, not an exact PSD certificate.
* An exactly matching covariance nuisance leaves zero information in the duplicated physical tangent direction.
* Rank-full small-response example: error 0.4980053 without discrepancy, exact overlapping mean 0.005 with radius 0.006.

No new source theorem has been proved here. The useful research advance is to turn R9's deterministic-versus-stochastic warning and kernel criterion into concrete falsifiable experiment-selection quantities, while preserving their assumptions and limits.
