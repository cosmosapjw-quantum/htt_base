import Mathlib
/- A necessary scalar relation for the stipulated power-law parameter. -/
theorem grstat_cas06_power_ratio (alpha : ℝ) (ha : alpha ≠ 0) :
    2 * ((1 + alpha) / (2 * alpha)) - 1 = 1 / alpha := by
  field_simp
  ring
#print axioms grstat_cas06_power_ratio
