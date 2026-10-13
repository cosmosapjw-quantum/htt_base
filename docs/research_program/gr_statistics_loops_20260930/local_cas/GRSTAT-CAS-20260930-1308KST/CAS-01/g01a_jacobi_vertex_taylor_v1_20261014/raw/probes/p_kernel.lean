import Mathlib
open Set intervalIntegral
example (s x : ℝ) : HasDerivAt (fun t => s * t ^ 2 / 2 - t ^ 3 / 3) ((s - x) * x) x := by
    have h1 := ((hasDerivAt_pow 2 x).const_mul s).div_const 2
    have h2 := (hasDerivAt_pow 3 x).div_const 3
    exact (h1.sub h2).congr_deriv (by norm_num; ring)
