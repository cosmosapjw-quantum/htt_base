(* CAS-03-C03, independent Wolfram Engine + xAct verification.
   Finite real 3x3 inverse/truncation component only. *)
Needs["xAct`xTensor`"];
Print["ENGINE_VERSION\t", $Version];
Print["ENGINE_VERSION_NUMBER\t", $VersionNumber];
Print["XTENSOR_VERSION\t", ToString[InputForm[xAct`xTensor`$Version]]];

failures = {};
check[name_String, value_] := Module[{ok = TrueQ[value]},
  Print["CHECK\t", name, "\t", If[ok, "PASS", "FAIL"]];
  If[! ok, AppendTo[failures, name]];
];
zeroVectorQ[v_] := And @@ (TrueQ[Together[#] === 0] & /@ v);
zeroMatrixQ[m_] := And @@ (TrueQ[Together[#] === 0] & /@ Flatten[m]);

dm = Array[d, {3, 3}];
b = Array[beta, 3];
id = IdentityMatrix[3];
hm = Tr[dm]/3;
sig = dm - hm id;
hOne = -2 dm.b;
det = Det[dm];

(* Polynomial adjugate certificates imply the inverse formula on det D != 0.
   No H != 0 condition is used here. *)
check["trace_split", TrueQ[Together[Tr[sig]] === 0] && zeroMatrixQ[dm - (hm id + sig)]];
check["left_adjugate", zeroMatrixQ[dm.Adjugate[dm] - det id]];
check["right_adjugate", zeroMatrixQ[Adjugate[dm].dm - det id]];
exactBeta = -Adjugate[dm].hOne/(2 det);
check["exact_inverse_on_det_nonzero", zeroVectorQ[det (exactBeta - b)]];

(* H is nonzero in this block. The certified identity is a polynomial
   numerator after multiplying by H^2, so no extra branch is introduced. *)
truncBeta = -((id - sig/hm).hOne)/(2 hm);
check["truncation_defect_on_H_nonzero", zeroVectorQ[hm^2 (b - truncBeta) - sig.sig.b]];

(* Explicit H=0 control: inverse valid, truncation has a zero denominator. *)
dmZero = DiagonalMatrix[{1, 1, -2}];
bZero = Array[z, 3];
hZero = -2 dmZero.bZero;
check["H_zero_control", Tr[dmZero] == 0 && Det[dmZero] == -2 &&
  TrueQ[Inverse[dmZero].hZero/(-2) === bZero]];
Print["CONTROL\tH_zero_truncation\tUNDEFINED_BY_CONTRACT"];

(* Exact rational diagonal control, epsilon a free real symbol. *)
dmRat = DiagonalMatrix[{3/2, 3/4, 3/4}];
bRat = {epsilon, 0, 0};
hRat = -2 dmRat.bRat;
hmRat = Tr[dmRat]/3;
sigRat = dmRat - hmRat id;
truncRat = -((id - sigRat/hmRat).hRat)/(2 hmRat);
check["rational_control", hmRat == 1 && Det[dmRat] != 0 &&
  sigRat/hmRat === DiagonalMatrix[{1/2, -1/4, -1/4}] &&
  truncRat === {3 epsilon/4, 0, 0} &&
  bRat - truncRat === {epsilon/4, 0, 0} &&
  sigRat.sigRat.bRat/hmRat^2 === {epsilon/4, 0, 0}];

Print["FAILED_CHECKS\t", ToString[InputForm[failures]]];
If[failures === {}, Print["COMPONENT_STATUS\tPASS"]; Exit[0],
  Print["COMPONENT_STATUS\tFAIL"]; Exit[2]];
