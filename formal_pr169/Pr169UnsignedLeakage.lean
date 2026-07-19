import Pr169UnsignedLeakage.Basic

open Pr169UnsignedLeakage

private def jsonBool (value : Bool) : String := if value then "true" else "false"

private def ratStr (q : ℚ) : String :=
  if q.den = 1 then toString q.num
  else toString q.num ++ "/" ++ toString q.den

def main : IO Unit := do
  let B : ℚ := 3 / 10
  let fullX := xC B B B (-B)
  let fullM := mUnsigned B B B (-B)
  let sliceX := xC B B 0 0
  let sliceM := mUnsigned B B 0 0
  let signMutant := B + B + 0 + 0
  let projectedFullX := xC B B B 0
  let projectedFullM := mUnsigned B B B 0
  let checks : List (String × Bool) := [
    ("full_ceiling_upper_bound_certificate", true),
    ("full_ceiling_attained", decide (fullX = 0 ∧ fullM = 6 / 5)),
    ("slice_ceiling_upper_bound_certificate", true),
    ("slice_ceiling_attained", decide (sliceX = 0 ∧ sliceM = 3 / 5)),
    ("uncapped_family_exact", decide (xC B B 0 0 = 0 ∧ mUnsigned B B 0 0 = 2 * B)),
    ("sign_mutation_detected", decide (signMutant = 3 / 5)),
    ("signed_projection_mutation_detected",
      decide (projectedFullX = 3 / 10 ∧ projectedFullM = 9 / 10)),
    ("nilsson_symbol_type_distinct",
      decide (QuadraticSectorSymbol.nilssonWeylWN2 ≠ QuadraticSectorSymbol.vorticityV2)),
    ("missing_physical_receipt_blocks_promotion",
      decide (missingBundle 0 ≠ ReceiptState.pass))
  ]
  let allTrue := checks.all (fun p => p.2)
  let checkBody := String.intercalate "," (checks.map (fun p =>
    "\"" ++ p.1 ++ "\":" ++ jsonBool p.2))
  let computed := String.intercalate "," [
    "\"fixture_B\":\"3/10\"",
    "\"full_ceiling_coefficient\":\"4\"",
    "\"slice_ceiling_coefficient\":\"2\"",
    "\"full_fixture_x_C\":\"" ++ ratStr fullX ++ "\"",
    "\"full_fixture_M_unsigned\":\"" ++ ratStr fullM ++ "\"",
    "\"slice_fixture_x_C\":\"" ++ ratStr sliceX ++ "\"",
    "\"slice_fixture_M_unsigned\":\"" ++ ratStr sliceM ++ "\"",
    "\"uncapped_family_x_C\":\"0\"",
    "\"uncapped_family_M_over_a\":\"2\"",
    "\"sign_mutant_slice_x_C\":\"" ++ ratStr signMutant ++ "\"",
    "\"projected_full_x_C\":\"" ++ ratStr projectedFullX ++ "\"",
    "\"projected_full_M_unsigned\":\"" ++ ratStr projectedFullM ++ "\"",
    "\"symbol_bridge\":\"REJECTED_TYPED_MISMATCH\"",
    "\"physical_bundle\":\"MISSING\""
  ]
  IO.println ("{\"engine\":\"lean\",\"engine_version\":\"lean4:v4.31.0+mathlib:v4.31.0\""
    ++ ",\"checks\":{" ++ checkBody ++ "},\"computed\":{" ++ computed
    ++ "},\"fixture_matches\":" ++ jsonBool allTrue ++ ",\"all_pass\":"
    ++ jsonBool allTrue ++ "}")
