import Mathlib
/- Linear adjoint annihilation in a scalar model; continuum and kernel moments remain open. -/
theorem grstat_cas12_adjoint_scalar (l f m : ℝ) (h : l*m=0) :
    (l*f)*m=0 := by
  calc
    (l*f)*m = f*(l*m) := by ring
    _ = 0 := by rw [h]; ring
#print axioms grstat_cas12_adjoint_scalar
