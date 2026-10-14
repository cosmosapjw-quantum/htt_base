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
  have hu'v : IntegrableOn ((fun E : ℝ => 4 * E ^ 3) * g) (Ioi 0) := by
    refine (h3.const_mul 4).congr_fun (fun E _ => ?_) measurableSet_Ioi
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
    rw [Real.norm_eq_abs, le_div_iff₀ hE0,
      show |E ^ 4 * g E| * E = |E ^ 5 * g E| by
        rw [show E ^ 5 * g E = (E ^ 4 * g E) * E by ring, abs_mul, abs_of_pos hE0]]
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
      have := Real.pow_div_factorial_le_exp hE0.le 6
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
    refine (gam 4).neg.congr_fun (fun E _ => ?_) measurableSet_Ioi
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
    exact (hGd (p, E)).hasFDerivAt.comp p (hasFDerivAt_prodMk_left p E)
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
    refine intervalIntegral.hasFDerivAt_integral_of_dominated_of_fderiv_le (bound := fun _ => C)
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

end G15C
