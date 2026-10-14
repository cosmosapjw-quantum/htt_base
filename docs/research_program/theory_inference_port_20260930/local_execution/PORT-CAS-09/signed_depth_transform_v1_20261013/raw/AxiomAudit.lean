import Mathlib
import P09SignedDepth

#check @P09SignedDepth.Idx
#check @P09SignedDepth.CIdx
#check @P09SignedDepth.Transport
#check @P09SignedDepth.contrast
#check @P09SignedDepth.contrastLin
#check @P09SignedDepth.H
#check @P09SignedDepth.anchored
#check @P09SignedDepth.anchored_zero
#check @P09SignedDepth.anchored_succ
#check @P09SignedDepth.anchored_add
#check @P09SignedDepth.anchored_smul
#check @P09SignedDepth.anchoredLin
#check @P09SignedDepth.Tmat
#check @P09SignedDepth.restoreBlock
#check @P09SignedDepth.restore
#check @P09SignedDepth.restoreBlock_zero
#check @P09SignedDepth.restoreBlock_succ
#check @P09SignedDepth.blockDiagPart
#check @P09SignedDepth.H_mulVec
#check @P09SignedDepth.H_apply'
#check @P09SignedDepth.H_apply_succ
#check @P09SignedDepth.H_apply_castSucc
#check @P09SignedDepth.H_apply_other
#check @P09SignedDepth.Tmat_mulVec
#check @P09SignedDepth.Tmat_apply'
#check @P09SignedDepth.Tmat_apply_zero
#check @P09SignedDepth.Tmat_apply_succ
#check @P09SignedDepth.Tmat_apply_diag
#check @P09SignedDepth.Tmat_apply_upper
#check @P09SignedDepth.Tmat_blockTriangular
#check @P09SignedDepth.anchored_depth_zero
#check @P09SignedDepth.Tmat_depth_zero
#check @P09SignedDepth.anchored_restore
#check @P09SignedDepth.restoreBlock_anchored
#check @P09SignedDepth.restore_anchored
#check @P09SignedDepth.restore_succ
#check @P09SignedDepth.anchored_bijective
#check @P09SignedDepth.Tequiv
#check @P09SignedDepth.Rmat
#check @P09SignedDepth.Tmat_mul_Rmat
#check @P09SignedDepth.Rmat_mul_Tmat
#check @P09SignedDepth.bijective_depth_zero
#check @P09SignedDepth.Tmat_det
#check @P09SignedDepth.meanVec
#check @P09SignedDepth.covMat
#check @P09SignedDepth.mean_mulVec
#check @P09SignedDepth.covMat_mulVec
#check @P09SignedDepth.contrast_moments
#check @P09SignedDepth.anchored_moments
#check @P09SignedDepth.HCHt_apply
#check @P09SignedDepth.law_mulVec
#check @P09SignedDepth.contrast_law
#check @P09SignedDepth.contrast_law_congr
#check @P09SignedDepth.contrast_law_marginal_of_anchored
#check @P09SignedDepth.n₁
#check @P09SignedDepth.K₁
#check @P09SignedDepth.ones
#check @P09SignedDepth.ones_contrast_cov_zero
#check @P09SignedDepth.blockDiag_contrast_cov_00
#check @P09SignedDepth.blockDiag_contrast_cov_01
#check @P09SignedDepth.dropping_cross_blocks_changes_cov
#check @P09SignedDepth.copy_covMat
#check @P09SignedDepth.copy_contrast_cov_zero
#check @P09SignedDepth.copy_covMat_var
#check @P09SignedDepth.copy_blockDiag_contrast_cov_00

#print axioms P09SignedDepth.anchored_zero
#print axioms P09SignedDepth.anchored_succ
#print axioms P09SignedDepth.anchored_add
#print axioms P09SignedDepth.anchored_smul
#print axioms P09SignedDepth.restoreBlock_zero
#print axioms P09SignedDepth.restoreBlock_succ
#print axioms P09SignedDepth.H_mulVec
#print axioms P09SignedDepth.H_apply'
#print axioms P09SignedDepth.H_apply_succ
#print axioms P09SignedDepth.H_apply_castSucc
#print axioms P09SignedDepth.H_apply_other
#print axioms P09SignedDepth.Tmat_mulVec
#print axioms P09SignedDepth.Tmat_apply'
#print axioms P09SignedDepth.Tmat_apply_zero
#print axioms P09SignedDepth.Tmat_apply_succ
#print axioms P09SignedDepth.Tmat_apply_diag
#print axioms P09SignedDepth.Tmat_apply_upper
#print axioms P09SignedDepth.Tmat_blockTriangular
#print axioms P09SignedDepth.anchored_depth_zero
#print axioms P09SignedDepth.Tmat_depth_zero
#print axioms P09SignedDepth.anchored_restore
#print axioms P09SignedDepth.restoreBlock_anchored
#print axioms P09SignedDepth.restore_anchored
#print axioms P09SignedDepth.restore_succ
#print axioms P09SignedDepth.anchored_bijective
#print axioms P09SignedDepth.Tmat_mul_Rmat
#print axioms P09SignedDepth.Rmat_mul_Tmat
#print axioms P09SignedDepth.bijective_depth_zero
#print axioms P09SignedDepth.Tmat_det
#print axioms P09SignedDepth.mean_mulVec
#print axioms P09SignedDepth.covMat_mulVec
#print axioms P09SignedDepth.contrast_moments
#print axioms P09SignedDepth.anchored_moments
#print axioms P09SignedDepth.HCHt_apply
#print axioms P09SignedDepth.law_mulVec
#print axioms P09SignedDepth.contrast_law
#print axioms P09SignedDepth.contrast_law_congr
#print axioms P09SignedDepth.contrast_law_marginal_of_anchored
#print axioms P09SignedDepth.ones_contrast_cov_zero
#print axioms P09SignedDepth.blockDiag_contrast_cov_00
#print axioms P09SignedDepth.blockDiag_contrast_cov_01
#print axioms P09SignedDepth.dropping_cross_blocks_changes_cov
#print axioms P09SignedDepth.copy_covMat
#print axioms P09SignedDepth.copy_contrast_cov_zero
#print axioms P09SignedDepth.copy_covMat_var
#print axioms P09SignedDepth.copy_blockDiag_contrast_cov_00
