(* Final PR-254 Wolfram+xAct blind axis.

   Scientific contract: CAS-PR254-ANCHOR-GEOMETRY-001
   Contract SHA-256: 4f7092860fde327e0029154e3c4ca4c7e60f7095c4026c7fb00d1899ca8c3322

   The registered JSON contract and counterexample oracle are parsed at
   runtime.  In particular, the POLYTOPE-FIXTURE normals and bounds are
   consumed in their sealed order; no box normals are supplied by this file.
   Stdout is reserved for exactly one compact JSON document.
*)

ClearAll["Global`*"];
$HistoryLength = 0;

contractPath =
  "docs/generated/pr254_anchor_geometry/CAS_CONTRACT_PR254_ANCHOR_GEOMETRY.json";
specPath = "docs/research_program/premise_anchor/pr254_spec.yaml";
sourcePath = "htt/src/common/anchor_geometry.py";
oraclePath =
  "docs/generated/pr254_anchor_geometry/counterexample_oracle.json";
sealedContractHash =
  "4f7092860fde327e0029154e3c4ca4c7e60f7095c4026c7fb00d1899ca8c3322";

contract = Import[contractPath, "RawJSON"];
oracle = Import[oraclePath, "RawJSON"];
contractHash = FileHash[contractPath, "SHA256", "HexString"];
contractHashOK = TrueQ[contractHash === sealedContractHash];

sourceHashes = Association[
  (#["path"] -> #["sha256"]) & /@
    contract["identity"]["source_input_hashes"]
];
specHashOK = TrueQ[
  FileHash[specPath, "SHA256", "HexString"] === sourceHashes[specPath]
];
sourceHashOK = TrueQ[
  FileHash[sourcePath, "SHA256", "HexString"] === sourceHashes[sourcePath]
];
oracleHashOK = TrueQ[
  FileHash[oraclePath, "SHA256", "HexString"] === sourceHashes[oraclePath]
];
inputIntegrityOK =
  contractHashOK && specHashOK && sourceHashOK && oracleHashOK;

exactPattern = RegularExpression[
  "-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?"
];
parseExact[text_String] := If[
  StringMatchQ[text, exactPattern],
  ToExpression[text, InputForm],
  Throw[{"INVALID_EXACT_LITERAL", text}]
];
ratString[value_] := ToString[Together[value], InputForm];
vectorStrings[vector_List] := ratString /@ vector;
matrixStrings[matrix_List] := vectorStrings /@ matrix;

fixtures = contract["target"]["numeric_test_vectors"];
fixtureById[id_String] := SelectFirst[fixtures, #["id"] === id &];

(* Load xAct without allowing its package banner to contaminate stdout. *)
xactLoaded = TrueQ[
  Quiet[
    Check[
      Block[
        {Print = Function[Null]},
        Needs["xAct`xTensor`"];
        MemberQ[$Packages, "xAct`xTensor`"]
      ],
      False
    ]
  ]
];
xactVersion = If[
  xactLoaded && ValueQ[xAct`xTensor`$Version],
  First[xAct`xTensor`$Version],
  "unavailable"
];
xactVersionParts = If[
  StringQ[xactVersion] &&
    StringMatchQ[xactVersion, RegularExpression["[0-9]+\\.[0-9]+\\.[0-9]+"]],
  parseExact /@ StringSplit[xactVersion, "."],
  {}
];
wolframPinnedOK = TrueQ[System`$VersionNumber == 15];
xactPinnedOK = TrueQ[
  Length[xactVersionParts] == 3 &&
    10000 xactVersionParts[[1]] +
      100 xactVersionParts[[2]] +
      xactVersionParts[[3]] >= 10200
];

(* Product-ball fixture and exact two-block unit-sublevel theorem. *)
productFixture = fixtureById["PRODUCT-FIXTURE"];
productBlockRecords = productFixture["blocks"];
productVectors = (parseExact /@ #["u"]) & /@ productBlockRecords;
productRadii = parseExact /@ ((#["radius"]) & /@ productBlockRecords);
productRatios = MapThread[
  Sqrt[#1.#1]/#2 &,
  {productVectors, productRadii}
];
productGauge = Max @@ productRatios;

productNormVariables = Table[
  Symbol["productNorm" <> ToString[index]],
  {index, Length[productRadii]}
];
productRadiusVariables = Table[
  Symbol["productRadius" <> ToString[index]],
  {index, Length[productRadii]}
];
productSublevelTheorem = Resolve[
  ForAll[
    Evaluate[Join[productNormVariables, productRadiusVariables]],
    Implies[
      And @@ (# >= 0 & /@ productNormVariables) &&
        And @@ (# > 0 & /@ productRadiusVariables),
      Equivalent[
        Max @@ MapThread[
          Divide,
          {productNormVariables, productRadiusVariables}
        ] <= 1,
        And @@ MapThread[
          LessEqual,
          {productNormVariables, productRadiusVariables}
        ]
      ]
    ]
  ],
  Reals
];

(* Ellipsoid fixture and exact unit-sublevel equivalence. *)
ellipsoidFixture = fixtureById["ELLIPSOID-FIXTURE"];
ellipsoidVector = parseExact /@ ellipsoidFixture["u"];
ellipsoidMatrix = (parseExact /@ #) & /@ ellipsoidFixture["Q"];
ellipsoidGaugeSq =
  Together[ellipsoidVector.ellipsoidMatrix.ellipsoidVector];
ellipsoidSymmetric =
  TrueQ[ellipsoidMatrix === Transpose[ellipsoidMatrix]];
ellipsoidLeadingMinors = Table[
  Det[ellipsoidMatrix[[1 ;; k, 1 ;; k]]],
  {k, Length[ellipsoidMatrix]}
];
ellipsoidPositiveDefinite =
  ellipsoidSymmetric && And @@ (# > 0 & /@ ellipsoidLeadingMinors);
ellipsoidSublevelTheorem = Resolve[
  ForAll[
    q0,
    Implies[
      q0 >= 0,
      Equivalent[Sqrt[q0] <= 1, q0 <= 1]
    ]
  ],
  Reals
];

(* The ordered H-polytope fixture is consumed directly from the contract. *)
polytopeFixture = fixtureById["POLYTOPE-FIXTURE"];
polytopeVector = parseExact /@ polytopeFixture["u"];
polytopeNormals =
  (parseExact /@ #) & /@ polytopeFixture["halfspace_normals"];
polytopeBounds =
  parseExact /@ polytopeFixture["halfspace_bounds"];
polytopeHalfspaces = MapThread[
  {#1, #2} &,
  {polytopeNormals, polytopeBounds}
];
polytopeRatios = MapThread[
  (#1.polytopeVector)/#2 &,
  {polytopeNormals, polytopeBounds}
];
polytopeRawGauge = Max @@ polytopeRatios;
polytopeGauge = Max[polytopeRawGauge, 0];
polytopeShapeOK = TrueQ[
  Length[polytopeNormals] == Length[polytopeBounds] &&
    And @@ (Length[#] == Length[polytopeVector] & /@ polytopeNormals)
];
polytopeNormalsNonzero =
  And @@ (#.# > 0 & /@ polytopeNormals);
polytopeSpanning =
  TrueQ[MatrixRank[polytopeNormals] == Length[polytopeVector]];
polytopePositiveBounds = And @@ (# > 0 & /@ polytopeBounds);
polytopeCentrallySymmetric = And @@ (
  MemberQ[polytopeHalfspaces, {-#[[1]], #[[2]]}] & /@
    polytopeHalfspaces
);
polytopeContainsOrigin = And @@ (# >= 0 & /@ polytopeBounds);

polytopeDotVariables = Table[
  Symbol["polytopeDot" <> ToString[index]],
  {index, Length[polytopeBounds]}
];
polytopeBoundVariables = Table[
  Symbol["polytopeBound" <> ToString[index]],
  {index, Length[polytopeBounds]}
];
polytopeSublevelTheorem = Resolve[
  ForAll[
    Evaluate[Join[polytopeDotVariables, polytopeBoundVariables]],
    Implies[
      And @@ (# > 0 & /@ polytopeBoundVariables),
      Equivalent[
        Max @@ MapThread[
          Divide,
          {polytopeDotVariables, polytopeBoundVariables}
        ] <= 1,
        And @@ MapThread[
          LessEqual,
          {polytopeDotVariables, polytopeBoundVariables}
        ]
      ]
    ]
  ],
  Reals
];

(* J1 and the one-way outer-envelope statement, sourced from the oracle. *)
j1 = oracle["j1_exact"];
physicalRadius = parseExact[j1["physical_radius"]];
anchorARadius = parseExact[j1["anchor_a_radius"]];
anchorBRadius = parseExact[j1["anchor_b_radius"]];
j1Probe = parseExact[j1["probe"]];
j1RhoA = Together[Abs[j1Probe]/anchorARadius];
j1RhoB = Together[Abs[j1Probe]/anchorBRadius];

oneWayA = Resolve[
  ForAll[
    x0,
    Implies[
      Abs[x0] <= physicalRadius,
      Abs[x0]/anchorARadius <= 1
    ]
  ],
  Reals
];
oneWayB = Resolve[
  ForAll[
    x0,
    Implies[
      Abs[x0] <= physicalRadius,
      Abs[x0]/anchorBRadius <= 1
    ]
  ],
  Reals
];
noConverseA = Resolve[
  Exists[
    x0,
    Abs[x0]/anchorARadius <= 1 &&
      Abs[x0] > physicalRadius
  ],
  Reals
];
noConverseB = Resolve[
  Exists[
    x0,
    Abs[x0]/anchorBRadius <= 1 &&
      Abs[x0] > physicalRadius
  ],
  Reals
];
oneWayViolationCount = Count[{oneWayA, oneWayB}, Except[True]];

(* Exact response-scaling fixture and a symbolic rank-strata proof. *)
rankFixture = fixtureById["RANK-FIXTURE"];
response = (parseExact /@ #) & /@ rankFixture["R"];
scaling = (parseExact /@ #) & /@ rankFixture["D"];
rankR = MatrixRank[response];
rankRD = MatrixRank[response.scaling];
detD = Together[Det[scaling]];

responseRows = Length[response];
responseColumns = Length[First[response]];
responseGeneral = Array[rr, {responseRows, responseColumns}];
scalingGeneral = Array[dd, {responseColumns, responseColumns}];
stateGeneral = Array[uu, responseColumns];
matrixAssumptions =
  Element[
    Flatten[{responseGeneral, scalingGeneral, stateGeneral}],
    Reals
  ] && Det[scalingGeneral] != 0;

rankRecoveryIdentity = FullSimplify[
  (responseGeneral.scalingGeneral).Inverse[scalingGeneral] ==
    responseGeneral,
  matrixAssumptions
];
rankMinorRowSets =
  Subsets[Range[responseRows], {responseColumns}];
rankTopMinorIdentities = And @@ Table[
  FullSimplify[
    Det[(responseGeneral.scalingGeneral)[[rows, All]]] ==
      Det[responseGeneral[[rows, All]]] Det[scalingGeneral],
    matrixAssumptions
  ],
  {rows, rankMinorRowSets}
];
transformedResponseIdentity = FullSimplify[
  responseGeneral.stateGeneral ==
    (responseGeneral.scalingGeneral).
      (Inverse[scalingGeneral].stateGeneral),
  matrixAssumptions
];
singularScaling = DiagonalMatrix[
  Join[ConstantArray[1, responseColumns - 1], {0}]
];
singularScalingNegativeControl = TrueQ[
  MatrixRank[response.singularScaling] < rankR
];

(* J2 dependence fixture, constructed from the sealed oracle marginals. *)
j2 = oracle["j2_exact"];
distributionAtoms[distribution_Association] := SortBy[
  KeyValueMap[
    {parseExact[#1], parseExact[#2]} &,
    distribution
  ],
  First
];
numeratorAtoms =
  distributionAtoms[j2["numerator_marginal"]];
anchorAtoms =
  distributionAtoms[j2["anchor_marginal"]];
j2CouplingFeasible = TrueQ[
  Length[numeratorAtoms] == Length[anchorAtoms] &&
    numeratorAtoms[[All, 2]] == anchorAtoms[[All, 2]] &&
    numeratorAtoms[[All, 2]] == Reverse[anchorAtoms][[All, 2]]
];
comonotoneLaw = MapThread[
  {#1[[1]], #2[[1]], #1[[2]]} &,
  {numeratorAtoms, anchorAtoms}
];
countermonotoneLaw = MapThread[
  {#1[[1]], #2[[1]], #1[[2]]} &,
  {numeratorAtoms, Reverse[anchorAtoms]}
];
marginalVector[law_List, column_Integer, support_List] := (
  Total[Pick[law[[All, 3]], law[[All, column]], #]] &
) /@ support;
exceedanceProbability[law_List] := Total[
  (If[#[[1]]/#[[2]] > 1, #[[3]], 0] &) /@ law
];

numeratorSupport = numeratorAtoms[[All, 1]];
anchorSupport = anchorAtoms[[All, 1]];
numeratorProbabilities = numeratorAtoms[[All, 2]];
anchorProbabilities = anchorAtoms[[All, 2]];
j2MarginalsPreserved = TrueQ[
  marginalVector[comonotoneLaw, 1, numeratorSupport] ==
      numeratorProbabilities &&
    marginalVector[countermonotoneLaw, 1, numeratorSupport] ==
      numeratorProbabilities &&
    marginalVector[comonotoneLaw, 2, anchorSupport] ==
      anchorProbabilities &&
    marginalVector[countermonotoneLaw, 2, anchorSupport] ==
      anchorProbabilities
];
j2ComonotoneExceedance =
  Together[exceedanceProbability[comonotoneLaw]];
j2CountermonotoneExceedance =
  Together[exceedanceProbability[countermonotoneLaw]];
j2ExpectedComonotone =
  parseExact[j2["comonotone_exceedance_probability"]];
j2ExpectedCountermonotone =
  parseExact[j2["countermonotone_exceedance_probability"]];
j2PositiveNumerators =
  And @@ (# > 0 & /@
    Join[comonotoneLaw[[All, 1]], countermonotoneLaw[[All, 1]]]);
j2PositiveAnchors =
  And @@ (# > 0 & /@
    Join[comonotoneLaw[[All, 2]], countermonotoneLaw[[All, 2]]]);
j2NormalizedLaws = TrueQ[
  Total[comonotoneLaw[[All, 3]]] == 1 &&
    Total[countermonotoneLaw[[All, 3]]] == 1
];

(* Assumption alignment is computed rather than asserted. *)
domainAssumptionDiff = {};
recordDiff[condition_, label_String] := If[
  ! TrueQ[condition],
  AppendTo[domainAssumptionDiff, label]
];
recordDiff[inputIntegrityOK, "required input hash mismatch"];
recordDiff[
  contract["identity"]["contract_id"] ===
    "CAS-PR254-ANCHOR-GEOMETRY-001",
  "contract identity mismatch"
];
recordDiff[
  And @@ (# > 0 & /@ productRadii),
  "product-ball radius is not strictly positive"
];
recordDiff[
  ellipsoidPositiveDefinite,
  "ellipsoid Q is not real symmetric positive definite"
];
recordDiff[
  polytopeShapeOK,
  "polytope normal/bound shape mismatch"
];
recordDiff[
  polytopePositiveBounds,
  "polytope bound is not strictly positive"
];
recordDiff[
  polytopeNormalsNonzero && polytopeSpanning,
  "polytope normals are zero or non-spanning"
];
recordDiff[
  polytopeCentrallySymmetric,
  "polytope lacks an exact same-bound antipodal halfspace"
];
recordDiff[
  polytopeContainsOrigin,
  "polytope does not contain the origin"
];
recordDiff[
  detD != 0,
  "anchor scaling D is singular"
];
recordDiff[
  physicalRadius > 0 &&
    anchorARadius >= physicalRadius &&
    anchorBRadius >= physicalRadius,
  "J1 outer-envelope radii are misaligned"
];
recordDiff[
  j2CouplingFeasible &&
    j2PositiveNumerators &&
    j2PositiveAnchors &&
    j2NormalizedLaws,
  "J2 positive uniform coupling assumptions are misaligned"
];
assumptionsAligned = TrueQ[domainAssumptionDiff === {}];

checks = <|
  "product_ball_max_ratio" -> TrueQ[
    assumptionsAligned &&
      productGauge == 5/2 &&
      productSublevelTheorem
  ],
  "ellipsoid_unit_sublevel" -> TrueQ[
    assumptionsAligned &&
      ellipsoidGaugeSq == 1 &&
      ellipsoidPositiveDefinite &&
      ellipsoidSublevelTheorem
  ],
  "polytope_unit_sublevel" -> TrueQ[
    assumptionsAligned &&
      polytopeGauge == 1/2 &&
      polytopeRawGauge >= 0 &&
      polytopeShapeOK &&
      polytopePositiveBounds &&
      polytopeNormalsNonzero &&
      polytopeSpanning &&
      polytopeCentrallySymmetric &&
      polytopeContainsOrigin &&
      polytopeSublevelTheorem
  ],
  "one_way_outer_envelope" -> TrueQ[
    assumptionsAligned &&
      oneWayA &&
      oneWayB &&
      noConverseA &&
      noConverseB &&
      oneWayViolationCount == 0
  ],
  "invertible_scaling_rank" -> TrueQ[
    assumptionsAligned &&
      rankR == rankRD &&
      detD != 0 &&
      rankRecoveryIdentity &&
      rankTopMinorIdentities &&
      singularScalingNegativeControl
  ],
  "transformed_response_identity" -> TrueQ[
    assumptionsAligned && transformedResponseIdentity
  ],
  "j1_counterexample" -> TrueQ[
    assumptionsAligned &&
      physicalRadius <= anchorARadius &&
      physicalRadius <= anchorBRadius &&
      physicalRadius != anchorARadius &&
      physicalRadius != anchorBRadius &&
      j1RhoA != j1RhoB &&
      j1RhoA == parseExact[j1["rho_a"]] &&
      j1RhoB == parseExact[j1["rho_b"]] &&
      j1["gate_outcome"] === "COUNTEREXAMPLE_FOUND" &&
      j1["disposition"] === "REFUTED_OR_RESTRICTED"
  ],
  "j2_dependence_counterexample" -> TrueQ[
    assumptionsAligned &&
      j2MarginalsPreserved &&
      j2ComonotoneExceedance == j2ExpectedComonotone &&
      j2CountermonotoneExceedance == j2ExpectedCountermonotone &&
      j2ComonotoneExceedance != j2CountermonotoneExceedance &&
      j2["gate_outcome"] === "COUNTEREXAMPLE_FOUND" &&
      j2["disposition"] === "REFUTED_OR_RESTRICTED"
  ]
|>;

computed = <|
  "product_gauge" -> ratString[productGauge],
  "ellipsoid_gauge_sq" -> ratString[ellipsoidGaugeSq],
  "polytope_gauge" -> ratString[polytopeGauge],
  "rank_R" -> ratString[rankR],
  "rank_RD" -> ratString[rankRD],
  "det_D" -> ratString[detD],
  "j1_rho_a" -> ratString[j1RhoA],
  "j1_rho_b" -> ratString[j1RhoB],
  "j2_comonotone_exceedance" -> ratString[j2ComonotoneExceedance],
  "j2_countermonotone_exceedance" ->
    ratString[j2CountermonotoneExceedance],
  "one_way_violation_count" -> ratString[oneWayViolationCount]
|>;

polytopeFixtureTrace = MapThread[
  <|
    "normal" -> vectorStrings[#1],
    "bound" -> ratString[#2],
    "dot_over_bound" -> ratString[(#1.polytopeVector)/#2]
  |> &,
  {polytopeNormals, polytopeBounds}
];

payload = <|
  "checks" -> checks,
  "domain_assumption_diff" -> domainAssumptionDiff,
  "computed" -> computed,
  "counterexample" -> Null,
  "tool_metadata" -> <|
    "engine" -> "wolfram_xact",
    "wolfram_version" -> System`$Version,
    "wolfram_version_number" ->
      ToString[System`$VersionNumber, InputForm],
    "wolfram_pinned_15_0_0" -> wolframPinnedOK,
    "xact_loaded" -> xactLoaded,
    "xact_xTensor_version" -> xactVersion,
    "xact_minimum_1_2_0" -> xactPinnedOK,
    "declared_dependencies" -> {"xAct`xTensor`"},
    "loaded_manifolds" -> {},
    "loaded_bundles" -> {},
    "loaded_metrics" -> {},
    "index_conventions" ->
      "none; exact scalar and finite real matrix algebra",
    "arithmetic" -> "exact integers and rationals",
    "numeric_precision_digits" ->
      contract["target"]["numeric_precision_digits"],
    "transformation_functions" -> {
      "Resolve",
      "FullSimplify",
      "Together",
      "MatrixRank",
      "Det",
      "Inverse"
    },
    "branch_changes" -> {}
  |>,
  "source_metadata" -> <|
    "contract_path" -> contractPath,
    "contract_sha256" -> contractHash,
    "spec_sha256" -> sourceHashes[specPath],
    "source_sha256" -> sourceHashes[sourcePath],
    "oracle_sha256" -> sourceHashes[oraclePath],
    "polytope_fixture_source" ->
      "target.numeric_test_vectors[id=POLYTOPE-FIXTURE]",
    "polytope_fixture_ordered_trace" -> polytopeFixtureTrace
  |>,
  "claim_boundary" -> <|
    "claim_ceiling" -> contract["identity"]["claim_ceiling"],
    "safe_scope" ->
      "conditional exact gauge, containment, scaling, and counterexample algebra",
    "forbidden_inference" ->
      "evidence, FLRW proximity, geometry detection, family identification, native solver status, or anchor uniqueness"
  |>,
  "authoring_correlation" ->
    "same Codex model family may author multiple axes; engine agreement is not derivation independence"
|>;

WriteString[
  $Output,
  ExportString[payload, "RawJSON", "Compact" -> True],
  "\n"
];
Exit[
  If[
    xactLoaded &&
      wolframPinnedOK &&
      xactPinnedOK &&
      assumptionsAligned &&
      And @@ Values[checks],
    0,
    2
  ]
];
