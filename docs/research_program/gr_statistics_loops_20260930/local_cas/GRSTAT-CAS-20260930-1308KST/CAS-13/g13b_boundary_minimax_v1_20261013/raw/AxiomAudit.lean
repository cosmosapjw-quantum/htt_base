import G13BBoundaryMinimax

/-! G13-B axiom audit: frozen targets first, then every helper theorem. -/

#check @CAS13G13B.region_necessary
#check @CAS13G13B.region_exact
#check @CAS13G13B.region_strata
#check @CAS13G13B.lowerCurve_lt_chord
#check @CAS13G13B.region_corners
#check @CAS13G13B.lower_boundary_dirac_collapse
#check @CAS13G13B.upper_boundary_endpoint_collapse
#check @CAS13G13B.lower_boundary_sharp
#check @CAS13G13B.upper_boundary_sharp
#check @CAS13G13B.energy_only_bounds
#check @CAS13G13B.energy_only_attained
#check @CAS13G13B.energy_fibre_nonempty_iff
#check @CAS13G13B.fibre_inclusion
#check @CAS13G13B.endpoint_strict_nesting
#check @CAS13G13B.interval_nesting_p56
#check @CAS13G13B.minimax_degenerate
#check @CAS13G13B.fibreMinimax_of_sharpInterval
#check @CAS13G13B.interior_sharp_minimax
#check @CAS13G13B.lower_boundary_minimax
#check @CAS13G13B.upper_boundary_minimax
#check @CAS13G13B.closed_region_sharp_minimax
#check @CAS13G13B.node_ratio_zero_div_zero
#check @CAS13G13B.cross_prior_nesting_fails
#check @CAS13G13B.lowerCurve_lt_iff
#check @CAS13G13B.strictInterior_witness
#check @CAS13G13B.boundary_witness
#check @CAS13G13B.integrable_of_Icc
#check @CAS13G13B.admissible_of_mem
#check @CAS13G13B.moment_bounds
#check @CAS13G13B.integral_poly
#check @CAS13G13B.measure_eq_of_real
#check @CAS13G13B.eq_dirac_of_ae
#check @CAS13G13B.cube_rpow
#check @CAS13G13B.rpow_four_div
#check @CAS13G13B.fibre_cube
#check @CAS13G13B.lower_gap_nonneg
#check @CAS13G13B.lower_gap_integral
#check @CAS13G13B.lower_ineq_core
#check @CAS13G13B.lower_rigid_core
#check @CAS13G13B.chord_gap_factor
#check @CAS13G13B.chord_gap_nonpos
#check @CAS13G13B.chord_gap_integral
#check @CAS13G13B.cube_den_pos
#check @CAS13G13B.quartic_den_pos
#check @CAS13G13B.upper_ineq_core
#check @CAS13G13B.upper_rigid_core
#check @CAS13G13B.indicator_two_point
#check @CAS13G13B.sharpInterval_of_const
#check @CAS13G13B.cube_root_mem
#check @CAS13G13B.integral_mix
#check @CAS13G13B.mix_mem
#check @CAS13G13B.sharpInterval_of_extremes
#check @CAS13G13B.chordE_le
#check @CAS13G13B.chordE_lt
#check @CAS13G13B.energy_dirac_mem
#check @CAS13G13B.interior_p56_bounds
#check @CAS13G13B.chord_value_pos

#print axioms CAS13G13B.region_necessary
#print axioms CAS13G13B.region_exact
#print axioms CAS13G13B.region_strata
#print axioms CAS13G13B.lowerCurve_lt_chord
#print axioms CAS13G13B.region_corners
#print axioms CAS13G13B.lower_boundary_dirac_collapse
#print axioms CAS13G13B.upper_boundary_endpoint_collapse
#print axioms CAS13G13B.lower_boundary_sharp
#print axioms CAS13G13B.upper_boundary_sharp
#print axioms CAS13G13B.energy_only_bounds
#print axioms CAS13G13B.energy_only_attained
#print axioms CAS13G13B.energy_fibre_nonempty_iff
#print axioms CAS13G13B.fibre_inclusion
#print axioms CAS13G13B.endpoint_strict_nesting
#print axioms CAS13G13B.interval_nesting_p56
#print axioms CAS13G13B.minimax_degenerate
#print axioms CAS13G13B.fibreMinimax_of_sharpInterval
#print axioms CAS13G13B.interior_sharp_minimax
#print axioms CAS13G13B.lower_boundary_minimax
#print axioms CAS13G13B.upper_boundary_minimax
#print axioms CAS13G13B.closed_region_sharp_minimax
#print axioms CAS13G13B.node_ratio_zero_div_zero
#print axioms CAS13G13B.cross_prior_nesting_fails
#print axioms CAS13G13B.lowerCurve_lt_iff
#print axioms CAS13G13B.strictInterior_witness
#print axioms CAS13G13B.boundary_witness
#print axioms CAS13G13B.integrable_of_Icc
#print axioms CAS13G13B.admissible_of_mem
#print axioms CAS13G13B.moment_bounds
#print axioms CAS13G13B.integral_poly
#print axioms CAS13G13B.measure_eq_of_real
#print axioms CAS13G13B.eq_dirac_of_ae
#print axioms CAS13G13B.cube_rpow
#print axioms CAS13G13B.rpow_four_div
#print axioms CAS13G13B.fibre_cube
#print axioms CAS13G13B.lower_gap_nonneg
#print axioms CAS13G13B.lower_gap_integral
#print axioms CAS13G13B.lower_ineq_core
#print axioms CAS13G13B.lower_rigid_core
#print axioms CAS13G13B.chord_gap_factor
#print axioms CAS13G13B.chord_gap_nonpos
#print axioms CAS13G13B.chord_gap_integral
#print axioms CAS13G13B.cube_den_pos
#print axioms CAS13G13B.quartic_den_pos
#print axioms CAS13G13B.upper_ineq_core
#print axioms CAS13G13B.upper_rigid_core
#print axioms CAS13G13B.indicator_two_point
#print axioms CAS13G13B.sharpInterval_of_const
#print axioms CAS13G13B.cube_root_mem
#print axioms CAS13G13B.integral_mix
#print axioms CAS13G13B.mix_mem
#print axioms CAS13G13B.sharpInterval_of_extremes
#print axioms CAS13G13B.chordE_le
#print axioms CAS13G13B.chordE_lt
#print axioms CAS13G13B.energy_dirac_mem
#print axioms CAS13G13B.interior_p56_bounds
#print axioms CAS13G13B.chord_value_pos
