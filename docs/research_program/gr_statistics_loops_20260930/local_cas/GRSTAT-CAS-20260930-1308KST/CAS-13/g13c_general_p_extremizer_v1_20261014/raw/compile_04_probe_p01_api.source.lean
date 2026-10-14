import G13BBoundaryMinimax

/-! API probe (no target proof): Mathlib names and definition elaboration only. -/

open MeasureTheory Set

#check @Real.hasDerivAt_rpow_const
#check @Real.deriv_rpow_const
#check @Real.iter_deriv_rpow_const
#check @iter_deriv_pow
#check @strictConvexOn_rpow
#check @strictConvexOn_of_deriv2_pos
#check @exists_hasDerivAt_eq_zero
#check @monotoneOn_of_deriv_nonneg
#check @antitoneOn_of_deriv_nonpos
#check @Matrix.det_succ_column_zero
#check @Matrix.det_fin_three
#check @descPochhammer_succ_right
#check @Real.rpow_add
#check @Real.continuous_rpow_const
#check @CAS13G13B.rmoment
#check @CAS13G13B.lowerEnd
#check @CAS13G13B.NEFibre
#check @CAS13MeasureComposition.hermite

noncomputable section
namespace ProbeG13C

def wronskian {n : ℕ} (f : Fin n → ℝ → ℝ) (y : ℝ) : ℝ :=
  (Matrix.of fun i j : Fin n => deriv^[(i : ℕ)] (f j) y).det

def powerSystem (p : ℝ) : Fin 4 → ℝ → ℝ :=
  ![fun _ => 1, fun x => x ^ 3, fun x => x ^ 4, fun x => x ^ p]

#check wronskian (powerSystem 5) 1
#check wronskian (![fun _ => (1 : ℝ), fun x : ℝ => x ^ 3] : Fin 2 → ℝ → ℝ) 1

end ProbeG13C
