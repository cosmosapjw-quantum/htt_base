# Post-review theoretical results and computational forms

MAIN, 2026-09-07. Status: explicit derivations and selected scalar arithmetic checks. No new native numerical/CAS/observational execution. Novelty is not certified.

The source conventions are the accepted pedagogical Report A at `9c86759f4ac7054d01d88689290a658e8ffd5863`. Existing results and original receipts remain unchanged. This note is a follow-up mathematical development and a narrow correction to one overly restrictive numerical-policy sentence, not a retroactive rewrite of a verified artifact.

Spatial tensors use the full Euclidean Frobenius metric. Spacetime signature is (-,+,+,+); beta is physical velocity divided by c. Q and O have temperature units. The unit shapes q=Q/A_Q and o=O/A_O, with A_Q squared=Q:Q and A_O squared=O:O, are dimensionless. All statistical results explicitly state the probability model. Bounds on geometric rates use one common rate convention; converting all rates by c leaves the dimensionless ratios unchanged.

## T1. The exact axial continuum threshold is L=10

Keep precisely the report's finite fit through ell=5, retained ell=2..5, identity transfer, axial boost generator, and piecewise wide mask. The retained real output dimension is 32. Its m=0,1,2,3,4,5 complex blocks have row counts (4,4,4,3,2,1).

The exact nonzero minors printed in Appendix B use source columns 7..10 for m=0,1,2; 7..9 for m=3; 7..8 for m=4; and 7 for m=5. Every column is already present at L=10. The existing twelve Fraction comparisons and printed certificate therefore imply

\[
\operatorname{rank}_{\mathbb R}K_z^{\rm cont}(10)
=4+2(4+4+3+2+1)=32.
\]

At L<=9 the m=0 block has at most three source columns but four retained rows, and hence cannot be surjective. It follows that **ten is the minimum axial full-row-rank cutoff for this exact operator**. This is a deduction from the existing certificate, not a new invocation of its checker. It does not certify a finite pixel transform.

For a fixed cutoff and mask, the first-order generator makes K_b linear in the three Cartesian components of b. Choose one 32-column minor nonzero for b=z. Its determinant is a nonzero homogeneous polynomial in b. Its zero set has measure zero on the unit sphere: a nonzero homogeneous polynomial cannot vanish identically on the sphere, and polynomial zeros have measure zero unless the polynomial is identically zero. A proof of the latter follows by treating one variable at a time and applying the finite number of roots of a nonzero one-variable polynomial, outside the lower-dimensional zero set of its coefficients. Thus full row rank holds for almost every direction at L=10. This does **not** assert every direction, give a uniform singular-value margin, or replace an exceptional-direction analysis.

Computational use: retain the old fractions; label the L=10 consequence separately. Do not change source columns to manufacture the result or turn a reviewer's unacquired rank scan into exact evidence.

## T2. Deterministic rank certification does not require a prechosen slack

Suppose an actual deterministic perturbation obeys Delta Delta^T <= Gamma, Gamma positive definite, and W=Gamma^(-1/2). For K_obs=K_true+Delta, Weyl's inequality gives

\[
s_m(WK_{\rm true})\ge s_m(WK_{\rm obs})-1.
\]

Therefore any rigorously established s_m(WK_obs)>1 implies full row rank. A displayed delta=s_m(WK_obs)-1 may be chosen after the computation. Prechoosing a positive slack is a reporting convention, not a hypothesis of this deterministic implication.

If the computed singular value has absolute error bounded by epsilon_s, the sufficient test is s_computed-epsilon_s>1. The premise that Gamma contains the actual error cannot be obtained by shrinking Gamma after seeing the desired rank. An empirically selected error family or radius needs its own justified coverage. This separates numerical logic from statistical selection.

This corrects the pedagogical report's blanket sentence that delta 'must not be tuned after inspecting the same singular values'. The stronger, correct restriction is: **do not tune an unjustified error envelope or ignore singular-value uncertainty to make a certificate pass**. An existing witness above the certified floor can be reported a posteriori. The archived PDF is preserved; the correction belongs in its next scientific revision/addendum.

## T3. The low-QO projection null, alternatives and velocity-coordinate variance

For nonzero Q define L_Q O=O:Q and B_Q beta=3 STF(beta tensor Q). The report proves

\[
B_Q^*=3L_Q,\qquad B_Q^*B_Q=3M_Q,
\qquad M_Q=(Q:Q)I+\frac65Q^2.
\]

The projector P_Q=B_Q(3M_Q)^(-1)B_Q^* has rank three in the seven-dimensional real STF3 space.

### Ideal null law

Assume conditional on Q that O=tau g, where g is a standard seven-dimensional Gaussian independent of Q. Choose an orthonormal basis diagonalising P_Q. The squared projected and complementary norms divided by tau squared are independent chi-square variables of dimensions three and four. Their ratio to their sum gives

\[
f_B=\frac{\|P_QO\|_F^2}{\|O\|_F^2}
\sim\mathrm{Beta}(3/2,2),
\qquad p(x)=\frac{15}{4}\sqrt{x}(1-x),
\]
\[
F(x)=\frac52x^{3/2}-\frac32x^{5/2},\qquad
\mathbb E f_B=\frac37.
\]

The density follows either from the chi-square gamma densities and a sum/ratio change of variables or from uniform spherical direction. Integrating the displayed density proves the CDF. The same ratio law holds for an independent uniform octupole direction with fixed nonzero norm. That fixed-norm law is not itself Gaussian.

Mere SO(3) invariance of an arbitrary non-Gaussian octupole distribution is insufficient: the three-dimensional rotation group does not act transitively on the six-sphere of octupole shapes. A covariance proportional to identity does not determine the full projection-fraction distribution. Masked/noisy Q and O can also be dependent. The beta law is an oracle and an ideal-model benchmark, not an automatic Planck p-value.

For a Gaussian mean B_Q beta with the same covariance, the numerator is noncentral chi-square with parameter

\[
\lambda=3\beta^TM_Q\beta/\tau^2,
\]

while the four-dimensional residual remains central and independent. Thus f_B has the corresponding singly noncentral beta law. This provides a power calculation only for this stated conditional mean model.

### Exact LS covariance and the proposal's decimal discrepancy

The algebraic estimator is beta_hat=M_Q^(-1)L_QO. Under the null,

\[
\operatorname{Cov}(\widehat\beta\mid Q)=\frac{\tau^2}{3}M_Q^{-1}
=\frac{A_O^2}{21}M_Q^{-1},
\]

where A_O squared=7 tau squared denotes the expected squared octupole norm. The same covariance follows for the fixed-amplitude sphere with that amplitude, but not the same Gaussian likelihood or Fisher theorem.

For unit q, let s3=tr(q cubed). The previously derived polynomial inverse gives

\[
\operatorname{tr}M_q^{-1}=\frac{90}{40+3s_3^2}.
\]

Tracefree unit eigenvalues imply s3 squared<=1/6. For completeness, maximise their product subject to fixed sum zero and squared norm one using Lagrange multipliers; an extremum has two equal eigenvalues, giving spectra proportional to (-1,-1,2) and s3 squared=1/6. The value zero is attained at (-1,0,1)/sqrt(2). Therefore

\[
\frac{20}{9}\le\operatorname{tr}M_q^{-1}\le\frac94,
\qquad
\sqrt{\frac{20}{189}}\frac{A_O}{A_Q}
\le\sqrt{\mathbb E\|\widehat\beta\|^2}
\le\sqrt{\frac3{28}}\frac{A_O}{A_Q}.
\]

The illustrative inputs D2=226 and D3=1018 microkelvin squared obey A_Q squared=25 D2/8 and A_O squared=245 D3/48. Scalar calculator evaluation gives the bracket **0.882350584718888 to 0.8878481493381544**, not 0.8435. These are dimensionless formal LS-coordinate fluctuations under the supplied ideal model, not inferred physical speeds. They are comparable to unity, so interpreting them as a measured small-beta physical posterior is especially inappropriate.

The Gaussian known-Q Fisher matrix is 3M_Q/tau squared. An arbitrary intrinsic O gives a deterministic degeneracy instead; a prior changes the inference. None of these statements rules out estimating motion with higher CMB multipoles, frequency information or other data.

Scalar check: P(f_B>0.8)=0.06979572136008738. This relatively large null tail illustrates why a large projection fraction alone is weak attribution evidence.

## T4. Sharper kinematical estimates inside the explicitly retained radiation model

These results concern Appendix E's first-order geodesic collisionless radiation model and its precise derivative envelopes. They are not replacements for every MES theorem or unqualified observational improvements.

At retained order, the brightness moments are q_a=(4/3)rho vartheta_a, pi_ab=(8/15)rho vartheta_ab and xi_abc=(8/35)rho vartheta_abc, with dot(rho)=-(4/3)Theta rho in first-order products. The quadrupole equation is

\[
\dot\pi_{\langle ab\rangle}+\frac43\Theta\pi_{ab}
+\frac8{15}\rho\sigma_{ab}
+\frac25D_{\langle a}q_{b\rangle}+D^c\xi_{abc}=0.
\]

Cancel the two background-expansion terms before applying a triangle inequality:

\[
\sigma_{ab}=-\dot\vartheta_{ab}
-D_{\langle a}\vartheta_{b\rangle}
-\frac37D^c\vartheta_{abc}.
\]

### Sharp norm of the STF derivative contraction

Let T map X in R^3 tensor STF3 to STF2 by (TX)_ab=sum_c X_c,abc. Its adjoint has components (T^*S)_c,abc=STF_abc(delta_ca S_bc), equivalently B_S e_c/3. By the normal-matrix identity,

\[
\|T^*S\|^2=\frac19\sum_c\|B_Se_c\|^2
=\frac13\operatorname{tr}M_S
=\frac75\|S\|_F^2.
\]

Thus T T^*=(7/5)I and ||T||=sqrt(7/5), with equality on a suitable adjoint-image vector. The old sqrt(3) contraction bound is valid but not sharp on the STF domain. STF projection of D_a vartheta_b is orthogonal and norm nonincreasing. The improved envelope is consequently

\[
\boxed{\frac{\|\sigma\|_F}{\Theta}
\le\epsilon_2^*+\epsilon_1'+\frac3{\sqrt{35}}\epsilon_3'.}
\]

Under the same characteristic scale substitutions epsilon2*<=epsilon2/3, epsilon1'<=epsilon1/3 and epsilon3'<=epsilon3/3,

\[
\boxed{\frac{\|\sigma\|_F}{\Theta}
\le\frac{\epsilon_1}{3}+\frac{\epsilon_2}{3}
+\frac{\epsilon_3}{\sqrt{35}}.}
\]

### The analogous vorticity cancellation

Let C_ab=D_[a vartheta_b] and Q_ab=D_[a q_b]. The retained commutator and flux equation give

\[
\frac49\Theta\rho\omega_{ab}
=-\dot Q_{ab}-\frac53\Theta Q_{ab}-D_{[a}D^c\pi_{b]c}.
\]

Insert Q=(4/3)rho C and cancel the background product before taking norms:

\[
\omega_{ab}=-\frac3\Theta\dot C_{ab}-C_{ab}
-\frac6{5\Theta}D_{[a}D^c\vartheta_{b]c}.
\]

Using exactly the contracted derivative envelope of Appendix E,

\[
\boxed{\frac{\|\omega_{ab}\|_F}{\Theta}
\le3\epsilon_1^{\prime *}+\epsilon_1'
+\frac65\epsilon_2^{\prime\prime}
\le\frac23\epsilon_1+\frac2{15}\epsilon_2.}
\]

Weak assumptions imply weak inequalities. With H=Theta/3, the corresponding quadratic ceilings are (3/2) times the squares of these displayed bounds. Full antisymmetric tensor norm is used, with omega_ab omega^ab=2 omega_a omega^a. All rates must be converted together if inverse-time units are used.

The gain is obtained by retaining algebraic cancellation and the correct STF domain, not by new data. A small-amplitude field epsilon F((x-x0)/d) can have derivatives of size epsilon/d or epsilon/d squared. Finite point/shell measurements cannot bound all-domain derivatives without regularity or dynamical assumptions. This supplies an explicit counterexample to an unconditional 'single-sky MES bound' or a finite-tomography proof of every observer premise.

## T5. Bounded nuisance is an optimisation problem, not an image-rank slogan

Consider y=A theta+K h+n with a declared source metric S positive definite and h^T S^(-1)h<=R squared. For an exact output displacement d in Im K, the minimum source cost is

\[
c(d)^2=d^T(KSK^T)^+d,
\qquad h_*(d)=SK^T(KSK^T)^+d.
\]

Outside Im K the exact cost is infinite. To prove the formula, set h=S^(1/2)z, use the SVD of K S^(1/2), solve each nonzero singular coordinate, and set null coordinates to zero. Every other solution adds an orthogonal null vector and increases squared norm.

At a fixed zero nuisance reference, d can be mimicked iff c(d)<=R. When comparing TWO arbitrary admissible nuisance states, their difference ranges over the radius-2R ellipsoid. The indistinguishability condition is c(A(theta1-theta2))<=2R, not R. Failing to distinguish these two questions changes the claimed identification region by a factor two.

A finite positive absolute-temperature sky adds another constraint. For a band-limited nuisance with harmonic row vector Y_H(n),

\[
|Y_H(n)h|\le R\sqrt{Y_H(n)S Y_H(n)^T}.
\]

This gives a sufficient positivity margin if the baseline temperature exceeds the supremum. It is not an unrestricted permission to use a large cancelling sky. Image-rank nonidentifiability is global in a linear unconstrained model; physical positivity and norm constraints must be checked in the actual model.

Computational form: use a whitened SVD/QR solve and report finite cost, null directions and singular scales. Never form a pseudoinverse with a threshold selected merely to obtain the desired scientific rank. Numerical accuracy and the model's nuisance radius are different quantities.

## T6. Gaussian marginalisation, measured high modes and directional information

If h and n are independent zero-mean Gaussians with fixed covariances S and N, then y has covariance C=N+KSK^T. This is a model choice, not a consequence of deterministic nuisance geometry.

For a scalar parameter with response A=e1 and N=I2, compare KSK^T=diag(k squared,0) with diag(0,k squared). Their trace powers are identical. Their Fisher informations are 1/(1+k squared) and 1, respectively. Hence a nuisance trace fraction, however close to one, does not determine the information about that parameter.

High modes are often measured by the same experiment. For a joint Gaussian vector (y,z), let its mean be (A_y theta,A_z theta) and covariance blocks C_yy,C_yz,C_zz. Conditional on z,

\[
C_{y|z}=C_{yy}-C_{yz}C_{zz}^{-1}C_{zy},
\]
\[
\mu_{y|z}=A_y\theta+C_{yz}C_{zz}^{-1}(z-A_z\theta),
\qquad A_c=A_y-C_{yz}C_{zz}^{-1}A_z.
\]

For parameter-independent covariance the complete information is

\[
F_{\rm joint}=A_z^TC_{zz}^{-1}A_z+A_c^TC_{y|z}^{-1}A_c.
\]

This follows by block Gaussian elimination, or by factoring p(y,z|theta)=p(z|theta)p(y|z,theta). The conditional residual has zero cross-covariance with z, so the score information adds. Dropping the z term describes a different conditioning experiment; ignoring A_z or C_yz generally changes the answer. A reconstructed high sky conditioned on the same data is not an independent second measurement.

When beta enters the mixing matrix, it also enters the covariance. The general Gaussian Fisher matrix has the additional term

\[
\frac12\operatorname{tr}(C^{-1}C_{,i}C^{-1}C_{,j})
\]

besides mean derivatives. A fixed-source derivative is not a substitute for this latent-sky covariance response.

The existing processed tensor has shape (3,32,49). The parameter derivative for a specified source s is D_alpha,i=sum_A J_i,alpha,A s_A and has shape (32,3). J_b with shape (32,48), after fixing direction b and removing the monopole source column, answers a source-coordinate question. The distinction must be enforced in types and tests.

The absolute processed-sky likelihood also contains zero-boost leakage of high modes under a mask. A pure boost-response K is not the entire high-mode matrix. The model must use the complete ordered transfer/boost/fit operator, including the already boosted or dipole-corrected state of each data release, rather than add a second boost to an existing one.

## T7. Soft-mask rank can remain full while nuisance information loss vanishes

This gives the central quantitative alternative to an unrestricted-image no-go.

Let F be the finite orthonormal fit space through ell=5 and retain its ell=2..5 rows by P. Let H be source ell=7..L, and B_b be the first-order temperature boost in a fixed direction. Define a soft-mask family

\[
w_\varepsilon=1-\varepsilon m,\qquad0\le m\le1,
\qquad0\le\varepsilon\le1.
\]

Let M be multiplication by m restricted between fit modes, M_FF, and V_b=<Y_F,m B_bY_H>. At full sky, the boost of source ell>=7 has ell>=6 and is orthogonal to F. Thus

\[
N_\varepsilon=I-\varepsilon M_{FF},\qquad
R_\varepsilon=-\varepsilon V_b,
\]
\[
\boxed{K_\varepsilon=-\varepsilon P(I-\varepsilon M_{FF})^{-1}V_b.}
\]

For epsilon ||M_FF||<1, the Neumann-series/operator-norm inequality gives

\[
\|K_\varepsilon\|_2\le
\frac{\varepsilon\|V_b\|_2}{1-\varepsilon\|M_{FF}\|_2}=O(\varepsilon).
\]

Choose m=1-w_wide of the exact axial example and L=10. N_epsilon remains positive definite for the whole closed interval: for epsilon<1 the weight is bounded below, and at one the positive open cap and finite harmonic uniqueness suffice. The exact full-rank minor at epsilon=1 is a nonzero rational function of epsilon, with nonvanishing denominator. Its numerator is a nonzero polynomial. It therefore vanishes only at finitely many epsilon values. Except for those values, the nuisance image is all 32 retained dimensions, even arbitrarily close to the unmasked limit.

Nevertheless, to mimic a fixed nonzero d, any nuisance h must satisfy

\[
\|h\|_2\ge\frac{\|d\|_2}{\|K_\varepsilon\|_2}
=\Omega(\varepsilon^{-1}).
\]

The cost metric has the corresponding divergence when its fixed source covariance is bounded. A leading-order equality of order epsilon^(-2) for squared cost additionally requires full row rank of P V_b; that stronger condition is NOT assumed here.

For a fixed bounded Gaussian S,

\[
\|K_\varepsilon S K_\varepsilon^T\|_2=O(\varepsilon^2).
\]

With a nonsingular baseline noise covariance and continuous parameter response, the fixed-covariance Fisher information approaches the no-leakage full-sky value. It need not approach zero although the unrestricted deterministic quotient vanishes at generic positive epsilon. An analogous expansion includes the zero-boost high-mode leakage of the absolute fit, which also vanishes at epsilon=0 for these source bands.

This theorem concerns decreasing mask AMPLITUDE along a specified smooth family, not every sequence of binary masks with the same f_sky. It proves a distinction among exact image rank, bounded-nuisance cost and Gaussian information. Numerical tests of that distinction can be designed without pretending to have a physical prior-free global-tilt measurement.

## T8. Finite observer motion and physical scale ordering

For a positive monopole in the outward-sky convention,

\[
T'(n)=\frac{T_0}{\gamma(1-\beta\cdot n)}.
\]

Writing x=beta dot n, its expansion through cubic order is T0[1+x+x squared-beta squared/2+x cubed-(beta squared/2)x]+O(beta to the fourth). The STF quadrupole is T0 beta_<a beta_b>, and the leading STF octupole is T0 beta_<a beta_b beta_c>. These do not vanish because the retained linear monopole response is a dipole.

For the explicitly illustrative T0=2.7255 K and |beta|=0.001234, the coefficient scale T0 beta squared is **4.150271478 microkelvin**. This is not itself the Frobenius quadrupole norm, and it is not a new sky measurement. It shows why retaining only terms linear in beta but dropping a known large monopole can be inconsistent with the precision sought for beta times anisotropy. Use the existing exact positive-temperature pullback and the actual release convention; do not double-subtract a kinematic correction already in the map.

## T9. Redshift data need new response directions, not merely more bins

For a local affine velocity field,

\[
v(rn)=V+r Hn+r\Sigma n+\Omega\times(rn),
\qquad n\cdot v=n\cdot V+rH+r n^T\Sigma n.
\]

The antisymmetric/rigid-rotation term has zero radial projection for every n and r. Perfect radial data therefore leave that vorticity mode unidentifiable. This is an exact kernel statement, not a sample-size limitation. Weak-lensing shear has a different physical response and is not a direct measurement of this congruence shear by shared terminology.

A simple frame-degeneracy example is

\[
d=\beta+d_{\rm int},\qquad
u_b(n)=n\cdot(V_b-c\beta).
\]

For any three-vector a, beta -> beta+a, d_int -> d_int-a and V_b -> V_b+c a leaves all these observations unchanged. Free shell velocities plus a dipole do not break the degeneracy. High-multipole aberration/modulation, or a declared dynamical prior/tracer response, can add genuinely new directions. A density-reconstructed velocity field that already used the CMB frame, the same distances or the same galaxies is not an independent anchor unless the joint law accounts for that reuse.

The identity a_lm=sum_b a_lm^(b) is a source-integral decomposition, not observation of a CMB sky at each redshift. A remote dipole/quadrupole estimator is a windowed electron-scattering response. Finite windows have a nontrivial nullspace; smooth functions supported between sampled locations, or orthogonal to the finite window span, can have arbitrarily large derivatives after rescaling their variation length. Thus such data cannot by themselves establish the universal derivative premises of T4. A regularity or transfer hypothesis must be stated and tested where possible.

## T10. Survey weights, covariance and a concrete static code finding

The existing `common/bulkflow_likelihood.py` treats selection weights as Gaussian precision and describes weight two as two independent measurements. A Gaussian with variance sigma squared/w is a valid normalised model IF w is genuinely a precision factor. It is not automatically the likelihood of a survey inverse-inclusion weight. Even its normalisation is not the product of two identical Gaussian observation densities. The distinction affects evidence and nuisance-scatter inference as well as uncertainty.

For a fixed weighting matrix W and actual observational covariance C, the linear estimator and covariance are

\[
\widehat b=(X^TWX)^{-1}X^TWu,
\]
\[
\operatorname{Cov}(\widehat b)=
(X^TWX)^{-1}X^TWCWX(X^TWX)^{-1}.
\]

A common rescaling W -> aW leaves both the estimate and this sandwich covariance unchanged. Treating (X^TWX)^(-1) as the uncertainty instead rescales it by 1/a. This is appropriate only under the different model C=W^(-1), not under arbitrary design reweighting.

Required regression counterexamples follow directly: at least four active rows all along e1 have design rank one, not three; adding inverse-selection weights does not create two missing response directions. Nonfinite velocities/errors/weights must be rejected explicitly. The current `pooled_rank_p` also lacks an input-finiteness check: if the observation score is NaN, every comparison s>=obs is false under ordinary floating semantics and the formula produces its smallest p. This is a static, source-visible failure mode, not a newly executed failing test. A caller must not encode chart unavailability as NaN and then rank it.

These findings justify focused future adapters and negative tests, not unscoped cleanup or reopening every historical result. Old CF4 P0 quarantine remains enforced until the relevant physical-data likelihood is genuinely repaired and admitted.

## Evidence status and closure

T1–T10 are explicit finite-dimensional or retained-model derivations. Their assumptions and limiting cases are part of the results. The cited baseline certificate and implementations are source inputs; they are not new executions. The f_B tail, LS RMS bracket and monopole coefficient scale were evaluated with the web calculator. Shell/Python and Wolfram failures prevented new native tests/CAS. No empirical anomaly probability, fitted velocity, simulated power curve or model-independent Bianchi-family statement is reported.

These results close the general algebra needed by the next programme. They do NOT specify the entire survey likelihood, foreground policy, actual release-matched covariance and data-selection function. The remaining MAIN theory decisions and a no-research-choice execution contract are listed in `IMPLEMENTATION_CONTRACT.md` and `THEORY_FIRST_DAG.yaml`; full production/data delegation is held until those choices are resolved rather than outsourced to Codex.
