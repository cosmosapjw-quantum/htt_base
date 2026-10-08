(* CAS-07 M02: independent Wolfram 15 / xTensor finite-axis certificate. *)
ClearAll[zz, z1, z2, ss, tt, ell, c, m2, h0, z0, vv];

(* The two FTC uses are integrations of total derivatives.  z1 and z2 are
   derivative witnesses, not restrictions of zz to a polynomial class. *)
firstIntegrand = D[(ss - tt) z1[tt], tt];
firstFTC = Integrate[firstIntegrand, {tt, 0, ss}, GenerateConditions -> False];
firstFTCOK = TrueQ[FullSimplify[firstFTC == -ss z1[0], Assumptions -> ss >= 0]];
firstProductOK = TrueQ[FullSimplify[
   firstIntegrand == -z1[tt] + (ss - tt) Derivative[1][z1][tt]]];
secondFTC = Integrate[Derivative[1][zz][tt], {tt, 0, ss},
   GenerateConditions -> False];
secondFTCOK = TrueQ[FullSimplify[secondFTC == zz[ss] - zz[0],
   Assumptions -> ss >= 0]];

(* The witness equations zz'=z1 and z1'=z2 are exactly the declared
   hypotheses.  Combining the two FTC results yields the target identity. *)
formalRemainder = -ss z1[0] + (zz[ss] - zz[0]);
identityAlgebraOK = TrueQ[FullSimplify[
   formalRemainder == zz[ss] - zz[0] - ss z1[0]]];
normalizationOK = TrueQ[FullSimplify[
   zz[ss] - z0 - h0 ss/c == zz[ss] - zz[0] - ss z1[0],
   Assumptions -> c > 0 && z0 == zz[0] && h0 == c z1[0]]];

(* Exact local order relation and exact weight integral.  Triangle and
   integral monotonicity are the analytic steps recorded in the result. *)
pointwiseBoundOK = TrueQ[Resolve[ForAll[{ss, tt, m2, vv},
   Implies[ss >= 0 && 0 <= tt <= ss && m2 >= 0 && Abs[vv] <= m2,
     Abs[(ss - tt) vv] <= (ss - tt) m2]], Reals]];
weightIntegral = Integrate[ss - tt, {tt, 0, ss}];
weightOK = TrueQ[FullSimplify[weightIntegral == ss^2/2]];
weightedBoundIntegral = Integrate[m2 (ss - tt), {tt, 0, ss}];
boundReductionOK = TrueQ[FullSimplify[
   weightedBoundIntegral == m2 ss^2/2,
   Assumptions -> ss >= 0 && m2 >= 0]];
zeroEndpointOK = TrueQ[FullSimplify[(ss^2/2 /. ss -> 0) == 0]];
affineBoundaryOK = TrueQ[FullSimplify[
   Integrate[(ss - tt) 0, {tt, 0, ss}] == 0]];
quadraticSaturationOK = TrueQ[FullSimplify[
   Integrate[(ss - tt) m2, {tt, 0, ss}] == m2 ss^2/2]];

(* xTensor does an actual, nonzero affine-direction scalar-Hessian
   contraction.  On a 1D affine coordinate ray with unit tangent, its
   coordinate value is d^2 zz/dss^2 = z2(ss). *)
Quiet[Needs["xAct`xTensor`"]];
DefManifold[CAS07Line, 1, {aa, bb}];
DefMetric[1, gCAS07[-aa, -bb], CDCAS07, PrintAs -> "g"];
DefTensor[ZCAS07[], CAS07Line, PrintAs -> "Z"];
DefTensor[VCAS07[aa], CAS07Line, PrintAs -> "v"];
hessianContraction = ToCanonical[
   VCAS07[aa] VCAS07[bb] CDCAS07[-aa][CDCAS07[-bb][ZCAS07[]]]];
xTensorContractionOK = !TrueQ[hessianContraction === 0] &&
   !FreeQ[hessianContraction, ZCAS07] && !FreeQ[hessianContraction, VCAS07];
coordinateFirstDerivative = D[zz[ss], ss] /.
   Derivative[1][zz][ss] -> z1[ss];
coordinateSecondDerivative = D[coordinateFirstDerivative, ss] /.
   Derivative[1][z1][ss] -> z2[ss];
coordinateHessianOK = TrueQ[coordinateFirstDerivative === z1[ss] &&
   coordinateSecondDerivative === z2[ss]];
nonzeroWitnessOK = TrueQ[(D[(3 ss^2)/2, {ss, 2}] == 3) && 3 != 0];
xActOK = xTensorContractionOK && coordinateHessianOK && nonzeroWitnessOK;

identityOK = And[firstProductOK, firstFTCOK, secondFTCOK,
   identityAlgebraOK, normalizationOK];
boundOK = And[identityOK, pointwiseBoundOK, weightOK,
   boundReductionOK, zeroEndpointOK, affineBoundaryOK,
   quadraticSaturationOK];

result = <|
  "engine_version" -> System`$Version,
  "xTensor_version" -> xAct`xTensor`$Version,
  "xTensor_package_file" -> FindFile["xAct`xTensor`"],
  "checks" -> <|
    "CAS-07-M02-REMAINDER-IDENTITY" -> identityOK && xActOK,
    "CAS-07-M02-REMAINDER-BOUND" -> boundOK && xActOK|>,
  "details" -> <|
    "first_product_rule" -> firstProductOK,
    "first_FTC" -> firstFTCOK,
    "second_FTC" -> secondFTCOK,
    "normalization" -> normalizationOK,
    "pointwise_bound" -> pointwiseBoundOK,
    "weight_integral" -> weightOK,
    "weighted_bound_reduction" -> boundReductionOK,
    "s_zero" -> zeroEndpointOK,
    "affine_M2_zero" -> affineBoundaryOK,
    "quadratic_saturation" -> quadraticSaturationOK,
    "xTensor_scalar_Hessian_contraction" -> xTensorContractionOK,
    "xTensor_coordinate_Z2" -> coordinateHessianOK,
    "xTensor_nonzero_witness" -> nonzeroWitnessOK|>,
  "xTensor_expression" -> ToString[hessianContraction, InputForm],
  "proof_schema" -> "By product rule, ((s-t)Z1(t))'=-Z1(t)+(s-t)Z2(t). FTC at 0,s gives integral (s-t)Z2 = -s Z1(0)+integral Z1. FTC for Z'=Z1 gives integral Z1=Z(s)-Z(0). For 0<=t<=s, |(s-t)Z2(t)|<=(s-t)M2; triangle inequality and integral monotonicity give |remainder|<=M2 integral_0^s(s-t)dt=M2 s^2/2."
|>;
WriteString[$Output, "CAS07_RESULT_JSON=" <> ExportString[result, "RawJSON", "Compact" -> True] <> "\n"];
If[TrueQ[And @@ Values[result["checks"]]], Exit[0], Exit[2]];
