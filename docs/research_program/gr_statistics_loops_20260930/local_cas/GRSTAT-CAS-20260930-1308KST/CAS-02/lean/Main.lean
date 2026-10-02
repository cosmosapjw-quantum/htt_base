import Mathlib
/- Scalar analogue of the exact swapped-anchor quadratic-form identity. -/
theorem grstat_cas02_anchor (u₁ u₂ s₁ s₂ : ℝ) :
    u₂*s₂*u₂ - u₁*s₁*u₁ =
      u₂*(s₂-s₁)*u₂ + (u₂-u₁)*s₁*u₂ + u₁*s₁*(u₂-u₁) := by ring
#print axioms grstat_cas02_anchor
