import Mathlib
open MeasureTheory Metric Set
open scoped RealInnerProductSpace ENNReal

abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := sphere (0 : E3) 1

lemma inner_eq3 (x y : E3) : ⟪x, y⟫ = x 0 * y 0 + x 1 * y 1 + x 2 * y 2 := by
  simp [PiLp.inner_apply, Fin.sum_univ_three] <;> ring

lemma det_rank_one (w v : E3) :
    (ContinuousLinearMap.id ℝ E3 + (innerSL ℝ w).smulRight v).det = 1 + ⟪w, v⟫ := by
  rw [ContinuousLinearMap.det, ← LinearMap.det_toMatrix (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis,
    Matrix.det_fin_three]
  simp [LinearMap.toMatrix_apply, inner_eq3]
  ring

lemma hasFDerivAt_norm3 {x : E3} (hx : x ≠ 0) :
    HasFDerivAt (fun y : E3 => ‖y‖) (‖x‖⁻¹ • innerSL ℝ x) x := by
  have hN : ‖x‖ ≠ 0 := norm_ne_zero_iff.2 hx
  have h1 := (hasStrictFDerivAt_norm_sq x).hasFDerivAt.sqrt (pow_ne_zero 2 hN)
  simp only [Real.sqrt_sq (norm_nonneg _)] at h1
  convert h1 using 1
  ext v
  simp
  field_simp

lemma radial_Iio {c : ℝ} (hc : 0 < c) :
    Measure.volumeIoiPow 2 {r : Ioi (0 : ℝ) | (r : ℝ) * c < 1} = ENNReal.ofReal (c⁻¹ ^ 3 / 3) := by
  have hset : {r : Ioi (0 : ℝ) | (r : ℝ) * c < 1} = Iio ⟨c⁻¹, inv_pos.2 hc⟩ := by
    ext r
    show (r : ℝ) * c < 1 ↔ (r : ℝ) < c⁻¹
    rw [← one_div, lt_div_iff₀ hc]
  rw [hset, Measure.volumeIoiPow_apply_Iio]
  norm_num

lemma lintegral_polar (f : E3 → ℝ≥0∞) :
    ∫⁻ x in ({0}ᶜ : Set E3), f x =
      ∫⁻ p : S2 × Ioi (0 : ℝ), f ((p.2 : ℝ) • (p.1 : E3))
        ∂((volume : Measure E3).toSphere.prod (Measure.volumeIoiPow 2)) := by
  rw [← lintegral_subtype_comap (measurableSet_singleton (0 : E3)).compl]
  have hmp := (volume : Measure E3).measurePreserving_homeomorphUnitSphereProd
  rw [finrank_euclideanSpace_fin] at hmp
  calc ∫⁻ x : ({0}ᶜ : Set E3), f x ∂(Measure.comap Subtype.val volume)
      = ∫⁻ x : ({0}ᶜ : Set E3), (fun p : S2 × Ioi (0 : ℝ) => f ((p.2 : ℝ) • (p.1 : E3)))
          (homeomorphUnitSphereProd E3 x) ∂(Measure.comap Subtype.val volume) := by
        congr 1; funext x
        simp only
        rw [← homeomorphUnitSphereProd_symm_apply_coe, Homeomorph.symm_apply_apply]
    _ = _ := hmp.lintegral_comp_emb (homeomorphUnitSphereProd E3).measurableEmbedding _

example (a b c : ℝ≥0∞) (h0 : c ≠ 0) (ht : c ≠ ⊤) (h : a * c = b * c) : a = b := by
  exact?

#check @setLIntegral_mono
#check @Set.indicator_of_notMem
#check @lintegral_indicator
#check @lintegral_image_eq_lintegral_abs_det_fderiv_mul
#check @MeasurableEmbedding.comap_apply
#check @Set.image_eq_preimage_of_inverse
#check @ne_zero_of_mem_unit_sphere
#check @inv_le_comm₀
#check @Measure.rnDeriv_withDensity
example : (volume : Measure E3).toSphere.IsOpenPosMeasure := inferInstance
example : IsFiniteMeasure (volume : Measure E3).toSphere := inferInstance
