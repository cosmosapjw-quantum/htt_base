import Mathlib
open MeasureTheory
#check @isFiniteMeasure_withDensity_ofReal
#check @Matrix.det_zero_of_row_eq
#check @Metric.infDist_eq_iInf
#check @MemLp.integrable_mul
#check @lintegral_dirac
#check @integral_dirac
#check @Submodule.starProjection_bot
#check @LinearMap.IsSymmetric.eigenvectorBasis_apply_self_apply
#check @OrthonormalBasis.inner_eq_sum
#check @Real.log_two_lt_d9
#check @Submodule.mem_orthogonal
#check @Submodule.inner_right_of_mem_orthogonal
#check @lintegral_withDensity_eq_lintegral_mul
#check @Matrix.dotProduct_mulVec
example : (2:ENNReal) ≠ 0 := by norm_num
example : Fact ((1:ENNReal) ≤ 2) := inferInstance
