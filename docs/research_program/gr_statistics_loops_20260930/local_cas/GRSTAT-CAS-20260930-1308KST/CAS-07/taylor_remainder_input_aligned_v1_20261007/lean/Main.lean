import Mathlib

open MeasureTheory Set intervalIntegral

/-! Formal verification of the CAS-07 M02 scalar integral Taylor remainder.
The derivative witnesses are given on the full closed interval, including its endpoints.
The proof itself works on every subinterval `[0,s]` with `0 ≤ s ≤ L`. -/

namespace CAS07M02

variable (L s c M2 : ℝ) (Z Z1 Z2 : ℝ → ℝ)
variable (hL : 0 < L) (hs0 : 0 ≤ s) (hsL : s ≤ L) (hc : 0 < c) (hM2 : 0 ≤ M2)
variable (hZ : ∀ t ∈ Icc (0 : ℝ) L, HasDerivAt Z (Z1 t) t)
variable (hZ1 : ∀ t ∈ Icc (0 : ℝ) L, HasDerivAt Z1 (Z2 t) t)
variable (hZ2 : ContinuousOn Z2 (Icc (0 : ℝ) L))
variable (hZ2bound : ∀ t ∈ Icc (0 : ℝ) L, |Z2 t| ≤ M2)

private theorem segment {L s : ℝ} (hsL : s ≤ L) (t : ℝ)
    (ht : t ∈ Icc (0 : ℝ) s) : t ∈ Icc (0 : ℝ) L :=
  ⟨ht.1, ht.2.trans hsL⟩

private theorem z2_cont_segment {L s : ℝ} {Z2 : ℝ → ℝ} (hsL : s ≤ L)
    (hZ2 : ContinuousOn Z2 (Icc (0 : ℝ) L)) :
    ContinuousOn Z2 (Icc (0 : ℝ) s) :=
  hZ2.mono (fun t ht => segment hsL t ht)

private theorem z1_cont_segment {L s : ℝ} {Z1 Z2 : ℝ → ℝ} (hsL : s ≤ L)
    (hZ1 : ∀ t ∈ Icc (0 : ℝ) L, HasDerivAt Z1 (Z2 t) t) :
    ContinuousOn Z1 (Icc (0 : ℝ) s) :=
  fun t ht => (hZ1 t (segment hsL t ht)).continuousAt.continuousWithinAt

private theorem z1_integrable {L s : ℝ} {Z1 Z2 : ℝ → ℝ} (hs0 : 0 ≤ s)
    (hsL : s ≤ L) (hZ1 : ∀ t ∈ Icc (0 : ℝ) L, HasDerivAt Z1 (Z2 t) t) :
    IntervalIntegrable Z1 volume 0 s :=
  (z1_cont_segment hsL hZ1).intervalIntegrable_of_Icc hs0

private theorem z2_integrable {L s : ℝ} {Z2 : ℝ → ℝ} (hs0 : 0 ≤ s)
    (hsL : s ≤ L) (hZ2 : ContinuousOn Z2 (Icc (0 : ℝ) L)) :
    IntervalIntegrable Z2 volume 0 s :=
  (z2_cont_segment hsL hZ2).intervalIntegrable_of_Icc hs0

private theorem weight_integral (s M2 : ℝ) (hs0 : 0 ≤ s) :
    (∫ t in (0 : ℝ)..s, (s - t) * M2) = M2 * s ^ 2 / 2 := by
  rw [intervalIntegral.integral_mul_const]
  have hsfun : IntervalIntegrable (fun _ : ℝ => s) volume 0 s :=
    continuousOn_const.intervalIntegrable_of_Icc hs0
  have htfun : IntervalIntegrable (fun t : ℝ => t) volume 0 s :=
    continuous_id.continuousOn.intervalIntegrable_of_Icc hs0
  rw [intervalIntegral.integral_sub hsfun htfun]
  simp only [intervalIntegral.integral_const, smul_eq_mul, sub_zero, integral_id]
  norm_num
  ring

include hL hs0 hsL hc hM2 hZ hZ1 hZ2 hZ2bound

omit hL hc hM2 hZ2bound in theorem remainder_identity :
    Z s - Z 0 - s * Z1 0 = ∫ t in (0 : ℝ)..s, (s - t) * Z2 t := by
  have hFTC : (∫ t in (0 : ℝ)..s, Z1 t) = Z s - Z 0 :=
    intervalIntegral.integral_eq_sub_of_hasDerivAt
      (a := 0) (b := s) (f := Z) (f' := Z1)
      (by intro t ht; exact hZ t (segment hsL t (by simpa [uIcc_of_le hs0] using ht)))
      (z1_integrable hs0 hsL hZ1)
  have hIBP := intervalIntegral.integral_mul_deriv_eq_deriv_mul
    (a := 0) (b := s) (u := fun t : ℝ => s - t) (u' := fun _ : ℝ => -1)
    (v := Z1) (v' := Z2)
    (by intro t ht; simpa using (hasDerivAt_id' t).const_sub s)
    (by intro t ht; exact hZ1 t (segment hsL t (by simpa [uIcc_of_le hs0] using ht)))
    (ContinuousOn.intervalIntegrable_of_Icc hs0 (continuousOn_const : ContinuousOn (fun _ : ℝ => (-1 : ℝ)) (Icc 0 s)))
    (z2_integrable hs0 hsL hZ2)
  simp only [sub_self, zero_mul, sub_zero, neg_one_mul] at hIBP
  have hNeg : (∫ t in (0 : ℝ)..s, -Z1 t) = -(∫ t in (0 : ℝ)..s, Z1 t) := by
    exact integral_neg
  rw [hNeg, hFTC] at hIBP
  linarith

theorem remainder_identity_physical (Z0 H0 : ℝ) (hZ0 : Z0 = Z 0)
    (hH0 : H0 = c * Z1 0) :
    Z s - Z0 - H0 * s / c = ∫ t in (0 : ℝ)..s, (s - t) * Z2 t := by
  rw [hZ0, hH0]
  have hc0 : c ≠ 0 := ne_of_gt hc
  field_simp
  nlinarith [remainder_identity L s Z Z1 Z2 hs0 hsL hZ hZ1 hZ2]

theorem remainder_bound :
    |Z s - Z 0 - s * Z1 0| ≤ M2 * s ^ 2 / 2 := by
  rw [remainder_identity L s Z Z1 Z2 hs0 hsL hZ hZ1 hZ2]
  have hwcont : ContinuousOn (fun t : ℝ => (s - t) * Z2 t) (Icc 0 s) :=
    (continuousOn_const.sub continuous_id.continuousOn).mul
      (z2_cont_segment hsL hZ2)
  have habsint : IntervalIntegrable (fun t : ℝ => |(s - t) * Z2 t|) volume 0 s :=
    hwcont.abs.intervalIntegrable_of_Icc hs0
  have hweightint : IntervalIntegrable (fun t : ℝ => (s - t) * M2) volume 0 s :=
    ((continuousOn_const.sub continuous_id.continuousOn).mul continuousOn_const).intervalIntegrable_of_Icc hs0
  calc
    |∫ t in (0 : ℝ)..s, (s - t) * Z2 t|
        ≤ ∫ t in (0 : ℝ)..s, |(s - t) * Z2 t| :=
          intervalIntegral.abs_integral_le_integral_abs hs0
    _ ≤ ∫ t in (0 : ℝ)..s, (s - t) * M2 := by
          apply intervalIntegral.integral_mono_on hs0 habsint hweightint
          intro t ht
          rw [abs_mul, abs_of_nonneg (sub_nonneg.mpr ht.2)]
          exact mul_le_mul_of_nonneg_left (hZ2bound t (segment hsL t ht)) (sub_nonneg.mpr ht.2)
    _ = M2 * s ^ 2 / 2 := weight_integral s M2 hs0

theorem remainder_bound_physical (Z0 H0 : ℝ) (hZ0 : Z0 = Z 0)
    (hH0 : H0 = c * Z1 0) :
    |Z s - Z0 - H0 * s / c| ≤ M2 * s ^ 2 / 2 := by
  rw [remainder_identity_physical L s c M2 Z Z1 Z2 hL hs0 hsL hc hM2 hZ hZ1 hZ2 hZ2bound Z0 H0 hZ0 hH0]
  rw [← remainder_identity L s Z Z1 Z2 hs0 hsL hZ hZ1 hZ2]
  exact remainder_bound L s c M2 Z Z1 Z2 hL hs0 hsL hc hM2 hZ hZ1 hZ2 hZ2bound

end CAS07M02

#print axioms CAS07M02.remainder_identity
#print axioms CAS07M02.remainder_bound
#print axioms CAS07M02.remainder_identity_physical
#print axioms CAS07M02.remainder_bound_physical
