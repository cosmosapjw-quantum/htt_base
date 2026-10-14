import G12DInterface
import PlanckIR

open MeasureTheory Set

noncomputable section
namespace G12D

private theorem positive_exp_sub_one {x : ℝ} (hx : 0 < x) :
    0 < Real.exp x - 1 := by
  have h := Real.add_one_le_exp x
  linarith

private theorem positive_occupation_denom {beta eta E : ℝ}
    (hb : 0 < beta) (he : eta ≤ 0) (hE : 0 < E) :
    0 < Real.exp (beta * E - eta) - 1 := by
  apply positive_exp_sub_one
  have : 0 < beta * E := mul_pos hb hE
  linarith

theorem weight_eq_occupation : weight_eq_occupation_type := by
  intro b E hb hE
  have hx : 0 < Real.exp (b * E) - 1 :=
    positive_exp_sub_one (mul_pos hb hE)
  have hn : Real.exp (b * E) - 1 ≠ 0 := ne_of_gt hx
  simp only [CAS12PlanckIR.weight, occupation, sub_zero]
  field_simp
  ring

theorem weight_nonneg : weight_nonneg_type := by
  intro b E
  unfold CAS12PlanckIR.weight
  positivity

private theorem exp_sub_one_sq_lower {x : ℝ} (hx : 0 < x) :
    x ^ 2 * Real.exp x ≤ (Real.exp x - 1) ^ 2 := by
  have hy : 0 ≤ x / 2 := by linarith
  have hs : x / 2 ≤ Real.sinh (x / 2) :=
    Real.self_le_sinh_iff.mpr hy
  rw [Real.sinh_eq] at hs
  have hmul := mul_le_mul_of_nonneg_right hs
    (show 0 ≤ 2 * Real.exp (x / 2) by positivity)
  have hinv : Real.exp (-(x / 2)) * Real.exp (x / 2) = 1 := by
    rw [← Real.exp_add]
    simp
  have hsq : Real.exp (x / 2) ^ 2 = Real.exp x := by
    rw [pow_two, ← Real.exp_add]
    congr 1
    ring
  have hlinear : x * Real.exp (x / 2) ≤ Real.exp x - 1 := by
    nlinarith [hmul]
  have hnonneg : 0 ≤ x * Real.exp (x / 2) := by positivity
  have hpow := (sq_le_sq₀ hnonneg (hnonneg.trans hlinear)).mpr hlinear
  nlinarith [hpow]

theorem weight_le_inv_sq : weight_le_inv_sq_type := by
  intro b E hb hE
  have hx : 0 < b * E := mul_pos hb hE
  have hd : 0 < Real.exp (b * E) - 1 := positive_exp_sub_one hx
  have hbound := exp_sub_one_sq_lower hx
  unfold CAS12PlanckIR.weight
  exact (div_le_div_iff₀ (sq_pos_of_pos hd) (sq_pos_of_pos hx)).mpr
    (by nlinarith)

private theorem weight_exp_neg_form (x : ℝ) (hx : 0 < x) :
    Real.exp x / (Real.exp x - 1) ^ 2 =
      Real.exp (-x) / (1 - Real.exp (-x)) ^ 2 := by
  have he : 0 < Real.exp x := Real.exp_pos x
  have hd : 0 < Real.exp x - 1 := positive_exp_sub_one hx
  rw [Real.exp_neg]
  field_simp

theorem weight_le_uv_bound : weight_le_uv_bound_type := by
  intro b E a hb ha hEa
  have hx : 0 < b * E := mul_pos hb (lt_of_lt_of_le ha hEa)
  have hy : 0 < b * a := mul_pos hb ha
  have hxy : b * a ≤ b * E := mul_le_mul_of_nonneg_left hEa (le_of_lt hb)
  let t := Real.exp (-(b * E))
  let u := Real.exp (-(b * a))
  have ht : 0 < t := Real.exp_pos _
  have hu : 0 < u := Real.exp_pos _
  have htu : t ≤ u := Real.exp_le_exp.mpr (neg_le_neg hxy)
  have hu1 : u < 1 := by
    dsimp [u]
    simpa only [Real.exp_zero] using (Real.exp_lt_exp.mpr (neg_lt_zero.mpr hy))
  have ht1 : t < 1 := lt_of_le_of_lt htu hu1
  have hden : (1 - u) ^ 2 ≤ (1 - t) ^ 2 :=
    (sq_le_sq₀ (by linarith) (by linarith)).mpr (by linarith)
  have hdiv : t / (1 - t) ^ 2 ≤ t / (1 - u) ^ 2 :=
    (div_le_div_iff₀ (sq_pos_of_pos (by linarith : 0 < 1 - t))
      (sq_pos_of_pos (by linarith : 0 < 1 - u))).mpr
      (mul_le_mul_of_nonneg_left hden (le_of_lt ht))
  simpa only [t, u, CAS12PlanckIR.weight,
    weight_exp_neg_form (b * E) hx] using hdiv

theorem weighted_power_integrable : weighted_power_integrable_type := by
  intro b hb n
  let f : ℝ → ℝ := fun E => E ^ (2 * n + 2) * CAS12PlanckIR.weight b E
  have hf : Measurable f := by
    dsimp [f, CAS12PlanckIR.weight]
    fun_prop
  have hnear_major : IntegrableOn
      (fun E : ℝ => b⁻¹ ^ 2 * E ^ (2 * n)) (Ioc 0 1) volume := by
    exact (Continuous.integrableOn_Icc (by fun_prop : Continuous
      (fun E : ℝ => b⁻¹ ^ 2 * E ^ (2 * n)))).mono_set Ioc_subset_Icc_self
  have hnear : IntegrableOn f (Ioc 0 1) volume := by
    apply Integrable.mono_nonneg hnear_major hf.aestronglyMeasurable
    · filter_upwards [ae_restrict_mem measurableSet_Ioc] with E hE
      dsimp [f]
      exact mul_nonneg (pow_nonneg (le_of_lt hE.1) _) (weight_nonneg b E)
    · filter_upwards [ae_restrict_mem measurableSet_Ioc] with E hE
      have hEpos : 0 < E := hE.1
      have hbound := weight_le_inv_sq b E hb hEpos
      have heq : E ^ 2 * (1 / (b * E) ^ 2) = b⁻¹ ^ 2 := by
        field_simp
      have hsmall : E ^ 2 * CAS12PlanckIR.weight b E ≤ b⁻¹ ^ 2 := by
        calc
          _ ≤ E ^ 2 * (1 / (b * E) ^ 2) :=
            mul_le_mul_of_nonneg_left hbound (sq_nonneg E)
          _ = _ := heq
      have hmul := mul_le_mul_of_nonneg_right hsmall (pow_nonneg hEpos.le (2 * n))
      dsimp [f]
      convert hmul using 1 <;> ring
  have htail_core : IntegrableOn
      (fun E : ℝ => E ^ (2 * n + 2) * Real.exp (-b * E)) (Ioi 0) volume := by
    simpa only [Real.rpow_natCast, Real.rpow_one, one_mul] using
      (integrableOn_rpow_mul_exp_neg_mul_rpow
        (p := (1 : ℝ)) (s := ((2 * n + 2 : ℕ) : ℝ)) (b := b)
        (by positivity)
        (by norm_num) hb)
  have hcut : 0 < 1 - Real.exp (-(b * 1)) := by
    have hh : Real.exp (-(b * 1)) < 1 := by
      simpa only [mul_one, Real.exp_zero] using
        (Real.exp_lt_exp.mpr (neg_lt_zero.mpr hb))
    linarith
  have htail_major : IntegrableOn
      (fun E : ℝ => (1 - Real.exp (-(b * 1)))⁻¹ ^ 2 *
        (E ^ (2 * n + 2) * Real.exp (-b * E))) (Ici 1) volume := by
    have hh : IntegrableOn
        (fun E : ℝ => (1 - Real.exp (-(b * 1)))⁻¹ ^ 2 *
          (E ^ (2 * n + 2) * Real.exp (-b * E))) (Ioi 0) volume :=
      htail_core.const_mul _
    exact hh.mono_set (by
      intro E hE
      exact lt_of_lt_of_le zero_lt_one hE)
  have htail : IntegrableOn f (Ici 1) volume := by
    apply Integrable.mono_nonneg htail_major hf.aestronglyMeasurable
    · filter_upwards [ae_restrict_mem measurableSet_Ici] with E hE
      dsimp [f]
      exact mul_nonneg (pow_nonneg (le_trans zero_le_one hE) _)
        (weight_nonneg b E)
    · filter_upwards [ae_restrict_mem measurableSet_Ici] with E hE
      have hUV := weight_le_uv_bound b E 1 hb zero_lt_one hE
      have hmul := mul_le_mul_of_nonneg_left hUV
        (pow_nonneg (le_trans zero_le_one hE) (2 * n + 2))
      dsimp [f]
      simpa [mul_one, div_eq_mul_inv, inv_pow, mul_comm, mul_left_comm, mul_assoc]
        using hmul
  simpa only [f, Ioc_union_Ici_eq_Ioi zero_lt_one] using hnear.union htail

theorem occupation_nonneg : occupation_nonneg_type := by
  intro beta eta E hb he hE
  exact le_of_lt (inv_pos.mpr (positive_occupation_denom hb he hE))

theorem occupation_envelope : occupation_envelope_type := by
  intro beta eta b E hbb hb he hE
  have hd₁ := positive_occupation_denom (lt_of_lt_of_le hb hbb) he hE
  have hd₀ := positive_occupation_denom hb (le_refl 0) hE
  have harg : b * E ≤ beta * E - eta := by
    have := mul_le_mul_of_nonneg_right hbb (le_of_lt hE)
    linarith
  have hden : Real.exp (b * E) - 1 ≤
      Real.exp (beta * E - eta) - 1 := by
    exact sub_le_sub_right (Real.exp_le_exp.mpr (by simpa using harg)) 1
  constructor
  · exact le_of_lt (inv_pos.mpr hd₁)
  · unfold occupation
    simp only [sub_zero]
    have hden' : Real.exp (b * E - 0) - 1 ≤
        Real.exp (beta * E - eta) - 1 := by simpa only [sub_zero] using hden
    simpa only [sub_zero, one_div] using one_div_le_one_div_of_le hd₀ hden'

theorem mixture_occupation_envelope : mixture_occupation_envelope_type := by
  intro S _ μ _ beta eta b E hb hE hbeta heta hint
  have hpoint : ∀ᵐ s ∂μ, 0 ≤ occupation (beta s) (eta s) E ∧
      occupation (beta s) (eta s) E ≤ occupation b 0 E := by
    filter_upwards [hbeta, heta] with s hbs hes
    exact occupation_envelope (beta s) (eta s) b E hbs hb hes hE
  constructor
  · exact integral_nonneg_of_ae (hpoint.mono fun s hs => hs.1)
  · have hc : Integrable (fun _ : S => occupation b 0 E) μ := integrable_const _
    simpa [mixtureOccupation] using
      (integral_mono_ae hint hc (hpoint.mono fun s hs => hs.2))

theorem reference_and_mixture_envelope : reference_and_mixture_envelope_type := by
  intro S _ μ _ beta eta b E betaRef etaRef hb hE hbeta heta hint href hetaRef
  have hm := mixture_occupation_envelope μ beta eta b E hb hE hbeta heta hint
  have hr := occupation_envelope betaRef etaRef b E href hb hetaRef hE
  exact ⟨hm.1, hm.2, hr.1, hr.2⟩

theorem temperature_to_beta_bound : temperature_to_beta_bound_type := by
  intro kB T Tmax hk hT hle
  have hmax : 0 < Tmax := lt_of_lt_of_le hT hle
  have hp : 0 < kB * T := mul_pos hk hT
  have hpmax : 0 < kB * Tmax := mul_pos hk hmax
  have hmul : kB * T ≤ kB * Tmax := mul_le_mul_of_nonneg_left hle (le_of_lt hk)
  unfold inverseTemperature
  exact ⟨inv_pos.mpr hpmax, by simpa only [one_div] using one_div_le_one_div_of_le hp hmul⟩

end G12D
