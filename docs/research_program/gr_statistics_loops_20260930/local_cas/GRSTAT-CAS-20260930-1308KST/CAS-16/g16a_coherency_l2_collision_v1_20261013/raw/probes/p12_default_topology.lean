import G16ACoherency

noncomputable section
open MeasureTheory Metric G16ACoherency
open scoped ENNReal

attribute [local instance] Matrix.frobeniusNormedAddCommGroup Matrix.frobeniusNormedSpace
  Matrix.frobeniusNormSMulClass Matrix.frobeniusIsBoundedSMul

-- frobTop is the standard (product) topology on matrices
example : G16ACoherency.frobTop = (instTopologicalSpaceMatrix : TopologicalSpace CMat) := rfl
-- Frobenius-metric topology equals the default one (stated with inferInstance, no frobTop)
example : G16ACoherency.frobTop = (inferInstance : TopologicalSpace CMat) := rfl

-- frozen statements re-elaborated WITHOUT the frobTop local instance
example : ∀ (J : S2 → CMat) (hJ : MemLp J 2 dΩ),
    MemLp (thomsonGain J) 2 dΩ ∧
      eLpNorm (thomsonGain J) 2 dΩ ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩ := gain_L2_bound
example : ∀ (Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ),
    MemLp (thomsonCollision Γ J) 2 dΩ ∧
      eLpNorm (thomsonCollision Γ J) 2 dΩ ≤ ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩ :=
  collision_L2_bound
example : ∀ (J : S2 → CMat) (hJ : MemLp J 2 dΩ),
    ‖∫ e, J e ∂dΩ‖ ≤ Real.sqrt (4 * Real.pi) * (eLpNorm J 2 dΩ).toReal := integral_cauchy
example : ‖gainCLM‖ ≤ 3 / 2 := gainCLM_opNorm
example : ∀ (Γ : ℝ) (hΓ : 0 ≤ Γ), ‖collisionCLM Γ‖ ≤ 5 / 2 * Γ := collisionCLM_opNorm
example : ∀ (J : Lp CMat 2 dΩ), (gainCLM J : S2 → CMat) =ᵐ[dΩ] thomsonGain (J : S2 → CMat) :=
  gainCLM_ae
example : ∀ (Γ : ℝ) (J : Lp CMat 2 dΩ),
    (collisionCLM Γ J : S2 → CMat) =ᵐ[dΩ] thomsonCollision Γ (J : S2 → CMat) := collisionCLM_ae
example : ∀ (Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩnorm),
    eLpNorm (gainField dΩnorm (3 / 2) thomsonP J) 2 dΩnorm ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩnorm ∧
    eLpNorm (collisionField dΩnorm Γ (3 / 2) thomsonP J) 2 dΩnorm ≤
      ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩnorm := normalized_bounds
-- the norm used is the Frobenius norm
example (A : CMat) : ‖A‖ = (∑ i, ∑ j, ‖A i j‖ ^ (2 : ℝ)) ^ (1 / 2 : ℝ) := Matrix.frobenius_norm_def A
