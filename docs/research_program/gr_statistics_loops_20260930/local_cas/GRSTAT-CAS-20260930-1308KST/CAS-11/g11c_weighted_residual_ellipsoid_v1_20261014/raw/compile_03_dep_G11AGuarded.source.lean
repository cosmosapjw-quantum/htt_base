import G11AIntegralBregman

/-!
Statistics-specialised, domain-guarded forms of the generic budget and
endpoint-limit theorems of `G11AIntegralBregman` (added after independent
review, which noted that the generic forms carry no `g ∈ dom` guard; with
Lean's `Real.log 0 = 0` a boundary reference can yield a spurious finite
value).  Here the reference is required to lie a.e. in the OPEN domain and
the argument a.e. in the closed admissible domain; nonnegativity of the
Bregman density is derived, not assumed.  `G11AIntegralBregman.lean` is
unchanged.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

namespace G11A

variable {X : Type*} [MeasurableSpace X]

/-- Finite budget with the reference in the open entropy domain. -/
theorem finite_budget_stat (μ : Measure X) (s : Stat) (f g : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    {ε : ℝ} (hε0 : 0 ≤ ε) (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε) :
    Integrable (fun x => bregDens (hS s) (hS' s) (f x) (g x)) μ ∧
      0 ≤ Dfin μ (hS s) (hS' s) f g ∧ Dfin μ (hS s) (hS' s) f g ≤ ε :=
  finite_budget μ (hS s) (hS' s) f g
    (measurable_bregDens_stat s hf hg).aestronglyMeasurable
    (by filter_upwards [hfd, hgd] with x h1 h2 using bregDens_nonneg_stat s h1 h2) hε0 hε

/-- Endpoint limit with the reference in the open domain and the limit argument
in the closed domain; the dominating function `G` remains an explicit added
premise (not stated by the source). -/
theorem integral_endpoint_limit_stat (μ : Measure X) (s : Stat) (fseq : ℕ → X → ℝ)
    (f g G : X → ℝ) (hfm : ∀ n, Measurable (fseq n)) (hf : Measurable f)
    (hgm : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hconv : ∀ᵐ x ∂μ, Tendsto (fun n => fseq n x) atTop (𝓝 (f x)))
    (hGi : Integrable G μ)
    (hdom : ∀ n, ∀ᵐ x ∂μ, ‖bregDens (hS s) (hS' s) (fseq n x) (g x)‖ ≤ G x) :
    Integrable (fun x => bregDens (hS s) (hS' s) (f x) (g x)) μ ∧
      Tendsto (fun n => Dfin μ (hS s) (hS' s) (fseq n) g) atTop
        (𝓝 (Dfin μ (hS s) (hS' s) f g)) ∧
      0 ≤ Dfin μ (hS s) (hS' s) f g := by
  obtain ⟨hi, ht⟩ := integral_endpoint_limit μ s fseq f g G hfm hf hgm hconv hGi hdom
  exact ⟨hi, ht, integral_nonneg_of_ae
    (by filter_upwards [hfd, hgd] with x h1 h2 using bregDens_nonneg_stat s h1 h2)⟩

/-- The open-domain guard excludes the boundary reference `0` used by
`junk_reference_control`. -/
theorem dom_excludes_zero (s : Stat) : (0 : ℝ) ∉ dom s := by
  intro h
  exact lt_irrefl _ (dom_pos s h).1

end G11A
