(* CAS-10-C03 independent finite block rotation and common-covariance KL algebra. *)
Needs["xAct`xTensor`"];
Print["WOLFRAM_VERSION|", $Version];
Print["XTENSOR_VERSION|", ToString[InputForm[xAct`xTensor`$Version]]];

rot = {{0, -1, 0}, {1, 0, 0}, {0, 0, 1}};
p = {15 h/8, 0, 0};
pPrime = {0, 15 h/8, 0};
unchanged = {{a0}, {b1, b2, b3}, {c0}, {d1, d2, d3, d4, d5}};
mu1 = Join[unchanged[[1]], unchanged[[2]], unchanged[[3]], p, unchanged[[4]]];
mu2 = Join[unchanged[[1]], unchanged[[2]], unchanged[[3]], pPrime, unchanged[[4]]];

blockRot = IdentityMatrix[13];
blockRot[[6 ;; 8, 6 ;; 8]] = rot;
sigma = DiagonalMatrix[Join[{s0^2}, ConstantArray[sB^2, 3], {sC^2},
  ConstantArray[sP^2, 3], ConstantArray[sD^2, 5]]];
assumptions = Element[{h, a0, b1, b2, b3, c0, d1, d2, d3, d4, d5,
    s0, sB, sC, sP, sD}, Reals] &&
  s0 > 0 && sB > 0 && sC > 0 && sP > 0 && sD > 0;

norms1 = {mu1[[1]]^2, Total[mu1[[2 ;; 4]]^2], mu1[[5]]^2,
  Total[mu1[[6 ;; 8]]^2], Total[mu1[[9 ;; 13]]^2]};
norms2 = {mu2[[1]]^2, Total[mu2[[2 ;; 4]]^2], mu2[[5]]^2,
  Total[mu2[[6 ;; 8]]^2], Total[mu2[[9 ;; 13]]^2]};
delta = mu1 - mu2;
kl = (delta . Inverse[sigma] . delta)/2;

checks = <|
  "rotation_orthogonal" -> FullSimplify[Transpose[rot].rot == IdentityMatrix[3]],
  "rotation_det_one" -> FullSimplify[Det[rot] == 1],
  "rotation_maps_p" -> FullSimplify[rot.p == pPrime, assumptions],
  "block_rotation_orthogonal" -> FullSimplify[Transpose[blockRot].blockRot == IdentityMatrix[13]],
  "block_rotation_maps_means" -> FullSimplify[blockRot.mu1 == mu2, assumptions],
  "all_five_block_norms" -> FullSimplify[norms1 == norms2, assumptions],
  "covariance_positive" -> FullSimplify[And @@ Map[# > 0 &, Diagonal[sigma]], assumptions],
  "kl_quadratic" -> FullSimplify[kl == 225 h^2/(64 sP^2), assumptions],
  "h_zero_coincident" -> FullSimplify[(mu1 == mu2) /. h -> 0, assumptions],
  "h_zero_kl" -> FullSimplify[(kl /. h -> 0) == 0, assumptions],
  "h_one_sigma_one_kl" -> FullSimplify[(kl /. {h -> 1, sP -> 1}) == 225/64, assumptions]
|>;
KeyValueMap[Print["CHECK|", #1, "|", ToString[InputForm[#2]]] &, checks];
Print["KL_EXPRESSION|", ToString[InputForm[FullSimplify[kl, assumptions]]]];
Print["ALL_PASS|", ToString[InputForm[And @@ Values[checks]]]];
If[TrueQ[And @@ Values[checks]], Exit[0], Exit[2]];
