# Independent review — P06 endpoint scalar invariant

Requested reviewer runtime: `gpt-6-astra/ultra`; observed runtime: `UNKNOWN`.
The reviewer was read-only and did not author the candidate.

**PASS_SCOPED** for source SHA-256
`6e2ba67718fa3ebb2feb5cce1ee3e5de2f837d9841562e60d394e6a7d2baed83`.
All four frozen input hashes match. The reviewer independently compiled the
exact source with Lean 4.31.0 and mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, exit 0. All audited theorems use
only `propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx` or extra axiom
appears.

The definitions match the implementation orientation: `(1+z)/D-1`, `D*dA`,
and `dL/D`. `0<D` supplies the sole denominator cancellation, while `z` is
unrestricted and hence includes `z=0`. The luminosity statement is
definitionally `rfl`, so it is not a derivation of reciprocity.

The one `unnecessarySeqFocus` linter warning is nonblocking. This result does
not derive `D`, a ray or measure geometry, aberration, reciprocity,
polarization/spin transfer, numerical fidelity, full PORT-CAS-06, or scientific
admission.
