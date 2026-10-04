(* Independent finite C01 certificate. All coordinate variables are real. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
Print["WOLFRAM_VERSION=", $Version];
Print["XTENSOR_VERSION=", xAct`xTensor`$Version];

DefManifold[C01M, 4, {a, b, c, d}];
DefMetric[-1, c01g[-a, -b], c01CD];
DefTensor[c01S[-a, -b], C01M, Symmetric[{-a, -b}]];
DefTensor[c01u[a], C01M];
DefTensor[c01st[], C01M];

(* These are genuinely indexed, nonzero expressions before reduction. The
   first raises the covector equation and contracts the inverse metric;
   the second uses the declared covariant symmetry of S. *)
indexInput = c01g[a, c] (c01S[-c, -b] - c01st[] c01g[-c, -b]) c01u[b]
  - c01g[a, c] c01S[-c, -b] c01u[b] + c01st[] c01u[a];
symmetryInput = c01S[-a, -b] c01u[a] c01u[b]
  - c01S[-b, -a] c01u[a] c01u[b];
indexReduced = ToCanonical[ContractMetric[indexInput]];
symmetryReduced = ToCanonical[symmetryInput];
xTensorCheck = (indexReduced === 0 && symmetryReduced === 0 && indexInput =!= 0);

Clear[c01s];
c01s[i_, j_] := Symbol["Global`q" <> ToString[Min[i, j]] <> ToString[Max[i, j]]];
covS = Table[c01s[i, j], {i, 1, 4}, {j, 1, 4}];
g = DiagonalMatrix[{-1, 1, 1, 1}];
u = Array[Symbol["Global`u" <> ToString[#]] &, 4];
st = Symbol["Global`st"];
st2 = Symbol["Global`st2"];
shell = u.g.u + 1;
bmat[t_] := covS - t g;

(* Exact polynomial certificates valid for arbitrary symmetric S and u.
   On shell=0, B(t)u=0 iff g^-1 S u=t u. Since g^-1=g, raising
   and lowering are inverse operations. Contracting B(t)u=0 with u
   gives 0=u.S.u+t, hence the unique t=-u.S.u. *)
raisedIdentity = Expand[g.(bmat[st].u) - (g.covS.u - st u)] === ConstantArray[0, 4];
loweredIdentity = Expand[g.(g.covS.u - st u) - bmat[st].u] === ConstantArray[0, 4];
coefficientIdentity = Expand[u.bmat[st].u - (u.covS.u + st) + st shell] === 0;
uniquenessIdentity = Expand[u.(bmat[st].u - bmat[st2].u)
  - (st - st2) + (st - st2) shell] === 0;
normalizedCoefficient = Expand[(u.covS.u + st) /. st -> -u.covS.u] === 0;

Clear[c01b];
c01b[i_, j_] := Symbol["Global`b" <> ToString[Min[i, j]] <> ToString[Max[i, j]]];
genericB = Table[c01b[i, j], {i, 0, 3}, {j, 0, 3}];
e0 = {1, 0, 0, 0};
timeColumn = genericB.e0;
timeRow = e0.genericB;
restRules = Thread[timeColumn -> ConstantArray[0, 4]];
restB0 = genericB /. restRules;
(* tr D=0 is the named zero-expansion condition; no eigenvalue is divided. *)
restB = restB0 /. c01b[3, 3] -> -c01b[1, 1] - c01b[2, 2];
Dsp = restB[[2 ;; 4, 2 ;; 4]];
w = Array[Symbol["Global`w" <> ToString[#]] &, 3];
v0 = Symbol["Global`v0"];
v = Join[{v0}, w];
phi = Join[{Sqrt[1 + w.w]}, w];
realW = And @@ (Element[#, Reals] & /@ w);

restDerivation = (timeColumn === timeRow && restB0[[1]] === ConstantArray[0, 4]
  && restB0[[All, 1]] === ConstantArray[0, 4]
  && Tr[Dsp] === 0 && restB === ArrayFlatten[{{{{0}}, ConstantArray[0, {1, 3}]},
    {ConstantArray[0, {3, 1}], Dsp}}]);
kernelEquation = Expand[restB.v - Join[{0}, Dsp.w]] === ConstantArray[0, 4];
chartEquation = Simplify[restB.phi - Join[{0}, Dsp.w]] === ConstantArray[0, 4];
chartNorm = FullSimplify[phi.g.phi == -1, realW] === True;
chartFuture = FullSimplify[phi[[1]] > 0, realW] === True;
chartInverse = FullSimplify[v0 == Sqrt[1 + w.w],
  realW && Element[v0, Reals] && v0 > 0 && v.g.v == -1] === True;
chartInjective = Rest[phi] === w;

(* The general equations Bv=(0,Dw), g(v,v)=-v0^2+w.w and v0>0
   establish both inclusions, independently of rank or repeated roots.
   These rank controls also exercise the full and singleton endpoints. *)
dFull = ConstantArray[0, {3, 3}];
dOne = DiagonalMatrix[{0, 1, -1}];
dZero = DiagonalMatrix[{1, 1, -2}];
rankControls = (And @@ (Tr[#] == 0 & /@ {dFull, dOne, dZero})
  && (3 - MatrixRank[dFull] == 3)
  && (3 - MatrixRank[dOne] == 1)
  && (3 - MatrixRank[dZero] == 0)
  && (dFull.w === ConstantArray[0, 3])
  && (dOne.w === {0, w[[2]], -w[[3]]})
  && (dZero.w === {w[[1]], w[[2]], -2 w[[3]]}));

subchecks = <|
  "xTensor_index_and_symmetry" -> xTensorCheck,
  "raised_and_lowered_eigen_equivalence" -> (raisedIdentity && loweredIdentity),
  "mass_shell_coefficient_and_uniqueness" ->
    (coefficientIdentity && uniquenessIdentity && normalizedCoefficient),
  "rest_block_derived" -> restDerivation,
  "kernel_membership_equation" -> (kernelEquation && chartEquation),
  "future_unit_chart" -> (chartNorm && chartFuture && chartInverse && chartInjective),
  "all_rank_controls" -> rankControls
|>;
checks = <|"CAS-03-C01" -> And @@ Values[subchecks]|>;
Print["C01_RESULT_JSON=", ExportString[<|
  "checks" -> checks,
  "subchecks" -> subchecks,
  "domain_assumption_diff" -> {},
  "counterexample" -> Null,
  "limitations" -> {"Finite real linear algebra only; existence of a timelike eigenvector is conditional.",
    "No smooth, global, physical-realization, C02, or C03 claim."}
|>, "RawJSON"]];
If[TrueQ[checks["CAS-03-C01"]], Exit[0], Exit[2]];
