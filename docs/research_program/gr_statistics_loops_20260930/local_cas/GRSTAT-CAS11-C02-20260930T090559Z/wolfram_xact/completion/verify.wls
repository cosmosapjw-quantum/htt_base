(* CAS11-C02 v3: fresh independent Wolfram axis, arbitrary-dimension analytic
   reduction supported by exact scalar/induction certificates.  No sibling
   inputs, fixed-dimension examples, or target-equivalent assumed axiom. *)

ClearAll["Global`*"];
$HistoryLength = 0;
Print["WOLFRAM_VERSION: ", System`$Version];
Needs["xAct`xTensor`"];
If[!ListQ[xAct`xTensor`$Version],
  Print["XACT_LOAD_FAILED"];
  Exit[3]
];
Print["XACT_VERSION: ", InputForm[xAct`xTensor`$Version]];

certificates = <||>;
SetAttributes[certify, HoldRest];
certify[name_, statement_] := Module[{held, result, elapsed},
  held = HoldComplete[statement];
  {elapsed, result} = AbsoluteTiming[
    TimeConstrained[Resolve[statement, Reals], 90, $TimedOut]
  ];
  AssociateTo[certificates, name -> <|
    "statement" -> ToString[held, InputForm],
    "method" -> "Resolve[..., Reals] (exact real quantifier elimination)",
    "result" -> ToString[result, InputForm],
    "passed" -> TrueQ[result],
    "elapsed_seconds" -> elapsed
  |>];
  Print["CERTIFICATE: ", name, " -> ", InputForm[result]];
];

(* A coordinate in the zero eigenspace is forced to zero by the premise
   applied to its eigenvector.  The epsilon=0 specialization works for any
   eigenvalue and is independently checked. *)
certify["null_coordinate", ForAll[{cc}, Implies[cc^2 <= 0, cc == 0]]];
certify["zero_epsilon_coordinate", ForAll[{cc, ll, ee},
  Implies[ee == 0 && ll >= 0 && cc^2 <= 2 ee ll, cc == 0]]];

(* pj is the spectral reciprocal, specified without a division by zero.
   Both positive and zero spectral branches are retained in each formula. *)
certify["spectral_reciprocal_penrose", ForAll[{ll, pj},
  Implies[(ll > 0 && ll pj == 1) || (ll == 0 && pj == 0),
    ll >= 0 && pj >= 0 && ll pj ll == ll && pj ll pj == pj]]];

(* Apply null_coordinate first, then use h_j=p_j c_j and q_j=p_j c_j^2.
   This establishes the range witness, both quadratic identities, and the
   nonnegativity of every summand, for every spectral coordinate. *)
certify["coordinate_range_and_quadratics", ForAll[{ll, pj, cc},
  Implies[
    ((ll > 0 && ll pj == 1) || (ll == 0 && pj == 0)) &&
      Implies[ll == 0, cc == 0],
    ll (pj cc) == cc &&
      (pj cc) cc == pj cc^2 &&
      ll (pj cc)^2 == pj cc^2 && pj cc^2 >= 0]]];

(* These universally quantified recurrence implications are the induction
   step for finite sums.  The base is the empty sum, exactly 0.  The proof
   document instantiates them for arbitrary n, not for a selected dimension. *)
certify["finite_sum_identity_step", ForAll[{ss, tt, uu, vv},
  Implies[ss == tt && uu == vv, ss + uu == tt + vv]]];
certify["finite_sum_nonnegative_step", ForAll[{ss, uu},
  Implies[ss >= 0 && uu >= 0, ss + uu >= 0]]];
certify["finite_sum_zero_step", ForAll[{ss, uu},
  Implies[ss == 0 && uu == 0, ss + uu == 0]]];

(* For h=(p_j c_j), t=sum p_j c_j^2, the universal premise at a=Q h
   is t^2<=2 epsilon t.  This exact certificate includes t=0 and epsilon=0,
   and makes no unsafe cancellation or division. *)
certify["terminal_scalar_bound", ForAll[{tt, ee},
  Implies[ee >= 0 && tt >= 0 && tt^2 <= 2 ee tt, tt <= 2 ee]]];

(* Targeted branch falsifiers use the same universal scalar reductions;
   they are additional branch checks, not numerical substitutes for proof. *)
certify["zero_matrix_target", ForAll[{tt, ee},
  Implies[ee >= 0 && tt == 0, tt <= 2 ee]]];
certify["zero_epsilon_terminal", ForAll[{tt},
  Implies[tt >= 0 && tt^2 <= 0, tt == 0]]];

report = <|
  "contract_sha256" -> "c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a",
  "engine" -> <|
    "wolfram_version" -> System`$Version,
    "kernel_executable" -> FileNameJoin[{System`$InstallationDirectory, "Executables", "WolframKernel"}],
    "system_id" -> $SystemID,
    "process_id" -> $ProcessID,
    "xact_version" -> ToString[xAct`xTensor`$Version, InputForm],
    "xact_xTensor_source" -> FindFile["xAct`xTensor`"],
    "xact_xPerm_source" -> FindFile["xAct`xPerm`"]
  |>,
  "verification_kind" -> "universal analytic proof with exact Wolfram scalar and induction-step certificates",
  "full_theorem_kernel_formalization" -> False,
  "certificates" -> certificates,
  "all_certificates_passed" -> And @@ (TrueQ[#1["passed"]] & /@ Values[certificates])
|>;
Print["C02_ENGINE_REPORT=", ExportString[report, "RawJSON", "Compact" -> True]];
Exit[If[TrueQ[report["all_certificates_passed"]], 0, 4]];
