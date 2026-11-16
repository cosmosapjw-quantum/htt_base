# R54 research state (2026-11-16)

Version: R54.1. Branch `research/r54-tensor-frame-tomography-20261116` on base `research/r50-observed-convergence-20261115`. Claim ceiling C0.

## Central question

Can the tensorized five-view layer make calibrated, frame- and epoch-typed statements about
(sigma_ab, omega_a, A_a, beta_a) from data already owned, and does any statement exceed what the
nearest published method gives?

## Active assumptions

- First order in the departure; type I for the CMB lane; linear LCDM for the low-redshift body.
- Two neutrino-stress variants: massless, and minimal normal ordering with the exact collisionless stress weight (R54-EQ-06).
  The present-shear map differs between them and depends on the initial state, so its numbers are illustrations.
- CF4 is analysed at catalogue level (35970 committed groups) with the log-distance estimator and the exact linear LCDM pair-sum body;
  no selection function and no calibration covariance between objects. Zero-point nuisance is modelled in three ways
  (pooled, method monopoles, method x hemisphere steps) and no model is preferred a priori.

## What changed in R54

- Views: all five are available on the CMB lane; on the low-redshift lanes x, Q, Pi and G_F are available and F is UNAVAILABLE
  (an axis scan is not a support functional). R52 had Q, F and Pi unavailable.
- CMB: two history functionals with closed-form kernels (a re-derivation of E46); r_E(perfect fluid) = 0.0711; Sigma_T = 0.9157 x the R51 sharp operator.
- CMB: the present-shear map is model-labelled: 1.42e-10 (perfect fluid, T+E), 6.66e-08 (massless stress family), 3.43e-08 (minimal normal ordering).
- CMB: the T functional is blind to a late-time shear whose sign changes; the E functional bounds its rms at 0.0735 for z < 0.2 (diagnostic lane).
- CMB: PR3 ell = 2 B-mode null fails (p = 9.54e-06); the E lane is diagnostic.
- CF4, corrected inside this loop: the R36 linear estimator is biased (14-40% of its pole dipole) and the
  ideal-sky body is too small (exact/ideal sd up to 1.61 for the dipole, 1.93 for the quadrupole).
- CF4 with the log-distance estimator and the exact body, by zero-point nuisance model (pooled / method monopoles / method x hemisphere steps):
  joint null p = 0.000344 / 0.00277 / 0.112; calibrated locking tail = 0.0242 / 0.0085 / 0.147;
  class = EXCESS_NOT_POLE_LOCKED / UNRESOLVED_POLE_LOCKED / LCDM_BODY_COMPATIBLE; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL.
  Neither "locked to the equatorial pole" nor "not locked" is stated.
- CF4 hemisphere step (z < 0.055): -1.66 +- 0.53% of H, consistent between FP, TF, SN and OTHER (p = 0.867);
  single-axis tail 0.0017, tail of the scan maximum over 151 split axes 0.0339. Its reading as a common mode is on HOLD
  (the four estimates share the body; E43 reports survey-level differences).
- Counts: the receipt estimator has power 0.20 against a doubled dipole, so its non-detection decides nothing; tilt closure with CF4 is preliminary (p = 0.0895).
- Theory (R54-THM, THEOREMS.md): the tie with the exact likelihood, the simultaneous validity of the views, the selection rule by multipole and parity,
  the zero-point and frame-spin gauge orbits, the sign-change theorem for shear histories and the frame closure identity are proved and machine-checked.
  No novelty is claimed for the statistics; the selection rule and the sign-change theorem carry an unverified LOW to MEDIUM novelty flag.

## Blockers

None for the cloud nodes. Local nodes need the data drive; PR4 simulations are not needed (PR4_BYPASS_CONTRACT.json).

## Local nodes

- R54-L01: DONE_SCOPED_C0
- R54-L04: DONE_SCOPED_C0
- R54-L02: DONE_SCOPED_C0
- R54-L03: DONE_SCOPED_C0
- R54-L06: DONE_SCOPED_C0
- R54-L07: DONE_SCOPED_C0
- R54-L08: DONE_SCOPED_C0

## Next minimal action

none: the programme has a manuscript decision, then the remaining nodes in the order above.
