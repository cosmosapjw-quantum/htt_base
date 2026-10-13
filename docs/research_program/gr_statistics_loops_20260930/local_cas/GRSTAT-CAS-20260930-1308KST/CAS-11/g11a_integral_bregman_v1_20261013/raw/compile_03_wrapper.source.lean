import Mathlib
import BregmanThreePoint

/-!
G11-A (GR-CAS-11, TEFF-A0/A1): integral Bregman three-point identity on a measure
space, cancellation under exact finite retained-moment matching, nonnegativity and
the finite/infinite divergence branch, statistics instance (MB/BE/FD, Paper I
(9)-(14), Def. 1) and the massless measure dν = C E² dE dΩ.  Targets are frozen in
`../FROZEN_TARGETS.md`.  The pointwise identity is obtained from the accepted
C01 v2 theorem `CAS11C01.three_point` at dimension one.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

namespace G11A

/-! ## Definitions -/

/-- Pointwise Bregman density, the integrand of Paper I (16) / Paper II (25). -/
def bregDens (h h' : ℝ → ℝ) (a b : ℝ) : ℝ := h a - h b - h' b * (a - b)

section General

variable {X : Type*} [MeasurableSpace X]

/-- Finite-branch (Bochner) integral divergence; meaningful only under integrability. -/
noncomputable def Dfin (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ) : ℝ :=
  ∫ x, bregDens h h' (f x) (g x) ∂μ

/-- Extended-value integral divergence in `[0, ∞]`. -/
noncomputable def Dext (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ) : ℝ≥0∞ :=
  ∫⁻ x, ENNReal.ofReal (bregDens h h' (f x) (g x)) ∂μ

end General

/-! ## P0/P1: reuse of the accepted C01 v2 finite identity -/

theorem bregDens_eq_c01 (h h' : ℝ → ℝ) (a b : ℝ) :
    bregDens h h' a b =
      CAS11C01.bregman (n := 1) (fun v => h (v 0)) (fun v _ => h' (v 0))
        (fun _ => a) (fun _ => b) := by
  simp [bregDens, CAS11C01.bregman, CAS11C01.dot]

theorem pointwise_three_point (h h' : ℝ → ℝ) (a b c : ℝ) :
    bregDens h h' a b - bregDens h h' a c - bregDens h h' c b =
      (h' c - h' b) * (a - c) := by
  rw [bregDens_eq_c01, bregDens_eq_c01, bregDens_eq_c01, CAS11C01.three_point]
  simp [CAS11C01.dot]

section General

variable {X : Type*} [MeasurableSpace X]

/-! ## K0: source-form agreement -/

theorem source_form_eq (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ)
    (hf : Integrable (fun x => h (f x)) μ) (hg : Integrable (fun x => h (g x)) μ)
    (hlin : Integrable (fun x => h' (g x) * (f x - g x)) μ) :
    Dfin μ h h' f g =
      (∫ x, h (f x) ∂μ) - (∫ x, h (g x) ∂μ) - ∫ x, h' (g x) * (f x - g x) ∂μ := by
  unfold Dfin bregDens
  have h1 := integral_sub (μ := μ) (f := fun x => h (f x) - h (g x))
    (g := fun x => h' (g x) * (f x - g x)) (hf.sub hg) hlin
  rw [h1, integral_sub hf hg]

/-! ## K1: integral three-point identity -/

theorem cross_integrable (μ : Measure X) (h h' : ℝ → ℝ) (f g k : X → ℝ)
    (hfg : Integrable (fun x => bregDens h h' (f x) (g x)) μ)
    (hfk : Integrable (fun x => bregDens h h' (f x) (k x)) μ)
    (hkg : Integrable (fun x => bregDens h h' (k x) (g x)) μ) :
    Integrable (fun x => (h' (k x) - h' (g x)) * (f x - k x)) μ := by
  refine ((hfg.sub hfk).sub hkg).congr (ae_of_all _ fun x => ?_)
  exact pointwise_three_point h h' (f x) (g x) (k x)

theorem integral_three_point (μ : Measure X) (h h' : ℝ → ℝ) (f g k : X → ℝ)
    (hfg : Integrable (fun x => bregDens h h' (f x) (g x)) μ)
    (hfk : Integrable (fun x => bregDens h h' (f x) (k x)) μ)
    (hkg : Integrable (fun x => bregDens h h' (k x) (g x)) μ) :
    Dfin μ h h' f g - Dfin μ h h' f k - Dfin μ h h' k g =
      ∫ x, (h' (k x) - h' (g x)) * (f x - k x) ∂μ := by
  unfold Dfin
  rw [← integral_sub hfg hfk]
  have h1 := integral_sub (μ := μ)
    (f := fun x => bregDens h h' (f x) (g x) - bregDens h h' (f x) (k x))
    (g := fun x => bregDens h h' (k x) (g x)) (hfg.sub hfk) hkg
  rw [← h1]
  congr 1
  funext x
  exact pointwise_three_point h h' (f x) (g x) (k x)

/-! ## K2: cancellation of the cross term -/

theorem cross_term_vanishes {m : ℕ} (μ : Measure X) (h h' : ℝ → ℝ) (f g k : X → ℝ)
    (φ : Fin m → X → ℝ) (lam : Fin m → ℝ)
    (hspan : ∀ᵐ x ∂μ, h' (k x) - h' (g x) = ∑ j, lam j * φ j x)
    (hφf : ∀ j, Integrable (fun x => φ j x * f x) μ)
    (hφk : ∀ j, Integrable (fun x => φ j x * k x) μ)
    (hmatch : ∀ j, ∫ x, φ j x * f x ∂μ = ∫ x, φ j x * k x ∂μ) :
    ∫ x, (h' (k x) - h' (g x)) * (f x - k x) ∂μ = 0 := by
  have h1 : ∫ x, (h' (k x) - h' (g x)) * (f x - k x) ∂μ =
      ∫ x, ∑ j, lam j * (φ j x * f x - φ j x * k x) ∂μ := by
    refine integral_congr_ae (hspan.mono fun x hx => ?_)
    simp only
    rw [hx, Finset.sum_mul]
    exact Finset.sum_congr rfl fun j _ => by ring
  rw [h1, integral_finset_sum]
  · refine Finset.sum_eq_zero fun j _ => ?_
    rw [integral_const_mul, integral_sub (hφf j) (hφk j), hmatch j, sub_self, mul_zero]
  · intro j _
    exact ((hφf j).sub (hφk j)).const_mul (lam j)

theorem pythagorean {m : ℕ} (μ : Measure X) (h h' : ℝ → ℝ) (f g k : X → ℝ)
    (hfg : Integrable (fun x => bregDens h h' (f x) (g x)) μ)
    (hfk : Integrable (fun x => bregDens h h' (f x) (k x)) μ)
    (hkg : Integrable (fun x => bregDens h h' (k x) (g x)) μ)
    (φ : Fin m → X → ℝ) (lam : Fin m → ℝ)
    (hspan : ∀ᵐ x ∂μ, h' (k x) - h' (g x) = ∑ j, lam j * φ j x)
    (hφf : ∀ j, Integrable (fun x => φ j x * f x) μ)
    (hφk : ∀ j, Integrable (fun x => φ j x * k x) μ)
    (hmatch : ∀ j, ∫ x, φ j x * f x ∂μ = ∫ x, φ j x * k x ∂μ) :
    Dfin μ h h' f g = Dfin μ h h' f k + Dfin μ h h' k g := by
  have h3 := integral_three_point μ h h' f g k hfg hfk hkg
  rw [cross_term_vanishes μ h h' f g k φ lam hspan hφf hφk hmatch] at h3
  linarith

end General

/-! ## K3: nonnegativity and the finite/infinite branch -/

theorem bregDens_nonneg {S : Set ℝ} {h h' : ℝ → ℝ} (hconv : ConvexOn ℝ S h) {a b : ℝ}
    (ha : a ∈ S) (hb : b ∈ S) (hd : HasDerivAt h (h' b) b) : 0 ≤ bregDens h h' a b := by
  unfold bregDens
  rcases lt_trichotomy a b with hab | rfl | hab
  · have hs := hconv.slope_le_of_hasDerivAt ha hb hab hd
    rw [slope_def_field, div_le_iff₀ (sub_pos.2 hab)] at hs
    nlinarith
  · simp
  · have hs := hconv.le_slope_of_hasDerivAt hb ha hab hd
    rw [slope_def_field, le_div_iff₀ (sub_pos.2 hab)] at hs
    linarith

section General

variable {X : Type*} [MeasurableSpace X]

theorem Dfin_nonneg (μ : Measure X) {S : Set ℝ} {h h' : ℝ → ℝ} (hconv : ConvexOn ℝ S h)
    (f g : X → ℝ) (hf : ∀ᵐ x ∂μ, f x ∈ S) (hg : ∀ᵐ x ∂μ, g x ∈ S)
    (hd : ∀ᵐ x ∂μ, HasDerivAt h (h' (g x)) (g x)) : 0 ≤ Dfin μ h h' f g := by
  unfold Dfin
  refine integral_nonneg_of_ae ?_
  filter_upwards [hf, hg, hd] with x hfx hgx hdx
  exact bregDens_nonneg hconv hfx hgx hdx

theorem Dext_ne_top_iff (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ)
    (hmeas : AEStronglyMeasurable (fun x => bregDens h h' (f x) (g x)) μ)
    (hnn : ∀ᵐ x ∂μ, 0 ≤ bregDens h h' (f x) (g x)) :
    Dext μ h h' f g ≠ ⊤ ↔ Integrable (fun x => bregDens h h' (f x) (g x)) μ := by
  unfold Dext
  exact lintegral_ofReal_ne_top_iff_integrable hmeas hnn

theorem Dext_eq_ofReal (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ)
    (hint : Integrable (fun x => bregDens h h' (f x) (g x)) μ)
    (hnn : ∀ᵐ x ∂μ, 0 ≤ bregDens h h' (f x) (g x)) :
    Dext μ h h' f g = ENNReal.ofReal (Dfin μ h h' f g) := by
  unfold Dext Dfin
  exact (ofReal_integral_eq_lintegral_ofReal hint hnn).symm

theorem finite_budget (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ)
    (hmeas : AEStronglyMeasurable (fun x => bregDens h h' (f x) (g x)) μ)
    (hnn : ∀ᵐ x ∂μ, 0 ≤ bregDens h h' (f x) (g x)) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ h h' f g ≤ ENNReal.ofReal ε) :
    Integrable (fun x => bregDens h h' (f x) (g x)) μ ∧ 0 ≤ Dfin μ h h' f g ∧
      Dfin μ h h' f g ≤ ε := by
  have hne : Dext μ h h' f g ≠ ⊤ := ne_top_of_le_ne_top ENNReal.ofReal_ne_top hε
  have hint := (Dext_ne_top_iff μ h h' f g hmeas hnn).1 hne
  refine ⟨hint, integral_nonneg_of_ae hnn, ?_⟩
  rw [Dext_eq_ofReal μ h h' f g hint hnn] at hε
  exact (ENNReal.ofReal_le_ofReal_iff hε0).1 hε

theorem infinite_branch_no_budget (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ)
    (hmeas : AEStronglyMeasurable (fun x => bregDens h h' (f x) (g x)) μ)
    (hnn : ∀ᵐ x ∂μ, 0 ≤ bregDens h h' (f x) (g x))
    (hni : ¬ Integrable (fun x => bregDens h h' (f x) (g x)) μ) :
    Dext μ h h' f g = ⊤ ∧ (∀ ε : ℝ, ¬ Dext μ h h' f g ≤ ENNReal.ofReal ε) ∧
      Dfin μ h h' f g = 0 := by
  have htop : Dext μ h h' f g = ⊤ := by
    by_contra hc
    exact hni ((Dext_ne_top_iff μ h h' f g hmeas hnn).1 hc)
  refine ⟨htop, fun ε hle => ?_, integral_undef hni⟩
  rw [htop, top_le_iff] at hle
  exact ENNReal.ofReal_ne_top hle

theorem nested_budget {m : ℕ} (μ : Measure X) {S : Set ℝ} {h h' : ℝ → ℝ}
    (f g k : X → ℝ)
    (hfg : Integrable (fun x => bregDens h h' (f x) (g x)) μ)
    (hfk : Integrable (fun x => bregDens h h' (f x) (k x)) μ)
    (hkg : Integrable (fun x => bregDens h h' (k x) (g x)) μ)
    (φ : Fin m → X → ℝ) (lam : Fin m → ℝ)
    (hspan : ∀ᵐ x ∂μ, h' (k x) - h' (g x) = ∑ j, lam j * φ j x)
    (hφf : ∀ j, Integrable (fun x => φ j x * f x) μ)
    (hφk : ∀ j, Integrable (fun x => φ j x * k x) μ)
    (hmatch : ∀ j, ∫ x, φ j x * f x ∂μ = ∫ x, φ j x * k x ∂μ)
    (hconv : ConvexOn ℝ S h) (hk : ∀ᵐ x ∂μ, k x ∈ S) (hg : ∀ᵐ x ∂μ, g x ∈ S)
    (hd : ∀ᵐ x ∂μ, HasDerivAt h (h' (g x)) (g x)) :
    Dfin μ h h' f k ≤ Dfin μ h h' f g := by
  rw [pythagorean μ h h' f g k hfg hfk hkg φ lam hspan hφf hφk hmatch]
  have := Dfin_nonneg μ hconv k g hk hg hd
  linarith

end General

/-! ## Statistics instance: Paper I (9)-(14), Definition 1 -/

inductive Stat
  | MB
  | BE
  | FD

/-- Paper I (9). -/
def xi : Stat → ℝ
  | .MB => 0
  | .BE => 1
  | .FD => -1

/-- Paper I (11). -/
noncomputable def hMB (f : ℝ) : ℝ := f * Real.log f - f
/-- Paper I (12). -/
noncomputable def hBE (f : ℝ) : ℝ := f * Real.log f - (1 + f) * Real.log (1 + f)
/-- Paper I (13). -/
noncomputable def hFD (f : ℝ) : ℝ := f * Real.log f + (1 - f) * Real.log (1 - f)

noncomputable def hS : Stat → ℝ → ℝ
  | .MB => hMB
  | .BE => hBE
  | .FD => hFD

/-- Paper I (14), first formula. -/
noncomputable def hS' (s : Stat) (f : ℝ) : ℝ := Real.log (f / (1 + xi s * f))

/-- Paper I (14), second formula. -/
noncomputable def hess (s : Stat) (f : ℝ) : ℝ := 1 / (f * (1 + xi s * f))

/-- Physical (regular, open) domains, Paper I p. 2. -/
def dom : Stat → Set ℝ
  | .MB => Ioi 0
  | .BE => Ioi 0
  | .FD => Ioo 0 1

/-- Admissible closure, Paper I Definition 1. -/
def cdom : Stat → Set ℝ
  | .MB => Ici 0
  | .BE => Ici 0
  | .FD => Icc 0 1

/-- Paper I (10). -/
noncomputable def Phi : Stat → ℝ → ℝ
  | .MB, z => Real.exp (-z)
  | .BE, z => 1 / (Real.exp z - 1)
  | .FD, z => 1 / (Real.exp z + 1)

theorem dom_subset_cdom (s : Stat) : dom s ⊆ cdom s := by
  cases s
  · exact Ioi_subset_Ici_self
  · exact Ioi_subset_Ici_self
  · exact Ioo_subset_Icc_self

theorem interior_cdom (s : Stat) : interior (cdom s) = dom s := by
  cases s
  · exact interior_Ici
  · exact interior_Ici
  · exact interior_Icc

theorem dom_pos (s : Stat) {x : ℝ} (hx : x ∈ dom s) : 0 < x ∧ 0 < 1 + xi s * x := by
  cases s
  · exact ⟨hx, by simp [xi]⟩
  · have : 0 < x := hx
    exact ⟨this, by simp [xi]; linarith⟩
  · obtain ⟨h0, h1⟩ := hx
    exact ⟨h0, by simp [xi]; linarith⟩

theorem continuous_hS (s : Stat) : Continuous (hS s) := by
  cases s
  · exact Real.continuous_mul_log.sub continuous_id
  · exact Real.continuous_mul_log.sub
      (Real.continuous_mul_log.comp (continuous_const.add continuous_id))
  · exact Real.continuous_mul_log.add
      (Real.continuous_mul_log.comp (continuous_const.sub continuous_id))

theorem hasDerivAt_hS (s : Stat) {x : ℝ} (hx : x ∈ dom s) :
    HasDerivAt (hS s) (hS' s x) x := by
  obtain ⟨hx0, hx1⟩ := dom_pos s hx
  cases s
  · show HasDerivAt (fun y => y * Real.log y - y) (hS' .MB x) x
    have := (Real.hasDerivAt_mul_log hx0.ne').sub (hasDerivAt_id' x)
    convert this using 1
    simp [hS', xi]
  · show HasDerivAt (fun y => y * Real.log y - (1 + y) * Real.log (1 + y)) (hS' .BE x) x
    simp only [xi] at hx1
    have h2 : HasDerivAt (fun y : ℝ => (1 + y) * Real.log (1 + y))
        ((Real.log (1 + x) + 1) * 1) x :=
      (Real.hasDerivAt_mul_log (by linarith : (1 + x) ≠ 0)).comp x
        ((hasDerivAt_id' x).const_add 1)
    have := (Real.hasDerivAt_mul_log hx0.ne').sub h2
    convert this using 1
    simp only [hS', xi, one_mul]
    rw [Real.log_div hx0.ne' (by linarith)]
    ring
  · show HasDerivAt (fun y => y * Real.log y + (1 - y) * Real.log (1 - y)) (hS' .FD x) x
    simp only [xi] at hx1
    have h2 : HasDerivAt (fun y : ℝ => (1 - y) * Real.log (1 - y))
        ((Real.log (1 - x) + 1) * (-1)) x :=
      (Real.hasDerivAt_mul_log (by linarith : (1 - x) ≠ 0)).comp x
        ((hasDerivAt_id' x).const_sub 1)
    have := (Real.hasDerivAt_mul_log hx0.ne').add h2
    convert this using 1
    simp only [hS', xi]
    rw [show (1 : ℝ) + -1 * x = 1 - x by ring, Real.log_div hx0.ne' (by linarith)]
    ring

theorem hS'_monotoneOn (s : Stat) : MonotoneOn (hS' s) (dom s) := by
  intro x hx y hy hxy
  obtain ⟨hx0, hx1⟩ := dom_pos s hx
  obtain ⟨hy0, hy1⟩ := dom_pos s hy
  unfold hS'
  apply Real.log_le_log (div_pos hx0 hx1)
  rw [div_le_div_iff₀ hx1 hy1]
  nlinarith

theorem convexOn_hS (s : Stat) : ConvexOn ℝ (cdom s) (hS s) := by
  have hconvex : Convex ℝ (cdom s) := by
    cases s
    · exact convex_Ici 0
    · exact convex_Ici 0
    · exact convex_Icc 0 1
  refine MonotoneOn.convexOn_of_deriv hconvex (continuous_hS s).continuousOn ?_ ?_
  · rw [interior_cdom]
    intro x hx
    exact (hasDerivAt_hS s hx).differentiableAt.differentiableWithinAt
  · rw [interior_cdom]
    intro x hx y hy hxy
    rw [(hasDerivAt_hS s hx).deriv, (hasDerivAt_hS s hy).deriv]
    exact hS'_monotoneOn s hx hy hxy

theorem bregDens_nonneg_stat (s : Stat) {a b : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s) :
    0 ≤ bregDens (hS s) (hS' s) a b :=
  bregDens_nonneg (convexOn_hS s) ha (dom_subset_cdom s hb) (hasDerivAt_hS s hb)

theorem measurable_hS' (s : Stat) : Measurable (hS' s) := by
  unfold hS'
  exact Real.measurable_log.comp
    (measurable_id.div (measurable_const.add (measurable_const.mul measurable_id)))

theorem measurable_bregDens_stat (s : Stat) {Y : Type*} [MeasurableSpace Y] {f g : Y → ℝ}
    (hf : Measurable f) (hg : Measurable g) :
    Measurable (fun y => bregDens (hS s) (hS' s) (f y) (g y)) := by
  unfold bregDens
  exact (((continuous_hS s).measurable.comp hf).sub ((continuous_hS s).measurable.comp hg)).sub
    (((measurable_hS' s).comp hg).mul (hf.sub hg))

/-! ## Measure instance dν = C E² dE dΩ -/

abbrev Sphere2 := Metric.sphere (0 : EuclideanSpace ℝ (Fin 3)) 1

/-- Surface measure dΩ on the unit sphere of ℝ³. -/
noncomputable def dOmega : Measure Sphere2 :=
  (volume : Measure (EuclideanSpace ℝ (Fin 3))).toSphere

/-- The massless one-event, one-observer measure dν = C E² dE dΩ on (0,∞) × S². -/
noncomputable def nu (C : ℝ) : Measure (ℝ × Sphere2) :=
  ((volume.restrict (Ioi (0 : ℝ))).withDensity (fun E => ENNReal.ofReal (C * E ^ 2))).prod
    dOmega

theorem K1_instance (s : Stat) (C : ℝ) (f g k : ℝ × Sphere2 → ℝ)
    (hfm : Measurable f) (hgm : Measurable g) (hkm : Measurable k)
    (hf : ∀ᵐ y ∂nu C, f y ∈ cdom s) (hg : ∀ᵐ y ∂nu C, g y ∈ dom s)
    (hk : ∀ᵐ y ∂nu C, k y ∈ dom s)
    (hfg : Dext (nu C) (hS s) (hS' s) f g ≠ ⊤) (hfk : Dext (nu C) (hS s) (hS' s) f k ≠ ⊤)
    (hkg : Dext (nu C) (hS s) (hS' s) k g ≠ ⊤) :
    Dfin (nu C) (hS s) (hS' s) f g - Dfin (nu C) (hS s) (hS' s) f k -
        Dfin (nu C) (hS s) (hS' s) k g =
      ∫ y, (hS' s (k y) - hS' s (g y)) * (f y - k y) ∂nu C := by
  have nfg : ∀ᵐ y ∂nu C, 0 ≤ bregDens (hS s) (hS' s) (f y) (g y) := by
    filter_upwards [hf, hg] with y h1 h2 using bregDens_nonneg_stat s h1 h2
  have nfk : ∀ᵐ y ∂nu C, 0 ≤ bregDens (hS s) (hS' s) (f y) (k y) := by
    filter_upwards [hf, hk] with y h1 h2 using bregDens_nonneg_stat s h1 h2
  have nkg : ∀ᵐ y ∂nu C, 0 ≤ bregDens (hS s) (hS' s) (k y) (g y) := by
    filter_upwards [hk, hg] with y h1 h2 using
      bregDens_nonneg_stat s (dom_subset_cdom s h1) h2
  exact integral_three_point (nu C) (hS s) (hS' s) f g k
    ((Dext_ne_top_iff _ _ _ f g
      (measurable_bregDens_stat s hfm hgm).aestronglyMeasurable nfg).1 hfg)
    ((Dext_ne_top_iff _ _ _ f k
      (measurable_bregDens_stat s hfm hkm).aestronglyMeasurable nfk).1 hfk)
    ((Dext_ne_top_iff _ _ _ k g
      (measurable_bregDens_stat s hkm hgm).aestronglyMeasurable nkg).1 hkg)

theorem K2_instance (s : Stat) (C : ℝ) (f g k : ℝ × Sphere2 → ℝ)
    (hfm : Measurable f) (hgm : Measurable g) (hkm : Measurable k)
    (hf : ∀ᵐ y ∂nu C, f y ∈ cdom s) (hg : ∀ᵐ y ∂nu C, g y ∈ dom s)
    (hk : ∀ᵐ y ∂nu C, k y ∈ dom s)
    (hfg : Dext (nu C) (hS s) (hS' s) f g ≠ ⊤) (hfk : Dext (nu C) (hS s) (hS' s) f k ≠ ⊤)
    (hkg : Dext (nu C) (hS s) (hS' s) k g ≠ ⊤)
    {m : ℕ} (φ : Fin m → ℝ × Sphere2 → ℝ) (lam : Fin m → ℝ)
    (hspan : ∀ᵐ y ∂nu C, hS' s (k y) - hS' s (g y) = ∑ j, lam j * φ j y)
    (hφf : ∀ j, Integrable (fun y => φ j y * f y) (nu C))
    (hφk : ∀ j, Integrable (fun y => φ j y * k y) (nu C))
    (hmatch : ∀ j, ∫ y, φ j y * f y ∂nu C = ∫ y, φ j y * k y ∂nu C) :
    Dfin (nu C) (hS s) (hS' s) f g =
        Dfin (nu C) (hS s) (hS' s) f k + Dfin (nu C) (hS s) (hS' s) k g ∧
      Dfin (nu C) (hS s) (hS' s) f k ≤ Dfin (nu C) (hS s) (hS' s) f g := by
  have nfg : ∀ᵐ y ∂nu C, 0 ≤ bregDens (hS s) (hS' s) (f y) (g y) := by
    filter_upwards [hf, hg] with y h1 h2 using bregDens_nonneg_stat s h1 h2
  have nfk : ∀ᵐ y ∂nu C, 0 ≤ bregDens (hS s) (hS' s) (f y) (k y) := by
    filter_upwards [hf, hk] with y h1 h2 using bregDens_nonneg_stat s h1 h2
  have nkg : ∀ᵐ y ∂nu C, 0 ≤ bregDens (hS s) (hS' s) (k y) (g y) := by
    filter_upwards [hk, hg] with y h1 h2 using
      bregDens_nonneg_stat s (dom_subset_cdom s h1) h2
  have ifg := (Dext_ne_top_iff _ _ _ f g
      (measurable_bregDens_stat s hfm hgm).aestronglyMeasurable nfg).1 hfg
  have ifk := (Dext_ne_top_iff _ _ _ f k
      (measurable_bregDens_stat s hfm hkm).aestronglyMeasurable nfk).1 hfk
  have ikg := (Dext_ne_top_iff _ _ _ k g
      (measurable_bregDens_stat s hkm hgm).aestronglyMeasurable nkg).1 hkg
  refine ⟨pythagorean (nu C) (hS s) (hS' s) f g k ifg ifk ikg φ lam hspan hφf hφk hmatch,
    nested_budget (nu C) f g k ifg ifk ikg φ lam hspan hφf hφk hmatch (convexOn_hS s)
      (hk.mono fun y hy => dom_subset_cdom s hy) (hg.mono fun y hy => dom_subset_cdom s hy)
      (hg.mono fun y hy => hasDerivAt_hS s hy)⟩

/-! ## K4: regular interior versus occupation endpoints -/

theorem endpoints_MB : cdom .MB \ dom .MB = {0} := by
  ext x
  simp only [cdom, dom, mem_sdiff, mem_Ici, mem_Ioi, not_lt, mem_singleton_iff]
  constructor
  · rintro ⟨h1, h2⟩
    exact le_antisymm h2 h1
  · rintro rfl
    exact ⟨le_refl _, le_refl _⟩

theorem endpoints_BE : cdom .BE \ dom .BE = {0} := by
  ext x
  simp only [cdom, dom, mem_sdiff, mem_Ici, mem_Ioi, not_lt, mem_singleton_iff]
  constructor
  · rintro ⟨h1, h2⟩
    exact le_antisymm h2 h1
  · rintro rfl
    exact ⟨le_refl _, le_refl _⟩

theorem endpoints_FD : cdom .FD \ dom .FD = {0, 1} := by
  simp only [cdom, dom]
  exact Icc_sdiff_Ioo_same zero_le_one

theorem continuous_bregDens_left (s : Stat) (b : ℝ) :
    Continuous (fun a => bregDens (hS s) (hS' s) a b) := by
  unfold bregDens
  exact ((continuous_hS s).sub continuous_const).sub
    (continuous_const.mul (continuous_id.sub continuous_const))

theorem endpoint_limit (s : Stat) (e b : ℝ) :
    Tendsto (fun a => bregDens (hS s) (hS' s) a b) (𝓝[dom s] e)
      (𝓝 (bregDens (hS s) (hS' s) e b)) :=
  ((continuous_bregDens_left s b).tendsto e).mono_left nhdsWithin_le_nhds

section General

variable {X : Type*} [MeasurableSpace X]

theorem integral_endpoint_limit (μ : Measure X) (s : Stat) (fseq : ℕ → X → ℝ)
    (f g G : X → ℝ) (hfm : ∀ n, Measurable (fseq n)) (hf : Measurable f)
    (hgm : Measurable g)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x)))
    (hGi : Integrable G μ)
    (hdom : ∀ n, ∀ᵐ x ∂μ, ‖bregDens (hS s) (hS' s) (fseq n x) (g x)‖ ≤ G x) :
    Integrable (fun x => bregDens (hS s) (hS' s) (f x) (g x)) μ ∧
      Tendsto (fun n => Dfin μ (hS s) (hS' s) (fseq n) g) atTop
        (𝓝 (Dfin μ (hS s) (hS' s) f g)) := by
  have hpt : ∀ᵐ x ∂μ, Tendsto (fun n => bregDens (hS s) (hS' s) (fseq n x) (g x)) atTop
      (𝓝 (bregDens (hS s) (hS' s) (f x) (g x))) := by
    filter_upwards [hconv] with x hx
    exact ((continuous_bregDens_left s (g x)).tendsto (f x)).comp hx
  refine ⟨?_, ?_⟩
  · refine Integrable.mono' hGi (measurable_bregDens_stat s hf hgm).aestronglyMeasurable ?_
    have hall : ∀ᵐ x ∂μ, ∀ n, ‖bregDens (hS s) (hS' s) (fseq n x) (g x)‖ ≤ G x :=
      ae_all_iff.2 hdom
    filter_upwards [hall, hpt] with x hx hpx
    exact le_of_tendsto' ((continuous_norm.tendsto _).comp hpx) hx
  · unfold Dfin
    exact tendsto_integral_of_dominated_convergence G
      (fun n => (measurable_bregDens_stat s (hfm n) hgm).aestronglyMeasurable) hGi hdom hpt

end General

theorem hS_zero (s : Stat) : hS s 0 = 0 := by
  cases s <;> simp [hS, hMB, hBE, hFD]

theorem reference_lower_boundary (s : Stat) {a : ℝ} (ha : 0 < a) :
    Tendsto (fun b => bregDens (hS s) (hS' s) a b) (𝓝[dom s] 0) atTop := by
  have hh : Tendsto (hS s) (𝓝[dom s] 0) (𝓝 0) := by
    have := ((continuous_hS s).tendsto 0).mono_left (nhdsWithin_le_nhds (s := dom s))
    rwa [hS_zero] at this
  have hlin : Tendsto (fun b : ℝ => a - b) (𝓝[dom s] 0) (𝓝 a) := by
    have hc : Continuous (fun b : ℝ => a - b) := continuous_const.sub continuous_id
    have := (hc.tendsto (0 : ℝ)).mono_left (nhdsWithin_le_nhds (s := dom s))
    simpa using this
  have hq : Tendsto (fun b => b / (1 + xi s * b)) (𝓝[dom s] 0) (𝓝[>] 0) := by
    refine tendsto_nhdsWithin_iff.2 ⟨?_, ?_⟩
    · have hc : ContinuousAt (fun b : ℝ => b / (1 + xi s * b)) 0 :=
        continuousAt_id.div (continuousAt_const.add (continuousAt_const.mul continuousAt_id))
          (by simp)
      have := hc.tendsto.mono_left (nhdsWithin_le_nhds (s := dom s))
      simpa using this
    · filter_upwards [self_mem_nhdsWithin] with b hb
      obtain ⟨h0, h1⟩ := dom_pos s hb
      exact div_pos h0 h1
  have hneg : Tendsto (fun b => -hS' s b) (𝓝[dom s] 0) atTop :=
    tendsto_neg_atBot_atTop.comp (Real.tendsto_log_nhdsGT_zero.comp hq)
  have hprod := Tendsto.pos_mul_atTop ha hlin hneg
  have hsum := (tendsto_const_nhds (x := hS s a)).sub hh |>.add_atTop hprod
  refine hsum.congr fun b => ?_
  simp only [bregDens]
  ring

theorem reference_upper_boundary_FD {a : ℝ} (ha : a < 1) :
    Tendsto (fun b => bregDens (hS .FD) (hS' .FD) a b) (𝓝[dom .FD] 1) atTop := by
  have hh : Tendsto (hS .FD) (𝓝[dom .FD] 1) (𝓝 0) := by
    have := ((continuous_hS .FD).tendsto 1).mono_left (nhdsWithin_le_nhds (s := dom .FD))
    simpa [hS, hFD] using this
  have hid : Tendsto (fun b : ℝ => b) (𝓝[dom .FD] 1) (𝓝 1) :=
    tendsto_id.mono_left nhdsWithin_le_nhds
  have hlin : Tendsto (fun b : ℝ => b - a) (𝓝[dom .FD] 1) (𝓝 (1 - a)) :=
    hid.sub tendsto_const_nhds
  have hone : Tendsto (fun b : ℝ => 1 - b) (𝓝[dom .FD] 1) (𝓝[>] 0) := by
    refine tendsto_nhdsWithin_iff.2 ⟨?_, ?_⟩
    · have := (tendsto_const_nhds (x := (1 : ℝ))).sub hid
      simpa using this
    · filter_upwards [self_mem_nhdsWithin] with b hb
      have : b < 1 := hb.2
      simp only [mem_Ioi]
      linarith
  have hinv : Tendsto (fun b : ℝ => (1 - b)⁻¹) (𝓝[dom .FD] 1) atTop :=
    tendsto_inv_nhdsGT_zero.comp hone
  have hratio : Tendsto (fun b : ℝ => b * (1 - b)⁻¹) (𝓝[dom .FD] 1) atTop :=
    Tendsto.pos_mul_atTop one_pos hid hinv
  have hlog : Tendsto (fun b => hS' .FD b) (𝓝[dom .FD] 1) atTop := by
    refine (Real.tendsto_log_atTop.comp hratio).congr fun b => ?_
    simp only [Function.comp, hS', xi]
    rw [div_eq_mul_inv, show (1 : ℝ) + -1 * b = 1 - b by ring]
  have hprod := Tendsto.pos_mul_atTop (sub_pos.2 ha) hlin hlog
  have hsum := (tendsto_const_nhds (x := hS .FD a)).sub hh |>.add_atTop hprod
  refine hsum.congr fun b => ?_
  simp only [bregDens]
  ring

theorem junk_reference_control : bregDens (hS .MB) (hS' .MB) 1 0 = -1 := by
  simp [bregDens, hS, hMB, hS', xi]

/-! ## Supplementary: reciprocal-Hessian envelope W and natural fields -/

theorem hasDerivAt_hS' (s : Stat) {x : ℝ} (hx : x ∈ dom s) :
    HasDerivAt (hS' s) (hess s x) x := by
  obtain ⟨hx0, hx1⟩ := dom_pos s hx
  show HasDerivAt (fun y => Real.log (y / (1 + xi s * y))) (hess s x) x
  have hq : HasDerivAt (fun y : ℝ => y / (1 + xi s * y))
      ((1 * (1 + xi s * x) - x * (xi s * 1)) / (1 + xi s * x) ^ 2) x :=
    (hasDerivAt_id' x).div (((hasDerivAt_id' x).const_mul (xi s)).const_add 1) hx1.ne'
  have := hq.log (div_pos hx0 hx1).ne'
  convert this using 1
  unfold hess
  field_simp
  ring

theorem W_lower_bounds_hessian (s : Stat) {z w : ℝ} (hz : z ∈ dom s)
    (hw : z * (1 + xi s * z) ≤ w) : 1 / w ≤ hess s z := by
  obtain ⟨h0, h1⟩ := dom_pos s hz
  exact one_div_le_one_div_of_le (mul_pos h0 h1) hw

section General

variable {X : Type*} [MeasurableSpace X]

/-- Supplement (A2): `W` is a positive measurable upper envelope of `z (1 + ξ z)`,
the reciprocal Hessian, on each pointwise segment between `f` and `g`. -/
def WEnvelope (μ : Measure X) (s : Stat) (W f g : X → ℝ) : Prop :=
  Measurable W ∧ (∀ᵐ x ∂μ, 0 < W x) ∧
    ∀ᵐ x ∂μ, ∀ z ∈ uIcc (f x) (g x), z * (1 + xi s * z) ≤ W x

theorem WEnvelope_bounds_hessian (μ : Measure X) (s : Stat) (W f g : X → ℝ)
    (hW : WEnvelope μ s W f g) :
    ∀ᵐ x ∂μ, ∀ z ∈ uIcc (f x) (g x), z ∈ dom s → 1 / W x ≤ hess s z := by
  filter_upwards [hW.2.2] with x hx z hz hzd
  exact W_lower_bounds_hessian s hzd (hx z hz)

end General

theorem Phi_mem_dom (s : Stat) {z : ℝ} (hz : 0 < z) : Phi s z ∈ dom s := by
  have he : 1 < Real.exp z := by linarith [Real.add_one_lt_exp hz.ne']
  cases s
  · exact Real.exp_pos _
  · show 0 < 1 / (Real.exp z - 1)
    exact one_div_pos.2 (by linarith)
  · show 0 < 1 / (Real.exp z + 1) ∧ 1 / (Real.exp z + 1) < 1
    refine ⟨one_div_pos.2 (by linarith), ?_⟩
    rw [div_lt_one (by linarith)]
    linarith

theorem hS'_Phi (s : Stat) {z : ℝ} (hz : 0 < z) : hS' s (Phi s z) = -z := by
  have he : 1 < Real.exp z := by linarith [Real.add_one_lt_exp hz.ne']
  have hpos : 0 < Real.exp z := Real.exp_pos z
  unfold hS'
  rw [← Real.log_exp (-z), Real.exp_neg]
  congr 1
  cases s
  · simp [Phi, xi, Real.exp_neg]
  · simp only [Phi, xi]
    have h1 : Real.exp z - 1 ≠ 0 := by linarith
    field_simp
    ring
  · simp only [Phi, xi]
    have h1 : Real.exp z + 1 ≠ 0 := by linarith
    field_simp
    ring

section General

variable {X : Type*} [MeasurableSpace X]

theorem span_of_natural_fields {m : ℕ} (μ : Measure X) (s : Stat) (φ : Fin m → X → ℝ)
    (β β' : Fin m → ℝ) (g k : X → ℝ)
    (hg : ∀ᵐ x ∂μ, 0 < ∑ j, β j * φ j x ∧ g x = Phi s (∑ j, β j * φ j x))
    (hk : ∀ᵐ x ∂μ, 0 < ∑ j, β' j * φ j x ∧ k x = Phi s (∑ j, β' j * φ j x)) :
    ∀ᵐ x ∂μ, hS' s (k x) - hS' s (g x) = ∑ j, (β j - β' j) * φ j x := by
  filter_upwards [hg, hk] with x ⟨hgp, hgx⟩ ⟨hkp, hkx⟩
  rw [hkx, hgx, hS'_Phi s hkp, hS'_Phi s hgp]
  simp only [sub_mul, Finset.sum_sub_distrib]
  ring

end General

end G11A
