# Current Blockers

Date: 2026-08-04

This file lists current blockers only. Historical failure narratives remain in
their owning PR deltas and frozen receipts.

## Closed success dependencies

- PR-190 is a terminal receipt-bearing refutation, not a successful theorem.
  Its `requires_success` edges into PR-191 and PR-205 remain closed.
- Completion status alone cannot reopen those edges. A future versioned
  `ClaimCapabilityDecision` must name the replacement statement/evidence and
  explicit supersession before any DAG replan.
- PR-172 remains `COMPLETED_FAILED_WITH_RECEIPT`; PR-184 is its completed
  premise-complete successor. The old failure does not justify a duplicate
  B-projector repair event.

## Data and execution blockers

- PR-274 admitted zero products. There is no observed execution authority.
- All lane approvals are absent: `H-PLANCK`, `H-CF4`, `H-HSC-KiDS`, `H-ACT`,
  `H-DESI`, and `H-JWST` are `NOT_AUTHORIZED`.
- PR-151 remains background acquisition only. Partial DESI inputs, `.part`
  files, or incomplete validation ensembles cannot enter a result.
- Name-only HSC/KiDS, cited-seed JWST rows, or incomplete Planck/CF4/ACT
  products do not pass admission.
- A clean checkout is not permission to redownload external data. Existing
  external roots must first pass the PR-289 identity/admission contract.

## External/native blockers

- The authenticated native low-ell solver and native morphology atlas are not
  available. PR-159--166, PR-183, PR-229--246, and native-dependent rows stay
  dormant.
- Pre-native family identification remains forbidden even if a scalar,
  nearest-orbit, response, or cross-probe diagnostic is numerically sharp.

## Harness and publication blockers

- The two historical broad-suite receipts agree on 406 failures but differ by
  one pass. They remain historical. PR-280 must create the cache-free JUnit
  baseline and classify every failure with `UNKNOWN_UNCLASSIFIED=0`.
- GitHub ruleset mutation is separately blocked on `G-CI-H`.
- PR-277 is merged at remote descendant `a780043...`; its historical failed
  and passed review receipts remain preserved.
- PR-278 content is complete. Immutable R1's source-regeneration failure is
  preserved; amended content R2 passed all 21 cells on `34ec32aa...`. The
  closeout commit changes status/handoff bytes and is not yet delivery-final:
  it requires a new exact seal/review, latest-target integration, and fresh PR
  inventory before the single attended transaction.
- Active graph `INVALIDATES_*`, `REQUIRES_RECALIBRATION`, and
  `REQUIRES_REEXECUTION` edges are capability blockers. They cannot be cleared
  by caller omission or a status/gate annotation.
- The owner authorized one content history slot, one closeout commit, and one
  attended non-draft review PR for PR-278. Direct push/PR commands remain
  forbidden; the exact final sealed SHA may
  be pushed only inside the single attended transaction. Approval, merge,
  force-push, and ruleset mutation remain unauthorized.
- Publication remains blocked until PR-208 and may consume only results granted
  by the capability engine with generated sources and admitted data identities.
