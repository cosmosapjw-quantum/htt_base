(* CAS-12-C03.  "en" represents the contract's energy E; E is protected in WL. *)
ClearAll[b, en, x, weight, hyperbolic, candidate, coefficients, expected,
  formalProduct, scaledLeading, rightLimit, vectors, packageLoaded, checks,
  scalarEqual, numericResiduals, allPass, result];

Needs["xAct`xTensor`"];
packageLoaded = MemberQ[$Packages, "xAct`xTensor`"] &&
  Length[Names["xAct`xTensor`DefManifold"]] > 0;

x = b en;
weight = Exp[x]/(Exp[x] - 1)^2;
hyperbolic = 1/(4 Sinh[x/2]^2);
candidate = x^(-2) - 1/12 + x^2/240 - x^4/6048;

scalarEqual[left_, right_] := TrueQ[FullSimplify[left == right, b > 0 && en > 0]];
coefficients = Association@Table[
    ToString[k] -> FullSimplify[SeriesCoefficient[weight, {en, 0, k}], b > 0],
    {k, {-2, -1, 0, 1, 2, 3, 4}}];
expected = <|"-2" -> 1/b^2, "-1" -> 0, "0" -> -1/12,
  "1" -> 0, "2" -> b^2/240, "3" -> 0, "4" -> -b^4/6048|>;
formalProduct = Normal[Series[
    (Exp[x] - 1)^2 candidate - Exp[x], {en, 0, 7}]];
scaledLeading = FullSimplify[SeriesCoefficient[en^2 weight, {en, 0, 0}], b > 0];
rightLimit = FullSimplify[
    Limit[en^2 weight, en -> 0, Direction -> "FromAbove",
      Assumptions -> b > 0], b > 0];

vectors = {{1, 1/10}, {2, 1/100}};
numericResiduals = Table[Module[{wv, hv, residual, threshold},
    wv = N[weight /. {b -> pair[[1]], en -> pair[[2]]}, 80];
    hv = N[hyperbolic /. {b -> pair[[1]], en -> pair[[2]]}, 80];
    residual = Abs[wv - hv];
    threshold = 10^-50 + 10^-40 Max[Abs[wv], Abs[hv]];
    <|"b" -> ToString[InputForm[pair[[1]]]],
      "E" -> ToString[InputForm[pair[[2]]]],
      "residual" -> ToString[InputForm[residual]],
      "threshold" -> ToString[InputForm[threshold]],
      "pass" -> TrueQ[residual <= threshold]|>
  ], {pair, vectors}];

checks = <|
  "xact_loaded" -> packageLoaded,
  "exact_exp_sinh_identity" -> scalarEqual[weight, hyperbolic],
  "exact_laurent_coefficients" -> And @@ KeyValueMap[
      TrueQ[FullSimplify[coefficients[#1] == #2, b > 0]] &, expected],
  "formal_cleared_product_residual_O_x8" -> TrueQ[FullSimplify[formalProduct == 0, b > 0]],
  "scaled_leading_coefficient" -> TrueQ[FullSimplify[scaledLeading == 1/b^2, b > 0]],
  "analytic_right_limit" -> TrueQ[FullSimplify[rightLimit == 1/b^2, b > 0]],
  "numeric_vectors_80_digits" -> And @@ (Lookup[#, "pass"] & /@ numericResiduals)
|>;
allPass = And @@ Values[checks];
result = <|
  "component" -> "CAS-12-C03",
  "axis" -> "wolfram_xact",
  "status" -> If[allPass, "PASS", "FAIL"],
  "wolfram_version" -> System`$Version,
  "wolfram_version_number" -> ToString[InputForm[System`$VersionNumber]],
  "xact_version" -> ToString[InputForm[xAct`xTensor`$Version]],
  "xact_package_file" -> ToString[FindFile["xAct`xTensor`"]],
  "checks" -> checks,
  "laurent_coefficients" -> Association@KeyValueMap[
      #1 -> ToString[InputForm[#2]] &, coefficients],
  "formal_product_residual" -> ToString[InputForm[formalProduct]],
  "scaled_leading_coefficient" -> ToString[InputForm[scaledLeading]],
  "right_limit" -> ToString[InputForm[rightLimit]],
  "numeric_residuals" -> numericResiduals,
  "domain_assumption_diff" -> {},
  "domain" -> "b real > 0; original weight on E > 0; Laurent formal at 0; right limit E -> 0+",
  "branch" -> "real exponential and real positive sinh argument"
|>;
Print["CAS12_C03_RESULT_JSON=" <> ExportString[result, "RawJSON"]];
Exit[If[allPass, 0, 2]];
