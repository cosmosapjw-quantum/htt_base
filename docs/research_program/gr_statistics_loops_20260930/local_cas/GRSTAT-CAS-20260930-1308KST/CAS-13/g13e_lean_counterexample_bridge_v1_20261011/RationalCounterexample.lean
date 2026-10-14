import Mathlib

namespace CAS13RationalCounterexample

theorem g13e_rational_counterexample :
    ∃ u : ℝ, (539 / 500 : ℝ) < u ∧ u < (1079 / 1000 : ℝ) ∧
      20625 * u ^ 3 - 9700 * u ^ 2 - 7760 * u - 6208 = 0 ∧
      (5698688 / 5078125 : ℝ) <
        (8250 * u ^ 4 + 6600 * u ^ 3 + 10400 * u ^ 2 + 8320 * u + 6656) /
          (15625 * u ^ 2 + 12500 * u + 10000) ∧
      (9619385344 / 8251953125 : ℝ) < 66 * u ^ 3 / 125 + 1664 / 3125 := by
  let p : ℝ → ℝ := fun u => 20625 * u ^ 3 - 9700 * u ^ 2 - 7760 * u - 6208
  have hc : ContinuousOn p (Set.Icc (539 / 500 : ℝ) (1079 / 1000)) := by
    fun_prop
  have hz : (0 : ℝ) ∈ Set.Ioo (p (539 / 500)) (p (1079 / 1000)) := by
    norm_num [p]
  obtain ⟨u, hu, hpu⟩ := intermediate_value_Ioo (by norm_num :
    (539 / 500 : ℝ) ≤ 1079 / 1000) hc hz
  refine ⟨u, hu.1, hu.2, hpu, ?_, ?_⟩
  · have ht : 0 < u - 539 / 500 := sub_pos.mpr hu.1
    have hd : 0 < 15625 * u ^ 2 + 12500 * u + 10000 := by
      have hu0 : 0 < u := lt_trans (by norm_num) hu.1
      positivity
    apply (lt_div_iff₀ hd).mpr
    have hi :
        (8250 * u ^ 4 + 6600 * u ^ 3 + 10400 * u ^ 2 + 8320 * u + 6656) -
          (5698688 / 5078125 : ℝ) * (15625 * u ^ 2 + 12500 * u + 10000) =
        8250 * (u - 539 / 500) ^ 4 + 42174 * (u - 539 / 500) ^ 3 +
        (466265367 / 6500 : ℝ) * (u - 539 / 500) ^ 2 +
        (70297305411 / 1625000 : ℝ) * (u - 539 / 500) +
        (1298565438669 / 3250000000 : ℝ) := by ring
    have hp : 0 <
        (8250 * u ^ 4 + 6600 * u ^ 3 + 10400 * u ^ 2 + 8320 * u + 6656) -
          (5698688 / 5078125 : ℝ) * (15625 * u ^ 2 + 12500 * u + 10000) := by
      rw [hi]
      positivity
    linarith
  · have ht : 0 < u - 539 / 500 := sub_pos.mpr hu.1
    have hi : 66 * u ^ 3 / 125 + (1664 / 3125 : ℝ) -
        (9619385344 / 8251953125 : ℝ) =
        (66 / 125 : ℝ) * (u - 539 / 500) ^ 3 +
        (53361 / 31250 : ℝ) * (u - 539 / 500) ^ 2 +
        (28761579 / 15625000 : ℝ) * (u - 539 / 500) +
        (37245342523 / 1320312500000 : ℝ) := by ring
    have hp : 0 < 66 * u ^ 3 / 125 + (1664 / 3125 : ℝ) -
        (9619385344 / 8251953125 : ℝ) := by
      rw [hi]
      positivity
    linarith

end CAS13RationalCounterexample

#print axioms CAS13RationalCounterexample.g13e_rational_counterexample
