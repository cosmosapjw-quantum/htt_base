# CAS15 spectral-wrapper successor

## Completed Lean bridge

`CAS15WrapperIntegration.full_symmetric_synthesis_from_ordered_gap` is a
kernel-checked wrapper around the existing conditional CAS15 full synthesis.
For real symmetric `M` and `Mhat`, it constructs the orthogonal diagonalizer,
the canonically decreasing eigenvalue enumeration, and the pairwise gap witness
from `Mhat`.  The caller supplies only the positive `delta` and the lower bound
of `delta` by the canonical ordered adjacent gap.

The wrapper preserves the two existing conclusions: the least-squares
perturbation bound and the ordered-gap perturbation bound.  It does not prove
that an observed gap is positive or that a least-squares minimizer exists.

## Validation

- Pinned Lean 4.31.0 with mathlib commit
  `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.
- A fresh independent review compiled the minimal eight-module existing CAS15
  dependency chain plus all three successor Lean modules.  The final wrapper
  and imported theorem axiom audit exited successfully.
- The wrapper theorem and all new supporting theorems depend only on
  `propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx` is present.

## Scope and status

This successor closes only the remaining Lean wrapper from symmetric input to
the existing conditional CAS15 synthesis.  The historical CAS15-C03
`CAS_CONFLICT` is retained, and scientific admission remains `HOLD`.  This is
not historical four-axis acceptance, nor does it address CAS16-C01/C02,
collision normalization, spin quadrature, DP06, or a scientific claim.
