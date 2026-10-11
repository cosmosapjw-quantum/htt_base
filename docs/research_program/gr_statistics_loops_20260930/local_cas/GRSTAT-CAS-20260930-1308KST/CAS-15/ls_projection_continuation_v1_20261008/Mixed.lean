import Mathlib

noncomputable section
namespace CAS15Mixed

abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ
abbrev V3 := EuclideanSpace ℝ (Fin 3)
abbrev F3 := EuclideanSpace ℝ (Fin 3 × Fin 3)

/-- The Euclidean norm on `F3` is the Frobenius norm of its 3 by 3 entries. -/
def col (X : F3) (j : Fin 3) : V3 := WithLp.toLp 2 (fun i => X (i, j))

def leftMul (A : M3) (X : F3) : F3 :=
  WithLp.toLp 2 (fun p => ∑ k : Fin 3, A p.1 k * X (k, p.2))

def rightMul (X : F3) (A : M3) : F3 :=
  WithLp.toLp 2 (fun p => ∑ k : Fin 3, X (p.1, k) * A k p.2)

def transpose (X : F3) : F3 := WithLp.toLp 2 (fun p => X (p.2, p.1))

def comm (A : M3) (X : F3) : F3 := leftMul A X - rightMul X A

/-- The norm is the induced Euclidean operator norm, not a matrix Frobenius norm. -/
def opNorm (A : M3) : ℝ := ‖(Matrix.toEuclideanCLM (n := Fin 3) (𝕜 := ℝ)) A‖

private lemma norm_sq_eq_sum_cols (X : F3) :
    ‖X‖ ^ 2 = ∑ j : Fin 3, ‖col X j‖ ^ 2 := by
  simp only [EuclideanSpace.real_norm_sq_eq, col]
  simpa only [Finset.univ_product_univ] using
    (Finset.sum_product_right (Finset.univ : Finset (Fin 3))
      (Finset.univ : Finset (Fin 3)) (fun p : Fin 3 × Fin 3 => X p ^ 2))

private lemma col_leftMul (A : M3) (X : F3) (j : Fin 3) :
    col (leftMul A X) j = (Matrix.toEuclideanCLM (n := Fin 3) (𝕜 := ℝ)) A (col X j) := by
  ext i
  simp [col, leftMul, Matrix.mulVec, dotProduct]

theorem norm_leftMul_le (A : M3) (X : F3) :
    ‖leftMul A X‖ ≤ opNorm A * ‖X‖ := by
  have hop : 0 ≤ opNorm A := norm_nonneg _
  apply (sq_le_sq₀ (norm_nonneg _) (mul_nonneg hop (norm_nonneg _))).mp
  calc
    ‖leftMul A X‖ ^ 2 = ∑ j : Fin 3, ‖col (leftMul A X) j‖ ^ 2 :=
      norm_sq_eq_sum_cols _
    _ ≤ ∑ j : Fin 3, (opNorm A * ‖col X j‖) ^ 2 := by
      apply Finset.sum_le_sum
      intro j _
      rw [col_leftMul]
      exact (sq_le_sq₀ (norm_nonneg _)
        (mul_nonneg hop (norm_nonneg _))).mpr
        (by simpa [opNorm] using
          (Matrix.toEuclideanCLM (n := Fin 3) (𝕜 := ℝ) A).le_opNorm (col X j))
    _ = (opNorm A * ‖X‖) ^ 2 := by
      calc
        _ = opNorm A ^ 2 * (∑ j : Fin 3, ‖col X j‖ ^ 2) := by
          simp [mul_pow, Finset.mul_sum]
        _ = _ := by rw [← norm_sq_eq_sum_cols]; ring

private lemma norm_transpose_sq (X : F3) : ‖transpose X‖ ^ 2 = ‖X‖ ^ 2 := by
  simp only [EuclideanSpace.real_norm_sq_eq, transpose]
  simp only [← Finset.univ_product_univ]
  rw [Finset.sum_product, Finset.sum_product]
  exact Finset.sum_comm

private lemma norm_transpose (X : F3) : ‖transpose X‖ = ‖X‖ := by
  nlinarith [norm_transpose_sq X, norm_nonneg (transpose X), norm_nonneg X]

private lemma rightMul_eq (A : M3) (X : F3) :
    rightMul X A = transpose (leftMul A.transpose (transpose X)) := by
  ext p
  simp [rightMul, leftMul, transpose, Matrix.transpose_apply, mul_comm]

private lemma opNorm_transpose (A : M3) : opNorm A.transpose = opNorm A := by
  letI : NormedAddCommGroup M3 := Matrix.instL2OpNormedAddCommGroup
  simp only [opNorm, Matrix.l2_opNorm_toEuclideanCLM]
  simpa using Matrix.l2_opNorm_conjTranspose A

theorem norm_rightMul_le (A : M3) (X : F3) :
    ‖rightMul X A‖ ≤ opNorm A * ‖X‖ := by
  rw [rightMul_eq, norm_transpose, ← opNorm_transpose A, ← norm_transpose X]
  exact norm_leftMul_le A.transpose (transpose X)

/-- No symmetry or skew assumption is needed for the mixed norm inequality. -/
theorem norm_comm_le (A : M3) (X : F3) :
    ‖comm A X‖ ≤ 2 * opNorm A * ‖X‖ := by
  calc
    ‖comm A X‖ = ‖leftMul A X - rightMul X A‖ := rfl
    _ ≤ ‖leftMul A X‖ + ‖rightMul X A‖ := norm_sub_le _ _
    _ ≤ opNorm A * ‖X‖ + opNorm A * ‖X‖ :=
      add_le_add (norm_leftMul_le A X) (norm_rightMul_le A X)
    _ = 2 * opNorm A * ‖X‖ := by ring

/-- Flat Euclidean entries interpreted as an ordinary real matrix. -/
def matrixOf (A : F3) : M3 := fun i j => A (i, j)

theorem norm_flat_comm_le (A X : F3) :
    ‖comm (matrixOf A) X‖ ≤ 2 * opNorm (matrixOf A) * ‖X‖ :=
  norm_comm_le (matrixOf A) X

#print axioms norm_leftMul_le
#print axioms norm_rightMul_le
#print axioms norm_comm_le
#print axioms norm_flat_comm_le

end CAS15Mixed
