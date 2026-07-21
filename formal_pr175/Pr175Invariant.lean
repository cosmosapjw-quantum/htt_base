import Pr175Invariant.Basic

open Pr175Invariant

private def jsonBool (value : Bool) : String := if value then "true" else "false"

private def ratStr (q : Rat) : String :=
  if q.den = 1 then toString q.num
  else toString q.num ++ "/" ++ toString q.den

def names : List String :=
  ["I", "II", "VI_0", "VII_0", "VIII", "IX", "V", "IV", "III", "VI_h", "VII_h"]

def main : IO Unit := do
  let checks : List (String × Bool) := [
    ("eleven_type_ricci_scalar_matches_anchor", allAnchorsMatch),
    ("class_b_vector_constraint_a_dot_n_zero", classBConstraint),
    ("vi_vii_h_relation_consistent", hRelations)
  ]
  let allTrue := checks.all (fun p => p.2)
  let checkBody := String.intercalate "," (checks.map (fun p =>
    "\"" ++ p.1 ++ "\":" ++ jsonBool p.2))
  let values := (names.zip reps).map (fun p =>
    "\"R_" ++ p.1 ++ "\":\"" ++ ratStr (anchor p.2) ++ "\"")
  IO.println ("{\"engine\":\"lean\",\"engine_version\":\"lean4:v4.31.0-core\""
    ++ ",\"checks\":{" ++ checkBody ++ "},\"computed\":{"
    ++ String.intercalate "," values ++ "},\"all_pass\":"
    ++ jsonBool allTrue ++ "}")
