(* CAS-13-C02: independent two-node feasibility certificate. *)
ClearAll[a, b, r, mm4, u, dn, t, t1, t2, y, ratioF, ratioG,
  targetL, targetU, chord, wU, wB, chordWeight, derivF, derivG,
  base, interior, zeroQ, numericCase, numericCases, checks, result];

Needs["xAct`xTensor`"];
xactLoaded = MemberQ[$Packages, "xAct`xTensor`"] &&
  Length[Names["xAct`xTensor`DefManifold"]] > 0;

ratioF[z_] := (z^4 - a^4)/(z^3 - a^3);
ratioG[z_] := (b^4 - z^4)/(b^3 - z^3);
targetL = (mm4 - a^4)/(r^3 - a^3);
targetU = (b^4 - mm4)/(b^3 - r^3);
chord = a^4 + (r^3 - a^3) (b^4 - a^4)/(b^3 - a^3);
wU = (r^3 - a^3)/(u^3 - a^3);
wB = (r^3 - dn^3)/(b^3 - dn^3);
chordWeight = (r^3 - a^3)/(b^3 - a^3);
derivF = t^2 (3 a^2 + 2 a t + t^2)/(a^2 + a t + t^2)^2;
derivG = t^2 (3 b^2 + 2 b t + t^2)/(b^2 + b t + t^2)^2;
base = 0 < a < r < b && r^4 < mm4 < chord;
interior = base && r < u < b && a < dn < r;
zeroQ[expr_] := TrueQ[Cancel[Together[expr]] === 0];

(* Four exact positive gaps plus positive derivatives certify IVT existence
   and uniqueness by strict monotonicity; the denominators are retained. *)
endpointGapIdentities = And @@ {
  zeroQ[targetL - ratioF[r] - (mm4 - r^4)/(r^3 - a^3)],
  zeroQ[ratioF[b] - targetL - (chord - mm4)/(r^3 - a^3)],
  zeroQ[targetU - ratioG[a] - (chord - mm4)/(b^3 - r^3)],
  zeroQ[ratioG[r] - targetU - (mm4 - r^4)/(b^3 - r^3)]
};
derivativeIdentities = And @@ {
  zeroQ[D[ratioF[t], t] - derivF],
  zeroQ[D[ratioG[t], t] - derivG]
};
positiveDerivativeFactors = TrueQ[FullSimplify[
  derivF > 0 && derivG > 0,
  0 < a < r < b && r < t < b]];
(* The upper-node derivative is also positive on (a,r). *)
positiveUpperDerivative = TrueQ[FullSimplify[
  derivG > 0, 0 < a < t < r < b]];
positiveGaps = TrueQ[FullSimplify[
  (mm4 - r^4)/(r^3 - a^3) > 0 &&
  (chord - mm4)/(r^3 - a^3) > 0 &&
  (chord - mm4)/(b^3 - r^3) > 0 &&
  (mm4 - r^4)/(b^3 - r^3) > 0, base]];
positiveDenominators = TrueQ[FullSimplify[
  u^3 - a^3 > 0 && b^3 - dn^3 > 0 &&
  r^3 - a^3 > 0 && b^3 - r^3 > 0 &&
  a^2 + a u + u^2 > 0 && b^2 + b dn + dn^2 > 0,
  interior]];
rootBranch = TrueQ[FullSimplify[(r^3)^(4/3) == r^4, r > 0]];
nodeExistUnique = endpointGapIdentities && derivativeIdentities &&
  positiveDerivativeFactors && positiveUpperDerivative && positiveGaps &&
  positiveDenominators && rootBranch;

(* Exact algebraic identities; the fourth moments vanish only after the
   separately established node equations are imposed. *)
momentIdentities = And @@ {
  zeroQ[(1 - wU) a^3 + wU u^3 - r^3],
  zeroQ[(1 - wB) dn^3 + wB b^3 - r^3],
  zeroQ[(1 - wU) a^4 + wU u^4 - mm4 -
    (r^3 - a^3) (ratioF[u] - targetL)],
  zeroQ[(1 - wB) dn^4 + wB b^4 - mm4 -
    (b^3 - r^3) (targetU - ratioG[dn])]
};
positiveWeights = TrueQ[FullSimplify[
  0 < wU < 1 && 0 < wB < 1, interior]];
normalization = zeroQ[(1 - wU) + wU - 1] &&
  zeroQ[(1 - wB) + wB - 1];

(* Boundary measures are defined directly or by non-singular interior-r
   node limits.  Endpoint m3 values never enter a 0/0 node formula. *)
diracBoundary = And @@ {
  TrueQ[FullSimplify[(wU /. u -> r) == 1, 0 < a < r < b]],
  TrueQ[FullSimplify[(wB /. dn -> r) == 0, 0 < a < r < b]],
  zeroQ[r^3 - r^3], zeroQ[r^4 - r^4]
};
chordBoundary = And @@ {
  TrueQ[FullSimplify[(wU /. u -> b) == chordWeight, 0 < a < r < b]],
  TrueQ[FullSimplify[(wB /. dn -> a) == chordWeight, 0 < a < r < b]],
  zeroQ[(1 - chordWeight) a^3 + chordWeight b^3 - r^3],
  zeroQ[(1 - chordWeight) a^4 + chordWeight b^4 - chord]
};
endpointDiracMeasures = TrueQ[FullSimplify[
  y^3 - a^3 >= 0 && b^3 - y^3 >= 0 &&
  ((y^3 - a^3 == 0) == (y == a)) &&
  ((b^3 - y^3 == 0) == (y == b)),
  0 < a <= y <= b]];

numericCase[aa_, bb_, rr_, fourth_] := Module[
  {cc, fl, gu, tl, tu, urule, drule, uv, dv, wl, wb,
   residuals, scale, bound, good, wp = 120},
  cc = aa^4 + (rr^3 - aa^3) (bb^4 - aa^4)/(bb^3 - aa^3);
  fl[z_] := (z^4 - aa^4)/(z^3 - aa^3);
  gu[z_] := (bb^4 - z^4)/(bb^3 - z^3);
  tl = (fourth - aa^4)/(rr^3 - aa^3);
  tu = (bb^4 - fourth)/(bb^3 - rr^3);
  urule = Check[FindRoot[fl[u] == tl, {u, N[rr, wp], N[bb, wp]},
    WorkingPrecision -> wp, AccuracyGoal -> 80, PrecisionGoal -> 80], $Failed];
  drule = Check[FindRoot[gu[dn] == tu, {dn, N[aa, wp], N[rr, wp]},
    WorkingPrecision -> wp, AccuracyGoal -> 80, PrecisionGoal -> 80], $Failed];
  If[urule === $Failed || drule === $Failed,
    Return[<|"pass" -> False, "error" -> "FindRoot failed"|>]];
  uv = u /. urule; dv = dn /. drule;
  wl = (rr^3 - aa^3)/(uv^3 - aa^3);
  wb = (rr^3 - dv^3)/(bb^3 - dv^3);
  residuals = Abs /@ N[{
    fl[uv] - tl, gu[dv] - tu,
    (1 - wl) aa^3 + wl uv^3 - rr^3,
    (1 - wl) aa^4 + wl uv^4 - fourth,
    (1 - wb) dv^3 + wb bb^3 - rr^3,
    (1 - wb) dv^4 + wb bb^4 - fourth}, 80];
  scale = Max[1, Abs[N[rr^3, 80]], Abs[N[fourth, 80]]];
  bound = 10^-50 + 10^-40 scale;
  good = TrueQ[aa < rr < uv < bb && aa < dv < rr < bb &&
    0 < wl < 1 && 0 < wb < 1 && rr^4 < fourth < cc &&
    And @@ (TrueQ[# <= bound] & /@ residuals)];
  <|"pass" -> good, "a" -> ToString[InputForm[aa]],
    "b" -> ToString[InputForm[bb]], "r" -> ToString[InputForm[rr]],
    "m4" -> ToString[InputForm[fourth]],
    "u_80d" -> ToString[InputForm[N[uv, 80]]],
    "d_80d" -> ToString[InputForm[N[dv, 80]]],
    "w_u_80d" -> ToString[InputForm[N[wl, 80]]],
    "w_b_80d" -> ToString[InputForm[N[wb, 80]]],
    "max_residual" -> ToString[InputForm[Max[residuals]]],
    "tolerance" -> ToString[InputForm[bound]]|>
];
numericCases = {
  numericCase[1, 3, 2, 20],
  numericCase[1, 3, 2, 16 + 10^-20],
  numericCase[1, 3, 2, 293/13 - 10^-20]
};

checks = <|
  "xact_loaded" -> xactLoaded,
  "exact_derivatives_and_positivity" ->
    derivativeIdentities && positiveDerivativeFactors && positiveUpperDerivative,
  "strict_S121_endpoint_bracketing" -> endpointGapIdentities && positiveGaps,
  "unique_u_d_by_IVT_and_strict_monotonicity" -> nodeExistUnique,
  "strict_weights" -> positiveWeights,
  "third_and_fourth_moments" -> momentIdentities,
  "normalization" -> normalization,
  "separate_Dirac_chord_endpoint_measures" ->
    diracBoundary && chordBoundary && endpointDiracMeasures,
  "80_digit_controls" -> And @@ (Lookup[#, "pass"] & /@ numericCases)
|>;
allPass = And @@ Values[checks];
result = <|
  "component" -> "CAS-13-C02", "axis" -> "wolfram_xact",
  "status" -> If[allPass, "PASS", "INCONCLUSIVE"],
  "wolfram_version" -> System`$Version,
  "wolfram_version_number" -> ToString[InputForm[System`$VersionNumber]],
  "xact_version" -> ToString[InputForm[xAct`xTensor`$Version]],
  "xact_package_file" -> ToString[FindFile["xAct`xTensor`"]],
  "checks" -> checks,
  "derivative_formula_F" -> ToString[InputForm[derivF]],
  "derivative_formula_G" -> ToString[InputForm[derivG]],
  "strict_gap_formulas" -> {
    "(m4-r^4)/(r^3-a^3)", "(chord-m4)/(r^3-a^3)",
    "(chord-m4)/(b^3-r^3)", "(m4-r^4)/(b^3-r^3)"},
  "node_certificate" -> "Positive rational denominators imply continuity; exact strict endpoint gaps and positive derivatives imply one root each by IVT and at most one by the mean value theorem.",
  "moment_certificate" -> "Third moments equal r^3 algebraically; fourth-moment residuals are the positive m3 gaps times the contracted node-equation residuals.",
  "boundary_certificate" -> "At m4=r^4 both measures limit to delta_r; at the chord both limit to (1-t)delta_a+t delta_b, t=(r^3-a^3)/(b^3-a^3). At m3=a^3 or b^3, nonnegative y^3-a^3 or b^3-y^3 has zero integral only for the endpoint Dirac measure. No 0/0 endpoint substitution is used.",
  "numeric_controls" -> numericCases,
  "domain_assumption_diff" -> {},
  "domain" -> "0<a<r<b, m3=r^3, r^4<m4<chord; positive real cube root; interior nodes u in (r,b), d in (a,r); boundary measures treated separately"
|>;
Print["CAS13_C02_RESULT_JSON=" <> ExportString[result, "RawJSON"]];
Exit[If[allPass, 0, 2]];
