# R64 directional distance-Hubble contract and constructions

Owner `/root/r64_hubble_theory`; baseline `33d87dd3e4a787e477327d37ee00b40e790211c9`, existing checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`. Requested runtime `gpt-6-astra/xhigh`; observed identity UNKNOWN. Initial scope R2/R3 source/convention alignment; parent subsequently authorized R5/C5 scratch implementation after `r64_design.md`. No remote mutation, actual-data fit, new CAS-four-axis admission or manuscript-readiness claim belongs to this lane. The parent owns integration and the separate final review.

## Source reuse and four different objects

Use signature (-,+,+,+), physical four-velocity U.U=-c², u=U/c, sourceward observed direction n, distances Mpc, velocities km/s, rates km/s/Mpc and c=299792.458 km/s. The angular basis is the existing ICRS/J2000 `[1,n_x,n_y,n_z,n.E_a.n (a=1..5)]`, with Frobenius-orthonormal STF tensors. R54/R58 source direction, redshift and distance processing are retained.

1. The **local congruence coefficient** is

   `Hcal(x,n)=Theta(x)/3+sigma_ab(x)n^a n^b−A_a(x)n^a/c`,

   where Theta and sigma are physical proper-time rates and A=U.nabla U is physical acceleration. This is literature-supported (Heinesen 2010.06534v2 Eq.11; R32-08 main.tex41–45) and follows from the null contraction below. Antisymmetric vorticity vanishes from this contraction. It need not vanish in other observables. A geodesic matter congruence has A=0, a materially stronger premise than choosing a boosted observer.
2. The **light-cone redshift rate** is the variation of photon energy along one ray relative to a specified congruence, with fixed endpoint frame normalization. It uses Hcal evaluated at the ray event and the locally decomposed ray direction. It is not an observer-time redshift drift and is not automatically the derivative of catalogue z_CMB after arbitrary processing.
3. The **distance-defined quantity** is `R(z,n_o)=D_L(z,n_o)/(1+z)`, `H_D=c/R_z`. The derivative holds the observed sky label n_o fixed and ranges over sources on that light-cone ray. It is a well-defined observable functional once distance calibration, redshift chart and a smooth distance relation have been specified. It is not generally Hcal at finite z.
4. A **finite survey H_W** is an estimator with an actual design/weight law. H01 defines `H_W=sum(w_i d_i cz_i)/sum(w_i d_i²)` at frozen weights. H03 fits the full nine angular columns with an actual source operator. Window responses mix velocity, scalar and STF channels and have cross-window covariance. Neither operation is a pointwise derivative. H01 lines7–37 and H03 S1 lines7–21 explicitly preserve these distinctions.

The existing R37 Hubble/optics result gives apparent angular H ratios, finite optical budgets and a synthetic CBL derivative control, not an empirical radial derivative. R61 THEORY183–219 already derives eta's local cosmography and separates its depth slope from a shear time derivative. R63 THEORY23–62 fixes the first-order source/observer/catalogue chart and source-velocity response; those equations remain applicable, without an added source-clock factor.

Primary-source checks: https://arxiv.org/html/2010.06534v2 Eqs.1,11,14,16,18 and luminosity-distance expansion; https://arxiv.org/html/2312.09875v3 for moving-observer distance conventions; https://arxiv.org/html/2406.06167v1 for congruence/smoothing and known errata. No shear-evolution or higher-order acceleration-vorticity equation from the uncorrected older source is imported. The new finite construction below is not claimed to be novel general cosmography.

## Exact covariant optical relation (derived here from the standard equations)

Let lambda be a past-directed affine parameter of length, increasing away from the observer, and let `ell^a=dx^a/dlambda=E(−u^a+n^a)`. Normalize E_o=1. Assume one smooth emitter/observer congruence, the observer comoving at the vertex, a unique caustic-free ray branch, geometric optics and photon conservation. Then E=u.ell=1+z. With

`nabla_b u_a=(Theta h_ab/3+sigma_ab+omega_ab)/c−u_b A_a/c²`,

the geodesic equation gives

`dE/dlambda=ell^a ell^b nabla_a u_b=E² Hcal/c`,
`dz/dlambda=(1+z)² Hcal/c`.                                      (1)

The acceleration sign is negative because ell.u=E and ell.A=E n.A. Reversing affine orientation gives the familiar future-directed `dE/dlambda=−E² Hcal/c`. Monotone positive-z parametrization requires Hcal>0 on the segment; local inversion only needs Hcal nonzero. Different source and observer endpoint velocities require the actual energy ratios and aberration/Jacobi normalization, as in R63. A redshift-only frame correction does not by itself turn a luminosity-distance catalogue into a same-congruence light cone.

The Sachs area-distance equation and vertex conditions are

`D_A,lambda lambda=−F D_A`,
`F=|sigma_opt|²+(1/2)R_ab ell^a ell^b`,
`|sigma_opt|²=(1/2)sigma_opt,ab sigma_opt^ab`,
`D_A(0)=0`, `D_A,lambda(0)=1`.                                  (2)

Thus `D_A(lambda)=lambda−integral_0^lambda (lambda−s)F(s)D_A(s)ds`. This is an exact Volterra equation when the optical tidal source is specified; it supplies no missing curvature closure. Etherington gives `R=(1+z)D_A`, so

`R_z=D_A+c D_A,lambda/[(1+z)Hcal]`,
`H_D=(1+z)Hcal/[D_A,lambda+(1+z)Hcal D_A/c]`.                     (3)

At the vertex H_D tends to Hcal_o under these matching assumptions. At finite depth its denominator contains the optical solution. Equivalently, putting primes for the total fixed-ray z derivative,

`D_A''+[2/(1+z)+Hcal'/Hcal]D_A' + c²F D_A/[(1+z)^4 Hcal²]=0`,
`R''+(Hcal'/Hcal)R'+[c²F/((1+z)^4 Hcal²)−Hcal'/((1+z)Hcal)]R=0`,
`(ln(H_D/Hcal))'=[c²F/((1+z)^4 Hcal²)−Hcal'/((1+z)Hcal)] R H_D/c`. (4)

These relations separate kinematics from focusing without introducing Einstein/matter or curvature closure. They do not allow Hcal to be recovered from one arbitrary distance curve without the missing optical function. Hcal' includes changing event, congruence and locally decomposed n along the ray. It is not a partial derivative with local n-components fixed, a proper-time derivative, or a parallel-transport rule for the matter congruence.

A constructive continuation is available when the missing optical input is supplied. Set Y=Hcal² in (4). Then `[R'−R/(1+z)]Y'/2+R''Y+c²F R/(1+z)^4=0` is a linear first-order ODE for Y, with calibrated vertex value Y(0)=Hcal_o². Here F must be given in the same affine/congruence normalization, and the positive solution selects the expanding branch. The coefficient of Y' is (1+z)D_A'; direct division fails at an angular-diameter-distance extremum and requires a separate regularity/compatibility treatment. This is a specified route to physical expansion, not a closure furnished by the distance curve alone.

**Genuine curved-FLRW counterexample.** Let `R=S_K(chi)`, `chi'=c/H`, `S_K'=C_K`. Then `H_D=H/C_K(chi)`. On the positive-derivative branch C_K>0, this differs from H unless the curvature factor is unity. In the exact Milne spacetime, curvature K=−(H0/c)², H=H0(1+z), chi=(c/H0)ln(1+z), and

`H_D=2H0(1+z)²/[(1+z)²+1]`,
`q_D=[1−(1+z)²]/[1+(1+z)²]`, while physical `q=0`.              (5)

Milne is flat spacetime with vanishing optical F; this counterexample needs neither opacity nor an invented stress closure. Its distinct congruence expansion and distance-defined H already refute their finite-z identification. A second elementary optical witness is `R_obs=exp[tau(z,n)/2]R_true`; then `H_D,obs=exp(−tau/2)c/[R_true'+tau' R_true/2]`. Grey z-independent transmission is a multiplicative calibration; depth-dependent transmission changes the derivative shape.

## Exact eta map and its invariant quotient

For a positive smooth flat reference `D_L,ref=(1+z)chi`, `chi'=c/H_ref`, set `eta=ln(D_L,ref/D_L)` and `B=H_ref chi/c`. Then R=chi exp(−eta), whence

`H_D/H_ref=exp(eta)/(1−B eta_z)`,                                (6)
`q_D=q_ref+(1+z)[eta_z+(B' eta_z+B eta_zz)/(1−B eta_z)]`,
`B'=1+(H_ref'/H_ref)B`, `q_ref=−1+(1+z)H_ref'/H_ref`.            (7)

Assumptions for the positive finite image are H_ref>0, R_ref>0 at z>0, finite eta and `D=1−B eta_z>0`; eta must be C1 for H_D and C2 for q_D. A denominator reaching zero is not a large finite Gaussian error bar. R>0 follows from its exponential form; R_z>0 is the separate condition D>0. For a curved reference replace H_ref by `H_D,ref=c/R_ref'` and B by `R_ref/R_ref'`. Calling that H_D,ref the physical FLRW H_ref would reintroduce the curvature error.

Under a source-distance calibration `D_L -> exp[a(n_o)]D_L`, with a independent of z, eta -> eta−a and H_D -> exp[−a]H_D. Therefore

`H_D(z,n)/H_D(z*,n)=[H_ref(z)/H_ref(z*)] exp[eta(z,n)−eta(z*,n)] D(z*,n)/D(z,n)` (8)

and q_D are **exactly invariant at the uncompressed field level** for any such angular a. Angular H_D ratios at fixed z are not invariant. Absolute H_D is not calibration-free. This invariance says nothing about depth-dependent calibration.

The owned chart is `eta_repo=ln[c(1+z)chi_hat/D_L(Mpc)]`, with the logarithm understood in its fixed numerical unit convention. It equals `ln H0+eta`, not eta. Consequently

`H_D[km/s/Mpc]=E exp(eta_repo)/(1−E chi_hat eta_repo,z)`,          (9)

and eta_relative=eta_repo−ln H0 when using (6). Retaining four measured monopoles does not supply an absolute physical distance calibration.

**Numerical-reference obligation.** R54 `flat_lcdm_distance_factors` computes chi_hat by a 6001-point trapezoid grid whose upper limit depends on the input zmax and then linearly interpolates. Its exact numerical derivative is not 1/E, and its second derivative is not a smooth physical reference derivative. R64's smooth-reference image uses an independently specified smooth chi_hat. Preserve the original eta observation and explicitly transport `delta_eta(z)=ln[chi_hat_smooth(z)/chi_hat_R54_actual(z)]` through O before fitting that chart, or quantify its omission as a numerical-chart remainder. Recalling the R54 function at one new z does not reproduce its original catalogue-dependent interpolation. This is a deterministic chart change, not a new distance measurement or covariance fit.

## Finite source family, derivative boundaries and identification

Use t=(z−0.055)/0.045 and Legendre polynomials P_j(t):

`eta_repo=sum_{j=0}^J P_j(t)b(n).a_j + g(z)n.V`,                  (10)

with parameter order `[V3,a0_9,...,aJ_9]`, free V in km/s and dimensionless coefficients. g is the preserved R63/R54 response `[(1+z)/(E chi_hat)−1]/c`, propagated at each source. No 1/z replacement is made in the actual design. The optical/background distance image excludes the declared coherent-velocity nuisance term; it is conditional on that decomposition. The total fitted distance field including gV is a different estimand and must not share its label.

R9 clarification: `g(z)n.V` is a first-order velocity tangent template. The fixed linear Gaussian experiment does not impose or certify `|g_i n_i.V| << 1`, an allowed physical velocity body, or a higher-order response remainder. Large fitted coefficients can therefore be valid parameters of this statistical experiment without being admitted physical velocities. Subtracting the template defines a conditional polynomial-distance image, not a physically validated velocity deboost. A physical interpretation must qualify the source response and its finite-amplitude remainder separately. See REPORT_KO.md for the actual saved-coefficient scales and the distinction between identified augmented fits and initial singular representatives.

For the optical polynomial, `eta_z=sum P_j'(t)b.a_j/0.045` and `eta_zz=sum P_j''(t)b.a_j/0.045²`. J1 has constant angular first derivative and zero second derivative; J2 has linear first derivative and constant second derivative; J3 has quadratic first derivative. The nonlinear image still has radial dependence through B. Derivatives amplify truncation errors: a bound on |delta_eta| alone cannot bound |delta_eta_z| or |delta_eta_zz|. For example delta_eta=epsilon sin(kz) has fixed amplitude but arbitrarily large derivatives. A physical derivative claim needs C1/C2 remainder control, finite resolution evidence, or a declared smoothness/model restriction. No extrapolation to z=0 is certified by data with zmin>0.

Let `y=O eta_repo`, C the same original R58 full36 covariance, `Z=O b(n)`, and X the source-integrated columns. Do not substitute window centres into (10). For C=LL^T, `P_Z=I−(L^-1Z)(L^-1Z)^+`. The finite calibration quotient is

`ybar=P_Z L^-1 y`, `A=P_Z L^-1 X_nonconstant`.                  (11)

It is invariant under y->y+Z a. This removes represented common l<=2 calibration using the actual operator. An arbitrary higher-angular calibration has image O a(n) and need not lie in col(Z); incomplete sky and depth-dependent angular sampling can leak it into the target. An explicit l=3 source injection is the cheapest current boundary witness. The unrestricted field-level invariance and the restricted finite estimator's invariance are different statements.

For a linear target L_t theta, estimability is `L_t ker(X)=0` (or the corresponding quotient A condition), not merely a nonzero diagonal of a pseudoinverse covariance. The full confidence object is a cylinder along every exact null. A nonlinear target F is identified iff it is constant on every admissible likelihood fibre. Identification of all its linear ingredients is a sufficient operational check. For (8), these ingredients are eta(z)−eta(z*), eta_z(z), eta_z(z*); for (7), eta_z and eta_zz. Preserve genuine unidentified directions instead of turning the SVD representative into an estimate of a physical parameter.

J1 has21 columns, J2 has30, J3 has39 before actual nulls. J2 leaves6 residual degrees only if all30 columns are identified; J3 cannot identify all39 from36 rows. The actual rank must be computed separately for every operator. In `log_mono_radial`, O z=0 by construction. Since P1=(z−zp)/s, its monopole is confounded with common calibration; eta_z's monopole and even the monopole of eta(z)−eta(z*) are unidentified. A depth-of-angular-difference cancels that particular scalar null, but must still pass the remaining null test.

**Explicit saturated-design witness.** At four distinct positive shell redshifts z_i, let p3 interpolate 1/z. Then

`1/z−p3(z)=product_i(z−z_i)/[z product_i z_i]`.                  (12)

The cubic-plus-velocity source family can vary by this function without changing any of those shell values, although its derivative at every z_i is nonzero. This demonstrates the failure of a saturated compressed fit to identify continuum derivatives; it is a scoped counterexample, not a universal prohibition on all distance reconstructions. The actual O-integrated J3 nulls, rather than this toy's numerical values, decide the actual experiment.

## Confidence images and selected finite computations

Under the declared fixed-C Gaussian linear law, use the existing `mt.fit_linear` rank model and the one rank-r confidence cylinder with chi-square_r(level) radius. `mt.linear_interval(...,simultaneous=True)` supplies support bounds for every estimable linear contrast using that same set, including nuisance uncertainty and cross-covariance. Never replace r by1 just because the final target is a scalar. A fit residual uses n−rank degrees when positive.

For each predeclared (z,n), obtain bounds on u=eta_z and D=1−Bu. If a required linear functional has a null component, return INGREDIENT_UNIDENTIFIED: the sufficient construction fails, but this status alone is not a proof that every nonlinear combination is unidentified. The equal-redshift ratio is identically1 on its admissible positive-domain fibre even when its ingredients are unidentified; keep this identity and report whether that domain is certified. If any required lower D bound is nonpositive, return DOMAIN_NOT_CERTIFIED and no finite H/q interval. For (8), joint supports on delta_eta, D(z), D(z*) give the conservative enclosure

`[H_ref(z)/H_ref(z*)] * [exp(delta_lo) D*_lo/D_hi, exp(delta_hi) D*_hi/D_lo]`, (13)

provided both denominator intervals have positive lower endpoints. It is an enclosing interval of the same joint set; rectangular support bounds do not assume independence and are generally not sharp. q_D can analogously enclose u+[B'u+B eta_zz]/D. Point values are permitted only on D>0 and are not a substitute for a valid confidence image. A finite list of sky/redshift checks certifies only that list; it is not an all-sky/continuous-z certificate. Even intersecting with D>0 need not yield a bounded image when the closure approaches D=0.

Recommended finite computation order: J1 primary source-integrated fit and correlated predictive check; J2 flexibility; J3 rank/null stress. Report linear radial contrasts first, including identification failures; then the exact positive-domain image where certified. Compare an l<=2 common zero-point witness through O and an l=3 leakage witness, scalar-z null, reference-chart offset, and R63 deterministic correction. Inspect the first uncertain step—actual rank and C1/C2 resolution of the source-integrated distance family—before drawing a physical expansion conclusion. Alternative Volterra Hcal inference remains open but requires F, endpoint frames and source terms; (2)–(4) specify exactly what is missing.

Implementation status at this checkpoint: equations (1)–(13) derived; literature and native source locations read; no new actual fit. Scratch `r64_directional_hubble.py` supplies scalar maps, Legendre jets, the source design and conservative confidence enclosures. `test_r64_directional_hubble.py` contains exact polynomial/background limits, source-operator calibration, confidence-cylinder witnesses, scalar-z null, nonpositive domain, normalization and Milne controls. Tests have not been executed by this lane: parent-owned execution and independent review determine implementation-verified status. A test file's presence is not PASS evidence.
