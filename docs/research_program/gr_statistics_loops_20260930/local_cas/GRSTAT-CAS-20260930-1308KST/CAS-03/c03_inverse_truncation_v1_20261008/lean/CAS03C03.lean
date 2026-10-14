import Mathlib

namespace CAS03C03

noncomputable section

abbrev M := Matrix (Fin 3) (Fin 3) ℝ
abbrev V := Matrix (Fin 3) (Fin 1) ℝ

def H (D : M) : ℝ := D.trace / 3
def sigma (D : M) : M := D - H D • 1
def h1 (D : M) (β : V) : V := (-2 : ℝ) • (D * β)
def betaTrunc (D : M) (_hH : H D ≠ 0) (h : V) : V :=
  (-(1 / (2 * H D)) : ℝ) • ((1 - (1 / H D) • sigma D) * h)

theorem trace_sigma (D : M) : (sigma D).trace = 0 := by
  simp [sigma, H, Matrix.trace_sub, Matrix.trace_smul, Matrix.trace_one]

theorem exact_inverse (D : M) (β : V) (hdet : D.det ≠ 0) :
    β = (-(1 / 2 : ℝ)) • (D⁻¹ * h1 D β) := by
  have hu : IsUnit D.det := isUnit_iff_ne_zero.mpr hdet
  simp [h1, Matrix.mul_smul, ← Matrix.mul_assoc, Matrix.nonsing_inv_mul D hu,
    Matrix.one_mul, smul_smul]

theorem split (D : M) : D = sigma D + H D • 1 := by
  simp [sigma]

private theorem algebra_operator (S : M) (t : ℝ) (ht : t ≠ 0) :
    1 - (1 / t) • ((1 - (1 / t) • S) * (S + t • 1)) =
      (1 / t^2) • (S * S) := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_three, Matrix.one_apply] <;>
    field_simp <;> ring

theorem operator_defect (D : M) (hH : H D ≠ 0) :
    1 - (1 / H D) • ((1 - (1 / H D) • sigma D) * D) =
      (1 / (H D)^2) • (sigma D * sigma D) := by
  simpa only [← split D] using algebra_operator (sigma D) (H D) hH

theorem trunc_defect (D : M) (β : V) (hH : H D ≠ 0) :
    β - betaTrunc D hH (h1 D β) =
      (1 / (H D)^2) • ((sigma D * sigma D) * β) := by
  simp only [betaTrunc, h1, Matrix.mul_smul, smul_smul]
  have hc : (-(1 / (2 * H D)) * (-2 : ℝ)) = 1 / H D := by
    field_simp
  rw [hc]
  calc
    β - (1 / H D) • ((1 - (1 / H D) • sigma D) * (D * β)) =
        (1 - (1 / H D) • ((1 - (1 / H D) • sigma D) * D)) * β := by
          simp [Matrix.sub_mul, Matrix.smul_mul, Matrix.mul_assoc]
    _ = (1 / (H D)^2) • ((sigma D * sigma D) * β) := by
      rw [operator_defect D hH, Matrix.smul_mul]

def zeroHD : M := fun i j =>
  if i = j then (if i = 0 then 1 else if i = 1 then 1 else -2) else 0

private theorem f20 : (2 : Fin 3) ≠ 0 := by decide
private theorem f21 : (2 : Fin 3) ≠ 1 := by decide
private theorem f02 : (0 : Fin 3) ≠ 2 := by decide
private theorem f12 : (1 : Fin 3) ≠ 2 := by decide

theorem zeroH_control : H zeroHD = 0 ∧ zeroHD.det = -2 := by
  constructor
  · norm_num [H, zeroHD, Matrix.trace, Fin.sum_univ_three, f20, f21]
  · norm_num [zeroHD, Matrix.det_fin_three, f20, f21, f02, f12]

theorem zeroH_exact_inverse (β : V) :
    β = (-(1 / 2 : ℝ)) • (zeroHD⁻¹ * h1 zeroHD β) := by
  apply exact_inverse
  rw [zeroH_control.2]
  norm_num

def rationalD : M := fun i j =>
  if i = j then (if i = 0 then 3/2 else 3/4) else 0
def rationalBeta (ε : ℝ) : V := fun i _ => if i = 0 then ε else 0
def rationalTrunc (ε : ℝ) : V := fun i _ => if i = 0 then 3*ε/4 else 0
def rationalDefect (ε : ℝ) : V := fun i _ => if i = 0 then ε/4 else 0

theorem rational_H : H rationalD = 1 := by
  norm_num [H, rationalD, Matrix.trace, Fin.sum_univ_three, f20]

theorem rational_det : rationalD.det = 27 / 32 := by
  norm_num [rationalD, Matrix.det_fin_three, f20, f21, f02, f12]

theorem rational_exact_inverse (ε : ℝ) :
    rationalBeta ε =
      (-(1 / 2 : ℝ)) • (rationalD⁻¹ * h1 rationalD (rationalBeta ε)) := by
  apply exact_inverse
  rw [rational_det]
  norm_num

theorem rational_normalized_D :
    (1 / H rationalD) • rationalD =
      (fun i j => if i = j then (if i = 0 then 3/2 else 3/4) else 0) := by
  rw [rational_H]
  simp
  rfl

theorem rational_sigma :
    sigma rationalD = (fun i j =>
      if i = j then (if i = 0 then 1/2 else -1/4) else 0) := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp only [sigma, rational_H]
    <;> norm_num [rationalD, f20, f21, f02, f12]

theorem rational_normalized_sigma :
    (1 / H rationalD) • sigma rationalD =
      (fun i j => if i = j then (if i = 0 then 1/2 else -1/4) else 0) := by
  rw [rational_H]
  simpa using rational_sigma

theorem rational_beta_trunc (ε : ℝ) :
    betaTrunc rationalD (by rw [rational_H]; norm_num) (h1 rationalD (rationalBeta ε)) =
      rationalTrunc ε := by
  simp only [betaTrunc, h1, rational_H, rational_sigma]
  ext i j
  fin_cases i <;> fin_cases j <;>
    norm_num [rationalD, rationalBeta, rationalTrunc,
      Matrix.mul_apply, Fin.sum_univ_three, Matrix.one_apply, f20, f21, f02, f12]
    <;> ring

theorem rational_defect (ε : ℝ) :
    rationalBeta ε -
      betaTrunc rationalD (by rw [rational_H]; norm_num) (h1 rationalD (rationalBeta ε)) =
        rationalDefect ε := by
  rw [rational_beta_trunc]
  ext i j
  fin_cases i <;> fin_cases j <;>
    norm_num [rationalBeta, rationalTrunc, rationalDefect]
    <;> ring

#print axioms trace_sigma
#print axioms exact_inverse
#print axioms operator_defect
#print axioms trunc_defect
#print axioms zeroH_control
#print axioms zeroH_exact_inverse
#print axioms rational_H
#print axioms rational_det
#print axioms rational_exact_inverse
#print axioms rational_normalized_D
#print axioms rational_sigma
#print axioms rational_normalized_sigma
#print axioms rational_beta_trunc
#print axioms rational_defect

end
end CAS03C03
