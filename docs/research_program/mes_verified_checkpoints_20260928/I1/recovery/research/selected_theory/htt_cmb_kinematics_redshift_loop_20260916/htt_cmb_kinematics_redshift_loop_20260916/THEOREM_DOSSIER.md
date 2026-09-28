# THEOREM DOSSIER

## T1. Exact directional expansion/redshift-generator decomposition

Let u^a be a unit timelike congruence and let n^a be a unit spatial outward-sky direction,
u_a n^a=0, n_a n^a=1. Define the past-directed null direction at the observer by
k^a ∝ -u^a+n^a. Then

H(n) := k^a k^b ∇_a u_b /(normalization)
      = theta/3 - A_a n^a + sigma_ab n^a n^b.

The vorticity term vanishes identically because n^a n^b is symmetric while omega_ab is
antisymmetric.

Status:
- ESTABLISHED in covariant cosmography / Kristian-Sachs type treatments.
- WOLFRAM-EXACT: direct contraction of the 1+3 decomposition gave zero residual and
  zero dependence on all three independent omega components.

### Exact full-sky inversion
For a full-sky directional field H(n),

theta = (3/4π) ∫ H(n) dΩ,

A_a = -(3/4π) ∫ H(n) n_a dΩ,

sigma_ab = (15/8π) ∫ H(n) n_{<a} n_{b>} dΩ.

The inversion follows from
∫n_a n_b dΩ=(4π/3)δ_ab
and
∫n_a n_b n_c n_d dΩ=(4π/15)
(δ_abδ_cd+δ_acδ_bd+δ_adδ_bc).

Wolfram exact checks:
- second moment = (4π/3) I_3;
- ∫n_1^4 dΩ = 4π/5;
- ∫n_1^2 n_2^2 dΩ = 4π/15;
- reconstructed A_a equals the input A_a exactly;
- reconstructed sigma_ab equals the input trace-free symmetric tensor exactly.

Interpretation:
The first-order directional Hubble/redshift-generator field is a 9-dimensional local
kinematic observable: 1 scalar theta + 3 acceleration components + 5 shear components.
omega_a is an exact null direction of this scalar observable.

This is not a novel mathematical result. It is an essential typed physical adapter.

---

## T2. CMB temperature STF is not algebraically equal to radiation brightness STF

For a blackbody with directional temperature
T(n)=Tbar[1+Theta(n)],
the bolometric intensity/brightness scales as T(n)^4.

Even if Theta contains only an l=2 quadrupole, nonlinear powers generate l=0,4,6,8
brightness multipoles. For the axisymmetric example Theta=q P_2(x), Wolfram gives

(1+qP_2)^4-1:

l=0: q^2 [42+q(8+3q)]/35
l=2: 4q [77+33q+33q^2+5q^3]/77
l=4: 108q^2 [143+52q+17q^2]/5005
l=6: 72q^3(5+q)/385
l=8: 72q^4/715.

Therefore
brightness quadrupole = 4 × temperature quadrupole + O(Theta^2),
not an exact all-orders identification.

Status:
- DERIVED / WOLFRAM-EXACT.
- Physical principle ESTABLISHED.
- Scientific use: prevents a category error between observed temperature STF tensors and
  the energy-integrated brightness multipoles that obey the covariant kinetic hierarchy.
- Spectral distortions further invalidate a single-temperature adapter.

---

## T3. Transport, not representation, maps kinematics into CMB multipoles

Let Pi_{A_l} denote energy-integrated radiation brightness PSTF multipoles. The exact
1+3 covariant Boltzmann hierarchy contains expansion, spatial streaming, acceleration,
vorticity, shear, and collision terms. Consequently, an observed instantaneous CMB
quadrupole is not, in general, an algebraic measurement of sigma_ab.

At l=2, schematically,

dot Pi_<ab>
+ (4/3) theta Pi_ab
+ D_<a Pi_b>
+ (3/7) D^c Pi_abc
+ 5 A_<a Pi_b>
+ 2 omega^c epsilon_{cd<a} Pi_{b>}^d
- (4/21) sigma^{cd} Pi_abcd
+ (10/7) sigma^c_<a Pi_{b>c}
- 4 sigma_ab Pi
= K_ab.

Thus sigma_ab is mixed with:
- the time derivative of Pi_ab,
- lower/higher radiation multipoles,
- spatial gradients,
- acceleration,
- vorticity acting on existing anisotropy,
- collision/polarization terms,
- and, in a complete forward problem, background geometry and source history.

Claim:
Q_ab (observed temperature STF) -> sigma_ab is not a generic instantaneous inverse map.

Status:
- ESTABLISHED structure, supported by the nonlinear 1+3 covariant hierarchy.
- Repo source inspection agrees at the implementation level for the listed nine terms.
- This is a central identifiability statement, not a new Boltzmann equation.

---

## T4. Local near-isotropic radiation–kinematics bridge theorem

Assumptions:
1. a common congruence u^a is declared;
2. radiation is locally blackbody and near-isotropic;
3. keep only first order in anisotropic radiation multipoles and in A_a, sigma_ab, omega_a;
4. homogeneous local closure: projected spatial-gradient terms are neglected;
5. collisionless over the interval considered;
6. use proper time;
7. outward sky direction n=-e is used for observed odd multipoles.

Write Pi for the brightness monopole and define the linear temperature multipoles by

T_a^sky = - Pi_a/(4 Pi),
T_ab^sky = Pi_ab/(4 Pi),

where the minus sign in the dipole is the propagation-direction to outward-sky adapter.

The linearized hierarchy yields

dot Pi = -(4/3) theta Pi,

dot Pi_a = -(4/3)theta Pi_a - 4 A_a Pi,

dot Pi_ab = -(4/3)theta Pi_ab + 4 sigma_ab Pi.

Therefore

boxed:
dot Tbar / Tbar = -theta/3,

dot T_a^sky = + A_a,

dot T_ab^sky = sigma_ab.

The vorticity term is absent as a source from an exactly isotropic radiation state at
this order because it rotates pre-existing anisotropic multipoles rather than creating
them from the monopole.

Wolfram exact quotient-rule check returned:
- dot Tbar/Tbar = -theta/3;
- propagation-direction dipole derivative = -A;
- quadrupole derivative = sigma.
After n=-e, the sky dipole sign is +A.

Combining with T1 gives the local bridge identity

H(n)
= - d/dtau ln Tbar
  - dot T_a^sky n^a
  + dot T_ab^sky n^a n^b.

Evidence state:
- DERIVED from established covariant radiation hierarchy.
- WOLFRAM-EXACT algebra.
- NOVELTY-CANDIDATE as a compact radiation–cosmography consistency identity.
- NOT novelty-certified: bounded literature search did not find the same combined
  theorem, but absence of a search hit is not proof of priority.

Critical limitation:
This identity is NOT valid as an inversion of a single present-day CMB sky in a generic
inhomogeneous universe. It is a local time-derivative relation under the assumptions above.

---

## T5. Integrated shear-memory corollary for the radiation quadrupole

Under the assumptions of T4,

T_ab^sky(tau_2)-T_ab^sky(tau_1)
= ∫_{tau_1}^{tau_2} sigma_ab(tau) dtau.

Likewise the sky dipole difference is the time integral of A_a.

Therefore an instantaneous CMB quadrupole generally records an integrated response history,
not the instantaneous local shear.

Status:
DERIVED / conditional corollary.

Adversarial caveat:
Remote quadrupoles at different redshifts are not automatically samples along one common
fluid worldline. In an inhomogeneous universe they are values at different spacetime points,
with different past light cones. A finite redshift difference must not be silently replaced by
a proper-time derivative without a spacetime/worldline model.

---

## T6. Vorticity selection theorem and its limits

Two exact facts coexist:

A. Local scalar photon-energy / directional-Hubble response:
omega_ab drops out exactly because n^a omega_ab n^b=0.

B. Radiation multipole hierarchy:
omega_a appears at fixed l through a generator-like angular rotation term
l omega^b epsilon_{bc<a_l} Pi^c_{A_{l-1}>}.

Consequences:
- omega cannot be recovered from the scalar local H(n) field.
- omega does not create first-order CMB anisotropy from an exactly isotropic monopole
  through the direct T6 term.
- omega can affect an already anisotropic radiation field through angular transport.

Therefore the statement "the CMB is blind to vorticity" is false in general.

Potential omega-sensitive channels:
direction drift / proper motion / cosmic parallax / parity- or curl-sensitive angular
transport, and full dynamical forward models.

Status:
first two bullets DERIVED/ESTABLISHED;
clean injectivity of any proposed omega-sensitive observable remains UNRESOLVED.

---

## T7. Redshift-kernel identifiability theorem

Let several physical source components x_r transform in the same angular irrep of
dimension d (for example d=3 for a dipole or d=5 for STF2). Suppose an idealized
redshift-separable response is

y_alpha = sum_r f_r(z_alpha) x_r + noise,

or in matrix form
R = T_z ⊗ I_d,
where (T_z)_{alpha r}=f_r(z_alpha).

Then

rank(R) = d rank(T_z).

Thus same-irrep sources can be separated by redshift tomography if and only if their
sampled redshift kernels are linearly independent.

For two source kernels f,g at two redshifts,

det(T_z⊗I_d) = det(T_z)^d.

Wolfram exact examples:
d=3: det = -(f_2 g_1 - f_1 g_2)^3;
d=5: det = -(f_2 g_1 - f_1 g_2)^5.

For the specific pair {1,1/z},

det T_z = (z_1-z_2)/(z_1 z_2),
det(T_z^T T_z) = (z_1-z_2)^2/(z_1^2 z_2^2).

Hence merely choosing distinct redshifts gives structural rank, but the problem becomes
arbitrarily ill-conditioned as z_2 -> z_1.

Status:
- mathematics ESTABLISHED linear algebra;
- WOLFRAM-EXACT;
- potential novelty lies in using this as a typed cosmological experiment-design principle.

---

## T8. Covariance-weighted statistical identifiability

For Gaussian data with covariance C positive definite and response R,

F = R^T C^{-1} R

has
ker(F)=ker(R).

Therefore covariance weighting does not repair a structural response null if C is
nonsingular. It changes practical resolution/conditioning and uncertainty, not the exact
identifiable subspace.

Redshift bins may be strongly correlated:
- remote CMB bins share primordial modes/cosmic variance;
- pSZ/kSZ reconstructions carry optical-depth and tracer nuisances;
- distance-redshift bins may share calibration/systematic modes.

Thus "number of redshift bins" is not equal to "number of independent physical modes."

Status:
ESTABLISHED statistics; methodological firewall.

