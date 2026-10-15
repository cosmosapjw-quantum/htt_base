# P4 V01 | Legacy Teff × finite observer/radiation/matter frames × Planck/CF4

Date: 2026-10-15 KST. Parent 6-paper HTT observational research commit b44e4cc43ad63fb75f0e7a15e71f276155b276e5. Isolated local branch research/htt-finite-boost-frames-20261015. Original owner checkout HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54, 57 pre-existing dirty paths unchanged. The analysis provides event-local kinematic mathematics and actual-source conditional injections, not a global-tilt history or detected physical 1+3 shear.

## The finite boost and legacy bridge

Define g=(-,+,+,+), photon k/E=(1,e) with e photon propagation, outward HEALPix sky look s=-e. Observer B moves with beta_B|A relative to source A in A's orthonormal tetrad. Four-momentum components:

k_B^0=gamma(k_A^0-beta·k_A^sp)
k_B^sp=k_A^sp + [gamma²/(gamma+1) beta·k_A^sp - gamma k_A^0] beta
D=E_B/E_A=gamma(1-beta·e_A)
T_B(s_B)=D T_A(s_A).

Use (gamma²/(gamma+1)) instead of (gamma-1)/beta² at small beta. Finite boost inversion uses velocity -beta; the Minkowski norm and photon null direction are preserved. Observer/radiation/matter frame velocities beta_AB mean velocity of A measured in B comoving tetrad: beta_RO, beta_RM, beta_MO and beta_OR are spatial components in distinct tetrad frames, not vectors freely subtractable after noncollinear boosts. Rapidity rho=atanh|beta|, not beta itself.

The prior rec_bianchi source HEAD 5694a5c has independently implemented the same gamma(1-beta·e) energy factor for ONE photon event and a screen-Jones basis transform. It does NOT provide global Bianchi photon source history, full line-of-sight, calibrated Planck sky likelihood or cosmological tilt posterior. The existing HTT local/global response library is explicitly a gated diagnostic skeleton.

## Local identifiability rank lemma (not a global no-go)

Relative observed beta_OR depends on six source variables beta_RN and beta_ON, but is three-dimensional. At zero:

beta_OR=beta_ON-beta_RN + O(beta²)
J=d beta_OR/d(beta_RN,beta_ON)=[-I3, I3].

J rank=3 with nullspace dimension3; all three nonzero singular values sqrt(2). At finite Planck solar velocity reference the measured numerical singular values are [1.4142135623731027,1.4142135623730931,1.4142124863666234], rank3, nullity3, residual4.08e-16. This is a one-event two-frame kinematic rank fact. Distinct source histories, separate proper-time/energy-depth/velocity-flow measurements could break the degeneracy in a physically qualified global radiation/matter model.

## Exact legacy boosted-monopole Teff moment and CAS check

For originally isotropic radiation T_R=T0 and local moving observer sky look s:

Theta_O(s)=sqrt(1-beta²)/(1-beta hatbeta·s),
F4_O=<Theta_O(s)^4>=(1+beta²/3)/(1-beta²)
F4_O-1=4 beta²/[3(1-beta²)].

Wolfram Language computed the exact angular integral difference from this rational closed form to be zero. Independent Python 160-node Gauss-Legendre quadrature over beta=0,.00123357,.1,.3 agrees. For the Planck Solar dipole first-order reference, beta=0.001233573535670781, deltaF4=2.0289413113238506e-6.

Prior legacy-modern Planck analysis used a DIFFERENT estimand, the dipole-removed finite ell2+ell3 harmonic source, deltaF4=2.5552062387959467e-10. The formal ratio is 7940.42 but cannot be interpreted as physical beyond-FLRW or a meaningful discrepancy of two matched sky estimators. It establishes why an unremoved observer-induced dipole strongly contaminates legacy Teff fourth moments, and why Teff F4 differs from the legacy MIO certified filling fraction F.

## Real Planck PR3 finite observer-boost source injection

Planck 2018 I Solar dipole first-order reference: amplitude=3362.08 microK, Galactic hot sky l=264.021 deg, b=48.253 deg, original thermodynamic T0=2.72548e6 microK. This is published reference input, not inferred intrinsic radiation dipole.

Read the retained Planck temperature coefficients from immutable source hash 900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459: nine same-physical-sky products, l2 five and l3 seven real harmonic modes. Use actual Planck common mask NSIDE2048 NESTED -> NSIDE64 RING, 26,846 selected pixels, source FFP K1 checksum 86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb.

Reinterpret the published map-processed, observer-frame, kinematic-dipole-removed l2/l3 coefficients as hypothetical radiation-rest source harmonics ONLY FOR INJECTION. Under exact finite observer boost and aberration, simultaneous l0..5 masked OLS yields:

- Isotropic T0 source -> dipole norm 3362.080511609 microK;
- Isotropic T0 source -> l2 real harmonic norm 4.38330805650 microK;
- Independent source-analytic order beta² quadrupole STF maximum mismatch 1.11363086175e-6 microK;
- Actual SMICA_FULL l2 intrinsic-pattern source modulation/aberration response norm 0.0377471916127 microK;
- Actual SMICA_FULL l3 intrinsic-pattern response norm 0.0566158991137 microK;
- Source normalized skewness s3 changes -0.10157208795 to -0.10197456288.

Pure monopole kinematic quadrupole and underlying intrinsic-pattern modulation were numerically separated before any source tensor inference. These are not direct corrections to an already processed Planck map, no cosmological posterior and no global-tilt constraint.

## Independent CF4 source frame and survey-depth response

CF4 H01 source contains 35,970 real selected groups with n_J2000 ICRS sky directions and seven redshift windows, not Planck Galactic. The true Galactic Planck Solar dipole axis is converted to ICRS using Astropy coordinates before applying the previously measured group-window local bulk response k_B(W). The resulting H01 conditional hypothetical observer-like bulk contribution has four disjoint window logH values
[.00202368815,.00708213673,.00837313979,.00801963425].

The released CF4 z_CMB has already corrected for local observer Doppler motion. Reapplying this response to actual H_eff would count the observer correction twice. The calculation is a coordinate/unit/frame stress injection illustrating how selection windows can turn an uncorrected hypothetical bulk velocity into an apparent depth-dependent monopole. The actual method selection and peculiar velocity covariance remain unqualified; it is not a physical H(z) anisotropy measurement and is not jointly multiplied into a Planck likelihood.

## Files, validation and scientific status

Source implementation: htt/obsstat/finite_boost_observer_frame.py.
Actual Planck+CF4 executable: scripts/run_htt_real_planck_finite_observer_boost.py.
Focused regression: tests/obsstat/test_finite_boost_observer_frame.py.
Actual-source admission regression: tests/obsstat/test_htt_finite_boost_source_acceptance.py.
Canonical create-only result: docs/research_program/observational_publication_20261015/results/V01_planck_cf4_finite_boost_v3/ (JSON, Korean report, 2D comparison PNG). v1/v2 are superseded same-turn intermediate runs, v3 is canonical.

V01 is completed_scoped only if the exact Lorentz and frame typing contract, intrinsic radiation epsilon1 versus real Solar dipole and beta versus rapidity pass source/physics verification. V02 remains blocked by P2 L01 full physically matched transfer; V03 requires genuine Bianchi/tilted radiation–matter source history and is blocked_input; V04 requires calibrated cross-channel covariance and full-rank nuisance quotient. No one-event rank lemma may be presented as a strong global non-observability theorem. Manuscript submission gates remain all held.

References: Planck 2018 I, A&A 641 A1, doi:10.1051/0004-6361/201833880; Challinor & van Leeuwen PRD65 (2002) 103001 doi:10.1103/PhysRevD.65.103001; Planck 2013 XXVII A&A 571 A27 (2014) doi:10.1051/0004-6361/201321556; Mukherjee, De & Souradeep PRD89 (2014) 083005 doi:10.1103/PhysRevD.89.083005; original 2026 legacy Teff and current source-registered rec_bianchi one-event screen transport.

Native subagent NOT_RUN (no native spawn exposed in tool inventory); local Codex NOT_USED. Original checkout unmodified. No main merge, journal submission or native global tilted universe simulation performed.
