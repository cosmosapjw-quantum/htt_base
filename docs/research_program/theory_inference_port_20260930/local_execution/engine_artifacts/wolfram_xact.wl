(* CAS_CONTRACT.json bc45fb9: -+++ and finite supplied law only. *)
Needs["xAct`xTensor`"];
DefManifold[CASM, 4, {ca, cb}];
DefMetric[-1, gCAS[-ca, -cb], CDCAS];
xactCheck = ToCanonical[gCAS[ca, -ca]] === 4;
cas07 = Resolve[ForAll[{km, um, em},
  Implies[um >= 0 && em >= 0 && em <= um,
    km <= km + em && km + em <= km + um]], Reals];
h = {{1, 0, 0}, {-1, 1, 0}, {0, -1, 1}};
c = {{c11, c12, c13}, {c12, c22, c23}, {c13, c23, c33}};
cas09 = Simplify[Det[h] == 1 && Inverse[h].h == IdentityMatrix[3] &&
  Transpose[h.c.Transpose[h]] == h.c.Transpose[h]];
Print["XACT_TENSOR_EVALUATED=", xactCheck];
Print["CAS07_FINITE_UNDEFINED_INTERVAL=", cas07];
Print["CAS09_DEPTH_LINEAR_COVARIANCE=", cas09];
If[!TrueQ[xactCheck && cas07 && cas09], Exit[1]];
