(* CAS-10-C04, independent Wolfram/xTensor axis. Exact real arithmetic only. *)
Needs["xAct`xTensor`"];
Print["WOLFRAM_VERSION=", System`$Version];
Print["XTENSOR_VERSION=", xAct`xTensor`$Version];

Clear[t, f];
f[t_] := 1 - 10 t^3 + 15 t^4 - 6 t^5;
fp = Expand[D[f[t], t]];
fpp = Expand[D[f[t], {t, 2}]];
fppp = Expand[D[f[t], {t, 3}]];
rminus = (3 - Sqrt[3])/6;
rplus = (3 + Sqrt[3])/6;

endpointJets = {
  f[0] == 1, f[1] == 0,
  (fp /. t -> 0) == 0, (fp /. t -> 1) == 0,
  (fpp /. t -> 0) == 0, (fpp /. t -> 1) == 0
};
factorIdentities = FullSimplify /@ {
  Factor[fp] == -30 t^2 (1 - t)^2,
  Factor[fpp] == -60 t (1 - t) (1 - 2 t),
  Factor[fppp] == -60 (1 - 6 t + 6 t^2)
};

(* Critical points of F' and F''; endpoints and the zero of F'' are included
   explicitly for absolute extrema. No numerical maximization is used. *)
criticalFirst = Sort[t /. Solve[fpp == 0, t, Reals]];
criticalSecond = Sort[t /. Solve[fppp == 0, t, Reals]];
candidatesFirst = Sort[DeleteDuplicates[Join[{0, 1}, criticalFirst]]];
candidatesSecond = Sort[DeleteDuplicates[Join[{0, 1, 1/2}, criticalSecond]]];
valuesFirst = FullSimplify[Abs[fp /. t -> #]] & /@ candidatesFirst;
valuesSecond = FullSimplify[Abs[fpp /. t -> #]] & /@ candidatesSecond;

candidateChecks = {
  criticalFirst === {0, 1/2, 1},
  FullSimplify[criticalSecond == {rminus, rplus}],
  candidatesFirst === {0, 1/2, 1},
  Sort[candidatesSecond] === Sort[{0, rminus, 1/2, rplus, 1}],
  valuesFirst === {0, 15/8, 0},
  Sort[valuesSecond] === Sort[{0, 10/Sqrt[3], 0, 10/Sqrt[3], 0}]
};

(* Universal exact bounds establish that these candidate maxima are global;
   the equality implications establish every maximizer on the closed domain. *)
globalFirst = Resolve[ForAll[t, 0 <= t <= 1,
  fp^2 <= (15/8)^2], Reals];
maximizersFirst = Resolve[ForAll[t,
  0 <= t <= 1 && fp^2 == (15/8)^2, t == 1/2], Reals];
globalSecond = Resolve[ForAll[t, 0 <= t <= 1,
  fpp^2 <= (10/Sqrt[3])^2], Reals];
maximizersSecond = Resolve[ForAll[t,
  0 <= t <= 1 && fpp^2 == (10/Sqrt[3])^2,
  t == rminus || t == rplus], Reals];

margin = (25/24) (14/15 + 9/400);
marginCheck = margin == 1147/1152 && margin < 1;
checks = Join[endpointJets, factorIdentities, candidateChecks,
  {globalFirst, maximizersFirst, globalSecond, maximizersSecond, marginCheck}];

Print["FP=", InputForm[fp]];
Print["FPP=", InputForm[fpp]];
Print["FPPP=", InputForm[fppp]];
Print["CRITICAL_FIRST=", InputForm[criticalFirst]];
Print["CRITICAL_SECOND=", InputForm[criticalSecond]];
Print["CANDIDATES_FIRST=", InputForm[candidatesFirst]];
Print["VALUES_FIRST=", InputForm[valuesFirst]];
Print["CANDIDATES_SECOND=", InputForm[candidatesSecond]];
Print["VALUES_SECOND=", InputForm[valuesSecond]];
Print["GLOBAL_FIRST=", InputForm[globalFirst]];
Print["MAXIMIZERS_FIRST=", InputForm[maximizersFirst]];
Print["GLOBAL_SECOND=", InputForm[globalSecond]];
Print["MAXIMIZERS_SECOND=", InputForm[maximizersSecond]];
Print["MARGIN=", InputForm[margin]];
Print["CHECKS=", InputForm[checks]];

result = <|
  "checks" -> <|"CAS-10-C04" -> TrueQ[And @@ checks]|>,
  "domain_assumption_diff" -> {}, "counterexample" -> Null|>;
Print["RESULT_JSON=", ExportString[result, "RawJSON", "Compact" -> True]];
If[!TrueQ[And @@ checks], Exit[1]];
Exit[0];
