# CLOSEOUT

## Strongest result of this loop
The mathematically cleanest synthesis is not a direct CMB tensor -> kinematics map.

Instead there are two distinct physical response lanes:

1. local optical/cosmographic lane:
   H(n) = theta/3 - A·n + sigma:nn,
   exactly invertible for theta, A_a, sigma_ab on the full sky, with omega_a null;

2. radiation-transport lane:
   theta, A, sigma, omega enter the nonlinear CMB brightness hierarchy.
   Under a homogeneous collisionless near-isotropic local closure only,
   the normalized temperature hierarchy reduces to
   dot ln Tbar=-theta/3,
   dot T_a^sky=A_a,
   dot T_ab^sky=sigma_ab.

Their combination produces a compact consistency identity:
H(n)=-dot ln Tbar-dot T_a^sky n^a+dot T_ab^sky n^a n^b.

This is a NOVELTY-CANDIDATE synthesis, not a certified priority claim.

## Redshift-dependent upgrade
Redshift should be treated as a response-coordinate/tomographic index, not merely metadata.

The most useful redshift-dependent lanes are:
- local/general distance-redshift multipoles d_L(z,n), d_A(z,n);
- T_CMB(z) monopole;
- redshift drift dot z(z,n);
- direction drift / proper motion;
- kSZ remote dipole field;
- pSZ remote quadrupole field.

The abstract identifiability criterion is:
same angular irrep + distinct redshift kernels can become distinguishable only when the
kernel matrix gains rank, and practical usefulness additionally requires acceptable
covariance-weighted conditioning.

## Candidate next theorem programme
A. Radiation–cosmography bridge:
   perform a dedicated source-by-source proof audit of the compact local identity and its
   sign/normalization conventions.

B. Redshift-tomographic identifiability:
   formulate response kernels for at least three physically distinct channels
   (distance cosmography, remote dipole, remote quadrupole) and derive joint rank/null spaces.

C. Vorticity channel:
   determine whether direction drift / proper-motion curl supplies an injective local
   response to omega_a after observer acceleration and frame-rotation nuisances are quotiented.

D. Statistical layer:
   carry redshift-bin covariance and shared optical-depth/calibration nuisance into the
   Fisher/null-space theorem; do not equate bin count with independent mode count.

E. Repository:
   repair the ell=0 special-case documentation after independent source confirmation.

## Claim gate
Analytic derivations: PASS.
Wolfram exact checks: PASS, after one transport 502 recovered by smaller exact evaluations.
Literature acquisition: PASS for bounded scope.
Repository source audit: PASS with one documentation inconsistency.
Novelty certification: HOLD.
Independent final decision reviewer: UNAVAILABLE.
Publication promotion: HOLD / INDEPENDENT_REVIEW_UNAVAILABLE.
