# G10-D frozen targets (written before any proof compile)

Origin: authored fresh in this run (directory T did not exist when this author started).
Frozen 2026-10-14 (UTC 2026-10-13 ~21:50) after only the five unchanged reused import modules had
been compiled (receipts compile_01..05, sources byte-identical to the reviewed originals) and
before any compile of `lean/G10DTwoPoint.lean` or of any probe.

Toolchain: Lean 4.31.0, mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f
(`/home/cosmosapjw/lean_oracles/viii_oracle`). Module `G10DTwoPoint`, namespace `G10D`.
Imports: `Mathlib`, `G10BGaussianKL` (reviewed G10-B, unchanged), `G10CSmoothCutoff`
(reviewed G10-C, unchanged); transitively `CAS10C01`, `CAS10C03`, `P12GaussianLaw` (unchanged).

## Original statements (see SOURCE_RECOVERY.md for file:line)

* Card G10-D scope: two-point probability conclusion of the original cutout / morphology
  non-identifiability. lean_steps: (1) state the two actual admissible models, target separation,
  estimator measurability and loss metric; (2) triangle inequality => simultaneous small-error
  events incompatible; (3) connect equal-law or TV/KL bound to the original testing inequality;
  (4) package the union / two-point probability lower bound with a quantifier over all measurable
  estimators. Pitfalls: do not give a KL constant without a testing bound; do not change the
  loss/target metric for proof convenience.
* ILT §6 Corollary (I15) (INFORMATION_LIMIT_THEOREMS.md:180-191): `θ0, θ1` with
  `d(θ0,θ1) = D > 0`; complete data laws identical; a random set `C` with coverage `≥ 1-α` at each
  point, `0 ≤ α < 1/2`; then under the common law `P{diam_d C ≥ D} ≥ 1-2α` and
  `E[diam_d C] ≥ (1-2α) D`; every point estimator has `max_i E_i d(θ̂,θ_i) ≥ D/2`.
  Instances: intercept dipoles `D = sinh δ ≥ δ`; source rapidity `D = δ`.
* ILT Theorem III (I11)-(I14) (lines 135-178), accepted as STAT-INFO-4: the two smooth future unit
  test fields `u0 = o`, `u1 = (cosh χ, sinh χ, 0, 0)`, `χ = δ q(|x|)`, `δ = min(1,Ma²)/25`; exact
  exterior data agree for every direction and `r ≥ a`; `|∂_r²(1+z)| ≤ M` along all rays including
  `0 ≤ r < a`; source values differ by rapidity `δ`, intercept dipoles by `sinh δ e_x`.
* ILT Theorem II (lines 109-127), accepted as STAT-INFO-3 / G10-B: compressed laws equal; every
  powers-only randomized test has equal rejection probability; full KL `225H²/(64σ_p²)`.

## Encoding decisions (stated, not hidden)

* Diameter: `Metric.ediam` (`ℝ≥0∞`-valued; `= ⊤` for unbounded sets). Mathlib's real
  `Metric.diam` is `0` on unbounded sets and would falsify the source meaning (negative control N3).
  The separation `D` enters as `ENNReal.ofReal (dist θ0 θ1)` (= `edist θ0 θ1`).
* Probabilities: `P.real s = (P s).toReal` (outer measure for non-measurable `s`). Coverage events
  `{ω | θi ∈ C ω}` are assumed measurable (card: "event measurability"). The conclusion is also
  given as an inner bound: a measurable subset of `{diam ≥ D}` of probability `≥ 1-2α`.
* "Complete data laws identical" is the hypothesis `P0 = P1` in the generic theorems; for the
  cutout it is *derived* (C5) from equality of exterior data for any observation model
  `obs : ExtData → Measure Ω` (an arbitrary map from the exterior data, which covers sampling,
  noise and nuisance integrated out with a common distribution); for the morphology pair it is
  G10-B A3 (compressed laws equal).
* `α`: the source's range `0 ≤ α < 1/2` is NOT assumed; the theorems hold for every real `α`
  (weaker hypotheses). `D > 0` is likewise not assumed in the generic theorems.
* Estimators: deterministic measurable `θ̂ : Ω → Θ` (`Θ` pseudo-metric with
  `[MeasurableSpace Θ] [OpensMeasurableSpace Θ]`); randomized estimators via Mathlib
  `ProbabilityTheory.minimaxRisk` (infimum over all Markov kernels `Ω → Θ`). Loss = the source's
  metric `d` (as `edist`), unchanged.
* Spacetime for the cutout: fixed Minkowski, signature (-+++), observer `o = (1,0,0,0)` at the origin,
  past ray `K = (-1, n)`; fields are stationary so a field is a map `E3 → (Fin 4 → ℝ)` of the
  spatial point (`E3 := EuclideanSpace ℝ (Fin 3)`); the emitter on the ray at affine distance `r`
  is the spatial point `r • n`. `1+z := g(K,u(r n)) / g(K,o)` with `g(v,w) = -v0 w0 + Σ vi wi`.
  Area distance: flat optical propagation in the fixed metric gives `d_A = r` for both fields
  (field independent); it enters the exterior data as the second component `r`.
* Cutoff `q := G10C.smoothCutoff a ρ` for an arbitrary `ρ` with `G10C.IsMollifier a ρ` (reused).
* Source value targets: rapidity `sourceRapidity u := arsinh (u 0 1)` on `ℝ` with `|·|`; intercept
  dipole `interceptDipole u := toLp 2 ![u 0 1, u 0 2, u 0 3] : E3` with Euclidean distance.
  The Lorentz-invariant relative rapidity is checked separately (C4: `-g(u1(0),u0(0)) = cosh δ`).
* Morphology target: the source fixes no estimation metric for the morphology pair; generic
  targets `θ0, θ1` in any pseudo-metric space are allowed, and the slope dipole
  `p ∈ E3` (Euclidean distance) is used as a worked instance (M2s/M4), labelled as such.

## Lean signatures

```lean
import Mathlib
import G10BGaussianKL
import G10CSmoothCutoff
open MeasureTheory ProbabilityTheory InformationTheory Real Set Filter Topology
open scoped ENNReal NNReal
namespace G10D
variable {Ω Θ : Type*} [MeasurableSpace Ω] [PseudoMetricSpace Θ]
```

### G — generic two-point bounds

| id | name | statement |
|---|---|---|
| G1 | `union_bound_both` | `(P : Measure Ω) [IsProbabilityMeasure P] {E₀ E₁ : Set Ω} (h₀ : MeasurableSet E₀) (h₁ : MeasurableSet E₁) (α : ℝ) (c₀ : 1 - α ≤ P.real E₀) (c₁ : 1 - α ≤ P.real E₁) : 1 - 2 * α ≤ P.real (E₀ ∩ E₁)` |
| G2 | `dist_le_ediam_of_mem` | `{S : Set Θ} {θ₀ θ₁ : Θ} (h₀ : θ₀ ∈ S) (h₁ : θ₁ ∈ S) : ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam S` |
| G3 | `confidence_set_floor` | `(P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] (hlaw : P₀ = P₁) (C : Ω → Set Θ) (θ₀ θ₁ : Θ) (α : ℝ) (hm₀ : MeasurableSet {ω \| θ₀ ∈ C ω}) (hm₁ : MeasurableSet {ω \| θ₁ ∈ C ω}) (hcov₀ : 1 - α ≤ P₀.real {ω \| θ₀ ∈ C ω}) (hcov₁ : 1 - α ≤ P₁.real {ω \| θ₁ ∈ C ω}) : (∃ S, MeasurableSet S ∧ S ⊆ {ω \| ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam (C ω)} ∧ 1 - 2 * α ≤ P₀.real S) ∧ 1 - 2 * α ≤ P₀.real {ω \| ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam (C ω)}` |
| G4 | `expected_diam_floor` | same hypotheses as G3 : `ENNReal.ofReal ((1 - 2 * α) * dist θ₀ θ₁) ≤ ∫⁻ ω, Metric.ediam (C ω) ∂P₀` |
| G5 | `small_errors_incompatible` | `(θ₀ θ₁ y : Θ) (h₀ : dist y θ₀ < dist θ₀ θ₁ / 2) (h₁ : dist y θ₁ < dist θ₀ θ₁ / 2) : False` |
| G6 | `estimator_two_point_prob` | `[MeasurableSpace Θ] [OpensMeasurableSpace Θ] (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] (hlaw : P₀ = P₁) (θhat : Ω → Θ) (hθ : Measurable θhat) (θ₀ θ₁ : Θ) : 1 ≤ P₀.real {ω \| dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀} + P₁.real {ω \| dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁} ∧ 1 / 2 ≤ max (P₀.real {ω \| dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀}) (P₁.real {ω \| dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁})` |
| G7 | `estimator_risk_floor` | `[MeasurableSpace Θ] [OpensMeasurableSpace Θ] (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] (hlaw : P₀ = P₁) (θhat : Ω → Θ) (hθ : Measurable θhat) (θ₀ θ₁ : Θ) : ENNReal.ofReal (dist θ₀ θ₁) ≤ (∫⁻ ω, edist (θhat ω) θ₀ ∂P₀) + ∫⁻ ω, edist (θhat ω) θ₁ ∂P₁ ∧ ENNReal.ofReal (dist θ₀ θ₁ / 2) ≤ max (∫⁻ ω, edist (θhat ω) θ₀ ∂P₀) (∫⁻ ω, edist (θhat ω) θ₁ ∂P₁)` |
| G8 | `minimaxRisk_two_point` | `[MeasurableSpace Θ] [OpensMeasurableSpace Θ] (P : Kernel (Fin 2) Ω) [IsMarkovKernel P] (hlaw : P 0 = P 1) (θ : Fin 2 → Θ) : ENNReal.ofReal (dist (θ 0) (θ 1) / 2) ≤ minimaxRisk (fun i y => edist y (θ i)) P` (all randomized Markov-kernel estimators) |

### K — KL/TV route to a testing bound (Bretagnolle–Huber, self-proved; absent at the pin)

| id | name | statement |
|---|---|---|
| K1 | `klDiv_restrict_add_compl` | `{α : Type*} [MeasurableSpace α] (μ ν : Measure α) [IsFiniteMeasure μ] [IsFiniteMeasure ν] (hac : μ ≪ ν) {A : Set α} (hA : MeasurableSet A) : klDiv μ ν = klDiv (μ.restrict A) (ν.restrict A) + klDiv (μ.restrict Aᶜ) (ν.restrict Aᶜ)` |
| K2 | `binary_kl_le_klDiv` | `(μ ν : Measure α) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν] {A : Set α} (hA : MeasurableSet A) : ENNReal.ofReal (μ.real A * log (μ.real A / ν.real A) + μ.real Aᶜ * log (μ.real Aᶜ / ν.real Aᶜ)) ≤ klDiv μ ν` (two-cell data processing) |
| K3 | `bh_real` | `(x y K : ℝ) (hx0 : 0 ≤ x) (hx1 : x ≤ 1) (hy0 : 0 ≤ y) (hy1 : y ≤ 1) (h0 : y = 0 → x = 0) (h1 : y = 1 → x = 1) (hK0 : 0 ≤ K) (hK : x * log (x / y) + (1 - x) * log ((1 - x) / (1 - y)) ≤ K) : 1 / 2 * exp (-K) ≤ x + (1 - y)` |
| K4 | `bretagnolle_huber` | `(μ ν : Measure α) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν] {A : Set α} (hA : MeasurableSet A) (K : ℝ) (hK0 : 0 ≤ K) (hK : klDiv μ ν ≤ ENNReal.ofReal K) : 1 / 2 * exp (-K) ≤ μ.real A + ν.real Aᶜ` |
| K5 | `estimator_two_point_kl` | `[MeasurableSpace Θ] [OpensMeasurableSpace Θ] (P₀ P₁ : Measure Ω) [IsProbabilityMeasure P₀] [IsProbabilityMeasure P₁] (K : ℝ) (hK0 : 0 ≤ K) (hK : klDiv P₀ P₁ ≤ ENNReal.ofReal K) (θhat : Ω → Θ) (hθ : Measurable θhat) (θ₀ θ₁ : Θ) : 1 / 2 * exp (-K) ≤ P₀.real {ω \| dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₀} + P₁.real {ω \| dist θ₀ θ₁ / 2 ≤ dist (θhat ω) θ₁}` |

### M — morphology pair (G10-B laws; `open G10BGaussianKL`)

`lawFirst H z0 m z1 t σ := obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ`,
`lawSecond ... := obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ` (abbrevs).
`slopeFirst H : E3 := WithLp.toLp 2 (CAS10C03.p H)`, `slopeSecond H := WithLp.toLp 2 (CAS10C03.pPrime H)`.

| id | name | statement |
|---|---|---|
| M1 | `morph_powers_test_errors` | `(H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ) (φ : (Fin 5 → ℝ) → ℝ) (hφ : Measurable φ) (h01 : ∀ y, 0 ≤ φ y ∧ φ y ≤ 1) : (∫ x, φ (powers blockDim x) ∂(lawFirst H z0 m z1 t σ)) + ∫ x, (1 - φ (powers blockDim x)) ∂(lawSecond H z0 m z1 t σ) = 1` (type I + type II = 1 for every powers-only randomized test) |
| M2 | `morph_confidence_floor` | `(H z0 m z1 t σ) (θ₀ θ₁ : Θ) (C : (Fin 5 → ℝ) → Set Θ) (α : ℝ) (hm₀ : MeasurableSet {y \| θ₀ ∈ C y}) (hm₁ : MeasurableSet {y \| θ₁ ∈ C y}) (hcov₀ : 1 - α ≤ ((lawFirst H z0 m z1 t σ).map (powers blockDim)).real {y \| θ₀ ∈ C y}) (hcov₁ : 1 - α ≤ ((lawSecond H z0 m z1 t σ).map (powers blockDim)).real {y \| θ₁ ∈ C y}) : 1 - 2 * α ≤ ((lawFirst ..).map (powers blockDim)).real {y \| ENNReal.ofReal (dist θ₀ θ₁) ≤ Metric.ediam (C y)} ∧ ENNReal.ofReal ((1 - 2 * α) * dist θ₀ θ₁) ≤ ∫⁻ y, Metric.ediam (C y) ∂((lawFirst ..).map (powers blockDim))` |
| M2s | `slope_separation` | `(H : ℝ) : dist (slopeFirst H) (slopeSecond H) = 15 * √2 * \|H\| / 8` |
| M3 | `morph_estimator_floor` | `[MeasurableSpace Θ] [OpensMeasurableSpace Θ] (H z0 m z1 t σ) (g : (Fin 5 → ℝ) → Θ) (hg : Measurable g) (θ₀ θ₁ : Θ) : ENNReal.ofReal (dist θ₀ θ₁ / 2) ≤ max (∫⁻ y, edist (g y) θ₀ ∂((lawFirst ..).map (powers blockDim))) (∫⁻ y, edist (g y) θ₁ ∂((lawSecond ..).map (powers blockDim)))` (all measurable powers-only estimators) |
| M4 | `morph_full_data_test_bound` | `(H z0 m z1 t σ) (hσ : ∀ j, 0 < σ j) {A : Set Obs} (hA : MeasurableSet A) : 1 / 2 * exp (-(225 * H ^ 2 / (64 * σ 3 ^ 2))) ≤ (lawFirst H z0 m z1 t σ).real A + (lawSecond H z0 m z1 t σ).real Aᶜ` (full data: KL constant connected to a testing bound) |
| M4e | `morph_full_data_slope_estimator` | `(H z0 m z1 t σ) (hσ) (g : Obs → E3) (hg : Measurable g) : 1 / 2 * exp (-(225 * H ^ 2 / (64 * σ 3 ^ 2))) ≤ (lawFirst ..).real {x \| 15 * √2 * \|H\| / 8 / 2 ≤ dist (g x) (slopeFirst H)} + (lawSecond ..).real {x \| 15 * √2 * \|H\| / 8 / 2 ≤ dist (g x) (slopeSecond H)}` |

### C — cutout pair (Theorem III fields; `G10C` cutoff reused)

```lean
abbrev E3 := EuclideanSpace ℝ (Fin 3)
def mink (v w : Fin 4 → ℝ) : ℝ := -(v 0 * w 0) + v 1 * w 1 + v 2 * w 2 + v 3 * w 3
def obsVec : Fin 4 → ℝ := ![1, 0, 0, 0]
def Kray (n : E3) : Fin 4 → ℝ := ![-1, n 0, n 1, n 2]
noncomputable def onePlusZ (u : E3 → Fin 4 → ℝ) (r : ℝ) (n : E3) : ℝ :=
  mink (Kray n) (u (r • n)) / mink (Kray n) obsVec
def u0 : E3 → Fin 4 → ℝ := fun _ => obsVec
noncomputable def chi (a : ℝ) (ρ : ℝ → ℝ) (δ : ℝ) (x : E3) : ℝ := δ * G10C.smoothCutoff a ρ ‖x‖
noncomputable def u1 (a : ℝ) (ρ : ℝ → ℝ) (δ : ℝ) (x : E3) : Fin 4 → ℝ :=
  ![cosh (chi a ρ δ x), sinh (chi a ρ δ x), 0, 0]
noncomputable def deltaOf (M a : ℝ) : ℝ := min 1 (M * a ^ 2) / 25
noncomputable def sourceRapidity (u : E3 → Fin 4 → ℝ) : ℝ := arsinh (u 0 1)
def interceptDipole (u : E3 → Fin 4 → ℝ) : E3 := WithLp.toLp 2 ![u 0 1, u 0 2, u 0 3]
def ExtData (a : ℝ) := Set.Ici a → Metric.sphere (0 : E3) 1 → ℝ × ℝ
noncomputable def extData (u : E3 → Fin 4 → ℝ) (a : ℝ) : ExtData a :=
  fun r n => (onePlusZ u r n, (r : ℝ))
```

| id | name | statement |
|---|---|---|
| C1 | `u0_future_unit`, `u1_future_unit` | `(x : E3) : mink (u0 x) (u0 x) = -1 ∧ 0 < u0 x 0`; `(a ρ δ) (x : E3) : mink (u1 a ρ δ x) (u1 a ρ δ x) = -1 ∧ 0 < u1 a ρ δ x 0` |
| C1s | `u1_contDiff`, `u0_contDiff` | `(ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) : ContDiff ℝ (⊤ : ℕ∞) (u1 a ρ δ)`; `ContDiff ℝ (⊤ : ℕ∞) u0` |
| C2 | `onePlusZ_u1_ray` | `(a ρ δ) {n : E3} (hn : ‖n‖ = 1) {r : ℝ} (hr : 0 ≤ r) : onePlusZ (u1 a ρ δ) r n = cosh (δ * G10C.smoothCutoff a ρ r) + n 0 * sinh (δ * G10C.smoothCutoff a ρ r)` (source's `Z_1`) |
| C3 | `exterior_redshift_agree` | `(ha) (hρ) (δ) {n : E3} (hn : ‖n‖ = 1) {r : ℝ} (hr : a ≤ r) : onePlusZ (u1 a ρ δ) r n = 1 ∧ onePlusZ u0 r n = 1` |
| C3e | `extData_eq` | `(ha) (hρ) (δ) : extData (u1 a ρ δ) a = extData u0 a` |
| C3l | `cutout_laws_identical` | `(ha) (hρ) (δ) {Ω} [MeasurableSpace Ω] (obs : ExtData a → Measure Ω) : obs (extData u0 a) = obs (extData (u1 a ρ δ) a)` |
| C4a | `ray_second_deriv_I13` | `(ha) (hρ) {δ : ℝ} (hδ : 0 ≤ δ) {n : E3} (hn : ‖n‖ = 1) {r : ℝ} (hr : 0 ≤ r) : \|deriv (deriv (fun s => onePlusZ (u1 a ρ δ) s n)) r\| ≤ exp δ / a ^ 2 * (40 / √3 * δ + 225 / 16 * δ ^ 2)` |
| C4b | `I14_bound` | `(ha : 0 < a) {M : ℝ} (hM : 0 < M) : exp (deltaOf M a) / a ^ 2 * (40 / √3 * deltaOf M a + 225 / 16 * deltaOf M a ^ 2) ≤ 1147 / 1152 * M` |
| C4 | `ray_second_deriv_bound` | `(ha) (hρ) {M} (hM : 0 < M) {n : E3} (hn : ‖n‖ = 1) {r} (hr : 0 ≤ r) : \|deriv (deriv (fun s => onePlusZ (u1 a ρ (deltaOf M a)) s n)) r\| ≤ M` and `ray_second_deriv_bound_u0 : (hM : 0 ≤ M) (n r) : \|deriv (deriv (fun s => onePlusZ u0 s n)) r\| ≤ M` |
| C5 | `u1_origin`, `relative_lorentz_factor`, `deltaOf_pos` | `u1 a ρ δ 0 = ![cosh δ, sinh δ, 0, 0]` (ha hρ); `-mink (u1 a ρ δ 0) (u0 0) = cosh δ` (ha hρ); `(ha) (hM) : 0 < deltaOf M a` |
| C5r | `rapidity_separation` | `(ha) (hρ) (δ) : dist (sourceRapidity (u1 a ρ δ)) (sourceRapidity u0) = \|δ\|` |
| C5d | `dipole_separation` | `(ha) (hρ) {δ} (hδ : 0 ≤ δ) : dist (interceptDipole (u1 a ρ δ)) (interceptDipole u0) = sinh δ ∧ δ ≤ sinh δ` |
| C6r | `cutout_rapidity_floor` | `(ha) (hρ) {M} (hM) {Ω} [MeasurableSpace Ω] (obs : ExtData a → Measure Ω) [IsProbabilityMeasure (obs (extData u0 a))] (C : Ω → Set ℝ) (α : ℝ)` with `δ := deltaOf M a`, measurable coverage events, `hcov₀ : 1 - α ≤ (obs (extData u0 a)).real {ω \| sourceRapidity u0 ∈ C ω}`, `hcov₁ : 1 - α ≤ (obs (extData (u1 a ρ δ) a)).real {ω \| sourceRapidity (u1 a ρ δ) ∈ C ω}` : `1 - 2 * α ≤ (obs (extData u0 a)).real {ω \| ENNReal.ofReal δ ≤ Metric.ediam (C ω)} ∧ ENNReal.ofReal ((1 - 2 * α) * δ) ≤ ∫⁻ ω, Metric.ediam (C ω) ∂(obs (extData u0 a))` |
| C6d | `cutout_dipole_floor` | same with `C : Ω → Set E3`, targets `interceptDipole u0`, `interceptDipole (u1 a ρ δ)`, separation `sinh δ` |
| C6e | `cutout_estimator_floor` | `(ha) (hρ) (hM) (obs) [IsProbabilityMeasure (obs (extData u0 a))] (g : Ω → E3) (hg : Measurable g) : ENNReal.ofReal (sinh δ / 2) ≤ max (∫⁻ ω, edist (g ω) (interceptDipole u0) ∂(obs (extData u0 a))) (∫⁻ ω, edist (g ω) (interceptDipole (u1 a ρ δ)) ∂(obs (extData (u1 a ρ δ) a)))`, and `cutout_rapidity_estimator_floor` (g : Ω → ℝ, separation `δ`) |
| C7 | `g10d_cutout_main` | `(ha : 0 < a) {M} (hM : 0 < M) : ∃ ρ, G10C.IsMollifier a ρ ∧ 0 < deltaOf M a ∧ ContDiff ℝ ⊤ (u1 a ρ (deltaOf M a)) ∧ (∀ x, mink (u1 ..x) (u1 ..x) = -1 ∧ 0 < u1 .. x 0) ∧ extData (u1 a ρ (deltaOf M a)) a = extData u0 a ∧ (∀ n, ‖n‖ = 1 → ∀ r, 0 ≤ r → \|deriv (deriv (fun s => onePlusZ (u1 ..) s n)) r\| ≤ M) ∧ dist (sourceRapidity (u1 ..)) (sourceRapidity u0) = deltaOf M a ∧ dist (interceptDipole (u1 ..)) (interceptDipole u0) = sinh (deltaOf M a)` |

### N — negative controls / non-vacuity

| id | name | statement |
|---|---|---|
| N1 | `law_equality_needed` | `∃ (P₀ P₁ : Measure ℝ), IsProbabilityMeasure P₀ ∧ IsProbabilityMeasure P₁ ∧ ∃ C : ℝ → Set ℝ, P₀.real {ω \| (0:ℝ) ∈ C ω} = 1 ∧ P₁.real {ω \| (1:ℝ) ∈ C ω} = 1 ∧ P₀.real {ω \| ENNReal.ofReal (dist (0:ℝ) 1) ≤ Metric.ediam (C ω)} = 0` (without equal laws the floor fails) |
| N2 | `coverage_satisfiable` | `(P : Measure Ω) [IsProbabilityMeasure P] (θ₀ θ₁ : Θ) : P.real {ω \| θ₀ ∈ (fun _ : Ω => ({θ₀, θ₁} : Set Θ)) ω} = 1 ∧ P.real {ω \| θ₁ ∈ (fun _ : Ω => ({θ₀, θ₁} : Set Θ)) ω} = 1` |
| N3 | `diam_vs_ediam_unbounded` | `Metric.diam (Set.univ : Set ℝ) = 0 ∧ Metric.ediam (Set.univ : Set ℝ) = ⊤` (why `ediam` is the faithful diameter) |
| N4 | `u1_ne_u0` | `(ha) (hρ) (hM : 0 < M) : u1 a ρ (deltaOf M a) ≠ u0` (cutout pair is a genuine pair) |
| N5 | `morph_full_laws_differ` | re-export of G10-B A7 for H ≠ 0 (full laws differ; equality only after compression) |

## Not targeted (out of scope)

* Physical admissibility of the morphology tuples (C01/C02/G10-A own that), real-survey
  equal law, masks, anisotropic covariance, priors; minimax sharpness; uniform consistency.
* Einstein–matter closure of the cutout fields (they are test congruences in fixed Minkowski,
  as in the source); the comoving-receiver variant.
* Any statement that the bounds are tight, or any numeric uncertainty for a real catalogue.
* Scientific admission (always HOLD).
