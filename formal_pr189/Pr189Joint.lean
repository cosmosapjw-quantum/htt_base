import Pr189Joint.Basic
open Pr189Joint
def main : IO Unit := do
  IO.println s!"strict_1_lt_2={strictNarrower}"
  IO.println s!"witness_feasible={feasible jointWitness.1 jointWitness.2}"
  IO.println s!"product_corner_infeasible_for_joint={!feasible productCorner.1 productCorner.2}"
  IO.println (if checks then "PR189_LEAN_PASS" else "PR189_LEAN_FAIL")
