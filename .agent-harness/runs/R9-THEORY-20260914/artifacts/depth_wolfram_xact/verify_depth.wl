(*
  R9 depth-formal Wolfram/xAct axis runner.

  Invocation: WolframKernel -noprompt -script verify_depth.wl D1|D3|D2|D4
  stdout is deliberately one RawJSON document for cas_gate.py run-adjudicate.
  The exact rational fixture exercises rectangular transports and a singular
  covariance.  It is evidence of a computed special case only: none of the
  quantified contracts is marked proved by this script.
*)

ClearAll["Global`*"];

prop = If[Length[$ScriptCommandLine] >= 2, Last[$ScriptCommandLine], ""];

(* d=(2,3,1), K0: R^2 -> R^3 and K1: R^3 -> R. *)
k0 = {{1, 2}, {0, 1}, {2, -1}};
k1 = {{1, -2, 3}};
h = ArrayFlatten[{{-k0, IdentityMatrix[3], ConstantArray[0, {3, 1}]},
                  {ConstantArray[0, {1, 2}], -k1, IdentityMatrix[1]}}];
t = Join[ArrayFlatten[{{IdentityMatrix[2], ConstantArray[0, {2, 4}]}}], h];

(* C=L L^T is PSD and singular: rank(C)=5.  The last latent coordinate is
   absent from the five-block past and leaves a positive Schur residual. *)
l = {{1, 0, 1, 0, 0},
     {0, 1, 1, 0, 0},
     {1, 1, 0, 1, 0},
     {2, 0, 1, 1, 0},
     {0, 1, 2, 1, 0},
     {1, -1, 0, 2, 1}};
c = l.Transpose[l];
v = h.c.Transpose[h];

bool[x_] := TrueQ[x];
zeroQ[x_] := bool[Simplify[x == ConstantArray[0, Dimensions[x]]]];

onecomp[] := Module[{crossFormula, directCross, psdWitness},
  directCross = v[[1 ;; 3, 4 ;; 4]];
  crossFormula = c[[3 ;; 5, 6 ;; 6]] - c[[3 ;; 5, 3 ;; 5]].Transpose[k1]
    - k0.c[[1 ;; 2, 6 ;; 6]] + k0.c[[1 ;; 2, 3 ;; 5]].Transpose[k1];
  psdWitness = Simplify[Transpose[Array[q, 4]].v.Array[q, 4]
    == Transpose[Transpose[h].Array[q, 4]].c.(Transpose[h].Array[q, 4])];
  <|"fixture_dimensions" -> {2, 3, 1},
    "covariance_rank" -> MatrixRank[c],
    "residual_covariance_rank" -> MatrixRank[v],
    "cross_block_exact" -> bool[directCross == crossFormula],
    "pullback_identity_exact" -> bool[psdWitness]|>
];

threecomp[] := Module[{y, r, rec, s, recS, kernelBasis, propagated},
  y = Array[y, 6]; r = h.y;
  rec = Join[y[[1 ;; 2]], r[[1 ;; 3]] + k0.y[[1 ;; 2]],
    {r[[4]] + (k1.(r[[1 ;; 3]] + k0.y[[1 ;; 2]]))[[1]]}];
  s = Array[s, 6];
  recS = Join[s[[1 ;; 2]], s[[3 ;; 5]] + k0.s[[1 ;; 2]],
    {s[[6]] + (k1.(s[[3 ;; 5]] + k0.s[[1 ;; 2]]))[[1]]}];
  kernelBasis = NullSpace[h];
  propagated = Transpose[Join[IdentityMatrix[2], k0, k1.k0]];
  <|"fixture_dimensions" -> {2, 3, 1},
    "inverse_after_h_exact" -> bool[And @@ Thread[rec == y]],
    "t_after_inverse_exact" -> bool[And @@ Thread[t.recS == s]],
    "determinant_T" -> Det[t], "rank_H" -> MatrixRank[h],
    "kernel_propagation_rank" -> MatrixRank[propagated],
    "kernel_span_exact" -> bool[MatrixRank[Join[kernelBasis, propagated]] == 2],
    "support_rank_preserved" -> bool[MatrixRank[t.c.Transpose[t]] == MatrixRank[c]]|>
];

twocomp[] := <|"fixture_dimensions" -> {2, 3, 1},
  "V_rank" -> MatrixRank[v],
  "moore_penrose_reflexive_exact" -> bool[v.PseudoInverse[v].v == v],
  "support_projector_idempotent_exact" -> bool[(v.PseudoInverse[v]).(v.PseudoInverse[v]) == v.PseudoInverse[v]],
  "rank_zero_branch_exercised" -> False,
  "distributional_chisquare_proved" -> False|>;

fourcomp[] := <|"past_dimension" -> 5, "current_dimension" -> 1,
  "past_covariance_rank" -> MatrixRank[c[[1 ;; 5, 1 ;; 5]]],
  "conditional_law_proved" -> False, "independence_proved" -> False|>;

payloadFor["D1"] := Association["checks" -> Association[
    "D1_MEAN_COVARIANCE_LINEAR_MAP" -> False,
    "D1_ALL_CROSS_STEP_BLOCKS" -> False,
    "D1_PSD_PULLBACK_GENERAL_DIMENSION" -> False],
  "domain_assumption_diff" -> {}, "counterexample" -> Null,
  "computed" -> onecomp[],
  "proof_scope" -> "Exact rational d=(2,3,1) fixture only; no theorem-level universal finite-block or finite-second-moment proof supplied."];
payloadFor["D3"] := Association["checks" -> Association[
    "D3_RECURSION_BOTH_INVERSES_ARBITRARY_BLOCKS" -> False,
    "D3_KERNEL_SURJECTIVITY_DETERMINANT" -> False,
    "D3_FULL_LAW_SUPPORT_PRESERVED" -> False],
  "domain_assumption_diff" -> {}, "counterexample" -> Null,
  "computed" -> threecomp[],
  "proof_scope" -> "Exact symbolic variables under one d=(2,3,1) transport fixture; no all-compatible-block proof or full-law support theorem supplied."];
payloadFor["D2"] := Association["checks" -> Association[
    "D2_GAUSSIAN_PUSHFORWARD_SUPPORT" -> False,
    "D2_SUPPORTED_PSEUDOINVERSE_CHISQUARE" -> False,
    "D2_RANK_ZERO_AND_OFF_SUPPORT" -> False],
  "domain_assumption_diff" -> {}, "counterexample" -> Null,
  "computed" -> twocomp[],
  "proof_scope" -> "Exact singular-covariance matrix identities only; no general Gaussian pushforward, whitening, support, or chi-square distribution proof supplied."];
payloadFor["D4"] := Association["checks" -> Association[
    "D4_PSD_RANGE_SCHUR_SUPPORT" -> False,
    "D4_FULL_PAST_CONDITIONAL_GAUSSIAN" -> False,
    "D4_INNOVATION_INDEPENDENCE_AND_FIXED_LAW_LIMIT" -> False],
  "domain_assumption_diff" -> {}, "counterexample" -> Null,
  "computed" -> fourcomp[],
  "proof_scope" -> "Exact singular past covariance fixture only; no theorem-level full-past conditional Gaussian or innovation-independence proof supplied."];
payloadFor[_] := Association["checks" -> Association[], "domain_assumption_diff" -> {"unknown proposition ID"},
  "counterexample" -> Null, "computed" -> Association[], "proof_scope" -> "invalid invocation"];

(* xAct changes the parser treatment of Association shorthand after Needs[].
   Build the payload before loading it, then mutate it without shorthand. *)
payload = payloadFor[prop];
xactLoaded = Block[{$Output = {}}, Quiet[Check[Needs["xAct`xTensor`]; True, False]]];
xactVersion = If[xactLoaded, ToString[xAct`xTensor`$Version, InputForm], "unavailable"];
AssociateTo[payload, "engine" -> $Version, "xact_loaded" -> xactLoaded,
  "xact_version" -> xactVersion, "proposition" -> prop];
Print[ExportString[payload, "RawJSON"]];
Quit[0];
