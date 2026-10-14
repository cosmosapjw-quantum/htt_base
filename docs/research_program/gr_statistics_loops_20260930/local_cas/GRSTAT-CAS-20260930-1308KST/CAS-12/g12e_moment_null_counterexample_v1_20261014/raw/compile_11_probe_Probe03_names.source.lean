import Mathlib
open MeasureTheory
#check @Set.indicator_of_notMem
#check @image_eq_zero_of_notMem_tsupport
#check @Measure.restrict_apply_le
#check @Continuous.bounded_above_of_compact_support
#check @isOpen_ne_fun
#check @inv_lt_inv₀
#check @ContinuousOn.inv₀
#check @withDensity_absolutelyContinuous
#check @Metric.measure_ball_pos
#check @Function.notMem_support
#check @Real.neg_one_le_sin
#check @Filter.Eventually.exists
#check @Set.prod_univ
#check @measurableSet_ball
#check @Filter.tendsto_pow_atTop
#check @ContDiffBump.pos_of_mem_ball
#check @HasDerivAt.mul_const
#check @HasDerivAt.const_mul
#check @Measurable.ennreal_ofReal
example (C : ℝ) : Measurable fun E : ℝ => ENNReal.ofReal (C * E ^ 2) := by fun_prop
example (b : ℝ) : Measurable fun E : ℝ => (Real.exp (b * E - 0) - 1)⁻¹ := by fun_prop
example (x : ℝ) (h : x ≠ 0) : 0 < x ^ 2 := by positivity
