Block[{$Output = {}}, Needs["xAct`xTensor`"]];

d = s + (1 - s) z;
sigma = s/d;
omega = (1 - s) z/d;
sigmaPrime = Together[3 z D[sigma, z]];
logHPrime = -3 + (3/2) (1 - s) z/d;

gaussCheck = FullSimplify[Together[sigma + omega - 1] == 0,
  Assumptions -> {d != 0}];
logisticCheck = FullSimplify[
  Together[sigmaPrime + 3 sigma (1 - sigma)] == 0,
  Assumptions -> {d != 0}];
hubbleCheck = FullSimplify[
  Together[logHPrime + (3/2) (1 + sigma)] == 0,
  Assumptions -> {d != 0}];

componentVector[sv_, tv_] := <|
  "Sigma2" -> 1/10 + tv/50,
  "W2" -> 3/100 + 3 tv/200,
  "Omega_tilt" -> 1/50 + sv/100,
  "DeltaOmega_k" -> -1/100 + sv/100 - tv/200
|>;
candidate[x_] := <|
  "Sigma2" -> x, "W2" -> 0, "Omega_tilt" -> 0,
  "DeltaOmega_k" -> 0
|>;
xC[v_] := v["Sigma2"] - v["W2"] + v["Omega_tilt"] +
  v["DeltaOmega_k"];
gap[a_, b_] := Max[Abs /@ (Values[a] - Values[b])];

lowerTarget = componentVector[0, -2/3];
upperTarget = componentVector[1, 0];
lowerCandidate = candidate[2/25];
upperCandidate = candidate[1/10];
lowerGap = gap[lowerTarget, lowerCandidate];
upperGap = gap[upperTarget, upperCandidate];

lowerCheck = xC[lowerTarget] == xC[lowerCandidate] == 2/25 &&
  lowerGap == 1/50 && lowerTarget["Omega_tilt"] == 1/50;
upperCheck = xC[upperTarget] == xC[upperCandidate] == 1/10 &&
  upperGap == 3/100 && upperTarget["Omega_tilt"] == 3/100;

checks = <|
  "dust_gauss_constraint_identity" -> TrueQ[gaussCheck],
  "dust_logistic_evolution_identity" -> TrueQ[logisticCheck],
  "dust_hubble_evolution_identity" -> TrueQ[hubbleCheck],
  "lower_scalar_match_component_gap" -> TrueQ[lowerCheck],
  "upper_scalar_match_component_gap" -> TrueQ[upperCheck]
|>;
computed = <|
  "lower_x_c" -> "2/25", "upper_x_c" -> "1/10",
  "lower_component_gap" -> "1/50", "upper_component_gap" -> "3/100"
|>;
payload = <|
  "checks" -> checks,
  "domain_assumption_diff" -> {},
  "computed" -> computed,
  "counterexample" -> Null
|>;
WriteString[$Output, ExportString[payload, "RawJSON"]];
If[And @@ Values[checks], Exit[0], Exit[2]];
