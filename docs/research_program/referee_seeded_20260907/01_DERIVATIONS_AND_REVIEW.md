# Referee-seeded mathematical results and falsifiable corrections

Date: 2026-09-07. Owner: MAIN. Status: direct derivations for the next scientific specification, not a new native execution or canonical proof receipt.

Conventions: spatial Euclidean full Frobenius products, metric signature (-,+,+,+), geometric observer derivatives unless converted explicitly by c, positive expansion when divided by Theta. The accepted 55-page source is retained at `9c86759f4ac7054d01d88689290a658e8ffd5863`. Its existing results are inputs, not rerun by this note. The displayed decimal arithmetic was evaluated with the web calculator; no Python, Monte Carlo or CAS run succeeded in MAIN.

## 1. Axial cutoff is exactly ten

For the specified continuum mask and axial generator, m is preserved. Retained complex-block row counts for m=0,...,5 are (4,4,4,3,2,1). The printed full-row minors use source columns (7,8,9,10), (7,8,9,10), (7,8,9,10), (7,8,9), (7,8), (7). Thus the accepted exact minor values prove full real row rank

\[
4+2(4+4+3+2+1)=32
\]

already at L=10. For L<=9, the m=0 block has at most three columns but four retained rows, so full real row rank is impossible. Therefore the minimal full-row-rank cutoff of this specific axial continuum operator is exactly 10. All L>=10 retain those columns.

At lower cutoffs the block-count upper bound is

\[
r_0(L)+2\sum_{m=1}^5r_m(L),\qquad
r_m(L)=\min(L-6,n_m),\quad n=(4,4,4,3,2,1),
\]

for L>=7. It gives 20 at L=8 and 27 at L=9. Achieving the upper bound still requires nonzero minors; counting alone is not that proof. The reported nonaxial ranks at L=9,10,11 are numerical observations on named directions, not a theorem for every direction.

## 2. Projection fraction and boost-coordinate uncertainty

Let Q be nonzero STF2, A_Q^2=Q:Q, and B_Q beta=3 beta_<a Q_bc>. With the previously derived adjoint,

\[
B_Q^*O=3(O:Q),\qquad B_Q^*B_Q=3M_Q,
\qquad M_Q=A_Q^2I+\frac65Q^2\succ0.
\]

The orthogonal projector P_Q=B_Q(3M_Q)^{-1}B_Q^* has rank three in the seven-dimensional STF3 space.

### 2.1 Exact null law

Assume O conditional on Q is independent, zero-mean Gaussian with covariance s_O^2 I_7 in a fixed Frobenius-orthonormal STF3 basis. Choose an orthonormal basis adapted to image(P_Q). The numerator and complementary squared norms divided by s_O^2 are independent chi-squared variables with three and four degrees of freedom. Transform their joint density to their sum and ratio. The Jacobian is the sum, and integrating it out gives

\[
f_B=\frac{\|P_QO\|^2}{\|O\|^2}\mid Q\sim\mathrm{Beta}(3/2,2),
\]

\[
p(f)=\frac{15}{4}\sqrt f(1-f),\quad
F(f)=\frac52f^{3/2}-\frac32f^{5/2},\quad 0\le f\le1,
\qquad E[f_B]=\frac37.
\]

The coefficient follows from integrating sqrt(f)(1-f) over [0,1], which gives 4/15. The CDF follows by elementary integration. Useful exact-tail controls are P(f_B>1/2)=0.38128156646 and P(f_B>4/5)=0.06979572136. The same ratio law holds for a nonzero vector with uniformly random direction on the seven-dimensional sphere; Gaussianity is one sufficient construction.

This is a geometric accidental-projection fraction, not a posterior kinematic fraction. A boost mean changes the Gaussian law to a noncentral problem; masking, anisotropic noise and Q/O correlations change it further. The observed map must not be assigned this ideal Beta p-value without the corresponding null conditions.

### 2.2 Correct error covariance and sharp shape range

In the conditional mean model O=B_Q beta+O_int with Cov(O_int)=s_O^2 I_7,

\[
e=\widehat\beta-\beta=M_Q^{-1}(O_{\rm int}:Q),
\qquad \operatorname{Cov}(e\mid Q)=\frac{s_O^2}{3}M_Q^{-1}.
\]

Proof: O:Q=B_Q^*O/3, hence Cov(O:Q)=s_O^2 B_Q^*B_Q/9=s_O^2 M_Q/3; multiply by M_Q^{-1} on both sides. If A_O^2 means E||O_int||^2=7s_O^2, then

\[
E\|e\|^2=\frac{A_O^2}{21}\operatorname{tr}M_Q^{-1}.
\]

A fixed-radius isotropic vector is not Gaussian, but its second moment A_O^2 I/7 yields the same quadratic risk. These two models must not be called 'Gaussian with fixed amplitude' without explaining the distinction.

Set q=Q/A_Q and s_3=tr(q^3). Trace-free unit eigenvalues give 0<=s_3^2<=1/6. For example, constrained extrema of the cubic trace require at most two distinct eigenvalues; the repeated pair gives s_3^2=1/6, and spectrum proportional to (-1,0,1) gives zero. From the Cayley-Hamilton inverse in the report, or direct multiplication,

\[
(I+6q^2/5)^{-1}
=\frac{40I+(15/2)s_3q-30q^2}{40+3s_3^2},
\quad
A_Q^2\operatorname{tr}M_Q^{-1}=\frac{90}{40+3s_3^2}.
\]

Consequently

\[
\frac{20}{9}\le A_Q^2\operatorname{tr}M_Q^{-1}\le\frac94,
\]

\[
\boxed{\sqrt{20/189}\,\frac{A_O}{A_Q}
\le \sqrt{E\|e\|^2}\le
\sqrt{3/28}\,\frac{A_O}{A_Q}}.
\]

The coefficients are 0.3253000243 and 0.3273268354. Using only the review's illustrative D_2=226 and D_3=1018 microkelvin-squared, with C_l=2pi D_l/[l(l+1)], gives A_O/A_Q=2.71242089998. Conditional RMS is therefore 0.88235058472 to 0.88784814934, not the proposal's 0.8435. This is an internal inconsistency of its stated amplitude model and number, not a new CMB measurement. If Q's amplitude is random, an additional average of its inverse amplitude is needed; the fixed-amplitude statement is not silently extended.

The Gaussian mean model has Fisher matrix 3M_Q/s_O^2, which is positive definite. It is statistically identifiable, though very imprecise at these illustrative amplitudes. Conversely, with a wholly unrestricted deterministic O_int, changing beta by d and O_int by -B_Qd leaves O unchanged exactly. That is structural non-identification. Neither an imprecise LS coordinate nor a heuristic beta sqrt(N_modes) proves a no-go for every estimator, prior, high-ell channel, spectral measurement or additional dataset.

## 3. Stronger internal Model-M bounds by preserving cancellations

The following is confined to the explicitly retained first-order radiation model. It does not replace the more general MES literature by claiming equivalent assumptions. Denote propagation-direction temperature multipoles by t_a,t_ab,t_abc; energy moments obey

\[
q_a^{\rm rad}=\frac43\rho t_a,\quad
\pi_{ab}=\frac8{15}\rho t_{ab},\quad
\xi_{abc}=\frac8{35}\rho t_{abc},\quad
\dot{\bar\rho}=-\frac43\Theta\bar\rho.
\]

Products of two first-order perturbations are excluded, exactly as in Appendix E. No rigorous finite-amplitude bound on discarded terms is supplied.

### 3.1 Shear cancellation

Insert these moments into

\[
\dot\pi_{\langle ab\rangle}+\frac43\Theta\pi_{ab}
+\frac8{15}\rho\sigma_{ab}
+\frac25D_{\langle a}q^{\rm rad}_{b\rangle}+D^c\xi_{abc}=0.
\]

The background derivative of rho cancels the expansion term before taking a norm. Dividing by 8rho/15 gives

\[
\boxed{\sigma_{ab}=-\dot t_{\langle ab\rangle}
-D_{\langle a}t_{b\rangle}-\frac37D^ct_{abc}.}
\]

The first referee's corresponding identity is correct. Its sqrt(3) contraction estimate is sufficient but can be sharpened using the actual STF domain.

Let T_{dabc} be STF in abc, with full tensor product norm, and (LT)_{ab}=sum_c T_{cabc}. For X in STF2, the adjoint is

\[
(L^*X)_{dabc}=\frac13(\delta_{da}X_{bc}+\delta_{db}X_{ac}+\delta_{dc}X_{ab})
-\frac{2}{15}(\delta_{ab}X_{dc}+\delta_{ac}X_{db}+\delta_{bc}X_{da}).
\]

The second group removes the abc traces. Substituting d=c and summing gives LL^*X=(5/3-4/15)X=(7/5)X. Therefore ||L||_2=sqrt(7/5). With the report's full derivative-norm envelopes,

\[
\boxed{\frac{\|\sigma\|_F}{\Theta}
\le\epsilon_2^*+\epsilon_1'+\frac3{\sqrt{35}}\epsilon_3'.}
\]

The contraction constant is sharp on V_1 tensor STF3. No claim that all simultaneous physical derivative-envelope extrema are realised is made. With the same characteristic derivative coefficients as the report,

\[
\frac{\|\sigma\|_F}{\Theta}
\le\frac13\epsilon_2+\frac13\epsilon_1+\frac1{\sqrt{35}}\epsilon_3.
\]

### 3.2 Vorticity cancellation

Put C_ab=D_[a t_b], G_ab=D_[a D^c t_b]c. The report's explicit contracted-operator envelope bounds dot(C) and G, not an uncontracted Hessian with an assumed unit contraction norm. Its antisymmetrised flux equation is

\[
\frac49\Theta\rho\,\omega_{ab}
=-\dot Q^{\rm rad}_{ab}-\frac53\Theta Q^{\rm rad}_{ab}
-D_{[a}D^c\pi_{b]c},\qquad
Q^{\rm rad}_{ab}=\frac43\rho C_{ab}.
\]

First combine the rho derivative and expansion contributions. The result is

\[
\boxed{\omega_{ab}=-\frac3\Theta\dot C_{ab}-C_{ab}
-\frac6{5\Theta}G_{ab}.}
\]

Hence

\[
\boxed{\frac{\|\omega_{ab}\|_F}{\Theta}
\le3\epsilon_1^{\prime *}+\epsilon_1'+\frac65\epsilon_2^{\prime\prime}}
\le\frac23\epsilon_1+\frac2{15}\epsilon_2
\]

under the specified characteristic estimates. This improves the internal model's conservative 10epsilon_1/3 term by retaining the cancellation. The axial vorticity-vector norm differs from the tensor norm by sqrt(2); the geometric-to-time rate conversion multiplies both numerator and H by c. Use non-strict inequalities unless a strict premise is actually imposed.

### 3.3 What a single sky cannot establish

The amplitude normalisations are obtained from Q/O, but the derivative-envelope and all-observer extension premises are not. For finitely many linear measurements m=Af of an unconstrained field, a target functional ell(f) is determined only if it annihilates ker(A). Otherwise a nonzero field perturbation h in ker(A) changes the target without changing the measurements; scaling h makes an unrestricted target unbounded. Smoothness, dynamics, positivity or norm constraints can alter this conclusion, but must be supplied.

Therefore the assumption ladder begins with 'no amplitude-only MES inference', not with an apparent 10^-3 bound before the required premises. ISW integrals and finite remote measurements constrain particular kernels; they are not pointwise bounds on every space/time derivative by themselves.

## 4. Bounded cancellation and small masks

For a positive-definite nuisance metric S and displacement d, consider min h^T S^{-1}h subject to Kh=d. Set h=S^{1/2}u. Orthogonal decomposition into kernel and row space of KS^{1/2} gives

\[
\operatorname{cost}(d)=
\begin{cases}
d^T(KSK^T)^\dagger d,&d\in\operatorname{Im}K,\\
+\infty,&\text{otherwise},
\end{cases}
\]

\[
h_{\min}=SK^T(KSK^T)^\dagger d.
\]

The metric must correspond to an actual amplitude budget or declared covariance, not be chosen to make the cost small. A change from a fixed nuisance baseline within radius R has cost<=R^2. Comparing any two nuisance vectors each in that ball allows differences up to radius 2R; these are different identification questions.

For orthonormal real high-band harmonics, the addition theorem and Cauchy-Schwarz give

\[
\left\|\sum_{l=7}^{L}\sum_m h_{lm}Y_{lm}\right\|_\infty
\le\sqrt{\frac{d_H(L)}{4\pi}}\|h\|_2,\quad d_H=(L-6)(L+8).
\]

If an unperturbed absolute sky has minimum T_*>0, the right-hand side strictly below T_* is a sufficient global positivity condition. It is conservative, not necessary. Raw-coordinate metrics require the harmonic isometry adapter. This makes local linear ambiguity physically admissible for sufficiently small changes without declaring all unbounded nuisance vectors to be positive skies.

For a finite-band full-sky baseline with high sources l>=7 and retained rows l<=5, the first-order boost overlap is zero. For w_epsilon=1-epsilon u, write N_epsilon=I-epsilon H and R_epsilon=-epsilon C. Then

\[
K_\epsilon=-\epsilon P(I-\epsilon H)^{-1}C,
\quad
\|K_\epsilon\|_2\le
\frac{|\epsilon|\|P\|_2\|C\|_2}{1-|\epsilon|\|H\|_2}
\]

when |epsilon|||H||<1. Full row rank can persist for every nonzero epsilon while singular values vanish as epsilon goes to zero. If PC has full row rank, weighted cancellation cost for fixed d grows at order epsilon^{-2}. A full-rank mask therefore need not erase practical information when the permitted nuisance amplitude is finite. This is an amplitude perturbation theorem for a fixed shape u, not a universal rate law determined by f_sky alone.

## 5. Joint data-conditioned nuisance: the correct statistical comparison

For the fixed-covariance linear Gaussian model

\[
y=A\theta+Kh+n_y,\qquad z=C\theta+Lh+n_z,\qquad h\sim N(0,S),
\]

assume h is independent of the joint noise, but permit N_yz=Cov(n_y,n_z). Then

\[
\Omega_{yy}=N_{yy}+KSK^T,\quad
\Omega_{yz}=N_{yz}+KSL^T,\quad
\Omega_{zz}=N_{zz}+LSL^T.
\]

The innovation and its mean derivative are

\[
\bar y=y-\Omega_{yz}\Omega_{zz}^{-1}z,\qquad
\bar A=A-\Omega_{yz}\Omega_{zz}^{-1}C,
\]

\[
\bar\Omega=\Omega_{yy}-\Omega_{yz}\Omega_{zz}^{-1}\Omega_{zy}.
\]

Completing the block Gaussian square factorises p(y,z|theta) into p(z|theta)p(y|z,theta). The full Fisher matrix is therefore

\[
\boxed{F_{\rm joint}=C^T\Omega_{zz}^{-1}C+\bar A^T\bar\Omega^{-1}\bar A.}
\]

Discarding p(z|theta) is incorrect when z itself carries theta information. Treating y and z from the same map as independent is also incorrect. For singular compressions one must work on their supported subspace rather than invert a zero-variance redundant direction.

If the model covariance depends on theta, include the covariance score term

\[
F_{ij}=\mu_{,i}^T\Omega^{-1}\mu_{,j}
+\frac12\operatorname{tr}(\Omega^{-1}\Omega_{,i}\Omega^{-1}\Omega_{,j}).
\]

A trace-power contamination ratio is not a Fisher information ratio. Two nuisance covariances with the same trace can act along entirely different signal directions. Report generalised directional information eigenvalues and compatible-region changes, in addition to trace diagnostics.

The report's J_b sends low-source coefficients to a first-order output for a fixed boost direction. It is not the derivative with respect to the three velocity components. In a full forward y=F[B(beta)a]+n, the velocity columns are G_i=partial y/partial beta_i at the declared source and processing state. If that source is latent, its uncertainty and cross-terms remain in the likelihood.

For the absolute monopole,

\[
\widetilde T_0(n)=\frac{T_0}{\gamma(1-\beta\cdot n)}
=T_0[1+\beta\cdot n+(\beta\cdot n)^2-\beta^2/2+\cdots].
\]

The second-order quadrupole is Q_ab^kin=T_0 beta_<a beta_b>, with full norm sqrt(2/3)T_0 beta^2. The zero first-order retained monopole column does not justify omitting this term. The pipeline reference must carry the exact low-order boost or a quantified truncation budget, not compare orders of beta while ignoring the huge T_0/DeltaT ratio.

## 6. Deterministic certification and finite-operator target

Suppose the actual error satisfies Delta Delta^T<=Gamma_E and W=Gamma_E^{-1/2} exists. Then ||WDelta||<=1 and Weyl's bound gives s_m(WK_true)>=s_m(WK_obs)-1. Once s_m(WK_obs)>1, a valid positive reported margin is any delta<=s_m-1, including half the observed excess. No statistical test level was changed. A data-estimated error set with claimed probability coverage needs selection-aware validation; that is a separate premise.

For one fixed finite weighted-design operator, distinguish three targets: exact finite pixel sum at specified centres/weights; implemented floating-point solve; continuum idealisation. Numerical roundoff and solve error concern the first two. Continuum-discretisation differences are an additional target change, not silently the same matrix.

Let N=Nhat+E_N, R=Rhat+E_R, with certified ||E_N||<=eta_N, ||E_R||<=eta_R. Let Xhat be a computed fit matrix and rhat=Rhat-Nhat Xhat. If ||Nhat^{-1}||eta_N<1, the Neumann-series inverse bound gives

\[
\|X-Xhat\|\le
\frac{\|Nhat^{-1}\|}{1-\|Nhat^{-1}\|\eta_N}
\bigl(\|rhat\|+\eta_R+\eta_N\|Xhat\|\bigr).
\]

All RHS bounds must refer to actual inputs; a observed resolution difference is not automatically eta_N or eta_R. A verified interval/rounding route may certify them. A practical multi-resolution comparison without such a proof remains numerically checked with an empirical error budget. Both are useful outputs, but only the former licenses a rigorous exact-target rank certificate.

## 7. Redshift and a concrete source-level coding defect

For a low-redshift affine physical velocity field v(x)=b+Gx and a radial observation at x=rn,

\[
v_r=n\cdot b+r\,n^T\operatorname{Sym}(G)n.
\]

Since n^T Anti(G)n=0 identically, radial-only observations from one origin do not measure the antisymmetric affine vorticity component. A reconstructed full 3D field can show a curl, but its posterior is conditional on the reconstruction prior and extra information. Coordinate redshift corrections, distance calibration and selection belong to the forward model; coherent residuals alone do not identify a native global tilt.

A fresh source review of `htt/obsstat/constrained_realizations.py` at `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`, blob `5378aa4f8c6560decbd997c5eda898a4b19f4c2c`, exposes a directly testable semantic mismatch. The scalar toy takes d=0 in a measurement model d=s+n, uses WF mean S d/(S+N), and generates constrained realisations. Its variance is

\[
S-\frac{S^2}{S+N}=\frac{SN}{S+N},
\]

not S. The default S=1,N=0.5 gives variance 1/3. Calling zero observed data 'no data constraint' and describing the finite-N ensemble as prior-width is incorrect. With no response H=0, posterior variance is S; with H=1 and d=0, a measurement still constrains the state. A prior with exactly zero curl power cannot generate physical curl merely by drawing more constrained realisations.

This is a source-level analytic counterexample, not an observed failing test in MAIN. The implementation unit must express H explicitly, use mean S H^T(HSH^T+N)^{-1}d and covariance S-SH^T(HSH^T+N)^{-1}HS, and test H=0 separately from zero d. It must retain the old toy's scope and not turn this repair into actual CF4 posterior validation.

The neighbouring `affine_flow.py` has `shear_amplitude=sqrt(0.5*sigma:sigma)` whereas the report's MES norm is sqrt(sigma:sigma). This is an intentional-looking convention difference requiring an adapter, not an automatic factor-of-two bug. Its cell bootstrap is not a calibrated covariance for correlated cells; even the docstring's 'lower bound' should not be used as a guaranteed inequality. Its least-squares routine only checks at least four cells, not design rank, so coplanar/rank-deficient configurations must receive explicit diagnostics before production inference.

## 8. Immediate validation oracles for the later coding phase

1. Projection CDF endpoints 0,1; exact integral/mean 3/7; the two tails above; distinguish Gaussian variance and fixed-radius second moment.
2. Error covariance under H=0 versus d=0 in the CR toy; S=1,N=0.5 gives 1 and 1/3 respectively. Reject S=N=0 in a denominator-based scalar helper unless explicitly defined as a deterministic degenerate case.
3. L contraction: use the explicit adjoint on a trace-free X and verify LL*=7I/5; do not compare to sqrt(3) as the optimal constant.
4. Shape trace endpoints q=diag(-1,0,1)/sqrt(2) and q=diag(-1,-1,2)/sqrt(6) give 9/4 and 20/9.
5. Nuisance cost on K=I,S=I gives ||d||^2; rank-deficient d outside image gives infeasible, not pseudoinverse zero cost.
6. Joint Gaussian scalar control A=1,K=1,C=0,L=1,S=1,Nyy=Nzz=1,Nyz=0 gives barOmega=3/2 and conditional Fisher 2/3, versus y-only Fisher 1/2.
7. Same control with C=1 gives total Fisher 2/3: C^T Omega_zz^{-1}C=1/2 plus barA^2/barOmega=1/6. Omitting z's marginal loses genuine information.
8. Radial solid-body rotation injected as omega cross x leaves all n dot v unchanged, although full 3D affine fit recovers omega. This tests the scientific observation operator, not merely an estimator routine.
9. Full-sky high-source-to-low response is zero at the stated first boost order; beta=0 still has ordinary cut-sky map leakage in the full unboosted observation operator. Do not confuse that leakage with K_b, which describes the boost derivative.
10. A singular value 1.2 and a contained unit error permit reported delta=0.1 after calculation. The negative fixture is an underestimated error bound, not retrospective delta reporting.

These are new analytic targets for the selected work, not claims that a test suite ran. No current observed significance, matrix rank for a new real mask, or physical cosmic vorticity result is created by this note.
