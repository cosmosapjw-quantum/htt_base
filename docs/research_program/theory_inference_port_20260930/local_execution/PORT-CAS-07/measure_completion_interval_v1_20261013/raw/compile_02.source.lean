import Mathlib

/-!
# P07-A: strict exceedance interval preserving undefined atoms

`D` is the (measurable) defined region; its complement `Dᶜ` carries the
undefined atoms.  A completion `g'` is any measurable real function agreeing
with `g` on `D`.  The strict event `{t < g'}` then has mass in the interval
`[μ (D ∩ {t < g}), μ (D ∩ {t < g}) + μ Dᶜ]`, and both endpoints are attained.
Intermediate values are NOT claimed (false in general with atoms).
-/

open MeasureTheory

namespace P07MeasureExceedance

variable {Ω : Type*} [MeasurableSpace Ω]

/-- A completion of `g` off the defined region `D`. -/
def IsCompletion (D : Set Ω) (g g' : Ω → ℝ) : Prop :=
  Measurable g' ∧ ∀ ω ∈ D, g' ω = g ω

/-- Target 1: every completion lies in the closed interval. -/
theorem completion_bounds (μ : Measure Ω) (D : Set Ω) (g : Ω → ℝ) (t : ℝ)
    (hD : MeasurableSet D) (hg : Measurable g) (g' : Ω → ℝ)
    (hc : IsCompletion D g g') :
    -- `hD`, `hg` are part of the frozen context; the bounds do not need them.
    μ (D ∩ {ω | t < g ω}) ≤ μ {ω | t < g' ω} ∧
      μ {ω | t < g' ω} ≤ μ (D ∩ {ω | t < g ω}) + μ Dᶜ := by
  obtain ⟨_, hagree⟩ := hc
  constructor
  · apply measure_mono
    rintro ω ⟨hωD, hωt⟩
    show t < g' ω
    rw [hagree ω hωD]
    exact hωt
  · calc
      μ {ω | t < g' ω} ≤ μ ((D ∩ {ω | t < g ω}) ∪ Dᶜ) := by
        apply measure_mono
        intro ω hω
        by_cases hωD : ω ∈ D
        · left
          refine ⟨hωD, ?_⟩
          show t < g ω
          rw [← hagree ω hωD]
          exact hω
        · right
          exact hωD
      _ ≤ μ (D ∩ {ω | t < g ω}) + μ Dᶜ := measure_union_le _ _

/-- Target 2: the lower endpoint is attained (undefined atoms set to `t`). -/
theorem lower_attained (μ : Measure Ω) (D : Set Ω) (g : Ω → ℝ) (t : ℝ)
    (hD : MeasurableSet D) (hg : Measurable g) :
    ∃ g', IsCompletion D g g' ∧
      μ {ω | t < g' ω} = μ (D ∩ {ω | t < g ω}) := by
  classical
  refine ⟨D.piecewise g (fun _ => t), ⟨hg.piecewise hD measurable_const, ?_⟩, ?_⟩
  · intro ω hω
    exact Set.piecewise_eq_of_mem D g (fun _ => t) hω
  · congr 1
    ext ω
    by_cases hωD : ω ∈ D
    · simp [hωD]
    · simp [hωD]

/-- Target 3: the upper endpoint is attained (undefined atoms set to `t + 1`). -/
theorem upper_attained (μ : Measure Ω) (D : Set Ω) (g : Ω → ℝ) (t : ℝ)
    (hD : MeasurableSet D) (hg : Measurable g) :
    ∃ g', IsCompletion D g g' ∧
      μ {ω | t < g' ω} = μ (D ∩ {ω | t < g ω}) + μ Dᶜ := by
  classical
  refine ⟨D.piecewise g (fun _ => t + 1),
    ⟨hg.piecewise hD measurable_const, ?_⟩, ?_⟩
  · intro ω hω
    exact Set.piecewise_eq_of_mem D g (fun _ => t + 1) hω
  · have hset : {ω | t < D.piecewise g (fun _ => t + 1) ω} =
        (D ∩ {ω | t < g ω}) ∪ Dᶜ := by
      ext ω
      by_cases hωD : ω ∈ D
      · simp [hωD]
      · simp [hωD]
    rw [hset]
    apply measure_union _ hD.compl
    rw [Set.disjoint_left]
    rintro ω ⟨hωD, _⟩ hωc
    exact hωc hωD

omit [MeasurableSpace Ω] in
/-- Target 4: threshold equality is excluded from the strict known event. -/
theorem threshold_equality_excluded (D : Set Ω) (g : Ω → ℝ) (t : ℝ) :
    ∀ ω ∈ D, g ω = t → ω ∉ D ∩ {ω | t < g ω} := by
  rintro ω _ hgt ⟨_, hlt⟩
  have hlt' : t < g ω := hlt
  rw [hgt] at hlt'
  exact lt_irrefl t hlt'

/-- Target 5: under a probability measure the interval lies in `[0, 1]`. -/
theorem probability_range (μ : Measure Ω) [IsProbabilityMeasure μ]
    (D : Set Ω) (g : Ω → ℝ) (t : ℝ)
    (hD : MeasurableSet D) (hg : Measurable g) (g' : Ω → ℝ)
    (hc : IsCompletion D g g') :
    μ {ω | t < g' ω} ≤ 1 ∧ μ (D ∩ {ω | t < g ω}) + μ Dᶜ ≤ 1 := by
  obtain ⟨g'', _, hup⟩ := upper_attained μ D g t hD hg
  have _hb := completion_bounds μ D g t hD hg g' hc
  exact ⟨prob_le_one, hup ▸ prob_le_one⟩

end P07MeasureExceedance
