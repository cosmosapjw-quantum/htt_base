# CAS17-C01 Lean successor

`CAS17C01.c01_gram_tilt_bridge` is kernel-checked for the frozen finite C01
component: a positive Lorentz Gram matrix of three spacelike four-vectors gives
the epsilon-cofactor wedge orthogonality and norm sign, then the constructed
future unit normal, `gamma >= 1`, projected spatial vector, and
`betaSq = 1 - gamma^-2` with `0 <= betaSq < 1`.

The proof uses Lean 4.31.0 and mathlib revision
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` through the existing local oracle
fallback. The frozen `formal_mathlib` package/build symlinks are broken, so
this fallback is a successor compilation path only; it does not repair or pass
the historical environment seal. The theorem has only standard Lean axioms.

Scope is C01 only. It does not prove C02--C04, coordinate-general tensor
formalization, historical four-axis acceptance, orbit identification, or a
scientific claim. Scientific admission remains `HOLD`.
