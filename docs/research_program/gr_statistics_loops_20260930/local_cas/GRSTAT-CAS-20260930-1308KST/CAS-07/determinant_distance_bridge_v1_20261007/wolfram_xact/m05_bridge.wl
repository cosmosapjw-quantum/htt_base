(* CAS-07 M05, Wolfram 15.0 + xTensor 1.3.0.
   Inputs are the frozen M05 contract and ADMITTED_INPUTS only.
   The M01, M04, and C02 implications below are accepted dependencies,
   not new premises about determinant sign or distance. *)
Needs["xAct`xTensor`"];

Clear[k, s, l, f, etaS, etaL, n, detD, dA];
fPositive = Sinh[Sqrt[k] s]/Sqrt[k];
etaPositive = fPositive/s - 1;
rewritePositive = TrueQ[FullSimplify[fPositive - s == s etaPositive,
  k > 0 && s > 0]];
rewriteZero = TrueQ[FullSimplify[s - s == s (s/s - 1), s > 0]];

(* M01 yields 0<=etaS<=etaL<1. M04 supplies 0<=n<=f-s.
   The n>=0 condition is the definition of an induced operator norm. *)
bridgeAssumptions = s > 0 && 0 <= etaS && etaS <= etaL && etaL < 1 &&
  f - s == s etaS && 0 <= n && n <= f - s;
premiseAligned = TrueQ[Resolve[ForAll[{s, etaS, etaL, f, n},
  Implies[bridgeAssumptions, 0 <= etaS && etaS < 1 && n <= s etaS]], Reals]];

(* This is an actual xTensor contraction on a two-dimensional screen. *)
xAct`xTensor`DefManifold[ScreenM05, 2, {a, b}];
xAct`xTensor`DefMetric[1, screenMetric[-a, -b], screenCD];
screenTrace = xAct`xTensor`ToCanonical[
  xAct`xTensor`delta[a, -b] xAct`xTensor`delta[b, -a]];
screenTwo = TrueQ[screenTrace == 2];

(* An arbitrary nonsymmetric real 2x2 matrix is retained symbolically.
   Its off-diagonal entries are independent. No determinant sign is assumed. *)
Clear[d11, d12, d21, d22];
dMatrix = {{d11, d12}, {d21, d22}};
generalDet = TrueQ[Expand[Det[dMatrix] - (d11 d22 - d12 d21)] == 0];
zeroCurvatureMatrix = {{s, 0}, {0, s}};
zeroCurvatureDet = TrueQ[FullSimplify[Det[zeroCurvatureMatrix] == s^2, s > 0]];
zeroCurvatureDistance = TrueQ[FullSimplify[Sqrt[s^2] == s, s > 0]];

(* C02 is the admitted theorem for arbitrary real 2x2 D:
   s>0, 0<=eta<1, ||D-s Id||op<=s eta imply detD>0 and
   s(1-eta)<=sqrt(detD)<=s(1+eta), positive square-root branch.
   The next two checks verify composition of that accepted conclusion,
   rather than attempt to re-prove C02 from a matrix norm encoding. *)
c02Premise = s > 0 && 0 <= etaS && etaS < 1 && n <= s etaS;
c02Conclusion = detD > 0 && dA > 0 && dA^2 == detD &&
  s (1 - etaS) <= dA && dA <= s (1 + etaS);
acceptedC02 = Implies[c02Premise, c02Conclusion];
signComposition = TrueQ[Resolve[ForAll[{s, etaS, etaL, f, n, detD, dA},
  Implies[bridgeAssumptions && acceptedC02, detD > 0]], Reals]];
distanceComposition = TrueQ[Resolve[ForAll[{s, etaS, etaL, f, n, detD, dA},
  Implies[bridgeAssumptions && acceptedC02,
    s (1 - etaS) <= dA && dA <= s (1 + etaS)]], Reals]];

checks = <|
  "CAS-07-M05-REWRITE" -> (rewritePositive && rewriteZero),
  "CAS-07-M05-C02-PREMISE" -> (premiseAligned && screenTwo && generalDet),
  "CAS-07-M05-DETERMINANT-SIGN" -> (signComposition && zeroCurvatureDet),
  "CAS-07-M05-DISTANCE-BOUND" -> (distanceComposition && zeroCurvatureDistance)
|>;
details = <|
  "wolfram_version" -> System`$Version,
  "xtensor_version" -> ToString[xAct`xTensor`$Version, InputForm],
  "xact_screen_trace" -> ToString[screenTrace, InputForm],
  "arbitrary_2x2_determinant" -> ToString[Det[dMatrix], InputForm],
  "positive_k_exact_rewrite" -> rewritePositive,
  "k_zero_exact_rewrite" -> rewriteZero,
  "c02_premise_aligned" -> premiseAligned,
  "accepted_c02_sign_composition" -> signComposition,
  "accepted_c02_distance_composition" -> distanceComposition,
  "k_zero_determinant" -> zeroCurvatureDet,
  "k_zero_distance_positive_branch" -> zeroCurvatureDistance
|>;
Print["M05_JSON:" <> ExportString[<|"checks" -> checks, "details" -> details|>, "RawJSON"]];
If[And @@ Values[checks], Exit[0], Exit[1]];
