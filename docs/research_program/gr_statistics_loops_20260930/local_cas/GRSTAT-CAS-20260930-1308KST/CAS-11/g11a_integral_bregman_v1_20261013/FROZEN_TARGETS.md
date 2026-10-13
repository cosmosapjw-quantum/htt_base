# G11-A frozen targets (GR-CAS-11, TEFF-A0/A1 integral Bregman bridge)

Frozen 2026-10-13 before any proof attempt. Lean module `G11AIntegralBregman`
(`lean/G11AIntegralBregman.lean`), namespace `G11A`, importing Mathlib
(rev fabf563a7c95a166b8d7b6efca11c8b4dc9d911f, Lean 4.31.0) and the accepted
C01 v2 module `BregmanThreePoint` (namespace `CAS11C01`, sha256
12f3dd682db93f0966fd3547f10f25eb4fca9e8506ff58fc7c1ba6ac7cf9975c, identical to
blob 10e02af5 on branch proof/cas11-c01-bregman-v2-20261008).

Only API-name probes (`#check`) were run in a scratch directory before freezing;
no target statement was elaborated before this file was written.

## 0. Recovered definitions (source citations)

Line numbers refer to the hashed pdftotext extracts in `raw/sources/`
(`I` = TEFF_PAPER_I_revised.pp2-3.pdftotext.txt, PDF sha256 d014d58f...;
`II` = TEFF_PAPER_II_revised.pp3-4.pdftotext.txt, PDF sha256 299870d7...;
`S` = supplements/TEFF_POSITIVE_BRIDGE.md sha256 f04d96fe...).

| Item | Source | Lean |
|---|---|---|
| measure dν = C E² dE dΩ, one event, one observer | S:37-39; II:29 ("dν_U = C E² dE dΩ"); I:33 (X_0=(0,∞)×S², dΠ_0 = C u² du dΩ, C>0; u=E/(k_B T_ref) at µ=0) | `nu C` on `ℝ × Sphere2` = (Lebesgue on Ioi 0 with density C E²) ⊗ (surface measure `volume.toSphere` on the unit sphere of ℝ³) |
| statistics label ξ = 0, +1, −1 (MB, BE, FD) | I:45 (9) | `Stat`, `xi` |
| h_0 = f ln f − f; h_{+1} = f ln f − (1+f) ln(1+f); h_{−1} = f ln f + (1−f) ln(1−f) | I:53-55 (11)-(13); II:12 (24) | `hS` |
| h'_ξ(f) = ln[f/(1+ξf)], h''_ξ(f) = 1/[f(1+ξf)] > 0 | I:60 (14); II:27 | `hS'`, `hess` |
| physical (regular, open) domains: f > 0 (MB, BE), 0 < f < 1 (FD) | I:57 | `dom` |
| admissible closure: f ≥ 0 (MB/BE), 0 ≤ f ≤ 1 (FD); entropy densities extended continuously to the physical endpoints; singular Bose condensates excluded | I:82-89 Def. 1 (18); II:13 ("Endpoint values are understood by continuity") | `cdom`, `continuous_hS` |
| D_H(f‖g) = H[f] − H[g] − ∫ h'(g)(f−g) dΠ | I:72 (16); II:23 (25) | `source_form_eq` (K0) links to `Dfin` |
| comparison theorems require finite displayed divergences | I:90; II:62 (Prop. 3) | `Dext ≠ ⊤` premises; K3 |
| retained linear moments ∫ φ_a δ dν = 0, a = 1..m, V = span{φ_a} | S:41-46 (A1) | `φ : Fin m → X → ℝ`, `hmatch` |
| matched Pythagorean identity D(f‖R_E) = D(f‖R_{N,E}) + D(R_{N,E}‖R_E); "cross term is a linear combination of the matched number and energy residuals" | II:58-69 (29) | `pythagorean`, `K2_instance` |
| positive measurable W with sup_{z between f,g} z(1+ξz) ≤ W a.e. | S:46-51 (A2) | `WEnvelope`; W bounds the reciprocal Hessian (1/W ≤ h''), never equals it |
| natural field f = Φ_ξ(z), Φ_0 = e^{−z}, Φ_ξ = 1/(e^z − ξ) | I:49 (10), I:126 (22) | `Phi`, `hS'_Phi` (supplementary) |
| ε: certified budget, never from a fitted reference entropy | S:43, S:104 | `ε` is a free real input; no construction |

## 1. Definitions (frozen)

```lean
def bregDens (h h' : ℝ → ℝ) (a b : ℝ) : ℝ := h a - h b - h' b * (a - b)
noncomputable def Dfin {X : Type*} [MeasurableSpace X] (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ) : ℝ :=
  ∫ x, bregDens h h' (f x) (g x) ∂μ
noncomputable def Dext {X : Type*} [MeasurableSpace X] (μ : Measure X) (h h' : ℝ → ℝ) (f g : X → ℝ) : ℝ≥0∞ :=
  ∫⁻ x, ENNReal.ofReal (bregDens h h' (f x) (g x)) ∂μ
inductive Stat | MB | BE | FD
def xi : Stat → ℝ  -- MB ↦ 0, BE ↦ 1, FD ↦ -1
noncomputable def hMB (f : ℝ) : ℝ := f * Real.log f - f
noncomputable def hBE (f : ℝ) : ℝ := f * Real.log f - (1 + f) * Real.log (1 + f)
noncomputable def hFD (f : ℝ) : ℝ := f * Real.log f + (1 - f) * Real.log (1 - f)
noncomputable def hS : Stat → ℝ → ℝ  -- MB ↦ hMB, BE ↦ hBE, FD ↦ hFD
noncomputable def hS' (s : Stat) (f : ℝ) : ℝ := Real.log (f / (1 + xi s * f))
noncomputable def hess (s : Stat) (f : ℝ) : ℝ := 1 / (f * (1 + xi s * f))
def dom : Stat → Set ℝ   -- MB, BE ↦ Ioi 0 ; FD ↦ Ioo 0 1
def cdom : Stat → Set ℝ  -- MB, BE ↦ Ici 0 ; FD ↦ Icc 0 1
noncomputable def Phi : Stat → ℝ → ℝ  -- MB ↦ exp(-z), BE ↦ 1/(exp z - 1), FD ↦ 1/(exp z + 1)
def WEnvelope {X} [MeasurableSpace X] (μ : Measure X) (s : Stat) (W f g : X → ℝ) : Prop :=
  Measurable W ∧ (∀ᵐ x ∂μ, 0 < W x) ∧ ∀ᵐ x ∂μ, ∀ z ∈ Set.uIcc (f x) (g x), z * (1 + xi s * z) ≤ W x
abbrev Sphere2 := Metric.sphere (0 : EuclideanSpace ℝ (Fin 3)) 1
noncomputable def dOmega : Measure Sphere2 := (volume : Measure (EuclideanSpace ℝ (Fin 3))).toSphere
noncomputable def nu (C : ℝ) : Measure (ℝ × Sphere2) :=
  ((volume.restrict (Set.Ioi (0:ℝ))).withDensity (fun E => ENNReal.ofReal (C * E ^ 2))).prod dOmega
```

Lean junk-value caveat (load-bearing): `Real.log 0 = 0`, so `hS' s 0` is a finite junk
value. Every theorem that uses h'(g) requires `g ∈ dom s` (open domain) explicitly;
`junk_reference_control` documents what goes wrong otherwise. The Bochner value
`Dfin` is 0 on the non-integrable branch; it is never used as a budget without
an integrability or `Dext ≠ ⊤` premise (K3f).

## 2. Targets (exact signatures; `X` an arbitrary measurable space, `μ : Measure X`)

### Reuse of accepted C01 v2 (pointwise a.e. theorem)
- P0 `bregDens_eq_c01 (h h' : ℝ → ℝ) (a b : ℝ) : bregDens h h' a b = CAS11C01.bregman (n := 1) (fun v => h (v 0)) (fun v _ => h' (v 0)) (fun _ => a) (fun _ => b)`
- P1 `pointwise_three_point (h h' : ℝ → ℝ) (a b c : ℝ) : bregDens h h' a b - bregDens h h' a c - bregDens h h' c b = (h' c - h' b) * (a - c)` (proof must go through `CAS11C01.three_point`)

### K0 source-form agreement (I (16) / II (25))
- `source_form_eq (μ) (h h') (f g : X → ℝ) (hf : Integrable (fun x => h (f x)) μ) (hg : Integrable (fun x => h (g x)) μ) (hlin : Integrable (fun x => h' (g x) * (f x - g x)) μ) : Dfin μ h h' f g = (∫ x, h (f x) ∂μ) - (∫ x, h (g x) ∂μ) - ∫ x, h' (g x) * (f x - g x) ∂μ`

### K1 integral three-point identity
- K1a `cross_integrable (μ) (h h') (f g k : X → ℝ) (hfg : Integrable (fun x => bregDens h h' (f x) (g x)) μ) (hfk : Integrable (fun x => bregDens h h' (f x) (k x)) μ) (hkg : Integrable (fun x => bregDens h h' (k x) (g x)) μ) : Integrable (fun x => (h' (k x) - h' (g x)) * (f x - k x)) μ`
- K1 `integral_three_point` (same premises) `: Dfin μ h h' f g - Dfin μ h h' f k - Dfin μ h h' k g = ∫ x, (h' (k x) - h' (g x)) * (f x - k x) ∂μ`

### K2 cross-term cancellation under exact retained-moment matching
- K2 `cross_term_vanishes {m : ℕ} (μ) (h h') (f g k : X → ℝ) (φ : Fin m → X → ℝ) (lam : Fin m → ℝ) (hspan : ∀ᵐ x ∂μ, h' (k x) - h' (g x) = ∑ j, lam j * φ j x) (hφf : ∀ j, Integrable (fun x => φ j x * f x) μ) (hφk : ∀ j, Integrable (fun x => φ j x * k x) μ) (hmatch : ∀ j, ∫ x, φ j x * f x ∂μ = ∫ x, φ j x * k x ∂μ) : ∫ x, (h' (k x) - h' (g x)) * (f x - k x) ∂μ = 0`
- K2b `pythagorean` (K1 premises hfg hfk hkg + K2 premises) `: Dfin μ h h' f g = Dfin μ h h' f k + Dfin μ h h' k g`

### K3 nonnegativity and the finite/infinite branch
- K3a `bregDens_nonneg {S : Set ℝ} {h h' : ℝ → ℝ} (hconv : ConvexOn ℝ S h) {a b : ℝ} (ha : a ∈ S) (hb : b ∈ S) (hd : HasDerivAt h (h' b) b) : 0 ≤ bregDens h h' a b`
- K3b `Dfin_nonneg (μ) {S} {h h'} (hconv : ConvexOn ℝ S h) (f g : X → ℝ) (hf : ∀ᵐ x ∂μ, f x ∈ S) (hg : ∀ᵐ x ∂μ, g x ∈ S) (hd : ∀ᵐ x ∂μ, HasDerivAt h (h' (g x)) (g x)) : 0 ≤ Dfin μ h h' f g`
- K3c `Dext_ne_top_iff (μ) (h h') (f g) (hmeas : AEStronglyMeasurable (fun x => bregDens h h' (f x) (g x)) μ) (hnn : ∀ᵐ x ∂μ, 0 ≤ bregDens h h' (f x) (g x)) : Dext μ h h' f g ≠ ⊤ ↔ Integrable (fun x => bregDens h h' (f x) (g x)) μ`
- K3d `Dext_eq_ofReal (μ) (h h') (f g) (hint : Integrable (fun x => bregDens h h' (f x) (g x)) μ) (hnn : ∀ᵐ x ∂μ, 0 ≤ bregDens h h' (f x) (g x)) : Dext μ h h' f g = ENNReal.ofReal (Dfin μ h h' f g)`
- K3e `finite_budget (μ) (h h') (f g) (hmeas) (hnn) {ε : ℝ} (hε0 : 0 ≤ ε) (hε : Dext μ h h' f g ≤ ENNReal.ofReal ε) : Integrable (fun x => bregDens h h' (f x) (g x)) μ ∧ 0 ≤ Dfin μ h h' f g ∧ Dfin μ h h' f g ≤ ε`
- K3f `infinite_branch_no_budget (μ) (h h') (f g) (hmeas) (hnn) (hni : ¬ Integrable (fun x => bregDens h h' (f x) (g x)) μ) : Dext μ h h' f g = ⊤ ∧ (∀ ε : ℝ, ¬ Dext μ h h' f g ≤ ENNReal.ofReal ε) ∧ Dfin μ h h' f g = 0` (last conjunct = Bochner junk value, recorded as NOT a budget)
- K3g `nested_budget` (K2b premises + `hconv : ConvexOn ℝ S h`, `hk : ∀ᵐ x ∂μ, k x ∈ S`, `hg : ∀ᵐ x ∂μ, g x ∈ S`, `hd : ∀ᵐ x ∂μ, HasDerivAt h (h' (g x)) (g x)`) `: Dfin μ h h' f k ≤ Dfin μ h h' f g`

### Statistics instance (I (9)-(14), Def. 1)
- S0 `dom_subset_cdom (s) : dom s ⊆ cdom s`; `interior_cdom (s) : interior (cdom s) = dom s`; `dom_pos (s) {x} (hx : x ∈ dom s) : 0 < x ∧ 0 < 1 + xi s * x`
- S1 `continuous_hS (s) : Continuous (hS s)` (continuous extension to the physical endpoints)
- S2 `hasDerivAt_hS (s) {x} (hx : x ∈ dom s) : HasDerivAt (hS s) (hS' s x) x`
- S3 `convexOn_hS (s) : ConvexOn ℝ (cdom s) (hS s)`
- S4 `bregDens_nonneg_stat (s) {a b} (ha : a ∈ cdom s) (hb : b ∈ dom s) : 0 ≤ bregDens (hS s) (hS' s) a b`
- S5 `measurable_bregDens_stat (s) {Y} [MeasurableSpace Y] {f g : Y → ℝ} (hf : Measurable f) (hg : Measurable g) : Measurable (fun y => bregDens (hS s) (hS' s) (f y) (g y))`

### Measure instance dν = C E² dE dΩ
- I1 `K1_instance (s : Stat) (C : ℝ) (f g k : ℝ × Sphere2 → ℝ) (hfm : Measurable f) (hgm : Measurable g) (hkm : Measurable k) (hf : ∀ᵐ y ∂nu C, f y ∈ cdom s) (hg : ∀ᵐ y ∂nu C, g y ∈ dom s) (hk : ∀ᵐ y ∂nu C, k y ∈ dom s) (hfg : Dext (nu C) (hS s) (hS' s) f g ≠ ⊤) (hfk : Dext (nu C) (hS s) (hS' s) f k ≠ ⊤) (hkg : Dext (nu C) (hS s) (hS' s) k g ≠ ⊤) : Dfin (nu C) (hS s) (hS' s) f g - Dfin (nu C) (hS s) (hS' s) f k - Dfin (nu C) (hS s) (hS' s) k g = ∫ y, (hS' s (k y) - hS' s (g y)) * (f y - k y) ∂nu C`
- I2 `K2_instance` (I1 premises + `{m : ℕ} (φ : Fin m → ℝ × Sphere2 → ℝ) (lam : Fin m → ℝ)` + `hspan hφf hφk hmatch` as in K2 with `μ := nu C`, `h' := hS' s`) `: Dfin (nu C) (hS s) (hS' s) f g = Dfin (nu C) (hS s) (hS' s) f k + Dfin (nu C) (hS s) (hS' s) k g ∧ Dfin (nu C) (hS s) (hS' s) f k ≤ Dfin (nu C) (hS s) (hS' s) f g`

### K4 regular interior versus occupation endpoints
- K4a endpoint sets: `endpoints_MB : cdom .MB \ dom .MB = {0}`, `endpoints_BE : cdom .BE \ dom .BE = {0}`, `endpoints_FD : cdom .FD \ dom .FD = {0, 1}`
- K4b (fine state at an endpoint is allowed): covered by I1/I2 whose `f` premise is `cdom s`; reference states `g, k` must lie in the open `dom s`.
- K4c `endpoint_limit (s) (e b : ℝ) : Tendsto (fun a => bregDens (hS s) (hS' s) a b) (𝓝[dom s] e) (𝓝 (bregDens (hS s) (hS' s) e b))` (pointwise limit from the regular interior to the endpoint value, source "extended continuously")
- K4d `integral_endpoint_limit (μ) (s) (fseq : ℕ → X → ℝ) (f g G : X → ℝ) (hfm : ∀ n, Measurable (fseq n)) (hf : Measurable f) (hgm : Measurable g) (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x))) (hGi : Integrable G μ) (hdom : ∀ n, ∀ᵐ x ∂μ, ‖bregDens (hS s) (hS' s) (fseq n x) (g x)‖ ≤ G x) : Integrable (fun x => bregDens (hS s) (hS' s) (f x) (g x)) μ ∧ Tendsto (fun n => Dfin μ (hS s) (hS' s) (fseq n) g) atTop (𝓝 (Dfin μ (hS s) (hS' s) f g))` — the domination `G` is an ADDED premise; the source does not state the mode of the integral endpoint limit.
- K4e reference at the entropy boundary is an infinite divergence, never a finite budget:
  `reference_lower_boundary (s) {a : ℝ} (ha : 0 < a) : Tendsto (fun b => bregDens (hS s) (hS' s) a b) (𝓝[dom s] 0) atTop`;
  `reference_upper_boundary_FD {a : ℝ} (ha : a < 1) : Tendsto (fun b => bregDens (hS .FD) (hS' .FD) a b) (𝓝[dom .FD] 1) atTop`
- K4f control `junk_reference_control : bregDens (hS .MB) (hS' .MB) 1 0 = -1` (Lean junk value at a boundary reference gives a negative "divergence"; shows the `dom` premise on references is load-bearing)

### Supplementary (non-blocking; failure recorded, does not block K1-K3)
- W1 `hasDerivAt_hS' (s) {x} (hx : x ∈ dom s) : HasDerivAt (hS' s) (hess s x) x`
- W2 `W_lower_bounds_hessian (s) {z w : ℝ} (hz : z ∈ dom s) (hw : z * (1 + xi s * z) ≤ w) : 1 / w ≤ hess s z`
- W3 `WEnvelope_bounds_hessian (μ) (s) (W f g : X → ℝ) (hW : WEnvelope μ s W f g) : ∀ᵐ x ∂μ, ∀ z ∈ Set.uIcc (f x) (g x), z ∈ dom s → 1 / W x ≤ hess s z`
- N1 `Phi_mem_dom (s) {z : ℝ} (hz : 0 < z) : Phi s z ∈ dom s`
- N2 `hS'_Phi (s) {z : ℝ} (hz : 0 < z) : hS' s (Phi s z) = -z`
- N3 `span_of_natural_fields {m : ℕ} (μ) (s) (φ : Fin m → X → ℝ) (β β' : Fin m → ℝ) (g k : X → ℝ) (hg : ∀ᵐ x ∂μ, 0 < ∑ j, β j * φ j x ∧ g x = Phi s (∑ j, β j * φ j x)) (hk : ∀ᵐ x ∂μ, 0 < ∑ j, β' j * φ j x ∧ k x = Phi s (∑ j, β' j * φ j x)) : ∀ᵐ x ∂μ, hS' s (k x) - hS' s (g x) = ∑ j, (β j - β' j) * φ j x`

## 3. Explicitly not targeted
- The direction-pointwise (infinitely many constraints) matching of II (29) and the Fubini reduction of I (17),(21) moments to ∫ φ f dν; K2 covers finitely many retained scores (S (A1), I (21) with finite N_Λ).
- Continuum Hessian/Taylor envelope d_h ≥ δ²/(2W) (S:76-83), (A3)/(A4), any ε certification, scientific admission.
