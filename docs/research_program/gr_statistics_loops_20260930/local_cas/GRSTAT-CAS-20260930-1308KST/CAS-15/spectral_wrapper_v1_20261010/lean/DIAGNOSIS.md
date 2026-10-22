# CAS15 ordered spectral witness: bounded diagnostic

`SpectralWitness.lean` compiles with pinned Lean 4.31.0 / mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` and proves three statements
for every real symmetric 3×3 matrix: `eigenQᵀ * eigenQ = 1`,
`eigenQ * eigenQᵀ = 1`, and `eigenQᵀ * A * eigenQ = diagonal eigenLamb`.
Their `#print axioms` output is exactly `propext`, `Classical.choice`,
`Quot.sound`.

This is not yet the canonical ordered witness required by `FullSynthesis`.
The attempted equality `eigenLamb A hA = orderedSpectrum A hA` is not justified
by this Matrix API. `Matrix.IsHermitian.eigenvalues` is defined by reindexing
`eigenvalues₀` through
`(Fintype.equivOfCardEq (Fintype.card_fin 3)).symm i`.
`Fintype.equivOfCardEq` is a noncomputable choice of an equivalence of equal-cardinality
finite types, not `Equiv.refl (Fin 3)`. The first compiler goal was
`eigenvalues ... ((Fintype.equivOfCardEq ...).symm i) = eigenvalues ... i`;
`fin_cases i <;> rfl` failed at all three indices. An arbitrary reindexing can
permute the eigenvalues, so replacing the goal by definitional equality would
lose the canonical decreasing order.

Next precise proof obligation: construct `Q` from
`(matrixOperator_symmetric A hA).eigenvectorBasis dim3` directly, or prove a
column-permutation bridge from the Hermitian matrix API to this particular
ordered linear-map basis. Then derive the pairwise lower gap from
`orderedSpectrum_antitone` and the positive `orderedGap`; only after that can
the Q/lamb/hgap-free `FullSynthesis` wrapper be composed. No `sorry`, `admit`,
new axiom, arbitrary-permutation premise, or historical adjudication was added.
