import Mathlib

/-!
An ordered orthogonal spectral witness for a real symmetric 3-by-3 matrix.
The columns are mathlib's decreasingly indexed eigenvector basis itself.
-/

noncomputable section
namespace CAS15OrderedWitness

open scoped InnerProductSpace

abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ
abbrev V3 := EuclideanSpace ℝ (Fin 3)

theorem dim3 : Module.finrank ℝ V3 = 3 := by simp [V3]

def matrixOperator (A : M3) : V3 →L[ℝ] V3 :=
  Matrix.toEuclideanCLM (n := Fin 3) (𝕜 := ℝ) A

theorem matrixOperator_symmetric (A : M3) (hA : A.IsSymm) :
    (matrixOperator A).toLinearMap.IsSymmetric := by
  apply Matrix.isSymmetric_toEuclideanLin_iff.mpr
  exact Matrix.isHermitian_iff_isSymm.mpr hA

def orderedBasis (A : M3) (hA : A.IsSymm) :
    OrthonormalBasis (Fin 3) ℝ V3 :=
  (matrixOperator_symmetric A hA).eigenvectorBasis dim3

def orderedSpectrum (A : M3) (hA : A.IsSymm) : Fin 3 → ℝ :=
  (matrixOperator_symmetric A hA).eigenvalues dim3

def orderedQ (A : M3) (hA : A.IsSymm) : M3 :=
  (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis.toMatrix (orderedBasis A hA).toBasis

theorem orderedQ_orthogonal_left (A : M3) (hA : A.IsSymm) :
    (orderedQ A hA).transpose * orderedQ A hA = 1 := by
  classical
  have h := (EuclideanSpace.basisFun (Fin 3) ℝ).toMatrix_orthonormalBasis_conjTranspose_mul_self
    (orderedBasis A hA)
  simpa only [orderedQ, Matrix.conjTranspose_eq_transpose_of_trivial,
    OrthonormalBasis.coe_toBasis] using h

theorem orderedQ_orthogonal_right (A : M3) (hA : A.IsSymm) :
    orderedQ A hA * (orderedQ A hA).transpose = 1 := by
  classical
  have h := (EuclideanSpace.basisFun (Fin 3) ℝ).toMatrix_orthonormalBasis_self_mul_conjTranspose
    (orderedBasis A hA)
  simpa only [orderedQ, Matrix.conjTranspose_eq_transpose_of_trivial,
    OrthonormalBasis.coe_toBasis] using h

private theorem standard_matrix (A : M3) :
    LinearMap.toMatrix (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis
      (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis
      (matrixOperator A).toLinearMap = A := by
  change LinearMap.toMatrix (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis
    (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis (Matrix.toEuclideanLin A) = A
  rw [Matrix.toEuclideanLin_eq_toLin_orthonormal]
  exact LinearMap.toMatrix_toLin _ _ A

private theorem orderedQ_transpose (A : M3) (hA : A.IsSymm) :
    (orderedQ A hA).transpose =
      (orderedBasis A hA).toBasis.toMatrix
        (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis := by
  classical
  have hp : orderedQ A hA *
      (orderedBasis A hA).toBasis.toMatrix
        (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis = 1 := by
    simpa only [orderedQ, OrthonormalBasis.coe_toBasis] using
      (Module.Basis.toMatrix_mul_toMatrix_flip
        (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis (orderedBasis A hA).toBasis)
  calc
    (orderedQ A hA).transpose = (orderedQ A hA).transpose * 1 := by simp
    _ = (orderedQ A hA).transpose *
      (orderedQ A hA * (orderedBasis A hA).toBasis.toMatrix
        (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis) := by rw [hp]
    _ = ((orderedQ A hA).transpose * orderedQ A hA) *
      (orderedBasis A hA).toBasis.toMatrix
        (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis := by rw [Matrix.mul_assoc]
    _ = _ := by rw [orderedQ_orthogonal_left, one_mul]

theorem orderedQ_diagonalizes (A : M3) (hA : A.IsSymm) :
    (orderedQ A hA).transpose * A * orderedQ A hA =
      Matrix.diagonal (orderedSpectrum A hA) := by
  classical
  rw [orderedQ_transpose]
  have hc := basis_toMatrix_mul_linearMap_toMatrix_mul_basis_toMatrix
    (orderedBasis A hA).toBasis (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis
    (orderedBasis A hA).toBasis (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis
    (matrixOperator A).toLinearMap
  rw [standard_matrix] at hc
  calc
    _ = LinearMap.toMatrix (orderedBasis A hA).toBasis
      (orderedBasis A hA).toBasis (matrixOperator A).toLinearMap := by
        simpa only [orderedQ, OrthonormalBasis.coe_toBasis] using hc
    _ = Matrix.diagonal (orderedSpectrum A hA) := by
      simpa [orderedBasis, orderedSpectrum, RCLike.ofReal_real_eq_id] using
        (matrixOperator_symmetric A hA).toMatrix_eigenvectorBasis dim3

def orderedGap (A : M3) (hA : A.IsSymm) : ℝ :=
  min (orderedSpectrum A hA 0 - orderedSpectrum A hA 1)
    (orderedSpectrum A hA 1 - orderedSpectrum A hA 2)

theorem orderedGap_pairwise (A : M3) (hA : A.IsSymm) (δ : ℝ)
    (hδ : δ ≤ orderedGap A hA) :
    ∀ i j : Fin 3, i ≠ j → δ ≤ |orderedSpectrum A hA i - orderedSpectrum A hA j| := by
  intro i j hij
  have hant := (matrixOperator_symmetric A hA).eigenvalues_antitone dim3
  have h01 : orderedSpectrum A hA 1 ≤ orderedSpectrum A hA 0 :=
    hant (by decide)
  have h12 : orderedSpectrum A hA 2 ≤ orderedSpectrum A hA 1 :=
    hant (by decide)
  have hd01 : δ ≤ orderedSpectrum A hA 0 - orderedSpectrum A hA 1 :=
    le_trans hδ (min_le_left _ _)
  have hd12 : δ ≤ orderedSpectrum A hA 1 - orderedSpectrum A hA 2 :=
    le_trans hδ (min_le_right _ _)
  fin_cases i <;> fin_cases j <;> simp_all
  all_goals
    first
    | rw [abs_of_nonneg (by linarith)]
      linarith
    | rw [abs_of_nonpos (by linarith)]
      linarith

/-- The exact inputs needed by the previously proved rotated coercivity theorem,
with the eigenvalue indices fixed to mathlib's decreasing order. -/
theorem ordered_witness (A : M3) (hA : A.IsSymm) (δ : ℝ)
    (hδ : δ ≤ orderedGap A hA) :
    ∃ Q : M3,
      Q.transpose * Q = 1 ∧ Q * Q.transpose = 1 ∧
      Q.transpose * A * Q = Matrix.diagonal (orderedSpectrum A hA) ∧
      (∀ i j : Fin 3, i ≠ j →
        δ ≤ |orderedSpectrum A hA i - orderedSpectrum A hA j|) := by
  exact ⟨orderedQ A hA, orderedQ_orthogonal_left A hA,
    orderedQ_orthogonal_right A hA, orderedQ_diagonalizes A hA,
    orderedGap_pairwise A hA δ hδ⟩

#print axioms orderedQ_orthogonal_left
#print axioms orderedQ_orthogonal_right
#print axioms orderedQ_diagonalizes
#print axioms orderedGap_pairwise
#print axioms ordered_witness

end CAS15OrderedWitness
