import Mathlib
import G09ADefinitions
open G09A
open scoped Matrix

def E4mat {ι : Type*} (dir : ι → V3) : Matrix ι (Fin 4) ℝ :=
  Matrix.of fun i => ![1, dir i 0, dir i 1, dir i 2]

example : (E4mat (dirStar ∘ σStar)).det = -2 := by
  simp [Matrix.det_succ_row_zero, Fin.sum_univ_succ, Fin.succAbove, Fin.lt_iff_val_lt_val, E4mat, dirStar, σStar]
  norm_num

example : (E4mat (dirStar ∘ σStar)).det = -2 := by
  have : E4mat (dirStar ∘ σStar) = !![1, 1, 0, 0; 1, -1, 0, 0; 1, 0, 1, 0; 1, 0, 0, 1] := by
    ext i j; fin_cases i <;> fin_cases j <;> simp [E4mat, dirStar, σStar]
  rw [this, Matrix.det_succ_row_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three, Fin.succAbove, Fin.lt_iff_val_lt_val]
  norm_num
