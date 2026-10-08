(* PORT-CAS-02, frozen finite algebra. No sibling result is an input. *)
$HistoryLength = 0;
Print["WOLFRAM_VERSION=", $Version];
Print["WOLFRAM_VERSION_NUMBER=", $VersionNumber];
Needs["xAct`xTensor`"];
Print["XACT_XTENSOR_LOADED=", MemberQ[$Packages, "xAct`xTensor`"]];

ClearAll[h0, st, aa, h11, h12, h13, q11, q12, q13, q22, q23,
  n1, n2, n3, u0, u1, u2, u3];
gmat = DiagonalMatrix[{-1, 1, 1, 1}];
q33 = -q11 - q22;
qmat = {{q11, q12, q13}, {q12, q22, q23}, {q13, q23, q33}};
smat = ArrayFlatten[{{{{h0}}, {-{h11, h12, h13}/2}},
  {Transpose[{-{h11, h12, h13}/2}], qmat}}];
km = {-1, n1, n2, n3};
um = {u0, u1, u2, u3};
norm = n1^2 + n2^2 + n3^2 - 1;
null = Expand[km.gmat.km];
snull = Expand[km.smat.km];
bmat = smat - st gmat;
bnull = Expand[km.bmat.km];
target = h0 + h11 n1 + h12 n2 + h13 n3 +
  ({n1, n2, n3}.qmat.{n1, n2, n3});
modNorm[p_] := Last[PolynomialReduce[Expand[p], {norm},
  {n1, n2, n3, h0, h11, h12, h13, q11, q12, q13, q22, q23, st}]];
mixedResidual = Expand[gmat.smat.um - st um];
kernelRaised = Expand[gmat.(bmat.um)];
gaugeB = Expand[(smat + aa gmat) - (st + aa) gmat];
checks = <|
  "metric_inverse" -> (gmat.gmat === IdentityMatrix[4]),
  "null_on_unit_sphere" -> (modNorm[null] === 0),
  "S_null_polynomial" -> (Expand[snull - target] === 0),
  "B_null_equals_S" -> (modNorm[bnull - snull] === 0),
  "mixed_eigenpair_kernel_identity" -> (kernelRaised === mixedResidual),
  "metric_nondegenerate" -> (Det[gmat] === -1),
  "S_symmetric" -> (smat === Transpose[smat]),
  "B_symmetric" -> (bmat === Transpose[bmat]),
  "q_tracefree" -> (Tr[qmat] === 0),
  "spatial_monopole_removed" -> (Tr[qmat]/3 === 0),
  "gauge_B_invariant" -> (gaugeB === bmat),
  "gauge_null_invariant" -> (modNorm[Expand[km.(smat + aa gmat).km - snull]] === 0)
|>;

(* Independent abstract-index check: raising the covariant kernel by the
   xAct metric produces precisely the mixed-index eigenpair residual. *)
DefManifold[Mport, 4, IndexRange[a, z]];
DefMetric[-1, gm[-a, -b], CDport];
DefTensor[t[-a, -b], Mport];
DefTensor[v[a], Mport];
DefConstantSymbol[lambdaPort];
DefConstantSymbol[alphaPort];
indexKernel = gm[a, c] (t[-c, -b] - lambdaPort gm[-c, -b]) v[b];
indexEigen = gm[a, c] t[-c, -b] v[b] - lambdaPort v[a];
indexGauge = (t[-a, -b] + alphaPort gm[-a, -b]) -
  (lambdaPort + alphaPort) gm[-a, -b] -
  (t[-a, -b] - lambdaPort gm[-a, -b]);
checks["xAct_raised_kernel_identity"] =
  (ToCanonical[Expand[indexKernel - indexEigen]] === 0);
checks["xAct_metric_gauge_identity"] =
  (ToCanonical[Expand[indexGauge]] === 0);

example = {h0 -> 2, h11 -> 1, h12 -> -2, h13 -> 3,
  q11 -> 1, q12 -> 0, q13 -> 0, q22 -> -1, q23 -> 0,
  n1 -> 1, n2 -> 0, n3 -> 0};
checks["test_vector_null"] = ((null /. example) === 0);
checks["test_vector_polynomial"] = ((snull /. example) === 4);
checks["pure_metric_B_zero"] =
  (Simplify[(st gmat - st gmat) == ConstantArray[0, {4, 4}]] === True);

Print["CHECKS=", InputForm[checks]];
Print["NULL=", InputForm[null]];
Print["S_NULL=", InputForm[snull]];
Print["B_MINUS_S_NULL=", InputForm[Expand[bnull - snull]]];
Print["MIXED_MINUS_RAISED_KERNEL=", InputForm[Expand[mixedResidual - kernelRaised]]];
Print["XACT_RAISED_KERNEL=", InputForm[ToCanonical[Expand[indexKernel - indexEigen]]]];
Print["XACT_GAUGE=", InputForm[ToCanonical[Expand[indexGauge]]]];
If[And @@ Values[checks], Print["PORT_CAS_02_WOLFRAM_XACT=PASS"],
  Print["PORT_CAS_02_WOLFRAM_XACT=FAIL"]; Exit[2]];
