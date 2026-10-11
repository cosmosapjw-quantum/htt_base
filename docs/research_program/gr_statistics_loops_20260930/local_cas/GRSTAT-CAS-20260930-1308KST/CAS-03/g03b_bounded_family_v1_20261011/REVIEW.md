# Independent review — G03-B bounded family

Final verdict: **PASS_SCOPED**, bound to `BoundedFamily.lean` SHA-256
`db171842c0a5eb898e85d706fd647c73509c6a12a3d6f2356b5231bc82c5062f`.
The requested reviewer runtime was `gpt-6-astra/xhigh`; independently observed
runtime remains `UNKNOWN`. The reviewer made no edits.

All five target signatures match the frozen packet without added premises or
weakened conclusions. The covariant boosted block contains both symmetric
off-diagonal entries, and the positive component Frobenius sum is exactly
`epsilon^2 * cosh (2*chi)^2 + b2^2 + b3^2`. Likewise the fixed-observer
vector identity is `|uChi chi|_E^2 = cosh (2*chi)`.

From `0 <= chi <= R`, the proof correctly derives `0 <= R`, applies cosh
monotonicity, and bounds both rapidities `chi` and `0`. Positivity and
`epsilonSeq <= epsilon0` justify squaring the sequence inequality, so
`rateCap` is independent of the sequence index. Positivity of `b2` and `b3`
is not needed for this norm bound and remains a separate premise for kernel
uniqueness.

All norms are positive Euclidean component norms in one fixed observer tetrad.
No Lorentz-invariant norm, invariant physical amplitude, unrestricted
`Q`/vorticity bound, or common spacetime neighbourhood is asserted. The
vector quantities are dimensionless; `epsilon`, `b2`, `b3`, and `rateCap`
have rate units.

The reviewer independently ran the pinned Lean 4.31.0/mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` target with the frozen import
root and no output file. It exited 0, and all five axiom reports contain only
`propext`, `Classical.choice`, and `Quot.sound`. The two
`unnecessarySimpa` warnings are nonblocking.

Packet, source, author return, raw logs, both snapshots, final `.olean`, eight
imported `.olean` files, and recorded dependency-source hashes match. Attempt
1 preserves its elaboration failure and `sorryAx`; attempt 2 uses the valid
transitive bound and removes the failure without changing the statement.

This review does not establish the positive observer-distance lemma, the final
quantified no-uniform-modulus theorem, complete G03-B, historical four-axis
closure, or scientific admission.
