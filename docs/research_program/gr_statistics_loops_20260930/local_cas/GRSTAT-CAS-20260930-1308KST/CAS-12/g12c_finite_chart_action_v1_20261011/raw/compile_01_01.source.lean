import SphereQuadrature

namespace CAS16C03
open Complex
open scoped Interval

private noncomputable def zeta (k : ℕ) : ℂ :=
  Complex.exp (2 * (Real.pi : ℂ) * Complex.I * (k : ℂ) / 9)

theorem zeta_sum_zero (k : ℕ) (hk0 : 0 < k) (hk9 : k < 9) :
    (∑ j : Fin 9, zeta k ^ j.val) = 0 := by
  have hz_ne : zeta k ≠ 1 := by
    intro h
    have hd : 9 ∣ k :=
      (Complex.exp_two_pi_mul_I_mul_div_eq_one_iff (by norm_num : (9:ℕ) ≠ 0)).mp
        (by simpa [zeta] using h)
    omega
  have hz_pow : zeta k ^ 9 = 1 := by
    calc
      zeta k ^ 9 = Complex.exp ((9:ℕ) * (2 * (Real.pi : ℂ) * Complex.I * (k : ℂ) / 9)) := by
        rw [zeta, Complex.exp_nat_mul]
      _ = Complex.exp ((k:ℕ) * (2 * (Real.pi : ℂ) * Complex.I)) := by
        congr 1
        push_cast
        ring
      _ = (Complex.exp (2 * (Real.pi : ℂ) * Complex.I)) ^ k := by
        rw [Complex.exp_nat_mul]
      _ = 1 := by rw [Complex.exp_two_pi_mul_I]; simp
  rw [Fin.sum_univ_eq_sum_range, geom_sum_eq hz_ne, hz_pow]
  simp

theorem mode_integral_zero (k : ℕ) (hk0 : 0 < k) :
    (∫ φ in (0:ℝ)..(2*Real.pi),
      Complex.exp (((k:ℂ) * Complex.I) * (φ:ℂ))) = 0 := by
  have hc : ((k:ℂ) * Complex.I) ≠ 0 := by
    exact mul_ne_zero (by exact_mod_cast Nat.ne_of_gt hk0) Complex.I_ne_zero
  rw [integral_exp_mul_complex hc]
  have hendpoint : Complex.exp (((k:ℂ) * Complex.I) * ((2*Real.pi:ℝ):ℂ)) = 1 := by
    calc
      Complex.exp (((k:ℂ) * Complex.I) * ((2*Real.pi:ℝ):ℂ)) =
        Complex.exp ((k:ℕ) * (2 * (Real.pi:ℂ) * Complex.I)) := by
          congr 1
          push_cast
          ring
      _ = (Complex.exp (2 * (Real.pi:ℂ) * Complex.I)) ^ k := by rw [Complex.exp_nat_mul]
      _ = 1 := by rw [Complex.exp_two_pi_mul_I]; simp
  rw [hendpoint]
  norm_num

theorem positive_mode_grid_zero (k : ℕ) (hk0 : 0 < k) (hk9 : k < 9) :
    (∑ j : Fin 9,
      Complex.exp (((k:ℂ) * Complex.I) * ((azimuth 9 j : ℝ):ℂ))) = 0 := by
  have hpoint (j : Fin 9) :
      Complex.exp (((k:ℂ) * Complex.I) * ((azimuth 9 j : ℝ):ℂ)) =
        zeta k ^ j.val := by
    calc
      Complex.exp (((k:ℂ) * Complex.I) * ((azimuth 9 j : ℝ):ℂ)) =
        Complex.exp ((j.val:ℕ) * (2 * (Real.pi : ℂ) * Complex.I * (k:ℂ) / 9)) := by
          congr 1
          simp only [azimuth]
          push_cast
          ring
      _ = zeta k ^ j.val := by rw [zeta, Complex.exp_nat_mul]
  simp_rw [hpoint]
  exact zeta_sum_zero k hk0 hk9

end CAS16C03
