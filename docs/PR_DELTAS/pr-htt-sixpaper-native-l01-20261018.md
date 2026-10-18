# L01 actual native matched splits and original-support response

The native full/HM/OE matched fit had not run, and its later PMASK support was
not the original 30021-pixel polarization support. This increment executes the
unchanged five-product native stream once and supplies the original-support
spin response/remainder bridge without conflating these estimators.

Native run started at reviewed HEAD `1e095a2749cce9b28e45aac043a82218c21f84e5`.
The S02/H02 sibling increment was published at `5450b044` while this disjoint
analysis finished. All native driver/dependency/input identities remain pinned.
No raw map download or extra native SHT was performed.

- Actual native full RHS replay is approximately 2e-15 relative; fixed-window
  counts 37120921/36951769. Full matched mask contrast is 26.6274 nK; HM/OE
  half-difference norms 22.8774/15.0500 nK and their angle 102.0052 degrees.
  These are coefficient diagnostics, not noise fractions or independent skies.
- Original intersection-first coverage>=0.995 mask reconstructs exactly 30021
  RING64 pixels. Finite low64/high90 spin-response norm is 1.70060815923;
  E-high→B-low gain 0.93449494753. Independent healpy injections agree.
- Five saved L128 products are projected on that original support, with vector
  closure and explicit low/mid/9..128 components. Full native-child-average
  versus L128 reconstruction differs by 94.0028 nK and 4.357018 degrees.
  The two processing operators remain explicitly distinct.

Artifacts: `CONTINUATION_20261018/L01_EXECUTION_20261018/` under the publication
programme; code, tests, numerical JSON/NPZ, two PNG/PDF figures, first failure,
execution log and frozen receipt. The reviewed native run JSON is also archived
unchanged, SHA256 bbd6a7221dcec4ac6d9983239ce74371a80ca458bf8724a5dfeb0fb0b07df31c.

Validation: 39 existing native tests and 20 new tests passed; parent reran the
20 pytest tests (8.94s). A parent unittest-discovery attempt collected zero tests
and exited 5 because these are pytest function tests; the correct pytest command
then passed. Fresh independent Astra review reran all 59 and independently
reconstructed mask, 154 spin columns, native moments and five QR projections.
No required repair or blocking finding remained. Review identities and limits
are recorded in `INDEPENDENT_REVIEW_NATIVE_L01_20261018.md`.

Decision: L01 completed_scoped in its original finite source-processing scope.
No acceptance/dependency was changed. Progress 15/42; derived frontier L02/V02,
with L03 externally blocked but its source-matched preparation executable.
T ell>32, polarization ell>128 and intrinsic physical tails remain unknown or
unbounded. Physical null calibration remains L03; all six papers remain
NOT_READY_TO_SUBMIT. No solver/ODE, main merge or journal submission.
