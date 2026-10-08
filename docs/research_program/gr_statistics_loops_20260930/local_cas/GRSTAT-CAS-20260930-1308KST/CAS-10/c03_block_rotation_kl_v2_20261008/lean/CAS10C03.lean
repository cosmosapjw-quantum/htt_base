import Mathlib

/-!
CAS-10-C03 v2: exact finite block rotation and common-covariance KL quadratic.
The blocks are ordered (Z₀, Z₁, m, p, T), of dimensions (1,3,1,3,5).
This file proves only the finite algebra specified by the frozen contract.
-/

namespace CAS10C03

def R : Matrix (Fin 3) (Fin 3) ℝ := !![0, -1, 0; 1, 0, 0; 0, 0, 1]

theorem R_orthogonal : R.transpose * R = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    norm_num [R, Matrix.mul_apply, Fin.sum_univ_succ, Matrix.transpose_apply]

theorem R_det : R.det = 1 := by
  have h00 : R 0 0 = 0 := by rfl
  have h01 : R 0 1 = -1 := by rfl
  have h02 : R 0 2 = 0 := by rfl
  have h10 : R 1 0 = 1 := by rfl
  have h11 : R 1 1 = 0 := by rfl
  have h12 : R 1 2 = 0 := by rfl
  have h20 : R 2 0 = 0 := by rfl
  have h21 : R 2 1 = 0 := by rfl
  have h22 : R 2 2 = 1 := by rfl
  rw [Matrix.det_fin_three]
  norm_num [h00, h01, h02, h10, h11, h12, h20, h21, h22]

noncomputable def p (H : ℝ) : Fin 3 → ℝ := ![15 * H / 8, 0, 0]
noncomputable def pPrime (H : ℝ) : Fin 3 → ℝ := ![0, 15 * H / 8, 0]

theorem R_maps_p (H : ℝ) : R.mulVec (p H) = pPrime H := by
  ext i
  fin_cases i <;> simp [R, p, pPrime, Matrix.mulVec, dotProduct, Fin.sum_univ_succ]

def sqNorm {n : ℕ} (v : Fin n → ℝ) : ℝ := ∑ i, v i ^ 2

theorem R_preserves_sqNorm (v : Fin 3 → ℝ) :
    sqNorm (R.mulVec v) = sqNorm v := by
  simp [sqNorm, R, Matrix.mulVec, dotProduct, Fin.sum_univ_succ]
  ring

theorem slope_norm_eq (H : ℝ) : sqNorm (p H) = sqNorm (pPrime H) := by
  simp [sqNorm, p, pPrime, Fin.sum_univ_succ]

structure Mean where
  z0 : ℝ
  z1 : Fin 3 → ℝ
  m : ℝ
  p : Fin 3 → ℝ
  t : Fin 5 → ℝ

noncomputable def first (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) : Mean :=
  ⟨z0, z1, m, p H, t⟩

noncomputable def second (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) : Mean :=
  ⟨z0, z1, m, pPrime H, t⟩

def rotate (u : Mean) : Mean :=
  ⟨u.z0, u.z1, u.m, R.mulVec u.p, u.t⟩

theorem rotate_first (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) :
    rotate (first H z0 m z1 t) = second H z0 m z1 t := by
  simp [rotate, first, second, R_maps_p]

theorem rotate_preserves_block_norms (u : Mean) :
    (rotate u).z0 ^ 2 = u.z0 ^ 2 ∧
    sqNorm (rotate u).z1 = sqNorm u.z1 ∧
    (rotate u).m ^ 2 = u.m ^ 2 ∧
    sqNorm (rotate u).p = sqNorm u.p ∧
    sqNorm (rotate u).t = sqNorm u.t := by
  simp [rotate, R_preserves_sqNorm]

theorem block_norms_agree (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) :
    (first H z0 m z1 t).z0 ^ 2 = (second H z0 m z1 t).z0 ^ 2 ∧
    sqNorm (first H z0 m z1 t).z1 = sqNorm (second H z0 m z1 t).z1 ∧
    (first H z0 m z1 t).m ^ 2 = (second H z0 m z1 t).m ^ 2 ∧
    sqNorm (first H z0 m z1 t).p = sqNorm (second H z0 m z1 t).p ∧
    sqNorm (first H z0 m z1 t).t = sqNorm (second H z0 m z1 t).t := by
  simp [first, second, slope_norm_eq]

-- This is the quadratic (μ₁-μ₂)ᵀΣ⁻¹(μ₁-μ₂) for the declared
-- positive block covariance diag(σ₀² I₁, σ₁² I₃, σₘ² I₁, σₚ² I₃, σₜ² I₅).
noncomputable def weightedQuadratic (σ0 σ1 σm σp σt : ℝ) (u v : Mean) : ℝ :=
  (u.z0 - v.z0)^2 / σ0^2 +
  sqNorm (fun i => u.z1 i - v.z1 i) / σ1^2 +
  (u.m - v.m)^2 / σm^2 +
  sqNorm (fun i => u.p i - v.p i) / σp^2 +
  sqNorm (fun i => u.t i - v.t i) / σt^2

noncomputable def KLQuadratic (σ0 σ1 σm σp σt : ℝ) (u v : Mean) : ℝ :=
  (1 / 2) * weightedQuadratic σ0 σ1 σm σp σt u v

theorem block_variances_positive (σ0 σ1 σm σp σt : ℝ)
    (hσ0 : 0 < σ0) (hσ1 : 0 < σ1) (hσm : 0 < σm)
    (hσp : 0 < σp) (hσt : 0 < σt) :
    0 < σ0^2 ∧ 0 < σ1^2 ∧ 0 < σm^2 ∧ 0 < σp^2 ∧ 0 < σt^2 := by
  exact ⟨sq_pos_of_pos hσ0, sq_pos_of_pos hσ1, sq_pos_of_pos hσm,
    sq_pos_of_pos hσp, sq_pos_of_pos hσt⟩

theorem kl_formula (H z0 m σ0 σ1 σm σp σt : ℝ)
    (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ)
    (_hσ0 : 0 < σ0) (_hσ1 : 0 < σ1) (_hσm : 0 < σm)
    (hσp : 0 < σp) (_hσt : 0 < σt) :
    KLQuadratic σ0 σ1 σm σp σt
      (first H z0 m z1 t) (second H z0 m z1 t) = 225 * H^2 / (64 * σp^2) := by
  have hn : σp ≠ 0 := ne_of_gt hσp
  simp [KLQuadratic, weightedQuadratic, first, second, sqNorm,
    p, pPrime, Fin.sum_univ_succ]
  field_simp
  ring

theorem control_zero (z0 m σ0 σ1 σm σp σt : ℝ)
    (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ)
    (hσ0 : 0 < σ0) (hσ1 : 0 < σ1) (hσm : 0 < σm)
    (hσp : 0 < σp) (hσt : 0 < σt) :
    KLQuadratic σ0 σ1 σm σp σt
      (first 0 z0 m z1 t) (second 0 z0 m z1 t) = 0 := by
  rw [kl_formula _ _ _ _ _ _ _ _ _ _ hσ0 hσ1 hσm hσp hσt]
  norm_num

theorem control_one (z0 m σ0 σ1 σm σt : ℝ)
    (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ)
    (hσ0 : 0 < σ0) (hσ1 : 0 < σ1) (hσm : 0 < σm)
    (hσt : 0 < σt) :
    KLQuadratic σ0 σ1 σm 1 σt
      (first 1 z0 m z1 t) (second 1 z0 m z1 t) = 225 / 64 := by
  rw [kl_formula _ _ _ _ _ _ _ _ _ _ hσ0 hσ1 hσm (by norm_num) hσt]
  norm_num

end CAS10C03
