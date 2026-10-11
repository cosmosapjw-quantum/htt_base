# Independent review — G13-E Lean rational counterexample

Reviewer request: `gpt-6-astra/ultra`.  Observed runtime: `UNKNOWN` (no
independent runtime attestation).  The reviewer was read-only and did not
author the candidate.

Verdict: **PASS_SCOPED** for source SHA-256
`28dd93427d6a2377e3c49cf9a205d46bf2d883204cb09c424337bd698b902e91`.

The theorem has precisely the packet's finite scope: it produces one real
root in `(539/500, 1079/1000)` of the displayed cubic and proves the two
displayed strict rational comparisons.  There are no extra hypotheses.

- The IVT orientation is correct: the endpoint values are
  `-1601933/200000` and `56444967/1600000`.
- The denominator is proved positive before cross multiplication.  Independent
  exact rational arithmetic confirmed both shifted positive-coefficient
  expansions, including their positive constant gaps.
- A fresh pinned compile in `/home/cosmosapjw/lean_oracles/viii_oracle` exited
  zero under Lean `4.31.0` and mathlib
  `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.  The axiom audit reports only
  `propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx`.

Nonblocking provenance limitation: the packet records upstream hashes without
paths in this candidate, so the reviewer did not independently bind those
upstream artifacts.  The standalone kernel theorem imports none of them.

Excluded: fixed-prior fibre membership, MaxEnt optimality, FD/BE inversion,
full G13-E, historical four-axis acceptance, and scientific admission.
