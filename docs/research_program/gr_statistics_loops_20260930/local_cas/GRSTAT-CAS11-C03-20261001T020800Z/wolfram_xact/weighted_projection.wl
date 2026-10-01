(* CAS11-C03 v3, Wolfram Engine + xAct. The dimension-free argument is in PROOF.md.
   These checks certify algebraic steps and tensor symmetry, not positivity by sampling. *)
Print["WOLFRAM_VERSION=" <> ToString[$Version]];
Needs["xAct`xTensor`"];
Print["XACT_VERSION=" <> ToString[xAct`xTensor`$Version, InputForm]];

DefManifold[CASManifold, 3, {ca, cb}];
DefMetric[1, casg[-ca, -cb], casCD];
DefTensor[casu[ca], CASManifold];
DefTensor[casv[ca], CASManifold];
tensorSymmetry = TrueQ[
  ToCanonical[casg[-ca, -cb] casu[ca] casv[cb] -
    casg[-ca, -cb] casv[ca] casu[cb]] === 0
];

(* Each coordinate of an orthogonal projector in an adapted orthonormal
   frame has eigenvalue 0 or 1. The frame-existence proof is in PROOF.md. *)
idempotenceComponents = And @@ (TrueQ[#^2 == #] & /@ {0, 1});
orthogonalityComponents = And @@ (TrueQ[# (1 - #) == 0] & /@ {0, 1});

(* Finite bilinear expansion: 2 family members and 3 coordinates, with all
   entries indeterminate. The arbitrary-size distributive step is proved
   separately in PROOF.md. *)
gramPolynomial = Expand[
  Sum[aa[ii] aa[jj] Sum[rr[ii, kk] rr[jj, kk], {kk, 1, 3}],
      {ii, 1, 2}, {jj, 1, 2}] -
  Sum[(Sum[aa[ii] rr[ii, kk], {ii, 1, 2}])^2, {kk, 1, 3}]
];
gramExpansion = TrueQ[gramPolynomial === 0];

(* For q=<y,y>>0, s=<x,y>, t=<x,x>, the residual
   z=x-(s/q)y satisfies q<z,z>=q t-s^2. *)
csPolynomial = FullSimplify[
  q (t - 2 (s/q) s + (s/q)^2 q) - (q t - s^2), q > 0
];
csSquareIdentity = TrueQ[csPolynomial === 0];

(* Edge-control checks; they are not substitutes for the universal proof. *)
emptyFamily = TrueQ[Total[{}] == 0];
dependentResidualControl = TrueQ[
  Sort[Eigenvalues[{{1, 2}, {2, 4}}]] === {0, 5}
];
checks = <|
  "xact_tensor_symmetry" -> tensorSymmetry,
  "projector_coordinate_idempotence" -> idempotenceComponents,
  "projector_coordinate_orthogonality" -> orthogonalityComponents,
  "gram_bilinear_polynomial" -> gramExpansion,
  "cauchy_schwarz_square_identity" -> csSquareIdentity,
  "empty_family_control" -> emptyFamily,
  "dependent_residual_control" -> dependentResidualControl
|>;
Print["CAS11_C03_CHECKS=" <> ExportString[checks, "RawJSON"]];
If[And @@ Values[checks], Exit[0], Exit[2]];
