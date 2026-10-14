# G12-F frozen targets (written before any proof compile)

Card: G12-F "Horizontal Fisher budget에서 실제 derivative observable 경계" (TEFF-A4 scope line;
source `supplements/TEFF_POSITIVE_BRIDGE.md:149-158`, conditions `DECISIONS.json:603-604`).
Source statement (verbatim, `:151`, `:155-158`):
`∫ |𝒟_X f|² / (f(1+f)) dν ≤ J_X` ⇒ in a parallel local tetrad, after controlling kernel and
measure differentiation, `|𝒟_X ∫ K f dν| ≤ √J_X [∫ K² f(1+f) dν]^{1/2}`.

Toolchain: Lean 4.31.0, Mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f.
Reviewed imports, unchanged: `G11AIntegralBregman` (→ `BregmanThreePoint`) for the core module;
`G12ECounterexample` (→ `G12EMomentNull` → `G11AGuarded`, `G12DCardClosure`,
`OscillatoryDerivative`) for the instance module.
New modules: `lean/G12FFisherBudget.lean` (namespace `G12F`, T0–T10),
`lean/G12FInstances.lean` (namespace `G12F`, T11–T14).

## Modelling (recovered, see SOURCE_RECOVERY.md §2)

The horizontal derivative `𝒟_X f` at the event `x0` is modelled as the pointwise `t`-derivative
`f' x0 z` of a one-parameter family `f : ℝ → X → ℝ` of occupations on a momentum fibre `X`
identified along the integral curve of `X` (parallel trivialization). `J` is a hypothesis about
that actual derivative (`f' x0`) — never about a static functional of `f x0`. The observable is
`∫ K f dν`; in a general trivialization `O(t) = ∫ K_t f_t ρ_t dμ` with a fixed reference measure
`μ`, a measure density `ρ_t` and a kernel `K_t`. The parallel construction is the case
`K_t = K`, `ρ_t = ρ` (`t`-independent). Statistics are general (`Stat` MB/BE/FD,
`statWeight s f = f(1+ξ f)`); the source's `f(1+f)` is the BE case and is stated verbatim in T6.

## Definitions (frozen)

```lean
/-- Extended Fisher density d²/w with 0/0 = 0 and d/0 = ∞ (d ≠ 0). -/
def fisherDens (d w : ℝ) : ℝ≥0∞ :=
  if 0 < w then ENNReal.ofReal (d ^ 2 / w) else if d = 0 then 0 else ⊤

/-- f(1 + ξ f); for BE this is f(1+f). -/
def statWeight (s : Stat) (f : ℝ) : ℝ := f * (1 + xi s * f)

/-- Null tetrad direction n = (1, e). -/
def nvec (e : Sphere2) : Fin 4 → ℝ :=
  ![1, (e : EuclideanSpace ℝ (Fin 3)) 0, (e : EuclideanSpace ℝ (Fin 3)) 1,
    (e : EuclideanSpace ℝ (Fin 3)) 2]

/-- Massless stress kernel K^{ab}(E, e) = n^a n^b E relative to dν = C E² dE dΩ. -/
def stressKernel (a c : Fin 4) (z : ℝ × Sphere2) : ℝ := (nvec z.2 a * nvec z.2 c) * z.1
```

## Targets — core module `G12FFisherBudget`

**T0 `fisherDens_of_dom` / `statWeight_nonneg`** (bridge to the reviewed G11A Fisher form)
```lean
theorem statWeight_nonneg (s : Stat) {f : ℝ} (hf : f ∈ cdom s) : 0 ≤ statWeight s f
theorem fisherDens_of_dom (s : Stat) {f : ℝ} (hf : f ∈ dom s) (d : ℝ) :
    fisherDens d (statWeight s f) = ENNReal.ofReal (d ^ 2 * hess s f)
```

**T1 `weighted_cauchy_schwarz`** (card step 3; general measure, measure density ρ ≥ 0)
```lean
theorem weighted_cauchy_schwarz {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (K d w ρ : X → ℝ) (J : ℝ)
    (hK : Measurable K) (hd : Measurable d) (hw : Measurable w) (hρ : Measurable ρ)
    (hw0 : ∀ᵐ z ∂μ, 0 ≤ w z) (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z)
    (hKw : Integrable (fun z => K z ^ 2 * w z * ρ z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (w z) ∂μ ≤ ENNReal.ofReal J) :
    Integrable (fun z => K z * d z * ρ z) μ ∧
      |∫ z, K z * d z * ρ z ∂μ| ≤ Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * w z * ρ z ∂μ)
```
Integrability of `K d ρ` is a conclusion, not an assumption (finite weighted norms suffice).

**T2 `real_budget_le`** (the G11A/G12E real-valued Fisher form implies the extended budget on
the open domain)
```lean
theorem real_budget_le {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (d f ρ : X → ℝ) (J : ℝ)
    (hdom : ∀ᵐ z ∂μ, f z ∈ dom s) (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z)
    (hint : Integrable (fun z => d z ^ 2 * hess s (f z) * ρ z) μ)
    (hle : ∫ z, d z ^ 2 * hess s (f z) * ρ z ∂μ ≤ J) :
    ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (statWeight s (f z)) ∂μ ≤ ENNReal.ofReal J
```

**T3 `zero_weight_null`** (zero occupation / FD saturation: a finite budget forces the
derivative to vanish a.e. where the weight vanishes and the density is positive)
```lean
theorem zero_weight_null {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (d w ρ : X → ℝ) (J : ℝ) (hd : Measurable d) (hw : Measurable w) (hρ : Measurable ρ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (w z) ∂μ ≤ ENNReal.ofReal J) :
    ∀ᵐ z ∂μ, w z ≤ 0 → 0 < ρ z → d z = 0
```

**T4 `zero_occupation_derivative`** (consistency: an admissible differentiable family has zero
derivative where `f(1+ξf) = 0`, so the extended Fisher density is finite (= 0) there)
```lean
theorem zero_occupation_derivative (s : Stat) (φ : ℝ → ℝ) (x0 d : ℝ)
    (hφ : ∀ᶠ t in 𝓝 x0, φ t ∈ cdom s) (hd : HasDerivAt φ d x0)
    (h0 : statWeight s (φ x0) = 0) :
    d = 0 ∧ fisherDens d (statWeight s (φ x0)) = 0
```

**T5 `parallel_derivative_bound`** (card steps 2–3; parallel construction: fixed kernel, fixed
measure density; differentiation under the integral by domination)
```lean
theorem parallel_derivative_bound {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (K ρ : X → ℝ) (f f' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K z * f t z * ρ z) μ)
    (hF_int : Integrable (fun z => K z * f x0 z * ρ z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K z * f' t z * ρ z| ≤ bound z)
    (hbound : Integrable bound μ)
    (h_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hK : Measurable K) (hρ : Measurable ρ) (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K z ^ 2 * statWeight s (f x0 z) * ρ z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J) :
    HasDerivAt (fun t => ∫ z, K z * f t z * ρ z ∂μ) (∫ z, K z * f' x0 z * ρ z ∂μ) x0 ∧
      |∫ z, K z * f' x0 z * ρ z ∂μ| ≤
        Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * statWeight s (f x0 z) * ρ z ∂μ)
```

**T6 `teff_a4_derivative_bound_BE`** (source statement verbatim: measure `μ = dν` itself, BE
weight `f(1+f)` written literally)
```lean
theorem teff_a4_derivative_bound_BE {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (K : X → ℝ) (f f' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K z * f t z) μ)
    (hF_int : Integrable (fun z => K z * f x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K z * f' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (h_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hK : Measurable K) (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (hnn : ∀ᵐ z ∂μ, 0 ≤ f x0 z)
    (hKw : Integrable (fun z => K z ^ 2 * (f x0 z * (1 + f x0 z))) μ)
    (hJ : ∫⁻ z, fisherDens (f' x0 z) (f x0 z * (1 + f x0 z)) ∂μ ≤ ENNReal.ofReal J) :
    HasDerivAt (fun t => ∫ z, K z * f t z ∂μ) (∫ z, K z * f' x0 z ∂μ) x0 ∧
      |∫ z, K z * f' x0 z ∂μ| ≤
        Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * (f x0 z * (1 + f x0 z)) ∂μ)
```

**T7 `general_derivative_bound`** (card step 4; non-parallel trivialization: kernel term and
measure term added exactly)
```lean
theorem general_derivative_bound {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (K K' f f' ρ ρ' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K t z * f t z * ρ t z) μ)
    (hF_int : Integrable (fun z => K x0 z * f x0 z * ρ x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K t z * f' t z * ρ t z + K' t z * f t z * ρ t z +
      K t z * f t z * ρ' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (hK_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => K t z) (K' t z) t)
    (hf_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hρ_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => ρ t z) (ρ' t z) t)
    (hKm : Measurable (K x0)) (hK'm : Measurable (K' x0)) (hfm : Measurable (f x0))
    (hdm : Measurable (f' x0)) (hρm : Measurable (ρ x0)) (hρ'm : Measurable (ρ' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ x0 z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ x0 z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J)
    (hkern : Integrable (fun z => K' x0 z * f x0 z * ρ x0 z) μ) :
    Integrable (fun z => K x0 z * f x0 z * ρ' x0 z) μ ∧
    HasDerivAt (fun t => ∫ z, K t z * f t z * ρ t z ∂μ)
      ((∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)) x0 ∧
    |(∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)| ≤
      Real.sqrt J * Real.sqrt (∫ z, K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z ∂μ) +
        |∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ| + |∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ|
```
Order of terms: horizontal (Fisher) term, kernel-derivative term, measure-derivative term.

**T8 `general_derivative_bound_envelope`** (card step 4: each correction bounded by an
occupation envelope `|f x0| ≤ F`)
```lean
theorem general_derivative_bound_envelope {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (s : Stat) (K K' f f' ρ ρ' : ℝ → X → ℝ) (x0 J : ℝ) (bound F : X → ℝ) (U : Set ℝ)
    (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K t z * f t z * ρ t z) μ)
    (hF_int : Integrable (fun z => K x0 z * f x0 z * ρ x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K t z * f' t z * ρ t z + K' t z * f t z * ρ t z +
      K t z * f t z * ρ' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (hK_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => K t z) (K' t z) t)
    (hf_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hρ_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => ρ t z) (ρ' t z) t)
    (hKm : Measurable (K x0)) (hK'm : Measurable (K' x0)) (hfm : Measurable (f x0))
    (hdm : Measurable (f' x0)) (hρm : Measurable (ρ x0)) (hρ'm : Measurable (ρ' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ x0 z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ x0 z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J)
    (hkern : Integrable (fun z => K' x0 z * f x0 z * ρ x0 z) μ)
    (henv : ∀ᵐ z ∂μ, |f x0 z| ≤ F z)
    (hI1 : Integrable (fun z => |K' x0 z| * F z * ρ x0 z) μ)
    (hI2 : Integrable (fun z => |K x0 z| * F z * |ρ' x0 z|) μ) :
    |(∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)| ≤
      Real.sqrt J * Real.sqrt (∫ z, K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z ∂μ) +
        (∫ z, |K' x0 z| * F z * ρ x0 z ∂μ) + (∫ z, |K x0 z| * F z * |ρ' x0 z| ∂μ)
```

**T9 `sharp_witness`** (non-vacuity and sharpness of the constant: one-point measure, BE,
`f_t = 1 + t`, `K = 1`; budget `J = 1/2`, weighted norm `2`, derivative `1 = √(1/2)·√2`)
```lean
theorem sharp_witness :
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 1 (statWeight .BE 1) ∂(Measure.dirac ()) =
      ENNReal.ofReal (1 / 2)) ∧
    (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ()) = 2) ∧
    HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 : ℝ) * (1 + t) * 1 ∂(Measure.dirac ())) 1 0 ∧
    |(1 : ℝ)| = Real.sqrt (1 / 2) * Real.sqrt 2
```

**T10 negative controls**
```lean
/-- (a) Lean's junk `hess s 0 = 0`: the real-valued Fisher form vanishes at zero weight while
the observable derivative does not, so the bound fails for the real form; the extended density
is `⊤` there. -/
theorem junk_hess_control :
    (∫ z : Unit, (1 : ℝ) ^ 2 * hess .BE 0 ∂(Measure.dirac ())) = 0 ∧
    ¬ (|∫ z : Unit, (1 : ℝ) * 1 * 1 ∂(Measure.dirac ())| ≤
        Real.sqrt 0 * Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 0 * 1 ∂(Measure.dirac ()))) ∧
    fisherDens 1 (statWeight .BE 0) = ⊤

/-- (b) The measure-derivative term cannot be dropped: f ≡ 1 (zero horizontal derivative,
budget 0), K ≡ 1, ρ_t = 1 + t. -/
theorem measure_term_necessary :
    HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 : ℝ) * 1 * (1 + t) ∂(Measure.dirac ())) 1 0 ∧
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 0 (statWeight .BE 1) ∂(Measure.dirac ()) = 0) ∧
    ¬ (|(1 : ℝ)| ≤ Real.sqrt 0 *
        Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ())))

/-- (c) The kernel-derivative term cannot be dropped: f ≡ 1, ρ ≡ 1, K_t = 1 + t. -/
theorem kernel_term_necessary :
    HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 + t) * 1 * 1 ∂(Measure.dirac ())) 1 0 ∧
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 0 (statWeight .BE 1) ∂(Measure.dirac ()) = 0) ∧
    ¬ (|(1 : ℝ)| ≤ Real.sqrt 0 *
        Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ())))
```

## Targets — instance module `G12FInstances` (card step 5 and pitfall)

Write `μE := G12D.energyAngularMeasure G11A.dOmega` (Lebesgue on `E > 0` times surface measure)
and `ρ(E) = C E²`, so `ρ μE` is the source `dν = C E² dE dΩ`.

**T11 `stress_weighted_norm`** (finite weighted norm of every stress kernel under the BE
envelope, with an explicit envelope-only bound)
```lean
theorem stress_weighted_norm (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (f : ℝ × Sphere2 → ℝ)
    (hf : Measurable f)
    (henv : ∀ z : ℝ × Sphere2, 0 < z.1 → 0 ≤ f z ∧ f z ≤ G12D.occupation b 0 z.1)
    (a c : Fin 4) :
    Integrable (fun z => stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2))
      (G12D.energyAngularMeasure dOmega) ∧
    ∫ z, stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega) ≤
      ∫ z, G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2 ∂(G12D.energyAngularMeasure dOmega)
```

**T12 `stress_derivative_bound`** (final typed energy-frame statement: parallel construction,
fixed stress kernel and fixed `dν`, BE envelope at the event; the weighted-norm hypothesis of
T5 is discharged by T11)
```lean
theorem stress_derivative_bound (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (a c : Fin 4)
    (f f' : ℝ → ℝ × Sphere2 → ℝ) (x0 J : ℝ) (bound : ℝ × Sphere2 → ℝ) (U : Set ℝ)
    (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable
      (fun z => stressKernel a c z * f t z * (C * z.1 ^ 2)) (G12D.energyAngularMeasure dOmega))
    (hF_int : Integrable (fun z => stressKernel a c z * f x0 z * (C * z.1 ^ 2))
      (G12D.energyAngularMeasure dOmega))
    (h_bound : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega), ∀ t ∈ U,
      |stressKernel a c z * f' t z * (C * z.1 ^ 2)| ≤ bound z)
    (hbound : Integrable bound (G12D.energyAngularMeasure dOmega))
    (h_diff : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega), ∀ t ∈ U,
      HasDerivAt (fun t => f t z) (f' t z) t)
    (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (henv : ∀ z : ℝ × Sphere2, 0 < z.1 → 0 ≤ f x0 z ∧ f x0 z ≤ G12D.occupation b 0 z.1)
    (hJ : ∫⁻ z, ENNReal.ofReal (C * z.1 ^ 2) * fisherDens (f' x0 z) (statWeight .BE (f x0 z))
      ∂(G12D.energyAngularMeasure dOmega) ≤ ENNReal.ofReal J) :
    HasDerivAt (fun t => ∫ z, stressKernel a c z * f t z * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega))
      (∫ z, stressKernel a c z * f' x0 z * (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega)) x0 ∧
    |∫ z, stressKernel a c z * f' x0 z * (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega)| ≤
      Real.sqrt J * Real.sqrt (∫ z, stressKernel a c z ^ 2 * statWeight .BE (f x0 z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega)) ∧
    ∫ z, stressKernel a c z ^ 2 * statWeight .BE (f x0 z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega) ≤
      ∫ z, G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2 ∂(G12D.energyAngularMeasure dOmega)
```

**T13 `stress_nonvacuity`** (non-vacuity of T12 on the photon envelope: the concrete family
`f_t = (1 + t) F_{2b}`, `F_{2b} = occupation (2b) 0`, at `x0 = 0`, satisfies every hypothesis
of T12 with a finite budget; the proof must go through T12)
```lean
theorem stress_nonvacuity (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (a c : Fin 4) :
    ∃ J : ℝ,
      HasDerivAt (fun t => ∫ z, stressKernel a c z * ((1 + t) * G12D.occupation (2 * b) 0 z.1) *
          (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega))
        (∫ z, stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)) 0 ∧
      |∫ z, stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)| ≤
        Real.sqrt J * Real.sqrt (∫ z, stressKernel a c z ^ 2 *
          statWeight .BE ((1 + 0) * G12D.occupation (2 * b) 0 z.1) * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega))
```

**T14 `g12e_family_violates_budget`** (pitfall: the positive conditional bound and the G12-E
no-go are consistent — for every finite `J` the G12-E family eventually violates the budget
hypothesis, so T5/T6 do not apply to it uniformly)
```lean
theorem g12e_family_violates_budget (C : ℝ) (hC : 0 < C) (s : Stat) (g q : ℝ → ℝ)
    {E1 E2 : ℝ} (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hq : Continuous q) (hE1 : 0 < E1)
    (hz : ∀ E ∉ Icc E1 E2, q E = 0) (hq0 : ∃ E0, q E0 ≠ 0) (a : ℝ) (ha : a ≠ 0) (J : ℝ) :
    ∀ᶠ n : ℕ in atTop, ¬ (∫⁻ z, fisherDens (a * n * q z.1)
        (statWeight s (G12E.family (Ω := Sphere2) g q a n 0 z)) ∂nu C ≤ ENNReal.ofReal J)
```

## Explicit non-claims

* The parallel local tetrad trivialization itself (bundle, connection, `𝒟_X = ∂_t`) is a
  modelling input, not formalized (SOURCE_RECOVERY M1).
* The constant `C` and factors of `c` in the stress kernel are not fixed (M2); units are a
  documented dimensional check only.
* `μE` with density `C E²` is the carrier used here; its identification with `G11A.nu C` is not
  claimed.
* The energy-frame spectral-gap bound consuming these derivative inputs is not proved.
* No physical certification of any `J_X` value; `J` is always a hypothesis.
* Scientific admission: HOLD.
