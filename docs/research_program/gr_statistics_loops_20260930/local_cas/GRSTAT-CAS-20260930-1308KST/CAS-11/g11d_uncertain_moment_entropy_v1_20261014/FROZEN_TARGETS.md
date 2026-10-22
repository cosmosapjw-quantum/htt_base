# G11-D frozen targets (GR-CAS-11: uncertain moment matching + measured entropy inputs, TEFF (A6))

Frozen 2026-10-14 before any proof compile. Before freezing only the unchanged recompilation of the seven
reused modules (`raw/compile_01..07_dep_*`) and one `#check`-only API probe (`raw/probes/probe01_api.lean`,
`raw/compile_08_probe01_api`) were run. Module `G11DUncertainMoment` (`lean/G11DUncertainMoment.lean`),
namespace `G11D`, Lean 4.31.0, Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, Lake project
`/home/cosmosapjw/lean_oracles/viii_oracle`. Imports (unchanged): `Mathlib`, `G11CWeightedEllipsoid`
(→ `G11BHessianEnvelope`, `G11AGuarded`, `G11AIntegralBregman`, `BregmanThreePoint`, `FiniteGram`,
`WeightedProjection`). Source map: `SOURCE_RECOVERY.md` §1. Card lean_steps 1-4 ↔ D1, D2, D3, D4;
card acceptance 1 (probability vs deterministic separated) ↔ D2 vs D5; acceptance 2 (ε not from fitted
entropy; acquisition status) ↔ D4b + `AUTHOR_RETURN.json` application status; acceptance 3 ↔ this file.

## 0. Definitions (frozen)

```lean
open MeasureTheory Set Filter Topology Matrix
open scoped ENNReal

namespace G11D
open G11A G11B G11C

section General
variable {X : Type*} [MeasurableSpace X]

/-- Δm_a = ∫ φ_a (f − g) dμ: the TRUE retained-moment mismatch of the pair (f, g). -/
noncomputable def dm {m : ℕ} (μ : Measure X) (φ : Fin m → X → ℝ) (f g : X → ℝ) : Fin m → ℝ :=
  fun a => ∫ x, φ a x * (f x - g x) ∂μ

/-- symmetric support function σ_S(c) = sup_{d ∈ S} |c · d| (real `sSup`; used only under `BddAbove`
and with S nonempty, never as a junk value). -/
noncomputable def suppAbs {m : ℕ} (S : Set (Fin m → ℝ)) (c : Fin m → ℝ) : ℝ :=
  sSup ((fun d => |c ⬝ᵥ d|) '' S)

/-- the per-moment box {d | |d_a| ≤ r_a ∀ a} (a simultaneous interval set). -/
def box {m : ℕ} (r : Fin m → ℝ) : Set (Fin m → ℝ) := {d | ∀ a, |d a| ≤ r a}

/-- the Planck occupation F_b(E) = 1/(e^{bE} − 1) on (E, e) ∈ ℝ × S². -/
noncomputable def planckF (b : ℝ) : ℝ × Sphere2 → ℝ := fun y => 1 / (Real.exp (b * y.1) - 1)
```

`(BH)` abbreviates, verbatim, the G11-B/G11-C budget hypothesis list

```lean
(μ : Measure X) (s : Stat) (f g W : X → ℝ) (hf : Measurable f) (hg : Measurable g)
(hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
(hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
(hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
```

NO theorem in D1-D3 assumes `∀ a, ∫ φ_a (f − g) = 0` unless it is explicitly the exact-matching special case
(D2f) or the reused nested-budget discharge (D3d), where it is the source's own hypothesis.

## D1 — split identity without removing Δm (card step 1)

```lean
theorem moment_split (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    {m : ℕ} (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) (c : Fin m → ℝ) :
    Integrable (fun x => (k x - ∑ a, c a * φ a x) * (f x - g x)) μ ∧
      ∫ x, k x * (f x - g x) ∂μ =
        ∫ x, (k x - ∑ a, c a * φ a x) * (f x - g x) ∂μ + c ⬝ᵥ dm μ φ f g ∧
      ∫ x, (k x - ∑ a, c a * φ a x) * (f x - g x) ∂μ =
        inner ℝ (hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)) (hz.toLp (zfun f g W))

-- final form under (BH): membership of z discharged by G11C.z_memLp
theorem moment_split_budget (BH) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (c : Fin m → ℝ) :
    Integrable (fun x => (k x - ∑ a, c a * φ a x) * (f x - g x)) μ ∧
      ∫ x, k x * (f x - g x) ∂μ =
        ∫ x, (k x - ∑ a, c a * φ a x) * (f x - g x) ∂μ + c ⬝ᵥ dm μ φ f g

-- the norm in (A6) is the L²(W dμ) norm of the FUNCTION k − c·φ
theorem combo_norm_sq (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (c : Fin m → ℝ) :
    ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ ^ 2 =
      ∫ x, W x * (k x - ∑ a, c a * φ a x) ^ 2 ∂μ
```

## D2 — deterministic residual bound ⊕ support function of the declared moment-error set (card step 2)

```lean
-- D2a: Δm ∈ S (declared set), σ any upper bound of |c·d| on S
theorem uncertain_bound (BH) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (S : Set (Fin m → ℝ)) (hS : dm μ φ f g ∈ S) (c : Fin m → ℝ) {σ : ℝ}
    (hσ : ∀ d ∈ S, |c ⬝ᵥ d| ≤ σ) :
    |∫ x, k x * (f x - g x) ∂μ| ≤
      Real.sqrt (2 * ε) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ

-- D2b: with the support function itself, simultaneously for every c whose image is bounded
theorem uncertain_bound_supp (BH) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (S : Set (Fin m → ℝ)) (hS : dm μ φ f g ∈ S) :
    ∀ c : Fin m → ℝ, BddAbove ((fun d => |c ⬝ᵥ d|) '' S) →
      |∫ x, k x * (f x - g x) ∂μ| ≤
        Real.sqrt (2 * ε) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + suppAbs S c

-- D2c: box support function, exact value (bound and attainment)
theorem box_support {m : ℕ} (r : Fin m → ℝ) (hr : ∀ a, 0 ≤ r a) (c : Fin m → ℝ) :
    BddAbove ((fun d => |c ⬝ᵥ d|) '' box r) ∧ suppAbs (box r) c = ∑ a, |c a| * r a

-- D2d: joint (all channels): coefficients of P_V K_j exist; e − BΔm is in the (A4) ellipsoid
theorem projection_coeffs_exist {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    ∃ B : Matrix (Fin n) (Fin m) ℝ, ∀ j, ∑ b, B j b • (hφ b).toLp (φ b) =
      (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j))

theorem uncertain_joint (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (B : Matrix (Fin n) (Fin m) ℝ)
    (hB : ∀ j, ∑ b, B j b • (hφ b).toLp (φ b) =
      (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j))) :
    (∀ a : Fin n → ℝ, |a ⬝ᵥ (evec μ K f g - B *ᵥ dm μ φ f g)| ≤
        Real.sqrt (2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a)))) ∧
      evec μ K f g - B *ᵥ dm μ φ f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      (evec μ K f g - B *ᵥ dm μ φ f g) ⬝ᵥ
          (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
            (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ (evec μ K f g - B *ᵥ dm μ φ f g))
        ≤ 2 * ε

-- D2e: joint + support: for every channel combination a, support term evaluated at Bᵀa
theorem uncertain_joint_support (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (B : Matrix (Fin n) (Fin m) ℝ)
    (hB : ∀ j, ∑ b, B j b • (hφ b).toLp (φ b) =
      (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j)))
    (S : Set (Fin m → ℝ)) (hS : dm μ φ f g ∈ S) (a : Fin n → ℝ) {σ : ℝ}
    (hσ : ∀ d ∈ S, |(Bᵀ *ᵥ a) ⬝ᵥ d| ≤ σ) :
    |a ⬝ᵥ evec μ K f g| ≤ Real.sqrt (2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a))) + σ

-- D2f: exact matching = the special case S = {0}; reduces to reviewed G11-C (A3)/(A4)
theorem exact_matching_special_case (BH) {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hS0 : dm μ φ f g ∈ ({0} : Set (Fin m → ℝ)))
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    (∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0) ∧
      (∀ c : Fin m → ℝ, suppAbs ({0} : Set (Fin m → ℝ)) c = 0) ∧
      (∀ j, |∫ x, K j x * (f x - g x) ∂μ| ≤
        Real.sqrt (2 * ε) *
          Metric.infDist ((hK j).toLp (K j)) (retainedSpan μ W φ hφ : Set (L2W μ W))) ∧
      evec μ K f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      evec μ K f g ⬝ᵥ (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
          (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ evec μ K f g) ≤ 2 * ε
```

## D3 — span enlargement under one envelope; nested budget kept as a separate premise (card step 3)

```lean
-- D3a: φ = φ' ∘ ι ⇒ V ⊆ V'
theorem retainedSpan_mono {m m' : ℕ} (μ : Measure X) (W : X → ℝ) (φ' : Fin m' → X → ℝ)
    (hφ' : ∀ b, MemLp (φ' b) 2 (wmeas μ W)) (ι : Fin m → Fin m') :
    retainedSpan μ W (φ' ∘ ι) (fun a => hφ' (ι a)) ≤ retainedSpan μ W φ' hφ'

-- D3b: the distance term decreases
theorem infDist_retained_mono {m m' : ℕ} (μ : Measure X) (W : X → ℝ) (φ' : Fin m' → X → ℝ)
    (hφ' : ∀ b, MemLp (φ' b) 2 (wmeas μ W)) (ι : Fin m → Fin m') (k : L2W μ W) :
    Metric.infDist k (retainedSpan μ W φ' hφ' : Set (L2W μ W)) ≤
      Metric.infDist k (retainedSpan μ W (φ' ∘ ι) (fun a => hφ' (ι a)) : Set (L2W μ W))

-- D3c: combination. Premises kept explicit and separate: the COMMON envelope W valid for the refined
-- pair (f, g'), the refined budget ε' for (f, g') (an input, not derived here), the nesting ε' ≤ ε
-- (an input), and exact matching of the ENLARGED family for (f, g').
theorem refined_bound (μ : Measure X) (s : Stat) (f g' W : X → ℝ)
    (hf : Measurable f) (hg' : Measurable g')
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hg'd : ∀ᵐ x ∂μ, g' x ∈ dom s)
    (hW' : WEnvelope μ s W f g') {ε' ε : ℝ} (hε'0 : 0 ≤ ε')
    (hε' : Dext μ (hS s) (hS' s) f g' ≤ ENNReal.ofReal ε') (hle : ε' ≤ ε)
    {m m' : ℕ} (φ' : Fin m' → X → ℝ) (hφ' : ∀ b, MemLp (φ' b) 2 (wmeas μ W))
    (ι : Fin m → Fin m') (hmatch' : ∀ b, ∫ x, φ' b x * (f x - g' x) ∂μ = 0)
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) :
    |∫ x, k x * (f x - g' x) ∂μ| ≤
        Real.sqrt (2 * ε') * Metric.infDist (hk.toLp k) (retainedSpan μ W φ' hφ' : Set (L2W μ W)) ∧
      Real.sqrt (2 * ε') * Metric.infDist (hk.toLp k) (retainedSpan μ W φ' hφ' : Set (L2W μ W)) ≤
        Real.sqrt (2 * ε) * Metric.infDist (hk.toLp k)
          (retainedSpan μ W (φ' ∘ ι) (fun a => hφ' (ι a)) : Set (L2W μ W))

-- D3d: when the reviewed G11-A Pythagorean hypotheses hold (EXACT matching of f and the refined
-- reference k on φ, gradient difference in span φ), the refined budget is discharged from the coarse one.
theorem nested_budget_discharge {m : ℕ} (μ : Measure X) (s : Stat) (f g k : X → ℝ)
    (hf : Measurable f) (hg : Measurable g) (hk : Measurable k)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s) (hkd : ∀ᵐ x ∂μ, k x ∈ dom s)
    {ε : ℝ} (hε0 : 0 ≤ ε) (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    (hfk : Integrable (fun x => bregDens (hS s) (hS' s) (f x) (k x)) μ)
    (hkg : Integrable (fun x => bregDens (hS s) (hS' s) (k x) (g x)) μ)
    (φ : Fin m → X → ℝ) (lam : Fin m → ℝ)
    (hspan : ∀ᵐ x ∂μ, hS' s (k x) - hS' s (g x) = ∑ j, lam j * φ j x)
    (hφf : ∀ j, Integrable (fun x => φ j x * f x) μ)
    (hφk : ∀ j, Integrable (fun x => φ j x * k x) μ)
    (hmatch : ∀ j, ∫ x, φ j x * f x ∂μ = ∫ x, φ j x * k x ∂μ) :
    Dext μ (hS s) (hS' s) f k ≤ ENNReal.ofReal ε
```

## D4 — input witnesses for W and ε; negative controls (card step 4)

```lean
-- D4a: (A5)-type upper envelope ⇒ (A2) for ξ ≥ 0 (MB, BE)
theorem envelope_of_upper (μ : Measure X) (s : Stat) (hs : 0 ≤ xi s) (F f g : X → ℝ)
    (hFm : Measurable F) (hFpos : ∀ᵐ x ∂μ, 0 < F x)
    (hfF : ∀ᵐ x ∂μ, 0 ≤ f x ∧ f x ≤ F x) (hgF : ∀ᵐ x ∂μ, 0 ≤ g x ∧ g x ≤ F x) :
    WEnvelope μ s (fun x => F x * (1 + xi s * F x)) f g

-- D4a': FD has the universal envelope W ≡ 1/4 on the admissible closure
theorem envelope_FD (μ : Measure X) (f g : X → ℝ)
    (hf : ∀ᵐ x ∂μ, f x ∈ cdom .FD) (hg : ∀ᵐ x ∂μ, g x ∈ cdom .FD) :
    WEnvelope μ .FD (fun _ => 1 / 4) f g

-- D4c: Planck instance of (A5) on dν = C E² dE dΩ; b > 0 is an input
theorem planck_envelope (C b : ℝ) (hb : 0 < b) (f g : ℝ × Sphere2 → ℝ)
    (hfF : ∀ᵐ y ∂nu C, 0 ≤ f y ∧ f y ≤ planckF b y)
    (hgF : ∀ᵐ y ∂nu C, 0 ≤ g y ∧ g y ≤ planckF b y) :
    WEnvelope (nu C) .BE (fun y => planckF b y * (1 + planckF b y)) f g

-- D4b (negative control, contract exclusion "No epsilon from fittedentropy alone", S:104):
-- with the reference g ≡ 1 FIXED (so its entropy is fixed) and the retained moment φ = 1_{true}
-- matched EXACTLY, no ε bounds the divergence: for every ε an admissible f violates Dext ≤ ε.
theorem eps_not_from_moments (ε : ℝ) :
    ∃ f : Bool → ℝ, Measurable f ∧ (∀ x, f x ∈ cdom .MB) ∧
      (∫ x, (if x then (1:ℝ) else 0) * (f x - 1)
          ∂(Measure.dirac true + Measure.dirac false)) = 0 ∧
      ¬ Dext (Measure.dirac true + Measure.dirac false) (hS .MB) (hS' .MB) f (fun _ => 1)
          ≤ ENNReal.ofReal ε

-- D4d (non-vacuity + necessity of the support term): every (BH) hypothesis holds (MB, ε = 1),
-- Δm ≠ 0 lies in the declared box S, the D2b bound is attained with equality, and the bound
-- WITHOUT the support term is false.
theorem support_term_necessary :
    ∃ (f g W : Unit → ℝ) (φ : Fin 1 → Unit → ℝ)
      (hφ : ∀ a, MemLp (φ a) 2 (wmeas (Measure.dirac ()) W))
      (k : Unit → ℝ) (hk : MemLp k 2 (wmeas (Measure.dirac ()) W))
      (S : Set (Fin 1 → ℝ)) (c : Fin 1 → ℝ),
      Measurable f ∧ Measurable g ∧
      (∀ᵐ x ∂(Measure.dirac ()), f x ∈ cdom .MB) ∧ (∀ᵐ x ∂(Measure.dirac ()), g x ∈ dom .MB) ∧
      WEnvelope (Measure.dirac ()) .MB W f g ∧
      Dext (Measure.dirac ()) (hS .MB) (hS' .MB) f g ≤ ENNReal.ofReal 1 ∧
      dm (Measure.dirac ()) φ f g ∈ S ∧ dm (Measure.dirac ()) φ f g ≠ 0 ∧
      BddAbove ((fun d => |c ⬝ᵥ d|) '' S) ∧
      |∫ x, k x * (f x - g x) ∂(Measure.dirac ())| =
        Real.sqrt (2 * 1) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + suppAbs S c ∧
      ¬ |∫ x, k x * (f x - g x) ∂(Measure.dirac ())| ≤
        Real.sqrt (2 * 1) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖
```

## D5 — coverage (probabilistic layer, kept separate from the deterministic D2)

```lean
-- D5a: generic union bound over three declared failure events; no independence, no measurability
theorem coverage_union {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω) (good : Ω → Prop)
    (E₁ E₂ E₃ : Set Ω) (himp : ∀ ω, ω ∈ E₁ → ω ∈ E₂ → ω ∈ E₃ → good ω)
    {α₁ α₂ α₃ : ℝ≥0∞} (h₁ : P E₁ᶜ ≤ α₁) (h₂ : P E₂ᶜ ≤ α₂) (h₃ : P E₃ᶜ ≤ α₃) :
    P {ω | ¬ good ω} ≤ α₁ + α₂ + α₃

theorem coverage_union_prob {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω)
    [IsProbabilityMeasure P] (good : Ω → Prop)
    (E₁ E₂ E₃ : Set Ω) (himp : ∀ ω, ω ∈ E₁ → ω ∈ E₂ → ω ∈ E₃ → good ω)
    {α₁ α₂ α₃ : ℝ≥0∞} (h₁ : P E₁ᶜ ≤ α₁) (h₂ : P E₂ᶜ ≤ α₂) (h₃ : P E₃ᶜ ≤ α₃) :
    1 - (α₁ + α₂ + α₃) ≤ P {ω | good ω}

-- D5b: (A6) with a data-dependent reference g ω, an entropy UPPER CONFIDENCE BOUND ε̂ ω (never exact),
-- a data-dependent moment set S ω; three declared failure bounds; true state f fixed.
theorem uncertain_bound_coverage {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω)
    (μ : Measure X) (s : Stat) (f W : X → ℝ) (hf : Measurable f)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s)
    (g : Ω → X → ℝ) (hg : ∀ ω, Measurable (g ω)) (hgd : ∀ ω, ∀ᵐ x ∂μ, g ω x ∈ dom s)
    (εhat : Ω → ℝ) (hε0 : ∀ ω, 0 ≤ εhat ω)
    {m : ℕ} (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (S : Ω → Set (Fin m → ℝ)) (σ : Ω → (Fin m → ℝ) → ℝ)
    (hσ : ∀ ω c, ∀ d ∈ S ω, |c ⬝ᵥ d| ≤ σ ω c)
    {αW αε αm : ℝ≥0∞}
    (hcovW : P {ω | ¬ WEnvelope μ s W f (g ω)} ≤ αW)
    (hcovε : P {ω | ¬ Dext μ (hS s) (hS' s) f (g ω) ≤ ENNReal.ofReal (εhat ω)} ≤ αε)
    (hcovm : P {ω | dm μ φ f (g ω) ∉ S ω} ≤ αm) :
    P {ω | ¬ ∀ c : Fin m → ℝ, |∫ x, k x * (f x - g ω x) ∂μ| ≤
        Real.sqrt (2 * εhat ω) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ ω c}
      ≤ αW + αε + αm

theorem uncertain_bound_coverage_prob {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω)
    [IsProbabilityMeasure P] -- remaining hypotheses exactly as uncertain_bound_coverage
    ... :
    1 - (αW + αε + αm) ≤ P {ω | ∀ c : Fin m → ℝ, |∫ x, k x * (f x - g ω x) ∂μ| ≤
        Real.sqrt (2 * εhat ω) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ ω c}

end General
end G11D
```

## Discipline

* Δm is never set to zero except in D2f (S = {0}) and D3d (the reviewed G11-A source hypothesis);
  Δm enters only through the declared set S and an upper bound of its support function.
* ε, ε̂, ε', W, b, S, σ, α_* are inputs. No theorem derives ε from moments or from a fitted reference
  (D4b shows it is impossible); ε̂ is used only on its declared coverage event.
* Deterministic kinetic bounds (D1-D3) carry no probability; D5 adds coverage only through the union bound
  of declared failure events (no independence, no product of coverages, no measurability assumption).
* Domains/branches inherited from G11-B/C: f ∈ cdom (closed), g ∈ dom (open), W > 0 a.e., D ≤ ε < ∞.
* Allowed axioms: propext, Classical.choice, Quot.sound only.
