# Beyond-FLRW kinematic measurement: derivation and computational contract

Baseline: `fb6ae9f21585e194ef29dabc91d79a529e0ac57e`. Owner: HTT inference. Scope: the existing CF4 conditional experiment, its direct kinematic confidence images, and a finite depth response. Source identities and owned-input limits are in REVIEW/kinematic_sources.md and REVIEW/owned_inputs.md. This is one integrated ten-stage study, with the R and C obligations tracked separately within each numbered stage.

## 1. Local quantities and what the experiment observes

Use metric (-,+,+,+), U.U=-c^2, sourceward spatial unit n, and H=Theta/3>0. With physical proper time, the congruence derivative is

$$
\nabla_b U_a={\Theta\over3}h_{ab}+\sigma_{ab}+\omega_{ab}
-{1\over c^2}U_b A_a.
$$

The leading directional Hubble coefficient is

$$
\mathfrak H(n)=H-{A_an^a\over c}+\sigma_{ab}n^an^b,
\quad D_L(z,n)={cz\over\mathfrak H_o(n)}+O(z^2).
$$

The antisymmetric omega term vanishes in this symmetric contraction. This leading coefficient follows Heinesen2010.06534v2 with c restored. It is a local, congruence-specific statement. Its use at finite depth requires a controlled higher-order expansion and an appropriate smoothing scale. A sourceward direction under incoming k=E(u-e) is essential to the acceleration sign. The observer-boost transformations in Maartens2312.09875v3 distinguish the matter congruence from the observer; changing redshift labels alone is not a complete boost of a distance experiment.

The retained CF4 experiment has y_m in R^32 and alpha=(V3,dH3,kappa5),

$$
y_m=X_m\alpha+\epsilon_m,\quad \epsilon_m\sim N(0,C_m),
\quad \eta_i=M_{m,i}\gamma_m+g(z_i)n_i\cdot V+n_i\cdot d_H+
\sum_A\kappa_A E_A:n_in_i.
$$

The five E_A are Frobenius orthonormal, in the R58 order diag(1,-1,0)/sqrt2, diag(1,1,-2)/sqrt6, xy/xz/yz symmetric offdiagonals divided by sqrt2. C_m includes the inherited full measurement and z=0 linear LCDM cosmic covariance. The seven operators transform the same selected 35,970 groups, so model uncertainty is a confidence-set union, not a product of seven likelihoods.

Under the declared first-order constant-response bridge,

$$
s=\sigma/H,\quad a=A/(cH),\quad \beta=V/c,\quad
d_H=-a+d_{cal},\quad \kappa=s+q_{cal}.
$$

The retained32D operator drops all four monopole rows. Thus this experiment measures normalized angular quantities, not an independently calibrated absolute H or Theta. It has no vorticity column. Free calibration leaves individual s and a unidentified; a bounded calibration body supplies conditional partial identification. No geometry-specific field equation is imposed.

## 2. One confidence set and its physical images

For a fixed full-rank Gaussian experiment, alpha_hat has covariance V and

$$
E_m(t)=\{\alpha:(\alpha-\hat\alpha)^T V^{-1}(\alpha-\hat\alpha)\le t\},
\quad t=\chi^2_{11}(.95).
$$

Let xi=(d_cal,q_cal) have a deterministic angular-calibration bound

$$
\xi^T G\xi\le\rho^2,\quad G=\operatorname{diag}(I_3/3,2I_5/15).
$$

This equals the full-sky mean square of b(n)=d_cal.n+Q_cal:nn. Its magnitude RMS is (5/ln10)rho. It is not an empirically estimated stochastic covariance. The physical set is the affine image of E_m times this calibration body, and the model-robust set is its finite union over m.

If the true apparent alpha lies in E_m and the true calibration lies in the stated body, every physical functional of the true state lies in its image. Thus all reported image intervals share the same simultaneous95% event. Images can overcover. Taking a scalar image never changes the cutoff to chi-square1. A separate marginal5D shear confidence set uses chi-square5 and is reported separately; it is not the same simultaneous object.

For a full-row-rank linear projection L, the image of E is exactly the ellipsoid with center L alpha_hat and covariance LVL^T, using the SAME cutoff t. A projected witness x lifts to alpha_hat+V L^T(LVL^T)^-1(x-L alpha_hat). This is a minimum-Mahalanobis lift; unused conditional coordinates do not consume radius.

## 3. Global quadratic confidence images

For f(alpha)=alpha^T M alpha+l^T alpha+c, write alpha=h+Au with A=sqrt(t)chol(V), ||u||<=1. Then

$$
f=u^TBu+2b^Tu+c_0,\quad B=A^TMA,\quad b=A^T(Mh+l/2).
$$

For lambda>=0 and B+lambda I positive definite, completion of the square gives

$$
f(u)-[c_0-\lambda-b^T(B+\lambda I)^{-1}b]
=v^T(B+\lambda I)v+\lambda(1-||u||^2)\ge0,
\qquad v=u+(B+\lambda I)^{-1}b.
$$

Therefore the bracket is a global lower bound. At a minimizer, (B+lambda I)u=-b, lambda>=0, B+lambda I>=0, and lambda(1-||u||²)=0. For singular B+lambda I the same result uses a pseudoinverse when b is in its range, with a nullspace component supplying the active radius (the hard case). Maximization applies this construction to -f.

The implementation diagonalizes B and solves a scalar secular equation, handles PSD interior and hard cases, produces a feasible witness, and exposes the dual enclosure/gap. A small positive shift makes the numerical dual nonsingular. These are floating primal/dual certificates, not directed-rounding interval proofs. Failure to meet the declared numerical gap raises an error.

This computes globally characterized intervals for |beta|², |a|², ||s||², and beta.a=-V.dH/c at zero added calibration. For the last quantity M_{i,i+3}=M_{i+3,i}=-1/(2c), preserving the velocity–dipole covariance. The coordinate box comparator uses the enclosing supports h_i +/-sqrt(t V_ii) from the SAME joint ellipsoid; it quantifies geometry lost by replacing that ellipsoid by a box, without inventing an independent-factor likelihood.

## 4. Norms, physical calibration and directional expansion

If r_- and r_+ are the minimum and maximum Euclidean norms on a projected ellipsoid, adding a Euclidean radius b gives [max(0,r_--b),r_++b]. Both endpoints follow by radial alignment, with cancellation possible when b>=r_-. Hence

$$
\Sigma={||s||\over\sqrt6}\in
\left[{\max(0,r_-^{(\kappa)}-\sqrt{15/2}\rho)\over\sqrt6},
{r_+^{(\kappa)}+\sqrt{15/2}\rho\over\sqrt6}\right],
$$

and |a| uses b=sqrt3 rho. For

$$
\mathcal A_H=\sqrt{\langle(\mathfrak H/H-1)^2\rangle}
=\sqrt{|a|^2/3+2||s||^2/15},
$$

the weighted angular ellipsoid is G^1/2(dH,kappa), and b=rho. This is an RMS of directional expansion, not a positive-definite total measure of all departures from FLRW: omega and H are not represented.

For beta.a at finite calibration, the implemented rigorous geometric outer enclosure adds +/-sqrt3 rho beta_max to the exact zero-calibration interval. It is conservative because the extremum of beta.a and the largest ||beta|| need not occur at the same alpha. That finite-budget interval is not labeled sharp.

For each direction n, let u_n=(0_3,n,E_A:nn). The exact support of the same confidence/calibration set is

$$
u_n^T\hat\alpha\ \pm\sqrt{t\,u_n^TVu_n}\ \pm\sqrt8\rho.
$$

The calibration term uses 3||n||²+(15/2)||STF(nn)||²=3+5=8. This is simultaneous in n because it projects one common set. A plotted finite sky grid is a visualization of this analytic band, not a computation of a global sky extremum.

## 5. Mixed shear contraction and exact conditional reduction

For phi=beta^T s beta, project the same11D ellipsoid to (beta3,kappa5), retaining all cross-covariance and its original cutoff. At fixed beta,

$$
\bar\kappa=\hat\kappa+C_{\kappa\beta}C_{\beta\beta}^{-1}(\beta-\hat\beta),
\quad C_{\kappa|\beta}=C_{\kappa\kappa}-C_{\kappa\beta}C_{\beta\beta}^{-1}C_{\beta\kappa},
$$

$$
r_\beta^2=(\beta-\hat\beta)^TC_{\beta\beta}^{-1}(\beta-\hat\beta),
\quad v_A(\beta)=\beta^TE_A\beta.
$$

Schur completion of the ellipsoid gives the conditional endpoints

$$
v^T\bar\kappa\ \pm\sqrt{t-r_\beta^2}\sqrt{v^TC_{\kappa|\beta}v}.
$$

The calibration part is also analytic: ||STF(beta beta^T)||=sqrt(2/3)||beta||², so a full-sky RMS allowance rho shifts phi by +/-sqrt5 rho ||beta||². Only the three beta coordinates remain to optimize. The companion mixed-invariant component provides global numerical enclosures and feasible conditional/calibration witnesses; its attained gap and capped status are part of the result.

### 5.1 Matched coordinate-box comparison

The legacy absolute-value bound also relaxes the quadratic signs; it is not the actual range on the enclosing coordinate box. To separate these effects, fix each of the 32 kappa corners. At fixed beta the objective is linear in kappa, so some corner attains each extreme. Calibration adds +/-sqrt5 rho I to the quadratic matrix in beta. Each resulting three-dimensional quadratic is optimized over all 27 box faces: an extremum is stationary in the relative interior of its smallest face. Nonsingular stationary equations are solved directly; a consistent singular equation uses a bounded linear feasibility problem. Inconsistent faces have no stationary point, and ambiguous numerical rank raises an explicit error.

This gives a complete finite characterization in exact arithmetic. The implementation reports float64 guards, stationary residuals, face counts and feasible witnesses; it is not a formal interval proof. The actual-box/joint-range ratio quantifies replacing the whole joint domain by its coordinate-support box, not the isolated effect of covariance off-diagonals. The legacy-triangle/actual-box ratio separately reports extra inequality slack. Existing mixed endpoints are reused without rerunning that inference.

## 6. A depth contrast that removes common angular calibration

The new finite response is

$$
K(z)=K_p+{z-z_p\over z_*}K_1,\qquad z_p=z_*=.05.
$$

Its operator is constructed from the actual sources: X16=[X11,O_m(((z-z_p)/z_*) E_A:nn)]. The retained experiment is unchanged. K1 is an observed-redshift slope in this response, not a proper-time derivative of local sigma. The constant-V/dipole assumptions are explicit.

Let alpha16=(V,dH,Kp,K1). A common additive calibration b(n)=dcal.n+qcal:nn shifts y by X16(delta_alpha,0_5). Full-rank GLS is affine-equivariant, so

$$
\hat\alpha_{16}(y+X_{16}\delta)=\hat\alpha_{16}(y)+\delta.
$$

Consequently K1 and DeltaK=K(z_h)-K(z_l) are exactly invariant under this common angular calibration. This is a response-specific cancellation, not immunity to depth-dependent calibration. If the calibration belongs to the SAME affine-z STF subspace (plus the fitted constant angular columns), its endpoint difference equals the induced estimator contrast and an RMS bound rho_delta enlarges the contrast interval by rho_delta. For an arbitrary depth-dependent calibration b(z,n), an endpoint-only bound is insufficient. Set delta_y=O b and

$$
B_\Delta=1.2 S_{K1} V_{16}X_{16}^T C^{-1},\qquad
\delta(\Delta K)=B_\Delta\delta y.
$$

The applicable budget is sqrt(2/15)||B_Delta delta_y||<=rho_delta. R61 releases this 5x32 bias operator. A concrete counterexample is Qcal(z)=0.01*((z-.02)/.05)*((z-.08)/.05)*E0: both endpoint tensors vanish, but the actual fitted contrast has nonzero bias because the calibration is outside the fitted affine-z subspace. Independent QR and direct GLS-injection checks quantify this effect; see REVIEW/final_review.md and the corrected depth result.

For z_l=.02,z_h=.08, DeltaK=1.2K1 and C_Delta=1.44 C_K1. The all-sky RMS contrast is sqrt(2/15)||DeltaK||. Its confidence image uses chi-square16 for a joint16D statement. The slope-zero test uses the marginal5D Wald statistic, equal to the difference in residual chi-square for the two nested fixed-C models.

Under an omitted finite velocity slope V(z)=V0+V1 z/.05, the estimator bias is B V1, B=V16 X16^T C^-1 Z_V1. The actual R60 Z_V1 is reused. For ||V1||<=b, the contrast RMS has the conservative additional radius sqrt(2/15)b||B_Delta||_2. This retains the declared finite-response meaning and does not use the unphysical unconstrained R60 slope optimum as a velocity prior.

The same joint set defines the support-based depth functional G(z_l,z_h,n)=n.DeltaK.n. This is the explicitly named depth contrast of F_support; no occupancy measure or original occupancy-based G_F is silently invented.

## 7. Pivot and observer extrapolation

For t_z=(z-z_p)/z_*, C_K(z)=C_pp+t_z(C_p1+C_1p)+t_z²C_11. The trace-minimizing pivot is

$$
z_{opt}=z_p-z_*{\operatorname{tr}C_{p1}\over\operatorname{tr}C_{11}}.
$$

It depends on the response and covariance, not on observed residual values. Comparing C_K(0) with C_K(z_opt) quantifies the cost of extrapolating beyond the sampled lower redshift. K(0) becomes a local normalized shear only after calibration, higher-order distance terms and congruence/smoothing conditions are supplied.

### 7.1 Why an observed-redshift slope is not a shear time derivative

The local distance coefficients in [Heinesen, Eqs.24–26](https://arxiv.org/html/2010.06534v2) imply, with c restored,

$$
D_L={cz\over\mathfrak H_o(n)}
\left[1+{1-\mathfrak Q_o(n)\over2}z+O(z^2)\right].
$$

Taking the ratio to a fiducial distance with deceleration q_f gives, after consistent observer/source-frame treatment,

$$
\eta=\log{D_{L,f}\over D_L}
=\log{\mathfrak H_o(n)\over H_f}
+{z\over2}[\mathfrak Q_o(n)-q_f]+O(z^2).
$$

Thus, under a full-sky quadrupole projection and a controlled remainder, the STF slope in eta would encode one half of the effective deceleration quadrupole: K1=(zstar/2) Q2, not dot(sigma)/H. The first term is a quadrupole of log(Hdir/Hf); it equals sigma/H only at the stated first order in angular anisotropy. Effective deceleration also contains spatial derivatives along the light ray. The actual masked CF4 operator can mix omitted angular multipoles, so neither this Q2 identification nor a numerical local-deceleration constraint is asserted in R61. The expansion supplies a concrete response model that must be controlled before promoting K(0) to local kinematics.

## 8. Angular linearization check

An explicit finite-depth multiplicative angular distance closure is D_L(z,n)=D_L_fid(z)/(1+h(n)), h=n.dH+n.K.n. It gives eta=log(1+h) at zero velocity. The current linear response is its first-order expansion. On |h|<=r<1,

$$
|\log(1+h)-h|\le {r^2\over2(1-r)}.
$$

The runner computes the actual operator-propagated remainder, its Gaussian norm and linear estimator bias, and fits this exact-log alternative with the same fixed data/covariance and first-order Doppler kernel. Analytic Jacobians and two starts check the reported stationary fit. All-sky positivity follows from global extrema of n.K.n+d.n. The comparison measures response sensitivity; it does not provide a full nonlinear GR distance solution or a globally calibrated nonlinear confidence set.

For any additive omitted response delta_y, the induced linear GLS bias is b=V X^T C^-1 delta_y. Writing F=V^-1 and P=C^-1/2 X V X^T C^-1/2, P is an orthogonal projector, so

$$
b^T F b=(C^{-1/2}\delta_y)^T P(C^{-1/2}\delta_y)
\le\|C^{-1/2}\delta_y\|^2.
$$

This turns a future uniform response-remainder bound into a bound on the entire joint bias in information-metric units. R61 evaluates the right side for the exact-log closure at fitted states only. That calculation does not establish a uniform bound over the confidence set or a bound on the general-spacetime cosmographic remainder.

## 9. Astrometric extension and the paper boundary

Heinesen–Korzynski2406.06167v1 gives, for a geodesic coarse-grained congruence and nearby sources, position drift P(sigma+omega)n+O(z). Its shear sector is a poloidal quadrupole and its rotation sector a toroidal dipole. It is defined in a nonrotating Fermi–Walker frame. The owned Gaia quasars require a source-depth/history transfer and a reference-frame likelihood before their apparent E2/B1 coefficients can be equated to the CF4 local quantities.

Existing actual Gaia coefficient/covariance products and failed robustness controls are reused as evidence of these precise input obligations. No phenomenological R39 gain or high-z-to-local substitution is used. The current paper can report the measured conditional CF4 kinematic images and depth contrast while identifying the additional observational inputs needed for absolute expansion and vorticity.

## 10. Contribution and status

The confidence-image principle, quadratic trust-region theory and leading covariant cosmography are established mathematics/physics. The current new work is their implementation on the preserved full CF4 experiment, actual joint nonlinear ranges, the measured information lost by component boxes, and finite-depth calibration-invariant contrasts with their response limitations. A publishability assessment must compare matched source-level analyses and quantify survey calibration/coverage; a new variable name does not supply novelty.
