(* Independent CAS-04 Wolfram Engine + xAct finite-component verification. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
Print["ENGINE_VERSION=", System`$Version];
Print["XACT_XTENSOR_VERSION=", xAct`xTensor`$Version];

DefManifold[CAS04M, 4, {a, b, d, e}];
DefMetric[-1, gg[-a, -b], CD, {";", "[Del]"}];
DefTensor[tt[b, -d], CAS04M];
DefTensor[uu[b], CAS04M];
DefTensor[ee[], CAS04M];
DefTensor[pp[], CAS04M];

sameZero[x_] := Module[{expanded = Expand[x]},
  If[expanded === 0, Return[True]];
  expanded = Expand[ExpandCovD[expanded]];
  If[expanded === 0, Return[True]];
  TrueQ[ToCanonical[expanded] === 0]
];
all = <||>;
details = <||>;

(* xAct performs the covariant Leibniz derivative of the eigen-residual.
   The subsequent rest-frame projection is independently checked below. *)
eigResidual = tt[b, -d] uu[d] + ee[] uu[b];
eigExpanded = CD[-a][tt[b, -d]] uu[d] + tt[b, -d] CD[-a][uu[d]] +
  CD[-a][ee[]] uu[b] + ee[] CD[-a][uu[b]];
eigLeibniz = sameZero[CD[-a][eigResidual] - eigExpanded];
projLeibniz = sameZero[(gg[b, -e] + uu[b] uu[-e])
  (CD[-a][eigResidual] - eigExpanded)];

Clear[energy, p1, p2, p3, cc, de, d00, d10, d20, d30, v1, v2, v3];
press = {p1, p2, p3};
gap = energy + press;
tmix = DiagonalMatrix[Join[{-energy}, press]];
restu = {1, 0, 0, 0};
du = {0, v1, v2, v3};
dt = Array[Unique["dt"] &, {4, 4}];
dt[[All, 1]] = {d00, d10, d20, d30};
derivativeResidual = dt.restu + (tmix + energy IdentityMatrix[4]).du + de restu;
restProjected = Rest[derivativeResidual];
ds = {d10, d20, d30};
vSolution = -ds/gap;
projectedIdentity = And @@ (TrueQ /@ (Simplify[restProjected /. Thread[{v1, v2, v3} -> vSolution]] == ConstantArray[0, 3]));
sourceProjection = TrueQ[Rest[dt.restu] === ds];
normalizationDerivative = TrueQ[du[[1]] == 0];
all["CAS-04-C01"] = eigLeibniz && projLeibniz && projectedIdentity && sourceProjection && normalizationDerivative;
details["C01"] = <|"xact_eigen_leibniz" -> eigLeibniz,
  "xact_projected_leibniz" -> projLeibniz,
  "rest_projected_gap_solution" -> projectedIdentity,
  "normalization_rest_time_derivative_zero" -> normalizationDerivative|>;

(* Independent 4 x 3 Euclidean orthogonal decomposition. *)
q = Array[Unique["q"] &, {4, 3}];
sp = q[[2 ;; 4, All]];
theta = Tr[sp];
sym = (sp + Transpose[sp])/2;
sigma = sym - theta IdentityMatrix[3]/3;
w = (sp - Transpose[sp])/2;
omega = {w[[2, 3]], w[[3, 1]], w[[1, 2]]};
aa = cc q[[1, All]];
frobsq[m_] := Total[Flatten[m^2]];
ortho = TrueQ[Expand[theta^2/3 + frobsq[sigma] + frobsq[w] +
  Total[aa^2]/cc^2 - frobsq[q]] == 0];
vort = TrueQ[Expand[frobsq[w] - 2 Total[omega^2]] == 0];
cross = {{0, -omega[[3]], omega[[2]]},
  {omega[[3]], 0, -omega[[1]]}, {-omega[[2]], omega[[1]], 0}};
orientation = TrueQ[Expand[w + cross] == ConstantArray[0, {3, 3}]];
dd = Array[Unique["D"] &, {4, 3}];
qRule = Flatten[Table[q[[i, j]] -> -cc dd[[i, j]]/gap[[j]], {i, 4}, {j, 3}]];
rateEq = TrueQ[Together[(frobsq[q] - cc^2 Sum[dd[[i, j]]^2/gap[[j]]^2,
    {i, 4}, {j, 3}]) /. qRule] == 0];
all["CAS-04-C02"] = ortho && vort && orientation && rateEq;
details["C02"] = <|"orthogonal_decomposition" -> ortho,
  "vorticity_norm" -> vort, "derivative_first_orientation" -> orientation,
  "signed_gap_rate_identity" -> rateEq|>;

(* Exact signed-gap SOS, reduced to a universally quantified scalar term.
   A finite sum of these three nonnegative column terms gives the bound. *)
Clear[gapOne, del, z, cOne];
term = z^2 (gapOne^2 - del^2)/(del^2 gapOne^2);
oneTermIdentity = TrueQ[Together[z^2/del^2 - z^2/gapOne^2 - term] == 0];
positiveTerm = TrueQ[Resolve[ForAll[{gapOne, del, z},
  Implies[del > 0 && gapOne^2 >= del^2, term >= 0]], Reals]];
equalityTerm = TrueQ[Resolve[ForAll[{gapOne, del, z},
  Implies[del > 0 && gapOne^2 >= del^2,
   Equivalent[z^2 (gapOne^2 - del^2) == 0,
    z == 0 || gapOne^2 == del^2]]], Reals]];
signedCase = TrueQ[Simplify[term /. {gapOne -> -2, del -> 1, z -> 3}] == 27/4];
all["CAS-04-C03"] = oneTermIdentity && positiveTerm && equalityTerm && signedCase;
details["C03"] = <|"sos_term_identity" -> oneTermIdentity,
  "universal_nonnegative_term" -> positiveTerm,
  "universal_zero_iff_support_or_minimal_gap" -> equalityTerm,
  "negative_gap_diagnostic" -> signedCase|>;

(* xAct differentiates the contravariant perfect-fluid tensor. *)
fluid = (ee[] + pp[]) uu[a] uu[b] + pp[] gg[a, b];
fluidExpanded = (CD[-a][ee[]] + CD[-a][pp[]]) uu[a] uu[b] +
  (ee[] + pp[]) CD[-a][uu[a]] uu[b] +
  (ee[] + pp[]) uu[a] CD[-a][uu[b]] + CD[-a][pp[]] gg[a, b];
fluidLeibniz = sameZero[CD[-a][fluid] - fluidExpanded];
fluidProjLeibniz = sameZero[(gg[-d, -b] + uu[-d] uu[-b])
  (CD[-a][fluid] - fluidExpanded)];
(* In the unit rest frame h^i_b u^b=0 and h^i_b g^{ab}=h^{ia}.
   The projected divergence is (epsilon+p) a_i + D_i p. *)
Clear[energyP, pressure, dp1, dp2, dp3, acc1, acc2, acc3, c2, ded1, ded2, ded3, cs2];
acc = {acc1, acc2, acc3};
gradp = {dp1, dp2, dp3};
gradE = {ded1, ded2, ded3};
euler = (energyP + pressure) acc + gradp;
aSolution = -gradp/(energyP + pressure);
eulerSolve = TrueQ[Simplify[euler /. Thread[acc -> aSolution]] == {0, 0, 0}];
physicalAccel = c2 aSolution;
barotropic = TrueQ[Simplify[(physicalAccel /. Thread[gradp -> (cs2/c2) gradE]) +
  cs2 gradE/(energyP + pressure)] == {0, 0, 0}];
dust = TrueQ[Simplify[physicalAccel /. {pressure -> 0, dp1 -> 0, dp2 -> 0, dp3 -> 0}] == {0, 0, 0}];
all["CAS-04-C04"] = fluidLeibniz && fluidProjLeibniz && eulerSolve && barotropic && dust;
details["C04"] = <|"xact_fluid_divergence_leibniz" -> fluidLeibniz,
  "xact_projected_divergence_leibniz" -> fluidProjLeibniz,
  "euler_solution" -> eulerSolve, "barotropic_chain_rule" -> barotropic,
  "positive_density_dust_zero" -> dust|>;

Print["CAS04_RESULT_JSON=", StringReplace[ExportString[<|"checks" -> all,
  "details" -> details|>, "RawJSON"], {"\n" -> "", "\t" -> ""}]];
If[And @@ Values[all], Exit[0], Exit[2]];
