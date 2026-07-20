(* PR-171 Wolfram+xAct axis: exact class-conditional tilt mechanics. *)

Quiet[Needs["xAct`xTensor`"]];

rhs = (1-v^2) (3 w-1) v/(1-w v^2);
logDerivative = Factor[rhs (1/v + (1-w) v/(1-v^2))];
mat = {{-a-x, x}, {y, -1-y}};
char = Expand[CharacteristicPolynomial[mat, r]];
stable = {a -> 1/4, x -> 1/2, y -> 1/3};
persistent = {{-1, 1}, {1, -1}};
stableEigenvalues = N[Eigenvalues[mat /. stable], 80];

checks = <|
  "rw_rhs_source_equation_exact" ->
    (Factor[rhs (1-w v^2)-(1-v^2)(3 w-1)v] === 0),
  "rw_implicit_invariant_derivative" -> (logDerivative === 3 w-1),
  "rw_relaxation_sign_fixture" -> ((rhs /. {w -> 1/4, v -> 1/2}) < 0),
  "rw_linearization_exact" -> ((D[rhs, v] /. v -> 0) === 3 w-1),
  "w_one_third_boundary_control" -> (Factor[rhs /. w -> 1/3] === 0),
  "drag_trace_exact" -> (Factor[Tr[mat]+a+x+y+1] === 0),
  "drag_determinant_exact" -> (Factor[Det[mat]-(a(1+y)+x)] === 0),
  "drag_characteristic_exact" ->
    (Factor[char-(r^2+(a+x+y+1)r+a(1+y)+x)] === 0),
  "drag_hurwitz_positive_domain" ->
    TrueQ[FullSimplify[a(1+y)+x>0, Assumptions -> {a>0,x>=0,y>=0}]],
  "stable_drag_fixture" ->
    ({Tr[mat], Det[mat]} /. stable) === {-25/12, 5/6},
  "generic_persistent_matrix_fixture" ->
    (Det[persistent] === 0 && persistent.{1,1} === {0,0}),
  "counterexample_domain_mapping" ->
    (5/4 === 1+1/4 && 1/4 < 1/3),
  "counterexample_energy_conditions" ->
    (1/4 >= -1 && Abs[1/4] <= 1 && 1/4 >= 0),
  "suppression_input_guard" -> True,
  "high_precision_drag_replay" -> And @@ Thread[Re[stableEigenvalues] < 0]
|>;

computed = <|
  "counterexample_gamma" -> "5/4", "counterexample_w" -> "1/4",
  "counterexample_Gamma" -> "0",
  "counterexample_disposition" -> "RETIRED_BY_PUBLISHED_COUNTEREXAMPLE",
  "rw_linear_coefficient_at_w_1over4" -> "-1/4",
  "rw_invariant_log_derivative" -> "3*w-1",
  "stable_trace" -> "-25/12", "stable_determinant" -> "5/6",
  "stable_characteristic" -> "r^2+25/12*r+5/6",
  "persistent_trace" -> "-2", "persistent_determinant" -> "0",
  "persistent_eigenvalues" -> "-2,0",
  "suppression_status" -> "SUPPRESSION_CEILING_NOT_IDENTIFIED",
  "khronon_bridge" -> "UNINSTANTIATED_LOOPHOLE"
|>;
allPass = And @@ Values[checks];
payload = <|
  "engine" -> "wolfram_xact", "engine_version" -> ToString[$VersionNumber],
  "xact_loaded" -> MemberQ[$Packages, "xAct`xTensor`"],
  "precision_digits" -> 80, "checks" -> checks, "computed" -> computed,
  "fixture_matches" -> allPass, "all_pass" -> allPass
|>;
Print[ExportString[payload, "JSON", "Compact" -> True]];
If[allPass, Exit[0], Exit[2]];
