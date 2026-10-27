# Independent review of the cosmological radiation-stress constraint

26 October 2026. Internal, bounded scientific review of COSMOLOGICAL_CONSTRAINT.md and stress_constraint_toy.py, with the CONVENTIONS and FOUR_AXES notes read for the changed interface. The earlier five-loop and v15-extension reviews are not repeated. The reviewer changed only REVIEW.md and REVIEW.json, ran no transport or ODE solver, and performed no publication or push.

**Disposition: PASS_SCOPED_AFTER_TARGETED_REPAIRS. Both findings are closed; no open mathematical blocker remains.** No change to the core proposition, finite-error certificate or toy calculation was required. Final candidate hashes and finding status are recorded in REVIEW.json.

## Findings and minimum repairs

| ID | Severity | Finding | Minimum repair | Status |
|---|---|---|---|---|
| COS-01 | Low | The positive vector sign in equation (8) did not by itself specify which frame's velocity beta denotes. The inverse points along the radiation energy-frame velocity measured by the chosen observer; the reverse observer velocity has the opposite sign. | The author added that exact convention immediately before (8). The speed-only toy needs no numerical change. | Closed; revised sentence inspected |
| COS-02 | Low | boost_null_wolfram.json recorded two zero outputs without the submitted expressions. The output alone did not bind the named identities to a reproducible symbolic check. | The author preserved the exact submitted input as cas/boost_null.wl alongside the original receipt. No rerun was necessary. | Closed; expression and 0<beta<1 assumptions inspected |

## Exact stress criterion

In the observer orthonormal tetrad, the symmetric tracefree tensor is completely specified by positive energy density rho, flux f and STF stress P. The dimensional binding is correct: physical energy flux is c times the raw rank-one moment, so f=q/(c rho); P=pi/rho is dimensionless. The nine-dimensional tensor count and the four-dimensional perfect-radiation submanifold give five constraints. This is a model dimension count, not removal of five gauge variables or a chi-square calibration.

For a perfect radiation tensor with rest density rho_L and dimensionless rest-frame velocity beta relative to the chosen observer,

\[
\rho=\rho_L\frac{3+\beta^2}{3(1-\beta^2)},\quad
f=\frac{4\beta}{3+\beta^2},\quad
P=\frac4{3+\beta^2}\operatorname{STF}(\beta\beta^T).
\]

Solving the radial quadratic gives the unique subluminal branch

\[
\beta=\frac{3f}{2+\sqrt{4-3f^2}}=\kappa(f^2)f.
\]

Its substitution yields P=kappa STF(ff). Conversely, for rho>0 and |f|<1 this beta is subluminal and rho_L=3rho(1-beta squared)/(3+beta squared)>0; the reconstructed tensor agrees in all components. Equivalently rho_L=rho(1-f dot beta). Therefore the iff statement in (7), including attainment by an actual timelike perfect-radiation tensor, is valid. The pure beam boundary |f|=1 is correctly excluded.

The condition D=0 is invariant under a Lorentz change of observer because it identifies a tensorial perfect-radiation orbit. A nonzero Frobenius norm of D is generally observer-dependent, although it is unchanged by spatial triad rotations. On the specified unique timelike eigenbranch, the eigenvalues of the mixed tensor transform by similarity. Thus the rest-pressure expression for A_gamma is a Lorentz scalar, provided rho_L>0. No branch claim is made at a pure null beam or another excluded degeneracy.

This null concerns the stress tensor, not microscopic isotropy. An explicit positive counterexample to that stronger interpretation is I(e)=I0[1+epsilon P4(e_z)], |epsilon|<1: it has nonzero angular structure but f=P=D=0. The candidate expressly retains this limitation. The radiation energy frame is also distinct from the matter congruence and from any global cosmological rest frame.

## Nonlinear harmonic interface

The observer and direction conventions are consistent: U squared equals -c squared, the unit tetrad time direction is U/c, propagation e=-n reverses odd raw moments, and radiance is divided by c before use as energy density. The massless velocity hierarchy collapses its radial index at fixed angular rank; this does not collapse independently defined spectral kernels.

The v15 energy-calibrated temperature preserves the actual directional bolometric energy, including for a nonthermal spectrum. Its T to the fourth-power conversion therefore preserves T_ab. A finite-band fitted temperature requires the stated spectral completion and calibration premises. Assigning a thermal lift to already known directional energy adds no new stress information.

The rank-one through rank-three expansion (11) has the correct quadratic coefficients: 4/5 for dipole self-coupling, 24/35 for dipole-octupole, 16/35 for quadrupole self-coupling and 8/35 for octupole self-coupling. With outward sky directions f=-4d/3+O(epsilon squared), the leading G contribution is (4/3)STF(dd). Subtraction gives precisely the coefficients and sign in (12), including the bracket term -STF(dd). The actual energy normalization affects the stress first at cubic order when the temperature monopole is zero. Higher temperature ranks require their additional products, as the candidate states.

Relative multipole orientations consequently enter this physical stress constraint. Separate angular powers lose those contractions. This does not by itself establish the practical importance of the nonlinear terms; actual calibration and foreground errors remain the comparison scale.

## Finite-error and statistical claims

Direct differentiation confirms

\[
DG_f[h]=\kappa\operatorname{STF}(hf^T+fh^T)
+2\kappa'(f^2)(f\cdot h)\operatorname{STF}(ff^T),\qquad
\kappa'(s)=\frac9{2\sqrt{4-3s}(2+\sqrt{4-3s})^2}.
\]

Both kappa and its derivative are nonnegative and increasing on 0<=s<1. The STF projection is a Frobenius contraction, the Euclidean ball is convex, and ||STF(ff)||=sqrt(2/3)|f| squared. These give the candidate's Lipschitz constant

\[
L_G(r)=2\kappa(r^2)r+2\sqrt{2/3}\kappa'(r^2)r^3.
\]

It is valid and conservative. In fact, resolving h parallel and orthogonal to f gives the exact local Jacobian operator norm 2 sqrt(2/3)|f|[kappa+|f| squared kappa prime], which is no larger than the displayed bound. No sharper constant is needed for the stated certificate.

On the joint event (13), the triangle inequality proves ||Dhat-D||<=e_P+L_G(r)e_f. Consequently ||Dhat|| greater than that radius excludes D=0. Uniform joint coverage at least 1-alpha gives type-I error at most alpha. The result does not supply the coverage premise: marginal errors, arbitrary entropy budgets or five residual coordinates alone do not establish it. The candidate correctly keeps correlations, positive-moment constraints and Gaussian/rank/linearization assumptions explicit. The two negative cross-covariance terms in (16) have the correct signs and dimensions.

The norm certificate is an observer-qualified sufficient exclusion rule. Its numerical threshold is not promoted to a Lorentz scalar. A joint confidence set pushed through the exact rest-frame eigenvalue map instead gives a confidence interval for the invariant A_gamma on its declared branch.

## Executed evidence

The reviewer executed the numerical portion of stress_constraint_toy.py in memory, stopping before figure and receipt writes. The saved author receipt was then compared with the recomputed values. All checks passed:

| Check | Recomputed result |
|---|---:|
| Maximum boosted perfect-radiation D norm | 1.6515307107109721e-16 |
| Maximum Landau invariant error | 4.557985933129061e-16 |
| Maximum rotation covariance error | 6.080894393112985e-16 |
| Largest Lipschitz ratio, 200 sampled pairs | 0.6804713302395458 |
| Cubic error ratios under two halvings | 7.962562059651964; 7.986701517224148 |

Independent closed-form inverse-velocity and rest-density checks also passed at speeds 0, 0.8 and 0.99. The analytic Jacobian bound was compared with its exact parallel/orthogonal decomposition at radii 0, 0.2, 0.8 and 0.999999. These are auxiliary finite checks; the proofs above justify the general statements.

The retained Wolfram input reduces the vector identities to their common radial coefficient and requests both inverse-velocity and stress residuals under 0<beta<1; the accompanying output is {0,0}. The beta=0 case follows directly from the stated continuous limit. This reviewer inspected that input and its receipt but did not rerun the remote Wolfram evaluator.

For the declared toy a=2e-5 and speed 0.00123, the reviewer obtains A_gamma=3.2659863237141705e-6, ||D||=3.2659764415019133e-6, error radius 5.247500597440408e-7 and positive lower bound 2.7412263817578726e-6. The input error radii are stipulated, not learned from real data. No empirical coverage simulation or observed CMB detection has been performed. The finite angular quadrature verifies this polynomial conversion; it is not a cosmological transport integration.

## Scope and scientific decision

The candidate consistently separates spatial rotations, changes of physical observer, coordinate/perturbative gauge, and statistical nuisance treatment. It preserves the distinct X/x and F namespaces and does not turn an entropy defect or an HTT support ratio into an observation probability. A point null with zero support is correctly barred from serving as a positive support denominator.

No false matter-shear conclusion was found. Radiation anisotropic stress, matter shear and curvature remain different physical objects. A matter-shear inference still needs the declared transport residual R, its derivatives and joint uncertainty. The proposition only establishes a local radiation-stress constraint.

The perfect-fluid boost algebra, STF/Gaunt couplings and confidence-set propagation are established ingredients. The candidate makes only a bounded application claim about combining them into a calibrated cosmological constraint. Its proposed common-input comparison and real-data application remain future work. This review does not certify broad novelty, empirical power or production readiness.

Both targeted repairs are confirmed. There are no remaining findings in this bounded review. The accepted result is DERIVED and NUMERICALLY CHECKED within the candidate's domains; observational coverage, measured constraints and matter-shear inference are not thereby established.
