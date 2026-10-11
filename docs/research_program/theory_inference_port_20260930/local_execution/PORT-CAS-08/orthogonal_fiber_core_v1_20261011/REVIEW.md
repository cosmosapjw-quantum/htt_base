# Independent review — P08 orthogonal fiber core

Requested reviewer runtime: `gpt-6-astra/ultra`; observed runtime: `UNKNOWN`.
The reviewer was read-only and did not author the candidate.

**PASS_SCOPED** for SHA-256
`91a1a9515232ae90deaacced50f96ff44c93d8c6ebea9564c41a19d91e75069b`.
The frozen input references, delegation packet, and direct Mathlib source and
compiled-root hashes agree with the author receipt.  Independent execution of
the prescribed `lake env lean …/OrthogonalFiberCore.lean` command exited 0
under Lean 4.31.0 and mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.  Each audited theorem depends
only on `propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx` is
reported.

All sums range over `Fin n`, and exact real orthogonality cancels the cross
term.  The lower bound follows from nonnegative squares, and equality forces
the entire function `k` to vanish, including `n = 0`.  No positivity condition
on the dimension was smuggled in.

This bridge does not prove that a numerical SVD output is exactly orthogonal,
construct a Moore--Penrose inverse, establish range feasibility or kernel
parametrization, or resolve any eta branch.  It therefore does not close full
PORT-CAS-08, historical four-axis acceptance, or scientific admission.
