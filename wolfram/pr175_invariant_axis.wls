(* PR-175 Wolfram axis: independent exact Koszul chain vs external anchor. *)
(* Loads xAct as the axis-identity receipt (enforced). No family ranking. *)

Needs["xAct`xTensor`"];
xactLoaded = Length[Names["xAct`xTensor`*"]] > 0;
If[!xactLoaded, Print["PR175_XACT False"]; Exit[3]];

types = <|
  "I" -> {{0, 0, 0}, 0}, "II" -> {{1, 0, 0}, 0},
  "VI_0" -> {{1, -1, 0}, 0}, "VII_0" -> {{1, 1, 0}, 0},
  "VIII" -> {{1, 1, -1}, 0}, "IX" -> {{1, 1, 1}, 0},
  "V" -> {{0, 0, 0}, 1}, "IV" -> {{0, 0, 1}, 1},
  "III" -> {{0, 1, -1}, 1},
  "VI_h" -> {{0, 1, -1}, 1/2}, "VII_h" -> {{0, 1, 1}, 1/2}|>;
hParams = <|"VI_h" -> -1/4, "VII_h" -> 1/4|>;

structure[nvec_, a_] := Module[{avec = {a, 0, 0}, C3},
  C3 = Table[
    Sum[Signature[{b, c, d}] * If[d == A, nvec[[A]], 0], {d, 1, 3}]
      + avec[[b]] * KroneckerDelta[A, c]
      - avec[[c]] * KroneckerDelta[A, b],
    {A, 1, 3}, {b, 1, 3}, {c, 1, 3}];
  C3];

ricciScalar[nvec_, a_] := Module[{C3 = structure[nvec, a], G, total},
  G = Table[
    (1/2) (C3[[c, x, b]] - C3[[x, b, c]] + C3[[b, c, x]]),
    {c, 1, 3}, {x, 1, 3}, {b, 1, 3}];
  total = Sum[
    Sum[
      G[[e, b, b]] G[[A, A, e]] - G[[e, A, b]] G[[A, b, e]]
        - C3[[e, A, b]] G[[A, e, b]],
      {A, 1, 3}, {e, 1, 3}],
    {b, 1, 3}];
  Simplify[total]];

anchor[nvec_, a_] := Module[{n1 = nvec[[1]], n2 = nvec[[2]], n3 = nvec[[3]]},
  -(1/2) (n1^2 + n2^2 + n3^2) + (n1 n2 + n2 n3 + n3 n1) - 6 a^2];

computed = <||>;
anchorOK = True;
Do[
  {nvec, a} = types[name];
  exact = ricciScalar[nvec, a];
  anchorOK = anchorOK && (exact === anchor[nvec, a]);
  computed["R_" <> name] = ToString[exact, InputForm],
  {name, Keys[types]}];

(* Class-B constraint DERIVED from constructed C: reconstruct n and a,
   require a.n = 0 and the Jacobi identity for every representative. *)
classBOK = And @@ Table[
  Module[{nvec, a, C3, nRec, nSym, aRec, aDotN, jacobiOK},
    {nvec, a} = types[name];
    C3 = structure[nvec, a];
    nRec = Table[(1/2) Sum[Signature[{b, c, d}] C3[[A, c, d]],
      {c, 1, 3}, {d, 1, 3}], {A, 1, 3}, {b, 1, 3}];
    nSym = (nRec + Transpose[nRec])/2;
    aRec = Table[(1/2) Sum[C3[[d, d, b]], {d, 1, 3}], {b, 1, 3}];
    aDotN = Table[Sum[aRec[[b]] nSym[[b, A]], {b, 1, 3}], {A, 1, 3}];
    jacobiOK = And @@ Flatten[Table[
      Sum[C3[[e, b, c]] C3[[A, d, e]] + C3[[e, c, d]] C3[[A, b, e]]
        + C3[[e, d, b]] C3[[A, c, e]], {e, 1, 3}] == 0,
      {A, 1, 3}, {b, 1, 3}, {c, 1, 3}, {d, 1, 3}]];
    (And @@ (# == 0 & /@ aDotN)) && jacobiOK],
  {name, Keys[types]}];
hOK = And @@ Table[
  Module[{nvec = types[name][[1]], a = types[name][[2]], h = hParams[name]},
    a^2 === Abs[h] Abs[nvec[[2]] nvec[[3]]] &&
      (h > 0) === (nvec[[2]] nvec[[3]] > 0)],
  {name, Keys[hParams]}];

checks = <|
  "eleven_type_ricci_scalar_matches_anchor" -> anchorOK,
  "class_b_vector_constraint_a_dot_n_zero" -> classBOK,
  "vi_vii_h_relation_consistent" -> hOK|>;
allPass = And @@ Values[checks];
Print["PR175_CHECKS " <> ToString[Normal[checks], InputForm]];
Print["PR175_COMPUTED " <> ToString[Normal[computed], InputForm]];
Print["PR175_XACT True"];
Print["PR175_ALL_PASS " <> ToString[allPass]];
If[allPass, Exit[0], Exit[1]];
