# R54 hypothesis graph (2026-11-16)

Decisions are per dimension; there is no aggregate score.

### H-C1 (CORE) - PROMOTE

The five views are a reporting convention on one precision-form carrier: Q and F are polar duals (R54-EQ-21) and no view adds information to the likelihood.

- evidence: module + unit tests
- validity: exact convex duality; 2-D enumeration to 1e-8
- novelty: NONE claimed (standard convex analysis)
- testability: HIGH
- robustness: exact
- risk: presenting a reporting layer as a statistic
- kill criterion: a view that changes a GLS estimate
- executed result: tests/r54 pass; ties GLS by construction (R53 theorem retained); the F view is UNAVAILABLE on both low-redshift lanes because an axis scan is not a support functional
- next action: use as the reporting layer of every lane; no novelty claim

### H-C2 (CORE) - REJECT

A tensorized carrier gains statistical power over the exact likelihood.

- evidence: R53 benchmark
- validity: contradicted by sufficiency
- novelty: none
- testability: done
- robustness: n/a
- risk: false-gain claim
- kill criterion: n/a
- executed result: R53: Fisher-distance ratio 1.0000, coverage tie
- next action: never claim gain; claim typed interpretation only

### H-C3 (CORE) - HOLD

Irreducible-carrier transport with the full cross-depth covariance tells a 1/d (velocity) law from a constant (zero-point or acceleration) law on the real CF4 footprint.

- evidence: injections on the real footprint with exact-body noise, pooled and method-monopole operators
- validity: exact GLS; synthetic recovery test
- novelty: LOW, pending R54-L07
- testability: HIGH
- robustness: constant law preferred for an injected step / an injected flow: 93% / 24% at 0.05 mag and 300 km/s; 82% / 20% at the observed sizes (0.036 mag, 371 km/s); method-monopole operator at the observed sizes 83% / 22%
- risk: the observed-size amplitudes are data-derived; on data the outcome depends on inter-method zero points
- kill criterion: at the observed sizes the constant law is preferred in fewer than 90% of step draws or more than 10% of flow draws on either operator (rule written before the observed-size run was read; not committed beforehand)
- executed result: pooled chi2(A)=10.4/9 vs chi2(V)=16.2/9; after method monopoles 6.67 vs 7.26
- next action: R54-L04

### H-L1a (L1) - PROMOTE

Re-derivation: the T and E quadrupoles measure two ionization-fixed linear functionals of the shear history, Sigma_T = int K_T s dN and Sigma_E = int K_E s dN, with closed-form kernels (R54-EQ-03).

- evidence: derivation + SymPy seal + ODE agreement inside the unit-test tolerance
- validity: first order, k = 0, type I
- novelty: NONE claimed: the first-order polarized transfer in a flat anisotropic universe was solved in E46 (see also E48, E47); E03 and E44 separate the line-of-sight temperature integral from the visibility-weighted polarization source
- testability: HIGH
- robustness: kernel exact; history-model free
- risk: none at this order
- kill criterion: an order-unity term missing from the k = 0 Thomson system
- executed result: r_E(perfect fluid)=0.0711; reionization share 19%; R54-L01: masked E response e_dev = 0.0003 (IDEAL_E_RESPONSE_KEPT)
- next action: R54-L07 literature check (B09)

### H-L1b (L1) - PROMOTE

The conversion of (Sigma_T, Sigma_E) to a present-day shear is not robust: it depends on the radiation anisotropic-stress history, on the neutrino masses and on the initial state, so a perfect-fluid bound cannot be quoted without its model label.

- evidence: ODE with photon and neutrino stress (massless and minimal normal ordering with the exact collisionless stress weight R54-EQ-06); analytic radiation-era oscillator test
- validity: linear; the statement is qualitative and every number is an illustration
- novelty: LOW, partly checked: E05 shows that free-streaming neutrinos invalidate CMB temperature limits in the magnetic Bianchi I case and E06, E07 give the modified shear decay under collisionless stresses; full check in R54-L07
- testability: HIGH
- robustness: s0/Sigma_T changes sign with photon stress (-0.000244); (c_T, c_E) = (0.00166, -0.0254) massless and (0.000858, -0.0147) for minimal normal ordering; Sigma_T per unit initial shear changes sign between an assumed free-streaming onset at z_i = 1.5e+10 (T_nu = 2.5 MeV) and 2e+10 (3.4 MeV), an interval that contains the decoupling estimate of 3.12 MeV for muon and tau neutrinos (E49; 1.87 MeV for electron neutrinos) (r_E from 0.050 to 0.109 before the sign change, -1.057 to 0.109 over all 8 points)
- risk: quoting an illustration number as a limit
- kill criterion: a prior paper that already gives stress-corrected Bianchi-I shear limits from CMB T+E
- executed result: 95% illustration values of |s0|: 1.42e-10 (perfect fluid, T+E), 6.66e-08 (massless two-mode family), 3.43e-08 (minimal normal ordering)
- next action: R54-L07 literature check

### H-L1c (L1) - REJECT

PR3 component-separated ell = 2 polarization can be used at face value.

- evidence: B-null gate on committed carrier
- validity: Hotelling law with N = 300
- novelty: n/a
- testability: done
- robustness: holds for SMICA and Commander
- risk: E-lane overclaim
- kill criterion: n/a
- executed result: B ell=2 tail p=9.54e-06 (SMICA), 3.96e-07 (Commander); observed rms 0.30 vs FFP10 0.11 uK; R54-L01 empirical LOO B ell=2 tail 0.00664 (SMICA), 0.00332 (Commander); E lane DIAGNOSTIC; R54-L02 adopted-covariance B ell=2 null passes in: Cosmoglobe_BeyondPlanck, Planck_PR3, WMAP9; E lane CLAIMABLE
- next action: R54-L06 (T lane; E lane as recorded)

### H-L1d (L1) - REJECT

Octupole or higher morphology constrains type-I parameters.

- evidence: first-order response is pure ell = 2
- validity: exact at first order
- novelty: n/a
- testability: done
- robustness: exact
- risk: none
- kill criterion: n/a
- executed result: ell >= 3 modes enter only through covariance
- next action: family comparison beyond type I remains blocked on a source-bound transfer

### H-L2a (L2) - REJECT

The owned count dipoles (Quaia G<20, NVSS; receipt estimator) exceed the kinematic expectation.

- evidence: committed receipt
- validity: per-axis sd includes mask and declination systematics; no clustering body
- novelty: n/a
- testability: LOW with this estimator
- robustness: power against a dipole twice the kinematic one: 0.20 at the 5% level
- risk: reading a non-detection as evidence against the published anomaly
- kill criterion: the calibrated estimators of R54-L03, with power of at least 0.8 against the published excess, give p >= 0.01
- executed result: excess tails p=0.27 (Quaia), 0.46 (NVSS); common excess p=0.12; no decision at this power; R54-L03 calibrated excess tails 0.309 (Quaia), 0.421 (NVSS); H-L2a stays REJECTED for the owned estimators; R54-L03 decision check: H-L2a stays REJECTED for the owned estimators (calibrated covariance; REJECT holds for the owned estimators only)
- next action: none for the owned estimators; R54-L06 tilt closure uses the calibrated count covariance

### H-L2b (L2) - HOLD

A linear clustering dipole body (R54-EQ-32) and a same-estimator velocity null change the significance of count-dipole excesses on the owned catalogues.

- evidence: not executed in the cloud session (needs catalogue N(z), selection maps and bias models)
- validity: linear theory; bias from cited primary sources only
- novelty: LOW (E20 addresses clustering for CatWISE2020)
- testability: HIGH
- robustness: bracketed by two N(z) and two bias models
- risk: bias taken from memory
- kill criterion: the body is below 10% of the shot term for every owned catalogue and cut
- executed result: no number yet
- next action: R54-L03

### H-L2c (L2) - REOPEN

The R52 counts-versus-CF4 frame inconsistency is a statement about cosmic frames.

- evidence: R52 result + R54-L05 exact CF4 carrier
- validity: R52 used the biased linear CF4 estimator without a cosmic body
- novelty: n/a
- testability: HIGH
- robustness: count side has no clustering body yet
- risk: mis-attribution
- kill criterion: the closure test rejects at p < 0.01 once the count side is calibrated
- executed result: tilt closure V_CF4 + c beta_excess = 0: p=0.0895 (V only), 0.0123 (constant dipole marginalised); count side preliminary
- next action: R54-L03, R54-L06

### H-L3a (L3) - PROMOTE

Vorticity is not identified by any owned first-order observable; identification needs a dynamical-versus-kinematic frame tie or a family-specific transfer.

- evidence: inherited from R52 (rank 14/17; parity and frame-definition argument); no new R54 computation
- validity: first order; structural
- novelty: NONE claimed (inherited identifiability statement)
- testability: MEDIUM
- robustness: structural
- risk: none
- kill criterion: an owned observable with a non-degenerate axial-vector column
- executed result: no column added in R54
- next action: state as an identifiability result

### H-L3b (L3) - PROMOTE

A constant fractional-H dipole is a gauge direction of a single distance-indicator sample (it equals a zero-point dipole).

- evidence: inherited R52 column identity; E09 states the same degeneracy
- validity: exact for one sample; several indicators only test for a common mode
- novelty: NONE claimed (inherited; stated in E09)
- testability: HIGH
- robustness: structural
- risk: none
- kill criterion: n/a
- executed result: per-family hemisphere steps are mutually consistent (p=0.867), as are the per-method dipoles (p=0.198); the common dipole itself has Wald p=0.43
- next action: R54-L04, R54-L06

### H-L3c (L3) - REJECT

Any type-I shear compatible with the CMB functionals is far below low-redshift sensitivity, so low-z STF2 signals are local or systematic within type I.

- evidence: late-time sensitivity of the two kernels (RESULTS/R54_L1_TYPE1_TE.json:data.late_time_shear_bounds)
- validity: counterexample inside type I: late-time anisotropic stress with a sign-changing shear (E44)
- novelty: n/a
- testability: done
- robustness: n/a
- risk: a family restriction read as a general statement
- kill criterion: n/a
- executed result: for a shear confined to z < 0.2 the T functional bounds a constant-sign history at 0.000227 and is blind to a sign-changing one; the E functional bounds its rms at 0.0735 (diagnostic lane; 0.0972 with the B-null floor), above the CF4 quadrupole of 2.5% of H
- next action: replaced by H-L3d

### H-L3d (L3) - PROMOTE

Without late-time anisotropic stress (perfect fluid or radiation-sourced stress histories) the type-I present shear allowed by the CMB functionals is orders of magnitude below low-redshift sensitivity; with late-time stress no such statement holds.

- evidence: three computed stress histories + late-time kernel sensitivity
- validity: type I; the three computed histories are not a class theorem; the E lane is diagnostic
- novelty: LOW (E44 treats late-time anisotropic stress in Bianchi I)
- testability: HIGH
- robustness: |s0| <= 6.66e-08 (massless two-mode) and 3.43e-08 (minimal normal ordering) against a CF4 quadrupole of 2.5% of H
- risk: dropping the condition
- kill criterion: a radiation-sourced history whose present shear reaches the percent level under the measured functionals
- executed result: late-time rms bound from E: 0.0735 (z < 0.2), 0.0113 (z < 0.5), 0.000697 (z < 2)
- next action: R54-L06 quotes the condition with every use

### H-L4a (L4) - HOLD

Classification at carrier level is the orbit type of the measured tensor (isotropic, axisymmetric, triaxial) by STF invariants; Bianchi-family identification stays blocked without a transfer atlas.

- evidence: stf2_invariants and the axisymmetry statistic (unit tests only)
- validity: exact invariants; no null calibration of the invariants on an owned carrier
- novelty: LOW (E26 gives the statistical theory)
- testability: MEDIUM
- robustness: eigen-axes of a marginal tensor are unstable (the axis moves under the zero-point split)
- risk: family overclaim
- kill criterion: the calibrated invariants cannot tell axisymmetric from triaxial at the measured noise
- executed result: CF4 constant quadrupole 2.5% of H, principal axis 9.5 deg from the equatorial pole (log estimator, exact body); family identification blocked
- next action: R54-L04, R54-L06

### H-L5a (L5) - REJECT

Conditional on linear theory without a selection model or a calibration covariance, the pooled CF4 window multipoles exceed the LCDM body.

- evidence: catalogue-level log-distance estimator + exact pair-sum body over 35970 groups
- validity: linear theory, redshift-space positions, no selection model, no calibration covariance
- novelty: LOW, pending R54-L07 (published bulk-flow tension E10-E13; E35 computes the CF4 velocity correlation; E43 uses the same estimator class)
- testability: HIGH
- robustness: joint null p: pooled 0.000344, method monopoles 0.00277, method x hemisphere steps 0.112; damped body 0.000155; body x2 0.188
- risk: the excess is strongest in the two outer windows, where the sample is northern FP
- kill criterion: survey-resolved zero points, a radial slope or a distance-error term bring the joint null above 0.01 (R54-L04)
- executed result: inner windows joint p=0.00558 (dipole 0.0375), outer windows joint p=3.89e-06 (dipole 0.000123); FP is 98% of the groups at z >= 0.055 and 95% of that FP sample is northern; R54-L04 decision check: REJECT (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL)
- next action: none (rejected by the R54-L04 decision check)

### H-L5f (L5) - PROMOTE

The R36/H03 linear-in-distance estimator carries a deterministic same-estimator bias (errors in variables plus the cosmographic trend) that mimics survey-locked multipoles.

- evidence: same-estimator mock with the operator rebuilt per draw; analytic exp(+s^2/2) check in the unit test
- validity: exact for Gaussian distance-modulus errors
- novelty: LOW (the log-normal distance bias is known, E41; E43 uses a log-distance estimator on CF4); new for this project's R36, H03 and R52 products
- testability: done
- robustness: bias carries 14-40% of the pole dipole; quadrupole null p 0.00343 -> 0.129; sky fraction 0 -> 0.0755
- risk: none
- kill criterion: n/a
- executed result: R36 operator reproduced from the committed source rows; log estimator unbiased in the unit test
- next action: use R54-EQ-34 everywhere; CF4 numbers of R36, H03 and R52 are superseded

### H-L5g (L5) - HOLD

The CF4 dipole excess is a hemisphere step of equal size in all four indicator families (a common mode rather than a single-survey calibration term).

- evidence: per-method hemisphere steps with the exact cross-covariance; hemisphere-split axis scan with the exact body
- validity: linear body; hemisphere is a proxy for survey labels; the sign(dec) axis was chosen after the first pass
- novelty: LOW, pending R54-L07: E43 fits per-catalogue dipoles with a log-distance estimator and finds larger dipoles for TFR and 6dFGS than for SDSS and SN; E09 and E33 find the TF dipole compatible with LCDM flows; specific here is the exact cross-covariance between families
- testability: HIGH
- robustness: consistency p=0.867; single-axis tail 0.0017; tail of the scan maximum over 151 split axes 0.0339; the pole ranks 1 of 151; jackknife pole dipole -3.6% to -3.1%
- risk: equal steps can have different causes (a 6dFGS versus SDSS zero point inside FP, local flows in the shallow TF and SN samples); the four estimates share the body (variance of the best single family / variance of the common step = 1.15); the step (z < 0.055) and the window excess (outer windows) are different measurements
- kill criterion: survey-resolved zero points absorb the step (R54-L04)
- executed result: common step -1.66 +- 0.53% of H; common-dipole Wald p=0.43; R54-L04 decision check: HOLD (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL)
- next action: R54-L06 joint tomography

### H-L5c (L5) - HOLD

The CF4 dipole-plus-quadrupole pattern is locked to the equatorial pole.

- evidence: exact body, unbiased estimator, null law drawn from the exact body under three zero-point nuisance models
- validity: same grid statistic for data and null draws; the answer depends on the nuisance model
- novelty: n/a
- testability: MEDIUM
- robustness: calibrated sky-fraction tail: pooled 0.0242, method monopoles 0.0085, method x hemisphere steps 0.147
- risk: the pole_locked flag fires in 17% of draws for an injected hemisphere step of the observed size (1% without injection), so a tail above 0.01 does not exclude locking
- kill criterion: survey-resolved zero points (R54-L04) put the tail on one side of 0.01 for every nuisance model
- executed result: first pass (ideal-sky body, linear estimator): 2.8 deg, sky fraction 0.0005; after the estimator bias is subtracted the sky fraction is 0.0755; class by nuisance model: EXCESS_NOT_POLE_LOCKED / UNRESOLVED_POLE_LOCKED / LCDM_BODY_COMPATIBLE; R54-L04 decision check: HOLD (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL)
- next action: R54-L06 joint tomography

### H-L5h (L5) - HOLD

A depth-independent fractional quadrupole remains after the method/hemisphere split.

- evidence: constant-tensor fit of the four windows
- validity: a posteriori statistic; selection and footprint systematics are not modelled
- novelty: n/a
- testability: HIGH
- robustness: Wald p=0.000146 pooled and 0.000489 after the split, but the 20-dof null has p=0.017
- risk: reading a footprint systematic as shear
- kill criterion: survey-resolved monopoles remove it (R54-L04)
- executed result: 2.5% of H; R54-L04 decision check: HOLD (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL)
- next action: R54-L06 joint tomography

### H-L5e (L5) - REJECT

A physical direction-dependent Hubble factor is detected in CF4.

- evidence: structural degeneracy (H-L3b) and the dependence of the excess on the zero-point nuisance model
- validity: a constant dipole is a gauge direction of distance-indicator data
- novelty: n/a
- testability: done
- robustness: n/a
- risk: detection-claim wording
- kill criterion: n/a
- executed result: joint null p from 0.000344 (pooled) to 0.112 (method x hemisphere steps marginalised); class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL
- next action: do not claim

### H-L6a (L6) - HOLD

Depth laws separate an observer boost or bulk flow (1/d), a zero-point or acceleration term (constant) and the LCDM stochastic body.

- evidence: CF4 execution with the exact body
- validity: linear
- novelty: LOW
- testability: HIGH
- robustness: not robust to inter-method zero points
- risk: none
- kill criterion: survey-resolved zero points leave no preference (R54-L04)
- executed result: delta chi2 (V - A) = 5.8 pooled, 0.592 after method monopoles
- next action: R54-L04, R54-L06

### H-L6b (L6) - HOLD

A single global tilt explains both the CF4 flow and a count-dipole excess.

- evidence: R52 + R54-L05 closure test
- validity: linear; the count side is the receipt estimator
- novelty: n/a
- testability: LOW until R54-L03
- robustness: count-side power against a doubled dipole is 0.20
- risk: rejecting on an underpowered count side
- kill criterion: the closure test rejects at p < 0.01 once the count side is calibrated (R54-L03)
- executed result: velocity term after the constant term: Wald 5.42/3; closure p=0.0895 / 0.0123 (preliminary)
- next action: R54-L03, R54-L06

### H-L6c (L6) - HOLD

Map-level aberration and Doppler-modulation estimators on owned CMB maps separate the observer boost from an intrinsic dipole inside this programme.

- evidence: published result E22 only
- validity: requires a high-ell estimator with simulated mode-coupling corrections that is not part of the owned products
- novelty: none (E22 did it)
- testability: LOW inside the stop rule
- robustness: n/a
- risk: scope growth
- kill criterion: n/a
- executed result: not executed; E21 and E22 enter R54-L06 as published anchors with their covariance
- next action: no new estimator; anchors only
