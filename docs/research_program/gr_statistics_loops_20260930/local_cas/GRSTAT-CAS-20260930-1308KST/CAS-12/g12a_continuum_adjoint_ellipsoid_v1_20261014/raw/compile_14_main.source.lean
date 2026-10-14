import Mathlib
import G11CWeightedEllipsoid
import G12DCardClosure

/-!
G12-A (GR-CAS-12, TEFF-A3): weighted continuum adjoint of a fixed linear
collision operator and the collision-moment ellipsoid.  Supplement
TEFF_POSITIVE_BRIDGE (A7) and the elastic scalar angular-scattering model
(lines 118-141).  Targets are frozen in `../FROZEN_TARGETS.md`; sources in
`../SOURCE_RECOVERY.md`.

* T1: the operator `collOp` (Lh)(E,e) = τ(E)[∫P(e,e')h(E,e')dσ(e') - h(E,e)], its
  formal dν-adjoint `collAdj` (transposed kernel), linearity, the Thomson-shape kernel.
* T2: the kernel-Fubini adjoint pair identity ⟨K, L h⟩ = ⟨L*K, h⟩ on the explicit
  domain of absolutely integrable kernel products (measure-preserving angle swap).
* T3: bounded route: bounded τ, bounded measurable P, finite σ, energy-only W
  discharge that domain and give L*K ∈ L²(W dν).
* T4/T5: the collision residual ellipsoid through the reused G11-C theorem.
* T6/T7: exact retained branch; energy-dependent τ keeps the τ(E) × score product.
* T8: negative control (COLL-TAU) and non-vacuity; T9: the source instance
  dν = C E² dE dΩ with the photon envelope (A5) and the Thomson-shape kernel.

Imported modules are used unchanged.  CAS12-C01 (finite adjoint) is not imported.
-/

open MeasureTheory Set Filter Topology Matrix
open scoped ENNReal

namespace G12A

open G11A G11B G11C

section Operator

variable {Y S : Type*} [MeasurableSpace Y] [MeasurableSpace S]

/-! ## Definitions -/

/-- Gain (angular redistribution) term at fixed energy. -/
noncomputable def gain (σ : Measure S) (P : S → S → ℝ) (h : Y × S → ℝ) : Y × S → ℝ :=
  fun x => ∫ e', P x.2 e' * h (x.1, e') ∂σ

/-- Source S:133: (Lh)(E,e) = τ(E)[∫ P(e,e') h(E,e') dσ(e') − h(E,e)]. -/
noncomputable def collOp (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ) (h : Y × S → ℝ) :
    Y × S → ℝ :=
  fun x => τ x.1 * (gain σ P h x - h x)

/-- Transposed kernel. -/
def transposeKernel (P : S → S → ℝ) : S → S → ℝ := fun e e' => P e' e

/-- The formal dν-adjoint: same rate, transposed kernel. -/
noncomputable def collAdj (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ) (K : Y × S → ℝ) :
    Y × S → ℝ :=
  collOp σ τ (transposeKernel P) K

/-- Kernel-product integrand of ⟨K, gain h⟩ on (ν ⊗ σ). -/
def fubKernel (τ : Y → ℝ) (P : S → S → ℝ) (K h : Y × S → ℝ) : (Y × S) × S → ℝ :=
  fun p => (τ p.1.1 * K p.1) * (P p.1.2 p.2 * h (p.1.1, p.2))

/-- Collision residual vector e_j = ⟨K_j, L(f − g)⟩_ν. -/
noncomputable def collEvec {n : ℕ} (ρ : Measure Y) (σ : Measure S) (τ : Y → ℝ)
    (P : S → S → ℝ) (K : Fin n → Y × S → ℝ) (f g : Y × S → ℝ) : Fin n → ℝ :=
  fun j => ∫ x, K j x * collOp σ τ P (fun y => f y - g y) x ∂(ρ.prod σ)

/-- ((E,e),e') ↦ ((E,e'),e). -/
def angSwap : (Y × S) × S ≃ᵐ (Y × S) × S :=
  (MeasurableEquiv.prodAssoc.trans
    ((MeasurableEquiv.refl Y).prodCongr MeasurableEquiv.prodComm)).trans
    MeasurableEquiv.prodAssoc.symm

/-! ## T1: operator facts -/

theorem collAdj_eq_collOp_of_symm (σ : Measure S) (τ : Y → ℝ) {P : S → S → ℝ}
    (hP : ∀ e e', P e e' = P e' e) : collAdj σ τ P = collOp σ τ P := by
  have h : transposeKernel P = P := by
    funext e e'
    exact (hP e e').symm
  unfold collAdj
  rw [h]

theorem collOp_sub_of_integrable (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ) (f g : Y × S → ℝ)
    (x : Y × S) (hfx : Integrable (fun e' => P x.2 e' * f (x.1, e')) σ)
    (hgx : Integrable (fun e' => P x.2 e' * g (x.1, e')) σ) :
    collOp σ τ P (fun y => f y - g y) x = collOp σ τ P f x - collOp σ τ P g x := by
  simp only [collOp, gain]
  rw [show (fun e' => P x.2 e' * (f (x.1, e') - g (x.1, e'))) =
      fun e' => P x.2 e' * f (x.1, e') - P x.2 e' * g (x.1, e') from
      funext fun _ => by ring, integral_sub hfx hgx]
  ring

theorem collEvec_eq_sub {n : ℕ} (ρ : Measure Y) (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ)
    (K : Fin n → Y × S → ℝ) (f g : Y × S → ℝ)
    (hsec : ∀ᵐ x ∂(ρ.prod σ), Integrable (fun e' => P x.2 e' * f (x.1, e')) σ ∧
      Integrable (fun e' => P x.2 e' * g (x.1, e')) σ) (j : Fin n) :
    collEvec ρ σ τ P K f g j =
      ∫ x, K j x * (collOp σ τ P f x - collOp σ τ P g x) ∂(ρ.prod σ) := by
  simp only [collEvec]
  refine integral_congr_ae ?_
  filter_upwards [hsec] with x hx
  rw [collOp_sub_of_integrable σ τ P f g x hx.1 hx.2]

/-! ## T2: the angle swap and the kernel-Fubini adjoint pair identity -/

theorem angSwap_apply (p : (Y × S) × S) : angSwap p = ((p.1.1, p.2), p.1.2) := rfl

theorem angSwap_measurePreserving (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] :
    MeasurePreserving angSwap ((ρ.prod σ).prod σ) ((ρ.prod σ).prod σ) := by
  have h1 := measurePreserving_prodAssoc ρ σ σ
  have h2 : MeasurePreserving (Prod.map (id : Y → Y) Prod.swap) (ρ.prod (σ.prod σ))
      (ρ.prod (σ.prod σ)) :=
    (MeasurePreserving.id ρ).prod Measure.measurePreserving_swap
  have h3 := MeasurePreserving.symm MeasurableEquiv.prodAssoc h1
  exact (h3.comp h2).comp h1

theorem adjoint_pair (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] (τ : Y → ℝ)
    (P : S → S → ℝ) (K h : Y × S → ℝ)
    (hG : Integrable (fubKernel τ P K h) ((ρ.prod σ).prod σ))
    (hloss : Integrable (fun x => τ x.1 * K x * h x) (ρ.prod σ)) :
    Integrable (fun x => K x * collOp σ τ P h x) (ρ.prod σ) ∧
      Integrable (fun x => collAdj σ τ P K x * h x) (ρ.prod σ) ∧
      ∫ x, K x * collOp σ τ P h x ∂(ρ.prod σ) =
        ∫ x, collAdj σ τ P K x * h x ∂(ρ.prod σ) := by
  have hmp := angSwap_measurePreserving ρ σ
  have hG' : Integrable (fun p => fubKernel τ P K h (angSwap p)) ((ρ.prod σ).prod σ) :=
    (hmp.integrable_comp_emb angSwap.measurableEmbedding).2 hG
  have h1 : (fun x => K x * collOp σ τ P h x) =
      fun x => (∫ e', fubKernel τ P K h (x, e') ∂σ) - τ x.1 * K x * h x := by
    funext x
    simp only [collOp, gain, fubKernel]
    rw [integral_const_mul]
    ring
  have h2 : (fun x => collAdj σ τ P K x * h x) =
      fun x => (∫ e', fubKernel τ P K h (angSwap (x, e')) ∂σ) - τ x.1 * K x * h x := by
    funext x
    simp only [collAdj, collOp, gain, transposeKernel, fubKernel, angSwap_apply]
    rw [show (fun e' => τ x.1 * K (x.1, e') * (P e' x.2 * h (x.1, x.2))) =
        fun e' => (τ x.1 * h x) * (P e' x.2 * K (x.1, e')) from funext fun _ => by ring,
      integral_const_mul]
    ring
  have hi1 := hG.integral_prod_left
  have hi2 := hG'.integral_prod_left
  refine ⟨?_, ?_, ?_⟩
  · rw [h1]
    exact hi1.sub hloss
  · rw [h2]
    exact hi2.sub hloss
  · rw [h1, h2, integral_sub hi1 hloss, integral_sub hi2 hloss]
    congr 1
    rw [← integral_prod _ hG, ← integral_prod (fun p => fubKernel τ P K h (angSwap p)) hG',
      hmp.integral_comp' (fubKernel τ P K h)]

/-! ## T3: bounded route -/

theorem sq_integral_le (σ : Measure S) [IsFiniteMeasure σ] {u : S → ℝ} (hu : Integrable u σ)
    (hu2 : Integrable (fun e => u e ^ 2) σ) :
    (∫ e, u e ∂σ) ^ 2 ≤ σ.real univ * ∫ e, u e ^ 2 ∂σ := by
  by_cases hσ : σ = 0
  · subst hσ
    simp
  have hpos : 0 < σ.real univ := by
    rw [measureReal_def]
    exact ENNReal.toReal_pos (Measure.measure_univ_ne_zero.2 hσ) (measure_ne_top σ univ)
  have hpt : ∀ e, 2 * (∫ e, u e ∂σ) * u e ≤
      (∫ e, u e ∂σ) ^ 2 / σ.real univ + σ.real univ * u e ^ 2 := by
    intro e
    have hsq := sq_nonneg ((∫ e, u e ∂σ) - σ.real univ * u e)
    have key : (∫ e, u e ∂σ) ^ 2 / σ.real univ + σ.real univ * u e ^ 2 - 2 * (∫ e, u e ∂σ) * u e
        = ((∫ e, u e ∂σ) - σ.real univ * u e) ^ 2 / σ.real univ := by
      field_simp
      ring
    have : 0 ≤ ((∫ e, u e ∂σ) - σ.real univ * u e) ^ 2 / σ.real univ :=
      div_nonneg hsq hpos.le
    linarith
  have hI := integral_mono (hu.const_mul (2 * ∫ e, u e ∂σ))
    ((integrable_const ((∫ e, u e ∂σ) ^ 2 / σ.real univ)).add (hu2.const_mul (σ.real univ))) hpt
  rw [integral_const_mul, integral_add (integrable_const _) (hu2.const_mul _), integral_const,
    integral_const_mul, smul_eq_mul] at hI
  have hc : σ.real univ * ((∫ e, u e ∂σ) ^ 2 / σ.real univ) = (∫ e, u e ∂σ) ^ 2 := by
    field_simp
  nlinarith [hI, hc]

theorem amgm_abs (w a b : ℝ) (hw : 0 < w) : |a * b| ≤ (w * a ^ 2 + b ^ 2 / w) / 2 := by
  have key : w * a ^ 2 + b ^ 2 / w - 2 * (|a| * |b|) = (w * |a| - |b|) ^ 2 / w := by
    rw [← sq_abs a, ← sq_abs b]
    field_simp
    ring
  have h2 : 0 ≤ (w * |a| - |b|) ^ 2 / w := div_nonneg (sq_nonneg _) hw.le
  rw [abs_mul]
  linarith

theorem ac_of_pos {X : Type*} [MeasurableSpace X] (μ : Measure X) (W : X → ℝ)
    (hWm : Measurable W) (hpos : ∀ᵐ x ∂μ, 0 < W x) : μ ≪ wmeas μ W := by
  unfold wmeas
  refine withDensity_absolutelyContinuous' hWm.ennreal_ofReal.aemeasurable ?_
  filter_upwards [hpos] with x hx
  exact ENNReal.ofReal_ne_zero_iff.2 hx

theorem wsq_integrable (ρ : Measure Y) (σ : Measure S) (w : Y → ℝ) (hwm : Measurable w)
    (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1) {K : Y × S → ℝ}
    (hK : MemLp K 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    Integrable (fun x => w x.1 * K x ^ 2) (ρ.prod σ) := by
  have hW0 : ∀ᵐ x ∂(ρ.prod σ), 0 ≤ w x.1 := hwpos.mono fun x hx => hx.le
  have := (memLp_two_iff_integrable_sq hK.1).1 hK
  exact (integrable_wmeas_iff _ _ (hwm.comp measurable_fst) hW0 _).1 this

theorem fubKernel_integrable (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (τ : Y → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax)
    (K h : Y × S → ℝ) (hKm : AEStronglyMeasurable K (ρ.prod σ))
    (hhm : AEStronglyMeasurable h (ρ.prod σ))
    (hK2 : Integrable (fun x => w x.1 * K x ^ 2) (ρ.prod σ))
    (hh2 : Integrable (fun x => h x ^ 2 / w x.1) (ρ.prod σ)) :
    Integrable (fubKernel τ P K h) ((ρ.prod σ).prod σ) ∧
      Integrable (fun x => τ x.1 * K x * h x) (ρ.prod σ) := by
  have hmp := angSwap_measurePreserving ρ σ
  have hqf : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => p.1)
      ((ρ.prod σ).prod σ) (ρ.prod σ) := Measure.quasiMeasurePreserving_fst
  have hqs : Measure.QuasiMeasurePreserving (fun p : (Y × S) × S => (p.1.1, p.2))
      ((ρ.prod σ).prod σ) (ρ.prod σ) := hqf.comp hmp.quasiMeasurePreserving
  have hwpos3 : ∀ᵐ p ∂((ρ.prod σ).prod σ), 0 < w p.1.1 := hqf.ae hwpos
  have hG1 : Integrable (fun p : (Y × S) × S => w p.1.1 * K p.1 ^ 2) ((ρ.prod σ).prod σ) :=
    hK2.comp_fst σ
  have hG2 : Integrable (fun p : (Y × S) × S => h (p.1.1, p.2) ^ 2 / w p.1.1)
      ((ρ.prod σ).prod σ) :=
    (hmp.integrable_comp_emb angSwap.measurableEmbedding).2 (hh2.comp_fst σ)
  have hτ3 : AEStronglyMeasurable (fun p : (Y × S) × S => τ p.1.1) ((ρ.prod σ).prod σ) :=
    (hτm.comp (measurable_fst.comp measurable_fst)).aestronglyMeasurable
  have hK3 : AEStronglyMeasurable (fun p : (Y × S) × S => K p.1) ((ρ.prod σ).prod σ) :=
    hKm.comp_quasiMeasurePreserving hqf
  have hP3 : AEStronglyMeasurable (fun p : (Y × S) × S => P p.1.2 p.2) ((ρ.prod σ).prod σ) :=
    (hPm.comp ((measurable_snd.comp measurable_fst).prodMk measurable_snd)).aestronglyMeasurable
  have hh3 : AEStronglyMeasurable (fun p : (Y × S) × S => h (p.1.1, p.2)) ((ρ.prod σ).prod σ) :=
    hhm.comp_quasiMeasurePreserving hqs
  have hbound : ∀ᵐ p ∂((ρ.prod σ).prod σ), ‖fubKernel τ P K h p‖ ≤
      τmax * Pmax * ((w p.1.1 * K p.1 ^ 2 + h (p.1.1, p.2) ^ 2 / w p.1.1) / 2) := by
    filter_upwards [hwpos3] with p hp
    have h1 := amgm_abs (w p.1.1) (K p.1) (h (p.1.1, p.2)) hp
    have hτp := hτ p.1.1
    have hPp := hP p.1.2 p.2
    have hτ0 : 0 ≤ τmax := (abs_nonneg _).trans hτp
    have hP0 : 0 ≤ Pmax := (abs_nonneg _).trans hPp
    rw [Real.norm_eq_abs]
    simp only [fubKernel]
    calc |τ p.1.1 * K p.1 * (P p.1.2 p.2 * h (p.1.1, p.2))|
        = (|τ p.1.1| * |P p.1.2 p.2|) * |K p.1 * h (p.1.1, p.2)| := by
          rw [abs_mul, abs_mul, abs_mul, abs_mul]; ring
      _ ≤ (τmax * Pmax) * ((w p.1.1 * K p.1 ^ 2 + h (p.1.1, p.2) ^ 2 / w p.1.1) / 2) :=
          mul_le_mul (mul_le_mul hτp hPp (abs_nonneg _) hτ0) h1 (abs_nonneg _)
            (mul_nonneg hτ0 hP0)
  have hbound2 : ∀ᵐ x ∂(ρ.prod σ), ‖τ x.1 * K x * h x‖ ≤
      τmax * ((w x.1 * K x ^ 2 + h x ^ 2 / w x.1) / 2) := by
    filter_upwards [hwpos] with x hx
    have h1 := amgm_abs (w x.1) (K x) (h x) hx
    have hτx := hτ x.1
    have hτ0 : 0 ≤ τmax := (abs_nonneg _).trans hτx
    rw [Real.norm_eq_abs, mul_assoc, abs_mul]
    exact mul_le_mul hτx h1 (abs_nonneg _) hτ0
  refine ⟨Integrable.mono' (((hG1.add hG2).div_const 2).const_mul (τmax * Pmax))
    ((hτ3.mul hK3).mul (hP3.mul hh3)) hbound, ?_⟩
  exact Integrable.mono' (((hK2.add hh2).div_const 2).const_mul τmax)
    (((hτm.comp measurable_fst).aestronglyMeasurable.mul hKm).mul hhm) hbound2

theorem gain_memLp (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax)
    {K : Y × S → ℝ} (hK : MemLp K 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    MemLp (gain σ P K) 2 (wmeas (ρ.prod σ) (fun x => w x.1)) := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hwm.comp measurable_fst
  have hW0 : ∀ᵐ x ∂(ρ.prod σ), 0 ≤ w x.1 := hwpos.mono fun x hx => hx.le
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
  have hgmW : AEStronglyMeasurable (gain σ P K) (wmeas (ρ.prod σ) (fun x => w x.1)) :=
    hgm.mono_ac (withDensity_absolutelyContinuous _ _)
  exact (memLp_two_iff_integrable_sq hgmW).2 ((integrable_wmeas_iff _ _ hWm hW0 _).2 hint)

theorem collOp_memLp (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (τ : Y → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax)
    {K : Y × S → ℝ} (hK : MemLp K 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    MemLp (collOp σ τ P K) 2 (wmeas (ρ.prod σ) (fun x => w x.1)) := by
  have hg := gain_memLp ρ σ w hwm hwpos P hPm hP hK
  have hd := hg.sub hK
  refine hd.of_le_mul (c := τmax) ((hτm.comp measurable_fst).aestronglyMeasurable.mul hd.1)
    (Eventually.of_forall fun x => ?_)
  simp only [Pi.mul_apply, Pi.sub_apply, Function.comp_apply, Real.norm_eq_abs, abs_mul]
  exact mul_le_mul_of_nonneg_right (hτ x.1) (abs_nonneg _)

theorem collAdj_memLp (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (τ : Y → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax)
    {K : Y × S → ℝ} (hK : MemLp K 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    MemLp (collAdj σ τ P K) 2 (wmeas (ρ.prod σ) (fun x => w x.1)) :=
  collOp_memLp ρ σ w hwm hwpos τ hτm hτ (transposeKernel P) (hPm.comp measurable_swap)
    (fun e e' => hP e' e) hK

/-! ## T4: layer 1, the collision residual ellipsoid -/

theorem collision_ellipsoid (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ]
    (s : Stat) (f g W : Y × S → ℝ) (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂(ρ.prod σ), f x ∈ cdom s) (hgd : ∀ᵐ x ∂(ρ.prod σ), g x ∈ dom s)
    (hW : WEnvelope (ρ.prod σ) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (ρ.prod σ) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (τ : Y → ℝ) (P : S → S → ℝ) (K : Fin n → Y × S → ℝ)
    (hLK : ∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) W))
    (hG : ∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ)) :
    collEvec ρ σ τ P K f g = evec (ρ.prod σ) (fun j => collAdj σ τ P (K j)) f g ∧
      (gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK).PosSemidef ∧
      collEvec ρ σ τ P K f g ∈
        LinearMap.range (gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK).toLin' ∧
      collEvec ρ σ τ P K f g ⬝ᵥ
        (CAS11C02.spectralPinvMatrix (gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK)
          (gramR_posSemidef (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK).isHermitian *ᵥ
          collEvec ρ σ τ P K f g) ≤ 2 * ε := by
  have heq : collEvec ρ σ τ P K f g = evec (ρ.prod σ) (fun j => collAdj σ τ P (K j)) f g := by
    funext j
    exact (adjoint_pair ρ σ τ P (K j) (fun y => f y - g y) (hG j) (hloss j)).2.2
  obtain ⟨h1, h2, h3⟩ := weighted_residual_ellipsoid (ρ.prod σ) s f g W hf hg hfd hgd hW hε0 hε
    φ hφ hmatch (fun j => collAdj σ τ P (K j)) hLK
  rw [heq]
  exact ⟨rfl, h1, h2, h3⟩

/-! ## T5: layer 2, bounded route -/

theorem collision_ellipsoid_bounded (ρ : Measure Y) (σ : Measure S) [SFinite ρ]
    [IsFiniteMeasure σ]
    (s : Stat) (f g : Y × S → ℝ) (w : Y → ℝ) (hwm : Measurable w)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂(ρ.prod σ), f x ∈ cdom s) (hgd : ∀ᵐ x ∂(ρ.prod σ), g x ∈ dom s)
    (hW : WEnvelope (ρ.prod σ) s (fun x => w x.1) f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (ρ.prod σ) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    (τ : Y → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
    (hP : ∀ e e', |P e e'| ≤ Pmax)
    {m n : ℕ} (φ : Fin m → Y × S → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) (fun x => w x.1)))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (K : Fin n → Y × S → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    (∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) (fun x => w x.1))) ∧
    (∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ) ∧
          Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ)) ∧
    ∀ hLK : (∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) (fun x => w x.1))),
      collEvec ρ σ τ P K f g = evec (ρ.prod σ) (fun j => collAdj σ τ P (K j)) f g ∧
      (gramR (ρ.prod σ) (fun x => w x.1) φ hφ (fun j => collAdj σ τ P (K j)) hLK).PosSemidef ∧
      collEvec ρ σ τ P K f g ∈ LinearMap.range
        (gramR (ρ.prod σ) (fun x => w x.1) φ hφ (fun j => collAdj σ τ P (K j)) hLK).toLin' ∧
      collEvec ρ σ τ P K f g ⬝ᵥ
        (CAS11C02.spectralPinvMatrix
            (gramR (ρ.prod σ) (fun x => w x.1) φ hφ (fun j => collAdj σ τ P (K j)) hLK)
            (gramR_posSemidef (ρ.prod σ) (fun x => w x.1) φ hφ
              (fun j => collAdj σ τ P (K j)) hLK).isHermitian *ᵥ
          collEvec ρ σ τ P K f g) ≤ 2 * ε := by
  have hWm : Measurable (fun x : Y × S => w x.1) := hW.1
  have hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1 := hW.2.1
  have hW0 : ∀ᵐ x ∂(ρ.prod σ), 0 ≤ w x.1 := hwpos.mono fun x hx => hx.le
  have hLK : ∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) (fun x => w x.1)) :=
    fun j => collAdj_memLp ρ σ w hwm hwpos τ hτm hτ P hPm hP (hK j)
  have hz := z_memLp (ρ.prod σ) s f g (fun x => w x.1) hf hg hfd hgd hW hε0 hε
  have hh2 : Integrable (fun x => (f x - g x) ^ 2 / w x.1) (ρ.prod σ) := by
    have := (integrable_wmeas_iff _ _ hWm hW0 _).1 ((memLp_two_iff_integrable_sq hz.1).1 hz)
    refine this.congr ?_
    filter_upwards [hwpos] with x hx
    simp only [zfun]
    field_simp
  have hac : (ρ.prod σ) ≪ wmeas (ρ.prod σ) (fun x => w x.1) := ac_of_pos _ _ hWm hwpos
  have hFub : ∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ) ∧
      Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ) := fun j =>
    fubKernel_integrable ρ σ w hwpos τ hτm hτ P hPm hP (K j) (fun y => f y - g y)
      ((hK j).1.mono_ac hac) (hf.sub hg).aestronglyMeasurable
      (wsq_integrable ρ σ w hwm hwpos (hK j)) hh2
  refine ⟨hLK, hFub, fun hLK' => ?_⟩
  exact collision_ellipsoid ρ σ s f g (fun x => w x.1) hf hg hfd hgd hW hε0 hε φ hφ hmatch
    τ P K hLK' (fun j => (hFub j).1) (fun j => (hFub j).2)

/-! ## T6: exact retained collision moment -/

theorem collision_exact_of_retained (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ]
    (s : Stat) (f g W : Y × S → ℝ) (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂(ρ.prod σ), f x ∈ cdom s) (hgd : ∀ᵐ x ∂(ρ.prod σ), g x ∈ dom s)
    (hW : WEnvelope (ρ.prod σ) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (ρ.prod σ) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (τ : Y → ℝ) (P : S → S → ℝ) (K : Fin n → Y × S → ℝ)
    (hLK : ∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) W))
    (hG : ∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ))
    (hret : ∀ j, (hLK j).toLp (collAdj σ τ P (K j)) ∈ retainedSpan (ρ.prod σ) W φ hφ) :
    gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK = 0 ∧
      collEvec ρ σ τ P K f g = 0 := by
  have heq := (collision_ellipsoid ρ σ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch τ P K hLK
    hG hloss).1
  obtain ⟨h0, he⟩ := all_retained (ρ.prod σ) s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch
    (fun j => collAdj σ τ P (K j)) hLK hret
  exact ⟨h0, heq.trans he⟩

theorem collision_moment_of_representation (ρ : Measure Y) (σ : Measure S) [SFinite ρ]
    [SFinite σ] (τ : Y → ℝ) (P : S → S → ℝ) (K f g : Y × S → ℝ) {m : ℕ}
    (φ : Fin m → Y × S → ℝ) (c : Fin m → ℝ)
    (hG : Integrable (fubKernel τ P K (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : Integrable (fun x => τ x.1 * K x * (f x - g x)) (ρ.prod σ))
    (hφi : ∀ a, Integrable (fun x => φ a x * (f x - g x)) (ρ.prod σ))
    (hrep : collAdj σ τ P K =ᵐ[ρ.prod σ] fun x => ∑ a, c a * φ a x) :
    ∫ x, K x * collOp σ τ P (fun y => f y - g y) x ∂(ρ.prod σ) =
      ∑ a, c a * ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) := by
  rw [(adjoint_pair ρ σ τ P K (fun y => f y - g y) hG hloss).2.2]
  have hae : (fun x => collAdj σ τ P K x * (f x - g x)) =ᵐ[ρ.prod σ]
      fun x => ∑ a, c a * (φ a x * (f x - g x)) := by
    filter_upwards [hrep] with x hx
    rw [hx, Finset.sum_mul]
    exact Finset.sum_congr rfl fun a _ => by ring
  rw [integral_congr_ae hae, integral_finset_sum _ (fun a _ => (hφi a).const_mul (c a))]
  exact Finset.sum_congr rfl fun a _ => integral_const_mul _ _

/-! ## T7: energy-dependent versus constant τ -/

theorem collAdj_eigen (μ : Measure (Y × S)) (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ)
    (K : Y × S → ℝ) (p : ℝ) (heig : ∀ᵐ x ∂μ, ∫ e', P e' x.2 * K (x.1, e') ∂σ = p * K x) :
    collAdj σ τ P K =ᵐ[μ] fun x => τ x.1 * (p - 1) * K x := by
  filter_upwards [heig] with x hx
  simp only [collAdj, collOp, gain, transposeKernel]
  rw [hx]
  ring

theorem collEvec_eigen (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] (τ : Y → ℝ)
    (P : S → S → ℝ) {n : ℕ} (K : Fin n → Y × S → ℝ) (f g : Y × S → ℝ) (p : Fin n → ℝ)
    (hG : ∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ))
    (heig : ∀ j, ∀ᵐ x ∂(ρ.prod σ), ∫ e', P e' x.2 * K j (x.1, e') ∂σ = p j * K j x)
    (j : Fin n) :
    collEvec ρ σ τ P K f g j = (p j - 1) * ∫ x, τ x.1 * K j x * (f x - g x) ∂(ρ.prod σ) := by
  have hadj := (adjoint_pair ρ σ τ P (K j) (fun y => f y - g y) (hG j) (hloss j)).2.2
  show ∫ x, K j x * collOp σ τ P (fun y => f y - g y) x ∂(ρ.prod σ) = _
  rw [hadj, ← integral_const_mul]
  refine integral_congr_ae ?_
  filter_upwards [collAdj_eigen (ρ.prod σ) σ τ P (K j) (p j) (heig j)] with x hx
  rw [hx]
  ring

theorem constant_tau_retained (ρ : Measure Y) (σ : Measure S) (W : Y × S → ℝ) {m : ℕ}
    (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (t : ℝ) (P : S → S → ℝ) (K : Y × S → ℝ) (p : ℝ)
    (heig : ∀ᵐ x ∂(ρ.prod σ), ∫ e', P e' x.2 * K (x.1, e') ∂σ = p * K x)
    (hK : MemLp K 2 (wmeas (ρ.prod σ) W))
    (hLK : MemLp (collAdj σ (fun _ => t) P K) 2 (wmeas (ρ.prod σ) W))
    (hKV : hK.toLp K ∈ retainedSpan (ρ.prod σ) W φ hφ) :
    hLK.toLp (collAdj σ (fun _ => t) P K) ∈ retainedSpan (ρ.prod σ) W φ hφ := by
  have hac : wmeas (ρ.prod σ) W ≪ ρ.prod σ := withDensity_absolutelyContinuous _ _
  have hae : collAdj σ (fun _ => t) P K =ᵐ[wmeas (ρ.prod σ) W] (t * (p - 1)) • K := by
    refine hac.ae_le ?_
    filter_upwards [collAdj_eigen (ρ.prod σ) σ (fun _ => t) P K p heig] with x hx
    rw [hx, Pi.smul_apply, smul_eq_mul]
    ring
  rw [hLK.toLp_congr (hK.const_smul (t * (p - 1))) hae, MemLp.toLp_const_smul]
  exact Submodule.smul_mem _ _ hKV

theorem constant_tau_exact (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ]
    (s : Stat) (f g W : Y × S → ℝ) (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂(ρ.prod σ), f x ∈ cdom s) (hgd : ∀ᵐ x ∂(ρ.prod σ), g x ∈ dom s)
    (hW : WEnvelope (ρ.prod σ) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (ρ.prod σ) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (t : ℝ) (P : S → S → ℝ) (K : Fin n → Y × S → ℝ) (p : Fin n → ℝ)
    (heig : ∀ j, ∀ᵐ x ∂(ρ.prod σ), ∫ e', P e' x.2 * K j (x.1, e') ∂σ = p j * K j x)
    (hK : ∀ j, MemLp (K j) 2 (wmeas (ρ.prod σ) W))
    (hKV : ∀ j, (hK j).toLp (K j) ∈ retainedSpan (ρ.prod σ) W φ hφ)
    (hLK : ∀ j, MemLp (collAdj σ (fun _ => t) P (K j)) 2 (wmeas (ρ.prod σ) W))
    (hG : ∀ j, Integrable (fubKernel (fun _ => t) P (K j) (fun y => f y - g y))
      ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => t * K j x * (f x - g x)) (ρ.prod σ)) :
    collEvec ρ σ (fun _ => t) P K f g = 0 :=
  (collision_exact_of_retained ρ σ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch (fun _ => t) P K
    hLK hG hloss (fun j => constant_tau_retained ρ σ W φ hφ t P (K j) (p j) (heig j) (hK j)
      (hLK j) (hKV j))).2

end Operator

/-! ## T8: negative control and non-vacuity (finite model on Bool × Bool, counting measures) -/

theorem integral_count_bool (u : Bool → ℝ) :
    ∫ e, u e ∂(Measure.count : Measure Bool) = u true + u false := by
  rw [integral_fintype Integrable.of_finite]
  simp [Measure.real, Measure.count_singleton]

theorem integral_count_bool2 (F : Bool × Bool → ℝ) :
    ∫ x, F x ∂((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) =
      F (true, true) + F (true, false) + (F (false, true) + F (false, false)) := by
  rw [integral_prod _ Integrable.of_finite]
  simp only [integral_count_bool]

/-- s(e) = ±1, the antisymmetric angular kernel on the two-point angle space. -/
def sgnB (e : Bool) : ℝ := if e then 1 else -1

theorem energy_dependent_tau_counterexample :
    ∃ (τ : Bool → ℝ) (P : Bool → Bool → ℝ) (K f g : Bool × Bool → ℝ) (p : ℝ),
      τ true ≠ τ false ∧ (∀ e e', P e e' = P e' e) ∧ (∀ x, 0 < f x ∧ 0 < g x) ∧
      (∀ x, ∫ e', P e' x.2 * K (x.1, e') ∂(Measure.count : Measure Bool) = p * K x) ∧
      Integrable (fubKernel τ P K (fun y => f y - g y))
        (((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)).prod
          (Measure.count : Measure Bool)) ∧
      Integrable (fun x => τ x.1 * K x * (f x - g x))
        ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) ∧
      ∫ x, K x * (f x - g x) ∂((Measure.count : Measure Bool).prod (Measure.count : Measure Bool))
        = 0 ∧
      collEvec (Measure.count : Measure Bool) (Measure.count : Measure Bool) τ P
        (fun _ : Fin 1 => K) f g 0 ≠ 0 ∧
      collEvec (Measure.count : Measure Bool) (Measure.count : Measure Bool) (fun _ => τ true) P
        (fun _ : Fin 1 => K) f g 0 = 0 := by
  refine ⟨fun E => if E then 2 else 1, fun _ _ => 1 / 2, fun x => sgnB x.2,
    fun x => 2 + (if x.1 then -1 else 1) * sgnB x.2, fun _ => 2, 0, by norm_num,
    fun _ _ => rfl, ?_, ?_, Integrable.of_finite, Integrable.of_finite, ?_, ?_, ?_⟩
  · intro x
    refine ⟨?_, by norm_num⟩
    rcases x with ⟨E, e⟩
    cases E <;> cases e <;> norm_num [sgnB]
  · intro x
    rw [integral_count_bool]
    norm_num [sgnB]
  · rw [integral_count_bool2]
    norm_num [sgnB]
  · simp only [collEvec, collOp, gain, integral_count_bool2, integral_count_bool]
    norm_num [sgnB]
  · simp only [collEvec, collOp, gain, integral_count_bool2, integral_count_bool]
    norm_num [sgnB]

theorem nonvacuity_bounded_witness :
    ∃ (f g : Bool × Bool → ℝ) (w τ : Bool → ℝ) (P : Bool → Bool → ℝ)
      (K : Fin 1 → Bool × Bool → ℝ) (ε : ℝ),
      Measurable f ∧ Measurable g ∧ Measurable w ∧ Measurable τ ∧
      Measurable (Function.uncurry P) ∧
      (∀ᵐ x ∂((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)),
        f x ∈ cdom .MB) ∧
      (∀ᵐ x ∂((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)),
        g x ∈ dom .MB) ∧
      WEnvelope ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) .MB
        (fun x => w x.1) f g ∧
      0 ≤ ε ∧
      Dext ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) (hS .MB)
        (hS' .MB) f g ≤ ENNReal.ofReal ε ∧
      (∀ E, |τ E| ≤ 1) ∧ (∀ e e', |P e e'| ≤ 1) ∧
      (∀ j, MemLp (K j) 2
        (wmeas ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool))
          (fun x => w x.1))) ∧
      f ≠ g ∧
      collEvec (Measure.count : Measure Bool) (Measure.count : Measure Bool) τ P K f g ≠ 0 := by
  set μ : Measure (Bool × Bool) := (Measure.count : Measure Bool).prod (Measure.count : Measure Bool)
    with hμ
  set f : Bool × Bool → ℝ := fun x => 2 + sgnB x.2 with hfdef
  set g : Bool × Bool → ℝ := fun _ => 2 with hgdef
  have hDtop : Dext μ (hS .MB) (hS' .MB) f g ≠ ⊤ := by
    unfold Dext
    rw [lintegral_fintype]
    exact ENNReal.sum_ne_top.2 fun x _ =>
      ENNReal.mul_ne_top ENNReal.ofReal_ne_top (measure_ne_top _ _)
  haveI : IsFiniteMeasure (wmeas μ (fun x : Bool × Bool => (fun _ : Bool => (3 : ℝ)) x.1)) := by
    unfold wmeas
    exact isFiniteMeasure_withDensity_ofReal (hasFiniteIntegral_const 3)
  have hf1 : ∀ x, 1 ≤ f x ∧ f x ≤ 3 := by
    intro x
    rcases x with ⟨E, e⟩
    cases e <;> norm_num [hfdef, sgnB]
  refine ⟨f, g, fun _ => 3, fun _ => 1, fun _ _ => 1 / 2, fun _ x => sgnB x.2,
    (Dext μ (hS .MB) (hS' .MB) f g).toReal, measurable_of_countable _, measurable_of_countable _,
    measurable_of_countable _, measurable_of_countable _, measurable_of_countable _,
    Eventually.of_forall fun x => ?_, Eventually.of_forall fun x => ?_, ⟨measurable_of_countable _,
      Eventually.of_forall fun _ => by norm_num, Eventually.of_forall fun x z hz => ?_⟩,
    ENNReal.toReal_nonneg, (ENNReal.ofReal_toReal hDtop).ge, fun _ => by norm_num,
    fun _ _ => by norm_num [abs_of_pos], fun _ => ?_, ?_, ?_⟩
  · show 0 ≤ f x
    linarith [(hf1 x).1]
  · show (0 : ℝ) < 2
    norm_num
  · simp only [xi, zero_mul, add_zero, mul_one]
    rcases Set.mem_uIcc.1 hz with h | h
    · linarith [(hf1 x).2, h.2]
    · have : g x = 2 := rfl
      linarith [h.2]
  · refine MemLp.of_bound (measurable_of_countable _).aestronglyMeasurable 1
      (Eventually.of_forall fun x => ?_)
    rcases x with ⟨E, e⟩
    cases e <;> norm_num [sgnB]
  · intro h
    have := congrFun h (true, true)
    norm_num [hfdef, hgdef, sgnB] at this
  · intro h
    have := congrFun h 0
    simp only [collEvec, collOp, gain, integral_count_bool2, integral_count_bool, Pi.zero_apply,
      hfdef, hgdef] at this
    norm_num [sgnB] at this

/-! ## T9: the source instance dν = C E² dE dΩ, photon envelope, Thomson-shape kernel -/

/-- The source's scalar elastic kernel P = 3[1 + (e·e')²]/(16π) on the unit sphere. -/
noncomputable def thomsonP (e e' : Sphere2) : ℝ :=
  3 * (1 + (inner ℝ (e : EuclideanSpace ℝ (Fin 3)) (e' : EuclideanSpace ℝ (Fin 3))) ^ 2) /
    (16 * Real.pi)

theorem thomsonP_symm (e e' : Sphere2) : thomsonP e e' = thomsonP e' e := by
  simp only [thomsonP, real_inner_comm]

theorem thomsonP_measurable : Measurable (Function.uncurry thomsonP) := by
  have h1 : Continuous fun p : Sphere2 × Sphere2 =>
      inner ℝ (p.1 : EuclideanSpace ℝ (Fin 3)) (p.2 : EuclideanSpace ℝ (Fin 3)) :=
    (continuous_subtype_val.comp continuous_fst).inner (continuous_subtype_val.comp continuous_snd)
  have hc : Continuous (Function.uncurry thomsonP) := by
    show Continuous fun p : Sphere2 × Sphere2 => thomsonP p.1 p.2
    simp only [thomsonP]
    exact (continuous_const.mul (continuous_const.add (h1.pow 2))).div_const _
  exact hc.measurable

theorem thomsonP_bounds (e e' : Sphere2) :
    0 ≤ thomsonP e e' ∧ thomsonP e e' ≤ 3 / (8 * Real.pi) := by
  have hn : ∀ v : Sphere2, ‖(v : EuclideanSpace ℝ (Fin 3))‖ = 1 := fun v =>
    mem_sphere_zero_iff_norm.1 v.2
  have hin : |inner ℝ (e : EuclideanSpace ℝ (Fin 3)) (e' : EuclideanSpace ℝ (Fin 3))| ≤ 1 := by
    have := abs_real_inner_le_norm (e : EuclideanSpace ℝ (Fin 3)) (e' : EuclideanSpace ℝ (Fin 3))
    rwa [hn e, hn e', one_mul] at this
  have hsq : (inner ℝ (e : EuclideanSpace ℝ (Fin 3)) (e' : EuclideanSpace ℝ (Fin 3))) ^ 2 ≤ 1 :=
    (sq_le_one_iff_abs_le_one _).2 hin
  have hpi : 0 < Real.pi := Real.pi_pos
  constructor
  · unfold thomsonP
    positivity
  · unfold thomsonP
    rw [div_le_div_iff₀ (by positivity) (by positivity)]
    nlinarith [mul_le_mul_of_nonneg_left hsq hpi.le]

/-- The energy factor C E² dE on (0, ∞). -/
noncomputable def energyMeasure (C : ℝ) : Measure ℝ :=
  (volume.restrict (Ioi (0 : ℝ))).withDensity (fun E => ENNReal.ofReal (C * E ^ 2))

theorem nu_eq_prod (C : ℝ) : nu C = (energyMeasure C).prod dOmega := rfl

/-- The photon weight W = F_b (1 + F_b), energy only. -/
noncomputable def photonW (b : ℝ) : ℝ × Sphere2 → ℝ := fun x => CAS12PlanckIR.weight b x.1

theorem weight_measurable (b : ℝ) : Measurable fun E : ℝ => CAS12PlanckIR.weight b E := by
  unfold CAS12PlanckIR.weight
  fun_prop

theorem weight_pos (b E : ℝ) (hb : 0 < b) (hE : 0 < E) : 0 < CAS12PlanckIR.weight b E := by
  unfold CAS12PlanckIR.weight
  have h1 : 1 < Real.exp (b * E) := by
    have := Real.add_one_lt_exp (mul_pos hb hE).ne'
    linarith [mul_pos hb hE]
  have h2 : 0 < Real.exp (b * E) - 1 := by linarith
  positivity

theorem nu_ae_pos (C : ℝ) : ∀ᵐ x ∂nu C, 0 < x.1 := by
  have h1 : ∀ᵐ E ∂(energyMeasure C), 0 < E := by
    unfold energyMeasure
    exact (withDensity_absolutelyContinuous _ _).ae_le (ae_restrict_mem measurableSet_Ioi)
  rw [nu_eq_prod]
  exact Measure.quasiMeasurePreserving_fst.ae h1

theorem photon_envelope (C b : ℝ) (hb : 0 < b) (f g : ℝ × Sphere2 → ℝ)
    (hfF : ∀ᵐ x ∂nu C, 0 ≤ f x ∧ f x ≤ G12D.occupation b 0 x.1)
    (hgF : ∀ᵐ x ∂nu C, 0 < g x ∧ g x ≤ G12D.occupation b 0 x.1) :
    (∀ᵐ x ∂nu C, f x ∈ cdom .BE) ∧ (∀ᵐ x ∂nu C, g x ∈ dom .BE) ∧
      WEnvelope (nu C) .BE (photonW b) f g := by
  refine ⟨hfF.mono fun x hx => hx.1, hgF.mono fun x hx => hx.1,
    (weight_measurable b).comp measurable_fst, ?_, ?_⟩
  · filter_upwards [nu_ae_pos C] with x hx
    exact weight_pos b x.1 hb hx
  · filter_upwards [nu_ae_pos C, hfF, hgF] with x hx hfx hgx z hz
    simp only [xi, one_mul]
    rw [Set.uIcc, Set.mem_Icc] at hz
    exact G12DClosure.between_states_weight_bound b x.1 (f x) (g x) z hb hx hfx.1 hfx.2
      hgx.1.le hgx.2 hz.1 hz.2

theorem photon_thomson_collision_ellipsoid (C b : ℝ) (hb : 0 < b) (f g : ℝ × Sphere2 → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfF : ∀ᵐ x ∂nu C, 0 ≤ f x ∧ f x ≤ G12D.occupation b 0 x.1)
    (hgF : ∀ᵐ x ∂nu C, 0 < g x ∧ g x ≤ G12D.occupation b 0 x.1)
    {ε : ℝ} (hε0 : 0 ≤ ε) (hε : Dext (nu C) (hS .BE) (hS' .BE) f g ≤ ENNReal.ofReal ε)
    (τ : ℝ → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    {m n : ℕ} (φ : Fin m → ℝ × Sphere2 → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (nu C) (photonW b)))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂nu C = 0)
    (K : Fin n → ℝ × Sphere2 → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas (nu C) (photonW b))) :
    collAdj dOmega τ thomsonP = collOp dOmega τ thomsonP ∧
    (∀ j, MemLp (collOp dOmega τ thomsonP (K j)) 2 (wmeas (nu C) (photonW b))) ∧
    ∀ hLK : (∀ j, MemLp (collOp dOmega τ thomsonP (K j)) 2 (wmeas (nu C) (photonW b))),
      collEvec (energyMeasure C) dOmega τ thomsonP K f g =
          evec (nu C) (fun j => collOp dOmega τ thomsonP (K j)) f g ∧
        (gramR (nu C) (photonW b) φ hφ (fun j => collOp dOmega τ thomsonP (K j)) hLK).PosSemidef ∧
        collEvec (energyMeasure C) dOmega τ thomsonP K f g ∈ LinearMap.range
          (gramR (nu C) (photonW b) φ hφ (fun j => collOp dOmega τ thomsonP (K j)) hLK).toLin' ∧
        collEvec (energyMeasure C) dOmega τ thomsonP K f g ⬝ᵥ
          (CAS11C02.spectralPinvMatrix
              (gramR (nu C) (photonW b) φ hφ (fun j => collOp dOmega τ thomsonP (K j)) hLK)
              (gramR_posSemidef (nu C) (photonW b) φ hφ
                (fun j => collOp dOmega τ thomsonP (K j)) hLK).isHermitian *ᵥ
            collEvec (energyMeasure C) dOmega τ thomsonP K f g) ≤ 2 * ε := by
  have hsym := collAdj_eq_collOp_of_symm (Y := ℝ) dOmega τ thomsonP_symm
  obtain ⟨hfd, hgd, hW⟩ := photon_envelope C b hb f g hfF hgF
  have hPbd : ∀ e e', |thomsonP e e'| ≤ 3 / (8 * Real.pi) := fun e e' => by
    rw [abs_of_nonneg (thomsonP_bounds e e').1]
    exact (thomsonP_bounds e e').2
  obtain ⟨hLK, -, hmain⟩ := collision_ellipsoid_bounded (energyMeasure C) dOmega .BE f g
    (fun E => CAS12PlanckIR.weight b E) (weight_measurable b) hf hg hfd hgd hW hε0 hε τ hτm hτ
    thomsonP thomsonP_measurable hPbd φ hφ hmatch K hK
  rw [hsym] at hLK hmain
  exact ⟨hsym, hLK, hmain⟩

end G12A
