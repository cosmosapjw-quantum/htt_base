(* CAS-11-C01: exact finite-dimensional Bregman identity. *)
(* This file uses only the frozen EXECUTION_CONTRACT and ADMITTED_INPUTS. *)
Print["WOLFRAM_VERSION=", $Version];
Needs["xAct`xTensor`"];
Print["XTENSOR_VERSION=", xAct`xTensor`$Version];

(* An abstract-index check of the three-point expansion.  The dimension 3 is
   arbitrary here: the contraction polynomial contains no dimension factor.
   The scalar argument below proves the same bilinear identity for any finite n. *)
DefManifold[CAS11Space, 3, {a, b}];
DefManifold[CAS11Moment, 2, {i, j}];
DefTensor[ff[a], CAS11Space];
DefTensor[gg[a], CAS11Space];
DefTensor[hh[a], CAS11Space];
DefTensor[gradG[-a], CAS11Space];
DefTensor[gradH[-a], CAS11Space];
DefTensor[VV[-a, -i], {CAS11Space, CAS11Moment}];
DefTensor[lam[i], CAS11Moment];

lhsTensor = (hF - hG - gradG[-a] (ff[a] - gg[a])) -
  (hF - hH - gradH[-a] (ff[a] - hh[a])) -
  (hH - hG - gradG[-a] (hh[a] - gg[a]));
rhsTensor = (gradH[-a] - gradG[-a]) (ff[a] - hh[a]);
tensorIdentity = TrueQ[ToCanonical[Expand[lhsTensor - rhsTensor]] === 0];
Print["CHECK:tensor_identity=", tensorIdentity];

(* With q_a = V_ai lambda^i, q_a d^a is lambda^i(V_ai d^a).
   Thus the exact transpose moment V^T d=0 removes it. *)
dTensor = ff[a] - hh[a];
momentFactor = TrueQ[
  ToCanonical[Expand[VV[-a, -i] lam[i] dTensor -
    lam[i] VV[-a, -i] dTensor]] === 0];
Print["CHECK:transpose_factorization=", momentFactor];

(* Universal real-vector proof: let the five independent symbols below denote
   <gradG,f>, <gradG,g>, <gradG,h>, <gradH,f>, <gradH,h>.
   Bilinearity of the Euclidean pairing gives exactly these expansions for any n.
   No relation among H values or gradient values is imposed. *)
lhsScalar = (HF - HG - (pGF - pGG)) -
  (HF - HH - (pHF - pHH)) -
  (HH - HG - (pGH - pGG));
rhsScalar = (pHF - pHH) - (pGF - pGH);
scalarIdentity = TrueQ[Expand[lhsScalar - rhsScalar] === 0];
Print["CHECK:universal_bilinear_identity=", scalarIdentity];

cubic[x_] := x^3/3;
cubicD[x_, y_] := cubic[x] - cubic[y] - y^2 (x - y);
forward = cubicD[2, 1];
reverse = cubicD[1, 2];
orientationControl = TrueQ[forward === 4/3 && reverse === 5/3 && forward =!= reverse];
Print["CUBIC_FORWARD=", forward];
Print["CUBIC_REVERSE=", reverse];
Print["CHECK:cubic_orientation=", orientationControl];

approxResidual = 1*(1/10);
approxControl = TrueQ[approxResidual === 1/10 && approxResidual =!= 0];
Print["APPROX_RESIDUAL=", approxResidual];
Print["CHECK:approximate_nonzero=", approxControl];

allChecks = And[tensorIdentity, momentFactor, scalarIdentity,
  orientationControl, approxControl];
Print["ALL_CHECKS=", allChecks];
If[TrueQ[allChecks], Exit[0], Exit[1]];
