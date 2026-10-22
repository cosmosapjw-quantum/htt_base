import Mathlib.RingTheory.Polynomial.ShiftedLegendre
import Mathlib.MeasureTheory.Integral.IntervalIntegral.Basic
import Mathlib.Analysis.Calculus.ContDiff.Defs
import Mathlib.Analysis.Calculus.Deriv.Polynomial
import Mathlib.MeasureTheory.Integral.IntervalIntegral.IntegrationByParts
import Mathlib.Topology.Algebra.Polynomial
import Mathlib.Analysis.SpecialFunctions.Integrals.Basic
import Mathlib.Tactic.ComputeDegree
import Mathlib.Tactic

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
      (p.derivative.continuous.intervalIntegrable 0 1)
      ((derivative (derivative^[k] q)).continuous.intervalIntegrable 0 1)
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

namespace CAS12WeightedMoment
open CAS12SignNormalization

theorem standardLift_two (x : Real) : standardLift 2 x = (3*x^2-1)/2 := by
  norm_num [standardLift, CAS12Affine.conventionalLift, CAS12Affine.shifted,
    Polynomial.shiftedLegendre, Finset.sum_range_succ, Nat.choose]
  ring

noncomputable def weight : Polynomial Real := 1 + (2*X-1)^2

theorem weighted_affine (n : Nat) :
    (∫ x in (-1 : Real)..1, (1+x^2)*standardLift n x) =
    (-1 : Real)^n * (2 * (∫ t in (0 : Real)..1,
      weight.eval t * (CAS12Rodrigues.shifted n).eval t)) := by
  have h := intervalIntegral.integral_comp_div_add
    (a := (-1 : Real)) (b := (1 : Real))
    (fun t : Real => weight.eval t * (CAS12Rodrigues.shifted n).eval t)
    (c := (2 : Real)) (by norm_num) (1/2 : Real)
  have he : ∀ x : Real, weight.eval (x/2+1/2) *
      (CAS12Rodrigues.shifted n).eval (x/2+1/2) =
      (1+x^2)*CAS12Affine.conventionalLift n x := by
    intro x
    simp only [weight, eval_add, eval_one, eval_pow, eval_sub, eval_mul,
      eval_ofNat, eval_X, CAS12Affine.conventionalLift,
      CAS12Rodrigues.shifted, CAS12Affine.shifted]
    congr 1 <;> ring
  simp_rw [he] at h
  norm_num only [show (-1 : Real)/2+1/2 = 0 by norm_num,
    show (1 : Real)/2+1/2 = 1 by norm_num, smul_eq_mul] at h
  simp_rw [standardLift, show ∀ x : Real,
    (1+x^2)*((-1 : Real)^n * CAS12Affine.conventionalLift n x) =
    (-1 : Real)^n*((1+x^2)*CAS12Affine.conventionalLift n x) by intro x; ring]
  rw [intervalIntegral.integral_const_mul, h]

theorem weighted_high (n : Nat) (hn : 3 ≤ n) :
    (∫ x in (-1 : Real)..1, (1+x^2)*standardLift n x) = 0 := by
  have hd : weight.natDegree ≤ 2 := by
    unfold weight
    compute_degree
  have hz := CAS12Rodrigues.shifted_orthogonal_lower_degree n weight
    (lt_of_le_of_lt hd (by omega))
  rw [MeasureTheory.integral_Icc_eq_integral_Ioc,
    ← intervalIntegral.integral_of_le (show (0 : Real) ≤ 1 by norm_num)] at hz
  rw [weighted_affine, hz]
  ring

theorem weighted_zero :
    (3/8 : Real) * (∫ x in (-1 : Real)..1, (1+x^2)*standardLift 0 x) = 1 := by
  simp_rw [standardLift_zero, mul_one]
  rw [intervalIntegral.integral_add]
  · norm_num [integral_pow]
  · exact continuous_const.intervalIntegrable _ _
  · exact (continuous_id.pow 2).intervalIntegrable _ _

theorem weighted_one :
    (3/8 : Real) * (∫ x in (-1 : Real)..1, (1+x^2)*standardLift 1 x) = 0 := by
  simp_rw [standardLift_one, show ∀ x : Real, (1+x^2)*x = x+x^3 by intro x; ring]
  rw [intervalIntegral.integral_add]
  · norm_num [integral_pow, integral_id]
  · exact continuous_id.intervalIntegrable _ _
  · exact (continuous_id.pow 3).intervalIntegrable _ _

theorem weighted_two :
    (3/8 : Real) * (∫ x in (-1 : Real)..1, (1+x^2)*standardLift 2 x) = 1/10 := by
  simp_rw [standardLift_two,
    show ∀ x : Real, (1+x^2)*((3*x^2-1)/2) = (3/2 : Real)*x^4+x^2-(1/2 : Real) by
      intro x; ring]
  rw [intervalIntegral.integral_sub, intervalIntegral.integral_add,
    intervalIntegral.integral_const_mul]
  · norm_num [integral_pow]
  all_goals apply Continuous.intervalIntegrable; fun_prop

theorem weighted_thomson_moment (n : Nat) :
    (3/8 : Real) * (∫ x in (-1 : Real)..1, (1+x^2)*standardLift n x) =
    if n = 0 then 1 else if n = 2 then 1/10 else 0 := by
  rcases n with _ | n
  · simpa using weighted_zero
  rcases n with _ | n
  · simpa using weighted_one
  rcases n with _ | n
  · simpa using weighted_two
  rw [weighted_high _ (by omega)]
  simp

end CAS12WeightedMoment

#check CAS12WeightedMoment.weighted_thomson_moment
#print axioms CAS12WeightedMoment.weighted_thomson_moment
#print axioms CAS12WeightedMoment.weighted_affine
#print axioms CAS12WeightedMoment.weighted_high
#print axioms CAS12WeightedMoment.weighted_zero
#print axioms CAS12WeightedMoment.weighted_one
#print axioms CAS12WeightedMoment.weighted_two

