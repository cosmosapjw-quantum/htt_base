import Mathlib
/- Exact candidate endpoint relative errors for the positive interval problem.
   Optimality over every candidate and C01-C03 remain open. -/
theorem grstat_cas13_candidate_errors (L U : ℝ) (hL : L ≠ 0)
    (hU : U ≠ 0) (hS : L+U ≠ 0) :
    ((2*L*U/(L+U)-L)/L = (U-L)/(U+L)) ∧
    ((U-2*L*U/(L+U))/U = (U-L)/(U+L)) := by
  have hUL : U+L ≠ 0 := by simpa [add_comm] using hS
  constructor <;> field_simp [hL, hU, hS, hUL] <;> ring
#print axioms grstat_cas13_candidate_errors

/- The positive-interval relative minimax statement is represented by:
   (i) a uniform bound at the candidate, (ii) endpoint attainment, and
   (iii) an endpoint lower bound for every competing estimator. -/
noncomputable def grstatTau (L U : ℝ) : ℝ := 2*L*U/(L+U)
noncomputable def grstatEps (L U : ℝ) : ℝ := (U-L)/(L+U)

theorem grstat_cas13_minimax (L U : ℝ) (hL : 0 < L) (hLU : L ≤ U) :
    (∀ m : ℝ, L ≤ m → m ≤ U →
      |(grstatTau L U-m)/m| ≤ grstatEps L U) ∧
    |(grstatTau L U-L)/L| = grstatEps L U ∧
    |(grstatTau L U-U)/U| = grstatEps L U ∧
    (∀ t : ℝ, grstatEps L U ≤
      max (|(t-L)/L|) (|(t-U)/U|)) := by
  have hU : 0 < U := lt_of_lt_of_le hL hLU
  have hS : 0 < L+U := by linarith
  have hSn : L+U ≠ 0 := ne_of_gt hS
  have hULn : U+L ≠ 0 := by simpa [add_comm] using hSn
  have heps0 : 0 ≤ grstatEps L U := by
    unfold grstatEps
    exact div_nonneg (sub_nonneg.mpr hLU) (le_of_lt hS)
  have heps1 : grstatEps L U < 1 := by
    unfold grstatEps
    apply (div_lt_one hS).2
    linarith
  have htL : grstatTau L U = (1+grstatEps L U)*L := by
    unfold grstatTau grstatEps
    field_simp [hSn]
    ring
  have htU : grstatTau L U = (1-grstatEps L U)*U := by
    unfold grstatTau grstatEps
    field_simp [hSn]
    ring
  constructor
  · intro m hmL hmU
    have hm : 0 < m := lt_of_lt_of_le hL hmL
    rw [abs_div, abs_of_pos hm]
    apply (div_le_iff₀ hm).2
    apply abs_le.mpr
    constructor
    · have hmul := mul_le_mul_of_nonneg_left hmU (by linarith : 0 ≤ 1-grstatEps L U)
      nlinarith [htU]
    · have hmul := mul_le_mul_of_nonneg_left hmL (by linarith : 0 ≤ 1+grstatEps L U)
      nlinarith [htL]
  constructor
  · rw [abs_div, abs_of_pos hL]
    have he : 0 ≤ grstatTau L U-L := by nlinarith [htL]
    rw [abs_of_nonneg he]
    apply (div_eq_iff (ne_of_gt hL)).2
    nlinarith [htL]
  constructor
  · rw [abs_div, abs_of_pos hU]
    have he : grstatTau L U-U ≤ 0 := by nlinarith [htU]
    rw [abs_of_nonpos he]
    apply (div_eq_iff (ne_of_gt hU)).2
    nlinarith [htU]
  · intro t
    by_contra hh
    have hh' : max (|(t-L)/L|) (|(t-U)/U|) < grstatEps L U := lt_of_not_ge hh
    have hleft : |(t-L)/L| < grstatEps L U := lt_of_le_of_lt (le_max_left _ _) hh'
    have hright : |(t-U)/U| < grstatEps L U := lt_of_le_of_lt (le_max_right _ _) hh'
    rw [abs_div, abs_of_pos hL] at hleft
    rw [abs_div, abs_of_pos hU] at hright
    have hleft' : |t-L| < grstatEps L U * L := (div_lt_iff₀ hL).mp hleft
    have hright' : |t-U| < grstatEps L U * U := (div_lt_iff₀ hU).mp hright
    have ha := (abs_lt.mp hleft').2
    have hb := (abs_lt.mp hright').1
    nlinarith [htL, htU]

#print axioms grstat_cas13_minimax

#print grstat_cas13_minimax
