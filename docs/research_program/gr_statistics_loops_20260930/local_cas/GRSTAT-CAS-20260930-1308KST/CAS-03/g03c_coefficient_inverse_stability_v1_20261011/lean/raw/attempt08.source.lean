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
    have ho : 0 ≤ opNorm D := norm_nonneg _
    positivity
  have hpert : opNorm (coefficientMatrix D beta - D) ≤ perturbationSize D r := by
    calc
      opNorm (coefficientMatrix D beta - D) ≤
          (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 :=
        coefficientMatrix_perturbation_norm_ball D hD beta r hr0 hr1 hbeta
      _ ≤ (2 * opNorm D / (1 - r ^ 2)) * r ^ 2 := by
        have ho : 0 ≤ opNorm D := norm_nonneg _
        have hb0 : 0 ≤ eNorm beta := norm_nonneg _
        gcongr
      _ = perturbationSize D r := rfl
  exact matrix_inverse_perturbation D (coefficientMatrix D beta) hdet
    (perturbationSize D r) heps hpert hsmall

private theorem inverse_difference_identity (A D : M3)
    (hA : A.det ≠ 0) (hD : D.det ≠ 0) :
    A⁻¹ - D⁻¹ = A⁻¹ * (D-A) * D⁻¹ := by
  have ha := Matrix.nonsing_inv_mul A (isUnit_det A hA)
  have hd := Matrix.mul_nonsing_inv D (isUnit_det D hD)
  calc
    A⁻¹ - D⁻¹ = A⁻¹ * (D * D⁻¹) - (A⁻¹ * A) * D⁻¹ := by
      rw [hd, ha, mul_one, one_mul]
    _ = A⁻¹ * (D-A) * D⁻¹ := by noncomm_ring

theorem coefficientMatrix_inverse_difference_ball (D : M3)
    (hD : ∀ i j, D i j = D j i) (hdet : Matrix.det D ≠ 0)
    (beta : V3) (r : ℝ) (hr0 : 0 ≤ r) (hr1 : r < 1)
    (hbeta : eNorm beta ≤ r) (hsmall : perturbationRatio D r < 1) :
    opNorm ((coefficientMatrix D beta)⁻¹ - D⁻¹) ≤
      (2*opNorm (D⁻¹)^2*opNorm D /
        ((1-perturbationRatio D r)*(1-r^2))) * eNorm beta^2 := by
  let A := coefficientMatrix D beta
  have hb := coefficientMatrix_inverse_ball D hD hdet beta r hr0 hr1 hbeta hsmall
  have hδ : opNorm (D-A) ≤
      (2 * opNorm D / (1-r^2)) * eNorm beta^2 := by
    rw [opNorm_sub_comm]
    exact coefficientMatrix_perturbation_norm_ball D hD beta r hr0 hr1 hbeta
  have hp : 0 ≤ opNorm (A⁻¹) := norm_nonneg _
  have hdi : 0 ≤ opNorm (D⁻¹) := norm_nonneg _
  have hc : 0 ≤ 2 * opNorm D / (1-r^2) := by
    have hn : 0 ≤ opNorm D := norm_nonneg _
    have hr : 0 < 1-r^2 := by nlinarith
    positivity
  have hg : 0 ≤ inverseGain D r :=
    (norm_nonneg _).trans hb.2
  calc
    opNorm (A⁻¹-D⁻¹) = opNorm (A⁻¹ * (D-A) * D⁻¹) := by
      rw [inverse_difference_identity A D hb.1 hdet]
    _ ≤ opNorm (A⁻¹ * (D-A)) * opNorm (D⁻¹) := opNorm_mul_le _ _
    _ ≤ (opNorm (A⁻¹) * opNorm (D-A)) * opNorm (D⁻¹) :=
      mul_le_mul_of_nonneg_right (opNorm_mul_le _ _) hdi
    _ ≤ (inverseGain D r * ((2 * opNorm D / (1-r^2)) * eNorm beta^2)) *
          opNorm (D⁻¹) := by
      gcongr <;> first | exact norm_nonneg _ | exact hb.2 | exact hδ
    _ = (2*opNorm (D⁻¹)^2*opNorm D /
        ((1-perturbationRatio D r)*(1-r^2))) * eNorm beta^2 := by
      have h1 : 1 - perturbationRatio D r ≠ 0 := ne_of_gt (sub_pos.mpr hsmall)
      have h2 : 1 - r^2 ≠ 0 := by nlinarith
      unfold inverseGain
      field_simp <;> ring

private theorem coefficientMatrix_mulVec_beta (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3) (hbeta : q beta < 1) :
    (coefficientMatrix D beta).mulVec beta =
      (-(1/2 : ℝ)) • dipoleMap D beta +
        timeCoefficient D beta • beta := by
  have ha := boostA_mul_q beta hbeta
  have hm := congrArg (fun M : M3 => M.mulVec beta)
    (coefficientMatrix_perturbation_exact D hD beta)
  rw [dipoleMap_exact D hD beta, timeCoefficient_exact]
  ext i
  have hi := congrFun hm i
  simp only [Matrix.sub_mulVec, Matrix.add_mulVec, Matrix.smul_mulVec,
    outer_mulVec, Matrix.one_mulVec, Pi.sub_apply, Pi.add_apply,
    Pi.smul_apply, smul_eq_mul] at hi ⊢
  simp only [outer_mulVec, Matrix.add_mulVec, Matrix.smul_mulVec,
    Matrix.one_mulVec, Pi.add_apply, Pi.smul_apply, smul_eq_mul] at hi
  simp only [sourceQuadratic, dot3] at hi
  simp only [q, dot3] at ha
  nlinarith [hi]

theorem coefficient_inverse_defect (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3)
    (hbeta : q beta < 1)
    (hA : Matrix.det (coefficientMatrix D beta) ≠ 0) :
    beta - coefficientEstimate D beta =
      timeCoefficient D beta • ((coefficientMatrix D beta)⁻¹).mulVec beta := by
  let A := coefficientMatrix D beta
  have hrel := coefficientMatrix_mulVec_beta D hD beta hbeta
  have hAinv := inv_mulVec_self A hA beta
  have hstep := congrArg (fun v : V3 => (A⁻¹).mulVec v) hrel
  ext i
  have hi := congrFun hstep i
  simp only [Matrix.mulVec_add, Matrix.mulVec_smul, Pi.add_apply,
    Pi.smul_apply, smul_eq_mul] at hi
  simp only [coefficientEstimate, exactEstimate, Pi.sub_apply,
    Pi.smul_apply, smul_eq_mul]
  simp only [hAinv] at hi
  linarith

end CoefficientInverseStability
