import Mathlib

open Set

theorem contDiffOn_three_of_chain {f f1 f2 f3 : ℝ → ℝ} {U : Set ℝ} (hU : IsOpen U)
    (h : ∀ y ∈ U, HasDerivAt f (f1 y) y ∧ HasDerivAt f1 (f2 y) y ∧ HasDerivAt f2 (f3 y) y)
    (hc : ContinuousOn f3 U) : ContDiffOn ℝ 3 f U := by
  have nω : ∀ k : ℕ, ¬ (((k : ℕ) : WithTop ℕ∞) = ⊤) := fun k => WithTop.natCast_ne_top k
  have d2 : ContDiffOn ℝ 1 f2 U := by
    have e : (1 : WithTop ℕ∞) = ((0 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
    rw [e, contDiffOn_succ_iff_deriv_of_isOpen hU]
    refine ⟨fun y hy => (h y hy).2.2.differentiableAt.differentiableWithinAt,
      fun hh => absurd hh (nω 0), ?_⟩
    have h3 : ContDiffOn ℝ ((0 : ℕ) : WithTop ℕ∞) f3 U := by rw [Nat.cast_zero, contDiffOn_zero]; exact hc
    exact h3.congr fun y hy => (h y hy).2.2.deriv
  have d1 : ContDiffOn ℝ 2 f1 U := by
    have e : (2 : WithTop ℕ∞) = ((1 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
    rw [e, contDiffOn_succ_iff_deriv_of_isOpen hU]
    refine ⟨fun y hy => (h y hy).2.1.differentiableAt.differentiableWithinAt,
      fun hh => absurd hh (nω 1), ?_⟩
    exact (by simpa using d2 : ContDiffOn ℝ ((1 : ℕ) : WithTop ℕ∞) f2 U).congr
      fun y hy => (h y hy).2.1.deriv
  have e : (3 : WithTop ℕ∞) = ((2 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
  rw [e, contDiffOn_succ_iff_deriv_of_isOpen hU]
  refine ⟨fun y hy => (h y hy).1.differentiableAt.differentiableWithinAt,
    fun hh => absurd hh (nω 2), ?_⟩
  exact (by simpa using d1 : ContDiffOn ℝ ((2 : ℕ) : WithTop ℕ∞) f1 U).congr
    fun y hy => (h y hy).1.deriv
