# R10 finite fixture conventions and derivations

Owner: HTT research; scope: diagnostic, exploratory finite calculations.
Plan: c8bd214a61088b684cad1d08873f05227cf5bfb0, tree d66ccc669492c2b6f233d58b818c86b69fc3aaa7.
No formal/observed admission or novelty claim. Source addition assertions remain imported.

## Units, signs and frames

Metric (-,+,+,+), epsilon_123=+1. Length coordinate x0=c t; physical energy
p=(epsilon/c)(u+e), u.u=-1, n=-e. A,sigma,omega,theta,H,V have inverse-length
units. With fixture L*=1, numerical parameters mean L* times their geometric
values; physical shear and rotation rates are c sigma and c omega, expansion
c theta, acceleration c^2 A. This is nondimensionalization, not c=1 as a
physical assertion. BASS eta is length-valued Mpc, ds=a d eta; its stored
Sigma=a sigma is divided by a in proper_shear_at_eta. No observer-time drift
or proper-motion measurement is represented by instantaneous H,V.

M_ab=D_b u_a=theta delta_ab/3+sigma_ab+epsilon_abc omega_c. For rigid
u_spatial=Omega cross r/c, M e=(Omega/c) cross e, hence omega=-Omega/c.
The independent Cartesian rotation test checks V=-M e. A rotating tetrad of
angular rate Omega_frame adds -Omega_frame cross e to coordinate direction
rates; this is a basis term and must not be added as matter vorticity.
The implemented endpoint screen is inertial/parallel, with zero screen connection.

Define [nabla_mu,nabla_nu] X^rho=R^rho_{sigma mu nu} X^sigma.
For screen Sachs vectors s_A, the focusing-sign tidal matrix is
Rcal_AB=R_{mu alpha nu beta} s_A^mu k^alpha s_B^nu k^beta;
D''=-Rcal D, trace Rcal=R_ab k^a k^b. O06 prescribes this optical matrix
without asserting that it is supplied by a global Einstein solution.
Our integration v increases into the past, k_past=(-1,n) in Minkowski units.
Its observer energy magnitude is 1, D(0)=0, D'(0)=I. The future photon
momentum is -k_past. Zero vertex determinant is regular but noninvertible.

## First-jet and optical derivation

Differentiating epsilon=-c u.p along an affine ray gives D_gamma ln epsilon=-H.
Projection of the direction derivative gives H u+V with
H=theta/3+A.e+sigma:ee and V=-P(A+sigma e)+omega cross e.
Sphere monomial integrals recover theta,A,sigma,omega using contract B.
The 12 basis columns have numerical rank 12; H-only rank 9 and V-only rank 11.
The E-mode potential A.e+sigma:ee/2 implies div V=2H1+3H2 (eight range
constraints); curl V=2 omega.e. The program checks their finite representative
and basis inversion. This is not a symbolic proof of all constraints.

D=diag(sin v,sinh v), D'=diag(cos v,cosh v) solves the independent tidal
fixture. Differentiating B=D'D^-1 gives B'=-Rcal-B^2. For z=v+v^2,
D_z=D'/z', D_zz=D''/(z')^2-D' z''/(z')^3. This exhibits the necessary
first derivative term. K_z=D_z D^-1 is unchanged by v_new=3v+2.
Vertex, sin(v)=0 caustic and z'=0 are refused by the inverse/chart helper.
The unsealed coordinate L_IJ expression is unused.

## Connected end-to-end fixture

The absolute ray endpoint is x_e=v n with a declared source surface and
source-axis rotation; D=v I only supplies its local angular derivative.
Source T_e=2.7 K [1+0.001 m_x m_y+0.0005 d_x d_y d_z] uses both position
m=x_e/|x_e| and emission sky direction d. The unit/rotated maps and constant
prescribed z=0.25 are boundary-transfer fixtures, not a claim that a static
flat emitter generates that redshift. Source-map rotations are coordinate
rotations, not geodesic rotation or null twist.

The physically connected nonzero-H example uses the flat Milne congruence
u=X/tau, tau=sqrt(t^2-r^2), with observer t=2 L*, source tau=1 L*.
A=sigma=omega=0 and theta=3/tau, so H=1/tau and V=0. The exact null
endpoint is (t,r)=(5/4,3/4)L*. Along the past ray tau(v)=sqrt(4-4v),
E(v)=2/tau. The code actually integrates d ln E/dv=E H by calling the
first-jet generator inside the ODE. It then transfers source T through this
integrated E, and extracts Q/O. Exact comparison: 1+z=2, mean T=1.35 K,
D=(3/4)I, Qxy=Qyx=0.0005 and each xyz permutation of O=0.0005/6.
These tensors are dimensionless; multiplying by mean T gives Kelvin tensors.
Milne radial boosts leave these radial sky labels unchanged. The separate
constant Lorentz observer boost checks the null condition and exact monopole
2.7 atanh(beta)/(gamma beta) and doubled-grid Q/O agreement, beta=0.1.

Liouville conserves I_nu/nu^3 and occupation at matched frequency; the tests
compare occupation at nu_e=(1+z)nu_o. There is no inverse-square factor for
diffuse surface brightness. The two-temperature mixture yields a frequency-
dependent effective temperature, with leading discrepancy proportional to
delta^2; this rejects an exact finite-anisotropy single-Planck closure.
No polarization/Thomson evolution is admitted.

## Independent T9 reference and scope

At the initially isotropic event, collisionless transport gives
partial_s f=epsilon (sigma:ee) partial_epsilon F. For F=exp(-epsilon/E*),
Pi0=integral epsilon^3 F d epsilon=6 E*^4 and
partial_s Pi2=sigma integral epsilon^4 F' d epsilon=-24 E*^4 sigma.
Boundary epsilon^4 F vanishes. Hence dPi2/deta=-4 a sigma Pi0.
The energy integral is evaluated independently at E*=0.5,1,2 without any
production coefficient table. For I_l=Delta_l Pi_l,
Delta2/Delta0=2/15, so the LHS coefficient is +8/15, not -8/15.
Future propagation e versus observed n does not flip an even quadrupole.

The current public photon RHS yields the opposite result on five Cartesian
STF tensors at a=1,2, including the actual Sigma/a adapter and packed scalar
round trip. Packed/full agreement is only implementation parity. A hypothetical
output sign reversal matches this isolated source; it is not a production patch.
The mixed CG five-m representation was executed but its independent physical
normalization is unresolved, so no mixed-mode sign repair is inferred.
The unnamed book equations in the attachment remain unsealed. Production
repair requires FORMAL_T9 and the current four-axis run-adjudicate path.

## Prior literature and limits

Fleury, Pitrou and Uzan, arXiv:1410.8473v3, sections III and V, distinguishes
central geodesics, screen transport and Jacobi optics; its Bianchi-I solution
is not reproduced or claimed here. Primary HTML inspected 2026-09-20.
https://arxiv.org/html/1410.8473
Korzyński–Kopiński 1711.00584 and Marcori et al. 1805.12121 concern actual
observer/source drift. Their primary abstracts were checked; full drift
response and equation-level reconciliation are not completed here.
https://arxiv.org/abs/1711.00584 ; https://arxiv.org/abs/1805.12121
