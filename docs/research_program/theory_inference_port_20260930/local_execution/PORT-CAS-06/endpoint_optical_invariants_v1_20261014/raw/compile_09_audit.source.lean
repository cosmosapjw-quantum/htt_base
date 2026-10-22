import P06AOptics

#check @P06AOptics.core
#check @P06AOptics.s_neg
#check @P06AOptics.gamma_neg
#check @P06AOptics.h_neg
#check @P06AOptics.dot_bound
#check @P06AOptics.dot_sq_lt_one
#check @P06AOptics.one_add_dot_pos
#check @P06AOptics.one_sub_dot_pos
#check @P06AOptics.photon_null
#check @P06AOptics.photon_future
#check @P06AOptics.energy_e0
#check @P06AOptics.energy_old
#check @P06AOptics.energy_new
#check @P06AOptics.doppler_pos
#check @P06AOptics.doppler_eq_energy_ratio
#check @P06AOptics.mink_eq
#check @P06AOptics.mink_boost
#check @P06AOptics.Binv_eq
#check @P06AOptics.Bst_mul_Binv
#check @P06AOptics.Binv_mul_Bst
#check @P06AOptics.mink_newComp
#check @P06AOptics.energy_frame_independent
#check @P06AOptics.newComp_observer
#check @P06AOptics.same_ray_components
#check @P06AOptics.newComp_energy
#check @P06AOptics.newComp_photon
#check @P06AOptics.newDir_formula
#check @P06AOptics.oldDir
#check @P06AOptics.dir_unit
#check @P06AOptics.dir_photon
#check @P06AOptics.aberr_unit
#check @P06AOptics.aberr_dot
#check @P06AOptics.doppler_reciprocal
#check @P06AOptics.aberr_surjective
#check @P06AOptics.gamma1_core
#check @P06AOptics.one_add_pos_of_mem
#check @P06AOptics.D1_pos
#check @P06AOptics.ab_hasDerivAt
#check @P06AOptics.solid_angle_jacobian
#check @P06AOptics.ab_endpoints
#check @P06AOptics.ab_mem
#check @P06AOptics.ab_strictMonoOn
#check @P06AOptics.ab_inverse
#check @P06AOptics.D1_inv_sq_continuousOn
#check @P06AOptics.solid_angle_change_of_variables
#check @P06AOptics.sphere_chart_change_of_variables
#check @P06AOptics.total_solid_angle
#check @P06AOptics.band_solid_angle
#check @P06AOptics.areaDist_aberration
#check @P06AOptics.chart_link
#check @P06AOptics.redshift_endpoint
#check @P06AOptics.endpoint_optical_same_ray
#check @P06AOptics.luminosity_from_reciprocity
#check @P06AOptics.distance_ratio_invariant
#check @P06AOptics.endpoint_luminosity_same_ray
#check @P06AOptics.planckOcc_injOn
#check @P06AOptics.temperature_transform
#check @P06AOptics.inverse_temperature_affine
#check @P06AOptics.affine_coeff_domain
#check @P06AOptics.inverse_temperature_inversion
#check @P06AOptics.isotropic_blackbody_criterion
#check @P06AOptics.boosted_isotropic_sky
#check @P06AOptics.gamma_zero
#check @P06AOptics.ab_zero
#check @P06AOptics.boundary_beta_zero
#check @P06AOptics.temperature_beta_zero
#check @P06AOptics.boundary_z_zero
#check @P06AOptics.gamma_three_fifths
#check @P06AOptics.nonvacuity_witness
#check @P06AOptics.distinct_ray_counterexample
#check @CAS17C04.physical_observer_replacement_counterexample
#check @PORTCAS06EndpointScalarInvariant.endpoint_product_invariant

#print axioms P06AOptics.core
#print axioms P06AOptics.s_neg
#print axioms P06AOptics.gamma_neg
#print axioms P06AOptics.h_neg
#print axioms P06AOptics.dot_bound
#print axioms P06AOptics.dot_sq_lt_one
#print axioms P06AOptics.one_add_dot_pos
#print axioms P06AOptics.one_sub_dot_pos
#print axioms P06AOptics.photon_null
#print axioms P06AOptics.photon_future
#print axioms P06AOptics.energy_e0
#print axioms P06AOptics.energy_old
#print axioms P06AOptics.energy_new
#print axioms P06AOptics.doppler_pos
#print axioms P06AOptics.doppler_eq_energy_ratio
#print axioms P06AOptics.mink_eq
#print axioms P06AOptics.mink_boost
#print axioms P06AOptics.Binv_eq
#print axioms P06AOptics.Bst_mul_Binv
#print axioms P06AOptics.Binv_mul_Bst
#print axioms P06AOptics.mink_newComp
#print axioms P06AOptics.energy_frame_independent
#print axioms P06AOptics.newComp_observer
#print axioms P06AOptics.same_ray_components
#print axioms P06AOptics.newComp_energy
#print axioms P06AOptics.newComp_photon
#print axioms P06AOptics.newDir_formula
#print axioms P06AOptics.oldDir
#print axioms P06AOptics.dir_unit
#print axioms P06AOptics.dir_photon
#print axioms P06AOptics.aberr_unit
#print axioms P06AOptics.aberr_dot
#print axioms P06AOptics.doppler_reciprocal
#print axioms P06AOptics.aberr_surjective
#print axioms P06AOptics.gamma1_core
#print axioms P06AOptics.one_add_pos_of_mem
#print axioms P06AOptics.D1_pos
#print axioms P06AOptics.ab_hasDerivAt
#print axioms P06AOptics.solid_angle_jacobian
#print axioms P06AOptics.ab_endpoints
#print axioms P06AOptics.ab_mem
#print axioms P06AOptics.ab_strictMonoOn
#print axioms P06AOptics.ab_inverse
#print axioms P06AOptics.D1_inv_sq_continuousOn
#print axioms P06AOptics.solid_angle_change_of_variables
#print axioms P06AOptics.sphere_chart_change_of_variables
#print axioms P06AOptics.total_solid_angle
#print axioms P06AOptics.band_solid_angle
#print axioms P06AOptics.areaDist_aberration
#print axioms P06AOptics.chart_link
#print axioms P06AOptics.redshift_endpoint
#print axioms P06AOptics.endpoint_optical_same_ray
#print axioms P06AOptics.luminosity_from_reciprocity
#print axioms P06AOptics.distance_ratio_invariant
#print axioms P06AOptics.endpoint_luminosity_same_ray
#print axioms P06AOptics.planckOcc_injOn
#print axioms P06AOptics.temperature_transform
#print axioms P06AOptics.inverse_temperature_affine
#print axioms P06AOptics.affine_coeff_domain
#print axioms P06AOptics.inverse_temperature_inversion
#print axioms P06AOptics.isotropic_blackbody_criterion
#print axioms P06AOptics.boosted_isotropic_sky
#print axioms P06AOptics.gamma_zero
#print axioms P06AOptics.ab_zero
#print axioms P06AOptics.boundary_beta_zero
#print axioms P06AOptics.temperature_beta_zero
#print axioms P06AOptics.boundary_z_zero
#print axioms P06AOptics.gamma_three_fifths
#print axioms P06AOptics.nonvacuity_witness
#print axioms P06AOptics.distinct_ray_counterexample
