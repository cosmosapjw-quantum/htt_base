import Mathlib
/- Scalar one-dimensional inverse sublemma; the full matrix/rank and rational controls remain open. -/
theorem grstat_cas03_scalar_inverse (d beta h1 : ℝ) (hd : d ≠ 0)
    (h : h1 = -2 * d * beta) : beta = -h1 / (2 * d) := by
  rw [h]
  field_simp
#print axioms grstat_cas03_scalar_inverse
