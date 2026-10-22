# Independent review — finite velocity-jet rest contraction

Requested reviewer runtime: `gpt-6-astra/ultra`. Observed runtime: `UNKNOWN`.
The reviewer was read-only and did not author this candidate.

Verdict: **PASS_SCOPED** for final source SHA-256
`0d696565adc1bac4490426e0d557c1429d3a63a873cf443ebe2b4d0ffac4b684`.

The finite-sum orientation is correct: the conclusion is rewritten as
`c^2 * sum_i u_i * (sum_j D_i_j * u_j)`, exactly matching the supplied
row contraction `hDu`.  The separate scaling result is definitional.

The reviewer verified all source-binding hashes and independently elaborated
the exact source through stdin with appended `#check` commands. It exited zero
under Lean `4.31.0`, core revision
`68218e876d2a38b1985b8590fff244a83c321783`, and mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. Axiom reports contain only
`propext`, `Classical.choice`, and `Quot.sound`; no placeholder or custom axiom
was found.

This is finite real algebra only. It neither supplies a metric, connection, or
manifold nor proves the full theta/shear/vorticity decomposition or full
PORT-CAS-03.
