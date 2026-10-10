import Mathlib

/-!
G02-B: universal Gram eigenvalue bound only.
Faithful literal C03 excerpts from the immutable Cas02.lean
SHA-256 283f64377e49585c697c3cb51f04cacece79015b36fa3c8d4a8e2d640678b520.
The original Chart is a section, hence its declarations belong to Cas02.
Only gramVec and its eigenvalue/rapidity prerequisites are reproduced below;
no projection, mean-value, C04, or scientific admission is asserted.
-/

namespace Cas02
section Chart

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

noncomputable def gramVec (d h : E) : E :=
  h + (inner ℝ d h / (1 + ‖d‖ ^ 2)) • d

theorem C03_transverse (d h : E) (ho : inner ℝ d h = 0) : gramVec d h = h := by
  simp [gramVec, ho]
theorem C03_zero_repeated (h : E) : gramVec (0 : E) h = h := by
  simp [gramVec]

theorem C03_eigenvalue_only (d h : E) (eig : ℝ) (hh : h ≠ 0)
    (he : gramVec d h = eig • h) :
    eig = 1 ∨ eig = 1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2) := by
  by_cases ho : inner ℝ d h = 0
  · left
    have he' : h = eig • h := (C03_transverse d h ho).symm.trans he
    have hz : (eig - 1) • h = 0 := by
      rw [sub_smul, one_smul]
      exact sub_eq_zero.mpr he'.symm
    have := (smul_eq_zero.mp hz).resolve_right hh
    linarith
  · right
    have hp : (1 + ‖d‖ ^ 2) ≠ 0 := by positivity
    have he' := congrArg (fun x : E => inner ℝ d x) he
    simp only [gramVec, inner_add_right, real_inner_smul_right,
      real_inner_self_eq_norm_sq] at he'
    have hc : (1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2)) * inner ℝ d h =
        eig * inner ℝ d h := by
      calc
        _ = inner ℝ d h + inner ℝ d h / (1 + ‖d‖ ^ 2) * ‖d‖ ^ 2 := by ring
        _ = eig * inner ℝ d h := by simpa only [smul_eq_mul] using he'
    exact (mul_right_cancel₀ ho hc).symm
theorem ratio_mono {a b : ℝ} (ha : 0 ≤ a) (hab : a ≤ b) :
    a / (1 + a) ≤ b / (1 + b) := by
  have h1 : 0 < 1 + a := by linarith
  have h2 : 0 < 1 + b := by linarith
  apply (div_le_div_iff₀ h1 h2).2
  nlinarith

theorem C03_rapidity_bound (d : E) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2) ≤ 1 + Real.tanh R ^ 2 := by
  have hsinh : 0 ≤ Real.sinh R := le_trans (norm_nonneg _) hd
  have hR : 0 ≤ R := Real.sinh_nonneg_iff.mp hsinh
  have hsq : ‖d‖ ^ 2 ≤ Real.sinh R ^ 2 :=
    sq_le_sq₀ (norm_nonneg _) hsinh |>.2 hd
  have hratio := ratio_mono (sq_nonneg ‖d‖) hsq
  have hc : 1 + Real.sinh R ^ 2 = Real.cosh R ^ 2 := by
    nlinarith [Real.cosh_sq_sub_sinh_sq R]
  have hcosh : Real.cosh R ≠ 0 := ne_of_gt (Real.cosh_pos R)
  have ht : Real.sinh R ^ 2 / (1 + Real.sinh R ^ 2) = Real.tanh R ^ 2 := by
    rw [hc, Real.tanh_eq_sinh_div_cosh]
    field_simp
  rw [← ht]
  linarith

/-- Every real Gram eigenvalue has the rapidity upper bound, including d = 0. -/
theorem C03_gram_eigenvalue_upper_bound (d h : E) (R eig : ℝ)
    (hh : h ≠ 0) (he : gramVec d h = eig • h)
    (hd : ‖d‖ ≤ Real.sinh R) :
    eig ≤ 1 + Real.tanh R ^ 2 := by
  rcases C03_eigenvalue_only d h eig hh he with hunit | hlong
  · rw [hunit]
    linarith [sq_nonneg (Real.tanh R)]
  · rw [hlong]
    exact C03_rapidity_bound d R hd

end Chart
end Cas02

#check @Cas02.C03_gram_eigenvalue_upper_bound
#print axioms Cas02.C03_gram_eigenvalue_upper_bound
#check @Cas02.C03_zero_repeated
#print axioms Cas02.C03_zero_repeated
