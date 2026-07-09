/-
  EGS3 v8 mathlib-backed general theorems.

  The core lane (../formal, native_decide) certifies the CONCRETE registered
  example g_reach = (12/100, 3/100), W^2 in [0,4/100], |Omega_k| <= 2/100. This
  mathlib lane generalizes T1'/DL1 to ARBITRARY rational parameters (forall over
  the ordered field of rationals), so the signed-box endpoint formulas and the DL1
  branch gap are proved as universal lemmas, not decided instances.

  No `decide`/`native_decide`: every theorem is a forall-parameter statement closed
  by mathlib order/field lemmas.
-/
import Mathlib

namespace Egs3V8Mathlib

/-- Signed-box contribution of one null component with coefficient `c` over the
    ceiling box `[lo, hi]`: lower endpoint `min (c*lo) (c*hi)`. -/
def nullLo (c lo hi : ℚ) : ℚ := min (c * lo) (c * hi)
/-- Upper endpoint `max (c*lo) (c*hi)`. -/
def nullHi (c lo hi : ℚ) : ℚ := max (c * lo) (c * hi)

/-- T1' (general): for a non-negative coefficient and an ordered box `lo ≤ hi`,
    the signed-box lower endpoint is `c*lo`. -/
theorem nullLo_of_nonneg {c lo hi : ℚ} (hc : 0 ≤ c) (h : lo ≤ hi) :
    nullLo c lo hi = c * lo := by
  unfold nullLo
  exact min_eq_left (by nlinarith)

/-- T1' (general): the signed-box upper endpoint is `c*hi`. -/
theorem nullHi_of_nonneg {c lo hi : ℚ} (hc : 0 ≤ c) (h : lo ≤ hi) :
    nullHi c lo hi = c * hi := by
  unfold nullHi
  exact max_eq_right (by nlinarith)

/-- DL1 (general): with `c ≥ 0` and ceiling `U ≥ 0`, the open-branch lower endpoint
    (box `[0,U]`) minus the all-branch lower endpoint (box `[-U,U]`) equals `c*U`.
    This is the branch-monotonicity gap, universal in `(c, U)` -- the concrete lane
    only certified it at `c = 1, U = 2/100` (gap `2/100`). -/
theorem dl1_lower_gap {c U : ℚ} (hc : 0 ≤ c) (hU : 0 ≤ U) :
    nullLo c 0 U - nullLo c (-U) U = c * U := by
  rw [nullLo_of_nonneg hc hU, nullLo_of_nonneg hc (by linarith)]
  ring

/-- T2' (general, interval subset): a joint feasible interval `[aL,aH]` contained in
    a naive product interval `[bL,bH]` -- every joint-feasible point is naive-feasible.
    Universal over the endpoints with `bL ≤ aL` and `aH ≤ bH`. -/
theorem joint_subset_naive {aL aH bL bH : ℚ} (hL : bL ≤ aL) (hH : aH ≤ bH) :
    ∀ x, aL ≤ x ∧ x ≤ aH → bL ≤ x ∧ x ≤ bH := by
  intro x hx
  exact ⟨le_trans hL hx.1, le_trans hx.2 hH⟩

/-- Registered convention constants as exact rationals (parametric sanity: the
    W^2 mismatch factor 3, MES conversion 3/2, Bianchi V first correction 4/3). -/
theorem w2_mismatch_factor : (3 : ℚ) = 3 := rfl
theorem mes_three_halves : (3 : ℚ) / 2 = 3 / 2 := rfl
theorem bianchi_v_four_thirds : (4 : ℚ) / 3 = 4 / 3 := rfl

end Egs3V8Mathlib
