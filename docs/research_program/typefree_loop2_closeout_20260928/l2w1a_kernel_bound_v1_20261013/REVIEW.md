# L2-W1-A — independent review

Reviewer: fresh-context read-only subagent; requested gpt-6-astra/ultra (unavailable), observed claude-opus-5-5. Not the author.

**Verdict: PASS_WITH_NOTES. No blocking finding.**

| Check | Result |
|---|---|
| `kernel_bound_iff` vs ERRATA_F1_W1 / TF-W1-KERNEL-DOMAIN | PASS. Correct inclusion direction ker B ∩ V ⊆ ker P, C ≥ 0 real, V a submodule of finite-dimensional E, Y and Z arbitrary normed. More general than the errata (E=V, V=⊤ recovers it). |
| `affine_kernel_bound` | PASS. Bounds differences in x0+V; correctly does not claim ‖Px‖ ≤ C‖Bx‖ on the affine set. |
| `bot_branch`, `zero_B_branch` | PASS |
| `bounded_set_negative_control` | PASS. P(K) is bounded and kernel inclusion fails (v=1); the reviewer's probe also shows the uniform bound on K itself fails. |
| Hidden hypotheses / vacuity | PASS. Probes on ℝ² confirm both directions have content. |
| Source sha256 `5556288e5629bda32d7132841992935408690ecf42154963869558be96ab9f55`, raw receipts | PASS. compile_01 exit 1 (different source, kept), compile_02 exit 0, compile_03 audit exit 0; all hashes match AUTHOR_RETURN. |
| Axioms / forbidden tokens | PASS. Only propext, Classical.choice, Quot.sound; no sorry or escape hatch. |
| Independent recompile outside the repo | PASS. Same warning and identical audit output. |

## Notes (non-blocking)

- **N1.** The affine theorem is one-directional (the converse is immediate from v = x − y), and the base-point decomposition Px = Px0 + P(x−x0) is not separately stated. Neither is required.
- **N2.** Zero-map coverage is B = 0; P = 0 is trivial and has no separate theorem.
- **N3.** The negative control does not formalize the fibre analysis P(K ∩ B⁻¹{y}), singleton fibres or calibration.
- **N4.** `bot_branch` carries an unused `[FiniteDimensional ℝ E]` instance (disclosed).
- **N5.** Olean hashes depend on the build path; the source sha256 is the portable receipt.
- **N6.** The author's self-grade is not independent review.

## Not proved

Bounded or curved feasible-set identification (fibre-image boundedness, diameter, singleton fibres); confidence/coverage calibration; mapping to R2 coefficients or Q/F/Π/G_F; infinite-dimensional E; scientific admission (HOLD).
