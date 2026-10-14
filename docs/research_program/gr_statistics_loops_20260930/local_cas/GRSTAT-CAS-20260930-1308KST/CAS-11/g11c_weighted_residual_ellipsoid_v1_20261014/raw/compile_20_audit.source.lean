import G11CWeightedEllipsoid

/-! G11-C axiom audit: #check and #print axioms for every public theorem of `G11C`;
definitions/instances are #check-ed (instances also #print axioms). -/

#check @G11C.wmeas
#check @G11C.L2W
#check @G11C.zfun
#check @G11C.retainedSpan
#check @G11C.residuals
#check @G11C.gramR
#check @G11C.evec
#check @G11C.retainedSpan_finiteDimensional
#print axioms G11C.retainedSpan_finiteDimensional
#check @G11C.retainedSpan_completeSpace
#print axioms G11C.retainedSpan_completeSpace

#check @G11C.real_inner_apply
#print axioms G11C.real_inner_apply
#check @G11C.integral_wmeas
#print axioms G11C.integral_wmeas
#check @G11C.integrable_wmeas_iff
#print axioms G11C.integrable_wmeas_iff
#check @G11C.starProj_mem
#print axioms G11C.starProj_mem
#check @G11C.inner_toLp_eq_integral
#print axioms G11C.inner_toLp_eq_integral
#check @G11C.z_memLp
#print axioms G11C.z_memLp
#check @G11C.z_norm_sq
#print axioms G11C.z_norm_sq
#check @G11C.retainedSpan_isClosed
#print axioms G11C.retainedSpan_isClosed
#check @G11C.projection_spec
#print axioms G11C.projection_spec
#check @G11C.kernel_moment_integrable
#print axioms G11C.kernel_moment_integrable
#check @G11C.matching_iff_orthogonal
#print axioms G11C.matching_iff_orthogonal
#check @G11C.evec_eq_inner_residual
#print axioms G11C.evec_eq_inner_residual
#check @G11C.gramR_eq_integral
#print axioms G11C.gramR_eq_integral
#check @G11C.gramR_posSemidef
#print axioms G11C.gramR_posSemidef
#check @G11C.dot_evec_eq_inner
#print axioms G11C.dot_evec_eq_inner
#check @G11C.quad_eq_norm_sq
#print axioms G11C.quad_eq_norm_sq
#check @G11C.cauchy_all_a
#print axioms G11C.cauchy_all_a
#check @G11C.single_kernel_dist_bound
#print axioms G11C.single_kernel_dist_bound
#check @G11C.weighted_residual_ellipsoid
#print axioms G11C.weighted_residual_ellipsoid
#check @G11C.gramR_zero_imp_evec_zero
#print axioms G11C.gramR_zero_imp_evec_zero
#check @G11C.gramR_eq_zero_of_retained
#print axioms G11C.gramR_eq_zero_of_retained
#check @G11C.all_retained
#print axioms G11C.all_retained
#check @G11C.gramR_dup
#print axioms G11C.gramR_dup
#check @G11C.duplicated_kernels
#print axioms G11C.duplicated_kernels
#check @G11C.mismatch_bound
#print axioms G11C.mismatch_bound
#check @G11C.weighted_residual_ellipsoid_nu
#print axioms G11C.weighted_residual_ellipsoid_nu
#check @G11C.dirac_wmeas_finite
#print axioms G11C.dirac_wmeas_finite
#check @G11C.memLp_const_dirac
#print axioms G11C.memLp_const_dirac
#check @G11C.witness_budget
#print axioms G11C.witness_budget
#check @G11C.negative_control_mismatch
#print axioms G11C.negative_control_mismatch
#check @G11C.nonvacuity_singular_witness
#print axioms G11C.nonvacuity_singular_witness
#check @G11C.repr_T
#print axioms G11C.repr_T
#check @G11C.repr_P
#print axioms G11C.repr_P
#check @G11C.diag_symm
#print axioms G11C.diag_symm
#check @G11C.abstract_penrose
#print axioms G11C.abstract_penrose
#check @G11C.spectralPinv_penrose
#print axioms G11C.spectralPinv_penrose
