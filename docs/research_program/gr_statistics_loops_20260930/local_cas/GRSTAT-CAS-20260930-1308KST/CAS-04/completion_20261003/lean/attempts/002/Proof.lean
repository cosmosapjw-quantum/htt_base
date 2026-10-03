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

end GRSTATCAS04
