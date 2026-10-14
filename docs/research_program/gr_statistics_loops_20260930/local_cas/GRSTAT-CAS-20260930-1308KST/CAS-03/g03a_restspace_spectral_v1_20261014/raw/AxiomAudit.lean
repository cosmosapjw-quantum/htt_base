import G03ARestspace

/-! Axiom audit for G03-A: #check and #print axioms for every theorem in namespace G03A,
plus the data definitions whose fields carry proofs. -/

#check @G03A.ofV_zero
#print axioms G03A.ofV_zero
#check @G03A.ofV_succ
#print axioms G03A.ofV_succ
#check @G03A.ofV_injective
#print axioms G03A.ofV_injective
#check @G03A.ofV_smulV
#print axioms G03A.ofV_smulV
#check @G03A.toMatrix_symm
#print axioms G03A.toMatrix_symm
#check @G03A.toMixed_selfAdjoint
#print axioms G03A.toMixed_selfAdjoint
#check @G03A.toMixed_matVec
#print axioms G03A.toMixed_matVec
#check @G03A.ofV_mass
#print axioms G03A.ofV_mass
#check @G03A.timelike_time_ne
#print axioms G03A.timelike_time_ne
#check @G03A.A2_normalize
#print axioms G03A.A2_normalize
#check @G03A.A1_premise_iff_mixed
#print axioms G03A.A1_premise_iff_mixed
#check @G03A.A1_premise_iff_geodesic
#print axioms G03A.A1_premise_iff_geodesic
#check @G03A.A3_rot_no_timelike
#print axioms G03A.A3_rot_no_timelike
#check @G03A.A3_null_no_timelike
#print axioms G03A.A3_null_no_timelike
#check @G03A.A3_selfadjoint_insufficient
#print axioms G03A.A3_selfadjoint_insufficient
#check @G03A.B1_rest_posdef
#print axioms G03A.B1_rest_posdef
#check @G03A.mem_restSub
#print axioms G03A.mem_restSub
#check @G03A.RestSpace.val_add
#print axioms G03A.RestSpace.val_add
#check @G03A.RestSpace.val_smul
#print axioms G03A.RestSpace.val_smul
#check @G03A.RestSpace.val_zero
#print axioms G03A.RestSpace.val_zero
#check @G03A.RestSpace.mk_val
#print axioms G03A.RestSpace.mk_val
#check @G03A.B2_val_injective
#print axioms G03A.B2_val_injective
#check @G03A.B2_val_mem
#print axioms G03A.B2_val_mem
#check @G03A.RestSpace.val_eq_zero
#print axioms G03A.RestSpace.val_eq_zero
#check @G03A.inner_def'
#print axioms G03A.inner_def'
#check @G03A.B2_inner_eq
#print axioms G03A.B2_inner_eq
#check @G03A.B2_posdef
#print axioms G03A.B2_posdef
#check @G03A.B2_finrank
#print axioms G03A.B2_finrank
#check @G03A.timelike_not_orth
#print axioms G03A.timelike_not_orth
#check @G03A.A2_timelike_eigenvalue_unique
#print axioms G03A.A2_timelike_eigenvalue_unique
#check @G03A.restOp_mem
#print axioms G03A.restOp_mem
#check @G03A.C0_restOp_val
#print axioms G03A.C0_restOp_val
#check @G03A.C1_restOp_symmetric
#print axioms G03A.C1_restOp_symmetric
#check @G03A.C1_rest_spectral
#print axioms G03A.C1_rest_spectral
#check @G03A.C1_restEigenbasis_G04A
#print axioms G03A.C1_restEigenbasis_G04A
#check @G03A.mem_restEig_iff
#print axioms G03A.mem_restEig_iff
#check @G03A.mem_eig_iff
#print axioms G03A.mem_eig_iff
#check @G03A.C2_eigenspace_split
#print axioms G03A.C2_eigenspace_split
#check @G03A.splitMap_bijective
#print axioms G03A.splitMap_bijective
#check @G03A.C2_finrank
#print axioms G03A.C2_finrank
#check @G03A.C3_isolation_iff
#print axioms G03A.C3_isolation_iff
#check @G03A.C4_C01_rest_eigen
#print axioms G03A.C4_C01_rest_eigen
#check @G03A.ofW_add
#print axioms G03A.ofW_add
#check @G03A.ofW_smul
#print axioms G03A.ofW_smul
#check @G03A.ofW_injective
#print axioms G03A.ofW_injective
#check @G03A.e0T_orth
#print axioms G03A.e0T_orth
#check @G03A.mem_kerDSub
#print axioms G03A.mem_kerDSub
#check @G03A.kerD_iff_mixed
#print axioms G03A.kerD_iff_mixed
#check @G03A.kerD_iff_eig
#print axioms G03A.kerD_iff_eig
#check @G03A.kerMap_bijective
#print axioms G03A.kerMap_bijective
#check @G03A.C4_C01_kernel_bridge
#print axioms G03A.C4_C01_kernel_bridge
#check @G03A.C4_C01_fibre
#print axioms G03A.C4_C01_fibre
#check @G03A.C5_C01_isolation_iff_unique_velocity
#print axioms G03A.C5_C01_isolation_iff_unique_velocity
#check @G03A.C6_C01_controls
#print axioms G03A.C6_C01_controls
#check @G03A.borderedE_contDiffAt
#print axioms G03A.borderedE_contDiffAt
#check @G03A.borderedE_fderiv_inr
#print axioms G03A.borderedE_fderiv_inr
#check @G03A.D1_branch
#print axioms G03A.D1_branch
#check @G03A.D2_branch_vec4_via_G04A
#print axioms G03A.D2_branch_vec4_via_G04A
#check @G03A.D3_branch_simple
#print axioms G03A.D3_branch_simple
#check @G03A.e0v_apply
#print axioms G03A.e0v_apply
#check @G03A.lorentzDot_e0v
#print axioms G03A.lorentzDot_e0v
#check @G03A.Srot_matVec
#print axioms G03A.Srot_matVec
#check @G03A.Scol_matVec
#print axioms G03A.Scol_matVec
#check @G03A.axis_limit
#print axioms G03A.axis_limit
#check @G03A.E1_isolation_needed
#print axioms G03A.E1_isolation_needed
#check @G03A.Scol_rest_identity
#print axioms G03A.Scol_rest_identity
#check @G03A.E2_collision_branch_exists
#print axioms G03A.E2_collision_branch_exists
#check @G03A.E3_no_continuous_rest_eigenvector
#print axioms G03A.E3_no_continuous_rest_eigenvector
#print axioms G03A.DactL
#print axioms G03A.restCore
#print axioms G03A.restOp
#print axioms G03A.restEigenbasis
#print axioms G03A.restEigenvalues
#print axioms G03A.e0T
#print axioms G03A.splitMap
#print axioms G03A.kerMap
