import G08DInversion

/-! G08-D axiom audit: #check and #print axioms for every public theorem
(26 in G08DCertificates, 23 in G08DInversion), the adapter/checker definitions, executable
checker evaluations, and a joint-satisfiability (non-vacuity) instance of the Gaussian size
control.  Accepted axioms: propext, Classical.choice, Quot.sound. -/

open MeasureTheory ProbabilityTheory Matrix WithLp G08C

-- ## theorems
#check @G08D.nullConfSet_eq_confSet_inter
#print axioms G08D.nullConfSet_eq_confSet_inter
#check @G08D.WitnessCert.sound
#print axioms G08D.WitnessCert.sound
#check @G08D.LowerBoundCert.sound
#print axioms G08D.LowerBoundCert.sound
#check @G08D.CoverCert.sound
#print axioms G08D.CoverCert.sound
#check @G08D.DualCert.sound
#print axioms G08D.DualCert.sound
#check @G08D.ExclCert.sound
#print axioms G08D.ExclCert.sound
#check @G08D.witness_excl_incompatible
#print axioms G08D.witness_excl_incompatible
#check @G08D.OptReport.toCert_unverified
#print axioms G08D.OptReport.toCert_unverified
#check @G08D.sourceDecision_run_irrelevant
#print axioms G08D.sourceDecision_run_irrelevant
#check @G08D.sourceDecision_unverified
#print axioms G08D.sourceDecision_unverified
#check @G08D.sourceDecision_rejected_requires_certs
#print axioms G08D.sourceDecision_rejected_requires_certs
#check @G08D.sourceDecision_no_null_excl
#print axioms G08D.sourceDecision_no_null_excl
#check @G08D.sourceDecision_no_full_excl
#print axioms G08D.sourceDecision_no_full_excl
#check @G08D.sourceDecision_sound
#print axioms G08D.sourceDecision_sound
#check @G08D.checkWitness_sound
#print axioms G08D.checkWitness_sound
#check @G08D.checkExclFinite_sound
#print axioms G08D.checkExclFinite_sound
#check @G08D.checkExclFinite_complete
#print axioms G08D.checkExclFinite_complete
#check @G08D.checkWitness_example
#print axioms G08D.checkWitness_example
#check @G08D.checkExclFinite_example
#print axioms G08D.checkExclFinite_example
#check @G08D.accelNorm_of_geodesic
#print axioms G08D.accelNorm_of_geodesic
#check @G08D.accel_lower_bound_excludes
#print axioms G08D.accel_lower_bound_excludes
#check @G08D.accel_lower_bound_excludes_geodesic
#print axioms G08D.accel_lower_bound_excludes_geodesic
#check @G08D.geodesicDual_sound
#print axioms G08D.geodesicDual_sound
#check @G08D.solver_claim_not_proof
#print axioms G08D.solver_claim_not_proof
#check @G08D.inner_samples_not_exclusion
#print axioms G08D.inner_samples_not_exclusion
#check @G08D.zero_excluded_no_positive_bound
#print axioms G08D.zero_excluded_no_positive_bound
#check @G08D.measurableSet_confGraph
#print axioms G08D.measurableSet_confGraph
#check @G08D.measurableSet_nullGraph
#print axioms G08D.measurableSet_nullGraph
#check @G08D.measurableSet_coverage
#print axioms G08D.measurableSet_coverage
#check @G08D.measurableSet_noncoverage
#print axioms G08D.measurableSet_noncoverage
#check @G08D.measurableSet_nonempty_countable
#print axioms G08D.measurableSet_nonempty_countable
#check @G08D.measurableSet_nonempty_compact
#print axioms G08D.measurableSet_nonempty_compact
#check @G08D.measurableSet_nonempty_sigmaCompact
#print axioms G08D.measurableSet_nonempty_sigmaCompact
#check @G08D.measurableSet_null_nonempty_sigmaCompact
#print axioms G08D.measurableSet_null_nonempty_sigmaCompact
#check @G08D.measurableSet_reports
#print axioms G08D.measurableSet_reports
#check @G08D.projection_not_auto_measurable
#print axioms G08D.projection_not_auto_measurable
#check @G08D.general_inversion_coverage
#print axioms G08D.general_inversion_coverage
#check @G08D.general_inversion_projection
#print axioms G08D.general_inversion_projection
#check @G08D.gaussian_reports_measurable
#print axioms G08D.gaussian_reports_measurable
#check @G08D.gaussian_noncoverage_eq
#print axioms G08D.gaussian_noncoverage_eq
#check @G08D.gaussian_size_control
#print axioms G08D.gaussian_size_control
#check @G08D.gaussian_semantic_size
#print axioms G08D.gaussian_semantic_size
#check @G08D.gaussian_incompatible_size
#print axioms G08D.gaussian_incompatible_size
#check @G08D.gaussian_sourceDecision_size
#print axioms G08D.gaussian_sourceDecision_size
#check @G08D.gaussian_error_envelope
#print axioms G08D.gaussian_error_envelope
#check @G08D.gaussian_size_rank_zero
#print axioms G08D.gaussian_size_rank_zero
#check @G08D.gaussian_projection_coverage
#print axioms G08D.gaussian_projection_coverage
#check @G08D.gaussian_robust_union_coverage
#print axioms G08D.gaussian_robust_union_coverage
#check @G08D.gaussian_robust_union_delta
#print axioms G08D.gaussian_robust_union_delta

-- ## definitions
#print axioms G08D.certCongr
#print axioms G08D.WitnessCert.toCert
#print axioms G08D.ExclCert.toCert
#print axioms G08D.OptReport.toCert
#print axioms G08D.sourceDecision
#print axioms G08D.checkWitness
#print axioms G08D.checkExclFinite
#print axioms G08D.accelNorm
#print axioms G08D.geodesicDualExcl
#print axioms G08D.ccMeasurableSpace

-- ## executable exact-rational checkers (compiled code, not used as proofs)
#eval G08D.checkWitness (fun _ : Fin 3 => true) (fun i => ((i : ℕ) : ℚ)) 1 1
#eval G08D.checkWitness (fun _ : Fin 3 => true) (fun i => ((i : ℕ) : ℚ)) 1 2
#eval G08D.checkExclFinite (fun i : Fin 3 => decide (1 ≤ (i : ℕ))) (fun i => ((i : ℕ) : ℚ)) (1 / 2)
#eval G08D.checkExclFinite (fun _ : Fin 3 => true) (fun i => ((i : ℕ) : ℚ)) (1 / 2)

-- ## non-vacuity: the hypotheses of gaussian_size_control are jointly satisfiable (ν = 1)
theorem audit_gaussian_size_nonvacuous : True := by
  have hX : G08AWhitening.IsMoorePenrose ((1 : Matrix (Fin 1) (Fin 1) ℝ) * 0) 0 := by
    simp [G08AWhitening.IsMoorePenrose]
  have hν : 0 < 1 - (0 : Matrix (Fin 1) (Fin 1) ℝ).rank := by simp [Matrix.rank_zero]
  have _h := G08D.gaussian_size_control (Set.univ : Set (EuclideanSpace ℝ (Fin 1)))
    (fun θ => θ) 0 (Set.mem_univ _) 1 1 0 0 Matrix.PosDef.one ⟨isUnit_one, by simp⟩ hX 0
    (α := 1 / 2) (by norm_num) (by norm_num) hν id (Set.univ : Set (EuclideanSpace ℝ (Fin 1)))
    (Set.mem_univ _) (fun _ => Cert.uncertified) (fun _ => Cert.uncertified)
  trivial
#print axioms audit_gaussian_size_nonvacuous
