# G11-B frozen targets (GR-CAS-11, TEFF-A1: integral Taylor / Hessian-envelope energy inequality)

Frozen 2026-10-13 before any proof attempt. Lean module `G11BHessianEnvelope`
(`lean/G11BHessianEnvelope.lean`), namespace `G11B`, importing Mathlib
(rev fabf563a7c95a166b8d7b6efca11c8b4dc9d911f, Lean 4.31.0) and the reviewed
G11-A modules `G11AIntegralBregman` (sha256 85993ce7...) and `G11AGuarded`
(sha256 92758d9a...), namespace `G11A`, via their compiled imports in
`../g11a_integral_bregman_v1_20261013/raw/imports` (LEAN_PATH). G11-A files
are imported, never edited or recompiled.

Only API-name probes (`#check`, `raw/probes/Probe_api_names_prefreeze.lean`)
were run before freezing; no target statement was elaborated.

## 0. Source recovery

`S` = `supplements/TEFF_POSITIVE_BRIDGE.md` (sha256 f04d96fe...);
`I`/`II` = hashed pdftotext extracts in
`../g11a_integral_bregman_v1_20261013/raw/sources/` (Paper I PDF d014d58f...,
Paper II PDF 299870d7...).

| Item | Source (verbatim gist) | Lean |
|---|---|---|
| δ = f − g; D_H(f‖g) ≤ ε < ∞ | S:41-44 (A1) | `Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε` (G11-A budget form) |
| "a known positive measurable weight W satisfies sup_{z between f(E,e),g(E,e)} z(1+ξz) ≤ W(E,e) a.e." | S:46-51 (A2) | `G11A.WEnvelope μ s W f g` = `Measurable W ∧ (∀ᵐ x, 0 < W x) ∧ ∀ᵐ x, ∀ z ∈ uIcc (f x) (g x), z * (1 + xi s * z) ≤ W x` |
| h''_ξ(f) = 1/[f(1+ξf)] | I:60 (14) | `G11A.hess` |
| "The integral Taylor remainder and I (14) give d_h(f‖g) = δ² ∫₀¹ (1−t) h''(g+tδ) dt ≥ δ²/(2W)" | S:76-81 | B0 (`taylor_integral_remainder`), B1 |
| "At physical endpoints the same statement follows by a limit." | S:83 | B3 (pointwise: regular approximation + continuity; integral: Fatou) |
| "Integrating gives ∫ δ²/W ≤ 2ε." | S:83 | B2 |
| entropy densities extended continuously to the physical endpoints; Bose condensates excluded | I:88-89 (Def. 1); II:13 "Endpoint values are understood by continuity" | `G11A.continuous_hS`, `G11A.continuous_bregDens_left`, `cdom` |
| contract wording "W bounds reciprocal Hessian on segment" | CAS-11.json task_assumptions | Hessian form `∀ z ∈ uIcc a b, z ∈ dom s → 1 / W ≤ hess s z` (implied by (A2) via `G11A.W_lower_bounds_hessian`) |
| measure dν = C E² dE dΩ | S:37-39 | `G11A.nu C` |

Domain discipline (inherited from G11-A review): the argument `f` ranges over
the closed admissible set `cdom s` (endpoints included), the reference `g`
over the OPEN set `dom s` (a boundary reference gives D = +∞, G11-A
`reference_lower_boundary`; ENT-DOMAIN excluded). `W > 0` exactly as the
source states ("positive"); W = 0 or W = ∞ is NOT admitted (card pitfall).
Only the `_stat` (domain-guarded) G11-A budget forms are used.

## 1. Targets (statements frozen verbatim)

```lean
open MeasureTheory Set Filter Topology
open scoped ENNReal
namespace G11B
open G11A
```

### B0 — integral Taylor remainder on the scalar entropy segment (regular case)

```lean
theorem taylor_integral_remainder (s : Stat) {a b : ℝ} (ha : a ∈ dom s) (hb : b ∈ dom s) :
    bregDens (hS s) (hS' s) a b =
      (a - b) ^ 2 * ∫ t in (0:ℝ)..1, (1 - t) * hess s (b + t * (a - b))
```

### B1 — pointwise Taylor / Hessian-envelope inequality

```lean
-- regular interior case, reciprocal-Hessian form of the envelope on the segment
theorem taylor_lower_regular (s : Stat) {a b W : ℝ} (ha : a ∈ dom s) (hb : b ∈ dom s)
    (hW : 0 < W) (henv : ∀ z ∈ uIcc a b, z ∈ dom s → 1 / W ≤ hess s z) :
    (a - b) ^ 2 / (2 * W) ≤ bregDens (hS s) (hS' s) a b

-- closed admissible argument (endpoints included), reciprocal-Hessian form
theorem hessian_envelope_pointwise (s : Stat) {a b W : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s)
    (hW : 0 < W) (henv : ∀ z ∈ uIcc a b, z ∈ dom s → 1 / W ≤ hess s z) :
    (a - b) ^ 2 / (2 * W) ≤ bregDens (hS s) (hS' s) a b

-- source (A2) form: sup over the segment of z(1+ξz) is ≤ W, W > 0
theorem B1_pointwise (s : Stat) {a b W : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s)
    (hW : 0 < W) (henv : ∀ z ∈ uIcc a b, z * (1 + xi s * z) ≤ W) :
    (a - b) ^ 2 / (2 * W) ≤ bregDens (hS s) (hS' s) a b

-- non-vacuity at a physical endpoint (MB, a = 0 ∉ dom, b = 1, W = 1)
theorem B1_nonvacuous_endpoint :
    (0:ℝ) ∈ cdom .MB ∧ (0:ℝ) ∉ dom .MB ∧ (1:ℝ) ∈ dom .MB ∧
      (∀ z ∈ uIcc (0:ℝ) 1, z * (1 + xi .MB * z) ≤ 1) ∧
      ((0:ℝ) - 1) ^ 2 / (2 * 1) ≤ bregDens (hS .MB) (hS' .MB) 0 1
```

### B3 (pointwise) — endpoint extension premises, each proved explicitly

```lean
-- regular approximants a_t = b + t (a − b), 0 ≤ t < 1, lie in the open domain
theorem regular_approx_mem (s : Stat) {a b t : ℝ} (ha : a ∈ cdom s) (hb : b ∈ dom s)
    (ht0 : 0 ≤ t) (ht1 : t < 1) : b + t * (a - b) ∈ dom s

-- the approximant segment is a sub-segment, so the envelope is inherited
theorem regular_approx_segment {a b t : ℝ} (ht0 : 0 ≤ t) (ht1 : t ≤ 1) :
    uIcc (b + t * (a - b)) b ⊆ uIcc a b

-- limit premise: continuity of the (continuously extended) Bregman density
theorem regular_approx_tendsto (s : Stat) (a b : ℝ) :
    Tendsto (fun t => bregDens (hS s) (hS' s) (b + t * (a - b)) b) (𝓝[<] 1)
      (𝓝 (bregDens (hS s) (hS' s) a b))
```
`hessian_envelope_pointwise` must be proved from `taylor_lower_regular` and
these three lemmas (limit t → 1⁻), not by a separate convexity argument.

### B2 — global energy inequality on an arbitrary measure, and on dν

```lean
variable {X : Type*} [MeasurableSpace X]

-- extended-value form (no finiteness assumed), Hessian-form envelope
theorem B2_lintegral_hess (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x)
    (hHess : ∀ᵐ x ∂μ, ∀ z ∈ uIcc (f x) (g x), z ∈ dom s → 1 / W x ≤ hess s z) :
    ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤ 2 * Dext μ (hS s) (hS' s) f g

-- extended-value form, source (A2) envelope
theorem B2_lintegral (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) :
    ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤ 2 * Dext μ (hS s) (hS' s) f g

-- Bochner form under the certified budget (uses G11A.finite_budget_stat)
theorem B2_integral (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε) :
    Integrable (fun x => (f x - g x) ^ 2 / W x) μ ∧
      ∫ x, (f x - g x) ^ 2 / W x ∂μ ≤ 2 * Dfin μ (hS s) (hS' s) f g ∧
      ∫ x, (f x - g x) ^ 2 / W x ∂μ ≤ 2 * ε

-- the massless one-event measure dν = C E² dE dΩ
theorem B2_nu (s : Stat) (C : ℝ) (f g W : ℝ × Sphere2 → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ y ∂nu C, f y ∈ cdom s) (hgd : ∀ᵐ y ∂nu C, g y ∈ dom s)
    (hW : WEnvelope (nu C) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (nu C) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε) :
    Integrable (fun y => (f y - g y) ^ 2 / W y) (nu C) ∧
      ∫ y, (f y - g y) ^ 2 / W y ∂nu C ≤ 2 * Dfin (nu C) (hS s) (hS' s) f g ∧
      ∫ y, (f y - g y) ^ 2 / W y ∂nu C ≤ 2 * ε
```

### B3 (integral) — lower semicontinuity and the endpoint limit by regular approximation

```lean
-- Fatou lower semicontinuity of the extended divergence under a.e. convergence
theorem B3_Dext_lsc (μ : Measure X) (s : Stat) (fseq : ℕ → X → ℝ) (f g : X → ℝ)
    (hfm : ∀ n, Measurable (fseq n)) (hgm : Measurable g)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x))) :
    Dext μ (hS s) (hS' s) f g ≤ liminf (fun n => Dext μ (hS s) (hS' s) (fseq n) g) atTop

-- Fatou lower semicontinuity of the weighted quadratic functional
theorem B3_quadratic_lsc (μ : Measure X) (fseq : ℕ → X → ℝ) (f g W : X → ℝ)
    (hfm : ∀ n, Measurable (fseq n)) (hgm : Measurable g) (hWm : Measurable W)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x))) :
    ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤
      liminf (fun n => ∫⁻ x, ENNReal.ofReal ((fseq n x - g x) ^ 2 / W x) ∂μ) atTop

-- endpoint limit: regular approximants with a common envelope and budget
theorem B3_endpoint_integral_by_regular_approx (μ : Measure X) (s : Stat)
    (fseq : ℕ → X → ℝ) (f g W : X → ℝ)
    (hfm : ∀ n, Measurable (fseq n)) (hgm : Measurable g)
    (hfseq : ∀ n, ∀ᵐ x ∂μ, fseq n x ∈ dom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : ∀ n, WEnvelope μ s W (fseq n) g)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x)))
    {ε : ℝ} (hε : ∀ n, Dext μ (hS s) (hS' s) (fseq n) g ≤ ENNReal.ofReal ε) :
    Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε ∧
      ∫⁻ x, ENNReal.ofReal ((f x - g x) ^ 2 / W x) ∂μ ≤ 2 * ENNReal.ofReal ε
```

## 2. Rules

* No `sorry`, `admit`, `sorryAx`, `native_decide`, new `axiom`, or hypothesis
  restating a conclusion. Accepted axioms: `propext`, `Classical.choice`,
  `Quot.sound` only.
* Statements above are frozen; only proofs may change. Any statement change
  must be recorded as a deviation in `AUTHOR_RETURN.json`.
* Auxiliary private/helper lemmas may be added; they are not claims.
* Stop rule: the same substantive failure twice after a real change → HOLD.

## 3. Not claimed

certified ε; unknown-shape ε from a fitted reference; scientific admission;
(A3)/(A4)/(A6) Cauchy–Schwarz / ellipsoid steps (other G11 cards); the BE
photon envelope (A5); a boundary reference g ∉ dom s; W = 0 or W = ∞.
