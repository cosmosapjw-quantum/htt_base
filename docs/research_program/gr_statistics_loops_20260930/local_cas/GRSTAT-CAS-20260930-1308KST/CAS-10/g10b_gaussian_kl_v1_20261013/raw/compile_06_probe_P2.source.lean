import Mathlib

namespace G10BProbe2

open MeasureTheory ProbabilityTheory InformationTheory
open scoped ENNReal NNReal

/-- KL is invariant under a common measurable embedding. -/
theorem klDiv_map_of_measurableEmbedding {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    {f : α → β} (hf : MeasurableEmbedding f) (μ ν : Measure α) [IsFiniteMeasure μ]
    [IsFiniteMeasure ν] : klDiv (μ.map f) (ν.map f) = klDiv μ ν := by
  have hac : μ.map f ≪ ν.map f ↔ μ ≪ ν := by
    refine ⟨fun h s hs => ?_, hf.absolutelyContinuous_map⟩
    have h1 : (ν.map f) (f '' s) = 0 := by
      rw [hf.map_apply, hf.injective.preimage_image]; exact hs
    have h2 := h h1
    rwa [hf.map_apply, hf.injective.preimage_image] at h2
  by_cases h : μ ≪ ν
  · rw [klDiv_eq_lintegral_klFun_of_ac h, klDiv_eq_lintegral_klFun_of_ac (hac.2 h),
      hf.lintegral_map]
    refine lintegral_congr_ae ?_
    filter_upwards [hf.rnDeriv_map μ ν] with x hx
    rw [hx]
  · rw [klDiv_of_not_ac h, klDiv_of_not_ac (fun h' => h (hac.1 h'))]

/-- Tensorization of KL for products of probability measures. -/
theorem klDiv_prod {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ ν : Measure α) (μ' ν' : Measure β) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    [IsProbabilityMeasure μ'] [IsProbabilityMeasure ν'] :
    klDiv (μ.prod μ') (ν.prod ν') = klDiv μ ν + klDiv μ' ν' := by
  rw [← Measure.compProd_const, ← Measure.compProd_const, klDiv_compProd_eq_add,
    Measure.compProd_const, Measure.compProd_const]
  congr 1
  rw [← Measure.prod_swap (μ := μ') (ν := μ), ← Measure.prod_swap (μ := ν') (ν := μ)]
  have hemb : MeasurableEmbedding (Prod.swap : β × α → α × β) :=
    (MeasurableEquiv.prodComm : β × α ≃ᵐ α × β).measurableEmbedding
  rw [klDiv_map_of_measurableEmbedding hemb]
  rw [← Measure.compProd_const, ← Measure.compProd_const, klDiv_compProd_left]

theorem klDiv_pi_fin {X : Type} [MeasurableSpace X] :
    ∀ (n : ℕ) (P Q : Fin n → Measure X) [∀ i, IsProbabilityMeasure (P i)]
      [∀ i, IsProbabilityMeasure (Q i)],
      klDiv (Measure.pi P) (Measure.pi Q) = ∑ i, klDiv (P i) (Q i)
  | 0, P, Q, _, _ => by
    have hP := (measurePreserving_pi_empty P).map_eq
    have hQ := (measurePreserving_pi_empty Q).map_eq
    rw [← klDiv_map_of_measurableEmbedding
      (MeasurableEquiv.ofUniqueOfUnique ((i : Fin 0) → X) Unit).measurableEmbedding, hP, hQ]
    simp
  | n + 1, P, Q, _, _ => by
    have hP := (measurePreserving_piFinSuccAbove P 0).map_eq
    have hQ := (measurePreserving_piFinSuccAbove Q 0).map_eq
    rw [← klDiv_map_of_measurableEmbedding
      (MeasurableEquiv.piFinSuccAbove (fun _ => X) 0).measurableEmbedding, hP, hQ, klDiv_prod,
      klDiv_pi_fin n, Fin.sum_univ_succ]
    rfl

theorem klDiv_pi {ι X : Type} [Fintype ι] [MeasurableSpace X] (P Q : ι → Measure X)
    [∀ i, IsProbabilityMeasure (P i)] [∀ i, IsProbabilityMeasure (Q i)] :
    klDiv (Measure.pi P) (Measure.pi Q) = ∑ i, klDiv (P i) (Q i) := by
  let e : Fin (Fintype.card ι) ≃ ι := (Fintype.equivFin ι).symm
  have hP := (measurePreserving_piCongrLeft P e).map_eq
  have hQ := (measurePreserving_piCongrLeft Q e).map_eq
  rw [← hP, ← hQ, klDiv_map_of_measurableEmbedding
    (MeasurableEquiv.piCongrLeft (fun _ => X) e).measurableEmbedding,
    klDiv_pi_fin, Equiv.sum_comp e (fun i => klDiv (P i) (Q i))]

/-- KL divergence of two real Gaussians with common positive variance. -/
theorem klDiv_gaussianReal_same_var (a b : ℝ) {v : ℝ≥0} (hv : v ≠ 0) :
    klDiv (gaussianReal a v) (gaussianReal b v) = ENNReal.ofReal ((a - b) ^ 2 / (2 * v)) := by
  have hac : gaussianReal a v ≪ gaussianReal b v :=
    (gaussianReal_absolutelyContinuous a hv).trans (gaussianReal_absolutelyContinuous' b hv)
  have hvpos : (0 : ℝ) < v := by positivity
  -- explicit log-likelihood ratio
  have hrn : (gaussianReal a v).rnDeriv (gaussianReal b v) =ᵐ[volume]
      fun x => (gaussianPDF b v x)⁻¹ * gaussianPDF a v x := by
    rw [gaussianReal_of_var_ne_zero b hv]
    have h1 := Measure.rnDeriv_withDensity_right (gaussianReal a v) volume
      (measurable_gaussianPDF b v).aemeasurable
      (ae_of_all _ fun x => (gaussianPDF_pos _ hv x).ne') (ae_of_all _ fun _ => gaussianPDF_ne_top)
    filter_upwards [h1, rnDeriv_gaussianReal a v] with x hx hx2
    rw [hx, hx2]
  have hllr : llr (gaussianReal a v) (gaussianReal b v) =ᵐ[gaussianReal a v]
      fun x => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v) := by
    have hrn' := gaussianReal_absolutelyContinuous a hv hrn
    filter_upwards [hrn'] with x hx
    rw [llr, hx, ENNReal.toReal_mul, ENNReal.toReal_inv, toReal_gaussianPDF, toReal_gaussianPDF,
      gaussianPDFReal_def, gaussianPDFReal_def]
    have hs : 0 < (√(2 * Real.pi * v))⁻¹ := by positivity
    rw [mul_inv, inv_inv, Real.exp_neg, ← mul_assoc, mul_comm _ (√(2 * Real.pi * v))⁻¹,
      ← mul_assoc, mul_inv_cancel₀ hs.ne', one_mul, ← Real.exp_neg, Real.log_mul,
      Real.log_exp, Real.log_exp]
    · ring
    · positivity
    · positivity
  have hint_id : Integrable (fun x : ℝ => x) (gaussianReal a v) :=
    (memLp_id_gaussianReal 1).integrable le_rfl
  have hint : Integrable (fun x : ℝ => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v))
      (gaussianReal a v) := by
    have : (fun x : ℝ => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v)) =
        fun x => (2 * (a - b) / (2 * v)) * x + (b ^ 2 - a ^ 2) / (2 * v) := by
      funext x; field_simp; ring
    rw [this]
    exact (hint_id.const_mul _).add (integrable_const _)
  rw [klDiv_of_ac_of_integrable hac ((integrable_congr hllr).2 hint), integral_congr_ae hllr]
  simp only [measureReal_univ_eq_one, add_sub_cancel_right]
  congr 1
  have : (fun x : ℝ => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v)) =
      fun x => (2 * (a - b) / (2 * v)) * x + (b ^ 2 - a ^ 2) / (2 * v) := by
    funext x; field_simp; ring
  rw [this, integral_add (hint_id.const_mul _) (integrable_const _), integral_const_mul,
    integral_id_gaussianReal, integral_const]
  simp only [measureReal_univ_eq_one, one_smul, smul_eq_mul, one_mul]
  field_simp
  ring

end G10BProbe2
