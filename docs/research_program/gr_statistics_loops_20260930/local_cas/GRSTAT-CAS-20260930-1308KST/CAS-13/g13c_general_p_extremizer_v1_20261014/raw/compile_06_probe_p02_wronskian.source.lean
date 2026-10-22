import G13BBoundaryMinimax

open MeasureTheory Set

noncomputable section
namespace ProbeG13C

def wronskian {n : ℕ} (f : Fin n → ℝ → ℝ) (y : ℝ) : ℝ :=
  (Matrix.of fun i j : Fin n => deriv^[(i : ℕ)] (f j) y).det

def powerSystem (p : ℝ) : Fin 4 → ℝ → ℝ :=
  ![fun _ => 1, fun x => x ^ 3, fun x => x ^ 4, fun x => x ^ p]

theorem rpow_shift {y : ℝ} (hy : 0 < y) (q : ℝ) (n : ℕ) : y ^ (q + n) = y ^ q * y ^ n := by
  rw [Real.rpow_add hy, Real.rpow_natCast]

theorem wronskian_two (y : ℝ) : wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3] y = 3 * y ^ 2 := by
  unfold wronskian
  rw [Matrix.det_fin_two]
  simp [iter_deriv_pow]

theorem wronskian_three (y : ℝ) :
    wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3, fun x : ℝ => x ^ 4] y = 12 * y ^ 4 := by
  unfold wronskian
  rw [Matrix.det_fin_three]
  simp [iter_deriv_pow, Finset.prod_range_succ]
  ring

theorem wronskian_power_system (p : ℝ) {y : ℝ} (hy : 0 < y) :
    wronskian (powerSystem p) y = 12 * p * (p - 3) * (p - 4) * y ^ (p + 1) := by
  unfold wronskian powerSystem
  rw [Matrix.det_succ_column_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three, iter_deriv_pow, Finset.prod_range_succ,
    Real.iter_deriv_rpow_const, descPochhammer_succ_right, Fin.succAbove]
  have e1 : y ^ (p - 1) = y ^ (p - 3) * y ^ 2 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  have e2 : y ^ (p - 2) = y ^ (p - 3) * y ^ 1 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  have e3 : y ^ (p + 1) = y ^ (p - 3) * y ^ 4 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  rw [e1, e2, e3]
  ring

end ProbeG13C
