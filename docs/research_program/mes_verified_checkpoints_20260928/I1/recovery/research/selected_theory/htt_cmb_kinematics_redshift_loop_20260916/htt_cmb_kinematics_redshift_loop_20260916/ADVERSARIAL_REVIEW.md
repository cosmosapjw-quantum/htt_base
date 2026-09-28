# ADVERSARIAL REVIEW

## Attack 1 — "Q_ab and sigma_ab are both STF2, so Q measures shear"
REJECTED.

Sharing the same SO(3) representation gives only a representation adapter, not a physical
response law. The radiation quadrupole obeys a transport equation containing time derivatives,
streaming, higher/lower multipoles, collisions, acceleration, vorticity acting on anisotropy,
and shear. Generic Q -> sigma is non-identifiable.

Surviving statement:
under a restrictive homogeneous collisionless near-isotropic local closure,
dot T_ab^sky = sigma_ab.

## Attack 2 — "The CMB is blind to vorticity"
REJECTED as a global statement.

omega is exactly absent from the scalar local photon-energy/Hubble projection, but it acts
as a same-l angular-rotation generator on pre-existing radiation multipoles. No direct
monopole-to-anisotropy vorticity source appears at first order about isotropic radiation.

Surviving statement:
omega is an exact null of the scalar directional Hubble/redshift-generator observable,
not of the full radiation transport problem.

## Attack 3 — "Multiple redshift bins automatically add independent information"
REJECTED.

Rank gain requires linearly independent redshift kernels. Near-proportional kernels give
poor conditioning even when the algebraic rank is formally full. Correlated covariance and
shared nuisance parameters reduce practical information.

## Attack 4 — "Remote quadrupoles at z1,z2 directly differentiate the CMB in time"
REJECTED in a generic spacetime.

Remote quadrupoles live at different spacetime points and have different past light cones.
A redshift finite difference is not a proper-time derivative along one congruence worldline
unless an explicit spacetime/worldline identification is supplied.

Conditional route:
homogeneous Bianchi-like or otherwise spatially controlled models can turn redshift tomography
into a temporal shear-history probe. In the general inhomogeneous case it is a 3D spacetime
field reconstruction problem.

## Attack 5 — "T_CMB(z) gives theta(z) model-independently"
REJECTED.

T_CMB(z)=T0(1+z) is an integrated adiabatic result. Recovering local theta from dT/dz requires
the time-redshift relation and photon-conservation assumptions. In a general spacetime,
redshift itself is path- and direction-dependent.

## Attack 6 — "First-order distance-redshift multipoles are a new result"
REJECTED.

The exact 9-DOF local directional-Hubble structure and higher-order cosmography are established
in the Heinesen / Maartens / Clarkson lineage.

Project value:
use these observables as an independent physical response lane against the radiation/CMB lane.

## Attack 7 — "The derived radiation–cosmography bridge identity is already established"
UNRESOLVED.

Each ingredient is established:
- covariant photon redshift generator,
- nonlinear radiation PSTF hierarchy,
- blackbody temperature/brightness adapter.

A bounded SciSpace search did not find a paper that states the compact combined local identity

H(n) = -dot ln Tbar - dot T_a^sky n^a + dot T_ab^sky n^a n^b

under the stated near-isotropic homogeneous collisionless assumptions.

This is insufficient for a priority claim.
Disposition: NOVELTY-CANDIDATE, targeted primary-literature hostile audit still required.

## Attack 8 — repository hierarchy table
CONCERN CONFIRMED, but implementation survives.

The documentation special-case table says ell=0 keeps only expansion and dipole divergence.
Direct substitution into its own general formula gives nonzero
(2/3) A·Pi_1 and (2/15) sigma:Pi_2 terms.
The actual code retains these terms.

Disposition:
DOCUMENTATION_BUG, not an implementation failure in the inspected code path.
