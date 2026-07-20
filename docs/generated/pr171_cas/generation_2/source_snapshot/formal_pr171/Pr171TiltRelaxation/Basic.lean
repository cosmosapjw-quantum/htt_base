import Mathlib

/-! Exact algebra for the frozen PR-171 class-conditional mechanics. -/

namespace Pr171TiltRelaxation

def dragTrace (a x y : ℚ) : ℚ := -(a + x + y + 1)
def dragDet (a x y : ℚ) : ℚ := a * (1 + y) + x
def dragChar (a x y r : ℚ) : ℚ := r^2 + (a + x + y + 1) * r + dragDet a x y

theorem rwInvariantCleared (v w : ℚ) :
    (3*w-1) * ((1-v^2) + (1-w)*v^2) = (3*w-1)*(1-w*v^2) := by
  ring

theorem rwLinearization (w : ℚ) : (1 : ℚ) * (3*w-1) = 3*w-1 := by ring

theorem radiationBoundary (v : ℚ) :
    (1-v^2) * (3*(1/3 : ℚ)-1) * v = 0 := by ring

theorem dragCharacteristicIdentity (a x y r : ℚ) :
    dragChar a x y r = r^2 + (a+x+y+1)*r + a*(1+y)+x := by
  simp [dragChar, dragDet]

theorem dragHurwitz (a x y : ℚ) (ha : 0 < a) (hx : 0 ≤ x) (hy : 0 ≤ y) :
    0 < a+x+y+1 ∧ 0 < dragDet a x y := by
  constructor
  · linarith
  · simp [dragDet]
    nlinarith

theorem stableFixture :
    dragTrace (1/4) (1/2) (1/3) = (-25/12 : ℚ) ∧
    dragDet (1/4) (1/2) (1/3) = (5/6 : ℚ) := by
  norm_num [dragTrace, dragDet]

theorem persistentFixture :
    ((-1 : ℚ) * 1 + 1 * 1 = 0) ∧ (1 * 1 + (-1) * 1 = 0) := by
  norm_num

theorem counterexampleMap :
    (5/4 : ℚ) = 1 + 1/4 ∧ (1/4 : ℚ) < 1/3 ∧ (0 : ℚ) ≥ 0 := by
  norm_num

theorem counterexampleEnergyConditions :
    (-1 : ℚ) ≤ 1/4 ∧ (1/4 : ℚ) ≤ 1 ∧ (0 : ℚ) ≤ 1/4 := by
  norm_num

end Pr171TiltRelaxation
