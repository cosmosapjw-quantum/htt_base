(* CAS-13-C01: independent positive-real power jet, on p>4 and y>0. *)
ClearAll[p, y, psi, c0, c3, c4, q, q3, mismatch, unitMismatch];
$Assumptions = Element[{p, y}, Reals] && p > 4 && y > 0;

xactPath = FindFile["xAct`xTensor`"];
xactLoaded = Quiet[Check[Needs["xAct`xTensor`"] ; True, False]];
xactVersionNames = If[xactLoaded,
  Select[Names["xAct`xTensor`*"], StringContainsQ[ToLowerCase[#], "version"] &], {}];

psi = y^p;
c0 = (p - 3) (p - 4)/12;
c3 = p (4 - p)/3;
c4 = p (p - 3)/4;
q = c0 + c3 y^3 + c4 y^4;
q3 = D[q, {y, 3}];
mismatch = D[psi, {y, 3}] - q3;
unitMismatch = FullSimplify[mismatch /. y -> 1, Element[p, Reals] && p > 4];

eq[a_, b_] := TrueQ[FullSimplify[a == b, $Assumptions]];
checks = <|
  "xact_loaded" -> TrueQ[xactLoaded],
  "branch" -> eq[psi, Exp[p Log[y]]],
  "psi_d1" -> eq[D[psi, y], p y^(p - 1)],
  "psi_d2" -> eq[D[psi, {y, 2}], p (p - 1) y^(p - 2)],
  "psi_d3" -> eq[D[psi, {y, 3}], p (p - 1) (p - 2) y^(p - 3)],
  "q_value_at_1" -> TrueQ[FullSimplify[(q /. y -> 1) == 1, p > 4]],
  "q_d1_at_1" -> TrueQ[FullSimplify[(D[q, y] /. y -> 1) == p, p > 4]],
  "q_d2_at_1" -> TrueQ[FullSimplify[(D[q, {y, 2}] /. y -> 1) == p (p - 1), p > 4]],
  "psi_value_at_1" -> TrueQ[FullSimplify[(psi /. y -> 1) == 1, p > 4]],
  "psi_d1_at_1" -> TrueQ[FullSimplify[(D[psi, y] /. y -> 1) == p, p > 4]],
  "psi_d2_at_1" -> TrueQ[FullSimplify[(D[psi, {y, 2}] /. y -> 1) == p (p - 1), p > 4]],
  "q_d3" -> eq[q3, 2 p (4 - p) + 6 p (p - 3) y],
  "mismatch" -> eq[mismatch,
    p (p - 1) (p - 2) y^(p - 3) - 2 p (4 - p) - 6 p (p - 3) y],
  "unit_mismatch" -> TrueQ[FullSimplify[unitMismatch == p (p - 3) (p - 4), p > 4]],
  "unit_positive_all_p" -> TrueQ[Resolve[ForAll[p,
    Implies[Element[p, Reals] && p > 4, p (p - 3) (p - 4) > 0]], Reals]]
|>;

vectors = {{5, 4/5}, {6, 6/5}};
numeric = Map[
  Function[pair, With[{pp = pair[[1]], yy = pair[[2]]},
  Module[{direct, proposed, residual, scale},
    direct = N[mismatch /. {p -> pp, y -> yy}, 80];
    proposed = N[(p (p - 1) (p - 2) y^(p - 3) -
        2 p (4 - p) - 6 p (p - 3) y) /. {p -> pp, y -> yy}, 80];
    residual = Abs[direct - proposed];
    scale = Max[1, Abs[direct], Abs[proposed]];
    <|"p" -> pp, "y" -> ToString[yy, InputForm],
      "direct80" -> ToString[direct, InputForm],
      "proposed80" -> ToString[proposed, InputForm],
      "absolute_residual" -> ToString[residual, InputForm],
      "absolute_ok" -> TrueQ[residual < 10^-50],
      "relative_ok" -> TrueQ[residual/scale < 10^-40]|>
  ]]], vectors];

all = And @@ Values[checks] &&
  And @@ Flatten[(Lookup[#, {"absolute_ok", "relative_ok"}] & /@ numeric)];
result = <|
  "status" -> If[all, "PASS", If[!TrueQ[xactLoaded], "BLOCKED", "FAIL"]],
  "checks" -> checks,
  "numeric" -> numeric,
  "wolfram_version" -> System`$Version,
  "wolfram_version_number" -> ToString[System`$VersionNumber, InputForm],
  "xact_xtensor_version" -> If[xactLoaded, xAct`xTensor`$Version, "unavailable"],
  "xact_path" -> If[StringQ[xactPath], xactPath, ToString[xactPath, InputForm]],
  "xact_version_symbols" -> xactVersionNames,
  "q_third" -> ToString[FullSimplify[q3], InputForm],
  "mismatch" -> ToString[mismatch, InputForm],
  "unit_mismatch" -> ToString[unitMismatch, InputForm],
  "assumptions" -> "p real >4; y real >0; y^p=Exp[p Log[y]]; dimensionless"
|>;
Print["AXIS_JSON=" <> ExportString[result, "RawJSON", "Compact" -> True]];
Exit[If[all, 0, 1]];
