# R66 R4–R5 / C3 — Commander morphology to a qualified radiation-stress observable

Date: 2026-11-17. Selected child scope: constructive equations, derivations, finite-experiment design, and implementation handoff. Requested profile: gpt-6-astra/xhigh; independently observed model identity: UNKNOWN. No child delegation, native repository mutation, FITS processing, fit, download, or publication is performed. Root owns execution and integration. This file preserves the user's occupancy meaning of F, correcting the incompatible support-function relabeling in the R63 scratch mapping.

Skill context actually read: PhysMath Research Loop 1.3.0 main; POLICY_INTEGRATION; THEORY_LOOP selected R4–R5; CODING_LOOP selected C3; SUBAGENT_MODE. Source prerequisites actually read: `r66_literature.md`, `r66_sources.json`, `r66_history.md`; `r63_five_variable_map.md` and `r64_likelihood_map.md` only for inherited symbol disambiguation. Original R36 radiation-core capability is reused, not reimplemented or claimed new. Equations below are direct derivations unless explicitly attributed to the source map. No strong no-go or priority claim is made.

## 1. Narrow physical question and conventions

For actual PR3/PR4 Commander temperatures processed by one explicitly known finite downstream estimator, determine the signed quadrupole-sector photon anisotropic stress that survives an unknown amplitude of one declared processed Doppler-quadrupole template. Retain the full tensor and removed coordinate; determine how much the scalar C2 and axes would discard; use only a source-qualified reference law. Execution rejected the existing100 005a I=0 rows and instead propagated an explicit ideal Gaussian pixel model; see IDEAL_REFERENCE.md and RESULTS/SOURCE_FAILURE_AND_REPAIR.json.

Metric is (-,+,+,+); x0=ct; n points toward the observed sky, photon propagation e=-n. Temperature is thermodynamic kelvin and T0=2.72548 K. Define T_mu=10^6 T0 in μK and

    rho0 = a_R T0^4,       a_R = pi^2 k_B^4/(15 hbar^3 c^3),
    Q_T = sum_A v_A S_A,   Theta_2(n) = Q_T:nn / T_mu,
    pi_lin = kappa sum_A v_A S_A,
    kappa = 8 rho0/(15 T_mu),       lambda = kappa/rho0 = 8/(15 T_mu).

Here v is a five-vector in μK, Q_T a temperature STF tensor in μK, pi_lin has units J m^-3=Pa, and s_lin=lambda v is the dimensionless five-vector for pi_lin/rho0. This Q_T is distinct from the five-view anchor/gauge denoted mathcal Q below. Physical anisotropic stress pi is distinct from five-view exceedance Pi.

The orthonormal STF basis is S=[(xx−yy)/sqrt2,(xx+yy−2zz)/sqrt6,(xy+yx)/sqrt2,(xz+zx)/sqrt2,(yz+zy)/sqrt2]. For the R60 packed real-harmonic vector

    d = [a20, sqrt2 Re a21, -sqrt2 Im a21,
              sqrt2 Re a22, -sqrt2 Im a22],
    v = C d = [d3,-d0,d4,-d1,-d2]/sqrt(8 pi/15).

Thus ||v||^2=15||d||^2/(8 pi) and C2=||d||^2/5=(8 pi/75)||v||^2. This map is signed, invertible, and unit preserving apart from its explicit dimensionless normalization. A change of basis creates no information.

The physical target is a local radiation observable, qualified by spectral and observer-frame assumptions. It is not an inference of spacetime shear. The radiation-stress relation and DQ physics are established in S2/S10/S11 of `r66_sources.json`; their application to actual common processing and the ensuing data result are the possible empirical increment.

## 2. Actual finite estimator and the response that it really calibrates

Let t be the finite selected pixel vector in μK after explicitly recorded unit conversion, ordering, mask/coverage choice and degradation. Let X2 be the five real ell=2 harmonics sampled on those pixels. Let Z contain the fitted monopole, dipole and the ell=3,...,6 columns. With a fixed positive weight matrix W on retained pixels,

    M_Z = I - Z (Z^T W Z)^-1 Z^T W,
    E = (X2^T W M_Z X2)^-1 X2^T W M_Z,
    y = E t  in R^5.

Pseudoinverse forms are allowed only with the resolved design rank recorded; a rank-deficient fit does not inherit the invertibility conclusions below. This Frisch–Waugh form is exactly the ell=2 block of the simultaneous ell=0,...,6 weighted least-squares estimator. It proves E Z=0 and E X2=I when the declared design has full column rank. E is fixed by geometry and declared weights, not refitted using each realization's residuals. Any additional known linear pixel operator can be included to the right of E.

For STF injection columns J[p,A]=S_A:n_p n_p, define

    R = E J,                      y = R v + a b + e,
    B = STF(beta beta),
    b = E [T_mu (B:nn)],           beta=v_obs/c.

R is 5x5 and maps the physical temperature-quadrupole coefficients v to the measured harmonic coefficients y. The stress response is R_pi=R/kappa. In the ideal consistently sampled fit R=C^-1, but this is a check, not an assumption. When native pixel injection and degradation are included, R must be obtained by forwarding the five J columns through precisely that same downstream chain. Native child averaging differs from evaluation at pixel centers and belongs in this injection.

The b defined here is an **actual downstream response to a declared ideal DQ sky template**. It is not an independently identified end-to-end PR3/PR4 residual calibration. If an upstream physical map response P is known, replace J by P J and the DQ template by its source-matched propagated residual. Without that P, the derived response is conditional on the released map's calibrated low-ell thermodynamic interpretation. Identical post-release processing does not prove identical upstream beams, component-separation transfer, DQ subtraction, foreground residuals or noise law.

Use the known finite beta vector only to define direction and normalization; the scalar a absorbs unknown residual amplitude and sign. Rescaling b rescales a but leaves the quotient unchanged. If beta=0 then b=0: there is no rank-one direction to remove and all five coordinates remain.

## 3. Rank-one nuisance quotient and physical identified set

For b nonzero, construct a 5x4 matrix U with U^T U=I4 and U^T b=0 by a stable full SVD or Householder completion. Keep its basis in the output, since the four coordinates are otherwise not interpretable. Then

    y_bar = U^T y,       A = U^T R,
    y_bar = A v + U^T e.

**Finite linear-algebra statement.** If R is nonsingular, rank(A)=4 and ker(A)=span{k}, where k=R^-1 b. Proof: multiplying a rank-four U^T by an invertible R preserves rank; A v=0 iff Rv belongs to ker(U^T)=span{b}. No general physical impossibility theorem is involved.

In the deterministic zero-error experiment the identified physical set is the affine line

    V(y) = {R^-1(y-a b): a in R}.

The corresponding linear stress set is kappa times its STF image. With a covariance C4 or an error body, replace the equality by its four-dimensional region; the full five-dimensional set is an unbounded cylinder unless an independently justified bound on a or on the physical tensor is supplied. A minimum-norm representative is a coordinate choice, not a measurement of the missing component.

Let V be a 5x4 orthonormal basis perpendicular to k, and let H=A V. H is invertible. The canonical representative and identifiable stress coordinates are

    v_hat_perp = V H^-1 y_bar,
    x = lambda H^-1 y_bar in R^4,
    s_rep = V x,                 pi_rep = rho0 sum_A (Vx)_A S_A.

This is the signed tensorized carrier in physical units with its missing direction explicitly retained. If b=R vec(T_mu B), then k is proportional to the expected beta-beta STF direction. More complicated processed nuisances need not have that special shape.

For several independent nuisance responses Bm=[b1,...,br], use U spanning ker(Bm^T), giving dimension 5-r and rank 5-r when R is invertible and rank(Bm)=r. For example, a spatially varying spectral response q_eff(n)=q0+q1 f(n) creates both E[B:nn] and E[f(n) B:nn]. Their ell=2 images can be linearly independent. A one-dimensional quotient then leaves a residual nuisance. Determine the response span from source-matched templates or state a conditional rank-one family; do not infer its physical rank from the five ideal STF injections.

### Euclidean quotient versus covariance profiling

For a fixed positive-definite C5, Gaussian profiling over a yields

    a_hat(v) = b^T C5^-1(y-Rv)/(b^T C5^-1 b),
    W_prof = C5^-1 - C5^-1 b (b^T C5^-1 b)^-1 b^T C5^-1,
    chi2_prof(v) = (y-Rv)^T W_prof (y-Rv).

The exact identity

    W_prof = U (U^T C5 U)^-1 U^T

shows that the Euclidean-coordinate quotient, with its full covariance C4=U^T C5 U, has exactly the same quadratic likelihood as covariance-weighted profiling. One proof uses C5^(-1/2)b and its orthogonal complement to write both sides as the same whitened rank-four projector. The covariance-weighted residual operator I-b(b^T C5^-1)/(b^T C5^-1 b) is generally oblique in Euclidean coordinates. This changes coordinates, not the identifiable subspace. Replacing C4 by a scalar variance is a different likelihood and can lose information.

For finite-N covariance inference, estimate the covariance directly in fixed U coordinates and use the dimension-four formulas below. Taking a five-dimensional predictive Student density and merely maximizing over a need not equal the normalized four-dimensional predictive density: marginalization/reduction changes the law. The quadratic profiling identity by itself establishes no such equality of Student normalizing factors or degrees of freedom.

## 4. Population reference and exact finite-N alternatives

Execution correction: the originally proposed100 public005a rows have exactlyzero I and are ineligible for a temperature reference. The executed primary law is a known-covariance ideal Gaussian model; its statistic is chi-square4. Its4096 synthetic operator draws validate that model and supply2048 training/2048 heldout rows for the exploratory paired construction. They are not Commander end-to-end simulations. The formulas below remain generic covariance-estimation alternatives; N=100 is only an illustrative example, not an acquired qualified temperature bank. Let p=4 after the fixed quotient (or p=5 before it), N>p, and z_i=U^T E t_i the identically processed hypothetical simulation rows. Independence, Gaussianity, shared covariance and observed/simulated exchangeability are hypotheses of this finite experiment. The last is not established by the available PR4 source contract. Fixed masks, U and injection responses must not be tuned on the same simulation realizations used for the exact formulas.

There are two different scientific questions.

1. **Realized-sky radiation image.** y_bar reports the actual sky's processed signed coefficients. An MC bank of different random CMB skies supplies a reference distribution across possible skies. Its scatter is not measurement error conditional on the realized sky. To quantify conditional measurement uncertainty requires an instrument/foreground law or repeated simulations with the same input sky. The deterministic physical image can be reported without mislabeling cosmic variance as an observational error bar.
2. **Deterministic mean stress plus stochastic sky.** Postulate y_bar=H_pi theta+epsilon, epsilon~N_p(0,Sigma), where theta is a chosen deterministic physical mean stress and H_pi is the explicit response (A/kappa for five physical components, or H/kappa for four transverse components). Then the CMB ensemble covariance is the correct stochastic background for that model. It is not a separation of the observed tensor into measured deterministic and random components. Four free identifiable mean coordinates fit four data coordinates exactly, so there is no residual full-model goodness-of-fit degree of freedom. Restricted source models can be tested against this saturated mean model.

The exact joint likelihood, with known zero background mean, is

    L(theta,Sigma | y_bar,z_1,...,z_N)
      ∝ |Sigma|^(-(N+1)/2)
        exp{-[tr(Sigma^-1 sum_i z_i z_i^T)
                    +(y_bar-H_pi theta)^T Sigma^-1(y_bar-H_pi theta)]/2}.

Unknown Sigma remains a parameter in this expression. The following pivots are exact frequentist statements under the listed Gaussian experiment. Predictive Student densities additionally integrate Sigma under the explicitly stated prior; they are not prior-free identities about an unknown covariance.

### Three legitimate covariance conventions — do not mix them

Let q=r^T S^-1 r. Use the matching row of this table.

| Simulation mean handling | S and residual r | Wishart df nu_W | k | Exact pivot |
|---|---|---:|---:|---|
| Background mean known zero; use uncentered scatter | S0=N^-1 sum z_i z_i^T; r=y_bar-H_pi theta | N | 1 | [(N-p+1)/(pN)] q ~ F_(p,N-p+1) |
| Background mean known zero; intentionally use centered sample covariance | S=(N-1)^-1 sum(z_i-zbar)(z_i-zbar)^T; r=y_bar-H_pi theta | N-1 | 1 | [(N-p)/(p(N-1))] q ~ F_(p,N-p) |
| Unknown common background mean estimated from MC | Same S; r=y_bar-zbar-H_pi theta | N-1 | 1+1/N | [(N-p)/(p(N-1)k)] q ~ F_(p,N-p) |

Derivation: W=nu_W S~Wishart_p(Sigma,nu_W); r/sqrt(k) is an independent N_p(0,Sigma). Whiten Sigma. Rotational invariance sets the Gaussian vector along one axis conditional on its length. The reciprocal corresponding diagonal entry of W^-1 is an independent chi-square with nu_W-p+1 degrees, whereas the squared vector length is chi-square_p. Therefore

    [(nu_W-p+1)/(p nu_W k)] q ~ F_(p,nu_W-p+1).

For the last row, independence of Gaussian sample mean and sample covariance gives Var(y_bar-zbar)=k Sigma. For the middle row the unused sample mean is not subtracted from the observation, so k remains 1. For the first row the known-zero scatter has N, not N-1, Wishart degrees. N=100,p=4 therefore gives denominator degrees 97 or 96; p=5 gives 96 or 95. Treating 100 skies as 100 independent measurements of this realized sky is incorrect.

With pi(Sigma)∝|Sigma|^(-(p+1)/2), and a flat prior on an unknown common mean only in the third row, the corresponding conditional predictive density is multivariate Student with

    nu = nu_W-p+1,
    Omega = k nu_W S/nu,
    p(r|simulations) = Gamma((nu+p)/2)
       / [Gamma(nu/2) (nu pi)^(p/2) |Omega|^(1/2)]
       × [1 + r^T Omega^-1 r / nu]^(-(nu+p)/2).

Use this as a likelihood in theta only after declaring the mean-background model and covariance prior. The confidence/reference ellipsoid obtained by pivot inversion is

    r^T S^-1 r <= c_alpha^2,
    c_alpha^2 = k p nu_W/nu × F_(p,nu)^(-1)(alpha).

Covariance in x units is Cx=lambda^2 H^-1 S H^-T. The same c_alpha applies after this invertible coordinate change. Sample-mean uncertainty does not justify another ad hoc covariance floor or a second use of the simulated mean.

Wishart also quantifies Monte Carlo uncertainty: E(S)=Sigma and

    Cov(S_ij,S_kl)=(Sigma_ik Sigma_jl+Sigma_il Sigma_jk)/nu_W.

For a fixed scalar direction u, nu_W (u^T S u)/(u^T Sigma u)~chi-square_(nu_W), so its estimated variance has relative standard deviation sqrt(2/nu_W), about 14.2% for nu_W=99. This is simulation calibration uncertainty, distinct from instrumental uncertainty and stochastic sky scatter. Inversion requires N>p in the centered case; the existence of a sample inverse alone does not establish Gaussianity or exchangeability.

An unmodeled foreground mean, an ensemble containing only one of signal/noise, different upstream transfer, or correlated/duplicated realizations invalidates these exact pivots for the actual observation. The equations remain an executable conditional experiment; outputs must retain that scope. PR3 and PR4 observe the same CMB realization, so do not multiply their likelihoods as independent skies. Their difference is a processing contrast whose uncertainty requires the paired joint covariance.

## 5. Tensorized five views with original occupancy semantics

These views are pushforwards of one experiment; they are not five independent likelihood factors. Keep the source of every measure explicit.

**x — signed carrier.** Retain y5, removed b coordinate, y_bar, U, R, V, H, x4, its physical STF representative and full affine null direction. Its exact physical interpretation is pi_lin/rho0 until the finite-temperature completion below supplies the correction to pi/rho. Store actual PR3/PR4 vectors and their contrast, not only norms or axes.

**mathcal Q — anchor and gauge.** For a declared positive-definite reference body K_B={x:x^T B^-1 x<=1}, mathcal Q_B(x)=sqrt(x^T B^-1 x). A stochastic covariance ellipsoid is a statistical anchor, not a universal physical ceiling. There is also a useful exact positivity body for normalized radiation stress, derived next.

**Pi — exceedance under a law.** For example, Pi_G(t)=Pr_G[x^T Cx^-1 x>t] under the zero-mean Gaussian reference, or its finite-N pivot tail under the table above. State whether it is an ensemble reference tail, a test of an imposed deterministic mean, or a posterior exceedance under a declared prior. A confidence region alone defines no probability measure on the true stress. Preserve the vector and response alongside any scalar tail.

**F — occupancy with explicit denominator.** F is not a support function. For an admissible body K in the identifiable physical coordinate space, a finite measure mu with 0<mu(K)<infinity, and a declared region E,

    F_mu(E;K)=mu(E intersect K)/mu(K).

This is occupancy of E in K under mu; it is neither probability that the true tensor lies in E nor the volume filling fraction of a spatial Universe unless that separate spatial interpretation is supplied. Save numerator, denominator, K, measure, coordinate frame, physical units, conditioning and finite-region threshold. A Gaussian reference measure gives

    mu_G(D)=∫_D N_p(x;0,C_ref) dx,
    F_G(E;K)=Pr_G(X in E intersect K)/Pr_G(X in K).

This is a valid vector-ellipsoid occupancy alternative to radial scalarization, but the scalar ratio itself still loses direction. Retain E's signed center/full quadratic form and optionally directional sectors D_j with F_j=mu(E intersect K intersect D_j)/mu(K intersect D_j); the denominator and selection are then part of every reported value. Zero-denominator sectors are undefined, not zero occupancy. Uniform volume and Gaussian-reference occupancy are distinct measures and must not be interchanged.

**G_F — declared depth-gap functional.** There is no physical depth series in this one last-scattering-sky experiment. G_F is NOT_APPLICABLE here. PR3/PR4 are releases of the same sky, and ell is angular scale, not source depth. A release difference of F may be labelled a processing sensitivity, but it is not the original physical depth gap. Future actual depth-bin F reports would require their bin measures, selections, transport and full joint dependence before forming the declared gap.

### A constructive physical reference body, and its exact limitation

For any nonnegative angular intensity I, define normalized pressure P=<I nn>/<I>. Then P is positive semidefinite and tr(P)=1, so

    S=pi/rho=P-I3/3,
    K_phys={S=S^T, tr S=0, I3/3+S positive semidefinite}.

Conversely, the spectral decomposition P=sum_i w_i e_i e_i^T, w_i>=0, sum_i w_i=1, constructs that pressure from positive intensities on antipodal rays. Smooth strictly positive thermal skies realize the interior and approach the boundary. Hence K_phys is the sharp closed moment body for nonnegative radiation intensity, not a theory of CMB production.

Eigenvalues of P lie in [0,1]; therefore eigenvalues of S lie in [-1/3,2/3] and ||S||_F<=sqrt(2/3). For traceless symmetric S, |lambda_min(S)|<=sqrt(2/3)||S||_F: fix its most negative eigenvalue -a, and minimize the other two squared eigenvalues subject to summing to a, giving ||S||^2>=3a^2/2. Thus the Frobenius ball of radius R_in=1/sqrt6 lies inside K_phys. It is a certified admissible **inner body**, not the sharp universal upper bound: diag(2/3,-1/3,-1/3) is a counterexample to such an upper-bound reading.

For an orthonormal identified transverse plane V, the exact quotient body is

    K_quot={V^T vec(S):S in K_phys}.

It contains the p=4 ball of radius R_in; a point in that ball has the admissible representative S=mat(Vx). The projected true S may also lie outside this inner ball while remaining physical. For the full K_quot, membership is the small semidefinite feasibility problem

    exists a: I3/3 + mat(Vx+a k_unit) >= 0.

Thus a physical, finite positivity-based reference exists even though it is far too broad to act as a useful CMB production prior. Report an inner-ball occupancy only as occupancy relative to that declared admissible reference body, not a fraction of the entire sharp physical body.

For E={x:(x-xhat)^T Cx^-1(x-xhat)<=c_alpha^2} wholly within B_(R_in), uniform four-volume gives the exact ratio

    F_vol(E;B_Rin)=c_alpha^4 sqrt(det Cx)/R_in^4.

A sufficient containment check is ||xhat||+c_alpha sqrt(lambda_max(Cx))<=R_in. If it fails, use the actual intersection volume; do not retain the whole-ellipsoid formula or clip a value exceeding 1. Its center independence while contained shows why this F alone does not retain directional information. Tiny occupancy is expected because radiation positivity permits order-unity normalized stress whereas CMB anisotropy is small; small F is not evidence for anomalous cosmology.

This positivity construction applies exactly to S=pi/rho. Applying it to x=lambda H^-1 y_bar is only a linear proxy until the normalization/nonlinear/frame bounds below are supplied. A cosmic-reference mean confidence ellipsoid is not automatically an ellipsoid for the realized normalized stress. Label the target and its law accordingly. If the required completion is absent, retain physical F as UNAVAILABLE and optionally report a distinctly labelled conditional proxy-reference occupancy. This leaves x/mathcal Q/Pi useful without inventing missing physics.

## 6. Why retaining the vector matters: a local information calculation

Consider a mean-shift experiment z~N_p(m,I), obtainable from the quotient by whitening with a fixed covariance. Its Fisher matrix for m is I_p. Retaining only T=||z||^2 gives a noncentral chi-square_p distribution with noncentrality lambda_nc=||m||^2. Consequently its density is even in m, every derivative with respect to m vanishes at m=0, and the Fisher matrix for the vector mean is zero at that point. More explicitly,

    score_T(m) = 2m ∂_(lambda_nc) log f(T;lambda_nc),
    I_T(m) = 4m m^T E[(∂_(lambda_nc) log f)^2],

which has rank at most one away from the origin and rank zero at the origin. The full vector retains p independent mean directions. This is a scoped local mean-parameter statement, not a claim that power contains no amplitude information: lambda_nc can be constrained, and nonregular behavior at lambda_nc=0 must be handled correctly.

For a general centered Gaussian with known anisotropic covariance, an unwhitened radial statistic is still even under m→−m, so its first derivative and mean Fisher information vanish at zero; its away-from-zero structure need not depend only on ||m||. The particularly simple rank-one formula belongs to the isotropic/whitened case. The stochastic realization-to-realization variance is not reduced by a coordinate change.

C2 is an unsigned radial compression of the full ell=2 vector. Quadrupole axes alone additionally discard amplitude; headless axes do not determine the sign of an eigenvector or the sign-reversed tensor, and repeated eigenvalues have an undetermined eigenspace. The zero tensor has no preferred axes. Signed eigenvalues plus an oriented orthogonal eigensystem can reconstruct Q_T modulo the standard eigenbasis equivalences, but axes-only morphology cannot. Since the DQ subtraction/quotient acts along a specific signed STF direction, retaining the full vector is operationally necessary to carry that physical nuisance correctly. This is standard information retention, not a novelty claim.

## 7. Exact T^4 completion, retained-band nonlinear terms and missing-band bounds

Assume directional blackbody radiation and an absolute observer-frame temperature T(n)=T0[1+delta(n)]>0. Let N(n)=nn-I3/3 and average over the full sphere. Exact local moments are

    rho/rho0=< (1+delta)^4 >,
    pi/rho0=< (1+delta)^4 N >,
    F_energy/(c rho0)= -< (1+delta)^4 n >.

The negative odd-moment sign follows from sky-look n. An anisotropy-only or dipole-subtracted component map does not itself supply this absolute T(n). Restore the physical monopole, dipole and release correction state before calling these exact observed stress moments. Otherwise call the result a retained-band/sector reconstruction under the explicitly supplied restoration.

Let delta_L contain the restored ell=0,1 terms and the fitted ell=2,...,6 terms, and h=delta-delta_L the missing field. Reusing the R36 exact moment integrator on (1+delta_L)^4 retains every cubic/quartic cross term without a new perturbative implementation. Because delta_L is a sphere polynomial of degree <=6, stress integrands have degree <=26. A product rule with 14 Gauss–Legendre nodes in cos(theta) and at least 27 equally spaced azimuth nodes integrates these polynomial moments exactly in exact arithmetic. A denser existing R36 grid is also valid; native-pixel integration of an actual map is a different finite observable and should retain its own quadrature/operator error.

For illustration take delta=d.n+Q:nn+O:nnn, with Q rank-two STF, O rank-three STF and no monopole. At second order,

    pi/rho0 = (8/15)Q + (4/5)STF(dd)
              + (16/35)STF(Q^2) + (24/35)d_k O_kij
              + the O^2 contribution + O(delta^3).

The dO coefficient follows directly from the sixth angular moment: all traces of O vanish, leaving six surviving contractions over 105, so <(d.n)(O:nnn)N_ij>=(2/35)d_k O_kij; the cross term in 6delta^2 multiplies it by 12. At ell<=6, all quadratic pairs satisfying |ell−ell'|<=2<=ell+ell' and ell+ell'+2 even can contribute. In particular dipole×octupole is order beta Theta3 and can be larger than Q^2. Computing only dipole^2 and Q^2 is not a consistent second-order retained-band stress reconstruction.

### Data-dependent finite-operator certificates

Let a known finite linear operator L map scalar pixel values to the final five- or four-vector. Examples are the actual angular moment operator, the processed brightness-quadrupole estimator, or its nuisance quotient. Let Wp=diag(w_p)>0 on retained pixels and define

    Lnorm = ||L Wp^(-1/2)||_2
          = sqrt(lambda_max(L Wp^-1 L^T)).

Then every pixel residual r satisfies

    ||L r||_2 <= Lnorm [sum_p w_p r_p^2]^(1/2).

This carries the actual weights/mask/processing amplification; it can be computed from a 4x4 or 5x5 Gram matrix, without constructing an enormous matrix norm. For exact full-sky STF moments Lf=<f vec(N)>, normalized full-sky L2 weights give Lnorm=sqrt(2/15), since <(S_A:nn)(S_B:nn)>=2 delta_AB/15. The easier pointwise bound uses ||N||_F=sqrt(2/3).

For retaining only the linear stress, put r_L=6delta_L^2+4delta_L^3+delta_L^4. For retaining quadratic stress, put r_Q=4delta_L^3+delta_L^4. Their actual finite-map remainders are bounded by rho0 Lnorm ||r||_(Wp,2). These are computable deterministic certificates on the declared retained-band/pixel experiment, not estimates obtained by fitting a new noise floor.

If |delta|<=epsilon on the full sky, the corresponding simpler bounds are

    ||pi-pi_lin||_F/rho0 <= sqrt(2/3)(6epsilon^2+4epsilon^3+epsilon^4),
    ||pi-pi_through2||_F/rho0 <= sqrt(2/3)(4epsilon^3+epsilon^4).

For the missing field, the exact polynomial difference is

    Delta_h=(1+delta_L+h)^4-(1+delta_L)^4
      =4(1+delta_L)^3 h+6(1+delta_L)^2 h^2
        +4(1+delta_L)h^3+h^4.

Use Lnorm ||Delta_h||_(Wp,2) if an actual finite residual h is supplied. If only |h|<=eta and |delta_L|<=epsilon_L are available, a full-sky conservative bound is sqrt(2/3) times

    4(1+epsilon_L)^3 eta + 6(1+epsilon_L)^2 eta^2
       +4(1+epsilon_L)eta^3+eta^4.

If h has strictly ell>=7 on the full sphere, the linear term <4h N> is exactly zero. Writing ell2-norms ell_L=<delta_L^2>^(1/2), r_h=<h^2>^(1/2), a sharper useful bound is

    ||Delta pi_h||_F/rho0 <= sqrt(2/3) [
       (12+12epsilon_L+4epsilon_L^2) ell_L r_h
       +{6(1+epsilon_L)^2+4(1+epsilon_L)eta+eta^2} r_h^2 ].

This follows by expanding Delta_h−4h, bounding the remaining cross terms with Cauchy–Schwarz, and using <|h|^3><=eta r_h^2 and <h^4><=eta^2 r_h^2. At quadratic order low/high cross terms are even more restricted: only ell5×ell7 and ell6×ell8 survive for an exact ell<=6/ell>=7 split. High×high terms remain. These cancellations do not hold merely because a masked finite LSQ residual is called 'high ell'. The actual finite L can leak h into the linear quadrupole; carry Lh or its operator-norm bound explicitly.

An observed downgraded map residual bounds that finite processed map, not every unresolved native/high-frequency CMB mode or unobserved masked region. A valid all-sky physical certificate needs the missing-mode envelope or a declared stochastic completion. Without it, report the exact retained-band result and the symbolic conditional bound separately. No numerical high-ell bound should be invented.

### Normalization and frame restoration

Let P_lin=pi_lin/rho0, pi/rho0=P_lin+e_pi, and rho/rho0=1+e_rho. If |e_rho|<=eta_rho<1 and ||e_pi||<=eta_pi, then

    ||pi/rho-P_lin|| <= [eta_pi+eta_rho ||P_lin||]/(1-eta_rho).

When <delta>=0, e_rho=6<delta^2>+4<delta^3>+<delta^4> and the exact mean of T^4 is at least T0^4 by convexity, so the denominator can be sharpened using the actual positive mean. These bounds, plus frame/calibration completion, are what permit transfer from the linear proxy to the exact positivity body in Section5.

For an isotropic radiation field seen after a boost, Q=STF(beta beta), d=beta+O(beta^3). The quadratic expression gives

    pi/rho_rest = [(8/15)+(4/5)]STF(beta beta)+O(beta^4)
                = (4/3)STF(beta beta)+O(beta^4),

matching the exact perfect-radiation boost, pi=(4/3)rho_rest gamma^2 STF(beta beta). Dropping the restored dipole loses the 4/5 term. The radiation Landau frame has zero anisotropic stress for this pure boost, whereas the observer frame need not. Projecting one DQ coefficient is not a Lorentz transformation and does not find the Landau frame. Reuse the existing exact R36 flux/stress/Landau/boost machinery only after a qualified full absolute temperature completion has supplied all required moments.

## 8. Implementable finite experiment and the specific new data question

The root's proposed computation can now be stated without an extra methodological loop:

1. Fit actual PR3 and PR4 temperatures with the same finite ell=0,...,6 downstream estimator at NSIDE64 and the declared NSIDE128 sensitivity alternative; retain all fitted modes and exact input units/order/mask. The actual NSIDE128 control recomputes coverage>=0.995 and keeps 145936 pixels, whereas NSIDE64 keeps 33277 pixels. This changes both pixel resolution and retained mask support; it is not a pure discretization-convergence test. The PR4 observed and MC temperature resolutions/units differ and must be converted according to their own headers/receipts.
2. Forward five STF skies and one ideal DQ sky through the actual native-pixel/degradation/fit chain. Save R,b,rank,condition,signed coefficients,scalar normalization and their NSIDE contrast. Claim downstream calibration only.
3. Compute U,A,k,V,H and the full signed physical proxy/identified set; keep both release tensors and the removed coordinate. Quantify release contrast parallel and perpendicular to b, preserving their common-sky character.
4. Preserve the rejection of all100 zero-I005a rows. Propagate the archived PlanckTT spectrum through the same three estimator weights under the declared Gaussian parent-pixel model (IDEAL_REFERENCE.md). Save analytic joint covariance and4096 synthetic signed carriers. Report exact-in-model Gaussian statistics separately from physical significance; the former do not qualify the latter. A single bare0200 temperature product is a content diagnostic with unresolved unit, not a covariance bank.
5. Reuse R36 on the actual retained ell<=6 fit with explicitly restored monopole/dipole. Report pi_lin, exact retained-band pi and rho, the dipole×octupole and total nonlinear differences, and actual finite-operator remainder norms. If restoration remains conditional, retain a finite set/range of declared restorations rather than claim an observed absolute stress.
6. Return x/mathcal Q/Pi from the same carrier. Only report F with its actual admissible body, numerator/denominator, measure and target; distinguish exact normalized stress from proxy occupancy. Record G_F NOT_APPLICABLE. Do not replace F by support or create a fictitious depth from ell/release.

**Specific new empirical question:** after identical actual Commander processing, how stable is the signed radiation quadrupole proxy orthogonal to a declared residual-DQ direction across PR3/PR4 and NSIDE choices, which signed components does scalar C2/axis-only morphology conceal, and what fraction of that proxy can be certified against the actually computed T^4 retained-band correction and a stated missing-band bound? The declared ideal Gaussian model supplies the executed conditional reference for this result; release-matched upstream DQ/beam/exchangeability remains a separate qualification.

Useful findings include a nonzero stable transverse stress proxy, a signed release difference hidden by nearly equal C2, dominant DQ-parallel sensitivity, or a failure of rank-one stability under a genuinely supplied wider residual family. None alone measures spacetime shear, identifies a deterministic cosmological anisotropy, or establishes an unconditional anomaly p-value. These are scoped consequences of the actual experiment, not generic prohibitions.

## 9. Completion and handoff

Constructive derivations are complete for the stated finite linear model, Gaussian finite-N experiments and blackbody retained-band stress. Algebraic formulas are DERIVED; their foundations in radiation kinetic theory and Doppler response are LITERATURE-SUPPORTED by the already read R2/R3 packet. Actual Commander response matrices, MC rows/statistics, restored absolute stress and numerical remainder values are NOT_RUN by this child and belong to root execution. Exact upstream DQ response rank, source-matched exchangeability and all-sky high-ell completion are UNRESOLVED. No claims of physical F certification or significance should exceed those inputs.

No oracle file was added because root reports its focused implementation checks already cover the boost/Landau, dipole-octupole, profile/quotient and finite-N identities. This child does not independently certify those root execution reports. Stop boundary: this construction and handoff only; no final review or recursive audit.


## Execution-status addendum

Root executed the observed PR3/PR4 native-mask estimator and exact retained-band radiation moments, the explicit ideal Gaussian covariance, conventional power tensor and paired GLS. See REPORT_KO.md and RESULTS/OBSERVABLES.json for measured values. The final code has24 passing focused tests. The child-stage NOT_RUN statement above records authorship of that construction, not the final root execution status. Actual source-qualified Commander temperature MC count remains0. UNIT_FREE_DIRECTION.md derives a validated angular alternative but it is not applied to an insufficient or unqualified actual bank.
