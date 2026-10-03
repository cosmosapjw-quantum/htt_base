import Mathlib

namespace GRSTATCAS04

open Finset

abbrev Arr := Fin 4 → Fin 3 → ℝ

def theta (q : Arr) : ℝ := ∑ i : Fin 3, q i.succ i
noncomputable def sigma (q : Arr) (i j : Fin 3) : ℝ :=
  (q i.succ j + q j.succ i) / 2 - (if i = j then theta q / 3 else 0)
noncomputable def skew (q : Arr) (i j : Fin 3) : ℝ :=
  (q i.succ j - q j.succ i) / 2
noncomputable def omega (q : Arr) : Fin 3 → ℝ
  | 0 => skew q 1 2
  | 1 => skew q 2 0
  | 2 => skew q 0 1

theorem spatial_orthogonal_decomposition (q : Arr) :
    (theta q)^2 / 3 + (∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j)^2) +
      2 * (∑ i : Fin 3, (omega q i)^2) =
      ∑ i : Fin 3, ∑ j : Fin 3, (q i.succ j)^2 := by
  simp [theta, sigma, omega, skew, Fin.sum_univ_succ]
  ring

def accel (c : ℝ) (q : Arr) (i : Fin 3) : ℝ := c * q 0 i

theorem rate_four_by_three (c : ℝ) (q : Arr) (hc : c ≠ 0) :
    (theta q)^2 / 3 + (∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j)^2) +
      2 * (∑ i : Fin 3, (omega q i)^2) +
      (∑ i : Fin 3, (accel c q i)^2) / c^2 =
      ∑ μ : Fin 4, ∑ i : Fin 3, (q μ i)^2 := by
  rw [spatial_orthogonal_decomposition]
  simp [Fin.sum_univ_succ, accel]
  field_simp
  ring

noncomputable def eigenRate (c : ℝ) (d : Arr) (gap : Fin 3 → ℝ) : Arr :=
  fun μ i => -c * d μ i / gap i

theorem weighted_rate (c : ℝ) (d : Arr) (gap : Fin 3 → ℝ)
    (hc : c ≠ 0) :
    (theta (eigenRate c d gap))^2 / 3 +
    (∑ i : Fin 3, ∑ j : Fin 3, (sigma (eigenRate c d gap) i j)^2) +
    2 * (∑ i : Fin 3, (omega (eigenRate c d gap) i)^2) +
    (∑ i : Fin 3, (accel c (eigenRate c d gap) i)^2) / c^2 =
    c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / (gap i)^2) := by
  rw [rate_four_by_three c _ hc]
  simp [eigenRate, Fin.sum_univ_succ]
  ring

theorem gap_square_lower {δ g : ℝ} (hδ : 0 < δ) (hg : δ ≤ |g|) : δ^2 ≤ g^2 := by
  have h0 : 0 ≤ |g| := abs_nonneg g
  have hs : δ^2 ≤ |g|^2 := by nlinarith
  rwa [sq_abs] at hs

theorem component_gap_bound {δ g d : ℝ} (hδ : 0 < δ) (hg : δ ≤ |g|) :
    d^2 / g^2 ≤ d^2 / δ^2 := by
  have hgn : g ≠ 0 := by
    intro hz
    simp [hz] at hg
    linarith
  have hgsq : 0 < g^2 := sq_pos_of_ne_zero hgn
  have hδsq : 0 < δ^2 := sq_pos_of_pos hδ
  apply (div_le_div_iff₀ hgsq hδsq).2
  nlinarith [mul_nonneg (sq_nonneg d) (sub_nonneg.mpr (gap_square_lower hδ hg))]

theorem component_gap_eq_iff {δ g d : ℝ} (hδ : 0 < δ) (hg : δ ≤ |g|) :
    d^2 / g^2 = d^2 / δ^2 ↔ d = 0 ∨ |g| = δ := by
  have hgn : g ≠ 0 := by
    intro hz
    simp [hz] at hg
    linarith
  have hδn : δ ≠ 0 := ne_of_gt hδ
  constructor
  · intro heq
    by_cases hd : d = 0
    · exact Or.inl hd
    · right
      have hcross : d^2 * δ^2 = d^2 * g^2 :=
        (div_eq_div_iff (pow_ne_zero 2 hgn) (pow_ne_zero 2 hδn)).mp heq
      have hdiff : g^2 = δ^2 := by
        have hmul : d^2 * (δ^2 - g^2) = 0 := by nlinarith
        rcases mul_eq_zero.mp hmul with hzero | hzero
        · exact False.elim ((pow_ne_zero 2 hd) hzero)
        · linarith
      nlinarith [sq_abs g, abs_nonneg g]
  · rintro (rfl | habs)
    · simp
    · have hsq : g^2 = δ^2 := by nlinarith [sq_abs g]
      rw [hsq]

theorem signed_gap_sum_bound (d : Arr) (gap : Fin 3 → ℝ) (δ : ℝ)
    (hδ : 0 < δ) (hg : ∀ i, δ ≤ |gap i|) :
    (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / (gap i)^2) ≤
      (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / δ^2) := by
  apply Finset.sum_le_sum
  intro μ _
  apply Finset.sum_le_sum
  intro i _
  exact component_gap_bound hδ (hg i)

theorem signed_gap_sum_eq_iff (d : Arr) (gap : Fin 3 → ℝ) (δ : ℝ)
    (hδ : 0 < δ) (hg : ∀ i, δ ≤ |gap i|) :
    (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / (gap i)^2) =
      (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / δ^2) ↔
      ∀ μ : Fin 4, ∀ i : Fin 3, d μ i = 0 ∨ |gap i| = δ := by
  constructor
  · intro h μ i
    have hμ : (∑ j : Fin 3, (d μ j)^2 / (gap j)^2) =
        (∑ j : Fin 3, (d μ j)^2 / δ^2) :=
      (Finset.sum_eq_sum_iff_of_le (fun ν _ =>
        Finset.sum_le_sum (fun j _ => component_gap_bound hδ (hg j)))).mp h μ (Finset.mem_univ μ)
    have hi : (d μ i)^2 / (gap i)^2 = (d μ i)^2 / δ^2 :=
      (Finset.sum_eq_sum_iff_of_le (fun j _ => component_gap_bound hδ (hg j))).mp hμ i (Finset.mem_univ i)
    exact (component_gap_eq_iff hδ (hg i)).mp hi
  · intro h
    apply Finset.sum_congr rfl
    intro μ _
    apply Finset.sum_congr rfl
    intro i _
    exact (component_gap_eq_iff hδ (hg i)).mpr (h μ i)

end GRSTATCAS04
