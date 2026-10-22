import Mathlib

open Filter Topology

namespace CAS12PlanckIR

noncomputable def weight (b E : Real) : Real :=
  Real.exp (b * E) / (Real.exp (b * E) - 1)^2

/-- The actual right-hand IR limit, derived from the derivative of the real exponential. -/
theorem scaled_weight_tendsto (b : Real) (hb : 0 < b) :
    Filter.Tendsto (fun E : Real => E^2 * weight b E)
      (nhdsWithin 0 (Set.Ioi 0)) (nhds (b^(-2 : Int))) := by
  have hd : HasDerivAt (fun E : Real => Real.exp (b * E)) b 0 := by
    simpa using ((hasDerivAt_id (0 : Real)).const_mul b).exp
  have hs : Tendsto (fun E : Real => (Real.exp (b * E) - 1) / E)
      (nhdsWithin 0 (Set.Ioi 0)) (nhds b) := by
    simpa [div_eq_mul_inv, mul_comm] using hd.tendsto_slope_zero_right
  have hi := (hs.inv₀ (ne_of_gt hb)).pow 2
  have he : Tendsto (fun E : Real => Real.exp (b * E))
      (nhdsWithin 0 (Set.Ioi 0)) (nhds (1 : Real)) := by
    simpa using hd.continuousAt.tendsto.mono_left nhdsWithin_le_nhds
  have hprod := he.mul hi
  convert hprod using 1
  · funext E
    simp only [weight, inv_div, div_pow]
    ring
  · simp [zpow_neg, zpow_ofNat, inv_pow]

end CAS12PlanckIR
