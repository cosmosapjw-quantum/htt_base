# Report A R2C local independent audit

Date: `2026-09-03`  
Audited draft SHA-256: `6facb97c9986cb87d6012fd80d5999eba1cbe38ef99c7c8cf74fa4e00b550d59`  
Audited length: `955` lines

## Verdict

```text
PASS_R2C_LOCAL_INDEPENDENT_DRAFT_AUDIT_WITH_EXECUTION_AND_CITATION_BLOCKERS
```

No P0 mathematical, statistical, scope, or claim-firewall defect was found in
the regenerated R2 draft. This is a local independent audit, not an exact-head
GitHub execution receipt and not publication approval.

## Exact checks

- Q/O quotient dimension: `5 + 7 - 3 = 9`.
- An exact STF3 witness has trace residual `(0,0,0)`.
- Its contraction vector is `v=(4,1,-5)`.
- The corresponding Krylov matrix has determinant `400` and rank `3`.
- The packet-image identity `O:Q = K e_0` has exact residual `(0,0,0)`.
- Tie-to-coordinate-2 selection has maximum size violation `1/4`.
- Tie-to-coordinate-1 selection has maximum size violation `1/4`.
- The symmetric pooled rule has zero maximum violation.
- Exactly 29 canonical claim IDs occur in the claim map.
- All 17 used external citation keys belong to the frozen citation registry.
- Code fences and display-math delimiters are balanced.

The fresh Wolfram replay was attempted twice but the evaluator returned an
upstream HTTP 502. The exact checks above were therefore executed with SymPy;
they do not replace earlier durable Wolfram receipts.

## Findings at the audited snapshot

### P0

None.

### P1

1. PR #450, PR #451, and the R2 exact-head workflows remained
   `PRESTART_NO_EXECUTION`; no hosted runner step began.
2. The MES coefficients and premise matrix required final page/equation-level
   comparison against the primary sources. This item is closed by the
   subsequent R2D primary-source audit.

### P2

1. The five non-axial continuum ranks remain high-precision numerical rather
   than interval-certified.
2. The novelty status of the repository-specific Q/O Krylov packet remains
   unresolved; the fresh SciSpace search found adjacent pure-octupole,
   vector-set, and general invariant-basis literature, but no direct match.

## Claim boundary

No observation-bearing result, current scalar MES rank, corrected Planck rank,
finite-HEALPix no-go theorem, empirical beta, global-tilt identification,
Bianchi-family attribution, native BASS result, merge, or publication approval
is introduced.
