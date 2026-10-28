# From physical reduction errors to one kinematic confidence image

This is a constructive integration of MF02 §13.5, especially Eq. (13.5.15), and the preceding HTT foundation study. The finite calculation below uses a specified physical error budget; it does not evolve a kinetic system or estimate that budget from observations.

## The joint detector-error image

Let the finite retained state error be $e$, with a supplied positive metric $G$ and $e^TGe\leq\epsilon_X^2$. Here $G$ may be the entropy metric of the specified linearized kinetic problem; it is not the fifth statistical coordinate $G_F$. Let the observation adapter be $b=Be$, after all stated source, transport and detector conventions. Then the exact linear image has support

$$h_{\mathcal B}(v)=\epsilon_X\sqrt{v^TKv},\qquad K=BG^{-1}B^T.$$

**Proof.** Put $u=G^{1/2}e$. Maximizing $v^TBG^{-1/2}u$ over $\|u\|\leq\epsilon_X$ gives the expression by Cauchy–Schwarz, with equality along $G^{-1/2}B^Tv$ when nonzero. The image may be rank deficient. It is one common physical error set, not a covariance matrix until a stochastic law for $e$ is specified.

MF02 Eq. (13.5.15) is its scalar counterpart. The joint form retains cancellations between detector channels. In the executed fixture

$$G=\operatorname{diag}(1,4),\quad B=\begin{pmatrix}1&1\\1&-1\\2&0\end{pmatrix},\quad v=(1,1,-1),$$

the exact support is zero, whereas replacing each output by its separate bound gives $2\sqrt{1.25}+2=4.23607$ at $\epsilon_X=1$. Every physical error obeys $b_1+b_2-b_3=0$. Scalar intervals erase that relation. The gain is due to retaining a common physical error source, and is equally available to a correctly specified joint GLS/robust-inference baseline.

For a nonlinear adapter $m(X)$ on a controlled domain, Taylor's theorem gives $b=Be+r$ with $\|r\|\leq L_2\|e\|^2/2$ if the Hessian operator norm is bounded by $L_2$. Add this finite remainder to the joint image before computing confidence or compression errors. No Gaussian noise law follows from this deterministic Taylor bound.

## Physical error becomes bias in a specified kinematic response

Take the conditional finite experiment

$$Y=J\theta+N\eta+Be+\xi,\qquad \xi\sim N(0,C),$$

with fixed known $C\succ0$, common linear nuisance $N$, and the same bound on $e$. Define $W=C^{-1/2}$, $M=I-P_{WN}$, $A=MWJ$, and assume $A$ has full column rank $p$. With $I=A^TA$,

$$\widehat\theta=I^{-1}A^TMWY,\qquad
\delta\theta=I^{-1}A^TMWBe.$$

The exact maximum Fisher-scaled parameter bias is

$$\epsilon_\theta=\epsilon_X\big\|I^{-1/2}A^TMWBG^{-1/2}\big\|_{\rm op}.$$

This follows by maximizing the norm of a linear map on the state-error ball. It is attained at a top right singular vector. Errors orthogonal to the response image can affect a goodness-of-fit diagnostic while leaving this parameter estimator unchanged. With a rank-deficient physical response, apply the statement to identifiable coordinates; preserve the remaining kernel in the reported physical image.

An elementary simultaneous confidence ball has radius $\sqrt{\chi^2_{p,1-\alpha}}+\epsilon_\theta$ in the $I$ norm. For this fixed Gaussian experiment, a tighter uniform radius is

$$r_\alpha(\epsilon_\theta)=\sqrt{F^{-1}_{\chi^2_p(\epsilon_\theta^2)}(1-\alpha)}.$$

**Proof.** The squared standardized estimation error is noncentral chi-square with noncentrality $\|\delta\theta\|_I^2\leq\epsilon_\theta^2$. Its distribution is stochastically increasing in noncentrality. The displayed upper critical value therefore covers every allowed deterministic bias with probability at least $1-\alpha$. This is a conservative ball when the bias image is anisotropic; using the full ellipsoid/Minkowski image can sharpen selected directions further. It is not asserted to be a globally optimal robust interval.

The executed 12-observable, 5-target, 2-nuisance fixture verifies the singular-vector maximum and the zero effect of response-orthogonal error. A second 100,000-draw calculation compares ordinary and bias-aware five-dimensional confidence balls. Results and Monte Carlo errors are in `JOINT_REMAINDER.json`; the plot gives coverage and interval radius versus a declared error budget. There is no new measured cosmological signal in this experiment.

The inference is a finite Gaussian specialization of established bias-aware inference. Armstrong and Kolesár, *Sensitivity analysis using approximate moment condition models*, Quantitative Economics 12 (2021), 77–108, [arXiv:1808.07387](https://arxiv.org/abs/1808.07387), shows that accounting for model bias can also change the optimal weighting matrix. Consequently ordinary GLS cannot be called optimal for every bounded-error objective. The proposed application contribution is the physically derived error set and its propagation from radiation/optical/fibre response to a kinematic target.

## The five coordinates remain sufficient as bookkeeping objects

The observation model fixes $x$ and its response family. The joint physical/confidence image supplies directional support $F$. A declared anchor supplies $Q$. Sampling/posterior probabilities supply $\Pi$. Calibrated fibre comparison, physical channel propagation and cross-window covariance supply $G_F$, with their roles recorded separately.

Two corrections to the proposed extension are mathematically necessary.

1. A positive cone by itself is not a useful gauge anchor: for every $x$ in a cone, $x\in\lambda\mathcal A$ for every $\lambda>0$, so its gauge is zero. A normalized density-matrix slice has a different issue: it is affine and does not contain the origin. Center a bounded reference region in the observable quotient/difference space. For a qubit Bloch anchor $a$ with $\|a\|<1$, the physical difference body is $\{x:\|a+x\|\leq1\}$ and its gauge is

$$Q_a(x)=\frac{a\cdot x+\sqrt{(a\cdot x)^2+(1-\|a\|^2)\|x\|^2}}{1-\|a\|^2}.$$

The formula follows by solving the boundary quadratic in $\lambda$. It is generally asymmetric and reduces to $\|x\|$ at the unpolarized anchor. Boundary anchors require their tangent/support domain rather than division by $1-\|a\|^2=0$. The executed example lands on the Bloch-sphere boundary to floating-point precision.

2. Support functions preserve the closed convex hull. Keep the actual family image and its labels for nonconvex classification, parity components and discrete model tests. Convexification is exact for optimizing linear observables, not for reconstructing every nonconvex physical alternative.

Born probabilities enter a measurement model once. For example, a known normalized state and a complete POVM give multinomial outcome probabilities $p_i=\operatorname{tr}(\rho R_i)$. A posterior exceedance of a physical gauge is subsequently computed from the posterior induced by those counts and nuisance assumptions; it is not a second independent likelihood factor.

## A common response requirement for the four goals

The useful retained space is determined jointly by the observables and physical targets. For detector $R_i$ behind a specified channel $\mathcal P_\gamma$, the accessible state functional is $\mathcal P_\gamma^*(R_i)$. For a kinematic target also requiring a radiation moment operator, include that operator's linear moment functionals. Compute the span and its nuisance quotient before choosing a compressor. A passive fibre basis change conjugates state, channel and effect together and leaves their pairings invariant; an additional physical path or analyzer is additional measurement design, not information produced by a coordinate change.

This closes the conceptual link to MF02's reduction-error theorem: use its supplied error bound in the entropy/state metric, retain the full detector Gram, transport it into identifiable physical coordinates, and propagate one covering event to all required functions of $(\Sigma,\Omega,A,\beta)$. The four science lanes supply the concrete adapters. No native kinetic evolution is required to prove or test this finite inference step.
