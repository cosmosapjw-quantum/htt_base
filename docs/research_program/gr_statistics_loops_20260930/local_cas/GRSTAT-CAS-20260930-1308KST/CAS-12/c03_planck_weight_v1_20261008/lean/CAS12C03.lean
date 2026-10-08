import Mathlib

/-! Exact CAS-12-C03 Planck weight component. -/

namespace CAS12C03

open Filter
open scoped Topology

private theorem exp_sub_one_ne_zero {x : ℝ} (hx : 0 < x) : Real.exp x - 1 ≠ 0 := by
  have h : 1 < Real.exp x := by simpa using Real.exp_lt_exp.mpr hx
  linarith

theorem hyperbolic_identity (b E : ℝ) (hb : 0 < b) (hE : 0 < E) :
    Real.exp (b * E) / (Real.exp (b * E) - 1) ^ 2 =
      1 / (4 * Real.sinh (b * E / 2) ^ 2) := by
  let t := Real.exp (b * E / 2)
  have ht : t ≠ 0 := Real.exp_ne_zero _
  have hfull : Real.exp (b * E) = t ^ 2 := by
    rw [show b * E = b * E / 2 + b * E / 2 by ring, Real.exp_add]
    change t * t = t ^ 2
    ring
  have ht2 : t ^ 2 - 1 ≠ 0 := by
    rw [← hfull]
    exact exp_sub_one_ne_zero (mul_pos hb hE)
  have hsinh : Real.sinh (b * E / 2) = (t ^ 2 - 1) / (2 * t) := by
    rw [Real.sinh_eq, Real.exp_neg]
    change (t - t⁻¹) / 2 = (t ^ 2 - 1) / (2 * t)
    field_simp
  rw [hsinh, hfull]
  field_simp
  ring

theorem scaled_right_limit (b : ℝ) (hb : 0 < b) :
    Filter.Tendsto
      (fun E : ℝ => E ^ 2 * Real.exp (b * E) / (Real.exp (b * E) - 1) ^ 2)
      (nhdsWithin (0 : ℝ) (Set.Ioi 0)) (𝓝 (1 / b ^ 2)) := by
  have hb0 : b ≠ 0 := ne_of_gt hb
  have hd : HasDerivAt (fun E : ℝ => Real.exp (b * E)) b 0 := by
    have hlin : HasDerivAt (fun E : ℝ => b * E) b 0 := by
      simpa using (hasDerivAt_id (0 : ℝ)).const_mul b
    simpa [Function.comp_def] using (Real.hasDerivAt_exp (b * (0 : ℝ))).comp 0 hlin
  have hq : Filter.Tendsto (fun E : ℝ => (Real.exp (b * E) - 1) / E)
      (nhdsWithin (0 : ℝ) (Set.Ioi 0)) (𝓝 b) := by
    simpa [slope_fun_def_field, Real.exp_zero, div_eq_mul_inv, mul_comm] using
      hd.tendsto_slope_zero_right
  have he : Filter.Tendsto (fun E : ℝ => Real.exp (b * E))
      (nhdsWithin (0 : ℝ) (Set.Ioi 0)) (𝓝 (1 : ℝ)) := by
    have hc : Continuous (fun E : ℝ => Real.exp (b * E)) :=
      Real.continuous_exp.comp (continuous_const.mul continuous_id)
    simpa using (hc.tendsto (0 : ℝ)).mono_left nhdsWithin_le_nhds
  have hlim : Filter.Tendsto
      (fun E : ℝ => Real.exp (b * E) / (((Real.exp (b * E) - 1) / E) ^ 2))
      (nhdsWithin (0 : ℝ) (Set.Ioi 0)) (𝓝 (1 / b ^ 2)) := by
    exact he.div (hq.pow 2) (pow_ne_zero 2 hb0)
  apply hlim.congr'
  filter_upwards [self_mem_nhdsWithin] with E hE
  have hE0 : E ≠ 0 := ne_of_gt hE
  have hden : Real.exp (b * E) - 1 ≠ 0 := exp_sub_one_ne_zero (mul_pos hb hE)
  field_simp

/-- The exact degree-eight Taylor polynomial of `exp x`. -/
noncomputable def exp8 : Polynomial ℚ :=
  1 + Polynomial.X + (1 / 2 : ℚ) • Polynomial.X ^ 2 +
    (1 / 6 : ℚ) • Polynomial.X ^ 3 + (1 / 24 : ℚ) • Polynomial.X ^ 4 +
    (1 / 120 : ℚ) • Polynomial.X ^ 5 + (1 / 720 : ℚ) • Polynomial.X ^ 6 +
    (1 / 5040 : ℚ) • Polynomial.X ^ 7 + (1 / 40320 : ℚ) • Polynomial.X ^ 8

theorem exp8_coeff (n : Fin 9) : exp8.coeff n.val = (1 : ℚ) / n.val.factorial := by
  fin_cases n <;> norm_num [exp8, Polynomial.coeff_one, Polynomial.coeff_X]

/-- `x²` times the contracted Laurent candidate. -/
noncomputable def scaledLaurent : Polynomial ℚ :=
  1 - (1 / 12 : ℚ) • Polynomial.X ^ 2 +
    (1 / 240 : ℚ) • Polynomial.X ^ 4 - (1 / 6048 : ℚ) • Polynomial.X ^ 6

theorem scaledLaurent_substitution (b E : ℚ) :
    scaledLaurent.eval (b * E) =
      1 - b ^ 2 * E ^ 2 / 12 + b ^ 4 * E ^ 4 / 240 - b ^ 6 * E ^ 6 / 6048 := by
  simp [scaledLaurent]
  ring

noncomputable def residualQuotient : Polynomial ℚ :=
  (41 / 3628800 : ℚ) • (1 : Polynomial ℚ) +
  (23 / 3628800 : ℚ) • Polynomial.X +
  (23 / 6220800 : ℚ) • Polynomial.X ^ 2 +
  (19 / 14515200 : ℚ) • Polynomial.X ^ 3 +
  (1193 / 3048192000 : ℚ) • Polynomial.X ^ 4 +
  (943 / 9144576000 : ℚ) • Polynomial.X ^ 5 +
  (247 / 10450944000 : ℚ) • Polynomial.X ^ 6 +
  (173 / 36578304000 : ℚ) • Polynomial.X ^ 7 +
  (709 / 877879296000 : ℚ) • Polynomial.X ^ 8 +
  (13 / 109734912000 : ℚ) • Polynomial.X ^ 9 +
  (377 / 24580620288000 : ℚ) • Polynomial.X ^ 10 +
  (1 / 614515507200 : ℚ) • Polynomial.X ^ 11 +
  (1 / 9832248115200 : ℚ) • Polynomial.X ^ 12

/-- Clearing the double zero leaves no term below `x¹⁰`. -/
theorem formal_product_certificate :
    ∀ n : Fin 10,
      (Polynomial.X ^ 2 * exp8 - scaledLaurent * (exp8 - 1) ^ 2).coeff n.val = 0 := by
  have hfactor : Polynomial.X ^ 2 * exp8 - scaledLaurent * (exp8 - 1) ^ 2 =
      Polynomial.X ^ 10 * residualQuotient := by
    apply Polynomial.funext
    intro x
    simp [exp8, scaledLaurent, residualQuotient]
    ring
  intro n
  rw [hfactor, Polynomial.coeff_X_pow_mul']
  simp [Nat.not_le.mpr n.isLt]

#print axioms CAS12C03.hyperbolic_identity
#print axioms CAS12C03.scaled_right_limit
#print axioms CAS12C03.exp8_coeff
#print axioms CAS12C03.scaledLaurent_substitution
#print axioms CAS12C03.formal_product_certificate

end CAS12C03
