(* CAS-07-C01, independent Wolfram+xTensor source. Exact real Kc>0, s>=0. *)
ClearAll[Kc, s, t, f, f0, emit];
f[k_, x_] := Sinh[Sqrt[k] x]/Sqrt[k];
f0[x_] := x;

pos = Kc > 0 && s >= 0;
initial = FullSimplify[f[Kc, 0], Kc > 0];
initialDerivative = FullSimplify[D[f[Kc, s], s] /. s -> 0, Kc > 0];
odeResidual = FullSimplify[D[f[Kc, s], {s, 2}] - Kc f[Kc, s], pos];
intervalIntegral = Integrate[(s - t) f[Kc, t], {t, 0, s},
  Assumptions -> pos, GenerateConditions -> True];
integralResidual = FullSimplify[
  Kc intervalIntegral - (f[Kc, s] - s), pos];
rightLimit = Limit[f[Kc, s], Kc -> 0, Direction -> "FromAbove",
  Assumptions -> s >= 0];
limitResidual = FullSimplify[rightLimit - f0[s], s >= 0];
flatInitial = f0[0];
flatDerivative = D[f0[s], s] /. s -> 0;
flatODE = D[f0[s], {s, 2}];
flatIntegral = 0 Integrate[(s - t) f0[t], {t, 0, s}];
flatIntegralResidual = flatIntegral - (f0[s] - s);

Needs["xAct`xTensor`"];
DefManifold[CASLine, 1, {a, b}];
DefMetric[1, g[-a, -b], CD];
DefTensor[scalarF[], CASLine];
(* A nonzero scalar gradient contraction, evaluated with index raising. *)
xtensorBefore = g[a, b] CD[-a][scalarF[]] CD[-b][scalarF[]];
xtensorAfter = ToCanonical[ContractMetric[xtensorBefore]];

checks = <|
  "initial_value" -> TrueQ[initial === 0],
  "initial_derivative" -> TrueQ[initialDerivative === 1],
  "ode" -> TrueQ[odeResidual === 0],
  "integral" -> TrueQ[integralResidual === 0],
  "zero_limit" -> TrueQ[limitResidual === 0],
  "flat_initial" -> TrueQ[flatInitial === 0],
  "flat_derivative" -> TrueQ[flatDerivative === 1],
  "flat_ode" -> TrueQ[flatODE === 0],
  "flat_integral" -> TrueQ[flatIntegralResidual === 0],
  "xtensor_nonzero_input" -> TrueQ[xtensorBefore =!= 0],
  "xtensor_transformed" -> TrueQ[xtensorAfter =!= xtensorBefore],
  "xtensor_equivalent" -> TrueQ[ToCanonical[ContractMetric[xtensorBefore - xtensorAfter]] === 0],
  "xtensor_scalar" -> TrueQ[FreeIndices[xtensorAfter] === {}],
  "xtensor_index_consistency" -> TrueQ[
    xtensorAfter =!= 0 && xtensorAfter =!= xtensorBefore &&
    ToCanonical[ContractMetric[xtensorBefore - xtensorAfter]] === 0 &&
    FreeIndices[xtensorAfter] === {}]
|>;
evidence = <|
  "version" -> System`$Version,
  "xtensor_version" -> ToString[xAct`xTensor`$Version, InputForm],
  "assumptions" -> ToString[pos, InputForm],
  "f" -> ToString[f[Kc, s], InputForm],
  "initial" -> ToString[initial, InputForm],
  "initial_derivative" -> ToString[initialDerivative, InputForm],
  "ode_residual" -> ToString[odeResidual, InputForm],
  "interval_integral" -> ToString[intervalIntegral, InputForm],
  "integral_residual" -> ToString[integralResidual, InputForm],
  "right_limit" -> ToString[rightLimit, InputForm],
  "limit_residual" -> ToString[limitResidual, InputForm],
  "flat_integral_residual" -> ToString[flatIntegralResidual, InputForm],
  "xtensor_before" -> ToString[xtensorBefore, InputForm],
  "xtensor_after" -> ToString[xtensorAfter, InputForm],
  "xtensor_free_indices" -> ToString[FreeIndices[xtensorAfter], InputForm],
  "checks" -> checks,
  "message_list" -> ToString[$MessageList, InputForm]
|>;
Print["CAS_JSON:", ExportString[evidence, "RawJSON"]];
If[And @@ Values[checks], Exit[0], Exit[2]];
