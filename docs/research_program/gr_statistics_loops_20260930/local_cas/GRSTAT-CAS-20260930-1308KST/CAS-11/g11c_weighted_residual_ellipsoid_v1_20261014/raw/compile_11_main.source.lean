import Mathlib
import G11BHessianEnvelope
import FiniteGram
import WeightedProjection

/-!
G11-C (GR-CAS-11, TEFF-A2): from the weighted Hilbert residual to the singular
ellipsoid.  Supplement TEFF_POSITIVE_BRIDGE (A1)-(A4), (A6) and the proof
lines 76-87.  Targets are frozen in `../FROZEN_TARGETS.md`; sources in
`../SOURCE_RECOVERY.md`.

* T1: the class of z = (f-g)/W in L²(W dμ); membership from the reviewed G11-B
  energy inequality `G11B.B2_integral`.
* T2: closedness of the finite retained span V and its orthogonal projection,
  inside the (infinite-dimensional) Hilbert space `Lp ℝ 2 (W dμ)`.
* T3: moment matching ⇔ z ⊥ V; r_j = K_j - P_V K_j, R_ij = ⟪r_i, r_j⟫ = ∫ W r_i r_j,
  e_j = ⟪r_j, z⟫; (A3).
* T4: a·e = ⟪Σ a_j r_j, z⟫ for every a and the all-a Cauchy bound (reused C03
  weighted Cauchy-Schwarz).
* T5: e ∈ range R and eᵀR†e ≤ 2ε through the accepted finite C02 theorem
  `CAS11C02.finiteGramForward`, for every n (n = 0 included) and every rank.
* T6-T8: ENT-R0, ENT-SINGULAR, ENT-MISMATCH (A6), negative control, non-vacuity.
* T9: the C02 spectral pseudoinverse satisfies the four Penrose equations.

Imported modules are used unchanged.
-/

open MeasureTheory Set Filter Topology Matrix
open scoped ENNReal

namespace G11C

open G11A G11B

section General

variable {X : Type*} [MeasurableSpace X]

/-! ## Definitions -/

/-- The weighted measure `W dμ`. -/
noncomputable def wmeas (μ : Measure X) (W : X → ℝ) : Measure X :=
  μ.withDensity (fun x => ENNReal.ofReal (W x))

/-- The Hilbert space `L²(W dμ)` of equivalence classes. -/
noncomputable abbrev L2W (μ : Measure X) (W : X → ℝ) := Lp ℝ 2 (wmeas μ W)

/-- Source z = (f - g)/W. -/
noncomputable def zfun (f g W : X → ℝ) : X → ℝ := fun x => (f x - g x) / W x

/-- V = span of the retained scores, inside `L²(W dμ)`. -/
noncomputable def retainedSpan {m : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) : Submodule ℝ (L2W μ W) :=
  Submodule.span ℝ (Set.range fun a => (hφ a).toLp (φ a))

instance retainedSpan_finiteDimensional {m : ℕ} (μ : Measure X) (W : X → ℝ)
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) :
    FiniteDimensional ℝ (retainedSpan μ W φ hφ) :=
  FiniteDimensional.span_of_finite ℝ (Set.finite_range _)

instance retainedSpan_completeSpace {m : ℕ} (μ : Measure X) (W : X → ℝ)
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) :
    CompleteSpace (retainedSpan μ W φ hφ) :=
  FiniteDimensional.complete ℝ _

/-- r_j = K_j - P_V K_j. -/
noncomputable def residuals {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) : Fin n → L2W μ W :=
  fun j => (hK j).toLp (K j) - (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j))

/-- R_ij = ⟪r_i, r_j⟫ in `L²(W dμ)`. -/
noncomputable def gramR {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) : Matrix (Fin n) (Fin n) ℝ :=
  Matrix.gram ℝ (residuals μ W φ hφ K hK)

/-- e_j = ∫ K_j (f - g) dμ. -/
noncomputable def evec {n : ℕ} (μ : Measure X) (K : Fin n → X → ℝ) (f g : X → ℝ) :
    Fin n → ℝ :=
  fun j => ∫ x, K j x * (f x - g x) ∂μ

/-! ## Weighted-measure helpers -/

theorem real_inner_apply (a b : ℝ) : inner ℝ a b = a * b := by
  have h := RCLike.inner_apply a b
  simp only [conj_trivial] at h
  linarith

theorem integral_wmeas (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) (h : X → ℝ) :
    ∫ x, h x ∂(wmeas μ W) = ∫ x, W x * h x ∂μ := by
  unfold wmeas
  rw [integral_withDensity_eq_integral_toReal_smul hWm.ennreal_ofReal
    (Eventually.of_forall fun _ => ENNReal.ofReal_lt_top)]
  refine integral_congr_ae ?_
  filter_upwards [hW0] with x hx
  simp [ENNReal.toReal_ofReal hx, smul_eq_mul]

theorem integrable_wmeas_iff (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) (h : X → ℝ) :
    Integrable h (wmeas μ W) ↔ Integrable (fun x => W x * h x) μ := by
  unfold wmeas
  rw [integrable_withDensity_iff hWm.ennreal_ofReal
    (Eventually.of_forall fun _ => ENNReal.ofReal_lt_top)]
  refine integrable_congr ?_
  filter_upwards [hW0] with x hx
  simp [ENNReal.toReal_ofReal hx, mul_comm]

theorem starProj_mem {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (V : Submodule ℝ E) [V.HasOrthogonalProjection] (k : E) : V.starProjection k ∈ V := by
  rw [Submodule.starProjection_apply]
  exact (V.orthogonalProjectionOnto k).2

/-! ## T3a: the weighted inner product -/

theorem inner_toLp_eq_integral (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) {u v : X → ℝ}
    (hu : MemLp u 2 (wmeas μ W)) (hv : MemLp v 2 (wmeas μ W)) :
    inner ℝ (hu.toLp u) (hv.toLp v) = ∫ x, W x * (u x * v x) ∂μ := by
  rw [L2.inner_def]
  have hae : (fun x => inner ℝ ((hu.toLp u : X → ℝ) x) ((hv.toLp v : X → ℝ) x))
      =ᵐ[wmeas μ W] fun x => u x * v x := by
    filter_upwards [hu.coeFn_toLp, hv.coeFn_toLp] with x h1 h2
    rw [h1, h2, real_inner_apply]
  rw [integral_congr_ae hae, integral_wmeas μ W hWm hW0]

/-! ## T1: the class of z in L²(W dμ) -/

theorem z_memLp (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε) :
    MemLp (zfun f g W) 2 (wmeas μ W) := by
  obtain ⟨hint, -, -⟩ := B2_integral μ s f g W hf hg hfd hgd hW hε0 hε
  have hzm : Measurable (zfun f g W) := (hf.sub hg).div hW.1
  rw [memLp_two_iff_integrable_sq hzm.aestronglyMeasurable,
    integrable_wmeas_iff μ W hW.1 (hW.2.1.mono fun x hx => hx.le)]
  refine hint.congr ?_
  filter_upwards [hW.2.1] with x hx
  simp only [zfun]
  field_simp

theorem z_norm_sq (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε) :
    ‖(z_memLp μ s f g W hf hg hfd hgd hW hε0 hε).toLp (zfun f g W)‖ ^ 2
        = ∫ x, (f x - g x) ^ 2 / W x ∂μ ∧
      ‖(z_memLp μ s f g W hf hg hfd hgd hW hε0 hε).toLp (zfun f g W)‖ ^ 2 ≤ 2 * ε := by
  obtain ⟨-, -, hle⟩ := B2_integral μ s f g W hf hg hfd hgd hW hε0 hε
  have hz := z_memLp μ s f g W hf hg hfd hgd hW hε0 hε
  have heq : ‖hz.toLp (zfun f g W)‖ ^ 2 = ∫ x, (f x - g x) ^ 2 / W x ∂μ := by
    rw [← real_inner_self_eq_norm_sq,
      inner_toLp_eq_integral μ W hW.1 (hW.2.1.mono fun x hx => hx.le) hz hz]
    refine integral_congr_ae ?_
    filter_upwards [hW.2.1] with x hx
    simp only [zfun]
    field_simp
  exact ⟨heq, heq ▸ hle⟩

/-! ## T2: closedness of V and the orthogonal projection -/

theorem retainedSpan_isClosed {m : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) :
    IsClosed (retainedSpan μ W φ hφ : Set (L2W μ W)) :=
  Submodule.closed_of_finiteDimensional _

theorem projection_spec {m : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (k : L2W μ W) :
    (retainedSpan μ W φ hφ).starProjection k ∈ retainedSpan μ W φ hφ ∧
      (∀ v ∈ retainedSpan μ W φ hφ,
        inner ℝ (k - (retainedSpan μ W φ hφ).starProjection k) v = 0) ∧
      (retainedSpan μ W φ hφ).starProjection ((retainedSpan μ W φ hφ).starProjection k)
        = (retainedSpan μ W φ hφ).starProjection k := by
  refine ⟨starProj_mem _ k, fun v hv => Submodule.starProjection_inner_eq_zero k v hv, ?_⟩
  exact Submodule.starProjection_eq_self_iff.mpr (starProj_mem _ k)

/-! ## T3: moment matching, residuals, Gram matrix -/

theorem kernel_moment_integrable (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) :
    Integrable (fun x => k x * (f x - g x)) μ ∧
      ∫ x, k x * (f x - g x) ∂μ = inner ℝ (hk.toLp k) (hz.toLp (zfun f g W)) := by
  have hW0 : ∀ᵐ x ∂μ, 0 ≤ W x := hWpos.mono fun x hx => hx.le
  have hae : (fun x => W x * (k x * zfun f g W x)) =ᵐ[μ] fun x => k x * (f x - g x) := by
    filter_upwards [hWpos] with x hx
    simp only [zfun]
    field_simp
  refine ⟨?_, ?_⟩
  · have hi : Integrable (k * zfun f g W) (wmeas μ W) := hk.integrable_mul hz
    rw [integrable_wmeas_iff μ W hWm hW0] at hi
    exact (integrable_congr hae).1 hi
  · rw [inner_toLp_eq_integral μ W hWm hW0 hk hz]
    exact (integral_congr_ae hae).symm

theorem matching_iff_orthogonal {m : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) :
    (∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0) ↔
      hz.toLp (zfun f g W) ∈ (retainedSpan μ W φ hφ)ᗮ := by
  constructor
  · intro hmatch
    rw [Submodule.mem_orthogonal]
    intro u hu
    induction hu using Submodule.span_induction with
    | mem x hx =>
      obtain ⟨a, rfl⟩ := hx
      rw [← (kernel_moment_integrable μ W hWm hWpos f g hz (hφ a)).2]
      exact hmatch a
    | zero => exact inner_zero_left _
    | add x y _ _ hx hy => rw [inner_add_left, hx, hy, add_zero]
    | smul c x _ hx => rw [real_inner_smul_left, hx, mul_zero]
  · intro horth a
    rw [(kernel_moment_integrable μ W hWm hWpos f g hz (hφ a)).2]
    exact Submodule.inner_right_of_mem_orthogonal
      (Submodule.subset_span (Set.mem_range_self a)) horth

theorem evec_eq_inner_residual {m n : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (j : Fin n) :
    evec μ K f g j = inner ℝ (residuals μ W φ hφ K hK j) (hz.toLp (zfun f g W)) := by
  have horth := (matching_iff_orthogonal μ W hWm hWpos f g hz φ hφ).1 hmatch
  have h0 : inner ℝ ((retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j)))
      (hz.toLp (zfun f g W)) = 0 :=
    Submodule.inner_right_of_mem_orthogonal (starProj_mem _ _) horth
  simp only [evec, residuals]
  rw [inner_sub_left, h0, sub_zero]
  exact (kernel_moment_integrable μ W hWm hWpos f g hz (hK j)).2

theorem gramR_eq_integral {m n : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (i j : Fin n) :
    gramR μ W φ hφ K hK i j =
      ∫ x, W x * (residuals μ W φ hφ K hK i x * residuals μ W φ hφ K hK j x) ∂μ := by
  rw [gramR, Matrix.gram_apply, L2.inner_def]
  simp_rw [real_inner_apply]
  exact integral_wmeas μ W hWm hW0 _

theorem gramR_posSemidef {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    (gramR μ W φ hφ K hK).PosSemidef :=
  Matrix.posSemidef_gram ℝ _

/-! ## T4: the all-a Cauchy bound -/

theorem dot_evec_eq_inner {m n : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (a : Fin n → ℝ) :
    a ⬝ᵥ evec μ K f g =
      inner ℝ (∑ j, a j • residuals μ W φ hφ K hK j) (hz.toLp (zfun f g W)) := by
  rw [sum_inner, dotProduct]
  refine Finset.sum_congr rfl fun j _ => ?_
  rw [real_inner_smul_left,
    evec_eq_inner_residual μ W hWm hWpos f g hz φ hφ hmatch K hK j]

theorem quad_eq_norm_sq {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (a : Fin n → ℝ) :
    a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a) = ‖∑ j, a j • residuals μ W φ hφ K hK j‖ ^ 2 := by
  have h := Matrix.star_dotProduct_gram_mulVec (𝕜 := ℝ) (residuals μ W φ hφ K hK) a a
  rw [star_trivial] at h
  rw [gramR, h, real_inner_self_eq_norm_sq]

theorem cauchy_all_a (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (a : Fin n → ℝ) :
    (a ⬝ᵥ evec μ K f g) ^ 2 ≤ 2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a)) ∧
      |a ⬝ᵥ evec μ K f g| ≤ Real.sqrt (2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a))) := by
  have hz := z_memLp μ s f g W hf hg hfd hgd hW hε0 hε
  have hzn := (z_norm_sq μ s f g W hf hg hfd hgd hW hε0 hε).2
  set z := hz.toLp (zfun f g W) with hzdef
  set u := ∑ j, a j • residuals μ W φ hφ K hK j with hudef
  have hdot := dot_evec_eq_inner μ W hW.1 hW.2.1 f g hz φ hφ hmatch K hK a
  have hquad := quad_eq_norm_sq μ W φ hφ K hK a
  have hcs := CAS11C03.weighted_cauchy_schwarz u z
  rw [real_inner_self_eq_norm_sq, real_inner_self_eq_norm_sq] at hcs
  have hsq : (a ⬝ᵥ evec μ K f g) ^ 2 ≤ 2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a)) := by
    rw [hdot, hquad, ← sq_abs]
    calc |inner ℝ u z| ^ 2 ≤ ‖u‖ ^ 2 * ‖z‖ ^ 2 := hcs
      _ ≤ ‖u‖ ^ 2 * (2 * ε) := mul_le_mul_of_nonneg_left hzn (sq_nonneg _)
      _ = 2 * ε * ‖u‖ ^ 2 := by ring
  exact ⟨hsq, Real.abs_le_sqrt hsq⟩

/-! ## T3 (A3): single-kernel distance bound -/

theorem single_kernel_dist_bound (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) :
    |∫ x, k x * (f x - g x) ∂μ| ≤
      Real.sqrt (2 * ε) * Metric.infDist (hk.toLp k) (retainedSpan μ W φ hφ : Set (L2W μ W)) := by
  have hz := z_memLp μ s f g W hf hg hfd hgd hW hε0 hε
  have hzn := (z_norm_sq μ s f g W hf hg hfd hgd hW hε0 hε).2
  set z := hz.toLp (zfun f g W) with hzdef
  set V := retainedSpan μ W φ hφ with hVdef
  set kl := hk.toLp k with hkldef
  have horth := (matching_iff_orthogonal μ W hW.1 hW.2.1 f g hz φ hφ).1 hmatch
  have hint : ∫ x, k x * (f x - g x) ∂μ = inner ℝ (kl - V.starProjection kl) z := by
    rw [(kernel_moment_integrable μ W hW.1 hW.2.1 f g hz hk).2, inner_sub_left,
      Submodule.inner_right_of_mem_orthogonal (starProj_mem V kl) horth, sub_zero]
  have hdist : ‖kl - V.starProjection kl‖ = Metric.infDist kl (V : Set (L2W μ W)) := by
    rw [Submodule.starProjection_minimal, Metric.infDist_eq_iInf]
    simp_rw [dist_eq_norm]
    rfl
  have hzs : ‖z‖ ≤ Real.sqrt (2 * ε) := by
    have := Real.abs_le_sqrt hzn
    rwa [abs_norm] at this
  rw [hint, ← hdist]
  calc |inner ℝ (kl - V.starProjection kl) z| ≤ ‖kl - V.starProjection kl‖ * ‖z‖ :=
        abs_real_inner_le_norm _ _
    _ ≤ ‖kl - V.starProjection kl‖ * Real.sqrt (2 * ε) :=
        mul_le_mul_of_nonneg_left hzs (norm_nonneg _)
    _ = Real.sqrt (2 * ε) * ‖kl - V.starProjection kl‖ := by ring

/-! ## T5: range and pseudoinverse ellipsoid -/

theorem weighted_residual_ellipsoid (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    (gramR μ W φ hφ K hK).PosSemidef ∧
      evec μ K f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      evec μ K f g ⬝ᵥ (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
          (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ evec μ K f g) ≤ 2 * ε := by
  have hR := gramR_posSemidef μ W φ hφ K hK
  refine ⟨hR, ?_⟩
  rcases Nat.eq_zero_or_pos n with hn | hn
  · subst hn
    have he : evec μ K f g = 0 := Subsingleton.elim _ _
    refine ⟨he ▸ Submodule.zero_mem _, ?_⟩
    rw [he, zero_dotProduct]
    linarith
  · obtain ⟨-, h1, h2⟩ := CAS11C02.finiteGramForward hn (gramR μ W φ hφ K hK) hR
      (evec μ K f g) ε hε0
      (fun a => (cauchy_all_a μ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch K hK a).1)
    exact ⟨h1, h2⟩

/-! ## T6: singular loci -/

theorem gramR_zero_imp_evec_zero (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    (h0 : gramR μ W φ hφ K hK = 0) : evec μ K f g = 0 := by
  obtain ⟨-, ⟨x, hx⟩, -⟩ :=
    weighted_residual_ellipsoid μ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch K hK
  rw [h0] at hx
  simpa using hx.symm

theorem gramR_eq_zero_of_retained {m n : ℕ} (μ : Measure X) (W : X → ℝ)
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    (hret : ∀ j, (hK j).toLp (K j) ∈ retainedSpan μ W φ hφ) :
    gramR μ W φ hφ K hK = 0 := by
  have hr : ∀ j, residuals μ W φ hφ K hK j = 0 := fun j => by
    simp only [residuals]
    rw [Submodule.starProjection_eq_self_iff.mpr (hret j), sub_self]
  ext i j
  simp [gramR, Matrix.gram_apply, hr]

theorem all_retained (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    (hret : ∀ j, (hK j).toLp (K j) ∈ retainedSpan μ W φ hφ) :
    gramR μ W φ hφ K hK = 0 ∧ evec μ K f g = 0 := by
  have h0 := gramR_eq_zero_of_retained μ W φ hφ K hK hret
  exact ⟨h0, gramR_zero_imp_evec_zero μ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch K hK h0⟩

theorem gramR_dup {m n : ℕ} (μ : Measure X) (W : X → ℝ)
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    {i j : Fin n} (hij : i ≠ j) (hdup : K i = K j) :
    (gramR μ W φ hφ K hK).det = 0 ∧
      gramR μ W φ hφ K hK *ᵥ (Pi.single i 1 - Pi.single j 1) = 0 := by
  have hl : (hK i).toLp (K i) = (hK j).toLp (K j) :=
    MemLp.toLp_congr (hK i) (hK j) (Eventually.of_forall fun x => by rw [hdup])
  have hr : residuals μ W φ hφ K hK i = residuals μ W φ hφ K hK j := by
    simp only [residuals, hl]
  have hrow : gramR μ W φ hφ K hK i = gramR μ W φ hφ K hK j := by
    funext l
    simp only [gramR, Matrix.gram_apply, hr]
  refine ⟨Matrix.det_zero_of_row_eq hij hrow, ?_⟩
  rw [Matrix.mulVec_sub, Matrix.mulVec_single_one, Matrix.mulVec_single_one]
  funext l
  simp only [Matrix.col_apply, Pi.sub_apply, Pi.zero_apply, gramR, Matrix.gram_apply, hr,
    sub_self]

theorem duplicated_kernels (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    {i j : Fin n} (hij : i ≠ j) (hdup : K i = K j) :
    (gramR μ W φ hφ K hK).det = 0 ∧
      gramR μ W φ hφ K hK *ᵥ (Pi.single i 1 - Pi.single j 1) = 0 ∧
      evec μ K f g i = evec μ K f g j ∧
      evec μ K f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      evec μ K f g ⬝ᵥ (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
          (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ evec μ K f g) ≤ 2 * ε := by
  obtain ⟨hdet, hnull⟩ := gramR_dup μ W φ hφ K hK hij hdup
  obtain ⟨-, hrange, hell⟩ :=
    weighted_residual_ellipsoid μ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch K hK
  exact ⟨hdet, hnull, by simp only [evec, hdup], hrange, hell⟩

/-! ## T7: ENT-MISMATCH, source (A6) -/

theorem mismatch_bound (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (c : Fin m → ℝ) :
    |∫ x, k x * (f x - g x) ∂μ| ≤
      Real.sqrt (2 * ε) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ +
        |∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ| := by
  have hz := z_memLp μ s f g W hf hg hfd hgd hW hε0 hε
  have hzn := (z_norm_sq μ s f g W hf hg hfd hgd hW hε0 hε).2
  set z := hz.toLp (zfun f g W) with hzdef
  set u := hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a) with hudef
  have hmom : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = inner ℝ ((hφ a).toLp (φ a)) z :=
    fun a => (kernel_moment_integrable μ W hW.1 hW.2.1 f g hz (hφ a)).2
  have hint : ∫ x, k x * (f x - g x) ∂μ =
      inner ℝ u z + ∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ := by
    rw [(kernel_moment_integrable μ W hW.1 hW.2.1 f g hz hk).2, hudef, inner_sub_left,
      sum_inner]
    simp_rw [real_inner_smul_left, hmom]
    ring
  have hzs : ‖z‖ ≤ Real.sqrt (2 * ε) := by
    have := Real.abs_le_sqrt hzn
    rwa [abs_norm] at this
  rw [hint]
  calc |inner ℝ u z + ∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ|
      ≤ |inner ℝ u z| + |∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ| := abs_add_le _ _
    _ ≤ ‖u‖ * ‖z‖ + |∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ| := by
        gcongr; exact abs_real_inner_le_norm _ _
    _ ≤ ‖u‖ * Real.sqrt (2 * ε) + |∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ| := by
        gcongr
    _ = Real.sqrt (2 * ε) * ‖u‖ + |∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ| := by ring

end General

/-! ## T5 on the massless measure dν = C E² dE dΩ -/

theorem weighted_residual_ellipsoid_nu (s : Stat) (C : ℝ) (f g W : ℝ × Sphere2 → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ y ∂nu C, f y ∈ cdom s) (hgd : ∀ᵐ y ∂nu C, g y ∈ dom s)
    (hW : WEnvelope (nu C) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (nu C) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → ℝ × Sphere2 → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (nu C) W))
    (hmatch : ∀ a, ∫ y, φ a y * (f y - g y) ∂nu C = 0)
    (K : Fin n → ℝ × Sphere2 → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas (nu C) W)) :
    (gramR (nu C) W φ hφ K hK).PosSemidef ∧
      evec (nu C) K f g ∈ LinearMap.range (gramR (nu C) W φ hφ K hK).toLin' ∧
      evec (nu C) K f g ⬝ᵥ (CAS11C02.spectralPinvMatrix (gramR (nu C) W φ hφ K hK)
          (gramR_posSemidef (nu C) W φ hφ K hK).isHermitian *ᵥ evec (nu C) K f g) ≤ 2 * ε :=
  weighted_residual_ellipsoid (nu C) s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch K hK

end G11C
