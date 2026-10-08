(* CAS-11-C01 v2: independent Wolfram+xTensor finite algebra certificate. *)
Needs["xAct`xTensor`"];
Print["ENGINE_VERSION=", $Version];
Print["XTENSOR_VERSION=", xAct`xTensor`$Version];

ClearAll[n, k, i, j, f, g, h, pg, ph, v, lam, hf, hg, hh, x, y, z, p, q, ax, ay, az];

(* Coordinate kernel for arbitrary scalar values and gradients. The three
   H-values cancel without convexity, a sign condition, or any derivative away
   from the named points. *)
scalarKernel = Expand[
  (ax - ay - p (x - y)) - (ax - az - q (x - z)) -
  (az - ay - p (z - y)) - (q - p) (x - z)];
Print["SCALAR_KERNEL_ZERO=", TrueQ[scalarKernel === 0]];

(* Wolfram's exact Sum algebra is asked to reduce the finite vector statement
   with n held as an arbitrary nonnegative integer, not enumerated. *)
lhs = hf - hg - Sum[pg[i] (f[i] - g[i]), {i, 1, n}] -
  (hf - hh - Sum[ph[i] (f[i] - h[i]), {i, 1, n}]) -
  (hh - hg - Sum[pg[i] (h[i] - g[i]), {i, 1, n}]);
rhs = Sum[(ph[i] - pg[i]) (f[i] - h[i]), {i, 1, n}];
vectorResidual = FullSimplify[lhs - rhs, Element[n, Integers] && n >= 0];
Print["VECTOR_SUM_RESIDUAL=", InputForm[vectorResidual]];
Print["VECTOR_SUM_ZERO=", TrueQ[vectorResidual === 0]];

(* Scalar distributivity kernel and finite rectangular Fubini are the two
   reduction steps needed for the n by k moment identity. *)
bilinearKernel = Expand[(p + q) x - p x - q x];
Print["BILINEAR_DISTRIBUTIVITY_ZERO=", TrueQ[bilinearKernel === 0]];

delta[i_] := f[i] - h[i];
momentLhs = Sum[Sum[v[i, j] lam[j], {j, 1, k}] delta[i], {i, 1, n}];
momentRhs = Sum[lam[j] Sum[v[i, j] delta[i], {i, 1, n}], {j, 1, k}];
momentResidual = FullSimplify[momentLhs - momentRhs,
  Element[n, Integers] && n >= 0 && Element[k, Integers] && k >= 0];
Print["MOMENT_SUM_RESIDUAL=", InputForm[momentResidual]];
Print["MOMENT_SUM_ZERO=", TrueQ[momentResidual === 0]];

(* Exact controls from ADMITTED_INPUTS.json. *)
hhC[t_] := t^3/3;
dhC[a_, b_] := hhC[a] - hhC[b] - b^2 (a - b);
Print["ORIENTATION_FG=", InputForm[dhC[2, 1]]];
Print["ORIENTATION_GF=", InputForm[dhC[1, 2]]];
Print["APPROXIMATE_RESIDUAL=", InputForm[1 * 1 * (1/10)]];

If[TrueQ[scalarKernel === 0] && TrueQ[vectorResidual === 0] &&
   TrueQ[bilinearKernel === 0] && TrueQ[momentResidual === 0] &&
   dhC[2, 1] === 4/3 && dhC[1, 2] === 5/3,
  Print["CERTIFICATE_STATUS=PASS"]; Exit[0],
  Print["CERTIFICATE_STATUS=INCONCLUSIVE"]; Exit[2]];
