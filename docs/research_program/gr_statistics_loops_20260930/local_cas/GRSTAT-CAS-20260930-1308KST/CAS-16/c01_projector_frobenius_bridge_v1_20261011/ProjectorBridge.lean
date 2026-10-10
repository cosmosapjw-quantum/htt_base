import Mathlib

/-! Finite real projector bridge. No collision operator is defined here. -/
namespace CAS16Projector
open scoped BigOperators

abbrev Vec := Fin 3 → ℝ
abbrev Mat := Matrix (Fin 3) (Fin 3) ℝ

def dot (u v : Vec) : ℝ := ∑ i, u i * v i
def vectorSquare (v : Vec) : ℝ := ∑ i, (v i)^2
def project (e v : Vec) : Vec := fun i => v i - e i * dot e v
def projector (e : Vec) : Mat := 1 - Matrix.of (fun i j => e i * e j)
def frobeniusSquare (J : Mat) : ℝ := ∑ i, ∑ j, (J i j)^2

theorem project_dot_zero (e v : Vec) (he : dot e e = 1) :
    dot e (project e v) = 0 := by
  simp only [dot, project, Fin.sum_univ_three] at *
  linear_combination -(e 0 * v 0 + e 1 * v 1 + e 2 * v 2) * he

theorem project_square_identity (e v : Vec) (he : dot e e = 1) :
    vectorSquare (project e v) + (dot e v)^2 = vectorSquare v := by
  simp only [dot, project, vectorSquare, Fin.sum_univ_three] at *
  linear_combination (e 0 * v 0 + e 1 * v 1 + e 2 * v 2)^2 * he

theorem project_square_le (e v : Vec) (he : dot e e = 1) :
    vectorSquare (project e v) ≤ vectorSquare v := by
  have h := project_square_identity e v he
  nlinarith [sq_nonneg (dot e v)]

theorem left_action (e : Vec) (J : Mat) (i j : Fin 3) :
    (projector e * J) i j = project e (fun k => J k j) i := by
  rw [projector, Matrix.sub_mul, Matrix.one_mul]
  simp only [Matrix.sub_apply,
    Matrix.mul_apply, Matrix.of_apply, project, dot, Fin.sum_univ_three]
  ring

theorem right_action (e : Vec) (J : Mat) (i j : Fin 3) :
    (J * projector e) i j = project e (fun k => J i k) j := by
  rw [projector, Matrix.mul_sub, Matrix.mul_one]
  simp only [Matrix.sub_apply,
    Matrix.mul_apply, Matrix.of_apply, project, dot, Fin.sum_univ_three]
  ring

theorem projector_symmetric (e : Vec) : (projector e).transpose = projector e := by
  ext i j
  simp [Matrix.transpose_apply, projector, Matrix.sub_apply, Matrix.one_apply,
    eq_comm, mul_comm]

theorem projector_column (e : Vec) (j : Fin 3) :
    (fun i => projector e i j) = project e (fun i => (1 : Mat) i j) := by
  funext i
  simpa using left_action e (1 : Mat) i j

theorem projector_idempotent (e : Vec) (he : dot e e = 1) :
    projector e * projector e = projector e := by
  ext i j
  rw [left_action]
  have hz : dot e (fun k => projector e k j) = 0 := by
    rw [projector_column]
    exact project_dot_zero e _ he
  simp only [project, hz, mul_zero, sub_zero]

theorem left_frobenius_identity (e : Vec) (J : Mat) (he : dot e e = 1) :
    frobeniusSquare (projector e * J) + ∑ j, (dot e (fun i => J i j))^2 =
      frobeniusSquare J := by
  unfold frobeniusSquare
  rw [Finset.sum_comm (f := fun i j => ((projector e * J) i j)^2)]
  rw [Finset.sum_comm (f := fun i j => (J i j)^2)]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro j _
  simp_rw [left_action]
  exact project_square_identity e (fun i => J i j) he

theorem right_frobenius_identity (e : Vec) (J : Mat) (he : dot e e = 1) :
    frobeniusSquare (J * projector e) + ∑ i, (dot e (fun j => J i j))^2 =
      frobeniusSquare J := by
  unfold frobeniusSquare
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  simp_rw [right_action]
  exact project_square_identity e (fun j => J i j) he

theorem left_frobenius_le (e : Vec) (J : Mat) (he : dot e e = 1) :
    frobeniusSquare (projector e * J) ≤ frobeniusSquare J := by
  have h := left_frobenius_identity e J he
  have hn : 0 ≤ ∑ j, (dot e (fun i => J i j))^2 :=
    Finset.sum_nonneg (fun j _ => sq_nonneg _)
  linarith

theorem right_frobenius_le (e : Vec) (J : Mat) (he : dot e e = 1) :
    frobeniusSquare (J * projector e) ≤ frobeniusSquare J := by
  have h := right_frobenius_identity e J he
  have hn : 0 ≤ ∑ i, (dot e (fun j => J i j))^2 :=
    Finset.sum_nonneg (fun i _ => sq_nonneg _)
  linarith

theorem sandwich_frobenius_le (e : Vec) (J : Mat) (he : dot e e = 1) :
    frobeniusSquare (projector e * J * projector e) ≤ frobeniusSquare J :=
  le_trans (right_frobenius_le e (projector e * J) he) (left_frobenius_le e J he)

theorem finite_projector_bridge (e : Vec) (J : Mat) (he : ∑ i, e i * e i = 1) :
    (projector e).transpose = projector e ∧
    projector e * projector e = projector e ∧
    frobeniusSquare (projector e * J * projector e) ≤ frobeniusSquare J :=
  ⟨projector_symmetric e, projector_idempotent e he, sandwich_frobenius_le e J he⟩

#print axioms project_dot_zero
#print axioms project_square_identity
#print axioms projector_symmetric
#print axioms projector_idempotent
#print axioms left_frobenius_identity
#print axioms right_frobenius_identity
#print axioms sandwich_frobenius_le
#print axioms finite_projector_bridge
end CAS16Projector
