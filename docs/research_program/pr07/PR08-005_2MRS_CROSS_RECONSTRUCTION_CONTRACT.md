# PR08-005 — Independent 2MRS Cross-Reconstruction Contract

state: ready (contract/spec; no covariance merge until cross-covariance owned)
owner_lane: cf4_reconstruction
depends_on: [PR08-004]

## Purpose

Define a provenance-complete comparison of the CF4 affine flow against an
**independent** 2MRS posterior reconstruction (Nusser 2026, arXiv:2606.08593)
evaluated at the CF4 object positions. This is a cross-check, not a combination.

## Contract (must all hold before any comparison number is reported)

1. **Provenance.** Record release hash, reconstruction method (WF/CR vs Bayesian),
   smoothing scale, prior, and frame convention for *both* fields.
2. **Position matching.** Evaluate both reconstructions at identical CF4
   supergalactic positions; report Cartesian affine components before any norm.
3. **No covariance merging.** The CF4 and 2MRS covariances are **never** added or
   inverse-variance-combined unless the cross-covariance between the two
   reconstructions is explicitly owned and registered. Absent that owner, only
   side-by-side component comparison is permitted.
4. **Curl handling.** If either reconstruction enforces potential flow, its
   vorticity channel is structurally absent (see PR08-004); the comparison is
   restricted to bulk/expansion/shear.

## Exit gate

A provenance-complete side-by-side component table with both fields' independent
(not merged) uncertainties. Any combined posterior requires the registered
cross-covariance owner; until then it terminates `BLOCKED_MISSING_CROSS_COVARIANCE`.

## Forbidden

- Merging CF4 + 2MRS covariance by assumption (independence is not given).
- Promoting agreement/disagreement to a global-tilt or family claim.
