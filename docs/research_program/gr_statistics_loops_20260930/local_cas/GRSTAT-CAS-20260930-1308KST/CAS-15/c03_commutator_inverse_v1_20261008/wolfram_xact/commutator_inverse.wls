(* Independent CAS-15-C03 Wolfram/xTensor finite algebra certificate.
   This source uses only EXECUTION_CONTRACT.json, ADMITTED_INPUTS.json and
   COMMON_SPEC.md. All variables below are real. The derivation is recorded
   in PROOF.md; no sibling result is an input. *)
Needs["xAct`xTensor`"];

ClearAll[m1, m2, m3, h1, h2, h3, x12, x13, x23, r12, r13, r23,
  q11, q12, q13, q21, q22, q23, q31, q32, q33, z12, z13, z23,
  epsR, epsM, ws, dh, u, v, d1, d2, checks, check, zeroMatrixQ, frobSquared];
checks = {};
check[id_, proposition_] := AppendTo[checks,
  <|"id" -> id, "pass" -> TrueQ[proposition]|>];
zeroMatrixQ[a_] := TrueQ[And @@ (TrueQ[Simplify[# == 0]] & /@ Flatten[a])];
frobSquared[a_] := Tr[Transpose[a].a];

mm = DiagonalMatrix[{m1, m2, m3}];
xx = {{0, x12, x13}, {-x12, 0, x23}, {-x13, -x23, 0}};
tt = Expand[mm.xx - xx.mm];
ttExpected = {{0, (m1 - m2) x12, (m1 - m3) x13},
  {(m1 - m2) x12, 0, (m2 - m3) x23},
  {(m1 - m3) x13, (m2 - m3) x23, 0}};
check["diagonal_commutator_map", zeroMatrixQ[tt - ttExpected]];
check["skew_input_symmetric_zero_diagonal_output",
  zeroMatrixQ[tt - Transpose[tt]] &&
  zeroMatrixQ[DiagonalMatrix[Diagonal[tt]]]];

map = DiagonalMatrix[{m1 - m2, m1 - m3, m2 - m3}];
check["rank_three_kernel_zero_for_distinct_eigenvalues",
  TrueQ[FullSimplify[Det[map] != 0,
    Element[{m1, m2, m3}, Reals] && m1 != m2 && m1 != m3 && m2 != m3]]];
rr = {{0, r12, r13}, {r12, 0, r23}, {r13, r23, 0}};
inv = {{0, r12/(m1 - m2), r13/(m1 - m3)},
  {-r12/(m1 - m2), 0, r23/(m2 - m3)},
  {-r13/(m1 - m3), -r23/(m2 - m3), 0}};
check["exact_inverse_for_compatible_R",
  zeroMatrixQ[Together[mm.inv - inv.mm - rr]]];
check["frob_gap_identity",
  TrueQ[FullSimplify[frobSquared[tt] ==
    2 ((m1 - m2)^2 x12^2 + (m1 - m3)^2 x13^2 +
       (m2 - m3)^2 x23^2)]] &&
  TrueQ[FullSimplify[frobSquared[xx] ==
    2 (x12^2 + x13^2 + x23^2)]]];

(* In the orthonormal eigenbasis of Mhat, the image of the skew domain is
   exactly the symmetric matrices with zero diagonal. This is its Frobenius
   orthogonal projection, including when Rhat is nonsymmetric. *)
hh = DiagonalMatrix[{h1, h2, h3}];
qq = {{q11, q12, q13}, {q21, q22, q23}, {q31, q32, q33}};
proj = (qq + Transpose[qq])/2 - DiagonalMatrix[Diagonal[qq]];
orth = qq - proj;
yy = {{0, z12, z13}, {-z12, 0, z23}, {-z13, -z23, 0}};
ty = hh.yy - yy.hh;
check["projection_orthogonality",
  TrueQ[FullSimplify[Tr[Transpose[orth].ty] == 0]]];
check["projection_idempotent_and_symmetric",
  zeroMatrixQ[(proj + Transpose[proj])/2 -
    DiagonalMatrix[Diagonal[proj]] - proj]];

wHat = {{0, proj[[1, 2]]/(h1 - h2), proj[[1, 3]]/(h1 - h3)},
  {-proj[[1, 2]]/(h1 - h2), 0, proj[[2, 3]]/(h2 - h3)},
  {-proj[[1, 3]]/(h1 - h3), -proj[[2, 3]]/(h2 - h3), 0}};
check["least_squares_projected_inverse",
  zeroMatrixQ[Together[hh.wHat - wHat.hh - proj]]];
check["diagonal_residual_not_fitted",
  zeroMatrixQ[DiagonalMatrix[Diagonal[qq - (hh.wHat - wHat.hh)]] -
    DiagonalMatrix[{q11, q22, q33}]]];

(* The error identity is the part of the least-squares proof that a direct
   triangle argument would miss: T_h(W_hat-W)=P(R_hat-T_h(W)). *)
ee = qq - (hh.xx - xx.hh);
projE = (ee + Transpose[ee])/2 - DiagonalMatrix[Diagonal[ee]];
check["least_squares_error_projection_identity",
  zeroMatrixQ[Together[hh.(wHat - xx) - (wHat - xx).hh - projE]]];
check["scalar_bound_implication",
  TrueQ[Resolve[ForAll[{epsR, epsM, ws, dh, u, v},
    Implies[epsR >= 0 && epsM >= 0 && ws >= 0 && dh > 0 &&
       0 <= u <= v && v <= epsR + 2 epsM ws,
       u/dh <= (epsR + 2 epsM ws)/dh]], Reals]]];
check["commutator_operator_frobenius_coefficient_bound",
  TrueQ[Resolve[ForAll[{d1, d2, epsM},
    Implies[epsM >= 0 && Abs[d1] <= epsM && Abs[d2] <= epsM,
      (d1 - d2)^2 <= 4 epsM^2]], Reals]]];
check["ordered_eigenvalue_gap_scalar_step",
  TrueQ[Resolve[ForAll[{m1, m2, h1, h2, epsM},
    Implies[epsM >= 0 && Abs[h1 - m1] <= epsM &&
      Abs[h2 - m2] <= epsM,
      Abs[h1 - h2] >= Abs[m1 - m2] - 2 epsM]], Reals]]];

check["repeated_eigenvalue_kernel_control",
  zeroMatrixQ[(mm.xx - xx.mm) /. {m2 -> m1, x13 -> 0, x23 -> 0}]];
check["isotropic_zero_map_control",
  zeroMatrixQ[(mm.xx - xx.mm) /. {m2 -> m1, m3 -> m1}]];
check["perturbed_zero_gap_excluded",
  TrueQ[FullSimplify[Det[DiagonalMatrix[{h1 - h2, h1 - h3, h2 - h3}]] == 0,
    h1 == h2]]];

result = <|
  "component" -> "CAS-15-C03",
  "engine" -> "Wolfram Engine + xAct xTensor",
  "wolfram_version" -> System`$Version,
  "xtensor_version" -> ToString[xAct`xTensor`$Version, InputForm],
  "checks" -> checks,
  "all_pass" -> And @@ (Lookup[#, "pass"] & /@ checks)
|>;
Print["GATE_JSON:", ExportString[result, "RawJSON"]];
Exit[If[TrueQ[result["all_pass"]], 0, 1]];
