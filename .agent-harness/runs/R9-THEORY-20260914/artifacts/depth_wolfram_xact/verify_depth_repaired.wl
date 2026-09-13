(* R9 Wolfram/xAct depth runner.  The earlier verify_depth.wl is retained as
   raw failed source.  This runner emits exactly one RawJSON object. *)
ClearAll["Global`*"];

prop = If[Length[$CommandLine] >= 2, Last[$CommandLine], ""];

checks = Switch[prop,
  "D1", Association[
    "D1_MEAN_COVARIANCE_LINEAR_MAP" -> False,
    "D1_ALL_CROSS_STEP_BLOCKS" -> False,
    "D1_PSD_PULLBACK_GENERAL_DIMENSION" -> False],
  "D3", Association[
    "D3_RECURSION_BOTH_INVERSES_ARBITRARY_BLOCKS" -> False,
    "D3_KERNEL_SURJECTIVITY_DETERMINANT" -> False,
    "D3_FULL_LAW_SUPPORT_PRESERVED" -> False],
  "D2", Association[
    "D2_GAUSSIAN_PUSHFORWARD_SUPPORT" -> False,
    "D2_SUPPORTED_PSEUDOINVERSE_CHISQUARE" -> False,
    "D2_RANK_ZERO_AND_OFF_SUPPORT" -> False],
  "D4", Association[
    "D4_PSD_RANGE_SCHUR_SUPPORT" -> False,
    "D4_FULL_PAST_CONDITIONAL_GAUSSIAN" -> False,
    "D4_INNOVATION_INDEPENDENCE_AND_FIXED_LAW_LIMIT" -> False],
  _, Association[]
];

scope = Switch[prop,
  "D1", "An exact rational d=(2,3,1) algebraic fixture is computed only; no universal finite-block or finite-second-moment proof is supplied.",
  "D3", "An exact rational d=(2,3,1) block-triangular fixture is computed only; no arbitrary-block inverse, kernel, or support theorem is supplied.",
  "D2", "A singular covariance rank fixture is computed only; no Gaussian pushforward, support, or chi-square distribution theorem is supplied.",
  "D4", "A singular past-covariance rank fixture is computed only; no conditional-Gaussian or innovation-independence theorem is supplied.",
  _, "Unknown proposition ID."
];

(* Exact finite fixture, deliberately not used to turn any contract check true. *)
kzero = {{1, 2}, {0, 1}, {2, -1}};
kone = {{1, -2, 3}};
hmat = ArrayFlatten[{{-kzero, IdentityMatrix[3], ConstantArray[0, {3, 1}]},
  {ConstantArray[0, {1, 2}], -kone, IdentityMatrix[1]}}];
lmat = {{1, 0, 1, 0, 0}, {0, 1, 1, 0, 0}, {1, 1, 0, 1, 0},
  {2, 0, 1, 1, 0}, {0, 1, 2, 1, 0}, {1, -1, 0, 2, 1}};
cmat = lmat.Transpose[lmat];
vmat = hmat.cmat.Transpose[hmat];
fixture = {"d=(2,3,1)", "rank(C)", MatrixRank[cmat], "rank(H C H^T)", MatrixRank[vmat]};

payload = Association["checks" -> checks, "domain_assumption_diff" -> {},
  "counterexample" -> Null, "proof_scope" -> scope];

AssociateTo[payload, "computed" -> fixture];
AssociateTo[payload, "engine" -> $Version];
AssociateTo[payload, "xact_loaded" -> "separate one-shot probe recorded in raw/toolchain_probe.combined.log"];
AssociateTo[payload, "xact_version" -> "1.3.0"];
AssociateTo[payload, "proposition" -> prop];
WriteString[$Output, ExportString[payload, "RawJSON"], "\n"];
Quit[0];
