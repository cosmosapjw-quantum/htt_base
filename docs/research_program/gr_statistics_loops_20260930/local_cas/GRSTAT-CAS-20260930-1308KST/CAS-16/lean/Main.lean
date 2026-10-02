import Mathlib
/- Exact degree/order arithmetic for the declared (4,6,4) instance. -/
theorem grstat_cas16_degree_instance :
    max (4+4) (max (6+2) (4+2)) = 8 ∧ 9 ≥ 8+1 ∧ 2*5-1 ≥ 8 := by
  decide
#print axioms grstat_cas16_degree_instance
