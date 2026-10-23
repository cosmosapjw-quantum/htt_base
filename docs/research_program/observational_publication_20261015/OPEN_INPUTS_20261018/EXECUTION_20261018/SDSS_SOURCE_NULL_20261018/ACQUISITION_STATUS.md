# SDSS source-null acquisition, 2026-10-18

Historical intake/preparation snapshot below. The original three transfers and
monitor later disappeared with unknown cause/exit codes; do not relaunch those
commands. Current reviewed parent-owned recovery and actual launch bindings are
in [RECOVERY_INDEPENDENT_REVIEW.md](RECOVERY_INDEPENDENT_REVIEW.md) and the parent
[RESUME.md](../RESUME.md). The recovery controller performs whole validation,
indexing and header inspection automatically, then stops before science; do not
run the historical inspector command concurrently or repeat a consumed phase.

Owner: obsstat source diagnostic. Scope: the public SDSS mock archive only;
non-claim-bearing preparation, with scientific computation **NOT_STARTED**.
This unit does not complete any original 42-input request or establish H02 coverage.
Requested executor: `gpt-6.1-sol/high`; observed runtime identity: UNKNOWN.

Intake checkout: `research/htt-open-input-theory-20261018`,
`ad27f4cb5f84dfaccc322e53f2810ad29dc72276`. The shared checkout subsequently
advanced independently; observed preparation HEAD:
`b4a93016afb57a5b115bff4dbfa65bc3d56d4b65`. No reset/rebinding occurred.

Frozen source: Zenodo record 6824749, version v1.1.0,
`https://zenodo.org/api/records/6824749/files/mocks.tar.gz/content`,
10,643,218,721 bytes, expected MD5 `9ba3e8876f6f08a2af00d30cbf1c6cd9`.
The complete archive identity remains unverified while acquisition is live.
The original two description PDFs and their headers are preserved unchanged.

External storage:
`/mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018/`.
The live process initially had PID 747838 and terminal session 54380;
verify its current status before any continuation. The process acquires exact
intervals 0–4294967295, 4294967296–8589934591, and 8589934592–10643218720,
each at most 4 GiB, then assembles and verifies the full archive.
Each completed range retains a size/SHA256 receipt; a continuation validates
and reuses completed ranges. Unvalidated partials are retained and cause an
explicit recovery stop rather than automatic restart or overwrite.

First response: HTTP 206 with exact
`Content-Range: bytes 0-4294967295/10643218721` and
`Content-Length: 4294967296`. ETag was unavailable. Raw response metadata is
`range.0-4294967295.response.json` externally. Observed initial sustained
throughput was approximately 0.9–1.0 MiB/s; network time is separate from
the 600-second cumulative scientific budget.

A separately authorized 1 MiB official UI-route probe returned HTTP 206 and
`Content-Range: bytes 0-1048575/10643218721`. Its bytes equal the API prefix;
SHA256 `00bb14de500c2129386e049e7a2277e90164f03da6e4e8da459e831181d84c12`.
Its measured request time was 4.245948 seconds (246,959 bytes/s including
startup); this does not establish a faster route. Both probe bytes and raw
headers are preserved externally. No completed bulk chunk was redownloaded.

The parent subsequently authorized concurrent acquisition of the other two
disjoint frozen intervals, with a maximum of three network streams. Actual
process bindings observed together:

| Interval | Terminal session | PID | Loaded source |
|---|---:|---:|---|
| 0–4294967295 | 54380 | 747838 | Initial sequential version |
| 4294967296–8589934591 | 68237 | 762427 | Range-only version, index 1 |
| 8589934592–10643218720 | 23005 | 762426 | Range-only version, index 2 |

Initial source preimage is preserved as `acquire_sdss_range0_loaded.py`, SHA256
`187527d79814508ec5776145a3e17c3cbf2e3ce82484c9c2476b11a650ec0b78`.
This preimage was reconstructed by exactly reversing the later range-index
option patch; it was not separately hashed at process launch. The later
`acquire_sdss.py` source used by range-only instances has SHA256
`5e458c48a28637eb10fb33bd8660d04e69ee4ed65910f1324f2e8449135f3d02`.
The live original process retains the original loaded code. If it reaches a
still-active next interval, its refusal to overwrite that unvalidated partial
is an orchestration stop; preserve all bytes and assemble only after all three
independent completed receipts validate. No reset or bulk retry is authorized.

The bounded source-stage continuation `finish_stage1.py` is also live:
terminal session12571, PythonPID799127 (shellPID799123). It logs to external
`stage1_monitor.log`, monitors only the existing three requests, and issues no
new range requests. After all three completed receipts exist, it waits for the
original coordinator to finish, reuses validated chunks for complete MD5-checked
assembly if needed, indexes/freezes the selection, and inspects only the first
selected member. It then exits `STAGE1_RETURN_TO_ASTRA`; no actual mock fitting
is authorized by this continuation. Verify these exact processes before any
restart. Observed preparation HEAD at launch:
`0d4d7a811323dccc4944a8c1c27dbc5a83068438`.

Six local boundary tests pass (`ACQUISITION_TESTS.txt`): reject ignored ranges
before body consumption, altered Content-Range/length, content encoding,
unsafe extraction, incomplete/duplicate identity sets; freeze numeric-box Y0
selection independently of archive ordering. These tests do not validate the
unseen archive or any scientific result.

The parent authorized finite estimator preparation while acquisition continues.
Eight pure fixture tests now pass: exact D07 basis parity via AST extraction
(without importing its campaign), zero/constant/dipole controls, independent
full-intercept SVD agreement, shared-window covariance and Gaussian inverse-Gram
distinction, rank rejection and invalid-value rejection. This is not actual-source
execution or field qualification. The test subprocess used one BLAS/OpenMP/MKL
thread and charged 0.322396 seconds to the same cumulative 600-second ledger
(`SCIENTIFIC_BUDGET.jsonl`); actual mock science remains NOT_STARTED, with
599.677604 seconds remaining at that checkpoint. `CONTRACT.md` preserves the
frozen source/header/stage2 contract for continuation and review.

After the download completes, run with the existing interpreter:

```sh
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/SDSS_SOURCE_NULL_20261018/inspect_archive.py /mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018 docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/SDSS_SOURCE_NULL_20261018
```

The inspector requires complete size/MD5 validation, indexes all regular
members with traversal/link safeguards, requires 256 box identities × eight
observers, freezes the 64 numerically lowest box identities at observer zero,
and enforces a 2 GiB selected-member cap. It then safely extracts only the
first selected member and records its first eight lines and token counts.
This preparation has not yet observed the actual header, delimiter, positional
mapping or precision. Return those observations to the Astra framer before
running the frozen scientific calculation.

Claim audit: source acquisition is IMPLEMENTED and boundary-tested; full-source
identity, actual-header qualification and scientific execution remain pending.
No transfer/native-solver, cosmological inference, physical null calibration,
independent-universe or family-identification claim is made. The retained mock
hierarchy is 256 L-PICOLA boxes × eight observers; seed-ledger independence is
not certified. This source cannot substitute for the CF4 joint mock law.
