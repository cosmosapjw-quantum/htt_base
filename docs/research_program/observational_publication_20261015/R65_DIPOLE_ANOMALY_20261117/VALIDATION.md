# R65 verification, actual execution and claim limits

Baseline `d76ef3a4e9b33c4703a02647b3aa850004d04253`; existing owner checkout only.
This is one integrated ten-stage dipole study, including one bounded R8 source
refinement. The primary scientific verification and the focused checks for the
newly admitted overlap code are complete. A fresh final review is recorded
separately in REVIEW/final_review.{md,json}; repository publication/DAG validation
has its own receipts and does not substitute for scientific evidence.

## Actually executed

| Operation | Evidence | Observed result |
|---|---|---|
| Original conditional-count and weighted-RACS semantics | RESULTS/AFFECTED_TEST_RECEIPT.json; REVIEW/affected_tests.log | 24 tests passed, process0 |
| Newly added same-source overlap/source-influence semantics | RESULTS/OVERLAP_TEST_RECEIPT.json; REVIEW/overlap_tests.log | 13 tests passed, process0; original24 not rerun just for another PASS |
| Exact symbolic reference identities | REVIEW/SYMPY_CHECK.json | 11 identities true, process0 |
| External CAS evaluation | REVIEW/WOLFRAM_CHECK.json | quotient difference0; finite power-law response2+q+alpha*q; physical linear-density axial derivative generally nonzero |
| Original NVSS actual-data models | RESULTS/NVSS_EXECUTION.json | 8 observed models; 24 independent bin fits; 68 observed optimizations;512 conditional bootstrap catalogues with2048 refits; process0 |
| RACS source-posterior projection | RESULTS/RACS_EXECUTION.json | 6 weighted joint posterior models; outer/child/internal-member identity checks; process0; no new SBI fit/training |
| R8 same-provider peak/integrated source repair | RESULTS/PROVIDER_NVSS_EXECUTION.json | 4 additional observed models;12 bin fits;34 observed optimizations; paired component overlap retained; process0 |
| R8 saved-carrier interpretation and figures | RESULTS/FINAL_INTERPRETATION_EXECUTION.json | source-overlap covariance and five views, conditional precision diagnostics,4 figures; process0; no new raw-catalogue fit |
| R9 bounded metadata/presentation correction | RESULTS/R9_PRESENTATION_EXECUTION.json; REVIEW/CORRECTION_RECEIPT.json | neutral provider-peak labels and claim-dependent future scope; saved-carrier renderer process0; existing numerical JSON structure and NPZ bytes unchanged; no new observed fit/bootstrap/test pass |

Totals are **37 distinct targeted test cases**, **12 observed models**, **36 bin
fits**, **102 observed optimization calls**, the original **512 conditional
bootstrap catalogues** and **6 released posterior projections**. Symbolic checks
and bootstrap refits are not counted as unit tests. Source-identity checks are not
extra empirical samples. No broad repository suite or new independent survey
measurement is claimed.

Native scientific processes used `.venv/bin/python`,
`PYTHONPATH=htt/src:htt:.`, `PYTHONDONTWRITEBYTECODE=1` and one thread each for
OpenBLAS/OMP/MKL. Runtime versions are embedded in the actual result JSON.
Pytest was invoked with `-p no:cacheprovider`. Test commands, return codes,
duration and logs are stored in the receipts above.

## Meaningful checks and their domain

The tests compare conditional and profiled-Poisson likelihood ratios, finite
differences of score/Hessian, full-information Schur profiling, exact ring
nuisance invariance, singular axial directions, the nonzero axial sensitivity
of a different physical linear-density model, finite-bin response limits,
full-covariance path invariance and frame transport. They reject invalid counts,
exposure, maps and likelihood ordering. They do not claim the true survey
selection is supplied merely because the numerical likelihood is concave.

RACS checks include nonuniform nested weights, valid zero-weight extremes,
coordinate transformation against an independent pole value, physical speed
normalization, invalid CSV/weights/latitude and internal-member corruption.
The archive initially encountered a read-only inspection error when a macOS
resource-fork member was treated as a nested ZIP. The final reader explicitly
excludes `__MACOSX` metadata and verifies the six named science archives and
every manifested member. The actual RACS production returned0. No failed science
fit was replaced by a fabricated summary.

Overlap checks use an independent explicit source-event Gram construction,
identical-selection zero contrast, disjoint membership variance addition,
invalid overlap margins/counts, coordinate covariance transport and a fit-free
known-information example. They validate the new same-source covariance
mechanism. The covariance is an empirical independent-source Poisson influence
law, not a cosmological clustering covariance. Source multiplicity remains a
scientific-model obligation rather than a software failure.

The 512 bootstrap draws calibrate the original raw-peak common-vector question
under its fitted multinomial null. They do not calibrate the later integrated
selection, the CMB physical null, or all alternative masks. The p-values derived
from observed information are asymptotic working-law values. The paired source
contrast uses a separately labelled linearized sandwich law.

## Source and physical qualification

Raw NRAO PEAK INT is a real peak-brightness quantity with a JY/BEAM header. Its
semantic distinction from integrated component flux is supported by original
survey documentation and direct coordinate/value comparisons, not the header
alone. R8 downloaded the provider's available integrated column and verified
its full-file SHA. The input-availability issue is resolved. Provider extraction
provenance, source spectra at the boundaries, peak-detection completeness,
component-to-galaxy grouping and LSS cross covariance remain distinct obligations.

The exact nuisance fibre belongs to the discrete loglinear model. It is not an
all-orders Lorentz/physical no-go. Angular STF coefficients are not spacetime
shear. Rank4 in beta+common residual coexists with poor actual precision; no
finite physical bound is assigned to a removed axial direction.

The two provider selections share241892components. Their marginal count fits
are not multiplied as independent likelihoods. Their joint4vector has an
influence-Gaussian covariance with the measured shared-membership block. The
RACS projection is geometric transport of the source posterior, not a new
declination-conditioned RACS fit. RACS ablations are sensitivity diagnostics,
not equally qualified models or an averaged physical posterior. No independent
NVSS–RACS product or global-tilt/Bianchi assignment is made.

## Evidence states and scientific decision

- **Literature-supported:** selection response, existing2D dipole methods,
  flux-bin fitting, original NVSS field semantics and RACS source model.
- **Derived:** finite conditional likelihood, profile/Schur identity, exact
  sufficient carrier, finite-bin boundary response and source-overlap influence.
- **Numerically checked / implementation-verified:** named semantic tests,
  symbolic checks, actual observed fits, bootstrap and posterior transformations.
- **Observed within a declared working law:** paired selection-dependent vector
  shift; signed flux consistency; angular nuisance sensitivity; weak beta/residual
  separation; RACS posterior/calibration coupling.
- **Unresolved:** physical origin of the selection shift; full cosmological null;
  a source-qualified velocity excess; standalone priority relative to a matched
  conventional analysis. No universal impossibility result is admitted.

Current paper decision: P4 companion consolidation, `NOT_READY_TO_SUBMIT`.
The ten-stage research execution can be complete while the original scientific
paper acceptance remains unchanged. Future work is finite and specified in
RESEARCH_PLAN_KO.md and RESEARCH_DAG.json; no automatic successor is launched.

## Independent review and release

The initial independent review found three LOW provenance/documentation issues,
preserved in `REVIEW/final_review_initial.{md,json}`. A single bounded correction
uses provider peak (`peak_flux`) without claiming a verified provider correction
pipeline, fixes final artifact paths/four-figure inventory, and makes LSS a
requirement for a physical-excess expansion rather than the narrow companion.
`REVIEW/CORRECTION_RECEIPT.json` retains before/after identities, exact metadata
replacements and numerical-structure/NPZ preservation evidence. The R8 execution
receipts remain unchanged; the later saved-carrier renderer has its own R9 receipt.
These presentation changes add no observed fits or test cases to the counts above.

One fresh independent final reviewer receives the actual current source, results,
derivations and publication plan. Findings and any single bounded correction
episode are preserved in REVIEW. Finalizer execution is forbidden until its
actual report says PASS, all findings are CLOSED and submission remains
NOT_READY_TO_SUBMIT. Finalizer guards original42/paper payloads and adds exactly
one canonical completion. Git publication is an authorized non-force push of
the scoped branch; no merge, worktree, clone or local-agent prompt is produced.
