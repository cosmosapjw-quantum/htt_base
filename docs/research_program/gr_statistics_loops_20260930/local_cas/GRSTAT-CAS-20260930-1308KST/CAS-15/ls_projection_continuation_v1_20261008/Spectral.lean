import Mathlib

/-!
CAS15-C03 spectral helper. The Euclidean norm on `V3` is the ordinary vector
2-norm. This file establishes the operator-norm control of Rayleigh quotients
and the elementary three-index ordered-gap consequence. The spectral min-max
and rotated Frobenius coercivity bridges are recorded separately in
`SPECTRAL_NOTES.md`; no theorem here assumes either as a conclusion.
-/

noncomputable section
namespace CAS15Spectral
open scoped InnerProductSpace

abbrev V3 := EuclideanSpace ℝ (Fin 3)

/-- The quadratic form of a perturbation on a unit vector changes by at most
its induced operator norm. -/
theorem rayleigh_error_le (A B : V3 →L[ℝ] V3) (v : V3)
    (hv : ‖v‖ = 1) :
    |⟪(A - B) v, v⟫_ℝ| ≤ ‖A - B‖ := by
  calc
    |⟪(A - B) v, v⟫_ℝ| ≤ ‖(A - B) v‖ * ‖v‖ := abs_real_inner_le_norm ((A - B) v) v
    _ ≤ ‖A - B‖ := by
      rw [hv, mul_one]
      simpa [hv] using (ContinuousLinearMap.le_opNorm (A - B) v)

/-- Each ordered adjacent gap loses at most twice a pointwise eigenvalue error. -/
theorem ordered_adjacent_gap (a b ah bh ε : ℝ)
    (ha : |ah - a| ≤ ε) (hb : |bh - b| ≤ ε) :
    (a - b) - 2 * ε ≤ ah - bh := by
  have ha' : -ε ≤ ah - a := (abs_le.mp ha).1
  have hb' : bh - b ≤ ε := (abs_le.mp hb).2
  linarith

/-- For decreasingly ordered real triples, the minimum pairwise gap is the
minimum adjacent gap. -/
def orderedGap (lamb : Fin 3 → ℝ) : ℝ :=
  min (lamb 0 - lamb 1) (lamb 1 - lamb 2)

/-- The gap perturbation deduction uses all three ordered eigenvalue matches.
No spectral perturbation theorem is hidden in the hypotheses. -/
theorem ordered_gap_from_pointwise_matches
    (lamb lambh : Fin 3 → ℝ) (ε : ℝ)
    (hmatch : ∀ i : Fin 3, |lambh i - lamb i| ≤ ε) :
    orderedGap lamb - 2 * ε ≤ orderedGap lambh := by
  have h01 := ordered_adjacent_gap (lamb 0) (lamb 1) (lambh 0) (lambh 1) ε
    (hmatch 0) (hmatch 1)
  have h12 := ordered_adjacent_gap (lamb 1) (lamb 2) (lambh 1) (lambh 2) ε
    (hmatch 1) (hmatch 2)
  dsimp [orderedGap]
  exact le_min (by linarith [min_le_left (lamb 0 - lamb 1) (lamb 1 - lamb 2), h01])
    (by linarith [min_le_right (lamb 0 - lamb 1) (lamb 1 - lamb 2), h12])

#print axioms rayleigh_error_le
#print axioms ordered_gap_from_pointwise_matches

end CAS15Spectral
