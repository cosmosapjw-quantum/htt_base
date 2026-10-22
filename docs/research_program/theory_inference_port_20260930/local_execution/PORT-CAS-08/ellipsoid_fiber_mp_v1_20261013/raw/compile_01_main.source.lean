import Mathlib
import G08AWhitening

/-!
P08-A (PORT-CAS-08): ellipsoid fibre minimum-norm and compatibility decomposition.

For a real matrix `A = B L : Matrix (Fin m) (Fin p) ℝ`, a right-hand side
`b = y - B c : Fin m → ℝ`, and any `X` satisfying the four Penrose conditions
`G08AWhitening.IsMoorePenrose A X` (existence/uniqueness proved in G08A by exact
spectral construction, no floating cutoff), put `z0 := X *ᵥ b` and
`η := z0 ⬝ᵥ z0` (Euclidean dot product).

Proved here, for every rank (zero, full column, and mixed):
* compatibility `∃ z, A z = b` iff `A z0 = b` (exact range test, no tolerance);
* `z0 ∈ range Aᵀ` (row space);
* every solution is `z0 + k` with `k ∈ ker A`, and conversely;
* Pythagoras `‖z0 + k‖² = ‖z0‖² + ‖k‖²` for `k ∈ ker A`;
* minimum norm with rigidity (equality iff `z = z0`);
* fibre `{z | A z = b ∧ z ⬝ᵥ z ≤ 1}` branches: `η > 1` empty, `η = 1` the
  singleton `{z0}` (proved separately, no interior formula used), `η < 1` the
  translate by `z0` of the `ker A`-ball of squared radius `1 - η`;
* incompatible support (`b ∉ range A`) gives the empty fibre, as a distinct cause;
* rank branches: `A = 0` forces `X *ᵥ b = 0`; `A.rank = p` forces `ker A = 0`
  and uniqueness of solutions.
A concrete mixed-rank 2×2 witness separates the three empty/nonempty causes.

No numerical SVD, physical-unit ellipsoid quotient image, or scientific
admission is asserted.
-/

noncomputable section

namespace P08EllipsoidFiber

open Matrix

variable {m p : ℕ}

/-! ### Basic algebra -/

/-- `A X A = A` acting on vectors. -/
theorem mulVec_AXA (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (hX : G08AWhitening.IsMoorePenrose A X) (z : Fin p → ℝ) :
    A *ᵥ (X *ᵥ (A *ᵥ z)) = A *ᵥ z := by
  rw [mulVec_mulVec, mulVec_mulVec, ← Matrix.mul_assoc, hX.1]

/-- `X = Aᵀ (Xᵀ X)` from `X A X = X` and symmetry of `X A`. -/
theorem X_eq_transpose_mul (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (hX : G08AWhitening.IsMoorePenrose A X) : X = Aᵀ * (Xᵀ * X) := by
  calc X = X * A * X := hX.2.1.symm
    _ = (X * A)ᵀ * X := by rw [hX.2.2.2]
    _ = Aᵀ * Xᵀ * X := by rw [transpose_mul]
    _ = Aᵀ * (Xᵀ * X) := Matrix.mul_assoc _ _ _

/-- Real dot-square is nonnegative. -/
theorem dot_self_nonneg (v : Fin p → ℝ) : 0 ≤ v ⬝ᵥ v := by
  simp only [dotProduct]
  exact Finset.sum_nonneg fun i _ => mul_self_nonneg (v i)

/-- Real dot-square vanishes only at zero. -/
theorem dot_self_eq_zero (v : Fin p → ℝ) (h : v ⬝ᵥ v = 0) : v = 0 := by
  funext i
  have hle : v i * v i ≤ v ⬝ᵥ v := by
    simp only [dotProduct]
    exact Finset.single_le_sum (f := fun j => v j * v j)
      (fun j _ => mul_self_nonneg (v j)) (Finset.mem_univ i)
  have h0 : v i * v i = 0 := le_antisymm (by linarith) (mul_self_nonneg (v i))
  simpa using mul_self_eq_zero.mp h0

/-! ### Target 1: exact compatibility test -/

theorem compatible_iff (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) :
    (∃ z, A *ᵥ z = b) ↔ A *ᵥ (X *ᵥ b) = b := by
  constructor
  · rintro ⟨z, rfl⟩
    exact mulVec_AXA A X hX z
  · intro h
    exact ⟨X *ᵥ b, h⟩

/-! ### Target 2: `z0` lies in the row space `range Aᵀ` -/

theorem z0_in_rowspace (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) :
    ∃ w, X *ᵥ b = Aᵀ *ᵥ w := by
  refine ⟨(Xᵀ * X) *ᵥ b, ?_⟩
  conv_lhs => rw [X_eq_transpose_mul A X hX]
  rw [← mulVec_mulVec]

/-- Row-space vectors are orthogonal to `ker A`. -/
theorem z0_orthogonal_kernel (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) (k : Fin p → ℝ)
    (hk : A *ᵥ k = 0) : (X *ᵥ b) ⬝ᵥ k = 0 := by
  obtain ⟨w, hw⟩ := z0_in_rowspace A X b hX
  rw [hw, mulVec_transpose, ← dotProduct_mulVec, hk, dotProduct_zero]

/-! ### Target 3: affine solution set `z0 + ker A` -/

theorem solution_decomposition (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X)
    (hcomp : ∃ z, A *ᵥ z = b) (z : Fin p → ℝ) :
    A *ᵥ z = b ↔ ∃ k, A *ᵥ k = 0 ∧ z = X *ᵥ b + k := by
  have h0 : A *ᵥ (X *ᵥ b) = b := (compatible_iff A X b hX).mp hcomp
  constructor
  · intro hz
    refine ⟨z - X *ᵥ b, ?_, ?_⟩
    · rw [mulVec_sub, hz, h0, sub_self]
    · abel
  · rintro ⟨k, hk, rfl⟩
    rw [mulVec_add, h0, hk, add_zero]

/-! ### Target 4: Pythagoras on the fibre -/

theorem pythagoras_fiber (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) (k : Fin p → ℝ)
    (hk : A *ᵥ k = 0) :
    (X *ᵥ b + k) ⬝ᵥ (X *ᵥ b + k) = (X *ᵥ b) ⬝ᵥ (X *ᵥ b) + k ⬝ᵥ k := by
  have horth := z0_orthogonal_kernel A X b hX k hk
  have horth' : k ⬝ᵥ (X *ᵥ b) = 0 := by rw [dotProduct_comm]; exact horth
  rw [add_dotProduct, dotProduct_add, dotProduct_add, horth, horth']
  ring

/-! ### Target 5: minimum norm with rigidity -/

theorem min_norm (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X)
    (hcomp : ∃ z, A *ᵥ z = b) (z : Fin p → ℝ) (hz : A *ᵥ z = b) :
    (X *ᵥ b) ⬝ᵥ (X *ᵥ b) ≤ z ⬝ᵥ z ∧
      (z ⬝ᵥ z = (X *ᵥ b) ⬝ᵥ (X *ᵥ b) ↔ z = X *ᵥ b) := by
  obtain ⟨k, hk, rfl⟩ := (solution_decomposition A X b hX hcomp z).mp hz
  rw [pythagoras_fiber A X b hX k hk]
  refine ⟨by linarith [dot_self_nonneg k], ?_, ?_⟩
  · intro heq
    have : k = 0 := dot_self_eq_zero k (by linarith)
    rw [this, add_zero]
  · intro heq
    have : k = 0 := by
      have h := congrArg (fun v => v - X *ᵥ b) heq
      simpa using h
    rw [this, dotProduct_zero, add_zero]

/-! ### Target 6: fibre branches -/

/-- The unit-ball fibre over `b`. -/
def Fib (A : Matrix (Fin m) (Fin p) ℝ) (b : Fin m → ℝ) : Set (Fin p → ℝ) :=
  {z | A *ᵥ z = b ∧ z ⬝ᵥ z ≤ 1}

/-- General characterization (any `η`): the fibre is `z0 + {k ∈ ker A | k⬝k ≤ 1 - η}`. -/
theorem fiber_eq_kernel_ball (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) (hcomp : ∃ z, A *ᵥ z = b) :
    Fib A b = {z | ∃ k, A *ᵥ k = 0 ∧ k ⬝ᵥ k ≤ 1 - (X *ᵥ b) ⬝ᵥ (X *ᵥ b) ∧ z = X *ᵥ b + k} := by
  ext z
  simp only [Fib, Set.mem_setOf_eq]
  constructor
  · rintro ⟨hz, hn⟩
    obtain ⟨k, hk, rfl⟩ := (solution_decomposition A X b hX hcomp z).mp hz
    rw [pythagoras_fiber A X b hX k hk] at hn
    exact ⟨k, hk, by linarith, rfl⟩
  · rintro ⟨k, hk, hkn, rfl⟩
    refine ⟨(solution_decomposition A X b hX hcomp _).mpr ⟨k, hk, rfl⟩, ?_⟩
    rw [pythagoras_fiber A X b hX k hk]
    linarith

theorem fiber_branches (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) (hcomp : ∃ z, A *ᵥ z = b) :
    (1 < (X *ᵥ b) ⬝ᵥ (X *ᵥ b) → {z | A *ᵥ z = b ∧ z ⬝ᵥ z ≤ 1} = ∅) ∧
    ((X *ᵥ b) ⬝ᵥ (X *ᵥ b) = 1 → {z | A *ᵥ z = b ∧ z ⬝ᵥ z ≤ 1} = {X *ᵥ b}) ∧
    ((X *ᵥ b) ⬝ᵥ (X *ᵥ b) < 1 → {z | A *ᵥ z = b ∧ z ⬝ᵥ z ≤ 1} =
      {z | ∃ k, A *ᵥ k = 0 ∧ k ⬝ᵥ k ≤ 1 - (X *ᵥ b) ⬝ᵥ (X *ᵥ b) ∧ z = X *ᵥ b + k}) := by
  refine ⟨?_, ?_, ?_⟩
  · -- η > 1: minimum norm already exceeds the ball.
    intro hη
    ext z
    simp only [Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false, not_and, not_le]
    intro hz
    exact lt_of_lt_of_le hη (min_norm A X b hX hcomp z hz).1
  · -- η = 1: boundary, proved directly as a singleton via rigidity.
    intro hη
    ext z
    simp only [Set.mem_setOf_eq, Set.mem_singleton_iff]
    constructor
    · rintro ⟨hz, hn⟩
      have hmin := min_norm A X b hX hcomp z hz
      exact hmin.2.mp (le_antisymm (by linarith) (by linarith [hmin.1]))
    · rintro rfl
      exact ⟨(compatible_iff A X b hX).mp hcomp, le_of_eq hη⟩
  · -- η < 1: kernel ball translate.
    intro _
    exact fiber_eq_kernel_ball A X b hX hcomp

/-! ### Target 7: incompatible support (distinct cause) -/

theorem incompatible_empty (A : Matrix (Fin m) (Fin p) ℝ) (b : Fin m → ℝ)
    (hinc : ¬ ∃ z, A *ᵥ z = b) : {z | A *ᵥ z = b ∧ z ⬝ᵥ z ≤ 1} = ∅ := by
  ext z
  simp only [Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false, not_and]
  intro hz
  exact absurd ⟨z, hz⟩ hinc

/-- Incompatibility is detected exactly by the Moore–Penrose residual, no tolerance. -/
theorem incompatible_iff_residual (A : Matrix (Fin m) (Fin p) ℝ) (X : Matrix (Fin p) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) :
    (¬ ∃ z, A *ᵥ z = b) ↔ A *ᵥ (X *ᵥ b) ≠ b := by
  rw [compatible_iff A X b hX]

/-! ### Target 8: rank branches -/

theorem rank_zero (A : Matrix (Fin m) (Fin p) ℝ) (b : Fin m → ℝ) (hA : A = 0) :
    ∀ X : Matrix (Fin p) (Fin m) ℝ, G08AWhitening.IsMoorePenrose A X → X *ᵥ b = 0 := by
  intro X hX
  have hX0 : X = 0 := by
    calc X = X * A * X := hX.2.1.symm
      _ = 0 := by rw [hA, Matrix.mul_zero, Matrix.zero_mul]
  rw [hX0, zero_mulVec]

theorem full_column_rank_ker (A : Matrix (Fin m) (Fin p) ℝ) (hA : A.rank = p) :
    ∀ k : Fin p → ℝ, A *ᵥ k = 0 → k = 0 := by
  intro k hk
  have hrn := LinearMap.finrank_range_add_finrank_ker A.mulVecLin
  rw [← Matrix.rank, hA, Module.finrank_fin_fun] at hrn
  have hker : LinearMap.ker A.mulVecLin = ⊥ :=
    Submodule.finrank_eq_zero.mp (by omega)
  have hmem : k ∈ LinearMap.ker A.mulVecLin := by
    rw [LinearMap.mem_ker, Matrix.mulVecLin_apply]
    exact hk
  rw [hker] at hmem
  exact (Submodule.mem_bot ℝ).mp hmem

theorem full_column_rank (A : Matrix (Fin m) (Fin p) ℝ) (b : Fin m → ℝ) (hA : A.rank = p) :
    ∀ z z' : Fin p → ℝ, A *ᵥ z = b → A *ᵥ z' = b → z = z' := by
  intro z z' hz hz'
  have h := full_column_rank_ker A hA (z - z') (by rw [mulVec_sub, hz, hz', sub_self])
  exact sub_eq_zero.mp h

/-! ### Concrete mixed-rank witness (2×2, rank strictly between 0 and full) -/

/-- `A₀ = diag(1, 0)`: nonzero and with nontrivial kernel. -/
def A₀ : Matrix (Fin 2) (Fin 2) ℝ := !![1, 0; 0, 0]

theorem A₀_isMoorePenrose : G08AWhitening.IsMoorePenrose A₀ A₀ := by
  have h : A₀ * A₀ = A₀ := by
    ext i j
    fin_cases i <;> fin_cases j <;> simp [A₀, Matrix.mul_apply, Fin.sum_univ_two]
  have ht : A₀ᵀ = A₀ := by
    ext i j
    fin_cases i <;> fin_cases j <;> simp [A₀]
  refine ⟨?_, ?_, ?_, ?_⟩ <;> simp only [h, ht]

theorem A₀_mixed : A₀ ≠ 0 ∧ A₀ *ᵥ ![0, 1] = 0 ∧ (![0, 1] : Fin 2 → ℝ) ≠ 0 := by
  refine ⟨?_, ?_, ?_⟩
  · intro h
    have := congrFun (congrFun h 0) 0
    simp [A₀] at this
  · ext i
    fin_cases i <;> simp [A₀, mulVec, dotProduct, Fin.sum_univ_two]
  · intro h
    have := congrFun h 1
    simp at this

/-- Interior branch instance: `b = (1/2, 0)`, `η = 1/4 < 1`. -/
theorem A₀_interior :
    A₀ *ᵥ (A₀ *ᵥ ![1/2, 0]) = ![1/2, 0] ∧
      (A₀ *ᵥ ![1/2, 0]) ⬝ᵥ (A₀ *ᵥ ![1/2, 0]) = 1/4 := by
  constructor
  · ext i
    fin_cases i <;> simp [A₀, mulVec, dotProduct, Fin.sum_univ_two]
  · simp [A₀, mulVec, dotProduct, Fin.sum_univ_two]
    norm_num

/-- Compatible but `η = 4 > 1`: empty for the norm reason. -/
theorem A₀_eta_gt_one :
    A₀ *ᵥ (A₀ *ᵥ ![2, 0]) = ![2, 0] ∧
      1 < (A₀ *ᵥ ![2, 0]) ⬝ᵥ (A₀ *ᵥ ![2, 0]) := by
  constructor
  · ext i
    fin_cases i <;> simp [A₀, mulVec, dotProduct, Fin.sum_univ_two]
  · simp [A₀, mulVec, dotProduct, Fin.sum_univ_two]
    norm_num

/-- `b = (0, 1)` is incompatible: empty for the support reason, although `η = 0 < 1`. -/
theorem A₀_incompatible :
    (¬ ∃ z, A₀ *ᵥ z = ![0, 1]) ∧ (A₀ *ᵥ ![0, 1]) ⬝ᵥ (A₀ *ᵥ ![0, 1]) = 0 := by
  constructor
  · rw [incompatible_iff_residual A₀ A₀ _ A₀_isMoorePenrose]
    intro h
    have := congrFun h 1
    simp [A₀, mulVec, dotProduct, Fin.sum_univ_two] at this
  · simp [A₀, mulVec, dotProduct, Fin.sum_univ_two]

end P08EllipsoidFiber
