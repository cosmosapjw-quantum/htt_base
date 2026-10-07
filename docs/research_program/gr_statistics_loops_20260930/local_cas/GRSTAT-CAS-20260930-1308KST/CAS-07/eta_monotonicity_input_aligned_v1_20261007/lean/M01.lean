import Mathlib

/-! Frozen CAS-07-M01: exact scalar eta nonnegativity and monotonicity.
    No result from another CAS axis is imported. -/

namespace CAS07M01

noncomputable def fd (K t : ℝ) : ℝ :=
  if K = 0 then t else Real.sinh (Real.sqrt K * t) / Real.sqrt K

noncomputable def eta (K t : ℝ) : ℝ := fd K t / t - 1

private noncomputable def q (x : ℝ) : ℝ := x * Real.cosh x - Real.sinh x
private noncomputable def h (x : ℝ) : ℝ := Real.sinh x / x - 1

private lemma q_hasDerivAt (x : ℝ) : HasDerivAt q (x * Real.sinh x) x := by
  have hd := ((hasDerivAt_id x).mul (Real.hasDerivAt_cosh x)).sub (Real.hasDerivAt_sinh x)
  have hfun : q = Real.cosh * id - Real.sinh := by
    funext y
    simp [q, id, mul_comm]
  rw [hfun]
  simpa [id, mul_comm] using hd

private lemma x_mul_sinh_nonneg (x : ℝ) : 0 ≤ x * Real.sinh x := by
  rcases le_total 0 x with hx | hx
  · exact mul_nonneg hx (Real.sinh_nonneg_iff.mpr hx)
  · exact mul_nonneg_of_nonpos_of_nonpos hx (Real.sinh_nonpos_iff.mpr hx)

private lemma q_nonneg {x : ℝ} (hx : 0 ≤ x) : 0 ≤ q x := by
  have hmono : Monotone q := monotone_of_hasDerivAt_nonneg q_hasDerivAt x_mul_sinh_nonneg
  have hq := hmono hx
  simpa [q] using hq

private lemma h_hasDerivAt {x : ℝ} (hx : x ≠ 0) :
    HasDerivAt h (q x / x ^ 2) x := by
  have hd := HasDerivAt.sub_const 1 ((Real.hasDerivAt_sinh x).div (hasDerivAt_id x) hx)
  change HasDerivAt (fun y : ℝ => Real.sinh y / y - 1)
    ((x * Real.cosh x - Real.sinh x) / x ^ 2) x
  simpa [id, mul_comm] using hd

private lemma h_nonneg {x : ℝ} (hx : 0 < x) : 0 ≤ h x := by
  have hsinh : x ≤ Real.sinh x := Real.self_le_sinh_iff.mpr hx.le
  have hratio : 1 ≤ Real.sinh x / x := (le_div_iff₀ hx).2 (by simpa using hsinh)
  unfold h
  linarith

private lemma h_monotoneOn : MonotoneOn h (Set.Ioi (0 : ℝ)) := by
  apply monotoneOn_of_deriv_nonneg (convex_Ioi 0)
  · intro x hx
    exact (h_hasDerivAt hx.ne').continuousAt.continuousWithinAt
  · intro x hx
    rw [interior_Ioi] at hx
    exact (h_hasDerivAt hx.ne').differentiableAt.differentiableWithinAt
  · intro x hx
    rw [interior_Ioi] at hx
    rw [(h_hasDerivAt hx.ne').deriv]
    exact div_nonneg (q_nonneg hx.le) (sq_nonneg x)

private lemma eta_zero_branch {t : ℝ} (ht : 0 < t) : eta 0 t = 0 := by
  simp [eta, fd, ht.ne']

private lemma eta_positive_branch {K t : ℝ} (hK : 0 < K) (ht : 0 < t) :
    eta K t = h (Real.sqrt K * t) := by
  have hsqrt : 0 < Real.sqrt K := Real.sqrt_pos.2 hK
  have hK0 : K ≠ 0 := hK.ne'
  unfold eta fd h
  rw [if_neg hK0]
  field_simp

theorem eta_bounds
    {K s L : ℝ} (hK : 0 ≤ K) (hs : 0 < s) (hsL : s ≤ L)
    (hsmall : eta K L < 1) :
    0 ≤ eta K s ∧ eta K s ≤ eta K L ∧ eta K s < 1 := by
  have hL : 0 < L := hs.trans_le hsL
  rcases hK.eq_or_lt with rfl | hKpos
  · rw [eta_zero_branch hL] at hsmall
    rw [eta_zero_branch hs, eta_zero_branch hL]
    exact ⟨le_rfl, le_rfl, hsmall⟩
  · have hsqrt : 0 < Real.sqrt K := Real.sqrt_pos.2 hKpos
    have hxs : 0 < Real.sqrt K * s := mul_pos hsqrt hs
    have hxL : 0 < Real.sqrt K * L := mul_pos hsqrt hL
    have hxorder : Real.sqrt K * s ≤ Real.sqrt K * L := mul_le_mul_of_nonneg_left hsL hsqrt.le
    rw [eta_positive_branch hKpos hL] at hsmall
    rw [eta_positive_branch hKpos hs, eta_positive_branch hKpos hL]
    have hnonneg : 0 ≤ h (Real.sqrt K * s) := h_nonneg hxs
    have hmono : h (Real.sqrt K * s) ≤ h (Real.sqrt K * L) :=
      h_monotoneOn hxs hxL hxorder
    exact ⟨hnonneg, hmono, hmono.trans_lt hsmall⟩

#print axioms eta_bounds

end CAS07M01
