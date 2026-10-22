import Mathlib
abbrev V3 := Fin 3 → ℝ
def dot3 (a b : V3) : ℝ := a 0 * b 0 + a 1 * b 1 + a 2 * b 2
noncomputable def zeta0 (ζ : V3) : ℝ := Real.sqrt (1 + dot3 ζ ζ)
noncomputable def zeta0Deriv (ζ : V3) : V3 →ₗ[ℝ] ℝ where
  toFun δ := dot3 ζ δ / zeta0 ζ
  map_add' a b := by simp only [dot3, Pi.add_apply]; ring
  map_smul' t a := by simp only [dot3, Pi.smul_apply, smul_eq_mul, RingHom.id_apply]; ring
theorem one_le_one_add_dot3 (ζ : V3) : 1 ≤ 1 + dot3 ζ ζ := by
  simp only [dot3]; nlinarith [sq_nonneg (ζ 0), sq_nonneg (ζ 1), sq_nonneg (ζ 2)]
example (ζ : V3) : HasFDerivAt zeta0 (LinearMap.toContinuousLinearMap (zeta0Deriv ζ)) ζ := by
  have p : ∀ k : Fin 3, HasFDerivAt (fun y : V3 => y k)
      (ContinuousLinearMap.proj (R := ℝ) (φ := fun _ : Fin 3 => ℝ) k) ζ :=
    fun k => hasFDerivAt_apply k ζ
  have hf := ((((p 0).mul (p 0)).add ((p 1).mul (p 1))).add ((p 2).mul (p 2))).const_add 1
  have hpos : 0 < 1 + dot3 ζ ζ := lt_of_lt_of_le one_pos (one_le_one_add_dot3 ζ)
  have hs := hf.sqrt (by simp only [Pi.add_apply, Pi.mul_apply]; exact hpos.ne')
  have hs' := hs.congr_of_eventuallyEq (f₁ := zeta0)
    (Filter.Eventually.of_forall fun y => by simp [zeta0, dot3])
  refine hs'.congr_fderiv ?_
  apply ContinuousLinearMap.ext
  intro δ
  have hsq : 0 < Real.sqrt (1 + dot3 ζ ζ) := Real.sqrt_pos.mpr hpos
  simp [zeta0Deriv, zeta0, dot3] at hsq ⊢
  field_simp
  ring
