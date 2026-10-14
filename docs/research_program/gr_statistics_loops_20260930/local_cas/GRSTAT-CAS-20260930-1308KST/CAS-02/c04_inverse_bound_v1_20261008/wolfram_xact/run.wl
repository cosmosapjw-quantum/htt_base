Needs["xAct`xTensor`"];

mat1 = Array[entry1, {4, 4}];
mat2 = Array[entry2, {4, 4}];
vec1 = Array[component1, 4];
vec2 = Array[component2, 4];
deltaS = mat2 - mat1;
deltaU = vec2 - vec1;
quad[s_, u_] := u.s.u;
deltaQ = quad[mat2, vec2] - quad[mat1, vec1];
g = DiagonalMatrix[{-1, 1, 1, 1}];
b1 = mat1 + quad[mat1, vec1] g;
b2 = mat2 + quad[mat2, vec2] g;

checks = <|
  "inverse_decomposition" -> TrueQ[Expand[b2 - b1 - deltaS - deltaQ g] === ConstantArray[0, {4, 4}]],
  "anchor_S1_identity" -> TrueQ[Expand[deltaQ - (quad[deltaS, vec2] + deltaU.mat1.vec2 + vec1.mat1.deltaU)] === 0],
  "anchor_S2_identity" -> TrueQ[Expand[deltaQ - (quad[deltaS, vec1] + deltaU.mat2.vec2 + vec1.mat2.deltaU)] === 0],
  "metric_frobenius_squared" -> TrueQ[Tr[Transpose[g].g] === 4],
  "positive_chart_norm" -> TrueQ[FullSimplify[(Sqrt[1 + t^2])^2 + t^2 == 1 + 2 t^2, Element[t, Reals] && t >= 0]],
  "hyperbolic_double_angle" -> TrueQ[FullSimplify[Cosh[2 r] == 1 + 2 Sinh[r]^2, Element[r, Reals]]],
  "negative_R_excluded" -> TrueQ[FullSimplify[Sinh[r] < 0, Element[r, Reals] && r < 0]],
  "R0_forces_zero_chart" -> TrueQ[Resolve[ForAll[t, Element[t, Reals] && t >= 0 && t <= Sinh[0] \[Implies] t == 0], Reals]],
  "amplitude_cases_exhaustive" -> TrueQ[Resolve[ForAll[{a, b}, Element[a, Reals] && Element[b, Reals] && a >= 0 && b >= 0 \[Implies] (a <= b || b < a)], Reals]],
  "scalar_constant_arithmetic" -> TrueQ[Expand[e + 2 (m^2 e + 2 m l z) - ((1 + 2 m^2) e + 4 m l z)] === 0],
  "epsilonH_zero_boundary" -> TrueQ[Expand[(1 + 2 m^2) 0 + 4 m l z] === 4 m l z],
  "epsilonZ_zero_boundary" -> TrueQ[Expand[(1 + 2 m^2) e + 4 m l 0 - (1 + 2 m^2) e] === 0]
|>;

result = <|
  "checks" -> <|"CAS-02-C04" -> AllTrue[Values[checks], TrueQ]|>,
  "details" -> checks,
  "domain_assumption_diff" -> {},
  "counterexample" -> Null,
  "wolfram_version" -> System`$Version,
  "xtensor_version" -> ToString[InputForm[xAct`xTensor`$Version]]
|>;
Print["CAS_RESULT_JSON:", ExportString[result, "RawJSON"]];
If[! TrueQ[result["checks"]["CAS-02-C04"]], Exit[1]];
Exit[0];
