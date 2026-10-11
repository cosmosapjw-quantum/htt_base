import CoefficientMatrixBridge
import InverseTruncationSynthesis

set_option maxHeartbeats 2000000

open ExactBoostMap NonlinearRemainder CoefficientMatrixBridge InverseTruncationSynthesis

namespace CoefficientInverseStability

abbrev V3 := ExactBoostMap.V3
abbrev M3 := ExactBoostMap.M3

noncomputable def perturbationSize (D : M3) (r : ℝ) : ℝ :=
  (2 * opNorm D / (1 - r ^ 2)) * r ^ 2
noncomputable def perturbationRatio (D : M3) (r : ℝ) : ℝ :=
  opNorm (D⁻¹) * perturbationSize D r
noncomputable def inverseGain (D : M3) (r : ℝ) : ℝ :=
  opNorm (D⁻¹) / (1 - perturbationRatio D r)
noncomputable def inverseErrorConstant (D : M3) (r : ℝ) : ℝ :=
  opNorm (D⁻¹) * opNorm D / ((1 - perturbationRatio D r) * (1 - r ^ 2))
noncomputable def coefficientEstimate (D : M3) (beta : V3) : V3 :=
  exactEstimate (coefficientMatrix D beta) (dipoleMap D beta)
noncomputable def admissibleRadius (D : M3) : ℝ :=
  1 / (2 * Real.sqrt (1 + 2 * opNorm (D⁻¹) * opNorm D))

private theorem opNorm_mul_le (A B : M3) :
    opNorm (A * B) ≤ opNorm A * opNorm B := by
  apply opNorm_le_of_mulVec_bound _ _ (mul_nonneg (norm_nonneg _) (norm_nonneg _))
  intro v
  calc
    eNorm ((A * B).mulVec v) = eNorm (A.mulVec (B.mulVec v)) := by rw [Matrix.mulVec_mulVec]
    _ ≤ opNorm A * eNorm (B.mulVec v) := eNorm_mulVec_le _ _
    _ ≤ opNorm A * (opNorm B * eNorm v) :=
      mul_le_mul_of_nonneg_left (eNorm_mulVec_le _ _) (norm_nonneg _)
    _ = _ := by simp only [opNorm]; ring

private theorem opNorm_sub_le (A B : M3) :
    opNorm (A - B) ≤ opNorm A + opNorm B := by
  have hm : matrixOp (A - B) = matrixOp A - matrixOp B := by
    simp [matrixOp, map_sub]
  simpa [opNorm, hm] using norm_sub_le (matrixOp A) (matrixOp B)

private theorem eNorm_eq_zero_iff (v : V3) : eNorm v = 0 ↔ v = 0 := by
  simp [eNorm, toE]

private theorem isUnit_det (D : M3) (hdet : D.det ≠ 0) : IsUnit D.det :=
  isUnit_iff_ne_zero.mpr hdet

private theorem opNorm_sub_comm (A B : M3) : opNorm (A - B) = opNorm (B - A) := by
  have hm (X Y : M3) : matrixOp (X - Y) = matrixOp X - matrixOp Y := by
    simp [matrixOp, map_sub]
  simp only [opNorm, hm, norm_sub_rev]

private theorem opNorm_add_le (A B : M3) :
    opNorm (A + B) ≤ opNorm A + opNorm B := by
  have hm : matrixOp (A + B) = matrixOp A + matrixOp B := by
    simp [matrixOp, map_add]
  simpa [opNorm, hm] using norm_add_le (matrixOp A) (matrixOp B)

private theorem inv_mulVec_self (D : M3) (hdet : D.det ≠ 0) (v : V3) :
    (D⁻¹).mulVec (D.mulVec v) = v := by
  rw [Matrix.mulVec_mulVec, Matrix.nonsing_inv_mul D (isUnit_det D hdet),
    Matrix.one_mulVec]

theorem matrix_inverse_perturbation (D A : M3) (hdet : Matrix.det D ≠ 0)
    (eps : ℝ) (heps : 0 ≤ eps) (hpert : opNorm (A-D) ≤ eps)
    (hsmall : opNorm (D⁻¹)*eps < 1) :
    Matrix.det A ≠ 0 ∧
      opNorm (A⁻¹) ≤ opNorm (D⁻¹)/(1-opNorm (D⁻¹)*eps) := by
  have hδ : opNorm (D - A) ≤ eps := by
    rw [opNorm_sub_comm]
    exact hpert
  have hgap : opNorm (D⁻¹) * opNorm (D-A) < 1 :=
    (mul_le_mul_of_nonneg_left hδ (norm_nonneg _)).trans_lt hsmall
  have hdetA : Matrix.det A ≠ 0 := by
    have hinj : Function.Injective A.mulVec := by
      intro v w hvw
      let z : V3 := v - w
      have hz : A.mulVec z = 0 := by
        simp [z, Matrix.mulVec_sub, hvw]
      have hDz : D.mulVec z = (D-A).mulVec z := by
        simp [Matrix.sub_mulVec, hz]
      have hznorm : eNorm z ≤
          opNorm (D⁻¹) * opNorm (D-A) * eNorm z := by
        calc
          eNorm z = eNorm ((D⁻¹).mulVec (D.mulVec z)) :=
            (congrArg eNorm (inv_mulVec_self D hdet z)).symm
          _ ≤ opNorm (D⁻¹) * eNorm (D.mulVec z) := eNorm_mulVec_le _ _
          _ ≤ opNorm (D⁻¹) * (opNorm (D-A) * eNorm z) := by
            rw [hDz]
            exact mul_le_mul_of_nonneg_left (eNorm_mulVec_le _ _) (norm_nonneg _)
          _ = _ := by ring
      have hz0 : eNorm z = 0 := by
        have hn : 0 ≤ eNorm z := norm_nonneg _
        nlinarith [mul_nonneg (sub_pos.mpr hgap).le hn]
      have : z = 0 := (eNorm_eq_zero_iff z).mp hz0
      exact sub_eq_zero.mp this
    have hu : IsUnit A := Matrix.mulVec_injective_iff_isUnit.mp hinj
    exact isUnit_iff_ne_zero.mp (A.isUnit_iff_isUnit_det.mp hu)
  refine ⟨hdetA, ?_⟩
  have hidentity : A⁻¹ = D⁻¹ + D⁻¹ * (D-A) * A⁻¹ := by
    have hDinv := Matrix.nonsing_inv_mul D (isUnit_det D hdet)
    have hAinv := Matrix.mul_nonsing_inv A (isUnit_det A hdetA)
    calc
      A⁻¹ = D⁻¹ * (D * A⁻¹) := by rw [← Matrix.mul_assoc, hDinv, one_mul]
      _ = D⁻¹ * ((A + (D-A)) * A⁻¹) := by congr 1; congr 1; abel
      _ = D⁻¹ + D⁻¹ * (D-A) * A⁻¹ := by
        rw [Matrix.add_mul, Matrix.mul_add, hAinv, mul_one, Matrix.mul_assoc]
  have hnorm : opNorm (A⁻¹) ≤ opNorm (D⁻¹) +
      opNorm (D⁻¹) * eps * opNorm (A⁻¹) := by
    calc
      opNorm (A⁻¹) = opNorm (D⁻¹ + D⁻¹ * (D-A) * A⁻¹) :=
        congrArg opNorm hidentity
      _ ≤ opNorm (D⁻¹) + opNorm (D⁻¹ * (D-A) * A⁻¹) := opNorm_add_le _ _
      _ ≤ opNorm (D⁻¹) + opNorm (D⁻¹ * (D-A)) * opNorm (A⁻¹) := by
        simpa only [add_comm, opNorm] using
          (add_le_add_right (opNorm_mul_le (D⁻¹ * (D-A)) (A⁻¹)) (opNorm (D⁻¹)))
      _ ≤ opNorm (D⁻¹) + (opNorm (D⁻¹) * opNorm (D-A)) * opNorm (A⁻¹) := by
        simpa only [add_comm, opNorm] using
          (add_le_add_right
            (mul_le_mul_of_nonneg_right (opNorm_mul_le (D⁻¹) (D-A))
              (norm_nonneg (matrixOp (A⁻¹)))) (opNorm (D⁻¹)))
      _ ≤ opNorm (D⁻¹) + opNorm (D⁻¹) * eps * opNorm (A⁻¹) := by
        simpa only [add_comm, opNorm] using
          (add_le_add_right
            (mul_le_mul_of_nonneg_right
              (mul_le_mul_of_nonneg_left hδ (norm_nonneg (matrixOp (D⁻¹))))
              (norm_nonneg (matrixOp (A⁻¹)))) (opNorm (D⁻¹)))
  have hden : 0 < 1 - opNorm (D⁻¹) * eps := sub_pos.mpr hsmall
  apply (le_div_iff₀ hden).2
  nlinarith

theorem coefficientMatrix_inverse_ball (D : M3)
    (hD : ∀ i j, D i j = D j i) (hdet : Matrix.det D ≠ 0)
    (beta : V3) (r : ℝ) (hr0 : 0 ≤ r) (hr1 : r < 1)
    (hbeta : eNorm beta ≤ r) (hsmall : perturbationRatio D r < 1) :
    Matrix.det (coefficientMatrix D beta) ≠ 0 ∧
      opNorm ((coefficientMatrix D beta)⁻¹) ≤ inverseGain D r := by
  have hden : 0 < 1 - r ^ 2 := by nlinarith
  have heps : 0 ≤ perturbationSize D r := by
    unfold perturbationSize
    positivity
  have hpert : opNorm (coefficientMatrix D beta - D) ≤ perturbationSize D r := by
    calc
      opNorm (coefficientMatrix D beta - D) ≤
          (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 :=
        coefficientMatrix_perturbation_norm_ball D hD beta r hr0 hr1 hbeta
      _ ≤ (2 * opNorm D / (1 - r ^ 2)) * r ^ 2 := by
        gcongr
      _ = perturbationSize D r := rfl
  exact matrix_inverse_perturbation D (coefficientMatrix D beta) hdet
    (perturbationSize D r) heps hpert hsmall

end CoefficientInverseStability
