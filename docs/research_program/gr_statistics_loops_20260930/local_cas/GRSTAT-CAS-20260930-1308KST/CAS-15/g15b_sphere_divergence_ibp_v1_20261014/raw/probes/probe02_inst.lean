import Mathlib
abbrev E3 := EuclideanSpace ℝ (Fin 3)
example : CompleteSpace (E3 →L[ℝ] E3) := inferInstance
example : CompleteSpace (E3 →L[ℝ] E3) := ContinuousLinearMap.completeSpace
#check @ContinuousLinearMap.completeSpace
noncomputable example : NormedAlgebra ℚ (E3 →L[ℝ] E3) := NormedAlgebra.restrictScalars ℚ ℝ _
