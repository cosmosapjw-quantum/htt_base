# G12-E frozen targets (written before any proof compile)

Card: G12-E "Compact moment-null perturbation과 entropy 대비 미분 반례" (TEFF-H1).
Original scope: *static entropy does not bound spacetime derivatives* — formal counterexample.
Source statement: `supplements/TEFF_POSITIVE_BRIDGE.md:145-151`.

Toolchain: Lean 4.31.0, Mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f.
Imports (reviewed, unchanged): `G11AGuarded` (→ `G11AIntegralBregman` → `BregmanThreePoint`),
`G12DCardClosure` (→ `G12DUVIntegrabilityEnvelope` → `G12DInterface`, `PlanckIR`),
`OscillatoryDerivative`.
New modules: `lean/G12EMomentNull.lean` (namespace `G12E`), `lean/G12ECounterexample.lean`.

Notation: `∞` below means `((⊤ : ℕ∞) : WithTop ℕ∞)` (C^∞, **not** analytic `ω`).
`Stat, dom, cdom, hS, hS', hess, Dext, Dfin, nu, Sphere2` are from `G11A`.

## Definitions (frozen)

```lean
def cellWidth (E1 E2 : ℝ) (m : ℕ) : ℝ := (E2 - E1) / (m + 1)
def cellCenter (E1 E2 : ℝ) (m : ℕ) (i : Fin (m + 1)) : ℝ :=
  E1 + ((i : ℝ) + 1 / 2) * cellWidth E1 E2 m
def cellBump {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (i : Fin (m + 1)) :
  ContDiffBump (cellCenter E1 E2 m i)          -- rIn = width/4, rOut = width/2
def psi {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (i : Fin (m + 1)) : ℝ → ℝ := ⇑(cellBump h m i)
def qOf {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (c : Fin (m + 1) → ℝ) : ℝ → ℝ :=
  fun E => ∑ i, c i * psi h m i E
def patchE {Ω : Type*} (E1 E2 : ℝ) : Set (ℝ × Ω) := Prod.fst ⁻¹' Icc E1 E2
def family {Ω : Type*} (g q : ℝ → ℝ) (a : ℝ) (n : ℕ) (x : ℝ) : ℝ × Ω → ℝ :=
  fun z => g z.1 + a * Real.sin ((n : ℝ) * x) * q z.1
def Admissible {Ω : Type*} (s : Stat) (F : ℝ → ℝ) (f : ℝ × Ω → ℝ) : Prop :=
  ∀ z : ℝ × Ω, 0 < z.1 → f z ∈ cdom s ∧ f z ≤ F z.1
def numberEnergyScores : Fin 2 → ℝ × Sphere2 → ℝ := ![fun _ => 1, fun z => z.1]
```

q depends only on the momentum (energy) variable, never on x: the q′ term of the general
product rule (`CAS12C04.hasDerivAt_oscillatory_perturbation`) is absent by construction (pitfall 1).

## Targets

**T1 `psi_props`** (bumps; card step 1)
```lean
theorem psi_props {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (i : Fin (m + 1)) :
    ContDiff ℝ ∞ (psi h m i) ∧ HasCompactSupport (psi h m i) ∧
    Function.support (psi h m i) ⊆ Ioo E1 E2 ∧
    (∀ E, 0 ≤ psi h m i E ∧ psi h m i E ≤ 1) ∧
    (∀ j, psi h m i (cellCenter E1 E2 m j) = if i = j then 1 else 0)
```

**T2 `q_props`** (smooth compact q from bumps; pitfall 2)
```lean
theorem q_props {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (c : Fin (m + 1) → ℝ) :
    ContDiff ℝ ∞ (qOf h m c) ∧ HasCompactSupport (qOf h m c) ∧
    tsupport (qOf h m c) ⊆ Icc E1 E2 ∧ (∀ E, |qOf h m c E| ≤ ∑ i, |c i|) ∧
    (∀ i, qOf h m c (cellCenter E1 E2 m i) = c i)
```

**T3 `moment_null_exists`** (kernel vector ⇒ q ≠ 0 with all retained moments 0; card step 2)
```lean
theorem moment_null_exists {Ω : Type*} [MeasurableSpace Ω] (μ : Measure (ℝ × Ω))
    {m : ℕ} (φ : Fin m → ℝ × Ω → ℝ) {E1 E2 : ℝ} (h : E1 < E2)
    (hφ : ∀ j, IntegrableOn (φ j) (patchE E1 E2) μ) :
    ∃ c : Fin (m + 1) → ℝ, c ≠ 0 ∧ (∃ E0 ∈ Ioo E1 E2, qOf h m c E0 ≠ 0) ∧
      ∀ j, Integrable (fun z => φ j z * qOf h m c z.1) μ ∧
        ∫ z, φ j z * qOf h m c z.1 ∂μ = 0
```

**T3b `momentum_lift`** (q as a C_c^∞ function on momentum space ℝ³, positive patch)
```lean
theorem momentum_lift (q : ℝ → ℝ) {E1 E2 : ℝ} (hq : ContDiff ℝ ∞ q) (hE1 : 0 < E1)
    (hz : ∀ E ∉ Icc E1 E2, q E = 0) :
    ContDiff ℝ ∞ (fun p : EuclideanSpace ℝ (Fin 3) => q ‖p‖) ∧
    HasCompactSupport (fun p : EuclideanSpace ℝ (Fin 3) => q ‖p‖) ∧
    ∀ p : EuclideanSpace ℝ (Fin 3), q ‖p‖ ≠ 0 → E1 ≤ ‖p‖ ∧ ‖p‖ ≤ E2
```

**T4 `moment_null_counterexample`** (general measure; card steps 2–5 on ONE family)
```lean
theorem moment_null_counterexample {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure (ℝ × Ω)) (s : Stat) {m : ℕ} (φ : Fin m → ℝ × Ω → ℝ)
    (g F : ℝ → ℝ) {E1 E2 : ℝ} (hE1 : 0 < E1) (hE12 : E1 < E2)
    (hμ0 : μ {z | z.1 ≤ 0} = 0) (hμP : μ (patchE E1 E2) ≠ ⊤)
    (hφ : ∀ j, IntegrableOn (φ j) (patchE E1 E2) μ)
    (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2)) (hFc : ContinuousOn F (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hgF : ∀ E, 0 < E → g E ≤ F E)
    (hFcdom : ∀ E, 0 < E → F E ∈ cdom s) (hslack : ∀ E ∈ Icc E1 E2, g E < F E) :
    ∃ q : ℝ → ℝ, ∃ a B : ℝ,
      ContDiff ℝ ∞ q ∧ HasCompactSupport q ∧ tsupport q ⊆ Icc E1 E2 ∧
      (∃ E0 ∈ Ioo E1 E2, q E0 ≠ 0) ∧
      (∀ j, Integrable (fun z => φ j z * q z.1) μ ∧ ∫ z, φ j z * q z.1 ∂μ = 0) ∧
      0 < a ∧ 0 ≤ B ∧
      ∀ (n : ℕ) (x : ℝ),
        Admissible s F (family g q a n x) ∧
        (∀ z : ℝ × Ω, 0 < z.1 → family g q a n x z ∈ dom s) ∧
        (∀ j, ∫ z, φ j z * (family g q a n x z - g z.1) ∂μ = 0) ∧
        Dext μ (hS s) (hS' s) (family g q a n x) (fun z => g z.1) ≤ ENNReal.ofReal B ∧
        Dfin μ (hS s) (hS' s) (family g q a n x) (fun z => g z.1) ≤ B ∧
        ∀ z, HasDerivAt (fun t => family g q a n t z) (a * n * q z.1) 0
```
`a` and `B` are chosen before `n, x` (uniformity in n is in the quantifier order).
The moment condition is the source's (A1) δ-form `∫ φ_a (f − g) dν = 0`.

**T4b `moments_equal`** (absolute moments fixed, when φ·g is integrable)
```lean
theorem moments_equal {Ω : Type*} [MeasurableSpace Ω] (μ : Measure (ℝ × Ω))
    (φ : ℝ × Ω → ℝ) (g q : ℝ → ℝ) (a : ℝ)
    (hφg : Integrable (fun z => φ z * g z.1) μ) (hφq : Integrable (fun z => φ z * q z.1) μ)
    (h0 : ∫ z, φ z * q z.1 ∂μ = 0) (n : ℕ) (x : ℝ) :
    ∫ z, φ z * family g q a n x z ∂μ = ∫ z, φ z * g z.1 ∂μ
```

**T4c `observable_derivative`** (differentiating the integral; card C04 residual)
```lean
theorem observable_derivative {Ω : Type*} [MeasurableSpace Ω] (μ : Measure (ℝ × Ω))
    (K : ℝ × Ω → ℝ) (g q : ℝ → ℝ) (a : ℝ) (n : ℕ) (x : ℝ) :
    HasDerivAt (fun t => ∫ z, K z * (family g q a n t z - g z.1) ∂μ)
      (a * n * Real.cos (n * x) * ∫ z, K z * q z.1 ∂μ) x
```

**T5 `nu_facts`** (the card measure C E² dE dΩ)
```lean
theorem nu_facts (C : ℝ) :
    nu C {z | z.1 ≤ 0} = 0 ∧
    ∀ E1 E2 : ℝ, 0 < E1 → nu C (patchE E1 E2) ≠ ⊤
```

**T6 `radial_integral_pos`** (positivity of radial integrals under ν)
```lean
theorem radial_integral_pos (C : ℝ) (hC : 0 < C) (w : ℝ → ℝ) {E1 E2 Mw : ℝ}
    (hE1 : 0 < E1) (hwm : Measurable w) (hwb : ∀ E, |w E| ≤ Mw)
    (hw0 : ∀ E ∉ Icc E1 E2, w E = 0) (hwnn : ∀ E, 0 ≤ w E)
    {E0 r : ℝ} (hr : 0 < r) (hball : Metric.ball E0 r ⊆ Ioi 0)
    (hpos : ∀ E ∈ Metric.ball E0 r, 0 < w E) :
    Integrable (fun z : ℝ × Sphere2 => w z.1) (nu C) ∧ 0 < ∫ z, w z.1 ∂nu C
```

**T7 `derivative_norm_unbounded`** (L²(ν) and pointwise growth; card step 5)
```lean
theorem derivative_norm_unbounded (C : ℝ) (hC : 0 < C) (q : ℝ → ℝ) {E1 E2 : ℝ}
    (hq : Continuous q) (hE1 : 0 < E1) (hz : ∀ E ∉ Icc E1 E2, q E = 0)
    (hq0 : ∃ E0, q E0 ≠ 0) (a : ℝ) (ha : a ≠ 0) :
    Tendsto (fun n : ℕ => ∫ z, (a * n * q z.1) ^ 2 ∂nu C) atTop atTop ∧
    ∃ E0, Tendsto (fun n : ℕ => |a * n * q E0|) atTop atTop
```

**T8 `fisher_unbounded`** (horizontal Fisher budget J_X of `:151` diverges on the family)
```lean
theorem fisher_unbounded (C : ℝ) (hC : 0 < C) (s : Stat) (g q : ℝ → ℝ) {E1 E2 : ℝ}
    (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hq : Continuous q) (hE1 : 0 < E1)
    (hz : ∀ E ∉ Icc E1 E2, q E = 0) (hq0 : ∃ E0, q E0 ≠ 0) (a : ℝ) (ha : a ≠ 0) :
    Tendsto (fun n : ℕ => ∫ z, (a * n * q z.1) ^ 2 *
      hess s (family (Ω := Sphere2) g q a n 0 z) ∂nu C) atTop atTop
```

**T9 `teff_h1_entropy_ball_derivative_unbounded`** (final typed TEFF-H1 statement on dν = C E² dE dΩ)
```lean
theorem teff_h1_entropy_ball_derivative_unbounded (C : ℝ) (hC : 0 < C) (s : Stat)
    {m : ℕ} (φ : Fin m → ℝ × Sphere2 → ℝ) (g F : ℝ → ℝ) {E1 E2 : ℝ}
    (hE1 : 0 < E1) (hE12 : E1 < E2)
    (hφ : ∀ j, IntegrableOn (φ j) (patchE E1 E2) (nu C))
    (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2)) (hFc : ContinuousOn F (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hgF : ∀ E, 0 < E → g E ≤ F E)
    (hFcdom : ∀ E, 0 < E → F E ∈ cdom s) (hslack : ∀ E ∈ Icc E1 E2, g E < F E) :
    ∃ B : ℝ, 0 ≤ B ∧ ∀ M : ℝ, ∃ (f : ℝ → ℝ × Sphere2 → ℝ) (d : ℝ × Sphere2 → ℝ),
      (∀ x, Admissible s F (f x)) ∧
      (∀ x, Dext (nu C) (hS s) (hS' s) (f x) (fun z => g z.1) ≤ ENNReal.ofReal B) ∧
      (∀ x j, ∫ z, φ j z * (f x z - g z.1) ∂nu C = 0) ∧
      (∀ z, HasDerivAt (fun t => f t z) (d z) 0) ∧
      M < ∫ z, d z ^ 2 ∂nu C ∧
      M < ∫ z, d z ^ 2 * hess s (f 0 z) ∂nu C
```
Reading: there is one entropy level B such that, on the class of spacetime families that are
admissible under the common envelope at every x, keep all retained moments fixed, and stay
within static divergence B at every x, neither the L²(ν) norm nor the horizontal Fisher norm
of ∂_x f at x = 0 is bounded. Hence no bound of the derivative by the static entropy alone.

**T10 `teff_h1_BE_instance`** (non-vacuity: BE photon envelope F_b, number+energy scores)
```lean
theorem teff_h1_BE_instance (C b : ℝ) (hC : 0 < C) (hb : 0 < b) :
    ∃ B : ℝ, 0 ≤ B ∧ ∀ M : ℝ, ∃ (f : ℝ → ℝ × Sphere2 → ℝ) (d : ℝ × Sphere2 → ℝ),
      (∀ x, Admissible Stat.BE (fun E => G12D.occupation b 0 E) (f x)) ∧
      (∀ x, Dext (nu C) (hS .BE) (hS' .BE) (f x)
          (fun z => G12D.occupation (2 * b) 0 z.1) ≤ ENNReal.ofReal B) ∧
      (∀ x j, ∫ z, numberEnergyScores j z * (f x z - G12D.occupation (2 * b) 0 z.1) ∂nu C = 0) ∧
      (∀ z, HasDerivAt (fun t => f t z) (d z) 0) ∧
      M < ∫ z, d z ^ 2 ∂nu C ∧
      M < ∫ z, d z ^ 2 * hess .BE (f 0 z) ∂nu C
```
(patch `[1, 2]`; base state `g = 1/(e^{2bE}−1)` strictly inside the envelope `F_b = 1/(e^{bE}−1)`.)

**T11 `single_bump_number_moment_pos`** (negative control: one bump alone does NOT annihilate
the number moment, so the kernel combination of T3 is necessary)
```lean
theorem single_bump_number_moment_pos (C : ℝ) (hC : 0 < C) {E1 E2 : ℝ}
    (hE1 : 0 < E1) (h : E1 < E2) (m : ℕ) (i : Fin (m + 1)) :
    0 < ∫ z, numberEnergyScores 0 z * psi h m i z.1 ∂nu C
```

## Explicit non-claims

* The base state g is energy-only (isotropic) and the envelope F is energy-only; anisotropic
  base states are not covered.
* `nu C` is the typed carrier measure; its identification with C·d³p on ℝ³ is not claimed.
* Angular Fisher budgets (the second half of the TEFF-H1 ledger sentence) are not treated.
* The positive replacement bound (weighted Cauchy–Schwarz with J_X) is not proved here.
* Scientific admission: HOLD.
