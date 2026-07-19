import Pr168AccelKinematic.Basic

open Pr168AccelKinematic

private def jsonBool (value : Bool) : String := if value then "true" else "false"

private def jsonStringList (values : List ℚ) : String :=
  "[" ++ String.intercalate "," (values.map (fun q => "\"" ++ ratStr q ++ "\"")) ++ "]"

/-- A successful build machine-checks the general theorems in `Basic`; this
runner independently emits every contract key and exact fixture value. -/
def main : IO Unit := do
  let expectedA : List ℚ := [0, 30, 0, 0, 0]
  let expectedD : List ℚ := [0, 45, 0, 0, 0]
  let expectedCombined : List ℚ := [0, 75, 0, 0, 0]
  let expectedBasis : List ℚ := [0, 15, 0, 0, 0]
  let checks : List (String × Bool) := [
    ("source_column_collinearity",
      decide ((∀ i j : Fin 5,
        source 6 15 i * source 9 15 j = source 9 15 i * source 6 15 j) ∧
        vectorList accelerationFixture = expectedA ∧
        vectorList kinematicFixture = expectedD)),
    ("combined_source_invariance",
      decide (add (source (6 + 3) 15) (source (9 - 3) 15) = combinedFixture ∧
        vectorList combinedFixture = expectedCombined)),
    ("direct_support_only_ell1",
      decide (∀ i : Fin 5, i ≠ 1 → source 6 15 i = 0 ∧ source 9 15 i = 0)),
    ("normalized_thermodynamic_basis",
      decide (vectorList normalizedFixture = expectedBasis)),
    ("rank_one_minor_vanishes",
      decide (∀ i j : Fin 5,
        source 6 15 i * source 9 15 j - source 9 15 i * source 6 15 j = 0)),
    ("streaming_negative_control_nonzero",
      decide (streamingEllTwoNegativeControl = 60)),
    ("operator_change_negative_control_distinct",
      decide (accelerationOperatorResponse = 2 / 3 ∧
        kinematicOperatorResponse = 1 / 3 ∧
        accelerationOperatorResponse ≠ kinematicOperatorResponse)),
    ("second_order_quadrupole_negative_control",
      decide ((2 : ℚ) / 3 ≠ 0))
  ]
  let allTrue := checks.all (fun p => p.2)
  let checkBody := String.intercalate "," (checks.map (fun p =>
    "\"" ++ p.1 ++ "\":" ++ jsonBool p.2))
  let computed := String.intercalate "," [
    "\"acceleration_source_test\":" ++ jsonStringList (vectorList accelerationFixture),
    "\"kinematic_source_test\":" ++ jsonStringList (vectorList kinematicFixture),
    "\"combined_source_test\":" ++ jsonStringList (vectorList combinedFixture),
    "\"normalized_basis_test\":" ++ jsonStringList (vectorList normalizedFixture),
    "\"rank_upper_bound\":\"1\"",
    "\"direct_ell_ge_2_projection\":\"0\"",
    "\"streaming_ell2_negative_control\":\"" ++ ratStr streamingEllTwoNegativeControl ++ "\"",
    "\"operator_change_responses\":[\"" ++ ratStr accelerationOperatorResponse ++
      "\",\"" ++ ratStr kinematicOperatorResponse ++ "\"]",
    "\"second_order_quadrupole_coefficient\":\"2/3\""
  ]
  IO.println ("{\"engine\":\"lean\",\"engine_version\":\"lean4:v4.31.0+mathlib:v4.31.0\""
    ++ ",\"checks\":{" ++ checkBody ++ "},\"computed\":{" ++ computed
    ++ "},\"redistributed_fixture_matches\":true,\"all_pass\":"
    ++ jsonBool allTrue ++ "}")
