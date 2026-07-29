#!/usr/bin/env wolframscript

(* Independent Wolfram Language + xAct axis for CAS-PR257-ORBIT-CATALOGUE-V2-001. *)
ClearAll["Global`*"];

(* xAct is a required toolchain witness; its startup banner is suppressed so the
   program emits exactly one JSON object on stdout. *)
Block[{$Output = {}}, Needs["xAct`xTensor`"]];

contractPath =
  "docs/generated/pr257_lowell_morphology/CAS_CONTRACT_PR257_ORBIT_V2.json";
contractSha256 =
  "1d3e0c76a3833dd72cb5e74dcd3ddedfe91a538902950df603587e77ad6c0e56";
contract = Import[contractPath, "RawJSON"];
contractId = contract["identity"]["contract_id"];
obligationNames = contract["target"]["exact_test_obligations"];

(* A unit quaternion parametrizes every SO(3) element.  Every improper O(3)
   element is -Q for some Q in SO(3), so the two branches below cover O(3). *)
qvars = {q0, q1, q2, q3};
qnorm = q0^2 + q1^2 + q2^2 + q3^2;
qRotation = {
  {q0^2 + q1^2 - q2^2 - q3^2, 2 (q1 q2 - q0 q3),
   2 (q1 q3 + q0 q2)},
  {2 (q1 q2 + q0 q3), q0^2 - q1^2 + q2^2 - q3^2,
   2 (q2 q3 - q0 q1)},
  {2 (q1 q3 - q0 q2), 2 (q2 q3 + q0 q1),
   q0^2 - q1^2 - q2^2 + q3^2}
  };
rProper = qRotation;
rImproper = -qRotation;

sigma = {
  {s11, s12, s13},
  {s12, s22, s23},
  {s13, s23, -s11 - s22}
  };
beta = {b1, b2, b3};
omega = {w1, w2, w3};
proofVars = Join[
   qvars,
   {s11, s22, s12, s13, s23},
   {b1, b2, b3},
   {w1, w2, w3}
   ];

quotientZeroQ[expression_] := Module[{remainder},
  remainder = Last[
    PolynomialReduce[Expand[expression], {qnorm - 1}, proofVars]
    ];
  TrueQ[Expand[remainder] === 0]
  ];

matrixQuotientZeroQ[matrix_] :=
  And @@ (quotientZeroQ /@ Flatten[matrix]);

catalogue[s_, b_, w_] := <|
  "tr_sigma2" -> Tr[MatrixPower[s, 2]],
  "tr_sigma3" -> Tr[MatrixPower[s, 3]],
  "beta2" -> b . b,
  "beta_sigma_beta" -> b . s . b,
  "beta_sigma2_beta" -> b . MatrixPower[s, 2] . b,
  "det_beta_sigma_beta_sigma2_beta" ->
    Det[Transpose[{b, s . b, MatrixPower[s, 2] . b}]],
  "omega2" -> w . w,
  "omega_sigma_omega" -> w . s . w,
  "omega_sigma2_omega" -> w . MatrixPower[s, 2] . w,
  "beta_dot_omega" -> b . w,
  "beta_sigma_omega" -> b . s . w,
  "beta_sigma2_omega" -> b . MatrixPower[s, 2] . w
  |>;

transformState[r_, s_, b_, w_] := Module[{detR = Det[r]},
  {
   Expand[r . s . Transpose[r]],
   Expand[r . b],
   Expand[detR r . w]
   }
  ];

evenNames = {
  "tr_sigma2", "tr_sigma3", "beta2", "beta_sigma_beta",
  "beta_sigma2_beta", "omega2", "omega_sigma_omega",
  "omega_sigma2_omega"
  };
oddNames = {
  "det_beta_sigma_beta_sigma2_beta", "beta_dot_omega",
  "beta_sigma_omega", "beta_sigma2_omega"
  };
baseCatalogue = catalogue[sigma, beta, omega];
allNames = Keys[baseCatalogue];

properState = transformState[rProper, sigma, beta, omega];
improperState = transformState[rImproper, sigma, beta, omega];
properCatalogue = catalogue @@ properState;
improperCatalogue = catalogue @@ improperState;

properParityChecks = AssociationMap[
   quotientZeroQ[properCatalogue[#] - baseCatalogue[#]] &,
   allNames
   ];
improperParityChecks = AssociationMap[
   quotientZeroQ[
     improperCatalogue[#] -
      If[MemberQ[evenNames, #], baseCatalogue[#], -baseCatalogue[#]]
     ] &,
   allNames
   ];
o3BranchChecks = <|
  "proper_orthogonal" ->
    matrixQuotientZeroQ[Transpose[rProper] . rProper - IdentityMatrix[3]],
  "proper_determinant_plus_one" ->
    quotientZeroQ[Det[rProper] - 1],
  "improper_orthogonal" ->
    matrixQuotientZeroQ[
      Transpose[rImproper] . rImproper - IdentityMatrix[3]],
  "improper_determinant_minus_one" ->
    quotientZeroQ[Det[rImproper] + 1]
  |>;
scalarPseudoscalarO3Q =
  And @@ Values[o3BranchChecks] &&
   And @@ Values[properParityChecks] &&
   And @@ Values[improperParityChecks] &&
   Sort[Join[evenNames, oddNames]] === Sort[allNames];

(* Exact trace-free 3x3 Cayley-Hamilton identity and its contractions. *)
chResidual = Expand[
   MatrixPower[sigma, 3] -
    Tr[MatrixPower[sigma, 2]] sigma/2 -
    Tr[MatrixPower[sigma, 3]] IdentityMatrix[3]/3
   ];
cayleyHamiltonQ = And @@ (TrueQ[# === 0] & /@ Flatten[chResidual]);
contractionResiduals = Expand /@ {
    beta . chResidual . beta,
    omega . chResidual . omega,
    beta . chResidual . omega
    };
cayleyHamiltonContractionsQ =
  And @@ (TrueQ[# === 0] & /@ contractionResiduals);

(* det(K)^2 = det(K^T K), with K = [beta, sigma beta, sigma^2 beta]. *)
kBeta = Transpose[
   {beta, sigma . beta, MatrixPower[sigma, 2] . beta}
   ];
gramResidual = Expand[
   Det[kBeta]^2 - Det[Transpose[kBeta] . kBeta]
   ];
gramSyzygyQ = TrueQ[gramResidual === 0];

(* Fixed exact-integer witness. *)
sigma0 = DiagonalMatrix[{1, 2, -3}];
beta0 = {1, 1, 1};
omega0 = {1, 2, 3};
fixedCatalogue = catalogue[sigma0, beta0, omega0];
kBeta0 = Transpose[
   {beta0, sigma0 . beta0, MatrixPower[sigma0, 2] . beta0}
   ];
computedValues = Join[
   fixedCatalogue,
   <|
    "beta_sigma3_beta" ->
      beta0 . MatrixPower[sigma0, 3] . beta0,
    "omega_sigma3_omega" ->
      omega0 . MatrixPower[sigma0, 3] . omega0,
    "beta_sigma3_omega" ->
      beta0 . MatrixPower[sigma0, 3] . omega0,
    "beta_krylov_gram_determinant" ->
      Det[Transpose[kBeta0] . kBeta0]
    |>
   ];
computedValueStrings = AssociationMap[
   ToString[computedValues[#], InputForm] &,
   Keys[computedValues]
   ];
expectedValueStrings = contract["target"]["expected_exact_values"];
fixedValuesQ = computedValueStrings === expectedValueStrings;

(* Registered beta=0, omega versus -omega non-separation witness. *)
zeroBeta = {0, 0, 0};
omegaLeft = {1, 2, 3};
omegaRight = {-1, -2, -3};
leftValues = catalogue[sigma0, zeroBeta, omegaLeft];
rightValues = catalogue[sigma0, zeroBeta, omegaRight];
nongenericWitnessQ =
  leftValues === rightValues &&
   omegaLeft =!= omegaRight;

genericSeparationStatus = "UNPROVEN";
completenessStatus = "UNPROVEN";

checks = <|
  "scalar_pseudoscalar_o3" -> scalarPseudoscalarO3Q,
  "cayley_hamilton_tracefree_3x3" -> cayleyHamiltonQ,
  "cayley_hamilton_vector_contractions" ->
    cayleyHamiltonContractionsQ,
  "beta_krylov_gram_syzygy" -> gramSyzygyQ,
  "fixed_rational_values" -> fixedValuesQ,
  "nongeneric_nonseparation_witness" -> nongenericWitnessQ,
  "generic_separation_not_promoted" ->
    TrueQ[genericSeparationStatus === "UNPROVEN"],
  "completeness_not_promoted" ->
    TrueQ[completenessStatus === "UNPROVEN"]
  |>;

obligationCoverageQ =
  Sort[Keys[checks]] === Sort[obligationNames];
allPassQ = obligationCoverageQ && And @@ Values[checks];

completedAt = DateString[
   Now,
   {"Year", "-", "Month", "-", "Day", "T", "Hour", ":", "Minute", ":",
    "Second", "Z"},
   TimeZone -> 0
   ];

payload = <|
  "schema_version" -> 1,
  "axis" -> "wolfram_xact",
  "contract_id" -> contractId,
  "contract_sha256" -> contractSha256,
  "status" -> If[allPassQ, "PASS", "FAIL"],
  "commands" -> {
    <|
     "cmd" ->
      "wolframscript -file docs/generated/pr257_lowell_morphology/axes/wolfram_xact/axis_program.wls",
     "exit" -> If[allPassQ, 0, 1]
     |>
    },
  "tool_versions" -> <|
    "wolfram" -> System`$Version,
    "wolframscript" -> "1.14.0",
    "xact_xTensor" ->
      First[xAct`xTensor`$Version],
    "xact_xPerm" ->
      First[xAct`xPerm`$Version]
    |>,
  "source_output_hashes" -> {},
  "domain_assumption_diff" -> {},
  "evidence_class" -> "exact",
  "counterexample" ->
    If[allPassQ, Null, <|
      "failed_checks" -> Keys[Select[checks, Not[TrueQ[#]] &]],
      "obligation_coverage" -> obligationCoverageQ
      |>],
  "completed_at" -> completedAt,
  "checks" -> checks,
  "computed" -> computedValueStrings,
  "proof_details" -> <|
    "o3_coverage" ->
      "unit-quaternion SO(3) parametrization plus -Q improper branch",
    "proper_branch_checks" -> o3BranchChecks,
    "proper_parity_checks" -> properParityChecks,
    "improper_parity_checks" -> improperParityChecks,
    "generic_orbit_separation_status" -> genericSeparationStatus,
    "degree_completeness_status" -> completenessStatus,
    "nongeneric_left_values" ->
      AssociationMap[ToString[leftValues[#], InputForm] &, Keys[leftValues]],
    "nongeneric_right_values" ->
      AssociationMap[ToString[rightValues[#], InputForm] &, Keys[rightValues]]
    |>,
  "correlation_disclosure" ->
    "This axis was authored by a GPT-5.6-family agent; engine agreement is not derivation independence."
  |>;

WriteString[$Output, ExportString[payload, "RawJSON"], "\n"];
Exit[If[allPassQ, 0, 1]];
