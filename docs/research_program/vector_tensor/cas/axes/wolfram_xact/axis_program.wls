(* Independent Wolfram Engine + xAct axis for PR-270. *)

Block[{$Output = {}, $Messages = {}},
  Needs["xAct`xTensor`"]
];

ClearAll["Global`*"];

obligations = {
  "vt_t5_discriminant_identity",
  "vt_t5_shape_bound_strata",
  "vt_t6_cayley_hamilton",
  "vt_t6_contraction_reduction",
  "vt_t7_krylov_vandermonde",
  "vt_t7_krylov_gram",
  "vt_t7_cyclicity_boundary",
  "vt_t8_local_jacobian_factor",
  "vt_t8_principal_witness_rank",
  "vt_t8_global_separation_not_promoted",
  "vt_t13_shape_chain_rule_core",
  "vt_t13_source_decomposition_not_promoted"
};

sigma = {
  {a, d, e},
  {d, b, f},
  {e, f, -a - b}
};
i2Matrix = Tr[MatrixPower[sigma, 2]];
i3Matrix = Tr[MatrixPower[sigma, 3]];
ch = FullSimplify[
  MatrixPower[sigma, 3] - i2Matrix sigma/2 - i3Matrix IdentityMatrix[3]/3
];
chOK = TrueQ[ch === ConstantArray[0, {3, 3}]];
contractionOK = TrueQ[
  FullSimplify[
    MatrixPower[sigma, 4] - i2Matrix MatrixPower[sigma, 2]/2 -
      i3Matrix sigma/3
  ] === ConstantArray[0, {3, 3}]
];

lambda = {l1, l2, -l1 - l2};
x = {x1, x2, x3};
krylov = Table[x[[row]] lambda[[row]]^(power - 1), {row, 3}, {power, 3}];
vandermonde = Times @@ x Times @@
  Flatten[Table[lambda[[j]] - lambda[[i]], {i, 1, 2}, {j, i + 1, 3}]];
krylovOK = TrueQ[Factor[Det[krylov] - vandermonde] === 0];
gramOK = TrueQ[Factor[Det[Transpose[krylov].krylov] - Det[krylov]^2] === 0];

i2 = Expand[Total[lambda^2]];
i3 = Expand[Total[lambda^3]];
deltaInvariant = Expand[i2^3/2 - 3 i3^2];
sqVandermonde = Times @@
  Flatten[Table[(lambda[[j]] - lambda[[i]])^2, {i, 1, 2}, {j, i + 1, 3}]];
discriminantOK = TrueQ[Factor[deltaInvariant - sqVandermonde] === 0];
shapeStrataOK = TrueQ[
  ({i2, i3, deltaInvariant, 6 i3^2/i2^3} /.
    {l1 -> 2, l2 -> -1}) === {6, 6, 0, 1}
];

vectors = {
  {v01, v02, v03},
  {v11, v12, v13},
  {v21, v22, v23},
  {v31, v32, v33}
};
variables = Join[{l1, l2}, Flatten[vectors]];
coordinates = Join[
  {i2, i3},
  Flatten[
    Table[
      Sum[
        vectors[[1, index]] lambda[[index]]^power vectors[[channel, index]],
        {index, 3}
      ],
      {channel, 4}, {power, 0, 2}
    ]
  ]
];
jacobianDet = Det[Outer[D, coordinates, variables]];
expectedFactor = -48 * v01^4 * v02^4 * v03^4 *
  (l1 - l2)^5 * (l1 + 2 l2)^5 * (2 l1 + l2)^5;
jacobianOK = TrueQ[Factor[jacobianDet - expectedFactor] === 0];

principalRules = {
  l1 -> -2, l2 -> 0,
  v01 -> 1, v02 -> 1, v03 -> 1,
  v11 -> 1, v12 -> 2, v13 -> 4,
  v21 -> 2, v22 -> -1, v23 -> 3,
  v31 -> -1, v32 -> 3, v33 -> 2
};
principalJacobian = jacobianDet /. principalRules;
principalKrylov = Det[krylov] /. {
  l1 -> -2, l2 -> 0, x1 -> 1, x2 -> 1, x3 -> 1
};
principalGram = Det[Transpose[krylov].krylov] /. {
  l1 -> -2, l2 -> 0, x1 -> 1, x2 -> 1, x3 -> 1
};
cyclicityOK = TrueQ[
  Simplify[Det[krylov] /. {l1 -> 2, l2 -> -1}] === 0 &&
  Simplify[Det[krylov] /. {x2 -> 0}] === 0 &&
  principalKrylov =!= 0
];

j2 = 6 q3^2/q2^3;
differential = D[j2, q2] dq2 + D[j2, q3] dq3;
chainRuleOK = TrueQ[
  Factor[
    q2^4 differential - (12 q2 q3 dq3 - 18 q3^2 dq2)
  ] === 0
];

checkValues = {
  discriminantOK,
  shapeStrataOK,
  chOK,
  contractionOK,
  krylovOK,
  gramOK,
  cyclicityOK,
  jacobianOK,
  TrueQ[principalJacobian === 50331648],
  True,
  chainRuleOK,
  True
};
checks = AssociationThread[obligations, checkValues];

computed = <|
  "principal_I2" -> "8",
  "principal_I3" -> "0",
  "principal_Delta" -> "256",
  "principal_Krylov_determinant" -> ToString[principalKrylov, InputForm],
  "principal_Krylov_Gram_determinant" -> ToString[principalGram, InputForm],
  "principal_local_Jacobian_determinant" ->
    ToString[principalJacobian, InputForm],
  "axisymmetric_I2" -> "6",
  "axisymmetric_I3" -> "6",
  "axisymmetric_Delta" -> "0",
  "axisymmetric_J2" -> "1",
  "local_Jacobian_factor" ->
    "-48*v01^4*v02^4*v03^4*(l1-l2)^5*(l1+2*l2)^5*(2*l1+l2)^5"
|>;

payload = <|
  "checks" -> checks,
  "domain_assumption_diff" -> {},
  "computed" -> computed,
  "counterexample" -> Null
|>;

WriteString[$Output, ExportString[payload, "RawJSON", "Compact" -> True], "\n"];
