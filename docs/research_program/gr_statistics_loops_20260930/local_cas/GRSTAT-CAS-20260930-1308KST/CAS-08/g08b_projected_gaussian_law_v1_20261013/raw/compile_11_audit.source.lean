import G08BGaussianLaw

/-! Axiom audit for G08-B. Accept only propext, Classical.choice, Quot.sound. -/

#print G08BGaussianLaw.chiSq
#print G08BGaussianLaw.lowerQuantile
#print G08BGaussianLaw.threshold
#print G08BGaussianLaw.Qstat
#print G08BGaussianLaw.confSet

#check @G08BGaussianLaw.map_affine_multivariateGaussian
#print axioms G08BGaussianLaw.map_affine_multivariateGaussian
#check @G08BGaussianLaw.projected_residual_law
#print axioms G08BGaussianLaw.projected_residual_law
#check @G08BGaussianLaw.projected_residual_law_rv
#print axioms G08BGaussianLaw.projected_residual_law_rv
#check @G08BGaussianLaw.stdGaussian_map_orthonormal
#print axioms G08BGaussianLaw.stdGaussian_map_orthonormal
#check @G08BGaussianLaw.projector_frame
#print axioms G08BGaussianLaw.projector_frame
#check @G08BGaussianLaw.projected_coordinates_rv
#print axioms G08BGaussianLaw.projected_coordinates_rv
#check @G08BGaussianLaw.chiSq_law
#print axioms G08BGaussianLaw.chiSq_law
#check @G08BGaussianLaw.chiSq_law_rv
#print axioms G08BGaussianLaw.chiSq_law_rv
#check @G08BGaussianLaw.chiSq_zero
#print axioms G08BGaussianLaw.chiSq_zero
#check @G08BGaussianLaw.chiSq_law_rank_zero
#print axioms G08BGaussianLaw.chiSq_law_rank_zero
#check @G08BGaussianLaw.isProbabilityMeasure_chiSq
#print axioms G08BGaussianLaw.isProbabilityMeasure_chiSq
#check @G08BGaussianLaw.chiSq_Iio_zero
#print axioms G08BGaussianLaw.chiSq_Iio_zero
#check @G08BGaussianLaw.chiSq_singleton
#print axioms G08BGaussianLaw.chiSq_singleton
#check @G08BGaussianLaw.cdf_lowerQuantile
#print axioms G08BGaussianLaw.cdf_lowerQuantile
#check @G08BGaussianLaw.cdf_threshold
#print axioms G08BGaussianLaw.cdf_threshold
#check @G08BGaussianLaw.lowerQuantile_chiSq_zero
#print axioms G08BGaussianLaw.lowerQuantile_chiSq_zero
#check @G08BGaussianLaw.coverage
#print axioms G08BGaussianLaw.coverage
#check @G08BGaussianLaw.coverage_rv
#print axioms G08BGaussianLaw.coverage_rv
#check @G08BGaussianLaw.confSet_rank_zero
#print axioms G08BGaussianLaw.confSet_rank_zero
#check @G08BGaussianLaw.coverage_rank_zero
#print axioms G08BGaussianLaw.coverage_rank_zero
#check @G08BGaussianLaw.coverage_strict
#print axioms G08BGaussianLaw.coverage_strict
#check @G08BGaussianLaw.strict_rank_zero_fails
#print axioms G08BGaussianLaw.strict_rank_zero_fails
#check @G08BGaussianLaw.nonvacuous_nu_pos
#print axioms G08BGaussianLaw.nonvacuous_nu_pos
#check @G08BGaussianLaw.nonvacuous_nu_zero
#print axioms G08BGaussianLaw.nonvacuous_nu_zero
#check @G08BGaussianLaw.chiSq_one_ne_zero
#print axioms G08BGaussianLaw.chiSq_one_ne_zero
