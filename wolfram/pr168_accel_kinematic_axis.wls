(* PR-168 Wolfram+xAct axis: exact aligned source-basis identity. *)

Quiet[Needs["xAct`xTensor`"]];

basis = {0, 1, 0, 0, 0};
sourceA = (a g/3) basis;
sourceD = (d g/3) basis;
columns = Transpose[{sourceA, sourceD}];
minors = Flatten@Table[
  Det[columns[[{i, j}, All]]], {i, 1, 4}, {j, i + 1, 5}];
redistributed = ((a + delta) g/3) basis + ((d - delta) g/3) basis;
normalizedA = FullSimplify[3 sourceA/a, Assumptions -> a != 0];
normalizedD = FullSimplify[3 sourceD/d, Assumptions -> d != 0];

sourceATest = sourceA /. {a -> 6, g -> 15};
sourceDTest = sourceD /. {d -> 9, g -> 15};
combinedTest = sourceATest + sourceDTest;
redistributedTest = redistributed /. {a -> 6, d -> 9, g -> 15, delta -> 3};

streaming = SparseArray[{{3, 2} -> 2}, {5, 5}];
streamingEll2 = (streaming.sourceATest)[[3]];
accelResponse = 6/(3*3);
kinematicResponse = 9/(3*(3 + 6));
secondOrderResidual = Expand[
  mu^2 - (1/3 + (2/3) LegendreP[2, mu])];

checks = <|
  "source_column_collinearity" -> And @@ Thread[minors == 0],
  "combined_source_invariance" ->
    (FullSimplify[sourceA + sourceD - redistributed] === ConstantArray[0, 5]),
  "direct_support_only_ell1" ->
    (And @@ Thread[sourceA[[{1, 3, 4, 5}]] == 0] &&
     And @@ Thread[sourceD[[{1, 3, 4, 5}]] == 0]),
  "normalized_thermodynamic_basis" ->
    (normalizedA === g basis && normalizedD === g basis),
  "rank_one_minor_vanishes" -> And @@ Thread[minors == 0],
  "streaming_negative_control_nonzero" -> (streamingEll2 === 60),
  "operator_change_negative_control_distinct" ->
    (accelResponse === 2/3 && kinematicResponse === 1/3 &&
     accelResponse =!= kinematicResponse),
  "second_order_quadrupole_negative_control" ->
    (secondOrderResidual === 0)
|>;

ratString[x_] := ToString[InputForm[x]];
computed = <|
  "acceleration_source_test" -> (ratString /@ sourceATest),
  "kinematic_source_test" -> (ratString /@ sourceDTest),
  "combined_source_test" -> (ratString /@ combinedTest),
  "normalized_basis_test" -> (ratString /@ (normalizedA /. g -> 15)),
  "rank_upper_bound" -> "1",
  "direct_ell_ge_2_projection" -> "0",
  "streaming_ell2_negative_control" -> ratString[streamingEll2],
  "operator_change_responses" ->
    {ratString[accelResponse], ratString[kinematicResponse]},
  "second_order_quadrupole_coefficient" -> "2/3"
|>;

allPass = And @@ Values[checks] && redistributedTest === combinedTest;
payload = <|
  "engine" -> "wolfram_xact",
  "engine_version" -> ToString[$VersionNumber],
  "xact_loaded" -> MemberQ[$Packages, "xAct`xTensor`"],
  "checks" -> checks,
  "computed" -> computed,
  "redistributed_fixture_matches" -> (redistributedTest === combinedTest),
  "all_pass" -> allPass
|>;

Print[ExportString[payload, "JSON", "Compact" -> True]];
If[allPass, Exit[0], Exit[2]];
