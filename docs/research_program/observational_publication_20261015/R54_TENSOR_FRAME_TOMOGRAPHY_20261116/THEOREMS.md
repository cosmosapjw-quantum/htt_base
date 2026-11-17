# R54 theorems: statements that need no data (2026-11-16)

Node R54-THM. This file collects the parts of the R54 claims that can be settled by statistics or by
mathematical physics alone. Nothing here uses an observation; no result number of `RESULTS/*.json` appears.
Each statement has a proof, an attribution, and an executable check in `tests/r54/test_r54_theorems.py`
(tools in `htt/htt/htt/infer/r54_identifiability.py`). Evidence ids (E..) refer to `state/EVIDENCE_LEDGER.md`.

Independent review: four recorded reviews read this file (`INDEPENDENT_REVIEW.json`): R54-A1, scientific-diff-reviewer of the local session, 2026-11-17, on the text before its fixes (R54-A1-01 to R54-A1-12); the R58 proof review, 2026-11-17, on the text of commit 77f61c17 (PRV-01 to PRV-05); the R58 closeout review, 2026-11-17, on the corrected text of commit f50d978a; and the referee-repair review of 2026-11-17, recorded last, which covers the current text. Coverage is bound to the file content: any later edit leaves this file uncovered until a new review is recorded.

## 0. Overview

| id | statement in one line | kind | attribution | check |
|---|---|---|---|---|
| T1 | no function, compression or re-coordinatization of the carrier exceeds the power envelope of the exact likelihood | statistics | textbook (sufficiency, E65) | `test_t1_*` |
| T2 | the confidence cylinder of a singular precision has exact coverage with rank(F) degrees of freedom; all views read from it are simultaneously valid | statistics | Scheffe's method (E64), routine extension | `test_t2_*` |
| T3 | along an unidentified direction every valid confidence set is unbounded, every bounded set has zero uniform coverage, and a posterior equals the conditional prior | statistics | E53, E54, E55, E69 | `test_t3_*` |
| T4 | Q and F are polar duals, including the singular case | convex analysis | E67 | `test_eq20_*` of `test_r54_modules.py` |
| T5 | exact second moments of GLS with a simulated covariance | statistics | classical Wishart theory (E59, E66) | `test_t5_*` |
| T6 | selection rule: the first-order response is block diagonal in (multipole, parity); identifiability is a rank statement per block | mathematical physics | Schur's lemma; ingredients in E18, E25, E50, E51 | `test_t6_*` |
| T7 | gauge orbits: distance zero points against Hubble multipoles, frame spin against vorticity; design-only separability of depth laws | mathematical physics | E09, E52; GLS | `test_t7*` |
| T8 | the T and E quadrupole kernels form a Chebyshev system: a shear history hidden from T changes sign at least once, hidden from T and E at least twice | mathematical physics | kernels E46; sign-change argument E68 | `test_t8_*` |
| T9 | frame algebra: count-dipole excess plus bulk flow of the same shell vanishes identically; the depth-constant velocity submodel is a linear hypothesis across shells | kinematics | first-order velocity composition; context E60, E61 | `test_t9_*` |
| L1 | errors-in-variables bias of the linear-in-distance estimator in closed form | statistics | elementary; context E41 | `test_l1_*` |
| L2 | anisotropic stress of a massive collisionless species at first order (R54-EQ-06) | kinetic theory | elementary; massless case E05 | `test_eq06_*` of `test_r54_modules.py` |

Notation. The linear Gaussian carrier is y ~ N(J theta, C) with C known and non-singular; F = J^T C^-1 J and
t = J^T C^-1 y (precision form). F^+ is the Moore-Penrose inverse, P = F^+ F the projector on row(F) and
r = rank F. N = ln a. n is the unit vector from the observer to a source.

## 1. Statistics

### T1. Sufficiency tie

**Statement.** Let T be a sufficient statistic for {P_theta}. For every test phi(y) with values in [0, 1] there
is a test psi(T) with the same power function, E_theta psi(T) = E_theta phi(Y) for all theta. In the carrier
model, t is sufficient, so (a) no procedure built on a function of the data, in particular on any of the five
views or on any re-coordinatization of the parameters, has a power function outside the set attainable from
(F, t); (b) for a linear compression z = A y with A of full row rank, F_A = J^T A^T (A C A^T)^-1 A J satisfies
F_A <= F in the Loewner order, with equality iff range(C^-1 J) is contained in range(A^T); (c) an invertible
change of parameters theta' = B theta leaves every noncentrality theta^T F theta unchanged.

**Proof.** psi(T) = E[phi(Y) | T] does not depend on theta because T is sufficient; the tower property gives
the equality of the power functions. Sufficiency of t follows from the factorization of the density, which is
exp(theta^T t - theta^T F theta / 2) times a function of y. For (b), C^(1/2) [C^-1 - A^T (A C A^T)^-1 A] C^(1/2)
= I - Pi, where Pi is the orthogonal projector on range(C^(1/2) A^T); I - Pi is positive semi-definite, and
J^T C^(-1/2) (I - Pi) C^(-1/2) J vanishes iff C^(-1/2) J lies in range(C^(1/2) A^T). (c) is a substitution. QED

**Consequence.** The tie between the tensor carrier and the exact likelihood measured in R53 is a theorem, not
an empirical finding. A gain in power can only come from different assumptions, never from the views.
Not covered: a misspecified C, a non-Gaussian law, or a nuisance model that differs between two analyses.

### T2. Exact simultaneous coverage with a singular precision

**Statement.** Let m = F^+ t and Theta_c = {theta : (theta - m)^T F (theta - m) <= c^2}. Then
(theta - m)^T F (theta - m) is chi-square with r degrees of freedom for every theta, so
P_theta(theta in Theta_c) = P(chi2_r <= c^2) exactly, whatever the unidentified component of theta. Moreover
{theta in Theta_c} = {for all v in row(F): |v.(theta - m)| <= c sqrt(v^T F^+ v)}, and for v outside row(F) the
set {v.theta : theta in Theta_c} is the whole line. Hence the support intervals are simultaneously exact
(they cannot all be shortened), and for every function phi of the parameters, in particular the gauge of any
declared body, P(phi(theta) in phi(Theta_c)) >= P(chi2_r <= c^2) jointly for all phi.

**Proof.** t = F theta + xi with xi ~ N(0, F), so m - P theta = F^+ xi and, because F P = F,
(theta - m)^T F (theta - m) = xi^T F^+ F F^+ xi = xi^T F^+ xi, a chi-square variable with r degrees of freedom.
For v in row(F) write v = F u; Cauchy-Schwarz in the semi-inner product of F gives
(v.(theta - m))^2 <= (u^T F u) ((theta - m)^T F (theta - m)) and u^T F u = v^T F^+ v, with equality at
u = theta - m. If v is not in row(F) there is k in ker F with v.k != 0, and Theta_c is invariant under
theta -> theta + s k. The last claim holds because the event {theta in Theta_c} implies all the others. QED

**Consequence.** Reading several views, bodies and directions from one Theta_c costs no additional
look-elsewhere factor, provided c^2 is the chi-square quantile with r degrees of freedom (this is what the R54
scripts use). The degrees of freedom are rank(F), not the number of parameters.

### T3. Unidentified directions

**Statement.** Let v be outside row(F). (i) Let C be a measurable set-valued map (every {a in C(y)} is an event).
For any confidence procedure C(y) for v.theta with coverage at least 1 - alpha for all theta there is, under every theta,
an event of probability at least 1 - alpha on which C(Y) is unbounded. (ii) If C(y) is
bounded for every y, then inf over theta of P_theta(v.theta in C(Y)) = 0. (iii) Split theta into its component
iota in row(F) and nu in ker F. For every prior, the posterior of nu given iota equals the prior of nu given
iota. (iv) Any bounded posterior credible interval for v.theta has zero uniform frequentist coverage
over the unrestricted null orbit. Its marginal width may shrink as data update iota when the prior couples
iota and nu; the conditional law pi(nu | iota, y) = pi(nu | iota) remains unchanged. For a proper posterior,
finite equal-tailed intervals at levels strictly between zero and one are bounded.

**Proof.** Choose k in ker F with v.k != 0. The law of Y is the same under theta and theta + s k.
(i) For s_j -> infinity let A_j = {v.theta + s_j v.k in C(Y)}. Validity at theta + s_j k gives
P_theta(A_j) >= 1 - alpha, and the reverse Fatou lemma gives P_theta(limsup A_j) >= 1 - alpha; on that event
C(Y) contains an unbounded sequence. (ii) For fixed y the indicator of {v.theta + s v.k in C(y)} tends to zero
as s grows; dominated convergence gives coverage tending to zero along theta + s k. (iii) The likelihood
depends on iota only, so pi(iota, nu | y) is proportional to L(iota; y) pi(iota) pi(nu | iota). (iv) follows
from (ii); the conditional-law statement is (iii). For example, a bivariate unit Gaussian prior
with correlation r and a likelihood of precision diag(n, 0) gives Var(nu | y) = 1 - n r^2/(1+n),
which decreases with n for r != 0 although Var(nu | iota, y) = 1-r^2 is unchanged. QED

**Attribution.** (i) and (ii) are the linear-Gaussian case of the impossibility theorems of E53 (see also E54);
(iii) is the standard observation recorded in E55 and E69. Nothing here is new.
**Consequence.** For the unidentified kinematic directions of T6 and T7 a finite interval is always a statement
dependent on a prior or a declared body; data can affect its marginal width through prior correlations.
The likelihood itself remains flat on the null orbit. The Q view makes a declared body explicit.
Part (i) has no executable check; the tests cover (ii) in a Gaussian instance and (iii).

### T4. Polar duality of Q and F

**Statement.** Let K0 be a convex body with the origin in its interior, p its gauge, K0* its polar and
h_Theta the support function of a closed convex set Theta. Then
sup over Theta of p = sup over v in K0* of h_Theta(v), and
inf over Theta of p = max(0, sup over v in K0* of [-h_Theta(-v)]). If Theta is the cylinder Theta_c of a
singular F the supremum is infinite and the infimum is finite.

**Proof.** p is the support function of K0* (bipolar theorem), so the first identity is an exchange of two
suprema. For the second, p(theta) = sup over v in K0* of v.theta is bilinear on the product of the compact
convex set K0* and the convex set Theta; Sion's minimax theorem exchanges inf and sup, and
inf over Theta of v.theta = -h_Theta(-v). If F is singular, h_Theta(v) is infinite for v outside row(F), and
K0* has non-empty interior. QED (E67; checked numerically by the gauge-range tests of `test_r54_modules.py`.)

### T5. Exact second moments with a simulated covariance

**Statement.** Let S be independent of y with n S ~ W_p(n, Sigma), y ~ N(J theta, Sigma), J of rank k,
Sigma positive definite, integer n >= p, q = p - k and n > q + 1. The condition n >= p
ensures S is invertible almost surely; n > q + 1 supplies the inverse moment. For theta_hat = (J^T S^-1 J)^-1 J^T S^-1 y, V_hat = (J^T S^-1 J)^-1 and
V = (J^T Sigma^-1 J)^-1:
E theta_hat = theta, Cov(theta_hat) = [(n - 1)/(n - q - 1)] V, E V_hat = [(n - q)/n] V, so that
Cov(theta_hat) = {n (n - 1) / [(n - q)(n - q - 1)]} E V_hat. For p = k the estimate does not depend on S,
Cov(theta_hat) = V, V_hat is unbiased and the Wald statistic is Hotelling's T^2(p, n).

**Proof.** Whiten with Sigma^(-1/2) and rotate with the orthogonal factor of a QR decomposition, so that
Sigma = I and J = [R; 0] with R invertible; n S stays W_p(n, I). The block inverse gives
theta_hat = R^-1 (y_1 - B y_2) with B = S_12 S_22^-1, and V_hat = R^-1 S_11.2 R^-T with
S_11.2 = S_11 - S_12 S_22^-1 S_21. Hence theta_hat - theta = R^-1 (e_1 - B e_2) with e ~ N(0, I) independent of
S, which is unbiased with conditional covariance R^-1 (I + B B^T) R^-T. Three Wishart facts (E66): n S_11.2 is
W_k(n - q, I) and independent of (S_12, S_22); given S_22 the rows of B are independent N(0, (n S_22)^-1); and
E (n S_22)^-1 = I/(n - q - 1). Therefore E[B B^T] = [q/(n - q - 1)] I and E S_11.2 = [(n - q)/n] I. QED

**Scope.** Second moments only. For q > 0 the law of theta_hat is not Gaussian (E29, E30); leave-one-out
calibration (node R54-L01) remains the test of the intervals. The least-squares setting with an estimated
dispersion matrix goes back to E59; the ratio is not claimed as new.

## 2. Mathematical physics

### T6. Selection rule and block identifiability

**Setting.** G = O(3) acts on the kinematic variables and on the ideal (full-sky, noise-free) observables. Its
real irreducible representations are labelled (l, pi): symmetric trace-free tensors of rank l on which the
inversion acts as pi. First-order variables: expansion (0,+), polar vectors such as an acceleration-type
Hubble dipole or an observer velocity (1,-), vorticity (1,+), shear (2,+). Fields on the sky: scalars
(redshift, distance modulus, counts, temperature) contain (l, (-1)^l) once for each l; pseudo-scalars contain
(l, (-1)^(l+1)); tangent vector fields (proper motions) contain a spheroidal copy (l, (-1)^l) and a toroidal
copy (l, (-1)^(l+1)) for l >= 1; spin-2 fields contain E_l of type (l, (-1)^l) and B_l of type (l, (-1)^(l+1))
for l >= 2.

**Statement.** Write the kinematic space as the direct sum over (l, pi) of R^m(l,pi) (x) V(l,pi) and the
observable space as the direct sum of R^p(l,pi) (x) V(l,pi). Every G-equivariant linear map R between them is
the direct sum of M(l,pi) (x) identity with real p x m multiplicity matrices M(l,pi). Consequently
ker R = direct sum of ker M(l,pi) (x) V(l,pi); the first-order model is identified iff every M(l,pi) has full
column rank; the unidentified dimension is the sum of (2l + 1) nullity(M(l,pi)); and p(l,pi) >= m(l,pi) is
necessary.

**Proof.** The spaces V(l,pi) have odd dimension, so they are of real type: an equivariant map between two of
them is zero if they differ and a real multiple of the identity if they coincide (Schur's lemma). Apply this
to every pair of summands. QED

**Corollaries.**
- C6.1 (scalar observables). Vorticity has no column in any scalar observable at any multipole. Polar vectors
  enter the dipole only, shear the quadrupole only. The leading-order scalar law therefore carries
  1 + 3 + 5 = 9 numbers, which is the count of E18.
- C6.2 (proper motions). A polar vector sources the spheroidal dipole only, vorticity the toroidal dipole
  only, shear the spheroidal quadrupole only. The dipole of the observer velocity and the quadrupole of the
  shear are the published patterns (E25); astrometry uses the aberration-drift and parallax dipoles and the
  curl-free quadrupole of anisotropic expansion (E50, E51). The toroidal dipole of a rigid rotation is elementary;
  E51 (section 2.3, read in full by addendum task R54-A2) states that a rotation of the universe would manifest
  as a B-mode dipole of the proper-motion field.
- C6.3 (null channels). B_2 and the toroidal proper-motion quadrupole are of type (2,-), for which the list of
  first-order variables has no member. Their first-order response is zero: a signal there contradicts either
  the model class or the equivariance of the measurement chain. This is the formal basis of the B-null gate.
- C6.4 (what can see vorticity). Only observables of type (1,+): the toroidal proper-motion dipole and
  pseudo-scalar dipoles such as a polarization-angle rotation pattern.
- C6.5 (mask independence). If the image of R consists of band-limited fields, restriction to any sky region
  with non-empty interior is injective on it (band-limited fields are real-analytic), so a mask changes the
  conditioning of F but not ker R.
- C6.6 (scope). Equivariance requires that the variables enter as tensors at the observer or as homogeneous
  histories, and that the source population and the measurement are isotropic and parity-symmetric. It fails
  for finite-wavelength modes (a wave vector supplies an extra polar vector, so that the vector modes of the
  Bianchi families with structure, sigma_V in E01, do reach the temperature), for a parity-violating measurement
  chain, and at second order (products such as acceleration times vorticity).

**Check that does not use the proof.** `equivariant_response_rank` counts the equivariant responses by
solving the equivariance equations on a polynomial ansatz. With reflections it returns the table above; with
rotations only, every scalar field couples to every variable and every vector field gains a second pattern,
which isolates parity as the operative assumption.

**Attribution.** Schur's lemma is classical and every pattern in C6.1 and C6.2 is in the literature. The block
statement, the null channels and the rank criterion as one identifiability theorem were not found in the
searches of 2026-11-16; this is an absence of a search hit, not a claim of priority.

### T7. Gauge orbits and separability

**T7a (distance zero points).** For K distance-indicator samples let the mean of the log-distance residual of
object i in sample p be h_p + (delta + d_p).n_i + g_i V.n_i, where delta is a depth-independent fractional
Hubble dipole, d_p a zero-point dipole of sample p and V a velocity with response g. Then
(i) the mean is invariant under (delta, d_p) -> (delta + eps, d_p - eps), a three-dimensional gauge orbit;
(ii) if the vectors (1, n_i) of every sample span R^4 (the directions of a sample do not all lie on one plane
section of the sphere), the null space of the design for (h_p, delta, d_1..d_K) is exactly this orbit, so the
identified functions are h_p and delta + d_p (equivalently the differences d_p - d_q and one sum); if h_p is known
and removed, directions spanning R^3 suffice; (iii) V is identified next to them if some sample contains two
groups with different g whose vectors (1, n_i) each span R^4, and is not identified if g is constant within
every sample; (iv) the hypothesis delta = 0 cannot be tested: every
level-alpha test has power at most alpha against every alternative; (v) the hypothesis d_p = d_q for all p, q
is testable, and its acceptance does not separate delta from a common zero-point dipole. The same holds
multipole by multipole for any depth-independent fractional Hubble anisotropy against a zero-point pattern.

**Proof.** (i) is immediate. (ii) A null vector satisfies c_p + (a + b_p).n_i = 0 on sample p; since the
(1, n_i) span R^4, c_p = 0 and a + b_p = 0. Without that condition the ring n_z = 1/2 gives the extra null
vector c_p = -u/2, a + b_p = u e_z (independent review, finding R54-A1-01).
(iii) A null vector with V-component b satisfies c_p + (a_p + g_i b).n_i = 0; two values of g on sets whose
(1, n_i) span R^4 give c_p = 0 and b = 0; for constant g the choice a_p = -g b is a null vector. (iv) For every parameter point there is a point
with delta = 0 and the same mean, so a test of level alpha on {delta = 0} rejects with probability at most
alpha everywhere. (v) The hypothesis restricts the identified functions delta + d_p to be equal. QED

**T7b (frame spin).** Proper motions are measured relative to a triad that rotates with angular velocity
Omega relative to a local inertial triad. By C6.2 the toroidal dipole measures the multiplicity matrix
(1, -1) applied to (vorticity, Omega): only their difference is identified. If the frame is defined
kinematically by removing the net rotation of the same sources, the difference is zero by construction and
the data carry no information on vorticity; identification needs a dynamical frame tie, which adds the row
(0, 1). The freedom is the spin degree of freedom of a global astrometric solution (E52).

**T7c (depth laws).** For dipole vectors y_w = A + g_w V + noise in K depth windows with covariance c (x) I_3,
the noncentrality of the test of V = 0 with A free is |V|^2 [g^T c^-1 g - (g^T c^-1 1)^2 / (1^T c^-1 1)]
= |V|^2 (g^T c^-1 g) sin^2(phi), where phi is the angle between g and the constant vector in the c^-1 metric.
The two laws are separable iff g is not constant, and the attainable power is fixed by the design before any
data are read. (Standard GLS; `depth_law_noncentrality` also covers a general cross-depth covariance.)

**Consequence.** T7a is the precise form of "a constant dipole equals a zero-point dipole" (E09): with several
indicators one can reject equality of their zero-point dipoles, and one can never establish a physical
depth-independent dipole from relative distances alone. Any finite bound on it is a calibration budget, that
is, a declared body in the sense of T3 and T4.

### T8. The two-kernel moment problem of the shear history

**Setting.** For one projection f(N) = e.s(N) of a type-I shear history, the temperature and E quadrupoles
measure Sigma_T(f) = int K_T f dN and Sigma_E(f) = int K_E f dN with K_T = k_T(tau(N)), K_E = k_E(tau(N)),
k_T = (6 e^-tau + e^(-3 tau/10))/7 and k_E = (sqrt6/7)(e^(-3 tau/10) - e^-tau) (R54-EQ-03, a re-derivation of
E46). Let I be an interval on which the scattering rate is positive almost everywhere, so that tau is
strictly monotone, and let rho = k_E/k_T. For the norm statements, take I to have finite,
nonzero length and finite nonnegative optical depth; more generally, (iv) needs only that the two kernels
lie in L^2(I) with a positive-definite Gram matrix. Norm conclusions concern the unrestricted
linear-history function space; a perturbative physical application also declares its amplitude regime.

**Statement.**
(i) k_T is strictly decreasing and convex with k_T(0) = 1 and k_T >= 1 - (9/10) tau; 0 <= k_E <= (sqrt6/10) tau;
rho = sqrt6 (x - 1)/(x + 6) with x = e^(7 tau/10) is strictly increasing from 0 towards sqrt6.
(ii) {K_T, K_E} is a Chebyshev system on I: a non-trivial combination a K_T + b K_E has at most one zero.
(iii) For f in L^1(I): (a) if f >= 0, then rho_min Sigma_T <= Sigma_E <= rho_max Sigma_T and
||f||_1 <= Sigma_T / k_T(tau_max), with rho and tau taken over I; (b) if f has exactly one sign change, at N_c,
then |Sigma_E - rho_c Sigma_T| = int |rho - rho_c| K_T |f| dN, which is positive unless f = 0; (c) hence a
non-zero f with Sigma_T = 0 changes sign at least once, and a non-zero f with Sigma_T = Sigma_E = 0 changes sign
at least twice; (d) histories with exactly two sign changes and Sigma_T = Sigma_E = 0 exist, so for any
prescribed pair of functionals there are histories of arbitrarily large norm.
(iv) The least L^2(I) norm compatible with (Sigma_T, Sigma_E) is sqrt(Sigma^T G^-1 Sigma), G the Gram matrix of
the kernels; there is no largest.
(v) A parametric family f = sum of theta_j f_j is identified iff the 2 x m matrix of the int K_i f_j has rank m,
so m <= 2 with T and E and m <= 1 with T alone.

**Proof.** (i) Differentiate; the tangent-line bound on k_T uses convexity, the bound on k_E uses concavity
for tau < (10/7) ln(100/9) and k_E <= max k_E beyond. d rho / dx = 7 sqrt6/(x + 6)^2 > 0. (ii) a K_T + b K_E =
K_T (a + b rho), K_T > 0 and rho is strictly monotone on I. (iii-a) Sigma_E = int rho K_T f and
Sigma_T >= k_T(tau_max) ||f||_1. (iii-b) Sigma_E - rho_c Sigma_T = int (rho - rho_c) K_T f; rho - rho_c and f both
change sign only at N_c, so the integrand has constant sign. (iii-c) follows from (a) and (b). (iii-d) Take
three positive bumps with disjoint supports; their 2 x 3 moment matrix has a non-trivial null vector, the
corresponding combination has at most two sign changes and, by (c), at least two; adding multiples of it to
any history leaves the functionals unchanged. (iv) is the projection theorem. (v) is linear algebra. QED

**Consequences.** (1) Without a shape restriction the two quadrupoles bound no norm of the shear history from
above. An upper amplitude bound requires a declared restriction controlling the moment kernel, such as
a finite-dimensional identified family, a sign restriction, or a physical norm/stress budget. The restriction
and its physical domain must be stated; arbitrary amplitudes may leave the linear transfer approximation. (2) Under a sign restriction T alone bounds the L^1 norm. (3) A
measured ratio Sigma_E/Sigma_T outside [rho_min, rho_max], in particular a negative one, certifies a sign change
of the history. (4) For late-time support tau_max is small: |Sigma_E| <= (sqrt6/10) tau_max ||f||_1 and the
weight in (iii-b) is at most rho(tau_max), so the sensitivity to a sign-changing late-time history is
suppressed by a factor of order tau_max relative to the sensitivity of T to a sign-definite one. This is the
blind spot quantified numerically in `RESULTS/R54_L1_TYPE1_TE.json:data.late_time_shear_bounds`.

**Attribution.** The kernels are those of the classical transfer problem (E46). The sign-change statement is
the standard property of Chebyshev systems (E68, quoted from a standard text that was not re-read in the
attribution check) applied to this pair; it was not found in the searches of
2026-11-16 for this problem. E44 writes the temperature quadrupole as a line-of-sight integral of the shear
and weights the polarization by the visibility; a history with vanishing temperature integral is the case
that T8 counts.

### T9. Frame algebra and closure

**Statement.** Let v_O, v_R and v_j be the first-order velocities of the observer, of the radiation frame and
of the matter of depth shell j. The CMB dipole is D_R = (v_O - v_R)/c. A flux-limited population a in shell j
with Ellis-Baldwin coefficient k_a and no intrinsic dipole has D_a = k_a (v_O - v_j)/c. The bulk flow of
shell j measured with redshifts in the radiation frame is V_j = v_j - v_R. Then
D_a/k_a - D_R + V_j/c = 0 identically. The depth-constant velocity submodel CONST_V is the linear hypothesis V_j = V for all j; with n_c
count populations and n_d distance shells it leaves 3 (n_c + n_d - 1) residual degrees of freedom.

**Proof.** Substitute. The design of the tilt hypothesis has 3 columns and 3 (n_c + n_d) rows of rank 3. QED

**Consequence.** For counts and distances of the same shell the closure relation R54-EQ-38 is an identity and
tests only the measurement chain. Across different shells it tests CONST_V, not every homogeneous tilted
cosmology: a time-dependent homogeneous tilt instead requires a source-bound transfer V_j = T(z_j) beta_0,
including the actual shell windows. A local bulk-flow null may predict a depth-dependent distribution, not
a deterministic decay in every realization. Relative velocities between the matter and radiation
frames from super-horizon isocurvature modes, and dipoles in tilted anisotropic models, are treated in E60
and E61; redshift tomography of the kinematic and intrinsic dipoles in E62.

### L1. Errors-in-variables bias of the linear-in-distance estimator

**Statement.** Let d_i = D_i exp(s_i eps_i) with independent standard normal eps_i and c z_i = H D_i. The
weighted regression of c z on d with weights 1/(s_i d_i)^2 (the distance-noise-dominated limit of
R54-EQ-35) gives H_hat = H [sum of s_i^-2 exp(-s_i eps_i)] / [sum of s_i^-2], and
E H_hat / H = [sum of s_i^-2 exp(s_i^2 / 2)] / [sum of s_i^-2] >= 1. For a common s the factor is exp(s^2/2).
Two sky regions with errors s_1 and s_2 differ by (s_1^2 - s_2^2)/2 in the logarithm of the fitted rate. The
log-distance estimator (R54-EQ-34) is linear in the Gaussian distance moduli and is unbiased for any weights
that do not depend on the noise.

**Proof.** w_i d_i c z_i = H s_i^-2 exp(-s_i eps_i) and w_i d_i^2 = s_i^-2; E exp(-s eps) = exp(s^2/2). QED

**Consequence.** A linear-in-distance estimator converts the sky map of the distance-error variance into
apparent Hubble multipoles; survey footprints with different error levels therefore imprint survey-aligned
patterns. This is the mechanism behind H-L5f.

### L2. Stress of a massive collisionless species

**Statement.** In a type-I background at first order, a collisionless species with isotropic initial
distribution f0 has f(q, n) = f0(a q (1 + beta_ij n^i n^j)) with beta_ij = int s_ij dN, and
pi_ij = -(2/15) beta_ij Kcal, Kcal = 4 pi int dq f0 q^4 (4 q^2 + 5 m^2)/E^3. For m = 0, Kcal = 4 rho; for
non-relativistic particles pi_ij = -2 P beta_ij.

**Proof.** The covariant momenta are conserved, so f depends on the conserved norm, which is
a q (1 + beta_ij n^i n^j) to first order. Then
pi_ij = int d^3q (q^2/E)(n_i n_j - delta_ij/3) f0'(a q) a q beta_kl n^k n^l; the angular integral is
(8 pi/15) beta_ij and an integration by parts gives int dq (q^5/E) f0' = -int dq f0 q^4 (4 q^2 + 5 m^2)/E^3.
The limits follow from E = q and E = m. QED

## 3. Prior work re-checked on 2026-11-16

| topic | what the source establishes | id |
|---|---|---|
| general Hubble law | luminosity-distance expansion in a general spacetime; 9, 25 and 61 degrees of freedom at first, second and third order in redshift | E18 |
| drifts | direction and redshift drift for general observers; the observer velocity contributes a dipole and shear a quadrupole | E25 |
| proper motions | anisotropic expansion gives a curl-free quadrupole; aberration drift and secular parallax; a B-mode dipole channel (passage seen only in part) | E50, E51 |
| reference frame | the astrometric solution has orientation and spin degrees of freedom fixed with quasars (kinematically non-rotating frame) | E52 |
| zero point | a distance zero-point dipole is degenerate with a Hubble dipole | E09 |
| impossibility | valid confidence sets for locally unidentified parameters are unbounded with positive probability; bounded sets have zero coverage | E53, E54 |
| Bayes under partial identification | credible sets can lie inside the identified set while frequentist sets extend beyond it; report the identified set and the conditional prior | E55, E69 |
| support functions | inference on partially identified sets through support functions | E56 |
| cosmology practice | profile likelihoods are used against prior-volume effects | E57, E58 |
| estimated dispersion | least squares with an estimated dispersion matrix | E59 |
| tilt | a super-horizon isocurvature mode gives a relative velocity of the radiation and matter frames and no intrinsic count dipole; dipoles in tilted anisotropic models and their side effects | E60, E61 |
| count tomography | separating the kinematic from the intrinsic count dipole with redshift information | E62 |
| transfer kernels | first-order polarized transfer in a flat anisotropic universe | E46 |

Rows marked as recalled from memory in the ledger (E54, E63 to E69) and the partly seen passage of E51 still need
the primary source (R54-L07).

## 4. What may be claimed after the re-check

- Identifiability (T6, T7). Every ingredient is published. What this file adds is the organization: one rank
  criterion per irreducible block, the null channels, the two gauge orbits with their testable and untestable
  hypotheses. Claim level: an organizing theorem with elementary proof. Novelty LOW to MEDIUM and unverified.
- Validity (T2, T3, T4). Classical. Cosmology already uses profile likelihoods for the same purpose. No
  novelty claim; the contribution is the application to the kinematic variables and the explicit body.
- Transport (T8, T9). T9 is an identity. T8 is elementary but gives exact statements that the R54 reports
  needed: no model-free upper limit on a shear amplitude, a sign-change certificate, and the order of the
  late-time blind spot. Novelty LOW to MEDIUM and unverified.
- Power (T1). None, by theorem.

## 5. Not proved here

Coverage under a misspecified covariance or selection; the size of the estimator bias on a real catalogue;
the power of any test at observed amplitudes; anything about finite-wavelength modes or Bianchi families
beyond type I. These need data or simulations and stay with the local nodes.
