import Mathlib
import CAS15Frobenius

/-! Rotated coercivity on the actual nine-coordinate Frobenius space.
The supplied diagonalization is an ordinary real orthogonal matrix. No
coercivity, commutator bound, or norm-invariance premise is assumed. -/
noncomputable section
namespace CAS15Coercivity
open CAS15Frobenius

abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ
def mat (X : E) : M3 := fun i j => X (i,j)
def flat (A : M3) : E := WithLp.toLp 2 (fun p => A p.1 p.2)
@[simp] lemma mat_flat (A : M3) : mat (flat A) = A := rfl
@[simp] lemma flat_mat (X : E) : flat (mat X) = X := rfl

def rotate (Q : M3) (X : E) : E := flat (Q.transpose * mat X * Q)

lemma norm_sq_trace (X : E) : ‖X‖ ^ 2 = ((mat X).transpose * mat X).trace := by
  rw [frobenius_norm_sq]
  simp only [Matrix.trace, Matrix.diag, Matrix.mul_apply, Matrix.transpose_apply, mat]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro i _
  apply Finset.sum_congr rfl
  intro j _
  ring

lemma norm_rotate (Q : M3) (hQQ : Q * Q.transpose = 1) (X : E) :
    ‖rotate Q X‖ = ‖X‖ := by
  have hs : ‖rotate Q X‖ ^ 2 = ‖X‖ ^ 2 := by
    rw [norm_sq_trace, norm_sq_trace]
    simp only [rotate, mat_flat, Matrix.transpose_mul, Matrix.transpose_transpose]
    calc
      _ = (Q.transpose * (mat X).transpose * (Q * Q.transpose) * mat X * Q).trace := by
        congr 1
        simp only [Matrix.mul_assoc]
      _ = (Q.transpose * (mat X).transpose * mat X * Q).trace := by rw [hQQ]; simp
      _ = ((mat X).transpose * mat X * (Q * Q.transpose)).trace := by
        rw [Matrix.mul_assoc, Matrix.mul_assoc, Matrix.trace_mul_comm]
        simp only [Matrix.mul_assoc]
      _ = _ := by rw [hQQ]; simp
  nlinarith [norm_nonneg (rotate Q X), norm_nonneg X]

lemma mat_skew (X : skew) : (mat X.1).transpose = -mat X.1 := by
  ext i j
  simpa only [Matrix.transpose_apply, Matrix.neg_apply, mat] using X.2 j i

lemma rotate_skew (Q : M3) (X : skew) : rotate Q X.1 ∈ skew := by
  have ht : (mat (rotate Q X.1)).transpose = -mat (rotate Q X.1) := by
    simp only [rotate, mat_flat, Matrix.transpose_mul, Matrix.transpose_transpose,
      mat_skew X, Matrix.mul_neg, Matrix.neg_mul]
    simp only [Matrix.mul_assoc]
  intro i j
  have hh := congrFun (congrFun ht j) i
  simpa only [Matrix.transpose_apply, Matrix.neg_apply, mat] using hh

lemma mat_comm (M X : E) : mat (comm M X) = mat M * mat X - mat X * mat M := by
  ext i j
  simp [mat, Matrix.mul_apply, Finset.sum_sub_distrib]

lemma rotate_comm (Q : M3) (hQQ : Q * Q.transpose = 1) (M X : E) :
    rotate Q (comm M X) = comm (rotate Q M) (rotate Q X) := by
  apply (show Function.Injective mat from fun A B h => by simpa using congrArg flat h)
  simp only [rotate, mat_flat, mat_comm]
  rw [Matrix.mul_sub, Matrix.sub_mul]
  have hprod (A B : M3) :
      Q.transpose * A * B * Q = (Q.transpose * A * Q) * (Q.transpose * B * Q) := by
    calc
      _ = Q.transpose * A * (Q * Q.transpose) * B * Q := by rw [hQQ]; simp
      _ = _ := by simp only [Matrix.mul_assoc]
  simpa only [Matrix.mul_assoc] using congrArg₂ (· - ·) (hprod (mat M) (mat X))
    (hprod (mat X) (mat M))

lemma comm_diagonal_apply (lamb : Fin 3 → ℝ) (Y : E) (i j : Fin 3) :
    comm (flat (Matrix.diagonal lamb)) Y (i,j) = (lamb i - lamb j) * Y (i,j) := by
  rw [show comm (flat (Matrix.diagonal lamb)) Y (i,j) =
    (Matrix.diagonal lamb * mat Y - mat Y * Matrix.diagonal lamb) i j from
      congrFun (congrFun (mat_comm _ _) i) j]
  simp [Matrix.diagonal_mul, Matrix.mul_diagonal, mat]
  ring

theorem diagonal_coercivity (lamb : Fin 3 → ℝ) (delta : ℝ) (hd : 0 ≤ delta)
    (hgap : ∀ i j : Fin 3, i ≠ j → delta ≤ |lamb i - lamb j|) (Y : skew) :
    delta * ‖Y.1‖ ≤ ‖comm (flat (Matrix.diagonal lamb)) Y.1‖ := by
  apply (sq_le_sq₀ (mul_nonneg hd (norm_nonneg _)) (norm_nonneg _)).mp
  rw [mul_pow, frobenius_norm_sq, frobenius_norm_sq]
  simp only [Finset.mul_sum]
  apply Finset.sum_le_sum
  intro i _
  apply Finset.sum_le_sum
  intro j _
  rw [comm_diagonal_apply]
  by_cases hij : i = j
  · subst j
    have hz : Y.1 (i,i) = 0 := by have hh := Y.2 i i; linarith
    simp [hz]
  · have hh : delta ^ 2 ≤ (lamb i - lamb j) ^ 2 := by
      have := (sq_le_sq₀ hd (abs_nonneg (lamb i - lamb j))).mpr (hgap i j hij)
      simpa only [sq_abs] using this
    simpa only [mul_pow] using mul_le_mul_of_nonneg_right hh (sq_nonneg (Y.1 (i,j)))

/-- Arbitrary real symmetric matrix, explicitly supplied orthogonal eigenbasis,
and a lower eigenvalue-gap bound. The conclusion remains valid at delta = 0. -/
theorem rotated_coercivity (Mhat : E) (Q : M3) (lamb : Fin 3 → ℝ) (delta : ℝ)
    (_hsym : (mat Mhat).transpose = mat Mhat)
    (_hQtQ : Q.transpose * Q = 1) (hQQt : Q * Q.transpose = 1)
    (hdiag : Q.transpose * mat Mhat * Q = Matrix.diagonal lamb)
    (hd : 0 ≤ delta)
    (hgap : ∀ i j : Fin 3, i ≠ j → delta ≤ |lamb i - lamb j|)
    (X : skew) : delta * ‖X.1‖ ≤ ‖comm Mhat X.1‖ := by
  let Y : skew := ⟨rotate Q X.1, rotate_skew Q X⟩
  have hh := diagonal_coercivity lamb delta hd hgap Y
  have hm : rotate Q Mhat = flat (Matrix.diagonal lamb) := congrArg flat hdiag
  rw [← hm, ← rotate_comm Q hQQt Mhat X.1] at hh
  simpa only [Y, norm_rotate Q hQQt] using hh

#print axioms norm_rotate
#print axioms rotate_skew
#print axioms rotate_comm
#print axioms diagonal_coercivity
#print axioms rotated_coercivity
end CAS15Coercivity
