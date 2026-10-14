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

namespace CAS12SignNormalization

/-- Explicit sign-normalized coordinate lift; no all-degree identification is asserted. -/
noncomputable def standardLift (n : Nat) (x : Real) : Real :=
  (-1 : Real) ^ n * CAS12Affine.conventionalLift n x

/-- Degree-zero normalization from mathlib's defining finite sum. -/
theorem standardLift_zero (x : Real) : standardLift 0 x = 1 := by
  simp [standardLift, CAS12Affine.conventionalLift, CAS12Affine.shifted,
    Polynomial.shiftedLegendre]

/-- Degree-one normalization from mathlib's defining finite sum. -/
theorem standardLift_one (x : Real) : standardLift 1 x = x := by
  norm_num [standardLift, CAS12Affine.conventionalLift, CAS12Affine.shifted,
    Polynomial.shiftedLegendre, Finset.sum_range_succ]
  ring

/-- All-degree affine transport with explicit sign and Jacobian factors. -/
theorem standardLift_integral (n : Nat) :
    (∫ x in (-1 : Real)..1, standardLift n x) =
      (-1 : Real) ^ n * (2 * (∫ t in (0 : Real)..1, (CAS12Affine.shifted n).eval t)) := by
  simp only [standardLift, intervalIntegral.integral_const_mul,
    CAS12Affine.conventionalLift_integral]

end CAS12SignNormalization
