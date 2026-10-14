# G11-C frozen targets (GR-CAS-11, TEFF-A2: weighted Hilbert residual → singular ellipsoid)

Frozen 2026-10-14 before any proof compile. Only API-name probes (`raw/probes/probe01_api.lean`,
`raw/probes/probe02_api.lean`: `#check` of Mathlib / imported names) and the unchanged recompilation of the
reused modules were run before freezing. Module `G11CWeightedEllipsoid` (`lean/G11CWeightedEllipsoid.lean`),
namespace `G11C`, Lean 4.31.0, Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, Lake project
`/home/cosmosapjw/lean_oracles/viii_oracle`. Imports (unchanged, see `SOURCE_RECOVERY.md` §2):
`Mathlib`, `G11BHessianEnvelope` (→ `G11AGuarded`, `G11AIntegralBregman`, `BregmanThreePoint`),
`FiniteGram` (`CAS11C02`), `WeightedProjection` (`CAS11C03`).

Source map: `SOURCE_RECOVERY.md` §1. Card lean_steps 1-5 ↔ T1-T5. Card acceptance ↔ T5 (all n, m incl. 0;
singular R), T6 (ENT-R0, ENT-SINGULAR), T4 (all-a hypothesis discharged by the real integral).

## 0. Definitions (frozen)

```lean
open MeasureTheory Set Filter Topology
open scoped ENNReal

namespace G11C
open G11A G11B

section General
variable {X : Type*} [MeasurableSpace X]

/-- the weighted measure `W dμ` -/
noncomputable def wmeas (μ : Measure X) (W : X → ℝ) : Measure X :=
  μ.withDensity (fun x => ENNReal.ofReal (W x))

/-- the Hilbert space `L²(W dμ)` (equivalence classes) -/
abbrev L2W (μ : Measure X) (W : X → ℝ) := Lp ℝ 2 (wmeas μ W)

/-- source z = (f − g)/W -/
noncomputable def zfun (f g W : X → ℝ) : X → ℝ := fun x => (f x - g x) / W x

/-- V = span of the retained scores, inside L²(W dμ) -/
noncomputable def retainedSpan {m : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) : Submodule ℝ (L2W μ W) :=
  Submodule.span ℝ (Set.range fun a => (hφ a).toLp (φ a))

-- instances (FiniteDimensional, CompleteSpace) on `retainedSpan`, giving `HasOrthogonalProjection`

/-- r_j = K_j − P_V K_j -/
noncomputable def residuals {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) : Fin n → L2W μ W :=
  fun j => (hK j).toLp (K j) - (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j))

/-- R_ij = ⟪r_i, r_j⟫_{L²(W)} -/
noncomputable def gramR {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) : Matrix (Fin n) (Fin n) ℝ :=
  Matrix.gram ℝ (residuals μ W φ hφ K hK)

/-- e_j = ∫ K_j (f − g) dμ -/
noncomputable def evec {n : ℕ} (μ : Measure X) (K : Fin n → X → ℝ) (f g : X → ℝ) : Fin n → ℝ :=
  fun j => ∫ x, K j x * (f x - g x) ∂μ
```

"Budget hypotheses" `(BH)` below abbreviate, verbatim, the G11-B `B2_integral` hypothesis list:

```lean
(μ : Measure X) (s : Stat) (f g W : X → ℝ) (hf : Measurable f) (hg : Measurable g)
(hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
(hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
(hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
```

Intermediate lemmas that only need the class of z take `(hz : MemLp (zfun f g W) 2 (wmeas μ W))`
(a Prop; the class does not depend on the proof). Every FINAL theorem (T3-A3, T4, T5, T6, T7)
takes only `(BH)` and discharges `hz` internally by T1 — no membership is assumed there.

## T1 — L²(W dμ) class of z and its membership from G11-B (card step 1)

```lean
theorem z_memLp (BH) : MemLp (zfun f g W) 2 (wmeas μ W)

theorem z_norm_sq (BH) :
    ‖(z_memLp μ s f g W hf hg hfd hgd hW hε0 hε).toLp (zfun f g W)‖ ^ 2
        = ∫ x, (f x - g x) ^ 2 / W x ∂μ ∧
      ‖(z_memLp μ s f g W hf hg hfd hgd hW hε0 hε).toLp (zfun f g W)‖ ^ 2 ≤ 2 * ε
```

## T2 — closedness of the finite retained span and the orthogonal projection (card step 2)

```lean
theorem retainedSpan_isClosed {m : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) :
    IsClosed (retainedSpan μ W φ hφ : Set (L2W μ W))

theorem projection_spec {m : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (k : L2W μ W) :
    (retainedSpan μ W φ hφ).starProjection k ∈ retainedSpan μ W φ hφ ∧
      (∀ v ∈ retainedSpan μ W φ hφ,
        inner ℝ (k - (retainedSpan μ W φ hφ).starProjection k) v = 0) ∧
      (retainedSpan μ W φ hφ).starProjection ((retainedSpan μ W φ hφ).starProjection k)
        = (retainedSpan μ W φ hφ).starProjection k
```

## T3 — weighted inner product, moment matching ⇔ z ⊥ V, residual/Gram/e identities (card step 3)

```lean
theorem inner_toLp_eq_integral (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) {u v : X → ℝ}
    (hu : MemLp u 2 (wmeas μ W)) (hv : MemLp v 2 (wmeas μ W)) :
    inner ℝ (hu.toLp u) (hv.toLp v) = ∫ x, W x * (u x * v x) ∂μ

theorem kernel_moment_integrable (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) :
    Integrable (fun x => k x * (f x - g x)) μ ∧
      ∫ x, k x * (f x - g x) ∂μ = inner ℝ (hk.toLp k) (hz.toLp (zfun f g W))

theorem matching_iff_orthogonal {m : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) :
    (∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0) ↔
      hz.toLp (zfun f g W) ∈ (retainedSpan μ W φ hφ)ᗮ

theorem evec_eq_inner_residual {m n : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (j : Fin n) :
    evec μ K f g j = inner ℝ (residuals μ W φ hφ K hK j) (hz.toLp (zfun f g W))

theorem gramR_eq_integral {m n : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (i j : Fin n) :
    gramR μ W φ hφ K hK i j =
      ∫ x, W x * (residuals μ W φ hφ K hK i x * residuals μ W φ hφ K hK j x) ∂μ

theorem gramR_posSemidef {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    (gramR μ W φ hφ K hK).PosSemidef

-- (A3), final form
theorem single_kernel_dist_bound (BH) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) :
    |∫ x, k x * (f x - g x) ∂μ| ≤
      Real.sqrt (2 * ε) * Metric.infDist (hk.toLp k) (retainedSpan μ W φ hφ : Set (L2W μ W))
```

## T4 — a·e = ⟪Σ a_j r_j, z⟫ for every a, and the all-a Cauchy bound (card step 4)

```lean
theorem dot_evec_eq_inner {m n : ℕ} (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (a : Fin n → ℝ) :
    a ⬝ᵥ evec μ K f g = inner ℝ (∑ j, a j • residuals μ W φ hφ K hK j) (hz.toLp (zfun f g W))

theorem quad_eq_norm_sq {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (a : Fin n → ℝ) :
    a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a) = ‖∑ j, a j • residuals μ W φ hφ K hK j‖ ^ 2

theorem cauchy_all_a (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (a : Fin n → ℝ) :
    (a ⬝ᵥ evec μ K f g) ^ 2 ≤ 2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a)) ∧
      |a ⬝ᵥ evec μ K f g| ≤ Real.sqrt (2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a)))
```

## T5 — range and pseudoinverse ellipsoid via the accepted finite C02 theorem (card step 5)

All n (n = 0 handled; C02 itself needs 0 < n), all m (m = 0 ⇒ V = ⊥), every rank of R.
R† is the accepted C02 spectral pseudoinverse `CAS11C02.spectralPinvMatrix`.

```lean
theorem weighted_residual_ellipsoid (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    (gramR μ W φ hφ K hK).PosSemidef ∧
      evec μ K f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      evec μ K f g ⬝ᵥ (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
          (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ evec μ K f g) ≤ 2 * ε

end General

-- instance on the massless measure dν = C E² dE dΩ
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
          (gramR_posSemidef (nu C) W φ hφ K hK).isHermitian *ᵥ evec (nu C) K f g) ≤ 2 * ε
```

## T6 — singular loci ENT-R0 and ENT-SINGULAR (card acceptance)

```lean
-- R = 0 ⇒ e = 0 (any reason for R = 0)
theorem gramR_zero_imp_evec_zero (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    (h0 : gramR μ W φ hφ K hK = 0) : evec μ K f g = 0

-- ENT-R0: all kernels retained (K_j ∈ V) ⇒ R = 0 and e = 0
theorem all_retained (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    (hret : ∀ j, (hK j).toLp (K j) ∈ retainedSpan μ W φ hφ) :
    gramR μ W φ hφ K hK = 0 ∧ evec μ K f g = 0

-- ENT-SINGULAR: duplicated kernels give singular R and the conclusion still holds
theorem duplicated_kernels (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0)
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W))
    {i j : Fin n} (hij : i ≠ j) (hdup : K i = K j) :
    (gramR μ W φ hφ K hK).det = 0 ∧
      gramR μ W φ hφ K hK *ᵥ (Pi.single i 1 - Pi.single j 1) = 0 ∧
      evec μ K f g i = evec μ K f g j ∧
      evec μ K f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      evec μ K f g ⬝ᵥ (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
          (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ evec μ K f g) ≤ 2 * ε
```

## T7 — ENT-MISMATCH, source (A6) (no matching hypothesis)

```lean
theorem mismatch_bound (BH) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (c : Fin m → ℝ) :
    |∫ x, k x * (f x - g x) ∂μ| ≤
      Real.sqrt (2 * ε) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ +
        |∑ a, c a * ∫ x, φ a x * (f x - g x) ∂μ|
```

## T8 — negative control and non-vacuity witness (one-point space, Dirac measure, MB)

```lean
-- the matching hypothesis cannot be dropped: every other hypothesis holds, the kernel is
-- retained (R = 0), the moment is NOT matched, and e ∉ range R.
theorem negative_control_mismatch :
    ∃ (f g W : Unit → ℝ) (φ : Fin 1 → Unit → ℝ)
      (hφ : ∀ a, MemLp (φ a) 2 (wmeas (Measure.dirac ()) W))
      (K : Fin 1 → Unit → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas (Measure.dirac ()) W)),
      Measurable f ∧ Measurable g ∧
      (∀ᵐ x ∂(Measure.dirac ()), f x ∈ cdom .MB) ∧ (∀ᵐ x ∂(Measure.dirac ()), g x ∈ dom .MB) ∧
      WEnvelope (Measure.dirac ()) .MB W f g ∧
      Dext (Measure.dirac ()) (hS .MB) (hS' .MB) f g ≤ ENNReal.ofReal 1 ∧
      (∫ x, φ 0 x * (f x - g x) ∂(Measure.dirac ())) ≠ 0 ∧
      gramR (Measure.dirac ()) W φ hφ K hK = 0 ∧
      evec (Measure.dirac ()) K f g ∉ LinearMap.range (gramR (Measure.dirac ()) W φ hφ K hK).toLin'

-- non-vacuity: all hypotheses of T5 hold with f ≠ g, duplicated kernels, R ≠ 0 singular, e ≠ 0
theorem nonvacuity_singular_witness :
    ∃ (f g W : Unit → ℝ) (φ : Fin 0 → Unit → ℝ)
      (hφ : ∀ a, MemLp (φ a) 2 (wmeas (Measure.dirac ()) W))
      (K : Fin 2 → Unit → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas (Measure.dirac ()) W)),
      Measurable f ∧ Measurable g ∧
      (∀ᵐ x ∂(Measure.dirac ()), f x ∈ cdom .MB) ∧ (∀ᵐ x ∂(Measure.dirac ()), g x ∈ dom .MB) ∧
      WEnvelope (Measure.dirac ()) .MB W f g ∧
      Dext (Measure.dirac ()) (hS .MB) (hS' .MB) f g ≤ ENNReal.ofReal 1 ∧
      (∀ a, ∫ x, φ a x * (f x - g x) ∂(Measure.dirac ()) = 0) ∧
      f ≠ g ∧ K 0 = K 1 ∧
      gramR (Measure.dirac ()) W φ hφ K hK ≠ 0 ∧
      (gramR (Measure.dirac ()) W φ hφ K hK).det = 0 ∧
      evec (Measure.dirac ()) K f g ≠ 0
```

## T9 (supplementary) — the C02 spectral pseudoinverse is the Moore–Penrose inverse

Source S:74 names R† the Moore–Penrose inverse; the accepted C02 theorem uses the spectral
pseudoinverse. T9 identifies them through the four Penrose equations. If T9 is not reached it is
reported as NOT_CLAIMED (T5 then claims only the spectral pseudoinverse, exactly as C02).

```lean
theorem spectralPinv_penrose {n : ℕ} (R : Matrix (Fin n) (Fin n) ℝ) (hR : R.IsHermitian) :
    R * CAS11C02.spectralPinvMatrix R hR * R = R ∧
      CAS11C02.spectralPinvMatrix R hR * R * CAS11C02.spectralPinvMatrix R hR
        = CAS11C02.spectralPinvMatrix R hR ∧
      (R * CAS11C02.spectralPinvMatrix R hR)ᵀ = R * CAS11C02.spectralPinvMatrix R hR ∧
      (CAS11C02.spectralPinvMatrix R hR * R)ᵀ = CAS11C02.spectralPinvMatrix R hR * R
```

## Discipline

* No target conclusion is assumed: e ∈ range R, the ellipsoid and the all-a inequality are derived; the
  L²(W) membership of z is derived from G11-B (T1); integrability of K_j δ is derived (T3).
* Domains/branches inherited from G11-B: `f ∈ cdom s` (closed, endpoints), `g ∈ dom s` (open), W > 0 a.e.,
  D ≤ ε < ∞ in extended form. W = 0, W = ∞, D = ∞ and boundary references are not admitted.
* R is the Gram matrix of residuals in L²(W dμ); it is never read as a noise covariance.
* Allowed axioms: propext, Classical.choice, Quot.sound only.
