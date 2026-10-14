import Mathlib
import G12AContinuumAdjoint
import G12AHilbertAdjoint

/-! G12-A axiom audit: #check and #print axioms for every public declaration of both modules. -/

#check @G12A.inner_L2W
#print axioms G12A.inner_L2W
#check @G12A.norm_sq_L2W
#print axioms G12A.norm_sq_L2W
#check @G12A.BoundedRoute
#print axioms G12A.BoundedRoute
#check @G12A.BoundedRoute.transpose
#print axioms G12A.BoundedRoute.transpose
#check @G12A.gain_congr_ae
#print axioms G12A.gain_congr_ae
#check @G12A.collOp_congr_ae
#print axioms G12A.collOp_congr_ae
#check @G12A.section_integrable
#print axioms G12A.section_integrable
#check @G12A.gain_sq_integral_le
#print axioms G12A.gain_sq_integral_le
#check @G12A.gain_toLp_norm_le
#print axioms G12A.gain_toLp_norm_le
#check @G12A.collLp
#print axioms G12A.collLp
#check @G12A.collLp_coeFn
#print axioms G12A.collLp_coeFn
#check @G12A.collLp_add
#print axioms G12A.collLp_add
#check @G12A.collLp_smul
#print axioms G12A.collLp_smul
#check @G12A.collLp_norm_le
#print axioms G12A.collLp_norm_le
#check @G12A.collLin
#print axioms G12A.collLin
#check @G12A.collCLM
#print axioms G12A.collCLM
#check @G12A.collCLM_coeFn
#print axioms G12A.collCLM_coeFn
#check @G12A.collLp_inner_adjoint
#print axioms G12A.collLp_inner_adjoint
#check @G12A.collCLM_adjoint
#print axioms G12A.collCLM_adjoint
#check @G12A.collCLM_adjoint_coeFn
#print axioms G12A.collCLM_adjoint_coeFn
#check @G12A.collCLM_kernel_congr
#print axioms G12A.collCLM_kernel_congr
#check @G12A.transposeKernel_thomsonP
#print axioms G12A.transposeKernel_thomsonP
#check @G12A.photon_boundedRoute
#print axioms G12A.photon_boundedRoute
#check @G12A.photon_collCLM_selfAdjoint
#print axioms G12A.photon_collCLM_selfAdjoint
#check @G12A.gain
#print axioms G12A.gain
#check @G12A.collOp
#print axioms G12A.collOp
#check @G12A.transposeKernel
#print axioms G12A.transposeKernel
#check @G12A.collAdj
#print axioms G12A.collAdj
#check @G12A.fubKernel
#print axioms G12A.fubKernel
#check @G12A.collEvec
#print axioms G12A.collEvec
#check @G12A.angSwap
#print axioms G12A.angSwap
#check @G12A.collAdj_eq_collOp_of_symm
#print axioms G12A.collAdj_eq_collOp_of_symm
#check @G12A.collOp_sub_of_integrable
#print axioms G12A.collOp_sub_of_integrable
#check @G12A.collEvec_eq_sub
#print axioms G12A.collEvec_eq_sub
#check @G12A.angSwap_apply
#print axioms G12A.angSwap_apply
#check @G12A.angSwap_measurePreserving
#print axioms G12A.angSwap_measurePreserving
#check @G12A.adjoint_pair
#print axioms G12A.adjoint_pair
#check @G12A.sq_integral_le
#print axioms G12A.sq_integral_le
#check @G12A.amgm_abs
#print axioms G12A.amgm_abs
#check @G12A.ac_of_pos
#print axioms G12A.ac_of_pos
#check @G12A.wsq_integrable
#print axioms G12A.wsq_integrable
#check @G12A.fubKernel_integrable
#print axioms G12A.fubKernel_integrable
#check @G12A.gain_memLp
#print axioms G12A.gain_memLp
#check @G12A.collOp_memLp
#print axioms G12A.collOp_memLp
#check @G12A.collAdj_memLp
#print axioms G12A.collAdj_memLp
#check @G12A.collision_ellipsoid
#print axioms G12A.collision_ellipsoid
#check @G12A.collision_ellipsoid_bounded
#print axioms G12A.collision_ellipsoid_bounded
#check @G12A.collision_exact_of_retained
#print axioms G12A.collision_exact_of_retained
#check @G12A.collision_moment_of_representation
#print axioms G12A.collision_moment_of_representation
#check @G12A.collAdj_eigen
#print axioms G12A.collAdj_eigen
#check @G12A.collEvec_eigen
#print axioms G12A.collEvec_eigen
#check @G12A.constant_tau_retained
#print axioms G12A.constant_tau_retained
#check @G12A.constant_tau_exact
#print axioms G12A.constant_tau_exact
#check @G12A.integral_count_bool
#print axioms G12A.integral_count_bool
#check @G12A.integral_count_bool2
#print axioms G12A.integral_count_bool2
#check @G12A.sgnB
#print axioms G12A.sgnB
#check @G12A.energy_dependent_tau_counterexample
#print axioms G12A.energy_dependent_tau_counterexample
#check @G12A.nonvacuity_bounded_witness
#print axioms G12A.nonvacuity_bounded_witness
#check @G12A.thomsonP
#print axioms G12A.thomsonP
#check @G12A.thomsonP_symm
#print axioms G12A.thomsonP_symm
#check @G12A.thomsonP_measurable
#print axioms G12A.thomsonP_measurable
#check @G12A.thomsonP_bounds
#print axioms G12A.thomsonP_bounds
#check @G12A.energyMeasure
#print axioms G12A.energyMeasure
#check @G12A.energyMeasure_sFinite
#print axioms G12A.energyMeasure_sFinite
#check @G12A.dOmega_isFinite
#print axioms G12A.dOmega_isFinite
#check @G12A.nu_eq_prod
#print axioms G12A.nu_eq_prod
#check @G12A.photonW
#print axioms G12A.photonW
#check @G12A.weight_measurable
#print axioms G12A.weight_measurable
#check @G12A.weight_pos
#print axioms G12A.weight_pos
#check @G12A.nu_ae_pos
#print axioms G12A.nu_ae_pos
#check @G12A.photon_envelope
#print axioms G12A.photon_envelope
#check @G12A.photon_thomson_collision_ellipsoid
#print axioms G12A.photon_thomson_collision_ellipsoid
