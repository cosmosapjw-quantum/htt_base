(* Independent Wolfram Engine + xTensor proof for CAS-03-C02.
   Permitted inputs are limited by the frozen execution contract. *)

Needs["xAct`xTensor`"];

$DefInfoQ = False;
DefManifold[M4, 4, {a, b, cc, dd}];
DefMetric[-1, metric[-a, -b], CD];
DefTensor[BT[-a, -b], M4, Symmetric[{-a, -b}]];

wolframVersion = System`$Version;
xTensorVersion = xAct`xTensor`$Version;
xTensorLoaded = MatchQ[xTensorVersion, {_String | _Real, _List}] || ListQ[xTensorVersion];

g = DiagonalMatrix[{-1, 1, 1, 1}];
k = {-1, n1, n2, n3};
rchi = {Sinh[chi], Cosh[chi], 0, 0};
rchiFlat = {-Sinh[chi], Cosh[chi], 0, 0};
e2Flat = {0, 0, 1, 0};
e3Flat = {0, 0, 0, 1};

bChi = epsilon Outer[Times, rchiFlat, rchiFlat] +
  b2 Outer[Times, e2Flat, e2Flat] +
  b3 Outer[Times, e3Flat, e3Flat];
bZero = FullSimplify[bChi /. chi -> 0];

qChi = Expand[k . bChi . k];
qZero = Expand[k . bZero . k];
targetDifference = epsilon (Sinh[chi]^2 +
    2 Sinh[chi] Cosh[chi] n1 + Sinh[chi]^2 n1^2);

realScalars = Element[{epsilon, b2, b3, chi, n1, n2, n3}, Reals];
differenceResidual = FullSimplify[
  TrigToExp[qChi - qZero - targetDifference],
  Assumptions -> realScalars
];
differenceProof = TrueQ[differenceResidual === 0];

sphereRelation = n1^2 + n2^2 + n3^2 == 1;
sphereNullProof = TrueQ[Resolve[
  ForAll[{n1, n2, n3}, Implies[sphereRelation, k . g . k == 0]],
  Reals
]];
loweringProof = TrueQ[FullSimplify[g . rchi == rchiFlat, Assumptions -> realScalars]];
spacelikeProof = TrueQ[FullSimplify[rchi . g . rchi == 1, Assumptions -> realScalars]];
restBlock = bZero[[2 ;; 4, 2 ;; 4]];
restBlockProof = TrueQ[restBlock === DiagonalMatrix[{epsilon, b2, b3}]];

coefficients = {epsilon, b2, b3};
kernelVariables = {v1, v2, v3};
restDiagonal = DiagonalMatrix[coefficients];
kernelEquations = And @@ Thread[restDiagonal . kernelVariables == ConstantArray[0, 3]];

stratumCertificate[bits_List] := Module[
  {assumptions, nonzeroPositions, zeroPositions, rank, expectedKernel,
   pivotCondition, higherMinorCondition, kernelResult, rankResult},
  nonzeroPositions = Flatten@Position[bits, 1];
  zeroPositions = Flatten@Position[bits, 0];
  rank = Total[bits];
  assumptions = And @@ MapThread[
    If[#1 == 0, #2 == 0, #2 != 0] &,
    {bits, coefficients}
  ];
  expectedKernel = If[
    nonzeroPositions === {},
    True,
    And @@ Thread[kernelVariables[[nonzeroPositions]] == 0]
  ];
  pivotCondition = If[
    rank == 0,
    True,
    Det[restDiagonal[[nonzeroPositions, nonzeroPositions]]] != 0
  ];
  higherMinorCondition = If[
    rank == 3,
    True,
    And @@ Thread[Flatten[Minors[restDiagonal, rank + 1]] == 0]
  ];
  kernelResult = Resolve[
    ForAll @@ {Join[coefficients, kernelVariables],
      Implies[assumptions, Equivalent[kernelEquations, expectedKernel]]},
    Reals
  ];
  rankResult = Resolve[
    ForAll @@ {coefficients,
      Implies[assumptions, pivotCondition && higherMinorCondition]},
    Reals
  ];
  <|
    "zero_pattern" -> bits,
    "rank" -> rank,
    "kernel_dimension" -> Length[zeroPositions],
    "kernel_equivalence_proved" -> TrueQ[kernelResult],
    "rank_minor_certificate_proved" -> TrueQ[rankResult]
  |>
];

rankStrata = stratumCertificate /@ Tuples[{0, 1}, 3];
allRankStrataProof = And @@ (
  TrueQ[#["kernel_equivalence_proved"]] &&
    TrueQ[#["rank_minor_certificate_proved"]] &&
    (#["kernel_dimension"] == Count[#["zero_pattern"], 0]) & /@ rankStrata
);

repeatedAllNonzeroProof = TrueQ[Resolve[
  ForAll[{rho, v1, v2, v3},
    Implies[rho != 0,
      Equivalent[
        DiagonalMatrix[{rho, rho, rho}] . {v1, v2, v3} == {0, 0, 0},
        {v1, v2, v3} == {0, 0, 0}
      ] && Det[DiagonalMatrix[{rho, rho, rho}]] != 0
    ]
  ],
  Reals
]];

repeatedTwoNonzeroProof = TrueQ[Resolve[
  ForAll[{rho, v1, v2, v3},
    Implies[rho != 0,
      Equivalent[
        DiagonalMatrix[{rho, rho, 0}] . {v1, v2, v3} == {0, 0, 0},
        v1 == 0 && v2 == 0
      ] && Det[DiagonalMatrix[{rho, rho}]] != 0
    ]
  ],
  Reals
]];

allZeroProof = TrueQ[
  (restDiagonal /. Thread[coefficients -> 0]) === ConstantArray[0, {3, 3}] &&
  MatrixRank[ConstantArray[0, {3, 3}]] == 0 &&
  Length[NullSpace[ConstantArray[0, {3, 3}]]] == 3
];

checks = <|
  "xTensor_loaded_and_definitions_executed" -> xTensorLoaded,
  "metric_lowering_rchi" -> loweringProof,
  "rchi_unit_spacelike" -> spacelikeProof,
  "unit_sphere_makes_K_null" -> sphereNullProof,
  "family_difference_exact" -> differenceProof,
  "chi0_rest_block_exact" -> restBlockProof,
  "all_eight_rank_strata_exact" -> allRankStrataProof,
  "repeated_all_nonzero_control" -> repeatedAllNonzeroProof,
  "repeated_two_nonzero_control" -> repeatedTwoNonzeroProof,
  "all_zero_control" -> allZeroProof
|>;

overallPass = And @@ Values[checks];
engineResult = <|
  "status" -> If[overallPass, "PASS", "FAIL"],
  "evidence_class" -> "exact",
  "wolfram_version" -> wolframVersion,
  "xtensor_version" -> ToString[xTensorVersion, InputForm],
  "difference" -> ToString[FullSimplify[qChi - qZero, Assumptions -> realScalars], InputForm],
  "target" -> ToString[targetDifference, InputForm],
  "difference_residual" -> ToString[differenceResidual, InputForm],
  "checks" -> checks,
  "rank_strata" -> rankStrata,
  "domain_assumption_diff" -> {},
  "remaining_obligations" -> {"CAS03 C03", "eigenfield existence/IFT", "science"}
|>;

Print["CAS_RESULT_JSON=" <> ExportString[engineResult, "RawJSON", "Compact" -> True]];
Exit[If[overallPass, 0, 2]];
