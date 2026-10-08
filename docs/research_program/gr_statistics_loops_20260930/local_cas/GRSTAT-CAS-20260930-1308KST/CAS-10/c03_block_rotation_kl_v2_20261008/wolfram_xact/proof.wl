(* CAS-10-C03 v2: independent finite block rotation and KL algebra. *)
Needs["xAct`xTensor`"];
Print["WOLFRAM_VERSION=", System`$Version];
Print["XTENSOR_VERSION=", xAct`xTensor`$Version];

(* xTensor checks the Euclidean index contraction used by the slope norm. *)
DefManifold[CAS10M3, 3, {ca, cb, cc, cd}];
DefMetric[1, cas10g[-ca, -cb], cas10D];
tensorContraction = ToCanonical[cas10g[ca, cb] cas10g[-cb, -cc] - delta[ca, -cc]];
xTensorOK = TrueQ[tensorContraction === 0];

r = {{0, -1, 0}, {1, 0, 0}, {0, 0, 1}};
p = {15 h/8, 0, 0};
pp = {0, 15 h/8, 0};
assumptions = Element[h, Reals] && And @@ (Element[#, Reals] && # > 0 & /@ {s0, s1, sm, sp, st});
exactZero[q_] := TrueQ[FullSimplify[q == 0, assumptions]];

orth = exactZero[Total[Flatten[Transpose[r].r - IdentityMatrix[3]]^2]];
detOne = TrueQ[Det[r] == 1];
mapsSlope = exactZero[Total[(r.p - pp)^2]];

(* The five ordered blocks are Z monopole, Z dipole, m, p slope, T. *)
unchanged = {z0, z1, z2, z3, m0, t1, t2, t3, t4, t5};
mu1 = Join[Take[unchanged, 5], p, Drop[unchanged, 5]];
mu2 = Join[Take[unchanged, 5], pp, Drop[unchanged, 5]];
blockR = ArrayFlatten[{{IdentityMatrix[5], ConstantArray[0, {5, 3}], ConstantArray[0, {5, 5}]},
  {ConstantArray[0, {3, 5}], r, ConstantArray[0, {3, 5}]},
  {ConstantArray[0, {5, 5}], ConstantArray[0, {5, 3}], IdentityMatrix[5]}}];
blockOrth = TrueQ[Transpose[blockR].blockR == IdentityMatrix[13]];
blockMaps = exactZero[Total[(blockR.mu1 - mu2)^2]];

norms1 = {mu1[[1]]^2, Total[mu1[[2 ;; 4]]^2], mu1[[5]]^2,
  Total[mu1[[6 ;; 8]]^2], Total[mu1[[9 ;; 13]]^2]};
norms2 = {mu2[[1]]^2, Total[mu2[[2 ;; 4]]^2], mu2[[5]]^2,
  Total[mu2[[6 ;; 8]]^2], Total[mu2[[9 ;; 13]]^2]};
normsAgree = And @@ MapThread[exactZero[#1 - #2] &, {norms1, norms2}];

scales = Join[{s0^2}, ConstantArray[s1^2, 3], {sm^2},
  ConstantArray[sp^2, 3], ConstantArray[st^2, 5]];
sigma = DiagonalMatrix[scales];
sigmaInv = DiagonalMatrix[1/scales];
covarianceInverse = exactZero[Total[Flatten[sigma.sigmaInv - IdentityMatrix[13]]^2]];
covarianceInvariant = exactZero[Total[Flatten[blockR.sigma.Transpose[blockR] - sigma]]^2];
deltaMu = mu1 - mu2;
kl = FullSimplify[(deltaMu.sigmaInv.deltaMu)/2, assumptions];
klExact = exactZero[kl - 225 h^2/(64 sp^2)];
controlZero = TrueQ[FullSimplify[(kl /. h -> 0) == 0, assumptions]];
controlOne = TrueQ[(kl /. {h -> 1, sp -> 1}) == 225/64];
positive = TrueQ[FullSimplify[sp^2 > 0 && kl >= 0, assumptions]];

checks = <|"xTensorEuclideanContraction" -> xTensorOK,
  "rotationOrthogonal" -> orth, "rotationDetOne" -> detOne,
  "rotationMapsSlope" -> mapsSlope, "blockRotationOrthogonal" -> blockOrth,
  "blockRotationMapsMeans" -> blockMaps, "allFiveNormsAgree" -> normsAgree,
  "covarianceInverse" -> covarianceInverse, "covarianceRotationInvariant" -> covarianceInvariant,
  "KLExact" -> klExact, "HZeroControl" -> controlZero,
  "HOneSigmaOneControl" -> controlOne, "positiveDomain" -> positive|>;
Print["CAS10_C03_JSON_BEGIN"];
Print[ExportString[<|"checks" -> checks, "computedKL" -> ToString[InputForm[kl]],
  "tensorContraction" -> ToString[InputForm[tensorContraction]],
  "dimensions" -> {1, 3, 1, 3, 5}, "slopeBlockOneBased" -> 4|>, "RawJSON"]];
Print["CAS10_C03_JSON_END"];
Exit[If[And @@ Values[checks], 0, 2]];
