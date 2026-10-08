(* PORT-CAS-01: independent finite exact algebra, signature (-,+,+,+). *)
Needs["xAct`xTensor`"];

(* Use xTensor's metric contraction for the abstract inverse-metric convention. *)
DefManifold[PortM4, 4, {pa, pb, pc}];
DefMetric[-1, portg[-pa, -pb], PortCD];
xActContraction = ToCanonical[ContractMetric[portg[-pa, -pb] portg[pb, pc]]];
xActCheck = TrueQ[ToCanonical[xActContraction - delta[-pa, pc]] === 0];

beta = {b1, b2, b3};
s = beta.beta;
h = gam^2/(gam + 1);
eta = DiagonalMatrix[{-1, 1, 1, 1}];
boost[v_] := Table[
  Which[
    i == 1 && j == 1, gam,
    i == 1, gam v[[j - 1]],
    j == 1, gam v[[i - 1]],
    True, KroneckerDelta[i, j] + h v[[i - 1]] v[[j - 1]]
  ], {i, 4}, {j, 4}
];
lp = boost[beta];
lm = boost[-beta];
relation = gam^2 (1 - s) - 1;
reduceOnShell[expression_] := TrueQ[
  Together[PolynomialRemainder[Expand[Numerator[Together[expression]]], relation, gam]] === 0
];

metricResidual = Transpose[lp].eta.lp - eta;
inverseResidual = lp.lm - IdentityMatrix[4];
u = lp.{1, 0, 0, 0};
metricEntries = And @@ (reduceOnShell /@ Flatten[metricResidual]);
inverseEntries = And @@ (reduceOnShell /@ Flatten[inverseResidual]);
massShell = reduceOnShell[u.eta.u + 1];
uComponents = TrueQ[u === Prepend[gam beta, gam]];
futureBranch = TrueQ[FullSimplify[
  1/Sqrt[1 - s] > 0 && 1/Sqrt[1 - s] + 1 > 0,
  Element[{b1, b2, b3}, Reals] && s < 1
]];
zeroControl = TrueQ[(lp /. {b1 -> 0, b2 -> 0, b3 -> 0, gam -> 1}) === IdentityMatrix[4]];

zeta = {z1, z2, z3};
r2 = zeta.zeta;
zetaAssumptions = Element[{z0, z1, z2, z3}, Reals] && z0 >= 1 && z0^2 - r2 == 1;
betaConverse = zeta/z0;
converseShell = TrueQ[FullSimplify[z0^2 (1 - betaConverse.betaConverse) - 1 == 0, zetaAssumptions]];
converseDomain = TrueQ[FullSimplify[betaConverse.betaConverse < 1, zetaAssumptions]];
conversePositiveGamma = TrueQ[FullSimplify[
  1/Sqrt[1 - betaConverse.betaConverse] == z0, zetaAssumptions
]];
converseComponents = TrueQ[FullSimplify[
  And @@ Thread[(1/Sqrt[1 - betaConverse.betaConverse]) betaConverse == zeta],
  zetaAssumptions
]];
zetaControl = TrueQ[FullSimplify[
  1/Sqrt[1 - (3/5)^2] == 5/4 && (5/4) {3/5, 0, 0} == {3/4, 0, 0}
]];
sampleBeta = N[{1/5, -1/10, 1/20}, 80];
sampleGamma = N[1/Sqrt[1 - 21/400], 80];
sampleLp = boost[sampleBeta] /. gam -> sampleGamma;
sampleLm = boost[-sampleBeta] /. gam -> sampleGamma;
sampleU = sampleLp.{1, 0, 0, 0};
sampleResiduals = Join[
  Flatten[Transpose[sampleLp].eta.sampleLp - eta],
  Flatten[sampleLp.sampleLm - IdentityMatrix[4]],
  {sampleU.eta.sampleU + 1}
];
numeric80Control = TrueQ[Max[Abs[sampleResiduals]] < 10^-50];

checks = <|
  "xact_metric_contraction" -> xActCheck,
  "metric_16_entries" -> metricEntries,
  "inverse_16_entries" -> inverseEntries,
  "u_components" -> uComponents,
  "mass_shell" -> massShell,
  "future_branch" -> futureBranch,
  "zero_control" -> zeroControl,
  "converse_shell" -> converseShell,
  "converse_domain" -> converseDomain,
  "converse_positive_gamma" -> conversePositiveGamma,
  "converse_components" -> converseComponents,
  "zeta_control" -> zetaControl,
  "numeric_80_digit_control" -> numeric80Control
|>;
Print["WOLFRAM_VERSION=" <> System`$Version];
Print["XACT_VERSION=" <> ToString[xAct`xTensor`$Version, InputForm]];
Print["XACT_PACKAGE_PATH=" <> ToString[FindFile["xAct`xTensor`"], InputForm]];
Print["XACT_VERSION_SYMBOLS=" <> ToString[Names["xAct`xTensor`*Version*"], InputForm]];
Print["PORT_CAS01_CHECKS_JSON=" <> ExportString[checks, "JSON", "Compact" -> True]];
Exit[If[And @@ Values[checks], 0, 2]];
