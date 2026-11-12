import Mathlib

/-- T1: the Hamiltonian-constraint combination only bounds the DIFFERENCE Σ² − W². -/
theorem T1_difference_bound (S W b : ℝ) (hS : 0 ≤ S) (hW : 0 ≤ W) (h : S - W ≤ b) : S ≤ b + W := by
  linarith

/-- With an independent ceiling on W² the shear block is bounded. -/
theorem T1_shear_bound_given_vorticity_ceiling (S W b w : ℝ) (h : S - W ≤ b) (hw : W ≤ w) : S ≤ b + w := by
  linarith

/-- Without an independent W² ceiling NO bound on Σ² alone follows from the difference constraint (any b). -/
theorem T1_no_standalone_shear_bound (b : ℝ) (hb : 0 ≤ b) :
    ∃ S W : ℝ, 0 ≤ S ∧ 0 ≤ W ∧ S - W ≤ b ∧ b < S := by
  refine ⟨b + 1, b + 1, by linarith, by linarith, by linarith, by linarith⟩

/-- Same for vorticity: the difference constraint gives only W ≥ S - b, never an upper bound without a shear ceiling. -/
theorem T1_no_standalone_vorticity_bound (b : ℝ) (hb : 0 ≤ b) :
    ∃ S W : ℝ, 0 ≤ S ∧ 0 ≤ W ∧ S - W ≤ b ∧ b < W := by
  refine ⟨0, b + 1, le_refl _, by linarith, by linarith, by linarith⟩

/-- Frobenius conversion of the repo definitions: Σ² = |σ|²/(6H²)  ⇒  |σ|/H = √6 · Σ  (as squares). -/
theorem frob_from_Sigma_sq (F S2 : ℝ) (h : F ^ 2 = 6 * S2) : F ^ 2 / 6 = S2 := by linarith

#print axioms T1_difference_bound
#print axioms T1_no_standalone_shear_bound
#print axioms T1_no_standalone_vorticity_bound
