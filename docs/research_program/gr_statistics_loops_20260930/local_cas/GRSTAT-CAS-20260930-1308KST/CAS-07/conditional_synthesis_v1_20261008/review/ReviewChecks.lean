import Synthesis
#check @CAS07M01.eta_bounds
#check @CAS07M02.remainder_bound_physical
#check @CAS07M03.scalar_volterra_comparison
#check @Cas07M04.d_norm
#check @Cas07M04.d_minus_si
#print CAS07M05.JacobiPremises
#check @CAS07M05.opnorm_error_eq
#check @CAS07M05.determinant_distance_bridge
#check @Cas07C03.FD1
#check @Cas07C03.FD2
#check @Cas07C03.FD3
#check @CAS07M06.t_domain
#check @CAS07M06.eta_order
#check @CAS07M06.refined_fd1
#check @CAS07M06.no_worse_than_fd2
#print axioms CAS07Synthesis.conditional_analytic_synthesis
#print axioms CAS07Synthesis.closed_interval_controls
#print axioms CAS07Synthesis.min_branches
example (K : ℝ) : CAS07M01.eta K 0 = -1 := by
  simp [CAS07M01.eta]
