(* KE-DYN second-engine lane (REV-R182): symbolic derivation AND numeric
   integration in ONE script -- the Wolfram-native combined workflow.

   INDEPENDENT of the SymPy lane (no shared intermediates):
     1. derives the off-diagonal rotating tilted system on
          ds^2 = -dt^2 + eta_ij(t) w^i w^j,  w^1 = dx, w^2 = e^{cx} dy,
          w^3 = e^{cx} dz,  eta = [[h11,h12,0],[h12,h22,0],[0,0,h33]]
        with u = (ut, w1, w2 e^{-cx}, 0), ut = Sqrt[1 + h11 w1^2
        + 2 h12 w1 w2 + h22 w2^2] symbolically (Einstein tensor from the
        metric, tilted perfect fluid, per-stream conservation);
     2. certifies the type-I obstruction G_tx = G_ty = 0 SYMBOLICALLY for
        the arbitrary off-diagonal homogeneous type-I metric;
     3. constructs constraint-satisfying rotating initial data with
        FindRoot on {E_tt, E_tx, E_ty} (type V, single oblique stream);
     4. NDSolve integrates the IMPLICIT evolution system {E_xx = 0,
        E_xy = 0, E_yy = 0, E_zz = 0, divT = 0} directly (no manual
        linear solve), MONITORS the three constraints along the solution,
        and evaluates omega_ab omega^ab [u] numerically from the same
        kinematic definitions;
     5. repeats the type-I antipodal-pair development and confirms the
        DYNAMICAL irrotationality (omega^2 = 0 to machine precision).

   House rules: avoid the reserved symbol Gamma; TimeConstrained around
   Simplify; flat `checks` of TrueQ booleans; numeric summaries for the
   Python runner to cross-check against the SymPy seal.

   Diagnostic-only; no data, geometry, or solver-produced sky claim. *)

ClearAll["Global`*"];

coords = {t, x, y, z};

buildSystem[cc_, nStreams_] := Module[
   {ex, g, gi, chr, ric, gein, ut, uu, um, tt, tcons, divT, eqsEvol, cons},
   ex = Exp[cc x];
   g = {{-1, 0, 0, 0},
        {0, h11[t], h12[t] ex, 0},
        {0, h12[t] ex, h22[t] ex^2, 0},
        {0, 0, 0, h33[t] ex^2}};
   gi = Inverse[g];
   chr = Table[Together[(1/2) Sum[gi[[l, k]] (D[g[[k, m]], coords[[n]]]
        + D[g[[k, n]], coords[[m]]] - D[g[[m, n]], coords[[k]]]), {k, 4}]],
     {l, 4}, {m, 4}, {n, 4}];
   ric = Table[Together[Sum[
        D[chr[[l, m, n]], coords[[l]]] - D[chr[[l, m, l]], coords[[n]]]
        + Sum[chr[[l, l, s]] chr[[s, m, n]] - chr[[l, n, s]] chr[[s, m, l]],
          {s, 4}], {l, 4}]], {m, 4}, {n, 4}];
   gein = ric - (1/2) Sum[gi[[m, n]] ric[[m, n]], {m, 4}, {n, 4}] g;
   ut = Sqrt[1 + h11[t] w1[t]^2 + 2 h12[t] w1[t] w2[t] + h22[t] w2[t]^2];
   uu = {ut, w1[t], w2[t]/ex, 0};
   um = {ut, -w1[t], -w2[t]/ex, 0};
   tt = If[nStreams == 1,
     (rho[t] + wEos rho[t]) Outer[Times, g . uu, g . uu]
       + wEos rho[t] g,
     (rho[t]/2 + wEos rho[t]/2) (Outer[Times, g . uu, g . uu]
         + Outer[Times, g . um, g . um]) + wEos rho[t] g];
   tcons = If[nStreams == 1, tt,
     (rho[t]/2 + wEos rho[t]/2) Outer[Times, g . uu, g . uu]
       + (wEos rho[t]/2) g];
   divT = Module[{tud = gi . tcons},
     Table[Together[Sum[D[tud[[m, nu]], coords[[m]]]
         + Sum[chr[[m, m, l]] tud[[l, nu]]
           - chr[[l, m, nu]] tud[[m, l]], {l, 4}], {m, 4}]], {nu, 3}]];
   eqsEvol = {gein[[2, 2]] == tt[[2, 2]], gein[[2, 3]] == tt[[2, 3]],
     gein[[3, 3]] == tt[[3, 3]], gein[[4, 4]] == tt[[4, 4]],
     divT[[1]] == 0, divT[[2]] == 0, divT[[3]] == 0} /. x -> 0;
   cons = ({gein[[1, 1]] - tt[[1, 1]], gein[[1, 2]] - tt[[1, 2]],
      Together[(gein[[1, 3]] - tt[[1, 3]])/ex]}) /. x -> 0;
   <|"evol" -> eqsEvol, "cons" -> cons, "g" -> (g /. x -> 0),
     "gi" -> (gi /. x -> 0), "chr" -> (chr /. x -> 0),
     "u" -> (uu /. x -> 0), "gein" -> gein,
     "gX" -> g, "chrX" -> chr, "uX" -> uu|>];

simp[e_] := TimeConstrained[Simplify[e], 300, $Failed];

(* ---- (2) type-I obstruction: G_tx = G_ty = 0 identically ---- *)
obstruction = Module[{sys = buildSystem[0, 1], gtx, gty},
   gtx = simp[sys["gein"][[1, 2]]];
   gty = simp[sys["gein"][[1, 3]]];
   <|"g_tx_identically_zero" -> TrueQ[gtx === 0],
     "g_ty_identically_zero" -> TrueQ[gty === 0]|>];

(* ---- (3)+(4) developments: numeric LinearSolve rhs (the symbolic
       solution of the 7x7 system explodes -- extract A, b once, solve
       numerically per step) + explicit vector NDSolve ---- *)
stateSyms = {H11, H12, H22, H33, DH11, DH12, DH22, DH33, RHO, W1v, W2v};
stateRep = {h11[t] -> H11, h12[t] -> H12, h22[t] -> H22, h33[t] -> H33,
   h11'[t] -> DH11, h12'[t] -> DH12, h22'[t] -> DH22, h33'[t] -> DH33,
   rho[t] -> RHO, w1[t] -> W1v, w2[t] -> W2v};

makeNumeric[sys_, wEosV_] := Module[
   {unks, resid, Amat, bvec, aF, bF, consF, consExpr},
   unks = {h11''[t], h12''[t], h22''[t], h33''[t],
     rho'[t], w1'[t], w2'[t]};
   resid = (Subtract @@@ sys["evol"]) /. wEos -> wEosV;
   Amat = Table[D[r, u], {r, resid}, {u, unks}] /. stateRep;
   bvec = (-(resid /. Thread[unks -> 0])) /. stateRep;
   aF = Function @@ {stateSyms, Amat};
   bF = Function @@ {stateSyms, bvec};
   (* the second derivatives inside G_tt/G_ti cancel identically (the
      constraints are first-order); Simplify realizes the cancellation *)
   consExpr = Simplify[Together[sys["cons"] /. wEos -> wEosV]];
   If[! FreeQ[consExpr, Derivative[2][_][t]],
     Throw["constraints not first-order after Simplify"]];
   consF = Function @@ {stateSyms, consExpr /. stateRep};
   <|"A" -> aF, "b" -> bF, "cons" -> consF|>];

runDevelopment[cc_, nStreams_, wEosV_, hInit_, tiltInit_, tEnd_] := Module[
   {sys = buildSystem[cc, nStreams], num, rhsN, icRates, found, y0, nds,
    yf, consMax, om2i, om2f, grid, kinNum, dw1s, dw2s},
   num = makeNumeric[sys, wEosV];
   rhsN[s_?(VectorQ[#, NumericQ] &)] := Module[{d},
     d = LinearSolve[num["A"] @@ s // N, num["b"] @@ s // N];
     Join[s[[5 ;; 8]], d[[1 ;; 4]], d[[5 ;; 7]]]];
   found = If[cc == 0 && nStreams == 2,
     {FindRoot[(num["cons"] @@ {hInit[[1]], hInit[[2]], hInit[[3]],
           hInit[[4]], dh11v, 0.05, 1.0, 0.9 hInit[[4]], 0.3,
           tiltInit[[1]], tiltInit[[2]]})[[1]] == 0,
        {dh11v, 0.8}][[1, 2]], 0.05, 1.0},
     {dh11v, dh12v, dh22v} /. FindRoot[
       Thread[(num["cons"] @@ {hInit[[1]], hInit[[2]], hInit[[3]],
           hInit[[4]], dh11v, dh12v, dh22v, 0.9 hInit[[4]], 0.3,
           tiltInit[[1]], tiltInit[[2]]}) == 0],
       {{dh11v, 0.8}, {dh12v, 0.05}, {dh22v, 1.0}}]];
   y0 = N[{hInit[[1]], hInit[[2]], hInit[[3]], hInit[[4]],
     found[[1]], found[[2]], found[[3]], 0.9 hInit[[4]], 0.3,
     tiltInit[[1]], tiltInit[[2]]}];
   nds = NDSolve[{yv'[t] == rhsN[yv[t]], yv[0] == y0}, yv, {t, 0, tEnd},
     AccuracyGoal -> 12, PrecisionGoal -> 12, MaxSteps -> 200000];
   yf = yv /. First[nds];
   grid = Table[yf[tv], {tv, 0., tEnd, tEnd/20.}];
   consMax = Max[Abs[Flatten[Table[num["cons"] @@ s, {s, grid}]]]];
   (* kinematics of the + stream: symbolic grad (x-derivatives taken
      BEFORE x -> 0) numericized once *)
   kinNum = Module[{ud, grad, krep},
     ud = sys["gX"] . sys["uX"];
     grad = (Table[D[ud[[n]], coords[[m]]]
          - Sum[sys["chrX"][[l, m, n]] ud[[l]], {l, 4}], {m, 4}, {n, 4}])
       /. x -> 0;
     krep = Join[stateRep, {w1'[t] -> dw1s, w2'[t] -> dw2s}];
     Function @@ {Join[stateSyms, {dw1s, dw2s}],
       {sys["g"] /. stateRep, sys["gi"] /. stateRep,
        sys["u"] /. stateRep, grad /. krep}}];
   om2At[s_] := Module[{d = rhsN[s], gm, gi, uu, gr, ud2, hmix, vv, om},
     {gm, gi, uu, gr} = kinNum @@ Join[s, {d[[10]], d[[11]]}] // N;
     ud2 = gm . uu;
     hmix = IdentityMatrix[4] + Outer[Times, uu, ud2];
     vv = Transpose[hmix] . gr . hmix;
     om = (vv - Transpose[vv])/2;
     Sum[gi[[a, c]] gi[[b, d2]] om[[a, b]] om[[c, d2]],
       {a, 4}, {b, 4}, {c, 4}, {d2, 4}]];
   om2i = om2At[grid[[1]]];
   om2f = om2At[grid[[-1]]];
   <|"max_constraint_residual" -> consMax,
     "omega2_initial" -> om2i, "omega2_final" -> om2f,
     "rho_final" -> grid[[-1, 9]],
     "tilt_final" -> {grid[[-1, 10]], grid[[-1, 11]]}|>];

devV = runDevelopment[1, 1, 0, {1, 0, 13/10, 17/10}, {3/100, 1/25}, 1];
devIPair = runDevelopment[0, 2, 0, {1, 0, 13/10, 17/10}, {3/100, 1/25}, 1];

<|
  "schema" -> "htt.egs3.ke_dynamics.wolfram.v1",
  "wolfram_version" -> ToString[InputForm[$Version]],
  "checks" -> <|
    "type_i_g_tx_identically_zero" ->
      TrueQ[obstruction["g_tx_identically_zero"]],
    "type_i_g_ty_identically_zero" ->
      TrueQ[obstruction["g_ty_identically_zero"]],
    "type_v_constraints_preserved" ->
      TrueQ[devV["max_constraint_residual"] < 10.^-6],
    "type_v_omega2_positive" ->
      TrueQ[devV["omega2_initial"] > 0 && devV["omega2_final"] > 0],
    "type_v_nonvacuum" -> TrueQ[devV["rho_final"] > 0],
    "type_i_pair_constraints_preserved" ->
      TrueQ[devIPair["max_constraint_residual"] < 10.^-6],
    "type_i_pair_dynamically_irrotational" ->
      TrueQ[Abs[devIPair["omega2_initial"]] < 10.^-20 &&
        Abs[devIPair["omega2_final"]] < 10.^-20]|>,
  "type_v_development" -> devV,
  "type_i_pair_development" -> devIPair
|>
