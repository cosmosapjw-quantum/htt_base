import Mathlib

open Polynomial

theorem rodrigues_endpoint_jets (n k : ℕ) (hk : k < n) :
    ((derivative^[k]) ((X : ℝ[X]) ^ n * (1 - X) ^ n)).eval 0 = 0 ∧
    ((derivative^[k]) ((X : ℝ[X]) ^ n * (1 - X) ^ n)).eval 1 = 0 := by
  have hnk : 0 < n - k := Nat.sub_pos_iff_lt.mpr hk
  have hne : n - k ≠ 0 := Nat.ne_of_gt hnk
  constructor
  · obtain ⟨r, hr⟩ :=
      pow_sub_dvd_iterate_derivative_of_pow_dvd (R := ℝ) k
        (dvd_mul_right ((X : ℝ[X]) ^ n) ((1 - X) ^ n))
    rw [hr, eval_mul, eval_pow]
    simp [hne]
  · obtain ⟨r, hr⟩ :=
      pow_sub_dvd_iterate_derivative_of_pow_dvd (R := ℝ) k
        (dvd_mul_left ((1 - X : ℝ[X]) ^ n) ((X : ℝ[X]) ^ n))
    rw [hr, eval_mul, eval_pow]
    simp [hne]

#check rodrigues_endpoint_jets
#print axioms rodrigues_endpoint_jets
