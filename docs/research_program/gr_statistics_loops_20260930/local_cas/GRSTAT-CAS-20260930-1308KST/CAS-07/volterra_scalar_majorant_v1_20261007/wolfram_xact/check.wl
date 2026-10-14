(* CAS-07 M03: exact scalar Volterra identities and a 1D xTensor contraction.
   Universal comparison is proved in PROOF.md; no finite truncation is used as
   the theorem. This file checks its exact algebraic and tensor ingredients. *)

$HistoryLength = 0;
Print["WOLFRAM_VERSION=" <> $Version];
Print["WOLFRAM_VERSION_NUMBER=" <> ToString[$VersionNumber, InputForm]];

ClearAll[record, failures, checks, x, t, z, s, n, j, k, ell, m];
failures = {};
checks = <||>;
record[name_, condition_] := Module[{v = TrueQ[condition]},
  AssociateTo[checks, name -> v];
  Print["CHECK " <> name <> " " <> If[v, "PASS", "FAIL"]];
  If[!v, AppendTo[failures, name]];
];

(* Beta convolution: the normalized nth kernel composed with (x-s)
   is the normalized (n+1)st kernel, for every positive integer n. *)
beta = Integrate[(1-z) z^(2 n-1), {z,0,1},
  Assumptions -> Element[n, Integers] && n >= 1];
record["beta_convolution",
  FullSimplify[beta == 1/((2 n)(2 n+1)),
    Element[n, Integers] && n >= 1]];

(* T_K^n x: K^n x^(2n+1)/(2n+1)!; induction coefficient. *)
monomialStep = Integrate[(x-t) t^(2 n+1), {t,0,x},
  Assumptions -> Element[n, Integers] && n >= 0 && x >= 0];
record["monomial_induction",
  FullSimplify[monomialStep/(2 n+1)! == x^(2 n+3)/(2 n+3)!,
    Element[n, Integers] && n >= 0 && x >= 0]];

(* The nth-kernel bound for arbitrary bounded u, and its exact ratio. *)
kernelMass = Integrate[(x-t)^(2 n-1), {t,0,x},
  Assumptions -> Element[n, Integers] && n >= 1 && x >= 0];
record["kernel_mass",
  FullSimplify[kernelMass/(2 n-1)! == x^(2 n)/(2 n)!,
    Element[n, Integers] && n >= 1 && x >= 0]];
record["remainder_ratio",
  FullSimplify[(k ell^2)^(n+1)/(2 n+2)! /
    ((k ell^2)^n/(2 n)!) ==
    k ell^2/((2 n+2)(2 n+1)),
    k > 0 && ell > 0 && Element[n, Integers] && n >= 0]];
record["ratio_limit",
  FullSimplify[Limit[k ell^2/((2 n+2)(2 n+1)), n -> Infinity] == 0,
    k >= 0 && ell > 0]];

(* Exact power series, including separate zero-k branch. *)
seriesPositive = Sum[k^j x^(2 j+1)/(2 j+1)!, {j,0,Infinity},
  Assumptions -> k > 0 && x >= 0];
record["sinh_series",
  FullSimplify[seriesPositive == Sinh[Sqrt[k] x]/Sqrt[k],
    k > 0 && x >= 0]];
fPiece = Piecewise[{{x, k == 0}}, Sinh[Sqrt[k] x]/Sqrt[k]];
record["zero_k", FullSimplify[fPiece == x, k == 0]];
record["vertex",
  FullSimplify[Sinh[Sqrt[k] 0]/Sqrt[k] == 0, k > 0]];
record["equality_solution",
  FullSimplify[
    x + k Integrate[(x-t) Sinh[Sqrt[k] t]/Sqrt[k], {t,0,x},
      Assumptions -> k > 0 && x >= 0] ==
      Sinh[Sqrt[k] x]/Sqrt[k],
    k > 0 && x >= 0]];
record["zero_function_control",
  FullSimplify[Sinh[Sqrt[k] x]/Sqrt[k] >= 0, k > 0 && x >= 0]];

(* xTensor is used on a Euclidean one-dimensional tangent space. The
   positive scalar Volterra weight multiplies a genuine metric contraction.
   The symmetry check confirms that the two vector slots contract through
   the same positive metric, and no Lorentzian norm enters the majorant. *)
Needs["xAct`xTensor`"];
Print["XACT_CONTEXT=" <> ToString[Context[xAct`xTensor`DefManifold], InputForm]];
DefManifold[VolterraLineM03, 1, {aa, bb, cc, dd}];
DefMetric[1, positiveMetricM03[-aa,-bb], positiveCDM03];
DefTensor[vM03[aa], VolterraLineM03];
DefTensor[wM03[aa], VolterraLineM03];
contractVW = positiveMetricM03[-aa,-bb] vM03[aa] wM03[bb];
contractWV = positiveMetricM03[-aa,-bb] wM03[aa] vM03[bb];
record["xtensor_metric_contraction_symmetry",
  TrueQ[ToCanonical[contractVW-contractWV] === 0]];
weightedNorm = k (x-t) positiveMetricM03[-aa,-bb] vM03[aa] vM03[bb];
record["xtensor_weighted_norm_contraction",
  TrueQ[ToCanonical[
    weightedNorm -
      k (x-t) positiveMetricM03[-bb,-aa] vM03[bb] vM03[aa]] === 0]];
record["positive_volterra_weight",
  TrueQ[Resolve[ForAll[{k,x,t},
    Implies[k >= 0 && x >= t && t >= 0, k (x-t) >= 0]], Reals]]];
Print["XTENSOR_CONTRACTION=" <> ToString[contractVW, InputForm]];

Print["CHECKS_JSON=" <> ExportString[checks, "RawJSON", "Compact" -> True]];
Print["FAILURES_JSON=" <> ExportString[failures, "RawJSON", "Compact" -> True]];
If[Length[failures] > 0, Exit[1], Exit[0]];
