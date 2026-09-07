# From a CMB Sky Map to Physical Constraints

## An introductory account of tensor morphology, kinematical bounds and response-limited inference

Jiwon Park — pedagogical working-paper source, 7 September 2026

This is a new reader-facing exposition of Report A, not a renamed copy of its accepted 29-page evidence-integrated edition. The intended reader knows basic differentiation, matrix multiplication and elementary probability. Tensor geometry, STF multipoles, quotient reconstruction, the statistical hypotheses and the needed matrix results are introduced in the text before they are used.

The final reading artifact is one book-length PDF/TeX/Markdown document containing all six source parts, Appendices A–E and the bibliography. The split files below are for editing; they are not six independent reports and no external repository log is required to complete an argument in the assembled text.

## Reading sequence

1. [Foundations and the sky](01_FOUNDATIONS_AND_THE_SKY.md): the representation/inference distinction; tensor products, STF projections, rank, adjoints, spectral decomposition, least squares and Cholesky; spherical harmonics and the complete real-harmonic-to-STF normalisation.
2. [Orbit geometry, physical state and MES](02_ORBITS_PHYSICAL_STATE_AND_MES.md): a deterministic proper-rotation reconstruction with an explicit worked tensor pair; local observer geometry, frame velocities and physical functionals; radial sector restrictions and their relation to tensor direction.
3. [Inference, randomisation and observer response](03_INFERENCE_RANDOMISATION_AND_OBSERVER_RESPONSE.md): exact affine fibres, identification versus compatibility and coverage, finite-sample row and group ranks with counterexamples, and the local Lorentz/temperature/STF response derived step by step.
4. [Masks, nuisance and numerical error](04_MASKS_NUISANCE_AND_NUMERICAL_ERROR.md): the ordered processed estimator, quotient-rank proof, continuum mask construction, finite-operator limitations, error envelopes, robust rank and a proved gap-dependent projector bound.
5. [Mathematical appendices](05_APPENDICES_CERTIFICATES_AND_FIBRES.md): the Legendre formulae, finite rational axial certificate, full contraction-fibre and Hausdorff derivations, and a notation guide.
6. [Radiation model and kinematical estimates](06_RADIATION_MODEL_AND_MES_DERIVATION.md): an explicit sufficient first-order collisionless-radiation model, angular moment equations, derivative operators, and the shear/vorticity estimate used in the main text.

## Self-contained scope

Definitions and mathematical propositions are accompanied by their hypotheses and internal arguments. The exact axial rank certificate includes the polynomial integration rule, selected matrices/minors and integer fractions, rather than requiring a private CAS receipt. Historical nonaxial numerical values are labelled calculations and are not presented as universal theorems.

For the physical bounds, Appendix E starts from a declared geodesic first-order radiation model. It derives the transport moments and the bounds, including all normalisation factors and the meaning of each derivative envelope. In particular, a contracted second-derivative envelope is not silently treated as an uncontracted tensor norm. Strict conclusions require corresponding strict premises; the closed feasible bodies use the non-strict estimates. The local model is sufficient for the stated deductions, but a general nonlinear Einstein–Liouville almost-isotropy theorem and its converse are not claimed. The observed amplitudes alone do not supply the derivative premises.

This distinction does not send the reader to an external proof: the conditional model, calculations and interpretation are included. References acknowledge sources and give further reading. They are not replacements for the displayed arguments.

## Assembly and checking

Appendix E was authored after the first five parts. `assemble_edition.py` supplies the final reading-guide and Model-M paragraphs that connect those parts to the internal derivation and removes their now-obsolete import-only descriptions. The replacement text is fully authored, not a request that another agent invent the missing physical argument. It also places References after Appendix E. The chapter files and the accepted old report remain unchanged.

From a complete checkout, using an empty external output directory:

```bash
python3 docs/research_reports/pedagogical_20260907/assemble_edition.py \
  --bibliography docs/research_reports/final_candidate_20260907/HTT_REPORT_A_REFERENCES.bib \
  --output /ABSOLUTE/NEW/EMPTY/OUTPUT/DIRECTORY
```

The bibliography must be the retained twenty-entry file, Git blob `331c557c0f6a7de84fdd97123d8bdb8fae0e0a53`. The script emits a single manuscript, a bibliography copy and an assembly record. It refuses unexpected source anchors rather than silently dropping a paragraph. A mechanical anchor mismatch, if observed, is to be corrected against the actual paragraph and the authored replacement, not by deleting the check or changing the argument.

`check_axial_certificate.py` is a small, transparent exact-arithmetic implementation of Appendix B. It uses only rational numbers, the printed Legendre-polynomial coefficients, the mask integrals and Gaussian elimination. Running it is a check of this new printed certificate, not a finite-HEALPix calculation or a rerun of the old multi-axis CAS harness.

```bash
python3 docs/research_reports/pedagogical_20260907/check_axial_certificate.py \
  --out /ABSOLUTE/NEW/OUTPUT/axial-certificate-check.json
```

Neither script is represented here as already executed. Native assembly, equation/citation and cross-reference checks, the document-specific rational comparison, and a newly rendered PDF/page inspection must be recorded with their actual results. The old 29-page PDF must not be renamed as this much-expanded exposition, and its old page count must not constrain this document.

## Publication and privacy

Only the new manuscript and its supporting build/check material belong to this branch. The user's example report and private stylometry documents are editorial inputs; their files are not copied into this repository or attached to a public artifact. No font or installed package files are to be published.

The accepted Report A R3 source/PDF, canonical ledger, existing claims, production code, tests and historical evidence are preserved. This exposition does not create a Planck result, a physical shear or tilt estimate, a native Bianchi-solver result, a resolution of PR284, or finite-HEALPix containment. The recent fibre results are now explained internally as companion mathematics, not retroactively covered by the old four-lemma R2 receipt.

The external-facing paper should not carry workflow IDs, Git hashes, test-count dashboards or internal acceptance labels in its scientific body. Those details belong to the separate build and return record. The current branch is an authored source draft pending its own native document checks and rendering, not a claim of a newly built or independently audited PDF.
