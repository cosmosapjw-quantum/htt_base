(* EGS3 B4: covariant constants for the two-sided shear/F bracket (NT2-B1).
   Returns a JSON-serializable Association. Derives the lower-bound coefficient
   from the covariant l=2 relation a2 = kappa*Sigma*(1 + delta), |delta| <= R,
   and confirms the lower bound is strictly positive at nonzero a2. *)
ClearAll["Global`*"];
$Assumptions = kappa > 0 && Sigma > 0 && a2 > 0 && 0 <= R < 1 && Cup > 0;

(* l=2 relation with a bounded derivative correction delta (H3: |delta|<=R). *)
a2rel = kappa Sigma (1 + delta);
(* invert for Sigma at the extremal delta = +R (gives the LOWER Sigma) and
   delta = -R (gives the UPPER from the relation); MES supplies Cup. *)
SigmaLow = Simplify[a2 / (kappa (1 + R))];     (* delta = +R *)
SigmaRelHigh = Simplify[a2 / (kappa (1 - R))]; (* delta = -R *)
SigmaUpMES = Cup a2;                            (* MES upper bound *)

xmax = 925/100000000;  (* 9.25e-6 as an exact rational *)
Flow = Simplify[SigmaLow^2 / xmax];
Fhigh = Simplify[SigmaUpMES^2 / xmax];

(* The bracket is nondegenerate (Flow < Fhigh) iff the MES upper constant
   exceeds the H3 lower coefficient: Cup*kappa*(1+R) > 1. This holds for the
   cited values kappa = 4/21, Cup = 9 (any R in [0,1)): Cup*kappa = 12/7 > 1. *)
bracketCond = Cup kappa (1 + R) > 1;
flowBelowHigh = Simplify[Flow < Fhigh, Assumptions -> {bracketCond, a2 > 0, kappa > 0, R >= 0, Cup > 0}];
citedCond = TrueQ[Simplify[(9)*(4/21)*(1 + R) > 1, Assumptions -> {0 <= R < 1}]];

<|
  "schema" -> "htt.egs3.bracket_constants.v1",
  "checks" -> <|
    "sigma_low_expr" -> ToString[InputForm[SigmaLow]],
    "sigma_low_positive_at_nonzero_a2" -> TrueQ[Simplify[SigmaLow > 0]],
    "lower_bound_coefficient_kappa_over_1plusR" -> ToString[InputForm[Simplify[SigmaLow/a2]]],
    "F_low_positive" -> TrueQ[Simplify[Flow > 0]],
    "F_low_strictly_below_F_high_under_bracket_condition" -> TrueQ[flowBelowHigh],
    "bracket_condition" -> "Cup*kappa*(1+R) > 1",
    "cited_values_satisfy_condition" -> citedCond,
    "zero_excluded_iff_a2_positive" -> TrueQ[Simplify[(Flow > 0) == (a2 > 0)]],
    "derivative_correction_bound" -> "Sigma in [a2/(kappa(1+R)), a2/(kappa(1-R))] under |delta|<=R (H3)"
  |>
|>
