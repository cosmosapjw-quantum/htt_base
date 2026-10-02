import Mathlib
/- Finite scalar perturbation envelope, necessary for a singular-value bound. -/
theorem grstat_cas07_scalar_envelope (s eta d : ℝ)
    (hs : 0 ≤ s) (he : 0 ≤ eta) (h : |d-s| ≤ s*eta) :
    s*(1-eta) ≤ d ∧ d ≤ s*(1+eta) := by
  constructor <;> nlinarith [abs_le.mp h]
#print axioms grstat_cas07_scalar_envelope
