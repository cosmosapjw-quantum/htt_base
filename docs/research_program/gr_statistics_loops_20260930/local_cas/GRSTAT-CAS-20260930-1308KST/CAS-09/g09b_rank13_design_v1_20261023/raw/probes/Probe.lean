import Mathlib
import G09ADefinitions
open G09A
open scoped Matrix

def E4mat {ι : Type*} (dir : ι → V3) : Matrix ι (Fin 4) ℝ :=
  Matrix.of fun i => ![1, dir i 0, dir i 1, dir i 2]

theorem lit : E4mat (dirStar ∘ σStar) = !![1, 1, 0, 0; 1, -1, 0, 0; 1, 0, 1, 0; 1, 0, 0, 1] := by
  ext i j; fin_cases i <;> fin_cases j <;> simp [E4mat, dirStar, σStar]

example : (E4mat (dirStar ∘ σStar)).det = -2 := by
  rw [lit, Matrix.det_succ_row_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three, Fin.succAbove]
  norm_num

example : (E4mat (dirStar ∘ σStar)).det = -2 := by
  rw [lit, Matrix.det_succ_column_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three]
  norm_num

example : (E4mat (dirStar ∘ σStar)).det = -2 := by
  rw [lit, Matrix.det_succ_row_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three, Fin.succAbove, Fin.lt_def]
  norm_num

example : (E4mat (dirStar ∘ σStar)).det = -2 := by
  rw [lit]
  simp [Matrix.det_succ_row_zero, Fin.sum_univ_succ, Fin.succAbove, Fin.lt_def]
  norm_num
