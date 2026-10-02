(* CAS-01: independent exact finite algebra, null-cone kernel, and vertex jet. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
DefManifold[GrstatM, 4, {a, b, d, e}];
DefMetric[-1, eta[-a, -b], CD];
DefTensor[ss[-a, -b], GrstatM, Symmetric[{-a, -b}]];
DefTensor[bb[-a, -b], GrstatM, Symmetric[{-a, -b}]];
DefTensor[ww[-a, -b], GrstatM, Antisymmetric[{-a, -b}]];
DefTensor[qq[-a, -b], GrstatM];
xact = <|
 "symS" -> TrueQ[ToCanonical[ss[-a, -b] - ss[-b, -a]] === 0],
 "symB" -> TrueQ[ToCanonical[bb[-a, -b] - bb[-b, -a]] === 0],
 "skewW" -> TrueQ[ToCanonical[ww[-a, -b] + ww[-b, -a]] === 0],
 "metricRaiseLower" -> TrueQ[ToCanonical[ContractMetric[eta[b, d] qq[-a, -d] eta[-b, -e] - qq[-a, -e]]] === 0]
|>;
Clear[c, al, h0, h1, h2, n, t, z, sx, xx];
g = DiagonalMatrix[{-1, 1, 1, 1}];
u = {1, 0, 0, 0}; uf = g.u;
zero[v_] := And @@ (TrueQ[FullSimplify[# == 0]] & /@ Flatten[{v}]);
S = Table[If[i <= j, sx[i, j], sx[j, i]], {i, 1, 4}, {j, 1, 4}];
B = S + (u.S.u) g;
bv = B.u;
W = {{0, 0, 0, 0}, {0, 0, t[1, 2], t[1, 3]},
     {0, -t[1, 2], 0, t[2, 3]}, {0, -t[1, 3], -t[2, 3], 0}};
Q = B + Outer[Times, bv, uf] - Outer[Times, uf, bv] + W;
(* The exact null-cone polynomial is evaluated at a determining set of unit
   directions: +/- coordinate axes and positive coordinate bisectors. *)
T = Table[If[i <= j, z[i, j], z[j, i]], {i, 0, 3}, {j, 0, 3}];
axes = Flatten[Table[{UnitVector[3, i], -UnitVector[3, i]}, {i, 1, 3}], 1];
bisectors = {(UnitVector[3, 1] + UnitVector[3, 2])/Sqrt[2],
             (UnitVector[3, 1] + UnitVector[3, 3])/Sqrt[2],
             (UnitVector[3, 2] + UnitVector[3, 3])/Sqrt[2]};
equations = Table[With[{k = Prepend[dir, -1]}, k.T.k == 0], {dir, Join[axes, bisectors]}];
unknowns = Flatten[Table[z[i, j], {i, 0, 3}, {j, i, 3}], 1];
sol = Solve[equations, unknowns];
cone = Length[sol] == 1 && zero[(T /. First[sol]) + z[0, 0] g];
shift = S + al g;
Bshift = shift + (u.shift.u) g;
c01 = zero[u.B.u] && zero[Bshift - B] && cone;
P = IdentityMatrix[4] + Outer[Times, u, uf];
Dsp = Transpose[P].B.P;
theta = Tr[g.B];
sigma = Dsp - theta/3 (g + Outer[Times, uf, uf]);
acc = 2 c bv;
c02 = zero[Q.u] && zero[(Q + Transpose[Q])/2 - B] &&
      zero[c Transpose[Q].u - acc] && zero[theta - Tr[g.Dsp]] &&
      zero[sigma.u] && zero[Tr[g.sigma]] &&
      zero[acc[[2 ;; 4]] - 2 c B[[2 ;; 4, 1]]];
ns = Array[n, 3]; K = Prepend[ns, -1];
rest = Expand[K.B.K - (theta/3 + ns.sigma[[2 ;; 4, 2 ;; 4]].ns - acc[[2 ;; 4]].ns/c)];
restRemainder = Last[PolynomialReduce[rest, {ns.ns - 1}, ns]];
h1s = Array[h1, 3];
h2m = Table[If[i <= j, h2[i, j], h2[j, i]], {i, 1, 3}, {j, 1, 3}];
Sgeneral = Join[{Prepend[-h1s/2, h0]}, MapThread[Prepend, {h2m, -h1s/2}]];
general = zero[Expand[K.Sgeneral.K - (h0 + h1s.ns + ns.h2m.ns)]] &&
          zero[Tr[h2m] /. h2[3, 3] -> -h2[1, 1] - h2[2, 2]];
c03 = zero[restRemainder] && general;
vars = Array[xx, 4];
seed = u + vars.Q.g/c;
norm2 = -seed.g.seed;
normalized = seed/Sqrt[norm2];
at0 = Thread[vars -> ConstantArray[0, 4]];
deriv = Table[D[normalized[[j]], vars[[i]]] /. at0, {i, 1, 4}, {j, 1, 4}];
expected = Q.g/c;
c04parts = {zero[(normalized /. at0) - u], zero[deriv - expected],
  zero[(norm2 /. at0) - 1]};
c04 = And @@ c04parts;
checks = <|"CAS-01-C01" -> c01, "CAS-01-C02" -> c02,
           "CAS-01-C03" -> c03, "CAS-01-C04" -> c04|>;
result = <|"checks" -> checks, "domain_assumption_diff" -> {},
 "counterexample" -> Null, "xact_actions" -> xact,
 "intermediate" -> <|"null_cone_solution" -> ToString[InputForm[sol]],
   "rest_remainder" -> ToString[InputForm[restRemainder]],
   "jet_derivative_residual" -> ToString[InputForm[FullSimplify[deriv - expected]]],
   "c04parts" -> c04parts, "norm_at_zero" -> ToString[InputForm[norm2 /. at0]]|>,
 "wolfram_version" -> System`$Version,
 "xtensor_version" -> ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];
Print[ExportString[result, "RawJSON"]];
Print["CAS_JSON_END"];
Exit[If[And @@ Values[checks] && And @@ Values[xact], 0, 2]];
