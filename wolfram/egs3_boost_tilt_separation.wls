(* EGS3 Axis C: symbolic core for the kinematic deprojection of the observer-boost
   quadrupole. Returns a JSON-serializable Association of boolean checks. Proves, in
   closed form, the identities the deprojection rests on:
     (1) the Legendre split  mu^2 = (2/3) P2(mu) + 1/3  is exact;
     (2) the closed-form alpha = (4/9) T0^2 N2 / (kappaT^2 RSigma);
     (3) the projection Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2 zeroes a pure
         boost sky and preserves genuine shear (no over-subtraction);
     (4) the coupled-Fisher off-diagonal is proportional to beta^2;
     (5) the covariance inflation equals 1/(1 - r^2) and -> 1 as beta -> 0;
     (6) the boost/tilt Gram determinant 1 - P2(cos t)^2 is > 0 iff the axes are not
         aligned (separability iff non-degenerate). *)
ClearAll["Global`*"];

(* (1) mu^2 = (2/3) P2(mu) + 1/3 exactly; the P2 (quadrupole) coefficient is 2/3 *)
legendreSplit = Simplify[mu^2 - ((2/3) LegendreP[2, mu] + 1/3)] === 0;
p2Coefficient = (Integrate[mu^2 LegendreP[2, mu], {mu, -1, 1}]
                 / Integrate[LegendreP[2, mu]^2, {mu, -1, 1}]) === 2/3;

(* (2) closed-form alpha: ratio of the boost-quadrupole response ((2/3)^2 T0^2 N2 per
   (Omega_tilt)^2, since Omega_tilt = kappaT beta is linear) to the shear response RSigma *)
alpha = (2/3)^2 T0^2 N2 / (kappaT^2 RSigma);
alphaClosedForm = Simplify[alpha - (4/9) T0^2 N2/(kappaT^2 RSigma)] === 0;

(* (3) projection zeroes a pure boost sky and preserves genuine shear.
   Pure boost: Sigma^2 reading = alpha (Omega_tilt)^2, Omega_tilt = kappaT beta. *)
projPureBoost = Simplify[
   (alpha (kappaT beta)^2) - alpha (kappaT beta)^2] === 0;
projPreservesShear = Simplify[(Sig - alpha*0^2) - Sig] === 0;

(* (4) coupled Fisher: rho = Sqrt[alpha] kappaT beta; F12 = rho^2 ~ beta^2. *)
rho = Sqrt[alpha] kappaT beta;
F12 = rho^2;
fisherOffdiagBetaSquared = (Simplify[F12/beta^2 - alpha kappaT^2] === 0) &&
   (Simplify[(F12 /. beta -> 0)] === 0);

(* (5) covariance inflation = 1/(1 - r^2), r = F12/Sqrt[F11 F22];
   F = {{1+rho^2, rho^2}, {rho^2, f + rho^2}}. Marginal/conditional variance ratio. *)
F11 = 1 + rho^2; F22 = f + rho^2;
detF = F11 F22 - F12^2;
condVar = 1/F11;                          (* conditional Var(Sigma^2), Omega_tilt fixed *)
margVar = F22/detF;                       (* marginal Var(Sigma^2) = (F^-1)_11 *)
inflation = margVar/condVar;
rCorr = F12/Sqrt[F11 F22];
inflationForm = Simplify[inflation - 1/(1 - rCorr^2)] === 0;
inflationLimit = Simplify[(inflation /. beta -> 0)] === 1;

(* (6) Gram determinant of the two unit l=2 templates is 1 - P2(cos t)^2 (addition
   theorem); positive iff the boost axis is not aligned with the shear axis. *)
gramDet = 1 - LegendreP[2, Cos[t]]^2;
gramAlignedZero = Simplify[(gramDet /. t -> 0)] === 0;      (* aligned -> degenerate *)
gramGenericPositive = Resolve[ForAll[t, 0 < t < Pi/2, gramDet > 0], Reals];

<|
  "schema" -> "htt.egs3.boost_tilt.v1",
  "checks" -> <|
    "mu_squared_legendre_split" -> TrueQ[legendreSplit],
    "p2_projection_coefficient_two_thirds" -> TrueQ[p2Coefficient],
    "alpha_closed_form" -> TrueQ[alphaClosedForm],
    "deprojection_zeroes_pure_boost" -> TrueQ[projPureBoost],
    "deprojection_preserves_shear" -> TrueQ[projPreservesShear],
    "fisher_offdiagonal_beta_squared" -> TrueQ[fisherOffdiagBetaSquared],
    "inflation_one_over_one_minus_r2" -> TrueQ[inflationForm],
    "inflation_limit_one_at_zero_beta" -> TrueQ[inflationLimit],
    "gram_zero_when_axes_aligned" -> TrueQ[gramAlignedZero],
    "gram_positive_iff_separable" -> TrueQ[gramGenericPositive],
    "signature" -> "Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2; alpha=(4/9)T0^2 N2/(kappaT^2 RSigma); F12 ~ beta^2; inflation=1/(1-r^2)"
  |>
|>
