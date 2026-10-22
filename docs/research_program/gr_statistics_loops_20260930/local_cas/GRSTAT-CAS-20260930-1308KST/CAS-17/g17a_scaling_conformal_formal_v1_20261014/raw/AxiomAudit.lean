import G17ACore
import G17AOptics

/-! G17-A axiom audit: #check and #print axioms for every public declaration. -/

#check @G17A.Pt
#check @G17A.Arr2
#check @G17A.chartPoint
#check @G17A.pd
#check @G17A.ginv
#check @G17A.chris
#check @G17A.covVec
#check @G17A.selfCov
#check @G17A.lower
#check @G17A.covCov
#check @G17A.Bcov
#check @G17A.Acov
#check @G17A.riemann
#check @G17A.contr
#check @G17A.covNorm
#check @G17A.hinv
#check @G17A.conf
#check @G17A.physVel
#check @G17A.Contra
#check @G17A.Cov
#check @G17A.Measured
#check @G17A.accelContra
#check @G17A.accelCov
#check @G17A.Orthonormal
#check @G17A.tet2
#check @G17A.tetVec
#check @G17A.measNorm
#check @G17A.freq
#check @G17A.onePlusZ
#check @G17A.zOf
#check @G17A.scaledLorentz
#check @G17A.Kvec
#check @G17A.gammaW
#check @G17A.relW
#check @G17A.betaSqW
#check @G17A.contr_smul
#check @G17A.sum_one_mul
#check @G17A.inv_smul_real
#check @G17A.pd_const_smul
#check @G17A.ginv_const_smul
#check @G17A.inv_mul_entry
#check @G17A.unit_preserved
#check @G17A.lorentz_Kvec_self
#check @G17A.lorentz_o_Kvec
#check @G17A.null_normalization_scale
#check @G17A.intercept_invariant
#check @G17A.intercept_formula
#check @G17A.gamma_scale
#check @G17A.betaSqW_lorentz
#check @G17A.relW_scale
#check @G17A.betaSq_scale
#check @G17A.beta_scale
#check @G17A.chris_scale
#check @G17A.physVel_scale
#check @G17A.velocity_norm_scale
#check @G17A.accelContra_scale
#check @G17A.lower_scale
#check @G17A.covCov_scale
#check @G17A.Bcov_scale
#check @G17A.accelCov_scale
#check @G17A.orthonormal_scale
#check @G17A.B_measured_scale
#check @G17A.accelContra_comp_scale
#check @G17A.A_measured_scale
#check @G17A.A_measNorm_scale
#check @G17A.chris_scale_fun
#check @G17A.riemann_scale
#check @G17A.chart_null_normalization
#check @G17A.affine_reparam
#check @G17A.freq_smul
#check @G17A.redshift_const_scale
#check @G17A.slope_scale
#check @G17A.pd_expsmul
#check @G17A.pd_conf
#check @G17A.ginv_conf
#check @G17A.conformal_christoffel
#check @G17A.conformal_selfCov
#check @G17A.conformal_velocity_norm
#check @G17A.conformal_accel
#check @G17A.conformal_null_affine
#check @G17A.conformal_covector_null
#check @G17A.conformal_freq
#check @G17A.conformal_redshift
#check @G17A.conformal_redshift_z
#check @G17A.redshift_const_is_special_case
#check @G17A.eta4
#check @G17A.e0
#check @G17A.eta4_diag
#check @G17A.eta4_det
#check @G17A.eta4_inv
#check @G17A.minkowski_witness
#check @G17A.pd_const
#check @G17A.pd_coord
#check @G17A.conf_grad_counterexample
#check @G17A.scale_inf_no_floor
#check @G17A.tidalMat
#check @G17A.remBound
#check @G17A.Dom5
#check @G17A.Dom6
#check @G17A.modulus
#check @G17A.zMean
#check @G17A.tidal_scale
#check @G17A.matrixOf_injective
#check @G17A.tidal_op_scale
#check @G17A.dA_scale
#check @G17A.bound_indices
#check @G17A.eta_scale
#check @G17A.M2_identity
#check @G17A.M2_scale
#check @G17A.remBound_scale
#check @G17A.dom5_scale
#check @G17A.dom6_scale
#check @G17A.modulus_offset_invariant
#check @G17A.zMean_invariant
#check @G17A.eta_zero_one
#check @G17A.fixed_bound_breaks_domain
#check @G17A.dA_scale_witness
#check @G17A.tidal_flat_witness
#check @G17A.straight_line_geodesic

#print axioms G17A.chartPoint
#print axioms G17A.pd
#print axioms G17A.ginv
#print axioms G17A.chris
#print axioms G17A.covVec
#print axioms G17A.selfCov
#print axioms G17A.lower
#print axioms G17A.covCov
#print axioms G17A.Bcov
#print axioms G17A.Acov
#print axioms G17A.riemann
#print axioms G17A.contr
#print axioms G17A.covNorm
#print axioms G17A.hinv
#print axioms G17A.conf
#print axioms G17A.physVel
#print axioms G17A.accelContra
#print axioms G17A.accelCov
#print axioms G17A.Orthonormal
#print axioms G17A.tet2
#print axioms G17A.tetVec
#print axioms G17A.measNorm
#print axioms G17A.freq
#print axioms G17A.onePlusZ
#print axioms G17A.zOf
#print axioms G17A.scaledLorentz
#print axioms G17A.Kvec
#print axioms G17A.gammaW
#print axioms G17A.relW
#print axioms G17A.betaSqW
#print axioms G17A.contr_smul
#print axioms G17A.sum_one_mul
#print axioms G17A.inv_smul_real
#print axioms G17A.pd_const_smul
#print axioms G17A.ginv_const_smul
#print axioms G17A.inv_mul_entry
#print axioms G17A.unit_preserved
#print axioms G17A.lorentz_Kvec_self
#print axioms G17A.lorentz_o_Kvec
#print axioms G17A.null_normalization_scale
#print axioms G17A.intercept_invariant
#print axioms G17A.intercept_formula
#print axioms G17A.gamma_scale
#print axioms G17A.betaSqW_lorentz
#print axioms G17A.relW_scale
#print axioms G17A.betaSq_scale
#print axioms G17A.beta_scale
#print axioms G17A.chris_scale
#print axioms G17A.physVel_scale
#print axioms G17A.velocity_norm_scale
#print axioms G17A.accelContra_scale
#print axioms G17A.lower_scale
#print axioms G17A.covCov_scale
#print axioms G17A.Bcov_scale
#print axioms G17A.accelCov_scale
#print axioms G17A.orthonormal_scale
#print axioms G17A.B_measured_scale
#print axioms G17A.accelContra_comp_scale
#print axioms G17A.A_measured_scale
#print axioms G17A.A_measNorm_scale
#print axioms G17A.chris_scale_fun
#print axioms G17A.riemann_scale
#print axioms G17A.chart_null_normalization
#print axioms G17A.affine_reparam
#print axioms G17A.freq_smul
#print axioms G17A.redshift_const_scale
#print axioms G17A.slope_scale
#print axioms G17A.pd_expsmul
#print axioms G17A.pd_conf
#print axioms G17A.ginv_conf
#print axioms G17A.conformal_christoffel
#print axioms G17A.conformal_selfCov
#print axioms G17A.conformal_velocity_norm
#print axioms G17A.conformal_accel
#print axioms G17A.conformal_null_affine
#print axioms G17A.conformal_covector_null
#print axioms G17A.conformal_freq
#print axioms G17A.conformal_redshift
#print axioms G17A.conformal_redshift_z
#print axioms G17A.redshift_const_is_special_case
#print axioms G17A.eta4
#print axioms G17A.e0
#print axioms G17A.eta4_diag
#print axioms G17A.eta4_det
#print axioms G17A.eta4_inv
#print axioms G17A.minkowski_witness
#print axioms G17A.pd_const
#print axioms G17A.pd_coord
#print axioms G17A.conf_grad_counterexample
#print axioms G17A.scale_inf_no_floor
#print axioms G17A.tidalMat
#print axioms G17A.remBound
#print axioms G17A.Dom5
#print axioms G17A.Dom6
#print axioms G17A.modulus
#print axioms G17A.zMean
#print axioms G17A.tidal_scale
#print axioms G17A.matrixOf_injective
#print axioms G17A.tidal_op_scale
#print axioms G17A.dA_scale
#print axioms G17A.bound_indices
#print axioms G17A.eta_scale
#print axioms G17A.M2_identity
#print axioms G17A.M2_scale
#print axioms G17A.remBound_scale
#print axioms G17A.dom5_scale
#print axioms G17A.dom6_scale
#print axioms G17A.modulus_offset_invariant
#print axioms G17A.zMean_invariant
#print axioms G17A.eta_zero_one
#print axioms G17A.fixed_bound_breaks_domain
#print axioms G17A.dA_scale_witness
#print axioms G17A.tidal_flat_witness
#print axioms G17A.straight_line_geodesic
#print axioms G17A.orthonormal_scale.velocity_norm_scale_gen
