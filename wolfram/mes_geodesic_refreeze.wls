(* MES-REFREEZE second-engine lane (REV-R188): independent Wolfram
   confirmation of the geodesic derivation + the hierarchy-preservation
   theorem that forces the e1 = 0 re-freeze.

     1. C1/C2 reduction of the primary-source raw MESa bounds
        (eq 51 shear, eq 52 vorticity) to the geodesic triples;
     2. the exact critical dipole e1_crit below which B_sigma > B_omega
        holds with the geodesic omega, and the evaluation at the observed
        dipole (FAILS) and at e1 = 0 (HOLDS);
     3. the re-frozen anchor W2_max = (3/2) B_omega(0, e2, e3)^2.

   House rules: avoid the reserved symbol Gamma; flat `checks` of TrueQ
   booleans; exact rationals throughout (no numeric drift).

   Diagnostic-only: symbolic derivation + provenance; no data claim. *)

ClearAll["Global`*"];

(* raw MESa bounds as (coeff, multipole L, derivative order); the C1/C2
   reduction multiplies each term by (1/3)^order *)
rawSigma = {{8/3, 2, 0}, {1, 2, 1}, {5, 1, 1}, {9/7, 3, 1}};
rawOmega = {{9, 1, 1}, {3, 1, 2}, {6/5, 2, 2}};

reduce[raw_] := Module[{acc = <|1 -> 0, 2 -> 0, 3 -> 0|>},
   Do[acc[t[[2]]] += t[[1]] (1/3)^t[[3]], {t, raw}];
   {acc[1], acc[2], acc[3]}];

sigTriple = reduce[rawSigma];
omTriple = reduce[rawOmega];

sigOK = (sigTriple === {5/3, 3, 3/7});
omOK = (omTriple === {10/3, 2/15, 0});

(* SSOT epsilons (exact rationals) *)
e1s = 12336/10^7; e2s = 3559629/10^12; e3s = 6065291/10^12;

(* hierarchy-preservation theorem: B_sigma - B_omega as a function of e1 *)
Bsig[e1_, e2_, e3_] := (5/3) e1 + 3 e2 + (3/7) e3;
Bom[e1_, e2_, e3_] := (10/3) e1 + (2/15) e2;    (* geodesic *)
diff[e1_, e2_, e3_] := Bsig[e1, e2, e3] - Bom[e1, e2, e3];
e1crit = e1 /. Solve[diff[e1, e2, e3] == 0, e1][[1]];
e1critExpected = ((43/15) e2 + (3/7) e3)/(5/3);
critOK = (Simplify[e1crit - e1critExpected] === 0);
e1critNum = e1crit /. {e2 -> e2s, e3 -> e3s};

fullHolds = TrueQ[Bsig[e1s, e2s, e3s] > Bom[e1s, e2s, e3s]];
zeroHolds = TrueQ[Bsig[0, e2s, e3s] > Bom[0, e2s, e3s]];
observedExceedsCrit = TrueQ[e1s > e1critNum];

(* re-frozen anchor *)
w2Refrozen = (3/2) Bom[0, e2s, e3s]^2;
sig2Refrozen = (3/2) Bsig[0, e2s, e3s]^2;

<|
  "schema" -> "htt.egs3.mes_geodesic_refreeze.wolfram.v1",
  "wolfram_version" -> ToString[InputForm[$Version]],
  "sigma_triple" -> ToString[sigTriple],
  "omega_triple" -> ToString[omTriple],
  "e1_crit" -> ToString[InputForm[Simplify[e1crit]]],
  "e1_crit_numeric" -> N[e1critNum, 16],
  "W2_max_refrozen" -> N[w2Refrozen, 16],
  "W2_max_refrozen_exact" -> ToString[InputForm[w2Refrozen]],
  "Sigma2_max_refrozen" -> N[sig2Refrozen, 16],
  "checks" -> <|
    "sigma_reduces_to_geodesic" -> sigOK,
    "omega_reduces_to_geodesic" -> omOK,
    "e1_crit_matches_derivation" -> critOK,
    "observed_dipole_exceeds_crit" -> observedExceedsCrit,
    "full_dipole_hierarchy_violated" -> Not[fullHolds],
    "e1_zero_hierarchy_holds" -> zeroHolds,
    "refrozen_hierarchy_strict" ->
      TrueQ[Bsig[0, e2s, e3s] > Bom[0, e2s, e3s] > 0]
  |>
|>
