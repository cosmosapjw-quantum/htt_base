import Mathlib
open MeasureTheory Metric
abbrev E3 := EuclideanSpace ℝ (Fin 3)
#check (fun (x : E3) => x 0)
#check @PiLp.single_apply
#check @EuclideanSpace.inner_single_left
#check @PiLp.inner_apply
#check @NormedSpace.exp
#check @exp_mem_unitary_of_mem_skewAdjoint
#check @NormedSpace.exp_mem_unitary_of_mem_skewAdjoint
#check @Unitary.linearIsometryEquiv
#check @hasDerivAt_exp_smul_const
#check @ContinuousLinearMap.eq_adjoint_iff
#check @skewAdjoint.mem_iff
#check @MeasurePreserving.measure_preimage_emb
#check @MeasurePreserving.integral_comp
#check @HasCompactSupport.of_compactSpace
#check @Continuous.integrable_of_hasCompactSupport
#check @IsCompact.exists_bound_of_continuousOn
#check @ContDiff.continuous_fderiv
#check @Measure.toSphere_apply'
#check @Measure.toSphere_ne_zero
#check @MvPolynomial.totalDegree_mul
#check @MvPolynomial.eval_eq
#check (volume : Measure E3).toSphere
example : ∀ x : E3, ‖x‖^2 = ∑ i, x i ^ 2 := by intro x; simp [EuclideanSpace.norm_sq_eq]
