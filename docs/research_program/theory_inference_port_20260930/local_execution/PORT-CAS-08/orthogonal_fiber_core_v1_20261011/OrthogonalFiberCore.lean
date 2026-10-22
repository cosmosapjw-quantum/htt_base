import Mathlib

namespace PORTCAS08OrthogonalFiberCore

/-- Exact finite-coordinate Pythagoras under the stated Euclidean orthogonality. -/
theorem pythagoras {n : ℕ} (z0 k : Fin n → ℝ)
    (horth : ∑ i, z0 i * k i = 0) :
    ∑ i, (z0 i + k i) ^ 2 = (∑ i, z0 i ^ 2) + ∑ i, k i ^ 2 := by
  have hcross : (∑ i, (2 : ℝ) * (z0 i * k i)) = 0 := by
    rw [← Finset.mul_sum, horth]
    ring
  calc
    ∑ i, (z0 i + k i) ^ 2 =
        ∑ i, (z0 i ^ 2 + k i ^ 2 + 2 * (z0 i * k i)) := by
      apply Finset.sum_congr rfl
      intro i _
      ring
    _ = (∑ i, z0 i ^ 2) + ∑ i, k i ^ 2 := by
      rw [Finset.sum_add_distrib, Finset.sum_add_distrib, hcross]
      ring

/-- Adding an orthogonal finite-coordinate displacement cannot lower squared norm. -/
theorem squared_norm_lower_bound {n : ℕ} (z0 k : Fin n → ℝ)
    (horth : ∑ i, z0 i * k i = 0) :
    (∑ i, z0 i ^ 2) ≤ ∑ i, (z0 i + k i) ^ 2 := by
  rw [pythagoras z0 k horth]
  have hnonneg : 0 ≤ ∑ i, k i ^ 2 :=
    Finset.sum_nonneg (fun i _ => sq_nonneg (k i))
  linarith

/-- Equality under orthogonality forces the entire displacement function to vanish. -/
theorem equality_rigidity {n : ℕ} (z0 k : Fin n → ℝ)
    (horth : ∑ i, z0 i * k i = 0)
    (heq : (∑ i, z0 i ^ 2) = ∑ i, (z0 i + k i) ^ 2) :
    k = 0 := by
  have hsum : (∑ i, k i ^ 2) = 0 := by
    rw [pythagoras z0 k horth] at heq
    linarith
  funext i
  have hle : k i ^ 2 ≤ ∑ j, k j ^ 2 :=
    Finset.single_le_sum (fun j _ => sq_nonneg (k j)) (Finset.mem_univ i)
  have hsquare : k i ^ 2 = 0 :=
    le_antisymm (by simpa [hsum] using hle) (sq_nonneg (k i))
  exact (sq_eq_zero_iff).mp hsquare

end PORTCAS08OrthogonalFiberCore

#check PORTCAS08OrthogonalFiberCore.pythagoras
#check PORTCAS08OrthogonalFiberCore.squared_norm_lower_bound
#check PORTCAS08OrthogonalFiberCore.equality_rigidity
#print axioms PORTCAS08OrthogonalFiberCore.pythagoras
#print axioms PORTCAS08OrthogonalFiberCore.squared_norm_lower_bound
#print axioms PORTCAS08OrthogonalFiberCore.equality_rigidity
