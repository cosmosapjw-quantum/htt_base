import Mathlib
import G15APhoton

open MeasureTheory Metric Filter Topology
open scoped RealInnerProductSpace Pointwise

namespace G15B

abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := sphere (0 : E3) 1

/-- Completeness of the operator space (an existing Mathlib instance, named explicitly
because unguided typeclass search times out on it). -/
instance instCLMComplete : CompleteSpace (E3 →L[ℝ] E3) := ContinuousLinearMap.instCompleteSpace

noncomputable def σS : Measure S2 := (volume : Measure E3).toSphere
noncomputable def bas (i : Fin 3) : E3 := EuclideanSpace.single i 1
noncomputable def Pt (e v : E3) : E3 := v - ⟪v, e⟫ • e
noncomputable def dS (f : E3 → ℝ) (e v : E3) : ℝ := fderiv ℝ f e (Pt e v)
noncomputable def gradS (f : E3 → ℝ) (e : E3) : E3 := ∑ i, dS f e (bas i) • bas i
noncomputable def divS (Y : E3 → E3) (e : E3) : ℝ := ∑ i, (fderiv ℝ Y e (Pt e (bas i))) i
def IsSkew (W : E3 →L[ℝ] E3) : Prop := ∀ x y, ⟪W x, y⟫ = -⟪x, W y⟫
noncomputable def trL (σ : E3 →L[ℝ] E3) : ℝ := ∑ i, (σ (bas i)) i
noncomputable def Ffield (a : E3) (σ : E3 →L[ℝ] E3) (x : E3) : E3 := Pt x (a + σ x)
noncomputable def Rrate3 (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) : ℝ :=
  H + ⟪a, e⟫ + ⟪e, σ e⟫
/-- The (B5) angular bracket `(4H - σ:ee) eeᵀ + a eᵀ + e aᵀ + (σe)eᵀ + e(σe)ᵀ`, entry `(i,j)`. -/
noncomputable def wB5 (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) (i j : Fin 3) : ℝ :=
  (4 * H - ⟪e, σ e⟫) * e i * e j + a i * e j + e i * a j + (σ e) i * e j + e i * (σ e) j

/-! ### coordinate algebra -/

lemma bas_apply (i j : Fin 3) : (bas i) j = if j = i then 1 else 0 := by
  simp [bas]

lemma inner_eq_sum (x y : E3) : ⟪x, y⟫ = ∑ i, x i * y i := by
  simp [PiLp.inner_apply, mul_comm]

lemma inner_bas_left (i : Fin 3) (v : E3) : ⟪bas i, v⟫ = v i := by
  simp [bas, EuclideanSpace.inner_single_left]

lemma inner_bas_right (i : Fin 3) (v : E3) : ⟪v, bas i⟫ = v i := by
  rw [real_inner_comm]; exact inner_bas_left i v

lemma decomp (v : E3) : v = ∑ k, v k • bas k := by
  ext i
  simp [bas_apply, Fin.sum_univ_three]
  fin_cases i <;> simp

lemma clm_comp_apply (D : E3 →L[ℝ] E3) (v : E3) (i : Fin 3) :
    (D v) i = ∑ k, (D (bas k)) i * v k := by
  conv_lhs => rw [decomp v]
  simp [map_sum, mul_comm]

lemma clm_real_apply (L : E3 →L[ℝ] ℝ) (v : E3) : L v = ∑ k, L (bas k) * v k := by
  conv_lhs => rw [decomp v]
  simp [map_sum, mul_comm]

lemma norm_one_sum {e : E3} (he : ‖e‖ = 1) : e 0 ^ 2 + e 1 ^ 2 + e 2 ^ 2 = 1 := by
  have h : ⟪e, e⟫ = 1 := by rw [real_inner_self_eq_norm_sq, he]; norm_num
  rw [inner_eq_sum, Fin.sum_univ_three] at h
  linarith [h]

lemma inner_self_one {e : E3} (he : ‖e‖ = 1) : ⟪e, e⟫ = 1 := by
  rw [real_inner_self_eq_norm_sq, he]; norm_num

/-! ### S: tangency and intrinsic character -/

theorem Pt_tangent {e : E3} (he : ‖e‖ = 1) (v : E3) : ⟪Pt e v, e⟫ = 0 := by
  simp [Pt, inner_sub_left, real_inner_smul_left, real_inner_self_eq_norm_sq, he]

noncomputable def PtL (e : E3) : E3 →L[ℝ] E3 :=
  ContinuousLinearMap.id ℝ E3 - (innerSL ℝ e).smulRight e

lemma Pt_eq_PtL (e v : E3) : Pt e v = PtL e v := by
  simp [Pt, PtL, real_inner_comm]

theorem gradS_inner (f : E3 → ℝ) (e v : E3) : ⟪gradS f e, v⟫ = dS f e v := by
  have h : dS f e v = ((fderiv ℝ f e).comp (PtL e)) v := by
    simp [dS, Pt_eq_PtL]
  rw [h, clm_real_apply]
  simp [gradS, sum_inner, real_inner_smul_left, inner_bas_left, dS, Pt_eq_PtL]

theorem gradS_tangent (f : E3 → ℝ) {e : E3} (he : ‖e‖ = 1) : ⟪gradS f e, e⟫ = 0 := by
  rw [gradS_inner]
  have : Pt e e = 0 := by simp [Pt, real_inner_self_eq_norm_sq, he]
  simp [dS, this]

theorem fderiv_eq_of_eqOn_sphere {F : Type*} [NormedAddCommGroup F] [NormedSpace ℝ F]
    {f g : E3 → F} {e v : E3} (hf : DifferentiableAt ℝ f e) (hg : DifferentiableAt ℝ g e)
    (hfg : ∀ x ∈ sphere (0 : E3) 1, f x = g x) (he : ‖e‖ = 1) (hv : ⟪v, e⟫ = 0) :
    fderiv ℝ f e v = fderiv ℝ g e v := by
  by_cases hv0 : v = 0
  · simp [hv0]
  have hnv : ‖v‖ ≠ 0 := norm_ne_zero_iff.mpr hv0
  set u : E3 := ‖v‖⁻¹ • v with hu
  have hu1 : ‖u‖ = 1 := by
    rw [hu, norm_smul, norm_inv, norm_norm, inv_mul_cancel₀ hnv]
  have hue : ⟪u, e⟫ = 0 := by rw [hu, real_inner_smul_left, hv, mul_zero]
  have hvu : v = ‖v‖ • u := by rw [hu, smul_smul, mul_inv_cancel₀ hnv, one_smul]
  clear_value u
  let γ : ℝ → E3 := fun t => Real.cos t • e + Real.sin t • u
  have hγ : ∀ t, γ t ∈ sphere (0 : E3) 1 := by
    intro t
    rw [mem_sphere_zero_iff_norm]
    have h2 : ‖γ t‖ ^ 2 = 1 := by
      simp only [γ]
      rw [norm_add_sq_real, norm_smul, norm_smul, real_inner_smul_left, real_inner_smul_right,
        real_inner_comm, hue, he, hu1, Real.norm_eq_abs, Real.norm_eq_abs]
      nlinarith [Real.cos_sq_add_sin_sq t, sq_abs (Real.cos t), sq_abs (Real.sin t)]
    have hn := norm_nonneg (γ t)
    nlinarith [h2, hn]
  have hγd : HasDerivAt γ u 0 := by
    have h := ((Real.hasDerivAt_cos 0).smul_const e).add ((Real.hasDerivAt_sin 0).smul_const u)
    have hd : -Real.sin 0 • e + Real.cos 0 • u = u := by simp
    rw [hd] at h
    exact h
  have hγ0 : γ 0 = e := by simp [γ]
  have h1 : HasDerivAt (f ∘ γ) (fderiv ℝ f e u) 0 := by
    have hf' : HasFDerivAt f (fderiv ℝ f e) (γ 0) := by rw [hγ0]; exact hf.hasFDerivAt
    exact hf'.comp_hasDerivAt 0 hγd
  have h2 : HasDerivAt (g ∘ γ) (fderiv ℝ g e u) 0 := by
    have hg' : HasFDerivAt g (fderiv ℝ g e) (γ 0) := by rw [hγ0]; exact hg.hasFDerivAt
    exact hg'.comp_hasDerivAt 0 hγd
  have heq : f ∘ γ = g ∘ γ := funext fun t => hfg _ (hγ t)
  rw [heq] at h1
  have hu_eq := h1.unique h2
  rw [hvu, map_smul, map_smul, hu_eq]

theorem dS_eq_of_eqOn_sphere {f g : E3 → ℝ} {e : E3} (hf : DifferentiableAt ℝ f e)
    (hg : DifferentiableAt ℝ g e) (hfg : ∀ x ∈ sphere (0 : E3) 1, f x = g x) (he : ‖e‖ = 1) :
    dS f e = dS g e := by
  funext v
  exact fderiv_eq_of_eqOn_sphere hf hg hfg he (Pt_tangent he v)

theorem divS_eq_of_eqOn_sphere {Y Z : E3 → E3} {e : E3} (hY : DifferentiableAt ℝ Y e)
    (hZ : DifferentiableAt ℝ Z e) (hYZ : ∀ x ∈ sphere (0 : E3) 1, Y x = Z x) (he : ‖e‖ = 1) :
    divS Y e = divS Z e := by
  unfold divS
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [fderiv_eq_of_eqOn_sphere hY hZ hYZ he (Pt_tangent he _)]

theorem dS_eq_fderiv_of_tangent (f : E3 → ℝ) {e X : E3} (he : ‖e‖ = 1) (hX : ⟪X, e⟫ = 0) :
    dS f e X = fderiv ℝ f e X := by
  simp [dS, Pt, hX]

theorem Ffield_tangent (a : E3) (σ : E3 →L[ℝ] E3) {e : E3} (he : ‖e‖ = 1) :
    ⟪Ffield a σ e, e⟫ = 0 :=
  Pt_tangent he _

theorem skew_tangent {W : E3 →L[ℝ] E3} (hW : IsSkew W) (e : E3) : ⟪W e, e⟫ = 0 := by
  have h := hW e e
  have h2 := real_inner_comm e (W e)
  linarith

/-! ### W: pointwise divergence weights -/

theorem divS_eq_trace (Y : E3 → E3) (e : E3) :
    divS Y e = ∑ i, (fderiv ℝ Y e (bas i)) i - ⟪e, fderiv ℝ Y e e⟫ := by
  unfold divS Pt
  simp only [map_sub, map_smul, PiLp.sub_apply, PiLp.smul_apply, smul_eq_mul, inner_bas_left,
    Finset.sum_sub_distrib, inner_eq_sum e]

theorem divS_skew {W : E3 →L[ℝ] E3} (hW : IsSkew W) (e : E3) : divS (fun x => W x) e = 0 := by
  rw [divS_eq_trace]
  have hfd : fderiv ℝ (fun x => W x) e = W := W.fderiv
  rw [hfd]
  have h1 : ∀ i, (W (bas i)) i = 0 := by
    intro i
    rw [← inner_bas_left i]
    have := skew_tangent hW (bas i)
    rw [real_inner_comm] at this
    exact this
  have h2 : ⟪e, W e⟫ = 0 := by rw [real_inner_comm]; exact skew_tangent hW e
  simp [h1, h2]


lemma hasFDerivAt_Ffield (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) :
    HasFDerivAt (Ffield a σ)
      (σ - (⟪a + σ e, e⟫ • ContinuousLinearMap.id ℝ E3 +
        ((fderivInnerCLM ℝ (a + σ e, e)).comp (σ.prod (ContinuousLinearMap.id ℝ E3))).smulRight e)) e := by
  have hA : HasFDerivAt (fun x => a + σ x) σ e := (σ.hasFDerivAt).const_add a
  have hI : HasFDerivAt (fun x : E3 => x) (ContinuousLinearMap.id ℝ E3) e := hasFDerivAt_id e
  have hin := hA.inner ℝ hI
  have hs := hin.smul hI
  have hF := hA.sub hs
  refine hF.congr_of_eventuallyEq (Eventually.of_forall fun x => ?_)
  simp [Ffield, Pt]

lemma fderiv_Ffield_apply (a : E3) (σ : E3 →L[ℝ] E3) (e v : E3) :
    fderiv ℝ (Ffield a σ) e v = σ v - (⟪σ v, e⟫ + ⟪a + σ e, v⟫) • e - ⟪a + σ e, e⟫ • v := by
  rw [(hasFDerivAt_Ffield a σ e).fderiv]
  simp [fderivInnerCLM_apply]
  module

theorem divS_Ffield (a : E3) (σ : E3 →L[ℝ] E3) {e : E3} (he : ‖e‖ = 1) :
    divS (Ffield a σ) e = trL σ - 2 * ⟪a, e⟫ - 3 * ⟪e, σ e⟫ := by
  have hn := norm_one_sum he
  rw [divS_eq_trace]
  simp only [fderiv_Ffield_apply, trL]
  simp only [inner_eq_sum, PiLp.sub_apply, PiLp.add_apply, PiLp.smul_apply, smul_eq_mul,
    Fin.sum_univ_three, bas_apply, clm_comp_apply σ e]
  simp
  linear_combination
    (3 * (e 0 * ((σ (bas 0)) 0 * e 0 + (σ (bas 1)) 0 * e 1 + (σ (bas 2)) 0 * e 2) +
      e 1 * ((σ (bas 0)) 1 * e 0 + (σ (bas 1)) 1 * e 1 + (σ (bas 2)) 1 * e 2) +
      e 2 * ((σ (bas 0)) 2 * e 0 + (σ (bas 1)) 2 * e 1 + (σ (bas 2)) 2 * e 2)) +
      2 * (a 0 * e 0 + a 1 * e 1 + a 2 * e 2)) * hn

theorem divS_Ffield_tracefree (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0) {e : E3}
    (he : ‖e‖ = 1) : divS (Ffield a σ) e = -2 * ⟪a, e⟫ - 3 * ⟪e, σ e⟫ := by
  rw [divS_Ffield a σ he, hσ]; ring

lemma hasFDerivAt_coord (i : Fin 3) (e : E3) :
    HasFDerivAt (fun x : E3 => x i) (EuclideanSpace.proj i : E3 →L[ℝ] ℝ) e :=
  (EuclideanSpace.proj i : E3 →L[ℝ] ℝ).hasFDerivAt

theorem fderiv_quadWeight (i j : Fin 3) (e v : E3) :
    fderiv ℝ (fun x : E3 => x i * x j) e v = v i * e j + e i * v j := by
  have h : HasFDerivAt (fun x : E3 => x i * x j) _ e :=
    (hasFDerivAt_coord i e).mul (hasFDerivAt_coord j e)
  rw [h.fderiv]
  simp [EuclideanSpace.coe_proj]
  ring

theorem divS_smul {g : E3 → ℝ} {Y : E3 → E3} {e : E3} (hg : DifferentiableAt ℝ g e)
    (hY : DifferentiableAt ℝ Y e) :
    divS (fun x => g x • Y x) e = dS g e (Y e) + g e * divS Y e := by
  have hd := hg.hasFDerivAt.smul hY.hasFDerivAt
  have hfd : fderiv ℝ (fun x => g x • Y x) e =
      g e • fderiv ℝ Y e + (fderiv ℝ g e).smulRight (Y e) := hd.fderiv
  have hdS : dS g e (Y e) = ∑ k, dS g e (bas k) * (Y e) k := by
    have h1 : ∀ v, dS g e v = ((fderiv ℝ g e).comp (PtL e)) v := by
      intro v; simp [dS, Pt_eq_PtL]
    rw [h1, clm_real_apply]
    simp [h1]
  unfold divS
  rw [hfd, hdS]
  simp only [ContinuousLinearMap.add_apply, ContinuousLinearMap.smul_apply,
    ContinuousLinearMap.smulRight_apply, PiLp.add_apply, PiLp.smul_apply, smul_eq_mul,
    Finset.sum_add_distrib, Finset.mul_sum]
  simp only [dS]
  ring_nf


/-! ### M: rotation-invariant measure -/

noncomputable def sphMap (L : E3 ≃ₗᵢ[ℝ] E3) (e : S2) : S2 :=
  ⟨L e, by simp [mem_sphere_zero_iff_norm, LinearIsometryEquiv.norm_map]⟩

def RotInv (μ : Measure S2) : Prop :=
  ∀ L : E3 ≃ₗᵢ[ℝ] E3, MeasurePreserving (sphMap L) μ μ

lemma continuous_sphMap (L : E3 ≃ₗᵢ[ℝ] E3) : Continuous (sphMap L) :=
  (L.continuous.comp continuous_subtype_val).subtype_mk _

noncomputable def sphEquiv (L : E3 ≃ₗᵢ[ℝ] E3) : S2 ≃ᵐ S2 where
  toFun := sphMap L
  invFun := sphMap L.symm
  left_inv e := by ext1; simp [sphMap]
  right_inv e := by ext1; simp [sphMap]
  measurable_toFun := (continuous_sphMap L).measurable
  measurable_invFun := (continuous_sphMap L.symm).measurable

theorem σS_rotInv : RotInv σS := by
  intro L
  have hme : Measurable (sphMap L) := (continuous_sphMap L).measurable
  refine ⟨hme, ?_⟩
  ext s hs
  rw [Measure.map_apply hme hs]
  simp only [σS]
  rw [Measure.toSphere_apply' _ (hme hs), Measure.toSphere_apply' _ hs]
  congr 1
  have hset : Set.Ioo (0 : ℝ) 1 • ((↑) '' (sphMap L ⁻¹' s) : Set E3) =
      L ⁻¹' (Set.Ioo (0 : ℝ) 1 • ((↑) '' s)) := by
    ext x
    simp only [Set.mem_smul, Set.mem_image, Set.mem_preimage]
    constructor
    · rintro ⟨r, hr, _, ⟨y, hy, rfl⟩, rfl⟩
      exact ⟨r, hr, _, ⟨sphMap L y, hy, rfl⟩, by simp [sphMap, map_smul]⟩
    · rintro ⟨r, hr, _, ⟨z, hz, rfl⟩, hx⟩
      refine ⟨r, hr, _, ⟨sphMap L.symm z, ?_, rfl⟩, ?_⟩
      · have : sphMap L (sphMap L.symm z) = z := by ext1; simp [sphMap]
        rw [this]; exact hz
      · have hx' : x = L.symm (r • (z : E3)) := by rw [hx]; simp
        rw [hx', map_smul]; rfl
  rw [hset]
  exact (L.measurePreserving).measure_preimage_emb L.toHomeomorph.measurableEmbedding _

lemma integral_rot {μ : Measure S2} (hμ : RotInv μ) (L : E3 ≃ₗᵢ[ℝ] E3) (g : E3 → ℝ) :
    ∫ e : S2, g (L e) ∂μ = ∫ e : S2, g e ∂μ :=
  (hμ L).integral_comp (sphEquiv L).measurableEmbedding (fun e : S2 => g e)

lemma integrable_cont (μ : Measure S2) [IsFiniteMeasure μ] {g : E3 → ℝ} (hg : Continuous g) :
    Integrable (fun e : S2 => g e) μ :=
  (hg.comp continuous_subtype_val).integrable_of_hasCompactSupport
    (HasCompactSupport.of_compactSpace _)

/-! ### D: Killing-field integral and the closed-sphere divergence theorem -/

lemma IsSkew.smul {W : E3 →L[ℝ] E3} (hW : IsSkew W) (t : ℝ) : IsSkew (t • W) := by
  intro x y
  simp [real_inner_smul_left, real_inner_smul_right, hW x y]

lemma skew_mem {W : E3 →L[ℝ] E3} (hW : IsSkew W) : W ∈ skewAdjoint (E3 →L[ℝ] E3) := by
  rw [skewAdjoint.mem_iff, ContinuousLinearMap.star_eq_adjoint]
  symm
  rw [ContinuousLinearMap.eq_adjoint_iff]
  intro x y
  simp [hW x y]

noncomputable def flowL {W : E3 →L[ℝ] E3} (hW : IsSkew W) (t : ℝ) : E3 ≃ₗᵢ[ℝ] E3 :=
  letI : NormedAlgebra ℚ (E3 →L[ℝ] E3) := NormedAlgebra.restrictScalars ℚ ℝ _
  Unitary.linearIsometryEquiv
    ⟨NormedSpace.exp (t • W), NormedSpace.exp_mem_unitary_of_mem_skewAdjoint (skew_mem (hW.smul t))⟩

lemma flowL_apply {W : E3 →L[ℝ] E3} (hW : IsSkew W) (t : ℝ) (x : E3) :
    flowL hW t x = NormedSpace.exp (t • W) x := rfl

theorem integral_fderiv_skew (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : E3 → ℝ} (hf : ContDiff ℝ 1 f) {W : E3 →L[ℝ] E3} (hW : IsSkew W) :
    ∫ e : S2, fderiv ℝ f e (W e) ∂μ = 0 := by
  have hdiff : Differentiable ℝ f := hf.differentiable (by norm_num)
  have hcf : Continuous (fderiv ℝ f) := hf.continuous_fderiv (by norm_num)
  obtain ⟨C, hC⟩ := (isCompact_sphere (0 : E3) 1).exists_bound_of_continuousOn hcf.continuousOn
  let Ex : ℝ → E3 →L[ℝ] E3 := fun t => NormedSpace.exp (t • W)
  have hnorm : ∀ t x, ‖Ex t x‖ = ‖x‖ := fun t x => (flowL hW t).norm_map x
  let F : ℝ → S2 → ℝ := fun t e => f (Ex t e)
  let F' : ℝ → S2 → ℝ := fun t e => fderiv ℝ f (Ex t e) ((Ex t * W) e)
  have hconst : ∀ t, ∫ e : S2, F t e ∂μ = ∫ e : S2, f e ∂μ := fun t =>
    integral_rot hμ (flowL hW t) f
  have hmain := hasDerivAt_integral_of_dominated_loc_of_deriv_le (μ := μ) (F := F) (F' := F')
    (x₀ := 0) (bound := fun _ => C * ‖W‖) (s := Set.univ) Filter.univ_mem
    (Eventually.of_forall fun t =>
      (hf.continuous.comp ((Ex t).continuous.comp continuous_subtype_val)).aestronglyMeasurable)
    (integrable_cont μ (hf.continuous.comp (Ex 0).continuous))
    ((hcf.comp ((Ex 0).continuous.comp continuous_subtype_val)).clm_apply
      ((Ex 0 * W).continuous.comp continuous_subtype_val)).aestronglyMeasurable
    (Eventually.of_forall fun e t _ => by
      have hs : Ex t e ∈ sphere (0 : E3) 1 := by
        rw [mem_sphere_zero_iff_norm, hnorm]; exact norm_eq_of_mem_sphere e
      have h1 : ‖fderiv ℝ f (Ex t e)‖ ≤ C := hC _ hs
      have h2 : ‖(Ex t * W) e‖ ≤ ‖W‖ := by
        rw [ContinuousLinearMap.mul_apply, hnorm]
        calc ‖W e‖ ≤ ‖W‖ * ‖(e : E3)‖ := W.le_opNorm _
          _ = ‖W‖ := by rw [norm_eq_of_mem_sphere e, mul_one]
      calc ‖F' t e‖ ≤ ‖fderiv ℝ f (Ex t e)‖ * ‖(Ex t * W) e‖ := (fderiv ℝ f (Ex t e)).le_opNorm _
        _ ≤ C * ‖W‖ := mul_le_mul h1 h2 (norm_nonneg _) ((norm_nonneg _).trans h1))
    (integrable_const _)
    (Eventually.of_forall fun e t _ => by
      have h1 : HasDerivAt (fun u : ℝ => Ex u) (Ex t * W) t := hasDerivAt_exp_smul_const W t
      have h2 : HasDerivAt (fun u : ℝ => Ex u (e : E3)) ((Ex t * W) e) t := by
        exact (ContinuousLinearMap.apply ℝ E3 (e : E3)).hasFDerivAt.comp_hasDerivAt t h1
      exact (hdiff _).hasFDerivAt.comp_hasDerivAt t h2)
  have h0 : HasDerivAt (fun t => ∫ e : S2, F t e ∂μ) 0 0 := by
    have : (fun t => ∫ e : S2, F t e ∂μ) = fun _ => ∫ e : S2, f e ∂μ := funext hconst
    rw [this]; exact hasDerivAt_const _ _
  have huniq := hmain.2.unique h0
  have hF0 : ∀ e : S2, F' 0 e = fderiv ℝ f e (W e) := by
    have hE0 : Ex 0 = 1 := by
      show NormedSpace.exp ((0 : ℝ) • W) = 1
      convert NormedSpace.exp_zero (𝔸 := E3 →L[ℝ] E3) using 2
      exact zero_smul ℝ W
    intro e
    simp only [F', hE0, ContinuousLinearMap.one_apply, one_mul]
  simpa [hF0] using huniq


/-! ### Killing generators and the divergence decomposition -/

noncomputable def Kuw (u w : E3) : E3 →L[ℝ] E3 :=
  (innerSL ℝ u).smulRight w - (innerSL ℝ w).smulRight u

lemma Kuw_apply (u w x : E3) : Kuw u w x = ⟪u, x⟫ • w - ⟪w, x⟫ • u := by
  simp [Kuw]

lemma Kuw_skew (u w : E3) : IsSkew (Kuw u w) := by
  intro x y
  simp only [Kuw_apply, inner_sub_left, inner_sub_right, real_inner_smul_left,
    real_inner_smul_right]
  rw [real_inner_comm w x, real_inner_comm u x]
  ring

/-- `h_{ij}(x) = x_i Y_j(x) - x_j Y_i(x)`, a component of `x × Y(x)`. -/
noncomputable def hpair (Y : E3 → E3) (i j : Fin 3) (x : E3) : ℝ := x i * (Y x) j - x j * (Y x) i

lemma hasFDerivAt_compY {Y : E3 → E3} {e : E3} (hY : DifferentiableAt ℝ Y e) (j : Fin 3) :
    HasFDerivAt (fun x => (Y x) j)
      ((EuclideanSpace.proj j : E3 →L[ℝ] ℝ).comp (fderiv ℝ Y e)) e :=
  (EuclideanSpace.proj j : E3 →L[ℝ] ℝ).hasFDerivAt.comp e hY.hasFDerivAt

lemma fderiv_hpair {Y : E3 → E3} {e : E3} (hY : DifferentiableAt ℝ Y e) (i j : Fin 3) (v : E3) :
    fderiv ℝ (hpair Y i j) e v =
      v i * (Y e) j + e i * (fderiv ℝ Y e v) j - (v j * (Y e) i + e j * (fderiv ℝ Y e v) i) := by
  have h : HasFDerivAt (hpair Y i j) _ e :=
    ((hasFDerivAt_coord i e).mul (hasFDerivAt_compY hY j)).sub
      ((hasFDerivAt_coord j e).mul (hasFDerivAt_compY hY i))
  rw [h.fderiv]
  simp [EuclideanSpace.coe_proj]
  ring

lemma contDiff_hpair {Y : E3 → E3} (hY : ContDiff ℝ 1 Y) (i j : Fin 3) :
    ContDiff ℝ 1 (hpair Y i j) := by
  have hc : ∀ k : Fin 3, ContDiff ℝ 1 (fun x : E3 => x k) := fun k =>
    (EuclideanSpace.proj k : E3 →L[ℝ] ℝ).contDiff
  have hYc : ∀ k : Fin 3, ContDiff ℝ 1 (fun x => (Y x) k) := fun k =>
    (EuclideanSpace.proj k : E3 →L[ℝ] ℝ).contDiff.comp hY
  exact ((hc i).mul (hYc j)).sub ((hc j).mul (hYc i))

/-- Pointwise: on S², for a tangent field, `div_S Y = Σ_k D h_k(e)(K_k e)`. -/
lemma divS_decomp {Y : E3 → E3} {e : E3} (hY : DifferentiableAt ℝ Y e) (he : ‖e‖ = 1)
    (ht : ⟪Y e, e⟫ = 0) :
    divS Y e = fderiv ℝ (hpair Y 1 2) e (Kuw (bas 1) (bas 2) e) +
      fderiv ℝ (hpair Y 2 0) e (Kuw (bas 2) (bas 0) e) +
      fderiv ℝ (hpair Y 0 1) e (Kuw (bas 0) (bas 1) e) := by
  have hn := norm_one_sum he
  have ht' : (Y e) 0 * e 0 + (Y e) 1 * e 1 + (Y e) 2 * e 2 = 0 := by
    rw [inner_eq_sum, Fin.sum_univ_three] at ht; exact ht
  rw [divS_eq_trace, fderiv_hpair hY, fderiv_hpair hY, fderiv_hpair hY]
  simp only [Kuw_apply, inner_bas_left, map_sub, map_smul, PiLp.sub_apply, PiLp.smul_apply,
    smul_eq_mul, bas_apply, inner_eq_sum e, clm_comp_apply (fderiv ℝ Y e) e, Fin.sum_univ_three]
  simp
  linear_combination
    (-((fderiv ℝ Y e (bas 0)) 0 + (fderiv ℝ Y e (bas 1)) 1 + (fderiv ℝ Y e (bas 2)) 2)) * hn +
      2 * ht'

theorem divergence_theorem (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {Y : E3 → E3} (hY : ContDiff ℝ 1 Y) (htan : ∀ x ∈ sphere (0 : E3) 1, ⟪Y x, x⟫ = 0) :
    ∫ e : S2, divS Y e ∂μ = 0 := by
  have hdY : Differentiable ℝ Y := hY.differentiable (by norm_num)
  have hpt : ∀ e : S2, divS Y e =
      fderiv ℝ (hpair Y 1 2) e (Kuw (bas 1) (bas 2) e) +
      fderiv ℝ (hpair Y 2 0) e (Kuw (bas 2) (bas 0) e) +
      fderiv ℝ (hpair Y 0 1) e (Kuw (bas 0) (bas 1) e) := fun e =>
    divS_decomp (hdY e) (norm_eq_of_mem_sphere e) (htan e e.2)
  have hint : ∀ (i j : Fin 3) (u w : E3),
      Integrable (fun e : S2 => fderiv ℝ (hpair Y i j) e (Kuw u w e)) μ := fun i j u w =>
    integrable_cont μ (g := fun x => fderiv ℝ (hpair Y i j) x (Kuw u w x))
      (((contDiff_hpair hY i j).continuous_fderiv (by norm_num)).clm_apply (Kuw u w).continuous)
  have i12 := hint 1 2 (bas 1) (bas 2)
  have i20 := hint 2 0 (bas 2) (bas 0)
  have i01 := hint 0 1 (bas 0) (bas 1)
  have i1220 : Integrable (fun e : S2 => fderiv ℝ (hpair Y 1 2) e (Kuw (bas 1) (bas 2) e) +
      fderiv ℝ (hpair Y 2 0) e (Kuw (bas 2) (bas 0) e)) μ := i12.add i20
  rw [integral_congr_ae (ae_of_all _ hpt), integral_add i1220 i01, integral_add i12 i20,
    integral_fderiv_skew μ hμ (contDiff_hpair hY 1 2) (Kuw_skew _ _),
    integral_fderiv_skew μ hμ (contDiff_hpair hY 2 0) (Kuw_skew _ _),
    integral_fderiv_skew μ hμ (contDiff_hpair hY 0 1) (Kuw_skew _ _)]
  norm_num

instance : IsFiniteMeasure σS := by unfold σS; infer_instance

theorem divergence_theorem_σS {Y : E3 → E3} (hY : ContDiff ℝ 1 Y)
    (htan : ∀ x ∈ sphere (0 : E3) 1, ⟪Y x, x⟫ = 0) : ∫ e : S2, divS Y e ∂σS = 0 :=
  divergence_theorem σS σS_rotInv hY htan

/-! ### N: negative control and non-vacuity -/

theorem divS_radial {e : E3} (he : ‖e‖ = 1) : divS (fun x => x) e = 2 := by
  rw [divS_eq_trace, fderiv_id']
  simp only [ContinuousLinearMap.id_apply]
  rw [real_inner_self_eq_norm_sq, he]
  simp [bas_apply, Fin.sum_univ_three]
  norm_num

theorem radial_negative_control : ∫ e : S2, divS (fun x => x) e ∂σS ≠ 0 := by
  have h : ∀ e : S2, divS (fun x => x) e = 2 := fun e => divS_radial (norm_eq_of_mem_sphere e)
  rw [integral_congr_ae (ae_of_all _ h), integral_const, smul_eq_mul]
  have hpos : 0 < σS.real Set.univ := by
    rw [measureReal_def]
    exact ENNReal.toReal_pos (Measure.measure_univ_ne_zero.mpr (Measure.toSphere_ne_zero _))
      (measure_ne_top _ _)
  positivity

noncomputable def Kz : E3 →L[ℝ] E3 := Kuw (bas 0) (bas 1)

theorem skew_witness : IsSkew Kz ∧ Kz ≠ 0 := by
  refine ⟨Kuw_skew _ _, fun h => ?_⟩
  have h1 := congrArg (fun L : E3 →L[ℝ] E3 => (L (bas 0)) 1) h
  simp [Kz, Kuw_apply, inner_bas_left, bas_apply] at h1
  have h2 := congrArg (fun v : E3 => v 0) h1
  simp [bas_apply] at h2

lemma contDiff_Ffield (a : E3) (σ : E3 →L[ℝ] E3) : ContDiff ℝ 1 (Ffield a σ) := by
  have hA : ContDiff ℝ 1 (fun x => a + σ x) := contDiff_const.add σ.contDiff
  have h : ContDiff ℝ 1 (fun x => (a + σ x) - ⟪a + σ x, x⟫ • x) :=
    hA.sub ((hA.inner ℝ contDiff_id).smul contDiff_id)
  convert h using 1
  funext x
  rfl

theorem witness_first_moment (a : E3) : ∫ e : S2, ⟪a, (e : E3)⟫ ∂σS = 0 := by
  have h := divergence_theorem_σS (contDiff_Ffield a 0)
    (fun x hx => Ffield_tangent a 0 (by simpa using hx))
  have hpt : ∀ e : S2, divS (Ffield a 0) e = -2 * ⟪a, (e : E3)⟫ := by
    intro e
    rw [divS_Ffield a 0 (norm_eq_of_mem_sphere e)]
    simp [trL]
  rw [integral_congr_ae (ae_of_all _ hpt), integral_const_mul] at h
  linarith


/-! ### I: integration by parts and the componentwise matrix identities -/

lemma continuous_divS {Y : E3 → E3} (hY : ContDiff ℝ 1 Y) : Continuous (divS Y) := by
  have hc := hY.continuous_fderiv (by norm_num : (1 : WithTop ℕ∞) ≠ 0)
  have h : divS Y = fun e => ∑ i, (fderiv ℝ Y e (bas i)) i - ⟪e, fderiv ℝ Y e e⟫ :=
    funext (divS_eq_trace Y)
  rw [h]
  refine (continuous_finset_sum _ fun i _ => ?_).sub (continuous_id.inner (hc.clm_apply continuous_id))
  exact (EuclideanSpace.proj i : E3 →L[ℝ] ℝ).continuous.comp (hc.clm_apply continuous_const)

lemma integral_dS_add_div (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ) {f : E3 → ℝ}
    (hf : ContDiff ℝ 1 f) {Y : E3 → E3} (hY : ContDiff ℝ 1 Y)
    (htan : ∀ x ∈ sphere (0 : E3) 1, ⟪Y x, x⟫ = 0) :
    ∫ e : S2, (fderiv ℝ f e (Y e) + f e * divS Y e) ∂μ = 0 := by
  have hZ : ContDiff ℝ 1 (fun x => f x • Y x) := hf.smul hY
  have htZ : ∀ x ∈ sphere (0 : E3) 1, ⟪f x • Y x, x⟫ = 0 := by
    intro x hx; rw [real_inner_smul_left, htan x hx, mul_zero]
  have h := divergence_theorem μ hμ hZ htZ
  have hpt : ∀ e : S2, divS (fun x => f x • Y x) e = fderiv ℝ f e (Y e) + f e * divS Y e := by
    intro e
    rw [divS_smul ((hf.differentiable (by norm_num)) e) ((hY.differentiable (by norm_num)) e),
      dS_eq_fderiv_of_tangent f (norm_eq_of_mem_sphere e) (htan e e.2)]
  rwa [integral_congr_ae (ae_of_all _ hpt)] at h

theorem ibp (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ) {f : E3 → ℝ}
    (hf : ContDiff ℝ 1 f) {Y : E3 → E3} (hY : ContDiff ℝ 1 Y)
    (htan : ∀ x ∈ sphere (0 : E3) 1, ⟪Y x, x⟫ = 0) :
    ∫ e : S2, fderiv ℝ f e (Y e) ∂μ = -∫ e : S2, f e * divS Y e ∂μ := by
  have h := integral_dS_add_div μ hμ hf hY htan
  have i1 : Integrable (fun e : S2 => fderiv ℝ f e (Y e)) μ :=
    integrable_cont μ (g := fun x => fderiv ℝ f x (Y x))
      ((hf.continuous_fderiv (by norm_num)).clm_apply hY.continuous)
  have i2 : Integrable (fun e : S2 => f e * divS Y e) μ :=
    integrable_cont μ (g := fun x => f x * divS Y x) (hf.continuous.mul (continuous_divS hY))
  rw [integral_add i1 i2] at h
  linarith

noncomputable def Mmom (μ : Measure S2) (I : E3 → ℝ) (i j : Fin 3) : ℝ :=
  ∫ e : S2, I e * (e : E3) i * (e : E3) j ∂μ

noncomputable def Wm (W : E3 →L[ℝ] E3) (i j : Fin 3) : ℝ := (W (bas j)) i

lemma Wm_skew {W : E3 →L[ℝ] E3} (hW : IsSkew W) (j k : Fin 3) : Wm W j k = -Wm W k j := by
  unfold Wm
  rw [← inner_bas_left j, ← inner_bas_left k, ← real_inner_comm (bas j) (W (bas k)), hW]

lemma apply_eq_Wm (W : E3 →L[ℝ] E3) (e : E3) (i : Fin 3) : (W e) i = ∑ k, Wm W i k * e k := by
  rw [clm_comp_apply]; rfl

lemma continuous_coord (k : Fin 3) : Continuous (fun x : E3 => x k) :=
  (EuclideanSpace.proj k : E3 →L[ℝ] ℝ).continuous

lemma fderiv_Iquad {I : E3 → ℝ} {e : E3} (hI : DifferentiableAt ℝ I e) (i j : Fin 3) (v : E3) :
    fderiv ℝ (fun x => I x * x i * x j) e v =
      fderiv ℝ I e v * e i * e j + I e * (v i * e j + e i * v j) := by
  have h : HasFDerivAt (fun x => I x * x i * x j) _ e :=
    (hI.hasFDerivAt.mul (hasFDerivAt_coord i e)).mul (hasFDerivAt_coord j e)
  rw [h.fderiv]
  simp [EuclideanSpace.coe_proj]
  ring

lemma contDiff_Iquad {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) (i j : Fin 3) :
    ContDiff ℝ 1 (fun x => I x * x i * x j) :=
  (hI.mul (EuclideanSpace.proj i : E3 →L[ℝ] ℝ).contDiff).mul
    (EuclideanSpace.proj j : E3 →L[ℝ] ℝ).contDiff

lemma integrable_quad (μ : Measure S2) [IsFiniteMeasure μ] {I : E3 → ℝ} (hI : Continuous I)
    (k l : Fin 3) : Integrable (fun e : S2 => I e * (e : E3) k * (e : E3) l) μ :=
  integrable_cont μ (g := fun x => I x * x k * x l)
    ((hI.mul (continuous_coord k)).mul (continuous_coord l))

theorem commutator_moments (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) {W : E3 →L[ℝ] E3} (hW : IsSkew W) (i j : Fin 3) :
    ∫ e : S2, fderiv ℝ I e (W e) * (e : E3) i * (e : E3) j ∂μ =
      ∑ k, (Mmom μ I i k * Wm W k j - Wm W i k * Mmom μ I k j) := by
  have hdI : Differentiable ℝ I := hI.differentiable (by norm_num)
  have h0 := integral_fderiv_skew μ hμ (contDiff_Iquad hI i j) hW
  have hpt : ∀ e : S2, fderiv ℝ (fun x => I x * x i * x j) e (W e) =
      fderiv ℝ I e (W e) * (e : E3) i * (e : E3) j +
        ((∑ k, Wm W i k * (I e * (e : E3) k * (e : E3) j)) -
          ∑ k, Wm W k j * (I e * (e : E3) i * (e : E3) k)) := by
    intro e
    rw [fderiv_Iquad (hdI e), apply_eq_Wm, apply_eq_Wm]
    simp only [Fin.sum_univ_three, Wm_skew hW j]
    ring
  have iA : Integrable (fun e : S2 => fderiv ℝ I e (W e) * (e : E3) i * (e : E3) j) μ :=
    integrable_cont μ (g := fun x => fderiv ℝ I x (W x) * x i * x j)
      ((((hI.continuous_fderiv (by norm_num)).clm_apply W.continuous).mul
        (continuous_coord i)).mul (continuous_coord j))
  have iS1 : Integrable (fun e : S2 => ∑ k, Wm W i k * (I e * (e : E3) k * (e : E3) j)) μ :=
    integrable_finset_sum _ fun k _ => (integrable_quad μ hI.continuous k j).const_mul _
  have iS2 : Integrable (fun e : S2 => ∑ k, Wm W k j * (I e * (e : E3) i * (e : E3) k)) μ :=
    integrable_finset_sum _ fun k _ => (integrable_quad μ hI.continuous i k).const_mul _
  have iS12 : Integrable (fun e : S2 => (∑ k, Wm W i k * (I e * (e : E3) k * (e : E3) j)) -
      ∑ k, Wm W k j * (I e * (e : E3) i * (e : E3) k)) μ := iS1.sub iS2
  rw [integral_congr_ae (ae_of_all _ hpt), integral_add iA iS12, integral_sub iS1 iS2,
    integral_finset_sum _ fun k _ => (integrable_quad μ hI.continuous k j).const_mul _,
    integral_finset_sum _ fun k _ => (integrable_quad μ hI.continuous i k).const_mul _] at h0
  simp only [integral_const_mul] at h0
  unfold Mmom
  simp only [Finset.sum_sub_distrib]
  have e1 : ∑ k, (∫ e : S2, I e * (e : E3) i * (e : E3) k ∂μ) * Wm W k j =
      ∑ k, Wm W k j * ∫ e : S2, I e * (e : E3) i * (e : E3) k ∂μ :=
    Finset.sum_congr rfl fun k _ => mul_comm _ _
  rw [e1]
  linarith

lemma Ffield_apply (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) (i : Fin 3) :
    (Ffield a σ e) i = a i + (σ e) i - (⟪a, e⟫ + ⟪e, σ e⟫) * e i := by
  simp [Ffield, Pt, inner_add_left, real_inner_comm e (σ e)]

lemma continuous_wB5 (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    Continuous (fun e : E3 => wB5 H a σ e i j) := by
  unfold wB5
  have ci := continuous_coord i
  have cj := continuous_coord j
  have csi : Continuous (fun e : E3 => (σ e) i) := ci.comp σ.continuous
  have csj : Continuous (fun e : E3 => (σ e) j) := cj.comp σ.continuous
  have cs : Continuous (fun e : E3 => ⟪e, σ e⟫) := continuous_id.inner σ.continuous
  exact (((((continuous_const.sub cs).mul ci).mul cj).add (continuous_const.mul cj)).add
    (ci.mul continuous_const)).add (csi.mul cj) |>.add (ci.mul csj)

theorem angular_B5 (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) (H : ℝ) (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0)
    (i j : Fin 3) :
    ∫ e : S2, (fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e) * (e : E3) i * (e : E3) j ∂μ
      = -∫ e : S2, I e * wB5 H a σ e i j ∂μ := by
  have hdI : Differentiable ℝ I := hI.differentiable (by norm_num)
  have hZ := integral_dS_add_div μ hμ (contDiff_Iquad hI i j) (contDiff_Ffield a σ)
    (fun x hx => Ffield_tangent a σ (by simpa using hx))
  have hpt : ∀ e : S2,
      (fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e) * (e : E3) i * (e : E3) j =
      (fderiv ℝ (fun x => I x * x i * x j) e (Ffield a σ e) +
          I e * (e : E3) i * (e : E3) j * divS (Ffield a σ) e) - I e * wB5 H a σ e i j := by
    intro e
    rw [fderiv_Iquad (hdI e), divS_Ffield_tracefree a hσ (norm_eq_of_mem_sphere e),
      Ffield_apply, Ffield_apply]
    unfold Rrate3 wB5
    ring
  have iZ : Integrable (fun e : S2 => fderiv ℝ (fun x => I x * x i * x j) e (Ffield a σ e) +
      I e * (e : E3) i * (e : E3) j * divS (Ffield a σ) e) μ :=
    integrable_cont μ (g := fun x => fderiv ℝ (fun x => I x * x i * x j) x (Ffield a σ x) +
      I x * x i * x j * divS (Ffield a σ) x)
      ((((contDiff_Iquad hI i j).continuous_fderiv (by norm_num)).clm_apply
        (contDiff_Ffield a σ).continuous).add
        ((contDiff_Iquad hI i j).continuous.mul (continuous_divS (contDiff_Ffield a σ))))
  have iW : Integrable (fun e : S2 => I e * wB5 H a σ e i j) μ :=
    integrable_cont μ (g := fun x => I x * wB5 H a σ x i j)
      (hI.continuous.mul (continuous_wB5 H a σ i j))
  rw [integral_congr_ae (ae_of_all _ hpt), integral_sub iZ iW, hZ, zero_sub]

theorem weak_residual_B5 (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) (H : ℝ) (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0)
    {Cc DI : E3 → ℝ} (i j : Fin 3)
    (hC : Integrable (fun e : S2 => Cc e * (e : E3) i * (e : E3) j) μ)
    (hD : Integrable (fun e : S2 => DI e * (e : E3) i * (e : E3) j) μ) :
    ∫ e : S2, (Cc e - DI e + fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e)
        * (e : E3) i * (e : E3) j ∂μ
      = ∫ e : S2, Cc e * (e : E3) i * (e : E3) j ∂μ - ∫ e : S2, DI e * (e : E3) i * (e : E3) j ∂μ
        - ∫ e : S2, I e * wB5 H a σ e i j ∂μ := by
  have hpt : ∀ e : S2,
      (Cc e - DI e + fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e)
        * (e : E3) i * (e : E3) j =
      (Cc e * (e : E3) i * (e : E3) j - DI e * (e : E3) i * (e : E3) j) +
        (fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e) * (e : E3) i * (e : E3) j := by
    intro e; ring
  have hR : Continuous (fun x : E3 => Rrate3 H a σ x) := by
    unfold Rrate3
    exact (continuous_const.add (continuous_const.inner continuous_id)).add
      (continuous_id.inner σ.continuous)
  have iA : Integrable (fun e : S2 =>
      (fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e) * (e : E3) i * (e : E3) j) μ :=
    integrable_cont μ (g := fun x => (fderiv ℝ I x (Ffield a σ x) - 4 * Rrate3 H a σ x * I x)
      * x i * x j)
      (((((hI.continuous_fderiv (by norm_num)).clm_apply (contDiff_Ffield a σ).continuous).sub
        ((continuous_const.mul hR).mul hI.continuous)).mul (continuous_coord i)).mul
        (continuous_coord j))
  have iCD : Integrable (fun e : S2 => Cc e * (e : E3) i * (e : E3) j -
      DI e * (e : E3) i * (e : E3) j) μ := hC.sub hD
  rw [integral_congr_ae (ae_of_all _ hpt), integral_add iCD iA, integral_sub hC hD,
    angular_B5 μ hμ hI H a hσ i j]
  ring

theorem weak_quadrupole_commutator (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) (H : ℝ) (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0)
    {W : E3 →L[ℝ] E3} (hW : IsSkew W) {Cc DI : E3 → ℝ} (i j : Fin 3)
    (hC : Integrable (fun e : S2 => Cc e * (e : E3) i * (e : E3) j) μ)
    (hD : Integrable (fun e : S2 => DI e * (e : E3) i * (e : E3) j) μ)
    (hB2 : ∀ e : S2, DI e + fderiv ℝ I e (W e - Ffield a σ e) + 4 * Rrate3 H a σ e * I e = Cc e) :
    ∫ e : S2, Cc e * (e : E3) i * (e : E3) j ∂μ - ∫ e : S2, DI e * (e : E3) i * (e : E3) j ∂μ
        - ∫ e : S2, I e * wB5 H a σ e i j ∂μ
      = ∑ k, (Mmom μ I i k * Wm W k j - Wm W i k * Mmom μ I k j) := by
  rw [← weak_residual_B5 μ hμ hI H a hσ i j hC hD, ← commutator_moments μ hμ hI hW i j]
  refine integral_congr_ae (ae_of_all _ fun e => ?_)
  have h := hB2 e
  rw [map_sub] at h
  have h' : Cc e - DI e + fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e =
      fderiv ℝ I e (W e) := by linarith
  simp only
  rw [h']


/-! ### G: angular polynomial degree ≤ 4 -/

section Poly
open MvPolynomial

/-- Explicit polynomial in `(e₀,e₁,e₂)` representing the (B5) weight. -/
noncomputable def pB5 (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    MvPolynomial (Fin 3) ℝ :=
  (C (4 * H) - ∑ k, ∑ l, C (Wm σ k l) * (X k * X l)) * (X i * X j) + C (a i) * X j +
    X i * C (a j) + (∑ l, C (Wm σ i l) * X l) * X j + X i * ∑ l, C (Wm σ j l) * X l

lemma eval_pB5 (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) (e : E3) :
    eval (fun k => e k) (pB5 H a σ i j) = wB5 H a σ e i j := by
  unfold pB5 wB5
  rw [inner_eq_sum e (σ e)]
  simp only [map_add, map_sub, map_mul, map_sum, eval_C, eval_X, apply_eq_Wm σ e]
  simp only [Fin.sum_univ_three]
  ring

lemma td_add {p q : MvPolynomial (Fin 3) ℝ} {n : ℕ} (hp : p.totalDegree ≤ n)
    (hq : q.totalDegree ≤ n) : (p + q).totalDegree ≤ n :=
  (totalDegree_add p q).trans (max_le hp hq)

lemma td_sub {p q : MvPolynomial (Fin 3) ℝ} {n : ℕ} (hp : p.totalDegree ≤ n)
    (hq : q.totalDegree ≤ n) : (p - q).totalDegree ≤ n :=
  (totalDegree_sub p q).trans (max_le hp hq)

lemma td_mul {p q : MvPolynomial (Fin 3) ℝ} {m n : ℕ} (hp : p.totalDegree ≤ m)
    (hq : q.totalDegree ≤ n) : (p * q).totalDegree ≤ m + n :=
  (totalDegree_mul p q).trans (add_le_add hp hq)

lemma td_sum {f : Fin 3 → MvPolynomial (Fin 3) ℝ} {n : ℕ} (h : ∀ k, (f k).totalDegree ≤ n) :
    (∑ k, f k).totalDegree ≤ n :=
  (totalDegree_finsetSum _ _).trans (Finset.sup_le fun k _ => h k)

lemma td_mono {p : MvPolynomial (Fin 3) ℝ} {m n : ℕ} (hp : p.totalDegree ≤ m) (h : m ≤ n) :
    p.totalDegree ≤ n := hp.trans h

lemma td_C (r : ℝ) : (C r : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 0 := (totalDegree_C r).le

lemma td_X (k : Fin 3) : (X k : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 1 := (totalDegree_X k).le

lemma pB5_totalDegree (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    (pB5 H a σ i j).totalDegree ≤ 4 := by
  have hXX : ∀ k l, (X k * X l : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 2 := fun k l =>
    td_mul (td_X k) (td_X l)
  have hCXX : ∀ r k l, (C r * (X k * X l) : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 2 :=
    fun r k l => td_mono (td_mul (td_C r) (hXX k l)) (by norm_num)
  have hCX : ∀ r k, (C r * X k : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 1 := fun r k =>
    td_mono (td_mul (td_C r) (td_X k)) (by norm_num)
  have hlin : ∀ i', (∑ l, C (Wm σ i' l) * X l : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 1 :=
    fun i' => td_sum fun l => hCX _ l
  have h1 : ((C (4 * H) - ∑ k, ∑ l, C (Wm σ k l) * (X k * X l)) * (X i * X j) :
      MvPolynomial (Fin 3) ℝ).totalDegree ≤ 4 :=
    td_mul (td_sub (td_mono (td_C _) (by norm_num)) (td_sum fun k => td_sum fun l => hCXX _ k l))
      (hXX i j)
  have h2 : (C (a i) * X j : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 4 :=
    td_mono (hCX _ _) (by norm_num)
  have h3 : (X i * C (a j) : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 4 :=
    td_mono (td_mul (td_X i) (td_C _)) (by norm_num)
  have h4 : ((∑ l, C (Wm σ i l) * X l) * X j : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 4 :=
    td_mono (td_mul (hlin i) (td_X j)) (by norm_num)
  have h5 : (X i * ∑ l, C (Wm σ j l) * X l : MvPolynomial (Fin 3) ℝ).totalDegree ≤ 4 :=
    td_mono (td_mul (td_X i) (hlin j)) (by norm_num)
  exact td_add (td_add (td_add (td_add h1 h2) h3) h4) h5

theorem wB5_degree_le_four (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      ∀ e : E3, MvPolynomial.eval (fun k => e k) p = wB5 H a σ e i j :=
  ⟨pB5 H a σ i j, pB5_totalDegree H a σ i j, eval_pB5 H a σ i j⟩

theorem B5_rank_le_four_moments (μ : Measure S2) [IsFiniteMeasure μ] {I : E3 → ℝ}
    (hI : Continuous I) (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      (∀ m ∈ p.support, (m.sum fun _ n => n) ≤ 4) ∧
      ∫ e : S2, I e * wB5 H a σ e i j ∂μ =
        ∑ m ∈ p.support, MvPolynomial.coeff m p * ∫ e : S2, I e * ∏ k, (e : E3) k ^ m k ∂μ := by
  refine ⟨pB5 H a σ i j, pB5_totalDegree H a σ i j,
    fun m hm => (le_totalDegree hm).trans (pB5_totalDegree H a σ i j), ?_⟩
  have hpt : ∀ e : S2, I e * wB5 H a σ e i j =
      ∑ m ∈ (pB5 H a σ i j).support,
        MvPolynomial.coeff m (pB5 H a σ i j) * (I e * ∏ k, (e : E3) k ^ m k) := by
    intro e
    rw [← eval_pB5, MvPolynomial.eval_eq', Finset.mul_sum]
    exact Finset.sum_congr rfl fun m _ => by ring
  have hint : ∀ m : Fin 3 →₀ ℕ, Integrable (fun e : S2 => I e * ∏ k, (e : E3) k ^ m k) μ :=
    fun m => integrable_cont μ (g := fun x => I x * ∏ k, x k ^ m k)
      (hI.mul (continuous_finset_prod _ fun k _ => (continuous_coord k).pow _))
  rw [integral_congr_ae (ae_of_all _ hpt),
    integral_finset_sum _ fun m _ => (hint m).const_mul _]
  exact Finset.sum_congr rfl fun m _ => integral_const_mul _ _

end Poly


/-! ### B: bridge to the reviewed G15-A definitions (imported unchanged) -/

/-- Rest-frame spatial embedding `x ↦ (0, x)` into the G15-A frame components. -/
def emb3 (x : E3) : G15A.V := ![0, x 0, x 1, x 2]

/-- Spatial part of a G15-A frame vector. -/
noncomputable def sp (X : G15A.V) : E3 := !₂[X 1, X 2, X 3]

lemma sp_add (X Y : G15A.V) : sp (X + Y) = sp X + sp Y := by
  ext i; fin_cases i <;> simp [sp]

lemma sp_smul (r : ℝ) (X : G15A.V) : sp (r • X) = r • sp X := by
  ext i; fin_cases i <;> simp [sp]

lemma sp_emb3 (x : E3) : sp (emb3 x) = x := by
  ext i; fin_cases i <;> simp [sp, emb3]

/-- `σ₄(X,Y) = ⟪σ (spatial X), spatial Y⟫`, the rest-frame lift of `σ`. -/
noncomputable def sig4 (σ : E3 →L[ℝ] E3) : LinearMap.BilinForm ℝ G15A.V :=
  LinearMap.mk₂ ℝ (fun X Y => ⟪σ (sp X), sp Y⟫)
    (fun X X' Y => by simp only [sp_add, map_add, inner_add_left])
    (fun r X Y => by simp only [sp_smul, map_smul, real_inner_smul_left, smul_eq_mul])
    (fun X Y Y' => by simp only [sp_add, inner_add_right])
    (fun r X Y => by simp only [sp_smul, real_inner_smul_right, smul_eq_mul])

lemma sig4_apply (σ : E3 →L[ℝ] E3) (X Y : G15A.V) : sig4 σ X Y = ⟪σ (sp X), sp Y⟫ := rfl

lemma mink_emb3 (x y : E3) : G15A.mink (emb3 x) (emb3 y) = ⟪x, y⟫ := by
  simp [G15A.mink, emb3, inner_eq_sum, Fin.sum_univ_three]

lemma mink_accel_emb3 {c : ℝ} (hc : c ≠ 0) (a z : E3) :
    G15A.mink (G15A.accel c (emb3 (c • a))) (emb3 z) = ⟪a, z⟫ := by
  rw [G15A.accel, G15A.mink_smul_left, mink_emb3, real_inner_smul_left]
  field_simp

theorem bridge_Fcov {c : ℝ} (hc : c ≠ 0) (a : E3) (σ : E3 →L[ℝ] E3) (e y : E3) :
    G15A.Fcov c (sig4 σ) (emb3 (c • a)) (emb3 e) (emb3 y) = ⟪Ffield a σ e, y⟫ := by
  rw [G15A.Fcov, mink_accel_emb3 hc, mink_accel_emb3 hc, sig4_apply, sig4_apply, sp_emb3, sp_emb3,
    mink_emb3]
  simp only [Ffield, Pt, inner_sub_left, inner_add_left, real_inner_smul_left]

theorem bridge_Rrate {c : ℝ} (hc : c ≠ 0) (θ : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) :
    G15A.Rrate c θ (sig4 σ) (emb3 (c • a)) (emb3 e) = Rrate3 (θ / 3) a σ e := by
  rw [G15A.Rrate, mink_accel_emb3 hc, sig4_apply, sp_emb3, Rrate3, real_inner_comm e (σ e)]

end G15B
