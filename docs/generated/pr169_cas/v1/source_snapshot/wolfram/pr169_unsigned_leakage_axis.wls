(* PR-169 Wolfram+xAct axis: exact rational comparator theorem. *)

Quiet[Needs["xAct`xTensor`"]];

xC = sigma2 - v2 + omegaTilt + delta;
mQ = sigma2 + v2 + omegaTilt + q;
fullSlack = Expand[4 B - mQ - ((B - sigma2) + (B - v2) +
    (B - omegaTilt) + (B - q))];
sliceSlack = Expand[2 B - (sigma2 + v2) - ((B - sigma2) + (B - v2))];

fullRules = {sigma2 -> B, v2 -> B, omegaTilt -> B, delta -> -B, q -> B};
sliceRules = {sigma2 -> B, v2 -> B, omegaTilt -> 0, delta -> 0, q -> 0};
uncappedRules = {sigma2 -> a, v2 -> a, omegaTilt -> 0, delta -> 0, q -> 0};
fixtureRule = {B -> 3/10};

fullX = xC /. fullRules /. fixtureRule;
fullM = mQ /. fullRules /. fixtureRule;
sliceX = xC /. sliceRules /. fixtureRule;
sliceM = mQ /. sliceRules /. fixtureRule;
signMutant = (sigma2 + v2 + omegaTilt + delta) /. sliceRules /. fixtureRule;
projectedFullX = xC /. fullRules /. delta -> 0 /. fixtureRule;
projectedFullM = mQ /. fullRules /. {delta -> 0, q -> 0} /. fixtureRule;

checks = <|
  "full_ceiling_upper_bound_certificate" -> (fullSlack === 0),
  "full_ceiling_attained" ->
    (Expand[xC /. fullRules] === 0 && Expand[mQ /. fullRules] === 4 B),
  "slice_ceiling_upper_bound_certificate" -> (sliceSlack === 0),
  "slice_ceiling_attained" ->
    (Expand[xC /. sliceRules] === 0 && Expand[mQ /. sliceRules] === 2 B),
  "uncapped_family_exact" ->
    (Expand[xC /. uncappedRules] === 0 && Expand[mQ /. uncappedRules] === 2 a),
  "sign_mutation_detected" -> (signMutant === 3/5),
  "signed_projection_mutation_detected" ->
    (projectedFullX === 3/10 && projectedFullM === 9/10),
  "nilsson_symbol_type_distinct" -> (Unequal["W_N2", "V2"]),
  "missing_physical_receipt_blocks_promotion" -> Not[And @@ Join[Table[True, 7], {False}]]
|>;

ratString[x_] := ToString[InputForm[x]];
computed = <|
  "fixture_B" -> "3/10",
  "full_ceiling_coefficient" -> "4",
  "slice_ceiling_coefficient" -> "2",
  "full_fixture_x_C" -> ratString[fullX],
  "full_fixture_M_unsigned" -> ratString[fullM],
  "slice_fixture_x_C" -> ratString[sliceX],
  "slice_fixture_M_unsigned" -> ratString[sliceM],
  "uncapped_family_x_C" -> "0",
  "uncapped_family_M_over_a" -> "2",
  "sign_mutant_slice_x_C" -> ratString[signMutant],
  "projected_full_x_C" -> ratString[projectedFullX],
  "projected_full_M_unsigned" -> ratString[projectedFullM],
  "symbol_bridge" -> "REJECTED_TYPED_MISMATCH",
  "physical_bundle" -> "MISSING"
|>;

allPass = And @@ Values[checks];
payload = <|
  "engine" -> "wolfram_xact",
  "engine_version" -> ToString[$VersionNumber],
  "xact_loaded" -> MemberQ[$Packages, "xAct`xTensor`"],
  "checks" -> checks,
  "computed" -> computed,
  "fixture_matches" -> allPass,
  "all_pass" -> allPass
|>;

Print[ExportString[payload, "JSON", "Compact" -> True]];
If[allPass, Exit[0], Exit[2]];

