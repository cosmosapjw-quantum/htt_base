(* PR-182 Wolfram axis: solver-free parity identities, exact arithmetic. *)
(* Independent implementation; loads xAct as the axis-identity receipt.  *)

Needs["xAct`xTensor`"];
xactLoaded = Length[Names["xAct`xTensor`*"]] > 0;
If[!xactLoaded, Print["PR182_XACT False"]; Exit[3]];

checks = <||>;
computed = <||>;

(* I1 parity involution + axisymmetric B annihilation *)
P = {{1, 0}, {0, -1}};
checks["parity_involution_exact"] = (P . P === IdentityMatrix[2]);
fixed = NullSpace[P - IdentityMatrix[2]];
checks["axisymmetric_source_forces_B_zero"] =
  (Length[fixed] === 1 && fixed[[1, 2]] === 0 && fixed[[1, 1]] =!= 0);
computed["fixed_space_dim"] = ToString[Length[fixed]];

(* I2 reflection flips TB/EB, preserves TT/EE/BB/TE *)
M = {{tt, te, tb}, {te, ee, eb}, {tb, eb, bb}};
R = DiagonalMatrix[{1, 1, -1}];
Mp = R . M . R;
symbolicOK = And[
   Simplify[Mp[[1, 3]] + tb] === 0,
   Simplify[Mp[[2, 3]] + eb] === 0,
   Simplify[Mp[[1, 1]] - tt] === 0,
   Simplify[Mp[[2, 2]] - ee] === 0,
   Simplify[Mp[[3, 3]] - bb] === 0,
   Simplify[Mp[[1, 2]] - te] === 0];
F = {{1, 1/4, 3/7}, {1/4, 2/3, -2/5}, {3/7, -2/5, 1/9}};
Fp = R . F . R;
fixtureOK = And[
   Fp[[1, 3]] === -3/7, Fp[[2, 3]] === 2/5,
   Fp[[1, 1]] === 1, Fp[[2, 2]] === 2/3,
   Fp[[3, 3]] === 1/9, Fp[[1, 2]] === 1/4];
checks["reflection_flips_TB_EB_fixture"] = (symbolicOK && fixtureOK);
checks["reflection_preserves_TT_EE_BB_TE_fixture"] = fixtureOK;
computed["fixture_TB_flip"] = "3/7->" <> ToString[Fp[[1, 3]], InputForm];
computed["fixture_EB_flip"] = "-2/5->" <> ToString[Fp[[2, 3]], InputForm];

(* I3 VII_h handedness sign under improper transform *)
n = DiagonalMatrix[{0, 1, 1}];
a = {{1/2, 0, 0}};
Lam = DiagonalMatrix[{-1, 1, 1}];
nPrime = Det[Lam] * Lam . n . Transpose[Lam];
checks["vii_h_improper_transform_flips_n_sign"] = (nPrime === -n);
checks["vii_h_vector_constraint_holds_both_orientations"] =
  (a . n === {{0, 0, 0}} && a . nPrime === {{0, 0, 0}});
computed["n_prime_diagonal"] =
  "[" <> StringRiffle[
    ToString[#, InputForm] & /@ {nPrime[[1, 1]], nPrime[[2, 2]], nPrime[[3, 3]]},
    ", "] <> "]";

(* I4 boost kernel Sqrt[1-b^2]/(1-b*mu) to O(b^3): mu-only coefficients *)
kernel = Normal[Series[Sqrt[1 - b^2]/(1 - b*mu), {b, 0, 3}]];
expected = <|0 -> {1}, 1 -> {0, 1}, 2 -> {-1/2, 0, 1}, 3 -> {0, -1/2, 0, 1}|>;
allOK = True;
lists = <||>;
Do[
  poly = Expand[Coefficient[kernel, b, order]];
  expect = expected[order];
  got = Table[Coefficient[poly, mu, k], {k, 0, Length[expect] - 1}];
  If[got =!= expect || Expand[poly - Sum[expect[[k + 1]] mu^k, {k, 0, Length[expect] - 1}]] =!= 0,
    allOK = False];
  lists[ToString[order]] =
    ToString[Map[ToString[#, InputForm] &, got], InputForm],
  {order, 0, 3}];
checks["boost_kernel_mu_only_coefficients_exact"] = allOK;
Do[
  poly = Expand[Coefficient[kernel, b, order]];
  expect = expected[order];
  got = Table[Coefficient[poly, mu, k], {k, 0, Length[expect] - 1}];
  computed["boost_order_" <> ToString[order]] =
    "['" <> StringRiffle[ToString[#, InputForm] & /@ got, "', '"] <> "']",
  {order, 0, 3}];

allPass = And @@ Values[checks];
Print["PR182_CHECKS " <> ToString[Normal[checks], InputForm]];
Print["PR182_COMPUTED " <> ToString[Normal[computed], InputForm]];
Print["PR182_XACT " <> ToString[xactLoaded]];
Print["PR182_ALL_PASS " <> ToString[allPass]];
If[allPass, Exit[0], Exit[1]];
