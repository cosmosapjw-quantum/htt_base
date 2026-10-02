(* Independent CAS-01 Wolfram Engine + xAct axis.  Mathematical inputs are
   EXECUTION_CONTRACT.json and cas/COMMON_SPEC.md only.  Q is derivative-first.
   This script checks finite/local algebra; it does not prove Jacobi or flow ODEs. *)

Needs["xAct`xTensor`"];
Print["CAS_AXIS_VERSION=", System`$Version];
Print["CAS_AXIS_XTENSOR_VERSION=", xAct`xTensor`$Version];

DefManifold[MCAS01, 4, {a, b, d, e, f}];
DefMetric[-1, gg[-a, -b], DD];
DefTensor[uu[a], MCAS01];
DefTensor[SS[-a, -b], MCAS01, Symmetric[{-a, -b}]];
DefTensor[BB[-a, -b], MCAS01, Symmetric[{-a, -b}]];
DefTensor[WW[-a, -b], MCAS01, Antisymmetric[{-a, -b}]];
DefTensor[bb[-a], MCAS01];
DefConstantSymbol[alpha];

unitRules = MakeRule[{uu[a] uu[-a], -1}, MetricOn -> All];
spatialRules = Join[
  unitRules,
  MakeRule[{bb[-a] uu[a], 0}, MetricOn -> All],
  MakeRule[{BB[-a, -b] uu[b], bb[-a]}, MetricOn -> All],
  MakeRule[{WW[-a, -b] uu[b], 0}, MetricOn -> All]
];
reduce[expr_, rr_] := ToCanonical[ToCanonical[ContractMetric[Expand[expr]]] //. rr];
abstractZero[name_, expr_, rr_] := Module[{res = reduce[expr, rr]},
  Print["ABSTRACT ", name, " residual=", InputForm[res]];
  TrueQ[res === 0]
];

(* Generic future unit u.  The future inequality selects a branch and is not
   used as an algebraic replacement. *)
suu = SS[-d, -e] uu[d] uu[e];
be[i_, j_] := SS[i, j] + suu gg[i, j];
shiftSuu = (SS[-d, -e] + alpha gg[-d, -e]) uu[d] uu[e];
c01Abstract = {
  abstractZero["Buu", be[-a, -b] uu[a] uu[b], unitRules],
  abstractZero["shift_invariance",
    SS[-a,-b] + alpha gg[-a,-b] + shiftSuu gg[-a,-b] - be[-a,-b],
    unitRules]
};

(* A fresh finite null-cone kernel elimination.  Universal vanishing implies
   vanishing at all nine listed unit directions.  Their exact linear system
   forces T=-t00 g.  Conversely this form vanishes on the entire null cone. *)
tt = {{t00,t01,t02,t03},{t01,t11,t12,t13},
      {t02,t12,t22,t23},{t03,t13,t23,t33}};
metric = DiagonalMatrix[{-1,1,1,1}];
spatialN = {n1,n2,n3};
kk = Join[{-1}, spatialN];
poly = Expand[kk . tt . kk];
unitDirections = Join[Flatten[Table[{UnitVector[3,i], -UnitVector[3,i]},
  {i,1,3}], 1],
  Table[(UnitVector[3,i] + UnitVector[3,j])/Sqrt[2],
    {i,1,2},{j,i+1,3}] // Flatten[#,1]&];
kernelEquations = Thread[(poly /. Thread[spatialN -> #] & /@ unitDirections) == 0];
kernelUnknowns = {t01,t02,t03,t11,t12,t13,t22,t23,t33};
kernelSolutions = Solve[kernelEquations, kernelUnknowns];
kernelMatrixResidual = If[Length[kernelSolutions] == 1,
  Simplify[tt + t00 metric /. First[kernelSolutions]], $Failed];
kernelSphereResidual = If[Length[kernelSolutions] == 1,
  FullSimplify[poly /. First[kernelSolutions],
    n1^2+n2^2+n3^2 == 1], $Failed];
Print["KERNEL directions=", InputForm[unitDirections]];
Print["KERNEL equations=", InputForm[kernelEquations]];
Print["KERNEL solutions=", InputForm[kernelSolutions]];
Print["KERNEL matrix residual=", InputForm[kernelMatrixResidual]];
Print["KERNEL sphere residual=", InputForm[kernelSphereResidual]];
c01Kernel = Length[kernelSolutions] == 1 &&
  TrueQ[kernelMatrixResidual == ConstantArray[0,{4,4}]] &&
  TrueQ[kernelSphereResidual === 0];

(* Abstract xAct normalization and decomposition, followed by independent
   explicit observer-frame contractions.  The mixed projectors act on the
   covariant slots; no index is raised without gg. *)
qx[i_,j_] := BB[i,j] + bb[i] uu[j] - uu[i] bb[j] + WW[i,j];
projB = (gg[d,-a]+uu[d]uu[-a]) (gg[e,-b]+uu[e]uu[-b]) BB[-d,-e];
thetaX = gg[d,e] BB[-d,-e];
hCov = gg[-a,-b]+uu[-a]uu[-b];
sigmaX = projB - thetaX hCov/3;
c02Abstract = {
  abstractZero["symQ_minus_B", (qx[-a,-b]+qx[-b,-a])/2-BB[-a,-b], spatialRules],
  abstractZero["Q_u", qx[-a,-b] uu[b], spatialRules],
  abstractZero["u_Q_minus_2b", uu[a] qx[-a,-b]-2bb[-b], spatialRules],
  abstractZero["D_projection", projB-BB[-a,-b]-uu[-a]bb[-b]-uu[-b]bb[-a], spatialRules],
  abstractZero["sigma_spatial", sigmaX uu[b], spatialRules],
  abstractZero["sigma_trace", gg[a,b] sigmaX, spatialRules],
  abstractZero["theta_spatial_trace",
    (gg[a,b]+uu[a]uu[b])BB[-a,-b]-gg[a,b]BB[-a,-b], spatialRules]
};

(* Arbitrary symmetric spatial components, arbitrary b_i, and all three
   unconstrained spatial skew components.  W_ij=epsilon_ijk omega_k. *)
urest = {1,0,0,0};
uflat = metric . urest;
brest = {0,b1,b2,b3};
bmat = {{0,b1,b2,b3},{b1,d11,d12,d13},
  {b2,d12,d22,d23},{b3,d13,d23,d33}};
wmat = {{0,0,0,0},{0,0,w3,-w2},
  {0,-w3,0,w1},{0,w2,-w1,0}};
qmat = bmat + Outer[Times,brest,uflat] -
  Outer[Times,uflat,brest] + wmat;
mixedH = IdentityMatrix[4] + Outer[Times,urest,uflat];
dmat = Transpose[mixedH] . bmat . mixedH;
theta = Tr[metric . bmat];
hmat = metric + Outer[Times,uflat,uflat];
sigmat = dmat-theta hmat/3;
accel = c Transpose[qmat] . urest;
omega = {w1,w2,w3};
xx = {x1,x2,x3};
c02Component = {
  TrueQ[Simplify[urest . metric . urest == -1]],
  TrueQ[Simplify[bmat . urest == brest]],
  TrueQ[Simplify[wmat . urest == ConstantArray[0,4]]],
  TrueQ[Simplify[qmat . urest == ConstantArray[0,4]]],
  TrueQ[Simplify[(qmat+Transpose[qmat])/2 == bmat]],
  TrueQ[Simplify[accel == 2c brest]],
  TrueQ[Simplify[dmat . urest == ConstantArray[0,4]]],
  TrueQ[Simplify[Tr[metric . sigmat] == 0]],
  TrueQ[Simplify[sigmat . urest == ConstantArray[0,4]]],
  TrueQ[Simplify[(wmat . Join[{0},xx])[[2;;4]] == -Cross[omega,xx]]]
};
Print["COMPONENT Q=", InputForm[qmat]];
Print["COMPONENT theta=", InputForm[theta]];
Print["COMPONENT sigma=", InputForm[sigmat]];
Print["COMPONENT C02 flags=", InputForm[c02Component]];

(* Observer-rest sourceward K=(-1,n).  Spatial STF S_ij is exact: h233=-h211-h222. *)
sourceK = Join[{-1},spatialN];
restLHS = Expand[sourceK . bmat . sourceK];
restRHS = theta/3 + spatialN . sigmat[[2;;4,2;;4]] . spatialN -
  accel[[2;;4]] . spatialN/c;
restResidual = FullSimplify[restLHS-restRHS,
  n1^2+n2^2+n3^2 == 1 && c > 0];
h2 = {{h211,h212,h213},{h212,h222,h223},
  {h213,h223,-h211-h222}};
sGeneral = {{h0,-h11/2,-h12/2,-h13/2},
  {-h11/2,h211,h212,h213},
  {-h12/2,h212,h222,h223},
  {-h13/2,h213,h223,-h211-h222}};
generalTarget = h0+{h11,h12,h13}.spatialN+spatialN.h2.spatialN;
generalResidual = Expand[sourceK.sGeneral.sourceK-generalTarget];
bGeneral = sGeneral+(urest.sGeneral.urest)metric;
nullInvarianceResidual = FullSimplify[
  sourceK.bGeneral.sourceK-sourceK.sGeneral.sourceK,
  n1^2+n2^2+n3^2 == 1];
Print["C03 rest residual=", InputForm[restResidual]];
Print["C03 general residual=", InputForm[generalResidual]];
Print["C03 null invariance residual=", InputForm[nullInvarianceResidual]];
c03Flags = {TrueQ[restResidual === 0],TrueQ[generalResidual === 0],
  TrueQ[nullInvarianceResidual === 0],TrueQ[Tr[h2] === 0]};

(* At x=0, d_a sqrt[-g(v,v)]=-u_b d_a v^b=-Q_ab u^b/c=0.
   xAct checks the arbitrary-u normalization correction; Mathematica separately
   differentiates the explicit four-component normalized field.  c>0 fixes the
   physical scale and the positive square root evaluates to 1 at the origin. *)
normDerivativeX = -uu[d] qx[-a,-d]/c;
normalizedCorrectionX = uu[b] uu[d] qx[-a,-d]/c;
c04Abstract = {
  abstractZero["norm_first_derivative",normDerivativeX,spatialRules],
  abstractZero["normalized_first_derivative_correction",normalizedCorrectionX,spatialRules]
};
coordinates = {x0,x1,x2,x3};
vfield = urest + metric.Transpose[qmat].coordinates/c;
normField = Sqrt[-vfield.metric.vfield];
unitField = vfield/normField;
atOrigin[expr_] := expr /. Thread[coordinates -> ConstantArray[0,4]];
jetValue = FullSimplify[atOrigin[unitField], c>0];
jetNorm = FullSimplify[atOrigin[normField], c>0];
jetNormDerivatives = Table[FullSimplify[atOrigin[D[normField,coordinates[[i]]]], c>0],{i,1,4}];
jetDerivatives = Table[FullSimplify[atOrigin[D[unitField[[j]],coordinates[[i]]]],c>0],
  {i,1,4},{j,1,4}];
jetTarget = qmat.metric/c;
Print["C04 value=", InputForm[jetValue]];
Print["C04 norm=", InputForm[jetNorm]];
Print["C04 norm derivatives=", InputForm[jetNormDerivatives]];
Print["C04 derivative residual=", InputForm[Simplify[jetDerivatives-jetTarget]]];
c04Component = {
  TrueQ[jetValue == urest],TrueQ[jetNorm === 1],
  TrueQ[jetNormDerivatives == ConstantArray[0,4]],
  TrueQ[Simplify[jetDerivatives-jetTarget] == ConstantArray[0,{4,4}]]
};

checkMap = <|
  "CAS-01-C01" -> And@@Join[c01Abstract,{c01Kernel}],
  "CAS-01-C02" -> And@@Join[c02Abstract,c02Component],
  "CAS-01-C03" -> And@@c03Flags,
  "CAS-01-C04" -> And@@Join[c04Abstract,c04Component]
|>;
detailMap = <|
  "c01_abstract" -> c01Abstract, "c01_kernel" -> c01Kernel,
  "c02_abstract" -> c02Abstract,"c02_component" -> c02Component,
  "c03" -> c03Flags,"c04_abstract" -> c04Abstract,
  "c04_component" -> c04Component
|>;
Print["CAS_AXIS_CHECKS=", InputForm[checkMap]];
outputPath = "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/completion/wolfram_xact/engine_result.json";
Export[outputPath,<|"checks"->checkMap,"details"->detailMap,
  "wolfram_version"->System`$Version,"xTensor_version"->xAct`xTensor`$Version|>,
  "RawJSON"];
If[!FileExistsQ[outputPath],Print["ENGINE_EXPORT_FAILED"];Exit[2]];
Exit[0];
