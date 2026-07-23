/- PR-222 multi-window bulk bridge rank (Lean 4 core). Gram G of 10W has
   det = 394584 != 0 (rank 3); single-window outer-product minor = 0 (rank 1). -/
namespace Pr222Bridge

def detG : Int :=
  140 * (78 * 54 - 28 * 28)
  - 44 * (44 * 54 - 28 * 14)
  + 14 * (44 * 28 - 78 * 14)

def singleWindowMinor : Int := (10*10)*(1*1) - (10*1)*(1*10)

def checks : Bool :=
  decide (detG = 394584) && decide (detG ≠ 0) && decide (singleWindowMinor = 0)

theorem all_checks : checks = true := by native_decide

end Pr222Bridge
