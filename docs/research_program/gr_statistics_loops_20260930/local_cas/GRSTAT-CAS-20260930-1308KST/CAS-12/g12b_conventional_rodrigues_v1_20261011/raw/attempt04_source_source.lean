import ScalarWrapper

open Polynomial MeasureTheory

namespace CAS12ConventionalRodrigues

private theorem derivative_comp_affine (p : Polynomial Real) (a b : Real) :
    derivative (p.comp (C a * X + C b)) =
      C a * (derivative p).comp (C a * X + C b) := by
  rw [Polynomial.derivative_comp]
  simp

private theorem iterate_derivative_comp_affine (p : Polynomial Real)
    (a b : Real) (n : Nat) :
    derivative^[n] (p.comp (C a * X + C b)) =
      C (a ^ n) * (derivative^[n] p).comp (C a * X + C b) := by
  induction n generalizing p with
  | zero => simp
  | succ n ih =>
    rw [Function.iterate_succ_apply', ih, Polynomial.derivative_C_mul,
      derivative_comp_affine, Function.iterate_succ_apply']
    simp [pow_succ, mul_assoc]

private theorem rodrigues_seed_comp (n : Nat) :
    (((X : Polynomial Real)^n * (1-X)^n).comp (C (1/2 : Real)*X+C (1/2 : Real))) =
      C ((-1/4 : Real)^n) * (((X : Polynomial Real)^2-1)^n) := by
  have hs : ((X : Polynomial Real) * (1-X)).comp
      (C (1/2 : Real)*X+C (1/2 : Real)) =
      C (-1/4 : Real) * ((X : Polynomial Real)^2-1) := by
    simp only [Polynomial.mul_comp, Polynomial.X_comp, Polynomial.sub_comp,
      Polynomial.one_comp]
    norm_num
    ring
  rw [← mul_pow, Polynomial.pow_comp, hs, mul_pow, ← map_pow]

private theorem shifted_rodrigues (n : Nat) :
    C (n.factorial : Real) * CAS12Affine.shifted n =
      derivative^[n] ((X : Polynomial Real)^n * (1-X)^n) := by
  have h := congrArg (Polynomial.map (Int.castRingHom Real))
    (Polynomial.factorial_mul_shiftedLegendre_eq n)
  rw [← Polynomial.iterate_derivative_map] at h
  simpa [CAS12Affine.shifted, Polynomial.map_mul, Polynomial.map_pow,
    Polynomial.map_sub] using h

theorem standardLift_eq_rodrigues (n : Nat) (x : Real) :
    CAS12SignNormalization.standardLift n x =
      (derivative^[n] (((X : Polynomial Real)^2 - 1)^n)).eval x /
        ((2 : Real)^n * (n.factorial : Real)) := by
  sorry

theorem scalar_thomson_rodrigues_moment (n : Nat) :
    2 * Real.pi * (∫ mu in (-1 : Real)..1,
      (3 * (1 + mu^2) / (16 * Real.pi)) *
        (derivative^[n] (((X : Polynomial Real)^2 - 1)^n)).eval mu /
          ((2 : Real)^n * (n.factorial : Real))) =
      if n = 0 then 1 else if n = 2 then 1/10 else 0 := by
  sorry

end CAS12ConventionalRodrigues
