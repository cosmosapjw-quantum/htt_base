# R32 independent source-integration review

**PASS after one targeted mathematical-domain repair. No open findings.**

Reviewed the selected source integration against base `0d5ab96bdb55398076629099664c77517ec33bb4`. Requested reviewer runtime was `gpt-6-astra/xhigh`; observed runtime is **UNKNOWN**. This is one independent read-only review and targeted closeout, with no nested agents, controller mutation, push, solver or ODE execution. Only these review files were written by the reviewer.

The reviewed payload contains 81 files. Its identity is `7f4f6c8f9bf81eb7ff91c9d5b942788cf9397ccc45f224dab7f0e71ef001e325`: SHA-256 of the compact sorted JSON map from payload-relative paths to byte SHA-256. Critical per-file hashes are recorded in the accompanying JSON. The executable frontier canonical digest is `27b1e5df1ffbe44e31a69772db64138b0c2cc6902c009cef87d4b57cc4f3a508`.

## Findings and closeout

1. **R32-REV-01 — closed.** The newly displayed ellipsoid formula originally used `M_Q^-1` without excluding `Q=0`. The author added `Q≠0, o≥0` and the explicit `Q=0` image `{0}`, `χ=0` treatment in both `QO_COMPARATOR.md` and `PUBLICATION_STRATEGY.md`. I checked the repaired payload. No underlying theorem or numerical witness changed.
2. **R32-REV-02 — author self-detected, independently verified closed.** Three retained `evidence/sources/latest` inputs needed by the imported checker were initially absent. The exact CF4 producer and two R28 result files are now included, all 54 evidence hashes pass, and the checker exits successfully. The frontier inputs bind the updated manifest.

## Preservation and execution

Every original publication-DAG top-level value is semantically identical, including six paper records and all 42 node contracts. Only a separate route pointer was added. All 245 old canonical backlog cards, original topological prefix and old status/execution-lane values are preserved. Nine new cards and nine pending entries were appended. Controller and router files are not changed; the validation copies are byte-identical to base.

The compact output map exactly matches the executable frontier. Seven tasks are independent roots. Both manuscript consumers require the correct exact qualified product; completion or a wrong product cannot open either gate. The handoff preserves active packets, attempts, failures and ultra budgets, uses the existing state at a serialized checkpoint, and distinguishes source delivery from live activation.

## Executed checks

- Focused uptake suite: **7 passed** on the current validation overlay.
- Static preflight: **54 evidence files verified**, seven candidate roots, no state write or live state observation.
- Canonical mirrors synchronized; PR DAG valid with **254 PRs**.
- Own semantic comparison and both exact-product dependency checks passed.
- Imported independent physical checker passed; source inputs and corrected CF4 dimensionless convention are available.
- Own H03 Cholesky/QR calculation from saved means/covariance gives `T=23.39672052266717`, `df=6`, conditional tail `0.0006739334199762943`, cutoff `12.591587243743977`, and unrestricted `η95=1.2885530036501112`. Five discrepancy radii attain `max(0, sqrt(T)−η)^2` as claimed. The block-diagonal statistic remains `8.925712182985695` in the independent reuse checker.

The producer uses the correct fixed-law discrepancy sensitivity and labels its radius as assumed rather than empirically calibrated. The QO figure is a deterministic attained witness, and the shear frontier is conditional on response and error assumptions. Retained results and publication work are not counted as new original42 completions.

## Scope and next action

This review supports the authorized **source integration**. It does not establish publication novelty, original42 acceptance, submission readiness, installation or live activation. No raw catalogue/map or complete historical proof campaign was rerun. The formula-specific prior-art comparison remains an explicit downstream task.

Proceed with source publication, then let the already-running host perform the actual-state preflight and one serialized append at its current checkpoint. Its real launch, acknowledgment, result and independent-review receipts are still required before any task completion claim.
