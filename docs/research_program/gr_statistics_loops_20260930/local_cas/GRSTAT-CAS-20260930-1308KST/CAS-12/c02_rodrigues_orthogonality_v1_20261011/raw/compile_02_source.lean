import Mathlib.RingTheory.Polynomial.ShiftedLegendre
import Mathlib.MeasureTheory.Integral.IntervalIntegral.Basic
import Mathlib.Analysis.Calculus.ContDiff.Defs
import Mathlib.Analysis.Calculus.Deriv.Polynomial
import Mathlib.MeasureTheory.Integral.IntervalIntegral.IntegrationByParts
import Mathlib.Topology.Algebra.Polynomial

open Polynomial MeasureTheory

namespace CAS12Rodrigues

noncomputable def shifted (n : Nat) : Polynomial Real :=
  (Polynomial.shiftedLegendre n).map (Int.castRingHom Real)

private theorem repeated_parts (k : Nat) (p q : Polynomial Real)
    (hp : derivative^[k] p = 0)
    (hq : ∀ j < k, (derivative^[j] q).eval 0 = 0 ∧
      (derivative^[j] q).eval 1 = 0) :
    (∫ x in (0 : Real)..1, p.eval x * (derivative^[k] q).eval x) = 0 := by
  induction k generalizing p with
  | zero => simp_all
  | succ k ih =>
    have hb := hq k (Nat.lt_succ_self k)
    have hpd : derivative^[k] (derivative p) = 0 := by
      simpa only [Function.iterate_succ_apply] using hp
    have hz := ih (derivative p) hpd (fun j hj => hq j (Nat.lt_trans hj (Nat.lt_succ_self k)))
    have hi := intervalIntegral.integral_mul_deriv_eq_deriv_mul_of_hasDerivAt
      p.continuous.continuousOn (derivative^[k] q).continuous.continuousOn
      (fun x _ => p.hasDerivAt x) (fun x _ => (derivative^[k] q).hasDerivAt x)
      p.derivative.continuous.intervalIntegrable
      (derivative (derivative^[k] q)).continuous.intervalIntegrable
    simpa only [Function.iterate_succ_apply', hb.1, hb.2, mul_zero, sub_self, hz] using hi

private theorem endpoint (n j : Nat) (hj : j < n) (x : Real)
    (hx : x = 0 ∨ x = 1) :
    (derivative^[j] ((X : Polynomial Real)^n * (1-X)^n)).eval x = 0 := by
  rcases hx with rfl | rfl
  · have hd := pow_sub_dvd_iterate_derivative_of_pow_dvd j
      (dvd_mul_right ((X : Polynomial Real)^n) ((1-X)^n))
    obtain ⟨r, hr⟩ := hd
    rw [hr]
    simp [Nat.sub_ne_zero_of_lt hj]
  · have hd := pow_sub_dvd_iterate_derivative_of_pow_dvd j
      (dvd_mul_left ((1-(X : Polynomial Real))^n) (X^n))
    obtain ⟨r, hr⟩ := hd
    rw [hr]
    simp [Nat.sub_ne_zero_of_lt hj]

theorem shifted_orthogonal_lower_degree (n : Nat) (p : Polynomial Real)
    (hp : p.natDegree < n) :
    (MeasureTheory.integral
      (MeasureTheory.Measure.restrict MeasureTheory.volume (Set.Icc 0 1))
      (fun x : Real => p.eval x * (shifted n).eval x)) = 0 := by
  have hr : (n.factorial : Polynomial Real) * shifted n =
      derivative^[n] ((X : Polynomial Real)^n * (1-X)^n) := by
    have h := congrArg (Polynomial.map (Int.castRingHom Real))
      (Polynomial.factorial_mul_shiftedLegendre_eq n)
    rw [← Polynomial.iterate_derivative_map] at h
    simpa [shifted, Polynomial.map_mul, Polynomial.map_pow,
      Polynomial.map_sub] using h
  have hz := repeated_parts n p ((X : Polynomial Real)^n * (1-X)^n)
    (Polynomial.iterate_derivative_eq_zero hp)
    (fun j hj => ⟨endpoint n j hj 0 (Or.inl rfl), endpoint n j hj 1 (Or.inr rfl)⟩)
  have he : ∀ x : Real, p.eval x * (derivative^[n]
      ((X : Polynomial Real)^n * (1-X)^n)).eval x =
      (n.factorial : Real) * (p.eval x * (shifted n).eval x) := by
    intro x
    rw [← hr]
    simp only [eval_mul, eval_natCast]
    ring
  simp_rw [he] at hz
  rw [intervalIntegral.integral_const_mul] at hz
  have hf : (n.factorial : Real) ≠ 0 := Nat.cast_ne_zero.mpr (Nat.factorial_ne_zero n)
  have hv := (mul_eq_zero.mp hz).resolve_left hf
  rw [MeasureTheory.integral_Icc_eq_integral_Ioc]
  rw [← intervalIntegral.integral_of_le (show (0 : Real) ≤ 1 by norm_num)]
  exact hv

end CAS12Rodrigues
