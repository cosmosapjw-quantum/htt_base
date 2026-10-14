import Mathlib
abbrev E3 := EuclideanSpace ℝ (Fin 3)
instance instCLMComplete : CompleteSpace (E3 →L[ℝ] E3) := ContinuousLinearMap.instCompleteSpace
example : CompleteSpace (E3 →L[ℝ] E3) := inferInstance
noncomputable example : NormedAlgebra ℚ (E3 →L[ℝ] E3) := NormedAlgebra.restrictScalars ℚ ℝ _
open NormedSpace in
example (W : E3 →L[ℝ] E3) (t : ℝ) : HasDerivAt (fun u : ℝ => NormedSpace.exp (u • W)) (NormedSpace.exp (t • W) * W) t := hasDerivAt_exp_smul_const W t
