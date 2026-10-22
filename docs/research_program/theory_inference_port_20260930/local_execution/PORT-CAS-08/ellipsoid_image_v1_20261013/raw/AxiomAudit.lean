import Mathlib
import G08AWhitening
import P08EllipsoidFiber
import P08EllipsoidImage

#print P08EllipsoidImage.Ell
#print P08EllipsoidImage.FibreImage
#print P08EllipsoidImage.IsKerONB
#print P08EllipsoidImage.EllImage
#check @P08EllipsoidImage.Ell
#check @P08EllipsoidImage.FibreImage
#check @P08EllipsoidImage.IsKerONB
#check @P08EllipsoidImage.EllImage
#check @P08EllipsoidImage.fibreImage_eq_latent
#check @P08EllipsoidImage.dot_mulVec_ONB
#check @P08EllipsoidImage.kernel_ball_param
#check @P08EllipsoidImage.fibreImage_eq_of_le
#check @P08EllipsoidImage.fibreImage_eq
#check @P08EllipsoidImage.basis_invariance
#check @P08EllipsoidImage.isKerONB_mul_orthogonal
#check @P08EllipsoidImage.ellImage_mul_orthogonal
#check @P08EllipsoidImage.ellImage_zero
#check @P08EllipsoidImage.boundary_eq_one
#check @P08EllipsoidImage.boundary_consistent
#check @P08EllipsoidImage.boundary_gt_one
#check @P08EllipsoidImage.incompatible_empty
#check @P08EllipsoidImage.kerE
#check @P08EllipsoidImage.mem_kerE
#check @P08EllipsoidImage.kerN
#check @P08EllipsoidImage.kerN_mulVec
#check @P08EllipsoidImage.kerN_orthonormal
#check @P08EllipsoidImage.kerN_range
#check @P08EllipsoidImage.exists_kerONB
#check @P08EllipsoidImage.fibreImage_exists_param
#check @P08EllipsoidImage.dot_sq_le
#check @P08EllipsoidImage.support_function
#check @P08EllipsoidImage.eta_squared_gauge
#check @P08EllipsoidImage.fibreImage_nonempty_iff
#print axioms P08EllipsoidImage.Ell
#print axioms P08EllipsoidImage.FibreImage
#print axioms P08EllipsoidImage.IsKerONB
#print axioms P08EllipsoidImage.EllImage
#print axioms P08EllipsoidImage.fibreImage_eq_latent
#print axioms P08EllipsoidImage.dot_mulVec_ONB
#print axioms P08EllipsoidImage.kernel_ball_param
#print axioms P08EllipsoidImage.fibreImage_eq_of_le
#print axioms P08EllipsoidImage.fibreImage_eq
#print axioms P08EllipsoidImage.basis_invariance
#print axioms P08EllipsoidImage.isKerONB_mul_orthogonal
#print axioms P08EllipsoidImage.ellImage_mul_orthogonal
#print axioms P08EllipsoidImage.ellImage_zero
#print axioms P08EllipsoidImage.boundary_eq_one
#print axioms P08EllipsoidImage.boundary_consistent
#print axioms P08EllipsoidImage.boundary_gt_one
#print axioms P08EllipsoidImage.incompatible_empty
#print axioms P08EllipsoidImage.kerE
#print axioms P08EllipsoidImage.mem_kerE
#print axioms P08EllipsoidImage.kerN
#print axioms P08EllipsoidImage.kerN_mulVec
#print axioms P08EllipsoidImage.kerN_orthonormal
#print axioms P08EllipsoidImage.kerN_range
#print axioms P08EllipsoidImage.exists_kerONB
#print axioms P08EllipsoidImage.fibreImage_exists_param
#print axioms P08EllipsoidImage.dot_sq_le
#print axioms P08EllipsoidImage.support_function
#print axioms P08EllipsoidImage.eta_squared_gauge
#print axioms P08EllipsoidImage.fibreImage_nonempty_iff
