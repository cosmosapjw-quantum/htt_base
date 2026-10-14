import Mathlib
open MeasureTheory Metric Set
open scoped RealInnerProductSpace ENNReal

abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := sphere (0 : E3) 1

lemma hasFDerivAt_norm3 {x : E3} (hx : x ≠ 0) :
    HasFDerivAt (fun y : E3 => ‖y‖) (‖x‖⁻¹ • innerSL ℝ x) x := by
  have hN : ‖x‖ ≠ 0 := norm_ne_zero_iff.2 hx
  have h1 := (hasStrictFDerivAt_norm_sq x).hasFDerivAt.sqrt (pow_ne_zero 2 hN)
  simp only [Real.sqrt_sq (norm_nonneg _)] at h1
  refine h1.congr_fderiv ?_
  ext v
  simp only [ContinuousLinearMap.smul_apply, innerSL_apply_apply, smul_eq_mul, nsmul_eq_mul]
  field_simp
  ring

lemma lintegral_polar (f : E3 → ℝ≥0∞) :
    ∫⁻ x in ({0}ᶜ : Set E3), f x =
      ∫⁻ p : S2 × Ioi (0 : ℝ), f ((p.2 : ℝ) • (p.1 : E3))
        ∂((volume : Measure E3).toSphere.prod (Measure.volumeIoiPow 2)) := by
  rw [← lintegral_subtype_comap (measurableSet_singleton (0 : E3)).compl]
  have hmp : MeasurePreserving (homeomorphUnitSphereProd E3) (Measure.comap Subtype.val volume)
      ((volume : Measure E3).toSphere.prod (Measure.volumeIoiPow 2)) := by
    have := (volume : Measure E3).measurePreserving_homeomorphUnitSphereProd
    rwa [finrank_euclideanSpace_fin] at this
  calc ∫⁻ x : ({0}ᶜ : Set E3), f x ∂(Measure.comap Subtype.val volume)
      = ∫⁻ x : ({0}ᶜ : Set E3), (fun p : S2 × Ioi (0 : ℝ) => f ((p.2 : ℝ) • (p.1 : E3)))
          (homeomorphUnitSphereProd E3 x) ∂(Measure.comap Subtype.val volume) := by
        congr 1; funext x
        simp only
        rw [← homeomorphUnitSphereProd_symm_apply_coe, Homeomorph.symm_apply_apply]
    _ = _ := hmp.lintegral_comp_emb (homeomorphUnitSphereProd E3).measurableEmbedding
          (fun p : S2 × Ioi (0 : ℝ) => f ((p.2 : ℝ) • (p.1 : E3)))
