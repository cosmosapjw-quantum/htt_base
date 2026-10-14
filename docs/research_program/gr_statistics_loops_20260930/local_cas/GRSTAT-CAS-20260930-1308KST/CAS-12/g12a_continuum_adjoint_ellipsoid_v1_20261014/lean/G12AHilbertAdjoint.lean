import Mathlib
import G12AContinuumAdjoint

/-!
G12-A T10 (supplementary, card lean_step 2 "bounded operator route"): under the bounded-route
hypotheses (measurable energy-only weight w(E) > 0 a.e., measurable bounded rate τ(E), jointly
measurable bounded kernel P, finite angular measure σ, s-finite energy measure ρ) the collision
operator `collOp σ τ P` descends to a bounded linear operator on L²(w(E) dν), dν = ρ ⊗ σ, and its
Hilbert-space adjoint (Mathlib `ContinuousLinearMap.adjoint`) is the transposed-kernel operator
`collAdj` (the same rate τ(E), kernel P(e',e)).  The pairing identity is derived from the
kernel-Fubini theorem `adjoint_pair` of the unchanged module `G12AContinuumAdjoint`.

Frozen signatures: `../FROZEN_TARGETS.md` §T10.  Placement in this second module (importing
`G12AContinuumAdjoint` unchanged) is recorded as an amendment in `../AUTHOR_RETURN.json`.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

namespace G12A

open G11A G11B G11C

/-! ## Weighted L² helpers -/

theorem inner_L2W {X : Type*} [MeasurableSpace X] (μ : Measure X) (W : X → ℝ)
    (hWm : Measurable W) (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) (A B : L2W μ W) :
    inner ℝ A B = ∫ x, W x * ((A : X → ℝ) x * (B : X → ℝ) x) ∂μ := by
  rw [L2.inner_def]
  simp only [G11C.real_inner_apply]
  exact integral_wmeas μ W hWm hW0 _

theorem norm_sq_L2W {X : Type*} [MeasurableSpace X] (μ : Measure X) (W : X → ℝ)
    (hWm : Measurable W) (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) (F : L2W μ W) :
    ‖F‖ ^ 2 = ∫ x, W x * (F : X → ℝ) x ^ 2 ∂μ := by
  rw [← real_inner_self_eq_norm_sq, inner_L2W μ W hWm hW0]
  congr 1
  funext x
  ring

section Hilbert

variable {Y S : Type*} [MeasurableSpace Y] [MeasurableSpace S]

/-! ## The bounded-route hypotheses -/

structure BoundedRoute (ρ : Measure Y) (σ : Measure S) (w τ : Y → ℝ) (P : S → S → ℝ) :
    Prop where
  hwm : Measurable w
  hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1
  hτm : Measurable τ
  τbd : ∃ τmax, ∀ E, |τ E| ≤ τmax
  hPm : Measurable (Function.uncurry P)
  Pbd : ∃ Pmax, ∀ e e', |P e e'| ≤ Pmax

theorem BoundedRoute.transpose {ρ : Measure Y} {σ : Measure S} {w τ : Y → ℝ} {P : S → S → ℝ}
    (hB : BoundedRoute ρ σ w τ P) : BoundedRoute ρ σ w τ (transposeKernel P) := by
  obtain ⟨M, hM⟩ := hB.Pbd
  exact ⟨hB.hwm, hB.hwpos, hB.hτm, hB.τbd, hB.hPm.comp measurable_swap,
    ⟨M, fun e e' => hM e' e⟩⟩

/-! ## a.e. congruence and section integrability -/

theorem gain_congr_ae (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] (P : S → S → ℝ)
    {F G : Y × S → ℝ} (h : F =ᵐ[ρ.prod σ] G) : gain σ P F =ᵐ[ρ.prod σ] gain σ P G := by
  have hmp := angSwap_measurePreserving ρ σ
  have hqf : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => p.1)
      ((ρ.prod σ).prod σ) (ρ.prod σ) := Measure.quasiMeasurePreserving_fst
  have hqs : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => (p.1.1, p.2))
      ((ρ.prod σ).prod σ) (ρ.prod σ) := hqf.comp hmp.quasiMeasurePreserving
  have h3 : ∀ᵐ p ∂((ρ.prod σ).prod σ), F (p.1.1, p.2) = G (p.1.1, p.2) :=
    hqs.ae (p := fun y => F y = G y) h
  filter_upwards [Measure.ae_ae_of_ae_prod h3] with x hx
  simp only [gain]
  refine integral_congr_ae ?_
  filter_upwards [hx] with e' he'
  rw [show F (x.1, e') = G (x.1, e') from he']

theorem collOp_congr_ae (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] (τ : Y → ℝ)
    (P : S → S → ℝ) {F G : Y × S → ℝ} (h : F =ᵐ[ρ.prod σ] G) :
    collOp σ τ P F =ᵐ[ρ.prod σ] collOp σ τ P G := by
  filter_upwards [gain_congr_ae ρ σ P h, h] with x h1 h2
  simp only [collOp]
  rw [h1, h2]

theorem section_integrable (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax)
    {K : Y × S → ℝ} (hK : MemLp K 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    ∀ᵐ x ∂(ρ.prod σ), Integrable (fun e' => P x.2 e' * K (x.1, e')) σ := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hwm.comp measurable_fst
  have hac : (ρ.prod σ) ≪ wmeas (ρ.prod σ) (fun x => w x.1) := ac_of_pos _ _ hWm hwpos
  have hKm : AEStronglyMeasurable K (ρ.prod σ) := hK.1.mono_ac hac
  have hK2 := wsq_integrable ρ σ w hwm hwpos hK
  have hmp := angSwap_measurePreserving ρ σ
  have hqf : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => p.1)
      ((ρ.prod σ).prod σ) (ρ.prod σ) := Measure.quasiMeasurePreserving_fst
  have hqs : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => (p.1.1, p.2))
      ((ρ.prod σ).prod σ) (ρ.prod σ) := hqf.comp hmp.quasiMeasurePreserving
  have hF : Integrable (fun p : (Y × S) × S => w p.1.1 * K (p.1.1, p.2) ^ 2)
      ((ρ.prod σ).prod σ) :=
    (hmp.integrable_comp_emb angSwap.measurableEmbedding).2 (hK2.comp_fst σ)
  have hKs : AEStronglyMeasurable (fun p : (Y × S) × S => K (p.1.1, p.2)) ((ρ.prod σ).prod σ) :=
    hKm.comp_quasiMeasurePreserving hqs
  have hsec := hF.prod_right_ae
  have hsecm := hKs.prodMk_left
  filter_upwards [hsec, hsecm, hwpos] with x hx hxm hxw
  have hk2 : Integrable (fun e' => K (x.1, e') ^ 2) σ := by
    refine (hx.const_mul (w x.1)⁻¹).congr (Eventually.of_forall fun e' => ?_)
    field_simp
  have hkL2 : MemLp (fun e' => K (x.1, e')) 2 σ := (memLp_two_iff_integrable_sq hxm).2 hk2
  have hPxm : AEStronglyMeasurable (fun e' => P x.2 e') σ :=
    (hPm.comp (measurable_const.prodMk measurable_id)).aestronglyMeasurable
  have hqL2 : MemLp (fun e' => P x.2 e' * K (x.1, e')) 2 σ :=
    hkL2.of_le_mul (hPxm.mul hxm) (Eventually.of_forall fun e' => by
      rw [Real.norm_eq_abs, Real.norm_eq_abs, abs_mul]
      exact mul_le_mul_of_nonneg_right (hP _ _) (abs_nonneg _))
  exact hqL2.integrable one_le_two

/-! ## The quantitative gain bound ∫ w (gain K)² ≤ Pmax² σ(S)² ∫ w K² -/

theorem gain_sq_integral_le (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax)
    {K : Y × S → ℝ} (hK : MemLp K 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    ∫ x, w x.1 * gain σ P K x ^ 2 ∂(ρ.prod σ) ≤
      Pmax ^ 2 * σ.real univ ^ 2 * ∫ x, w x.1 * K x ^ 2 ∂(ρ.prod σ) := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hwm.comp measurable_fst
  have hac : (ρ.prod σ) ≪ wmeas (ρ.prod σ) (fun x => w x.1) := ac_of_pos _ _ hWm hwpos
  have hKm : AEStronglyMeasurable K (ρ.prod σ) := hK.1.mono_ac hac
  have hK2 := wsq_integrable ρ σ w hwm hwpos hK
  have hmp := angSwap_measurePreserving ρ σ
  have hqf : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => p.1)
      ((ρ.prod σ).prod σ) (ρ.prod σ) := Measure.quasiMeasurePreserving_fst
  have hqs : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => (p.1.1, p.2))
      ((ρ.prod σ).prod σ) (ρ.prod σ) := hqf.comp hmp.quasiMeasurePreserving
  have hF : Integrable (fun p : (Y × S) × S => w p.1.1 * K (p.1.1, p.2) ^ 2)
      ((ρ.prod σ).prod σ) :=
    (hmp.integrable_comp_emb angSwap.measurableEmbedding).2 (hK2.comp_fst σ)
  have hKs : AEStronglyMeasurable (fun p : (Y × S) × S => K (p.1.1, p.2)) ((ρ.prod σ).prod σ) :=
    hKm.comp_quasiMeasurePreserving hqs
  have hPs : AEStronglyMeasurable (fun p : (Y × S) × S => P p.1.2 p.2) ((ρ.prod σ).prod σ) :=
    (hPm.comp ((measurable_snd.comp measurable_fst).prodMk measurable_snd)).aestronglyMeasurable
  have hgm : AEStronglyMeasurable (gain σ P K) (ρ.prod σ) :=
    (hPs.mul hKs).integral_prod_right'
  have hsec := hF.prod_right_ae
  have hsecm := hKs.prodMk_left
  have hdom : Integrable (fun x => Pmax ^ 2 * σ.real univ * ∫ e', w x.1 * K (x.1, e') ^ 2 ∂σ)
      (ρ.prod σ) :=
    hF.integral_prod_left.const_mul _
  have hbd : ∀ᵐ x ∂(ρ.prod σ), ‖w x.1 * gain σ P K x ^ 2‖ ≤
      Pmax ^ 2 * σ.real univ * ∫ e', w x.1 * K (x.1, e') ^ 2 ∂σ := by
    filter_upwards [hsec, hsecm, hwpos] with x hx hxm hxw
    have hk2 : Integrable (fun e' => K (x.1, e') ^ 2) σ := by
      refine (hx.const_mul (w x.1)⁻¹).congr (Eventually.of_forall fun e' => ?_)
      field_simp
    have hkL2 : MemLp (fun e' => K (x.1, e')) 2 σ := (memLp_two_iff_integrable_sq hxm).2 hk2
    have hPxm : AEStronglyMeasurable (fun e' => P x.2 e') σ :=
      (hPm.comp (measurable_const.prodMk measurable_id)).aestronglyMeasurable
    have hqL2 : MemLp (fun e' => P x.2 e' * K (x.1, e')) 2 σ :=
      hkL2.of_le_mul (hPxm.mul hxm) (Eventually.of_forall fun e' => by
        rw [Real.norm_eq_abs, Real.norm_eq_abs, abs_mul]
        exact mul_le_mul_of_nonneg_right (hP _ _) (abs_nonneg _))
    have hq1 : Integrable (fun e' => P x.2 e' * K (x.1, e')) σ := hqL2.integrable one_le_two
    have hq2 : Integrable (fun e' => (P x.2 e' * K (x.1, e')) ^ 2) σ :=
      (memLp_two_iff_integrable_sq hqL2.1).1 hqL2
    have hcs := sq_integral_le σ hq1 hq2
    have hmono : ∫ e', (P x.2 e' * K (x.1, e')) ^ 2 ∂σ ≤ ∫ e', Pmax ^ 2 * K (x.1, e') ^ 2 ∂σ :=
      integral_mono hq2 (hk2.const_mul _) (fun e' => by
        have hPe := hP x.2 e'
        have hsq : P x.2 e' ^ 2 ≤ Pmax ^ 2 := by
          rw [← sq_abs (P x.2 e')]
          exact pow_le_pow_left₀ (abs_nonneg _) hPe 2
        rw [mul_pow]
        exact mul_le_mul_of_nonneg_right hsq (sq_nonneg _))
    rw [integral_const_mul] at hmono
    have hM0 : 0 ≤ σ.real univ := measureReal_nonneg
    rw [Real.norm_eq_abs, abs_of_nonneg (mul_nonneg hxw.le (sq_nonneg _)), integral_const_mul]
    simp only [gain]
    calc w x.1 * (∫ e', P x.2 e' * K (x.1, e') ∂σ) ^ 2
        ≤ w x.1 * (σ.real univ * (Pmax ^ 2 * ∫ e', K (x.1, e') ^ 2 ∂σ)) :=
          mul_le_mul_of_nonneg_left (hcs.trans (mul_le_mul_of_nonneg_left hmono hM0)) hxw.le
      _ = Pmax ^ 2 * σ.real univ * (w x.1 * ∫ e', K (x.1, e') ^ 2 ∂σ) := by ring
  have hint : Integrable (fun x => w x.1 * gain σ P K x ^ 2) (ρ.prod σ) :=
    Integrable.mono' hdom (hWm.aestronglyMeasurable.mul (hgm.pow 2)) hbd
  have e1 : ∫ x, (∫ e', w x.1 * K (x.1, e') ^ 2 ∂σ) ∂(ρ.prod σ) =
      ∫ p, w (angSwap p).1.1 * K (angSwap p).1 ^ 2 ∂((ρ.prod σ).prod σ) :=
    (integral_prod _ hF).symm
  have e2 : ∫ p, w (angSwap p).1.1 * K (angSwap p).1 ^ 2 ∂((ρ.prod σ).prod σ) =
      ∫ p, w p.1.1 * K p.1 ^ 2 ∂((ρ.prod σ).prod σ) :=
    hmp.integral_comp' (fun q : (Y × S) × S => w q.1.1 * K q.1 ^ 2)
  have e3 : ∫ p, w p.1.1 * K p.1 ^ 2 ∂((ρ.prod σ).prod σ) =
      ∫ x, (∫ _e', w x.1 * K x ^ 2 ∂σ) ∂(ρ.prod σ) :=
    integral_prod _ (hK2.comp_fst σ)
  have e4 : ∫ x, (∫ _e', w x.1 * K x ^ 2 ∂σ) ∂(ρ.prod σ) =
      σ.real univ * ∫ x, w x.1 * K x ^ 2 ∂(ρ.prod σ) := by
    simp only [integral_const, smul_eq_mul]
    exact integral_const_mul _ _
  calc ∫ x, w x.1 * gain σ P K x ^ 2 ∂(ρ.prod σ)
      ≤ ∫ x, Pmax ^ 2 * σ.real univ * ∫ e', w x.1 * K (x.1, e') ^ 2 ∂σ ∂(ρ.prod σ) :=
        integral_mono_ae hint hdom (hbd.mono fun x hx =>
          (le_abs_self _).trans (by rwa [Real.norm_eq_abs] at hx))
    _ = Pmax ^ 2 * σ.real univ * ∫ x, (∫ e', w x.1 * K (x.1, e') ^ 2 ∂σ) ∂(ρ.prod σ) :=
        integral_const_mul _ _
    _ = Pmax ^ 2 * σ.real univ ^ 2 * ∫ x, w x.1 * K x ^ 2 ∂(ρ.prod σ) := by
        rw [e1, e2, e3, e4]
        ring

theorem gain_toLp_norm_le (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax) (F : L2W (ρ.prod σ) (fun x => w x.1)) :
    ‖(gain_memLp ρ σ w hwm hwpos P hPm hP (Lp.memLp F)).toLp (gain σ P (F : Y × S → ℝ))‖ ≤
      |Pmax| * σ.real univ * ‖F‖ := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hwm.comp measurable_fst
  have hW0 : ∀ᵐ x ∂(ρ.prod σ), 0 ≤ w x.1 := hwpos.mono fun x hx => hx.le
  have hac : (ρ.prod σ) ≪ wmeas (ρ.prod σ) (fun x => w x.1) := ac_of_pos _ _ hWm hwpos
  have hg := gain_memLp ρ σ w hwm hwpos P hPm hP (Lp.memLp F)
  have he : ∫ x, w x.1 * (hg.toLp (gain σ P (F : Y × S → ℝ)) : Y × S → ℝ) x ^ 2 ∂(ρ.prod σ) =
      ∫ x, w x.1 * gain σ P (F : Y × S → ℝ) x ^ 2 ∂(ρ.prod σ) :=
    integral_congr_ae (by
      filter_upwards [hac.ae_le hg.coeFn_toLp] with x hx
      rw [hx])
  have hsq : ‖hg.toLp (gain σ P (F : Y × S → ℝ))‖ ^ 2 ≤ (|Pmax| * σ.real univ * ‖F‖) ^ 2 := by
    rw [norm_sq_L2W _ _ hWm hW0 (hg.toLp (gain σ P (F : Y × S → ℝ))), he, mul_pow, mul_pow,
      sq_abs, norm_sq_L2W _ _ hWm hW0 F]
    exact gain_sq_integral_le ρ σ w hwm hwpos P hPm hP (Lp.memLp F)
  exact (pow_le_pow_iff_left₀ (norm_nonneg _)
    (mul_nonneg (mul_nonneg (abs_nonneg _) measureReal_nonneg) (norm_nonneg _))
    two_ne_zero).1 hsq

/-! ## The operator on L²(w(E) dν) -/

/-- The class of `collOp σ τ P F` in L²(w(E) dν). -/
noncomputable def collLp (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P)
    (F : L2W (ρ.prod σ) (fun x => w x.1)) : L2W (ρ.prod σ) (fun x => w x.1) :=
  (collOp_memLp ρ σ w hB.hwm hB.hwpos τ hB.hτm hB.τbd.choose_spec P hB.hPm hB.Pbd.choose_spec
    (Lp.memLp F)).toLp (collOp σ τ P (F : Y × S → ℝ))

theorem collLp_coeFn (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P)
    (F : L2W (ρ.prod σ) (fun x => w x.1)) :
    (collLp ρ σ w τ P hB F : Y × S → ℝ) =ᵐ[wmeas (ρ.prod σ) (fun x => w x.1)]
      collOp σ τ P (F : Y × S → ℝ) :=
  MemLp.coeFn_toLp _

theorem collLp_add (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P)
    (F G : L2W (ρ.prod σ) (fun x => w x.1)) :
    collLp ρ σ w τ P hB (F + G) = collLp ρ σ w τ P hB F + collLp ρ σ w τ P hB G := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hB.hwm.comp measurable_fst
  have hac : (ρ.prod σ) ≪ wmeas (ρ.prod σ) (fun x => w x.1) := ac_of_pos _ _ hWm hB.hwpos
  have hac' : wmeas (ρ.prod σ) (fun x => w x.1) ≪ ρ.prod σ :=
    withDensity_absolutelyContinuous _ _
  have hP := hB.Pbd.choose_spec
  have hsF := section_integrable ρ σ w hB.hwm hB.hwpos P hB.hPm hP (Lp.memLp F)
  have hsG := section_integrable ρ σ w hB.hwm hB.hwpos P hB.hPm hP (Lp.memLp G)
  have hadd : ((F + G : L2W (ρ.prod σ) (fun x => w x.1)) : Y × S → ℝ) =ᵐ[ρ.prod σ]
      fun x => (F : Y × S → ℝ) x + (G : Y × S → ℝ) x := by
    filter_upwards [hac.ae_le (Lp.coeFn_add F G)] with x hx
    rw [hx, Pi.add_apply]
  have hlin : ∀ᵐ x ∂(ρ.prod σ),
      collOp σ τ P ((F + G : L2W (ρ.prod σ) (fun x => w x.1)) : Y × S → ℝ) x =
        collOp σ τ P (F : Y × S → ℝ) x + collOp σ τ P (G : Y × S → ℝ) x := by
    filter_upwards [collOp_congr_ae ρ σ τ P hadd, hsF, hsG] with x h1 h2 h3
    rw [h1]
    simp only [collOp, gain]
    rw [show (fun e' => P x.2 e' * ((F : Y × S → ℝ) (x.1, e') + (G : Y × S → ℝ) (x.1, e'))) =
        fun e' => P x.2 e' * (F : Y × S → ℝ) (x.1, e') + P x.2 e' * (G : Y × S → ℝ) (x.1, e')
        from funext fun _ => by ring, integral_add h2 h3]
    ring
  apply Lp.ext
  filter_upwards [collLp_coeFn ρ σ w τ P hB (F + G),
    Lp.coeFn_add (collLp ρ σ w τ P hB F) (collLp ρ σ w τ P hB G),
    collLp_coeFn ρ σ w τ P hB F, collLp_coeFn ρ σ w τ P hB G, hac'.ae_le hlin]
    with x h1 h2 h3 h4 h5
  rw [h1, h2, Pi.add_apply, h3, h4, h5]

theorem collLp_smul (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P) (c : ℝ)
    (F : L2W (ρ.prod σ) (fun x => w x.1)) :
    collLp ρ σ w τ P hB (c • F) = c • collLp ρ σ w τ P hB F := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hB.hwm.comp measurable_fst
  have hac : (ρ.prod σ) ≪ wmeas (ρ.prod σ) (fun x => w x.1) := ac_of_pos _ _ hWm hB.hwpos
  have hac' : wmeas (ρ.prod σ) (fun x => w x.1) ≪ ρ.prod σ :=
    withDensity_absolutelyContinuous _ _
  have hsm : ((c • F : L2W (ρ.prod σ) (fun x => w x.1)) : Y × S → ℝ) =ᵐ[ρ.prod σ]
      fun x => c * (F : Y × S → ℝ) x := by
    filter_upwards [hac.ae_le (Lp.coeFn_smul c F)] with x hx
    rw [hx, Pi.smul_apply, smul_eq_mul]
  have hlin : ∀ᵐ x ∂(ρ.prod σ),
      collOp σ τ P ((c • F : L2W (ρ.prod σ) (fun x => w x.1)) : Y × S → ℝ) x =
        c * collOp σ τ P (F : Y × S → ℝ) x := by
    filter_upwards [collOp_congr_ae ρ σ τ P hsm] with x h1
    rw [h1]
    simp only [collOp, gain]
    rw [show (fun e' => P x.2 e' * (c * (F : Y × S → ℝ) (x.1, e'))) =
        fun e' => c * (P x.2 e' * (F : Y × S → ℝ) (x.1, e')) from funext fun _ => by ring,
      integral_const_mul]
    ring
  apply Lp.ext
  filter_upwards [collLp_coeFn ρ σ w τ P hB (c • F), Lp.coeFn_smul c (collLp ρ σ w τ P hB F),
    collLp_coeFn ρ σ w τ P hB F, hac'.ae_le hlin] with x h1 h2 h3 h4
  rw [h1, h2, Pi.smul_apply, h3, h4, smul_eq_mul]

theorem collLp_norm_le (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P)
    (F : L2W (ρ.prod σ) (fun x => w x.1)) :
    ‖collLp ρ σ w τ P hB F‖ ≤
      (max hB.τbd.choose 0 * (|hB.Pbd.choose| * σ.real univ + 1)) * ‖F‖ := by
  have hτ := hB.τbd.choose_spec
  have hP := hB.Pbd.choose_spec
  have hg := gain_memLp ρ σ w hB.hwm hB.hwpos P hB.hPm hP (Lp.memLp F)
  have h1 : ‖collLp ρ σ w τ P hB F‖ ≤
      max hB.τbd.choose 0 * ‖hg.toLp (gain σ P (F : Y × S → ℝ)) - F‖ := by
    refine Lp.norm_le_mul_norm_of_ae_le_mul ?_
    filter_upwards [collLp_coeFn ρ σ w τ P hB F,
      Lp.coeFn_sub (hg.toLp (gain σ P (F : Y × S → ℝ))) F, hg.coeFn_toLp] with x h1 h2 h3
    rw [h1, h2, Pi.sub_apply, h3]
    simp only [collOp, Real.norm_eq_abs, abs_mul]
    exact mul_le_mul_of_nonneg_right ((hτ x.1).trans (le_max_left _ _)) (abs_nonneg _)
  have h2 := gain_toLp_norm_le ρ σ w hB.hwm hB.hwpos P hB.hPm hP F
  have h3 : ‖hg.toLp (gain σ P (F : Y × S → ℝ)) - F‖ ≤
      |hB.Pbd.choose| * σ.real univ * ‖F‖ + ‖F‖ :=
    (norm_sub_le _ _).trans (by linarith [h2])
  calc ‖collLp ρ σ w τ P hB F‖
      ≤ max hB.τbd.choose 0 * ‖hg.toLp (gain σ P (F : Y × S → ℝ)) - F‖ := h1
    _ ≤ max hB.τbd.choose 0 * (|hB.Pbd.choose| * σ.real univ * ‖F‖ + ‖F‖) :=
        mul_le_mul_of_nonneg_left h3 (le_max_right _ _)
    _ = (max hB.τbd.choose 0 * (|hB.Pbd.choose| * σ.real univ + 1)) * ‖F‖ := by ring

/-- The collision operator as a linear map on L²(w(E) dν). -/
noncomputable def collLin (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P) :
    L2W (ρ.prod σ) (fun x => w x.1) →ₗ[ℝ] L2W (ρ.prod σ) (fun x => w x.1) where
  toFun := collLp ρ σ w τ P hB
  map_add' F G := collLp_add ρ σ w τ P hB F G
  map_smul' c F := collLp_smul ρ σ w τ P hB c F

/-- T10: the bounded collision operator on L²(w(E) dν). -/
noncomputable def collCLM (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P) :
    L2W (ρ.prod σ) (fun x => w x.1) →L[ℝ] L2W (ρ.prod σ) (fun x => w x.1) :=
  (collLin ρ σ w τ P hB).mkContinuous _ (fun F => collLp_norm_le ρ σ w τ P hB F)

theorem collCLM_coeFn (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P)
    (F : L2W (ρ.prod σ) (fun x => w x.1)) :
    (collCLM ρ σ w τ P hB F : Y × S → ℝ) =ᵐ[wmeas (ρ.prod σ) (fun x => w x.1)]
      collOp σ τ P F :=
  collLp_coeFn ρ σ w τ P hB F

/-! ## The adjoint pairing in L²(w(E) dν) and the Hilbert adjoint -/

theorem collLp_inner_adjoint (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P)
    (K h : L2W (ρ.prod σ) (fun x => w x.1)) :
    inner ℝ (collLp ρ σ w τ (transposeKernel P) hB.transpose K) h =
      inner ℝ K (collLp ρ σ w τ P hB h) := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hB.hwm.comp measurable_fst
  have hW0 : ∀ᵐ x ∂(ρ.prod σ), 0 ≤ w x.1 := hB.hwpos.mono fun x hx => hx.le
  have hac : (ρ.prod σ) ≪ wmeas (ρ.prod σ) (fun x => w x.1) := ac_of_pos _ _ hWm hB.hwpos
  obtain ⟨τmax, hτ⟩ := hB.τbd
  obtain ⟨Pmax, hP⟩ := hB.Pbd
  have hL : ∀ᵐ x ∂(ρ.prod σ),
      (collLp ρ σ w τ (transposeKernel P) hB.transpose K : Y × S → ℝ) x =
        collAdj σ τ P (K : Y × S → ℝ) x :=
    hac.ae_le (collLp_coeFn ρ σ w τ (transposeKernel P) hB.transpose K)
  have hR : ∀ᵐ x ∂(ρ.prod σ), (collLp ρ σ w τ P hB h : Y × S → ℝ) x =
      collOp σ τ P (h : Y × S → ℝ) x :=
    hac.ae_le (collLp_coeFn ρ σ w τ P hB h)
  rw [inner_L2W _ _ hWm hW0, inner_L2W _ _ hWm hW0]
  have eL : ∫ x, w x.1 * ((collLp ρ σ w τ (transposeKernel P) hB.transpose K : Y × S → ℝ) x *
      (h : Y × S → ℝ) x) ∂(ρ.prod σ) =
      ∫ x, w x.1 * (collAdj σ τ P (K : Y × S → ℝ) x * (h : Y × S → ℝ) x) ∂(ρ.prod σ) :=
    integral_congr_ae (by
      filter_upwards [hL] with x hx
      rw [hx])
  have eR : ∫ x, w x.1 * ((K : Y × S → ℝ) x * (collLp ρ σ w τ P hB h : Y × S → ℝ) x)
      ∂(ρ.prod σ) =
      ∫ x, w x.1 * ((K : Y × S → ℝ) x * collOp σ τ P (h : Y × S → ℝ) x) ∂(ρ.prod σ) :=
    integral_congr_ae (by
      filter_upwards [hR] with x hx
      rw [hx])
  rw [eL, eR]
  -- the weighted kernel K' = w(E) K
  have hKm : AEStronglyMeasurable (K : Y × S → ℝ) (ρ.prod σ) := (Lp.memLp K).1.mono_ac hac
  have hhm : AEStronglyMeasurable (h : Y × S → ℝ) (ρ.prod σ) := (Lp.memLp h).1.mono_ac hac
  have hK'm : AEStronglyMeasurable (fun y : Y × S => w y.1 * (K : Y × S → ℝ) y) (ρ.prod σ) :=
    hWm.aestronglyMeasurable.mul hKm
  have hK2 := wsq_integrable ρ σ w hB.hwm hB.hwpos (Lp.memLp K)
  have hh2 := wsq_integrable ρ σ w hB.hwm hB.hwpos (Lp.memLp h)
  have hwpos' : ∀ᵐ x ∂(ρ.prod σ), 0 < (fun E => (w E)⁻¹) x.1 :=
    hB.hwpos.mono fun x hx => inv_pos.2 hx
  have hK2' : Integrable (fun x : Y × S => (fun E => (w E)⁻¹) x.1 *
      (fun y : Y × S => w y.1 * (K : Y × S → ℝ) y) x ^ 2) (ρ.prod σ) := by
    refine hK2.congr ?_
    filter_upwards [hB.hwpos] with x hx
    have hne : w x.1 ≠ 0 := hx.ne'
    field_simp
  have hh2' : Integrable (fun x : Y × S => (h : Y × S → ℝ) x ^ 2 / (fun E => (w E)⁻¹) x.1)
      (ρ.prod σ) := by
    refine hh2.congr (Eventually.of_forall fun x => ?_)
    simp only [div_inv_eq_mul]
    ring
  obtain ⟨hGi, hli⟩ := fubKernel_integrable ρ σ (fun E => (w E)⁻¹) hwpos' τ hB.hτm hτ P hB.hPm
    hP (fun y => w y.1 * (K : Y × S → ℝ) y) (h : Y × S → ℝ) hK'm hhm hK2' hh2'
  have hpair := (adjoint_pair ρ σ τ P (fun y => w y.1 * (K : Y × S → ℝ) y) (h : Y × S → ℝ)
    hGi hli).2.2
  have hcomm : ∀ x : Y × S, collAdj σ τ P (fun y => w y.1 * (K : Y × S → ℝ) y) x =
      w x.1 * collAdj σ τ P (K : Y × S → ℝ) x := by
    intro x
    simp only [collAdj, collOp, gain, transposeKernel]
    rw [show (fun e' => P e' x.2 * (w x.1 * (K : Y × S → ℝ) (x.1, e'))) =
        fun e' => w x.1 * (P e' x.2 * (K : Y × S → ℝ) (x.1, e')) from funext fun _ => by ring,
      integral_const_mul]
    ring
  calc ∫ x, w x.1 * (collAdj σ τ P (K : Y × S → ℝ) x * (h : Y × S → ℝ) x) ∂(ρ.prod σ)
      = ∫ x, collAdj σ τ P (fun y => w y.1 * (K : Y × S → ℝ) y) x * (h : Y × S → ℝ) x
          ∂(ρ.prod σ) := by
        congr 1
        funext x
        rw [hcomm]
        ring
    _ = ∫ x, w x.1 * (K : Y × S → ℝ) x * collOp σ τ P (h : Y × S → ℝ) x ∂(ρ.prod σ) :=
        hpair.symm
    _ = ∫ x, w x.1 * ((K : Y × S → ℝ) x * collOp σ τ P (h : Y × S → ℝ) x) ∂(ρ.prod σ) := by
        congr 1
        funext x
        ring

/-- T10: the Hilbert adjoint of the bounded collision operator on L²(w(E) dν) is the
transposed-kernel operator with the same rate τ(E). -/
theorem collCLM_adjoint (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P) :
    ContinuousLinearMap.adjoint (collCLM ρ σ w τ P hB) =
      collCLM ρ σ w τ (transposeKernel P) hB.transpose :=
  ((ContinuousLinearMap.eq_adjoint_iff _ _).2 fun K h =>
    collLp_inner_adjoint ρ σ w τ P hB K h).symm

/-- The Hilbert adjoint acts on representatives as the formal adjoint `collAdj` used by T4/T5. -/
theorem collCLM_adjoint_coeFn (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P)
    (K : L2W (ρ.prod σ) (fun x => w x.1)) :
    (ContinuousLinearMap.adjoint (collCLM ρ σ w τ P hB) K : Y × S → ℝ)
      =ᵐ[wmeas (ρ.prod σ) (fun x => w x.1)] collAdj σ τ P K := by
  rw [collCLM_adjoint]
  exact collCLM_coeFn ρ σ w τ (transposeKernel P) hB.transpose K

theorem collCLM_kernel_congr (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) {P Q : S → S → ℝ} (hPQ : P = Q) (hP : BoundedRoute ρ σ w τ P)
    (hQ : BoundedRoute ρ σ w τ Q) : collCLM ρ σ w τ P hP = collCLM ρ σ w τ Q hQ := by
  subst hPQ
  rfl

end Hilbert

/-! ## Source instance: the Thomson-shape operator is self-adjoint on L²(F_b(1+F_b) dν) -/

theorem transposeKernel_thomsonP : transposeKernel thomsonP = thomsonP := by
  funext e e'
  exact thomsonP_symm e' e

theorem photon_boundedRoute (C b : ℝ) (hb : 0 < b) (τ : ℝ → ℝ) (hτm : Measurable τ)
    {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax) :
    BoundedRoute (energyMeasure C) dOmega (fun E => CAS12PlanckIR.weight b E) τ thomsonP := by
  have h := nu_ae_pos C
  rw [nu_eq_prod] at h
  refine ⟨weight_measurable b, ?_, hτm, ⟨τmax, hτ⟩, thomsonP_measurable,
    ⟨3 / (8 * Real.pi), fun e e' => ?_⟩⟩
  · filter_upwards [h] with x hx
    exact weight_pos b x.1 hb hx
  · rw [abs_of_nonneg (thomsonP_bounds e e').1]
    exact (thomsonP_bounds e e').2

theorem photon_collCLM_selfAdjoint (C b : ℝ) (hb : 0 < b) (τ : ℝ → ℝ) (hτm : Measurable τ)
    {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax) :
    ContinuousLinearMap.adjoint (collCLM (energyMeasure C) dOmega
        (fun E => CAS12PlanckIR.weight b E) τ thomsonP (photon_boundedRoute C b hb τ hτm hτ)) =
      collCLM (energyMeasure C) dOmega (fun E => CAS12PlanckIR.weight b E) τ thomsonP
        (photon_boundedRoute C b hb τ hτm hτ) := by
  rw [collCLM_adjoint]
  exact collCLM_kernel_congr _ _ _ _ transposeKernel_thomsonP _ _

end G12A
