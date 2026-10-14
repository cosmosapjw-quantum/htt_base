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

/-! ## Part C: cutout pair (Theorem III fields, G10-C cutoff) -/

section Cutout

/-- Minkowski product, signature `(-+++)`. -/
noncomputable def mink (v w : Fin 4 → ℝ) : ℝ := -(v 0 * w 0) + v 1 * w 1 + v 2 * w 2 + v 3 * w 3

/-- Fixed observer/receiver `o = (1,0,0,0)`. -/
noncomputable def obsVec : Fin 4 → ℝ := ![1, 0, 0, 0]

/-- Past sourceward null direction `K = (-1, n)`. -/
noncomputable def Kray (n : E3) : Fin 4 → ℝ := ![-1, n 0, n 1, n 2]

/-- Redshift factor `1+z = g(K,u)/g(K,o)` of a stationary field `u` emitting at `r • n`. -/
noncomputable def onePlusZ (u : E3 → Fin 4 → ℝ) (r : ℝ) (n : E3) : ℝ :=
  mink (Kray n) (u (r • n)) / mink (Kray n) obsVec

/-- The observer field `u0 = o`. -/
noncomputable def u0 : E3 → Fin 4 → ℝ := fun _ => obsVec

/-- Rapidity profile `χ = δ q(|x|)`. -/
noncomputable def chi (a : ℝ) (ρ : ℝ → ℝ) (δ : ℝ) (x : E3) : ℝ :=
  δ * G10C.smoothCutoff a ρ ‖x‖

/-- The boosted field `u1 = (cosh χ, sinh χ, 0, 0)` (I12). -/
noncomputable def u1 (a : ℝ) (ρ : ℝ → ℝ) (δ : ℝ) (x : E3) : Fin 4 → ℝ :=
  ![cosh (chi a ρ δ x), sinh (chi a ρ δ x), 0, 0]

/-- (I11): `δ = min(1, M a²)/25`. -/
noncomputable def deltaOf (M a : ℝ) : ℝ := min 1 (M * a ^ 2) / 25

/-- Source rapidity at the origin (boost along `e_x`). -/
noncomputable def sourceRapidity (u : E3 → Fin 4 → ℝ) : ℝ := arsinh (u 0 1)

/-- Intercept dipole at the origin (spatial part of the source value). -/
noncomputable def interceptDipole (u : E3 → Fin 4 → ℝ) : E3 := WithLp.toLp 2 ![u 0 1, u 0 2, u 0 3]

/-- Exterior optical data: `(1+z, d_A)` for every unit direction and every `r ≥ a`. -/
def ExtData (a : ℝ) := Set.Ici a → Metric.sphere (0 : E3) 1 → ℝ × ℝ

noncomputable def extData (u : E3 → Fin 4 → ℝ) (a : ℝ) : ExtData a :=
  fun r n => (onePlusZ u r n, (r : ℝ))

theorem mink_Kray_obsVec (n : E3) : mink (Kray n) obsVec = 1 := by
  simp [mink, Kray, obsVec]

theorem onePlusZ_eq (u : E3 → Fin 4 → ℝ) (r : ℝ) (n : E3) :
    onePlusZ u r n = u (r • n) 0 + n 0 * u (r • n) 1 + n 1 * u (r • n) 2 + n 2 * u (r • n) 3 := by
  rw [onePlusZ, mink_Kray_obsVec, div_one]
  simp [mink, Kray]

theorem onePlusZ_u0 (r : ℝ) (n : E3) : onePlusZ u0 r n = 1 := by
  rw [onePlusZ_eq]; simp [u0, obsVec]

theorem onePlusZ_u1 (a : ℝ) (ρ : ℝ → ℝ) (δ r : ℝ) (n : E3) :
    onePlusZ (u1 a ρ δ) r n = cosh (chi a ρ δ (r • n)) + n 0 * sinh (chi a ρ δ (r • n)) := by
  rw [onePlusZ_eq]; simp [u1]

/-- C1 -/
theorem u0_future_unit (x : E3) : mink (u0 x) (u0 x) = -1 ∧ 0 < u0 x 0 := by
  simp [mink, u0, obsVec]

/-- C1 -/
theorem u1_future_unit (a : ℝ) (ρ : ℝ → ℝ) (δ : ℝ) (x : E3) :
    mink (u1 a ρ δ x) (u1 a ρ δ x) = -1 ∧ 0 < u1 a ρ δ x 0 := by
  refine ⟨?_, by simp [u1, cosh_pos]⟩
  simp [mink, u1]
  nlinarith [cosh_sq (chi a ρ δ x)]

variable {a : ℝ} {ρ : ℝ → ℝ}

theorem chi_contDiff (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    ContDiff ℝ (⊤ : ℕ∞) (chi a ρ δ) :=
  contDiff_const.mul (G10C.radial_contDiff ha hρ)

/-- C1s -/
theorem u0_contDiff : ContDiff ℝ (⊤ : ℕ∞) u0 := contDiff_const

/-- C1s: the boosted field is globally smooth. -/
theorem u1_contDiff (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    ContDiff ℝ (⊤ : ℕ∞) (u1 a ρ δ) := by
  have hc := chi_contDiff ha hρ δ
  rw [contDiff_pi]
  intro i
  fin_cases i
  · exact Real.contDiff_cosh.comp hc
  · exact Real.contDiff_sinh.comp hc
  · exact contDiff_const
  · exact contDiff_const

theorem chi_ray (δ : ℝ) {n : E3} (hn : ‖n‖ = 1) {r : ℝ} (hr : 0 ≤ r) :
    chi a ρ δ (r • n) = δ * G10C.smoothCutoff a ρ r := by
  rw [chi, G10C.radial_ray (a := a) (ρ := ρ) hn hr]

/-- C2: the source's `Z₁(r,n) = cosh χ(r) + n_x sinh χ(r)`. -/
theorem onePlusZ_u1_ray (δ : ℝ) {n : E3} (hn : ‖n‖ = 1) {r : ℝ} (hr : 0 ≤ r) :
    onePlusZ (u1 a ρ δ) r n =
      cosh (δ * G10C.smoothCutoff a ρ r) + n 0 * sinh (δ * G10C.smoothCutoff a ρ r) := by
  rw [onePlusZ_u1, chi_ray δ hn hr]

/-- C3: exact exterior redshift agreement for every direction and every `r ≥ a`. -/
theorem exterior_redshift_agree (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) {n : E3}
    (hn : ‖n‖ = 1) {r : ℝ} (hr : a ≤ r) :
    onePlusZ (u1 a ρ δ) r n = 1 ∧ onePlusZ u0 r n = 1 := by
  refine ⟨?_, onePlusZ_u0 r n⟩
  rw [onePlusZ_u1_ray δ hn (by linarith),
    G10C.smoothCutoff_support ha hρ (by rw [abs_of_nonneg (by linarith)]; linarith)]
  simp

/-- C3e -/
theorem extData_eq (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    extData (u1 a ρ δ) a = extData u0 a := by
  funext r n
  have hn : ‖(n : E3)‖ = 1 := by simpa using n.2
  have h := exterior_redshift_agree ha hρ δ hn (Set.mem_Ici.mp r.2)
  simp only [extData, h.1, h.2]

/-- C3l: any observation model depending only on the exterior data gives identical laws. -/
theorem cutout_laws_identical (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ)
    {Ω : Type*} [MeasurableSpace Ω] (obs : ExtData a → Measure Ω) :
    obs (extData u0 a) = obs (extData (u1 a ρ δ) a) := by
  rw [extData_eq ha hρ δ]

/-! ### Ray second derivative: (I13) and (I14) -/

/-- Ray profile `cosh(δ q s) + c sinh(δ q s)`. -/
noncomputable def prof (a : ℝ) (ρ : ℝ → ℝ) (δ c s : ℝ) : ℝ :=
  cosh (δ * G10C.smoothCutoff a ρ s) + c * sinh (δ * G10C.smoothCutoff a ρ s)

noncomputable def prof1 (a : ℝ) (ρ : ℝ → ℝ) (δ c s : ℝ) : ℝ :=
  (sinh (δ * G10C.smoothCutoff a ρ s) + c * cosh (δ * G10C.smoothCutoff a ρ s)) *
    (δ * deriv (G10C.smoothCutoff a ρ) s)

noncomputable def prof2 (a : ℝ) (ρ : ℝ → ℝ) (δ c s : ℝ) : ℝ :=
  (cosh (δ * G10C.smoothCutoff a ρ s) + c * sinh (δ * G10C.smoothCutoff a ρ s)) *
      (δ * deriv (G10C.smoothCutoff a ρ) s) * (δ * deriv (G10C.smoothCutoff a ρ) s) +
    (sinh (δ * G10C.smoothCutoff a ρ s) + c * cosh (δ * G10C.smoothCutoff a ρ s)) *
      (δ * deriv (deriv (G10C.smoothCutoff a ρ)) s)

theorem smoothCutoff_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (s : ℝ) :
    HasDerivAt (G10C.smoothCutoff a ρ) (deriv (G10C.smoothCutoff a ρ) s) s :=
  ((G10C.smoothCutoff_contDiff ha hρ).differentiable (by simp)).differentiableAt.hasDerivAt

theorem deriv_smoothCutoff_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (s : ℝ) :
    HasDerivAt (deriv (G10C.smoothCutoff a ρ)) (deriv (deriv (G10C.smoothCutoff a ρ)) s) s := by
  have h : ContDiff ℝ (⊤ : ℕ∞) (G10C.smoothCutoff a ρ) := G10C.smoothCutoff_contDiff ha hρ
  have h' : ContDiff ℝ (⊤ : ℕ∞) (deriv (G10C.smoothCutoff a ρ)) := (contDiff_infty_iff_deriv.mp h).2
  exact (h'.differentiable (by simp)).differentiableAt.hasDerivAt

theorem prof_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ c s : ℝ) :
    HasDerivAt (prof a ρ δ c) (prof1 a ρ δ c s) s := by
  have hq := (smoothCutoff_hasDerivAt ha hρ s).const_mul δ
  have h := hq.cosh.add (hq.sinh.const_mul c)
  refine h.congr_deriv ?_
  simp only [prof1]
  ring

theorem prof1_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ c s : ℝ) :
    HasDerivAt (prof1 a ρ δ c) (prof2 a ρ δ c s) s := by
  have hq := (smoothCutoff_hasDerivAt ha hρ s).const_mul δ
  have hq' := (deriv_smoothCutoff_hasDerivAt ha hρ s).const_mul δ
  have hA := hq.sinh.add (hq.cosh.const_mul c)
  have h := hA.mul hq'
  refine h.congr_deriv ?_
  simp only [prof2, Pi.add_apply]
  ring

theorem deriv_deriv_prof (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ c s : ℝ) :
    deriv (deriv (prof a ρ δ c)) s = prof2 a ρ δ c s := by
  have h1 : deriv (prof a ρ δ c) = prof1 a ρ δ c :=
    funext fun t => (prof_hasDerivAt ha hρ δ c t).deriv
  rw [h1]
  exact (prof1_hasDerivAt ha hρ δ c s).deriv

theorem prof2_bound (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {δ c : ℝ} (hδ : 0 ≤ δ)
    (hc : |c| ≤ 1) (s : ℝ) :
    |prof2 a ρ δ c s| ≤ exp δ / a ^ 2 * (40 / √3 * δ + 225 / 16 * δ ^ 2) := by
  unfold prof2
  set q := G10C.smoothCutoff a ρ with hqdef
  have hq := G10C.smoothCutoff_mem ha hρ s
  have hq1 := G10C.smoothCutoff_deriv_bound ha hρ s
  have hq2 := G10C.smoothCutoff_deriv2_bound ha hρ s
  rw [← hqdef] at hq hq1 hq2
  set t := δ * q s with htdef
  have ht0 : 0 ≤ t := mul_nonneg hδ hq.1
  have htδ : t ≤ δ := by nlinarith [hq.2]
  have hsh : 0 ≤ sinh t := sinh_nonneg_iff.mpr ht0
  have hch := cosh_pos t
  have hex : cosh t + sinh t ≤ exp δ := by rw [cosh_add_sinh]; exact exp_le_exp.mpr htδ
  have hc' := abs_le.mp hc
  have hA : |cosh t + c * sinh t| ≤ exp δ := by
    rw [abs_le]; constructor <;>
      nlinarith [mul_nonneg (by linarith : (0:ℝ) ≤ 1 - c) hsh,
        mul_nonneg (by linarith : (0:ℝ) ≤ 1 + c) hsh]
  have hB : |sinh t + c * cosh t| ≤ exp δ := by
    rw [abs_le]; constructor <;>
      nlinarith [mul_nonneg (by linarith : (0:ℝ) ≤ 1 - c) hch.le,
        mul_nonneg (by linarith : (0:ℝ) ≤ 1 + c) hch.le]
  have h3 : (0:ℝ) < √3 := by positivity
  calc _ ≤ |cosh t + c * sinh t| * (δ * |deriv q s|) * (δ * |deriv q s|) +
        |sinh t + c * cosh t| * (δ * |deriv (deriv q) s|) := by
        refine (abs_add_le _ _).trans ?_
        simp only [abs_mul, abs_of_nonneg hδ]
        exact le_rfl
    _ ≤ exp δ * (δ * (15 / (4 * a))) * (δ * (15 / (4 * a))) +
        exp δ * (δ * (40 / (√3 * a ^ 2))) := by
        gcongr
    _ = exp δ / a ^ 2 * (40 / √3 * δ + 225 / 16 * δ ^ 2) := by
        field_simp
        ring

/-- C4a: (I13) along every ray, including the unobserved segment `0 ≤ r < a`. -/
theorem ray_second_deriv_I13 (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {δ : ℝ} (hδ : 0 ≤ δ)
    {n : E3} (hn : ‖n‖ = 1) {r : ℝ} (hr : 0 ≤ r) :
    |deriv (deriv (fun s => onePlusZ (u1 a ρ δ) s n)) r| ≤
      exp δ / a ^ 2 * (40 / √3 * δ + 225 / 16 * δ ^ 2) := by
  have hc : |n 0| ≤ 1 := by
    have := PiLp.norm_apply_le n 0
    rwa [Real.norm_eq_abs, hn] at this
  rcases lt_or_ge r (a / 8) with hra | hra
  · have hev : (fun s => onePlusZ (u1 a ρ δ) s n) =ᶠ[𝓝 r]
        fun _ => cosh δ + n 0 * sinh δ := by
      filter_upwards [Ioo_mem_nhds (by linarith : -(a / 8) < r) hra] with t ht
      have hx : ‖t • n‖ ≤ a / 8 := by
        rw [norm_smul, hn, mul_one, Real.norm_eq_abs]
        exact abs_le.mpr ⟨ht.1.le, ht.2.le⟩
      rw [onePlusZ_u1, chi, G10C.radial_plateau ha hρ hx, mul_one]
    rw [hev.deriv.deriv_eq]
    simp only [deriv_const', abs_zero]
    exact mul_nonneg (by positivity) (add_nonneg (mul_nonneg (by positivity) hδ) (by positivity))
  · have hr0 : 0 < r := by linarith
    have hev : (fun s => onePlusZ (u1 a ρ δ) s n) =ᶠ[𝓝 r] prof a ρ δ (n 0) := by
      filter_upwards [Ioi_mem_nhds hr0] with t ht
      rw [onePlusZ_u1_ray δ hn (le_of_lt ht)]
      rfl
    rw [hev.deriv.deriv_eq, deriv_deriv_prof ha hρ]
    exact prof2_bound ha hρ hδ hc r

theorem exp_one_div_25_le : exp (1 / 25) ≤ 25 / 24 := by
  have h := add_one_le_exp (-(1 / 25 : ℝ))
  have hpos := exp_pos (1 / 25 : ℝ)
  have hmul : exp (1 / 25) * exp (-(1 / 25)) = 1 := by rw [← exp_add]; simp
  nlinarith

theorem sqrt3_ge : (12 : ℝ) / 7 ≤ √3 := Real.le_sqrt_of_sq_le (by norm_num)

/-- C5 -/
theorem deltaOf_pos (ha : 0 < a) {M : ℝ} (hM : 0 < M) : 0 < deltaOf M a := by
  unfold deltaOf
  have : 0 < min 1 (M * a ^ 2) := lt_min one_pos (by positivity)
  positivity

/-- C4b: (I14) with the rational certificate `e^{1/25} < 25/24`, `√3 > 12/7`. -/
theorem I14_bound (ha : 0 < a) {M : ℝ} (hM : 0 < M) :
    exp (deltaOf M a) / a ^ 2 * (40 / √3 * deltaOf M a + 225 / 16 * deltaOf M a ^ 2) ≤
      1147 / 1152 * M := by
  set s := min 1 (M * a ^ 2) with hs
  have hs0 : 0 < s := lt_min one_pos (by positivity)
  have hs1 : s ≤ 1 := min_le_left _ _
  have hsM : s ≤ M * a ^ 2 := min_le_right _ _
  have hδ : deltaOf M a = s / 25 := rfl
  rw [hδ]
  have he : exp (s / 25) ≤ 25 / 24 := (exp_le_exp.mpr (by linarith)).trans exp_one_div_25_le
  have h3pos : (0:ℝ) < √3 := by positivity
  have h3 : 40 / √3 ≤ 70 / 3 := by
    rw [div_le_div_iff₀ h3pos (by norm_num)]
    nlinarith [sqrt3_ge]
  have ha2 : 0 < a ^ 2 := by positivity
  have hss : s * s ≤ s * 1 := mul_le_mul_of_nonneg_left hs1 hs0.le
  have hin : 40 / √3 * (s / 25) + 225 / 16 * (s / 25) ^ 2 ≤ 1147 / 1200 * s := by
    nlinarith [mul_le_mul_of_nonneg_right h3 (by positivity : (0:ℝ) ≤ s / 25)]
  calc exp (s / 25) / a ^ 2 * (40 / √3 * (s / 25) + 225 / 16 * (s / 25) ^ 2)
      ≤ (25 / 24) / a ^ 2 * (1147 / 1200 * s) := by gcongr
    _ = 1147 / 1152 * (s / a ^ 2) := by field_simp; ring
    _ ≤ 1147 / 1152 * M := by
        gcongr
        rw [div_le_iff₀ ha2]
        linarith

/-- C4: the prescribed bound `|∂_r²(1+z)| ≤ M` for the boosted field. -/
theorem ray_second_deriv_bound (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {M : ℝ} (hM : 0 < M)
    {n : E3} (hn : ‖n‖ = 1) {r : ℝ} (hr : 0 ≤ r) :
    |deriv (deriv (fun s => onePlusZ (u1 a ρ (deltaOf M a)) s n)) r| ≤ M :=
  (ray_second_deriv_I13 ha hρ (deltaOf_pos ha hM).le hn hr).trans
    ((I14_bound ha hM).trans (by linarith))

/-- C4 (observer field). -/
theorem ray_second_deriv_bound_u0 {M : ℝ} (hM : 0 ≤ M) (n : E3) (r : ℝ) :
    |deriv (deriv (fun s => onePlusZ u0 s n)) r| ≤ M := by
  simp only [onePlusZ_u0, deriv_const', abs_zero]
  exact hM

theorem chi_origin (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) : chi a ρ δ 0 = δ := by
  rw [chi, norm_zero, G10C.smoothCutoff_plateau ha hρ (by rw [abs_zero]; positivity), mul_one]

/-- C5: source value of the boosted field. -/
theorem u1_origin (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    u1 a ρ δ 0 = ![cosh δ, sinh δ, 0, 0] := by
  rw [u1, chi_origin ha hρ]

/-- C5: Lorentz-invariant relative factor `-g(u1(0), u0(0)) = cosh δ` (relative rapidity δ). -/
theorem relative_lorentz_factor (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    -mink (u1 a ρ δ 0) (u0 0) = cosh δ := by
  rw [u1_origin ha hρ]; simp [mink, u0, obsVec]

/-- C5r -/
theorem rapidity_separation (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    dist (sourceRapidity (u1 a ρ δ)) (sourceRapidity u0) = |δ| := by
  simp [sourceRapidity, u1_origin ha hρ, u0, obsVec, arsinh_sinh]

/-- C5d -/
theorem dipole_separation (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {δ : ℝ} (hδ : 0 ≤ δ) :
    dist (interceptDipole (u1 a ρ δ)) (interceptDipole u0) = sinh δ ∧ δ ≤ sinh δ := by
  refine ⟨?_, self_le_sinh_iff.mpr hδ⟩
  rw [EuclideanSpace.dist_eq]
  simp [interceptDipole, u1_origin ha hρ, u0, obsVec, Fin.sum_univ_succ, Real.dist_eq]
  rw [Real.sqrt_sq (sinh_nonneg_iff.mpr hδ)]

section CutoutFloors

variable {Ω : Type*} [MeasurableSpace Ω]

/-- C6r: confidence-set floor for the source rapidity, `D = δ`. -/
theorem cutout_rapidity_floor (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {M : ℝ} (hM : 0 < M)
    (obs : ExtData a → Measure Ω) [IsProbabilityMeasure (obs (extData u0 a))]
    (C : Ω → Set ℝ) (α : ℝ)
    (hm₀ : MeasurableSet {ω | sourceRapidity u0 ∈ C ω})
    (hm₁ : MeasurableSet {ω | sourceRapidity (u1 a ρ (deltaOf M a)) ∈ C ω})
    (hcov₀ : 1 - α ≤ (obs (extData u0 a)).real {ω | sourceRapidity u0 ∈ C ω})
    (hcov₁ : 1 - α ≤ (obs (extData (u1 a ρ (deltaOf M a)) a)).real
      {ω | sourceRapidity (u1 a ρ (deltaOf M a)) ∈ C ω}) :
    1 - 2 * α ≤ (obs (extData u0 a)).real
        {ω | ENNReal.ofReal (deltaOf M a) ≤ Metric.ediam (C ω)} ∧
    ENNReal.ofReal ((1 - 2 * α) * deltaOf M a) ≤
        ∫⁻ ω, Metric.ediam (C ω) ∂(obs (extData u0 a)) := by
  have hlaw := cutout_laws_identical ha hρ (deltaOf M a) obs
  have hD : dist (sourceRapidity u0) (sourceRapidity (u1 a ρ (deltaOf M a))) = deltaOf M a := by
    rw [dist_comm, rapidity_separation ha hρ, abs_of_pos (deltaOf_pos ha hM)]
  have h1 := (confidence_set_floor _ _ hlaw C _ _ α hm₀ hm₁ hcov₀ hcov₁).2
  have h2 := expected_diam_floor _ _ hlaw C _ _ α hm₀ hm₁ hcov₀ hcov₁
  rw [hD] at h1 h2
  exact ⟨h1, h2⟩

/-- C6d: confidence-set floor for the intercept dipole, `D = sinh δ`. -/
theorem cutout_dipole_floor (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {M : ℝ} (hM : 0 < M)
    (obs : ExtData a → Measure Ω) [IsProbabilityMeasure (obs (extData u0 a))]
    (C : Ω → Set E3) (α : ℝ)
    (hm₀ : MeasurableSet {ω | interceptDipole u0 ∈ C ω})
    (hm₁ : MeasurableSet {ω | interceptDipole (u1 a ρ (deltaOf M a)) ∈ C ω})
    (hcov₀ : 1 - α ≤ (obs (extData u0 a)).real {ω | interceptDipole u0 ∈ C ω})
    (hcov₁ : 1 - α ≤ (obs (extData (u1 a ρ (deltaOf M a)) a)).real
      {ω | interceptDipole (u1 a ρ (deltaOf M a)) ∈ C ω}) :
    1 - 2 * α ≤ (obs (extData u0 a)).real
        {ω | ENNReal.ofReal (sinh (deltaOf M a)) ≤ Metric.ediam (C ω)} ∧
    ENNReal.ofReal ((1 - 2 * α) * sinh (deltaOf M a)) ≤
        ∫⁻ ω, Metric.ediam (C ω) ∂(obs (extData u0 a)) := by
  have hlaw := cutout_laws_identical ha hρ (deltaOf M a) obs
  have hD : dist (interceptDipole u0) (interceptDipole (u1 a ρ (deltaOf M a))) =
      sinh (deltaOf M a) := by
    rw [dist_comm, (dipole_separation ha hρ (deltaOf_pos ha hM).le).1]
  have h1 := (confidence_set_floor _ _ hlaw C _ _ α hm₀ hm₁ hcov₀ hcov₁).2
  have h2 := expected_diam_floor _ _ hlaw C _ _ α hm₀ hm₁ hcov₀ hcov₁
  rw [hD] at h1 h2
  exact ⟨h1, h2⟩

/-- C6e: estimator floor for the intercept dipole. -/
theorem cutout_estimator_floor (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {M : ℝ} (hM : 0 < M)
    (obs : ExtData a → Measure Ω) [IsProbabilityMeasure (obs (extData u0 a))]
    (g : Ω → E3) (hg : Measurable g) :
    ENNReal.ofReal (sinh (deltaOf M a) / 2) ≤
      max (∫⁻ ω, edist (g ω) (interceptDipole u0) ∂(obs (extData u0 a)))
        (∫⁻ ω, edist (g ω) (interceptDipole (u1 a ρ (deltaOf M a)))
          ∂(obs (extData (u1 a ρ (deltaOf M a)) a))) := by
  have hlaw := cutout_laws_identical ha hρ (deltaOf M a) obs
  have hD : dist (interceptDipole u0) (interceptDipole (u1 a ρ (deltaOf M a))) =
      sinh (deltaOf M a) := by
    rw [dist_comm, (dipole_separation ha hρ (deltaOf_pos ha hM).le).1]
  have h := (estimator_risk_floor _ _ hlaw g hg (interceptDipole u0)
    (interceptDipole (u1 a ρ (deltaOf M a)))).2
  rwa [hD] at h

/-- C6e: estimator floor for the source rapidity. -/
theorem cutout_rapidity_estimator_floor (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {M : ℝ}
    (hM : 0 < M) (obs : ExtData a → Measure Ω) [IsProbabilityMeasure (obs (extData u0 a))]
    (g : Ω → ℝ) (hg : Measurable g) :
    ENNReal.ofReal (deltaOf M a / 2) ≤
      max (∫⁻ ω, edist (g ω) (sourceRapidity u0) ∂(obs (extData u0 a)))
        (∫⁻ ω, edist (g ω) (sourceRapidity (u1 a ρ (deltaOf M a)))
          ∂(obs (extData (u1 a ρ (deltaOf M a)) a))) := by
  have hlaw := cutout_laws_identical ha hρ (deltaOf M a) obs
  have hD : dist (sourceRapidity u0) (sourceRapidity (u1 a ρ (deltaOf M a))) = deltaOf M a := by
    rw [dist_comm, rapidity_separation ha hρ, abs_of_pos (deltaOf_pos ha hM)]
  have h := (estimator_risk_floor _ _ hlaw g hg (sourceRapidity u0)
    (sourceRapidity (u1 a ρ (deltaOf M a)))).2
  rwa [hD] at h

end CutoutFloors

/-- C7: packaged cutout pair (Theorem III) with its separations. -/
theorem g10d_cutout_main (ha : 0 < a) {M : ℝ} (hM : 0 < M) :
    ∃ ρ, G10C.IsMollifier a ρ ∧ 0 < deltaOf M a ∧
      ContDiff ℝ (⊤ : ℕ∞) (u1 a ρ (deltaOf M a)) ∧
      (∀ x, mink (u1 a ρ (deltaOf M a) x) (u1 a ρ (deltaOf M a) x) = -1 ∧
        0 < u1 a ρ (deltaOf M a) x 0) ∧
      extData (u1 a ρ (deltaOf M a)) a = extData u0 a ∧
      (∀ n : E3, ‖n‖ = 1 → ∀ r, 0 ≤ r →
        |deriv (deriv (fun s => onePlusZ (u1 a ρ (deltaOf M a)) s n)) r| ≤ M) ∧
      dist (sourceRapidity (u1 a ρ (deltaOf M a))) (sourceRapidity u0) = deltaOf M a ∧
      dist (interceptDipole (u1 a ρ (deltaOf M a))) (interceptDipole u0) =
        sinh (deltaOf M a) := by
  obtain ⟨ρ, hρ⟩ := G10C.exists_mollifier ha
  have hδ := deltaOf_pos ha hM
  refine ⟨ρ, hρ, hδ, u1_contDiff ha hρ _, fun x => u1_future_unit a ρ _ x, extData_eq ha hρ _,
    fun n hn r hr => ray_second_deriv_bound ha hρ hM hn hr, ?_,
    (dipole_separation ha hρ hδ.le).1⟩
  rw [rapidity_separation ha hρ, abs_of_pos hδ]

/-- N4: the cutout pair is a genuine pair. -/
theorem u1_ne_u0 (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) {M : ℝ} (hM : 0 < M) :
    u1 a ρ (deltaOf M a) ≠ u0 := by
  intro h
  have h1 := congrFun (congrFun h 0) 1
  rw [u1_origin ha hρ] at h1
  simp [u0, obsVec] at h1
  exact (deltaOf_pos ha hM).ne' h1

end Cutout

/-! ## Part N: negative controls -/

/-- N1: without equal laws the floor fails. -/
theorem law_equality_needed :
    ∃ (P₀ P₁ : Measure ℝ), IsProbabilityMeasure P₀ ∧ IsProbabilityMeasure P₁ ∧
      ∃ C : ℝ → Set ℝ, P₀.real {ω | (0:ℝ) ∈ C ω} = 1 ∧ P₁.real {ω | (1:ℝ) ∈ C ω} = 1 ∧
        P₀.real {ω | ENNReal.ofReal (dist (0:ℝ) 1) ≤ Metric.ediam (C ω)} = 0 := by
  refine ⟨Measure.dirac 0, Measure.dirac 1, inferInstance, inferInstance, fun ω => {ω}, ?_, ?_, ?_⟩
  · have : {ω : ℝ | (0:ℝ) ∈ ({ω} : Set ℝ)} = {0} := by ext ω; simp [eq_comm]
    rw [this]; simp [measureReal_def]
  · have : {ω : ℝ | (1:ℝ) ∈ ({ω} : Set ℝ)} = {1} := by ext ω; simp [eq_comm]
    rw [this]; simp [measureReal_def]
  · have : {ω : ℝ | ENNReal.ofReal (dist (0:ℝ) 1) ≤ Metric.ediam ({ω} : Set ℝ)} = ∅ := by
      ext ω; simp
    rw [this]; simp

/-- N2: the coverage hypothesis is satisfiable (constant two-point set). -/
theorem coverage_satisfiable {Ω Θ : Type*} [MeasurableSpace Ω] (P : Measure Ω)
    [IsProbabilityMeasure P] (θ₀ θ₁ : Θ) :
    P.real {ω | θ₀ ∈ (fun _ : Ω => ({θ₀, θ₁} : Set Θ)) ω} = 1 ∧
      P.real {ω | θ₁ ∈ (fun _ : Ω => ({θ₀, θ₁} : Set Θ)) ω} = 1 := by
  simp

/-- N3: Mathlib's real `diam` vanishes on unbounded sets; `ediam` is the faithful diameter. -/
theorem diam_vs_ediam_unbounded :
    Metric.diam (Set.univ : Set ℝ) = 0 ∧ Metric.ediam (Set.univ : Set ℝ) = ⊤ :=
  ⟨Metric.diam_univ_of_noncompact, Metric.ediam_univ_of_noncompact⟩

end G10D
