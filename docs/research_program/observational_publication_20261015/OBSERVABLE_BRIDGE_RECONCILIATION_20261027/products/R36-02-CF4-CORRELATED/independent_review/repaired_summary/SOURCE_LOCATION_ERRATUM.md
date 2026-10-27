# R36-02 outer source-location erratum

This erratum accompanies, and does not modify, candidate
`sha256:a0edd2e76d0b74630d47bbccd5cd90dcb4e372ca1772ee202585a34270d68fb4`.
The current source entrypoint must consume `RESULT_REFERENCE_RESOLUTION.json`
when exposing the inherited controls references in `repair_01/RESULT.json`.

| RESULT field | Frozen value | Explicit path relative to repair_01/RESULT.json |
|---|---|---|
| controls | CONTROLS.json | ../CONTROLS.json |
| sample_covariance_uncertainty | CONTROLS.json#sample_covariance_if_N64_p36 | ../CONTROLS.json#sample_covariance_if_N64_p36 |

Both controls references resolve to:
`/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED/CONTROLS.json`.
The retained controls SHA-256 is
`5bc24992254da084775eff20b89f49346db9be85158a54ad12df76caefa726e9`.
Its source authority is the parent base manifest, candidate
`sha256:dd3cb2d77c97e33380ec06e04bc5465f65129dc319f8795dc30e3bc84b3e877b`.
The independent review actually read this file, matched its hash to that manifest,
and checked that the `sample_covariance_if_N64_p36` key exists.

`footprint_method_sensitivity` already resolves to the repaired sibling
`SENSITIVITY.json`; its hash is
`ebacda58de95a46e5418ecdbf400976ecd21829c013f774e74ecc7c1ff3d47c5`.

Bare document-relative resolution of the two frozen controls fields fails because
there is no `repair_01/CONTROLS.json`. This is a P3 packaging locator ambiguity.
The actual bounded cache-summary consumer does not read either field and
reproduces RESULT.json and SENSITIVITY.json byte for byte. The parent manifest
already gives an unambiguous source identity. No separate RESULT resolver
contract or failing operational controls consumer was found in the searched
scripts, tests, or R36 package. This erratum does not assert that the frozen
relative fields themselves have been corrected.

Reproduce the explicit source resolution with the existing project interpreter:
`.venv/bin/python -B /mnt/extdrive/workdir/htt_open_data/r36_cf4_summary_repair_independent_review/check_result_references.py`.
The script performs actual file reads, hashes and the fragment check; its
`RESULT_REFERENCE_RESOLUTION.json` is the machine-readable map consumed by this
review. Before publication, the publisher must carry this erratum/map into the
current README/source map entrypoint so that consumers see the correct locations.
This packaging integration does not require covariance or summary recalculation.
The frozen candidate, failed candidate, preimages and scientific ceilings remain
unchanged. No original 42-node acceptance is promoted.
