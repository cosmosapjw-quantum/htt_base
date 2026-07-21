import Pr187Frame.Basic
open Pr187Frame
def main : IO Unit := do
  let checks : List (String × Bool) :=
    [ ("omega_tilt_squared_order_4", omegaTiltSquaredOrder == 4),
      ("quadrupole_order_2", quadrupoleOrder == 2),
      ("forbidden_subtraction_4_ne_2", forbiddenSubtraction),
      ("deprojection_matches_order_2", deprojectionMatches),
      ("rapidity_roundtrip_zero", roundtripAllZero) ]
  for (n, ok) in checks do IO.println s!"{n}={ok}"
  IO.println (if checks.all (fun c => c.2) then "PR187_LEAN_PASS" else "PR187_LEAN_FAIL")
