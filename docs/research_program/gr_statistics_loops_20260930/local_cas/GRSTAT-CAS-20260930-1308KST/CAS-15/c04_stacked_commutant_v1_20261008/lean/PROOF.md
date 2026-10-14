# CAS-15 C04 Lean certificate

The admitted finite real space is `Fin 3 → ℝ`. `skew w` is the 3 × 3
cross-product matrix, and `skew_represents_all` proves that every real skew
3 × 3 matrix has this form. `E₀`, `E₁`, `E₂` divide the three coordinate skew
matrices by `√2`; `orthonormal_skew_basis` proves their orthonormality for the
standard Frobenius product.

For any finite stack of real matrices, `response` has entries
`[M_a,E_i]_{pq}` and `gram = responseᵀ * response`.
`gram_frobenius` proves the exact component sum, while `gram_kernel_iff` and
`gram_kernel_all_skew` identify the Gram kernel with all skew matrices
commuting with every channel. The proof uses mathlib's real ordered-field theorem for the kernel
of `AᵀA`, not a numerical sample.

For `M(n,α,β)=αI+βnnᵀ`, `axis_comm_apply` computes the commutator exactly.
Under `n·n=1` and `β≠0`, `axis_comm_zero_iff_cross_zero` gives
`[M,skew w]=0 ↔ w×n=0`, and `cross_zero_iff_span` makes this the line
`ℝ∙n`. `one_axis_rank_two` follows from rank–nullity. For two linearly
independent unit axes, `two_cross_zero` proves the common line intersection
is zero. `pair_gram_posDef_rank_three` uses injectivity of the response to
prove positive definiteness and rank three. `isotropic_response_zero` and
`parallel_pair_kernel_dimension_one` are the declared boundary controls.

`Main.lean` ends with `#print axioms` for eight principal theorems. The
observed output contains only `propext`, `Classical.choice`, and `Quot.sound`.
The finite component proves no sphere integration by parts, photon transport,
measurement contract, or scientific admission.

The intermediate editing errors were observed in this Codex tool transcript.
Their full stdout/stderr was not persisted during development. The final
bounded engine execution is preserved in `lean_compile.stdout.log` and
`lean_compile.stderr.log`, with exact argv and exit in `result.json`.
