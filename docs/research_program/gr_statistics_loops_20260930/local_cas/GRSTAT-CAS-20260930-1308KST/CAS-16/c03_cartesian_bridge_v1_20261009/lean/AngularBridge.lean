import AngularModes

/-!
Angular part of the CAS-16-C03 Cartesian bridge.  The nine-point angular
grid has no alias in the nonzero Fourier band of absolute frequency at most
eight.  The negative-frequency facts below are obtained by conjugating the
already-proved positive-frequency facts.
-/

namespace CAS16C03

open Complex
open scoped Interval
open scoped ComplexConjugate

private noncomputable def positiveMode (k : ℕ) (φ : ℝ) : ℂ :=
  Complex.exp (((k : ℂ) * Complex.I) * (φ : ℂ))

private noncomputable def negativeMode (k : ℕ) (φ : ℝ) : ℂ :=
  Complex.exp (((-(k : ℂ)) * Complex.I) * (φ : ℂ))

private theorem negativeMode_eq_conj (k : ℕ) (φ : ℝ) :
    negativeMode k φ = conj (positiveMode k φ) := by
  unfold negativeMode positiveMode
  rw [← Complex.exp_conj]
  congr 1
  simp [mul_assoc]

theorem negative_mode_grid_zero (k : ℕ) (hk0 : 0 < k) (hk9 : k < 9) :
    (∑ j : Fin 9, negativeMode k (azimuth 9 j)) = 0 := by
  simp_rw [negativeMode_eq_conj]
  rw [← map_sum]
  change conj (∑ j : Fin 9,
    Complex.exp (((k : ℂ) * Complex.I) * ((azimuth 9 j : ℝ) : ℂ))) = 0
  rw [positive_mode_grid_zero k hk0 hk9]
  simp

theorem negative_mode_integral_zero (k : ℕ) (hk0 : 0 < k) :
    (∫ φ in (0 : ℝ)..(2 * Real.pi), negativeMode k φ) = 0 := by
  simp_rw [negativeMode_eq_conj]
  rw [show (∫ φ in (0 : ℝ)..(2 * Real.pi),
      conj (positiveMode k φ)) =
      conj (∫ φ in (0 : ℝ)..(2 * Real.pi), positiveMode k φ) by
        simp only [intervalIntegral, integral_conj]
        simp]
  change conj (∫ φ in (0 : ℝ)..(2 * Real.pi),
    Complex.exp (((k : ℂ) * Complex.I) * (φ : ℂ))) = 0
  rw [mode_integral_zero k hk0]
  simp

/-- Complex Fourier mode, with an integer rather than natural frequency. -/
private noncomputable def integerMode (k : ℤ) (φ : ℝ) : ℂ :=
  Complex.exp (((k : ℂ) * Complex.I) * (φ : ℂ))

theorem integer_mode_grid_zero (k : ℤ) (hk0 : k ≠ 0)
    (hk8 : k.natAbs ≤ 8) :
    (∑ j : Fin 9, integerMode k (azimuth 9 j)) = 0 := by
  rcases lt_or_gt_of_ne hk0 with hneg | hpos
  · let n : ℕ := (-k).toNat
    have hn0 : 0 < n := by omega
    have hn9 : n < 9 := by omega
    have hkn : k = -(n : ℤ) := by omega
    rw [hkn]
    simpa [integerMode, negativeMode] using negative_mode_grid_zero n hn0 hn9
  · let n : ℕ := k.toNat
    have hn0 : 0 < n := by omega
    have hn9 : n < 9 := by omega
    have hkn : k = (n : ℤ) := by omega
    rw [hkn]
    simpa [integerMode] using positive_mode_grid_zero n hn0 hn9

theorem integer_mode_integral_zero (k : ℤ) (hk0 : k ≠ 0) :
    (∫ φ in (0 : ℝ)..(2 * Real.pi), integerMode k φ) = 0 := by
  rcases lt_or_gt_of_ne hk0 with hneg | hpos
  · let n : ℕ := (-k).toNat
    have hn0 : 0 < n := by omega
    have hkn : k = -(n : ℤ) := by omega
    rw [hkn]
    simpa [integerMode, negativeMode] using negative_mode_integral_zero n hn0
  · let n : ℕ := k.toNat
    have hn0 : 0 < n := by omega
    have hkn : k = (n : ℤ) := by omega
    rw [hkn]
    simpa [integerMode] using mode_integral_zero n hn0

private def sign (s : Fin 2) : ℤ := if s = 0 then 1 else -1

private noncomputable def cosCoefficient (_s : Fin 2) : ℂ := 1 / 2
private noncomputable def sinCoefficient (s : Fin 2) : ℂ :=
  if s = 0 then 1 / (2 * Complex.I) else -(1 / (2 * Complex.I))

private theorem mode_one (φ : ℝ) :
    integerMode 1 φ = (Real.cos φ : ℂ) + (Real.sin φ : ℂ) * Complex.I := by
  unfold integerMode
  convert Complex.exp_mul_I (φ : ℂ) using 1
  · congr 1
    ring
  · simp

private theorem mode_neg_one (φ : ℝ) :
    integerMode (-1) φ = (Real.cos φ : ℂ) - (Real.sin φ : ℂ) * Complex.I := by
  have h : integerMode (-1) φ = conj (integerMode 1 φ) := by
    simpa [integerMode, negativeMode, positiveMode] using negativeMode_eq_conj 1 φ
  rw [h, mode_one]
  simp [← Complex.ofReal_cos, ← Complex.ofReal_sin, sub_eq_add_neg]

private theorem cos_as_two_modes (φ : ℝ) :
    (Real.cos φ : ℂ) =
      ∑ s : Fin 2, cosCoefficient s * integerMode (sign s) φ := by
  rw [Fin.sum_univ_two]
  norm_num [sign, cosCoefficient, mode_one, mode_neg_one]
  ring

private theorem sin_as_two_modes (φ : ℝ) :
    (Real.sin φ : ℂ) =
      ∑ s : Fin 2, sinCoefficient s * integerMode (sign s) φ := by
  rw [Fin.sum_univ_two]
  norm_num [sign, sinCoefficient, mode_one, mode_neg_one]
  simp [div_eq_mul_inv, Complex.inv_I]
  ring_nf
  simp [Complex.I_sq]

/-- Every integer frequency in the degree-eight band has the same normalized
nine-grid average and normalized interval integral. -/
theorem integer_mode_exact (k : ℤ) (hk8 : k.natAbs ≤ 8) :
    (1 / 9 : ℂ) * (∑ j : Fin 9, integerMode k (azimuth 9 j)) =
      (1 / (2 * (Real.pi : ℂ))) *
        ∫ φ in (0 : ℝ)..(2 * Real.pi), integerMode k φ := by
  by_cases hk : k = 0
  · subst k
    simp [integerMode]
    have hp : (Real.pi : ℂ) ≠ 0 := Complex.ofReal_ne_zero.mpr Real.pi_ne_zero
    field_simp
  · rw [integer_mode_grid_zero k hk hk8, integer_mode_integral_zero k hk]
    ring

private theorem integerMode_add (k l : ℤ) (φ : ℝ) :
    integerMode (k + l) φ = integerMode k φ * integerMode l φ := by
  unfold integerMode
  rw [show (((k + l : ℤ) : ℂ) * Complex.I) * (φ : ℂ) =
      ((k : ℂ) * Complex.I) * (φ : ℂ) +
      ((l : ℂ) * Complex.I) * (φ : ℂ) by push_cast; ring]
  exact Complex.exp_add _ _

private theorem integerMode_sum {ι : Type*} [DecidableEq ι]
    (s : Finset ι) (k : ι → ℤ) (φ : ℝ) :
    (∏ i ∈ s, integerMode (k i) φ) =
      integerMode (∑ i ∈ s, k i) φ := by
  induction s using Finset.induction with
  | empty => simp [integerMode]
  | @insert i s hi ih =>
      simp [hi, ih, integerMode_add]

private noncomputable def factorCoefficient (a b : ℕ)
    (i : Fin (a + b)) (s : Fin 2) : ℂ :=
  if i.val < a then cosCoefficient s else sinCoefficient s

private theorem factor_as_two_modes (a b : ℕ) (i : Fin (a + b)) (φ : ℝ) :
    (if i.val < a then (Real.cos φ : ℂ) else (Real.sin φ : ℂ)) =
      ∑ s : Fin 2, factorCoefficient a b i s * integerMode (sign s) φ := by
  unfold factorCoefficient
  split_ifs with hi
  · exact cos_as_two_modes φ
  · exact sin_as_two_modes φ

private theorem angular_product_as_factors (a b : ℕ) (φ : ℝ) :
    (Real.cos φ : ℂ) ^ a * (Real.sin φ : ℂ) ^ b =
      ∏ i : Fin (a + b),
        if i.val < a then (Real.cos φ : ℂ) else (Real.sin φ : ℂ) := by
  rw [Fin.prod_univ_add]
  simp [Fin.prod_const]

/-- A concrete finite Fourier expansion.  Each summand is a mode whose
frequency is the sum of exactly `a+b` signs, so it lies in `[-(a+b),a+b]`. -/
theorem angular_fourier_expansion (a b : ℕ) (φ : ℝ) :
    (Real.cos φ : ℂ) ^ a * (Real.sin φ : ℂ) ^ b =
      ∑ p ∈ Fintype.piFinset (fun _i : Fin (a + b) => (Finset.univ : Finset (Fin 2))),
        (∏ i : Fin (a + b), factorCoefficient a b i (p i)) *
          integerMode (∑ i : Fin (a + b), sign (p i)) φ := by
  rw [angular_product_as_factors]
  simp_rw [factor_as_two_modes]
  rw [Finset.prod_univ_sum]
  refine Finset.sum_congr rfl ?_
  intro p hp
  rw [Finset.prod_mul_distrib]
  congr 1
  exact integerMode_sum Finset.univ (fun i => sign (p i)) φ

theorem angular_frequency_bound (a b : ℕ)
    (p : Fin (a + b) → Fin 2) :
    (∑ i : Fin (a + b), sign (p i)).natAbs ≤ a + b := by
  have hlo (i : Fin (a + b)) : (-1 : ℤ) ≤ sign (p i) := by
    unfold sign
    split_ifs <;> omega
  have hhi (i : Fin (a + b)) : sign (p i) ≤ (1 : ℤ) := by
    unfold sign
    split_ifs <;> omega
  have hsumlo : ∑ _i : Fin (a + b), (-1 : ℤ) ≤
      ∑ i : Fin (a + b), sign (p i) :=
    Finset.sum_le_sum (fun i _ => hlo i)
  have hsumhi : ∑ i : Fin (a + b), sign (p i) ≤
      ∑ _i : Fin (a + b), (1 : ℤ) :=
    Finset.sum_le_sum (fun i _ => hhi i)
  simp only [Finset.sum_const, Finset.card_univ,
    Fintype.card_fin, nsmul_eq_mul] at hsumlo hsumhi
  omega

private theorem coefficient_mode_intervalIntegrable (c : ℂ) (k : ℤ) :
    IntervalIntegrable (fun φ : ℝ => c * integerMode k φ)
      MeasureTheory.volume 0 (2 * Real.pi) := by
  apply Continuous.intervalIntegrable
  unfold integerMode
  fun_prop

/-- Linear extension of the mode identity to an arbitrary finite sum of
frequencies in the alias-free band. -/
theorem finite_fourier_exact {ι : Type*} (s : Finset ι)
    (c : ι → ℂ) (k : ι → ℤ)
    (hk : ∀ i ∈ s, (k i).natAbs ≤ 8) :
    (1 / 9 : ℂ) *
      (∑ j : Fin 9, ∑ i ∈ s, c i * integerMode (k i) (azimuth 9 j)) =
    (1 / (2 * (Real.pi : ℂ))) *
      ∫ φ in (0 : ℝ)..(2 * Real.pi),
        ∑ i ∈ s, c i * integerMode (k i) φ := by
  have hint : ∀ i ∈ s, IntervalIntegrable
      (fun φ : ℝ => c i * integerMode (k i) φ)
      MeasureTheory.volume 0 (2 * Real.pi) := by
    intro i _
    exact coefficient_mode_intervalIntegrable (c i) (k i)
  rw [intervalIntegral.integral_finsetSum hint]
  simp_rw [intervalIntegral.integral_const_mul]
  rw [Finset.sum_comm]
  simp_rw [← Finset.mul_sum]
  rw [Finset.mul_sum, Finset.mul_sum]
  refine Finset.sum_congr rfl ?_
  intro i hi
  convert congrArg (fun z : ℂ => c i * z)
    (integer_mode_exact (k i) (hk i hi)) using 1 <;> ring

private theorem angular_complex_exact (a b : ℕ) (hdegree : a + b ≤ 8) :
    (1 / 9 : ℂ) *
      (∑ j : Fin 9,
        (Real.cos (azimuth 9 j) : ℂ) ^ a *
          (Real.sin (azimuth 9 j) : ℂ) ^ b) =
    (1 / (2 * (Real.pi : ℂ))) *
      ∫ φ in (0 : ℝ)..(2 * Real.pi),
        (Real.cos φ : ℂ) ^ a * (Real.sin φ : ℂ) ^ b := by
  let s := Fintype.piFinset
    (fun _i : Fin (a + b) => (Finset.univ : Finset (Fin 2)))
  let c (p : Fin (a + b) → Fin 2) :=
    ∏ i : Fin (a + b), factorCoefficient a b i (p i)
  let k (p : Fin (a + b) → Fin 2) :=
    ∑ i : Fin (a + b), sign (p i)
  have hk : ∀ p ∈ s, (k p).natAbs ≤ 8 := by
    intro p _
    exact (angular_frequency_bound a b p).trans hdegree
  have hexact := finite_fourier_exact s c k hk
  simpa only [s, c, k, ← angular_fourier_expansion] using hexact

/-- Normalized Nphi9 angular quadrature for every Cartesian angular factor of
total degree at most eight.  This compares the actual interval integral with
the actual nine-node sum; it is not a comparison of tabulated moments. -/
theorem angularGridExact (a b : ℕ) (hdegree : a + b ≤ 8) :
    (1 / 9 : ℝ) *
      (∑ j : Fin 9,
        Real.cos (azimuth 9 j) ^ a * Real.sin (azimuth 9 j) ^ b) =
    (1 / (2 * Real.pi) : ℝ) *
      ∫ φ in (0 : ℝ)..(2 * Real.pi),
        Real.cos φ ^ a * Real.sin φ ^ b := by
  have hc :
      (((1 / 9 : ℝ) *
        (∑ j : Fin 9,
          Real.cos (azimuth 9 j) ^ a * Real.sin (azimuth 9 j) ^ b)) : ℂ) =
      (((1 / (2 * Real.pi) : ℝ) *
        (∫ φ in (0 : ℝ)..(2 * Real.pi),
          Real.cos φ ^ a * Real.sin φ ^ b)) : ℂ) := by
    push_cast
    rw [← intervalIntegral.integral_ofReal]
    simpa [Complex.ofReal_cos, Complex.ofReal_sin] using
      angular_complex_exact a b hdegree
  exact Complex.ofReal_injective (by simpa only [Complex.ofReal_mul] using hc)

private theorem odd_frequency_nonzero (a b : ℕ)
    (hodd : Odd (a + b)) (p : Fin (a + b) → Fin 2) :
    (∑ i : Fin (a + b), sign (p i)) ≠ 0 := by
  intro hz
  have heach (i : Fin (a + b)) : sign (p i) % 2 = 1 := by
    unfold sign
    split_ifs <;> omega
  have hmod := Finset.sum_int_mod Finset.univ 2 (fun i : Fin (a + b) => sign (p i))
  simp_rw [heach] at hmod
  simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin,
    nsmul_eq_mul, mul_one] at hmod
  obtain ⟨m, hm⟩ := hodd
  omega

/-- An odd total angular degree contains only odd Fourier frequencies, hence
has zero nine-grid mean.  The same integral vanishes by `angularGridExact`. -/
theorem angularOddGridZero (a b : ℕ) (hdegree : a + b ≤ 8)
    (hodd : Odd (a + b)) :
    (1 / 9 : ℝ) *
      (∑ j : Fin 9,
        Real.cos (azimuth 9 j) ^ a * Real.sin (azimuth 9 j) ^ b) = 0 := by
  have hc :
      (1 / 9 : ℂ) *
        (∑ j : Fin 9,
          (Real.cos (azimuth 9 j) : ℂ) ^ a *
            (Real.sin (azimuth 9 j) : ℂ) ^ b) = 0 := by
    simp_rw [angular_fourier_expansion]
    rw [Finset.sum_comm]
    simp_rw [← Finset.mul_sum]
    have hzero (p : Fin (a + b) → Fin 2) :
        (∑ j : Fin 9,
          integerMode (∑ i : Fin (a + b), sign (p i)) (azimuth 9 j)) = 0 :=
      integer_mode_grid_zero _ (odd_frequency_nonzero a b hodd p)
        ((angular_frequency_bound a b p).trans hdegree)
    simp [hzero]
  have hcast :
      (((1 / 9 : ℝ) *
        (∑ j : Fin 9,
          Real.cos (azimuth 9 j) ^ a * Real.sin (azimuth 9 j) ^ b)) : ℂ) = 0 := by
    push_cast
    simpa [Complex.ofReal_cos, Complex.ofReal_sin] using hc
  exact Complex.ofReal_injective
    (by simpa only [Complex.ofReal_mul, Complex.ofReal_zero] using hcast)

end CAS16C03
