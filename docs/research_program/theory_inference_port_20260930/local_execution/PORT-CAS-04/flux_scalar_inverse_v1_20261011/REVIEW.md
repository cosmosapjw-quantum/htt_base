# Independent review — P04 scalar flux inverse

Requested reviewer runtime: `gpt-6-astra/ultra`. Observed runtime: `UNKNOWN`.
The reviewer was read-only and did not author the candidate.

## Verdict

**PASS_SCOPED.** Candidate SHA-256 is
`79f94942cc493e1dd798fe1e7e8c1af60b022b2d281de0cf8c839545568b6f04`.
All four frozen input hashes match `DELEGATION_PACKET.json` (packet SHA-256
`076409b3e16fe57f9d164cc17379cb780c201708e71548ab805601ef6399abcb`).

The reviewer independently compiled the exact source with Lean 4.31.0 and
mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, exit 0. The checked type is

```lean
forall b : R, 0 <= b -> b < 1 ->
  betaOfRatio (b / (1 - b ^ 2)) = b
```

where `betaOfRatio r = 2*r/(1 + sqrt(1 + 4*r^2))`. The positivity proof covers
the denominator and both square-root-side conditions. No cancellation divides
by `b`, so `b = 0` is included. All three audited lemmas depend only on
`propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx`, added axiom, or
numeric square-root approximation was found.

## Scope boundary

This is only the real scalar inverse on the declared single-fluid branch after
`r = |J|/w`. It does not prove the vector direction, perfect-fluid projection,
Codazzi identity or sign, multifluid converse, floating-point stability, full
PORT-CAS-04, historical four-axis status, or scientific admission.
