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

end G10D
