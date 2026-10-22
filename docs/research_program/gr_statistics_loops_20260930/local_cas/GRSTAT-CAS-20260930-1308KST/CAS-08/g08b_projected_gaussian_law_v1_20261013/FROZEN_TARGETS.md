# G08-B frozen targets

Origin: written fresh by this author run, before any proof compile. No earlier `FROZEN_TARGETS.md` existed because `T` was absent at start. Sources are listed in `SOURCE_RECOVERY.md`; the controlling statements are in NATIVE_INFERENCE_THEOREMS.md §4, lines 41, 73–92.

## Toolchain and setup

- Lean 4.31.0, Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.
- Working directory `/home/cosmosapjw/lean_oracles/viii_oracle`.
- Module `G08BGaussianLaw` in `lean/G08BGaussianLaw.lean`.
- It imports `Mathlib` and `G08ACorollaries` (which imports `G08AWhitening` and `ProjectionBridge`); all three are unchanged.

The Lean header is:

```lean
namespace G08BGaussianLaw
open MeasureTheory ProbabilityTheory Matrix WithLp
open scoped RealInnerProductSpace
variable {n k : ℕ}
```

## Notation

Source symbols map to Lean as follows:
- Data dimension `m` → `n`.
- `E := EuclideanSpace ℝ (Fin n)`.
- `C W : Matrix (Fin n) (Fin n) ℝ`.
- `F : Matrix (Fin n) (Fin k) ℝ`.
- `X : Matrix (Fin k) (Fin n) ℝ`.
- `P := 1 - W * F * X`.
- `ν := n - F.rank`, a natural number; `n - F.rank` is the source's `m - rank(F)`.

The standing hypotheses are those of G08-A. They are never strengthened:
- `hC : C.PosDef` (known SPD C).
- `hW : IsUnit W ∧ W * C * Wᵀ = 1` (any fixed whitening).
- `hX : G08AWhitening.IsMoorePenrose (W * F) X`, which means `P = I - (WF)(WF)⁺`. It allows any rank of F, including rank deficiency, F = 0 and full row rank.

The data law is source (4), `y = m(θ*) + Fβ* + ε` with `ε ~ N(0,C)`. It is formalized in two equivalent ways:
- **Measure form.** The law of `y` is `multivariateGaussian (mθ + toLp 2 (F *ᵥ β)) C`.
- **Random-variable form.** A measurable `ε : Ω → E` on a measure space `(Ω, ℙ)` with `ℙ.map ε = multivariateGaussian 0 C`, and `y ω = mθ + toLp 2 (F *ᵥ β) + ε ω`.

`β` is universally quantified. That universality *is* the source's "uniformly in β*".

## Definitions

These are definitions, not hypotheses. None of them postulates a target formula.

```lean
/-- χ²_ν: the law of the sum of squares of ν independent standard normals. -/
noncomputable def chiSq (ν : ℕ) : Measure ℝ :=
  (Measure.pi fun _ : Fin ν => gaussianReal 0 1).map (fun z => ∑ i, z i ^ 2)

/-- Lower p-quantile (generalized inverse of the CDF). -/
noncomputable def lowerQuantile (ρ : Measure ℝ) (p : ℝ) : ℝ := sInf {x | p ≤ cdf ρ x}

/-- Source threshold: q_{ν,α} = (1-α)-quantile of χ²_ν for ν > 0; q = 0 for ν = 0 (line 90). -/
noncomputable def threshold (ν : ℕ) (α : ℝ) : ℝ :=
  if ν = 0 then 0 else lowerQuantile (chiSq ν) (1 - α)

/-- Q_y(θ) = ‖P W (y - m(θ))‖², source (7). -/
noncomputable def Qstat (W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (mθ y : EuclideanSpace ℝ (Fin n)) : ℝ :=
  ‖toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W (y - mθ))‖ ^ 2

/-- Source confidence set (7): Cα(y) = {θ ∈ Ω : Q_y(θ) ≤ q}  (non-strict ≤). -/
def confSet {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n))
    (W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (q : ℝ) (y : EuclideanSpace ℝ (Fin n)) : Set Θ :=
  {θ | θ ∈ Ωd ∧ Qstat W F X (m θ) y ≤ q}
```

## Targets

### T1: linear (affine) pushforward of a Gaussian law
This is card lean_steps[1], "linear pushforward의 mean/covariance law". It is a *law* equality, not just a covariance identity: the image is Gaussian (`isGaussian_map`), and `IsGaussian.ext` is applied.
```lean
theorem map_affine_multivariateGaussian {μ c : EuclideanSpace ℝ (Fin n)}
    {S : Matrix (Fin n) (Fin n) ℝ} (hS : S.PosSemidef) (A : Matrix (Fin n) (Fin n) ℝ) :
    (multivariateGaussian μ S).map (fun x => toEuclideanCLM (𝕜 := ℝ) A (x - c)) =
      multivariateGaussian (toEuclideanCLM (𝕜 := ℝ) A (μ - c)) (A * S * Aᵀ)
```

### T2: actual law of the projected whitened residual is N(0, P), uniformly in β
```lean
theorem projected_residual_law (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) :
    (multivariateGaussian (mθ + toLp 2 (F *ᵥ β)) C).map
        (fun y => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W (y - mθ))) =
      multivariateGaussian 0 (1 - W * F * X)

theorem projected_residual_law_rv {Ω : Type*} [MeasurableSpace Ω] (ℙ : Measure Ω)
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n))
    (hε : Measurable ε) (hlaw : ℙ.map ε = multivariateGaussian 0 C) :
    ℙ.map (fun ω => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
        (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ))) =
      multivariateGaussian 0 (1 - W * F * X)
```

### T3: orthonormal coordinates are iid N(0,1)
This is card lean_steps[1], second half. The general rotational-invariance lemma:
```lean
theorem stdGaussian_map_orthonormal {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    [FiniteDimensional ℝ E] [MeasurableSpace E] [BorelSpace E] {ν : ℕ} (u : Fin ν → E)
    (hu : Orthonormal ℝ u) :
    (stdGaussian E).map (fun x i => ⟪u i, x⟫) = Measure.pi (fun _ : Fin ν => gaussianReal 0 1)
```
The ν-dimensional orthonormal frame of `P`. It exhibits the spectral form `P = Σ_{i<ν} u_i u_iᵀ`, with ν ones and n−ν zeros. The law of its coordinates is a product:
```lean
theorem projector_frame (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) :
    ∃ u : Fin (n - F.rank) → EuclideanSpace ℝ (Fin n), Orthonormal ℝ u ∧
      ∀ x, toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) x = ∑ i, ⟪u i, x⟫ • u i

theorem projected_coordinates_rv {Ω : Type*} [MeasurableSpace Ω] (ℙ : Measure Ω)
    [IsProbabilityMeasure ℙ]
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n))
    (hε : Measurable ε) (hlaw : ℙ.map ε = multivariateGaussian 0 C)
    (u : Fin (n - F.rank) → EuclideanSpace ℝ (Fin n)) (hu : Orthonormal ℝ u)
    (hP : ∀ x, toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) x = ∑ i, ⟪u i, x⟫ • u i) :
    let R : Ω → EuclideanSpace ℝ (Fin n) := fun ω => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
        (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ))
    ℙ.map (fun ω i => ⟪u i, R ω⟫) = Measure.pi (fun _ => gaussianReal 0 1) ∧
      (∀ i, ℙ.map (fun ω => ⟪u i, R ω⟫) = gaussianReal 0 1) ∧
      iIndepFun (fun i ω => ⟪u i, R ω⟫) ℙ ∧
      ∀ ω, ‖R ω‖ ^ 2 = ∑ i, ⟪u i, R ω⟫ ^ 2
```
`[IsProbabilityMeasure ℙ]` is already implied by `hε` and `hlaw`. It is stated explicitly for the independence API, so it is not a strengthening.

### T4: χ²_ν law of the statistic, with ν = n − rank F, and the ν = 0 degenerate law kept separate
This is card lean_steps[2].
```lean
theorem chiSq_law (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) :
    (multivariateGaussian (mθ + toLp 2 (F *ᵥ β)) C).map (Qstat W F X mθ) = chiSq (n - F.rank)

theorem chiSq_law_rv {Ω : Type*} [MeasurableSpace Ω] (ℙ : Measure Ω)
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n))
    (hε : Measurable ε) (hlaw : ℙ.map ε = multivariateGaussian 0 C) :
    ℙ.map (fun ω => Qstat W F X mθ (mθ + toLp 2 (F *ᵥ β) + ε ω)) = chiSq (n - F.rank)

theorem chiSq_zero : chiSq 0 = Measure.dirac 0

theorem chiSq_law_rank_zero (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ)
    (hν : n - F.rank = 0) :
    (multivariateGaussian (mθ + toLp 2 (F *ᵥ β)) C).map (Qstat W F X mθ) = Measure.dirac 0
```

### T5: properties of χ²_ν used by the quantile
```lean
instance isProbabilityMeasure_chiSq (ν : ℕ) : IsProbabilityMeasure (chiSq ν)
theorem chiSq_Iio_zero (ν : ℕ) : chiSq ν (Set.Iio 0) = 0
theorem chiSq_singleton {ν : ℕ} (hν : 0 < ν) (c : ℝ) : chiSq ν {c} = 0
```

### T6: quantile convention (0 < α < 1 as in the source; the endpoints are excluded by hypotheses)
```lean
theorem cdf_lowerQuantile (ρ : Measure ℝ) [IsProbabilityMeasure ρ] {p : ℝ} (hp0 : 0 < p)
    (hp1 : p < 1) (hatom : ρ {lowerQuantile ρ p} = 0) : cdf ρ (lowerQuantile ρ p) = p

theorem cdf_threshold {ν : ℕ} (hν : 0 < ν) {α : ℝ} (hα0 : 0 < α) (hα1 : α < 1) :
    cdf (chiSq ν) (threshold ν α) = 1 - α

/-- consistency: at ν = 0 the lower quantile of χ²_0 = δ₀ is the source's q = 0 -/
theorem lowerQuantile_chiSq_zero {p : ℝ} (hp0 : 0 < p) (hp1 : p ≤ 1) :
    lowerQuantile (chiSq 0) p = 0
```

### T7: coverage, source (8), with non-strict ≤, equality 1 − α, uniform in β*
This is card lean_steps[3]. `Θ`, `Ωd` and `m` are arbitrary, so any deterministic remainder inside the complete θ is covered.
```lean
theorem coverage {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α) y} = ENNReal.ofReal (1 - α)

theorem coverage_rv {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) {Ω : Type*} [MeasurableSpace Ω] (ℙ : Measure Ω)
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n)) (hε : Measurable ε)
    (hlaw : ℙ.map ε = multivariateGaussian 0 C) {α : ℝ} (hα0 : 0 < α) (hα1 : α < 1)
    (hν : 0 < n - F.rank) :
    ℙ {ω | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α) (m θs + toLp 2 (F *ᵥ β) + ε ω)} =
      ENNReal.ofReal (1 - α)
```
Rank-0 branch (source line 90: q = 0, Cα = Ω, coverage one). It holds for every α, so no hypothesis on α is needed:
```lean
theorem confSet_rank_zero {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n))
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (hν : n - F.rank = 0) (α : ℝ) (y : EuclideanSpace ℝ (Fin n)) :
    confSet Ωd m W F X (threshold (n - F.rank) α) y = Ωd

theorem coverage_rank_zero {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) (α : ℝ)
    (hν : n - F.rank = 0) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α) y} = 1
```

### T8: ≤ versus < boundary controls
For ν > 0, the strict event has the same probability, so the choice is immaterial there:
```lean
theorem coverage_strict {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ Ωd ∧ Qstat W F X (m θs) y < threshold (n - F.rank) α} = ENNReal.ofReal (1 - α)
```
Negative control at ν = 0: a strict `<` would give coverage 0, not 1. The source's non-strict `≤` is therefore load-bearing.
```lean
theorem strict_rank_zero_fails {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n))
    (θs : Θ) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) (α : ℝ)
    (hν : n - F.rank = 0) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ Ωd ∧ Qstat W F X (m θs) y < threshold (n - F.rank) α} = 0
```

### T9: non-vacuity and negative controls
```lean
/-- hypotheses jointly satisfiable with ν = 1 > 0 (n = k = 1, C = W = 1, F = X = 0) -/
theorem nonvacuous_nu_pos :
    ∃ (C W F X : Matrix (Fin 1) (Fin 1) ℝ), C.PosDef ∧ (IsUnit W ∧ W * C * Wᵀ = 1) ∧
      G08AWhitening.IsMoorePenrose (W * F) X ∧ 1 - F.rank = 1

/-- hypotheses jointly satisfiable with ν = 0 (n = k = 1, C = W = F = X = 1) -/
theorem nonvacuous_nu_zero :
    ∃ (C W F X : Matrix (Fin 1) (Fin 1) ℝ), C.PosDef ∧ (IsUnit W ∧ W * C * Wᵀ = 1) ∧
      G08AWhitening.IsMoorePenrose (W * F) X ∧ 1 - F.rank = 0

/-- the degrees of freedom matter: χ²_1 ≠ χ²_0 = δ₀ -/
theorem chiSq_one_ne_zero : chiSq 1 ≠ chiSq 0
```

## Faithfulness notes

- **Quantifiers.** C, W, F, X, β, m, Θ, Ω and θ* are all universal. The rank of F is arbitrary, and ν is the actual `n - F.rank`.
- **Measure.** The probability is the actual law `multivariateGaussian`, or a random variable with that law. Nothing is pulled back from a covariance identity alone.
- **Boundary branches.** The theorem keeps the source's `0 < α < 1`; endpoints are not claimed. Rank 0 is kept separate (`q = 0`, coverage 1, Cα = Ω). The `≤` / `<` distinction is checked by T8.
- **The pitfall "covariance match alone".** T1/T2 use Gaussianity of the image measure plus mean and covariance, through Mathlib `IsGaussian.ext`, i.e. characteristic functions. This is a law-level identification.

## Not claimed

The following are outside this card's targets:
- Identification of `chiSq ν` with `gammaMeasure (ν/2) (1/2)`, or with any closed-form density.
- Numerical agreement of `threshold` with SciPy `chi2.ppf`.
- The α endpoints α ∈ {0, 1}.
- Estimated C and selected or data-dependent F (CONF-ESTIMATEDC: no exact χ²).
- A law for `min_θ Q`.
- Wilks.
- The union bound `1-α-δ` for separately estimated remainder bounds.
- N1a projections and N2/G08-C decisions.
- SymPy and Sage tool tasks.
- Four-axis CAS status.
- Scientific admission (HOLD).
