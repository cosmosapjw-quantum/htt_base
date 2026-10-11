import RadialBridge
import AngularBridge

/-!
The Cartesian bridge for CAS-16-C03.  This file retains the actual iterated
interval integral in `sphereMean`; angular and radial moments enter only after
the integrand has been factored from the definitions.
-/

namespace CAS16C03

open scoped Interval

private noncomputable def radialFactor (a b c : ℕ) (μ : ℝ) : ℝ :=
  Real.sqrt (1 - μ ^ 2) ^ (a + b) * μ ^ c

private noncomputable def angularFactor (a b : ℕ) (φ : ℝ) : ℝ :=
  Real.cos φ ^ a * Real.sin φ ^ b

private noncomputable def angularGrid (a b : ℕ) : ℝ :=
  (1 / 9 : ℝ) * ∑ j : Fin 9, angularFactor a b (azimuth 9 j)

private noncomputable def angularMean (a b : ℕ) : ℝ :=
  (1 / (2 * Real.pi) : ℝ) *
    ∫ φ in (0 : ℝ)..(2 * Real.pi), angularFactor a b φ

private theorem monomial_factor (a b c : ℕ) (μ φ : ℝ) :
    monomial a b c μ φ = radialFactor a b c μ * angularFactor a b φ := by
  simp only [monomial, sphereX, sphereY, sphereZ, radialFactor,
    angularFactor, mul_pow, pow_add]
  ring

private theorem grid_factor (a b c : ℕ) (μ : ℝ) :
    (1 / 9 : ℝ) * ∑ j : Fin 9, monomial a b c μ (azimuth 9 j) =
      radialFactor a b c μ * angularGrid a b := by
  simp_rw [monomial_factor]
  simp only [angularGrid, ← Finset.mul_sum]
  ring

private theorem angular_integral_factor (a b c : ℕ) (μ : ℝ) :
    (∫ φ in (0 : ℝ)..(2 * Real.pi), monomial a b c μ φ) =
      radialFactor a b c μ *
        (∫ φ in (0 : ℝ)..(2 * Real.pi), angularFactor a b φ) := by
  simp_rw [monomial_factor]
  exact intervalIntegral.integral_const_mul _ _

private theorem radialFactor_integrable (a b c : ℕ) :
    IntervalIntegrable (radialFactor a b c) MeasureTheory.volume (-1 : ℝ) 1 := by
  apply Continuous.intervalIntegrable
  unfold radialFactor
  fun_prop

/-- A definitional product-rule reduction. -/
theorem productRule_as_radial_angular (a b c : ℕ) :
    productRule a b c =
      (1 / 2 : ℝ) * ∑ r : Fin 5,
        gl5Weight r * (radialFactor a b c (gl5Node r) * angularGrid a b) := by
  unfold productRule
  simp_rw [grid_factor]

/-- The normalized sphere integral, still as an actual radial interval integral. -/
theorem sphereMean_as_radial_angular (a b c : ℕ) :
    sphereMean a b c =
      (1 / 2 : ℝ) *
        ∫ μ in (-1 : ℝ)..1, radialFactor a b c μ * angularMean a b := by
  unfold sphereMean angularMean
  simp_rw [angular_integral_factor]
  have hpoint (μ : ℝ) :
      radialFactor a b c μ *
        ((1 / (2 * Real.pi) : ℝ) *
          ∫ φ in (0 : ℝ)..(2 * Real.pi), angularFactor a b φ) =
      (1 / (2 * Real.pi) : ℝ) *
        (radialFactor a b c μ *
          ∫ φ in (0 : ℝ)..(2 * Real.pi), angularFactor a b φ) := by ring
  simp_rw [hpoint, intervalIntegral.integral_const_mul]
  have hpi : Real.pi ≠ 0 := ne_of_gt Real.pi_pos
  field_simp
  have hcomm :
      (∫ μ in (-1 : ℝ)..1,
        radialFactor a b c μ *
          ∫ φ in (0 : ℝ)..(2 * Real.pi), angularFactor a b φ) =
      (∫ μ in (-1 : ℝ)..1,
        (∫ φ in (0 : ℝ)..(2 * Real.pi), angularFactor a b φ) *
          radialFactor a b c μ) := by
    apply intervalIntegral.integral_congr
    intro μ _
    ring
  rw [mul_comm (2 : ℝ) Real.pi] at hcomm
  nlinarith [hcomm]

private theorem grid_weighted_factor (a b c : ℕ) :
    (∑ r : Fin 5,
      gl5Weight r * (radialFactor a b c (gl5Node r) * angularGrid a b)) =
    (∑ r : Fin 5, gl5Weight r * radialFactor a b c (gl5Node r)) *
      angularGrid a b := by
  rw [Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro r _
  ring

private theorem radial_integral_factor (a b c : ℕ) :
    (∫ μ in (-1 : ℝ)..1, radialFactor a b c μ * angularMean a b) =
      (∫ μ in (-1 : ℝ)..1, radialFactor a b c μ) * angularMean a b := by
  exact intervalIntegral.integral_mul_const _ _

/-- The independent angular facts and the proved GL5 radial fact imply the
universal Cartesian statement without replacing the sphere integral by a
precomputed moment formula. -/
theorem full_of_angular_facts
    (hgrid : ∀ a b : ℕ, a + b ≤ 8 → angularGrid a b = angularMean a b)
    (hodd : ∀ a b : ℕ, a + b ≤ 8 → Odd (a + b) → angularGrid a b = 0) :
    fullMonomialClaim := by
  intro a b c hdegree
  have hab : a + b ≤ 8 := by omega
  rw [productRule_as_radial_angular, sphereMean_as_radial_angular,
    grid_weighted_factor, radial_integral_factor]
  rcases Nat.even_or_odd (a + b) with heven | hodd_degree
  · rw [hgrid a b hab]
    have hr := radialFactorExact a b c hdegree heven
    change (∑ r : Fin 5, gl5Weight r * radialFactor a b c (gl5Node r)) =
      (∫ μ in (-1 : ℝ)..1, radialFactor a b c μ) at hr
    rw [hr]
  · have hz := hodd a b hab hodd_degree
    have hzmean : angularMean a b = 0 := by
      rw [← hgrid a b hab]
      exact hz
    rw [hz, hzmean]
    ring

/-- Every Cartesian monomial of total degree at most eight is integrated exactly
by the explicit GL5 × Nphi9 product rule and the normalized spherical integral
as defined in `SphereQuadrature`. -/
theorem fullMonomialTheorem : fullMonomialClaim := by
  apply full_of_angular_facts
  · intro a b hdegree
    simpa [angularGrid, angularMean, angularFactor] using
      angularGridExact a b hdegree
  · intro a b hdegree hodd
    simpa [angularGrid, angularFactor] using
      angularOddGridZero a b hdegree hodd

end CAS16C03
