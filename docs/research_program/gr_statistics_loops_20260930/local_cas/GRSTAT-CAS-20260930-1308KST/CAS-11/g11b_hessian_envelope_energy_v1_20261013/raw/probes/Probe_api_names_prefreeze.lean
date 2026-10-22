import Mathlib
import G11AGuarded
open MeasureTheory Set Filter Topology
#check @intervalIntegral.integral_eq_sub_of_hasDerivAt
#check @intervalIntegral.integral_mono_on
#check @ContinuousOn.intervalIntegrable
#check @MeasureTheory.lintegral_liminf_le
#check @MeasureTheory.lintegral_liminf_le'
#check @MeasureTheory.lintegral_const_mul'
#check @Ioo_mem_nhdsLT
#check @Filter.Tendsto.liminf_eq
#check @Filter.liminf_le_of_le
#check @Filter.liminf_le_of_frequently_le'
#check @integral_mono_ae
#check @MeasureTheory.integral_const_mul
#check @le_of_tendsto_of_tendsto
#check @G11A.WEnvelope_bounds_hessian
#check @G11A.W_lower_bounds_hessian
#check @G11A.hasDerivAt_hS'
#check @G11A.continuous_bregDens_left
#check @lintegral_mono_ae
example : ∫ x in (0:ℝ)..1, (1 - x) = 1/2 := by norm_num [integral_sub, integral_id]
