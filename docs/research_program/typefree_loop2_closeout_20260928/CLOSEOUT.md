# Loop 2 scoped closeout

## Decision

`CLOSED_SCOPED_WITH_EXTERNAL_BLOCKERS`

The bounded type-free Loop 2 correction is implemented and locally validated.
This decision does not mean all scientific propositions, historical PRs, future
solver work, or observational inference are complete.

## Corrections

- **F1:** the kernel condition is now stated only for unconstrained finite-dimensional
  linear/affine variations; a bounded/curved feasible set uses its fibre image.
  Boundedness, unique identification, and confidence calibration are distinct.
- **F2:** `db/safe_append.py` accepts the hash-pinned final Loop 2 gzip as a
  read-only source, rejects path/inode aliases and every existing output before
  mutation, holds exclusive descriptors, appends transactionally, and cleans
  only outputs it created after failure. Six focused tests pass.
- **F3:** `gap_column3` is described as one three-component column. The explicit
  3×3 Frobenius identity is a separate theorem; TF-S2/S4 remain component-level.

The corrected deterministic gzip is
`db/THEORY_INHERITANCE_LOOP2_CORRECTED.sqlite.gz` (SHA-256
`a7f2052c4e71a94e8784749ac359023e505873d2d20c2889ab4128f4db70f6f6`,
59,021,082 bytes). The uncompressed result SHA-256 is
`71781daf3f5cd65296b78928dafab3e0a59cac65cf94f018e3bffbfe23377c72`.
`db/SAFE_APPEND_RECEIPT.json` records all 22 pre-existing table row hashes,
`integrity_check=ok`, three correction rows, two review rows, and measured source
identity before/after. The 549 MB working SQLite was temporary because it exceeds
the repository transport limit; the deterministic gzip is the durable form.

## Review boundary

The supplied external audit remains the independent pre-correction review and is
recorded as `FAIL_CORRECTIONS_REQUIRED`. A fresh follow-up assignment was
registered, but the installed router correctly refused launch because this host
session exposes no actual author model/effort attestation. Requested routing is
not actual execution evidence, so no reviewer PASS is claimed. This is the
remaining correction-package admission blocker, not a reason to reopen the wider
research loop or to promote four-axis/observational claims.

## PR and issue disposition

- `ALREADY_INTEGRATED_CLOSED`: #440, #449, #460, #461, #463, #465, #466, #467.
  Their audited heads are ancestors of `de3ab202`; GitHub close is not relabeled
  as a merge event.
- `SUPERSEDED_CLOSED`: #468 and #470. Current R9/optical recovery paths and the
  211-card DAG retain the usable requirements without restoring old status files.
- `OPEN_HOLD`: #469 and all remaining entries classified that way in
  `PR_DISPOSITION.json`; #427's actual 337-file diff and #469's 591-commit base
  gap prohibit smoke integration.
- `OUT_OF_SCOPE`: #428, whose 2,131-file delta includes 2,106 deletions.
- Issue #448 is closed after unchanged-head run 33718012456 attempt 3 succeeded.
- Issue #445 remains open. On repaired head `f621a581…`, independent attempt 1
  failed with projection `2dbe0061…`, while attempt 2 passed with `8b0aadf1…`.
  That cross-run bifurcation is the exact remaining blocker.

## Scientific ceiling

I2 remains `DEFENDED_CONDITIONAL`; I3 remains `HOLD_INPUT_INCOMPLETE`. P3 is a
local total-Einstein-source statement, not a dust EOS or global cosmology result.
The historical engines did not execute one shared contract and are not combined
into a four-axis pass. Numerical (Q,F,\Pi,G_F), MES percentage, p-value,
likelihood, family identification and observational admission remain unavailable.

## Preservation

The original Loop 1 ZIP, original database/gzip, both historical Loop 2 gzip
files, raw transcripts, receipts, and source documents were not modified or
deleted. The active R9 run, task/thread identities, historical usage, failures,
scientific HOLDs, and protected files were not rebound or reset. The seven
pre-existing tracked user modifications and unrelated untracked materials remain
outside this change set.
