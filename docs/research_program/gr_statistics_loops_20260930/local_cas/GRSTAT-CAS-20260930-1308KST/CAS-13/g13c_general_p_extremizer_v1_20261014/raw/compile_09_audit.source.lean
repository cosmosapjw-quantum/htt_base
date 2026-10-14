import G13CGeneralPExtremizer

/-! G13-C axiom audit: frozen targets first, then every helper theorem. -/

#check @CAS13G13C.wronskian_one
#check @CAS13G13C.wronskian_two
#check @CAS13G13C.wronskian_three
#check @CAS13G13C.wronskian_power_system
#check @CAS13G13C.wronskian_chain_pos
#check @CAS13G13C.reduced_deriv2_wronskian
#check @CAS13G13C.reduced_convex_of_wronskian_pos
#check @CAS13G13C.residual_hasDerivAt
#check @CAS13G13C.interp_conditions
#check @CAS13G13C.interp_slope
#check @CAS13G13C.minorant_of_reduced_convex
#check @CAS13G13C.majorant_of_reduced_convex
#check @CAS13G13C.reduced_convex
#check @CAS13G13C.lower_interp_minorant
#check @CAS13G13C.upper_interp_majorant
#check @CAS13G13C.interior_real_bounds
#check @CAS13G13C.interior_real_sharp
#check @CAS13G13C.rfibreMinimax_of_rsharpInterval
#check @CAS13G13C.interior_real_sharp_minimax
#check @CAS13G13C.interior_real_exists
#check @CAS13G13C.interior_real_nesting
#check @CAS13G13C.interior_sharp_nat
#check @CAS13G13C.lower_boundary_rsharp
#check @CAS13G13C.upper_boundary_rsharp
#check @CAS13G13C.closed_region_real_sharp_minimax
#check @CAS13G13C.wronskian_negative_exponent
#check @CAS13G13C.minorant_fails_negative_exponent
#check @CAS13G13C.real_witness
#check @CAS13G13C.rpow_shift
#check @CAS13G13C.reduced_deriv1
#check @CAS13G13C.reduced_deriv2
#check @CAS13G13C.hermite_hasDerivAt
#check @CAS13G13C.interpDet_eq
#check @CAS13G13C.interpDet_ne
#check @CAS13G13C.reducedH_three
#check @CAS13G13C.residual_monotoneOn
#check @CAS13G13C.residual_antitoneOn
#check @CAS13G13C.rolle_reduced
#check @CAS13G13C.minorant_core
#check @CAS13G13C.majorant_core
#check @CAS13G13C.integrable_rpow_of_mem
#check @CAS13G13C.rsharpInterval_of_extremes
#check @CAS13G13C.rmoment_natCast
#check @CAS13G13C.rsharpInterval_of_const
#check @CAS13G13C.chord_rvalue_pos

#print axioms CAS13G13C.wronskian_one
#print axioms CAS13G13C.wronskian_two
#print axioms CAS13G13C.wronskian_three
#print axioms CAS13G13C.wronskian_power_system
#print axioms CAS13G13C.wronskian_chain_pos
#print axioms CAS13G13C.reduced_deriv2_wronskian
#print axioms CAS13G13C.reduced_convex_of_wronskian_pos
#print axioms CAS13G13C.residual_hasDerivAt
#print axioms CAS13G13C.interp_conditions
#print axioms CAS13G13C.interp_slope
#print axioms CAS13G13C.minorant_of_reduced_convex
#print axioms CAS13G13C.majorant_of_reduced_convex
#print axioms CAS13G13C.reduced_convex
#print axioms CAS13G13C.lower_interp_minorant
#print axioms CAS13G13C.upper_interp_majorant
#print axioms CAS13G13C.interior_real_bounds
#print axioms CAS13G13C.interior_real_sharp
#print axioms CAS13G13C.rfibreMinimax_of_rsharpInterval
#print axioms CAS13G13C.interior_real_sharp_minimax
#print axioms CAS13G13C.interior_real_exists
#print axioms CAS13G13C.interior_real_nesting
#print axioms CAS13G13C.interior_sharp_nat
#print axioms CAS13G13C.lower_boundary_rsharp
#print axioms CAS13G13C.upper_boundary_rsharp
#print axioms CAS13G13C.closed_region_real_sharp_minimax
#print axioms CAS13G13C.wronskian_negative_exponent
#print axioms CAS13G13C.minorant_fails_negative_exponent
#print axioms CAS13G13C.real_witness
#print axioms CAS13G13C.rpow_shift
#print axioms CAS13G13C.reduced_deriv1
#print axioms CAS13G13C.reduced_deriv2
#print axioms CAS13G13C.hermite_hasDerivAt
#print axioms CAS13G13C.interpDet_eq
#print axioms CAS13G13C.interpDet_ne
#print axioms CAS13G13C.reducedH_three
#print axioms CAS13G13C.residual_monotoneOn
#print axioms CAS13G13C.residual_antitoneOn
#print axioms CAS13G13C.rolle_reduced
#print axioms CAS13G13C.minorant_core
#print axioms CAS13G13C.majorant_core
#print axioms CAS13G13C.integrable_rpow_of_mem
#print axioms CAS13G13C.rsharpInterval_of_extremes
#print axioms CAS13G13C.rmoment_natCast
#print axioms CAS13G13C.rsharpInterval_of_const
#print axioms CAS13G13C.chord_rvalue_pos

/-! Instantiation: ℕ-form at p = 7 on the G13-B interior witness (consistency beyond p = 5, 6). -/
example : ∃ u d : ℝ, CAS13G13B.SharpInterval (CAS13G13B.NEFibre 1 2 (9 / 2) 8) 7
    (CAS13G13B.lowerEnd 1 (9 / 2) u 7) (CAS13G13B.upperEnd 2 (9 / 2) d 7) := by
  obtain ⟨hI, -⟩ := CAS13G13B.strictInterior_witness
  obtain ⟨u, hu, -⟩ := CAS13C02.lower_node_existsUnique hI
  obtain ⟨d, hd, -⟩ := CAS13C02.upper_node_existsUnique hI
  exact ⟨u, d, by exact_mod_cast (CAS13G13C.interior_sharp_nat hI 7 (by norm_num) hu hd).1⟩
