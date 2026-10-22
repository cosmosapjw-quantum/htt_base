import G09ADefinitions

/-! G09-A axiom audit: #check and #print axioms for every public theorem of G09ADefinitions. -/

#check @G09A.stf_transpose
#print axioms G09A.stf_transpose
#check @G09A.stf_trace
#print axioms G09A.stf_trace
#check @G09A.stf_injective
#print axioms G09A.stf_injective
#check @G09A.stf_stfCoords
#print axioms G09A.stf_stfCoords
#check @G09A.quad_eq
#print axioms G09A.quad_eq
#check @G09A.finrank_IPar
#print axioms G09A.finrank_IPar
#check @G09A.finrank_HPar
#print axioms G09A.finrank_HPar
#check @G09A.finrank_PhysPar
#print axioms G09A.finrank_PhysPar
#check @G09A.Dmap_injective
#print axioms G09A.Dmap_injective
#check @G09A.finrank_range_DE9
#print axioms G09A.finrank_range_DE9
#check @G09A.rank_concat_identity
#print axioms G09A.rank_concat_identity
#check @G09A.rank13_iff
#print axioms G09A.rank13_iff
#check @G09A.rank13_needs_N
#print axioms G09A.rank13_needs_N
#check @G09A.Hval_add
#print axioms G09A.Hval_add
#check @G09A.Hval_smul
#print axioms G09A.Hval_smul
#check @G09A.Hval_liftLin
#print axioms G09A.Hval_liftLin
#check @G09A.two_radius_injective
#print axioms G09A.two_radius_injective
#check @G09A.finrank_range_of_injective_13
#print axioms G09A.finrank_range_of_injective_13
#check @G09A.two_radius_rank13
#print axioms G09A.two_radius_rank13
#check @G09A.finrank_range_lt_13_of_not_injective
#print axioms G09A.finrank_range_lt_13_of_not_injective
#check @G09A.two_radius_fails_of_E4_deficient
#print axioms G09A.two_radius_fails_of_E4_deficient
#check @G09A.dirStar_unit
#print axioms G09A.dirStar_unit
#check @G09A.dirStar_unisolvent
#print axioms G09A.dirStar_unisolvent
#check @G09A.σStar_E4
#print axioms G09A.σStar_E4
#check @G09A.witness_rank13
#print axioms G09A.witness_rank13
#check @G09A.one_le_one_add_dot3
#print axioms G09A.one_le_one_add_dot3
#check @G09A.one_le_zeta0
#print axioms G09A.one_le_zeta0
#check @G09A.zeta0_pos
#print axioms G09A.zeta0_pos
#check @G09A.massShell_hyperboloid
#print axioms G09A.massShell_hyperboloid
#check @G09A.massShell_injective
#print axioms G09A.massShell_injective
#check @G09A.physMean_eq_X
#print axioms G09A.physMean_eq_X
#check @G09A.Jphys_apply
#print axioms G09A.Jphys_apply
#check @G09A.hasFDerivAt_zeta0
#print axioms G09A.hasFDerivAt_zeta0
#check @G09A.hasFDerivAt_physMean
#print axioms G09A.hasFDerivAt_physMean
#check @G09A.dEmb_injective
#print axioms G09A.dEmb_injective
#check @G09A.chartDeriv_injective
#print axioms G09A.chartDeriv_injective
#check @G09A.dEmb_rank3
#print axioms G09A.dEmb_rank3
#check @G09A.Xmap_injective_of_rank13
#print axioms G09A.Xmap_injective_of_rank13
#check @G09A.rank12_of_rank13
#print axioms G09A.rank12_of_rank13
#check @G09A.witness_rank12
#print axioms G09A.witness_rank12
#check @G09A.aliasDenom_pos
#print axioms G09A.aliasDenom_pos
#check @G09A.aliasRadius_pos
#print axioms G09A.aliasRadius_pos
#check @G09A.scale_cancel
#print axioms G09A.scale_cancel
#check @G09A.const_radius_range_le
#print axioms G09A.const_radius_range_le
#check @G09A.range_X_of_le
#print axioms G09A.range_X_of_le
#check @G09A.const_radius_rank
#print axioms G09A.const_radius_rank
#check @G09A.const_radius_rank_le9
#print axioms G09A.const_radius_rank_le9
#check @G09A.const_radius_rank9
#print axioms G09A.const_radius_rank9
#check @G09A.const_radius_Jphys_rank9
#print axioms G09A.const_radius_Jphys_rank9
#check @G09A.const_radius_exact_degeneracy
#print axioms G09A.const_radius_exact_degeneracy
#check @G09A.const_radius_physMean_degeneracy
#print axioms G09A.const_radius_physMean_degeneracy
#check @G09A.two_radius_equal_fails
#print axioms G09A.two_radius_equal_fails
#check @G09A.Hval_aliasLift
#print axioms G09A.Hval_aliasLift
#check @G09A.radial_alias_range_le
#print axioms G09A.radial_alias_range_le
#check @G09A.radial_alias_rank
#print axioms G09A.radial_alias_rank
#check @G09A.radial_alias_rank9
#print axioms G09A.radial_alias_rank9
#check @G09A.witness_radial_alias_rank9
#print axioms G09A.witness_radial_alias_rank9
#check @G09A.nativeZ_rhoOf
#print axioms G09A.nativeZ_rhoOf
#check @G09A.rhoOf_native_means
#print axioms G09A.rhoOf_native_means
#check @G09A.rhoOf_true
#print axioms G09A.rhoOf_true
#check @G09A.meanMu_arg_pos
#print axioms G09A.meanMu_arg_pos
#check @G09A.eta_nonneg
#print axioms G09A.eta_nonneg
#check @G09A.one_sub_etaL_pos
#print axioms G09A.one_sub_etaL_pos
#check @G09A.E5_nonneg
#print axioms G09A.E5_nonneg
#check @G09A.continuous_zeta0
#print axioms G09A.continuous_zeta0
#check @G09A.continuous_Hval
#print axioms G09A.continuous_Hval
#check @G09A.strict_slack_local_identification
#print axioms G09A.strict_slack_local_identification
#check @G09A.slack_boundary_no_neighbourhood
#print axioms G09A.slack_boundary_no_neighbourhood
