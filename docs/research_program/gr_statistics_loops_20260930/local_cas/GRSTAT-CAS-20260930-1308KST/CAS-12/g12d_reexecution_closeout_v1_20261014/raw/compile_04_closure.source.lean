import G12DUVIntegrabilityEnvelope

/-!
# G12-D card closure (additive module, re-execution closeout 2026-10-14)

Imports the reviewed, unchanged `PlanckIR`, `G12DInterface` and
`G12DUVIntegrabilityEnvelope` sources and adds only the card items they do not state
as public theorems:

* IR limit stated with the card's literal value `1 / b^2`;
* explicit UV dominating bound for `E^m * W` and integrability of the dominating
  function on `[a, ∞)`;
* weighted-L² integrability for the kernel classes "bounded angular factor times a
  nonnegative (real) energy power" and "polynomial in E with nonnegative coefficients"
  (the reviewed unit covered only an a.e. single monomial `M E^n`, `n : ℕ`);
* both-state mixture envelopes and the (A2)-type weight bound `z(1+z) ≤ W` for every
  `z` between the two states, including the temperature-indexed specialisation;
* regular-branch condensate exclusion: positive BE denominator on `E > 0` when
  `η ≤ 0`, no mass on `E ≤ 0` in either measure, and a negative control showing a
  pole / negative occupation when `η > 0`.

No reviewed source is edited. Scientific admission is not claimed.
-/

open MeasureTheory Set Filter Topology

noncomputable section
universe u

namespace G12DClosure

open G12D

/-! ## Frozen additive target types -/

def ir_limit_one_div_sq_type : Prop :=
  ∀ (b : ℝ), 0 < b →
    Tendsto (fun E : ℝ => E ^ 2 * CAS12PlanckIR.weight b E)
      (nhdsWithin 0 (Ioi 0)) (nhds (1 / b ^ 2))

def power_weight_uv_dominating_type : Prop :=
  ∀ (b a E : ℝ) (m : ℕ), 0 < b → 0 < a → a ≤ E →
    0 ≤ E ^ m * CAS12PlanckIR.weight b E ∧
      E ^ m * CAS12PlanckIR.weight b E ≤
        ((1 - Real.exp (-(b * a)))⁻¹) ^ 2 * (E ^ m * Real.exp (-(b * E)))

def uv_dominating_integrable_type : Prop :=
  ∀ (b a : ℝ) (m : ℕ), 0 < b → 0 < a →
    IntegrableOn
      (fun E : ℝ => ((1 - Real.exp (-(b * a)))⁻¹) ^ 2 * (E ^ m * Real.exp (-(b * E))))
      (Ici a) volume

def poly_envelope_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M : ℝ) (N : ℕ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ M * (1 + z.1 ^ N)) →
    Integrable (fun z => kernelDensity b C z.1 * (K z) ^ 2) (energyAngularMeasure μ) ∧
      Integrable (fun z => (K z) ^ 2) (weightedKernelMeasure b C μ)

def polynomial_sum_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C : ℝ) (s : Finset ℕ) (c : ℕ → ℝ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → (∀ k ∈ s, 0 ≤ c k) →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ ∑ k ∈ s, c k * z.1 ^ k) →
    Integrable (fun z => kernelDensity b C z.1 * (K z) ^ 2) (energyAngularMeasure μ) ∧
      Integrable (fun z => (K z) ^ 2) (weightedKernelMeasure b C μ)

def rpow_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M p : ℝ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M → 0 ≤ p →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ M * z.1 ^ p) →
    Integrable (fun z => kernelDensity b C z.1 * (K z) ^ 2) (energyAngularMeasure μ) ∧
      Integrable (fun z => (K z) ^ 2) (weightedKernelMeasure b C μ)

def angular_bounded_rpow_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M p : ℝ) (A : Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M → 0 ≤ p →
    AEStronglyMeasurable A μ →
    (∀ᵐ ω ∂μ, |A ω| ≤ M) →
    Integrable (fun z : ℝ × Ω => kernelDensity b C z.1 * (A z.2 * z.1 ^ p) ^ 2)
        (energyAngularMeasure μ) ∧
      Integrable (fun z : ℝ × Ω => (A z.2 * z.1 ^ p) ^ 2) (weightedKernelMeasure b C μ)

def two_state_mixture_envelope_type : Prop :=
  ∀ {S S' : Type u} [MeasurableSpace S] [MeasurableSpace S']
    (μf : Measure S) [IsProbabilityMeasure μf]
    (μg : Measure S') [IsProbabilityMeasure μg]
    (betaf etaf : S → ℝ) (betag etag : S' → ℝ) (b E : ℝ),
    0 < b → 0 < E →
    (∀ᵐ s ∂μf, b ≤ betaf s) → (∀ᵐ s ∂μf, etaf s ≤ 0) →
    Integrable (fun s => occupation (betaf s) (etaf s) E) μf →
    (∀ᵐ s ∂μg, b ≤ betag s) → (∀ᵐ s ∂μg, etag s ≤ 0) →
    Integrable (fun s => occupation (betag s) (etag s) E) μg →
    (0 ≤ mixtureOccupation μf betaf etaf E ∧
        mixtureOccupation μf betaf etaf E ≤ occupation b 0 E) ∧
      (0 ≤ mixtureOccupation μg betag etag E ∧
        mixtureOccupation μg betag etag E ≤ occupation b 0 E)

def between_states_weight_bound_type : Prop :=
  ∀ (b E f g z : ℝ), 0 < b → 0 < E →
    0 ≤ f → f ≤ occupation b 0 E → 0 ≤ g → g ≤ occupation b 0 E →
    min f g ≤ z → z ≤ max f g →
    z * (1 + z) ≤ CAS12PlanckIR.weight b E

def temperature_envelope_weight_type : Prop :=
  ∀ {S : Type u} [MeasurableSpace S]
    (μ : Measure S) [IsProbabilityMeasure μ] (T : S → ℝ)
    (kB Tmax eta0 betaRef etaRef : ℝ),
    0 < kB → 0 < Tmax → (∀ᵐ s ∂μ, 0 < T s ∧ T s ≤ Tmax) → eta0 ≤ 0 →
    inverseTemperature kB Tmax ≤ betaRef → etaRef ≤ 0 →
    ∀ E : ℝ, 0 < E →
    Integrable (fun s => occupation (inverseTemperature kB (T s)) eta0 E) μ →
    ∀ z : ℝ,
      min (mixtureOccupation μ (fun s => inverseTemperature kB (T s)) (fun _ => eta0) E)
          (occupation betaRef etaRef E) ≤ z →
      z ≤ max (mixtureOccupation μ (fun s => inverseTemperature kB (T s)) (fun _ => eta0) E)
          (occupation betaRef etaRef E) →
      z * (1 + z) ≤ CAS12PlanckIR.weight (inverseTemperature kB Tmax) E

def occupation_denominator_pos_type : Prop :=
  ∀ (beta eta E : ℝ), 0 < beta → eta ≤ 0 → 0 < E →
    0 < Real.exp (beta * E - eta) - 1

def no_nonpositive_energy_mass_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (b C : ℝ),
    energyAngularMeasure μ {z : ℝ × Ω | z.1 ≤ 0} = 0 ∧
      weightedKernelMeasure b C μ {z : ℝ × Ω | z.1 ≤ 0} = 0

def positive_fugacity_pole_control_type : Prop :=
  ∀ (beta eta : ℝ), 0 < beta → 0 < eta →
    (∃ E : ℝ, 0 < E ∧ Real.exp (beta * E - eta) - 1 = 0) ∧
      (∃ E : ℝ, 0 < E ∧ occupation beta eta E < 0)

/-! ## Proofs -/

theorem ir_limit_one_div_sq : ir_limit_one_div_sq_type := by
  intro b hb
  have h := CAS12PlanckIR.scaled_weight_tendsto b hb
  have hv : b ^ (-2 : ℤ) = 1 / b ^ 2 := by
    rw [zpow_neg, zpow_ofNat, one_div]
  rw [hv] at h
  exact h

theorem power_weight_uv_dominating : power_weight_uv_dominating_type := by
  intro b a E m hb ha hE
  have hE0 : 0 ≤ E := le_trans ha.le hE
  have hpow : 0 ≤ E ^ m := pow_nonneg hE0 m
  refine ⟨mul_nonneg hpow (weight_nonneg b E), ?_⟩
  have hUV := weight_le_uv_bound b E a hb ha hE
  calc
    E ^ m * CAS12PlanckIR.weight b E ≤
        E ^ m * (Real.exp (-(b * E)) / (1 - Real.exp (-(b * a))) ^ 2) :=
      mul_le_mul_of_nonneg_left hUV hpow
    _ = ((1 - Real.exp (-(b * a)))⁻¹) ^ 2 * (E ^ m * Real.exp (-(b * E))) := by
      rw [div_eq_mul_inv, inv_pow]
      ring

theorem uv_dominating_integrable : uv_dominating_integrable_type := by
  intro b a m hb ha
  have hcore : IntegrableOn
      (fun E : ℝ => E ^ m * Real.exp (-(b * E))) (Ioi 0) volume := by
    have h := integrableOn_rpow_mul_exp_neg_mul_rpow
      (p := (1 : ℝ)) (s := (m : ℝ)) (b := b)
      (by
        have hn : 0 ≤ (m : ℝ) := Nat.cast_nonneg m
        linarith)
      (le_refl 1) hb
    simpa only [Real.rpow_natCast, Real.rpow_one, neg_mul] using h
  have hc := hcore.const_mul (((1 - Real.exp (-(b * a)))⁻¹) ^ 2)
  exact hc.mono_set (fun E hE => lt_of_lt_of_le ha (mem_Ici.mp hE))

/-- Positivity of the energy coordinate almost everywhere for the product measure. -/
private theorem ae_energy_pos {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) :
    ∀ᵐ z ∂energyAngularMeasure μ, 0 < z.1 := by
  unfold energyAngularMeasure
  exact (Measure.quasiMeasurePreserving_fst).ae
    (ae_restrict_mem measurableSet_Ioi)

/-- Transfer from the density formulation to the `withDensity` formulation. -/
private theorem density_to_withDensity {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) (b C : ℝ) (hC : 0 < C) (F : ℝ × Ω → ℝ)
    (hd : Integrable (fun z => kernelDensity b C z.1 * F z) (energyAngularMeasure μ)) :
    Integrable F (weightedKernelMeasure b C μ) := by
  have hden_nonneg (z : ℝ × Ω) : 0 ≤ kernelDensity b C z.1 := by
    dsimp [kernelDensity]
    exact mul_nonneg (mul_nonneg (le_of_lt hC) (sq_nonneg z.1)) (weight_nonneg b z.1)
  have hden_meas : Measurable
      (fun z : ℝ × Ω => ENNReal.ofReal (kernelDensity b C z.1)) := by
    dsimp [kernelDensity, CAS12PlanckIR.weight]
    fun_prop
  have hden_fin : ∀ᵐ z ∂energyAngularMeasure μ,
      ENNReal.ofReal (kernelDensity b C z.1) < ⊤ := by
    filter_upwards with z
    exact ENNReal.ofReal_lt_top
  change Integrable F ((energyAngularMeasure μ).withDensity
    (fun z => ENNReal.ofReal (kernelDensity b C z.1)))
  apply (integrable_withDensity_iff hden_meas hden_fin).mpr
  convert hd using 1
  funext z
  rw [ENNReal.toReal_ofReal (hden_nonneg z)]
  ring

private theorem radial_major_integrable (b : ℝ) (hb : 0 < b) (N : ℕ) :
    IntegrableOn
      (fun E : ℝ => E ^ 2 * CAS12PlanckIR.weight b E +
        E ^ (2 * N + 2) * CAS12PlanckIR.weight b E) (Ioi 0) volume := by
  have h0 : IntegrableOn (fun E : ℝ => E ^ 2 * CAS12PlanckIR.weight b E) (Ioi 0) volume := by
    simpa using weighted_power_integrable b hb 0
  have hN := weighted_power_integrable b hb N
  exact h0.add hN

theorem poly_envelope_kernel_integrable : poly_envelope_kernel_integrable_type := by
  intro Ω _ μ _ b C M N K hb hC hM hK hbound
  have hrad : Integrable
      (fun E : ℝ => (2 * C * M ^ 2) *
        (E ^ 2 * CAS12PlanckIR.weight b E +
          E ^ (2 * N + 2) * CAS12PlanckIR.weight b E))
      (volume.restrict (Ioi 0)) :=
    (radial_major_integrable b hb N).const_mul (2 * C * M ^ 2)
  have hprod : Integrable
      (fun z : ℝ × Ω => (2 * C * M ^ 2) *
        (z.1 ^ 2 * CAS12PlanckIR.weight b z.1 +
          z.1 ^ (2 * N + 2) * CAS12PlanckIR.weight b z.1))
      (energyAngularMeasure μ) :=
    hrad.comp_fst μ
  have hdens : Integrable (fun z => kernelDensity b C z.1 * (K z) ^ 2)
      (energyAngularMeasure μ) := by
    apply Integrable.mono_nonneg hprod
    · have hd : Measurable (fun z : ℝ × Ω => kernelDensity b C z.1) := by
        dsimp [kernelDensity, CAS12PlanckIR.weight]
        fun_prop
      exact hd.aestronglyMeasurable.mul (hK.pow 2)
    · filter_upwards with z
      dsimp [kernelDensity]
      exact mul_nonneg
        (mul_nonneg (mul_nonneg (le_of_lt hC) (sq_nonneg z.1))
          (weight_nonneg b z.1)) (sq_nonneg (K z))
    · filter_upwards [hbound] with z hKbound
      have hsq : (K z) ^ 2 ≤ (M * (1 + z.1 ^ N)) ^ 2 := by
        have h := (sq_le_sq₀ (abs_nonneg _) (le_trans (abs_nonneg _) hKbound)).mpr hKbound
        simpa only [sq_abs] using h
      have hpoly : (M * (1 + z.1 ^ N)) ^ 2 ≤ M ^ 2 * (2 * (1 + (z.1 ^ N) ^ 2)) := by
        have h2 : (1 + z.1 ^ N) ^ 2 ≤ 2 * (1 + (z.1 ^ N) ^ 2) := by
          nlinarith [sq_nonneg (1 - z.1 ^ N)]
        rw [mul_pow]
        exact mul_le_mul_of_nonneg_left h2 (sq_nonneg M)
      have hfactor : 0 ≤ C * z.1 ^ 2 * CAS12PlanckIR.weight b z.1 :=
        mul_nonneg (mul_nonneg (le_of_lt hC) (sq_nonneg _)) (weight_nonneg b z.1)
      calc
        kernelDensity b C z.1 * (K z) ^ 2 ≤
            (C * z.1 ^ 2 * CAS12PlanckIR.weight b z.1) *
              (M ^ 2 * (2 * (1 + (z.1 ^ N) ^ 2))) :=
          mul_le_mul_of_nonneg_left (le_trans hsq hpoly) hfactor
        _ = (2 * C * M ^ 2) *
              (z.1 ^ 2 * CAS12PlanckIR.weight b z.1 +
                z.1 ^ (2 * N + 2) * CAS12PlanckIR.weight b z.1) := by
          simp only [← pow_mul]
          ring
  exact ⟨hdens, density_to_withDensity μ b C hC _ hdens⟩

private theorem pow_le_one_add_pow {E : ℝ} (hE : 0 < E) {k N : ℕ} (hk : k ≤ N) :
    E ^ k ≤ 1 + E ^ N := by
  rcases le_total E 1 with h1 | h1
  · have := pow_le_one₀ (n := k) hE.le h1
    have := pow_nonneg hE.le N
    linarith
  · have := pow_le_pow_right₀ h1 hk
    linarith

theorem polynomial_sum_kernel_integrable : polynomial_sum_kernel_integrable_type := by
  intro Ω _ μ _ b C s c K hb hC hc hK hbound
  set N : ℕ := s.sup id with hN
  have hM : 0 ≤ ∑ k ∈ s, c k := Finset.sum_nonneg hc
  apply poly_envelope_kernel_integrable μ b C (∑ k ∈ s, c k) N K hb hC hM hK
  filter_upwards [hbound, ae_energy_pos μ] with z hz hpos
  have hsum : ∑ k ∈ s, c k * z.1 ^ k ≤ ∑ k ∈ s, c k * (1 + z.1 ^ N) := by
    apply Finset.sum_le_sum
    intro k hk
    have hkN : k ≤ N := by
      have := Finset.le_sup (f := id) hk
      simpa [hN] using this
    exact mul_le_mul_of_nonneg_left (pow_le_one_add_pow hpos hkN) (hc k hk)
  rw [← Finset.sum_mul] at hsum
  exact le_trans hz hsum

private theorem rpow_le_one_add_pow {E p : ℝ} (hE : 0 < E) (hp : 0 ≤ p) :
    E ^ p ≤ 1 + E ^ (⌈p⌉₊) := by
  rcases le_total E 1 with h1 | h1
  · have := Real.rpow_le_one hE.le h1 hp
    have := pow_nonneg hE.le (⌈p⌉₊)
    linarith
  · have h := Real.rpow_le_rpow_of_exponent_le h1 (Nat.le_ceil p)
    rw [Real.rpow_natCast] at h
    linarith

theorem rpow_kernel_integrable : rpow_kernel_integrable_type := by
  intro Ω _ μ _ b C M p K hb hC hM hp hK hbound
  apply poly_envelope_kernel_integrable μ b C M (⌈p⌉₊) K hb hC hM hK
  filter_upwards [hbound, ae_energy_pos μ] with z hz hpos
  exact le_trans hz (mul_le_mul_of_nonneg_left (rpow_le_one_add_pow hpos hp) hM)

theorem angular_bounded_rpow_kernel_integrable :
    angular_bounded_rpow_kernel_integrable_type := by
  intro Ω _ μ _ b C M p A hb hC hM hp hA hAbound
  have hmeas : AEStronglyMeasurable (fun z : ℝ × Ω => A z.2 * z.1 ^ p)
      (energyAngularMeasure μ) := by
    have h1 : AEStronglyMeasurable (fun z : ℝ × Ω => A z.2) (energyAngularMeasure μ) := by
      unfold energyAngularMeasure
      exact hA.comp_snd
    have h2 : Measurable (fun z : ℝ × Ω => z.1 ^ p) := by fun_prop
    exact h1.mul h2.aestronglyMeasurable
  have hAz : ∀ᵐ z ∂energyAngularMeasure μ, |A z.2| ≤ M := by
    unfold energyAngularMeasure
    exact (Measure.quasiMeasurePreserving_snd).ae hAbound
  apply rpow_kernel_integrable μ b C M p (fun z : ℝ × Ω => A z.2 * z.1 ^ p)
    hb hC hM hp hmeas
  filter_upwards [hAz, ae_energy_pos μ] with z hz hpos
  have hr : 0 ≤ z.1 ^ p := Real.rpow_nonneg hpos.le p
  rw [abs_mul, abs_of_nonneg hr]
  exact mul_le_mul_of_nonneg_right hz hr

theorem two_state_mixture_envelope : two_state_mixture_envelope_type := by
  intro S S' _ _ μf _ μg _ betaf etaf betag etag b E hb hE hbf hef hif hbg heg hig
  exact ⟨mixture_occupation_envelope μf betaf etaf b E hb hE hbf hef hif,
    mixture_occupation_envelope μg betag etag b E hb hE hbg heg hig⟩

theorem between_states_weight_bound : between_states_weight_bound_type := by
  intro b E f g z hb hE hf0 hfF hg0 hgF hlo hhi
  have hz0 : 0 ≤ z := le_trans (le_min hf0 hg0) hlo
  have hzF : z ≤ occupation b 0 E := le_trans hhi (max_le hfF hgF)
  have hF0 : 0 ≤ occupation b 0 E := le_trans hz0 hzF
  rw [weight_eq_occupation b E hb hE]
  exact mul_le_mul hzF (by linarith) (by linarith) hF0

theorem temperature_envelope_weight : temperature_envelope_weight_type := by
  intro S _ μ _ T kB Tmax eta0 betaRef etaRef hkB hTmax hT heta0 href hetaRef E hE hint z hlo hhi
  have h := temperature_mixture_and_reference_envelope μ T kB Tmax eta0 E betaRef etaRef
    hkB hTmax hE hT heta0 hint href hetaRef
  have hb : 0 < inverseTemperature kB Tmax :=
    (temperature_to_beta_bound kB Tmax Tmax hkB hTmax le_rfl).1
  exact between_states_weight_bound (inverseTemperature kB Tmax) E _ _ z hb hE
    h.1 h.2.1 h.2.2.1 h.2.2.2 hlo hhi

theorem occupation_denominator_pos : occupation_denominator_pos_type := by
  intro beta eta E hb he hE
  have hx : 0 < beta * E - eta := by
    have : 0 < beta * E := mul_pos hb hE
    linarith
  have h := Real.add_one_le_exp (beta * E - eta)
  linarith

theorem no_nonpositive_energy_mass : no_nonpositive_energy_mass_type := by
  intro Ω _ μ b C
  have hrad : (volume.restrict (Ioi (0 : ℝ))) (Iic 0) = 0 := by
    rw [Measure.restrict_apply measurableSet_Iic]
    have hempty : Iic (0 : ℝ) ∩ Ioi 0 = ∅ := by
      ext x
      simp only [mem_inter_iff, mem_Iic, mem_Ioi, mem_empty_iff_false, iff_false, not_and,
        not_lt]
      intro hx
      exact hx
    rw [hempty, measure_empty]
  have hset : {z : ℝ × Ω | z.1 ≤ 0} = Prod.fst ⁻¹' Iic 0 := rfl
  have h1 : energyAngularMeasure μ {z : ℝ × Ω | z.1 ≤ 0} = 0 := by
    rw [hset]
    unfold energyAngularMeasure
    exact (Measure.quasiMeasurePreserving_fst).preimage_null hrad
  refine ⟨h1, ?_⟩
  exact withDensity_absolutelyContinuous _ _ h1

theorem positive_fugacity_pole_control : positive_fugacity_pole_control_type := by
  intro beta eta hb he
  refine ⟨⟨eta / beta, div_pos he hb, ?_⟩, ⟨eta / (2 * beta), div_pos he (by linarith), ?_⟩⟩
  · have h : beta * (eta / beta) - eta = 0 := by
      field_simp
      ring
    rw [h, Real.exp_zero]
    ring
  · have h : beta * (eta / (2 * beta)) - eta = -(eta / 2) := by
      field_simp
      ring
    have hneg : Real.exp (beta * (eta / (2 * beta)) - eta) - 1 < 0 := by
      rw [h]
      have := Real.exp_lt_exp.mpr (show -(eta / 2) < 0 by linarith)
      rw [Real.exp_zero] at this
      linarith
    unfold occupation
    exact inv_lt_zero.mpr hneg

/-! ## Non-vacuity witnesses -/

/-- The kernel-class premises are satisfiable: the constant kernel `1` on a one-point
angular space has a finite weighted norm (so the weighted measure is not vacuous). -/
theorem nonvacuity_constant_kernel :
    Integrable (fun _ : ℝ × Unit => ((1 : ℝ)) ^ 2)
      (weightedKernelMeasure 1 1 (Measure.dirac ())) := by
  have h := poly_envelope_kernel_integrable.{0} (Measure.dirac ()) 1 1 1 0
    (fun _ : ℝ × Unit => (1 : ℝ)) one_pos one_pos zero_le_one
    aestronglyMeasurable_const
    (by
      filter_upwards with z
      norm_num)
  exact h.2

/-- The temperature-indexed premises are satisfiable (Dirac mixture at `T = Tmax = 1`,
`kB = 1`, `η₀ = 0`, reference equal to the envelope), and the conclusion is then a
concrete inequality at `E = 1`. -/
theorem nonvacuity_temperature_instance :
    (occupation (inverseTemperature 1 1) 0 1) * (1 + occupation (inverseTemperature 1 1) 0 1) ≤
      CAS12PlanckIR.weight (inverseTemperature 1 1) 1 := by
  have hint : Integrable
      (fun _ : Unit => occupation (inverseTemperature 1 ((fun _ : Unit => (1 : ℝ)) ())) 0 1)
      (Measure.dirac ()) := integrable_const _
  have href : inverseTemperature 1 1 ≤ inverseTemperature 1 1 := le_rfl
  have hw := temperature_envelope_weight.{0} (Measure.dirac ()) (fun _ : Unit => (1 : ℝ))
    1 1 0 (inverseTemperature 1 1) 0 one_pos one_pos
    (by filter_upwards with s; exact ⟨one_pos, le_rfl⟩) le_rfl href le_rfl 1 one_pos hint
    (occupation (inverseTemperature 1 1) 0 1) (min_le_right _ _) (le_max_right _ _)
  exact hw

end G12DClosure
