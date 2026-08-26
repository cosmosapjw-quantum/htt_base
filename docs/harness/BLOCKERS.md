# Current Blockers

Date: 2026-08-26

Historical failures remain in their PR deltas and strict result envelopes.

## Active MES stack blockers

- The exact PR-315/PR-325 Planck package contains scalar features and rowwise
  anchors only. It has no direction vectors, alms, m-phase, or direction-indexed
  field. PR-327 must therefore keep `directional_moment_state` at
  `BLOCKED_DIRECTIONAL_SUPPORT`; a scalar value cannot create an axis or STF
  tensor.
- Raw sampled fields do not certify intrinsic parity or a global harmonic
  bandlimit. PR-326 preserves
  `DECLARED_UNVERIFIED_BANDLIMIT_AND_PARITY`, rejects only detectable component
  contradictions, and refuses ill-conditioned joint fits.
- Planck is one high-redshift shell and cannot identify local boost versus
  global tilt. PR-328 must bind physical response columns, frames, units,
  depths, covariance, and parameter identities before any conditional
  discrimination statement.
- PR-329 may proceed only with the first lane satisfying all six registered
  directional/depth/admission/covariance/response/frame gates. PR-321 HSC SACC
  fails the direction-indexed criterion. If no lane passes, terminate exactly
  `BLOCKED_NO_ELIGIBLE_DIRECTIONAL_LOWZ_LANE`.

## Preserved historical and external blockers

- PR-172, PR-190, PR-280, PR-307, and PR-312 remain terminal blocked receipts;
  completion is not success and their histories are not rewritten here.
- The authenticated native low-ell solver and native morphology atlas remain
  unavailable. Native-dependent rows stay dormant and pre-native family
  identification remains forbidden.
- PR-151 remains background-only. Partial acquisition files are not admitted
  into this MES execution.

## Process boundaries

- Do not import legacy `planck_mes_bounds.py` into observed code.
- Do not bulk merge PR-387/388 or PR-405..408, and do not cherry-pick PR-411.
- Do not close any PR automatically. PR-330 must emit the human-action
  disposition list.
- No security, privileged launcher, anti-tamper, publication, merge, or claim
  promotion work is authorized by this stack.
