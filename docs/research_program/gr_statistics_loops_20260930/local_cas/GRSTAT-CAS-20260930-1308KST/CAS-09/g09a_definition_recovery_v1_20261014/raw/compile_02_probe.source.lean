import Mathlib
abbrev V3 := Fin 3 → ℝ
example (ζ : V3) (f : V3 →L[ℝ] ℝ) : True := by
  have p : ∀ k : Fin 3, HasFDerivAt (fun y : V3 => y k)
      (ContinuousLinearMap.proj (R := ℝ) (φ := fun _ : Fin 3 => ℝ) k) ζ :=
    fun k => hasFDerivAt_apply k ζ
  have hf := ((((p 0).mul (p 0)).add ((p 1).mul (p 1))).add ((p 2).mul (p 2))).const_add 1
  have hs := hf.sqrt (by positivity)
  trace_state
  trivial
