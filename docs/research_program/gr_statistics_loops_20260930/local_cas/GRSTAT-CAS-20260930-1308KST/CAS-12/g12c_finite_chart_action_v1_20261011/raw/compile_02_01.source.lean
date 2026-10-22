import SphereQuadrature

/-!
Radial half of the CAS16-C03 Cartesian bridge.  The square-root factor is
reduced to a polynomial only when its exponent is even.  The GL5 exactness
below is derived from the source theorem for powers through degree eight.
-/

namespace CAS16C03

open scoped Interval

private def radialPoly (m c : ℕ) (μ : ℝ) : ℝ :=
  (1 - μ ^ 2) ^ m * μ ^ c

private theorem radialPoly_succ (m c : ℕ) (μ : ℝ) :
    radialPoly (m + 1) c μ = radialPoly m c μ - radialPoly m (c + 2) μ := by
  simp only [radialPoly, pow_succ]
  ring

private theorem radialPoly_integrable (m c : ℕ) :
    IntervalIntegrable (radialPoly m c) MeasureTheory.volume (-1 : ℝ) 1 := by
  apply Continuous.intervalIntegrable
  unfold radialPoly
  fun_prop

/-- GL5 integrates the polynomial left after an even angular exponent. -/
theorem gl5RadialPolyExact (m c : ℕ) (hdeg : 2 * m + c ≤ 8) :
    (∑ r : Fin 5, gl5Weight r * radialPoly m c (gl5Node r)) =
      ∫ μ in (-1 : ℝ)..1, radialPoly m c μ := by
  induction m generalizing c with
  | zero =>
      simpa [radialPoly] using gl5PowerExact c (by omega)
  | succ m ih =>
      have hleft : 2 * m + c ≤ 8 := by omega
      have hright : 2 * m + (c + 2) ≤ 8 := by omega
      have hp := ih c hleft
      have hq := ih (c + 2) hright
      simp_rw [radialPoly_succ m c]
      simp only [mul_sub, Finset.sum_sub_distrib]
      rw [intervalIntegral.integral_sub
        (radialPoly_integrable m c) (radialPoly_integrable m (c + 2))]
      rw [hp, hq]

/-- On the spherical radial chart, an even square-root power is polynomial. -/
theorem sqrtRadialEven (m c : ℕ) (μ : ℝ) (hμ : -1 ≤ μ ∧ μ ≤ 1) :
    (Real.sqrt (1 - μ ^ 2)) ^ (2 * m) * μ ^ c = radialPoly m c μ := by
  have hnonneg : 0 ≤ 1 - μ ^ 2 := by nlinarith [hμ.1, hμ.2]
  rw [pow_mul, Real.sq_sqrt hnonneg]
  rfl

private theorem gl5Node_sq_le_one (r : Fin 5) : gl5Node r ^ 2 ≤ 1 := by
  have hs : 0 ≤ Real.sqrt (10 / 7 : ℝ) := Real.sqrt_nonneg _
  have hs2 : Real.sqrt (10 / 7 : ℝ) ^ 2 = 10 / 7 :=
    Real.sq_sqrt (by norm_num)
  have hroot : Real.sqrt (10 / 7 : ℝ) ≤ 2 := by nlinarith
  have hinner : 0 ≤ (5 - 2 * Real.sqrt (10 / 7 : ℝ)) / 9 := by
    nlinarith
  have houter : 0 ≤ (5 + 2 * Real.sqrt (10 / 7 : ℝ)) / 9 := by
    positivity
  have hi : (Real.sqrt ((5 - 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 =
      (5 - 2 * Real.sqrt (10 / 7 : ℝ)) / 9 := Real.sq_sqrt hinner
  have ho : (Real.sqrt ((5 + 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 =
      (5 + 2 * Real.sqrt (10 / 7 : ℝ)) / 9 := Real.sq_sqrt houter
  fin_cases r
  · norm_num [gl5Node]
  · change (Real.sqrt ((5 - 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 ≤ 1
    rw [hi]
    nlinarith
  · change (-Real.sqrt ((5 - 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 ≤ 1
    rw [show (-Real.sqrt ((5 - 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 =
      (Real.sqrt ((5 - 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 by ring]
    rw [hi]
    nlinarith
  · change (Real.sqrt ((5 + 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 ≤ 1
    rw [ho]
    nlinarith
  · change (-Real.sqrt ((5 + 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 ≤ 1
    rw [show (-Real.sqrt ((5 + 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 =
      (Real.sqrt ((5 + 2 * Real.sqrt (10 / 7 : ℝ)) / 9)) ^ 2 by ring]
    rw [ho]
    nlinarith

private theorem gl5Node_mem (r : Fin 5) :
    -1 ≤ gl5Node r ∧ gl5Node r ≤ 1 := by
  have hs := gl5Node_sq_le_one r
  constructor <;> nlinarith

/-- Radial exactness for every surviving even angular degree in the
total-degree-eight Cartesian family. Odd angular degrees are deliberately
excluded: their square-root radial factor need not be polynomial. -/
theorem radialFactorExact (a b c : ℕ) (hdegree : a + b + c ≤ 8)
    (heven : Even (a + b)) :
    (∑ r : Fin 5, gl5Weight r *
      ((Real.sqrt (1 - gl5Node r ^ 2)) ^ (a + b) * gl5Node r ^ c)) =
      ∫ μ in (-1 : ℝ)..1,
        (Real.sqrt (1 - μ ^ 2)) ^ (a + b) * μ ^ c := by
  rcases heven with ⟨m, hm⟩
  have hab : a + b = 2 * m := by omega
  have hdeg : 2 * m + c ≤ 8 := by omega
  calc
    (∑ r : Fin 5, gl5Weight r *
      ((Real.sqrt (1 - gl5Node r ^ 2)) ^ (a + b) * gl5Node r ^ c)) =
        ∑ r : Fin 5, gl5Weight r * radialPoly m c (gl5Node r) := by
          apply Finset.sum_congr rfl
          intro r _
          rw [hab, sqrtRadialEven m c (gl5Node r) (gl5Node_mem r)]
    _ = ∫ μ in (-1 : ℝ)..1, radialPoly m c μ :=
      gl5RadialPolyExact m c hdeg
    _ = ∫ μ in (-1 : ℝ)..1,
        (Real.sqrt (1 - μ ^ 2)) ^ (a + b) * μ ^ c := by
          symm
          apply intervalIntegral.integral_congr
          intro μ hμ
          rw [hab]
          have hbound : -1 ≤ μ ∧ μ ≤ 1 := by simpa using hμ
          exact sqrtRadialEven m c μ hbound

end CAS16C03
