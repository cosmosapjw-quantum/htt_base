import G13BBoundaryMinimax

open MeasureTheory Set

noncomputable section
namespace ProbeG13C

def wronskian {n : ℕ} (f : Fin n → ℝ → ℝ) (y : ℝ) : ℝ :=
  (Matrix.of fun i j : Fin n => deriv^[(i : ℕ)] (f j) y).det

def powerSystem (p : ℝ) : Fin 4 → ℝ → ℝ :=
  ![fun _ => 1, fun x => x ^ 3, fun x => x ^ 4, fun x => x ^ p]

theorem iter_deriv_one (k : ℕ) (y : ℝ) : deriv^[k + 1] (fun _ : ℝ => (1 : ℝ)) y = 0 := by
  induction k with
  | zero => simp
  | succ k ih =>
    rw [Function.iterate_succ_apply']
    have : deriv^[k + 1] (fun _ : ℝ => (1 : ℝ)) = fun _ => 0 := funext fun z => by
      induction k with
      | zero => simp
      | succ j _ => rw [Function.iterate_succ_apply']; simp
    rw [this]; simp

theorem wronskian_two (y : ℝ) : wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3] y = 3 * y ^ 2 := by
  unfold wronskian
  rw [Matrix.det_fin_two]
  simp [iter_deriv_pow]

theorem wronskian_three (y : ℝ) :
    wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3, fun x : ℝ => x ^ 4] y = 12 * y ^ 4 := by
  unfold wronskian
  rw [Matrix.det_fin_three]
  simp [iter_deriv_pow, Finset.prod_range_succ, iter_deriv_one]
  ring

theorem wronskian_power_system (p : ℝ) {y : ℝ} (hy : 0 < y) :
    wronskian (powerSystem p) y = 12 * p * (p - 3) * (p - 4) * y ^ (p + 1) := by
  unfold wronskian powerSystem
  rw [Matrix.det_succ_column_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three, iter_deriv_pow, Finset.prod_range_succ,
    Real.iter_deriv_rpow_const, descPochhammer_succ_right, Fin.succAbove]
  done

end ProbeG13C
