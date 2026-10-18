# HTT Loop7: 최신 PR의 typed signed-defect와 실제 관측입력의 분포를 연결한 이론 결과

2026-10-15 KST. Source checkout: obs/solver-free-dossier-20261014,
HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54.
Legacy basis: uploaded main_FINAL.pdf §§2.4–2.9, 3, 6–8,
original HTT/code_package archives as preserved and previously audited
in loop6_kinematics. Preserve original scientific motivation:
distribution of kinematical shear/vorticity/acceleration/tilt and an
interpretable beyond-FLRW departure variable, not merely code critique.

## Authoritative PR genealogy and actual source consumers

- https://github.com/cosmosapjw-quantum/htt_base/pull/360
  PR-248–252, historical scalar labels preserved as BC1_LEGACY_PROJECTION,
  BC2_NO_REPRESENTATION_PROMOTION. Signed x_C is the exact constrained
  Gauss/Friedmann projection for the SAME congruence, not a measured
  statistical distance or geometry posterior.
- https://github.com/cosmosapjw-quantum/htt_base/pull/362
  PR254 typed normalizer/anchor body/one-way envelope. MES anchors are one
  anchor among purpose-specific families, never physical total-defect
  maximum or a converse for FLRW.
- https://github.com/cosmosapjw-quantum/htt_base/pull/363
  PR255 actual post-transfer/post-nuisance subspace, singular values and
  Schur information; a numerical rank cannot identify a forbidden
  nullspace physical tensor by imposing a coordinate normalization.
- https://github.com/cosmosapjw-quantum/htt_base/pull/364
  PR256 explicit beta_RO / beta_RM / beta_MO; galaxy bulk velocity,
  solar CMB dipole and radiation-matter background tilt are different.
- https://github.com/cosmosapjw-quantum/htt_base/pull/365
  PR257 proper tensor rank O(3)/parity morphology and tested counterpairs.
- https://github.com/cosmosapjw-quantum/htt_base/pull/521
  R2-04 actual conditional_legacy_image and frozen LegacyAdapter:
  original signed x, samplewise Q, unique joint draw IDs/weights,
  strict Pi and undefined mass. Its code was ACCEPTED_SCOPED for
  synthetic finite sampling, actual physical posterior HOLD.
- PR124 actual primary-source MES registry:
  htt/src/common/mes_theorem_authority.py and
  htt/src/common/statistical_foundations.py, branch-specific exact
  rational coefficients and congruence/frame contracts.

## 1. The physically distinct objects

For one specified geometry-frame congruence, one compatible signed
Hamiltonian comparator and matter rest-frame perfect-fluid source:

    x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k,            [legacy algebra]
    Omega_tilt = (1+w)Omega_rest sinh²(beta_RM).

It is mandatory to use the same metric/normal, epoch,
curvature sign and density normalization in all four terms.
An observer-frame apparent Hubble quadrupole from CF4 distance moduli
is not a geometry-frame Sigma2. A finite-volume MV bulk velocity
is not the homogeneous global beta_RM. A real CMB sky HM/OE
processing variant is not another independent cosmological realization.

In PR360 language, x_C is a *signed budget projection*.
The original ratio

    Q_legacy = x_C / [(3/2) B_sigma²]

is not a registered physical filling fraction for arbitrary
positive tilt, signed curvature or vorticity. MES B_sigma is a
one-way shear-sector bound (conditional on EGS/linear/Copernican
derivative hypotheses). PR254 permits physically channel-matched
sector stress only after complete anchor and numerator contract.
A generalized signed total-defect occupancy requires a
separate physically proved total-defect anchor.

### Registered MES compared against archived historical branch

Under the current **verified geodesic** PR124 branches:

    B_sigma=(5/3)e1+3e2+(3/7)e3,
    B_omega=(10/3)e1+(2/15)e2,
    sigma-sector anchor=(3/2)B_sigma²,
    omega-sector anchor=(3/2)B_omega².

Geodesic four-acceleration u-dot=0 *structurally*, so there is
NO active independent geodesic acceleration ceiling.
Anisotropic curvature also has NO MES anchor.
The historical non-geodesic-style B_omega=
(3/4)e1+2e2+(2/7)e3 and B_acc=
(3/4)e1+e2+(3/14)e3 cannot be inserted as active
geodesic-sector bounds. The legacy multiplicative
frame correction 1+2.69e1 is WITHHELD for derivation mismatch.

The registered geodesic input requires observer-motion attribution;
feeding the entire 1.23357e-3 measured solar CMB dipole into e1
is rejected by the real registry strict-hierarchy validator.
Declaring e1=0 (fully subtracted cosmological residual) yields
algebraic shear-sector 6.77564e-10 through 7.02819e-10,
and omega-sector ~9.86e-13 through 1.03e-12,
over nine actually measured same-sky Planck processed maps.
These are **not admitted observational MES limits** because
sqrt(C_l)/T0 from masked OLS maps is not certified the covariant
MES epsilon_l field with spatial/time derivative controls.

Consequently CF4 local apparent STF2 vs PR124 shear anchor
returns typed CHANNEL_MISMATCH. It cannot be assigned a
Shear/MES saturation ratio, even if the raw scalar quotient
could be numerically computed.

## 2. PR521 rigorous finite signed-defect pushforward

For a validated source posterior with normalized joint
atom weights p_i, draw identities i, full physically
specified sectors and positive *total-defect* anchors c_i,
set

    x_i = Sigma2_i-W2_i+Omega_tilt_i+DeltaOmegaK_i,
    Q_i = x_i/c_i,
    Pi(t) = sum_i p_i 1{defined_i AND Q_i > t}
            + remaining unknown contribution.

No missing sector is assigned zero and no defined draw weight
is re-normalized after dropping an undefined value.
Let p_L=sum_{known,Q_i>t} p_i and
u=sum_{undefined}p_i. Then the exact finite image
reports Pi(t) in [p_L,p_L+u] for the declared
joint measure. Equality Q_i=t is NOT counted
in the strict tail. Those interval endpoints are
not a frequentist confidence band or astrophysical
posterior probability until the producing
observation/selection/response model is valid.

PR521's actual existing R2-04 frozen source adapter was
invoked here and checked against an independently
computed Gaussian analytic distribution.
This is a constructive selected R/C calculation, not
a reimplementation of the historic R2-04 logic.

## 3. Exact analytic survival probability for a declared legacy scenario

As a deliberately CONDITIONAL source model let

    Z ~ Normal(mu_v,sigma_v²), V=max(0,Z),
    beta_hyp=V/c, x_hyp=x0+Omega_m*sinh²(beta_hyp),
    Q_hyp=x_hyp/c_LEGACY,

where c_LEGACY>0 is a specified *historical shear*
normalizer, NOT an admitted total x ceiling.

For threshold q, define T=q*c_LEGACY-x0.
Then strict P(Q_hyp>q) is exactly:

  T<0 : 1;
  T=0 : Normal survival at Z>0, 1-Phi(-mu_v/sigma_v);
  T>0 : Normal survival at
          Z > c*asinh(sqrt(T/Omega_m)).

The zero-speed atom in V must be treated separately for
T=0. This exact distribution uses a *reported Gaussian
bulk-speed magnitude scenario*, not the real
galaxy catalogue's posterior and selection likelihood.

With Omega_m=.3153, x0=0 and e1 equal to the
**historical** full observed solar CMB dipole, actual
SMICA_FULL l2–3, and cited original bulk windows:

  source                              Q median   Pi(Q>0.1)
  WFH 2009 COMPOSITE 407±81          0.08976     0.39016
  CF4 2023 R150 387±28              0.08115     0.06412
  CF4 2023 R200 419±36              0.09513     0.38431

The two CF4 windows are one shared raw survey and
are NOT independently multiplied. The old HTT source
mis-attributed WFH2009 to CF4; the attached later code
corrected this and the current loop inherits that correction.

2048 matched quantile atoms per window in PR521's
existing finite_joint_pushforward reproduce analytic
tail probabilities within 1/2048 and preserve all
original ID/weights and strict threshold equality.

## 4. What the actual nine Planck maps constrain in this exercise

Same-window same-latent processing sensitivity:
  WFH2009 Pi(Q>.1) spread: [0.3901072,0.3904917]
  CF4 R150 Pi(Q>.1) spread: [0.0640662,0.0644304]
  CF4 R200 Pi(Q>.1) spread: [0.3841856,0.3850471].

The map-to-map variation is a same-physical-sky
source-processing sensitivity, not a CMB cosmic-variance
confidence band. In contrast, different published
bulk-flow window means and widths lead to materially
different conditional q-tail distributions.
One must not interpret the latter as a measured
redshift evolution of universal tilt.

The actual CF4 Table3/4 fixed source cohort of
35,970 groups yielded a formal *apparent modulus STF2
Hubble residual* in earlier loop6:
  norm ||gamma_app||=.03325774236,
  apparent normalized amplitude ~.011085914
  conditional source-diagonal Gaussian range
  roughly [.008616585,.014225786].
That direction is highly model/selection/sky treatment
dependent and cannot be called sigma_G/Theta.
The previously audited Bianchi V/IX curvature
sign and mixed-congruence source identities are still
not repaired, so actual signed Bianchi curvature
posterior cannot be inferred from those assumptions.

## 5. Null admission and next feasible scientific computation

If the same actual reported speed windows are supplied
but the physical global geometry sectors are
properly marked *unknown* in the PR521 operator,
x/Q unknown mass is exactly 1 and Pi(t) is [0,1]
for each threshold. This does NOT mean a scientific
posterior is uniform; it is the exact statement that
this restricted observational source has not
identified the requisite nonlinear physical map.

Next substantive physics objectives:
  A. Obtain source-qualified **same-congruence**
     optical first-jet tensor response and its
     finite-distance remainder, then infer actual
     background shear if identifiable under source selection.
  B. Construct a native Bianchi photon Boltzmann/Thomson
     forward transport for geometry sigma, matter tilt
     beta_RM, vorticity, acceleration and sky morphology
     with observer beta_RO separately integrated.
  C. With the genuine joint posterior and consistent
     geometric curvature comparator, use PR521
     posterior_legacy_image and PR254 qualified
     *total defect* anchor if one is proved;
     otherwise report x_C signed distribution,
     sector one-way stresses and identified ranges,
     leaving physical Q/Pi undefined.
  D. Register source sky masks, CF4 depth-window shared
     covariance, actual normalized selection likelihood,
     and proper prior/evidence calibration.

Admitted in this loop: formal PR521 finite conditional law
with actual published source inputs, analytic exact CDF,
PR124 geodesic algebraic scenario, typed channel mismatch,
same-latent Planck processing comparison.
Not admitted: a physical posterior of sigma/omega/u-dot
or global beta, an FLRW departure detection, an H0
correction, independent 9-sky likelihood, Bayesian evidence.

Native delegation: NOT_RUN (no native host dispatch tool);
symbolic scalar identity verified with Wolfram and
real local Python source code/suites executed.
