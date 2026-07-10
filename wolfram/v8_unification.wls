(* EGS3 v8-update U1/U2/U3: independent Wolfram verification of the MES /
   comparator / Teff unification lane. Everything recomputed from first
   principles -- nothing read from the Python seals.
     U1: boosted-blackbody antipodal temperatures T0 e^{+/-beta}; two-
         temperature reduction s = tanh(beta); elimination s^2 = t/(2+t);
         exact series R3 - 1 = -(3/4) t + (87/32) t^2, R5 - 1 = (5/4) t
         - (185/32) t^2; single-species -(3/2) pin; R4 == 1 identically.
     U2: envelope inequalities 1 - R3 <= (3/2) s^2 and 0 <= R5 - 1 <=
         (5/2) s^2 on 0 < s < 1 via Resolve/ForAll; exact rational ceilings
         at eps1 = 771/625000.
     U3: comparator design MatrixRank 2 with axis-aligned null {W2, Omega_k};
         Teff response {{-1/16,-3/2},{0,0},{1/64,5/2}} with the p=4 selector
         row exactly zero and full rank 2. *)
ClearAll["Global`*"];

(* Teff two-temperature machinery, independent implementation *)
aOf[s_] := (1 + 6 s^2 + s^4)^(-1/4);
Rp[p_, s_] := aOf[s]^p ((1 + s)^p + (1 - s)^p)/2;

(* U1: boost antipodes and the reduction *)
v = Tanh[beta]; gamma = 1/Sqrt[1 - v^2];
antipodes = FullSimplify[1/(gamma (1 - v)) - Exp[beta],
    Assumptions -> beta > 0] === 0;
cMid = (Exp[beta] + Exp[-beta])/2;
sRed = FullSimplify[(Exp[beta] - cMid)/cMid - Tanh[beta]] === 0;
s2Elim = FullSimplify[Tanh[beta]^2 - (2 Sinh[beta]^2)/(2 + 2 Sinh[beta]^2)] === 0;

r3t = Normal[Series[Rp[3, Sqrt[t/(2 + t)]], {t, 0, 2}]];
r5t = Normal[Series[Rp[5, Sqrt[t/(2 + t)]], {t, 0, 2}]];
seriesOK = (Coefficient[r3t, t, 1] === -3/4) &&
           (Coefficient[r5t, t, 1] === 5/4) &&
           (Coefficient[r3t, t, 2] === 87/32) &&
           (Coefficient[r5t, t, 2] === -185/32);
r3single = Normal[Series[Rp[3, Sqrt[t1/(1 + t1)]], {t1, 0, 1}]];
singlePin = Coefficient[r3single, t1, 1] === -3/2;
r4Ident = FullSimplify[Rp[4, s] - 1, Assumptions -> 0 < s < 1] === 0;

(* U2: envelopes via Resolve (exact quantifier elimination) *)
env3lo = Resolve[ForAll[s, 0 < s < 1, Rp[3, s] <= 1], Reals];
env3hi = Resolve[ForAll[s, 0 < s < 1, 1 - Rp[3, s] <= (3/2) s^2], Reals];
env5lo = Resolve[ForAll[s, 0 < s < 1, Rp[5, s] >= 1], Reals];
env5hi = Resolve[ForAll[s, 0 < s < 1, Rp[5, s] - 1 <= (5/2) s^2], Reals];

eps1 = 771/625000;                                  (* registered ssot eps1 *)
ceil3 = (3/2) eps1^2; ceil5 = (5/2) eps1^2;
ceilOK = (ceil3 === 1783323/781250000000) && (ceil5 === 594441/156250000000);

(* U3: both response matrices *)
Dcomp = {{1, 0, 0, 0}, {0, 0, 1, 0}, {0, 0, 1, 0}};   (* channel x sector *)
rankComp = MatrixRank[Dcomp] === 2;
nullComp = NullSpace[Transpose[Dcomp] . Dcomp];
nullAligned = Sort[Flatten[Position[#, 1 | -1] & /@ nullComp]] === {2, 4};
cp[p_] := (p - 4)/2^(p + 1);
dRp[p_] := SeriesCoefficient[Rp[p, Sqrt[u]], {u, 0, 1}];
Tteff = Table[{cp[p], dRp[p]}, {p, {3, 4, 5}}];
teffOK = Tteff === {{-1/16, -3/2}, {0, 0}, {1/64, 5/2}};
rankTeff = MatrixRank[Tteff] === 2;
p4Zero = Tteff[[2]] === {0, 0};

<|
  "schema" -> "htt.egs3.v8_unification.v1",
  "checks" -> <|
    "boost_antipodes_exp_beta" -> TrueQ[antipodes],
    "s_equals_tanh_beta" -> TrueQ[sRed],
    "s2_equals_t_over_2_plus_t" -> TrueQ[s2Elim],
    "series_coeffs_m34_54_8732_m18532" -> TrueQ[seriesOK],
    "single_species_pin_m32" -> TrueQ[singlePin],
    "R4_identically_one" -> TrueQ[r4Ident],
    "envelope_R3_below_one" -> TrueQ[env3lo],
    "envelope_one_minus_R3_below_3half_s2" -> TrueQ[env3hi],
    "envelope_R5_above_one" -> TrueQ[env5lo],
    "envelope_R5_minus_one_below_5half_s2" -> TrueQ[env5hi],
    "exact_rational_ceilings_at_eps1" -> TrueQ[ceilOK],
    "comparator_design_rank_two" -> TrueQ[rankComp],
    "comparator_null_axis_aligned_W2_Omegak" -> TrueQ[nullAligned],
    "teff_response_matrix_exact" -> TrueQ[teffOK],
    "teff_full_response_rank_two" -> TrueQ[rankTeff],
    "teff_p4_selector_row_zero" -> TrueQ[p4Zero],
    "signature" -> "U1 s=tanh(beta), R3-1=-(3/4)t; U2 (3/2,5/2) s^2 envelopes + eps1 ceilings; U3 rank-2 schema on both sides"
  |>
|>
