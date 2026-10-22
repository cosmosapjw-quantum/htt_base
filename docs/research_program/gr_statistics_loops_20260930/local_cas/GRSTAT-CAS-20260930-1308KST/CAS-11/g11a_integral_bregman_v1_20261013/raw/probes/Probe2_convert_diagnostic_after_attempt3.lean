import Mathlib
inductive Stat
  | MB
  | BE
  | FD
def xi : Stat → ℝ
  | .MB => 0
  | .BE => 1
  | .FD => -1
noncomputable def hS' (s : Stat) (f : ℝ) : ℝ := Real.log (f / (1 + xi s * f))
example (x : ℝ) (hx0 : 0 < x) : HasDerivAt (fun y => y * Real.log y - y) (hS' .MB x) x := by
  have := (Real.hasDerivAt_mul_log hx0.ne').sub (hasDerivAt_id' x)
  convert this using 1
  trace_state
  simp [hS', xi]
