# R62 — Anisotropy classification and conditional Bianchi compatibility

One owner-selected ten-stage theory/coding study, dated 2026-11-17. Base commit: `c118982e56ee50d68dd0446aa10f16ffe65bd02b`. Branch: `research/r62-anisotropy-classification-20261117`.

## Read first

- [Korean results and publication assessment](REPORT_KO.md)
- [Theory, conventions and derivations](THEORY.md)
- [Finite paper/research plan](RESEARCH_PLAN_KO.md)
- [Research DAG](RESEARCH_DAG.json)
- [Executed result summary](RESULTS/INTERPRETATION_SUMMARY.json)
- [Validation and provenance](VALIDATION.md)

The actual CF4 calculation uses 35,970 groups, seven declared nuisance operators, the full existing Gaussian covariance, and source-bound 21/26-parameter quadratic/cubic response models. It evaluates 42 tensor carriers and 210 class questions. All 168 structured-class queries have explicit witnesses inside their corresponding 95% joint confidence ellipsoids. Every calibration-free varying carrier includes zero. The tensor-zero conclusion depends on nuisance treatment and response order. There is no claimed physical Bianchi-family identification, tilt detection or cosmological frame rotation.

The actual-operator injection demonstrates that a common-frame source can yield noncommuting apparent window tensors. Source-response inversion recovers the commuting coefficients to floating-point precision. This is a constructed noiseless example, not a stochastic survey simulation.

The already-qualified R36-08 Pantheon+ magnitude carrier is also reused without a new source fit: two-depth STF10 and difference-STF5 carriers under primary and lower-z selections all contain zero. Their explicit zero witnesses therefore establish compatibility with every structured class. A one-tensor difference has no nontrivial common-frame restriction. No CF4/SN joint likelihood is formed because the physical frame, overlap and shared-PV contracts remain unresolved.

## Reused and repaired physics

R48/R49 algebra, Ricci, constraints and tilt invariants are reused with explicit scope. The active constructor now evaluates the actual momentum-map range, correcting an invalid extrapolation of canonical isotropic-n IX to all IX states. It retains rank-zero restrictions and the exceptional VI_-1/9 rank-two condition. The physical-velocity moment Jacobian is now distinguished from the squared-component moment map. Historical receipts remain historical; the unrelated legacy constraint-sign path is explicitly not certified.

The independent review's R62-F1 correction makes momentum-range acceptance independent of the Einstein-coupling scale and uses equation-relative residual checks. Raw residuals, their scales and normalized values are retained. Initial affected verification passed 113 tests; the targeted physical suite after the correction passed 100 tests, including 14 new unit/coupling regressions. The statistical code and observed results were unchanged by this repair.

## Executable interfaces

- `htt/htt/htt/infer/r62_tensor_classes.py`: full-covariance STF-series witnesses, calibration quotient, signed commutator forms and optional numerical enclosures.
- `scripts/r62/build_r62_source_carriers.py`: actual-source CF4 response and J1/R61 control, calibration and fixed-frame injections.
- `scripts/r62/run_r62_classification.py`: all actual tensor class results with per-carrier receipts.
- `scripts/r62/run_r62_bianchi_examples.py`: conditional positive-dust IX, V, exceptional VI_h and action-equivalence examples.
- `scripts/r62/summarize_r62.py`: result aggregation and PNG/SVG figures.
- `scripts/r62/reuse_r62_sn_carrier.py`: narrow analytic reuse of the qualified SN carrier, preserving units and source-contract limitations.
- `tests/r62/`: analytic, independent-coordinate and physical constraint regressions.

Imports use `PYTHONPATH=htt/src:htt:.` and the existing `.venv/bin/python`. Use one BLAS thread and `PYTHONDONTWRITEBYTECODE=1`. The source builder and classification runners refuse to overwrite populated result directories. A replay must use a fresh output directory; the supplied receipts preserve the original executed inputs and code hashes. The R62 DAG finalizer is intentionally a one-shot metadata mutation, not part of scientific replay.

## Result identity

- Original R58 carrier SHA-256: `42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d`.
- R62 source carrier SHA-256: `1d0f3c353ea9189bffbab5728f295264c6925d4a3d82561c4457e48746beefd2`.
- The full source carrier retains response, precision, score, q0, whitened likelihood factor and covariance. Individual classification receipts retain every witness, amplitude, frame/shape, direct distance and quadratic enclosure.
- `ARTIFACT_MANIFEST.json` binds the release files. `REVIEW/history_sources.json` binds the prior work that was actually inspected.

The original six-track publication programme and its 42 scientific gates are preserved. This is a P5 companion route with `NOT_READY_TO_SUBMIT` publication status. No automatic successor research loop or local-agent restart prompt is created.
