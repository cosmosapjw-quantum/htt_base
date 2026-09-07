# Post-review theoretical results and computational forms

MAIN, 2026-09-07. Explicit derivations and selected scalar arithmetic checks; no new native numerical/CAS/observational execution. Novelty is not certified.

Conventions and inherited inputs are the accepted pedagogical Report A at `9c86759f4ac7054d01d88689290a658e8ffd5863`. Existing artifacts and receipts remain unchanged. Spatial tensors use the full Euclidean Frobenius metric. Spacetime signature is (-,+,+,+); beta is velocity divided by c. Q and O have temperature units, q=Q/A_Q and o=O/A_O are unit dimensionless shapes. Rates use one common geometric or inverse-time convention, with a factor c converting all rates together. Probability models and physical premises below are part of the statements.

## T1. The exact axial continuum threshold is L=10

Retain the report's fit through ell=5, output ell=2..5, source ell=7..L, identity transfer, axial first-order generator and exact wide mask. The m=0..5 complex blocks have row counts (4,4,4,3,2,1).

The existing nonzero minors use source columns 7..10 for m=0,1,2; 7..9 for m=3; 7..8 for m=4; and 7 for m=5. All are already available at L=10. Thus the accepted certificate implies

\[
\operatorname{rank}_{\mathbb R}K_z^{\rm cont}(10)
=4+2(4+4+3+2+1)=32.
\]

At L<=9 the m=0 block has at most three columns for four rows. Full row rank is impossible. **Ten is therefore the minimum axial full-row-rank cutoff for this operator.** This deduction does not rerun the certificate or certify a finite pixel calculation.

For fixed mask/cutoff, K_b is linear in the three components of the direction vector b. A 32-column minor nonzero at b=z has a nonzero homogeneous polynomial determinant. Its exceptional zero set on the unit sphere has measure zero. One proof uses rational stereographic charts on the sphere and the fact that a nonzero polynomial has measure-zero zeros, proved by induction on variables and the finite-root property outside the zero set of its coefficient polynomials. Homogeneity excludes a nonzero polynomial vanishing on the entire sphere. Consequently full rank holds for almost every direction at L=10. This is not every-direction certification or a uniform singular-value bound.

## T2. A posteriori deterministic rank slack is valid

Suppose the actual error satisfies Delta Delta^T <= Gamma, Gamma positive definite, with W=Gamma^(-1/2) and K_obs=K_true+Delta. Then

\[
s_m(WK_{\rm true})\ge s_m(WK_{\rm obs})-1.
\]

A rigorously established s_m(WK_obs)>1 proves full row rank. The slack delta=s_m(WK_obs)-1 may be reported after computing it. Prechoosing delta is not a mathematical hypothesis. If the numerical singular value has certified absolute error epsilon_s, use s_computed-epsilon_s>1.

What cannot be inferred from the desired rank is actual error membership in Gamma. An empirical family/radius selected on the same outputs needs justified coverage; shrinking an unjustified envelope until it passes is invalid. This corrects the old report's blanket prohibition on choosing a margin after inspecting singular values. The archived PDF remains unchanged; its next scientific revision should distinguish deterministic logic from statistical calibration.

## T3. Projection null and the low-QO LS variance

For nonzero Q, let L_Q O=O:Q and B_Q beta=3 STF(beta tensor Q). Inherited algebra gives

\[
B_Q^*=3L_Q,\qquad B_Q^*B_Q=3M_Q,
\qquad M_Q=(Q:Q)I+\frac65Q^2.
\]

P_Q=B_Q(3M_Q)^(-1)B_Q^* is a rank-three orthogonal projector in real STF3, which has dimension seven.

Assume O conditional on Q is tau times a standard seven-dimensional Gaussian independent of Q. In an orthonormal basis adapted to P_Q, its projected and residual norm squares divided by tau squared are independent chi-square variables of dimensions three and four. A sum/ratio change of variables in their gamma densities gives

\[
f_B=\frac{\|P_QO\|_F^2}{\|O\|_F^2}
\sim\mathrm{Beta}(3/2,2),\qquad
p(x)=\frac{15}{4}\sqrt{x}(1-x),
\]
\[
F(x)=\frac52x^{3/2}-\frac32x^{5/2},\qquad
\mathbb E f_B=\frac37.
\]

The ratio has the same law for a uniform spherical direction at fixed norm, but that law is not Gaussian. SO(3) invariance alone is insufficient for arbitrary non-Gaussian O: rotation does not act transitively on its six-sphere of shapes. Isotropic covariance alone likewise does not determine the ratio distribution. Masked/noisy Q and O need not be independent. This is an ideal-model oracle, not an automatic observational p-value.

For conditional Gaussian mean B_Q beta and the same covariance, the numerator is noncentral chi-square with parameter lambda=3 beta^T M_Q beta/tau squared. The residual remains central and independent. This gives a singly noncentral beta alternative only for that mean model.

The algebraic estimator beta_hat=M_Q^(-1)L_QO obeys

\[
\operatorname{Cov}(\widehat\beta\mid Q)
=\frac{\tau^2}{3}M_Q^{-1}
=\frac{A_O^2}{21}M_Q^{-1},
\]

where A_O squared=7 tau squared is the expected squared norm. The same second moment holds for a fixed-amplitude spherical O with that amplitude; Gaussian likelihood/Fisher conclusions do not follow for that distinct law.

For unit q and s3=tr(q cubed), the inherited polynomial inverse gives

\[
\operatorname{tr}M_q^{-1}=\frac{90}{40+3s_3^2}.
\]

The tracefree unit-eigenvalue constraints give 0<=s3 squared<=1/6. To derive the upper endpoint, extremise the product of the three eigenvalues at fixed sum and norm: the multiplier equations imply two eigenvalues coincide at a nonzero extremum. Spectra proportional to (-1,-1,2) attain s3 squared=1/6; (-1,0,1) attains zero. Hence

\[
\frac{20}{9}\le\operatorname{tr}M_q^{-1}\le\frac94,
\qquad
\sqrt{\frac{20}{189}}\frac{A_O}{A_Q}
\le\sqrt{\mathbb E\|\widehat\beta\|^2}
\le\sqrt{\frac3{28}}\frac{A_O}{A_Q}.
\]

For the supplied illustrative D2=226 and D3=1018 microkelvin squared, A_Q squared=25 D2/8 and A_O squared=245 D3/48. Calculator evaluation gives **0.882350584718888 to 0.8878481493381544**, not 0.8435. This is an unconstrained LS-coordinate fluctuation, not an inferred near-light-speed physical velocity or a prior-independent uncertainty bound. The Gaussian known-Q Fisher matrix is 3M_Q/tau squared; arbitrary intrinsic O instead gives deterministic nonidentifiability. Neither excludes high-multipole, spectral or external-frame information.

A scalar calculator check also gives P(f_B>0.8)=0.06979572136008738. A large projection fraction is therefore not, by itself, strong attribution evidence even in the ideal null.

## T4. Sharper bounds within the explicit first-order radiation model

Use precisely Appendix E's geodesic collisionless first-order model and derivative envelopes, not an unrestricted nonlinear MES theorem. Its radiation moments are q_a=(4/3)rho vartheta_a, pi_ab=(8/15)rho vartheta_ab and xi_abc=(8/35)rho vartheta_abc. The background product rule is dot(rho)=-(4/3)Theta rho in first-order products.

The quadrupole equation is

\[
\dot\pi_{\langle ab\rangle}+\frac43\Theta\pi_{ab}
+\frac8{15}\rho\sigma_{ab}
+\frac25D_{\langle a}q_{b\rangle}+D^c\xi_{abc}=0.
\]

Cancel the background expansion BEFORE applying norm inequalities:

\[
\sigma_{ab}=-\dot\vartheta_{ab}
-D_{\langle a}\vartheta_{b\rangle}
-\frac37D^c\vartheta_{abc}.
\]

### Sharp STF derivative-contraction factor

Let T: R^3 tensor STF3 -> STF2 satisfy (TX)_ab=sum_c X_{c,abc}. For an STF2 tensor S, use a separate free derivative index d in the adjoint:

\[
(T^*S)_{d,abc}=\mathrm{STF}_{abc}(\delta_{da}S_{bc})
=\frac13(B_Se_d)_{abc}.
\]

Only a,b,c are symmetrised; d is not contracted in this definition. The inherited normal-matrix identity gives

\[
\|T^*S\|^2=\frac19\sum_d\|B_Se_d\|^2
=\frac13\operatorname{tr}M_S
=\frac75\|S\|_F^2.
\]

By polarisation, T T^*=(7/5)I on STF2; its operator norm is sqrt(7/5), attained by an adjoint-image input. This improves the valid but loose sqrt(3) contraction bound. The STF projection of D_a vartheta_b is orthogonal and nonexpansive. Thus

\[
\boxed{\frac{\|\sigma\|_F}{\Theta}
\le\epsilon_2^*+\epsilon_1'+\frac3{\sqrt{35}}\epsilon_3'
\le\frac{\epsilon_1}{3}+\frac{\epsilon_2}{3}
+\frac{\epsilon_3}{\sqrt{35}}.}
\]

The last step uses the same maintained characteristic-derivative estimates as Appendix E. It is not a statement that observed amplitudes imply those estimates.

### Vorticity cancellation

Let C_ab=D_[a vartheta_b] and Q_ab=D_[a q_b]. The retained flux equation and commutators give

\[
\frac49\Theta\rho\omega_{ab}
=-\dot Q_{ab}-\frac53\Theta Q_{ab}-D_{[a}D^c\pi_{b]c}.
\]

Substitute Q=(4/3)rho C before taking norms:

\[
\omega_{ab}=-\frac3\Theta\dot C_{ab}-C_{ab}
-\frac6{5\Theta}D_{[a}D^c\vartheta_{b]c}.
\]

The exact contracted-operator envelopes then imply

\[
\boxed{\frac{\|\omega_{ab}\|_F}{\Theta}
\le3\epsilon_1^{\prime *}+\epsilon_1'+\frac65\epsilon_2^{\prime\prime}
\le\frac23\epsilon_1+\frac2{15}\epsilon_2.}
\]

These are non-strict bounds from weak premises. With H=Theta/3 the quadratic sector ceilings equal (3/2) times their squares. Full tensor vorticity norm is used, with omega_ab omega^ab=2 omega_a omega^a. All rates must use the same c convention.

Small amplitudes do not bound gradients: epsilon F((x-x0)/d) can have derivatives of order epsilon/d and epsilon/d squared. Finite point or shell measurements cannot impose all-domain derivative bounds without a dynamical/regularity premise. No empirical all-observer claim follows from this model-specific improvement.

## T5. Minimum bounded-nuisance cost

For y=A theta+K h+n and a fixed positive-definite source metric S, constrain h^T S^(-1)h<=R squared. For d in Im K,

\[
c(d)^2=d^T(KSK^T)^+d,\qquad
h_*(d)=SK^T(KSK^T)^+d.
\]

Outside Im K the exact matching cost is infinite. Proof: set h=S^(1/2)z and use the SVD of K S^(1/2). Solve each nonzero singular coordinate and set null coordinates to zero. Any other solution adds an orthogonal null vector and increases the norm.

A fixed zero-nuisance reference can be shifted by d iff c(d)<=R. Differences of TWO admissible nuisance states span the radius-2R ellipsoid. Pairwise parameter ambiguity therefore uses c(A(theta1-theta2))<=2R, not R.

Positivity is an additional physical restriction. For finite-band harmonic row Y_H(n),

\[
|Y_H(n)h|\le R\sqrt{Y_H(n)S Y_H(n)^T}.
\]

A baseline positive temperature exceeding the supremum supplies a sufficient margin. The unrestricted linear image does not authorise an arbitrarily large cancelling physical sky. Compute costs by whitened QR/SVD with explicit numerical range residuals; model radius and numerical rank tolerance are distinct.

## T6. Information is directional; measured high modes require the joint law

For independent Gaussian h,n with fixed covariances S,N, marginalising h gives C=N+KSK^T. This is a stochastic model, not a deduction from image rank.

Take A=e1 and N=I2. The nuisance covariances diag(k squared,0) and diag(0,k squared) have the same trace but mean-response Fisher informations 1/(1+k squared) and 1. A trace fraction cannot measure information loss about a specified parameter.

For a joint Gaussian (y,z) with mean (A_y theta,A_z theta),

\[
C_{y|z}=C_{yy}-C_{yz}C_{zz}^{-1}C_{zy},
\]
\[
\mu_{y|z}=A_y\theta+C_{yz}C_{zz}^{-1}(z-A_z\theta),
\qquad A_c=A_y-C_{yz}C_{zz}^{-1}A_z.
\]

With parameter-independent covariance,

\[
F_{\rm joint}=A_z^TC_{zz}^{-1}A_z+A_c^TC_{y|z}^{-1}A_c.
\]

Block Gaussian elimination proves the conditional law. The conditional residual has zero cross-covariance with z, so information adds as shown. Ignoring C_yz, ignoring A_z or treating a same-data posterior high sky as an independent measurement changes the experiment. A conditional-only likelihood is not the entire joint likelihood.

When beta changes the covariance, include the Gaussian term one half times tr(C^(-1) C_,i C^(-1) C_,j), in addition to the mean-response term. The existing processed tensor has shape (3,32,49); for a fixed source s the velocity derivative is D_alpha,i=sum_A J_i,alpha,A s_A, shape (32,3). J_b with shape (32,48) is a different source-coordinate operator.

For absolute processed maps, high modes also have zero-boost leakage under a mask. A pure boost-difference matrix is not the whole nuisance response. Use the complete ordered operator and the actual release's boosting/dipole/quadrupole corrections; do not add a second boost blindly.

## T7. Soft-mask rank versus quantitative nuisance cost

Let F be the orthonormal fit space through ell=5, P retain ell=2..5, and H contain source ell=7..L. For a fixed direction b define

\[
w_\varepsilon=1-\varepsilon m,\qquad0\le m\le1,\quad0\le\varepsilon\le1.
\]

Let M_FF be multiplication by m projected between fit modes and V_b=<Y_F,m B_b Y_H>. At full sky the first-order boost of H has no fit component, since its smallest possible ell is six. Therefore

\[
N_\varepsilon=I-\varepsilon M_{FF},\quad R_\varepsilon=-\varepsilon V_b,
\quad\boxed{K_\varepsilon=-\varepsilon P(I-\varepsilon M_{FF})^{-1}V_b.}
\]

The resolvent/Neumann bound gives

\[
\|K_\varepsilon\|_2\le
\frac{\varepsilon\|V_b\|_2}{1-\varepsilon\|M_{FF}\|_2}=O(\varepsilon)
\]

whenever its denominator is positive. Choose m=1-w_wide and the axial L=10 example. N_epsilon is positive definite on the whole interval: for epsilon<1 the weight is bounded below; at one the positive open cap and finite-harmonic uniqueness suffice. The nonzero minor at epsilon=1 is a rational function of epsilon with nonvanishing denominator. Its numerator is a nonzero polynomial, so it vanishes only at finitely many values. The nuisance image is all 32 output dimensions at every other positive epsilon, including values arbitrarily near zero.

Yet any h reproducing a fixed nonzero d satisfies

\[
\|h\|_2\ge\|d\|_2/\|K_\varepsilon\|_2=\Omega(\varepsilon^{-1}).
\]

For fixed positive-definite source metric the cost norm has the same lower-order divergence. An exact leading epsilon^(-2) squared-cost asymptotic additionally requires full row rank of P V_b, which is NOT assumed here.

For fixed bounded S,

\[
\|K_\varepsilon S K_\varepsilon^T\|_2=O(\varepsilon^2).
\]

With nonsingular baseline noise and continuous parameter response, the fixed-covariance information approaches the no-leakage full-sky limit, not necessarily zero. The absolute high-mode leakage has an analogous vanishing limit and must also be included in an actual map model.

Thus exact unrestricted image rank, bounded-source cost and stochastic information have different limits. This is a specified SOFT MASK AMPLITUDE family, not a universal claim about binary masks or f_sky. It supplies a testable quantitative replacement for an overbroad information-loss interpretation of the rank no-go.

## T8. Finite-beta monopole terms matter

In the outward convention,

\[
T'(n)=T_0/[\gamma(1-\beta\cdot n)].
\]

For x=beta dot n its expansion is T0[1+x+x squared-beta squared/2+x cubed-(beta squared/2)x]+O(beta to the fourth). The STF quadrupole is T0 beta_<a beta_b>, and the leading octupole is T0 beta_<a beta_b beta_c>. The linear monopole null in a retained quadrupole fit does not remove these finite-beta terms.

At illustrative T0=2.7255 K and |beta|=0.001234, T0 beta squared is **4.150271478 microkelvin** by calculator evaluation. This is a coefficient scale, not a full Frobenius norm or a measured sky value. It shows why beta squared times the large monopole can matter relative to beta times a small anisotropy. Reuse the exact positive-temperature operator and correct release conventions rather than a blanket first-order truncation.

## T9. Redshift information must add response directions

A local affine flow obeys

\[
v(rn)=V+rHn+r\Sigma n+\Omega\times(rn),
\quad n\cdot v=n\cdot V+rH+r n^T\Sigma n.
\]

Rigid rotation about the observer has exactly zero radial projection. Perfect radial data leave that mode unidentifiable. Lensing shear has a different physical response and cannot supply a congruence-shear measurement merely by sharing a name.

For the simple model d=beta+d_int and u_b(n)=n dot (V_b-c beta), the transformation beta -> beta+a, d_int -> d_int-a, V_b -> V_b+c a preserves every prediction. More free redshift bins do not break this gauge. A high-multipole/spectral response or a declared dynamical/tracer model can add information; a CMB-frame-corrected catalogue or shared-data reconstruction is not automatically an independent anchor.

The decomposition a_lm=sum_b a_lm^(b) is a source integral, not separately observed CMB skies at every redshift. Remote dipole/quadrupole estimators have scattering windows and optical-depth/tracer structure. Finite windows have null directions; functions supported between points or orthogonal to the finite window span can have large derivatives after rescaling their variation length. Thus finite tomography does not by itself prove the all-domain derivative premises of T4.

## T10. Survey weights and concrete code-consumer counterexamples

The existing bulk-flow likelihood treats selection weights as Gaussian precision and describes weight two as two independent measurements. Variance sigma squared/w defines a valid Gaussian IF w is genuine precision. An inverse-inclusion survey weight is a different object, and the normalisation is not that of two independent Gaussian observations. This affects both uncertainty and evidence.

For a fixed design weight W and true data covariance C,

\[
\widehat b=(X^TWX)^{-1}X^TWu,
\]
\[
\operatorname{Cov}(\widehat b)=
(X^TWX)^{-1}X^TWCWX(X^TWX)^{-1}.
\]

A common positive rescaling of W leaves both unchanged; an inverse-Hessian proxy instead rescales by the inverse factor. That proxy is justified by a different precision model, not arbitrary selection reweighting.

Four active unit directions all equal to e1 give design rank one. A bounded prior can make a proper posterior, but adds no data information in the other two directions. Nonfinite inputs must be rejected explicitly. The current pooled_rank_p code does not check score finiteness: an observed NaN makes every ordinary floating comparison false and yields the minimum finite p. This is a source-visible failure mode, NOT a newly run failed test. Chart unavailability must not enter ranking as NaN.

These independent counterexamples define focused future regressions and typed consumers. They do not authorise global legacy cleanup or lifting the existing CF4 P0 quarantine.

## Evidence and remaining closure

T1–T10 are derived under their stated hypotheses. Existing certificate/implementation records are inputs, not new executions. Scalar calculator checks cover the Beta tail, LS RMS bracket and monopole scale. Shell/Python and Wolfram failures prevented new native/CAS/Monte Carlo verification. No empirical anomaly probability, fitted velocity or Bianchi-family inference is reported.

The general algebra is now explicit; the actual CMB foreground/null law, redshift distance/selection likelihood and end-to-end calibration are still MAIN scientific decisions. IMPLEMENTATION_CONTRACT and THEORY_FIRST_DAG keep those three closures ahead of production/data delegation. Codex is not asked to invent their missing assumptions.
