import Mathlib
example (x : ℝ) : HasDerivAt (fun t : ℝ => t^3) (3*x^2) x := by simpa using (hasDerivAt_pow 3 x)
