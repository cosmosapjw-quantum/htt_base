import Mathlib
import G11AGuarded

/-!
G11-B (GR-CAS-11, TEFF-A1): integral Taylor remainder on the scalar entropy
segment, the reciprocal-Hessian envelope lower bound d_h(f‖g) ≥ δ²/(2W)
(supplement TEFF_POSITIVE_BRIDGE (A2) and its proof, lines 76-83), the
physical-endpoint extension by regular approximation and continuity, and the
global energy inequality ∫ δ²/W ≤ 2 D ≤ 2ε on an arbitrary measure and on
dν = C E² dE dΩ.  Targets are frozen in `../FROZEN_TARGETS.md`.  The reviewed
G11-A modules are imported unchanged; budget statements use the domain-guarded
`G11A.finite_budget_stat`.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

namespace G11B

open G11A

/-! ## Segment helpers -/

theorem seg_mem {a b t : ℝ} (ht0 : 0 ≤ t) (ht1 : t ≤ 1) : b + t * (a - b) ∈ uIcc a b := by
  rw [mem_uIcc]
  rcases le_total a b with h | h
  · left
    constructor <;>
      nlinarith [mul_nonneg ht0 (sub_nonneg.2 h), mul_nonneg (sub_nonneg.2 ht1) (sub_nonneg.2 h)]
  · right
    constructor <;>
      nlinarith [mul_nonneg ht0 (sub_nonneg.2 h), mul_nonneg (sub_nonneg.2 ht1) (sub_nonneg.2 h)]

theorem ordConnected_dom (s : Stat) : OrdConnected (dom s) := by
  cases s
  · exact ordConnected_Ioi
  · exact ordConnected_Ioi
  · exact ordConnected_Ioo

theorem seg_dom (s : Stat) {a b t : ℝ} (ha : a ∈ dom s) (hb : b ∈ dom s) (ht0 : 0 ≤ t)
    (ht1 : t ≤ 1) : b + t * (a - b) ∈ dom s :=
  (ordConnected_dom s).uIcc_subset ha hb (seg_mem ht0 ht1)

theorem seg_integrand_contOn (s : Stat) {a b : ℝ} (ha : a ∈ dom s) (hb : b ∈ dom s) :
    ContinuousOn (fun t => (1 - t) * hess s (b + t * (a - b))) (uIcc 0 1) := by
  intro t ht
  rw [uIcc_of_le zero_le_one] at ht
  obtain ⟨p0, p1⟩ := dom_pos s (seg_dom s ha hb ht.1 ht.2)
  have hne : (b + t * (a - b)) * (1 + xi s * (b + t * (a - b))) ≠ 0 := (mul_pos p0 p1).ne'
  refine ContinuousAt.continuousWithinAt ?_
  unfold hess
  exact (continuousAt_const.sub continuousAt_id).mul (continuousAt_const.div (by fun_prop) hne)

/-! ## B0: integral Taylor remainder -/

theorem taylor_integral_remainder (s : Stat) {a b : ℝ} (ha : a ∈ dom s) (hb : b ∈ dom s) :
    bregDens (hS s) (hS' s) a b =
      (a - b) ^ 2 * ∫ t in (0:ℝ)..1, (1 - t) * hess s (b + t * (a - b)) := by
  rw [← intervalIntegral.integral_const_mul]
  have hderiv : ∀ t ∈ uIcc (0:ℝ) 1, HasDerivAt
      (fun t => hS s (b + t * (a - b)) + (1 - t) * (a - b) * hS' s (b + t * (a - b)))
      ((a - b) ^ 2 * ((1 - t) * hess s (b + t * (a - b)))) t := by
    intro t ht
    rw [uIcc_of_le zero_le_one] at ht
    have hz := seg_dom s ha hb ht.1 ht.2
    have hlin : HasDerivAt (fun t : ℝ => b + t * (a - b)) (1 * (a - b)) t :=
      ((hasDerivAt_id' t).mul_const (a - b)).const_add b
    have h1 := (hasDerivAt_hS s hz).comp t hlin
    have h2 := (hasDerivAt_hS' s hz).comp t hlin
    have h3 : HasDerivAt (fun t : ℝ => (1 - t) * (a - b)) (-1 * (a - b)) t :=
      ((hasDerivAt_id' t).const_sub 1).mul_const (a - b)
    refine (h1.add (h3.mul h2)).congr_deriv ?_
    ring
  have hint : IntervalIntegrable
      (fun t => (a - b) ^ 2 * ((1 - t) * hess s (b + t * (a - b)))) volume 0 1 :=
    (continuousOn_const.mul (seg_integrand_contOn s ha hb)).intervalIntegrable
  rw [intervalIntegral.integral_eq_sub_of_hasDerivAt hderiv hint]
  have e1 : b + 1 * (a - b) = a := by ring
  have e0 : b + 0 * (a - b) = b := by ring
  simp only [e1, e0, bregDens]
  ring

/-! ## B1: pointwise envelope inequality, regular case -/

theorem taylor_lower_regular (s : Stat) {a b W : ℝ} (ha : a ∈ dom s) (hb : b ∈ dom s)
    (hW : 0 < W) (henv : ∀ z ∈ uIcc a b, z ∈ dom s → 1 / W ≤ hess s z) :
    (a - b) ^ 2 / (2 * W) ≤ bregDens (hS s) (hS' s) a b := by
  rw [taylor_integral_remainder s ha hb]
  have hk := seg_integrand_contOn s ha hb
  have hlow : (1:ℝ) / W / 2 ≤ ∫ t in (0:ℝ)..1, (1 - t) * hess s (b + t * (a - b)) := by
    have hc : ∫ t in (0:ℝ)..1, (1 - t) * (1 / W) = 1 / W / 2 := by
      rw [intervalIntegral.integral_mul_const,
        intervalIntegral.integral_sub intervalIntegrable_const
          intervalIntegral.intervalIntegrable_id]
      simp
      ring
    rw [← hc]
    refine intervalIntegral.integral_mono_on zero_le_one ?_ hk.intervalIntegrable ?_
    · exact (by fun_prop : Continuous fun t : ℝ => (1 - t) * (1 / W)).intervalIntegrable 0 1
    · intro t ht
      have hz := seg_dom s ha hb ht.1 ht.2
      exact mul_le_mul_of_nonneg_left (henv _ (seg_mem ht.1 ht.2) hz) (by linarith [ht.2])
  have hW0 : W ≠ 0 := hW.ne'
  calc (a - b) ^ 2 / (2 * W) = (a - b) ^ 2 * (1 / W / 2) := by ring
    _ ≤ _ := mul_le_mul_of_nonneg_left hlow (sq_nonneg _)

/-! ## B3 (pointwise): endpoint-extension premises -/

theorem regular_approx_mem (s : Stat) {a b t : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s)
    (ht0 : 0 ≤ t) (ht1 : t < 1) : b + t * (a - b) ∈ dom s := by
  cases s
  · simp only [cdom, dom, mem_Ici, mem_Ioi] at ha hb ⊢
    nlinarith [mul_nonneg ht0 ha, mul_pos (sub_pos.2 ht1) hb]
  · simp only [cdom, dom, mem_Ici, mem_Ioi] at ha hb ⊢
    nlinarith [mul_nonneg ht0 ha, mul_pos (sub_pos.2 ht1) hb]
  · simp only [cdom, dom, mem_Icc, mem_Ioo] at ha hb ⊢
    obtain ⟨ha0, ha1⟩ := ha
    obtain ⟨hb0, hb1⟩ := hb
    constructor
    · nlinarith [mul_nonneg ht0 ha0, mul_pos (sub_pos.2 ht1) hb0]
    · nlinarith [mul_nonneg ht0 (sub_nonneg.2 ha1), mul_pos (sub_pos.2 ht1) (sub_pos.2 hb1)]

theorem regular_approx_segment {a b t : ℝ} (ht0 : 0 ≤ t) (ht1 : t ≤ 1) :
    uIcc (b + t * (a - b)) b ⊆ uIcc a b :=
  uIcc_subset_uIcc (seg_mem ht0 ht1) right_mem_uIcc

theorem regular_approx_tendsto (s : Stat) (a b : ℝ) :
    Tendsto (fun t => bregDens (hS s) (hS' s) (b + t * (a - b)) b) (𝓝[<] 1)
      (𝓝 (bregDens (hS s) (hS' s) a b)) := by
  have hc : Continuous (fun t : ℝ => bregDens (hS s) (hS' s) (b + t * (a - b)) b) :=
    (continuous_bregDens_left s b).comp (by fun_prop)
  have h := (hc.tendsto 1).mono_left (nhdsWithin_le_nhds (s := Iio 1))
  have e : b + 1 * (a - b) = a := by ring
  simpa only [e] using h

/-! ## B1: closed admissible argument (endpoints included) -/

theorem hessian_envelope_pointwise (s : Stat) {a b W : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s)
    (hW : 0 < W) (henv : ∀ z ∈ uIcc a b, z ∈ dom s → 1 / W ≤ hess s z) :
    (a - b) ^ 2 / (2 * W) ≤ bregDens (hS s) (hS' s) a b := by
  have hlim2 : Tendsto (fun t : ℝ => (t * (a - b)) ^ 2 / (2 * W)) (𝓝[<] 1)
      (𝓝 ((a - b) ^ 2 / (2 * W))) := by
    have hc : Continuous (fun t : ℝ => (t * (a - b)) ^ 2 / (2 * W)) := by fun_prop
    have h := (hc.tendsto 1).mono_left (nhdsWithin_le_nhds (s := Iio 1))
    simpa only [one_mul] using h
  refine le_of_tendsto_of_tendsto hlim2 (regular_approx_tendsto s a b) ?_
  filter_upwards [Ioo_mem_nhdsLT (show (0:ℝ) < 1 by norm_num)] with t ht
  have hm := regular_approx_mem s ha hb ht.1.le ht.2
  have hreg := taylor_lower_regular s hm hb hW
    (fun z hz hzd => henv z (regular_approx_segment ht.1.le ht.2.le hz) hzd)
  have e : b + t * (a - b) - b = t * (a - b) := by ring
  rwa [e] at hreg

theorem B1_pointwise (s : Stat) {a b W : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s)
    (hW : 0 < W) (henv : ∀ z ∈ uIcc a b, z * (1 + xi s * z) ≤ W) :
    (a - b) ^ 2 / (2 * W) ≤ bregDens (hS s) (hS' s) a b :=
  hessian_envelope_pointwise s ha hb hW fun z hz hzd => W_lower_bounds_hessian s hzd (henv z hz)

theorem B1_nonvacuous_endpoint :
    (0:ℝ) ∈ cdom .MB ∧ (0:ℝ) ∉ dom .MB ∧ (1:ℝ) ∈ dom .MB ∧
      (∀ z ∈ uIcc (0:ℝ) 1, z * (1 + xi .MB * z) ≤ 1) ∧
      ((0:ℝ) - 1) ^ 2 / (2 * 1) ≤ bregDens (hS .MB) (hS' .MB) 0 1 := by
  have h0 : (0:ℝ) ∈ cdom .MB := by simp [cdom]
  have h1 : (1:ℝ) ∈ dom .MB := by simp [dom]
  have henv : ∀ z ∈ uIcc (0:ℝ) 1, z * (1 + xi .MB * z) ≤ 1 := by
    intro z hz
    rw [uIcc_of_le zero_le_one] at hz
    simp only [xi, zero_mul, add_zero, mul_one]
    exact hz.2
  exact ⟨h0, dom_excludes_zero .MB, h1, henv, B1_pointwise .MB h0 h1 one_pos henv⟩

/-! ## B2: global energy inequality -/

section General

variable {X : Type*} [MeasurableSpace X]

theorem quad_le_two_breg (s : Stat) {a b W : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s)
    (hW : 0 < W) (henv : ∀ z ∈ uIcc a b, z ∈ dom s → 1 / W ≤ hess s z) :
    (a - b) ^ 2 / W ≤ 2 * bregDens (hS s) (hS' s) a b := by
  have hb' := hessian_envelope_pointwise s ha hb hW henv
  have e : (a - b) ^ 2 / W = 2 * ((a - b) ^ 2 / (2 * W)) := by
    rw [mul_div_assoc', mul_div_mul_left _ _ two_ne_zero]
  rw [e]
  linarith

theorem B2_lintegral_hess (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x)
    (hHess : ∀ᵐ x ∂μ, ∀ z ∈ uIcc (f x) (g x), z ∈ dom s → 1 / W x ≤ hess s z) :
    ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤ 2 * Dext μ (hS s) (hS' s) f g := by
  unfold Dext
  rw [← lintegral_const_mul' (2:ℝ≥0∞)
    (fun x => ENNReal.ofReal (bregDens (hS s) (hS' s) (f x) (g x))) (by simp)]
  refine lintegral_mono_ae ?_
  filter_upwards [hfd, hgd, hWpos, hHess] with x h1 h2 h3 h4
  have hq := quad_le_two_breg s h1 h2 h3 h4
  rw [show (2:ℝ≥0∞) = ENNReal.ofReal 2 by simp, ← ENNReal.ofReal_mul (by norm_num)]
  exact ENNReal.ofReal_le_ofReal hq

theorem B2_lintegral (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) :
    ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤ 2 * Dext μ (hS s) (hS' s) f g :=
  B2_lintegral_hess μ s f g W hfd hgd hW.2.1 (WEnvelope_bounds_hessian μ s W f g hW)

theorem B2_integral (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε) :
    Integrable (fun x => (f x - g x) ^ 2 / W x) μ ∧
      ∫ x, (f x - g x) ^ 2 / W x ∂μ ≤ 2 * Dfin μ (hS s) (hS' s) f g ∧
      ∫ x, (f x - g x) ^ 2 / W x ∂μ ≤ 2 * ε := by
  obtain ⟨hint, -, hle⟩ := finite_budget_stat μ s f g hf hg hfd hgd hε0 hε
  have hpt : ∀ᵐ x ∂μ, 0 ≤ (f x - g x) ^ 2 / W x ∧
      (f x - g x) ^ 2 / W x ≤ 2 * bregDens (hS s) (hS' s) (f x) (g x) := by
    filter_upwards [hfd, hgd, hW.2.1, WEnvelope_bounds_hessian μ s W f g hW]
      with x h1 h2 h3 h4
    exact ⟨div_nonneg (sq_nonneg _) h3.le, quad_le_two_breg s h1 h2 h3 h4⟩
  have hqm : AEStronglyMeasurable (fun x => (f x - g x) ^ 2 / W x) μ :=
    (((hf.sub hg).pow_const 2).div hW.1).aestronglyMeasurable
  have hqi : Integrable (fun x => (f x - g x) ^ 2 / W x) μ := by
    refine Integrable.mono' (hint.const_mul 2) hqm ?_
    filter_upwards [hpt] with x hx
    rw [Real.norm_eq_abs, abs_of_nonneg hx.1]
    exact hx.2
  have hI : ∫ x, (f x - g x) ^ 2 / W x ∂μ ≤ 2 * Dfin μ (hS s) (hS' s) f g := by
    unfold Dfin
    rw [← integral_const_mul]
    exact integral_mono_ae hqi (hint.const_mul 2) (hpt.mono fun x hx => hx.2)
  exact ⟨hqi, hI, by linarith⟩

end General

theorem B2_nu (s : Stat) (C : ℝ) (f g W : ℝ × Sphere2 → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ y ∂nu C, f y ∈ cdom s) (hgd : ∀ᵐ y ∂nu C, g y ∈ dom s)
    (hW : WEnvelope (nu C) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (nu C) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε) :
    Integrable (fun y => (f y - g y) ^ 2 / W y) (nu C) ∧
      ∫ y, (f y - g y) ^ 2 / W y ∂nu C ≤ 2 * Dfin (nu C) (hS s) (hS' s) f g ∧
      ∫ y, (f y - g y) ^ 2 / W y ∂nu C ≤ 2 * ε :=
  B2_integral (nu C) s f g W hf hg hfd hgd hW hε0 hε

/-! ## B3 (integral): lower semicontinuity and the endpoint limit -/

section General

variable {X : Type*} [MeasurableSpace X]

theorem B3_Dext_lsc (μ : Measure X) (s : Stat) (fseq : ℕ → X → ℝ) (f g : X → ℝ)
    (hfm : ∀ n, Measurable (fseq n)) (hgm : Measurable g)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x))) :
    Dext μ (hS s) (hS' s) f g ≤ liminf (fun n => Dext μ (hS s) (hS' s) (fseq n) g) atTop := by
  unfold Dext
  have hmeas : ∀ n, Measurable
      (fun x => ENNReal.ofReal (bregDens (hS s) (hS' s) (fseq n x) (g x))) :=
    fun n => ENNReal.measurable_ofReal.comp (measurable_bregDens_stat s (hfm n) hgm)
  calc ∫⁻ x, ENNReal.ofReal (bregDens (hS s) (hS' s) (f x) (g x)) ∂μ
      = ∫⁻ x, liminf (fun n => ENNReal.ofReal (bregDens (hS s) (hS' s) (fseq n x) (g x)))
          atTop ∂μ := by
        refine lintegral_congr_ae ?_
        filter_upwards [hconv] with x hx
        have ht : Tendsto (fun n => ENNReal.ofReal (bregDens (hS s) (hS' s) (fseq n x) (g x)))
            atTop (𝓝 (ENNReal.ofReal (bregDens (hS s) (hS' s) (f x) (g x)))) :=
          (ENNReal.continuous_ofReal.tendsto _).comp
            (((continuous_bregDens_left s (g x)).tendsto (f x)).comp hx)
        exact ht.liminf_eq.symm
    _ ≤ _ := lintegral_liminf_le hmeas

theorem B3_quadratic_lsc (μ : Measure X) (fseq : ℕ → X → ℝ) (f g W : X → ℝ)
    (hfm : ∀ n, Measurable (fseq n)) (hgm : Measurable g) (hWm : Measurable W)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x))) :
    ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤
      liminf (fun n => ∫⁻ x, ENNReal.ofReal ((fseq n x - g x) ^ 2 / W x) ∂μ) atTop := by
  have hmeas : ∀ n, Measurable (fun x => ENNReal.ofReal ((fseq n x - g x) ^ 2 / W x)) :=
    fun n => ENNReal.measurable_ofReal.comp ((((hfm n).sub hgm).pow_const 2).div hWm)
  calc ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ
      = ∫⁻ x, liminf (fun n => ENNReal.ofReal ((fseq n x - g x) ^ 2 / W x)) atTop ∂μ := by
        refine lintegral_congr_ae ?_
        filter_upwards [hconv] with x hx
        have hc : Continuous (fun a : ℝ => ENNReal.ofReal ((a - g x) ^ 2 / W x)) :=
          ENNReal.continuous_ofReal.comp (by fun_prop)
        have ht : Tendsto (fun n => ENNReal.ofReal ((fseq n x - g x) ^ 2 / W x)) atTop
            (𝓝 (ENNReal.ofReal ((f x - g x) ^ 2 / W x))) :=
          (hc.tendsto (f x)).comp hx
        exact ht.liminf_eq.symm
    _ ≤ _ := lintegral_liminf_le hmeas

theorem B3_endpoint_integral_by_regular_approx (μ : Measure X) (s : Stat)
    (fseq : ℕ → X → ℝ) (f g W : X → ℝ)
    (hfm : ∀ n, Measurable (fseq n)) (hgm : Measurable g)
    (hfseq : ∀ n, ∀ᵐ x ∂μ, fseq n x ∈ dom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : ∀ n, WEnvelope μ s W (fseq n) g)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x)))
    {ε : ℝ} (hε : ∀ n, Dext μ (hS s) (hS' s) (fseq n) g ≤ ENNReal.ofReal ε) :
    Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε ∧
      ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤ 2 * ENNReal.ofReal ε := by
  refine ⟨?_, ?_⟩
  · calc Dext μ (hS s) (hS' s) f g
        ≤ liminf (fun n => Dext μ (hS s) (hS' s) (fseq n) g) atTop :=
          B3_Dext_lsc μ s fseq f g hfm hgm hconv
      _ ≤ ENNReal.ofReal ε :=
          liminf_le_of_frequently_le' (Eventually.of_forall hε).frequently
  · calc ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ
        ≤ liminf (fun n => ∫⁻ x, ENNReal.ofReal ((fseq n x - g x) ^ 2 / W x) ∂μ) atTop :=
          B3_quadratic_lsc μ fseq f g W hfm hgm (hW 0).1 hconv
      _ ≤ 2 * ENNReal.ofReal ε := by
          refine liminf_le_of_frequently_le' (Eventually.of_forall fun n => ?_).frequently
          exact (B2_lintegral μ s (fseq n) g W
            ((hfseq n).mono fun x hx => dom_subset_cdom s hx) hgd (hW n)).trans
            (mul_le_mul_left' (hε n) 2)

end General

end G11B
