# P08-B frozen targets (frozen before any proof attempt, 2026-10-13)

Lean 4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, Lake project
`/home/cosmosapjw/lean_oracles/viii_oracle`. Module `P08EllipsoidImage` in `lean/`.
Imports (unchanged, reused): `G08AWhitening` (sha256 `e62280213d23...6bf045`),
`P08EllipsoidFiber` (P08-A, sha256 `a69fb0ad3f47...06c8ab`).

## Definitions (all exact; Euclidean dot product `⬝ᵥ`)

```
variable {n r m q d : ℕ}
Ell c L          := {x : Fin n → ℝ | ∃ z : Fin r → ℝ, z ⬝ᵥ z ≤ 1 ∧ x = c + L *ᵥ z}
FibreImage c L B P y := (fun x => P *ᵥ x) '' (Ell c L ∩ {x | B *ᵥ x = y})
IsKerONB A N     := Nᵀ * N = 1 ∧ ∀ k, A *ᵥ k = 0 ↔ ∃ u, k = N *ᵥ u
EllImage θ0 s F  := {θ | ∃ u, u ⬝ᵥ u ≤ 1 ∧ θ = θ0 + s • (F *ᵥ u)}
```
with `A = B * L`, `b = y - B *ᵥ c`, `X` satisfying `G08AWhitening.IsMoorePenrose (B * L) X`,
`z0 = X *ᵥ b`, `η = z0 ⬝ᵥ z0`.

## Required targets

* **Q1 (image, interior).** Under `IsMoorePenrose (B*L) X`, compatibility
  `∃ z, (B*L) *ᵥ z = y - B *ᵥ c`, `IsKerONB (B*L) N`, and `η < 1`:
  `FibreImage c L B P y = EllImage (P *ᵥ (c + L *ᵥ z0)) (√(1-η)) (P * L * N)`
  (two-sided set equality over the whole original bounded ellipsoid `K`).
* **Q2 (basis invariance).**
  (a) For any two orthonormal kernel parametrisations `N : Fin r × Fin d`, `N' : Fin r × Fin d'`
  (any `d, d'`), the two Q1 right-hand sides coincide.
  (b) For `R : Matrix (Fin d) (Fin d) ℝ` with `Rᵀ * R = 1`: `IsKerONB A N → IsKerONB A (N * R)`
  and `EllImage θ0 s (F * R) = EllImage θ0 s F` for all `θ0, s, F`.
* **Q3 (boundary return).** Under MP and compatibility: `η = 1 → FibreImage = {P *ᵥ (c + L *ᵥ z0)}`;
  `1 < η → FibreImage = ∅`; and without MP, incompatibility `¬ ∃ z, (B*L) *ᵥ z = y - B *ᵥ c`
  gives `FibreImage = ∅`. The `η = 1` and `η > 1` branches reuse P08-A `fiber_branches`.
* **Q4 (existence of N).** For every `A : Matrix (Fin m) (Fin r) ℝ` there exist `d` and
  `N : Matrix (Fin r) (Fin d) ℝ` with `IsKerONB A N`. Plus the unconditional corollary: for all
  `c L B P y` with compatibility and `η < 1` (with `X` from `G08AWhitening.moorePenrose_exists`)
  there exist `d, N` realising Q1.

## Stretch targets (attempted only after Q1-Q4; failure does not block Q1-Q4)

* **Q1' (closed form up to boundary).** Q1 with `η ≤ 1` in place of `η < 1`.
* **Q5a (support function).** For `s ≥ 0`, every `θ ∈ EllImage θ0 s F` satisfies
  `w ⬝ᵥ θ ≤ w ⬝ᵥ θ0 + s * √((Fᵀ *ᵥ w) ⬝ᵥ (Fᵀ *ᵥ w))`, and some `θ ∈ EllImage θ0 s F` attains it
  (mirrors `EllipsoidFiberImage.support`, `typefree_fibers.py:126-133`).
* **Q5b (gauge-boundary link).** `η` is the squared quotient gauge: for compatible data,
  `η ≤ z ⬝ᵥ z` for every solution of `(B*L) z = b` with equality attained at `z0`; and
  `FibreImage c L B P y` is nonempty iff compatibility holds and `η ≤ 1`.

## Forbidden

`sorry`, `admit`, `sorryAx`, `native_decide`, new `axiom`s, hypotheses that assume a conclusion,
floating cutoffs/tolerances. Accepted axioms: `propext`, `Classical.choice`, `Quot.sound`.

## Out of scope (not claimed)

numerical SVD link (that `_solve_range` computes `X`, `N` to any accuracy), physical units,
full PORT-CAS-08, scientific admission; `rational_polytope_fiber_support` (not part of this card's
minimum targets).
