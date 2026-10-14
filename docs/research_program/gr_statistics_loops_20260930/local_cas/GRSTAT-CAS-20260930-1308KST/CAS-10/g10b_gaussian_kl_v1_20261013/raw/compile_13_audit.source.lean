import G10BGaussianKL

/-! Axiom audit for G10-B. Accept only propext, Classical.choice, Quot.sound. -/

#check @G10BGaussianKL.klDiv_map_of_measurableEmbedding
#check @G10BGaussianKL.klDiv_prod
#check @G10BGaussianKL.klDiv_pi_fin
#check @G10BGaussianKL.klDiv_pi
#check @G10BGaussianKL.klDiv_gaussianReal_same_var
#check @G10BGaussianKL.coordVar_coe
#check @G10BGaussianKL.measurable_toLp
#check @G10BGaussianKL.measurable_blockMap
#check @G10BGaussianKL.measurable_powers
#check @G10BGaussianKL.sum_blockMap_mul
#check @G10BGaussianKL.sum_sq_blockMap
#check @G10BGaussianKL.obsLaw_map_blockMap
#check @G10BGaussianKL.blockMap_zero
#check @G10BGaussianKL.obsLaw_zero_map_blockMap
#check @G10BGaussianKL.powers_blockMap
#check @G10BGaussianKL.compressed_law_eq
#check @G10BGaussianKL.powersOnly_integral_eq
#check @G10BGaussianKL.powersOnly_power_le_size
#check @G10BGaussianKL.klDiv_coordLaw
#check @G10BGaussianKL.klDiv_obsLaw
#check @G10BGaussianKL.obsLaw_toLp_eq_multivariateGaussian
#check @G10BGaussianKL.obsLaw_eq_iff
#check @G10BGaussianKL.meanOf_0
#check @G10BGaussianKL.meanOf_1
#check @G10BGaussianKL.meanOf_2
#check @G10BGaussianKL.meanOf_3
#check @G10BGaussianKL.meanOf_4
#check @G10BGaussianKL.sum_Obs
#check @G10BGaussianKL.powers_apply
#check @G10BGaussianKL.rotP_orthogonal
#check @G10BGaussianKL.blockMap_rotP_first
#check @G10BGaussianKL.compressed_laws_equal
#check @G10BGaussianKL.powersOnly_tests_agree
#check @G10BGaussianKL.full_kl_eq_C03
#check @G10BGaussianKL.full_kl_eq
#check @G10BGaussianKL.full_kl_pos
#check @G10BGaussianKL.full_kl_ne_top
#check @G10BGaussianKL.ofMean_first_pIdx
#check @G10BGaussianKL.ofMean_second_pIdx
#check @G10BGaussianKL.full_laws_ne
#check @G10BGaussianKL.full_kl_singular_branch
#check @G10BGaussianKL.slope_vectors_agree
#check @G10BGaussianKL.powers_explicit_first
#check @G10BGaussianKL.powers_explicit_second
#check @G10BGaussianKL.powers_explicit_matches_C01
#check @G10BGaussianKL.tDiag_eq_coord_E1
#check @G10BGaussianKL.E1_symm
#check @G10BGaussianKL.E1_trace
#check @G10BGaussianKL.E1_frobenius
#check @G10BGaussianKL.blockMap_rotP_pIdx1
#check @G10BGaussianKL.anisotropic_rotation_changes_law

#print axioms G10BGaussianKL.klDiv_map_of_measurableEmbedding
#print axioms G10BGaussianKL.klDiv_prod
#print axioms G10BGaussianKL.klDiv_pi_fin
#print axioms G10BGaussianKL.klDiv_pi
#print axioms G10BGaussianKL.klDiv_gaussianReal_same_var
#print axioms G10BGaussianKL.coordVar_coe
#print axioms G10BGaussianKL.measurable_toLp
#print axioms G10BGaussianKL.measurable_blockMap
#print axioms G10BGaussianKL.measurable_powers
#print axioms G10BGaussianKL.sum_blockMap_mul
#print axioms G10BGaussianKL.sum_sq_blockMap
#print axioms G10BGaussianKL.obsLaw_map_blockMap
#print axioms G10BGaussianKL.blockMap_zero
#print axioms G10BGaussianKL.obsLaw_zero_map_blockMap
#print axioms G10BGaussianKL.powers_blockMap
#print axioms G10BGaussianKL.compressed_law_eq
#print axioms G10BGaussianKL.powersOnly_integral_eq
#print axioms G10BGaussianKL.powersOnly_power_le_size
#print axioms G10BGaussianKL.klDiv_coordLaw
#print axioms G10BGaussianKL.klDiv_obsLaw
#print axioms G10BGaussianKL.obsLaw_toLp_eq_multivariateGaussian
#print axioms G10BGaussianKL.obsLaw_eq_iff
#print axioms G10BGaussianKL.meanOf_0
#print axioms G10BGaussianKL.meanOf_1
#print axioms G10BGaussianKL.meanOf_2
#print axioms G10BGaussianKL.meanOf_3
#print axioms G10BGaussianKL.meanOf_4
#print axioms G10BGaussianKL.sum_Obs
#print axioms G10BGaussianKL.powers_apply
#print axioms G10BGaussianKL.rotP_orthogonal
#print axioms G10BGaussianKL.blockMap_rotP_first
#print axioms G10BGaussianKL.compressed_laws_equal
#print axioms G10BGaussianKL.powersOnly_tests_agree
#print axioms G10BGaussianKL.full_kl_eq_C03
#print axioms G10BGaussianKL.full_kl_eq
#print axioms G10BGaussianKL.full_kl_pos
#print axioms G10BGaussianKL.full_kl_ne_top
#print axioms G10BGaussianKL.ofMean_first_pIdx
#print axioms G10BGaussianKL.ofMean_second_pIdx
#print axioms G10BGaussianKL.full_laws_ne
#print axioms G10BGaussianKL.full_kl_singular_branch
#print axioms G10BGaussianKL.slope_vectors_agree
#print axioms G10BGaussianKL.powers_explicit_first
#print axioms G10BGaussianKL.powers_explicit_second
#print axioms G10BGaussianKL.powers_explicit_matches_C01
#print axioms G10BGaussianKL.tDiag_eq_coord_E1
#print axioms G10BGaussianKL.E1_symm
#print axioms G10BGaussianKL.E1_trace
#print axioms G10BGaussianKL.E1_frobenius
#print axioms G10BGaussianKL.blockMap_rotP_pIdx1
#print axioms G10BGaussianKL.anisotropic_rotation_changes_law
