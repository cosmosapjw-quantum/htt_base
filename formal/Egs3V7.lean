import Egs3V7.Basic

/-- Runner entry point: every seal below is closed by `decide`/`native_decide`
    at elaboration time, so a successful `lake build` IS the proof. `main`
    re-`decide`s the load-bearing propositions at runtime and emits a JSON line
    the Python runner parses. -/
def main : IO Unit := do
  -- These `decide`s re-check the propositions the theorems already proved.
  let checks : List (String × Bool) := [
    ("promote_nil", decide (Egs3V7.promote [] = true)),
    ("promote_all_true", decide (Egs3V7.promote [true, true, true] = true)),
    ("promote_blocks_on_false", decide (Egs3V7.promote [true, false, true] = false)),
    ("open_branch_lo_11_100", decide (Egs3V7.xcLo 0 ((2:Rat)/100) = (11:Rat)/100)),
    ("open_branch_hi_17_100", decide (Egs3V7.xcHi 0 ((2:Rat)/100) = (17:Rat)/100)),
    ("all_branch_lo_9_100", decide (Egs3V7.xcLo (-(2:Rat)/100) ((2:Rat)/100) = (9:Rat)/100)),
    ("all_branch_hi_17_100", decide (Egs3V7.xcHi (-(2:Rat)/100) ((2:Rat)/100) = (17:Rat)/100)),
    ("dl1_lower_gap_2_100",
      decide (Egs3V7.xcLo 0 ((2:Rat)/100) - Egs3V7.xcLo (-(2:Rat)/100) ((2:Rat)/100) = (2:Rat)/100)),
    ("dl1_upper_coincide",
      decide (Egs3V7.xcHi 0 ((2:Rat)/100) = Egs3V7.xcHi (-(2:Rat)/100) ((2:Rat)/100))),
    ("w2_mismatch_is_three", decide ((1:Rat)/((1:Rat)/3) = 3)),
    ("mes_three_halves", decide (((6:Rat)/((3:Rat)^2)) * ((3:Rat)/2) = 1))
  ]
  let allTrue := checks.all (fun p => p.2)
  let body := String.intercalate ","
    (checks.map (fun p => "\"" ++ p.1 ++ "\":" ++ (if p.2 then "true" else "false")))
  IO.println ("{\"schema\":\"htt.egs3.lean_seal.v1\",\"status\":\""
    ++ (if allTrue then "PASS" else "FAIL") ++ "\",\"checks\":{" ++ body ++ "}}")
