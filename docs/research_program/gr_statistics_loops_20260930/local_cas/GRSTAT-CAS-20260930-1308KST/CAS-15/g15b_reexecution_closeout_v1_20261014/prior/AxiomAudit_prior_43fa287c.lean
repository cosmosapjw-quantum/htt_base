import G15BSphere

open G15B

/-! Frozen targets: final types -/
#check @G15B.Pt_tangent
#check @G15B.gradS_inner
#check @G15B.gradS_tangent
#check @G15B.fderiv_eq_of_eqOn_sphere
#check @G15B.dS_eq_of_eqOn_sphere
#check @G15B.divS_eq_of_eqOn_sphere
#check @G15B.dS_eq_fderiv_of_tangent
#check @G15B.Ffield_tangent
#check @G15B.skew_tangent
#check @G15B.divS_eq_trace
#check @G15B.divS_skew
#check @G15B.divS_Ffield
#check @G15B.divS_Ffield_tracefree
#check @G15B.fderiv_quadWeight
#check @G15B.divS_smul
#check @G15B.σS_rotInv
#check @G15B.integral_fderiv_skew
#check @G15B.divergence_theorem
#check @G15B.divergence_theorem_σS
#check @G15B.divS_radial
#check @G15B.radial_negative_control
#check @G15B.skew_witness
#check @G15B.witness_first_moment
#check @G15B.ibp
#check @G15B.commutator_moments
#check @G15B.angular_B5
#check @G15B.weak_residual_B5
#check @G15B.weak_quadrupole_commutator
#check @G15B.wB5_degree_le_four
#check @G15B.B5_rank_le_four_moments
#check @G15B.bridge_Fcov
#check @G15B.bridge_Rrate

/-! Axioms: every theorem and lemma of the module -/
#print axioms G15B.bas_apply
#print axioms G15B.inner_eq_sum
#print axioms G15B.inner_bas_left
#print axioms G15B.inner_bas_right
#print axioms G15B.decomp
#print axioms G15B.clm_comp_apply
#print axioms G15B.clm_real_apply
#print axioms G15B.norm_one_sum
#print axioms G15B.inner_self_one
#print axioms G15B.Pt_tangent
#print axioms G15B.Pt_eq_PtL
#print axioms G15B.gradS_inner
#print axioms G15B.gradS_tangent
#print axioms G15B.fderiv_eq_of_eqOn_sphere
#print axioms G15B.dS_eq_of_eqOn_sphere
#print axioms G15B.divS_eq_of_eqOn_sphere
#print axioms G15B.dS_eq_fderiv_of_tangent
#print axioms G15B.Ffield_tangent
#print axioms G15B.skew_tangent
#print axioms G15B.divS_eq_trace
#print axioms G15B.divS_skew
#print axioms G15B.hasFDerivAt_Ffield
#print axioms G15B.fderiv_Ffield_apply
#print axioms G15B.divS_Ffield
#print axioms G15B.divS_Ffield_tracefree
#print axioms G15B.hasFDerivAt_coord
#print axioms G15B.fderiv_quadWeight
#print axioms G15B.divS_smul
#print axioms G15B.continuous_sphMap
#print axioms G15B.σS_rotInv
#print axioms G15B.integral_rot
#print axioms G15B.integrable_cont
#print axioms G15B.IsSkew.smul
#print axioms G15B.skew_mem
#print axioms G15B.flowL_apply
#print axioms G15B.integral_fderiv_skew
#print axioms G15B.Kuw_apply
#print axioms G15B.Kuw_skew
#print axioms G15B.hasFDerivAt_compY
#print axioms G15B.fderiv_hpair
#print axioms G15B.contDiff_hpair
#print axioms G15B.divS_decomp
#print axioms G15B.divergence_theorem
#print axioms G15B.divergence_theorem_σS
#print axioms G15B.divS_radial
#print axioms G15B.radial_negative_control
#print axioms G15B.skew_witness
#print axioms G15B.contDiff_Ffield
#print axioms G15B.witness_first_moment
#print axioms G15B.continuous_divS
#print axioms G15B.integral_dS_add_div
#print axioms G15B.ibp
#print axioms G15B.Wm_skew
#print axioms G15B.apply_eq_Wm
#print axioms G15B.continuous_coord
#print axioms G15B.fderiv_Iquad
#print axioms G15B.contDiff_Iquad
#print axioms G15B.integrable_quad
#print axioms G15B.commutator_moments
#print axioms G15B.Ffield_apply
#print axioms G15B.continuous_wB5
#print axioms G15B.angular_B5
#print axioms G15B.weak_residual_B5
#print axioms G15B.weak_quadrupole_commutator
#print axioms G15B.eval_pB5
#print axioms G15B.td_add
#print axioms G15B.td_sub
#print axioms G15B.td_mul
#print axioms G15B.td_sum
#print axioms G15B.td_mono
#print axioms G15B.td_C
#print axioms G15B.td_X
#print axioms G15B.pB5_totalDegree
#print axioms G15B.wB5_degree_le_four
#print axioms G15B.B5_rank_le_four_moments
#print axioms G15B.sp_add
#print axioms G15B.sp_smul
#print axioms G15B.sp_emb3
#print axioms G15B.sig4_apply
#print axioms G15B.mink_emb3
#print axioms G15B.mink_accel_emb3
#print axioms G15B.bridge_Fcov
#print axioms G15B.bridge_Rrate
