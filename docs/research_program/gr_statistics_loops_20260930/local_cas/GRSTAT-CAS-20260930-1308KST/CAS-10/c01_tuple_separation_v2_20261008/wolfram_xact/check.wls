(* Independent exact CAS-10-C01 Wolfram/xTensor axis. *)
Needs["xAct`xTensor`"];
Clear[H];
u = {5/4, 3/4, 0, 0};
gInv = DiagonalMatrix[{-1, 1, 1, 1}];
b1Matrix = H {{9/16, -15/16, 0, 0}, {-15/16, 25/16, 0, 0},
              {0, 0, 1, 0}, {0, 0, 0, 1}};
b2Matrix = (H/128) {{-153, 0, -120, 0}, {0, 425, 0, 0},
                    {-120, 0, 353, 0}, {0, 0, 0, 353}};
b1u = b1Matrix.u;
b2u = b2Matrix.u;
orthogonality = u.b2u;
lorentzNorm2 = b2u.gInv.b2u;

sectorPowers[z0_, z1_, mass_, momentum_, tensor_] := {
  z0^2, z1^2, mass^2, momentum.momentum,
  Total[Flatten[tensor]^2]
};
tensor = DiagonalMatrix[{3 H/8, -3 H/16, -3 H/16}];
tuple1 = sectorPowers[5/4, 3/4, 7 H/4, {15 H/8, 0, 0}, tensor];
tuple2 = sectorPowers[5/4, 3/4, 7 H/4, {0, 15 H/8, 0}, tensor];
expectedB2 = (H/512) {-765, 1275, -600, 0};
expectedPowers = {25/16, 9/16, 49 H^2/16, 225 H^2/64,
                  27 H^2/128};
zeroVectorQ[v_] := And @@ (TrueQ[FullSimplify[# == 0]] & /@ v);
equalVectorQ[a_, b_] := zeroVectorQ[a - b];
checks = <|
  "u_timelike_unit" -> TrueQ[FullSimplify[u.gInv.u == -1]],
  "B1_u_zero" -> zeroVectorQ[b1u],
  "B2_u_exact" -> equalVectorQ[b2u, expectedB2],
  "u_dot_b2_zero" -> TrueQ[FullSimplify[orthogonality == 0]],
  "b2_lorentz_norm_exact" ->
    TrueQ[FullSimplify[lorentzNorm2 == 87525 H^2/16384]],
  "H_nonzero_strict_positive" ->
    TrueQ[Resolve[ForAll[H, Implies[H != 0, lorentzNorm2 > 0]], Reals]],
  "H_zero_boundary" ->
    TrueQ[FullSimplify[(b2u /. H -> 0) == {0, 0, 0, 0} &&
      (lorentzNorm2 /. H -> 0) == 0]],
  "tuple1_separate_powers" -> equalVectorQ[tuple1, expectedPowers],
  "tuple2_separate_powers" -> equalVectorQ[tuple2, expectedPowers]
|>;
results = <|
  "wolfram_version" -> System`$Version,
  "xtensor_version" -> ToString[InputForm[xAct`xTensor`$Version]],
  "checks" -> checks,
  "actual" -> <|
    "B1_u" -> ToString[InputForm[b1u]],
    "B2_u" -> ToString[InputForm[b2u]],
    "u_dot_b2" -> ToString[InputForm[orthogonality]],
    "b2_lorentz_norm_squared" -> ToString[InputForm[lorentzNorm2]],
    "tuple1_powers" -> ToString[InputForm[tuple1]],
    "tuple2_powers" -> ToString[InputForm[tuple2]]
  |>
|>;
Print["CAS10_JSON=", ExportString[results, "RawJSON", "Compact" -> True]];
If[And @@ Values[checks], Exit[0], Exit[1]];
