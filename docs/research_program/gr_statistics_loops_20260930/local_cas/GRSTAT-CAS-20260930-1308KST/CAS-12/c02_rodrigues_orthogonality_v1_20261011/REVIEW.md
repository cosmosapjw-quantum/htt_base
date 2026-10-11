# Independent review — G12-B Rodrigues sublemma

Verdict: **PASS_SCOPED**.

Requested reviewer setting was `gpt-6-astra/ultra`; observed model and effort are `UNKNOWN`. The reviewer was read-only and did not rerun Lean.

The final theorem quantifies over every natural `n`, every real polynomial `p`, and the explicit hypothesis `p.natDegree < n`. It concludes the actual Lebesgue integral restricted to `Set.Icc 0 1`. The proof uses the mapped Mathlib Rodrigues identity, endpoint derivative divisibility, repeated integration by parts, derivative-degree annihilation, and nonzero-factorial cancellation. The reviewer found no assumed orthogonality conclusion, finite cutoff, `sorry`, or custom axiom.

Source and raw audit bindings reviewed: `AllDegree.lean` and `raw/compile_03_source.lean` both have SHA-256 `22f23f175ffc21347ffeb77b0f104c3ed4d4fd9cb14ddc4eaaa0c3d4ade43625`; the accepted audit reports only `propext`, `Classical.choice`, and `Quot.sound`.

This does **not** close G12-B/CAS12-C02: the separate affine coordinate transfer and normalized all-natural Thomson moments on `[-1,1]` remain open. No four-axis or scientific admission follows.
