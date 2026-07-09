(* v8 TEFF representative-theory constants: independent Wolfram cross-check.

   Verifies, in exact closed form, the load-bearing constants of the max-entropy
   effective-temperature representative theory (draft "Maximum-Entropy Effective-
   Temperature Representatives"):

     (Thm 3) radial constants a_xi from the exact Bose/Fermi integrals:
        a_0   = int s^2 e^{-s} ds                = 2
        a_{+1}= int s^2 [-Log(1-e^{-s})] ds      = 2 Zeta[4]
        a_{-1}= int s^2 Log(1+e^{-s}) ds         = (7/4) Zeta[4]
     (Def 13) insertion fingerprints c_p = (p-4)/2^{p+1}: c3=-1/16, c4=0, c5=1/64.
     (Thm 22) two-temperature ratios R_p(s)=a(s)^p ((1+s)^p+(1-s)^p)/2,
        a(s)=(1+6 s^2+s^4)^{-1/4}:  R4(s)==1 exactly; series R3=1-(3/2)s^2+...,
        R5=1+(5/2)s^2+...  (opposite signs).

   This is the report-independent second engine for the SymPy seal
   (htt/teff/representative.teff_representative_seal). Diagnostic-only; representation
   theory + exact closed forms; no data/detection/family/solver/posterior claim. *)

ClearAll["Global`*"];

(* ---- Thm 3: exact Bose/Fermi radial integrals ---- *)
aMB = TimeConstrained[Integrate[s^2 Exp[-s], {s, 0, Infinity}], 60, $Failed];
aBE = TimeConstrained[Integrate[s^2 (-Log[1 - Exp[-s]]), {s, 0, Infinity},
    Assumptions -> True], 120, $Failed];
aFD = TimeConstrained[Integrate[s^2 Log[1 + Exp[-s]], {s, 0, Infinity},
    Assumptions -> True], 120, $Failed];
aMBok = TrueQ[Simplify[aMB - 2] === 0];
aBEok = TrueQ[Simplify[aBE - 2 Zeta[4]] === 0];
aFDok = TrueQ[Simplify[aFD - (7/4) Zeta[4]] === 0];

(* ---- Def 13: insertion fingerprints ---- *)
cp[p_] := (p - 4)/2^(p + 1);
c3ok = TrueQ[cp[3] === -1/16];
c4ok = TrueQ[cp[4] === 0];
c5ok = TrueQ[cp[5] === 1/64];

(* ---- Thm 22: two-temperature ratios ---- *)
aOf[s_] := (1 + 6 s^2 + s^4)^(-1/4);
Rp[p_, s_] := aOf[s]^p ((1 + s)^p + (1 - s)^p)/2;
R4one = TrueQ[Simplify[Rp[4, s] - 1] === 0];
R3ser = Series[Rp[3, s], {s, 0, 2}];
R5ser = Series[Rp[5, s], {s, 0, 2}];
R3c2 = SeriesCoefficient[R3ser, 2];
R5c2 = SeriesCoefficient[R5ser, 2];
R3ok = TrueQ[R3c2 === -3/2];
R5ok = TrueQ[R5c2 === 5/2];

<|
  "schema" -> "htt.teff.representative.constants.v1",
  "wolfram_version" -> ToString[InputForm[$Version]],
  "a_MB_expr" -> ToString[InputForm[aMB]],
  "a_BE_expr" -> ToString[InputForm[aBE]],
  "a_FD_expr" -> ToString[InputForm[aFD]],
  "R3_s2_coeff" -> ToString[InputForm[R3c2]],
  "R5_s2_coeff" -> ToString[InputForm[R5c2]],
  "checks" -> <|
    "a_MB_is_2" -> aMBok,
    "a_BE_is_2zeta4" -> aBEok,
    "a_FD_is_7_4_zeta4" -> aFDok,
    "c3_is_minus_1_16" -> c3ok,
    "c4_is_zero" -> c4ok,
    "c5_is_1_64" -> c5ok,
    "R4_invariant" -> R4one,
    "R3_minus_three_halves" -> R3ok,
    "R5_plus_five_halves" -> R5ok
  |>
|>
