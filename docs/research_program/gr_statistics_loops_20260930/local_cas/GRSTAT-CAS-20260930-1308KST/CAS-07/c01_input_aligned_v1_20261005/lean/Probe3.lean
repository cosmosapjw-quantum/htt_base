import Mathlib
example : Real.instAddCommGroup = Real.normedAddCommGroup.toAddCommGroup := by rfl
example : (Semiring.toModule : Module ℝ ℝ) = RCLike.toInnerProductSpaceReal.toModule := by rfl
