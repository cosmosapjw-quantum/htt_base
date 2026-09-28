import Mathlib

/-!
Finite, model independent set and probability components of TF-S2/TF-S4.
The same-law hypothesis of TF-S4 is represented by one common measure on the
observation space. No claim about a physical data law is made here.
-/

namespace TypefreeLoop2

open MeasureTheory

theorem joint_event_subset_image_event
    {Ω Z V : Type*} (truth : Ω → Z) (C : Ω → Set Z) (ψ : Z → V) :
    {ω | truth ω ∈ C ω} ⊆ {ω | ψ (truth ω) ∈ ψ '' C ω} := by
  intro ω h
  exact ⟨truth ω, h, rfl⟩

theorem joint_coverage_le_image_coverage
    {Ω Z V : Type*} [MeasurableSpace Ω] (μ : Measure Ω) (truth : Ω → Z)
    (C : Ω → Set Z) (ψ : Z → V) :
    μ {ω | truth ω ∈ C ω} ≤
      μ {ω | ψ (truth ω) ∈ ψ '' C ω} :=
  measure_mono (joint_event_subset_image_event truth C ψ)

theorem two_cover_events_force_diameter
    {Ω V : Type*} [PseudoMetricSpace V] (A : Ω → Set V)
    (hBounded : ∀ ω, Bornology.IsBounded (A ω)) (x y : V) :
    {ω | x ∈ A ω} ∩ {ω | y ∈ A ω} ⊆
      {ω | dist x y ≤ Metric.diam (A ω)} := by
  intro ω h
  exact Metric.dist_le_diam_of_mem (hBounded ω) h.1 h.2

theorem two_cover_union_bound_real
    (α p₀ p₁ pBoth : ℝ)
    (h₀ : 1 - α ≤ p₀) (h₁ : 1 - α ≤ p₁)
    (hUnion : p₀ + p₁ ≤ 1 + pBoth) :
    1 - 2 * α ≤ pBoth := by
  linarith

/- The diagonal spectral-gap column estimate. The self-adjoint spectral
   reduction to such columns is still a differential-geometric/mathlib bridge. -/
theorem gap_column_component
    (δ ell d : ℝ) (hδ : 0 < δ) (hgap : δ ^ 2 ≤ ell ^ 2) :
    (d / ell) ^ 2 ≤ d ^ 2 / δ ^ 2 := by
  rw [div_pow]
  have hδsq : 0 < δ ^ 2 := sq_pos_of_pos hδ
  have hellsq : 0 < ell ^ 2 := lt_of_lt_of_le hδsq hgap
  apply (div_le_div_iff₀ hellsq hδsq).2
  nlinarith [mul_nonneg (sq_nonneg d) (sub_nonneg.mpr hgap)]

theorem gap_column3
    (δ ell₁ ell₂ ell₃ c d₁ d₂ d₃ : ℝ)
    (hδ : 0 < δ)
    (h₁ : δ ^ 2 ≤ ell₁ ^ 2)
    (h₂ : δ ^ 2 ≤ ell₂ ^ 2)
    (h₃ : δ ^ 2 ≤ ell₃ ^ 2) :
    c ^ 2 * ((d₁ / ell₁) ^ 2 + (d₂ / ell₂) ^ 2 + (d₃ / ell₃) ^ 2)
      ≤ c ^ 2 * ((d₁ ^ 2 + d₂ ^ 2 + d₃ ^ 2) / δ ^ 2) := by
  have hsum :
      (d₁ / ell₁) ^ 2 + (d₂ / ell₂) ^ 2 + (d₃ / ell₃) ^ 2
        ≤ d₁ ^ 2 / δ ^ 2 + d₂ ^ 2 / δ ^ 2 + d₃ ^ 2 / δ ^ 2 := by
    linarith [gap_column_component δ ell₁ d₁ hδ h₁,
      gap_column_component δ ell₂ d₂ hδ h₂,
      gap_column_component δ ell₃ d₃ hδ h₃]
  calc
    c ^ 2 * ((d₁ / ell₁) ^ 2 + (d₂ / ell₂) ^ 2 + (d₃ / ell₃) ^ 2)
        ≤ c ^ 2 * (d₁ ^ 2 / δ ^ 2 + d₂ ^ 2 / δ ^ 2 + d₃ ^ 2 / δ ^ 2) :=
          mul_le_mul_of_nonneg_left hsum (sq_nonneg c)
    _ = c ^ 2 * ((d₁ ^ 2 + d₂ ^ 2 + d₃ ^ 2) / δ ^ 2) := by ring

/- Explicit 3 by 3 trace/STF/antisymmetric Frobenius identity.
   The three antisymmetric independent entries have factor two. -/
theorem frobenius_trace_stf_antisym_3
    (k00 k01 k02 k10 k11 k12 k20 k21 k22 : ℝ) :
    let θ := k00 + k11 + k22
    θ ^ 2 / 3
      + (k00 - θ / 3) ^ 2 + (k11 - θ / 3) ^ 2
      + (k22 - θ / 3) ^ 2
      + 2 * ((k01 + k10) / 2) ^ 2
      + 2 * ((k02 + k20) / 2) ^ 2
      + 2 * ((k12 + k21) / 2) ^ 2
      + 2 * (((k01 - k10) / 2) ^ 2
            + ((k02 - k20) / 2) ^ 2
            + ((k12 - k21) / 2) ^ 2)
      = k00 ^ 2 + k01 ^ 2 + k02 ^ 2
        + k10 ^ 2 + k11 ^ 2 + k12 ^ 2
        + k20 ^ 2 + k21 ^ 2 + k22 ^ 2 := by
  dsimp
  ring

end TypefreeLoop2

#print axioms TypefreeLoop2.joint_event_subset_image_event
#print axioms TypefreeLoop2.joint_coverage_le_image_coverage
#print axioms TypefreeLoop2.two_cover_events_force_diameter
#print axioms TypefreeLoop2.two_cover_union_bound_real
#print axioms TypefreeLoop2.gap_column_component
#print axioms TypefreeLoop2.gap_column3
#print axioms TypefreeLoop2.frobenius_trace_stf_antisym_3
