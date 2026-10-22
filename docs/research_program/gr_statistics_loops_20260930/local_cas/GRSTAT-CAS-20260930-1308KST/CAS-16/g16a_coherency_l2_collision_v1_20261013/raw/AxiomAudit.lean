import G16ACoherency

noncomputable section
open MeasureTheory Metric G16ACoherency
open scoped ENNReal

attribute [local instance] Matrix.frobeniusNormedAddCommGroup Matrix.frobeniusNormedSpace
  Matrix.frobeniusNormSMulClass Matrix.frobeniusIsBoundedSMul
-- default-topology bindings: elaborated BEFORE frobTop is made a local instance
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

attribute [local instance high] G16ACoherency.frobTop

-- frozen-signature bindings

example : ∀ (v : CAS16Projector.Vec) (hv : ∑ i, v i * v i = 1) (A : CMat),
    ‖Pc v * A * Pc v‖ ≤ ‖A‖ := pointwise_complex_contraction
example : dΩ Set.univ = ENNReal.ofReal (4 * Real.pi) := sphere_mass
example : IsFiniteMeasure dΩ := inferInstance
example : ∀ (J : S2 → CMat) (hJ : MemLp J 2 dΩ),
    ‖∫ e, J e ∂dΩ‖ ≤ Real.sqrt (4 * Real.pi) * (eLpNorm J 2 dΩ).toReal := integral_cauchy
example : ∀ (J : S2 → CMat) (hJ : MemLp J 2 dΩ),
    MemLp (thomsonGain J) 2 dΩ ∧
      eLpNorm (thomsonGain J) 2 dΩ ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩ := gain_L2_bound
example : ∀ (Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ),
    MemLp (thomsonCollision Γ J) 2 dΩ ∧
      eLpNorm (thomsonCollision Γ J) 2 dΩ ≤ ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩ :=
  collision_L2_bound
example : ∀ (J : Lp CMat 2 dΩ), (gainCLM J : S2 → CMat) =ᵐ[dΩ] thomsonGain (J : S2 → CMat) :=
  gainCLM_ae
example : ‖gainCLM‖ ≤ 3 / 2 := gainCLM_opNorm
example : ∀ (Γ : ℝ) (J : Lp CMat 2 dΩ),
    (collisionCLM Γ J : S2 → CMat) =ᵐ[dΩ] thomsonCollision Γ (J : S2 → CMat) := collisionCLM_ae
example : ∀ (Γ : ℝ) (hΓ : 0 ≤ Γ), ‖collisionCLM Γ‖ ≤ 5 / 2 * Γ := collisionCLM_opNorm
example : ∀ Γ : ℝ, collisionCLM Γ = Γ • (gainCLM - ContinuousLinearMap.id ℝ _) := fun _ => rfl
example : dΩnorm = (ENNReal.ofReal (4 * Real.pi))⁻¹ • dΩ := rfl
example : dΩnorm Set.univ = 1 := normalized_mass
example : ∀ (Γ : ℝ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ),
    collisionField dΩnorm Γ (3 / 2) thomsonP J = thomsonCollision Γ J := normalized_operator_eq
example : ∀ (Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩnorm),
    eLpNorm (gainField dΩnorm (3 / 2) thomsonP J) 2 dΩnorm ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩnorm ∧
    eLpNorm (collisionField dΩnorm Γ (3 / 2) thomsonP J) 2 dΩnorm ≤
      ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩnorm := normalized_bounds
example : ∀ (f : S2 → CMat),
    eLpNorm f 2 dΩnorm = (ENNReal.ofReal (4 * Real.pi))⁻¹ ^ (1 / 2 : ℝ) * eLpNorm f 2 dΩ :=
  normalized_norm_scaling
example : ¬ (‖Pc ![2, 0, 0] * Matrix.single 0 0 1 * Pc ![2, 0, 0]‖ ≤ ‖(Matrix.single 0 0 1 : CMat)‖) :=
  neg_control_nonunit
example : ∀ (e : S2), thomsonGain (fun _ => (1 : CMat)) e = ((3 / 2 : ℝ) : ℂ) • thomsonP e :=
  isotropic_gain_witness
-- definitional bindings to the frozen definitions
example : dΩ = (volume : Measure E3).toSphere := rfl
example : ∀ e : S2, thomsonP e = Pc (vecOf e) := fun _ => rfl
example : ∀ v, Pc v = (CAS16Projector.projector v).map (fun r : ℝ => (r : ℂ)) := fun _ => rfl
example : ∀ J, thomsonGain J = gainField dΩ (3 / (8 * Real.pi)) thomsonP J := fun _ => rfl
example : ∀ Γ J, thomsonCollision Γ J = collisionField dΩ Γ (3 / (8 * Real.pi)) thomsonP J :=
  fun _ _ => rfl
example : ∀ Γ J e, thomsonCollision Γ J e =
    Γ • (-(J e) + (3 / (8 * Real.pi)) • (thomsonP e * (∫ y, J y ∂dΩ) * thomsonP e)) :=
  fun _ _ _ => rfl


#check @G16ACoherency.frob_sq
#check @G16ACoherency.decomp
#check @G16ACoherency.frob_sq_split
#check @G16ACoherency.sandwich_re
#check @G16ACoherency.pointwise_complex_contraction
#check @G16ACoherency.sphere_mass
#check @G16ACoherency.vecOf_unit
#check @G16ACoherency.enorm_integral_le_sqrt_mass
#check @G16ACoherency.gain_abstract
#check @G16ACoherency.collision_abstract
#check @G16ACoherency.thomsonP_contract
#check @G16ACoherency.thomsonP_apply
#check @G16ACoherency.continuous_thomsonP
#check @G16ACoherency.thomsonP_meas
#check @G16ACoherency.integral_cauchy
#check @G16ACoherency.gain_coeff
#check @G16ACoherency.gain_L2_bound
#check @G16ACoherency.five_halves
#check @G16ACoherency.collision_L2_bound
#check @G16ACoherency.integral_add_Lp
#check @G16ACoherency.integral_smul_Lp
#check @G16ACoherency.gainLin_bound
#check @G16ACoherency.gainCLM_ae
#check @G16ACoherency.gainCLM_opNorm
#check @G16ACoherency.collisionCLM_ae
#check @G16ACoherency.collisionCLM_opNorm
#check @G16ACoherency.normalized_mass
#check @G16ACoherency.normalized_operator_eq
#check @G16ACoherency.normalized_bounds
#check @G16ACoherency.normalized_norm_scaling
#check @G16ACoherency.neg_control_nonunit
#check @G16ACoherency.thomsonP_idem
#check @G16ACoherency.isotropic_gain_witness
#print axioms G16ACoherency.frob_sq
#print axioms G16ACoherency.decomp
#print axioms G16ACoherency.frob_sq_split
#print axioms G16ACoherency.sandwich_re
#print axioms G16ACoherency.pointwise_complex_contraction
#print axioms G16ACoherency.sphere_mass
#print axioms G16ACoherency.vecOf_unit
#print axioms G16ACoherency.enorm_integral_le_sqrt_mass
#print axioms G16ACoherency.gain_abstract
#print axioms G16ACoherency.collision_abstract
#print axioms G16ACoherency.thomsonP_contract
#print axioms G16ACoherency.thomsonP_apply
#print axioms G16ACoherency.continuous_thomsonP
#print axioms G16ACoherency.thomsonP_meas
#print axioms G16ACoherency.integral_cauchy
#print axioms G16ACoherency.gain_coeff
#print axioms G16ACoherency.gain_L2_bound
#print axioms G16ACoherency.five_halves
#print axioms G16ACoherency.collision_L2_bound
#print axioms G16ACoherency.integral_add_Lp
#print axioms G16ACoherency.integral_smul_Lp
#print axioms G16ACoherency.gainLin_bound
#print axioms G16ACoherency.gainCLM_ae
#print axioms G16ACoherency.gainCLM_opNorm
#print axioms G16ACoherency.collisionCLM_ae
#print axioms G16ACoherency.collisionCLM_opNorm
#print axioms G16ACoherency.normalized_mass
#print axioms G16ACoherency.normalized_operator_eq
#print axioms G16ACoherency.normalized_bounds
#print axioms G16ACoherency.normalized_norm_scaling
#print axioms G16ACoherency.neg_control_nonunit
#print axioms G16ACoherency.thomsonP_idem
#print axioms G16ACoherency.isotropic_gain_witness
#print axioms G16ACoherency.gainLin
#print axioms G16ACoherency.gainCLM
#print axioms G16ACoherency.collisionCLM
#print axioms G16ACoherency.dΩnorm
#print axioms G16ACoherency.thomsonGain
#print axioms G16ACoherency.thomsonCollision
