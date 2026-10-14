import Mathlib

/-!
The canonical spectral witness for a real symmetric 3×3 matrix.
This successor consumes mathlib's ordered spectral theorem and does not alter
the earlier CAS15 Frobenius, least-squares, or matching proofs.
-/

noncomputable section
namespace CAS15SpectralWitness

abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ

private def hermitian (A : M3) (hA : A.IsSymm) : A.IsHermitian :=
  Matrix.isHermitian_iff_isSymm.mpr hA

def eigenQ (A : M3) (hA : A.IsSymm) : M3 :=
  (hermitian A hA).eigenvectorUnitary

def eigenLamb (A : M3) (hA : A.IsSymm) : Fin 3 → ℝ :=
  (hermitian A hA).eigenvalues

theorem eigenQ_orthogonal_left (A : M3) (hA : A.IsSymm) :
    (eigenQ A hA).transpose * eigenQ A hA = 1 := by
  change (star ((hermitian A hA).eigenvectorUnitary : M3)) *
    ((hermitian A hA).eigenvectorUnitary : M3) = 1
  exact Matrix.UnitaryGroup.star_mul_self _

theorem eigenQ_orthogonal_right (A : M3) (hA : A.IsSymm) :
    eigenQ A hA * (eigenQ A hA).transpose = 1 := by
  change ((hermitian A hA).eigenvectorUnitary : M3) *
    star ((hermitian A hA).eigenvectorUnitary : M3) = 1
  exact ((hermitian A hA).eigenvectorUnitary).2.2

theorem eigenQ_diagonalizes (A : M3) (hA : A.IsSymm) :
    (eigenQ A hA).transpose * A * eigenQ A hA = Matrix.diagonal (eigenLamb A hA) := by
  simpa [eigenQ, eigenLamb, Unitary.conjStarAlgAut_star_apply,
    Matrix.star_eq_conjTranspose] using
    (hermitian A hA).conjStarAlgAut_star_eigenvectorUnitary

#print axioms eigenQ_orthogonal_left
#print axioms eigenQ_orthogonal_right
#print axioms eigenQ_diagonalizes

end CAS15SpectralWitness
