import Mathlib
import PlanckIR

open MeasureTheory Set

universe u

noncomputable section
namespace G12D

def occupation (beta eta E : ℝ) : ℝ :=
  (Real.exp (beta * E - eta) - 1)⁻¹

def inverseTemperature (kB T : ℝ) : ℝ :=
  (kB * T)⁻¹

def mixtureOccupation {S : Type u} [MeasurableSpace S]
    (μ : Measure S) (beta eta : S → ℝ) (E : ℝ) : ℝ :=
  ∫ s, occupation (beta s) (eta s) E ∂μ

def energyAngularMeasure {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) : Measure (ℝ × Ω) :=
  (volume.restrict (Ioi (0 : ℝ))).prod μ

def kernelDensity (b C E : ℝ) : ℝ :=
  C * E ^ 2 * CAS12PlanckIR.weight b E

def weightedKernelMeasure {Ω : Type u} [MeasurableSpace Ω]
    (b C : ℝ) (μ : Measure Ω) : Measure (ℝ × Ω) :=
  (energyAngularMeasure μ).withDensity
    (fun z : ℝ × Ω => ENNReal.ofReal (kernelDensity b C z.1))

def weight_eq_occupation_type : Prop :=
  ∀ (b E : ℝ), 0 < b → 0 < E →
    CAS12PlanckIR.weight b E =
      occupation b 0 E * (1 + occupation b 0 E)

def weight_nonneg_type : Prop :=
  ∀ (b E : ℝ), 0 ≤ CAS12PlanckIR.weight b E

def weight_le_inv_sq_type : Prop :=
  ∀ (b E : ℝ), 0 < b → 0 < E →
    CAS12PlanckIR.weight b E ≤ 1 / (b * E) ^ 2

def weight_le_uv_bound_type : Prop :=
  ∀ (b E a : ℝ), 0 < b → 0 < a → a ≤ E →
    CAS12PlanckIR.weight b E ≤
      Real.exp (-(b * E)) /
        (1 - Real.exp (-(b * a))) ^ 2

def weighted_power_integrable_type : Prop :=
  ∀ (b : ℝ), 0 < b → ∀ (n : ℕ),
    IntegrableOn
      (fun E : ℝ => E ^ (2 * n + 2) * CAS12PlanckIR.weight b E)
      (Ioi 0) volume

def weighted_kernel_density_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M : ℝ) (n : ℕ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ M * z.1 ^ n) →
    Integrable
      (fun z => kernelDensity b C z.1 * (K z) ^ 2)
      (energyAngularMeasure μ)

def weighted_kernel_sq_integrable_type : Prop :=
  ∀ {Ω : Type u} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsFiniteMeasure μ]
    (b C M : ℝ) (n : ℕ) (K : ℝ × Ω → ℝ),
    0 < b → 0 < C → 0 ≤ M →
    AEStronglyMeasurable K (energyAngularMeasure μ) →
    (∀ᵐ z ∂energyAngularMeasure μ, |K z| ≤ M * z.1 ^ n) →
    Integrable
      (fun z => (K z) ^ 2)
      (weightedKernelMeasure b C μ)

def occupation_nonneg_type : Prop :=
  ∀ (beta eta E : ℝ),
    0 < beta → eta ≤ 0 → 0 < E →
    0 ≤ occupation beta eta E

def occupation_envelope_type : Prop :=
  ∀ (beta eta b E : ℝ),
    b ≤ beta → 0 < b → eta ≤ 0 → 0 < E →
    0 ≤ occupation beta eta E ∧
      occupation beta eta E ≤ occupation b 0 E

def mixture_occupation_envelope_type : Prop :=
  ∀ {S : Type u} [MeasurableSpace S]
    (μ : Measure S) [IsProbabilityMeasure μ]
    (beta eta : S → ℝ) (b E : ℝ),
    0 < b → 0 < E →
    (∀ᵐ s ∂μ, b ≤ beta s) →
    (∀ᵐ s ∂μ, eta s ≤ 0) →
    Integrable (fun s => occupation (beta s) (eta s) E) μ →
    0 ≤ mixtureOccupation μ beta eta E ∧
      mixtureOccupation μ beta eta E ≤ occupation b 0 E

def reference_and_mixture_envelope_type : Prop :=
  ∀ {S : Type u} [MeasurableSpace S]
    (μ : Measure S) [IsProbabilityMeasure μ]
    (beta eta : S → ℝ) (b E betaRef etaRef : ℝ),
    0 < b → 0 < E →
    (∀ᵐ s ∂μ, b ≤ beta s) →
    (∀ᵐ s ∂μ, eta s ≤ 0) →
    Integrable (fun s => occupation (beta s) (eta s) E) μ →
    b ≤ betaRef → etaRef ≤ 0 →
    0 ≤ mixtureOccupation μ beta eta E ∧
      mixtureOccupation μ beta eta E ≤ occupation b 0 E ∧
      0 ≤ occupation betaRef etaRef E ∧
      occupation betaRef etaRef E ≤ occupation b 0 E

def temperature_to_beta_bound_type : Prop :=
  ∀ (kB T Tmax : ℝ),
    0 < kB → 0 < T → T ≤ Tmax →
    0 < inverseTemperature kB Tmax ∧
      inverseTemperature kB Tmax ≤ inverseTemperature kB T

end G12D
