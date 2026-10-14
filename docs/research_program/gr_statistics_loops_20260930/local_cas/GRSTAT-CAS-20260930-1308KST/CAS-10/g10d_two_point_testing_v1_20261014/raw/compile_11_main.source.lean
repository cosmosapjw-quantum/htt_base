import Mathlib
import G10BGaussianKL
import G10CSmoothCutoff

/-!
# G10-D: two-point testing, union and triangle probability bounds

Source: `INFORMATION_LIMIT_THEOREMS.md` §6 Corollary (I15), Theorem II and Theorem III
(sha256 775b7d15…), card `tasks/G10-D.json`. Targets frozen in `FROZEN_TARGETS.md`.

* Part G: generic two-point bounds (union bound, confidence-set diameter floor, expected
  diameter, triangle incompatibility, estimator risk, Mathlib `minimaxRisk`).
* Part K: KL to testing (two-cell data processing and a self-proved Bretagnolle–Huber bound).
* Part M: morphology pair (G10-B laws).
* Part C: cutout pair (Theorem III fields on top of the G10-C smooth cutoff).
* Part N: negative controls.
-/

open MeasureTheory ProbabilityTheory InformationTheory Real Set Filter Topology
open scoped ENNReal NNReal

namespace G10D

/-! ## Part G: generic two-point bounds -/

section Generic

variable {Ω Θ : Type*} [MeasurableSpace Ω] [PseudoMetricSpace Θ]

/-- G1: union bound for two coverage events. -/
theorem union_bound_both (P : Measure Ω) [IsProbabilityMeasure P] {E₀ E₁ : Set Ω}
    (h₀ : MeasurableSet E₀) (h₁ : MeasurableSet E₁) (α : ℝ)
    (c₀ : 1 - α ≤ P.real E₀) (c₁ : 1 - α ≤ P.real E₁) : 1 - 2 * α ≤ P.real (E₀ ∩ E₁) := by
  have hu : P.real (E₀ ∪ E₁) ≤ 1 := measureReal_le_one
  have h := measureReal_union_add_inter (μ := P) (s := E₀) h₁
  linarith

/-- G2: two members of a set are at most its (extended) diameter apart. -/
theorem dist_le_ediam_of_mem {S : Set Θ} {θ₀ θ₁ : Θ} (h₀ : θ₀ ∈ S) (h₁ : θ₁ ∈ S) :
    ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam S := by
  rw [← edist_dist]
  exact Metric.edist_le_ediam_of_mem h₀ h₁

theorem both_mem_subset (C : Ω → Set Θ) (θ₀ θ₁ : Θ) :
    {ω | θ₀ ∈ C ω} ∩ {ω | θ₁ ∈ C ω} ⊆
      {ω | ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam (C ω)} :=
  fun _ hω => dist_le_ediam_of_mem hω.1 hω.2

/-- G3: confidence-set diameter floor (I15, first inequality), inner and outer forms. -/
theorem confidence_set_floor (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] (hlaw : P₀ = P₁)
    (C : Ω → Set Θ) (θ₀ θ₁ : Θ) (α : ℝ)
    (hm₀ : MeasurableSet {ω | θ₀ ∈ C ω}) (hm₁ : MeasurableSet {ω | θ₁ ∈ C ω})
    (hcov₀ : 1 - α ≤ P₀.real {ω | θ₀ ∈ C ω}) (hcov₁ : 1 - α ≤ P₁.real {ω | θ₁ ∈ C ω}) :
    (∃ S, MeasurableSet S ∧ S ⊆ {ω | ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam (C ω)} ∧
      1 - 2 * α ≤ P₀.real S) ∧
    1 - 2 * α ≤ P₀.real {ω | ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam (C ω)} := by
  subst hlaw
  have hS := union_bound_both P₀ hm₀ hm₁ α hcov₀ hcov₁
  refine ⟨⟨_, hm₀.inter hm₁, both_mem_subset C θ₀ θ₁, hS⟩, ?_⟩
  exact hS.trans (measureReal_mono (both_mem_subset C θ₀ θ₁))

/-- G4: expected-diameter floor (I15, second inequality). -/
theorem expected_diam_floor (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] (hlaw : P₀ = P₁)
    (C : Ω → Set Θ) (θ₀ θ₁ : Θ) (α : ℝ)
    (hm₀ : MeasurableSet {ω | θ₀ ∈ C ω}) (hm₁ : MeasurableSet {ω | θ₁ ∈ C ω})
    (hcov₀ : 1 - α ≤ P₀.real {ω | θ₀ ∈ C ω}) (hcov₁ : 1 - α ≤ P₁.real {ω | θ₁ ∈ C ω}) :
    ENNReal.ofReal ((1 - 2 * α) * dist θ₀ θ₁) ≤ ∫⁻ ω, Metric.ediam (C ω) ∂P₀ := by
  subst hlaw
  set S := {ω | θ₀ ∈ C ω} ∩ {ω | θ₁ ∈ C ω} with hSdef
  have hSm : MeasurableSet S := hm₀.inter hm₁
  have hS := union_bound_both P₀ hm₀ hm₁ α hcov₀ hcov₁
  have hD : 0 ≤ dist θ₀ θ₁ := dist_nonneg
  have hind : S.indicator (fun _ => ENNReal.ofReal (dist θ₀ θ₁)) ≤ fun ω => Metric.ediam (C ω) := by
    intro ω
    by_cases hω : ω ∈ S
    · rw [indicator_of_mem hω]
      exact dist_le_ediam_of_mem hω.1 hω.2
    · rw [indicator_of_notMem hω]
      simp
  calc ENNReal.ofReal ((1 - 2 * α) * dist θ₀ θ₁)
      ≤ ENNReal.ofReal (dist θ₀ θ₁ * P₀.real S) := by
        apply ENNReal.ofReal_le_ofReal
        nlinarith
    _ = ENNReal.ofReal (dist θ₀ θ₁) * P₀ S := by
        rw [ENNReal.ofReal_mul hD, ofReal_measureReal]
    _ = ∫⁻ ω, S.indicator (fun _ => ENNReal.ofReal (dist θ₀ θ₁)) ω ∂P₀ := by
        rw [lintegral_indicator_const hSm]
    _ ≤ ∫⁻ ω, Metric.ediam (C ω) ∂P₀ := lintegral_mono hind

/-- G5: triangle inequality — the two small-error events are incompatible. -/
theorem small_errors_incompatible (θ₀ θ₁ y : Θ) (h₀ : dist y θ₀ < dist θ₀ θ₁ / 2)
    (h₁ : dist y θ₁ < dist θ₀ θ₁ / 2) : False := by
  have := dist_triangle_left θ₀ θ₁ y
  linarith

theorem large_error_cover (θ₀ θ₁ y : Θ) :
    dist θ₀ θ₁ / 2 ≤ dist y θ₀ ∨ dist θ₀ θ₁ / 2 ≤ dist y θ₁ := by
  by_contra h
  push Not at h
  exact small_errors_incompatible θ₀ θ₁ y h.1 h.2

theorem measurableSet_large_error [MeasurableSpace Θ] [OpensMeasurableSpace Θ]
    {θhat : Ω → Θ} (hθ : Measurable θhat) (c : ℝ) (θ : Θ) :
    MeasurableSet {ω | c ≤ dist (θhat ω) θ} :=
  measurableSet_le measurable_const ((continuous_id.dist continuous_const).measurable.comp hθ)

/-- G6: two-point probability lower bound for every measurable estimator. -/
theorem estimator_two_point_prob [MeasurableSpace Θ] [OpensMeasurableSpace Θ]
    (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] (hlaw : P₀ = P₁)
    (θhat : Ω → Θ) (hθ : Measurable θhat) (θ₀ θ₁ : Θ) :
    1 ≤ P₀.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀} +
        P₁.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁} ∧
    1 / 2 ≤ max (P₀.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀})
        (P₁.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁}) := by
  subst hlaw
  have hA := measurableSet_large_error hθ (dist θ₀ θ₁ / 2) θ₀
  have hB := measurableSet_large_error hθ (dist θ₀ θ₁ / 2) θ₁
  have huniv : {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀} ∪
      {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁} = univ := by
    ext ω
    simp only [mem_union, mem_setOf_eq, mem_univ, iff_true]
    exact large_error_cover θ₀ θ₁ (θhat ω)
  have h := measureReal_union_add_inter (μ := P₀) (s := {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀}) hB
  rw [huniv, probReal_univ] at h
  have hi : 0 ≤ P₀.real ({ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀} ∩
      {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁}) := measureReal_nonneg
  have h1 : 1 ≤ P₀.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀} +
      P₀.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁} := by linarith
  refine ⟨h1, ?_⟩
  rcases le_total (P₀.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀})
      (P₀.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁}) with hle | hle
  · rw [max_eq_right hle]; linarith
  · rw [max_eq_left hle]; linarith

theorem ennreal_half_le_max {a b c : ℝ≥0∞} (h : c ≤ a + b) : c / 2 ≤ max a b := by
  rw [ENNReal.div_le_iff (by norm_num) (by norm_num)]
  calc c ≤ a + b := h
    _ ≤ max a b + max a b := add_le_add (le_max_left a b) (le_max_right a b)
    _ = max a b * 2 := by rw [mul_two]

theorem lintegral_edist_sum_ge [MeasurableSpace Θ] [OpensMeasurableSpace Θ]
    (ν : Measure Θ) [IsProbabilityMeasure ν] (θ₀ θ₁ : Θ) :
    ENNReal.ofReal (dist θ₀ θ₁) ≤ (∫⁻ y, edist y θ₀ ∂ν) + ∫⁻ y, edist y θ₁ ∂ν := by
  have hm0 : Measurable (fun y : Θ => edist y θ₀) := (continuous_id.edist continuous_const).measurable
  rw [← lintegral_add_left hm0]
  calc ENNReal.ofReal (dist θ₀ θ₁) = ∫⁻ _, ENNReal.ofReal (dist θ₀ θ₁) ∂ν := by
        rw [lintegral_const, measure_univ, mul_one]
    _ ≤ ∫⁻ y, edist y θ₀ + edist y θ₁ ∂ν := by
        apply lintegral_mono
        intro y
        rw [← edist_dist]
        calc edist θ₀ θ₁ ≤ edist θ₀ y + edist y θ₁ := edist_triangle _ _ _
          _ = edist y θ₀ + edist y θ₁ := by rw [edist_comm]

/-- G7: estimator risk floor `max_i E_i d(θ̂, θ_i) ≥ D/2` under the common law. -/
theorem estimator_risk_floor [MeasurableSpace Θ] [OpensMeasurableSpace Θ]
    (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] (hlaw : P₀ = P₁)
    (θhat : Ω → Θ) (hθ : Measurable θhat) (θ₀ θ₁ : Θ) :
    ENNReal.ofReal (dist θ₀ θ₁) ≤
        (∫⁻ ω, edist (θhat ω) θ₀ ∂P₀) + ∫⁻ ω, edist (θhat ω) θ₁ ∂P₁ ∧
    ENNReal.ofReal (dist θ₀ θ₁ / 2) ≤
        max (∫⁻ ω, edist (θhat ω) θ₀ ∂P₀) (∫⁻ ω, edist (θhat ω) θ₁ ∂P₁) := by
  subst hlaw
  have : IsProbabilityMeasure (P₀.map θhat) := Measure.isProbabilityMeasure_map hθ.aemeasurable
  have h := lintegral_edist_sum_ge (P₀.map θhat) θ₀ θ₁
  have hm0 : Measurable (fun y : Θ => edist y θ₀) := (continuous_id.edist continuous_const).measurable
  have hm1 : Measurable (fun y : Θ => edist y θ₁) := (continuous_id.edist continuous_const).measurable
  rw [lintegral_map hm0 hθ, lintegral_map hm1 hθ] at h
  refine ⟨h, ?_⟩
  rw [ENNReal.ofReal_div_of_pos (by norm_num), ENNReal.ofReal_ofNat]
  exact ennreal_half_le_max h

/-- G8: minimax lower bound over all randomized (Markov-kernel) estimators. -/
theorem minimaxRisk_two_point [MeasurableSpace Θ] [OpensMeasurableSpace Θ]
    (P : Kernel (Fin 2) Ω) [IsMarkovKernel P] (hlaw : P 0 = P 1) (θ : Fin 2 → Θ) :
    ENNReal.ofReal (dist (θ 0) (θ 1) / 2) ≤ minimaxRisk (fun i y => edist y (θ i)) P := by
  unfold minimaxRisk
  refine le_iInf₂ fun κ hκ => ?_
  have hc : (κ ∘ₖ P) 1 = (κ ∘ₖ P) 0 := by
    rw [Kernel.comp_apply, Kernel.comp_apply, hlaw]
  have : IsProbabilityMeasure ((κ ∘ₖ P) 0) := inferInstance
  have h := lintegral_edist_sum_ge ((κ ∘ₖ P) 0) (θ 0) (θ 1)
  rw [ENNReal.ofReal_div_of_pos (by norm_num), ENNReal.ofReal_ofNat]
  refine (ennreal_half_le_max h).trans (max_le ?_ ?_)
  · exact le_iSup (fun i => ∫⁻ y, edist y (θ i) ∂((κ ∘ₖ P) i)) 0
  · have := le_iSup (fun i => ∫⁻ y, edist y (θ i) ∂((κ ∘ₖ P) i)) 1
    simpa [hc] using this

end Generic

/-! ## Part K: KL to testing (two-cell data processing, Bretagnolle–Huber) -/

section KL

variable {α : Type*} [MeasurableSpace α]

theorem restrict_rnDeriv_ae (μ ν : Measure α) [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    (hac : μ ≪ ν) {A : Set α} (hA : MeasurableSet A) :
    (μ.restrict A).rnDeriv (ν.restrict A) =ᵐ[ν.restrict A] μ.rnDeriv ν := by
  have h1 : μ.restrict A = (ν.restrict A).withDensity (μ.rnDeriv ν) := by
    conv_lhs => rw [← Measure.withDensity_rnDeriv_eq μ ν hac]
    exact restrict_withDensity hA _
  rw [h1]
  exact Measure.rnDeriv_withDensity _ (Measure.measurable_rnDeriv μ ν)

theorem klDiv_restrict_eq (μ ν : Measure α) [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    (hac : μ ≪ ν) {A : Set α} (hA : MeasurableSet A) :
    klDiv (μ.restrict A) (ν.restrict A) =
      ∫⁻ x in A, ENNReal.ofReal (klFun (μ.rnDeriv ν x).toReal) ∂ν := by
  rw [klDiv_eq_lintegral_klFun_of_ac (hac.restrict A)]
  apply lintegral_congr_ae
  filter_upwards [restrict_rnDeriv_ae μ ν hac hA] with x hx
  rw [hx]

/-- K1: additivity of the actual KL over a measurable two-cell partition. -/
theorem klDiv_restrict_add_compl (μ ν : Measure α) [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    (hac : μ ≪ ν) {A : Set α} (hA : MeasurableSet A) :
    klDiv μ ν = klDiv (μ.restrict A) (ν.restrict A) + klDiv (μ.restrict Aᶜ) (ν.restrict Aᶜ) := by
  rw [klDiv_restrict_eq μ ν hac hA, klDiv_restrict_eq μ ν hac hA.compl, lintegral_add_compl _ hA,
    klDiv_eq_lintegral_klFun_of_ac hac]

/-- K2: two-cell data processing — the binary relative entropy of a test event is at most the
actual KL divergence. -/
theorem binary_kl_le_klDiv (μ ν : Measure α) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    {A : Set α} (hA : MeasurableSet A) :
    ENNReal.ofReal (μ.real A * log (μ.real A / ν.real A) +
      μ.real Aᶜ * log (μ.real Aᶜ / ν.real Aᶜ)) ≤ klDiv μ ν := by
  by_cases hac : μ ≪ ν
  swap
  · rw [klDiv_of_not_ac hac]; exact le_top
  rw [klDiv_restrict_add_compl μ ν hac hA]
  have h1 := mul_log_le_klDiv (μ.restrict A) (ν.restrict A)
  have h2 := mul_log_le_klDiv (μ.restrict Aᶜ) (ν.restrict Aᶜ)
  simp only [measureReal_restrict_apply_univ] at h1 h2
  have hμ := probReal_add_probReal_compl (μ := μ) hA
  have hν := probReal_add_probReal_compl (μ := ν) hA
  have hsum : μ.real A * log (μ.real A / ν.real A) + μ.real Aᶜ * log (μ.real Aᶜ / ν.real Aᶜ)
      = (μ.real A * log (μ.real A / ν.real A) + ν.real A - μ.real A) +
        (μ.real Aᶜ * log (μ.real Aᶜ / ν.real Aᶜ) + ν.real Aᶜ - μ.real Aᶜ) := by
    linarith
  rw [hsum]
  exact ENNReal.ofReal_add_le.trans (add_le_add h1 h2)

/-- K3: the two-point (Bernoulli) Bretagnolle–Huber inequality. -/
theorem bh_real (x y K : ℝ) (hx0 : 0 ≤ x) (hx1 : x ≤ 1) (hy0 : 0 ≤ y) (hy1 : y ≤ 1)
    (h0 : y = 0 → x = 0) (h1 : y = 1 → x = 1) (hK0 : 0 ≤ K)
    (hK : x * log (x / y) + (1 - x) * log ((1 - x) / (1 - y)) ≤ K) :
    1 / 2 * exp (-K) ≤ x + (1 - y) := by
  have hexp1 : exp (-K) ≤ 1 := exp_le_one_iff.mpr (by linarith)
  rcases eq_or_lt_of_le hx0 with hx | hx
  · subst hx
    have hy1' : y < 1 := lt_of_le_of_ne hy1 (fun h => by have := h1 h; linarith)
    have hK' : log ((1 - y)⁻¹) ≤ K := by simpa using hK
    rw [log_inv] at hK'
    have hle : exp (-K) ≤ 1 - y := by
      calc exp (-K) ≤ exp (log (1 - y)) := exp_le_exp.mpr (by linarith)
        _ = 1 - y := exp_log (by linarith)
    linarith
  rcases eq_or_lt_of_le hx1 with hx' | hx'
  · subst hx'
    linarith
  have hy : 0 < y := lt_of_le_of_ne hy0 (fun h => by have := h0 h.symm; linarith)
  have hy' : y < 1 := lt_of_le_of_ne hy1 (fun h => by have := h1 h; linarith)
  have hsx : 0 < √x := sqrt_pos.mpr hx
  have hsy : 0 < √y := sqrt_pos.mpr hy
  have hsx' : 0 < √(1 - x) := sqrt_pos.mpr (by linarith)
  have hsy' : 0 < √(1 - y) := sqrt_pos.mpr (by linarith)
  have ha : 0 < √y / √x := div_pos hsy hsx
  have hb : 0 < √(1 - y) / √(1 - x) := div_pos hsy' hsx'
  have hconc := (strictConcaveOn_log_Ioi.concaveOn).2 (mem_Ioi.mpr ha) (mem_Ioi.mpr hb)
    hx.le (by linarith : (0:ℝ) ≤ 1 - x) (by ring : x + (1 - x) = 1)
  simp only [smul_eq_mul] at hconc
  have hxa : x * (√y / √x) = √x * √y := by
    calc x * (√y / √x) = x / √x * √y := by ring
      _ = √x * √y := by rw [div_sqrt]
  have hxb : (1 - x) * (√(1 - y) / √(1 - x)) = √(1 - x) * √(1 - y) := by
    calc (1 - x) * (√(1 - y) / √(1 - x)) = (1 - x) / √(1 - x) * √(1 - y) := by ring
      _ = √(1 - x) * √(1 - y) := by rw [div_sqrt]
  rw [hxa, hxb] at hconc
  have hla : log (√y / √x) = (log y - log x) / 2 := by
    rw [log_div hsy.ne' hsx.ne', log_sqrt hy.le, log_sqrt hx.le]; ring
  have hlb : log (√(1 - y) / √(1 - x)) = (log (1 - y) - log (1 - x)) / 2 := by
    rw [log_div hsy'.ne' hsx'.ne', log_sqrt (by linarith), log_sqrt (by linarith)]; ring
  rw [hla, hlb] at hconc
  rw [log_div hx.ne' hy.ne', log_div (by linarith : (1:ℝ) - x ≠ 0) (by linarith : (1:ℝ) - y ≠ 0)]
    at hK
  set S := √x * √y + √(1 - x) * √(1 - y) with hS
  have hSpos : 0 < S := by positivity
  have hhalf : exp (-K / 2) ≤ S := by
    calc exp (-K / 2) ≤ exp (log S) := exp_le_exp.mpr (by nlinarith)
      _ = S := exp_log hSpos
  have hsq : exp (-K) ≤ S * S := by
    have : exp (-K) = exp (-K / 2) * exp (-K / 2) := by rw [← exp_add]; ring_nf
    rw [this]
    exact mul_le_mul hhalf hhalf (exp_pos _).le hSpos.le
  have hx2 : √x * √x = x := mul_self_sqrt hx.le
  have hy2 : √y * √y = y := mul_self_sqrt hy.le
  have hx2' : √(1 - x) * √(1 - x) = 1 - x := mul_self_sqrt (by linarith)
  have hy2' : √(1 - y) * √(1 - y) = 1 - y := mul_self_sqrt (by linarith)
  have hcs : S * S ≤ (x + (1 - y)) * (y + (1 - x)) := by
    rw [hS]
    nlinarith [sq_nonneg (√x * √(1 - x) - √y * √(1 - y))]
  have h2 : (x + (1 - y)) * (y + (1 - x)) ≤ (x + (1 - y)) * 2 :=
    mul_le_mul_of_nonneg_left (by linarith) (by linarith)
  linarith

/-- K4: Bretagnolle–Huber testing bound on the actual laws. -/
theorem bretagnolle_huber (μ ν : Measure α) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    {A : Set α} (hA : MeasurableSet A) (K : ℝ) (hK0 : 0 ≤ K)
    (hK : klDiv μ ν ≤ ENNReal.ofReal K) : 1 / 2 * exp (-K) ≤ μ.real A + ν.real Aᶜ := by
  have hac : μ ≪ ν := by
    by_contra h
    rw [klDiv_of_not_ac h] at hK
    exact ENNReal.ofReal_ne_top (top_le_iff.mp hK)
  have hbin := (binary_kl_le_klDiv μ ν hA).trans hK
  rw [ENNReal.ofReal_le_ofReal_iff hK0] at hbin
  rw [probReal_compl_eq_one_sub hA, probReal_compl_eq_one_sub hA] at hbin
  rw [probReal_compl_eq_one_sub hA]
  refine bh_real _ _ K measureReal_nonneg measureReal_le_one measureReal_nonneg
    measureReal_le_one ?_ ?_ hK0 hbin
  · intro hy
    have hν0 : ν A = 0 := (measureReal_eq_zero_iff).mp hy
    exact (measureReal_eq_zero_iff).mpr (hac hν0)
  · intro hy
    have hc : ν.real Aᶜ = 0 := by rw [probReal_compl_eq_one_sub hA, hy]; ring
    have hν0 : ν Aᶜ = 0 := (measureReal_eq_zero_iff).mp hc
    have hμ0 : μ.real Aᶜ = 0 := (measureReal_eq_zero_iff).mpr (hac hν0)
    rw [probReal_compl_eq_one_sub hA] at hμ0
    linarith

end KL

section KLEstimator

variable {Ω Θ : Type*} [MeasurableSpace Ω] [PseudoMetricSpace Θ]

/-- K5: Le Cam two-point bound for every measurable estimator, through the actual KL. -/
theorem estimator_two_point_kl [MeasurableSpace Θ] [OpensMeasurableSpace Θ]
    (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] [IsProbabilityMeasure P₁] (K : ℝ)
    (hK0 : 0 ≤ K) (hK : klDiv P₀ P₁ ≤ ENNReal.ofReal K) (θhat : Ω → Θ) (hθ : Measurable θhat)
    (θ₀ θ₁ : Θ) :
    1 / 2 * exp (-K) ≤ P₀.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀} +
      P₁.real {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁} := by
  have hA := measurableSet_large_error hθ (dist θ₀ θ₁ / 2) θ₀
  have h := bretagnolle_huber P₀ P₁ hA K hK0 hK
  have hsub : {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀}ᶜ ⊆
      {ω | dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁} := by
    intro ω hω
    simp only [mem_compl_iff, mem_setOf_eq] at hω ⊢
    rcases large_error_cover θ₀ θ₁ (θhat ω) with h' | h'
    · exact absurd h' hω
    · exact h'
  have := measureReal_mono (μ := P₁) hsub
  linarith

end KLEstimator

/-! ## Part M: morphology pair (G10-B laws) -/

abbrev E3 := EuclideanSpace ℝ (Fin 3)

section Morphology

open G10BGaussianKL

/-- Full Gaussian law of the geodesic member (G10-B `obsLaw`). -/
noncomputable abbrev lawFirst (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ) : Measure Obs :=
  obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ

/-- Full Gaussian law of the accelerated member. -/
noncomputable abbrev lawSecond (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ) : Measure Obs :=
  obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ

noncomputable def slopeFirst (H : ℝ) : E3 := WithLp.toLp 2 (CAS10C03.p H)
noncomputable def slopeSecond (H : ℝ) : E3 := WithLp.toLp 2 (CAS10C03.pPrime H)

theorem powers_bounded_integrable (μ : Measure Obs) [IsProbabilityMeasure μ]
    (φ : (Fin 5 → ℝ) → ℝ) (hφ : Measurable φ) (h01 : ∀ y, 0 ≤ φ y ∧ φ y ≤ 1) :
    Integrable (fun x => φ (powers blockDim x)) μ := by
  refine (integrable_const (1:ℝ)).mono' (hφ.comp (measurable_powers blockDim)).aestronglyMeasurable
    (ae_of_all _ fun x => ?_)
  rw [Real.norm_eq_abs, abs_of_nonneg (h01 _).1]
  exact (h01 _).2

/-- M1: for every powers-only randomized test, type I plus type II error equals one. -/
theorem morph_powers_test_errors (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ)
    (φ : (Fin 5 → ℝ) → ℝ) (hφ : Measurable φ) (h01 : ∀ y, 0 ≤ φ y ∧ φ y ≤ 1) :
    (∫ x, φ (powers blockDim x) ∂(lawFirst H z0 m z1 t σ)) +
      ∫ x, (1 - φ (powers blockDim x)) ∂(lawSecond H z0 m z1 t σ) = 1 := by
  have hint := powers_bounded_integrable (lawSecond H z0 m z1 t σ) φ hφ h01
  rw [integral_sub (integrable_const 1) hint, integral_const, probReal_univ, one_smul,
    powersOnly_tests_agree H z0 m z1 t σ φ hφ]
  ring

theorem compressed_isProb (μ : Measure Obs) [IsProbabilityMeasure μ] :
    IsProbabilityMeasure (μ.map (powers blockDim)) :=
  Measure.isProbabilityMeasure_map (measurable_powers blockDim).aemeasurable

section MorphGeneric

variable {Θ : Type*} [PseudoMetricSpace Θ]

/-- M2: confidence-set floor for every powers-only confidence set (any target metric). -/
theorem morph_confidence_floor (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ)
    (θ₀ θ₁ : Θ) (C : (Fin 5 → ℝ) → Set Θ) (α : ℝ)
    (hm₀ : MeasurableSet {y | θ₀ ∈ C y}) (hm₁ : MeasurableSet {y | θ₁ ∈ C y})
    (hcov₀ : 1 - α ≤ ((lawFirst H z0 m z1 t σ).map (powers blockDim)).real {y | θ₀ ∈ C y})
    (hcov₁ : 1 - α ≤ ((lawSecond H z0 m z1 t σ).map (powers blockDim)).real {y | θ₁ ∈ C y}) :
    1 - 2 * α ≤ ((lawFirst H z0 m z1 t σ).map (powers blockDim)).real
        {y | ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam (C y)} ∧
    ENNReal.ofReal ((1 - 2 * α) * dist θ₀ θ₁) ≤
        ∫⁻ y, Metric.ediam (C y) ∂((lawFirst H z0 m z1 t σ).map (powers blockDim)) := by
  haveI := compressed_isProb (lawFirst H z0 m z1 t σ)
  have hlaw := (compressed_laws_equal H z0 m z1 t σ).symm
  exact ⟨(confidence_set_floor _ _ hlaw C θ₀ θ₁ α hm₀ hm₁ hcov₀ hcov₁).2,
    expected_diam_floor _ _ hlaw C θ₀ θ₁ α hm₀ hm₁ hcov₀ hcov₁⟩

/-- M3: estimator-risk floor for every measurable powers-only estimator. -/
theorem morph_estimator_floor [MeasurableSpace Θ] [OpensMeasurableSpace Θ]
    (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ)
    (g : (Fin 5 → ℝ) → Θ) (hg : Measurable g) (θ₀ θ₁ : Θ) :
    ENNReal.ofReal (dist θ₀ θ₁ / 2) ≤
      max (∫⁻ y, edist (g y) θ₀ ∂((lawFirst H z0 m z1 t σ).map (powers blockDim)))
        (∫⁻ y, edist (g y) θ₁ ∂((lawSecond H z0 m z1 t σ).map (powers blockDim))) := by
  haveI := compressed_isProb (lawFirst H z0 m z1 t σ)
  exact (estimator_risk_floor _ _ (compressed_laws_equal H z0 m z1 t σ).symm g hg θ₀ θ₁).2

end MorphGeneric

/-- M2s: slope-dipole separation of the pair. -/
theorem slope_separation (H : ℝ) : dist (slopeFirst H) (slopeSecond H) = 15 * √2 * |H| / 8 := by
  rw [EuclideanSpace.dist_eq]
  have hsum : (∑ i, dist (slopeFirst H i) (slopeSecond H i) ^ 2) = (15 * √2 * |H| / 8) ^ 2 := by
    simp only [slopeFirst, slopeSecond, PiLp.toLp_apply, Fin.sum_univ_succ, Fin.sum_univ_zero,
      CAS10C03.p, CAS10C03.pPrime, Real.dist_eq]
    simp only [Matrix.cons_val_zero, Matrix.cons_val_succ]
    have h2 : (√2) ^ 2 = 2 := Real.sq_sqrt (by norm_num)
    have e : (15 * √2 * |H| / 8) ^ 2 = 225 * (√2) ^ 2 * |H| ^ 2 / 64 := by ring
    rw [e, h2]
    simp only [sq_abs]
    ring
  rw [hsum, Real.sqrt_sq (by positivity)]

/-- M4: full data — the actual KL constant `225H²/(64σ_p²)` gives a testing lower bound for
every measurable test event. -/
theorem morph_full_data_test_bound (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ)
    (hσ : ∀ j, 0 < σ j) {A : Set Obs} (hA : MeasurableSet A) :
    1 / 2 * exp (-(225 * H ^ 2 / (64 * σ 3 ^ 2))) ≤
      (lawFirst H z0 m z1 t σ).real A + (lawSecond H z0 m z1 t σ).real Aᶜ :=
  bretagnolle_huber _ _ hA _ (by positivity) (full_kl_eq H z0 m z1 t σ hσ).le

/-- M4e: full-data two-point bound for every measurable estimator of the slope dipole. -/
theorem morph_full_data_slope_estimator (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ)
    (hσ : ∀ j, 0 < σ j) (g : Obs → E3) (hg : Measurable g) :
    1 / 2 * exp (-(225 * H ^ 2 / (64 * σ 3 ^ 2))) ≤
      (lawFirst H z0 m z1 t σ).real {x | 15 * √2 * |H| / 8 / 2 ≤ dist (g x) (slopeFirst H)} +
      (lawSecond H z0 m z1 t σ).real {x | 15 * √2 * |H| / 8 / 2 ≤ dist (g x) (slopeSecond H)} := by
  have h := estimator_two_point_kl (lawFirst H z0 m z1 t σ) (lawSecond H z0 m z1 t σ) _
    (by positivity) (full_kl_eq H z0 m z1 t σ hσ).le g hg (slopeFirst H) (slopeSecond H)
  rwa [slope_separation] at h

/-- N5: the full laws differ (G10-B A7), so the equal-law conclusions are compression effects. -/
theorem morph_full_laws_differ (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t σ : Fin 5 → ℝ) (hH : H ≠ 0) :
    lawFirst H z0 m z1 t σ ≠ lawSecond H z0 m z1 t σ :=
  full_laws_ne H z0 m z1 t σ hH

end Morphology

end G10D
