import NonlinearRemainder
import CAS03C03

open ExactBoostMap NonlinearRemainder

namespace InverseTruncationSynthesis

noncomputable section

abbrev H (D : M3) : ℝ := CAS03C03.H D
abbrev sigma (D : M3) : M3 := CAS03C03.sigma D
def toCol (v : V3) : CAS03C03.V := fun i _ => v i
def fromCol (v : CAS03C03.V) : V3 := fun i => v i 0
def linearSignal (D : M3) (beta : V3) : V3 := (-2 : ℝ) • D.mulVec beta
def exactEstimate (D : M3) (h : V3) : V3 := (-(1 / 2 : ℝ)) • (D⁻¹).mulVec h
def truncEstimate (D : M3) (hH : H D ≠ 0) (h : V3) : V3 :=
  fromCol (CAS03C03.betaTrunc D hH (toCol h))
def linearDefect (D : M3) (_hH : H D ≠ 0) (beta : V3) : V3 :=
  (1 / (H D)^2) • ((sigma D * sigma D).mulVec beta)
def truncGain (D : M3) (_hH : H D ≠ 0) : ℝ :=
  (1 + opNorm (sigma D) / |H D|) / (2 * |H D|)

private theorem fromCol_toCol (v : V3) : fromCol (toCol v) = v := rfl

private theorem toCol_mulVec (D : M3) (v : V3) :
    toCol (D.mulVec v) = D * toCol v := by
  ext i j
  fin_cases j
  simp [toCol, Matrix.mulVec, Matrix.mul_apply, dotProduct]

private theorem fromCol_mul (D : M3) (v : CAS03C03.V) :
    fromCol (D * v) = D.mulVec (fromCol v) := by
  ext i
  simp [fromCol, Matrix.mulVec, Matrix.mul_apply, dotProduct]

private theorem fromCol_smul (a : ℝ) (v : CAS03C03.V) :
    fromCol (a • v) = a • fromCol v := rfl

private theorem fromCol_sub (v w : CAS03C03.V) :
    fromCol (v - w) = fromCol v - fromCol w := rfl

private theorem toCol_smul (a : ℝ) (v : V3) :
    toCol (a • v) = a • toCol v := rfl

private theorem toCol_linearSignal (D : M3) (beta : V3) :
    toCol (linearSignal D beta) = CAS03C03.h1 D (toCol beta) := by
  dsimp only [linearSignal, CAS03C03.h1]
  rw [toCol_smul, toCol_mulVec]

private theorem fromCol_betaTrunc (D : M3) (hH : H D ≠ 0) (h : V3) :
    truncEstimate D hH h =
      (-(1 / (2 * H D)) : ℝ) •
        (1 - (1 / H D) • sigma D).mulVec h := by
  dsimp only [truncEstimate, CAS03C03.betaTrunc]
  rw [fromCol_smul, fromCol_mul, fromCol_toCol]

private theorem dipole_eq_linear_add (D : M3) (beta : V3) :
    dipoleMap D beta = linearSignal D beta + remainder D beta := by
  ext i
  simp [linearSignal, remainder]

theorem exact_inverse_linear (D : M3) (beta : V3) (hdet : D.det ≠ 0) :
    beta = exactEstimate D (linearSignal D beta) := by
  have h := CAS03C03.exact_inverse D (toCol beta) hdet
  rw [← toCol_linearSignal] at h
  have hf := congrArg fromCol h
  simpa only [fromCol_toCol, fromCol_smul, fromCol_mul,
    exactEstimate] using hf

theorem exact_inverse_nonlinear_defect (D : M3) (beta : V3) (hdet : D.det ≠ 0) :
    beta - exactEstimate D (dipoleMap D beta) =
      (1 / 2 : ℝ) • (D⁻¹).mulVec (remainder D beta) := by
  rw [dipole_eq_linear_add]
  have hl := exact_inverse_linear D beta hdet
  rw [show exactEstimate D (linearSignal D beta + remainder D beta) =
      exactEstimate D (linearSignal D beta) +
        exactEstimate D (remainder D beta) by
          simp [exactEstimate, Matrix.mulVec_add, smul_add]]
  rw [← hl]
  ext i
  simp only [Pi.sub_apply, Pi.add_apply, Pi.smul_apply, smul_eq_mul,
    exactEstimate]
  ring

theorem exact_inverse_error_le_remainder (D : M3) (beta : V3) (hdet : D.det ≠ 0) :
    eNorm (beta - exactEstimate D (dipoleMap D beta)) ≤
      (opNorm (D⁻¹) / 2) * eNorm (remainder D beta) := by
  rw [exact_inverse_nonlinear_defect D beta hdet, eNorm_smul]
  have h := eNorm_mulVec_le (D⁻¹) (remainder D beta)
  have hn : |(1 / 2 : ℝ)| = 1 / 2 := by norm_num
  rw [hn]
  calc
    (1 / 2 : ℝ) * eNorm ((D⁻¹).mulVec (remainder D beta)) ≤
      (1 / 2) * (opNorm (D⁻¹) * eNorm (remainder D beta)) := by gcongr
    _ = _ := by ring

theorem exact_inverse_error_pointwise (D : M3) (hD : ∀ i j, D i j = D j i)
    (hdet : D.det ≠ 0) (beta : V3) (hbeta : q beta < 1) :
    eNorm (beta - exactEstimate D (dipoleMap D beta)) ≤
      (opNorm (D⁻¹) * opNorm D / (1 - q beta)) * eNorm beta ^ 3 := by
  have ho : 0 ≤ opNorm (D⁻¹) := norm_nonneg _
  calc
    _ ≤ (opNorm (D⁻¹) / 2) * eNorm (remainder D beta) :=
      exact_inverse_error_le_remainder D beta hdet
    _ ≤ (opNorm (D⁻¹) / 2) *
        ((2 * opNorm D / (1 - q beta)) * eNorm beta ^ 3) := by
          exact mul_le_mul_of_nonneg_left
            (remainder_norm_le_pointwise D hD beta hbeta)
            (by positivity)
    _ = _ := by ring

theorem exact_inverse_error_ball (D : M3) (hD : ∀ i j, D i j = D j i)
    (hdet : D.det ≠ 0) (beta : V3) (r : ℝ) (hr0 : 0 ≤ r) (hr1 : r < 1)
    (hbeta : eNorm beta ≤ r) :
    eNorm (beta - exactEstimate D (dipoleMap D beta)) ≤
      (opNorm (D⁻¹) * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 3 ∧
    eNorm (beta - exactEstimate D (dipoleMap D beta)) ≤
      (r * opNorm (D⁻¹) * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 := by
  have ho : 0 ≤ opNorm (D⁻¹) := norm_nonneg _
  constructor
  · calc
      _ ≤ (opNorm (D⁻¹) / 2) * eNorm (remainder D beta) :=
        exact_inverse_error_le_remainder D beta hdet
      _ ≤ (opNorm (D⁻¹) / 2) *
          ((2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 3) := by
            exact mul_le_mul_of_nonneg_left
              (remainder_norm_le_cubic_ball D hD beta r hr0 hr1 hbeta)
              (by positivity)
      _ = _ := by ring
  · calc
      _ ≤ (opNorm (D⁻¹) / 2) * eNorm (remainder D beta) :=
        exact_inverse_error_le_remainder D beta hdet
      _ ≤ (opNorm (D⁻¹) / 2) *
          ((2 * r * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2) := by
            exact mul_le_mul_of_nonneg_left
              (remainder_norm_le_quadratic_ball D hD beta r hr0 hr1 hbeta)
              (by positivity)
      _ = _ := by ring

theorem trunc_linear_defect (D : M3) (beta : V3) (hH : H D ≠ 0) :
    beta - truncEstimate D hH (linearSignal D beta) = linearDefect D hH beta := by
  have h := CAS03C03.trunc_defect D (toCol beta) hH
  rw [← toCol_linearSignal] at h
  have hf := congrArg fromCol h
  simpa only [fromCol_toCol, fromCol_smul, fromCol_mul,
    fromCol_sub, truncEstimate, linearDefect] using hf

theorem trunc_nonlinear_defect (D : M3) (beta : V3) (hH : H D ≠ 0) :
    beta - truncEstimate D hH (dipoleMap D beta) =
      linearDefect D hH beta +
        (1 / (2 * H D)) •
          (1 - (1 / H D) • sigma D).mulVec (remainder D beta) := by
  rw [dipole_eq_linear_add]
  rw [show truncEstimate D hH (linearSignal D beta + remainder D beta) =
      truncEstimate D hH (linearSignal D beta) +
        truncEstimate D hH (remainder D beta) by
          simp [fromCol_betaTrunc, Matrix.mulVec_add, smul_add]]
  rw [← trunc_linear_defect D beta hH]
  rw [fromCol_betaTrunc D hH (linearSignal D beta),
    fromCol_betaTrunc D hH (remainder D beta)]
  ext i
  simp only [Pi.sub_apply, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  ring

private theorem eNorm_operator_product_le (A B : M3) (v : V3) :
    eNorm ((A * B).mulVec v) ≤ opNorm A * opNorm B * eNorm v := by
  rw [← Matrix.mulVec_mulVec]
  calc
    _ ≤ opNorm A * eNorm (B.mulVec v) := eNorm_mulVec_le A (B.mulVec v)
    _ ≤ opNorm A * (opNorm B * eNorm v) := by
      exact mul_le_mul_of_nonneg_left (eNorm_mulVec_le B v) (norm_nonneg _)
    _ = _ := by ring

private theorem eNorm_operator_difference_le (D : M3) (hH : H D ≠ 0)
    (v : V3) :
    eNorm ((1 - (1 / H D) • sigma D).mulVec v) ≤
      (1 + opNorm (sigma D) / |H D|) * eNorm v := by
  have habs : |(1 / H D : ℝ)| = 1 / |H D| := by
    rw [abs_div, abs_one]
  have htri := eNorm_add_le v ((-(1 / H D)) • (sigma D).mulVec v)
  have hm := eNorm_mulVec_le (sigma D) v
  have heq : (1 - (1 / H D) • sigma D).mulVec v =
      v + (-(1 / H D)) • (sigma D).mulVec v := by
    rw [Matrix.sub_mulVec, Matrix.one_mulVec, Matrix.smul_mulVec]
    simp only [neg_smul, sub_eq_add_neg]
  rw [heq]
  calc
    _ ≤ eNorm v + eNorm ((-(1 / H D)) • (sigma D).mulVec v) := htri
    _ = eNorm v + (1 / |H D|) * eNorm ((sigma D).mulVec v) := by
      rw [eNorm_smul, abs_neg, habs]
    _ ≤ eNorm v + (1 / |H D|) * (opNorm (sigma D) * eNorm v) := by
      gcongr
    _ = _ := by ring

private theorem linearDefect_norm_le (D : M3) (hH : H D ≠ 0)
    (beta : V3) :
    eNorm (linearDefect D hH beta) ≤
      (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta := by
  have hh2 : 0 ≤ (H D)^2 := sq_nonneg _
  rw [linearDefect, eNorm_smul]
  have habs : |(1 / (H D)^2 : ℝ)| = 1 / (H D)^2 := by
    rw [abs_of_nonneg (by positivity)]
  rw [habs]
  calc
    (1 / (H D)^2) * eNorm ((sigma D * sigma D).mulVec beta) ≤
      (1 / (H D)^2) *
        (opNorm (sigma D) * opNorm (sigma D) * eNorm beta) := by
          gcongr
          exact eNorm_operator_product_le _ _ _
    _ = _ := by ring

theorem trunc_nonlinear_residual_le_remainder (D : M3) (beta : V3)
    (hH : H D ≠ 0) :
    eNorm ((beta - truncEstimate D hH (dipoleMap D beta)) -
      linearDefect D hH beta) ≤
      truncGain D hH * eNorm (remainder D beta) := by
  rw [trunc_nonlinear_defect D beta hH]
  simp only [add_sub_cancel_left, eNorm_smul]
  have hne : |H D| ≠ 0 := abs_ne_zero.mpr hH
  have habs : |(1 / (2 * H D) : ℝ)| = 1 / (2 * |H D|) := by
    rw [abs_div, abs_one, abs_mul, abs_of_pos (by norm_num : (0:ℝ)<2)]
  rw [habs]
  calc
    (1 / (2 * |H D|)) *
        eNorm ((1 - (1 / H D) • sigma D).mulVec (remainder D beta)) ≤
      (1 / (2 * |H D|)) *
        ((1 + opNorm (sigma D) / |H D|) * eNorm (remainder D beta)) := by
          gcongr
          exact eNorm_operator_difference_le D hH _
    _ = truncGain D hH * eNorm (remainder D beta) := by
      simp only [truncGain]
      ring

theorem trunc_error_ball (D : M3) (hD : ∀ i j, D i j = D j i)
    (hH : H D ≠ 0) (beta : V3) (r : ℝ) (hr0 : 0 ≤ r)
    (hr1 : r < 1) (hbeta : eNorm beta ≤ r) :
    eNorm (beta - truncEstimate D hH (dipoleMap D beta)) ≤
      (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta +
        truncGain D hH * (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 3 ∧
    eNorm (beta - truncEstimate D hH (dipoleMap D beta)) ≤
      (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta +
        truncGain D hH * (2 * r * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 := by
  have hgain : 0 ≤ truncGain D hH := by
    unfold truncGain
    have hp : 0 < |H D| := abs_pos.mpr hH
    have ho : 0 ≤ opNorm (sigma D) := norm_nonneg _
    positivity
  have hbase : eNorm (beta - truncEstimate D hH (dipoleMap D beta)) ≤
      (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta +
        truncGain D hH * eNorm (remainder D beta) := by
    have ht := eNorm_add_le (linearDefect D hH beta)
      ((beta - truncEstimate D hH (dipoleMap D beta)) - linearDefect D hH beta)
    have heq : linearDefect D hH beta +
        ((beta - truncEstimate D hH (dipoleMap D beta)) -
          linearDefect D hH beta) =
        beta - truncEstimate D hH (dipoleMap D beta) := by abel
    rw [heq] at ht
    exact le_trans ht (add_le_add (linearDefect_norm_le D hH beta)
      (trunc_nonlinear_residual_le_remainder D beta hH))
  constructor
  · calc
      _ ≤ (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta +
          truncGain D hH * eNorm (remainder D beta) := hbase
      _ ≤ (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta +
          truncGain D hH *
            ((2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 3) := by
              gcongr
              exact remainder_norm_le_cubic_ball D hD beta r hr0 hr1 hbeta
      _ = _ := by ring
  · calc
      _ ≤ (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta +
          truncGain D hH * eNorm (remainder D beta) := hbase
      _ ≤ (opNorm (sigma D) ^ 2 / (H D)^2) * eNorm beta +
          truncGain D hH *
            ((2 * r * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2) := by
              gcongr
              exact remainder_norm_le_quadratic_ball D hD beta r hr0 hr1 hbeta
      _ = _ := by ring

theorem zeroH_exact_only_control :
    H CAS03C03.zeroHD = 0 ∧ CAS03C03.zeroHD.det = -2 ∧
      ¬ (H CAS03C03.zeroHD ≠ 0) := by
  rcases CAS03C03.zeroH_control with ⟨hH, hd⟩
  exact ⟨hH, hd, by simpa [hH]⟩

theorem zeroH_exact_error_ball (beta : V3) (r : ℝ)
    (hr0 : 0 ≤ r) (hr1 : r < 1) (hbeta : eNorm beta ≤ r) :
    eNorm (beta - exactEstimate CAS03C03.zeroHD
      (dipoleMap CAS03C03.zeroHD beta)) ≤
      (opNorm (CAS03C03.zeroHD⁻¹) * opNorm CAS03C03.zeroHD /
        (1 - r ^ 2)) * eNorm beta ^ 3 := by
  exact (exact_inverse_error_ball CAS03C03.zeroHD
    (by intro i j; fin_cases i <;> fin_cases j <;> norm_num [CAS03C03.zeroHD])
    (by rw [CAS03C03.zeroH_control.2]; norm_num)
    beta r hr0 hr1 hbeta).1

#check exact_inverse_linear
#print axioms exact_inverse_linear
#check exact_inverse_nonlinear_defect
#print axioms exact_inverse_nonlinear_defect
#check exact_inverse_error_le_remainder
#print axioms exact_inverse_error_le_remainder
#check exact_inverse_error_pointwise
#print axioms exact_inverse_error_pointwise
#check exact_inverse_error_ball
#print axioms exact_inverse_error_ball
#check trunc_linear_defect
#print axioms trunc_linear_defect
#check trunc_nonlinear_defect
#print axioms trunc_nonlinear_defect
#check trunc_nonlinear_residual_le_remainder
#print axioms trunc_nonlinear_residual_le_remainder
#check trunc_error_ball
#print axioms trunc_error_ball
#check zeroH_exact_only_control
#print axioms zeroH_exact_only_control
#check zeroH_exact_error_ball
#print axioms zeroH_exact_error_ball

end
end InverseTruncationSynthesis
