# Independent Lean/mathlib review: D1 and D3

## Scope and inputs

This review used the sealed D1 and D3 contracts, the depth obligations, the
two current Lean sources, and the assigned `verify_lean.py` wrapper.  The
assignment context version and every sealed input SHA-256 matched before
review.  This is a source and compiler review only; it does not adjudicate
other CAS axes or elevate `FORMAL_DEPTH`.

## Compiler evidence

The required wrapper compiled `Recursion.lean` first and `Covariance.lean`
second against mathlib commit `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`
and the repository's `leanprover/lean4:v4.31.0` toolchain.  Each exit code was
zero.  Raw compiler stdout was inspected in the two `execution.json` files,
not inferred from MLflow status.  It reports only linter warnings for
`Covariance.lean` and the following printed dependencies:

- the two D3 inverse theorems and `pathEquiv` depend on `propext`; the real
  specialization additionally lists `Classical.choice` and `Quot.sound`;
- all four D1 lemmas list only `propext`, `Classical.choice`, and `Quot.sound`.

No `sorry`, `admit`, `unsafe`, or target-assuming axiom occurs in either
source.  `AddSubCancel` is an explicit theorem premise, not an admitted target
theorem.

## D1 verdict

`mean_linear_map` and `covariance_linear_map` prove the coordinatewise
finite-dimensional identities for arbitrary `Fintype` source and target index
types and arbitrary real `H`, assuming coordinatewise `MemLp 2`.  The latter
is sufficient for the integrability used by the covariance expansion.  No
independence or diagonal-covariance premise appears.  The displayed covariance
is the full coordinate covariance matrix.

`covariance_pullback_psd` proves real PSD preservation under arbitrary `H` by
the library's conjugate-transpose pullback theorem, with semidefinite (not
definite) input.  `all_cross_step_blocks` proves the full four-term residual
cross block

`C11 - C10 L^T - K C01 + K C00 L^T`

for independent arbitrary finite index types, including rectangular K and L.
Together, the generic linear-map theorem covers a concatenated finite block
operator H; the cross-block lemma checks the D1 sign/order expansion.  D1's
finite-dimensional algebra/probability lemmas are therefore compiled and
faithful to their stated D1 sub-obligations.  This does not prove D2 or D4.

## D3 verdict

`DepChain` and `DepResidual` encode arbitrary finite heterogeneous paths.
`residualsDependent_reconstructDependent` and
`reconstructDependent_residualsDependent` establish the two inverse
compositions for every natural finite depth under the stated add/sub
cancellation laws.  `pathEquiv` packages the two-sided equivalence, and
`realBlockPathEquiv` specializes it to real vectors with arbitrary `Fin (d j)`
dimensions and arbitrary rectangular or singular real matrices K.  Thus the
deterministic inverse-recursion portion of D3 is present.

The source does not define a flattened block matrix for T, prove its unit
determinant, characterize `ker H`, or prove H surjective in that matrix form.
It also does not formalize preservation of the transformed joint mean,
covariance, support, or initial-residual cross terms for a singular law.  The
source comments state this limitation explicitly.  Therefore it cannot
discharge D3's determinant/kernel/surjectivity/full-law obligations, and it
cannot support `FORMAL_DEPTH` admission.

## D2/D4 boundary and source delta

Neither source asserts a Gaussian pushforward/support/chi-square result (D2)
or full-past singular conditional-innovation result (D4).  The governing
obligations retain both as missing.  The two Lean source paths are untracked
additions relative to base `9ca515ad891e59eff72eb06dfef05f06131bfb2c` and are
also absent at the cited prior commit `a6a4827f`; there is no prior in-tree
version of either path to compare.  Their new-source comments accurately state
the retained D3 and D2/D4 boundaries.

## Admission conclusion

The compiler receipts support the scoped D1 lemmas and the D3 two-sided
recursion equivalence only.  They are not a four-axis result and do not
establish the complete D3, D2, D4, or `FORMAL_DEPTH` contracts.
