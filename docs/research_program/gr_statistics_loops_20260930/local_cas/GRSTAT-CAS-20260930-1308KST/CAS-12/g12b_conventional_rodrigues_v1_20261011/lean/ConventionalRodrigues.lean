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
    apply Polynomial.funext
    intro t
    simp only [Polynomial.eval_comp, Polynomial.eval_mul, Polynomial.eval_X,
      Polynomial.eval_sub, Polynomial.eval_one, Polynomial.eval_add,
      Polynomial.eval_C, Polynomial.eval_pow]
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
  have h := iterate_derivative_comp_affine
    ((X : Polynomial Real)^n * (1-X)^n) (1/2) (1/2) n
  rw [rodrigues_seed_comp, Polynomial.iterate_derivative_C_mul,
    ← shifted_rodrigues] at h
  have he := congrArg (fun p : Polynomial Real => p.eval x) h
  simp only [eval_mul, eval_C, eval_comp, eval_add, eval_X] at he
  have hc : (-4 : Real)^n * (-1/4 : Real)^n = 1 := by
    rw [← mul_pow]
    norm_num
  have hs : (-4 : Real)^n * (1/2 : Real)^n =
      (-1 : Real)^n * (2 : Real)^n := by
    rw [← mul_pow, ← mul_pow]
    norm_num
  have hm := congrArg (fun y : Real => (-4 : Real)^n * y) he
  have hd : (derivative^[n] (((X : Polynomial Real)^2 - 1)^n)).eval x =
      (-1 : Real)^n * (2 : Real)^n * (n.factorial : Real) *
        (CAS12Affine.shifted n).eval ((x+1)/2) := by
    calc
      _ = (-4 : Real)^n * ((-1/4 : Real)^n *
            (derivative^[n] (((X : Polynomial Real)^2 - 1)^n)).eval x) := by
          rw [← mul_assoc, hc, one_mul]
      _ = (-4 : Real)^n * ((1/2 : Real)^n *
            ((n.factorial : Real) *
              (CAS12Affine.shifted n).eval ((x+1)/2))) := by
          convert hm using 1 <;> ring
      _ = _ := by rw [← mul_assoc, hs]; ring
  have hden : (2 : Real)^n * (n.factorial : Real) ≠ 0 :=
    mul_ne_zero (pow_ne_zero n (by norm_num))
      (Nat.cast_ne_zero.mpr (Nat.factorial_ne_zero n))
  apply (eq_div_iff hden).2
  unfold CAS12SignNormalization.standardLift CAS12Affine.conventionalLift
  rw [hd]
  ring

theorem scalar_thomson_rodrigues_moment (n : Nat) :
    2 * Real.pi * (∫ mu in (-1 : Real)..1,
      (3 * (1 + mu^2) / (16 * Real.pi)) *
        ((derivative^[n] (((X : Polynomial Real)^2 - 1)^n)).eval mu /
          ((2 : Real)^n * (n.factorial : Real)))) =
      if n = 0 then 1 else if n = 2 then 1/10 else 0 := by
  simpa only [CAS12ScalarWrapper.moment, CAS12ScalarWrapper.kernel,
    standardLift_eq_rodrigues] using
      CAS12ScalarWrapper.scalar_thomson_moment n

end CAS12ConventionalRodrigues
