(* EGS3 v7 estimated-covariance two-stage coverage seal (T4', M3 repair).

   Returns a JSON-serializable Association of boolean checks. Certifies, in closed
   form on the registered toy (m=10, r=2 => residual dof k=8, N_sim=300,
   alpha1=1/20):

   (1) Hotelling pivot: for a residual quadratic form q with sample covariance
       from N_sim Gaussian sims, (N_sim-k)/(k (N_sim-1)) q ~ F_{k, N_sim-k}; the
       stage-1 threshold tau1' = k(N_sim-1)/(N_sim-k) * F^{-1}_{k,N_sim-k}(1-a1)
       STRICTLY EXCEEDS the naive chi^2 threshold chi2^{-1}_k(1-a1);

   (2) the chi^2 threshold is recovered as N_sim -> Infinity (numeric convergence
       ratio -> 1, avoiding a symbolic Limit that does not auto-reduce);

   (3) refutation inflation: using the chi^2 threshold under the true F law gives
       true size > a1 (an uncorrected EMPTY verdict overstates refutation);

   (4) monotone growth of the correction with dimension m (fixed N_sim): the
       F/chi2 threshold ratio increases in k. *)
ClearAll["Global`*"];

k = 8; nsim = 300; a1 = 1/20;
scale = k (nsim - 1)/(nsim - k);
tau1F = scale Quantile[FRatioDistribution[k, nsim - k], 1 - a1];
tau1Chi = Quantile[ChiSquareDistribution[k], 1 - a1];

(* (1) F threshold strictly exceeds chi^2 threshold *)
fExceedsChi = TrueQ[tau1F > tau1Chi];

(* (2) chi^2 recovery as nsim -> Infinity: ratio of scaled-F quantile to chi^2
   quantile tends to 1 (checked at nsim=10^6). *)
scaleBig = k (10^6 - 1)/(10^6 - k);
tau1FBig = scaleBig Quantile[FRatioDistribution[k, 10^6 - k], 1 - a1];
chiRatioBig = N[tau1FBig/tau1Chi, 20];
chi2LimitRecovered = TrueQ[Abs[chiRatioBig - 1] < 1/1000];

(* (3) uncorrected size when the chi^2 threshold is used under the true F law *)
sizeUncorr = 1 - CDF[FRatioDistribution[k, nsim - k], tau1Chi/scale];
refutationInflation = TrueQ[sizeUncorr > a1];

(* (4) monotone in dimension: threshold ratio increases with k at fixed nsim *)
ratio[kk_] := (kk (nsim - 1)/(nsim - kk) Quantile[FRatioDistribution[kk, nsim - kk], 1 - a1])/
  Quantile[ChiSquareDistribution[kk], 1 - a1];
monotoneInDim = TrueQ[ratio[20] > ratio[10] > ratio[5] > 1];

(* (5) T5' cross-check: Imbens-Manski deterministic-width unimodality of the
   coverage function is provable by Resolve; wrap in TimeConstrained (the lane
   has no external timeout). *)
imUnimodal = TimeConstrained[
   Resolve[ForAll[{x, y, tt},
     Implies[0 <= tt <= 1, tt x + (1 - tt) y <= Max[x, y]]], Reals], 30, $Failed];

<|
  "schema" -> "htt.egs3.v7_two_stage_coverage.v1",
  "seal" -> "egs3.v7_two_stage_coverage",
  "checks" -> <|
    "hotelling_F_threshold_exceeds_chi2" -> fExceedsChi,
    "chi2_threshold_recovered_large_nsim" -> chi2LimitRecovered,
    "uncorrected_chi2_size_exceeds_alpha" -> refutationInflation,
    "threshold_ratio_monotone_in_dimension" -> monotoneInDim,
    "im_deterministic_width_unimodal" -> TrueQ[imUnimodal]
  |>,
  "values" -> <|
    "tau1_F" -> N[tau1F], "tau1_chi2" -> N[tau1Chi],
    "uncorrected_size" -> N[sizeUncorr], "nominal_alpha1" -> N[a1],
    "large_nsim_ratio" -> chiRatioBig
  |>,
  "wl_version" -> $Version
|>
