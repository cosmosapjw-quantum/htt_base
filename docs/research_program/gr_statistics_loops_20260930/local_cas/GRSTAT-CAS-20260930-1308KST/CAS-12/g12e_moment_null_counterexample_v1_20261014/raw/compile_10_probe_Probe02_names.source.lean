import Mathlib
import G11AGuarded
open MeasureTheory
#check @integral_finsetSum
#check @ContDiff.sum
#check @Measure.restrict_restrict
#check @Real.volume_ball
#check @measure_ball_pos
#check @finrank_euclideanSpace_fin
#check @integrableOn_const
#check @Measure.integrableOn_of_bounded
#check @HasCompactSupport.intro
#check @Finset.abs_sum_le_sum_abs
#check @Matrix.mulVecLin
#check @Matrix.mulVecLin_apply
#check @Module.finrank_fin_fun
#check @Submodule.ne_bot_iff
#check @integral_const_mul
#check @integral_mul_left
#check @setLIntegral_const
#check @ENNReal.mul_pos
#check @integral_sub
#check @integral_indicator
#check @integrable_indicator_iff
#check @IntegrableOn.integrable_indicator
#check @Finset.exists_ne_zero_of_sum_ne_zero
#check @Integrable.mono'
#check @ContDiffBump.mk
#check @Real.continuous_log
#check @ContinuousOn.log
#check @tendsto_pow_atTop
#check @Filter.Tendsto.const_mul_atTop
#check @ae_restrict_iff'
#check @setIntegral_le_integral
#check @integral_mono_of_nonneg
#check @lintegral_indicator_const
#check @lintegral_mono
#check @Measure.prod_apply
example : SFinite G11A.dOmega := inferInstance
example : IsFiniteMeasure G11A.dOmega := inferInstance
example (C : ℝ) : SFinite (G11A.nu C) := inferInstance
example : CompactSpace G11A.Sphere2 := inferInstance
example : BorelSpace (ℝ × G11A.Sphere2) := inferInstance
#print G11A.nu
