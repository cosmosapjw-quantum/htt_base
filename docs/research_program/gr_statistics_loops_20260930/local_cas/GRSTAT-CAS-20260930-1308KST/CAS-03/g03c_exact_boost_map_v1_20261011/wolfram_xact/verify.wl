(* G03-C exact canonical boost: independent finite-component Wolfram axis. *)
ClearAll[assert, b, n, d, q, gamma, a, eta, l, restB, boostedB, s, redshift];
$HistoryLength = 0;
failed = {};
assert[name_, expr_] := Module[{v = Quiet[Check[TrueQ[expr], $Failed]]},
  Print[name, ": ", If[v === True, "PASS", "FAIL"]];
  If[v =!= True, AppendTo[failed, name]];
];
Print["WolframVersion: ", $Version];
Print["SystemID: ", $SystemID];
Print["InputFile: ", $InputFileName];
Print["xActLoad: ", If[Quiet[Check[Needs["xAct`xTensor`"], $Failed]] === $Failed,
  "UNAVAILABLE", "LOADED xTensor " <> ToString[Quiet[Check[xAct`xTensor`$Version, "VERSION_UNKNOWN"]]]]];
Print["xActScope: package availability only; all identities below use exact finite matrix/component algebra"];

b = Array[bb, 3]; n = Array[nn, 3];
d = {{d11, d12, d13}, {d12, d22, d23}, {d13, d23, d33}};
q = b.b;
gamma = 1/Sqrt[1 - q];
a = gamma^2/(gamma + 1);
eta = DiagonalMatrix[{-1, 1, 1, 1}];
l = Prepend[MapThread[Prepend, {IdentityMatrix[3] + a Outer[Times, b, b], gamma b}], Prepend[gamma b, gamma]];
restB = Prepend[Map[Prepend[#, 0] &, d], ConstantArray[0, 4]];
boostedB = Transpose[l].restB.l;
s = b.d.b;
redshift = -(l.Join[{-1}, n])[[1]];
assumptions = Element[Join[b, n, {d11, d12, d13, d22, d23, d33}], Reals] && q < 1;

(* Canonical rotation-free spatial block follows from gamma^2(1-q)=1. *)
assert["positive_gamma", FullSimplify[gamma > 0, assumptions]];
assert["gamma_square", FullSimplify[gamma^2 (1 - q) == 1, assumptions]];
assert["boostA_q", FullSimplify[a q == gamma - 1, assumptions]];
assert["canonical_spatial_block", And @@ (FullSimplify[# == 0, assumptions && q > 0] & /@
  Flatten[l[[2 ;; 4, 2 ;; 4]] - IdentityMatrix[3] - ((gamma - 1)/q) Outer[Times, b, b]])];
assert["zero_beta_continuation", (l /. Thread[b -> {0, 0, 0}]) === IdentityMatrix[4]];
assert["lorentz_identity", And @@ (FullSimplify[# == 0, assumptions] & /@
  Flatten[Transpose[l].eta.l - eta])];
assert["future_time", FullSimplify[l[[1, 1]] > 0, assumptions]];
assert["future_column_norm", FullSimplify[l[[1, 1]]^2 - Sum[l[[i, 1]]^2, {i, 2, 4}] == 1, assumptions]];
assert["B0i_symmetric_D", And @@ Table[FullSimplify[
  boostedB[[1, i + 1]] == gamma ((d.b)[[i]] + a b[[i]] s), assumptions], {i, 3}]];
assert["redshift_sign", FullSimplify[redshift == gamma (1 - b.n), assumptions]];
assert["dipole_exact", And @@ Table[FullSimplify[
  -2 boostedB[[1, i + 1]] == -2 gamma ((d.b)[[i]] + a b[[i]] s), assumptions], {i, 3}]];
Print["Scope: exact finite one-event component identities with fixed symmetric D; no remainder, inverse error, distance or matter theorem"];
Print["FailedChecks: ", failed];
Exit[If[failed === {}, 0, 1]];
