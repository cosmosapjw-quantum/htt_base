import Mathlib
import C01
import G01AJacobiVertex
-- API probe only (no target proof).
#check @HasFDerivAt.smul
#check @HasFDerivAt.exp
#check @HasFDerivAt.const_mul
#check @fderiv_const_smul_field
#check @deriv_comp_mul_left
#check @deriv_const_smul_field
#check @Matrix.inv_smul'
#check @Matrix.smul_of
#check @Matrix.nonsing_inv_mul
#check @hasFDerivAt_apply
#check @G01A.rescale
#check @G01A.jacobi_unique
#check @G01A.rescale_area_distance
#check @G01A.eta_rescale_invariant
#check @CAS07M05.matrixOf
#check @CAS17C01.betaSq
#check @CAS17C01.relativeSpatial
example (n : ℕ) (f : (Fin n → ℝ) → Fin n → Fin n → ℝ) (x : Fin n → ℝ) (b : Fin n) :
    (Fin n → Fin n → ℝ) := fderiv ℝ f x (Pi.single b 1)
