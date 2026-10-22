import Mathlib
import FiniteGram
open Matrix
#check @Matrix.toEuclideanLin_apply
#check @LinearIsometryEquiv.inner_map_map
#check @PiLp.inner_apply
#check @Matrix.conjTranspose_eq_transpose_of_trivial
#check @Matrix.isSymmetric_toEuclideanLin_iff
#check @Matrix.mulVec_mulVec
#check @Matrix.toLin'_apply
#check @CAS11C02.spectralPinvLin_apply
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
    {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (v : E) (i : Fin (Module.finrank ℝ E)) :
    ((hT.eigenvectorBasis rfl).repr (CAS11C02.spectralPinvLin hT v)).ofLp i
      = ((hT.eigenvalues rfl i))⁻¹ * ((hT.eigenvectorBasis rfl).repr v).ofLp i := by
  rw [CAS11C02.spectralPinvLin_apply]
  simp [CAS11C02.spectralPinvVec]
