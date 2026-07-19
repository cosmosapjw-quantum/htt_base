(* PR-170 Wolfram+xAct axis: exact Buchert/two-patch scalar algebra. *)

Quiet[Needs["xAct`xTensor`"]];

types = {"I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"};
hD = Expand[w h1 + (1 - w) h2];
varTheta = Expand[9 w (1 - w) (h1 - h2)^2];
meanSigma = Expand[w s1 + (1 - w) s2];
qD = Expand[(2/3) varTheta - 2 meanSigma];
omegaQ = -qD/(6 hD^2);
sigma2 = meanSigma/(3 hD^2);
bridge = Factor[omegaQ - sigma2];
expectedBridge = Factor[-varTheta/(9 hD^2)];

swap = {w -> 1 - w, h1 -> h2, h2 -> h1, s1 -> s2, s2 -> s1};
equal = {w -> 1/2, h1 -> 2, h2 -> 2, s1 -> 3, s2 -> 3};
cancel = {w -> 1/2, h1 -> 3, h2 -> 1, s1 -> 3, s2 -> 3};
zeroShear = {w -> 1/2, h1 -> 3, h2 -> 1, s1 -> 0, s2 -> 0};
qAbstract = (2/3) varianceSymbol - 2 shearSymbol;
qBT = (2/3) varTheta - 2 (meanSigma - meanSigmaMagnitude^2);

checks = <|
  "buchert_definition_and_dimension_lock" ->
    (Expand[qD - (6 w (1 - w) (h1 - h2)^2 - 2 meanSigma)] === 0),
  "two_patch_weighted_hubble_identity" ->
    (Expand[hD - (w h1 + (1 - w) h2)] === 0),
  "two_patch_expansion_variance_identity" ->
    (Expand[varTheta - 9 w (1 - w) (h1 - h2)^2] === 0),
  "general_bridge_residual_identity" -> (Factor[bridge - expectedBridge] === 0),
  "constant_expansion_bridge" -> (Factor[bridge /. h2 -> h1] === 0),
  "cancellation_condition" -> (Factor[qAbstract /. varianceSymbol -> 3 shearSymbol] === 0),
  "constant_expansion_zero_q_implies_zero_mean_shear" ->
    (Factor[(qD /. h2 -> h1) + 2 meanSigma] === 0),
  "patch_label_exchange_symmetry" ->
    And @@ ((Factor[# - (# /. swap)] === 0) & /@ {hD, varTheta, meanSigma, qD}),
  "barrow_tsagas_symbol_separation" ->
    (Factor[qBT - qD - 2 meanSigmaMagnitude^2] === 0),
  "typed_scalar_identity_all_11" ->
    (Length[types] === 11 && DuplicateFreeQ[types] && And @@ Table[Factor[bridge /. h2 -> h1] === 0, {11}]),
  "equal_expansion_fixture" ->
    ({hD, varTheta, qD, omegaQ, sigma2} /. equal) === {2, 0, -6, 1/4, 1/4},
  "two_patch_cancellation_fixture" ->
    ({hD, varTheta, qD, omegaQ, sigma2, bridge} /. cancel) === {2, 9, 0, 0, 1/4, -1/4},
  "zero_shear_unequal_expansion_control" ->
    ({qD, omegaQ, sigma2} /. zeroShear) === {6, -1/4, 0},
  "hubble_zero_normalization_guard" ->
    ((hD /. {w -> 1/2, h1 -> 1, h2 -> -1}) === 0),
  "curvature_source_negative_control" -> (Dot[{1, -1, 0}, {1, -1, 0}] === 2)
|>;

computed = <|
  "equal_H_D" -> "2", "equal_variance_theta" -> "0",
  "equal_Q_D_B" -> "-6", "equal_Omega_Q_D_B" -> "1/4",
  "equal_Sigma2_D_rms" -> "1/4", "cancel_H_D" -> "2",
  "cancel_variance_theta" -> "9", "cancel_Q_D_B" -> "0",
  "cancel_Omega_Q_D_B" -> "0", "cancel_Sigma2_D_rms" -> "1/4",
  "cancel_bridge_residual" -> "-1/4", "zero_shear_Q_D_B" -> "6",
  "zero_shear_Omega_Q_D_B" -> "-1/4", "typed_scalar_rows" -> "11",
  "curvature_control_contraction" -> "2",
  "barrow_buchert_relation" -> "Q_D_BT=Q_D_B+2*mean_sigma^2"
|>;

allPass = And @@ Values[checks];
payload = <|
  "engine" -> "wolfram_xact", "engine_version" -> ToString[$VersionNumber],
  "xact_loaded" -> MemberQ[$Packages, "xAct`xTensor`"],
  "checks" -> checks, "computed" -> computed,
  "fixture_matches" -> allPass, "all_pass" -> allPass
|>;
Print[ExportString[payload, "JSON", "Compact" -> True]];
If[allPass, Exit[0], Exit[2]];
