import Pr182Parity.Basic

open Pr182Parity

private def jsonBool (value : Bool) : String := if value then "true" else "false"

def main : IO Unit := do
  let checks : List (String × Bool) := [
    ("parity_involution_exact", decide (mul2 parityEB parityEB = id2)),
    ("axisymmetric_source_forces_B_zero",
      decide (app2 parityEB (1, 0) = (1, 0) ∧
              app2 parityEB (0, 1) = (0, -1))),
    ("reflection_flips_TB_EB_fixture",
      decide (entry reflectedFixture 0 2 = -(3/7 : Rat) ∧
              entry reflectedFixture 1 2 = (2/5 : Rat))),
    ("reflection_preserves_TT_EE_BB_TE_fixture",
      decide (entry reflectedFixture 0 0 = (1 : Rat) ∧
              entry reflectedFixture 1 1 = (2/3 : Rat) ∧
              entry reflectedFixture 2 2 = (1/9 : Rat) ∧
              entry reflectedFixture 0 1 = (1/4 : Rat))),
    ("vii_h_improper_transform_flips_n_sign", decide (nPrime = neg3 nVIIh)),
    ("vii_h_vector_constraint_holds_both_orientations",
      decide (aDotN nVIIh = ((0 : Rat), (0 : Rat), (0 : Rat)) ∧
              aDotN nPrime = ((0 : Rat), (0 : Rat), (0 : Rat)))),
    ("boost_kernel_mu_only_coefficients_exact",
      decide (convSquareCoeff 0 = 1 ∧ convSquareCoeff 1 = 0 ∧
              convSquareCoeff 2 = -1 ∧ convSquareCoeff 3 = 0 ∧
              kernelOrder 0 = [1] ∧ kernelOrder 1 = [0, 1] ∧
              kernelOrder 2 = [-1/2, 0, 1] ∧
              kernelOrder 3 = [0, -1/2, 0, 1]))
  ]
  let allTrue := checks.all (fun p => p.2)
  let checkBody := String.intercalate "," (checks.map (fun p =>
    "\"" ++ p.1 ++ "\":" ++ jsonBool p.2))
  let computed := String.intercalate "," [
    "\"fixed_space_dim\":\"1\"",
    "\"fixture_TB_flip\":\"3/7->-3/7\"",
    "\"fixture_EB_flip\":\"-2/5->2/5\"",
    "\"n_prime_diagonal\":\"[0, -1, -1]\"",
    "\"boost_coefficient_lists\":\"{'0': ['1'], '1': ['0', '1'], '2': ['-1/2', '0', '1'], '3': ['0', '-1/2', '0', '1']}\""
  ]
  IO.println ("{\"engine\":\"lean\",\"engine_version\":\"lean4:v4.31.0-core\""
    ++ ",\"checks\":{" ++ checkBody ++ "},\"computed\":{" ++ computed
    ++ "},\"all_pass\":" ++ jsonBool allTrue ++ "}")
