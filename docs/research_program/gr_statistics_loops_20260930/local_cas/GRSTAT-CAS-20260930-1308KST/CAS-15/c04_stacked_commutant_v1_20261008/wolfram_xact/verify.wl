Needs["xAct`xTensor`"];
Print["WOLFRAM_VERSION=", System`$Version];
Print["XTENSOR_VERSION=", ToString[xAct`xTensor`$Version, InputForm]];

(* The three matrices are an orthonormal Frobenius basis of Skew(3). *)
e = {
  {{0, 0, 0}, {0, 0, -1/Sqrt[2]}, {0, 1/Sqrt[2], 0}},
  {{0, 0, 1/Sqrt[2]}, {0, 0, 0}, {-1/Sqrt[2], 0, 0}},
  {{0, -1/Sqrt[2], 0}, {1/Sqrt[2], 0, 0}, {0, 0, 0}}
};
frob[a_, b_] := Tr[Transpose[a].b];
comm[a_, b_] := a.b - b.a;
gram[a_] := Table[Expand[frob[comm[a, e[[i]]], comm[a, e[[j]]]]], {i, 3}, {j, 3}];
w = {w1, w2, w3};
ww = Sum[w[[i]] e[[i]], {i, 3}];
sym[a_, b_, c_, d_, ee_, f_] := {{a, b, c}, {b, d, ee}, {c, ee, f}};
m1 = sym[a1, b1, c1, d1, ee1, f1];
m2 = sym[a2, b2, c2, d2, ee2, f2];
gStack = gram[m1] + gram[m2];
qStack = Expand[w.gStack.w];
sumSquares = Expand[frob[comm[m1, ww], comm[m1, ww]] + frob[comm[m2, ww], comm[m2, ww]]];
genericCheck = (Expand[qStack - sumSquares] === 0) &&
  (Transpose[gStack] === gStack) &&
  (Table[frob[e[[i]], e[[j]]], {i, 3}, {j, 3}] === IdentityMatrix[3]);

n = {n1, n2, n3};
n2norm = n.n;
axmat[nn_, alpha_, beta_] := alpha IdentityMatrix[3] + beta Outer[Times, nn, nn];
gAxis = gram[axmat[n, alpha, beta]];
axisPolynomial = Expand[gAxis - beta^2 n2norm (n2norm IdentityMatrix[3] - Outer[Times, n, n])];
vn = ww.n;
axisComm = comm[axmat[n, alpha, beta], ww];
axisCommPolynomial = Expand[axisComm + beta (Outer[Times, n, vn] + Outer[Times, vn, n])];
axisConversePolynomial = Expand[(axisComm.n + beta n2norm vn)];
axisGaugeGram = gram[axmat[{0, 0, 1}, alpha, beta]];
axisCheck = (axisPolynomial === ConstantArray[0, {3, 3}]) &&
  (axisCommPolynomial === ConstantArray[0, {3, 3}]) &&
  (axisConversePolynomial === ConstantArray[0, 3]) &&
  (axisGaugeGram === beta^2 DiagonalMatrix[{1, 1, 0}]) &&
  (Length[NullSpace[axisGaugeGram]] === 1) &&
  (Cross[First[NullSpace[axisGaugeGram]], {0, 0, 1}] === {0, 0, 0});
Print["AXIS_DIAGNOSTICS=", ToString[{
  axisPolynomial === ConstantArray[0, {3, 3}],
  axisCommPolynomial === ConstantArray[0, {3, 3}],
  axisConversePolynomial === ConstantArray[0, 3],
  axisGaugeGram === beta^2 DiagonalMatrix[{1, 1, 0}],
  Length[NullSpace[axisGaugeGram]] === 1,
  Cross[First[NullSpace[axisGaugeGram]], {0, 0, 1}] === {0, 0, 0}
}, InputForm]];

(* Rotate the first unit axis to e3 and the second into the e1-e3 plane.
   s != 0 is precisely nonparallel.  The polynomial relation s^2+c^2=1
   is imposed only after deriving the unconstrained matrix identities. *)
na = {0, 0, 1};
nb = {s, 0, cc};
gTwoRaw = gram[axmat[na, alpha1, beta1]] + gram[axmat[nb, alpha2, beta2]];
gTwoUnit = beta1^2 (IdentityMatrix[3] - Outer[Times, na, na]) +
  beta2^2 (IdentityMatrix[3] - Outer[Times, nb, nb]);
reduceUnit[pol_] := Last[PolynomialReduce[Expand[pol], {s^2 + cc^2 - 1}, {s, cc}]];
twoGramIdentity = Map[reduceUnit, gTwoRaw - gTwoUnit, {2}];
detUnit = reduceUnit[Det[gTwoUnit] - beta1^2 beta2^2 (beta1^2 + beta2^2) s^2];
qUnit = Expand[w.gTwoUnit.w];
qSquares = beta1^2 (w1^2 + w2^2) + beta2^2 ((cc w1 - s w3)^2 + w2^2);
qUnitIdentity = reduceUnit[qUnit - qSquares];
(* These exact certificates imply q>0 for real nonzero w, beta1,beta2,s.
   The first two squares force w1=w2=0; the last then forces w3=0. *)
stackCheck = (twoGramIdentity === ConstantArray[0, {3, 3}]) &&
  (detUnit === 0) && (qUnitIdentity === 0);

isotropicCheck = (gram[axmat[na, alpha, 0]] === ConstantArray[0, {3, 3}]);
parallelGram = gram[axmat[na, alpha1, beta1]] + gram[axmat[na, alpha2, beta2]];
parallelCheck = (parallelGram === (beta1^2 + beta2^2) DiagonalMatrix[{1, 1, 0}]) &&
  (Length[NullSpace[parallelGram]] === 1) &&
  (Cross[First[NullSpace[parallelGram]], {0, 0, 1}] === {0, 0, 0});
controlsCheck = isotropicCheck && parallelCheck && axisCheck;

checks = <|"generic_gram_kernel" -> genericCheck,
  "axisymmetric_one_axis" -> axisCheck,
  "two_nonparallel_pd_rank3" -> stackCheck,
  "isotropic_parallel_one_axis_controls" -> controlsCheck|>;
Print["CHECKS=", ToString[checks, InputForm]];
cert = <|
  "checks" -> checks,
  "generic_gram_sum_of_squares_zero" -> ToString[Expand[qStack - sumSquares], InputForm],
  "axis_gram_polynomial_zero" -> ToString[axisPolynomial, InputForm],
  "axis_commutator_polynomial_zero" -> ToString[axisCommPolynomial, InputForm],
  "axis_converse_polynomial_zero" -> ToString[axisConversePolynomial, InputForm],
  "axis_gauge_gram" -> ToString[axisGaugeGram, InputForm],
  "two_gram_mod_unit_zero" -> ToString[twoGramIdentity, InputForm],
  "two_determinant_mod_unit_zero" -> ToString[detUnit, InputForm],
  "two_positive_squares_mod_unit_zero" -> ToString[qUnitIdentity, InputForm],
  "isotropic_gram_zero" -> isotropicCheck,
  "parallel_kernel" -> ToString[NullSpace[parallelGram], InputForm],
  "wolfram_version" -> System`$Version,
  "xtensor_version" -> ToString[xAct`xTensor`$Version, InputForm]
|>;
Export[Last[$ScriptCommandLine], cert, "RawJSON"];
If[And @@ Values[checks], Exit[0], Exit[2]];
