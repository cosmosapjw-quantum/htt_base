import Mathlib
import Mathlib.Analysis.SpecialFunctions.Integrals.Basic

/-!
CAS-16-C03, Lean axis. The following propositions state the exact contracted
finite scalar problem. The declarations are definitions, not proofs or axioms.
The normalized spherical integral retains the fixed nonnegative square-root
branch through `Real.sqrt`.
-/

namespace CAS16C03

open Real
open scoped Interval

private noncomputable def innerRad : ℝ := (5 - 2 * Real.sqrt (10 / 7)) / 9
private noncomputable def outerRad : ℝ := (5 + 2 * Real.sqrt (10 / 7)) / 9

/-- Explicit five-node Gauss-Legendre abscissae in the frozen order. -/
noncomputable def gl5Node : Fin 5 → ℝ
  | ⟨0, _⟩ => 0
  | ⟨1, _⟩ => Real.sqrt innerRad
  | ⟨2, _⟩ => -Real.sqrt innerRad
  | ⟨3, _⟩ => Real.sqrt outerRad
  | ⟨4, _⟩ => -Real.sqrt outerRad

/-- Explicit five-node Gauss-Legendre weights in the frozen order. -/
noncomputable def gl5Weight : Fin 5 → ℝ
  | ⟨0, _⟩ => 128 / 225
  | ⟨1, _⟩ => (322 + 13 * Real.sqrt 70) / 900
  | ⟨2, _⟩ => (322 + 13 * Real.sqrt 70) / 900
  | ⟨3, _⟩ => (322 - 13 * Real.sqrt 70) / 900
  | ⟨4, _⟩ => (322 - 13 * Real.sqrt 70) / 900

noncomputable def azimuth (n : ℕ) (j : Fin n) : ℝ := 2 * Real.pi * (j.val : ℝ) / n

noncomputable def sphereX (μ φ : ℝ) : ℝ := Real.sqrt (1 - μ ^ 2) * Real.cos φ
noncomputable def sphereY (μ φ : ℝ) : ℝ := Real.sqrt (1 - μ ^ 2) * Real.sin φ
noncomputable def sphereZ (μ : ℝ) : ℝ := μ

noncomputable def monomial (a b c : ℕ) (μ φ : ℝ) : ℝ :=
  sphereX μ φ ^ a * sphereY μ φ ^ b * sphereZ μ ^ c

/-- The exact normalized GL5 times Nphi9 rule of the contract. -/
noncomputable def productRule (a b c : ℕ) : ℝ :=
  (1 / 2 : ℝ) * ∑ r : Fin 5, gl5Weight r *
    ((1 / 9 : ℝ) * ∑ j : Fin 9, monomial a b c (gl5Node r) (azimuth 9 j))

/-- The normalized spherical integral in the declared chart and measure. -/
noncomputable def sphereMean (a b c : ℕ) : ℝ :=
  (1 / (4 * Real.pi) : ℝ) *
    ∫ μ in (-1 : ℝ)..1, ∫ φ in (0 : ℝ)..(2 * Real.pi), monomial a b c μ φ

/-- Full finite monomial obligation, with natural exponents and total degree at most eight. -/
noncomputable def fullMonomialClaim : Prop :=
  ∀ a b c : ℕ, a + b + c ≤ 8 → productRule a b c = sphereMean a b c

private noncomputable def gl4InnerRad : ℝ := (3 - 2 * Real.sqrt (6 / 5)) / 7
private noncomputable def gl4OuterRad : ℝ := (3 + 2 * Real.sqrt (6 / 5)) / 7

noncomputable def gl4Node : Fin 4 → ℝ
  | ⟨0, _⟩ => Real.sqrt gl4InnerRad
  | ⟨1, _⟩ => -Real.sqrt gl4InnerRad
  | ⟨2, _⟩ => Real.sqrt gl4OuterRad
  | ⟨3, _⟩ => -Real.sqrt gl4OuterRad

noncomputable def gl4Weight : Fin 4 → ℝ
  | ⟨0, _⟩ => (18 + Real.sqrt 30) / 36
  | ⟨1, _⟩ => (18 + Real.sqrt 30) / 36
  | ⟨2, _⟩ => (18 - Real.sqrt 30) / 36
  | ⟨3, _⟩ => (18 - Real.sqrt 30) / 36

/-- The unnormalized radial GL4 failure witness. -/
noncomputable def radialFailureClaim : Prop :=
  (∑ r : Fin 4, gl4Weight r * gl4Node r ^ 8) -
    (∫ μ in (-1 : ℝ)..1, μ ^ 8) = -(128 / 11025 : ℝ)

/-- The normalized eight-point azimuth failure witness. -/
noncomputable def azimuthFailureClaim : Prop :=
  ((1 / 8 : ℝ) * ∑ j : Fin 8, Real.cos (azimuth 8 j) ^ 8) -
    ((1 / (2 * Real.pi) : ℝ) *
      ∫ φ in (0 : ℝ)..(2 * Real.pi), Real.cos φ ^ 8) = (1 / 128 : ℝ)

theorem azimuthIntegral :
    (∫ φ in (0:ℝ)..(2*Real.pi), Real.cos φ ^8) = 35*Real.pi/64 := by
  norm_num [integral_cos_pow, integral_cos_sq]
  ring

theorem azimuthGrid :
    (1/8:ℝ) * ∑ j : Fin 8, Real.cos (azimuth 8 j)^8 = 9/32 := by
  norm_num [Fin.sum_univ_eight, azimuth]
  rw [show 2 * π / 8 = π / 4 by ring,
      show 2 * π * 2 / 8 = π / 2 by ring,
      show 2 * π * 3 / 8 = π - π / 4 by ring,
      show 2 * π * 4 / 8 = π by ring,
      show 2 * π * 5 / 8 = π + π / 4 by ring,
      show 2 * π * 6 / 8 = π + π / 2 by ring,
      show 2 * π * 7 / 8 = 2 * π - π / 4 by ring]
  simp [cos_pi_sub, cos_add, cos_two_pi_sub, cos_pi_div_four, cos_pi_div_two, cos_pi]
  have h2 : (Real.sqrt (2:ℝ))^2 = 2 := Real.sq_sqrt (by norm_num)
  have hpow : (Real.sqrt (2:ℝ) / 2)^8 = (1/16:ℝ) := by
    calc
      (Real.sqrt (2:ℝ) / 2)^8 = ((Real.sqrt (2:ℝ))^2 / 4)^4 := by ring
      _ = (1/2:ℝ)^4 := by rw [h2]; ring
      _ = 1/16 := by norm_num
  norm_num [hpow]

theorem azimuthFailure : azimuthFailureClaim := by
  unfold azimuthFailureClaim
  rw [azimuthGrid, azimuthIntegral]
  have hp : Real.pi ≠ 0 := ne_of_gt Real.pi_pos
  field_simp
  ring

end CAS16C03

namespace CAS16C03

theorem radialFailure : radialFailureClaim := by
  have h6 : (Real.sqrt (6 / 5 : ℝ)) ^ 2 = 6 / 5 := Real.sq_sqrt (by norm_num)
  have h30 : (Real.sqrt (30 : ℝ)) ^ 2 = 30 := Real.sq_sqrt (by norm_num)
  have hrel : Real.sqrt (30 : ℝ) = 5 * Real.sqrt (6 / 5 : ℝ) := by
    nlinarith [Real.sqrt_nonneg (30 : ℝ), Real.sqrt_nonneg (6 / 5 : ℝ)]
  have hi : 0 ≤ gl4InnerRad := by
    unfold gl4InnerRad
    nlinarith [Real.sqrt_nonneg (6 / 5 : ℝ)]
  have ho : 0 ≤ gl4OuterRad := by
    unfold gl4OuterRad
    positivity
  have hi8 : (Real.sqrt gl4InnerRad) ^ 8 = gl4InnerRad ^ 4 := by
    rw [show 8 = 2 * 4 by norm_num, pow_mul, Real.sq_sqrt hi]
  have ho8 : (Real.sqrt gl4OuterRad) ^ 8 = gl4OuterRad ^ 4 := by
    rw [show 8 = 2 * 4 by norm_num, pow_mul, Real.sq_sqrt ho]
  unfold radialFailureClaim
  rw [integral_pow]
  simp only [Fin.sum_univ_four, gl4Node, gl4Weight]
  have hnegi : (-Real.sqrt gl4InnerRad) ^ 8 = (Real.sqrt gl4InnerRad) ^ 8 := by ring
  have hnego : (-Real.sqrt gl4OuterRad) ^ 8 = (Real.sqrt gl4OuterRad) ^ 8 := by ring
  rw [hnegi, hnego, hi8, ho8]
  simp only [gl4InnerRad, gl4OuterRad]
  rw [hrel]
  nlinarith [h6]

end CAS16C03

namespace CAS16C03

theorem constantExact : productRule 0 0 0 = sphereMean 0 0 0 := by
  norm_num [productRule, sphereMean, monomial, Fin.sum_univ_five,
    gl5Weight]
  have hp : Real.pi ≠ 0 := ne_of_gt Real.pi_pos
  field_simp
  ring

end CAS16C03

namespace CAS16C03

/-- Highest even radial moment required by the fixed total-degree bound. -/
theorem gl5Mu8 :
    (∑ r : Fin 5, gl5Weight r * gl5Node r ^ 8) =
      (∫ μ in (-1 : ℝ)..1, μ ^ 8) := by
  have hs : (Real.sqrt (10 / 7 : ℝ)) ^ 2 = 10 / 7 := Real.sq_sqrt (by norm_num)
  have h70 : (Real.sqrt (70 : ℝ)) ^ 2 = 70 := Real.sq_sqrt (by norm_num)
  have hrel : Real.sqrt (70 : ℝ) = 7 * Real.sqrt (10 / 7 : ℝ) := by
    nlinarith [Real.sqrt_nonneg (70 : ℝ), Real.sqrt_nonneg (10 / 7 : ℝ)]
  have hi : 0 ≤ innerRad := by
    unfold innerRad
    nlinarith [Real.sqrt_nonneg (10 / 7 : ℝ)]
  have ho : 0 ≤ outerRad := by
    unfold outerRad
    positivity
  have hi8 : (Real.sqrt innerRad) ^ 8 = innerRad ^ 4 := by
    rw [show 8 = 2 * 4 by norm_num, pow_mul, Real.sq_sqrt hi]
  have ho8 : (Real.sqrt outerRad) ^ 8 = outerRad ^ 4 := by
    rw [show 8 = 2 * 4 by norm_num, pow_mul, Real.sq_sqrt ho]
  rw [integral_pow]
  simp only [Fin.sum_univ_five, gl5Node, gl5Weight]
  have hnegi : (-Real.sqrt innerRad) ^ 8 = (Real.sqrt innerRad) ^ 8 := by ring
  have hnego : (-Real.sqrt outerRad) ^ 8 = (Real.sqrt outerRad) ^ 8 := by ring
  rw [hnegi, hnego, hi8, ho8]
  simp only [innerRad, outerRad]
  rw [hrel]
  nlinarith [hs]

end CAS16C03

namespace CAS16C03

/-- Exact GL5 radial moments for every even power through degree eight. -/
theorem gl5EvenMoments (m : ℕ) (hm : m ≤ 4) :
    (∑ r : Fin 5, gl5Weight r * gl5Node r ^ (2 * m)) =
      (∫ μ in (-1 : ℝ)..1, μ ^ (2 * m)) := by
  have hs : (Real.sqrt (10 / 7 : ℝ)) ^ 2 = 10 / 7 := Real.sq_sqrt (by norm_num)
  have h70 : (Real.sqrt (70 : ℝ)) ^ 2 = 70 := Real.sq_sqrt (by norm_num)
  have hrel : Real.sqrt (70 : ℝ) = 7 * Real.sqrt (10 / 7 : ℝ) := by
    nlinarith [Real.sqrt_nonneg (70 : ℝ), Real.sqrt_nonneg (10 / 7 : ℝ)]
  have hi : 0 ≤ innerRad := by
    unfold innerRad
    nlinarith [Real.sqrt_nonneg (10 / 7 : ℝ)]
  have ho : 0 ≤ outerRad := by
    unfold outerRad
    positivity
  have hpowi : (Real.sqrt innerRad) ^ (2 * m) = innerRad ^ m := by
    rw [pow_mul, Real.sq_sqrt hi]
  have hpowo : (Real.sqrt outerRad) ^ (2 * m) = outerRad ^ m := by
    rw [pow_mul, Real.sq_sqrt ho]
  have hnegi : (-Real.sqrt innerRad) ^ (2 * m) = (Real.sqrt innerRad) ^ (2 * m) := by
    rw [pow_mul, pow_mul]
    congr 1
    ring
  have hnego : (-Real.sqrt outerRad) ^ (2 * m) = (Real.sqrt outerRad) ^ (2 * m) := by
    rw [pow_mul, pow_mul]
    congr 1
    ring
  rw [integral_pow]
  simp only [Fin.sum_univ_five, gl5Node, gl5Weight]
  rw [hnegi, hnego, hpowi, hpowo]
  simp only [innerRad, outerRad]
  rw [hrel]
  interval_cases m <;> norm_num at * <;> nlinarith [hs]

end CAS16C03

namespace CAS16C03

/-- The symmetric GL5 rule has exact odd radial moments, without a degree limit. -/
theorem gl5OddMoments (m : ℕ) :
    (∑ r : Fin 5, gl5Weight r * gl5Node r ^ (2 * m + 1)) =
      (∫ μ in (-1 : ℝ)..1, μ ^ (2 * m + 1)) := by
  have hneg (x : ℝ) : (-x) ^ (2 * m + 1) = -(x ^ (2 * m + 1)) := by
    calc
      (-x) ^ (2 * m + 1) = ((-x) ^ 2) ^ m * (-x) := by rw [pow_add, pow_mul, pow_one]
      _ = -((x ^ 2) ^ m * x) := by ring
      _ = -(x ^ (2 * m + 1)) := by rw [pow_add, pow_mul, pow_one]
  rw [integral_pow]
  simp only [Fin.sum_univ_five, gl5Node, gl5Weight]
  rw [hneg, hneg]
  have heven : (-1 : ℝ) ^ (2 * m + 2) = 1 := by
    rw [show 2 * m + 2 = 2 * (m + 1) by omega, pow_mul]
    norm_num
  rw [show 2 * m + 1 + 1 = 2 * m + 2 by omega, heven]
  simp

end CAS16C03

namespace CAS16C03

/-- The fixed GL5 rule integrates every radial monomial through degree eight. -/
theorem gl5PowerExact (k : ℕ) (hk : k ≤ 8) :
    (∑ r : Fin 5, gl5Weight r * gl5Node r ^ k) =
      (∫ μ in (-1 : ℝ)..1, μ ^ k) := by
  rcases Nat.even_or_odd k with ⟨m, hm⟩ | ⟨m, hm⟩
  · have hkm : k = 2 * m := by omega
    subst k
    simpa [two_mul] using gl5EvenMoments m (by omega)
  · have hkm : k = 2 * m + 1 := by omega
    subst k
    simpa [two_mul] using gl5OddMoments m

end CAS16C03
