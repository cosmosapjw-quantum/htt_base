/- PR-189 joint support vs product box (Lean 4 core). Fixture c=(1,1),
   0<=x<=1, 0<=y<=1, x+y<=1. Convention/mechanics only. -/
namespace Pr189Joint

def feasible (x y : Rat) : Bool :=
  decide (0 <= x) && decide (x <= 1) && decide (0 <= y) && decide (y <= 1)
    && decide (x + y <= 1)

def obj (x y : Rat) : Rat := x + y

def jointWitness : Rat × Rat := (1, 0)
def productCorner : Rat × Rat := (1, 1)
def jointSup : Rat := 1
def productSup : Rat := 2

def strictNarrower : Bool := decide (jointSup < productSup)

def checks : Bool :=
  feasible jointWitness.1 jointWitness.2
  && decide (obj jointWitness.1 jointWitness.2 = jointSup)
  && (!feasible productCorner.1 productCorner.2)
  && decide (obj productCorner.1 productCorner.2 = productSup)
  && strictNarrower

theorem strict_narrower : strictNarrower = true := by native_decide
theorem all_checks : checks = true := by native_decide

end Pr189Joint
