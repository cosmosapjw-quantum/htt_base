# Current Blockers

Date: 2026-08-08

This file lists current blockers only. Historical failures remain in their PR
deltas and strict result envelopes.

## PR-280 successor blockers

- PR-280 is terminal `COMPLETED_FAILED_WITH_RECEIPT`; completion is not success.
- PR-295 is `COMPLETED_SUCCESS` and satisfies only its own successor edge.
- PR-296 must repair the exact D2 PSTF progressive-closure active-core failure.
- PR-297 must repair the exact repo-scoped installer/config active-core failure.
- PR-280 `success_dependency_satisfied` remains false and PR-281--294 remain
  held until PR-296 and PR-297 both close successfully. No status annotation
  or partial test pass may clear this aggregate dependency.

## Closed success dependencies

- PR-190 is a terminal receipt-bearing refutation, not a successful theorem.
  Its `requires_success` edges into PR-191 and PR-205 remain closed.
- PR-172 remains `COMPLETED_FAILED_WITH_RECEIPT`; PR-184 is its completed
  premise-complete successor. The old failure does not justify a duplicate
  B-projector repair event.

## Data and execution blockers

- PR-274 admitted zero products. No observed execution authority exists.
- All lane approvals remain absent: `H-PLANCK`, `H-CF4`, `H-HSC-KiDS`,
  `H-ACT`, `H-DESI`, and `H-JWST` are `NOT_AUTHORIZED`.
- PR-151 is background acquisition only. At this checkpoint 540/1000 EZmocks
  were complete, batch 55 was active, and Abacus was 0/25. `.part` files and
  incomplete ensembles cannot enter a result or finalize phase.
- A clean checkout is not permission to redownload external data. Existing
  external roots must first pass their registered identity/admission contract.

## External/native blockers

- The authenticated native low-ell solver and native morphology atlas are not
  available. PR-159--166, PR-183, PR-229--246, and native-dependent rows stay
  dormant.
- PR-295 preserves a CAMB external-transfer diagnostic only. It is neither a
  native transfer nor a morphology atlas.
- Pre-native family identification remains forbidden even if a scalar,
  response, or cross-probe diagnostic is numerically sharp.

## Harness and publication blockers

- The final PR-295 staged candidate passed exact review, but delivery still
  requires the closeout commit, current-target integration/CI, and merge of one
  review PR before starting PR-296 from the new remote target.
- Active graph `INVALIDATES_*`, `REQUIRES_RECALIBRATION`, and
  `REQUIRES_REEXECUTION` edges remain capability blockers and cannot be cleared
  by omission or status prose.
- GitHub ruleset mutation remains separately blocked on `G-CI-H`.
- Publication remains blocked until PR-208 and may consume only capability-
  granted results with generated sources and admitted data identities.
