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
    _ = _ := by ring

private theorem opNorm_sub_le (A B : M3) :
    opNorm (A - B) ≤ opNorm A + opNorm B := by
  have hm : matrixOp (A - B) = matrixOp A - matrixOp B := by
    simp [matrixOp, map_sub]
  simpa [opNorm, hm] using norm_sub_le (matrixOp A) (matrixOp B)

private theorem eNorm_eq_zero_iff (v : V3) : eNorm v = 0 ↔ v = 0 := by
  simp [eNorm, toE]

private theorem isUnit_det (D : M3) (hdet : D.det ≠ 0) : IsUnit D.det :=
  isUnit_iff_ne_zero.mpr hdet

end CoefficientInverseStability
