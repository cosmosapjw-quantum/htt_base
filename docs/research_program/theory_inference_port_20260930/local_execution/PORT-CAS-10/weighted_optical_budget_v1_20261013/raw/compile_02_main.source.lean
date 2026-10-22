import Mathlib

/-!
# P10-A (PORT-CAS-10): stress-gap body and weighted optical budget

Sources (see SOURCE_RECOVERY.md):
* `htt/src/common/typefree_physical_budgets.py` (`stress_gap_budget`, `weak_response_budget`)
* `typefree_loop2_20260928/source/ADJUDICATED_AMENDMENTS_KO.md` (TF-P2, TF-W1)
* GR-CAS-04 `completion_20261003/lean/Proof.lean` (velocity-jet encoding, rate identity),
  whose definitions are re-declared below verbatim and cited, not re-claimed.

Not claimed: universal MES anchor, physical stress provider, full PORT-CAS-10,
scientific admission.
-/

namespace P10A

open MeasureTheory Set intervalIntegral Matrix
open scoped Interval

/-! ## W1: B* = c d* / δ* -/

noncomputable def Bstar (c dstar deltastar : ℝ) : ℝ := c * dstar / deltastar

theorem W1_Bstar_pos {c dstar deltastar : ℝ} (hc : 0 < c) (hd : 0 < dstar)
    (hδ : 0 < deltastar) : 0 < Bstar c dstar deltastar := by
  unfold Bstar
  positivity

theorem W1_python_fixture : Bstar 2 2 4 = 1 := by
  norm_num [Bstar]

/-! ## Velocity-jet encoding (GR-CAS-04, cited) -/

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

def accel (c : ℝ) (q : Arr) (i : Fin 3) : ℝ := c * q 0 i

/-- Frobenius-orthonormal STF five-vector coordinates of `sigma`. -/
noncomputable def stf (q : Arr) : Fin 5 → ℝ :=
  ![(sigma q 0 0 - sigma q 1 1) * (√2 / 2), sigma q 2 2 * (√6 / 2),
    sigma q 0 1 * √2, sigma q 0 2 * √2, sigma q 1 2 * √2]

/-- Coordinate order (theta, sigma1..5, omega1..3, A1..3). -/
noncomputable def channel (c : ℝ) (q : Arr) : Fin 12 → ℝ :=
  ![theta q, stf q 0, stf q 1, stf q 2, stf q 3, stf q 4,
    omega q 0, omega q 1, omega q 2, accel c q 0, accel c q 1, accel c q 2]

noncomputable def baseWeight (c : ℝ) : Fin 12 → ℝ :=
  ![1/3, 1, 1, 1, 1, 1, 2, 2, 2, (c^2)⁻¹, (c^2)⁻¹, (c^2)⁻¹]

noncomputable def qWeight (c B : ℝ) : Fin 12 → ℝ := fun i => baseWeight c i / B ^ 2

noncomputable def Qmat (c B : ℝ) : Matrix (Fin 12) (Fin 12) ℝ := Matrix.diagonal (qWeight c B)

structure StressGapPremise where
  c : ℝ
  dstar : ℝ
  deltastar : ℝ
  hc : 0 < c
  hd : 0 < dstar
  hδ : 0 < deltastar
  D : Arr
  gap : Fin 3 → ℝ
  jet : Arr
  eigenbranch : ∀ μ i, gap i * jet μ i = -c * D μ i
  gap_lower : ∀ i, deltastar ≤ |gap i|
  deriv_bound : Real.sqrt (∑ μ : Fin 4, ∑ i : Fin 3, (D μ i) ^ 2) ≤ dstar

/-! ## W2: Q positivity, quadratic form, body -/

theorem W2a_Q_entries_pos {c B : ℝ} (hc : 0 < c) (hB : 0 < B) :
    ∀ i, 0 < qWeight c B i := by
  intro i
  unfold qWeight
  apply div_pos _ (pow_pos hB 2)
  fin_cases i <;> simp [baseWeight] <;> positivity

private theorem sq_half_sqrt2 (x : ℝ) : (x * (√2 / 2)) ^ 2 = x ^ 2 / 2 := by
  rw [mul_pow, div_pow, Real.sq_sqrt (by norm_num : (0:ℝ) ≤ 2)]
  ring

private theorem sq_half_sqrt6 (x : ℝ) : (x * (√6 / 2)) ^ 2 = x ^ 2 * (3 / 2) := by
  rw [mul_pow, div_pow, Real.sq_sqrt (by norm_num : (0:ℝ) ≤ 6)]
  ring

private theorem sq_sqrt2 (x : ℝ) : (x * √2) ^ 2 = 2 * x ^ 2 := by
  rw [mul_pow, Real.sq_sqrt (by norm_num : (0:ℝ) ≤ 2)]
  ring

theorem W2b_stf_frobenius (q : Arr) :
    ∑ k : Fin 5, (stf q k) ^ 2 = ∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j) ^ 2 := by
  have e : ∑ k : Fin 5, (stf q k) ^ 2 =
      (sigma q 0 0 - sigma q 1 1) ^ 2 / 2 + (sigma q 2 2) ^ 2 * (3 / 2)
        + 2 * (sigma q 0 1) ^ 2 + 2 * (sigma q 0 2) ^ 2 + 2 * (sigma q 1 2) ^ 2 := by
    have h0 : stf q 0 = (sigma q 0 0 - sigma q 1 1) * (√2 / 2) := rfl
    have h1 : stf q 1 = sigma q 2 2 * (√6 / 2) := rfl
    have h2 : stf q 2 = sigma q 0 1 * √2 := rfl
    have h3 : stf q 3 = sigma q 0 2 * √2 := rfl
    have h4 : stf q 4 = sigma q 1 2 * √2 := rfl
    rw [Fin.sum_univ_five, h0, h1, h2, h3, h4, sq_half_sqrt2, sq_half_sqrt6, sq_sqrt2,
      sq_sqrt2, sq_sqrt2]
    ring
  rw [e]
  simp [Fin.sum_univ_three, sigma, theta, Fin.sum_univ_succ]
  ring

/-- Re-statement of GR-CAS-04 `rate_four_by_three` (cited). -/
private theorem rate_four_by_three (c : ℝ) (q : Arr) (hc : c ≠ 0) :
    (theta q) ^ 2 / 3 + (∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j) ^ 2) +
      2 * (∑ i : Fin 3, (omega q i) ^ 2) +
      (∑ i : Fin 3, (accel c q i) ^ 2) / c ^ 2 =
      ∑ μ : Fin 4, ∑ i : Fin 3, (q μ i) ^ 2 := by
  simp [theta, sigma, omega, skew, accel, Fin.sum_univ_succ]
  field_simp
  ring

theorem W2c_channel_rate (c : ℝ) (q : Arr) (hc : c ≠ 0) :
    ∑ i : Fin 12, baseWeight c i * (channel c q i) ^ 2 =
      ∑ μ : Fin 4, ∑ i : Fin 3, (q μ i) ^ 2 := by
  rw [← rate_four_by_three c q hc, ← W2b_stf_frobenius q]
  simp [Fin.sum_univ_succ, baseWeight, channel, Fin.sum_univ_five]
  ring

theorem W2d_Q_quadratic_form (c B : ℝ) (q : Arr) (hc : c ≠ 0) :
    channel c q ⬝ᵥ (Qmat c B *ᵥ channel c q) =
      (∑ μ : Fin 4, ∑ i : Fin 3, (q μ i) ^ 2) / B ^ 2 := by
  rw [← W2c_channel_rate c q hc, Finset.sum_div]
  simp only [dotProduct, Qmat, Matrix.mulVec_diagonal, qWeight]
  apply Finset.sum_congr rfl
  intro i _
  ring

private theorem component_gap_bound {δ g d : ℝ} (hδ : 0 < δ) (hg : δ ≤ |g|) :
    d ^ 2 / g ^ 2 ≤ d ^ 2 / δ ^ 2 := by
  have hgsq : δ ^ 2 ≤ g ^ 2 := by
    have h0 : 0 ≤ δ := le_of_lt hδ
    have := pow_le_pow_left₀ h0 hg 2
    rwa [sq_abs] at this
  have hδsq : 0 < δ ^ 2 := pow_pos hδ 2
  exact div_le_div_of_nonneg_left (sq_nonneg d) hδsq hgsq

theorem W2e_stress_gap_body (P : StressGapPremise) :
    channel P.c P.jet ⬝ᵥ (Qmat P.c (Bstar P.c P.dstar P.deltastar) *ᵥ channel P.c P.jet) ≤ 1 := by
  have hc0 : P.c ≠ 0 := ne_of_gt P.hc
  have hB : 0 < Bstar P.c P.dstar P.deltastar := W1_Bstar_pos P.hc P.hd P.hδ
  rw [W2d_Q_quadratic_form _ _ _ hc0, div_le_one (pow_pos hB 2)]
  have hgap0 : ∀ i, P.gap i ≠ 0 := by
    intro i hz
    have := P.gap_lower i
    rw [hz, abs_zero] at this
    exact absurd P.hδ (not_lt.mpr this)
  have hjet : ∀ μ i, (P.jet μ i) ^ 2 = P.c ^ 2 * ((P.D μ i) ^ 2 / (P.gap i) ^ 2) := by
    intro μ i
    have h1 : P.jet μ i = -P.c * P.D μ i / P.gap i := by
      rw [eq_div_iff (hgap0 i), mul_comm]
      exact P.eigenbranch μ i
    rw [h1]
    field_simp
  have hsumD : ∑ μ : Fin 4, ∑ i : Fin 3, (P.D μ i) ^ 2 ≤ P.dstar ^ 2 := by
    have hx : 0 ≤ ∑ μ : Fin 4, ∑ i : Fin 3, (P.D μ i) ^ 2 := by positivity
    have := pow_le_pow_left₀ (Real.sqrt_nonneg _) P.deriv_bound 2
    rwa [Real.sq_sqrt hx] at this
  calc ∑ μ : Fin 4, ∑ i : Fin 3, (P.jet μ i) ^ 2
      = ∑ μ : Fin 4, ∑ i : Fin 3, P.c ^ 2 * ((P.D μ i) ^ 2 / (P.gap i) ^ 2) := by
        simp only [hjet]
    _ ≤ ∑ μ : Fin 4, ∑ i : Fin 3, P.c ^ 2 * ((P.D μ i) ^ 2 / P.deltastar ^ 2) := by
        apply Finset.sum_le_sum; intro μ _
        apply Finset.sum_le_sum; intro i _
        exact mul_le_mul_of_nonneg_left (component_gap_bound P.hδ (P.gap_lower i))
          (sq_nonneg _)
    _ = P.c ^ 2 * (∑ μ : Fin 4, ∑ i : Fin 3, (P.D μ i) ^ 2) / P.deltastar ^ 2 := by
        simp only [Fin.sum_univ_succ, Fin.sum_univ_zero]
        ring
    _ ≤ P.c ^ 2 * P.dstar ^ 2 / P.deltastar ^ 2 := by
        apply div_le_div_of_nonneg_right _ (le_of_lt (pow_pos P.hδ 2))
        exact mul_le_mul_of_nonneg_left hsumD (sq_nonneg _)
    _ = (Bstar P.c P.dstar P.deltastar) ^ 2 := by
        unfold Bstar
        ring

/-! ## W3: product differentiation and integration by parts -/

section Weak

variable {V E : Type*} [NormedAddCommGroup V] [NormedSpace ℝ V]
  [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]

theorem W3a_product_derivative {w w' : ℝ → ℝ} {m m' : ℝ → E} {t : ℝ}
    (hw : HasDerivAt w (w' t) t) (hm : HasDerivAt m (m' t) t) :
    HasDerivAt (fun x => w x • m x) (w' t • m t + w t • m' t) t := by
  have := hw.smul hm
  rw [add_comm] at this
  exact this

theorem W3b_ibp {a b : ℝ} {w w' : ℝ → ℝ} {m m' : ℝ → E}
    (hw : ∀ t ∈ [[a, b]], HasDerivAt w (w' t) t) (hm : ∀ t ∈ [[a, b]], HasDerivAt m (m' t) t)
    (hw' : IntervalIntegrable w' volume a b) (hm' : IntervalIntegrable m' volume a b) :
    ∫ t in a..b, w t • m' t = (w b • m b - w a • m a) - ∫ t in a..b, w' t • m t := by
  have hcw : ContinuousOn w [[a, b]] := fun t ht => (hw t ht).continuousAt.continuousWithinAt
  have hcm : ContinuousOn m [[a, b]] := fun t ht => (hm t ht).continuousAt.continuousWithinAt
  have i1 : IntervalIntegrable (fun t => w' t • m t) volume a b := hw'.smul_continuousOn hcm
  have i2 : IntervalIntegrable (fun t => w t • m' t) volume a b := hm'.continuousOn_smul hcw
  have hftc : ∫ t in a..b, (w' t • m t + w t • m' t) = w b • m b - w a • m a :=
    integral_eq_sub_of_hasDerivAt (fun t ht => W3a_product_derivative (hw t ht) (hm t ht))
      (i1.add i2)
  rw [integral_add i1 i2] at hftc
  rw [← hftc]
  abel

theorem W3c_ibp_absolutelyContinuous {a b : ℝ} {w m : ℝ → ℝ}
    (hw : AbsolutelyContinuousOnInterval w a b) (hm : AbsolutelyContinuousOnInterval m a b) :
    ∫ t in a..b, w t * deriv m t = (w b * m b - w a * m a) - ∫ t in a..b, deriv w t * m t :=
  AbsolutelyContinuousOnInterval.integral_mul_deriv_eq_deriv_mul hw hm

/-! ## W4: K_w identity -/

noncomputable def Kw (a b : ℝ) (w : ℝ → ℝ) (A : ℝ → V →L[ℝ] E) (k : ℝ → V) : E :=
  ∫ t in a..b, w t • A t (k t)

theorem W4a_Kw_identity {a b : ℝ} {w w' : ℝ → ℝ} {m m' s : ℝ → E}
    {A : ℝ → V →L[ℝ] E} {k : ℝ → V}
    (hw : ∀ t ∈ [[a, b]], HasDerivAt w (w' t) t) (hm : ∀ t ∈ [[a, b]], HasDerivAt m (m' t) t)
    (hw' : IntervalIntegrable w' volume a b) (hm' : IntervalIntegrable m' volume a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → m' t + A t (k t) = s t) :
    Kw a b w A k = (∫ t in a..b, w t • s t) + (∫ t in a..b, w' t • m t)
      - (w b • m b - w a • m a) := by
  have hcw : ContinuousOn w [[a, b]] := fun t ht => (hw t ht).continuousAt.continuousWithinAt
  have hcongr : Kw a b w A k = ∫ t in a..b, (w t • s t - w t • m' t) := by
    unfold Kw
    apply intervalIntegral.integral_congr_ae
    filter_upwards [hbal] with t ht hmem
    have hA : A t (k t) = s t - m' t := by
      rw [← ht hmem]; abel
    rw [hA, smul_sub]
  rw [hcongr, integral_sub (hs.continuousOn_smul hcw) (hm'.continuousOn_smul hcw),
    W3b_ibp hw hm hw' hm']
  abel

theorem W4b_Kw_identity_AC {a b : ℝ} {w m s : ℝ → ℝ} {A : ℝ → V →L[ℝ] ℝ} {k : ℝ → V}
    (hw : AbsolutelyContinuousOnInterval w a b) (hm : AbsolutelyContinuousOnInterval m a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → deriv m t + A t (k t) = s t) :
    Kw a b w A k = (∫ t in a..b, w t * s t) + (∫ t in a..b, deriv w t * m t)
      - (w b * m b - w a * m a) := by
  have hcongr : Kw a b w A k = ∫ t in a..b, (w t * s t - w t * deriv m t) := by
    unfold Kw
    apply intervalIntegral.integral_congr_ae
    filter_upwards [hbal] with t ht hmem
    have hA : A t (k t) = s t - deriv m t := by
      rw [← ht hmem]; ring
    rw [hA, smul_eq_mul, mul_sub]
  rw [hcongr, integral_sub (hs.continuousOn_mul hw.continuousOn)
    (hm.intervalIntegrable_deriv.continuousOn_mul hw.continuousOn),
    W3c_ibp_absolutelyContinuous hw hm]
  ring

/-! ## W5: remainder budget using the finite k bound -/

theorem W5a_remainder_budget {a b t0 L Mk : ℝ} (hab : a ≤ b) {w : ℝ → ℝ}
    {Ahat dA : ℝ → V →L[ℝ] E} {k : ℝ → V}
    (hk_lip : ∀ᵐ t, t ∈ Ioc a b → ‖k t - k t0‖ ≤ L * |t - t0|)
    (hk_bd : ∀ᵐ t, t ∈ Ioc a b → ‖k t‖ ≤ Mk)
    (hA_int : IntervalIntegrable (fun t => w t • Ahat t) volume a b)
    (hAk_int : IntervalIntegrable (fun t => w t • Ahat t (k t)) volume a b)
    (hdAk_int : IntervalIntegrable (fun t => w t • dA t (k t)) volume a b)
    (hV_int : IntervalIntegrable (fun t => |w t| * ‖Ahat t‖ * |t - t0|) volume a b)
    (hP_int : IntervalIntegrable (fun t => |w t| * ‖dA t‖) volume a b) :
    ‖(∫ t in a..b, w t • Ahat t) (k t0) - Kw a b w (fun t => Ahat t + dA t) k‖
      ≤ L * (∫ t in a..b, |w t| * ‖Ahat t‖ * |t - t0|)
        + Mk * (∫ t in a..b, |w t| * ‖dA t‖) := by
  have hA0_int : IntervalIntegrable (fun t => (w t • Ahat t) (k t0)) volume a b :=
    ⟨hA_int.1.apply_continuousLinearMap _, hA_int.2.apply_continuousLinearMap _⟩
  have h1 : (∫ t in a..b, w t • Ahat t) (k t0) = ∫ t in a..b, (w t • Ahat t) (k t0) :=
    ContinuousLinearMap.intervalIntegral_apply hA_int (k t0)
  have h2 : Kw a b w (fun t => Ahat t + dA t) k =
      (∫ t in a..b, w t • Ahat t (k t)) + ∫ t in a..b, w t • dA t (k t) := by
    unfold Kw
    rw [← integral_add hAk_int hdAk_int]
    apply integral_congr
    intro t _
    simp only [ContinuousLinearMap.add_apply, smul_add]
  have h3 : (∫ t in a..b, (w t • Ahat t) (k t0)) - ∫ t in a..b, w t • Ahat t (k t) =
      ∫ t in a..b, w t • Ahat t (k t0 - k t) := by
    rw [← integral_sub hA0_int hAk_int]
    apply integral_congr
    intro t _
    simp only [ContinuousLinearMap.smul_apply, map_sub, smul_sub]
  have bound1 : ‖∫ t in a..b, w t • Ahat t (k t0 - k t)‖ ≤
      ∫ t in a..b, L * (|w t| * ‖Ahat t‖ * |t - t0|) := by
    apply norm_integral_le_of_norm_le hab _ (hV_int.const_mul L)
    filter_upwards [hk_lip] with t ht hmem
    have hk := ht hmem
    rw [norm_sub_rev] at hk
    calc ‖w t • Ahat t (k t0 - k t)‖ = |w t| * ‖Ahat t (k t0 - k t)‖ := by
          rw [norm_smul, Real.norm_eq_abs]
      _ ≤ |w t| * (‖Ahat t‖ * ‖k t0 - k t‖) :=
          mul_le_mul_of_nonneg_left ((Ahat t).le_opNorm _) (abs_nonneg _)
      _ ≤ |w t| * (‖Ahat t‖ * (L * |t - t0|)) :=
          mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left hk (norm_nonneg _))
            (abs_nonneg _)
      _ = L * (|w t| * ‖Ahat t‖ * |t - t0|) := by ring
  have bound2 : ‖∫ t in a..b, w t • dA t (k t)‖ ≤
      ∫ t in a..b, Mk * (|w t| * ‖dA t‖) := by
    apply norm_integral_le_of_norm_le hab _ (hP_int.const_mul Mk)
    filter_upwards [hk_bd] with t ht hmem
    have hk := ht hmem
    calc ‖w t • dA t (k t)‖ = |w t| * ‖dA t (k t)‖ := by
          rw [norm_smul, Real.norm_eq_abs]
      _ ≤ |w t| * (‖dA t‖ * ‖k t‖) :=
          mul_le_mul_of_nonneg_left ((dA t).le_opNorm _) (abs_nonneg _)
      _ ≤ |w t| * (‖dA t‖ * Mk) :=
          mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left hk (norm_nonneg _))
            (abs_nonneg _)
      _ = Mk * (|w t| * ‖dA t‖) := by ring
  rw [intervalIntegral.integral_const_mul] at bound1 bound2
  rw [h1, h2, ← sub_sub, h3]
  exact (norm_sub_le _ _).trans (add_le_add bound1 bound2)

theorem W5b_weighted_optical_budget {a b t0 L Mk εnum : ℝ} (hab : a ≤ b)
    {w w' : ℝ → ℝ} {m m' s : ℝ → E} {Ahat dA : ℝ → V →L[ℝ] E} {k : ℝ → V}
    (hw : ∀ t ∈ [[a, b]], HasDerivAt w (w' t) t) (hm : ∀ t ∈ [[a, b]], HasDerivAt m (m' t) t)
    (hw' : IntervalIntegrable w' volume a b) (hm' : IntervalIntegrable m' volume a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → m' t + (Ahat t + dA t) (k t) = s t)
    (hk_lip : ∀ᵐ t, t ∈ Ioc a b → ‖k t - k t0‖ ≤ L * |t - t0|)
    (hk_bd : ∀ᵐ t, t ∈ Ioc a b → ‖k t‖ ≤ Mk)
    (hA_int : IntervalIntegrable (fun t => w t • Ahat t) volume a b)
    (hAk_int : IntervalIntegrable (fun t => w t • Ahat t (k t)) volume a b)
    (hdAk_int : IntervalIntegrable (fun t => w t • dA t (k t)) volume a b)
    (hV_int : IntervalIntegrable (fun t => |w t| * ‖Ahat t‖ * |t - t0|) volume a b)
    (hP_int : IntervalIntegrable (fun t => |w t| * ‖dA t‖) volume a b)
    (Iws Iwpm Ea Eb : E)
    (hnum : ‖(Iws + Iwpm - (Eb - Ea)) -
        ((∫ t in a..b, w t • s t) + (∫ t in a..b, w' t • m t) - (w b • m b - w a • m a))‖
          ≤ εnum) :
    ‖(∫ t in a..b, w t • Ahat t) (k t0) - (Iws + Iwpm - (Eb - Ea))‖
      ≤ L * (∫ t in a..b, |w t| * ‖Ahat t‖ * |t - t0|)
        + Mk * (∫ t in a..b, |w t| * ‖dA t‖) + εnum := by
  have hK := W4a_Kw_identity (A := fun t => Ahat t + dA t) hw hm hw' hm' hs hbal
  have hR := W5a_remainder_budget hab hk_lip hk_bd hA_int hAk_int hdAk_int hV_int hP_int
  have hN : ‖Kw a b w (fun t => Ahat t + dA t) k - (Iws + Iwpm - (Eb - Ea))‖ ≤ εnum := by
    rw [hK, norm_sub_rev]; exact hnum
  exact (norm_sub_le_norm_sub_add_norm_sub _ _ _).trans (add_le_add hR hN)

theorem W5c_weighted_optical_budget_AC {a b t0 L Mk εnum : ℝ} (hab : a ≤ b)
    {w m s : ℝ → ℝ} {Ahat dA : ℝ → V →L[ℝ] ℝ} {k : ℝ → V}
    (hw : AbsolutelyContinuousOnInterval w a b) (hm : AbsolutelyContinuousOnInterval m a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → deriv m t + (Ahat t + dA t) (k t) = s t)
    (hk_lip : ∀ᵐ t, t ∈ Ioc a b → ‖k t - k t0‖ ≤ L * |t - t0|)
    (hk_bd : ∀ᵐ t, t ∈ Ioc a b → ‖k t‖ ≤ Mk)
    (hA_int : IntervalIntegrable (fun t => w t • Ahat t) volume a b)
    (hAk_int : IntervalIntegrable (fun t => w t • Ahat t (k t)) volume a b)
    (hdAk_int : IntervalIntegrable (fun t => w t • dA t (k t)) volume a b)
    (hV_int : IntervalIntegrable (fun t => |w t| * ‖Ahat t‖ * |t - t0|) volume a b)
    (hP_int : IntervalIntegrable (fun t => |w t| * ‖dA t‖) volume a b)
    (Iws Iwpm Ea Eb : ℝ)
    (hnum : |(Iws + Iwpm - (Eb - Ea)) -
        ((∫ t in a..b, w t * s t) + (∫ t in a..b, deriv w t * m t) - (w b * m b - w a * m a))|
          ≤ εnum) :
    |(∫ t in a..b, w t • Ahat t) (k t0) - (Iws + Iwpm - (Eb - Ea))|
      ≤ L * (∫ t in a..b, |w t| * ‖Ahat t‖ * |t - t0|)
        + Mk * (∫ t in a..b, |w t| * ‖dA t‖) + εnum := by
  have hK := W4b_Kw_identity_AC (A := fun t => Ahat t + dA t) hw hm hs hbal
  have hR := W5a_remainder_budget hab hk_lip hk_bd hA_int hAk_int hdAk_int hV_int hP_int
  rw [Real.norm_eq_abs] at hR
  have hN : |Kw a b w (fun t => Ahat t + dA t) k - (Iws + Iwpm - (Eb - Ea))| ≤ εnum := by
    rw [hK, abs_sub_comm]; exact hnum
  exact (abs_sub_le _ _ _).trans (add_le_add hR hN)

end Weak

/-! ## W6: negative controls -/

theorem W6a_no_finite_radius_without_k_bound (C : ℝ) : ∃ κ : ℝ,
    (∫ t in (0:ℝ)..1, |(1:ℝ)| * ‖(0 : ℝ →L[ℝ] ℝ)‖ * |t - 0|) = 0 ∧
    (∫ t in (0:ℝ)..1, |(1:ℝ)| * ‖ContinuousLinearMap.id ℝ ℝ‖) = 1 ∧
    C < ‖(∫ t in (0:ℝ)..1, (1:ℝ) • (0 : ℝ →L[ℝ] ℝ)) κ -
        Kw 0 1 (fun _ => (1:ℝ)) (fun _ => (0 : ℝ →L[ℝ] ℝ) + ContinuousLinearMap.id ℝ ℝ)
          (fun _ => κ)‖ := by
  refine ⟨|C| + 1, by simp, by simp [ContinuousLinearMap.norm_id], ?_⟩
  simp only [Kw, one_smul, zero_add, ContinuousLinearMap.id_apply,
    intervalIntegral.integral_const, smul_eq_mul]
  simp only [intervalIntegral.integral_zero, ContinuousLinearMap.zero_apply]
  norm_num
  rw [abs_of_pos (by positivity : (0:ℝ) < |C| + 1)]
  linarith [le_abs_self C]

theorem W6b_endpoint_term_needed :
    (∫ t in (0:ℝ)..1, (1:ℝ) • (1:ℝ)) ≠ -(∫ t in (0:ℝ)..1, (0:ℝ) • t) := by
  simp

theorem W6c_endpoint_sign :
    (∀ t : ℝ, (1:ℝ) + (-(ContinuousLinearMap.id ℝ ℝ)) (1:ℝ) = (0:ℝ)) ∧
    Kw 0 1 (fun _ => (1:ℝ)) (fun _ => -(ContinuousLinearMap.id ℝ ℝ)) (fun _ => (1:ℝ)) =
      (∫ t in (0:ℝ)..1, (1:ℝ) • (0:ℝ)) + (∫ t in (0:ℝ)..1, (0:ℝ) • t)
        - ((1:ℝ) • (1:ℝ) - (1:ℝ) • (0:ℝ)) ∧
    Kw 0 1 (fun _ => (1:ℝ)) (fun _ => -(ContinuousLinearMap.id ℝ ℝ)) (fun _ => (1:ℝ)) ≠
      (∫ t in (0:ℝ)..1, (1:ℝ) • (0:ℝ)) + (∫ t in (0:ℝ)..1, (0:ℝ) • t)
        + ((1:ℝ) • (1:ℝ) - (1:ℝ) • (0:ℝ)) := by
  refine ⟨fun _ => by simp, ?_, ?_⟩
  · simp [Kw]
  · simp [Kw]
    norm_num

end P10A
