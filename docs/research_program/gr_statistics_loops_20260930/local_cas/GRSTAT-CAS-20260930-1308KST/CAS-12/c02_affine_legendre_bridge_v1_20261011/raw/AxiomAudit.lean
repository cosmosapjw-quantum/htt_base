import Mathlib.RingTheory.Polynomial.ShiftedLegendre
import Mathlib.MeasureTheory.Integral.IntervalIntegral.Basic

open Polynomial MeasureTheory

namespace CAS12Affine

/-- The shifted Legendre polynomial with real coefficients. -/
noncomputable def shifted (n : Nat) : Polynomial Real :=
  (Polynomial.shiftedLegendre n).map (Int.castRingHom Real)

/-- Explicit conventional-coordinate lift of the shifted polynomial.
This definition makes no independent conventional-Legendre normalization claim. -/
noncomputable def conventionalLift (n : Nat) (x : Real) : Real :=
  (shifted n).eval ((x + 1) / 2)

/-- Affine transport from `[-1,1]` to `[0,1]`, including its Jacobian. -/
theorem conventionalLift_integral (n : Nat) :
    (∫ x in (-1 : Real)..1, conventionalLift n x) =
      2 * (∫ t in (0 : Real)..1, (shifted n).eval t) := by
  have h := intervalIntegral.integral_comp_div_add
    (a := (-1 : Real)) (b := (1 : Real))
    (fun t : Real => (shifted n).eval t)
    (c := (2 : Real)) (by norm_num) (1 / 2 : Real)
  have ha : ∀ x : Real, (x + 1) / 2 = x / 2 + 1 / 2 := by
    intro x
    ring
  simpa only [conventionalLift, ha, show (-1 : Real) / 2 + 1 / 2 = 0 by norm_num,
    show (1 : Real) / 2 + 1 / 2 = 1 by norm_num, smul_eq_mul] using h

end CAS12Affine

set_option pp.all true in
#check CAS12Affine.conventionalLift_integral
#print axioms CAS12Affine.conventionalLift_integral
#print CAS12Affine.conventionalLift
#print CAS12Affine.shifted

