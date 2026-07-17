(* PR-124 CAS axis: Wolfram — independent exact verification of the MES
   geodesic reduction statement (contract CAS-PR124-MES-GEODESIC-001).
   Implements the C1/C2 reduction and every exact evaluation from the
   contract-registered raw data with Wolfram Rational arithmetic only.
   Emits one JSON object on stdout; the PR-124 runner wraps it into the
   axis result envelope. *)

rawSigma = {{8/3, 2, 0}, {1, 2, 1}, {5, 1, 1}, {9/7, 3, 1}};
rawOmega = {{9, 1, 1}, {3, 1, 2}, {6/5, 2, 2}};
expectSigma = {5/3, 3, 3/7};
expectOmega = {10/3, 2/15, 0};
e2v = 3559629/10^12;
e3v = 6065291/10^12;
e1obs = 771/625000;
expectW2 = 4223652872547/12500000000000000000000000;
expectSig2 = 6479509460609043/24500000000000000000000000;

reduceRaw[terms_] := Module[{acc = <|1 -> 0, 2 -> 0, 3 -> 0|>},
  Do[acc[t[[2]]] += t[[1]]*(1/3)^t[[3]], {t, terms}];
  {acc[1], acc[2], acc[3]}];

sig = reduceRaw[rawSigma];
om = reduceRaw[rawOmega];

bSigma[e1_, e2_, e3_] := sig[[1]] e1 + sig[[2]] e2 + sig[[3]] e3;
bOmega[e1_, e2_, e3_] := om[[1]] e1 + om[[2]] e2 + om[[3]] e3;

e1crit = e1 /. First@Solve[bSigma[e1, e2, e3] == bOmega[e1, e2, e3], e1];
c2coef = Simplify[Coefficient[e1crit, e2]];
c3coef = Simplify[Coefficient[e1crit, e3]];

bs0 = bSigma[0, e2v, e3v];
bo0 = bOmega[0, e2v, e3v];
w2 = (3/2) bo0^2;
sig2 = (3/2) bs0^2;
e1critNum = e1crit /. {e2 -> e2v, e3 -> e3v};
bsObs = bSigma[e1obs, e2v, e3v];
boObs = bOmega[e1obs, e2v, e3v];

checks = <|
  "sigma_reduction" -> (sig === expectSigma),
  "omega_reduction" -> (om === expectOmega),
  "e1_crit_coefficients" -> (c2coef === 43/25 && c3coef === 9/35),
  "w2_ceiling_exact" -> (w2 === expectW2),
  "sigma2_ceiling_exact" -> (sig2 === expectSig2),
  "hierarchy_e1_zero_strict" -> (bs0 > bo0 > 0),
  "hierarchy_observed_fails" -> (bsObs <= boObs),
  "boundary_e1_crit_equality" ->
    (Simplify[bSigma[e1critNum, e2v, e3v] - bOmega[e1critNum, e2v, e3v]] === 0)
|>;

allPass = And @@ Values[checks];

payload = <|
  "engine" -> "wolfram",
  "engine_version" -> ToString[$VersionNumber],
  "checks" -> checks,
  "computed" -> <|
    "sigma_triple" -> ToString /@ (InputForm /@ sig),
    "omega_triple" -> ToString /@ (InputForm /@ om),
    "e1_crit_coefficients" -> {ToString[InputForm[c2coef]], ToString[InputForm[c3coef]]},
    "B_sigma_exact" -> ToString[InputForm[bs0]],
    "B_omega_exact" -> ToString[InputForm[bo0]],
    "W2_max_exact" -> ToString[InputForm[w2]],
    "Sigma2_max_exact" -> ToString[InputForm[sig2]]
  |>,
  "all_pass" -> allPass
|>;

Print[ExportString[payload, "JSON", "Compact" -> True]];
If[allPass, Exit[0], Exit[1]];
