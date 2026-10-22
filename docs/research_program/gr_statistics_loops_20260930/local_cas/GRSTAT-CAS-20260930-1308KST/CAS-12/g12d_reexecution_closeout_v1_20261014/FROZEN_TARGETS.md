# G12-D re-execution closeout — FROZEN TARGETS

Frozen 2026-10-14 BEFORE any compile attempt in this unit (no `raw/compile_*` existed when this file was written).
Toolchain: Lean 4.31.0 + mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f (Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`).

## Part A — reviewed targets re-executed UNCHANGED (no edits; sha256 equality required)

| Source (copied verbatim into `lean/`) | Origin | sha256 |
|---|---|---|
| `PlanckIR.lean` | `CAS-12/c03_planck_ir_limit_v1_20261011/PlanckIR.lean` | `5ae963f5a7fd584e038856a0f3da627db6dc2b60c57b9e070fc27f67979995a3` |
| `G12DInterface.lean` | `CAS-12/g12d_uv_integrability_envelope_v1_20261011/lean/G12DInterface.lean` | `340d348ebd41799865731771c6d9cf21677af846c075292a80b510d217f5edff` |
| `G12DUVIntegrabilityEnvelope.lean` | `CAS-12/g12d_uv_integrability_envelope_v1_20261011/lean/G12DUVIntegrabilityEnvelope.lean` | `77fed344f590155fdbdb35a4bceb55b5470a2a40aa5c4bd41c2bec1f0cbc560b` |

Reviewed exact types (cited verbatim from `G12DInterface.lean`, line numbers in that file):

- A0 `CAS12PlanckIR.scaled_weight_tendsto (b : Real) (hb : 0 < b) : Filter.Tendsto (fun E : Real => E^2 * weight b E) (nhdsWithin 0 (Set.Ioi 0)) (nhds (b^(-2 : Int)))` (PlanckIR.lean:11) with `weight b E := Real.exp (b * E) / (Real.exp (b * E) - 1)^2` (PlanckIR.lean:7).
- A1 `G12D.weight_eq_occupation : weight_eq_occupation_type` (Interface:33) — `∀ b E, 0<b → 0<E → weight b E = occupation b 0 E * (1 + occupation b 0 E)`.
- A2 `G12D.weight_nonneg : weight_nonneg_type` (Interface:38).
- A3 `G12D.weight_le_inv_sq : weight_le_inv_sq_type` (Interface:41) — IR pointwise bound `weight b E ≤ 1/(bE)^2`.
- A4 `G12D.weight_le_uv_bound : weight_le_uv_bound_type` (Interface:45) — `0<b → 0<a → a≤E → weight b E ≤ exp(-(bE)) / (1-exp(-(ba)))^2`.
- A5 `G12D.weighted_power_integrable : weighted_power_integrable_type` (Interface:51) — `IntegrableOn (E^(2n+2) * weight b E) (Ioi 0)`.
- A6 `G12D.weighted_kernel_density_integrable : weighted_kernel_density_integrable_type` (Interface:57) — finite μ, a.e. `|K z| ≤ M * z.1^n`, `n:ℕ`, density form on `energyAngularMeasure μ = (volume.restrict (Ioi 0)).prod μ`.
- A7 `G12D.weighted_kernel_sq_integrable : weighted_kernel_sq_integrable_type` (Interface:68) — same class, `withDensity` form `weightedKernelMeasure b C μ` with density `C E^2 W`.
- A8 `G12D.occupation_nonneg : occupation_nonneg_type` (Interface:79).
- A9 `G12D.occupation_envelope : occupation_envelope_type` (Interface:84) — `b≤β, 0<b, η≤0, 0<E → 0 ≤ occ β η E ≤ occ b 0 E`.
- A10 `G12D.mixture_occupation_envelope : mixture_occupation_envelope_type` (Interface:90) — probability μ, a.e. `b≤β`, a.e. `η≤0`, integrability premise.
- A11 `G12D.reference_and_mixture_envelope : reference_and_mixture_envelope_type` (Interface:101).
- A12 `G12D.temperature_to_beta_bound : temperature_to_beta_bound_type` (Interface:115).
- A13 `G12D.temperature_mixture_and_reference_envelope` (Envelope:285) — a.e. `0<T s ≤ Tmax`, common `eta0 ≤ 0`, reference `inverseTemperature kB Tmax ≤ betaRef`, `etaRef ≤ 0`.

## Part B — card item coverage audit of Part A (card G12-D lean_steps L1–L5, acceptance X1–X4)

| Card item | Covered by Part A? | Gap → Part C target |
|---|---|---|
| L1 W as a real function on b>0,E>0 | YES — `CAS12PlanckIR.weight` (total real function; domain enforced by hypotheses) | — |
| L2 one-sided `lim_{E→0+} E²W = 1/b²` | YES in value `b^(-2:ℤ)` (A0) | literal `1/b^2` form: C1 (cosmetic restatement) |
| L3 explicit UV dominating bound for polynomial × exp(−bE) | PARTIAL — A4 bounds W alone; polynomial factor and integrability of the dominating function appear only inside a proof | C2, C3 |
| L4 weighted L² integrability, dν = C E² dE dΩ, bounded angular kernel × nonnegative energy power | PARTIAL — A6/A7 cover only an a.e. single monomial `M E^n`, `n:ℕ`; real nonnegative powers, bounded angular factor × power, and polynomial sums (TEFF-A4 "polynomial-energy targets") absent | C4, C5, C6, C7 |
| L5 mixture T≤Tmax, common fugacity, reference β≥b, η≤0 ⇒ both states satisfy envelope | YES — A10, A11, A13 | both-state-as-mixtures C8; (A2)-type link of envelope to W for every z between f and g: C9, C10 |
| X1 formal series vs actual limit/integrability separated | YES — A0 is an actual `Tendsto`; integrability via actual measures | — |
| X2 envelope for both f and g; keep condensate exclusion | envelope YES; condensate exclusion only implicit (η≤0 hypotheses, measure on Ioi 0) | C11, C12, negative control C13 |
| X3 final typed statements match original quantifiers/domain/measure/boundary branch | YES for Part A (reviewed) | Part C keeps the same measure `energyAngularMeasure`, same density `kernelDensity`, same `occupation`, same one-sided filter |
| X4 kernel build + #print axioms + independent fresh review | build/axioms re-executed here; fresh independent review NOT performed by this author | — (review is a separate lane) |

## Part C — NEW additive module `lean/G12DCardClosure.lean` (imports Part A unchanged; namespace `G12DClosure`)

Exact Lean signatures (verbatim from the source, frozen before compile):

```lean
def ir_limit_one_div_sq_type : Prop :=
  ∀ (b : ℝ), 0 < b →
    Tendsto (fun E : ℝ => E ^ 2 * CAS12PlanckIR.weight b E)
      (nhdsWithin 0 (Ioi 0)) (nhds (1 / b ^ 2))

def power_weight_uv_dominating_type : Prop :=
  ∀ (b a E : ℝ) (m : ℕ), 0 < b → 0 < a → a ≤ E →
    0 ≤ E ^ m * CAS12PlanckIR.weight b E ∧
      E ^ m * CAS12PlanckIR.weight b E ≤
        ((1 - Real.exp (-(b * a)))⁻¹) ^ 2 * (E ^ m * Real.exp (-(b * E)))

def uv_dominating_integrable_type : Prop :=
  ∀ (b a : ℝ) (m : ℕ), 0 < b → 0 < a →
    IntegrableOn
      (fun E : ℝ => ((1 - Real.exp (-(b * a)))⁻¹) ^ 2 * (E ^ m * Real.exp (-(b * E))))
      (Ici a) volume

def poly_envelope_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M : ℝ) (N : ℕ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ M * (1 + z.1 ^ N)) →
    Integrable (fun z => kernelDensity b C z.1 * (K z) ^ 2) (energyAngularMeasure μ) ∧
      Integrable (fun z => (K z) ^ 2) (weightedKernelMeasure b C μ)

def polynomial_sum_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C : ℝ) (s : Finset ℕ) (c : ℕ → ℝ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → (∀ k ∈ s, 0 ≤ c k) →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ ∑ k ∈ s, c k * z.1 ^ k) →
    Integrable (fun z => kernelDensity b C z.1 * (K z) ^ 2) (energyAngularMeasure μ) ∧
      Integrable (fun z => (K z) ^ 2) (weightedKernelMeasure b C μ)

def rpow_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M p : ℝ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M → 0 ≤ p →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ M * z.1 ^ p) →
    Integrable (fun z => kernelDensity b C z.1 * (K z) ^ 2) (energyAngularMeasure μ) ∧
      Integrable (fun z => (K z) ^ 2) (weightedKernelMeasure b C μ)

def angular_bounded_rpow_kernel_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M p : ℝ) (A : Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M → 0 ≤ p →
    AEStronglyMeasurable A μ →
    (∀ᵐ ω ∂μ, |A ω| ≤ M) →
    Integrable (fun z : ℝ × Ω => kernelDensity b C z.1 * (A z.2 * z.1 ^ p) ^ 2)
        (energyAngularMeasure μ) ∧
      Integrable (fun z : ℝ × Ω => (A z.2 * z.1 ^ p) ^ 2) (weightedKernelMeasure b C μ)

def two_state_mixture_envelope_type : Prop :=
  ∀ {S S' : Type u} [MeasurableSpace S] [MeasurableSpace S']
    (μf : Measure S) [IsProbabilityMeasure μf]
    (μg : Measure S') [IsProbabilityMeasure μg]
    (betaf etaf : S → ℝ) (betag etag : S' → ℝ) (b E : ℝ),
    0 < b → 0 < E →
    (∀ᵐ s ∂μf, b ≤ betaf s) → (∀ᵐ s ∂μf, etaf s ≤ 0) →
    Integrable (fun s => occupation (betaf s) (etaf s) E) μf →
    (∀ᵐ s ∂μg, b ≤ betag s) → (∀ᵐ s ∂μg, etag s ≤ 0) →
    Integrable (fun s => occupation (betag s) (etag s) E) μg →
    (0 ≤ mixtureOccupation μf betaf etaf E ∧
        mixtureOccupation μf betaf etaf E ≤ occupation b 0 E) ∧
      (0 ≤ mixtureOccupation μg betag etag E ∧
        mixtureOccupation μg betag etag E ≤ occupation b 0 E)

def between_states_weight_bound_type : Prop :=
  ∀ (b E f g z : ℝ), 0 < b → 0 < E →
    0 ≤ f → f ≤ occupation b 0 E → 0 ≤ g → g ≤ occupation b 0 E →
    min f g ≤ z → z ≤ max f g →
    z * (1 + z) ≤ CAS12PlanckIR.weight b E

def temperature_envelope_weight_type : Prop :=
  ∀ {S : Type u} [MeasurableSpace S]
    (μ : Measure S) [IsProbabilityMeasure μ] (T : S → ℝ)
    (kB Tmax eta0 betaRef etaRef : ℝ),
    0 < kB → 0 < Tmax → (∀ᵐ s ∂μ, 0 < T s ∧ T s ≤ Tmax) → eta0 ≤ 0 →
    inverseTemperature kB Tmax ≤ betaRef → etaRef ≤ 0 →
    ∀ E : ℝ, 0 < E →
    Integrable (fun s => occupation (inverseTemperature kB (T s)) eta0 E) μ →
    ∀ z : ℝ,
      min (mixtureOccupation μ (fun s => inverseTemperature kB (T s)) (fun _ => eta0) E)
          (occupation betaRef etaRef E) ≤ z →
      z ≤ max (mixtureOccupation μ (fun s => inverseTemperature kB (T s)) (fun _ => eta0) E)
          (occupation betaRef etaRef E) →
      z * (1 + z) ≤ CAS12PlanckIR.weight (inverseTemperature kB Tmax) E

def occupation_denominator_pos_type : Prop :=
  ∀ (beta eta E : ℝ), 0 < beta → eta ≤ 0 → 0 < E →
    0 < Real.exp (beta * E - eta) - 1

def no_nonpositive_energy_mass_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (b C : ℝ),
    energyAngularMeasure μ {z : ℝ × Ω | z.1 ≤ 0} = 0 ∧
      weightedKernelMeasure b C μ {z : ℝ × Ω | z.1 ≤ 0} = 0

def positive_fugacity_pole_control_type : Prop :=
  ∀ (beta eta : ℝ), 0 < beta → 0 < eta →
    (∃ E : ℝ, 0 < E ∧ Real.exp (beta * E - eta) - 1 = 0) ∧
      (∃ E : ℝ, 0 < E ∧ occupation beta eta E < 0)

```

Theorems (one per type): `G12DClosure.ir_limit_one_div_sq` (C1), `power_weight_uv_dominating` (C2),
`uv_dominating_integrable` (C3), `poly_envelope_kernel_integrable` (C4), `polynomial_sum_kernel_integrable` (C5),
`rpow_kernel_integrable` (C6), `angular_bounded_rpow_kernel_integrable` (C7), `two_state_mixture_envelope` (C8),
`between_states_weight_bound` (C9), `temperature_envelope_weight` (C10), `occupation_denominator_pos` (C11),
`no_nonpositive_energy_mass` (C12), `positive_fugacity_pole_control` (C13, negative control).

Non-vacuity witnesses: `G12DClosure.nonvacuity_constant_kernel` (constant kernel on Dirac angular measure has
finite weighted norm) and `G12DClosure.nonvacuity_temperature_instance` (all premises of C10 discharged for a
Dirac mixture; conclusion instantiated).

Scope guards (no silent strengthening):
- Quantifiers/domains match Part A: `0<b`, `0<C`, finite angular measure, a.e. bounds on the actual product
  measure, probability mixtures, a.e. `b ≤ β`, a.e. `η ≤ 0`, integrability premise retained for mixtures.
- C6/C7 allow real `p ≥ 0` (strictly weaker hypothesis than A6's `n:ℕ` monomial). C5 requires nonnegative
  coefficients (a polynomial envelope); signed polynomial kernels are covered only through |K| ≤ Σ|c_k|E^k.
- C11–C13 formalize the regular BE branch only ("no singular condensate is included", TEFF_CLAIMS.json:92):
  positive denominator for η≤0 on E>0, zero mass of {E ≤ 0} in both measures, and failure (pole + negative
  occupation) for η>0. This is NOT a physical condensate-exclusion theorem.
- `b`/`Tmax` are hypotheses; nothing is inferred from bolometric energy (card pitfall).
