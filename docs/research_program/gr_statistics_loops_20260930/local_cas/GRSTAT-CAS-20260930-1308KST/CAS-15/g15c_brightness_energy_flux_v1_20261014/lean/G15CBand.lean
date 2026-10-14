/-
G15-C (GR-CAS-15): brightness energy integral, finite-band boundary flux,
bolometric endpoint vanishing, and the moment-level link
r = C − 𝒟I + F·∇I − 4𝓡I (+ band flux) = (We)·∇I.

Source: supplements/DOSSIER_POSITIVE_BRIDGE.md (B1)-(B5), lines 74-150, 179;
contract cas/contracts/CAS-15.json ("COMM-BAND boundaryflux required").
See SOURCE_RECOVERY.md and FROZEN_TARGETS.md.

Model: `f s E x` is the occupation in a horizontal chart (s along L = U + c e,
E the u-measured energy, x ∈ E3 ambient rest direction, directions x ∈ S²).
The reviewed G15-A and G15-B modules are imported unchanged.
-/
import Mathlib
import G15APhoton
import G15BSphere

open MeasureTheory Metric Filter Topology Set
open scoped RealInnerProductSpace

namespace G15C

open G15B

/-! ### Definitions -/

/-- Uncurried occupation `(s, E, x) ↦ f s E x`. -/
def F3 (f : ℝ → ℝ → E3 → ℝ) : ℝ × ℝ × E3 → ℝ := fun q => f q.1 q.2.1 q.2.2

/-- Band brightness `α ∫_{E1}^{E2} E³ f dE`. -/
noncomputable def bandI (α E1 E2 : ℝ) (f : ℝ → ℝ → E3 → ℝ) (s : ℝ) (x : E3) : ℝ :=
  α * ∫ E in E1..E2, E ^ 3 * f s E x

/-- Band transport moment `α ∫_{E1}^{E2} E³ ∂_s f dE` (the band `𝒟I` input). -/
noncomputable def bandD (α E1 E2 : ℝ) (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  α * ∫ E in E1..E2, E ^ 3 * deriv (fun s => f s E x) t

/-- Band collision moment `α ∫_{E1}^{E2} E³ C_t dE`. -/
noncomputable def bandC (α E1 E2 : ℝ) (Ct : ℝ → E3 → ℝ) (x : E3) : ℝ :=
  α * ∫ E in E1..E2, E ^ 3 * Ct E x

/-- Band-edge energy flux `α [E⁴ f]_{E1}^{E2}`. -/
noncomputable def bandFlux (α E1 E2 : ℝ) (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  α * (E2 ^ 4 * f t E2 x - E1 ^ 4 * f t E1 x)

/-- Bolometric brightness `𝓘 = α ∫_0^∞ E³ f dE` (DOSSIER:91). -/
noncomputable def bolI (α : ℝ) (f : ℝ → ℝ → E3 → ℝ) (s : ℝ) (x : E3) : ℝ :=
  α * ∫ E in Ioi (0 : ℝ), E ^ 3 * f s E x

/-- Bolometric transport moment `α ∫_0^∞ E³ ∂_s f dE`. -/
noncomputable def bolD (α : ℝ) (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  α * ∫ E in Ioi (0 : ℝ), E ^ 3 * deriv (fun s => f s E x) t

/-- Bolometric collision moment `𝓒 = α ∫_0^∞ E³ C_t dE` (DOSSIER:96). -/
noncomputable def bolC (α : ℝ) (Ct : ℝ → E3 → ℝ) (x : E3) : ℝ :=
  α * ∫ E in Ioi (0 : ℝ), E ^ 3 * Ct E x

/-- Expanded Liouville (photon-trajectory) operator with the (B1) rates
`dE/ds = −𝓡 E`, `de/ds = W e − F`. -/
noncomputable def liouville (H : ℝ) (a : E3) (σ W : E3 →L[ℝ] E3) (f : ℝ → ℝ → E3 → ℝ)
    (t E : ℝ) (x : E3) : ℝ :=
  deriv (fun s => f s E x) t + -(Rrate3 H a σ x * E) * deriv (fun E' => f t E' x) E
    + fderiv ℝ (f t E) x (W x - Ffield a σ x)

/-- Band residual `r_band = C − 𝒟I + F·∇I − 4𝓡I + 𝓡·flux` (flux kept). -/
noncomputable def bandResidual (α E1 E2 H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3)
    (f : ℝ → ℝ → E3 → ℝ) (Ct : ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  bandC α E1 E2 Ct x - bandD α E1 E2 f t x + fderiv ℝ (bandI α E1 E2 f t) x (Ffield a σ x)
    - 4 * Rrate3 H a σ x * bandI α E1 E2 f t x + Rrate3 H a σ x * bandFlux α E1 E2 f t x

/-- Bolometric regularity package; every field is a stated assumption. -/
structure BolHyp (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) where
  δ : ℝ
  bound : ℝ → ℝ
  hδ : 0 < δ
  c1 : ∀ E ∈ Ioi (0 : ℝ), ContDiff ℝ 1 (fun p : ℝ × E3 => f p.1 E p.2)
  dE : ∀ E ∈ Ioi (0 : ℝ), DifferentiableAt ℝ (fun E' => f t E' x) E
  meas : ∀ p ∈ ball ((t, x) : ℝ × E3) δ,
    AEStronglyMeasurable (fun E => E ^ 3 * f p.1 E p.2) (volume.restrict (Ioi 0))
  meas' : AEStronglyMeasurable
    (fun E => fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x)) (volume.restrict (Ioi 0))
  dom : ∀ E ∈ Ioi (0 : ℝ), ∀ p ∈ ball ((t, x) : ℝ × E3) δ,
    ‖fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) p‖ ≤ bound E
  domInt : IntegrableOn bound (Ioi 0)
  int3 : IntegrableOn (fun E => E ^ 3 * f t E x) (Ioi 0)
  int4 : IntegrableOn (fun E => E ^ 4 * deriv (fun E' => f t E' x) E) (Ioi 0)
  IR : Tendsto (fun E => E ^ 4 * f t E x) (𝓝[>] 0) (𝓝 0)
  UV : Tendsto (fun E => E ^ 4 * f t E x) atTop (𝓝 0)

/-! ### E: energy integration by parts -/

lemma hasDerivAt_pow4 (E : ℝ) : HasDerivAt (fun E : ℝ => E ^ 4) (4 * E ^ 3) E := by
  simpa using hasDerivAt_pow 4 E

theorem band_energy_ibp {g g' : ℝ → ℝ} {E1 E2 : ℝ}
    (hg : ∀ E ∈ uIcc E1 E2, HasDerivAt g (g' E) E) (hg' : IntervalIntegrable g' volume E1 E2) :
    ∫ E in E1..E2, E ^ 4 * g' E =
      (E2 ^ 4 * g E2 - E1 ^ 4 * g E1) - 4 * ∫ E in E1..E2, E ^ 3 * g E := by
  have hu' : IntervalIntegrable (fun E : ℝ => 4 * E ^ 3) volume E1 E2 :=
    (continuous_const.mul (continuous_pow 3)).intervalIntegrable _ _
  rw [intervalIntegral.integral_mul_deriv_eq_deriv_mul (fun E _ => hasDerivAt_pow4 E) hg hu' hg']
  have h : ∫ E in E1..E2, 4 * E ^ 3 * g E = 4 * ∫ E in E1..E2, E ^ 3 * g E := by
    rw [← intervalIntegral.integral_const_mul]
    congr 1; funext E; ring
  rw [h]

theorem bolometric_energy_ibp_limits {g g' : ℝ → ℝ} {LIR LUV : ℝ}
    (hg : ∀ E ∈ Ioi (0 : ℝ), HasDerivAt g (g' E) E)
    (h4 : IntegrableOn (fun E => E ^ 4 * g' E) (Ioi 0))
    (h3 : IntegrableOn (fun E => E ^ 3 * g E) (Ioi 0))
    (hIR : Tendsto (fun E => E ^ 4 * g E) (𝓝[>] 0) (𝓝 LIR))
    (hUV : Tendsto (fun E => E ^ 4 * g E) atTop (𝓝 LUV)) :
    ∫ E in Ioi (0 : ℝ), E ^ 4 * g' E = (LUV - LIR) - 4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * g E := by
  have h3' : IntegrableOn (fun E => 4 * (E ^ 3 * g E)) (Ioi 0) := h3.const_mul 4
  have hu'v : IntegrableOn ((fun E : ℝ => 4 * E ^ 3) * g) (Ioi 0) := by
    refine h3'.congr_fun (fun E _ => ?_) measurableSet_Ioi
    simp only [Pi.mul_apply]; ring
  rw [MeasureTheory.integral_Ioi_mul_deriv_eq_deriv_mul (fun E _ => hasDerivAt_pow4 E) hg h4 hu'v
    hIR hUV]
  have h : ∫ E in Ioi (0 : ℝ), 4 * E ^ 3 * g E = 4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * g E := by
    rw [← integral_const_mul]
    congr 1; funext E; ring
  rw [h]

theorem bolometric_energy_ibp {g g' : ℝ → ℝ}
    (hg : ∀ E ∈ Ioi (0 : ℝ), HasDerivAt g (g' E) E)
    (h4 : IntegrableOn (fun E => E ^ 4 * g' E) (Ioi 0))
    (h3 : IntegrableOn (fun E => E ^ 3 * g E) (Ioi 0))
    (hIR : Tendsto (fun E => E ^ 4 * g E) (𝓝[>] 0) (𝓝 0))
    (hUV : Tendsto (fun E => E ^ 4 * g E) atTop (𝓝 0)) :
    ∫ E in Ioi (0 : ℝ), E ^ 4 * g' E = -4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * g E := by
  rw [bolometric_energy_ibp_limits hg h4 h3 hIR hUV]
  ring

theorem band_flux_negative_control :
    (∫ E in (1 : ℝ)..2, E ^ 4 * (0 : ℝ)) ≠ -4 * ∫ E in (1 : ℝ)..2, E ^ 3 * (1 : ℝ) ∧
    (∫ E in (1 : ℝ)..2, E ^ 4 * (0 : ℝ)) =
      ((2 : ℝ) ^ 4 * 1 - 1 ^ 4 * 1) - 4 * ∫ E in (1 : ℝ)..2, E ^ 3 * (1 : ℝ) := by
  have h1 : (∫ E in (1 : ℝ)..2, E ^ 4 * (0 : ℝ)) = 0 := by simp
  have h2 : (∫ E in (1 : ℝ)..2, E ^ 3 * (1 : ℝ)) = 15 / 4 := by
    simp only [mul_one, integral_pow]; norm_num
  rw [h1, h2]
  constructor <;> norm_num

theorem endpoint_vanishing_of_envelopes {g : ℝ → ℝ}
    (hIR : ∃ K δ : ℝ, 0 < δ ∧ ∀ E ∈ Ioo 0 δ, |E ^ 3 * g E| ≤ K)
    (hUV : ∃ K R : ℝ, ∀ E, R ≤ E → |E ^ 5 * g E| ≤ K) :
    Tendsto (fun E => E ^ 4 * g E) (𝓝[>] 0) (𝓝 0) ∧
      Tendsto (fun E => E ^ 4 * g E) atTop (𝓝 0) := by
  obtain ⟨K, δ, hδ, hK⟩ := hIR
  obtain ⟨K', R, hK'⟩ := hUV
  constructor
  · have hlim : Tendsto (fun E : ℝ => E * K) (𝓝[>] 0) (𝓝 0) := by
      have : Tendsto (fun E : ℝ => E * K) (𝓝 0) (𝓝 (0 * K)) :=
        (continuous_id.mul continuous_const).tendsto 0
      rw [zero_mul] at this
      exact this.mono_left nhdsWithin_le_nhds
    refine squeeze_zero_norm' ?_ hlim
    filter_upwards [Ioo_mem_nhdsGT hδ] with E hE
    have hE0 : 0 < E := hE.1
    rw [Real.norm_eq_abs, show E ^ 4 * g E = E * (E ^ 3 * g E) by ring, abs_mul,
      abs_of_pos hE0]
    exact mul_le_mul_of_nonneg_left (hK E hE) hE0.le
  · have hlim : Tendsto (fun E : ℝ => K' / E) atTop (𝓝 0) :=
      tendsto_const_nhds.div_atTop tendsto_id
    refine squeeze_zero_norm' ?_ hlim
    filter_upwards [eventually_ge_atTop (max R 1)] with E hE
    have hE1 : 1 ≤ E := le_trans (le_max_right _ _) hE
    have hE0 : 0 < E := by linarith
    have hRE : R ≤ E := le_trans (le_max_left _ _) hE
    have hrw : |E ^ 4 * g E| * E = |E ^ 5 * g E| := by
      rw [show E ^ 5 * g E = (E ^ 4 * g E) * E by ring, abs_mul (E ^ 4 * g E) E, abs_of_pos hE0]
    rw [Real.norm_eq_abs, le_div_iff₀ hE0, hrw]
    exact hK' E hRE

theorem planck_envelopes :
    (∃ K δ : ℝ, 0 < δ ∧ ∀ E ∈ Ioo 0 δ, |E ^ 3 * (1 / (Real.exp E - 1))| ≤ K) ∧
    (∃ K R : ℝ, ∀ E, R ≤ E → |E ^ 5 * (1 / (Real.exp E - 1))| ≤ K) := by
  constructor
  · refine ⟨1, 1, one_pos, fun E hE => ?_⟩
    have hE0 : 0 < E := hE.1
    have hlt : E < 1 := hE.2
    have hx : E ≤ Real.exp E - 1 := by linarith [Real.add_one_le_exp E]
    have hpos : 0 < Real.exp E - 1 := lt_of_lt_of_le hE0 hx
    rw [abs_of_nonneg (by positivity), mul_one_div, div_le_iff₀ hpos]
    have h3 : E ^ 3 ≤ E := by
      have : E ^ 3 = E * (E * E) := by ring
      rw [this]
      have hEE : E * E ≤ 1 := by nlinarith
      nlinarith
    linarith
  · refine ⟨1440, 1, fun E hE => ?_⟩
    have hE0 : 0 < E := by linarith
    have h2 : 2 ≤ Real.exp E := by linarith [Real.add_one_le_exp E]
    have hpos : 0 < Real.exp E - 1 := by linarith
    have h6 : E ^ 6 / 720 ≤ Real.exp E := by
      have := Real.pow_div_factorial_le_exp E hE0.le 6
      simpa [Nat.factorial] using this
    have h56 : E ^ 5 ≤ E ^ 6 := pow_le_pow_right₀ hE (by norm_num)
    rw [abs_of_nonneg (by positivity), mul_one_div, div_le_iff₀ hpos]
    linarith

theorem bolometric_witness :
    (∀ E ∈ Ioi (0 : ℝ), HasDerivAt (fun E => Real.exp (-E)) (-Real.exp (-E)) E) ∧
    IntegrableOn (fun E : ℝ => E ^ 4 * -Real.exp (-E)) (Ioi 0) ∧
    IntegrableOn (fun E : ℝ => E ^ 3 * Real.exp (-E)) (Ioi 0) ∧
    Tendsto (fun E : ℝ => E ^ 4 * Real.exp (-E)) (𝓝[>] 0) (𝓝 0) ∧
    Tendsto (fun E : ℝ => E ^ 4 * Real.exp (-E)) atTop (𝓝 0) ∧
    ∫ E in Ioi (0 : ℝ), E ^ 4 * -Real.exp (-E) =
      -4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * Real.exp (-E) := by
  have hd : ∀ E ∈ Ioi (0 : ℝ), HasDerivAt (fun E => Real.exp (-E)) (-Real.exp (-E)) E := by
    intro E _
    simpa using (hasDerivAt_neg E).exp
  have gam : ∀ n : ℕ, IntegrableOn (fun E : ℝ => E ^ n * Real.exp (-E)) (Ioi 0) := by
    intro n
    refine (Real.GammaIntegral_convergent (s := (n : ℝ) + 1) (by positivity)).congr_fun
      (fun E hE => ?_) measurableSet_Ioi
    simp only [add_sub_cancel_right, Real.rpow_natCast]
    ring
  have h4 : IntegrableOn (fun E : ℝ => E ^ 4 * -Real.exp (-E)) (Ioi 0) := by
    have g4 : IntegrableOn (fun E : ℝ => -(E ^ 4 * Real.exp (-E))) (Ioi 0) := (gam 4).neg
    refine g4.congr_fun (fun E _ => ?_) measurableSet_Ioi
    simp only [Pi.neg_apply]; ring
  have hIR : Tendsto (fun E : ℝ => E ^ 4 * Real.exp (-E)) (𝓝[>] 0) (𝓝 0) := by
    have hc : Continuous (fun E : ℝ => E ^ 4 * Real.exp (-E)) := by fun_prop
    have := hc.tendsto 0
    simp only [ne_eq, OfNat.ofNat_ne_zero, not_false_eq_true, zero_pow, neg_zero,
      Real.exp_zero, mul_one] at this
    exact this.mono_left nhdsWithin_le_nhds
  have hUV : Tendsto (fun E : ℝ => E ^ 4 * Real.exp (-E)) atTop (𝓝 0) :=
    Real.tendsto_pow_mul_exp_neg_atTop_nhds_zero 4
  exact ⟨hd, h4, gam 3, hIR, hUV, bolometric_energy_ibp hd h4 (gam 3) hIR hUV⟩

/-! ### L: Leibniz interchange -/

theorem param_band {P : Type*} [NormedAddCommGroup P] [NormedSpace ℝ P] [ProperSpace P]
    {g : P → ℝ → ℝ} (hg : ContDiff ℝ 1 (fun q : P × ℝ => g q.1 q.2)) (a b : ℝ) :
    (∀ p₀ : P, HasFDerivAt (fun p => ∫ E in a..b, g p E)
        (∫ E in a..b, fderiv ℝ (fun p => g p E) p₀) p₀) ∧
    Continuous (fun q : P × ℝ => fderiv ℝ (fun p => g p q.2) q.1) ∧
    ContDiff ℝ 1 (fun p => ∫ E in a..b, g p E) := by
  set G : P × ℝ → ℝ := fun q => g q.1 q.2 with hGdef
  have hGd : Differentiable ℝ G := hg.differentiable (by norm_num)
  have hGc : Continuous (fderiv ℝ G) := hg.continuous_fderiv (by norm_num)
  have hpart : ∀ p E, HasFDerivAt (fun p => g p E)
      ((fderiv ℝ G (p, E)).comp (ContinuousLinearMap.inl ℝ P ℝ)) p := by
    intro p E
    have h1 : HasFDerivAt (fun e : P => (e, E)) (ContinuousLinearMap.inl ℝ P ℝ) p :=
      hasFDerivAt_prodMk_left p E
    exact (hGd (p, E)).hasFDerivAt.comp p h1
  have hF'eq : ∀ p E, fderiv ℝ (fun p => g p E) p =
      (fderiv ℝ G (p, E)).comp (ContinuousLinearMap.inl ℝ P ℝ) :=
    fun p E => (hpart p E).fderiv
  have hF'c : Continuous (fun q : P × ℝ => fderiv ℝ (fun p => g p q.2) q.1) := by
    have : (fun q : P × ℝ => fderiv ℝ (fun p => g p q.2) q.1) =
        fun q => (fderiv ℝ G q).comp (ContinuousLinearMap.inl ℝ P ℝ) := by
      funext q; rw [hF'eq]
    rw [this]
    exact hGc.clm_comp continuous_const
  have hsec : ∀ p : P, Continuous (fun E => g p E) := fun p =>
    hg.continuous.comp (continuous_const.prodMk continuous_id)
  have hderiv : ∀ p₀ : P, HasFDerivAt (fun p => ∫ E in a..b, g p E)
      (∫ E in a..b, fderiv ℝ (fun p => g p E) p₀) p₀ := by
    intro p₀
    obtain ⟨C, hC⟩ := ((isCompact_closedBall p₀ 1).prod isCompact_uIcc).exists_bound_of_continuousOn
      hF'c.continuousOn
    refine intervalIntegral.hasFDerivAt_integral_of_dominated_of_fderiv_le (μ := volume)
      (F := fun p E => g p E) (F' := fun p E => fderiv ℝ (fun p' => g p' E) p) (bound := fun _ => C)
      (closedBall_mem_nhds p₀ one_pos) ?_ ?_ ?_ ?_ ?_ ?_
    · exact Filter.Eventually.of_forall fun p => (hsec p).aestronglyMeasurable
    · exact (hsec p₀).intervalIntegrable _ _
    · exact (hF'c.comp (continuous_const.prodMk continuous_id)).aestronglyMeasurable
    · exact Filter.Eventually.of_forall fun E hE p hp =>
        hC (p, E) ⟨hp, Set.uIoc_subset_uIcc hE⟩
    · exact intervalIntegrable_const
    · exact Filter.Eventually.of_forall fun E _ p _ => by rw [hF'eq]; exact hpart p E
  refine ⟨hderiv, hF'c, ?_⟩
  refine contDiff_one_iff_fderiv.2 ⟨fun p => (hderiv p).differentiableAt, ?_⟩
  have : fderiv ℝ (fun p => ∫ E in a..b, g p E) =
      fun p => ∫ E in a..b, fderiv ℝ (fun p' => g p' E) p := by
    funext p; exact (hderiv p).fderiv
  rw [this]
  exact intervalIntegral.continuous_parametric_intervalIntegral_of_continuous' hF'c a b


/-! ### Partial-derivative helpers -/

lemma contDiff_sec {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (E : ℝ) :
    ContDiff ℝ 1 (fun p : ℝ × E3 => f p.1 E p.2) :=
  hf.comp (contDiff_fst.prodMk (contDiff_const.prodMk contDiff_snd))

lemma diff_sec {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (E t : ℝ) (x : E3) :
    DifferentiableAt ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x) :=
  ((contDiff_sec hf E).differentiable (by norm_num)) _

lemma contDiff_w3 {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) :
    ContDiff ℝ 1 (fun q : (ℝ × E3) × ℝ => q.2 ^ 3 * f q.1.1 q.2 q.1.2) :=
  (contDiff_snd.pow 3).mul (hf.comp ((contDiff_fst.comp contDiff_fst).prodMk
    (contDiff_snd.prodMk (contDiff_snd.comp contDiff_fst))))

lemma hasDerivAt_slice_s {Φ : ℝ × E3 → ℝ} {L : ℝ × E3 →L[ℝ] ℝ} {t : ℝ} {x : E3}
    (h : HasFDerivAt Φ L (t, x)) : HasDerivAt (fun s => Φ (s, x)) (L ((1 : ℝ), (0 : E3))) t := by
  have hp : HasDerivAt (fun s : ℝ => (s, x)) ((1 : ℝ), (0 : E3)) t :=
    (hasDerivAt_id' t).prodMk (hasDerivAt_const t x)
  exact h.comp_hasDerivAt t hp

lemma hasFDerivAt_slice_x {Φ : ℝ × E3 → ℝ} {L : ℝ × E3 →L[ℝ] ℝ} {t : ℝ} {x : E3}
    (h : HasFDerivAt Φ L (t, x)) :
    HasFDerivAt (fun y => Φ (t, y)) (L.comp (ContinuousLinearMap.inr ℝ ℝ E3)) x :=
  h.comp x (hasFDerivAt_prodMk_right t x)

lemma sec_s {f : ℝ → ℝ → E3 → ℝ} {E t : ℝ} {x : E3}
    (h : DifferentiableAt ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x)) :
    HasDerivAt (fun s => f s E x)
      (fderiv ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x) ((1 : ℝ), (0 : E3))) t :=
  hasDerivAt_slice_s h.hasFDerivAt

lemma sec_x {f : ℝ → ℝ → E3 → ℝ} {E t : ℝ} {x : E3}
    (h : DifferentiableAt ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x)) :
    HasFDerivAt (f t E)
      ((fderiv ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x)).comp (ContinuousLinearMap.inr ℝ ℝ E3)) x :=
  hasFDerivAt_slice_x h.hasFDerivAt

lemma fderiv_w3 {f : ℝ → ℝ → E3 → ℝ} {E t : ℝ} {x : E3}
    (h : DifferentiableAt ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x)) :
    fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x) =
      E ^ 3 • fderiv ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x) :=
  (h.hasFDerivAt.const_mul (E ^ 3)).fderiv

lemma w3_s {f : ℝ → ℝ → E3 → ℝ} {E t : ℝ} {x : E3}
    (h : DifferentiableAt ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x)) :
    fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x) ((1 : ℝ), (0 : E3)) =
      E ^ 3 * deriv (fun s => f s E x) t := by
  rw [fderiv_w3 h, (sec_s h).deriv, FunLike.coe_smul, Pi.smul_apply, smul_eq_mul]

lemma w3_x {f : ℝ → ℝ → E3 → ℝ} {E t : ℝ} {x : E3}
    (h : DifferentiableAt ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x)) (v : E3) :
    fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x) ((0 : ℝ), v) =
      E ^ 3 * fderiv ℝ (f t E) x v := by
  rw [fderiv_w3 h, (sec_x h).fderiv, FunLike.coe_smul, Pi.smul_apply, smul_eq_mul,
    ContinuousLinearMap.comp_apply, ContinuousLinearMap.inr_apply]

lemma F3_s {f : ℝ → ℝ → E3 → ℝ} {t E : ℝ} {x : E3} (h : DifferentiableAt ℝ (F3 f) (t, E, x)) :
    HasDerivAt (fun s => f s E x) (fderiv ℝ (F3 f) (t, E, x) ((1 : ℝ), (0 : ℝ), (0 : E3))) t := by
  have hp : HasDerivAt (fun s : ℝ => (s, E, x)) ((1 : ℝ), (0 : ℝ), (0 : E3)) t :=
    (hasDerivAt_id' t).prodMk ((hasDerivAt_const t E).prodMk (hasDerivAt_const t x))
  exact h.hasFDerivAt.comp_hasDerivAt t hp

lemma F3_E {f : ℝ → ℝ → E3 → ℝ} {t E : ℝ} {x : E3} (h : DifferentiableAt ℝ (F3 f) (t, E, x)) :
    HasDerivAt (fun E' => f t E' x) (fderiv ℝ (F3 f) (t, E, x) ((0 : ℝ), (1 : ℝ), (0 : E3))) E := by
  have hp : HasDerivAt (fun E' : ℝ => (t, E', x)) ((0 : ℝ), (1 : ℝ), (0 : E3)) E :=
    (hasDerivAt_const E t).prodMk ((hasDerivAt_id' E).prodMk (hasDerivAt_const E x))
  exact h.hasFDerivAt.comp_hasDerivAt E hp

lemma F3_x {f : ℝ → ℝ → E3 → ℝ} {t E : ℝ} {x : E3} (h : DifferentiableAt ℝ (F3 f) (t, E, x)) :
    HasFDerivAt (f t E) ((fderiv ℝ (F3 f) (t, E, x)).comp
      ((ContinuousLinearMap.inr ℝ ℝ (ℝ × E3)).comp (ContinuousLinearMap.inr ℝ ℝ E3))) x := by
  have hp : HasFDerivAt (fun y : E3 => ((t, E, y) : ℝ × ℝ × E3))
      ((ContinuousLinearMap.inr ℝ ℝ (ℝ × E3)).comp (ContinuousLinearMap.inr ℝ ℝ E3)) x :=
    (hasFDerivAt_prodMk_right t (E, x)).comp x (hasFDerivAt_prodMk_right E x)
  exact h.hasFDerivAt.comp x hp

lemma F3_x_apply {f : ℝ → ℝ → E3 → ℝ} {t E : ℝ} {x : E3}
    (h : DifferentiableAt ℝ (F3 f) (t, E, x)) (v : E3) :
    fderiv ℝ (f t E) x v = fderiv ℝ (F3 f) (t, E, x) ((0 : ℝ), (0 : ℝ), v) := by
  rw [(F3_x h).fderiv, ContinuousLinearMap.comp_apply, ContinuousLinearMap.comp_apply,
    ContinuousLinearMap.inr_apply, ContinuousLinearMap.inr_apply]

lemma cont_line {t : ℝ} {x : E3} : Continuous (fun E : ℝ => ((t, E, x) : ℝ × ℝ × E3)) :=
  continuous_const.prodMk (continuous_id.prodMk continuous_const)

lemma cont_s {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (t : ℝ) (x : E3) :
    Continuous (fun E => deriv (fun s => f s E x) t) := by
  have hfun : (fun E => deriv (fun s => f s E x) t) =
      fun E => fderiv ℝ (F3 f) (t, E, x) ((1 : ℝ), (0 : ℝ), (0 : E3)) := by
    funext E; exact (F3_s ((hf.differentiable (by norm_num)) _)).deriv
  rw [hfun]
  exact ((hf.continuous_fderiv (by norm_num)).comp cont_line).clm_apply continuous_const

lemma cont_E {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (t : ℝ) (x : E3) :
    Continuous (fun E => deriv (fun E' => f t E' x) E) := by
  have hfun : (fun E => deriv (fun E' => f t E' x) E) =
      fun E => fderiv ℝ (F3 f) (t, E, x) ((0 : ℝ), (1 : ℝ), (0 : E3)) := by
    funext E; exact (F3_E ((hf.differentiable (by norm_num)) _)).deriv
  rw [hfun]
  exact ((hf.continuous_fderiv (by norm_num)).comp cont_line).clm_apply continuous_const

lemma cont_x {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (t : ℝ) (x v : E3) :
    Continuous (fun E => fderiv ℝ (f t E) x v) := by
  have hfun : (fun E => fderiv ℝ (f t E) x v) =
      fun E => fderiv ℝ (F3 f) (t, E, x) ((0 : ℝ), (0 : ℝ), v) := by
    funext E; exact F3_x_apply ((hf.differentiable (by norm_num)) _) v
  rw [hfun]
  exact ((hf.continuous_fderiv (by norm_num)).comp cont_line).clm_apply continuous_const

lemma band_ii {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (E1 E2 t : ℝ) (x : E3) :
    IntervalIntegrable (fun E => fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x))
      volume E1 E2 := by
  obtain ⟨-, hc, -⟩ := param_band (P := ℝ × E3) (g := fun p E => E ^ 3 * f p.1 E p.2)
    (contDiff_w3 hf) E1 E2
  have h : Continuous (fun E => fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x)) :=
    hc.comp (continuous_const.prodMk continuous_id)
  exact h.intervalIntegrable _ _

/-! ### L: band Leibniz interchange and bolometric dominated interchange -/

theorem band_hasDerivAt_s {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ)
    (x : E3) :
    HasDerivAt (fun s => bandI α E1 E2 f s x) (bandD α E1 E2 f t x) t := by
  obtain ⟨hd, -, -⟩ := param_band (P := ℝ × E3) (g := fun p E => E ^ 3 * f p.1 E p.2)
    (contDiff_w3 hf) E1 E2
  have e1 : (∫ E in E1..E2, fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x))
      ((1 : ℝ), (0 : E3)) = ∫ E in E1..E2, E ^ 3 * deriv (fun s => f s E x) t := by
    rw [ContinuousLinearMap.intervalIntegral_apply (band_ii hf E1 E2 t x)]
    congr 1; funext E; exact w3_s (diff_sec hf E t x)
  have h1 : HasDerivAt (fun s => ∫ E in E1..E2, E ^ 3 * f s E x)
      (∫ E in E1..E2, E ^ 3 * deriv (fun s => f s E x) t) t :=
    (hasDerivAt_slice_s (hd (t, x))).congr_deriv e1
  exact h1.const_mul α

theorem band_contDiff_x {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ) :
    ContDiff ℝ 1 (bandI α E1 E2 f t) := by
  obtain ⟨-, -, hC⟩ := param_band (P := ℝ × E3) (g := fun p E => E ^ 3 * f p.1 E p.2)
    (contDiff_w3 hf) E1 E2
  have h : ContDiff ℝ 1 (fun y : E3 => ∫ E in E1..E2, E ^ 3 * f t E y) :=
    hC.comp (contDiff_const.prodMk contDiff_id)
  show ContDiff ℝ 1 (fun y : E3 => α * ∫ E in E1..E2, E ^ 3 * f t E y)
  exact contDiff_const.mul h

theorem band_fderiv_x {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ)
    (x v : E3) :
    fderiv ℝ (bandI α E1 E2 f t) x v = α * ∫ E in E1..E2, E ^ 3 * fderiv ℝ (f t E) x v := by
  obtain ⟨hd, -, -⟩ := param_band (P := ℝ × E3) (g := fun p E => E ^ 3 * f p.1 E p.2)
    (contDiff_w3 hf) E1 E2
  have h2 : HasFDerivAt (bandI α E1 E2 f t)
      (α • ((∫ E in E1..E2, fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x)).comp
        (ContinuousLinearMap.inr ℝ ℝ E3))) x :=
    (hasFDerivAt_slice_x (hd (t, x))).const_mul α
  rw [h2.fderiv, FunLike.coe_smul, Pi.smul_apply, smul_eq_mul, ContinuousLinearMap.comp_apply,
    ContinuousLinearMap.inr_apply, ContinuousLinearMap.intervalIntegral_apply (band_ii hf E1 E2 t x)]
  congr 1
  congr 1; funext E; exact w3_x (diff_sec hf E t x) v

theorem band_continuous_D {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ) :
    Continuous (bandD α E1 E2 f t) := by
  obtain ⟨-, hc, -⟩ := param_band (P := ℝ × E3) (g := fun p E => E ^ 3 * f p.1 E p.2)
    (contDiff_w3 hf) E1 E2
  have hcont : Continuous (fun q : E3 × ℝ => q.2 ^ 3 * deriv (fun s => f s q.2 q.1) t) := by
    have hfun : (fun q : E3 × ℝ => q.2 ^ 3 * deriv (fun s => f s q.2 q.1) t) =
        fun q => fderiv ℝ (fun p : ℝ × E3 => q.2 ^ 3 * f p.1 q.2 p.2) (t, q.1) ((1 : ℝ), (0 : E3)) := by
      funext q; exact (w3_s (diff_sec hf q.2 t q.1)).symm
    rw [hfun]
    have hm : Continuous (fun q : E3 × ℝ => (((t, q.1) : ℝ × E3), q.2)) :=
      (continuous_const.prodMk continuous_fst).prodMk continuous_snd
    exact (hc.comp hm).clm_apply continuous_const
  show Continuous (fun y : E3 => α * ∫ E in E1..E2, E ^ 3 * deriv (fun s => f s E y) t)
  exact continuous_const.mul (intervalIntegral.continuous_parametric_intervalIntegral_of_continuous'
    (f := fun y E => E ^ 3 * deriv (fun s => f s E y) t) hcont E1 E2)

theorem param_Ioi {P : Type*} [NormedAddCommGroup P] [NormedSpace ℝ P]
    {g : P → ℝ → ℝ} {p₀ : P} {δ : ℝ} {bound : ℝ → ℝ} (hδ : 0 < δ)
    (hmeas : ∀ p ∈ ball p₀ δ, AEStronglyMeasurable (g p) (volume.restrict (Ioi 0)))
    (hint : IntegrableOn (g p₀) (Ioi 0))
    (hdiff : ∀ E ∈ Ioi (0 : ℝ), ∀ p ∈ ball p₀ δ, DifferentiableAt ℝ (fun p => g p E) p)
    (hmeas' : AEStronglyMeasurable (fun E => fderiv ℝ (fun p => g p E) p₀)
      (volume.restrict (Ioi 0)))
    (hbound : ∀ E ∈ Ioi (0 : ℝ), ∀ p ∈ ball p₀ δ, ‖fderiv ℝ (fun p => g p E) p‖ ≤ bound E)
    (hbint : IntegrableOn bound (Ioi 0)) :
    Integrable (fun E => fderiv ℝ (fun p => g p E) p₀) (volume.restrict (Ioi 0)) ∧
    HasFDerivAt (fun p => ∫ E in Ioi (0 : ℝ), g p E)
      (∫ E in Ioi (0 : ℝ), fderiv ℝ (fun p => g p E) p₀) p₀ := by
  have hball : ball p₀ δ ∈ 𝓝 p₀ := ball_mem_nhds p₀ hδ
  refine ⟨?_, ?_⟩
  · refine Integrable.mono' hbint hmeas' ?_
    exact ae_restrict_of_forall_mem measurableSet_Ioi fun E hE =>
      hbound E hE p₀ (mem_ball_self hδ)
  · refine hasFDerivAt_integral_of_dominated_of_fderiv_le (F := g)
      (F' := fun p E => fderiv ℝ (fun p => g p E) p) (bound := bound) hball ?_ hint hmeas' ?_
      hbint ?_
    · filter_upwards [hball] with p hp using hmeas p hp
    · exact ae_restrict_of_forall_mem measurableSet_Ioi fun E hE p hp => hbound E hE p hp
    · exact ae_restrict_of_forall_mem measurableSet_Ioi fun E hE p hp =>
        (hdiff E hE p hp).hasFDerivAt

/-! ### K: brightness equations (pointwise in x) -/

theorem band_brightness_equation {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f))
    {α E1 E2 : ℝ} (hE : E1 ≤ E2) {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {Ct : ℝ → E3 → ℝ} {t : ℝ} {x : E3}
    (hkin : ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x) :
    HasDerivAt (fun s => bandI α E1 E2 f s x) (bandD α E1 E2 f t x) t ∧
    bandD α E1 E2 f t x + fderiv ℝ (bandI α E1 E2 f t) x (W x - Ffield a σ x)
      + 4 * Rrate3 H a σ x * bandI α E1 E2 f t x
      - Rrate3 H a σ x * bandFlux α E1 E2 f t x = bandC α E1 E2 Ct x := by
  refine ⟨band_hasDerivAt_s hf α E1 E2 t x, ?_⟩
  have hdE : ∀ E, DifferentiableAt ℝ (fun E' => f t E' x) E := fun E =>
    (F3_E ((hf.differentiable (by norm_num)) (t, E, x))).differentiableAt
  have cS := cont_s hf t x
  have cE := cont_E hf t x
  have cX := cont_x hf t x (W x - Ffield a σ x)
  have iS : IntervalIntegrable (fun E : ℝ => E ^ 3 * deriv (fun s => f s E x) t) volume E1 E2 :=
    ((continuous_pow 3).mul cS).intervalIntegrable _ _
  have iB : IntervalIntegrable
      (fun E : ℝ => -Rrate3 H a σ x * (E ^ 4 * deriv (fun E' => f t E' x) E)) volume E1 E2 :=
    (continuous_const.mul ((continuous_pow 4).mul cE)).intervalIntegrable _ _
  have iX : IntervalIntegrable
      (fun E : ℝ => E ^ 3 * fderiv ℝ (f t E) x (W x - Ffield a σ x)) volume E1 E2 :=
    ((continuous_pow 3).mul cX).intervalIntegrable _ _
  have iSB : IntervalIntegrable (fun E : ℝ => E ^ 3 * deriv (fun s => f s E x) t +
      -Rrate3 H a σ x * (E ^ 4 * deriv (fun E' => f t E' x) E)) volume E1 E2 := iS.add iB
  have hC : ∫ E in E1..E2, E ^ 3 * Ct E x = ∫ E in E1..E2, E ^ 3 * liouville H a σ W f t E x := by
    refine intervalIntegral.integral_congr fun E hE' => ?_
    rw [uIcc_of_le hE] at hE'
    rw [hkin E hE']
  have hpt : (fun E : ℝ => E ^ 3 * liouville H a σ W f t E x) = fun E =>
      (E ^ 3 * deriv (fun s => f s E x) t +
        -Rrate3 H a σ x * (E ^ 4 * deriv (fun E' => f t E' x) E))
        + E ^ 3 * fderiv ℝ (f t E) x (W x - Ffield a σ x) := by
    funext E; unfold liouville; ring
  have hibp : ∫ E in E1..E2, E ^ 4 * deriv (fun E' => f t E' x) E =
      (E2 ^ 4 * f t E2 x - E1 ^ 4 * f t E1 x) - 4 * ∫ E in E1..E2, E ^ 3 * f t E x :=
    band_energy_ibp (g := fun E => f t E x) (g' := fun E => deriv (fun E' => f t E' x) E)
      (fun E _ => (hdE E).hasDerivAt) (cE.intervalIntegrable _ _)
  rw [band_fderiv_x hf α E1 E2 t x (W x - Ffield a σ x)]
  simp only [bandD, bandI, bandC, bandFlux]
  rw [hC, hpt, intervalIntegral.integral_add iSB iX, intervalIntegral.integral_add iS iB,
    intervalIntegral.integral_const_mul, hibp]
  ring

theorem band_residual_eq {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f))
    {α E1 E2 : ℝ} (hE : E1 ≤ E2) {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {Ct : ℝ → E3 → ℝ} {t : ℝ} {x : E3}
    (hkin : ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x) :
    bandResidual α E1 E2 H a σ f Ct t x = fderiv ℝ (bandI α E1 E2 f t) x (W x) := by
  have h := (band_brightness_equation hf hE (α := α) hkin).2
  rw [map_sub] at h
  unfold bandResidual
  linarith

lemma bol_leibniz {f : ℝ → ℝ → E3 → ℝ} {t : ℝ} {x : E3} (h : BolHyp f t x) :
    Integrable (fun E => fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x))
        (volume.restrict (Ioi 0)) ∧
      HasFDerivAt (fun p : ℝ × E3 => ∫ E in Ioi (0 : ℝ), E ^ 3 * f p.1 E p.2)
        (∫ E in Ioi (0 : ℝ), fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x)) (t, x) := by
  have hdiff : ∀ E ∈ Ioi (0 : ℝ), ∀ p ∈ ball ((t, x) : ℝ × E3) h.δ,
      DifferentiableAt ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) p := fun E hE p _ =>
    (((h.c1 E hE).differentiable (by norm_num)) p).const_mul _
  exact param_Ioi h.hδ h.meas h.int3 hdiff h.meas' h.dom h.domInt

theorem bol_brightness_equation {f : ℝ → ℝ → E3 → ℝ} {t : ℝ} {x : E3} (h : BolHyp f t x)
    {α H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3} {Ct : ℝ → E3 → ℝ}
    (hkin : ∀ E ∈ Ioi (0 : ℝ), liouville H a σ W f t E x = Ct E x) :
    HasDerivAt (fun s => bolI α f s x) (bolD α f t x) t ∧
    bolD α f t x + fderiv ℝ (bolI α f t) x (W x - Ffield a σ x)
      + 4 * Rrate3 H a σ x * bolI α f t x = bolC α Ct x := by
  have hsec : ∀ E ∈ Ioi (0 : ℝ), DifferentiableAt ℝ (fun p : ℝ × E3 => f p.1 E p.2) (t, x) :=
    fun E hE => ((h.c1 E hE).differentiable (by norm_num)) _
  obtain ⟨hLint, hL⟩ := bol_leibniz h
  have eS : (∫ E in Ioi (0 : ℝ), fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x))
      ((1 : ℝ), (0 : E3)) = ∫ E in Ioi (0 : ℝ), E ^ 3 * deriv (fun s => f s E x) t := by
    rw [ContinuousLinearMap.integral_apply hLint]
    exact setIntegral_congr_fun measurableSet_Ioi fun E hE => w3_s (hsec E hE)
  have eX : ∀ v : E3,
      (∫ E in Ioi (0 : ℝ), fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x))
        ((0 : ℝ), v) = ∫ E in Ioi (0 : ℝ), E ^ 3 * fderiv ℝ (f t E) x v := by
    intro v
    rw [ContinuousLinearMap.integral_apply hLint]
    exact setIntegral_congr_fun measurableSet_Ioi fun E hE => w3_x (hsec E hE) v
  have hS1 : HasDerivAt (fun s => ∫ E in Ioi (0 : ℝ), E ^ 3 * f s E x)
      (∫ E in Ioi (0 : ℝ), E ^ 3 * deriv (fun s => f s E x) t) t :=
    (hasDerivAt_slice_s hL).congr_deriv eS
  refine ⟨hS1.const_mul α, ?_⟩
  have hX : HasFDerivAt (bolI α f t)
      (α • ((∫ E in Ioi (0 : ℝ), fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x)).comp
        (ContinuousLinearMap.inr ℝ ℝ E3))) x :=
    (hasFDerivAt_slice_x hL).const_mul α
  have hfx : fderiv ℝ (bolI α f t) x (W x - Ffield a σ x) =
      α * ∫ E in Ioi (0 : ℝ), E ^ 3 * fderiv ℝ (f t E) x (W x - Ffield a σ x) := by
    rw [hX.fderiv, FunLike.coe_smul, Pi.smul_apply, smul_eq_mul, ContinuousLinearMap.comp_apply,
      ContinuousLinearMap.inr_apply, eX]
  have hibp : ∫ E in Ioi (0 : ℝ), E ^ 4 * deriv (fun E' => f t E' x) E =
      -4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * f t E x :=
    bolometric_energy_ibp (g := fun E => f t E x) (g' := fun E => deriv (fun E' => f t E' x) E)
      (fun E hE => (h.dE E hE).hasDerivAt) h.int4 h.int3 h.IR h.UV
  have iS : IntegrableOn (fun E : ℝ => E ^ 3 * deriv (fun s => f s E x) t) (Ioi 0) := by
    have h0 : IntegrableOn (fun E : ℝ =>
        fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x) ((1 : ℝ), (0 : E3))) (Ioi 0) :=
      hLint.apply_continuousLinearMap _
    exact h0.congr_fun (fun E hE => w3_s (hsec E hE)) measurableSet_Ioi
  have iX : IntegrableOn
      (fun E : ℝ => E ^ 3 * fderiv ℝ (f t E) x (W x - Ffield a σ x)) (Ioi 0) := by
    have h0 : IntegrableOn (fun E : ℝ =>
        fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x)
          ((0 : ℝ), W x - Ffield a σ x)) (Ioi 0) :=
      hLint.apply_continuousLinearMap _
    exact h0.congr_fun (fun E hE => w3_x (hsec E hE) _) measurableSet_Ioi
  have iB : IntegrableOn
      (fun E : ℝ => -Rrate3 H a σ x * (E ^ 4 * deriv (fun E' => f t E' x) E)) (Ioi 0) :=
    h.int4.const_mul _
  have iSB : IntegrableOn (fun E : ℝ => E ^ 3 * deriv (fun s => f s E x) t +
      -Rrate3 H a σ x * (E ^ 4 * deriv (fun E' => f t E' x) E)) (Ioi 0) := iS.add iB
  have hC : ∫ E in Ioi (0 : ℝ), E ^ 3 * Ct E x =
      ∫ E in Ioi (0 : ℝ), E ^ 3 * liouville H a σ W f t E x := by
    refine setIntegral_congr_fun measurableSet_Ioi fun E hE => ?_
    rw [hkin E hE]
  have hpt : (fun E : ℝ => E ^ 3 * liouville H a σ W f t E x) = fun E =>
      (E ^ 3 * deriv (fun s => f s E x) t +
        -Rrate3 H a σ x * (E ^ 4 * deriv (fun E' => f t E' x) E))
        + E ^ 3 * fderiv ℝ (f t E) x (W x - Ffield a σ x) := by
    funext E; unfold liouville; ring
  rw [hfx]
  simp only [bolD, bolI, bolC]
  rw [hC, hpt, integral_add iSB iX, integral_add iS iB, integral_const_mul, hibp]
  ring

lemma pow_mul_exp_neg_integrableOn (n : ℕ) :
    IntegrableOn (fun E : ℝ => E ^ n * Real.exp (-E)) (Ioi 0) := by
  refine (Real.GammaIntegral_convergent (s := (n : ℝ) + 1) (by positivity)).congr_fun
    (fun E hE => ?_) measurableSet_Ioi
  simp only [add_sub_cancel_right, Real.rpow_natCast]
  ring

theorem bolHyp_witness (t : ℝ) (x : E3) :
    Nonempty (BolHyp (fun _ E _ => Real.exp (-E)) t x) := by
  obtain ⟨-, h4, h3, hIR, hUV, -⟩ := bolometric_witness
  have hd' : ∀ E : ℝ, HasDerivAt (fun E => Real.exp (-E)) (-Real.exp (-E)) E := fun E => by
    simpa using (hasDerivAt_neg E).exp
  refine ⟨{
    δ := 1
    bound := fun _ => 0
    hδ := one_pos
    c1 := fun _ _ => contDiff_const
    dE := fun E _ => (hd' E).differentiableAt
    meas := fun _ _ =>
      (by fun_prop : Continuous fun E : ℝ => E ^ 3 * Real.exp (-E)).aestronglyMeasurable
    meas' := ?_
    dom := ?_
    domInt := integrableOn_zero
    int3 := h3
    int4 := ?_
    IR := hIR
    UV := hUV }⟩
  · simp only [fderiv_const_apply]
    exact aestronglyMeasurable_const
  · intro E _ p _
    simp only [fderiv_const_apply, norm_zero, le_refl]
  · refine h4.congr_fun (fun E _ => ?_) measurableSet_Ioi
    show E ^ 4 * -Real.exp (-E) = E ^ 4 * deriv (fun E' : ℝ => Real.exp (-E')) E
    rw [(hd' E).deriv]

/-- The constant occupation `f ≡ 1`. -/
def fone : ℝ → ℝ → E3 → ℝ := fun _ _ _ => 1

theorem band_flux_required :
    ContDiff ℝ 1 (F3 fone) ∧
    (∀ E ∈ Icc (1 : ℝ) 2, liouville 1 0 0 0 fone 0 E (bas 0) = (fun _ _ => (0 : ℝ)) E (bas 0)) ∧
    Rrate3 1 0 0 (bas 0) * bandFlux 1 1 2 fone 0 (bas 0) = 15 ∧
    bandD 1 1 2 fone 0 (bas 0) + fderiv ℝ (bandI 1 1 2 fone 0) (bas 0) ((0 : E3 →L[ℝ] E3) (bas 0) - Ffield 0 0 (bas 0))
      + 4 * Rrate3 1 0 0 (bas 0) * bandI 1 1 2 fone 0 (bas 0)
      ≠ bandC 1 1 2 (fun _ _ => (0 : ℝ)) (bas 0) := by
  have hR : Rrate3 1 0 0 (bas 0) = 1 := by simp [Rrate3]
  have hI : bandI 1 1 2 fone 0 = fun _ => 15 / 4 := by
    funext y
    simp only [bandI, fone, mul_one, one_mul, integral_pow]
    norm_num
  refine ⟨contDiff_const, ?_, ?_, ?_⟩
  · intro E _
    have h1 : ∀ s E : ℝ, fone s E = fun _ => (1 : ℝ) := fun _ _ => rfl
    simp [liouville, fone, h1]
  · rw [hR]
    simp only [bandFlux, fone]
    norm_num
  · rw [hR, hI]
    simp [bandD, bandC, fone]

/-! ### M: moments -/

theorem band_residual_moment (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) {α E1 E2 : ℝ} (hE : E1 ≤ E2)
    {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3} (hW : IsSkew W) {Ct : ℝ → E3 → ℝ} {t : ℝ}
    (hkin : ∀ x ∈ sphere (0 : E3) 1, ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x)
    (i j : Fin 3) :
    ∫ e : S2, bandResidual α E1 E2 H a σ f Ct t e * (e : E3) i * (e : E3) j ∂μ =
      ∑ k, (Mmom μ (bandI α E1 E2 f t) i k * Wm W k j
        - Wm W i k * Mmom μ (bandI α E1 E2 f t) k j) := by
  rw [← commutator_moments μ hμ (band_contDiff_x hf α E1 E2 t) hW i j]
  refine integral_congr_ae (ae_of_all _ fun e => ?_)
  beta_reduce
  rw [band_residual_eq hf hE (hkin e e.2)]

theorem band_weak_quadrupole (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) {α E1 E2 : ℝ} (hE : E1 ≤ E2)
    {H : ℝ} {a : E3} {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0) {W : E3 →L[ℝ] E3} (hW : IsSkew W)
    {Ct : ℝ → E3 → ℝ} {t : ℝ}
    (hkin : ∀ x ∈ sphere (0 : E3) 1, ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x)
    (i j : Fin 3) :
    Integrable (fun e : S2 => bandC α E1 E2 Ct e * (e : E3) i * (e : E3) j) μ ∧
    Integrable (fun e : S2 => bandD α E1 E2 f t e * (e : E3) i * (e : E3) j) μ ∧
    Integrable (fun e : S2 =>
      Rrate3 H a σ e * bandFlux α E1 E2 f t e * (e : E3) i * (e : E3) j) μ ∧
    ∫ e : S2, bandC α E1 E2 Ct e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bandD α E1 E2 f t e * (e : E3) i * (e : E3) j ∂μ
      + ∫ e : S2, Rrate3 H a σ e * bandFlux α E1 E2 f t e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bandI α E1 E2 f t e * wB5 H a σ e i j ∂μ
      = ∑ k, (Mmom μ (bandI α E1 E2 f t) i k * Wm W k j
        - Wm W i k * Mmom μ (bandI α E1 E2 f t) k j) := by
  have hI : ContDiff ℝ 1 (bandI α E1 E2 f t) := band_contDiff_x hf α E1 E2 t
  have hRc : Continuous (fun x : E3 => Rrate3 H a σ x) := by
    unfold Rrate3
    exact (continuous_const.add (continuous_const.inner continuous_id)).add
      (continuous_id.inner σ.continuous)
  have hFl : Continuous (bandFlux α E1 E2 f t) := by
    have c2 : Continuous (fun y : E3 => f t E2 y) :=
      hf.continuous.comp (continuous_const.prodMk (continuous_const.prodMk continuous_id))
    have c1 : Continuous (fun y : E3 => f t E1 y) :=
      hf.continuous.comp (continuous_const.prodMk (continuous_const.prodMk continuous_id))
    show Continuous (fun y : E3 => α * (E2 ^ 4 * f t E2 y - E1 ^ 4 * f t E1 y))
    exact continuous_const.mul ((continuous_const.mul c2).sub (continuous_const.mul c1))
  have hDc : Continuous (bandD α E1 E2 f t) := band_continuous_D hf α E1 E2 t
  have hB2 : ∀ e : S2, bandD α E1 E2 f t e
      + fderiv ℝ (bandI α E1 E2 f t) e (W e - Ffield a σ e)
      + 4 * Rrate3 H a σ e * bandI α E1 E2 f t e
      = bandC α E1 E2 Ct e + Rrate3 H a σ e * bandFlux α E1 E2 f t e := by
    intro e
    have := (band_brightness_equation hf hE (α := α) (hkin e e.2)).2
    linarith
  have hGc : Continuous (fun x : E3 => bandD α E1 E2 f t x
      + fderiv ℝ (bandI α E1 E2 f t) x (W x - Ffield a σ x)
      + 4 * Rrate3 H a σ x * bandI α E1 E2 f t x) :=
    (hDc.add ((hI.continuous_fderiv (by norm_num)).clm_apply
      (W.continuous.sub (contDiff_Ffield a σ).continuous))).add
      ((continuous_const.mul hRc).mul hI.continuous)
  have iCF : Integrable (fun e : S2 =>
      (bandC α E1 E2 Ct e + Rrate3 H a σ e * bandFlux α E1 E2 f t e) * (e : E3) i * (e : E3) j) μ := by
    refine (integrable_quad μ hGc i j).congr (ae_of_all _ fun e => ?_)
    beta_reduce
    rw [hB2 e]
  have iF : Integrable (fun e : S2 =>
      Rrate3 H a σ e * bandFlux α E1 E2 f t e * (e : E3) i * (e : E3) j) μ :=
    integrable_quad μ (hRc.mul hFl) i j
  have iC : Integrable (fun e : S2 => bandC α E1 E2 Ct e * (e : E3) i * (e : E3) j) μ := by
    refine (iCF.sub iF).congr (ae_of_all _ fun e => ?_)
    simp only [Pi.sub_apply]
    ring
  have iD : Integrable (fun e : S2 => bandD α E1 E2 f t e * (e : E3) i * (e : E3) j) μ :=
    integrable_quad μ hDc i j
  refine ⟨iC, iD, iF, ?_⟩
  have hW5 : ∫ e : S2, (bandC α E1 E2 Ct e + Rrate3 H a σ e * bandFlux α E1 E2 f t e)
        * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bandD α E1 E2 f t e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bandI α E1 E2 f t e * wB5 H a σ e i j ∂μ
      = ∑ k, (Mmom μ (bandI α E1 E2 f t) i k * Wm W k j
        - Wm W i k * Mmom μ (bandI α E1 E2 f t) k j) :=
    weak_quadrupole_commutator μ hμ hI H a hσ hW
      (Cc := fun x => bandC α E1 E2 Ct x + Rrate3 H a σ x * bandFlux α E1 E2 f t x)
      (DI := bandD α E1 E2 f t) i j iCF iD hB2
  have hsplit : ∫ e : S2, (bandC α E1 E2 Ct e + Rrate3 H a σ e * bandFlux α E1 E2 f t e)
        * (e : E3) i * (e : E3) j ∂μ
      = ∫ e : S2, bandC α E1 E2 Ct e * (e : E3) i * (e : E3) j ∂μ
        + ∫ e : S2, Rrate3 H a σ e * bandFlux α E1 E2 f t e * (e : E3) i * (e : E3) j ∂μ := by
    rw [← integral_add iC iF]
    refine integral_congr_ae (ae_of_all _ fun e => ?_)
    beta_reduce
    ring
  rw [hsplit] at hW5
  linarith

theorem bol_weak_quadrupole (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : ℝ → ℝ → E3 → ℝ} {t : ℝ} (h : ∀ x ∈ sphere (0 : E3) 1, BolHyp f t x)
    {α : ℝ} (hI : ContDiff ℝ 1 (bolI α f t))
    {H : ℝ} {a : E3} {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0) {W : E3 →L[ℝ] E3} (hW : IsSkew W)
    {Ct : ℝ → E3 → ℝ}
    (hkin : ∀ x ∈ sphere (0 : E3) 1, ∀ E ∈ Ioi (0 : ℝ), liouville H a σ W f t E x = Ct E x)
    (i j : Fin 3)
    (hC : Integrable (fun e : S2 => bolC α Ct e * (e : E3) i * (e : E3) j) μ)
    (hD : Integrable (fun e : S2 => bolD α f t e * (e : E3) i * (e : E3) j) μ) :
    ∫ e : S2, bolC α Ct e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bolD α f t e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bolI α f t e * wB5 H a σ e i j ∂μ
      = ∑ k, (Mmom μ (bolI α f t) i k * Wm W k j - Wm W i k * Mmom μ (bolI α f t) k j) :=
  weak_quadrupole_commutator μ hμ hI H a hσ hW (Cc := bolC α Ct) (DI := bolD α f t) i j hC hD
    (fun e => (bol_brightness_equation (h e e.2) (α := α) (hkin e e.2)).2)

/-! ### T: transport link to (B1) and to the reviewed G15-A outputs -/

theorem liouville_chain {f : ℝ → ℝ → E3 → ℝ} {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {t : ℝ} {Eγ : ℝ → ℝ} {eγ : ℝ → E3}
    (hf : DifferentiableAt ℝ (F3 f) (t, Eγ t, eγ t))
    (hE : HasDerivAt Eγ (-(Rrate3 H a σ (eγ t) * Eγ t)) t)
    (he : HasDerivAt eγ (W (eγ t) - Ffield a σ (eγ t)) t) :
    HasDerivAt (fun s => f s (Eγ s) (eγ s)) (liouville H a σ W f t (Eγ t) (eγ t)) t := by
  have hp : HasDerivAt (fun s => ((s, Eγ s, eγ s) : ℝ × ℝ × E3))
      ((1 : ℝ), -(Rrate3 H a σ (eγ t) * Eγ t), W (eγ t) - Ffield a σ (eγ t)) t :=
    (hasDerivAt_id' t).prodMk (hE.prodMk he)
  have h1 := hf.hasFDerivAt.comp_hasDerivAt t hp
  refine h1.congr_deriv ?_
  have hsplit : (((1 : ℝ), -(Rrate3 H a σ (eγ t) * Eγ t), W (eγ t) - Ffield a σ (eγ t)) :
      ℝ × ℝ × E3) = ((1 : ℝ), (0 : ℝ), (0 : E3))
        + (-(Rrate3 H a σ (eγ t) * Eγ t)) • ((0 : ℝ), (1 : ℝ), (0 : E3))
        + ((0 : ℝ), (0 : ℝ), W (eγ t) - Ffield a σ (eγ t)) := by
    simp only [Prod.smul_mk, Prod.mk_add_mk, smul_eq_mul, mul_one, mul_zero, smul_zero,
      add_zero, zero_add]
  rw [hsplit, map_add, map_add, map_smul, smul_eq_mul]
  unfold liouville
  rw [(F3_s hf).deriv, (F3_E hf).deriv, F3_x_apply hf]

theorem liouville_of_transport {f : ℝ → ℝ → E3 → ℝ} {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {Ct : ℝ → E3 → ℝ} {t : ℝ} {Eγ : ℝ → ℝ} {eγ : ℝ → E3}
    (hf : DifferentiableAt ℝ (F3 f) (t, Eγ t, eγ t))
    (hE : HasDerivAt Eγ (-(Rrate3 H a σ (eγ t) * Eγ t)) t)
    (he : HasDerivAt eγ (W (eγ t) - Ffield a σ (eγ t)) t)
    (hcoll : HasDerivAt (fun s => f s (Eγ s) (eγ s)) (Ct (Eγ t) (eγ t)) t) :
    liouville H a σ W f t (Eγ t) (eγ t) = Ct (Eγ t) (eγ t) :=
  (liouville_chain hf hE he).unique hcoll

/-- Rest-frame observer `U = (c, 0, 0, 0)` in the G15-A frame components. -/
noncomputable def U0 (c : ℝ) : G15A.V := ![c, 0, 0, 0]

/-- `w4 W X Y = ⟪spatial X, W (spatial Y)⟫`, the rest-frame lift of the vorticity `W`. -/
noncomputable def w4 (W : E3 →L[ℝ] E3) : LinearMap.BilinForm ℝ G15A.V :=
  LinearMap.mk₂ ℝ (fun X Y => ⟪sp X, W (sp Y)⟫)
    (fun X X' Y => by simp only [sp_add, inner_add_left])
    (fun r X Y => by simp only [sp_smul, real_inner_smul_left, smul_eq_mul])
    (fun X Y Y' => by simp only [sp_add, map_add, inner_add_right])
    (fun r X Y => by simp only [sp_smul, map_smul, real_inner_smul_right, smul_eq_mul])

lemma w4_apply (W : E3 →L[ℝ] E3) (X Y : G15A.V) : w4 W X Y = ⟪sp X, W (sp Y)⟫ := rfl

theorem energy_rate_of_G15A {c θ : ℝ} (hc : c ≠ 0) {a : E3} {σ : E3 →L[ℝ] E3} {e : E3}
    {Eγ : ℝ → ℝ} {t E' : ℝ} (hpos : 0 < Eγ t) (hEd : HasDerivAt Eγ E' t)
    (hlog : HasDerivAt (fun s => Real.log (Eγ s))
      (-G15A.Rrate c θ (sig4 σ) (emb3 (c • a)) (emb3 e)) t) :
    HasDerivAt Eγ (-(Rrate3 (θ / 3) a σ e * Eγ t)) t := by
  have h2 := (hEd.log hpos.ne').unique hlog
  rw [bridge_Rrate hc θ a σ e] at h2
  have h3 : E' = -(Rrate3 (θ / 3) a σ e * Eγ t) := by
    rw [(div_eq_iff hpos.ne').1 h2]; ring
  rw [h3] at hEd
  exact hEd

theorem direction_rate_of_G15A {c : ℝ} (hc : c ≠ 0) (a : E3) (σ W : E3 →L[ℝ] E3) (e : E3)
    (e' : G15A.V)
    (h3 : ∀ Y, G15A.mink (G15A.hproj c (U0 c) e') Y =
      -G15A.Fcov c (sig4 σ) (emb3 (c • a)) (emb3 e) Y + w4 W Y (emb3 e)) :
    sp e' = W e - Ffield a σ e := by
  have hpr : G15A.hproj c (U0 c) e' = emb3 (sp e') := by
    funext k
    fin_cases k <;> simp [G15A.hproj, G15A.uvec, U0, G15A.mink, emb3, sp, hc]
  have hy : ∀ y : E3, ⟪sp e', y⟫ = ⟪W e - Ffield a σ e, y⟫ := by
    intro y
    have h := h3 (emb3 y)
    rw [hpr, mink_emb3, bridge_Fcov hc, w4_apply, sp_emb3, sp_emb3] at h
    rw [h, inner_sub_left, real_inner_comm (W e) y]
    ring
  ext i
  have h := hy (bas i)
  rwa [inner_bas_right, inner_bas_right] at h

end G15C
