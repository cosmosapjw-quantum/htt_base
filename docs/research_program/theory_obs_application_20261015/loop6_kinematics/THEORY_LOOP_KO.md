# HTT Loop6: Legacy beyond-FLRW 운동학량 분포의 이론 연구

2026-10-15 KST. Starting code HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54,
branch obs/solver-free-dossier-20261014. The original old_version/main_FINAL.pdf
and the attached HTT, code_package and Bianchi defect-framework archives
were used as primary historical baselines, not authoritative recent observations.

## 1. 원래 연구 질문과 사용한 정의

원래 목표는 Bianchi congruence의 네 운동학적 양
(sigma, omega, four-acceleration a, matter/geometry tilt beta)의
측정 가능한 분포로 FLRW 이탈 정도를 정량화하는 것이다.
legacy §2.4–2.7, §3, §6–8의 해석 구조와 선호하는 comparator를 보존한다.
Metric (-+++), geometry H=Theta/3, dimensionless components:

  Sigma2 = sigma_ab sigma^ab /(6 H^2);
  W2 = omega_ab omega^ab /(6 H^2);
  A2 = a_a a^a /(6 H^2).

Legacy algebraic identity (paper eq 2.45, same congruence and
consistent curvature convention assumed):

  x = Omega_FLRW - Omega_m
    = Sigma2 - W2 + (1+w) Omega_m sinh(beta)^2
      + [Omega_k-Omega_k,ref].

Signed x and Q=x/x_max; Pi(t)=P(Q>t | data, model).
For legacy MES coefficient scenarios:

  Bsigma=5 eps1/3 + 3 eps2 + 3 eps3/7;
  Bomega=3 eps1/4 + 2 eps2 + 2 eps3/7;
  Bacc=3 eps1/4 + eps2 + 3 eps3/14;
  x_max=(3/2) Bsigma^2.

These bounds require the stated Copernican almost-EGS hypotheses,
including radiation multipole spatial/time derivative restrictions.
An exact deterministic pushforward of an existing posterior is not
itself new evidence. The Planck nine maps are one CMB sky processed
in alternative ways; eps_l derived as sqrt(C_l)/T0 is explicitly
a scalar-real-harmonic convention, not a general PSTF tensor norm.

## 2. Local radial shear response: exact identifiable and nonidentifiable directions

For Euclidean tangent velocity gradient in a declared local chart:

  dv_i/dx_j = H delta_ij + S_ij + W_ij
  S_ij=S_ji, Tr S=0, W_ij=-W_ji.

The first radial directional moment is

  n_i n_j dv_i/dx_j = H + n_i n_j S_ij,

since n_i n_j W_ij = 0 exactly. Wolfram independently verified
this cancellation for arbitrary n and arbitrary antisymmetric W.
A pure radial first-jet has zero Jacobian with respect to the
antisymmetric vorticity components, so it does not construct a
vorticity distribution. This statement is limited to this observable.
A physical gamma-to-omega relation would need transverse motion,
screen rotation or specified Einstein–Boltzmann dynamics.

Define the observable CF4 group-distance-modulus residual

  y_i=DMzp_i - (25+5 log10[dL_ref(Vcmb_i/c)/Mpc]).

A deliberately conditional, linearized angular regression uses
six nuisance method zero points, optional per-method log(z) slopes,
bulk-velocity-shaped dipole and arbitrary angular dipole nuisance,
and the five STF angular tensors T^alpha_ij, where
Tr(Talpha*Tbeta)=delta_alpha,beta. With
K=5/ln10 and normalized sky n_i:

  y_i = b_method + b_method,z(log z_i - mean_method log z)
        -K[sum_alpha gamma_alpha n_i Talpha n_i
           +(1+z_i)d(ln dL)/dz_i n_i.vbulk/c
           +n_i.dipole_proxy]+epsilon_i.

The apparent dimensionless tensor S_app/Href =
sum_gamma Talpha is a five-parameter *Hubble-modulus*
source-processing residual. Only under a physically verified
single-congruence optical first-jet and shared calibration/selection
law would it be an estimator of actual geometry-frame shear.
The nuisance dipole is not four-acceleration, and the finite
survey vbulk is not geometry–matter homogeneous beta.
Published CF4 Vcmb is corrected CMB-frame systemic velocity,
not an untouched heliocentric redshift.

## 3. Actual CF4 conditioned source distribution and checks

Published Table3,4 CF4 source rows: 38,053;
select 35,970 authentic groups at 0.01 <= Vcmb/c <= 0.10.
Selected sorted 1PGC SHA-256:
f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88.

The explicitly scenario-chosen independent diagonal error is:

  var_i = e_DMzp_i^2 + (0.15 mag)^2 +
        [(250 km/s)(5/ln10)(1+z_i)dln dL/dz_i/c]^2.

These added terms are hypothesized floors, NOT the measured CF4
joint group covariance. The normalized QR-based Gaussian
conditional law is
  gamma | y, ansatz ~ N(gamma_hat,(X'WX)^-1).
It is NOT a Bianchi matter/shear posterior.

Original method counts: FP 26916, TF 7614, SN 700,
MIXED 724, SBF 14, CAL 2. The original per-method-slope
case became rank deficient in 2 of 12 leave-one-sky-region-out
fits when the tiny CAL family disappeared from a patch.
A separate declared method-nuisance alternative pools
CAL/SBF/MIXED into OTHER=740. It preserves the original
catalogue bytes and allows all 12 patches to fit.

Method-pooled fit:
  ||gamma|| = 0.03325774236;
  proxy ||gamma||/3 = 0.011085914;
  formal conditional Gaussian 2.5/16/50/84/97.5%:
  [0.008616585,0.009989457,0.011392468,
   0.012806721,0.014225786].
  normalized chi-square/dof ~=0.76594.

Changing source/nuisance:
  no method-depth slopes ||gamma||=.033529;
  0.30-mag floor .033038;
  500 km/s floor .032738;
  low-z .01-.05 .033827;
  high-z .05-.10 .033198;
  FP only .046093, TF only .048816, SN only .031049.
  All 12 leave-one-HEALPix-NSIDE1 cases in pooled model pass,
  but ||gamma||/3 still ranges .00872-.01284.

The apparent normal-direction modulus quadrupole signal is
not physically or statistically certified as homogeneous sigma/Theta.
The formal 95% source-diagonal Gaussian credible interval is not
a CF4 selection/cosmic-variance calibrated astrophysical interval.

## 4. Actual legacy source identification correction and occupancy

Original attached HTT.zip file HTT/data/obs_defaults.json labels
beta=.001334 +/- .000267 as Watkins et al 2023 CF4.
The later attached code_package/data/obs_defaults.json explicitly
corrects this as WFH2009 COMPOSITE, NOT Watkins 2023.
The 2009 survey has 4481 peculiar-velocity observations and
407 +/- 81 km/s at 50 h^-1 Mpc Gaussian window.
Watkins et al. CF4 (MNRAS 524,1885, DOI 10.1093/mnras/stad1984)
reports 387 +/- 28 km/s (150 h^-1 Mpc) and 419 +/- 36
(200 h^-1 Mpc), correlated windows of a SHARED CF4 sample.

Scenario-specific deterministic pushforward of reported
Gaussian speed *magnitudes* to beta_proxy = v/c, then
Omega_tilt = (1+w)Omega_m sinh^2(beta_proxy) is
physically valid as a conditional transform only IF
finite-volume bulk is IDENTIFIED with uniform global
matter–geometry rapidity, an unestablished hypothesis.

81 combinations: 9 actual Planck PR3 map-derived C2/C3,
3 e1 source choices, 3 distinct published velocity windows.
Nominal SMICA full, epsilon1=observed-total-CMB (Doppler
dominated) and 2023 CF4 R200:
  Omega_tilt median 6.1598841e-7,
  legacy x_max 6.4743009e-6,
  conditional Q median .09514362 and Pi(Q>.05)=.99922.
2009 WFH gives Q~.089789; true 2023 R150 gives Q~.081164.
Replacing CMB e1 with the old CatWISE NUMBER COUNT dipole
e1=.001476 gives R200 Q~.066684.
Number counts are NOT temperature multipole eps1:
that substitution is not a physical MES calculation.
If one sets the intrinsic CMB e1=0, the assumed bound
shrinks to ~6.9925e-10 and formal Q~880.9.
This does NOT reject MES: it exposes non-equivalent physical
eps1 sources and the unqualified bulk-to-global-tilt map.

Using observed CF4 local apparent Sigma2 proxy directly as
background Sigma2 produces formal ratio to MES ceiling
~30.07. That is an ILLUSTRATIVE WRONG-DICTIONARY
failure, not a measurement of 30x global Bianchi anisotropy.

No 2026 posterior or Bayes factor was rederived from a new
full selection-corrected catalogue likelihood. Legacy lnB≈26
therefore cannot be transported as a new empirical BF.

## 5. Same-frame comparison with observed Planck Q

Source CF4 apparent Hubble STF2 lives in equatorial ICRS
J2000 frame and published Planck Q is Galactic.
Apply IAU/Astropy orthogonal rotation R on both tensor indices:
  S_G = R S_ICRS R^T.
Numerical ||R^T R-I|| below 3e-15; synthetic tests show
STF cosine and principal-axis angle invariant under
joint SO(3) change of basis.

Actual Frobenius normalized contraction with Planck Q:
  SMICA full -0.5371982257,
  NILC full  -0.5012994478,
  SMICA noSZ -0.5873916672.

CF4 selected-group model-dependent bulk WLS direction vs
published CMB kinematic dipole: ~30.8129 degrees.
Formal CF4 independent-diagonal Gaussian
95% direction interval [14.5139,48.3370] degrees.
This is not a cosmic preferred-axis p-value.
The maps are correlated versions of one sky; the CF4
velocity window/covariance/selection and physical congruence
are not modelled in this orientation interval.

## 6. Targeted legacy theoretical inconsistencies

A: Source PDF eqs 1.1, 2.27 write
3-R(FLRW) = 6k/a^2 and Omega_k=-3-R/(6H^2).
Therefore open k=-1 must have 3-R<0 and Omega_k>0,
and closed k=+1 has 3-R>0 and Omega_k<0.
The SAME PDF eq 2.30 and Table 3.1 instead claim
Bianchi V open 3-R>0, Omega_k<0 and
Bianchi IX closed 3-R<0, Omega_k>0.
These are contradictory sign conventions as printed.

Wolfram explicitly computed the hyperbolic 3-metric
diag(1,exp(2x),exp(2x)) and found Ricci
diag(-2,-2 exp(2x),-2 exp(2x)), scalar 3-R=-6.
Hence Bianchi V/IX curvature terms in old x/Q posterior
MUST be rederived with one sign convention before reuse.
This is a targeted counterexample, not a general new no-go.

B: Group-orbit normal geometry congruence is
hypersurface-orthogonal, so omega_G=0. Matter tilt
may create omega_M, but one cannot insert omega_M
into the group-normal Hamiltonian while retaining
group-normal expansion and slice curvature unchanged.
Vortical threading and hypersurface curvature must be
handled with matching congruence/constraint conventions.
Legacy description of nonzero geometry-frame omega for
VIIh alongside group-normal slicing is inconsistent.

C: Bundled MIO core comment uses a different tilt
term [(1+w)Omega_m]^2 beta^2/4 instead of
(1+w)Omega_m sinh^2 beta from the manuscript.
At Om=.3153 beta=.001334 w=0 the correct term
is 5.6109434e-7 vs comment-form 4.4228235e-8
(factor ~12.686). This is a COMMENT discrepancy;
not evidence of a numerical software bug until
affected callers are inspected.
Bundled MIO identified_vs_reporting module already
warns that x/Q/Pi are reporting, not independent
identified posteriors.

## 7. Final research judgement and next executable physics

Admit under source-limited qualifications:
- authentic apparent CF4 direction-dependent Hubble
  STF2 conditional distribution and survey/method tests;
- algebraic n^T W n=0 for radial jet;
- legacy x/Q/Pi conditional reinterpretation with
  proper old/new bulk-window identity;
- frame-correct morphological CMB–CF4 STF inner products;
- concrete mismatch in legacy curvature sign and
  congruence dictionary.

HOLD (do not claim measured):
- global Bianchi sigma/Theta, omega/Theta, dot u/Theta
  or uniform background tilt beta posteriors;
- Bianchi-specific evidence/rejection; corrected
  signed x for curvature-bearing types;
- new cosmological preferred-axis significance.

Next physics-first tasks:
1. source identity, CF4 method selection and shared
   anchor covariance; SDSS-PV random-catalogue check;
2. physically genuine observer/source-redshift and
   optical first-jet via Jacobi/boost transfer with
   finite depth and velocity covariance;
3. physical mapping of selected radial STF2 to GR
   shear plus calibrated E2E null; proper-motion
   or spin-transport channel for vorticity;
4. resolve legacy sign/frame bug in symbolic equations
   before any posterior of Bianchi V/IX;
5. refit any Bayes factor using corrected independent
   survey windows and verified CMB/MES multipole
   provenance.

Sources reviewed:
- Tully et al. CF4 ApJ944 94,
  doi:10.3847/1538-4357/ac94d8.
- Watkins et al. CF4 2023 MNRAS524 1885,
  doi:10.1093/mnras/stad1984.
- Watkins Feldman Hudson 2009 MNRAS392 743,
  doi:10.1111/j.1365-2966.2008.14089.x.
- Feldman Watkins Hudson MV shear 2010,
  doi:10.1111/j.1365-2966.2010.17052.x.
- Kristian Sachs ApJ143 379 (1966),
  doi:10.1086/148522.
- Maartens et al. boosted covariant cosmography 2024,
  doi:10.1088/1475-7516/2024/09/070.
- Saadeh et al. anisotropy 2016 arxiv:1605.07178.
- Planck 2018 diffuse component separation A&A641 A4.
