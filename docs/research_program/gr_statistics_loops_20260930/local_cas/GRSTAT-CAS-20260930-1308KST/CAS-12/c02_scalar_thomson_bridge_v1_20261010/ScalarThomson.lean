import Mathlib

/-!
CAS12-C02, independently authored from the frozen neutral inputs.
The scalar elastic phase kernel is 3 (1 + μ²) / (16 π).
The axisymmetric moment convention is p_l = 2π ∫[-1,1] P(μ) L_l(μ) dμ.
This file proves actual interval integrals, not a finite sampling rule.
The polynomial harmonic declarations below are L_0 through L_6.
-/

open MeasureTheory

namespace CAS12C02

noncomputable def kernel (μ : ℝ) : ℝ := 3 * (1 + μ ^ 2) / (16 * Real.pi)

noncomputable def legendre : Fin 7 → ℝ → ℝ
  | 0 => fun _ => 1
  | 1 => fun μ => μ
  | 2 => fun μ => (3 * μ ^ 2 - 1) / 2
  | 3 => fun μ => (5 * μ ^ 3 - 3 * μ) / 2
  | 4 => fun μ => (35 * μ ^ 4 - 30 * μ ^ 2 + 3) / 8
  | 5 => fun μ => (63 * μ ^ 5 - 70 * μ ^ 3 + 15 * μ) / 8
  | 6 => fun μ => (231 * μ ^ 6 - 315 * μ ^ 4 + 105 * μ ^ 2 - 5) / 16

noncomputable def moment (l : Fin 7) : ℝ :=
  2 * Real.pi * ∫ μ in (-1 : ℝ)..1, kernel μ * legendre l μ

theorem phase_expansion (μ : ℝ) :
    kernel μ = (1 / (4 * Real.pi)) *
      (legendre 0 μ + (5 : ℝ) * (1 / 10) * legendre 2 μ) := by
  unfold kernel legendre
  field_simp
  <;> ring

theorem reduced_moment (l : Fin 7) :
    moment l = (3 / 8 : ℝ) * ∫ μ in (-1 : ℝ)..1, (1 + μ ^ 2) * legendre l μ := by
  have hp : Real.pi ≠ 0 := Real.pi_ne_zero
  have heq : (fun μ => kernel μ * legendre l μ) =
      fun μ => (3 / (16 * Real.pi)) * ((1 + μ ^ 2) * legendre l μ) := by
    funext μ
    unfold kernel
    ring
  unfold moment
  rw [heq, intervalIntegral.integral_const_mul]
  field_simp
  <;> ring

private theorem integrable (l : Fin 7) :
    IntervalIntegrable (fun μ => (1 + μ ^ 2) * legendre l μ) volume (-1 : ℝ) 1 := by
  fin_cases l <;> simp only [legendre]
  all_goals apply Continuous.intervalIntegrable; fun_prop

-- Explicit polynomial primitives keep the first analytical step kernel checked.
open Polynomial in
noncomputable def primitivePoly : Fin 7 → ℝ[X]
  | 0 => X + C (1 / 3) * X ^ 3
  | 1 => C (1 / 2) * X ^ 2 + C (1 / 4) * X ^ 4
  | 2 => C (3 / 10) * X ^ 5 + C (1 / 3) * X ^ 3 - C (1 / 2) * X
  | 3 => C (5 / 12) * X ^ 6 + C (1 / 4) * X ^ 4 - C (3 / 4) * X ^ 2
  | 4 => C (5 / 8) * X ^ 7 + C (1 / 8) * X ^ 5 - C (9 / 8) * X ^ 3 + C (3 / 8) * X
  | 5 => C (63 / 64) * X ^ 8 - C (7 / 48) * X ^ 6 - C (55 / 32) * X ^ 4 + C (15 / 16) * X ^ 2
  | 6 => C (77 / 48) * X ^ 9 - C (3 / 4) * X ^ 7 - C (21 / 8) * X ^ 5 + C (25 / 12) * X ^ 3 - C (5 / 16) * X

noncomputable def primitive (l : Fin 7) (μ : ℝ) : ℝ := (primitivePoly l).eval μ

private theorem primitive_derivative (l : Fin 7) (μ : ℝ) :
    HasDerivAt (primitive l) ((1 + μ ^ 2) * legendre l μ) μ := by
  change HasDerivAt (fun x => (primitivePoly l).eval x) _ μ
  apply ((primitivePoly l).hasDerivAt μ).congr_deriv
  fin_cases l <;> simp [primitivePoly, legendre, Polynomial.derivative_mul,
    Polynomial.derivative_pow, Polynomial.derivative_sub, Polynomial.derivative_add]
  all_goals ring

theorem moment_integral (l : Fin 7) :
    moment l = (3 / 8 : ℝ) * (primitive l 1 - primitive l (-1)) := by
  rw [reduced_moment]
  congr 1
  exact intervalIntegral.integral_eq_sub_of_hasDerivAt
    (fun μ _ => primitive_derivative l μ) (integrable l)

theorem finite_harmonic_moments (l : Fin 7) :
    moment l = if l = 0 then 1 else if l = 2 then 1 / 10 else 0 := by
  rw [moment_integral]
  fin_cases l <;> norm_num [primitive, primitivePoly, Fin.ext_iff]

theorem monopole : moment 0 = 1 := by simpa using finite_harmonic_moments 0
theorem quadrupole : moment 2 = 1 / 10 := by simpa using finite_harmonic_moments 2
theorem remaining_declared (l : Fin 7) (h0 : l ≠ 0) (h2 : l ≠ 2) :
    moment l = 0 := by simp [finite_harmonic_moments, h0, h2]

#print axioms phase_expansion
#print axioms reduced_moment
#print axioms finite_harmonic_moments
#print axioms monopole
#print axioms quadrupole
#print axioms remaining_declared

end CAS12C02
