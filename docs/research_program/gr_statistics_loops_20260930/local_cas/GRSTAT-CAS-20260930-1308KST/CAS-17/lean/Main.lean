import Mathlib
/- Pure mass-shell beta-gamma algebra; spacelike Gram and conformal claims remain open. -/
theorem grstat_cas17_beta_gamma (gamma beta : ℝ)
    (hg : gamma ≠ 0) (h : beta^2 = 1 - gamma⁻¹^2) :
    gamma^2 * beta^2 = gamma^2 - 1 := by
  rw [h]
  field_simp
#print axioms grstat_cas17_beta_gamma
