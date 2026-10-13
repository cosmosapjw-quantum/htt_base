# R2-03 candidate for independent review

Owner `obsstat` for released-product diagnostics; `htt` for the conditional
finite-ansatz moment. Claim tier C0. Upstream proofs are assumed valid under
owner direction; no proof campaign was rerun. No native solver or physical
closure is introduced. This return is an implementation report awaiting fresh
independent review.

## Changes and validation

The R2 ZIP `code/teff_invariants.py` is integrated unchanged in the existing
HTT core. `TeffMomentMap.moment` dispatches its full-sky finite four-coefficient
ansatz at alpha=4 through `legacy_coefficients`; arbitrary alpha retains the
original quadrature. No masked moment is dispatched through this identity.

The new obsstat bridge accepts an explicitly supplied positive angular-mean
T0 and a physical Cartesian dipole in the same frame as the dimensional
temperature STF quadrupole. It returns dimensionless d,S, F4, intensity-equivalent
Tbol and the STF-coordinate Jacobian, with a sufficient positivity condition.
Directional temperature, angular mean and intensity-equivalent temperature
remain distinct. S is temperature anisotropy, not velocity shear.
An optional full-sphere sup norm r of omitted temperature modes gives the
nonlinear envelope `|F4(full)-F4(finite)| <= 4(M+r)^3 r`, where
`M=1+||d||+||S||op`. Absent r remains UNKNOWN; no omitted mode is zero-filled.

The released-product response requires map/mask identities, the signed
anisotropy convention, explicit beam/pixel/removal policy, a supplied processor
implementation, and an absolute thermodynamic source in the same frame. It
uses the existing R7 Lorentz response. This wrapper creates a response, not a
likelihood or independent observation law. Its mask/removal/beam injection is
synthetic validation; an actual complete Planck processor remains unavailable.

Final affected suite: **15 passed**, with one existing matplotlib Axes3D
warning. It covers independent full-sky quadrature, rotations, legacy adapter,
arbitrary-alpha dispatch, centered gradients, Kelvin/microkelvin, the signed
dipole/STF harmonic crosswalk, positivity, omission envelope, zero-boost
processor/mask injection and existing R7 NSIDE64 zero/nonzero boost.
First environment failures remain in raw logs: the venv lacks astropy/healpy.
The existing `/usr/bin/python` has those dependencies and was used explicitly
for the successful affected suite and diagnostic. Commands and versions are
recorded in `COMMANDS.md` and `raw/runtime_versions.json`.

## Actual observation diagnostic

The numerical inputs are the existing R8 `cmb_controls.npz` and `cmb.json`,
whose identities are recorded by the runner. All four Planck component products
share a sky. The extraction uses NSIDE64, simultaneous ell=0..5 fit, retained
ell=2..5, the common intersection mask with **36,433 of 49,152 pixels**, and
released maps followed by pixel averaging without beam deconvolution.
Its masked residual ell=1 is never restored as the physical dipole.

Across the six same-sky pairs, retained ell=2..5 coefficient difference norms
range from **1.95916 to 5.51951 microK**. Quadrupole Frobenius differences range
from **1.20922 to 3.13289 microK**. These are descriptive coefficient differences;
they are neither calibrated bias estimates nor independent constraints.

Original SMICA/Commander/common-mask FITS paths, sizes, header hashes, mtimes and
observed headers are recorded by the diagnostic. The initial optional full-byte
hash attempt was interrupted after several minutes at the owner controller direction;
its exit 130 and raw streams are retained. Full-byte hashes of these exploratory
original-source records are NOT_MEASURED; exact numerical reduction inputs are hashed. NILC and SEVEM original headers and
release filenames are separately recorded in `raw/released_additional_headers.json`;
their byte hashes were not measured because those original files are not numerical
inputs to this reused reduction. The four intensity headers specify
NSIDE2048, NESTED, GALACTIC, K_CMB. Header/source capture does not rerun the
high-resolution reduction or establish its end-to-end calibration.

The diagnostic leaves actual full-field F4 and posterior as HOLD: a physical
dipole restoration, angular mean T0, omitted-mode treatment, full release
processor, and joint shared-sky cross-product measurement law are missing.
Published solar dipole parameters are not treated as independent of these maps.
The optional sensitivity API requires explicit T0, dipole and source identity;
no default physical dipole or T0 was supplied to this actual run.

## Claim and physics audit

Evidence: owner-frozen R2 card/package, accepted exact polynomial source,
current R7 response and harmonic bridge, R8 controls/processing metadata,
runner tests and original FITS headers. [Planck 2018 IV](https://arxiv.org/abs/1807.06208)
was verified for component method and release limitations; the official
[PR3 DOI](https://doi.org/10.5270/esa-zfx8b4s) remains the release reference
although the browser open failed. Monopole/dipole treatment is conditional on
each product's supplied removal convention; no uniform treatment across all
released component maps is asserted.

| Claim | Owner | Status | Evidence and ceiling |
|---|---|---|---|
| Finite full-sphere F4 evaluation | htt | IMPLEMENTED / CONDITIONAL | Exact accepted source and independent numerical checks; finite ansatz only |
| Reduced component coefficient differences | obsstat | DIAGNOSTIC_ONLY | Actual R8 same-sky controls; no bias calibration or product independence |
| Complete released-product response | obsstat | CONDITIONAL | Supplied-processor injection passes; actual full processor unavailable |
| Actual full-field F4 or posterior | htt | HOLD | Physical dipole/mean, omission treatment, processor and shared-sky measurement law missing |

Units are temperature K, or explicitly converted microK; harmonic normalization
is orthonormal real Condon--Shortley. Frames must match. The local observer boost
retains the existing R7 outward-direction convention. No family or geometry claim,
native transfer validation, MIO posterior or TSC solver claim is made. No new
permanent claim-registry row is needed for this bounded implementation report.

Requested author gpt-6.1-sol/medium; observed model and effort UNKNOWN.
The finite-ansatz implementation and C0 same-sky diagnostic received a fresh
read-only Astra/ultra scoped PASS. Full-field empirical integration remains HOLD;
see `REVIEW.md` for the exact decision and limitations.

## Reviewer scope repair

The reviewer identified overgeneralized monopole/dipole removal language. The module docstring and matching documentation now condition removal on the supplied per-product convention. Numerical code and the actual diagnostic are unchanged; its historical code hashes remain intact. The focused bridge suite passes 10 tests after the wording change. Current candidate hashes are recorded in `RETURN.json`, with the preceding candidate preserved in `PRE_SCOPE_REPAIR_RETURN.json`. Independent closeout is scoped PASS.
