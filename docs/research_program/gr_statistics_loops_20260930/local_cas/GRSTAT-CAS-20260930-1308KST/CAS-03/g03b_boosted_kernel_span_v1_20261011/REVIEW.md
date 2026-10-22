# Independent review — G03-B boosted kernel span

Verdict: **PASS_SCOPED**, bound to `BoostedKernelSpan.lean` SHA-256
`b86362f462c07f4e912355bbdc905eb445f355234583fabef2864cd03c372a96`.

The requested reviewer setting was `gpt-6-astra/ultra`; independently observed
model and effort remain `UNKNOWN/UNKNOWN`. The reviewer made no edits.

The reviewed theorem has exactly the required positivity assumptions on
`epsilon`, `b2`, and `b3`, and proves that the right kernel of the displayed
boosted covariant matrix consists precisely of the real scalar multiples of
`uChi chi`. The coordinate signs agree with the source's `(-+++)` convention.
The forward direction uses rows 1, 2, and 3, positivity of the three weights,
and positivity of `cosh`; the reverse direction uses linearity and the exact
imported kernel-membership theorem.

All stipulated source hashes matched. `lean --deps` resolved the import to the
isolated `raw/source_root/BoostedKernelMembership.olean`. An independent
read-only compilation on Lean 4.31.0 and mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` exited 0 and reported exactly
`propext`, `Classical.choice`, and `Quot.sound`. No `sorry`, `admit`, custom
axiom, or assumed conclusion occurs.

The preserved failures are correctly separated from accepted evidence:
package-root binding, missing dependency, and proof-tactic/type-shape errors.
The failed attempt's `sorryAx` output is not accepted as final evidence.

This review does **not** establish future-unit uniqueness, an observable norm
countersequence, uniform-modulus negation, complete G03-B, historical four-axis
closure, or scientific admission. Scientific admission remains `HOLD`.
