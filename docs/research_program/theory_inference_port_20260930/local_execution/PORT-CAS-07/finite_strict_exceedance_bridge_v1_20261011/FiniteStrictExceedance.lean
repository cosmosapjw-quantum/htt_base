import Mathlib

namespace PORTCAS07FiniteStrictExceedance

noncomputable def knownExceedance {I : Type*} [Fintype I]
    (v : I → Option ℝ) (t : ℝ) : Finset I := by
  classical
  exact Finset.univ.filter fun i => ∃ x, v i = some x ∧ t < x

noncomputable def undefinedEvent {I : Type*} [Fintype I]
    (v : I → Option ℝ) : Finset I := by
  classical
  exact Finset.univ.filter fun i => v i = none

theorem mem_knownExceedance {I : Type*} [Fintype I]
    (v : I → Option ℝ) (t : ℝ) (i : I) :
    i ∈ knownExceedance v t ↔ ∃ x, v i = some x ∧ t < x := by
  classical
  simp [knownExceedance]

theorem threshold_equality_excluded {I : Type*} [Fintype I]
    (v : I → Option ℝ) (t : ℝ) (i : I) (hi : v i = some t) :
    i ∉ knownExceedance v t := by
  rw [mem_knownExceedance]
  simp [hi]

theorem known_undefined_disjoint {I : Type*} [Fintype I]
    (v : I → Option ℝ) (t : ℝ) :
    Disjoint (knownExceedance v t) (undefinedEvent v) := by
  classical
  apply Finset.disjoint_left.mpr
  intro i hi hu
  obtain ⟨x, hx, _⟩ := (mem_knownExceedance v t i).mp hi
  have hn : v i = none := by simpa [undefinedEvent] using hu
  rw [hn] at hx
  cases hx

theorem finite_strict_exceedance_bounds {I : Type*} [Fintype I] [DecidableEq I]
    (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (v : I → Option ℝ) (t : ℝ)
    (E : Finset I) (hKnown : knownExceedance v t ⊆ E)
    (hCompletion : E ⊆ knownExceedance v t ∪ undefinedEvent v) :
    (∑ i ∈ knownExceedance v t, w i) ≤ (∑ i ∈ E, w i) ∧
      (∑ i ∈ E, w i) ≤
        (∑ i ∈ knownExceedance v t, w i) + (∑ i ∈ undefinedEvent v, w i) := by
  constructor
  · exact Finset.sum_le_sum_of_subset_of_nonneg hKnown (fun i _ _ => hw i)
  · calc
      (∑ i ∈ E, w i) ≤
          ∑ i ∈ knownExceedance v t ∪ undefinedEvent v, w i :=
        Finset.sum_le_sum_of_subset_of_nonneg hCompletion (fun i _ _ => hw i)
      _ = (∑ i ∈ knownExceedance v t, w i) +
          (∑ i ∈ undefinedEvent v, w i) :=
        Finset.sum_union (known_undefined_disjoint v t)

end PORTCAS07FiniteStrictExceedance

#print axioms PORTCAS07FiniteStrictExceedance.threshold_equality_excluded
#print axioms PORTCAS07FiniteStrictExceedance.finite_strict_exceedance_bounds
