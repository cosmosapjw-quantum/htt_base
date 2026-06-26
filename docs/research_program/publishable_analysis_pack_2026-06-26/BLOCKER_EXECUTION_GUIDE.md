# Blocker Execution Guide

## K1: Public E2E Low-Ell Global Calibration

Goal: replace the current synthetic K1 stand-in with a global rank p-value from matched public E2E simulations.

Inputs:

- Planck FFP10 or NPIPE/PR4 E2E simulation products;
- observed map processed through the same method;
- fixed mask, beam, NSIDE, ell range, and statistic list.

Execution stages:

1. Validate `examples/k1_e2e_manifest.example.json` against the real manifest schema.
2. Generate per-map low-ell summaries outside git.
3. Run the frozen max-scan on simulation summaries.
4. Compute +1 rank p-value.
5. Update generated result table only through its builder.

Required code PR:

- input manifest validator for real maps;
- summary builder that emits compact JSON/Parquet, not raw maps;
- regression fixture with tiny synthetic maps;
- claim scan tests for K1 result text.

Exit gate:

- global rank p-value;
- matched-pipeline config hash;
- map IDs and input hashes;
- exact command log.

## K5: CF4 Release-Matched Forward Mocks

Goal: convert bulk-flow apex/depth from fixed-noise mechanics into release-matched coverage.

Inputs:

- CF4 release binding;
- release selection and distance-error model;
- release-matched mock ensemble.

Execution stages:

1. Validate `examples/cf4_release_mock_manifest.example.json` against real mock metadata.
2. Run the same estimator on data and each mock.
3. Report component coverage, amplitude coverage, bias, and depth/frame ablations.
4. Keep cosmic variance and measurement noise separate.

Exit gate:

- coverage report with mock manifest;
- figure manifest with generating command and input hashes;
- generated K5 result row.

## K6: CF4 Realization-Conditioned Curl Posterior

Goal: report a curl/vorticity-sector posterior only if the supplied field ensemble can carry it.

Inputs:

- constrained 3D CF4 field realizations;
- grid geometry, frame, smoothing, units, and seed/provenance metadata.

Execution stages:

1. Validate `examples/cf4_realization_manifest.example.json`.
2. Fit affine components per realization.
3. Report Cartesian components and covariance before norms.
4. If the field is curl-suppressed, emit a structural no-go instead of a posterior.

Exit gate:

- posterior median plus 16/84 percentiles, or explicit no-go;
- field realization manifest;
- stability report over radius/boundary/subsample choices.

## PR08-006: Joint Artifact

Do not start until K1, K5, and K6 all close.

Required rule:

- missing sectors remain missing;
- blind sectors remain blind;
- no MIO diagnostic payload is consumed as HTT evidence.

## PR10: Native Low-Ell Solver

The current pack does not implement PR10. It can only provide:

- interface requirements;
- exact FLRW comparator requirements;
- transfer schema expectations;
- atlas gate checklist.

