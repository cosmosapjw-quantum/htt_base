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
    simpa only [sub_zero, one_div] using one_div_le_one_div_of_le hd₀ hden

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
