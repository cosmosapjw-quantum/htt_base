import Mathlib
open MeasureTheory Set Filter Topology
example (W : ℝ) : ∫ t in (0:ℝ)..1, (1 - t) * (1 / W) = 1 / W / 2 := by
  rw [intervalIntegral.integral_mul_const, intervalIntegral.integral_sub intervalIntegrable_const intervalIntegral.intervalIntegrable_id]
  simp; ring
#check @Set.OrdConnected.uIcc_subset
#check @Set.ordConnected_Ioi
#check @Filter.Eventually.frequently
#check @Filter.Eventually.of_forall
#check @Measurable.div
#check @ENNReal.ofReal_mul
example (x W : ℝ) : x / (2 * W) = x * (1 / W / 2) := by ring
