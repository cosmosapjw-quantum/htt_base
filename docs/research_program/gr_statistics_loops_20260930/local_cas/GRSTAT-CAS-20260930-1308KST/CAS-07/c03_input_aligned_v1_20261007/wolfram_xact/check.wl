(* CAS-07 C03, frozen input-aligned contract.  No target is assumed in its own proof. *)
$HistoryLength = 0;
ClearAll[ss, dd, ee, el, cc, mm, hh, xx, ll, kk, u, v];

realDomain = Element[{ss, dd, ee, el, cc, mm, hh, xx, ll, kk}, Reals];
premises = realDomain && kk >= 0 && 0 < ss <= ll && cc > 0 &&
  mm >= 0 && dd > 0 && 0 <= ee <= el < 1 &&
  ss (1 - ee) <= dd <= ss (1 + ee) &&
  Abs[xx - hh ss/cc] <= mm ss^2/2;
fd1 = Abs[xx - hh dd/cc] <= mm ss^2/2 + Abs[hh] ss ee/cc;
fd2 = Abs[xx - hh dd/cc] <= mm dd^2/(2 (1 - el)^2) +
  Abs[hh] dd el/(cc (1 - el));
fd3 = Abs[cc xx/dd - hh] <= cc mm ss/(2 (1 - ee)) +
  Abs[hh] ee/(1 - ee);

(* The first three facts are the exact triangle/screen decomposition. *)
screenBound = TrueQ @ FullSimplify[
  Abs[dd - ss] <= ss ee,
  Element[{ss, dd, ee}, Reals] && ss > 0 && ee >= 0 &&
    ss (1 - ee) <= dd <= ss (1 + ee)];
triangle = TrueQ @ Resolve[
  ForAll[{u, v}, Abs[u + v] <= Abs[u] + Abs[v]], Reals];
decomposition = TrueQ @ FullSimplify[
  xx - hh dd/cc == (xx - hh ss/cc) + hh (ss - dd)/cc,
  realDomain && cc > 0];
productAbs = TrueQ @ FullSimplify[
  Abs[hh (ss - dd)/cc] == Abs[hh] Abs[dd - ss]/cc,
  realDomain && cc > 0];

(* Independent exact implication checks, with FD2/FD3 allowed to use proven FD1. *)
screenProductBound = TrueQ @ FullSimplify[
  Abs[hh] Abs[dd - ss]/cc <= Abs[hh] ss ee/cc, premises];
fd1Pass = And[screenBound, triangle, decomposition, productAbs,
  screenProductBound];

positiveDenominators = TrueQ @ FullSimplify[
  0 < 1 - el <= 1 - ee && dd > 0,
  premises];
sScaledUpper = TrueQ @ Resolve[
  ForAll[{ss, dd, ee, el},
    Implies[ss > 0 && 0 <= ee <= el < 1 && dd >= ss (1 - ee),
      ss (1 - el) <= dd]], Reals];
sUpper = TrueQ @ Resolve[
  ForAll[{ss, dd, el},
    Implies[ss > 0 && el < 1 && dd >= ss (1 - el),
      ss <= dd/(1 - el)]], Reals];
etaUpper = TrueQ @ FullSimplify[
  ss ee <= dd el/(1 - el), premises];
quadraticUpper = TrueQ @ Resolve[
  ForAll[{ss, dd, el, mm},
    Implies[ss > 0 && el < 1 && dd >= ss (1 - el) && mm >= 0,
      mm ss^2/2 <= mm dd^2/(2 (1 - el)^2)]], Reals];
linearUpper = TrueQ @ FullSimplify[
  Abs[hh] ss ee/cc <= Abs[hh] dd el/(cc (1 - el)), premises];
fd2Pass = And[fd1Pass, positiveDenominators, sScaledUpper, sUpper,
  etaUpper, quadraticUpper, linearUpper];

fd3Identity = TrueQ @ FullSimplify[
  Abs[cc xx/dd - hh] == cc Abs[xx - hh dd/cc]/dd,
  realDomain && cc > 0 && dd > 0];
fd3Quadratic = TrueQ @ FullSimplify[
  cc mm ss^2/(2 dd) <= cc mm ss/(2 (1 - ee)), premises];
fd3Linear = TrueQ @ FullSimplify[
  Abs[hh] ss ee/dd <= Abs[hh] ee/(1 - ee), premises];
fd3Pass = And[fd1Pass, positiveDenominators, fd3Identity,
  fd3Quadratic, fd3Linear];

(* Exact-rational boundary vectors are ancillary to the universal proof. *)
caseRules[etaValue_, etaLValue_, dValue_, hValue_, mValue_, rValue_] :=
  {ss -> 2, ll -> 3, cc -> 5, kk -> 0, ee -> etaValue,
    el -> etaLValue, dd -> dValue, hh -> hValue, mm -> mValue,
    xx -> 2 hValue/5 + rValue};
casePass[rules_] := And @@ (TrueQ[# /. rules] & /@
  {premises, fd1, fd2, fd3});
boundaryCases = <|
  "eta_zero_dA_equals_s" -> casePass[caseRules[0, 0, 2, 7, 1, 1]],
  "H0_zero" -> casePass[caseRules[1/10, 1/5, 9/5, 0, 1, 1]],
  "M2_zero" -> casePass[caseRules[1/10, 1/5, 11/5, 7, 0, 0]],
  "strict_eta_lower_endpoint" -> casePass[caseRules[1/10, 1/5, 9/5, 7, 1, 1]],
  "strict_eta_upper_endpoint" -> casePass[caseRules[1/10, 1/5, 11/5, 7, 1, 1]]|>;

(* xTensor performs an actual positive one-dimensional metric contraction of
   the screen displacement vector (dd-ss) e^a.  The unit frame component is 1. *)
xActLoaded = Quiet @ Check[Needs["xAct`xTensor`"] ; True, False];
xActPass = False;
xActDetail = "xTensor did not load";
If[xActLoaded,
  xActPass = Quiet @ Check[
    xAct`xTensor`DefManifold[CAS07Screen, 1, {ia, ib}];
    xAct`xTensor`DefMetric[1, cas07g[-ia, -ib], cas07D];
    xAct`xTensor`DefTensor[cas07e[ia], CAS07Screen];
    tensorContraction = xAct`xTensor`ToCanonical @
      xAct`xTensor`ContractMetric[
        (dd - ss)^2 cas07g[-ia, -ib] cas07e[ia] cas07e[ib]];
    tensorExpected = xAct`xTensor`ToCanonical[
      (dd - ss)^2 cas07e[-ia] cas07e[ia]];
    scalarComponent = FullSimplify[
      ({dd - ss}.{{1}}.{dd - ss}) == (dd - ss)^2,
      Element[{dd, ss}, Reals]];
    xActDetail = ToString[InputForm[tensorContraction]];
    TrueQ[xAct`xTensor`ToCanonical[tensorContraction - tensorExpected] === 0] &&
      TrueQ[scalarComponent] && tensorContraction =!= 0,
    False,
  {xAct`xTensor`Validate::inv}];
];

checks = <|
  "CAS-07-C03-FD1" -> <|"pass" -> fd1Pass,
    "screen_bound" -> screenBound, "triangle" -> triangle,
    "decomposition" -> decomposition, "absolute_product" -> productAbs,
    "screen_product_bound" -> screenProductBound|>,
  "CAS-07-C03-FD2" -> <|"pass" -> fd2Pass,
    "positive_denominators" -> positiveDenominators,
    "s_scaled_upper" -> sScaledUpper, "s_upper" -> sUpper,
    "eta_upper" -> etaUpper, "quadratic_upper" -> quadraticUpper,
    "linear_upper" -> linearUpper|>,
  "CAS-07-C03-FD3" -> <|"pass" -> fd3Pass,
    "identity" -> fd3Identity, "quadratic_upper" -> fd3Quadratic,
    "linear_upper" -> fd3Linear|>|>;

result = <|
  "checks" -> checks,
  "xact" -> <|"pass" -> xActPass, "contraction" -> xActDetail,
    "one_dimensional_metric_component" -> 1|>,
  "boundary_cases" -> boundaryCases,
  "domain_assumption_diff" -> {},
  "counterexample" -> If[And[fd1Pass, fd2Pass, fd3Pass, xActPass,
    And @@ Values[boundaryCases]], Null,
    "At least one exact proof or xTensor check did not return True; see checks"],
  "tool_versions" -> <|"wolfram" -> System`$Version,
    "wolfram_version_number" -> System`$VersionNumber,
    "xact_xtensor" -> xAct`xTensor`$Version|>
|>;
WriteString["stdout", "AXIS_JSON:" <>
  ExportString[result, "RawJSON", "Compact" -> True] <> "\n"];
If[And[fd1Pass, fd2Pass, fd3Pass, xActPass,
  And @@ Values[boundaryCases]], Exit[0], Exit[1]];
