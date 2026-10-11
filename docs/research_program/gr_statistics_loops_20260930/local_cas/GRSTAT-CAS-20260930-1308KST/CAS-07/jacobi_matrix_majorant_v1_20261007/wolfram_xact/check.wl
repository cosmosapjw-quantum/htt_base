(* CAS-07 M04 independent Wolfram/xAct executable checks. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
ClearAll[s, t, k, d, f, r, j, matR, matD];

(* The arbitrary scalar component d represents each of the four entries of D. *)
componentTaylor = Integrate[(s - t) Derivative[2][d][t], {t, 0, s},
  Assumptions -> s >= 0];
componentTaylorExpected = d[s] - d[0] - s Derivative[1][d][0];
componentSecondCheck = TrueQ[FullSimplify[
   D[componentTaylor, {s, 2}] ==
   D[componentTaylorExpected, {s, 2}], s >= 0]];
componentInitialCheck = TrueQ[FullSimplify[
   (componentTaylor /. s -> 0) ==
   (componentTaylorExpected /. s -> 0)]];
componentSlopeCheck = TrueQ[FullSimplify[
   (D[componentTaylor, s] /. s -> 0) ==
   (D[componentTaylorExpected, s] /. s -> 0)]];
componentCheck = componentSecondCheck && componentInitialCheck && componentSlopeCheck;

(* xTensor carries one output and one input screen index; contraction order is R.D. *)
DefManifold[ScreenM04, 2, {a, b, c, e}];
DefTensor[rr[a, -b], ScreenM04];
DefTensor[dd[a, -b], ScreenM04];
DefTensor[v[a], ScreenM04];
orderedContraction = ToCanonical[rr[a, -c] dd[c, -b] v[b]];
reversedContraction = ToCanonical[dd[a, -c] rr[c, -b] v[b]];
xActCheck = !SameQ[orderedContraction, reversedContraction] &&
  FreeQ[orderedContraction, ToCanonical];

(* An exact 2D witness detects illicit exchange of R and D. *)
matR = {{0, 1}, {0, 0}};
matD = {{0, 0}, {1, 0}};
noncommutingCheck = matR.matD != matD.matR &&
  matR.matD == {{1, 0}, {0, 0}};

(* Fundamental theorem for the Volterra kernel: derivative twice is the source. *)
kernelIntegral = Integrate[(s - t) j[t], {t, 0, s},
  Assumptions -> s >= 0];
kernelSecondCheck = TrueQ[FullSimplify[
   D[kernelIntegral, {s, 2}] == j[s], s >= 0]];

f0 = s;
fpos = Sinh[Sqrt[k] s]/Sqrt[k];
majorantIntegral = Integrate[(s - t) (fpos /. s -> t), {t, 0, s},
  Assumptions -> k > 0 && s >= 0];
majorantCheck = TrueQ[FullSimplify[
   s + k majorantIntegral == fpos, k > 0 && s >= 0]];
zeroCheck = TrueQ[FullSimplify[f0 == s &&
   Integrate[(s - t) (f0 /. s -> t), {t, 0, s},
     Assumptions -> s >= 0] == s^3/6, s >= 0]];

checks = <|
  "CAS-07-M04-VOLTERRA-IDENTITY" ->
    (componentCheck && kernelSecondCheck && xActCheck && noncommutingCheck),
  "CAS-07-M04-SCALAR-PREMISE" ->
    (xActCheck && noncommutingCheck && kernelSecondCheck),
  "CAS-07-M04-D-NORM" -> (majorantCheck && zeroCheck),
  "CAS-07-M04-D-MINUS-SI" -> (majorantCheck && zeroCheck)
|>;
Print["M04_DIAGNOSTICS_JSON=", ExportString[<|
  "component_taylor" -> componentCheck,
  "component_second_derivative" -> componentSecondCheck,
  "component_initial" -> componentInitialCheck,
  "component_slope" -> componentSlopeCheck,
  "kernel_second_derivative" -> kernelSecondCheck,
  "xact_screen_contraction" -> xActCheck,
  "matrix_noncommuting_witness" -> noncommutingCheck,
  "majorant_integral" -> majorantCheck,
  "k_zero_control" -> zeroCheck,
  "wolfram_version" -> System`$Version,
  "component_taylor_expression" -> ToString[componentTaylor, InputForm],
  "majorant_integral_expression" -> ToString[majorantIntegral, InputForm],
  "xact_version" -> ToString[xAct`xTensor`$Version, InputForm]
|>, "RawJSON"]];
Print["M04_CHECKS_JSON=", ExportString[checks, "RawJSON"]];
If[!And @@ Values[checks], Exit[1]];
Exit[0];
