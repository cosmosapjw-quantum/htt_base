# Independent review — PR-OBS-ANALYSIS-PREP

**SCOPED_PASS. No BLOCK_NOW findings.** This passes the released-summary and descriptive-report delivery plus its full continuation handoff. It does not validate a new physical fit, joint posterior, native transfer, Bianchi identification or the historical proof corpus.

Reviewed read-only in the existing `cosmosapjw` checkout on branch `obs/scientific-analysis-ready-20261014`, based on commit `6365e36d0ccc6acddb7f6909aacea8d766c0fc4a` (tree `02976f294a26854daee6116d34e71af0a8bce232`). One fresh bounded reviewer; no authorship or recursive reviewers. Requested runtime: `gpt-6-astra / ultra`. Observed model and effort: **UNKNOWN**.

## Findings

No blocking correctness, regression or scientific claim-scope defect was found in the three new commands, two new tests, generated results, DAG change or OA00–OA11 handoff.

- DESI uses the existing hash-bound release reader and fixed-Gaussian law. The result is `D_V/r_d = 7.924712263167666 ± 0.15073384889703623` at `z_eff = 0.2952346949471036`. The positive-domain intervals invert Gaussian acceptance rules. Sampling-coordinate conversion includes `1/f`; prediction reparameterization adds no likelihood Jacobian. No posterior or simultaneous family-coverage interpretation appears.
- CF4 plotting preserves the observed grouped coverage, overlapping method presence, fiducial distance convention, coefficient scales and stored singular values. The report excludes the manufactured injection. Numerical rank remains conditional sensitivity, not detection.
- CMB coefficient order and harmonic convention agree with the referenced implementation; the ell 0–5 fit is distinguished from the plotted ell 2–5 block. Kelvin conversion is correct. Four products/six contrasts remain one correlated sky, with physical dipole, full-field F4 and posterior requirements still open.
- New runners preserve existing output directories. Preparation records path/runtime availability separately from scientific eligibility, includes the current CMB original-header paths and defaults to CF4/CMB evidence reuse.
- OA05–OA11 retain the physical analysis destination, including the genuine DESI conditioning adapter and currently refused legacy POSTERIOR input. No all-PR merge, conditional-premise promotion or blanket native-solver gate is introduced.

## Evidence and bounded checks

Read AGENTS.md and the compact repository adversarial-review, scientific-validation, claim-firewall and claim-provenance skills. Read the new source/tests, relevant existing readers/laws/conventions, plan/handoff, README, DELIVERY, NEXT_TASK, PR delta, actual result metadata and execution evidence.

Reused recorded **49 passing focused cases** and the **12 passing reporter cases after the final layout correction**, both exit 0. The two Matplotlib/Pillow warnings are deprecations; output generation succeeded. Did not duplicate these tests or rerun scientific campaigns.

Independently compared the current bytes with recorded identities: all five DESI source hashes, four DESI output hashes, three report-input hashes, eight report-output hashes and the final report-code hash match. All three canonical DAG files match their compatibility mirrors byte-for-byte; the recorded strict DAG check passes. All four final PNGs were visually inspected and have readable axes, units, legends and scope caveats. PDFs are generated companions; this review did not independently render their pages.

Exact source/result hashes and machine-readable scope are in `REVIEW.json`. The reviewed PR status is still `in_progress`; root owns routine status closure, commit and publication. No remote mutations were performed by this reviewer.

## Claim audit

| Product | Owner | Accepted scope | Evidence |
|---|---|---|---|
| DESI scalar summary | HTT | C1 / CONDITIONAL | Retained published Gaussian HDF5 through existing reader/law |
| CF4 coverage and sensitivity | HTT/obsstat diagnostic source | DIAGNOSTIC_ONLY | Accepted R2-02 report reused |
| CMB same-sky contrasts | obsstat | C0 / DIAGNOSTIC_ONLY | Accepted R2-03 report reused |
| Combined presentation | manuscript | C0 / REPORT_ONLY | Named source JSON and newly generated figures |

No claim upgrade or downgrade is required. Existing scientific HOLD/UNKNOWN states remain unchanged.

## Nonblocking note and follow-up

The README terminology note was resolved by changing the DESI link label to `DESI 공개 요약자료 결과`; the exact changed line and final README hash were checked. OA05–OA11 remain scientific/model/implementation work, not completed by this scoped pass.

Proceed with the authorized publication after routine status metadata closure. Any subsequent scientific-code change needs only its concrete targeted closeout against the new hash.

