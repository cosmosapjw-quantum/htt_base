(* CAS-16-C03: finite scalar product quadrature. Independent Wolfram/xAct axis. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
DefManifold[CAS16Sphere, 2, {cas16i, cas16j}];
Print["WOLFRAM_VERSION=", System`$Version];
Print["XACT_XTENSOR_VERSION=", xAct`xTensor`$Version];
Print["XACT_VERSION_SYMBOLS=", ToString[InputForm[Names["xAct`xTensor`*Version*"]]]];
Print["XACT_MANIFOLD_DEFINED=", TrueQ[ManifoldQ[CAS16Sphere]]];

failures = {};
record[id_, actual_, expected_] := Module[{difference},
  difference = FullSimplify[RootReduce[actual - expected]];
  If[! TrueQ[difference == 0], AppendTo[failures, {id, ToString[InputForm[difference]]}]];
];

(* The constant Fourier coefficient of cos(phi)^a sin(phi)^b, derived by
   expanding ((z+z^-1)/2)^a ((z-z^-1)/(2 I))^b. *)
angularConstant[a_Integer, b_Integer] := If[OddQ[a + b], 0,
  FullSimplify[I^(-b) 2^(-a-b) Sum[
    If[p + q == (a + b)/2, Binomial[a, p] Binomial[b, q] (-1)^q, 0],
    {p, 0, a}, {q, 0, b}]]];
monomialPower[value_, exponent_Integer] := If[exponent == 0, 1, value^exponent];
angularGrid[a_Integer, b_Integer] := RootReduce[
  Sum[monomialPower[Cos[2 Pi j/9], a] monomialPower[Sin[2 Pi j/9], b],
    {j, 0, 8}]/9];

(* With a+b even, the radial factor is a polynomial of degree a+b+c <= 8.
   With a+b odd the angular coefficient vanishes on both sides, so the
   nonnegative sqrt branch never needs algebraic cancellation. *)
muNodes = {0,
  Sqrt[5 - 2 Sqrt[10/7]]/3, -Sqrt[5 - 2 Sqrt[10/7]]/3,
  Sqrt[5 + 2 Sqrt[10/7]]/3, -Sqrt[5 + 2 Sqrt[10/7]]/3};
muWeights = {128/225,
  (322 + 13 Sqrt[70])/900, (322 + 13 Sqrt[70])/900,
  (322 - 13 Sqrt[70])/900, (322 - 13 Sqrt[70])/900};
record["GL5_weight_normalization", Total[muWeights], 2];
record["GL5_node_domain", Boole[And @@ (TrueQ[FullSimplify[-1 <= # <= 1]] & /@ muNodes)], 1];
record["GL5_positive_weights", Boole[And @@ (TrueQ[FullSimplify[# > 0]] & /@ muWeights)], 1];
record["xAct_load", Boole[TrueQ[ManifoldQ[CAS16Sphere]]], 1];

radialGrid[n_Integer, c_Integer] := FullSimplify[
  Sum[muWeights[[r]] monomialPower[muNodes[[r]], c]
    (1 - muNodes[[r]]^2)^(n/2), {r, 1, 5}]/2];
radialIntegral[n_Integer, c_Integer] := Integrate[
  mu^c (1 - mu^2)^(n/2), {mu, -1, 1}]/2;

triples = Flatten[Table[{a, b, c}, {a, 0, 8}, {b, 0, 8-a}, {c, 0, 8-a-b}], 2];
anglePairs = DeleteDuplicates[triples[[All, {1, 2}]]];
angles = Association[Table[
  With[{a = pair[[1]], b = pair[[2]]},
    pair -> angularGrid[a, b]], {pair, anglePairs}]];
Do[record["azimuth_" <> ToString[pair], angles[pair], angularConstant @@ pair], {pair, anglePairs}];
Do[
  a = triple[[1]]; b = triple[[2]]; c = triple[[3]]; n = a + b;
  angle = angles[{a, b}]; targetAngle = angularConstant[a, b];
  If[OddQ[n],
    (* Exact zero from the already computed nine-node sum. *)
    record["monomial_" <> ToString[triple], angle, 0],
    record["monomial_" <> ToString[triple],
      angle radialGrid[n, c], targetAngle radialIntegral[n, c]]],
  {triple, triples}];

gl4t1 = Sqrt[(3 - 2 Sqrt[6/5])/7];
gl4t2 = Sqrt[(3 + 2 Sqrt[6/5])/7];
gl4w1 = (18 + Sqrt[30])/36;
gl4w2 = (18 - Sqrt[30])/36;
gl4e = 2 gl4w1 gl4t1^8 + 2 gl4w2 gl4t2^8 - Integrate[mu^8, {mu, -1, 1}];
record["GL4_mu8_witness", gl4e, -128/11025];
record["GL4_mu8_nonzero", Boole[TrueQ[FullSimplify[gl4e != 0]]], 1];

n8e = Sum[Cos[2 Pi j/8]^8, {j, 0, 7}]/8 -
  Integrate[Cos[phi]^8, {phi, 0, 2 Pi}]/(2 Pi);
record["Nphi8_cos8_witness", n8e, 1/128];
record["Nphi8_cos8_nonzero", Boole[TrueQ[FullSimplify[n8e != 0]]], 1];

Print["MONOMIAL_COUNT=", Length[triples]];
Print["ANGLE_PAIR_COUNT=", Length[anglePairs]];
Print["GL4_MU8_DIFFERENCE=", ToString[InputForm[FullSimplify[gl4e]]]];
Print["NPHI8_COS8_DIFFERENCE=", ToString[InputForm[FullSimplify[n8e]]]];
Print["FAILURE_COUNT=", Length[failures]];
Scan[Print["FAILURE=", ToString[InputForm[#]]] &, failures];
If[Length[triples] != 165 || Length[failures] > 0, Exit[2], Exit[0]];
