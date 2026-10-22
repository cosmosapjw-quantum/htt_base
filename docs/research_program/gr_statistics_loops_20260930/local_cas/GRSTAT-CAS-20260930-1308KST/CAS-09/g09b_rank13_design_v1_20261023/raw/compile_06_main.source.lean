import Mathlib
import G09ADefinitions

/-!
# G09-B — general rank identity and two-radius 9+4 unisolvence (CAS-09 C01)

Source: `statistics/NATIVE_INFERENCE_THEOREMS.md`
(sha256 e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322), §6, l.124–157.
Reuses the reviewed G09-A module `G09ADefinitions` UNCHANGED (definitions `E4`, `E9`, `Dmap`,
`Xmap`, `twoRadiusDir`, `twoRadiusR`, `liftLin`, witness `dirStar`, `σStar`).

New here:
1. general dimension formula for subspaces and for column concatenation of matrices
   (additive, truncated-ℕ-subtraction and ℤ forms);
2. explicit matrices `E4mat`, `E9mat`, `Dmat`, `Xmat = [E4, D E9]` and the identification of
   their column spaces with the G09-A linear-map ranges, and of col X with col E4 ⊔ col (D E9);
3. exact two-radius coefficient-kernel elimination (an iff, no rank hypothesis on E4);
4. kernel = 0 / matrix rank 13 from the source's nonzero determinants (9×9 `E9` block,
   4×4 repeated `E4` block) and radius hypotheses `R1 > 0`, `R2 > 0`, `R1 ≠ R2`;
   equivalence of those determinant hypotheses with unisolvency / rank 4 / rank 9.

Claim ceiling: finite exact linear algebra only.  Scientific admission: HOLD.
-/

namespace G09B

open G09A
open scoped Matrix

/-! ## Step 1 — general dimension formula -/

section General

variable {K : Type*} [Field K]

/-- `dim(U+W) + dim(U∩W) = dim U + dim W` (Mathlib `Submodule.finrank_sup_add_finrank_inf_eq`). -/
theorem dim_sup_add_dim_inf {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V)
    [FiniteDimensional K U] [FiniteDimensional K W] :
    Module.finrank K ↥(U ⊔ W) + Module.finrank K ↥(U ⊓ W) =
      Module.finrank K ↥U + Module.finrank K ↥W :=
  Submodule.finrank_sup_add_finrank_inf_eq U W

theorem dim_inf_le_left {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V)
    [FiniteDimensional K U] :
    Module.finrank K ↥(U ⊓ W) ≤ Module.finrank K ↥U :=
  Submodule.finrank_mono inf_le_left

theorem dim_inf_le_right {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V)
    [FiniteDimensional K W] :
    Module.finrank K ↥(U ⊓ W) ≤ Module.finrank K ↥W :=
  Submodule.finrank_mono inf_le_right

/-- Subtraction form in `ℕ`; the truncated subtraction is exact here because
`dim(U∩W) ≤ dim U + dim W` (indeed `≤ dim U`). -/
theorem dim_sup_eq_sub {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V)
    [FiniteDimensional K U] [FiniteDimensional K W] :
    Module.finrank K ↥(U ⊔ W) =
      Module.finrank K ↥U + Module.finrank K ↥W - Module.finrank K ↥(U ⊓ W) := by
  have := dim_sup_add_dim_inf U W
  omega

/-- The same identity in `ℤ` (no truncation issue at all). -/
theorem dim_sup_eq_sub_int {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V)
    [FiniteDimensional K U] [FiniteDimensional K W] :
    (Module.finrank K ↥(U ⊔ W) : ℤ) =
      Module.finrank K ↥U + Module.finrank K ↥W - Module.finrank K ↥(U ⊓ W) := by
  have := dim_sup_add_dim_inf U W
  omega

/-- Two linear maps with the same image, witnessed by explicit coordinate transfers. -/
theorem range_eq_of_transfer {M₁ M₂ W : Type*} [AddCommGroup M₁] [Module K M₁]
    [AddCommGroup M₂] [Module K M₂] [AddCommGroup W] [Module K W]
    (A : M₁ →ₗ[K] W) (B : M₂ →ₗ[K] W) (f : M₁ → M₂) (g : M₂ → M₁)
    (hf : ∀ x, A x = B (f x)) (hg : ∀ y, B y = A (g y)) :
    LinearMap.range A = LinearMap.range B := by
  apply le_antisymm
  · rintro _ ⟨x, rfl⟩; exact ⟨f x, (hf x).symm⟩
  · rintro _ ⟨y, rfl⟩; exact ⟨g y, (hg y).symm⟩

variable {m n₁ n₂ : Type*} [Fintype m] [Fintype n₁] [Fintype n₂]

/-- Column space of a column concatenation is the subspace sum. -/
theorem range_fromCols (A : Matrix m n₁ K) (B : Matrix m n₂ K) :
    LinearMap.range (Matrix.fromCols A B).mulVecLin =
      LinearMap.range A.mulVecLin ⊔ LinearMap.range B.mulVecLin := by
  rw [← LinearMap.range_coprod]
  apply range_eq_of_transfer _ _ (fun v => (v ∘ Sum.inl, v ∘ Sum.inr))
    (fun p => Sum.elim p.1 p.2)
  · intro v; simp [Matrix.mulVecLin_apply]
  · intro p
    simp only [LinearMap.coprod_apply, Matrix.mulVecLin_apply]
    rw [Matrix.fromCols_mulVec_sumElim]

/-- Rank of a concatenation: `rank[A,B] + dim(col A ∩ col B) = rank A + rank B`. -/
theorem rank_fromCols_add (A : Matrix m n₁ K) (B : Matrix m n₂ K) :
    (Matrix.fromCols A B).rank +
        Module.finrank K
          ↥(LinearMap.range A.mulVecLin ⊓ LinearMap.range B.mulVecLin) =
      A.rank + B.rank := by
  unfold Matrix.rank
  rw [range_fromCols]
  exact Submodule.finrank_sup_add_finrank_inf_eq _ _

/-- Subtraction form (`ℕ`, exact since the intersection is no larger than either part). -/
theorem rank_fromCols_eq_sub (A : Matrix m n₁ K) (B : Matrix m n₂ K) :
    (Matrix.fromCols A B).rank =
      A.rank + B.rank -
        Module.finrank K ↥(LinearMap.range A.mulVecLin ⊓ LinearMap.range B.mulVecLin) := by
  have := rank_fromCols_add A B
  omega

end General

/-! ## Step 2 — explicit matrices and design-range identification -/

/-- Coordinates of `IPar` (columns of `E4`: `1, n0, n1, n2`). -/
def icoord (a : IPar) : Fin 4 → ℝ := ![a.1, a.2 0, a.2 1, a.2 2]

def idecode (v : Fin 4 → ℝ) : IPar := (v 0, ![v 1, v 2, v 3])

/-- Coordinates of `HPar` in the basis
`1, n0, n1, n2, n0²−n2², 2n0n1, 2n0n2, n1²−n2², 2n1n2` (STF coordinates of G09-A). -/
def hcoord (h : HPar) : Fin 9 → ℝ :=
  ![h.1, h.2.1 0, h.2.1 1, h.2.1 2, h.2.2 0, h.2.2 1, h.2.2 2, h.2.2 3, h.2.2 4]

def hdecode (v : Fin 9 → ℝ) : HPar := (v 0, ![v 1, v 2, v 3], ![v 4, v 5, v 6, v 7, v 8])

theorem idecode_icoord (a : IPar) : idecode (icoord a) = a := by
  obtain ⟨a0, a⟩ := a
  refine Prod.ext rfl ?_
  funext k; fin_cases k <;> rfl

theorem icoord_idecode (v : Fin 4 → ℝ) : icoord (idecode v) = v := by
  funext k; fin_cases k <;> rfl

theorem hdecode_hcoord (h : HPar) : hdecode (hcoord h) = h := by
  obtain ⟨h0, h1, q⟩ := h
  refine Prod.ext rfl (Prod.ext ?_ ?_)
  · funext k; fin_cases k <;> rfl
  · funext k; fin_cases k <;> rfl

theorem hcoord_hdecode (v : Fin 9 → ℝ) : hcoord (hdecode v) = v := by
  funext k; fin_cases k <;> rfl

section Matrices

variable {ι : Type*} [Fintype ι]

/-- `E4` matrix: rows `(1, n_iᵀ)`. -/
def E4mat (dir : ι → V3) : Matrix ι (Fin 4) ℝ :=
  Matrix.of fun i => ![1, dir i 0, dir i 1, dir i 2]

/-- `E9` matrix: rows `(1, n, n0²−n2², 2n0n1, 2n0n2, n1²−n2², 2n1n2)`. -/
def E9mat (dir : ι → V3) : Matrix ι (Fin 9) ℝ :=
  Matrix.of fun i => ![1, dir i 0, dir i 1, dir i 2, dir i 0 ^ 2 - dir i 2 ^ 2,
    2 * dir i 0 * dir i 1, 2 * dir i 0 * dir i 2, dir i 1 ^ 2 - dir i 2 ^ 2,
    2 * dir i 1 * dir i 2]

/-- `D = diag(r_i / c)`. -/
noncomputable def Dmat [DecidableEq ι] (r : ι → ℝ) (c : ℝ) : Matrix ι ι ℝ :=
  Matrix.diagonal fun i => r i / c

/-- `X = [E4, D E9]` (NATIVE (10)), 13 columns. -/
noncomputable def Xmat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) :
    Matrix ι (Fin 4 ⊕ Fin 9) ℝ :=
  Matrix.fromCols (E4mat dir) (Dmat r c * E9mat dir)

/-- The `E9` basis contains the degree ≤ 1 basis: its first four columns are `E4`. -/
theorem E9mat_first_cols (dir : ι → V3) (i : ι) (k : Fin 4) :
    E9mat dir i (Fin.castLE (by norm_num) k) = E4mat dir i k := by
  fin_cases k <;> rfl

theorem E4mat_mulVec (dir : ι → V3) (v : Fin 4 → ℝ) :
    E4mat dir *ᵥ v = E4 dir (idecode v) := by
  funext i
  simp [Matrix.mulVec, dotProduct, Fin.sum_univ_four, E4mat, E4, ipoly, dot3, idecode]
  ring

theorem E9mat_mulVec (dir : ι → V3) (v : Fin 9 → ℝ) :
    E9mat dir *ᵥ v = E9 dir (hdecode v) := by
  funext i
  simp [Matrix.mulVec, dotProduct, Fin.sum_univ_succ, E9mat, E9, Hval, quad, dot3, hdecode]
  ring

theorem E4_eq_mulVec (dir : ι → V3) (a : IPar) : E4 dir a = E4mat dir *ᵥ icoord a := by
  rw [E4mat_mulVec, idecode_icoord]

theorem E9_eq_mulVec (dir : ι → V3) (h : HPar) : E9 dir h = E9mat dir *ᵥ hcoord h := by
  rw [E9mat_mulVec, hdecode_hcoord]

theorem Dmat_mulVec [DecidableEq ι] (r : ι → ℝ) (c : ℝ) (v : ι → ℝ) :
    Dmat r c *ᵥ v = Dmap r c v := by
  funext i
  rw [Dmat, Matrix.mulVec_diagonal]
  simp [Dmap]

theorem DE9mat_mulVec [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (v : Fin 9 → ℝ) :
    (Dmat r c * E9mat dir) *ᵥ v = (Dmap r c).comp (E9 dir) (hdecode v) := by
  rw [← Matrix.mulVec_mulVec, E9mat_mulVec, Dmat_mulVec, LinearMap.comp_apply]

theorem Xmat_mulVec [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ)
    (v : Fin 4 ⊕ Fin 9 → ℝ) :
    Xmat dir r c *ᵥ v = Xmap dir r c (idecode (v ∘ Sum.inl), hdecode (v ∘ Sum.inr)) := by
  rw [Xmat, Matrix.fromCols_mulVec, E4mat_mulVec, DE9mat_mulVec, Xmap,
    LinearMap.coprod_apply]

theorem Xmap_eq_mulVec [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (a : IPar)
    (h : HPar) :
    Xmap dir r c (a, h) = Xmat dir r c *ᵥ Sum.elim (icoord a) (hcoord h) := by
  rw [Xmat_mulVec]
  simp only [Sum.elim_comp_inl, Sum.elim_comp_inr, idecode_icoord, hdecode_hcoord]

theorem range_E4mat (dir : ι → V3) :
    LinearMap.range (E4mat dir).mulVecLin = LinearMap.range (E4 dir) :=
  range_eq_of_transfer _ _ idecode icoord
    (fun v => by rw [Matrix.mulVecLin_apply, E4mat_mulVec])
    (fun a => by rw [Matrix.mulVecLin_apply, E4_eq_mulVec])

theorem range_E9mat (dir : ι → V3) :
    LinearMap.range (E9mat dir).mulVecLin = LinearMap.range (E9 dir) :=
  range_eq_of_transfer _ _ hdecode hcoord
    (fun v => by rw [Matrix.mulVecLin_apply, E9mat_mulVec])
    (fun h => by rw [Matrix.mulVecLin_apply, E9_eq_mulVec])

theorem range_DE9mat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) :
    LinearMap.range (Dmat r c * E9mat dir).mulVecLin =
      LinearMap.range ((Dmap r c).comp (E9 dir)) :=
  range_eq_of_transfer _ _ hdecode hcoord
    (fun v => by rw [Matrix.mulVecLin_apply, DE9mat_mulVec])
    (fun h => by
      rw [Matrix.mulVecLin_apply, DE9mat_mulVec, hdecode_hcoord])

theorem range_Xmat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) :
    LinearMap.range (Xmat dir r c).mulVecLin = LinearMap.range (Xmap dir r c) :=
  range_eq_of_transfer _ _ (fun v => (idecode (v ∘ Sum.inl), hdecode (v ∘ Sum.inr)))
    (fun p => Sum.elim (icoord p.1) (hcoord p.2))
    (fun v => by rw [Matrix.mulVecLin_apply, Xmat_mulVec])
    (fun p => by rw [Matrix.mulVecLin_apply, ← Xmap_eq_mulVec])

/-- Design-range identification (G09-A maps): `col X = col E4 ⊔ col (D E9)`. -/
theorem range_Xmap_eq_sup (dir : ι → V3) (r : ι → ℝ) (c : ℝ) :
    LinearMap.range (Xmap dir r c) =
      LinearMap.range (E4 dir) ⊔ LinearMap.range ((Dmap r c).comp (E9 dir)) :=
  LinearMap.range_coprod _ _

/-- Design-range identification (matrices): `col [E4, D E9] = col E4 ⊔ col (D E9)`. -/
theorem range_Xmat_eq_sup [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) :
    LinearMap.range (Xmat dir r c).mulVecLin =
      LinearMap.range (E4mat dir).mulVecLin ⊔ LinearMap.range (Dmat r c * E9mat dir).mulVecLin :=
  range_fromCols _ _

theorem rank_E4mat (dir : ι → V3) :
    (E4mat dir).rank = Module.finrank ℝ (LinearMap.range (E4 dir)) := by
  unfold Matrix.rank; rw [range_E4mat]

theorem rank_E9mat (dir : ι → V3) :
    (E9mat dir).rank = Module.finrank ℝ (LinearMap.range (E9 dir)) := by
  unfold Matrix.rank; rw [range_E9mat]

theorem rank_Xmat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) :
    (Xmat dir r c).rank = Module.finrank ℝ (LinearMap.range (Xmap dir r c)) := by
  unfold Matrix.rank; rw [range_Xmat]

/-- `rank(D E9) = rank E9` for `r_i > 0`, `c > 0`. -/
theorem rank_DE9mat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i)
    (hc : 0 < c) : (Dmat r c * E9mat dir).rank = (E9mat dir).rank := by
  apply Matrix.rank_mul_eq_right_of_isUnit_det
  rw [Dmat, Matrix.det_diagonal, isUnit_iff_ne_zero]
  exact Finset.prod_ne_zero_iff.mpr fun i _ => (div_pos (hr i) hc).ne'

/-- NATIVE l.132 in matrix form:
`rank[E4, D E9] + dim(col E4 ∩ col D E9) = rank E4 + rank E9`. -/
theorem Xmat_rank_concat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ)
    (hr : ∀ i, 0 < r i) (hc : 0 < c) :
    (Xmat dir r c).rank +
        Module.finrank ℝ ↥(LinearMap.range (E4mat dir).mulVecLin ⊓
          LinearMap.range (Dmat r c * E9mat dir).mulVecLin) =
      (E4mat dir).rank + (E9mat dir).rank := by
  rw [← rank_DE9mat dir r c hr hc, Xmat]
  exact rank_fromCols_add _ _

/-- Subtraction form (`ℕ`; exact, see `rank_fromCols_eq_sub`). -/
theorem Xmat_rank_eq_sub [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ)
    (hr : ∀ i, 0 < r i) (hc : 0 < c) :
    (Xmat dir r c).rank =
      (E4mat dir).rank + (E9mat dir).rank -
        Module.finrank ℝ ↥(LinearMap.range (E4mat dir).mulVecLin ⊓
          LinearMap.range (Dmat r c * E9mat dir).mulVecLin) := by
  have := Xmat_rank_concat dir r c hr hc
  omega

end Matrices

/-! ## Step 4a — nonzero determinants ↔ unisolvency / rank -/

theorem E9_injective_iff_det (dir9 : Fin 9 → V3) :
    Function.Injective (E9 dir9) ↔ (E9mat dir9).det ≠ 0 := by
  rw [← isUnit_iff_ne_zero, ← Matrix.isUnit_iff_isUnit_det, ← Matrix.mulVec_injective_iff_isUnit]
  constructor
  · intro hinj v w hvw
    rw [E9mat_mulVec, E9mat_mulVec] at hvw
    have := hinj hvw
    rw [← hcoord_hdecode v, ← hcoord_hdecode w, this]
  · intro hinj h k hhk
    rw [E9_eq_mulVec, E9_eq_mulVec] at hhk
    have := hinj hhk
    rw [← hdecode_hcoord h, ← hdecode_hcoord k, this]

theorem E4_injective_iff_det (dir4 : Fin 4 → V3) :
    Function.Injective (E4 dir4) ↔ (E4mat dir4).det ≠ 0 := by
  rw [← isUnit_iff_ne_zero, ← Matrix.isUnit_iff_isUnit_det, ← Matrix.mulVec_injective_iff_isUnit]
  constructor
  · intro hinj v w hvw
    rw [E4mat_mulVec, E4mat_mulVec] at hvw
    have := hinj hvw
    rw [← icoord_idecode v, ← icoord_idecode w, this]
  · intro hinj a b hab
    rw [E4_eq_mulVec, E4_eq_mulVec] at hab
    have := hinj hab
    rw [← idecode_icoord a, ← idecode_icoord b, this]

theorem E9_injective_iff_rank {ι : Type*} [Fintype ι] (dir : ι → V3) :
    Function.Injective (E9 dir) ↔ (E9mat dir).rank = 9 := by
  rw [rank_E9mat]
  have hrn := LinearMap.finrank_range_add_finrank_ker (E9 dir)
  rw [finrank_HPar] at hrn
  rw [← LinearMap.ker_eq_bot, ← Submodule.finrank_eq_zero]
  omega

theorem E4_injective_iff_rank {ι : Type*} [Fintype ι] (dir : ι → V3) :
    Function.Injective (E4 dir) ↔ (E4mat dir).rank = 4 := by
  rw [rank_E4mat]
  have hrn := LinearMap.finrank_range_add_finrank_ker (E4 dir)
  rw [finrank_IPar] at hrn
  rw [← LinearMap.ker_eq_bot, ← Submodule.finrank_eq_zero]
  omega

/-- Any other real basis of the degree ≤ 2 space: `E9mat * P` with `det P ≠ 0`
has a nonzero determinant iff `E9mat` does. -/
theorem E9_basis_change_det (dir9 : Fin 9 → V3) (P : Matrix (Fin 9) (Fin 9) ℝ)
    (hP : P.det ≠ 0) : (E9mat dir9 * P).det ≠ 0 ↔ (E9mat dir9).det ≠ 0 := by
  rw [Matrix.det_mul]
  exact ⟨fun h h0 => h (by rw [h0, zero_mul]), fun h => mul_ne_zero h hP⟩

theorem E9_basis_change_rank {ι : Type*} [Fintype ι] (dir : ι → V3)
    (P : Matrix (Fin 9) (Fin 9) ℝ) (hP : P.det ≠ 0) :
    (E9mat dir * P).rank = (E9mat dir).rank :=
  Matrix.rank_mul_eq_left_of_isUnit_det P _ (isUnit_iff_ne_zero.mpr hP)

/-! ## Step 3 — exact two-radius coefficient-kernel elimination -/

theorem Xmap_apply {ι : Type*} (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (a : IPar) (h : HPar)
    (i : ι) : Xmap dir r c (a, h) i = ipoly a (dir i) + (r i / c) * Hval h (dir i) := by
  simp [Xmap, E4, E9, Dmap]

/-- Kernel of the two-radius design, given only unisolvency of the nine `R1` directions:
`X(a,h) = 0 ↔ h = -(c/R1)·lift(a) ∧ (1 - R2/R1)·E4_σ a = 0`. -/
theorem two_radius_ker_iff (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ)
    (hR1 : 0 < R1) (hc : 0 < c) (huni : Function.Injective (E9 dir9)) (a : IPar) (h : HPar) :
    Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c (a, h) = 0 ↔
      h = (-(c / R1)) • liftLin a ∧ (1 - R2 / R1) • E4 (dir9 ∘ σ) a = 0 := by
  have e1 : c / R1 * (R1 / c) = 1 := by field_simp
  have e2 : R2 / c * (c / R1) = R2 / R1 := by field_simp
  constructor
  · intro hX
    have hrow : ∀ j, ipoly a (twoRadiusDir dir9 σ j) +
        (twoRadiusR R1 R2 j / c) * Hval h (twoRadiusDir dir9 σ j) = 0 := by
      intro j; rw [← Xmap_apply, hX]; rfl
    have hk : h + (c / R1) • liftLin a = 0 := by
      apply huni
      rw [map_zero]
      funext j
      have hj := hrow (Sum.inl j)
      simp only [twoRadiusDir, twoRadiusR, Sum.elim_inl] at hj
      simp only [E9, LinearMap.coe_mk, AddHom.coe_mk, Pi.zero_apply, Hval_add, Hval_smul,
        Hval_liftLin]
      linear_combination (c / R1) * hj - (Hval h (dir9 j)) * e1
    have hh : h = (-(c / R1)) • liftLin a := by
      rw [neg_smul]; exact eq_neg_of_add_eq_zero_left hk
    refine ⟨hh, ?_⟩
    funext k
    have hj := hrow (Sum.inr k)
    simp only [twoRadiusDir, twoRadiusR, Sum.elim_inr, Function.comp_apply] at hj
    rw [hh, Hval_smul, Hval_liftLin] at hj
    simp only [E4, LinearMap.coe_mk, AddHom.coe_mk, Pi.smul_apply, Pi.zero_apply,
      Function.comp_apply, smul_eq_mul]
    linear_combination hj + (ipoly a (dir9 (σ k))) * e2
  · rintro ⟨hh, h4⟩
    funext j
    rw [Xmap_apply, hh, Hval_smul, Hval_liftLin]
    rcases j with j | k
    · simp only [twoRadiusDir, twoRadiusR, Sum.elim_inl, Pi.zero_apply]
      linear_combination (-(ipoly a (dir9 j))) * e1
    · have hk := congrFun h4 k
      simp only [E4, LinearMap.coe_mk, AddHom.coe_mk, Pi.smul_apply, Pi.zero_apply,
        Function.comp_apply, smul_eq_mul] at hk
      simp only [twoRadiusDir, twoRadiusR, Sum.elim_inr, Pi.zero_apply, Function.comp_apply]
      linear_combination hk - (ipoly a (dir9 (σ k))) * e2

/-! ## Step 4b — kernel = 0 and rank 13 from the source determinants and radii -/

/-- NATIVE l.150 with the source's hypotheses: nine directions at `R1 > 0` with nonzero
9×9 `E9` determinant (unisolvent), four of them repeated at `R2 > 0`, `R2 ≠ R1`, with nonzero
4×4 `E4` determinant (rank 4).  Then `ker X = 0`. -/
theorem two_radius_ker_eq_bot_of_det (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ)
    (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2)
    (hdet9 : (E9mat dir9).det ≠ 0) (hdet4 : (E4mat (dir9 ∘ σ)).det ≠ 0) :
    LinearMap.ker (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c) = ⊥ := by
  have huni := (E9_injective_iff_det dir9).mpr hdet9
  have hE4 := (E4_injective_iff_det (dir9 ∘ σ)).mpr hdet4
  rw [LinearMap.ker_eq_bot']
  rintro ⟨a, h⟩ hz
  obtain ⟨hh, h4⟩ := (two_radius_ker_iff dir9 σ R1 R2 c hR1 hc huni a h).mp hz
  have hfac : (1 - R2 / R1) ≠ 0 := by
    intro h0
    have : R2 / R1 = 1 := by linarith
    rw [div_eq_one_iff_eq hR1.ne'] at this
    exact hne this.symm
  have ha : a = 0 := hE4 (by rw [map_zero]; exact (smul_eq_zero.mp h4).resolve_left hfac)
  subst ha
  have hl : liftLin (0 : IPar) = 0 := rfl
  rw [hl, smul_zero] at hh
  rw [hh]; rfl

/-- Matrix kernel form: `X v = 0 → v = 0` for the 13-column matrix `[E4, D E9]`. -/
theorem two_radius_Xmat_mulVec_eq_zero (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ)
    (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2)
    (hdet9 : (E9mat dir9).det ≠ 0) (hdet4 : (E4mat (dir9 ∘ σ)).det ≠ 0)
    (v : Fin 4 ⊕ Fin 9 → ℝ)
    (hv : Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c *ᵥ v = 0) : v = 0 := by
  rw [Xmat_mulVec] at hv
  have hk := two_radius_ker_eq_bot_of_det dir9 σ R1 R2 c hR1 hR2 hc hne hdet9 hdet4
  have h0 : (idecode (v ∘ Sum.inl), hdecode (v ∘ Sum.inr)) = 0 :=
    (LinearMap.ker_eq_bot'.mp hk) _ hv
  have hl : v ∘ Sum.inl = 0 := by
    rw [← icoord_idecode (v ∘ Sum.inl), (Prod.mk.inj h0).1]
    funext k; fin_cases k <;> rfl
  have hr : v ∘ Sum.inr = 0 := by
    rw [← hcoord_hdecode (v ∘ Sum.inr), (Prod.mk.inj h0).2]
    funext k; fin_cases k <;> rfl
  funext x
  rcases x with x | x
  · exact congrFun hl x
  · exact congrFun hr x

/-- Rank 13 of the explicit matrix `X = [E4, D E9]` from the source's determinants and radii. -/
theorem two_radius_Xmat_rank13_of_det (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ)
    (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2)
    (hdet9 : (E9mat dir9).det ≠ 0) (hdet4 : (E4mat (dir9 ∘ σ)).det ≠ 0) :
    (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c).rank = 13 := by
  rw [rank_Xmat]
  exact finrank_range_of_injective_13 _ _ _ (LinearMap.ker_eq_bot.mp
    (two_radius_ker_eq_bot_of_det dir9 σ R1 R2 c hR1 hR2 hc hne hdet9 hdet4))

/-- Same theorem with the source's rank wording: `rank E9 = 9` (unisolvent) and the repeated
`E4` block of rank 4. -/
theorem two_radius_Xmat_rank13_of_ranks (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9)
    (R1 R2 c : ℝ) (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2)
    (hrank9 : (E9mat dir9).rank = 9) (hrank4 : (E4mat (dir9 ∘ σ)).rank = 4) :
    (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c).rank = 13 :=
  two_radius_Xmat_rank13_of_det dir9 σ R1 R2 c hR1 hR2 hc hne
    ((E9_injective_iff_det dir9).mp ((E9_injective_iff_rank dir9).mpr hrank9))
    ((E4_injective_iff_det _).mp ((E4_injective_iff_rank _).mpr hrank4))

/-! ## Negative controls -/

/-- DESIGN-ANGULAR: a vanishing 4×4 repeated-block determinant gives rank < 13. -/
theorem two_radius_Xmat_rank_lt13_of_det4_eq_zero (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9)
    (R1 R2 c : ℝ) (hR1 : 0 < R1) (hc : 0 < c) (hdet4 : (E4mat (dir9 ∘ σ)).det = 0) :
    (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c).rank < 13 := by
  rw [rank_Xmat]
  apply two_radius_fails_of_E4_deficient dir9 σ R1 R2 c hR1 hc
  rw [E4_injective_iff_det]; exact not_not.mpr hdet4

/-- DESIGN-R1R2: equal radii give rank ≤ 9 even when both determinants are nonzero. -/
theorem two_radius_Xmat_equal_radius_le9 (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R c : ℝ)
    (hR : 0 < R) (hc : 0 < c) :
    (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R R) c).rank ≤ 9 := by
  rw [rank_Xmat]; exact two_radius_equal_fails dir9 σ R c hR hc

/-! ## Exact witness (non-vacuity) -/

/-- Exact determinant of the repeated `E4` block (rows `e1, -e1, e2, e3`). -/
theorem witness_E4block : E4mat (dirStar ∘ σStar) =
    !![1, 1, 0, 0; 1, -1, 0, 0; 1, 0, 1, 0; 1, 0, 0, 1] := by
  ext i j; fin_cases i <;> fin_cases j <;> simp [E4mat, dirStar, σStar]

theorem witness_det4 : (E4mat (dirStar ∘ σStar)).det = -2 := by
  rw [witness_E4block, Matrix.det_succ_row_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three, Fin.succAbove]
  norm_num

/-- The 9×9 `E9` determinant of the witness directions is nonzero (exact, via linear
independence `dirStar_unisolvent`). -/
theorem witness_det9_ne_zero : (E9mat dirStar).det ≠ 0 :=
  (E9_injective_iff_det dirStar).mp dirStar_unisolvent

theorem witness_Xmat_rank13 :
    (Xmat (twoRadiusDir dirStar σStar) (twoRadiusR 1 2) 1).rank = 13 :=
  two_radius_Xmat_rank13_of_det dirStar σStar 1 2 1 one_pos two_pos one_pos (by norm_num)
    witness_det9_ne_zero (by rw [witness_det4]; norm_num)

/-- All determinant hypotheses hold but `R1 = R2 = 1`: rank ≤ 9 (radius inequality is needed). -/
theorem witness_equal_radius_le9 :
    (Xmat (twoRadiusDir dirStar σStar) (twoRadiusR 1 1) 1).rank ≤ 9 :=
  two_radius_Xmat_equal_radius_le9 dirStar σStar 1 1 one_pos one_pos

/-- Boundary instance of the dimension formula with a NONZERO intersection
(constant radius 1 on the witness directions): `4 + 9 - 4 = 9`. -/
theorem witness_const_radius_dims :
    (E4mat dirStar).rank = 4 ∧ (E9mat dirStar).rank = 9 ∧
      Module.finrank ℝ ↥(LinearMap.range (E4mat dirStar).mulVecLin ⊓
        LinearMap.range (Dmat (fun _ => (1 : ℝ)) 1 * E9mat dirStar).mulVecLin) = 4 ∧
      (Xmat dirStar (fun _ => (1 : ℝ)) 1).rank = 9 := by
  have hE4 : Function.Injective (E4 dirStar) := by
    rw [← LinearMap.ker_eq_bot, LinearMap.ker_eq_bot']
    intro a ha
    apply σStar_E4
    rw [map_zero]
    funext k
    exact congrFun ha (σStar k)
  have h4 : (E4mat dirStar).rank = 4 := (E4_injective_iff_rank dirStar).mp hE4
  have h9 : (E9mat dirStar).rank = 9 := (E9_injective_iff_rank dirStar).mp dirStar_unisolvent
  have hle : LinearMap.range (E4mat dirStar).mulVecLin ≤
      LinearMap.range (Dmat (fun _ => (1 : ℝ)) 1 * E9mat dirStar).mulVecLin := by
    rw [range_E4mat, range_DE9mat]
    exact const_radius_range_le dirStar 1 1 one_pos one_pos
  have hinf : Module.finrank ℝ ↥(LinearMap.range (E4mat dirStar).mulVecLin ⊓
      LinearMap.range (Dmat (fun _ => (1 : ℝ)) 1 * E9mat dirStar).mulVecLin) = 4 := by
    rw [inf_eq_left.mpr hle]; exact h4
  refine ⟨h4, h9, hinf, ?_⟩
  have := Xmat_rank_concat dirStar (fun _ => (1 : ℝ)) 1 (fun _ => one_pos) one_pos
  omega

end G09B
