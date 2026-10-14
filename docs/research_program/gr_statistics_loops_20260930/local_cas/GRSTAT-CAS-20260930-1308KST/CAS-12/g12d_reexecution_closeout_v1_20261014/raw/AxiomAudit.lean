import G12DCardClosure

-- Axiom audit: every public theorem of PlanckIR, G12DInterface/G12DUVIntegrabilityEnvelope (reviewed, unchanged) and G12DCardClosure (new).

#print G12DClosure.ir_limit_one_div_sq_type
#print G12DClosure.power_weight_uv_dominating_type
#print G12DClosure.uv_dominating_integrable_type
#print G12DClosure.poly_envelope_kernel_integrable_type
#print G12DClosure.polynomial_sum_kernel_integrable_type
#print G12DClosure.rpow_kernel_integrable_type
#print G12DClosure.angular_bounded_rpow_kernel_integrable_type
#print G12DClosure.two_state_mixture_envelope_type
#print G12DClosure.between_states_weight_bound_type
#print G12DClosure.temperature_envelope_weight_type
#print G12DClosure.occupation_denominator_pos_type
#print G12DClosure.no_nonpositive_energy_mass_type
#print G12DClosure.positive_fugacity_pole_control_type

#check @CAS12PlanckIR.scaled_weight_tendsto
#print axioms CAS12PlanckIR.scaled_weight_tendsto
#check @G12D.reviewed_scaled_weight_tendsto
#print axioms G12D.reviewed_scaled_weight_tendsto
#check @G12D.weight_eq_occupation
#print axioms G12D.weight_eq_occupation
#check @G12D.weight_nonneg
#print axioms G12D.weight_nonneg
#check @G12D.weight_le_inv_sq
#print axioms G12D.weight_le_inv_sq
#check @G12D.weight_le_uv_bound
#print axioms G12D.weight_le_uv_bound
#check @G12D.weighted_power_integrable
#print axioms G12D.weighted_power_integrable
#check @G12D.weighted_kernel_density_integrable
#print axioms G12D.weighted_kernel_density_integrable
#check @G12D.weighted_kernel_sq_integrable
#print axioms G12D.weighted_kernel_sq_integrable
#check @G12D.occupation_nonneg
#print axioms G12D.occupation_nonneg
#check @G12D.occupation_envelope
#print axioms G12D.occupation_envelope
#check @G12D.mixture_occupation_envelope
#print axioms G12D.mixture_occupation_envelope
#check @G12D.reference_and_mixture_envelope
#print axioms G12D.reference_and_mixture_envelope
#check @G12D.temperature_to_beta_bound
#print axioms G12D.temperature_to_beta_bound
#check @G12D.temperature_mixture_and_reference_envelope
#print axioms G12D.temperature_mixture_and_reference_envelope
#check @G12DClosure.ir_limit_one_div_sq
#print axioms G12DClosure.ir_limit_one_div_sq
#check @G12DClosure.power_weight_uv_dominating
#print axioms G12DClosure.power_weight_uv_dominating
#check @G12DClosure.uv_dominating_integrable
#print axioms G12DClosure.uv_dominating_integrable
#check @G12DClosure.poly_envelope_kernel_integrable
#print axioms G12DClosure.poly_envelope_kernel_integrable
#check @G12DClosure.polynomial_sum_kernel_integrable
#print axioms G12DClosure.polynomial_sum_kernel_integrable
#check @G12DClosure.rpow_kernel_integrable
#print axioms G12DClosure.rpow_kernel_integrable
#check @G12DClosure.angular_bounded_rpow_kernel_integrable
#print axioms G12DClosure.angular_bounded_rpow_kernel_integrable
#check @G12DClosure.two_state_mixture_envelope
#print axioms G12DClosure.two_state_mixture_envelope
#check @G12DClosure.between_states_weight_bound
#print axioms G12DClosure.between_states_weight_bound
#check @G12DClosure.temperature_envelope_weight
#print axioms G12DClosure.temperature_envelope_weight
#check @G12DClosure.occupation_denominator_pos
#print axioms G12DClosure.occupation_denominator_pos
#check @G12DClosure.no_nonpositive_energy_mass
#print axioms G12DClosure.no_nonpositive_energy_mass
#check @G12DClosure.positive_fugacity_pole_control
#print axioms G12DClosure.positive_fugacity_pole_control
#check @G12DClosure.nonvacuity_constant_kernel
#print axioms G12DClosure.nonvacuity_constant_kernel
#check @G12DClosure.nonvacuity_temperature_instance
#print axioms G12DClosure.nonvacuity_temperature_instance
