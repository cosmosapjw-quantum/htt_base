import Pr186W2.Basic
open Pr186W2

def main : IO Unit := do
  let checks : List (String × Bool) :=
    [ ("identity_A_eq_2w_witnesses", witnesses.all (fun w => identityHolds w.1 w.2.1 w.2.2.1)),
      ("W2reg_eq_vecform", witnesses.all (fun w => W2reg w.1 w.2.1 w.2.2.1 w.2.2.2.1 == W2vec w.1 w.2.1 w.2.2.1 w.2.2.2.1)),
      ("wrong_over_right_is_3", witnesses.all (fun w => wrongDisplay w.1 w.2.1 w.2.2.1 w.2.2.2.1 == 3 * W2reg w.1 w.2.1 w.2.2.1 w.2.2.2.1)),
      ("ceiling_is_three_halves", witnesses.all (fun w => W2max w.2.2.2.2 w.2.2.2.1 == (3/2) * w.2.2.2.2^2)),
      ("all_witnesses_hold", allWitnessesHold) ]
  for (name, ok) in checks do
    IO.println s!"{name}={ok}"
  if checks.all (fun c => c.2) then
    IO.println "PR186_LEAN_PASS"
  else
    IO.println "PR186_LEAN_FAIL"
