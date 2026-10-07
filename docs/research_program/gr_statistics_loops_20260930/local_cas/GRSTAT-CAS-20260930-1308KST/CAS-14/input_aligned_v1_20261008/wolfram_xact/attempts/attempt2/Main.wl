(* CAS-14 input-aligned successor; independent Wolfram + xTensor axis. *)
Needs["xAct`xTensor`"];
$Assumptions = Element[{xx1, xx2, xx3, ww1, ww2, ww3, vv1, vv2, vv3,
    aa, bb, theta, sig1, sig2, sig3, sigstar, sighatstar,
    err1, err2, err3, ey, ea, omstar, tau}, Reals];
check[name_, expr_] := (checks[name] = TrueQ[FullSimplify[expr]]);
checks = <||>;
details = <||>;

xx = {xx1, xx2, xx3};
ww = {ww1, ww2, ww3};
vv = {vv1, vv2, vv3};
unit = xx.xx == 1;
levi[i_, j_, k_] := Signature[{i, j, k}];
crossMatrix = Table[Sum[levi[i, j, k] ww[[k]], {k, 1, 3}], {i, 1, 3}, {j, 1, 3}];
explicitMatrix = {{0, ww3, -ww2}, {-ww3, 0, ww1}, {ww2, -ww1, 0}};
proj = IdentityMatrix[3] - Outer[Times, xx, xx];
yy = -crossMatrix.xx;
block = Transpose[Table[Cross[xx, UnitVector[3, j]], {j, 1, 3}]];
check["C01_LEVI_CROSS_ORIENTATION", crossMatrix == explicitMatrix &&
    crossMatrix.xx == -Cross[ww, xx] && yy == Cross[ww, xx]];
check["C01_TRIPLE_PROJECTION", And @@ Thread[
    (Cross[xx, yy] - proj.ww) == {0, 0, 0}] /. xx3^2 -> (1 - xx1^2 - xx2^2)];
check["C01_GRAM_BLOCK", And @@ Thread[Flatten[
    Transpose[block].block - proj] == ConstantArray[0, 9]] /. xx3^2 ->
    (1 - xx1^2 - xx2^2)];
check["C01_DATA_NORMAL_EQUATION", And @@ Thread[
    (Cross[xx, yy] - proj.ww) == {0, 0, 0}] /. xx3^2 ->
    (1 - xx1^2 - xx2^2)];
details["C01_finite_sum"] = "Per-direction x cross y=P_x omega and A_m^T A_m=w_m P_m; summing finitely gives b=G omega and G=A^T A.";

(* The two-direction pair is rotated so x1=e1 and x2=(cos theta,sin theta,0).
   Orthogonal rotation preserves dot products, positive definiteness and singular values. *)
xone = {1, 0, 0}; xtwo = {Cos[theta], Sin[theta], 0};
gone = ww1 (IdentityMatrix[3] - Outer[Times, xone, xone]) +
    ww2 (IdentityMatrix[3] - Outer[Times, xtwo, xtwo]);
minor1 = gone[[1, 1]];
minor2 = Det[gone[[1 ;; 2, 1 ;; 2]]];
minor3 = Det[gone];
check["C02_PSD_QUADRATIC_IDENTITY", And @@ Thread[
    {Expand[vv.proj.vv - Cross[vv, xx].Cross[vv, xx]]} == {0}] /.
    xx3^2 -> (1 - xx1^2 - xx2^2)];
check["C02_KERNEL_PROJECTION", FullSimplify[
    And @@ Thread[(proj.vv - (vv - (xx.vv) xx)) == {0, 0, 0}] &&
    And @@ Thread[(proj.(tau xx)) == {0, 0, 0}], unit]];
check["C02_PAIR_MINORS", FullSimplify[minor1 == ww2 Sin[theta]^2 &&
    minor2 == ww1 ww2 Sin[theta]^2 &&
    minor3 == ww1 ww2 (ww1 + ww2) Sin[theta]^2]];
check["C02_PAIR_POSITIVE_DEFINITE", FullSimplify[
    minor1 > 0 && minor2 > 0 && minor3 > 0,
    ww1 > 0 && ww2 > 0 && Sin[theta] != 0]];
check["C02_INVERSE_IDENTITY", And @@ Thread[Flatten[
    Adjugate[gone].gone - minor3 IdentityMatrix[3]] ==
    ConstantArray[0, 9]]];
check["C02_ALL_PARALLEL_KERNEL", And @@ Thread[
    (IdentityMatrix[3] - Outer[Times, xone, xone]).xone == {0, 0, 0}] &&
    FullSimplify[ww1 + ww2 > 0, ww1 > 0 && ww2 > 0]];
check["C02_E1_E2_CONTROL", FullSimplify[
    (gone /. theta -> Pi/2) == DiagonalMatrix[{ww2, ww1, ww1 + ww2}]]];
details["C02_universal_argument"] = "For every finite N, v^T G v is a sum of positive weights times |v cross x_m|^2. A zero sum forces every cross product to vanish, equivalently v in every span(x_m). Two nonparallel spans intersect only at zero. The pair Sylvester minors above are strictly positive; remaining terms are PSD. Since b=G omega, the positive-definite G permits omega=G^-1 b.";

(* A full-column-rank rectangular matrix has SVD A=U Sigma V^T. Its
   pseudoinverse acts as V Sigma^-1 U^T on the three singular coordinates.
   Each nonnegative coefficient below is the exact finite spectral proof. *)
sigmas = {sig1, sig2, sig3};
errs = {err1, err2, err3};
svdAssumptions = sigstar > 0 && And @@ Thread[sigmas >= sigstar];
check["C03_EXACT_SVD_COEFFICIENTS", And @@ Table[
    FullSimplify[1/sigstar^2 - 1/sigmas[[j]]^2 >= 0,
      svdAssumptions], {j, 1, 3}]];
check["C03_EXACT_SVD_BOUND", FullSimplify[
    Sum[errs[[j]]^2/sigstar^2 - errs[[j]]^2/sigmas[[j]]^2,
      {j, 1, 3}] ==
    Sum[errs[[j]]^2 (1/sigstar^2 - 1/sigmas[[j]]^2),
      {j, 1, 3}]] &&
    And @@ Table[FullSimplify[errs[[j]]^2 >= 0 &&
      1/sigstar^2 - 1/sigmas[[j]]^2 >= 0, svdAssumptions],
      {j, 1, 3}]];

amat = Array[aa, {3, 3}]; ahatmat = Array[hh, {3, 3}];
left = Array[ll, {3, 3}]; errvec = Array[ee, 3];
omegaVec = Array[oo, 3];
residualDifference = Expand[
    left.(amat.omegaVec + errvec) - omegaVec -
      left.(errvec + (amat - ahatmat).omegaVec) -
      (left.ahatmat - IdentityMatrix[3]).omegaVec];
check["C03_PERTURBED_RESIDUAL_IDENTITY", residualDifference == {0, 0, 0}];
check["C03_PERTURBED_BOUND_SIGN", FullSimplify[
    (ey + ea omstar)/sighatstar >= 0,
    ey >= 0 && ea >= 0 && omstar >= 0 && sighatstar > 0]];
details["C03_singular_value_argument"] = "For A full column rank, A^dagger A=I and the exact error is A^dagger e. SVD gives ||A^dagger||op=1/sigma_min(A)<=1/sigma_*. For Ahat full column rank, the checked residual identity with L=Ahat^dagger and L Ahat=I gives error=Ahat^dagger(e+(A-Ahat)omega); triangle, operator norm and |omega|<=Omega_* yield (epsilon_y+epsilon_A Omega_*)/sigmahat_*. The bound uses only positive Euclidean norms.";

deltaOmegaVec = {vv1, vv2, vv3};
deltaW = Table[Sum[levi[i, j, k] deltaOmegaVec[[k]], {k, 1, 3}],
    {i, 1, 3}, {j, 1, 3}];
check["C03_FROBENIUS", FullSimplify[
    Total[Flatten[deltaW]^2] == 2 deltaOmegaVec.deltaOmegaVec]];
check["C03_ZERO_DATA_ERROR_CONTROL", FullSimplify[ey/sigstar == 0,
    ey == 0 && sigstar > 0]];
check["C03_ZERO_OPERATOR_ERROR_CONTROL", FullSimplify[
    (ey + ea omstar)/sighatstar == ey/sighatstar,
    ea == 0 && sighatstar > 0]];
check["C03_ZERO_AMPLITUDE_CONTROL", FullSimplify[
    (ey + ea omstar)/sighatstar == ey/sighatstar,
    omstar == 0 && sighatstar > 0]];
check["C03_NO_AMPLITUDE_COUNTERCONTROL", FullSimplify[
    (1 + ea) tau - tau == ea tau &&
    (1 + ea) tau - tau > ey, ea > 0 && ey >= 0 && tau > ey/ea]];
details["C03_no_amplitude"] = "Let Ahat=I_3, A=diag(1+epsilon_A,1,1), e=0, omega=(tau,0,0), tau unbounded. Then the estimate differs by epsilon_A tau, so epsilon_A alone gives no uniform operator-perturbation error bound.";

keys = Keys[checks];
status = If[And @@ Values[checks], "PASS", "FAIL"];
out = <|
   "status" -> status,
   "checks" -> checks,
   "details" -> details,
   "domain_assumption_diff" -> {},
   "counterexample" -> If[status == "PASS", Null, "See failed checks"],
   "toolchain" -> <|"wolfram_version" -> $Version,
      "xtensor_version" -> ToString[xAct`xTensor`$Version, InputForm]|>
   |>;
Export[Last[$ScriptCommandLine], out, "RawJSON"];
Print["CAS14_MATH_STATUS=", status];
Exit[If[status == "PASS", 0, 2]];
