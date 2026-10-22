import Mathlib
import G09ADefinitions
import G09BRankDesign

/-! G09-B axiom audit: #check and #print axioms for every public theorem of G09BRankDesign. -/

#check @G09B.dim_sup_add_dim_inf
#print axioms G09B.dim_sup_add_dim_inf
#check @G09B.dim_inf_le_left
#print axioms G09B.dim_inf_le_left
#check @G09B.dim_inf_le_right
#print axioms G09B.dim_inf_le_right
#check @G09B.dim_sup_eq_sub
#print axioms G09B.dim_sup_eq_sub
#check @G09B.dim_sup_eq_sub_int
#print axioms G09B.dim_sup_eq_sub_int
#check @G09B.range_eq_of_transfer
#print axioms G09B.range_eq_of_transfer
#check @G09B.range_fromCols
#print axioms G09B.range_fromCols
#check @G09B.rank_fromCols_add
#print axioms G09B.rank_fromCols_add
#check @G09B.rank_fromCols_eq_sub
#print axioms G09B.rank_fromCols_eq_sub
#check @G09B.idecode_icoord
#print axioms G09B.idecode_icoord
#check @G09B.icoord_idecode
#print axioms G09B.icoord_idecode
#check @G09B.hdecode_hcoord
#print axioms G09B.hdecode_hcoord
#check @G09B.hcoord_hdecode
#print axioms G09B.hcoord_hdecode
#check @G09B.E9mat_first_cols
#print axioms G09B.E9mat_first_cols
#check @G09B.E4mat_mulVec
#print axioms G09B.E4mat_mulVec
#check @G09B.E9mat_mulVec
#print axioms G09B.E9mat_mulVec
#check @G09B.E4_eq_mulVec
#print axioms G09B.E4_eq_mulVec
#check @G09B.E9_eq_mulVec
#print axioms G09B.E9_eq_mulVec
#check @G09B.Dmat_mulVec
#print axioms G09B.Dmat_mulVec
#check @G09B.DE9mat_mulVec
#print axioms G09B.DE9mat_mulVec
#check @G09B.Xmat_mulVec
#print axioms G09B.Xmat_mulVec
#check @G09B.Xmap_eq_mulVec
#print axioms G09B.Xmap_eq_mulVec
#check @G09B.range_E4mat
#print axioms G09B.range_E4mat
#check @G09B.range_E9mat
#print axioms G09B.range_E9mat
#check @G09B.range_DE9mat
#print axioms G09B.range_DE9mat
#check @G09B.range_Xmat
#print axioms G09B.range_Xmat
#check @G09B.range_Xmap_eq_sup
#print axioms G09B.range_Xmap_eq_sup
#check @G09B.range_Xmat_eq_sup
#print axioms G09B.range_Xmat_eq_sup
#check @G09B.rank_E4mat
#print axioms G09B.rank_E4mat
#check @G09B.rank_E9mat
#print axioms G09B.rank_E9mat
#check @G09B.rank_Xmat
#print axioms G09B.rank_Xmat
#check @G09B.rank_DE9mat
#print axioms G09B.rank_DE9mat
#check @G09B.Xmat_rank_concat
#print axioms G09B.Xmat_rank_concat
#check @G09B.Xmat_rank_eq_sub
#print axioms G09B.Xmat_rank_eq_sub
#check @G09B.E9_injective_iff_det
#print axioms G09B.E9_injective_iff_det
#check @G09B.E4_injective_iff_det
#print axioms G09B.E4_injective_iff_det
#check @G09B.E9_injective_iff_rank
#print axioms G09B.E9_injective_iff_rank
#check @G09B.E4_injective_iff_rank
#print axioms G09B.E4_injective_iff_rank
#check @G09B.E9_basis_change_det
#print axioms G09B.E9_basis_change_det
#check @G09B.E9_basis_change_rank
#print axioms G09B.E9_basis_change_rank
#check @G09B.Xmap_apply
#print axioms G09B.Xmap_apply
#check @G09B.two_radius_ker_iff
#print axioms G09B.two_radius_ker_iff
#check @G09B.two_radius_ker_eq_bot_of_det
#print axioms G09B.two_radius_ker_eq_bot_of_det
#check @G09B.two_radius_Xmat_mulVec_eq_zero
#print axioms G09B.two_radius_Xmat_mulVec_eq_zero
#check @G09B.two_radius_Xmat_rank13_of_det
#print axioms G09B.two_radius_Xmat_rank13_of_det
#check @G09B.two_radius_Xmat_rank13_of_ranks
#print axioms G09B.two_radius_Xmat_rank13_of_ranks
#check @G09B.two_radius_Xmat_rank_lt13_of_det4_eq_zero
#print axioms G09B.two_radius_Xmat_rank_lt13_of_det4_eq_zero
#check @G09B.two_radius_Xmat_equal_radius_le9
#print axioms G09B.two_radius_Xmat_equal_radius_le9
#check @G09B.witness_E4block
#print axioms G09B.witness_E4block
#check @G09B.witness_det4
#print axioms G09B.witness_det4
#check @G09B.witness_det9_ne_zero
#print axioms G09B.witness_det9_ne_zero
#check @G09B.witness_Xmat_rank13
#print axioms G09B.witness_Xmat_rank13
#check @G09B.witness_equal_radius_le9
#print axioms G09B.witness_equal_radius_le9
#check @G09B.witness_const_radius_dims
#print axioms G09B.witness_const_radius_dims
