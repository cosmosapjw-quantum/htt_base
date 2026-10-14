(* Independent Wolfram+xTensor proof of the frozen CAS-02 C01--C03 components. *)
ClearAll["Global`*"];
Needs["xAct`xTensor`"];
wolframVersion = $Version;
xTensorVersion = ToString[xAct`xTensor`$Version, InputForm];
Print["CAS_STAGE:loaded"];

(* C01: two arbitrary real optical embeddings, with symmetric tracefree h2. *)
qa = {{pa, ra, sa}, {ra, ta, va}, {sa, va, -pa - ta}};
qb = {{pb, rb, sb}, {rb, tb, vb}, {sb, vb, -pb - tb}};
ha = {aa, ba, ca}; hb = {ab, bb, cb};
embed[h0_, h_, h2_] := ArrayFlatten[{{{{h0}}, {-h/2}}, {Transpose[{-h/2}], h2}}];
sa = embed[h0a, ha, qa]; sb = embed[h0b, hb, qb];
deltaS = sb - sa;
deltaH0 = h0b - h0a; deltaH1 = hb - ha; deltaH2 = qb - qa;
frob2[m_] := Total[Flatten[m*m]];
c01normResidual = Factor[frob2[deltaS] - deltaH0^2 - Total[deltaH1^2]/2 - frob2[deltaH2]];
metric = DiagonalMatrix[{-1, 1, 1, 1}];
c01metric = FullSimplify[Sqrt[frob2[metric]] == 2];
c01trace = Tr[qa] == 0 && Tr[qb] == 0;
Print["CAS_STAGE:C01"];

(* C02: universal coordinate polynomial, requiring no special unit-vector simplification. *)
s1 = {{a11, a12, a13, a14}, {a12, a22, a23, a24},
      {a13, a23, a33, a34}, {a14, a24, a34, a44}};
s2 = {{b11, b12, b13, b14}, {b12, b22, b23, b24},
      {b13, b23, b33, b34}, {b14, b24, b34, b44}};
u1 = {x1, x2, x3, x4}; u2 = {y1, y2, y3, y4};
quad[m_, x_, y_] := x . m . y;
deltaQuadratic = quad[s2, u2, u2] - quad[s1, u1, u1];
c02first = Expand[deltaQuadratic - (quad[s2 - s1, u2, u2] +
    quad[s1, u2 - u1, u2] + quad[s1, u1, u2 - u1])];
c02swapped = Expand[deltaQuadratic - (quad[s2 - s1, u1, u1] +
    quad[s2, u2 - u1, u2] + quad[s2, u1, u2 - u1])];
Print["CAS_STAGE:C02-coordinate"];

(* Independent abstract-index contraction/canonicalization by xTensor. *)
DefManifold[CASM, 4, {ia, ib}];
DefTensor[SA[-ia, -ib], CASM, Symmetric[{-ia, -ib}]];
DefTensor[SB[-ia, -ib], CASM, Symmetric[{-ia, -ib}]];
DefTensor[UA[ia], CASM]; DefTensor[UB[ia], CASM];
abstractDelta = SB[-ia, -ib] UB[ia] UB[ib] - SA[-ia, -ib] UA[ia] UA[ib];
abstractFirst = (SB[-ia, -ib] - SA[-ia, -ib]) UB[ia] UB[ib] +
   (UB[ia] - UA[ia]) SA[-ia, -ib] UB[ib] +
   UA[ia] SA[-ia, -ib] (UB[ib] - UA[ib]);
abstractSwapped = (SB[-ia, -ib] - SA[-ia, -ib]) UA[ia] UA[ib] +
   (UB[ia] - UA[ia]) SB[-ia, -ib] UB[ib] +
   UA[ia] SB[-ia, -ib] (UB[ib] - UA[ib]);
c02xactFirst = ToCanonical[Expand[abstractDelta - abstractFirst]];
c02xactSwapped = ToCanonical[Expand[abstractDelta - abstractSwapped]];
Print["CAS_STAGE:C02-xTensor"];

(* C03: differentiate the actual positive-branch map, then construct its Gram. *)
d = {d1, d2, d3}; rho2 = d . d;
chart = Join[{Sqrt[1 + rho2]}, d];
jac = Table[D[chart[[i]], d[[j]]], {i, 1, 4}, {j, 1, 3}];
expectedJac = Join[{d/Sqrt[1 + rho2]}, IdentityMatrix[3]];
c03jacResidual = FullSimplify[jac - expectedJac, Element[d, Reals]];
gram = Transpose[jac] . jac;
expectedGram = IdentityMatrix[3] + Outer[Times, d, d]/(1 + rho2);
c03gramResidual = FullSimplify[gram - expectedGram, Element[d, Reals]];
lam = Unique["lambda"];
charPoly = Factor[CharacteristicPolynomial[gram, lam]];
expectedPoly = (lam - 1)^2 (lam - 1 - rho2/(1 + rho2));
c03polyResidual = FullSimplify[charPoly - expectedPoly, Element[d, Reals]];
c03radialResidual = FullSimplify[gram . d - (1 + rho2/(1 + rho2)) d,
  Element[d, Reals]];
c03zeroEigen = Eigenvalues[gram /. Thread[d -> {0, 0, 0}]];
Print["CAS_STAGE:C03-spectrum"];

(* The ball condition gives rho2 <= sinh(R)^2 and forces R >= 0. *)
c03radiusNonnegative = FullSimplify[
  Implies[Sinh[rr] >= 0, rr >= 0], Element[rr, Reals]];
c03monotone = Resolve[ForAll[{qvar, svar},
   Implies[0 <= qvar && qvar <= svar,
    1 + qvar/(1 + qvar) <= 1 + svar/(1 + svar)]], Reals];
c03hyperbolic = FullSimplify[
  Sinh[rr]^2/(1 + Sinh[rr]^2) == Tanh[rr]^2,
  Element[rr, Reals]];
Print["CAS_STAGE:C03-bound"];

checks = <|
  "CAS-02-C01" -> TrueQ[c01normResidual == 0 && c01metric && c01trace],
  "CAS-02-C02" -> TrueQ[c02first == 0 && c02swapped == 0 &&
    c02xactFirst == 0 && c02xactSwapped == 0],
  "CAS-02-C03" -> TrueQ[c03jacResidual == ConstantArray[0, {4, 3}] &&
    c03gramResidual == ConstantArray[0, {3, 3}] && c03polyResidual == 0 &&
    c03radialResidual == {0, 0, 0} && c03zeroEigen == {1, 1, 1} &&
    c03radiusNonnegative && c03monotone && c03hyperbolic]
|>;
details = <|
  "C01_Frobenius_residual" -> ToString[c01normResidual, InputForm],
  "C01_metric_norm_two" -> c01metric,
  "C02_coordinate_first_residual" -> ToString[c02first, InputForm],
  "C02_coordinate_swapped_residual" -> ToString[c02swapped, InputForm],
  "C02_xTensor_first_canonical" -> ToString[c02xactFirst, InputForm],
  "C02_xTensor_swapped_canonical" -> ToString[c02xactSwapped, InputForm],
  "C03_Jacobian" -> ToString[jac, InputForm],
  "C03_Jacobian_residual" -> ToString[c03jacResidual, InputForm],
  "C03_Gram" -> ToString[gram, InputForm],
  "C03_Gram_residual" -> ToString[c03gramResidual, InputForm],
  "C03_characteristic_polynomial" -> ToString[charPoly, InputForm],
  "C03_characteristic_residual" -> ToString[c03polyResidual, InputForm],
  "C03_radial_eigen_residual" -> ToString[c03radialResidual, InputForm],
  "C03_zero_eigenvalues" -> ToString[c03zeroEigen, InputForm],
  "C03_radius_nonnegative" -> c03radiusNonnegative,
  "C03_monotone_rational_bound" -> c03monotone,
  "C03_hyperbolic_identity" -> c03hyperbolic
|>;
Print["CAS_JSON:" <> ExportString[<|
  "checks" -> checks, "details" -> details,
  "wolfram_version" -> wolframVersion, "xtensor_version" -> xTensorVersion
|>, "RawJSON", "Compact" -> True]];
If[! And @@ Values[checks], Exit[2], Exit[0]];
