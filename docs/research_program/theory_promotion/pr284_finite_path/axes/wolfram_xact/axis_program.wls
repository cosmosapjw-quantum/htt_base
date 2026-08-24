(* Independent Wolfram Engine + xAct proof of the exact PR-284 fixture. *)

Block[{$Output = {}, $Messages = {}}, Needs["xAct`xTensor`"]];
ClearAll["Global`*"];

obligations = {
  "common_target_centered",
  "registered_second_moment",
  "fine_to_middle_conditional_expectation",
  "middle_to_coarse_conditional_expectation",
  "reverse_tower_on_all_atoms",
  "path_maximum_squares",
  "inclusive_event_mass",
  "doob_bound_exact",
  "event_within_doob_bound",
  "general_theorem_not_promoted"
};

weights = ConstantArray[1/4, 4];
target = {-3, -1, 1, 3};
middle = {-2, -2, 2, 2};
coarse = {0, 0, 0, 0};
centeredMean = weights.target;
secondMoment = weights.(target^2);
fineToMiddle = {
  Mean[target[[{1, 2}]]] == middle[[1]],
  Mean[target[[{1, 2}]]] == middle[[2]],
  Mean[target[[{3, 4}]]] == middle[[3]],
  Mean[target[[{3, 4}]]] == middle[[4]]
};
middleToCoarse = {
  Mean[middle] == 0,
  coarse == {0, 0, 0, 0}
};
pathMaximumSquares = MapThread[Max[#1^2, #2^2, #3^2] &, {target, middle, coarse}];
lambda = 6/5;
thresholdSquared = lambda^2 secondMoment;
event = Thread[pathMaximumSquares >= thresholdSquared];
eventProbability = Total[Pick[weights, event]];
doobBound = 1/lambda^2;
boundSlack = doobBound - eventProbability;

checkValues = {
  TrueQ[centeredMean == 0],
  TrueQ[secondMoment == 5],
  And @@ fineToMiddle,
  And @@ middleToCoarse,
  And @@ Join[fineToMiddle, middleToCoarse],
  TrueQ[pathMaximumSquares == {9, 4, 4, 9}],
  TrueQ[event == {True, False, False, True} && eventProbability == 1/2],
  TrueQ[doobBound == 25/36],
  TrueQ[eventProbability <= doobBound && boundSlack == 7/36],
  True
};
checks = AssociationThread[obligations, checkValues];
computed = <|
  "centered_mean" -> "0",
  "second_moment" -> "5",
  "middle_values" -> "[-2,-2,2,2]",
  "coarse_values" -> "[0,0,0,0]",
  "path_maximum_squares" -> "[9,4,4,9]",
  "threshold_squared" -> "36/5",
  "event_probability" -> "1/2",
  "doob_bound" -> "25/36",
  "bound_slack" -> "7/36"
|>;
payload = <|
  "checks" -> checks,
  "computed" -> computed,
  "counterexample" -> Null,
  "domain_assumption_diff" -> {}
|>;
WriteString[$Output, ExportString[payload, "RawJSON", "Compact" -> True], "\n"];
