import Mathlib
import CAS15ProjectionAccepted

/-!
Concrete CAS-15-C03 least-squares bridge. `E` is the nine-coordinate real
Euclidean space, so its norm is exactly the Frobenius norm. The domain is the
actual submodule of skew 3 by 3 arrays. No spectral-gap or exact-fit hypothesis
is used in the least-squares result.
-/

noncomputable section
namespace CAS15Frobenius

abbrev E := EuclideanSpace ℝ (Fin 3 × Fin 3)

/-- The native Euclidean norm is the sum-of-entry-squares Frobenius norm. -/
theorem frobenius_norm_sq (X : E) :
    ‖X‖ ^ 2 = ∑ i : Fin 3, ∑ j : Fin 3, X (i, j) ^ 2 := by
  rw [EuclideanSpace.real_norm_sq_eq, Fintype.sum_prod_type]

def skew : Submodule ℝ E where
  carrier := {X | ∀ i j : Fin 3, X (i, j) = -X (j, i)}
  zero_mem' := by
    intro i j
    simp
  add_mem' := by
    intro X Y hX hY i j
    simp [hX i j, hY i j]
    abel
  smul_mem' := by
    intro a X hX i j
    simp [hX i j]

/-- Matrix product commutator written directly in Euclidean coordinates. -/
def comm (M X : E) : E :=
  WithLp.toLp 2 (fun p : Fin 3 × Fin 3 =>
    ∑ k : Fin 3, (M (p.1, k) * X (k, p.2) - X (p.1, k) * M (k, p.2)))

@[simp] theorem comm_apply (M X : E) (i j : Fin 3) :
    comm M X (i, j) =
      ∑ k : Fin 3, (M (i, k) * X (k, j) - X (i, k) * M (k, j)) := rfl

theorem comm_add_right (M X Y : E) : comm M (X + Y) = comm M X + comm M Y := by
  ext ⟨i, j⟩
  simp [comm, mul_add, add_mul, Finset.sum_add_distrib]
  ring

theorem comm_smul_right (M X : E) (a : ℝ) : comm M (a • X) = a • comm M X := by
  ext ⟨i, j⟩
  simp [comm, mul_left_comm, mul_comm]
  rw [mul_sub, Finset.mul_sum, Finset.mul_sum]

theorem comm_sub_left (M N X : E) : comm (M - N) X = comm M X - comm N X := by
  ext ⟨i, j⟩
  simp [comm, sub_mul, mul_sub, Finset.sum_sub_distrib]
  ring

def commLinear (M : E) : skew →ₗ[ℝ] E where
  toFun X := comm M X.1
  map_add' X Y := comm_add_right M X.1 Y.1
  map_smul' a X := comm_smul_right M X.1 a

/-- An arbitrary-data norm least-squares minimizer satisfies projection contraction. -/
theorem skew_least_squares_contraction (Mhat Rhat : E) (What W : skew)
    (hmin : ∀ X : skew,
      ‖Rhat - comm Mhat What.1‖ ≤ ‖Rhat - comm Mhat X.1‖) :
    ‖comm Mhat (What - W).1‖ ≤ ‖Rhat - comm Mhat W.1‖ := by
  exact CAS15Continuation.least_squares_error_contraction
    (commLinear Mhat) Rhat What W hmin

/-- Squared-loss minimization gives the same contraction, since norms are nonnegative. -/
theorem skew_squared_least_squares_contraction (Mhat Rhat : E) (What W : skew)
    (hmin : ∀ X : skew,
      ‖Rhat - comm Mhat What.1‖ ^ 2 ≤ ‖Rhat - comm Mhat X.1‖ ^ 2) :
    ‖comm Mhat (What - W).1‖ ≤ ‖Rhat - comm Mhat W.1‖ := by
  apply skew_least_squares_contraction Mhat Rhat What W
  intro X
  have h₁ := norm_nonneg (Rhat - comm Mhat What.1)
  have h₂ := norm_nonneg (Rhat - comm Mhat X.1)
  nlinarith [hmin X]

/-- Exact residual identity when the comparator signal is `R = [M,W]`. -/
theorem residual_identity (M Mhat R Rhat : E) (W : skew)
    (hR : R = comm M W.1) :
    Rhat - comm Mhat W.1 = (Rhat - R) - comm (Mhat - M) W.1 := by
  rw [hR, comm_sub_left]
  abel

theorem skew_least_squares_perturbation_residual
    (M Mhat R Rhat : E) (W What : skew)
    (hR : R = comm M W.1)
    (hmin : ∀ X : skew,
      ‖Rhat - comm Mhat What.1‖ ≤ ‖Rhat - comm Mhat X.1‖) :
    ‖comm Mhat (What - W).1‖ ≤
      ‖(Rhat - R) - comm (Mhat - M) W.1‖ := by
  rw [← residual_identity M Mhat R Rhat W hR]
  exact skew_least_squares_contraction Mhat Rhat What W hmin

#print axioms frobenius_norm_sq
#print axioms skew_least_squares_contraction
#print axioms skew_squared_least_squares_contraction
#print axioms residual_identity
#print axioms skew_least_squares_perturbation_residual

end CAS15Frobenius
