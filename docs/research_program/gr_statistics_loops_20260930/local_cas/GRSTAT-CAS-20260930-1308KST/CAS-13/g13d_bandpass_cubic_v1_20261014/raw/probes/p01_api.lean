import Mathlib
import MeasureExtremizerBridge
import PowerJet

open MeasureTheory Set

example (a b : ℝ) : |a + b| ≤ |a| + |b| := abs_add_le a b
example : ((3 : WithTop ℕ∞) + 1 ≤ 4) := by norm_num
example : ((2 : WithTop ℕ∞) + 1 = 3) := by norm_num
example : ((0 : WithTop ℕ∞) + 1 = 1) := by norm_num
example : ((1 : WithTop ℕ∞) ≠ 0) := by norm_num
example : ¬ ((2 : WithTop ℕ∞) = ω) := by simp
example (π : Measure ℝ) [IsProbabilityMeasure π] : IsFiniteMeasureOnCompacts π := inferInstance
example (x : ℝ) (hx : 0 < x) : 1 < Real.exp x := by linarith [Real.add_one_le_exp x]
example (x p : ℝ) (hx : 0 < x) : HasDerivAt (fun y : ℝ => y ^ p) (p * x ^ (p - 1)) x :=
  Real.hasDerivAt_rpow_const (Or.inl hx.ne')
#check @CAS13MeasureComposition.integral_hermite
#check @CAS13MeasureComposition.moment_twoDirac
#check @Cas13C01.dq3
#check @ContDiffOn.fderiv_of_isOpen
