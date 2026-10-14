import G10DTwoPoint

#check @G10D.union_bound_both
#check @G10D.dist_le_ediam_of_mem
#check @G10D.both_mem_subset
#check @G10D.confidence_set_floor
#check @G10D.expected_diam_floor
#check @G10D.small_errors_incompatible
#check @G10D.large_error_cover
#check @G10D.measurableSet_large_error
#check @G10D.estimator_two_point_prob
#check @G10D.ennreal_half_le_max
#check @G10D.lintegral_edist_sum_ge
#check @G10D.estimator_risk_floor
#check @G10D.minimaxRisk_two_point
#check @G10D.restrict_rnDeriv_ae
#check @G10D.klDiv_restrict_eq
#check @G10D.klDiv_restrict_add_compl
#check @G10D.binary_kl_le_klDiv
#check @G10D.bh_real
#check @G10D.bretagnolle_huber
#check @G10D.estimator_two_point_kl
#check @G10D.powers_bounded_integrable
#check @G10D.morph_powers_test_errors
#check @G10D.compressed_isProb
#check @G10D.morph_confidence_floor
#check @G10D.morph_estimator_floor
#check @G10D.slope_separation
#check @G10D.morph_full_data_test_bound
#check @G10D.morph_full_data_slope_estimator
#check @G10D.morph_full_laws_differ
#check @G10D.mink_Kray_obsVec
#check @G10D.onePlusZ_eq
#check @G10D.onePlusZ_u0
#check @G10D.onePlusZ_u1
#check @G10D.u0_future_unit
#check @G10D.u1_future_unit
#check @G10D.chi_contDiff
#check @G10D.u0_contDiff
#check @G10D.u1_contDiff
#check @G10D.chi_ray
#check @G10D.onePlusZ_u1_ray
#check @G10D.exterior_redshift_agree
#check @G10D.extData_eq
#check @G10D.cutout_laws_identical
#check @G10D.smoothCutoff_hasDerivAt
#check @G10D.deriv_smoothCutoff_hasDerivAt
#check @G10D.prof_hasDerivAt
#check @G10D.prof1_hasDerivAt
#check @G10D.deriv_deriv_prof
#check @G10D.prof2_bound
#check @G10D.ray_second_deriv_I13
#check @G10D.exp_one_div_25_le
#check @G10D.sqrt3_ge
#check @G10D.deltaOf_pos
#check @G10D.I14_bound
#check @G10D.ray_second_deriv_bound
#check @G10D.ray_second_deriv_bound_u0
#check @G10D.chi_origin
#check @G10D.u1_origin
#check @G10D.relative_lorentz_factor
#check @G10D.rapidity_separation
#check @G10D.dipole_separation
#check @G10D.cutout_rapidity_floor
#check @G10D.cutout_dipole_floor
#check @G10D.cutout_estimator_floor
#check @G10D.cutout_rapidity_estimator_floor
#check @G10D.g10d_cutout_main
#check @G10D.u1_ne_u0
#check @G10D.law_equality_needed
#check @G10D.coverage_satisfiable
#check @G10D.diam_vs_ediam_unbounded

#print axioms G10D.union_bound_both
#print axioms G10D.dist_le_ediam_of_mem
#print axioms G10D.both_mem_subset
#print axioms G10D.confidence_set_floor
#print axioms G10D.expected_diam_floor
#print axioms G10D.small_errors_incompatible
#print axioms G10D.large_error_cover
#print axioms G10D.measurableSet_large_error
#print axioms G10D.estimator_two_point_prob
#print axioms G10D.ennreal_half_le_max
#print axioms G10D.lintegral_edist_sum_ge
#print axioms G10D.estimator_risk_floor
#print axioms G10D.minimaxRisk_two_point
#print axioms G10D.restrict_rnDeriv_ae
#print axioms G10D.klDiv_restrict_eq
#print axioms G10D.klDiv_restrict_add_compl
#print axioms G10D.binary_kl_le_klDiv
#print axioms G10D.bh_real
#print axioms G10D.bretagnolle_huber
#print axioms G10D.estimator_two_point_kl
#print axioms G10D.powers_bounded_integrable
#print axioms G10D.morph_powers_test_errors
#print axioms G10D.compressed_isProb
#print axioms G10D.morph_confidence_floor
#print axioms G10D.morph_estimator_floor
#print axioms G10D.slope_separation
#print axioms G10D.morph_full_data_test_bound
#print axioms G10D.morph_full_data_slope_estimator
#print axioms G10D.morph_full_laws_differ
#print axioms G10D.mink_Kray_obsVec
#print axioms G10D.onePlusZ_eq
#print axioms G10D.onePlusZ_u0
#print axioms G10D.onePlusZ_u1
#print axioms G10D.u0_future_unit
#print axioms G10D.u1_future_unit
#print axioms G10D.chi_contDiff
#print axioms G10D.u0_contDiff
#print axioms G10D.u1_contDiff
#print axioms G10D.chi_ray
#print axioms G10D.onePlusZ_u1_ray
#print axioms G10D.exterior_redshift_agree
#print axioms G10D.extData_eq
#print axioms G10D.cutout_laws_identical
#print axioms G10D.smoothCutoff_hasDerivAt
#print axioms G10D.deriv_smoothCutoff_hasDerivAt
#print axioms G10D.prof_hasDerivAt
#print axioms G10D.prof1_hasDerivAt
#print axioms G10D.deriv_deriv_prof
#print axioms G10D.prof2_bound
#print axioms G10D.ray_second_deriv_I13
#print axioms G10D.exp_one_div_25_le
#print axioms G10D.sqrt3_ge
#print axioms G10D.deltaOf_pos
#print axioms G10D.I14_bound
#print axioms G10D.ray_second_deriv_bound
#print axioms G10D.ray_second_deriv_bound_u0
#print axioms G10D.chi_origin
#print axioms G10D.u1_origin
#print axioms G10D.relative_lorentz_factor
#print axioms G10D.rapidity_separation
#print axioms G10D.dipole_separation
#print axioms G10D.cutout_rapidity_floor
#print axioms G10D.cutout_dipole_floor
#print axioms G10D.cutout_estimator_floor
#print axioms G10D.cutout_rapidity_estimator_floor
#print axioms G10D.g10d_cutout_main
#print axioms G10D.u1_ne_u0
#print axioms G10D.law_equality_needed
#print axioms G10D.coverage_satisfiable
#print axioms G10D.diam_vs_ediam_unbounded
