import Mathlib
open MeasureTheory
example (a b : ℝ) : inner ℝ a b = a * b := by simp [mul_comm]
example (a b : ℝ) : inner ℝ a b = a * b := by rw [RCLike.inner_apply, conj_trivial]
example : ENNReal.HolderTriple 2 2 1 := inferInstance
#check @MemLp.toLp_congr
#check @withDensity_absolutelyContinuous
#check @integrable_congr
#check @Matrix.mulVec_single_one
#check @Real.abs_le_sqrt
#check @FiniteDimensional.complete
#check @abs_real_inner_le_norm
#check @Submodule.span_induction
#check @Submodule.span_empty
#check @IsComplete.completeSpace_coe
example : MeasurableSingletonClass Unit := inferInstance
