(* OMK-REOPEN second-engine lane (REV-R184): symbolic derivation AND
   numeric integration in ONE script, INDEPENDENT of the SymPy lane.

     1. derives the LRS Bianchi III / Kantowski-Sachs field equations from
        ds^2 = -dt^2 + a2^2 (dx^2 + f^2 dy^2) + a1^2 dz^2 (f = e^x / sin x)
        with a comoving perfect fluid p = w rho;
     2. reduces to the expansion-normalized (Sigma, K) system and certifies
        the exact reduction: 1 = Omega + Sigma^2 + K,
        q = (1+3w)(1-K)/2 + (3/2)(1-w) Sigma^2,
        dSigma/dN = -K - (Sigma/2)[(1+3w)K + 3(1-w)(1-Sigma^2)],
        dK/dN = 2K(q + Sigma) -- the curvature source coefficient is
        EXACTLY -1;
     3. certifies the slaving coefficient kappa = -2/(5+3w) = -1/(2+q0)
        (particular-solution algebra) and the exact vacuum fixed point
        (-1/2, 3/4) with dust eigenvalues (-3/2, 0);
     4. NDSolve: metric-level trajectory (Gauss residual monitored) with
        the Sigma/K plateau at kappa, and the deep-N reduced-system run
        approaching the vacuum anchor.

   House rules: avoid the reserved symbol Gamma; TimeConstrained around
   Simplify; flat `checks` of TrueQ booleans; numeric summaries for the
   Python runner to cross-check against the SymPy seal.

   Diagnostic-only: attribution/class-conditional algebra; no data,
   detection, geometry, or posterior claim. *)

ClearAll["Global`*"];

coords = {t, x, y, z};

fieldEqs[f_] := Module[{g, gi, chr, ric, rs, gein, tt, uu, ud},
   g = DiagonalMatrix[{-1, a2[t]^2, a2[t]^2 f^2, a1[t]^2}];
   gi = Inverse[g];
   chr = Table[Together[(1/2) Sum[gi[[l, k]] (D[g[[k, m]], coords[[n]]]
        + D[g[[k, n]], coords[[m]]] - D[g[[m, n]], coords[[k]]]), {k, 4}]],
     {l, 4}, {m, 4}, {n, 4}];
   ric = Table[Together[Sum[
        D[chr[[l, m, n]], coords[[l]]] - D[chr[[l, m, l]], coords[[n]]]
        + Sum[chr[[l, l, s]] chr[[s, m, n]] - chr[[l, n, s]] chr[[s, m, l]],
          {s, 4}], {l, 4}]], {m, 4}, {n, 4}];
   rs = Sum[gi[[m, n]] ric[[m, n]], {m, 4}, {n, 4}];
   gein = ric - rs/2 g;
   uu = {1, 0, 0, 0}; ud = g . uu;
   tt = (rho[t] + wEos rho[t]) Outer[Times, ud, ud] + wEos rho[t] g;
   <|"E" -> (gein - tt), "g" -> g|>];

simp[e_] := TimeConstrained[Simplify[e], 300, $Failed];

sys3 = fieldEqs[Exp[x]];
sysKS = fieldEqs[Sin[x]];

(* invariant components; x-independence *)
ett3 = simp[sys3["E"][[1, 1]]];
exx3 = simp[sys3["E"][[2, 2]]/a2[t]^2];
ezz3 = simp[sys3["E"][[4, 4]]/a1[t]^2];
xfree = TrueQ[simp[D[ett3, x]] === 0 && simp[D[exx3, x]] === 0
    && simp[D[ezz3, x]] === 0];

(* KS mirror: same equations with 1/a2^2 -> -1/a2^2 *)
ettKS = simp[sysKS["E"][[1, 1]] /. x -> Pi/4];
mirror = TrueQ[simp[(ettKS /. a2[t] -> a2m) - (ett3 /. x -> 0 /.
       a2[t] -> a2m) - 2/a2m^2] === 0];

(* reduction: solve evolution for accelerations, normalize *)
red = Module[{dd1, dd2, sol, dH1, dH2, rep, dH1n, dH2n, dHn, qq, dSg, dK,
    elim},
   sol = Solve[{(exx3 /. {a2''[t] -> dd2 a2[t], a1''[t] -> dd1 a1[t]}) == 0,
      (ezz3 /. a2''[t] -> dd2 a2[t]) == 0}, {dd1, dd2}][[1]];
   dH1 = (dd1 /. sol) - (a1'[t]/a1[t])^2;
   dH2 = (dd2 /. sol) - (a2'[t]/a2[t])^2;
   (* SEQUENTIAL passes: the derivative rules insert a2[t], which must
      only be replaced in a second pass *)
   rep1 = {a1'[t] -> HH (1 + 2 SS) a1[t], a2'[t] -> HH (1 - SS) a2[t],
     rho[t] -> 3 HH^2 OM};
   rep2 = a2[t] -> 1/Sqrt[3 KK HH^2];
   dH1n = Expand[Cancel[Together[dH1 /. rep1]] /. rep2];
   dH2n = Expand[Cancel[Together[dH2 /. rep1]] /. rep2];
   dHn = Expand[(dH1n + 2 dH2n)/3];
   qq = Expand[-dHn/HH^2 - 1];
   dSg = Expand[(dH1n - dH2n)/(3 HH^2) - SS dHn/HH^2];
   dK = Expand[KK (-2 (1 - SS) - 2 dHn/HH^2)];
   elim = OM -> 1 - SS^2 - KK;
   <|"q" -> Factor[qq /. elim], "dSg" -> Factor[dSg /. elim],
     "dK" -> Factor[dK /. elim]|>];

qOK = TrueQ[simp[red["q"] - ((1 + 3 wEos) (1 - KK)/2
       + (3/2) (1 - wEos) SS^2)] === 0];
dSgOK = TrueQ[simp[red["dSg"] - (-KK - (SS/2) ((1 + 3 wEos) KK
        + 3 (1 - wEos) (1 - SS^2)))] === 0];
dKOK = TrueQ[simp[red["dK"] - 2 KK (red["q"] + SS)] === 0];
srcMinusOne = TrueQ[simp[(D[red["dSg"], KK] /. {SS -> 0, KK -> 0})] === -1];

(* slaving coefficient: dSg(kappa K, K) = kappa dK at linear order *)
kappaSol = Module[{lhs, rhs2, ks},
   lhs = Coefficient[Expand[red["dSg"] /. SS -> ks KK], KK, 1];
   rhs2 = ks Coefficient[Expand[red["dK"] /. SS -> 0], KK, 1];
   Solve[lhs == rhs2, ks][[1, 1, 2]]];
kappaOK = TrueQ[simp[kappaSol + 2/(5 + 3 wEos)] === 0];

(* vacuum fixed point + dust eigenvalues *)
fp = {SS -> -1/2, KK -> 3/4};
fpOK = TrueQ[simp[red["dSg"] /. fp] === 0 && simp[red["dK"] /. fp] === 0];
eigs = Sort[Eigenvalues[
    (D[{red["dSg"], red["dK"]}, {{SS, KK}}] /. fp /. wEos -> 0)]];
eigOK = TrueQ[eigs === {-3/2, 0}];

(* ---- numeric lanes ---- *)
(* metric-level: near-FLRW, Sigma(0)=0, K(0)=1e-5; Gauss monitored *)
metric = Module[{dd1e, dd2e, sol, ndsol, a1f, a2f, rf, H1f, H2f, Hf, Sgf,
    Kf, gaussf, ratio, plateau, k00 = 1.*^-5, a20, rho0, tEnd = 50.},
   sol = Solve[{(exx3 /. {a2''[t] -> dd2 a2[t], a1''[t] -> dd1 a1[t]}) == 0,
      (ezz3 /. a2''[t] -> dd2 a2[t]) == 0}, {dd1, dd2}][[1]];
   a20 = Sqrt[1/(3 k00)]; rho0 = 3 (1 - k00);
   ndsol = NDSolve[{
      a1''[t] == (dd1 /. sol /. wEos -> 0) a1[t],
      a2''[t] == (dd2 /. sol /. wEos -> 0) a2[t],
      rho'[t] == -(a1'[t]/a1[t] + 2 a2'[t]/a2[t]) rho[t],
      a1[0] == 1, a2[0] == a20, a1'[0] == 1, a2'[0] == a20,
      rho[0] == rho0}, {a1, a2, rho}, {t, 0, tEnd},
     AccuracyGoal -> 12, PrecisionGoal -> 12, MaxSteps -> 200000];
   {a1f, a2f, rf} = {a1, a2, rho} /. First[ndsol];
   H1f[tv_] := a1f'[tv]/a1f[tv]; H2f[tv_] := a2f'[tv]/a2f[tv];
   Hf[tv_] := (H1f[tv] + 2 H2f[tv])/3;
   Sgf[tv_] := (H1f[tv] - H2f[tv])/(3 Hf[tv]);
   Kf[tv_] := 1/(3 a2f[tv]^2 Hf[tv]^2);
   gaussf[tv_] := H2f[tv]^2 + 2 H1f[tv] H2f[tv] - 1/a2f[tv]^2 - rf[tv];
   plateau = Table[Sgf[tv]/Kf[tv], {tv, 35., tEnd, 1.}];
   <|"plateau_ratio_mean" -> Mean[plateau],
     "max_rel_dev" -> Max[Abs[plateau - (-2/5)]]/(2/5),
     "max_gauss_residual" -> Max[Table[Abs[gaussf[tv]], {tv, 0., tEnd,
         tEnd/100.}]]|>];

(* reduced deep-N run to the vacuum anchor (dust) *)
deep = Module[{nds, sf, kf},
   nds = NDSolve[{ss'[n] == (red["dSg"] /. {SS -> ss[n], KK -> kk[n],
         wEos -> 0}),
      kk'[n] == (red["dK"] /. {SS -> ss[n], KK -> kk[n], wEos -> 0}),
      ss[0] == 0, kk[0] == 1.*^-4}, {ss, kk}, {n, 0, 40},
     AccuracyGoal -> 12, PrecisionGoal -> 12];
   {sf, kf} = {ss[40], kk[40]} /. First[nds];
   <|"sigma_final" -> sf, "k_final" -> kf|>];

<|
  "schema" -> "htt.egs3.omega_k_reopening.wolfram.v1",
  "wolfram_version" -> ToString[InputForm[$Version]],
  "checks" -> <|
    "field_equations_homogeneous" -> xfree,
    "ks_mirror_flips_curvature_sign" -> mirror,
    "q_closed_form" -> qOK,
    "dSigma_closed_form" -> dSgOK,
    "dK_closed_form" -> dKOK,
    "curvature_source_coefficient_minus_one" -> srcMinusOne,
    "kappa_minus_2_over_5_plus_3w" -> kappaOK,
    "vacuum_fixed_point" -> fpOK,
    "vacuum_eigenvalues_dust" -> eigOK,
    "metric_plateau_at_kappa" ->
      TrueQ[metric["max_rel_dev"] < 0.01],
    "gauss_monitored_small" ->
      TrueQ[metric["max_gauss_residual"] < 10.^-7],
    "deep_run_approaches_anchor" ->
      TrueQ[Abs[deep["sigma_final"] + 1/2] < 0.02 &&
        Abs[deep["k_final"] - 3/4] < 0.02]|>,
  "metric_lane" -> metric,
  "deep_lane" -> deep
|>
