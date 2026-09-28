# One-to-one source matrix

## S1 — Photon energy / temperature redshift generator

### Proposed PAPER-A object
Directional kinematical response
H(n)=theta/3-A_a n^a+sigma_ab n^a n^b.

### Primary source correspondence
Räsänen (PRD 79, 123522, 2009) uses photon propagation direction e^a and writes the
collisionless blackbody law

(∂_t + e^a D_a) ln T
= -(theta/3 + A_a e^a + sigma_ab e^a e^b).

Heinesen (JCAP 05 (2021) 008) uses outward observation direction n^a=-e^a and defines

H(n)=theta/3-A_a n^a+sigma_ab n^a n^b,

with dE/dλ=-E^2 H.

Therefore, for the same physical congruence and collisionless blackbody radiation,

(∂_t - n^aD_a)ln T = -H(n).

Status:
ESTABLISHED, not novel.

Wolfram:
the sign/direction adapter gives exact zero residual.

Implication:
The previous "strict radiation–cosmography bridge theorem" must be demoted to a
literature-anchored dictionary lemma.

---

## S2 — Harmonic coefficients of the directional derivative

Räsänen explicitly expands the directional derivative of ln E/T in angular harmonics and
obtains the scalar/vector/STF2 coefficients

monopole = -theta/3,
dipole   = -A_a    (in propagation-direction convention),
quadrupole = -sigma_ab.

Status:
ESTABLISHED.

Important:
These are coefficients of a DIRECTIONAL DERIVATIVE of ln T/E, not of the instantaneous
temperature sky itself. This directly supports PAPER-A's instantaneous-Q-to-shear
non-identifiability, but substantially reduces the novelty of that no-go.

---

## S3 — Radiation PSTF hierarchy

Maartens, Gebbie & Ellis (PRD 59, 083506, 1999), Gebbie/Ellis and later reviews establish
the nonlinear covariant radiation multipole hierarchy.

PAPER-A may use the hierarchy as prior machinery but must not claim it as a new result.

Status:
ESTABLISHED.

---

## S4 — Exact isotropic-radiation / EGS-side kinematics

The EGS/generalised-EGS literature already establishes strong relations between exact
radiation isotropy and congruence/spacetime kinematics, with crucial assumptions on the
observer congruence, acceleration/geodesicity, matter content and Copernican extension.

Status:
ESTABLISHED.

PAPER-A role:
assumption audit and physical boundary, not novelty.

---

## S5 — General-spacetime directional Hubble / distance-redshift cosmography

Heinesen 2021 gives the general luminosity-distance expansion without assuming FLRW or field
equations, with 9, 25 and 61 coefficients through first, second and third order in z.
The first-order directional Hubble object is exactly the theta/A/sigma combination above.

Status:
ESTABLISHED.

PAPER-A role:
the clean operational-optics response lane.

---

## S6 — Observer/frame dependence

Maartens, Gebbie & Ellis explicitly note that covariant/gauge-invariant physical quantities
become physically meaningful only after a physically appropriate four-velocity is chosen,
and discuss distinct energy/particle frames.

Mitsou & Yoo and Yoo et al. show that observer/source tetrads are required to translate a
photon wavevector into measured energies, angles and lensing quantities.

Status:
ESTABLISHED.

PAPER-A role:
formal type system separating coordinate gauge from physical observer changes.

---

## S7 — Optical observables and propagation

Sachs/Jacobi-map and bilocal-geodesic-operator literature provides coordinate-independent
descriptions of:
- redshift,
- angular/luminosity distance,
- image deformation,
- parallax,
- position/direction drift,
- redshift drift,
- combinations insensitive to endpoint motion.

Status:
ESTABLISHED.

PAPER-A role:
measurement layer / future data interface, not a new optics formalism.

---

## S8 — CMB phase-space observables

Relativistic kinetic theory treats the photon distribution as a phase-space scalar (or
matrix-valued distribution with polarization). Its decomposition into energy, direction,
brightness/temperature multipoles and Stokes components requires an observer tetrad/screen.

Status:
ESTABLISHED.

---

## S9 — Remote CMB tomography

kSZ/pSZ literature already reconstructs redshift-tagged remote CMB dipole/quadrupole fields
and evaluates the number of accessible modes.

Status:
ESTABLISHED.

PAPER-A role:
future instantiation of the redshift-response architecture.

---

## S10 — Vorticity sensitivity

The scalar photon-energy/directional-Hubble contraction has an exact vorticity null.
However CMB vector modes and late-time combinations such as kSZ + moving-lens are sensitive
to vortical/vector information.

Status:
channel-specific null ESTABLISHED/DERIVED;
"vorticity unobservable" REJECTED.

---

## S11 — What survives as plausible novelty

1. Exact local-observer STF2->STF3 inverse/projector/conditioning geometry:
   M_Q=(Q:Q)I+(6/5)Q^2 and sharp kappa_2(M_Q)<=5/3.
   Status: strong NOVELTY_CANDIDATE; separate final hostile audit required.

2. PAPER-A's typed inverse-problem architecture that prevents observer change, gauge
   redundancy, representation basis and statistical nuisance from being conflated.
   Status: methodological synthesis candidate, not new GR.

3. Metric-aware representation-covariant practical-rank contract for cosmological tensor
   inference.
   Status: standard linear algebra, potentially useful methodological contribution.

4. Joint multi-observable / multi-redshift kinematical consistency programme.
   Status: programme significance, not yet a completed scientific result.
