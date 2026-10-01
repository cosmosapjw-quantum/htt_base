import Mathlib.Analysis.InnerProductSpace.Projection.FiniteDimensional
import Mathlib.Analysis.InnerProductSpace.Basic

/-!
CAS11-C03. The arbitrary real inner product below is the positive-definite
W-weighted product. No coordinate basis or Euclidean replacement is chosen.
A finite-dimensional subspace is complete, hence its orthogonal projection
exists, including in dimension zero. The index type may be empty.
-/

open scoped RealInnerProductSpace
open Finset

namespace CAS11C03

variable {E ι : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
  [FiniteDimensional ℝ E] [Fintype ι]

noncomputable def projection (V : Submodule ℝ E) : E →L[ℝ] E :=
  V.starProjection

noncomputable def residual (V : Submodule ℝ E) (K : ι → E) (i : ι) : E :=
  K i - projection V (K i)

noncomputable def gram (V : Submodule ℝ E) (K : ι → E) (i j : ι) : ℝ :=
  inner ℝ (residual V K i) (residual V K j)

noncomputable def linearCombination (V : Submodule ℝ E) (K : ι → E)
    (a : ι → ℝ) : E :=
  ∑ i : ι, a i • residual V K i

noncomputable def quadratic (V : Submodule ℝ E) (K : ι → E)
    (a : ι → ℝ) : ℝ :=
  ∑ i : ι, ∑ j : ι, a i * gram V K i j * a j

theorem projection_idempotent (V : Submodule ℝ E) (x : E) :
    projection V (projection V x) = projection V x := by
  letI : V.HasOrthogonalProjection := inferInstance
  exact congrFun (congrArg DFunLike.coe V.isIdempotentElem_starProjection.eq) x

theorem projection_orthogonal (V : Submodule ℝ E) (v x : E) (hv : v ∈ V) :
    inner ℝ v (x - projection V x) = 0 := by
  letI : V.HasOrthogonalProjection := inferInstance
  rw [real_inner_comm]
  exact V.starProjection_inner_eq_zero x v hv

theorem gram_quadratic_identity (V : Submodule ℝ E) (K : ι → E)
    (a : ι → ℝ) :
    quadratic V K a = inner ℝ (linearCombination V K a) (linearCombination V K a) := by
  simp only [quadratic, gram, linearCombination, sum_inner, inner_sum,
    real_inner_smul_left, real_inner_smul_right]
  congr 1
  ext i
  congr 1
  ext j
  rw [real_inner_comm (residual V K i) (residual V K j)]
  ring

theorem gram_quadratic_norm_sq (V : Submodule ℝ E) (K : ι → E)
    (a : ι → ℝ) :
    quadratic V K a = ‖linearCombination V K a‖ ^ 2 := by
  rw [gram_quadratic_identity, real_inner_self_eq_norm_sq]

theorem gram_positive_semidefinite (V : Submodule ℝ E) (K : ι → E)
    (a : ι → ℝ) : 0 ≤ quadratic V K a := by
  rw [gram_quadratic_norm_sq]
  positivity

-- The witness z is the square-certificate vector. If y = 0, the
-- inequality is equality; otherwise positive definiteness permits cancellation.
omit [FiniteDimensional ℝ E] in
theorem weighted_cauchy_schwarz (x y : E) :
    |inner ℝ x y| ^ 2 ≤ inner ℝ x x * inner ℝ y y := by
  let b : ℝ := inner ℝ y y
  let c : ℝ := inner ℝ x y
  let z : E := b • x - c • y
  have hcert : inner ℝ z z =
      b * (b * inner ℝ x x - c ^ 2) := by
    dsimp [z, b, c]
    simp only [inner_sub_left, inner_sub_right, real_inner_smul_left,
      real_inner_smul_right]
    rw [real_inner_comm y x]
    ring
  have hz : 0 ≤ inner ℝ z z := real_inner_self_nonneg
  by_cases hy : y = 0
  · subst y
    simp
  · have hb : 0 < b := (real_inner_self_pos).2 hy
    have hprod : 0 ≤ b * (b * inner ℝ x x - c ^ 2) := hcert ▸ hz
    have hineq : c ^ 2 ≤ inner ℝ x x * b := by
      have := (mul_nonneg_iff).mp hprod
      nlinarith
    simpa [b, c, sq_abs] using hineq

#print axioms projection_idempotent
#print axioms projection_orthogonal
#print axioms gram_quadratic_identity
#print axioms gram_quadratic_norm_sq
#print axioms gram_positive_semidefinite
#print axioms weighted_cauchy_schwarz

end CAS11C03
