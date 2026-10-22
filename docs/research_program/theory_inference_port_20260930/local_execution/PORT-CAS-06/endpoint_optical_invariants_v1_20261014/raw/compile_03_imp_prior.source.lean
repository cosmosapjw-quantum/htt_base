import Mathlib

namespace PORTCAS06EndpointScalarInvariant

noncomputable def zNew (z D : ℝ) : ℝ := (1 + z) / D - 1
def dANew (dA D : ℝ) : ℝ := D * dA
noncomputable def dLNew (dL D : ℝ) : ℝ := dL / D

theorem endpoint_product_invariant (z dA D : ℝ) (hD : 0 < D) :
    (1 + zNew z D) * dANew dA D = (1 + z) * dA := by
  unfold zNew dANew
  field_simp [ne_of_gt hD]
  <;> ring

theorem luminosity_distance_scaling (dL D : ℝ) :
    dLNew dL D = dL / D := rfl

theorem endpoint_scalar_invariant (z dA dL D : ℝ) (hD : 0 < D) :
    (1 + zNew z D) * dANew dA D = (1 + z) * dA ∧
      dLNew dL D = dL / D :=
  ⟨endpoint_product_invariant z dA D hD, luminosity_distance_scaling dL D⟩

end PORTCAS06EndpointScalarInvariant

#print axioms PORTCAS06EndpointScalarInvariant.endpoint_product_invariant
#print axioms PORTCAS06EndpointScalarInvariant.luminosity_distance_scaling
#print axioms PORTCAS06EndpointScalarInvariant.endpoint_scalar_invariant
