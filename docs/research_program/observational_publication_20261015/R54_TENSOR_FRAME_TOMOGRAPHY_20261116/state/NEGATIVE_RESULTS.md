# R54 negative and reopened results (2026-11-16)

Rejected and reopened hypotheses are retained on purpose. A REJECT entry is not re-tested without new data or a new model; HOLD entries are open and are listed in DECISION_LOG.md.

- **H-C2** (CORE): A tensorized carrier gains statistical power over the exact likelihood. Result: R53: Fisher-distance ratio 1.0000, coverage tie.
- **H-L1c** (L1): PR3 component-separated ell = 2 polarization can be used at face value. Result: B ell=2 tail p=9.54e-06 (SMICA), 3.96e-07 (Commander); observed rms 0.30 vs FFP10 0.11 uK.
- **H-L1d** (L1): Octupole or higher morphology constrains type-I parameters. Result: ell >= 3 modes enter only through covariance.
- **H-L2c** (L2): The R52 counts-versus-CF4 frame inconsistency is a statement about cosmic frames. Result: tilt closure V_CF4 + c beta_excess = 0: p=0.0895 (V only), 0.0123 (constant dipole marginalised); count side preliminary.
- **H-L3c** (L3): Any type-I shear compatible with the CMB functionals is far below low-redshift sensitivity, so low-z STF2 signals are local or systematic within type I. Result: for a shear confined to z < 0.2 the T functional bounds a constant-sign history at 0.000225 and is blind to a sign-changing one; the E functional bounds its rms at 0.0729 (diagnostic lane; 0.0972 with the B-null floor), above the CF4 quadrupole of 2.5% of H.
- **H-L5e** (L5): A physical direction-dependent Hubble factor is detected in CF4. Result: joint null p from 0.000344 (pooled) to 0.112 (method x hemisphere steps marginalised); class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL.
- **R53 (retained)**: the tensor carrier ties the exact likelihood and the optimal score; it does not beat them.
- **Withdrawn inside R54, twice**: (1) the first pass (committed R36 multipoles, ideal-sky body, linear estimator) gave a pattern axis 2.8 deg from the equatorial pole with sky fraction 0.0005 and nulls of 5.71e-05 and 1.07e-05; the catalogue-level run showed the estimator bias and the too-small ideal-sky body. (2) The opposite statement of the second pass, 'not locked to the pole', was withdrawn after the independent review: the calibrated tail is pooled 0.0242, method monopoles 0.0085, method x hemisphere steps 0.147 under the three zero-point nuisance models and the flag has low power (17% for a step of the observed size). The question is open (H-L5c HOLD).
- **Per-method dipoles with white errors** (p down to 8.04e-29 for TF) are not evidence: with the exact body every family has p >= 0.0873.
- **'The dipole excess is absorbed by method x hemisphere steps'** is not evidence either: that nuisance model removes the hemisphere direction by construction.
- **Finite-MC inflation**: the R53 expression is conservative; the exact Wishart ratio is sqrt[n(n-1)/((n-p+k)(n-p+k-1))] and equals 1 for p = k (analytic 1.1547 against leave-one-out 1.1546 for the T-only carrier).
