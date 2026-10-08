(* CAS-13-C03: independent finite Hermite certificate, Wolfram Engine + xAct. *)
ClearAll[aa, uu, bb, lo, yy, c0, c3, c4, m3, m4, ww];
output = Last[$ScriptCommandLine];
xactLoad = Quiet[Check[Needs["xAct`xTensor`"], $Failed]];
xactLoaded = MemberQ[$Packages, "xAct`xTensor`"] && xactLoad =!= $Failed;
disc = 3 aa^2 + 2 aa uu + uu^2;
matrix = {{1, aa^3, aa^4}, {1, uu^3, uu^4}, {0, 3 uu^2, 4 uu^3}};
exactZero[expr_] := TrueQ[Expand[Numerator[Together[expr]]] === 0];
determinantOK = exactZero[Det[matrix] - uu^2 (uu - aa)^2 disc];
deltaPositive = TrueQ[Resolve[ForAll[{aa, uu},
  Implies[aa > 0 && uu > 0, disc > 0]], Reals]];
lowerOrderSign = TrueQ[Resolve[ForAll[{aa, uu, bb, yy},
  Implies[0 < aa && aa < uu && uu <= bb && aa <= yy && yy <= bb,
    (yy - aa) (yy - uu)^2 >= 0]], Reals]];
upperOrderSign = TrueQ[Resolve[ForAll[{lo, uu, aa, yy},
  Implies[0 < lo && lo <= uu && uu < aa && lo <= yy && yy <= aa,
    (yy - aa) (yy - uu)^2 <= 0]], Reals]];

targetP[5] = disc yy^2 + (2 aa^2 uu + aa uu^2) yy + aa^2 uu^2;
targetP[6] = disc yy^3 +
  (3 aa^3 + 8 aa^2 uu + 5 aa uu^2 + 2 uu^3) yy^2 +
  (2 aa^3 uu + 5 aa^2 uu^2 + 2 aa uu^3) yy +
  aa^3 uu^2 + 2 aa^2 uu^3;

checks = <|"xact_loaded" -> xactLoaded,
  "interpolation_matrix_nonsingular_on_interior" -> determinantOK && deltaPositive,
  "delta_positive" -> deltaPositive,
  "lower_order_factor_nonnegative" -> lowerOrderSign,
  "upper_order_factor_nonpositive" -> upperOrderSign|>;
details = <|"determinant" -> ToString[InputForm[Factor[Det[matrix]]]],
  "disc" -> ToString[InputForm[disc]],
  "xact_package_file" -> ToString[FindFile["xAct`xTensor`"]],
  "wolfram_version" -> System`$Version|>;

Do[
  equations = {
    c0 + c3 aa^3 + c4 aa^4 == aa^power,
    c0 + c3 uu^3 + c4 uu^4 == uu^power,
    3 c3 uu^2 + 4 c4 uu^3 == power uu^(power - 1)};
  solutions = Solve[equations, {c0, c3, c4}];
  unique = Length[solutions] === 1;
  coeff = If[unique, solutions[[1]], {}];
  q = If[unique, Cancel[(c0 + c3 yy^3 + c4 yy^4) /. coeff], 0];
  independentFactor = If[unique, Factor[Cancel[disc (yy^power - q)]], 0];
  quotient = If[unique,
    Cancel[independentFactor/((yy - aa) (yy - uu)^2)], 0];
  prefix = "p" <> ToString[power] <> "_";
  checks[prefix <> "unique_generic_solution"] = unique;
  checks[prefix <> "value_at_A"] = unique && exactZero[(q /. yy -> aa) - aa^power];
  checks[prefix <> "value_at_U"] = unique && exactZero[(q /. yy -> uu) - uu^power];
  checks[prefix <> "derivative_at_U"] = unique &&
    exactZero[(D[q, yy] /. yy -> uu) - power uu^(power - 1)];
  checks[prefix <> "independent_factor_matches_SE3_SE5"] = unique &&
    exactZero[quotient - targetP[power]] &&
    exactZero[disc (yy^power - q) - independentFactor];
  checks[prefix <> "positive_quotient"] = TrueQ[Resolve[
    ForAll[{aa, uu, yy}, Implies[aa > 0 && uu > 0 && yy >= 0,
      targetP[power] > 0]], Reals]];
  checks[prefix <> "moment_identity"] = unique &&
    exactZero[((1 - ww) (q /. yy -> aa) + ww (q /. yy -> uu)) -
      ((c0 /. coeff) + (c3 /. coeff) ((1 - ww) aa^3 + ww uu^3) +
      (c4 /. coeff) ((1 - ww) aa^4 + ww uu^4))] &&
    exactZero[((1 - ww) (q /. yy -> aa) + ww (q /. yy -> uu)) -
      ((1 - ww) aa^power + ww uu^power)] &&
    exactZero[q - ((c0 + c3 yy^3 + c4 yy^4) /. coeff)];
  (* For an arbitrary probability measure, linearity sends 1,y^3,y^4 to
     1,m3,m4. The weight check is conditional on admitted moment matching. *)
  momentFunctional[poly_] := Coefficient[poly, yy, 0] +
    Coefficient[poly, yy, 3] m3 + Coefficient[poly, yy, 4] m4;
  checks[prefix <> "arbitrary_measure_conditional_identity"] = unique &&
    exactZero[momentFunctional[q] -
      ((c0 + c3 m3 + c4 m4) /. coeff)] &&
    And @@ (exactZero[Coefficient[q, yy, #]] & /@ {1, 2, 5, 6});
  checks[prefix <> "upper_two_node_attainment_conditional"] = unique &&
    exactZero[ww (q /. yy -> aa) + (1 - ww) (q /. yy -> uu) -
      (ww aa^power + (1 - ww) uu^power)];
  boundaryQ = If[unique, Limit[q, uu -> aa], 0];
  boundaryP = targetP[power] /. uu -> aa;
  checks[prefix <> "boundary_polynomial_specialization"] = unique &&
    exactZero[(6 aa^2) (yy^power - boundaryQ) -
      (yy - aa)^3 boundaryP] &&
    TrueQ[Resolve[ForAll[aa, Implies[aa > 0, 6 aa^2 > 0]], Reals]];
  lowerNumeric = N[(yy^power - q) /. {aa -> 1, uu -> 2, yy -> 3}, 80];
  upperNumeric = N[(yy^power - q) /. {aa -> 3, uu -> 2, yy -> 1}, 80];
  checks[prefix <> "numeric_vectors_80_digit"] =
    TrueQ[lowerNumeric > 0 && upperNumeric < 0] &&
    TrueQ[Abs[N[(disc (yy^power - q) -
      (yy - aa) (yy - uu)^2 targetP[power]) /.
      {aa -> 1, uu -> 2, yy -> 3}, 80]] < 10^-50] &&
    TrueQ[Abs[N[(disc (yy^power - q) -
      (yy - aa) (yy - uu)^2 targetP[power]) /.
      {aa -> 3, uu -> 2, yy -> 1}, 80]] < 10^-50];
  details[prefix <> "coefficients"] = ToString[InputForm[coeff]];
  details[prefix <> "independent_factor"] = ToString[InputForm[independentFactor]];
  details[prefix <> "boundary_Q"] = ToString[InputForm[boundaryQ]];
  details[prefix <> "lower_numeric"] = ToString[InputForm[lowerNumeric]];
  details[prefix <> "upper_numeric"] = ToString[InputForm[upperNumeric]];
, {power, {5, 6}}];

payload = <|"checks" -> checks, "details" -> details,
  "domain_assumption_diff" -> {}, "counterexample" -> Null|>;
Export[output, payload, "RawJSON"];
Exit[If[And @@ Values[checks], 0, 1]];
