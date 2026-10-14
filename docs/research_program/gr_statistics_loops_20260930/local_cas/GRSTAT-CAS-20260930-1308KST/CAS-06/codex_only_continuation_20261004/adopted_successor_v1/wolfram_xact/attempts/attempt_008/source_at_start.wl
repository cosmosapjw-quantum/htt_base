(* Independent finite-jet calculation for the owner-adopted CAS-06 contract.
   No target curvature components enter the metric calculation. *)
wolframVersion = $Version;
Needs["xAct`xCoba`"];
$HistoryLength = 0;
ClearAll[rr, tt, th, ph, mm, nn, ee, lam, kap, al, mu, e0, r0, cc, ps, qq, xx];
coords = {tt, rr, th, ph};
ff = 1 - 2 mm[rr]/rr - lam rr^2/3;
gg = DiagonalMatrix[{-Exp[2 nn[rr]], 1/ff, rr^2, rr^2 Sin[th]^2}];
gi = DiagonalMatrix[{-Exp[-2 nn[rr]], ff, 1/rr^2, 1/(rr^2 Sin[th]^2)}];
zeroQ[z_] := TrueQ[Together[z /. {Cot[th]^2 -> Csc[th]^2 - 1,
 Cos[th]^2 -> 1 - Sin[th]^2}] === 0];
mark[s_] := Print["CAS06_STAGE:", s];

(* xCoba derives the metric connection, curvature and Einstein tensor from
   the same admitted metric, independently of the coordinate-array routine. *)
DefManifold[MTOV, 4, {a, b, d, h, j, k}];
DefChart[chTOV, MTOV, {0, 1, 2, 3}, {xt[], xr[], xth[], xph[]}];
DefScalarFunction[nuf];
DefScalarFunction[massf];
metTOV = CTensor[DiagonalMatrix[{-Exp[2 nuf[xr[]]],
   1/(1 - 2 massf[xr[]]/xr[] - lam xr[]^2/3), xr[]^2,
   xr[]^2 Sin[xth[]]^2}], {-chTOV, -chTOV}];
SetCMetric[metTOV, chTOV, SignatureOfMetric -> {3, 1, 0}];
MetricCompute[metTOV, chTOV, All];
mark["xact_metric_computed"];
xactMetric = ToValues[metTOV[-{0, chTOV}, -{0, chTOV}]];
xactInverse = ToValues[metTOV[{0, chTOV}, {0, chTOV}]];
xactMetricOK = zeroQ[xactMetric + Exp[2 nuf[xr[]]]] &&
  zeroQ[xactMetric xactInverse - 1];
xactCD = CovDOfMetric[metTOV];
xactGamma = xactCD[[2, 1]];
xactEinTensor = ToValues[Einstein[xactCD][-a,-b]];
xactEinDiag = Diagonal[xactEinTensor[[0,1]]];
mark["xact_einstein_computed"];
toCoordinate[z_] := z /. {
  Derivative[3][nuf][xr[]] -> Derivative[3][nn][rr],
  Derivative[2][nuf][xr[]] -> Derivative[2][nn][rr],
  Derivative[1][nuf][xr[]] -> Derivative[1][nn][rr],
  Derivative[2][massf][xr[]] -> Derivative[2][mm][rr],
  Derivative[1][massf][xr[]] -> Derivative[1][mm][rr],
  nuf[xr[]] -> nn[rr], massf[xr[]] -> mm[rr],
  xr[] -> rr, xth[] -> th};

gam[i_, j_, k_] := gam[i, j, k] = Together[1/2 Sum[gi[[i, l]]
  (D[gg[[l, j]], coords[[k]]] + D[gg[[l, k]], coords[[j]]] -
   D[gg[[j, k]], coords[[l]]]), {l, 1, 4}]];
rup[i_, j_, k_, l_] := rup[i, j, k, l] = Together[
 D[gam[i, l, j], coords[[k]]] - D[gam[i, k, j], coords[[l]]] +
 Sum[gam[i, k, h] gam[h, l, j] - gam[i, l, h] gam[h, k, j], {h, 1, 4}]];
rlow[i_, j_, k_, l_] := rlow[i, j, k, l] = Together[
 Sum[gg[[i, h]] rup[h, j, k, l], {h, 1, 4}]];
ric[i_, j_] := ric[i, j] = Together[Sum[rup[h, i, h, j], {h, 1, 4}]];
rscalar = Together[Sum[gi[[i, i]] ric[i, i], {i, 1, 4}]];
ein[i_, j_] := ein[i, j] = Together[ric[i, j] - gg[[i, j]] rscalar/2];
weyl[i_, j_, k_, l_] := weyl[i, j, k, l] = Together[
 rlow[i, j, k, l] - (gg[[i, k]] ric[j, l] - gg[[i, l]] ric[j, k] -
 gg[[j, k]] ric[i, l] + gg[[j, l]] ric[i, k])/2 +
 rscalar (gg[[i, k]] gg[[j, l]] - gg[[i, l]] gg[[j, k]])/6];

tovM = kap rr^2 ee[rr]/2;
tovN = (mm[rr] + kap al ee[rr] rr^3/2 - lam rr^3/3)/(rr^2 ff);
tovE = -(1 + al) ee[rr] tovN/al;
jet1 = {Derivative[1][mm][rr] -> tovM,
  Derivative[1][nn][rr] -> tovN, Derivative[1][ee][rr] -> tovE};
tovN2 = Together[D[tovN, rr] /. jet1];
tovM2 = Together[D[tovM, rr] /. jet1];
tovE2 = Together[D[tovE, rr] /. jet1];
tovN3 = Together[D[tovN2, rr] /. {
  Derivative[2][mm][rr] -> tovM2,
  Derivative[2][ee][rr] -> tovE2} /. jet1];
reduce[0] := 0;
reduce[z_] := Module[{w},
 w = z /. Derivative[3][nn][rr] -> tovN3;
 w = w /. Derivative[2][nn][rr] -> tovN2 /.
    Derivative[2][mm][rr] -> tovM2 /.
    Derivative[2][ee][rr] -> tovE2;
 Together[w /. jet1]
];
match[z_] := Together[(z /. {mm[rr] -> mu r0^3, nn[rr] -> 0,
  ee[rr] -> e0, rr -> r0}) /. al -> al];
frame = {Exp[-nn[rr]], Sqrt[ff], 1/rr, 1/(rr Sin[th])};
pairs = Subsets[Range[4], {2}];
orthoR[i_, j_, k_, l_] := Together[rlow[i, j, k, l] frame[[i]] frame[[j]] frame[[k]] frame[[l]]];
orthoW[i_, j_, k_, l_] := Together[weyl[i, j, k, l] frame[[i]] frame[[j]] frame[[k]] frame[[l]]];

einExpected = DiagonalMatrix[{kap ee[rr] Exp[2 nn[rr]],
   kap al ee[rr]/ff, kap al ee[rr] rr^2,
   kap al ee[rr] rr^2 Sin[th]^2}];
riemBivector = Table[reduce[rlow @@ Join[pairs[[i]],pairs[[j]]]],
 {i,1,6},{j,1,6}];
riemGenericSymmetry = And @@ Flatten[Table[
 zeroQ[riemBivector[[i,j]] - riemBivector[[j,i]]],
 {i,1,6},{j,1,6}]];
riemGenericOffDiagonal = And @@ Flatten[Table[
 If[i < j,zeroQ[riemBivector[[i,j]]],True],
 {i,1,6},{j,1,6}]];
c01Residuals = Flatten[Table[reduce[ein[i, j] + lam gg[[i, j]] -
   einExpected[[i, j]]], {i, 1, 4}, {j, i, 4}]];
xactCurvatureResiduals = Table[Together[
 toCoordinate[xactEinDiag[[i]]] - ein[i, i]], {i, 1, 4}];
xactCurvatureAgreement = And @@ (zeroQ /@ xactCurvatureResiduals);
mark["xact_curvature_compared"];
xactConnectionResiduals = Flatten[Table[Together[
 toCoordinate[xactGamma[[i, j, k]]] - gam[i, j, k]],
 {i, 1, 4}, {j, 1, 4}, {k, 1, 4}]];
xactConnectionAgreement = And @@ (zeroQ /@ xactConnectionResiduals);
mark["xact_connection_compared"];
c01 = xactMetricOK && riemGenericSymmetry &&
 riemGenericOffDiagonal && xactCurvatureAgreement &&
 xactConnectionAgreement && And @@ (zeroQ /@ c01Residuals);
mark["c01_finished"];

b0 = mu + kap al e0/2 - lam/3;
c0 = 2 mu + lam/3;
expectedR = {kap (e0 + al e0)/2 - 2 mu - lam/3,
 b0, b0, kap e0/2 - mu + lam/3,
 kap e0/2 - mu + lam/3, c0};
diagonalR = Table[match[reduce[orthoR @@ Join[pairs[[i]], pairs[[i]]]]],
 {i, 1, 6}];
offR = Flatten[Table[If[i < j,
  match[reduce[orthoR @@ Join[pairs[[i]], pairs[[j]]]]],
  Nothing], {i, 1, 6}, {j, 1, 6}]];

(* For U=c e0, the coordinate covariant derivative is computed from Gamma,
   then transformed to the orthonormal frame before taking rates. *)
ucon = {cc Exp[-nn[rr]], 0, 0, 0};
ucov = gg.ucon;
derU[i_, j_] := Together[D[ucov[[j]], coords[[i]]] -
  Sum[gam[h, i, j] ucov[[h]], {h, 1, 4}]];
qhat = Table[reduce[derU[i, j] frame[[i]] frame[[j]]],
  {i, 1, 4}, {j, 1, 4}];
xactRateAgreement = And @@ Flatten[Table[
 zeroQ[reduce[(D[ucov[[j]], coords[[i]]] -
  Sum[toCoordinate[xactGamma[[h, i, j]]] ucov[[h]], {h, 1, 4}])
  frame[[i]] frame[[j]] - qhat[[i, j]]]],
  {i, 1, 4}, {j, 1, 4}]];
ahat = Table[cc match[qhat[[1, j]]], {j, 1, 4}];
accelSquared = Together[Sum[ahat[[j]]^2, {j, 2, 4}]];
rateOK = xactRateAgreement &&
 zeroQ[accelSquared - cc^4 b0^2 r0^2/(1 - c0 r0^2)] &&
 And @@ (zeroQ /@ Flatten[qhat[[2 ;; 4, 2 ;; 4]]]);

(* Derive the full coordinate covariant radial derivative before any matching.
   All 21 independent Weyl components are then tested at the special event. *)
dw[i_, j_, k_, l_] := Together[D[weyl[i, j, k, l], rr] -
 Sum[gam[h, 2, i] weyl[h, j, k, l] +
     gam[h, 2, j] weyl[i, h, k, l] +
     gam[h, 2, k] weyl[i, j, h, l] +
     gam[h, 2, l] weyl[i, j, k, h], {h, 1, 4}]];
dw0101Raw = dw[1, 2, 1, 2];
dw0101 = match[reduce[dw0101Raw frame[[2]] frame[[1]]^2 frame[[2]]^2]];
special[z_] := Together[z /. {lam -> 0, mu -> kap e0/6}];
specialDerivative = FullSimplify[special[dw0101] /. Cot[th]^2 -> Csc[th]^2 - 1,
 Assumptions -> {kap > 0, e0 > 0, r0 > 0, 0 < al < 1,
  1 - kap e0 r0^2/3 > 0, 0 < th < Pi}];
derivativeNonzero = TrueQ[FullSimplify[specialDerivative < 0,
 Assumptions -> {kap > 0, e0 > 0, r0 > 0, 0 < al < 1,
  1 - kap e0 r0^2/3 > 0, 0 < th < Pi}]];
weylPoint = Table[special[match[reduce[orthoW @@ Join[pairs[[i]], pairs[[j]]]]]],
  {i, 1, 6}, {j, i, 6}];
c02 = And @@ (zeroQ /@ MapThread[Subtract, {diagonalR, expectedR}]) &&
 And @@ (zeroQ /@ offR) && rateOK &&
 And @@ (zeroQ /@ Flatten[weylPoint]) && derivativeNonzero;
mark["c02_finished"];

(* Variation at fixed psi is done for each of the ten independent symmetric
   inverse-metric perturbations. The coefficients of delta S derive T_ij. *)
s = (1 + al)/(2 al);
pow = ps xx^s;
px = D[pow, xx]; pxx = D[pow, {xx, 2}];
xrad = qq^2 Exp[-2 nn[rr]]/2;
prad = ps xrad^s;
erad = (2 s - 1) prad;
pxrad = px /. xx -> xrad;
psiGradient = {qq, 0, 0, 0};
deltaInverse = Table[dv[Min[i,j],Max[i,j]], {i,1,4},{j,1,4}];
deltaX = -psiGradient.deltaInverse.psiGradient/2;
deltaVolumeOverVolume = -Tr[gg.deltaInverse]/2;
deltaLOverVolume = pxrad deltaX + prad deltaVolumeOverVolume;
stressAction = Table[-If[i == j, 2, 1]
 Coefficient[deltaLOverVolume, dv[Min[i,j],Max[i,j]]],
 {i,1,4},{j,1,4}];
stressVariationOK = And @@ Flatten[Table[
 zeroQ[stressAction[[i,j]] - (pxrad psiGradient[[i]] psiGradient[[j]] +
  prad gg[[i,j]])], {i,1,4},{j,1,4}]];
varPsi = {v0,v1,v2,v3};
kineticVar = -varPsi.gi.varPsi/2;
currentEL = Table[-D[Pfun[kineticVar],varPsi[[i]]],{i,1,4}];
current = Together[(currentEL /. Thread[varPsi -> psiGradient]) /.
 Derivative[1][Pfun][xrad] -> pxrad];
currentVariationOK = And @@ Table[
 zeroQ[current[[i]] - pxrad Sum[gi[[i,j]] psiGradient[[j]],{j,1,4}]],
 {i,1,4}];
sqrtDet = Exp[nn[rr]] rr^2 Sin[th]/Sqrt[ff];
divJ = Together[Sum[D[sqrtDet current[[i]], coords[[i]]], {i, 1, 4}]/sqrtDet];
xactDivJ = Together[Sum[D[current[[i]], coords[[i]]] +
  Sum[toCoordinate[xactGamma[[i, i, j]]] current[[j]], {j, 1, 4}],
  {i, 1, 4}]];
conservation = Together[D[prad, rr] + (erad + prad) D[nn[rr], rr]];
normRules = {ps (qq^2/2)^s -> al e0};
matchedP = Together[(prad /. nn[rr] -> 0) /. normRules];
matchedE = Together[(erad /. nn[rr] -> 0) /. normRules];
matchedDerivative = Together[(D[erad, rr] /.
  Derivative[1][nn][rr] -> tovN /. {nn[rr] -> 0, mm[rr] -> mu r0^3,
  ee[rr] -> e0, rr -> r0}) /. normRules];
tovDerivative = match[tovE];
matchedSecondDerivative = Together[(D[erad,{rr,2}] /.
 Derivative[2][nn][rr] -> tovN2 /.
 Derivative[1][nn][rr] -> tovN) /.
 {nn[rr]->0,mm[rr]->mu r0^3,ee[rr]->e0,rr->r0} /.
 ps -> al e0/(qq^2/2)^s];
tovSecondDerivative = match[tovE2];
secondJetOK = TrueQ[FullSimplify[
 matchedSecondDerivative == tovSecondDerivative,
 Assumptions -> {qq>0,e0>0,kap>0,0<al<1,r0>0,
 1-(2 mu+lam/3) r0^2>0}]];
matchedStressResiduals = Flatten[Table[
 Together[(match[stressAction[[i,j]]] /.
    ps -> al e0/(qq^2/2)^s) -
  DiagonalMatrix[{e0,al e0,al e0,al e0}][[i,j]]/
  (frame[[i]] frame[[j]] /. {nn[rr]->0,rr->r0,mm[rr]->mu r0^3})],
 {i,1,4},{j,1,4}]];
matchedStressOK = And @@ (TrueQ[FullSimplify[# == 0,
 Assumptions -> {qq > 0, e0 > 0, 0 < al < 1, r0 > 0,
 1 - (2 mu + lam/3) r0^2 > 0, 0 < th < Pi}]]& /@
 matchedStressResiduals);
c03 = stressVariationOK && currentVariationOK && matchedStressOK &&
 zeroQ[divJ] && zeroQ[xactDivJ] &&
 zeroQ[conservation] &&
 zeroQ[2 xx px - pow - (2 s - 1) pow] &&
 zeroQ[px/(px + 2 xx pxx) - al] &&
 zeroQ[matchedP - al e0] && zeroQ[matchedE - e0] &&
 zeroQ[matchedDerivative - tovDerivative] && secondJetOK;
mark["c03_finished"];

ay = cc^2 Abs[b0]/Sqrt[c0] yy/Sqrt[1 - yy^2];
derivedAy = cc^2 Abs[b0] (yy/Sqrt[c0]) /
 Sqrt[1 - c0 (yy/Sqrt[c0])^2];
c04Algebra = FullSimplify[derivedAy == ay,
  Assumptions -> {c0 > 0, 0 < yy < 1, cc > 0}];
c04Limit = Limit[ay, yy -> 1, Direction -> "FromBelow",
 Assumptions -> {cc > 0, c0 > 0, b0 != 0}];
c04 = TrueQ[c04Algebra] && c04Limit === Infinity &&
 TrueQ[FullSimplify[ay > 0 && ay < Infinity,
  Assumptions -> {cc > 0, c0 > 0, b0 != 0, 0 < yy < 1}]];
mark["c04_finished"];

out = <|"checks" -> <|"CAS-06-C01" -> c01,
   "CAS-06-C02" -> c02, "CAS-06-C03" -> c03,
   "CAS-06-C04" -> c04|>, "domain_assumption_diff" -> {},
  "counterexample" -> Null,
  "details" -> <|"wolfram_version" -> wolframVersion,
  "xact_metric" -> ToString[InputForm[xactMetric]],
  "xact_einstein_diagonal" -> ToString[InputForm[xactEinDiag]],
  "xact_curvature_agreement" -> xactCurvatureAgreement,
  "xact_connection_agreement" -> xactConnectionAgreement,
  "xact_curvature_nonzero_residuals" -> ToString[InputForm[Select[xactCurvatureResiduals, !zeroQ[#]&]]],
  "xact_connection_nonzero_residuals" -> ToString[InputForm[Take[Select[xactConnectionResiduals, !zeroQ[#]&], UpTo[4]]]],
  "xact_rate_agreement" -> xactRateAgreement,
  "xact_current_divergence" -> ToString[InputForm[xactDivJ]],
  "c01_coordinate_residuals" -> ToString[InputForm[Select[c01Residuals,!zeroQ[#]&]]],
  "c01_generic_riemann_bivector_diagonal" -> ToString[InputForm[Diagonal[riemBivector]]],
  "c01_generic_riemann_symmetry" -> riemGenericSymmetry,
  "c01_generic_riemann_off_diagonal" -> riemGenericOffDiagonal,
  "c02_rate_ok" -> rateOK,
  "c02_weyl_derivative_nonzero" -> derivativeNonzero,
  "c02_weyl_nonzero_residuals" -> ToString[InputForm[Select[Flatten[weylPoint],!zeroQ[#]&]]],
  "c03_stress_variation_ok" -> stressVariationOK,
  "c03_current_variation_ok" -> currentVariationOK,
  "c03_matched_stress_ok" -> matchedStressOK,
  "c03_matched_stress_residuals" -> ToString[InputForm[Select[matchedStressResiduals,!zeroQ[#]&]]],
  "c03_matched_derivative_residual" -> ToString[InputForm[matchedDerivative-tovDerivative]],
  "c03_matched_second_jet_ok" -> secondJetOK,
  "coordinate_riemann_orthonormal" -> ToString[InputForm[diagonalR]],
  "weyl_radial_covariant_derivative" -> ToString[InputForm[specialDerivative]],
  "action_current_divergence" -> ToString[InputForm[divJ]],
  "acceleration_limit" -> ToString[InputForm[c04Limit]]|>|>;
Export[Environment["CAS06_ENGINE_OUT"], out, "RawJSON"];
Print[ExportString[out, "RawJSON"]];
