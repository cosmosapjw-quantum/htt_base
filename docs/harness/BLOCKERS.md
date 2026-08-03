# Current Blockers

Date: 2026-08-03

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
- PR-276's mutable history preserves failed R1, R2, R4, and R5 reviews; R3
  passed but was invalidated by later byte changes, and R6 passed both bounded
  pre-freeze axes. Immutable content review R1 then failed on generated-source
  self-reference and stale handoff wording; that receipt is preserved. The
  local content candidate remains unpushed, and its exact seal/review state is
  governed by the latest registered runtime evidence. Completion requires a
  strict-valid immutable PASS.
- Publication remains blocked until PR-208 and may consume only results granted
  by the capability engine with generated sources and admitted data identities.
