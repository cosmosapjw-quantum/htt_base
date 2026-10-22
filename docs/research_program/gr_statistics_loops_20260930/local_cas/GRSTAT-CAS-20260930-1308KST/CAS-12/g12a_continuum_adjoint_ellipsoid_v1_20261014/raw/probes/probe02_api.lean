import Mathlib
open MeasureTheory
#check @MeasureTheory.withDensity_absolutelyContinuous'
#check @Measure.measure_univ_ne_zero
#check @measurable_of_countable
#check @MeasureTheory.lintegral_fintype
#check @ENNReal.sum_ne_top
#check @MeasureTheory.MemLp.of_bound
#check @MeasureTheory.isFiniteMeasure_withDensity_ofReal
#check @Fintype.sum_bool
#check @MeasureTheory.MeasurePreserving.id
#check @MeasureTheory.MeasurePreserving.comp
#check @MeasureTheory.MemLp.integrable
#check @MeasureTheory.integral_finset_sum
#check @Measure.AbsolutelyContinuous.ae_le
#check @mem_sphere_zero_iff_norm
#check @abs_real_inner_le_norm
#check @sq_le_one_iff_abs_le_one
#check @MeasurableEquiv.measurableEmbedding
#check @Real.add_one_lt_exp
#check @ContinuousLinearMap.adjoint
#check @ContinuousLinearMap.eq_adjoint_iff
#check @LinearMap.mkContinuous
#check @MeasureTheory.Measure.ae_ae_of_ae_prod
example (b : ℝ) : Measurable fun E : ℝ => Real.exp (b * E) / (Real.exp (b * E) - 1) ^ 2 := by fun_prop
example (u : Bool → ℝ) : ∫ e, u e ∂(Measure.count : Measure Bool) = u true + u false := by
  rw [integral_fintype _ Integrable.of_finite]; simp [Measure.real, Measure.count_singleton]
