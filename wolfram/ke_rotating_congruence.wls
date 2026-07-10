(* KE-FRAME / KE-OBS second-engine lane (REV-R181).

   INDEPENDENT Wolfram computation (no SymPy intermediate is imported) of the
   King-Ellis tilted-congruence frame kinematics on

     ds^2 = -dt^2 + a1^2 dx^2 + a2^2 E^(2 c x) dy^2 + a3^2 E^(2 c x) dz^2

   (c = 1 type V, c = 0 type I) with the group-invariant congruence
   u = Cosh[b] e0 + Sinh[b](c1 e1 + c2 e2 + c3 e3). Certifies:

     1. Frobenius omega[n] = 0; aligned tilt omega[u] = 0 (all orders);
     2. the exact vorticity classification (KE-OBS closed form)
        omega_ab omega^ab = (S^2 Sin[phi]^2/2)
                            (S Cos[phi](H1-H2) - Sqrt[1+S^2] c/a1)^2;
     3. the derived contracted Gauss identity
        R3 = 2 G_ab u^a u^b - (2/3) Theta^2 + sigma^2 + omega^2
        (same projection definition as the SymPy lane) on five
        configurations including two rotating ones;
     4. the tilted-fluid n-frame matter decomposition closed forms;
     5. exact rational anchors at the pinned cross-engine point
        a=(2,3,5), da=(1/2,1/3,1/5), db=1/7, E^b=3/2, x=0.

   House rules: avoid the reserved symbol Gamma (use Chr); wrap Simplify in
   TimeConstrained; return a flat Association whose `checks` are TrueQ
   booleans and whose `anchors` are exact-rational InputForm strings.

   Diagnostic-only: exact frame kinematics on a registered ansatz class; no
   data, geometry, or solver-produced claim. *)

ClearAll["Global`*"];

coords = {t, x, y, z};

metric[c_, lrs_] := DiagonalMatrix[{-1, a1[t]^2,
   If[lrs, a2[t], a2[t]]^2 Exp[2 c x],
   If[lrs, a2[t], a3[t]]^2 Exp[2 c x]}];

chr[g_] := Module[{gi = Inverse[g]},
   Table[Together[(1/2) Sum[gi[[l, k]] (D[g[[k, m]], coords[[n]]]
        + D[g[[k, n]], coords[[m]]] - D[g[[m, n]], coords[[k]]]),
       {k, 4}]], {l, 4}, {m, 4}, {n, 4}]];

riemDn[g_, ch_] := Module[{ru},
   ru[l_, m_, k_, n_] := D[ch[[l, n, m]], coords[[k]]]
     - D[ch[[l, k, m]], coords[[n]]]
     + Sum[ch[[l, k, p]] ch[[p, n, m]] - ch[[l, n, p]] ch[[p, k, m]], {p, 4}];
   Table[Together[Sum[g[[l, p]] ru[p, m, k, n], {p, 4}]],
     {l, 4}, {m, 4}, {k, 4}, {n, 4}]];

uVec[c_, cv_, lrs_] := {Cosh[b[t]],
   Sinh[b[t]] cv[[1]]/a1[t],
   Sinh[b[t]] cv[[2]] Exp[-c x]/If[lrs, a2[t], a2[t]],
   Sinh[b[t]] cv[[3]] Exp[-c x]/If[lrs, a2[t], a3[t]]};

kinematics[g_, ch_, uu_] := Module[
   {gi = Inverse[g], ud, grad, hmix, vv, om, th, hdn, sg, adn},
   ud = g . uu;
   grad = Table[Together[D[ud[[n]], coords[[m]]]
       - Sum[ch[[l, m, n]] ud[[l]], {l, 4}]], {m, 4}, {n, 4}];
   th = Together[Sum[gi[[m, n]] grad[[m, n]], {m, 4}, {n, 4}]];
   adn = Table[Together[Sum[uu[[m]] grad[[m, n]], {m, 4}]], {n, 4}];
   hmix = Table[KroneckerDelta[m, a] + uu[[m]] ud[[a]], {m, 4}, {a, 4}];
   hdn = g + Transpose[{ud}] . {ud};
   vv = Table[Together[Sum[hmix[[m, a]] hmix[[n, bb]] grad[[m, n]],
       {m, 4}, {n, 4}]], {a, 4}, {bb, 4}];
   om = (vv - Transpose[vv])/2;
   sg = (vv + Transpose[vv])/2 - th/3 hdn;
   <|"theta" -> th, "A" -> adn,
     "omega2" -> Together[Sum[gi[[a, cc]] gi[[bb, dd]] om[[a, bb]] om[[cc, dd]],
        {a, 4}, {bb, 4}, {cc, 4}, {dd, 4}]],
     "sigma2" -> Together[Sum[gi[[a, cc]] gi[[bb, dd]] sg[[a, bb]] sg[[cc, dd]],
        {a, 4}, {bb, 4}, {cc, 4}, {dd, 4}]],
     "omega" -> om, "V" -> vv, "gi" -> gi, "u" -> uu, "ud" -> ud|>];

hyper[e_] := Together[e /. {Cosh[b[t]] -> Sqrt[1 + SS^2], Sinh[b[t]] -> SS,
    Derivative[1][b][t] -> db}];

simp[e_] := TimeConstrained[Simplify[e], 300, $Failed];

(* ---- configurations ---- *)
gV = metric[1, False]; chV = chr[gV];
gI = metric[0, False]; chI = chr[gI];
gS = metric[cc0, True]; chS = chr[gS];   (* symbolic curvature, LRS *)

kinNormal = kinematics[gV, chV, {1, 0, 0, 0}];
kinAligned = kinematics[gV, chV, uVec[1, {1, 0, 0}, False]];
kinTransverse = kinematics[gV, chV, uVec[1, {0, 1, 0}, False]];
kinObliqueV = kinematics[gV, chV, uVec[1, {3/5, 4/5, 0}, False]];
kinObliqueI = kinematics[gI, chI, uVec[0, {3/5, 4/5, 0}, False]];
kinGeneral = kinematics[gS, chS,
   uVec[cc0, {Cos[phi], Sin[phi] Cos[psi], Sin[phi] Sin[psi]}, True]];

omegaNormalZero = TrueQ[simp[kinNormal["omega"]] === ConstantArray[0, {4, 4}]];
omegaAlignedZero = TrueQ[simp[hyper[kinAligned["omega2"]]] === 0];

(* ---- KE-OBS closed form ---- *)
H1 = Derivative[1][a1][t]/a1[t]; H2 = Derivative[1][a2][t]/a2[t];
closed = (SS^2 Sin[phi]^2/2) (SS Cos[phi] (H1 - H2)
     - Sqrt[1 + SS^2] cc0/a1[t])^2;
closedResidual = simp[FullSimplify[hyper[kinGeneral["omega2"]] - closed,
    Assumptions -> {a1[t] > 0, a2[t] > 0, Element[{phi, psi, SS, db}, Reals]}]];
closedFormMatch = TrueQ[closedResidual === 0];
typeIOblique = TrueQ[simp[(closed /. cc0 -> 0)
      - SS^4 Sin[phi]^2 Cos[phi]^2 (H1 - H2)^2/2] === 0];
obliqueIRotates = TrueQ[simp[hyper[kinObliqueI["omega2"]]] =!= 0];

(* ---- derived contracted Gauss identity (same projection definition) ---- *)
gaussResidual[g_, ch_, kin_] := Module[
   {gi = kin["gi"], uu = kin["u"], rdn, hup, rr, trV, trVV, guu, ric, rs, gein},
   rdn = riemDn[g, ch];
   hup = Table[gi[[a, bb]] + uu[[a]] uu[[bb]], {a, 4}, {bb, 4}];
   rr = Sum[hup[[m, k]] hup[[n, l]] rdn[[m, n, k, l]],
      {m, 4}, {n, 4}, {k, 4}, {l, 4}];
   trV = Sum[hup[[a, bb]] kin["V"][[a, bb]], {a, 4}, {bb, 4}];
   trVV = Sum[hup[[a, cc2]] hup[[bb, dd]] kin["V"][[a, dd]] kin["V"][[cc2, bb]],
      {a, 4}, {bb, 4}, {cc2, 4}, {dd, 4}];
   ric = Table[Sum[gi[[k, l]] rdn[[k, m, l, n]], {k, 4}, {l, 4}], {m, 4}, {n, 4}];
   rs = Sum[gi[[m, n]] ric[[m, n]], {m, 4}, {n, 4}];
   gein = ric - rs/2 g;
   guu = Sum[gein[[m, n]] uu[[m]] uu[[n]], {m, 4}, {n, 4}];
   Together[(rr + trVV - trV^2)
     - (2 guu - (2/3) kin["theta"]^2 + kin["sigma2"] + kin["omega2"])]];

gaussChecks = Association[Map[
    (#[[1]] -> TrueQ[simp[hyper[gaussResidual @@ #[[2]]]] === 0]) &,
    {"gauss_v_normal" -> {gV, chV, kinNormal},
     "gauss_v_aligned" -> {gV, chV, kinAligned},
     "gauss_v_transverse" -> {gV, chV, kinTransverse},
     "gauss_v_oblique" -> {gV, chV, kinObliqueV},
     "gauss_i_oblique" -> {gI, chI, kinObliqueI}}]];

(* ---- tilted-fluid n-frame matter decomposition (transverse config) ---- *)
matterChecks = Module[{uu, ud, tmn, nup, ndn, gi, rhon, hnmix, qn, q2},
   uu = kinTransverse["u"]; ud = kinTransverse["ud"]; gi = kinTransverse["gi"];
   tmn = (rho + w rho) Transpose[{ud}] . {ud} + w rho gV;
   nup = {1, 0, 0, 0}; ndn = gV . nup;
   hnmix = Table[KroneckerDelta[m, a] + nup[[m]] ndn[[a]], {m, 4}, {a, 4}];
   rhon = Sum[tmn[[m, n]] nup[[m]] nup[[n]], {m, 4}, {n, 4}];
   qn = Table[-Sum[hnmix[[m, a]] tmn[[m, n]] nup[[n]], {m, 4}, {n, 4}], {a, 4}];
   q2 = Sum[gi[[a, bb]] qn[[a]] qn[[bb]], {a, 4}, {bb, 4}];
   <|"rho_n_form" -> TrueQ[simp[rhon
         - rho (Cosh[b[t]]^2 + w Sinh[b[t]]^2)] === 0],
     "q_n_magnitude" -> TrueQ[simp[q2
         - ((1 + w) rho Cosh[b[t]] Sinh[b[t]])^2] === 0],
     "u_frame_trivial" -> TrueQ[simp[Sum[tmn[[m, n]] uu[[m]] uu[[n]],
          {m, 4}, {n, 4}] - rho] === 0]|>];

(* ---- structure constants: type V triad Lie brackets + Jacobi ---- *)
structChecks = Module[{X, lie, cst, ok, jac},
   X = {{1, 0, 0}, {0, Exp[-x], 0}, {0, 0, Exp[-x]}};
   lie[u_, v_] := Table[Sum[u[[m]] D[v[[k]], {x, y, z}[[m]]]
        - v[[m]] D[u[[k]], {x, y, z}[[m]]], {m, 3}], {k, 3}];
   cst = Table[KroneckerDelta[k, bb] {1, 0, 0}[[cc2]]
      - KroneckerDelta[k, cc2] {1, 0, 0}[[bb]], {k, 3}, {bb, 3}, {cc2, 3}];
   ok = And @@ Flatten[Table[
       simp[lie[X[[bb]], X[[cc2]]] - Sum[cst[[k, bb, cc2]] X[[k]], {k, 3}]]
         === {0, 0, 0}, {bb, 3}, {cc2, 3}]];
   jac = And @@ Flatten[Table[
       Sum[cst[[k, bb, cc2]] cst[[dd, ee, k]] + cst[[k, cc2, ee]] cst[[dd, bb, k]]
         + cst[[k, ee, bb]] cst[[dd, cc2, k]], {k, 3}] === 0,
       {dd, 3}, {bb, 3}, {cc2, 3}, {ee, 3}]];
   <|"commutators_match_type_v" -> TrueQ[ok], "jacobi" -> TrueQ[jac]|>];

(* ---- exact rational anchors at the pinned cross-engine point ---- *)
anchorSubs = {Derivative[1][a1][t] -> 1/2, Derivative[1][a2][t] -> 1/3,
   Derivative[1][a3][t] -> 1/5, Derivative[1][b][t] -> 1/7,
   Cosh[b[t]] -> 13/12, Sinh[b[t]] -> 5/12,
   a1[t] -> 2, a2[t] -> 3, a3[t] -> 5, x -> 0};

anchorRow[kin_] := Module[{gi = kin["gi"], a2v},
   a2v = Sum[gi[[a, bb]] kin["A"][[a]] kin["A"][[bb]], {a, 4}, {bb, 4}];
   <|"theta" -> ToString[InputForm[Together[kin["theta"] //. anchorSubs]]],
     "omega2" -> ToString[InputForm[Together[kin["omega2"] //. anchorSubs]]],
     "sigma2" -> ToString[InputForm[Together[kin["sigma2"] //. anchorSubs]]],
     "A2" -> ToString[InputForm[Together[a2v //. anchorSubs]]]|>];

<|
  "schema" -> "htt.egs3.ke_frame.wolfram.v1",
  "wolfram_version" -> ToString[InputForm[$Version]],
  "closed_form" -> "omega_ab omega^ab = (S^2 Sin[phi]^2/2)(S Cos[phi](H1-H2) - Sqrt[1+S^2] c/a1)^2",
  "gauss_identity" -> "R3 = 2 G_uu - (2/3) Theta^2 + sigma^2 + omega^2 (projection-definition as stated)",
  "checks" -> Join[<|
      "omega_normal_zero_frobenius" -> omegaNormalZero,
      "omega_aligned_zero" -> omegaAlignedZero,
      "ke_obs_closed_form" -> closedFormMatch,
      "type_i_oblique_form" -> typeIOblique,
      "type_i_oblique_rotates" -> obliqueIRotates|>,
    gaussChecks, matterChecks, structChecks],
  "anchors" -> <|
    "normal" -> anchorRow[kinNormal],
    "aligned" -> anchorRow[kinAligned],
    "transverse" -> anchorRow[kinTransverse]|>
|>
