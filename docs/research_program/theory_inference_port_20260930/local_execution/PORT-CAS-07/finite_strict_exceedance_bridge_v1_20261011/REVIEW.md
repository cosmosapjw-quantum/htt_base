# Independent review — P07 finite strict exceedance

Requested reviewer runtime: `gpt-6-astra/ultra`; observed runtime: `UNKNOWN`.
The reviewer was read-only and did not author the candidate.

**PASS_SCOPED** for SHA-256
`5999191e9c4af08b1595de883aa91db07b3875ca04e0cc839ec437aada166c6e`.
All five frozen-input hashes and the candidate identity matched before and after
independent exact-source compilation. Lean 4.31.0 with mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` exited 0. Both audited theorems
depend only on `propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx`.

`K` uses strictly `t < x`, while `U` uses `v i = none`; equality is explicitly
excluded and the sets are proved disjoint. The theorem exposes nonnegative
weights and `K subset E subset K union U`, then uses finite-sum monotonicity and
disjoint union. Empty finite types/events and zero weights remain valid. No
normalization or `none`-as-false conversion is introduced.

It does not establish floating-point behavior or the implementation's
`min(1,p+q)` cap, arbitrary measures, completion attainability, sharpness, full
PORT-CAS-07, historical four-axis status, or scientific admission.
