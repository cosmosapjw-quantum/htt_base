/-
PR-187 boost-order bookkeeping and the exact rapidity round-trip
(Lean 4 core, no mathlib). Convention/type mechanics only.
-/
namespace Pr187Frame

def omegaTiltOrder : Nat := 2
def quadrupoleOrder : Nat := 2
def omegaTiltSquaredOrder : Nat := 2 * omegaTiltOrder      -- product adds orders
def deprojectionOrder : Nat := quadrupoleOrder             -- order-correct subtraction

-- an O(beta^4) term cannot cancel an O(beta^2) term
def forbiddenSubtraction : Bool := omegaTiltSquaredOrder ≠ quadrupoleOrder
-- the order-correct deprojection matches the quadrupole order
def deprojectionMatches : Bool := deprojectionOrder = quadrupoleOrder

-- exact rapidity round-trip over ℚ: boost by beta then -beta
def roundtrip (beta : Rat) : Rat := beta + (-beta)
def betas : List Rat := [0, 1, -3, 1/2, -7/5, 123/17]
def roundtripAllZero : Bool := betas.all (fun x => roundtrip x == 0)

def allHold : Bool :=
  (omegaTiltSquaredOrder == 4) && (quadrupoleOrder == 2)
  && forbiddenSubtraction && deprojectionMatches && roundtripAllZero

theorem sq_order_four : omegaTiltSquaredOrder = 4 := by native_decide
theorem order_mismatch : forbiddenSubtraction = true := by native_decide
theorem roundtrip_zero : roundtripAllZero = true := by native_decide
theorem all_hold : allHold = true := by native_decide

end Pr187Frame
