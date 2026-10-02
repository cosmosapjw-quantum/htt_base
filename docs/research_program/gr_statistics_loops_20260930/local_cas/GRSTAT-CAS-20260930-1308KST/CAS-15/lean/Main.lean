import Mathlib
/- A diagonal-basis entry of [M,W], not the complete component inverse. -/
theorem grstat_cas15_commutator_entry (mi mj wij : ℝ) :
    mi * wij - wij * mj = (mi - mj) * wij := by ring
#print axioms grstat_cas15_commutator_entry
