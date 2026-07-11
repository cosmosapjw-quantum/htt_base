#!/usr/bin/env wolframscript
(* MES-MESB-TRACE independent lane (REV-R190).
   Exact-rational reduction of the raw MESa bounds by C1/C2, the in-house
   non-geodesic refutation against the DeltaT/T companion reduced bound,
   and the two candidate anchors. No xAct needed (pure rational algebra).
   Cross-engine twin of htt/obsstat/egs3_mesb_web_trace.py.               *)

(* --- SSOT epsilons (exact) --- *)
eps1 = 771/625000;
eps2 = 3559629/1000000000000;
eps3 = 6065291/1000000000000;

(* --- C1/C2 reduction of a raw bound: list of {coeff, order} on eps_L --- *)
(* raw shear MESa eq(51): (8/3)eps2 + eps2* + 5 eps1' + (9/7) eps3'
   reduce: eps_L^(k derivs) -> (1/3)^k eps_L                            *)
redSigma = (8/3)*eps2 + (1/3)*eps2 + 5*(1/3)*eps1 + (9/7)*(1/3)*eps3;
(* raw vorticity MESa eq(52): 9 eps1' + 3 eps1'* + (6/5) eps2''         *)
redOmega = 9*(1/3)*eps1 + 3*(1/9)*eps1 + (6/5)*(1/9)*eps2;

(* published reduced targets: eq(59) sigma, eq(60) omega (geodesic)     *)
eq59 = (5/3)*eps1 + 3*eps2 + (3/7)*eps3;
eq60 = (10/3)*eps1 + (2/15)*eps2;

sigmaReductionOK = (Simplify[redSigma - eq59] === 0);
omegaReductionOK = (Simplify[redOmega - eq60] === 0);

(* coefficient-level cross checks (independent of eps values) *)
sSym = Simplify[(8/3) + 1/3];           (* -> 3 (eps2 coeff of eq59) *)
oSym = Simplify[9*(1/3) + 3*(1/9)];     (* -> 10/3 (eps1 coeff of eq60) *)
sigmaCoeffOK = (sSym === 3);
omegaCoeffOK = (oSym === 10/3);

(* --- geodesic anchor (precise), eps1 = 0 --- *)
BomegaGeo = (2/15)*eps2;
W2geo = (3/2)*BomegaGeo^2;

(* --- companion / MESb non-geodesic envelope: omega/Theta < alpha 1e-5.
   assumption (c): alpha 1e-5 = max(eps2,eps3) = eps3 (faithful);
   COBE alpha~1 -> 1e-5 (loose). --- *)
cobeCap = 1/100000;
eMax = Max[eps2, eps3];           (* = eps3 *)
BomegaComp = eMax;                (* faithful cap *)
W2comp = (3/2)*BomegaComp^2;      (* faithful 5.52e-11 *)
W2compCobe = (3/2)*cobeCap^2;     (* COBE loose 1.50e-10 *)

(* --- in-house non-geodesic omega (3/4,2,2/7), eps1 = 0 --- *)
BomegaIH = 2*eps2 + (2/7)*eps3;
W2IH = (3/2)*BomegaIH^2;

(* companion cap: faithful = max(eps2,eps3) = eps3; COBE = 1e-5 *)
companionCapFaithful = eMax;
inHouseExceedsFaithful = (BomegaIH > companionCapFaithful);
inHouseWithinCobe = (BomegaIH < cobeCap);
geodesicConsistent  = (BomegaGeo < companionCapFaithful);

(* sigma reduced (eps1 = 0) rounds to 4 alpha 1e-5 *)
eq59zero = 3*eps2 + (3/7)*eps3;
sigmaReducedRatio = N[eq59zero]/N[eps2];   (* -> ~3.7 -> rounds to 4 *)

allOK = sigmaReductionOK && omegaReductionOK && sigmaCoeffOK && omegaCoeffOK &&
        inHouseExceedsFaithful && geodesicConsistent;

result = <|
  "engine" -> "wolfram",
  "seal" -> "mesb_web_trace",
  "sigma_reduction_reproduces_eq59" -> sigmaReductionOK,
  "omega_reduction_reproduces_eq60" -> omegaReductionOK,
  "sigma_eps2_coeff_is_3" -> sigmaCoeffOK,
  "omega_eps1_coeff_is_10_3" -> omegaCoeffOK,
  "W2_geodesic" -> N[W2geo, 16],
  "W2_geodesic_exact" -> ToString[W2geo],
  "B_omega_companion_faithful" -> N[BomegaComp, 16],
  "W2_companion_faithful" -> N[W2comp, 16],
  "W2_companion_cobe" -> N[W2compCobe, 16],
  "B_omega_in_house_eps1_zero" -> N[BomegaIH, 16],
  "W2_in_house" -> N[W2IH, 16],
  "in_house_exceeds_companion_faithful" -> inHouseExceedsFaithful,
  "in_house_within_cobe_cap" -> inHouseWithinCobe,
  "in_house_excess_factor_faithful" -> N[BomegaIH/companionCapFaithful, 6],
  "geodesic_consistent_with_companion" -> geodesicConsistent,
  "sigma_reduced_over_eps2" -> N[sigmaReducedRatio, 6],
  "status" -> If[allOK, "PASS", "FAIL"]
|>;

Print[ExportString[result, "RawJSON", "Compact" -> True]];
