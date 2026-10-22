# G13-D frozen targets (written before any proof compile)

Module: `lean/G13DBandpassCubic.lean`, namespace `G13D`.
Imports (unchanged): `Mathlib`, `MeasureExtremizerBridge` (reviewed G13-A),
`PowerJet` (PR #501, CAS-13-C01). Toolchain Lean 4.31.0, Mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. Prelude:

```lean
open MeasureTheory Set
open CAS13MeasureComposition (hermite moment twoDirac)
```

`hermite c0 c3 c4 x = c0 + c3*x^3 + c4*x^4` and `moment μ p = ∫ x, x^p ∂μ` are the G13-A
definitions (real Bochner integrals).

## Definitions (card / BRIDGE:178-188, 210)

```lean
def c3 (d1 d2 : ℝ) : ℝ := d1 - d2 / 3
def c4 (d1 d2 : ℝ) : ℝ := d2 / 4 - d1 / 2
def c0 (v d1 d2 : ℝ) : ℝ := v - d1 / 2 + d2 / 12
def estimator (v d1 d2 m3 m4 : ℝ) : ℝ := c0 v d1 d2 + c3 d1 d2 * m3 + c4 d1 d2 * m4   -- (B2)
def cE0 (v d1 : ℝ) : ℝ := v - d1 / 4
def cE4 (d1 : ℝ) : ℝ := d1 / 4
def energyEstimator (v d1 m4 : ℝ) : ℝ := cE0 v d1 + cE4 d1 * m4
-- kernel layer
def bandIntegral (K : ℝ → ℝ) (E1 E2 : ℝ) (G : ℝ × ℝ → ℝ) (y : ℝ) : ℝ :=
  ∫ E in Icc E1 E2, K E * G (y, E)
def dY (G : ℝ × ℝ → ℝ) : ℝ × ℝ → ℝ := fun p => fderiv ℝ G p (1, 0)      -- ∂/∂y
def thermalFactor (θ η0 ξ : ℝ) (p : ℝ × ℝ) : ℝ :=
  p.2 ^ 2 / (Real.exp (p.2 / (θ * p.1) - η0) - ξ)                          -- E²/(e^{E/(θy)-η0}-ξ)
def regDomain (θ η0 ξ : ℝ) : Set (ℝ × ℝ) :=
  {p | 0 < p.1 ∧ 0 < p.2 ∧ ξ < Real.exp (p.2 / (θ * p.1) - η0)}
def bandResponse  (C θ η0 ξ : ℝ) (K : ℝ → ℝ) (E1 E2 y : ℝ) : ℝ :=
  C * bandIntegral K E1 E2 (thermalFactor θ η0 ξ) y
def bandResponse1 ... := C * bandIntegral K E1 E2 (dY (thermalFactor θ η0 ξ)) y
def bandResponse2 ... := C * bandIntegral K E1 E2 (dY (dY (thermalFactor θ η0 ξ))) y
def bandResponse3 ... := C * bandIntegral K E1 E2 (dY (dY (dY (thermalFactor θ η0 ξ)))) y
```

`θ = k_B T_*`. `bandResponse1..3` are the explicitly interchanged (differentiated-under-the-
integral) derivatives; they are definitions, not hypotheses, and the theorems prove they are
the derivatives.

## Targets

T0 `hermite_jets` (value/first/second matching at 1, finite algebra):
```lean
theorem hermite_jets (v d1 d2 : ℝ) :
    hermite (c0 v d1 d2) (c3 d1 d2) (c4 d1 d2) 1 = v ∧
    3 * c3 d1 d2 * 1 ^ 2 + 4 * c4 d1 d2 * 1 ^ 3 = d1 ∧
    6 * c3 d1 d2 * 1 + 12 * c4 d1 d2 * 1 ^ 2 = d2
```

T1 `taylor_step` (one-step fencing used three times; replaces the "integral Taylor" remainder
by the same bound):
```lean
theorem taylor_step {f f' : ℝ → ℝ} {s c : ℝ} {n : ℕ} (hs : 0 ≤ s)
    (hf : ∀ z ∈ Icc (1 - s) (1 + s), HasDerivAt f (f' z) z) (h1 : f 1 = 0)
    (hb : ∀ z ∈ Icc (1 - s) (1 + s), |f' z| ≤ c * |z - 1| ^ n) :
    ∀ y ∈ Icc (1 - s) (1 + s), |f y| ≤ c / ((n : ℝ) + 1) * |y - 1| ^ (n + 1)
```

T2 `cubic_pointwise` (h = ψ − q, three jets vanish, |h| ≤ |y−1|³ sup|h'''|/6):
```lean
theorem cubic_pointwise {ψ ψ1 ψ2 ψ3 : ℝ → ℝ} {s0 M : ℝ} (hs0 : 0 ≤ s0)
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z ∧ HasDerivAt ψ2 (ψ3 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0),
      |ψ3 z - 6 * c3 (ψ1 1) (ψ2 1) - 24 * c4 (ψ1 1) (ψ2 1) * z| ≤ M) :
    ∀ y ∈ Icc (1 - s0) (1 + s0),
      |ψ y - hermite (c0 (ψ 1) (ψ1 1) (ψ2 1)) (c3 (ψ1 1) (ψ2 1)) (c4 (ψ1 1) (ψ2 1)) y|
        ≤ M / 6 * |y - 1| ^ 3
```
`M` is any bound of `|h'''|` on `[1−s₀,1+s₀]`; taking `M` = the supremum gives (B3) exactly.

T3 `cubic_mixture` (B3; integration against the probability mixture):
```lean
theorem cubic_mixture {ψ ψ1 ψ2 ψ3 : ℝ → ℝ} {s s0 M : ℝ} (π : Measure ℝ) [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hd : <as T2>) (hM : <as T2>) :
    Integrable ψ π ∧
    |(∫ y, ψ y ∂π) - estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4)| ≤ s ^ 3 / 6 * M
```

T3b `cubic_mixture_uncertain` (moment uncertainties):
same hypotheses plus `{m3 m4 d3 d4 : ℝ} (h3 : |moment π 3 - m3| ≤ d3) (h4 : |moment π 4 - m4| ≤ d4)`,
conclusion
```lean
|(∫ y, ψ y ∂π) - estimator (ψ 1) (ψ1 1) (ψ2 1) m3 m4|
  ≤ s ^ 3 / 6 * M + |c3 (ψ1 1) (ψ2 1)| * d3 + |c4 (ψ1 1) (ψ2 1)| * d4
```

T3c `retained_span` (MOM-RETAINED exact span):
```lean
theorem retained_span (a0 a3 a4 : ℝ) (π : Measure ℝ) [IsProbabilityMeasure π]
    (h3 : Integrable (fun x : ℝ => x ^ 3) π) (h4 : Integrable (fun x : ℝ => x ^ 4) π) :
    c0 (hermite a0 a3 a4 1) (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a0 ∧
    c3 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a3 ∧
    c4 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a4 ∧
    (∀ z : ℝ, 6 * a3 + 24 * a4 * z - 6 * c3 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4)
        - 24 * c4 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) * z = 0) ∧
    (∫ y, hermite a0 a3 a4 y ∂π) =
      estimator (hermite a0 a3 a4 1) (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) (moment π 3) (moment π 4)
```
(`3a3+4a4`, `6a3+12a4` are the first/second derivatives of `hermite a0 a3 a4` at 1; T0-style
`HasDerivAt` lemmas for `hermite` are proved alongside.)

T4 `energy_pointwise` / `energy_mixture` (B4, same prior and target):
```lean
theorem energy_pointwise {ψ ψ1 ψ2 : ℝ → ℝ} {s0 M2 : ℝ} (hs0 : 0 ≤ s0)
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0), HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |ψ2 z - 3 * ψ1 1 * z ^ 2| ≤ M2) :
    ∀ y ∈ Icc (1 - s0) (1 + s0), |ψ y - (cE0 (ψ 1) (ψ1 1) + cE4 (ψ1 1) * y ^ 4)| ≤ M2 / 2 * |y - 1| ^ 2
theorem energy_mixture {ψ ψ1 ψ2 : ℝ → ℝ} {s s0 M2 : ℝ} (π : Measure ℝ) [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s)) (hd) (hM) :
    Integrable ψ π ∧ |(∫ y, ψ y ∂π) - energyEstimator (ψ 1) (ψ1 1) (moment π 4)| ≤ s ^ 2 / 2 * M2
```

T4b `same_prior_gap` (non-vacuity witness / negative control for MOM-PRIOR: same prior, same
target `ψ=y³`, two-point prior `½δ_{1−s}+½δ_{1+s}`; number–energy estimator exact, energy-only
error exactly `−(3/2 s² + 3/4 s⁴) ≠ 0`):
```lean
theorem same_prior_gap {s : ℝ} (hs : 0 < s) (hs1 : s < 1) :
    IsProbabilityMeasure (twoDirac (1/2) (1 - s) (1 + s)) ∧
    (∀ᵐ y ∂twoDirac (1/2) (1 - s) (1 + s), y ∈ Icc (1 - s) (1 + s)) ∧
    (∫ y, y ^ 3 ∂twoDirac (1/2) (1 - s) (1 + s)) =
      estimator 1 3 6 (moment (twoDirac (1/2) (1 - s) (1 + s)) 3)
        (moment (twoDirac (1/2) (1 - s) (1 + s)) 4) ∧
    (∫ y, y ^ 3 ∂twoDirac (1/2) (1 - s) (1 + s)) -
      energyEstimator 1 3 (moment (twoDirac (1/2) (1 - s) (1 + s)) 4) = -(3/2 * s ^ 2 + 3/4 * s ^ 4) ∧
    -(3/2 * s ^ 2 + 3/4 * s ^ 4) ≠ 0
```

T5 `relative_bound` / `relative_cubic` (ψ_min > 0 on the support):
```lean
theorem relative_bound {ψ : ℝ → ℝ} {ψmin Ohat B : ℝ} (π : Measure ℝ) [IsProbabilityMeasure π]
    (hint : Integrable ψ π) (hmin : ∀ᵐ y ∂π, ψmin ≤ ψ y) (hpos : 0 < ψmin)
    (herr : |(∫ y, ψ y ∂π) - Ohat| ≤ B) :
    ψmin ≤ ∫ y, ψ y ∂π ∧ |(∫ y, ψ y ∂π) - Ohat| / |∫ y, ψ y ∂π| ≤ B / ψmin
theorem relative_cubic  -- T3 hypotheses + (hmin : ∀ y ∈ Icc (1 - s) (1 + s), ψmin ≤ ψ y) (hpos : 0 < ψmin)
    : |(∫ ψ) - estimator ..| / |∫ ψ| ≤ s ^ 3 / 6 * M / ψmin
```

T6 `beam_abs` / `beam_uniform` (signed beam: absolute-weight integration, no division):
```lean
theorem beam_abs {α : Type*} [MeasurableSpace α] (σ : Measure α) (b O Oh ε : α → ℝ)
    (hO : Integrable (fun ω => b ω * O ω) σ) (hOh : Integrable (fun ω => b ω * Oh ω) σ)
    (hε : Integrable (fun ω => |b ω| * ε ω) σ) (hray : ∀ᵐ ω ∂σ, |O ω - Oh ω| ≤ ε ω) :
    |(∫ ω, b ω * O ω ∂σ) - ∫ ω, b ω * Oh ω ∂σ| ≤ ∫ ω, |b ω| * ε ω ∂σ
theorem beam_uniform {α : Type*} [MeasurableSpace α] (σ : Measure α) (b O Oh : α → ℝ) (ε : ℝ)
    (hO) (hOh) (hb : Integrable b σ) (hray : ∀ᵐ ω ∂σ, |O ω - Oh ω| ≤ ε) :
    |(∫ ω, b ω * O ω ∂σ) - ∫ ω, b ω * Oh ω ∂σ| ≤ ε * ∫ ω, |b ω| ∂σ
```

T6b `signed_mode_no_relative` (negative control: relative division is invalid for signed modes):
with `σ = twoDirac (1/2) (-1) 1`, signed weight `b ω = ω`, true raywise value `1`, estimate `1+δω`,
```lean
theorem signed_mode_no_relative {δ : ℝ} (hδ : δ ≠ 0) :
    (∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1) = 0 ∧
    (∫ ω, ω * (1 + δ * ω) ∂twoDirac (1/2) (-1) 1) = δ ∧
    (∀ᵐ ω ∂twoDirac (1/2) (-1) 1, |1 - (1 + δ * ω)| ≤ |δ|) ∧
    ¬ ∃ c : ℝ, |(∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1) - ∫ ω, ω * (1 + δ * ω) ∂twoDirac (1/2) (-1) 1|
        ≤ c * |∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1|
```

T7 `radial_data_do_not_fix_dipole` (negative control: extra radial data do not identify an
unmeasured angular mode; swapping two rays' mixtures leaves the sky-summed mixture, hence every
radial datum, unchanged, while the dipole flips):
```lean
theorem radial_data_do_not_fix_dipole (ψ : ℝ → ℝ) {yN yS : ℝ} (hne : ψ yN ≠ ψ yS) :
    (Measure.dirac yN + Measure.dirac yS : Measure ℝ) = Measure.dirac yS + Measure.dirac yN ∧
    (∀ g : ℝ → ℝ, (∫ y, g y ∂(Measure.dirac yN + Measure.dirac yS)) =
        ∫ y, g y ∂(Measure.dirac yS + Measure.dirac yN)) ∧
    (∫ y, ψ y ∂Measure.dirac yN) - (∫ y, ψ y ∂Measure.dirac yS) ≠
      (∫ y, ψ y ∂Measure.dirac yS) - (∫ y, ψ y ∂Measure.dirac yN)
```

T8 kernel layer (derivative–integral interchange three times, ψ ∈ C³):
```lean
theorem bandIntegral_hasDerivAt {K : ℝ → ℝ} {E1 E2 A B y : ℝ} {G : ℝ × ℝ → ℝ} {Ω : Set (ℝ × ℝ)}
    (hK : IntegrableOn K (Icc E1 E2)) (hΩ : IsOpen Ω) (hG : ContDiffOn ℝ 1 G Ω)
    (hsub : Icc A B ×ˢ Icc E1 E2 ⊆ Ω) (hy : y ∈ Ioo A B) :
    HasDerivAt (bandIntegral K E1 E2 G) (bandIntegral K E1 E2 (dY G) y) y
theorem bandIntegral_C3 {K : ℝ → ℝ} {E1 E2 A B : ℝ} {G : ℝ × ℝ → ℝ} {Ω : Set (ℝ × ℝ)}
    (hK : IntegrableOn K (Icc E1 E2)) (hΩ : IsOpen Ω) (hG : ContDiffOn ℝ 4 G Ω)
    (hsub : Icc A B ×ˢ Icc E1 E2 ⊆ Ω) :
    (∀ y ∈ Ioo A B,
      HasDerivAt (bandIntegral K E1 E2 G) (bandIntegral K E1 E2 (dY G) y) y ∧
      HasDerivAt (bandIntegral K E1 E2 (dY G)) (bandIntegral K E1 E2 (dY (dY G)) y) y ∧
      HasDerivAt (bandIntegral K E1 E2 (dY (dY G)))
        (bandIntegral K E1 E2 (dY (dY (dY G))) y) y) ∧
    ContinuousOn (bandIntegral K E1 E2 (dY (dY (dY G)))) (Ioo A B) ∧
    ContDiffOn ℝ 3 (bandIntegral K E1 E2 G) (Ioo A B)
theorem regDomain_isOpen {θ η0 ξ : ℝ} (hθ : 0 < θ) : IsOpen (regDomain θ η0 ξ)
theorem thermalFactor_contDiffOn {θ η0 ξ : ℝ} (hθ : 0 < θ) :
    ContDiffOn ℝ 4 (thermalFactor θ η0 ξ) (regDomain θ η0 ξ)
theorem bandResponse_B1_form {C θ η0 ξ E1 E2 : ℝ} {K : ℝ → ℝ} (hE1 : 0 < E1)
    (hK0 : ∀ E, E ∉ Icc E1 E2 → K E = 0) (y : ℝ) :
    C * (∫ E in Ioi (0:ℝ), E ^ 2 * K E / (Real.exp (E / (θ * y) - η0) - ξ)) =
      bandResponse C θ η0 ξ K E1 E2 y
theorem bandResponse_C3 {C θ η0 ξ E1 E2 A B : ℝ} {K : ℝ → ℝ} (hθ : 0 < θ) (hA : 0 < A)
    (hE1 : 0 < E1) (hK : IntegrableOn K (Icc E1 E2))
    (hreg : ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0)) :
    (∀ y ∈ Ioo A B,
      HasDerivAt (bandResponse C θ η0 ξ K E1 E2) (bandResponse1 C θ η0 ξ K E1 E2 y) y ∧
      HasDerivAt (bandResponse1 C θ η0 ξ K E1 E2) (bandResponse2 C θ η0 ξ K E1 E2 y) y ∧
      HasDerivAt (bandResponse2 C θ η0 ξ K E1 E2) (bandResponse3 C θ η0 ξ K E1 E2 y) y) ∧
    ContinuousOn (bandResponse3 C θ η0 ξ K E1 E2) (Ioo A B) ∧
    ContDiffOn ℝ 3 (bandResponse C θ η0 ξ K E1 E2) (Ioo A B)
theorem hreg_of_nonpos_fugacity {θ η0 ξ E1 E2 A B : ℝ} (hθ : 0 < θ) (hA : 0 < A) (hE1 : 0 < E1)
    (hξ : ξ ≤ 1) (hη : η0 ≤ 0) :
    ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0)
theorem hreg_of_xi_nonpos {θ η0 ξ E1 E2 A B : ℝ} (hξ : ξ ≤ 0) :
    ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0)
```
Admissible kernel class (explicit): `K` integrable on a compact positive-energy interval
`[E₁,E₂]`, `E₁>0`, vanishing outside it for the (B1) `∫₀^∞` form; occupation regular on the
compact domain. A bounded measurable bandpass on `[E₁,E₂]` is a special case.

T9 connected conditional ⇄ kernel theorems:
```lean
-- (a) conditional theorem assuming ψ ∈ C³ on an open interval containing [1−s₀,1+s₀]
theorem cubic_mixture_of_contDiffOn {ψ : ℝ → ℝ} {A B s s0 M : ℝ} (π : Measure ℝ)
    [IsProbabilityMeasure π] (hψ : ContDiffOn ℝ 3 ψ (Ioo A B)) (hA : A < 1 - s0) (hB : 1 + s0 < B)
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |iteratedDeriv 3 ψ z
        - 6 * c3 (deriv ψ 1) (iteratedDeriv 2 ψ 1) - 24 * c4 (deriv ψ 1) (iteratedDeriv 2 ψ 1) * z| ≤ M) :
    Integrable ψ π ∧
    |(∫ y, ψ y ∂π) - estimator (ψ 1) (deriv ψ 1) (iteratedDeriv 2 ψ 1) (moment π 3) (moment π 4)|
      ≤ s ^ 3 / 6 * M
-- (b) actual-kernel verification for the stated admissible class, connected to (a)'s certificate
theorem bandpass_cubic_certificate {C θ η0 ξ E1 E2 A B s s0 M : ℝ} {K : ℝ → ℝ}
    (π : Measure ℝ) [IsProbabilityMeasure π]
    (hθ : 0 < θ) (hA : 0 < A) (hA' : A < 1 - s0) (hB : 1 + s0 < B) (hE1 : 0 < E1)
    (hK : IntegrableOn K (Icc E1 E2))
    (hreg : ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0))
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |bandResponse3 C θ η0 ξ K E1 E2 z
        - 6 * c3 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1)
        - 24 * c4 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1) * z| ≤ M) :
    ContDiffOn ℝ 3 (bandResponse C θ η0 ξ K E1 E2) (Ioo A B) ∧
    Integrable (bandResponse C θ η0 ξ K E1 E2) π ∧
    |(∫ y, bandResponse C θ η0 ξ K E1 E2 y ∂π) - estimator (bandResponse C θ η0 ξ K E1 E2 1)
        (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1)
        (moment π 3) (moment π 4)| ≤ s ^ 3 / 6 * M
theorem bandpass_M_exists  -- same kernel hypotheses: ∃ M, (hM-shaped bound holds)   (finite sup)
theorem bandpass_cubic_BE {C θ η0 E1 E2 s s0 : ℝ} {K : ℝ → ℝ} (π : Measure ℝ) [IsProbabilityMeasure π]
    (hθ : 0 < θ) (hE1 : 0 < E1) (hK : IntegrableOn K (Icc E1 E2)) (hη : η0 ≤ 0)
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hs0 : s0 < 1) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s)) :
    -- BE photons, ξ = 1 (B1)
    (∃ M, ∀ z ∈ Icc (1 - s0) (1 + s0), |bandResponse3 C θ η0 1 K E1 E2 z - 6 * c3 (..1) (..1)
        - 24 * c4 (..1) (..1) * z| ≤ M) ∧
    (∀ M, (∀ z ∈ Icc (1 - s0) (1 + s0), |… | ≤ M) →
      |(∫ y, bandResponse C θ η0 1 K E1 E2 y ∂π) - estimator … (moment π 3) (moment π 4)| ≤ s ^ 3 / 6 * M) ∧
    (∀ M2, (∀ z ∈ Icc (1 - s0) (1 + s0),
        |bandResponse2 C θ η0 1 K E1 E2 z - 3 * bandResponse1 C θ η0 1 K E1 E2 1 * z ^ 2| ≤ M2) →
      |(∫ y, bandResponse C θ η0 1 K E1 E2 y ∂π) - energyEstimator (bandResponse C θ η0 1 K E1 E2 1)
          (bandResponse1 C θ η0 1 K E1 E2 1) (moment π 4)| ≤ s ^ 2 / 2 * M2)
```

T10 PR #501 connection (power response `ψ = y^p`, real `p`):
```lean
theorem power_coeffs (p : ℝ) :
    c0 (Cas13C01.psi p 1) (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1) = Cas13C01.c0 p ∧
    c3 (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1) = Cas13C01.c3 p ∧
    c4 (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1) = Cas13C01.c4 p
theorem power_cubic_mixture {p s s0 M : ℝ} (π : Measure ℝ) [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hs0 : s0 < 1) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |Cas13C01.dpsi3 p z - Cas13C01.dq3 p z| ≤ M) :
    |(∫ y, Cas13C01.psi p y ∂π) -
      (Cas13C01.c0 p + Cas13C01.c3 p * moment π 3 + Cas13C01.c4 p * moment π 4)| ≤ s ^ 3 / 6 * M
```

## Fidelity notes (no silent strengthening)

* Card domain `0<s≤s₀<1`: T2-T5 hold under the weaker `0≤s≤s₀` (they never use `y>0`);
  `s₀<1` (positive temperatures) is required exactly where positivity is used (T9 BE corollary,
  T10). `s=0` (MOM-ZEROWIDTH) is included and gives exact collapse.
* `sup` in (B3)/(B4) is represented by an arbitrary bound `M` of the same quantity on the same
  interval `[1−s₀,1+s₀]`; `bandpass_M_exists` shows a finite such `M` exists for the kernel.
* T1/T2 use a fencing (iterated mean-value) proof rather than the integral form of Taylor's
  remainder; the proved bound is the card's `|h| ≤ s³ sup|h'''|/6`.
* Measures are arbitrary probability measures on ℝ with a.e. support in `[1−s,1+s]`; moments are
  the actual Bochner integrals (no finite/atomic restriction except in the explicit witnesses).
* Not claimed: sharp minimax for every band kernel; that radial data determine angular modes;
  any statement about the actual (external, unrecovered) calibrated kernel beyond the class.
