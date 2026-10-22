import Mathlib

namespace PORTCAS05EigenframeGap

/-- The scalar component equation can be divided only under a nonzero gap. -/
theorem recover_coefficient (li lj gamma d : ℝ)
    (hgap : li ≠ lj) (heq : d = (li - lj) * gamma) :
    gamma = d / (li - lj) := by
  apply (eq_div_iff (sub_ne_zero.mpr hgap)).2
  rw [heq]
  ring

/-- At a repeated eigenvalue, the zero-data equation holds for every coefficient. -/
theorem repeated_gap_equations (li lj gamma1 gamma2 : ℝ) (hgap : li = lj) :
    (0 : ℝ) = (li - lj) * gamma1 ∧
    (0 : ℝ) = (li - lj) * gamma2 := by
  subst lj
  simp

/-- The same repeated-gap equation admits the distinct coefficients zero and one. -/
theorem repeated_gap_nonunique (li : ℝ) :
    (0 : ℝ) = (li - li) * (0 : ℝ) ∧
    (0 : ℝ) = (li - li) * (1 : ℝ) ∧
    (0 : ℝ) ≠ (1 : ℝ) := by
  norm_num

end PORTCAS05EigenframeGap

#check PORTCAS05EigenframeGap.recover_coefficient
#check PORTCAS05EigenframeGap.repeated_gap_equations
#check PORTCAS05EigenframeGap.repeated_gap_nonunique
#print axioms PORTCAS05EigenframeGap.recover_coefficient
#print axioms PORTCAS05EigenframeGap.repeated_gap_equations
#print axioms PORTCAS05EigenframeGap.repeated_gap_nonunique
