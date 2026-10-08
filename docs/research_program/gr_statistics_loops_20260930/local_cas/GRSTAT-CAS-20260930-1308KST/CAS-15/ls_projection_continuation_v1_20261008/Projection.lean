import Mathlib

noncomputable section
namespace CAS15Continuation
open Set
variable {X E : Type*} [AddCommGroup X] [Module ℝ X]
  [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]

/-- A genuine arbitrary-data least-squares minimizer maps to the range projection.
No exact-fit equation A what = r is assumed. -/
theorem least_squares_projection (A : X →ₗ[ℝ] E) (r : E) (what : X)
    (hmin : ∀ x : X, ‖r - A what‖ ≤ ‖r - A x‖) :
    A what = (LinearMap.range A).starProjection r := by
  let U := LinearMap.range A
  have hw : A what ∈ U := ⟨what, rfl⟩
  have hb : BddBelow (Set.range (fun y : U => ‖r - (y : E)‖)) := by
    refine ⟨0, ?_⟩
    rintro _ ⟨y, rfl⟩
    exact norm_nonneg _
  have hi : ‖r - A what‖ = ⨅ y : U, ‖r - (y : E)‖ := by
    apply le_antisymm
    · apply le_ciInf
      intro y
      obtain ⟨x, hx⟩ := y.property
      simpa only [hx] using hmin x
    · exact ciInf_le hb ⟨A what, hw⟩
  have ho := (U.norm_eq_iInf_iff_inner_eq_zero hw).mp hi
  exact (U.eq_starProjection_of_mem_of_inner_eq_zero hw ho).symm

/-- Range projection yields contraction of the error relative to any comparator. -/
theorem least_squares_error_contraction (A : X →ₗ[ℝ] E) (r : E) (what w : X)
    (hmin : ∀ x : X, ‖r - A what‖ ≤ ‖r - A x‖) :
    ‖A (what - w)‖ ≤ ‖r - A w‖ := by
  let U := LinearMap.range A
  have hp := least_squares_projection A r what hmin
  have hw : U.starProjection (A w) = A w := U.starProjection_eq_self_iff.mpr ⟨w, rfl⟩
  have hi : A (what - w) = U.starProjection (r - A w) := by
    rw [map_sub, hp, map_sub, hw]
  rw [hi]
  exact U.norm_starProjection_apply_le _

/-- This generic implication is conditional on a supplied coercivity estimate.
It does not prove rotated-matrix coercivity, the mixed matrix norm bound, or Weyl. -/
theorem perturbation_from_least_squares
    {X : Type*} [NormedAddCommGroup X] [NormedSpace ℝ X]
    (A : X →ₗ[ℝ] E) (r : E) (what w : X) (delta eps : ℝ)
    (hdelta : 0 < delta)
    (hmin : ∀ x : X, ‖r - A what‖ ≤ ‖r - A x‖)
    (hcoerc : ∀ x : X, delta * ‖x‖ ≤ ‖A x‖)
    (hnoise : ‖r - A w‖ ≤ eps) :
    ‖what - w‖ ≤ eps / delta := by
  apply (le_div_iff₀ hdelta).mpr
  calc
    ‖what - w‖ * delta = delta * ‖what - w‖ := mul_comm _ _
    _ ≤ ‖A (what - w)‖ := hcoerc _
    _ ≤ ‖r - A w‖ := least_squares_error_contraction A r what w hmin
    _ ≤ eps := hnoise

#print axioms least_squares_projection
#print axioms least_squares_error_contraction
#print axioms perturbation_from_least_squares
end CAS15Continuation
