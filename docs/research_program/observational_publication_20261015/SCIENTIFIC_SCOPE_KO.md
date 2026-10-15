# Six-paper HTT observational programme: scientific scope contract

Date 2026-10-15 KST. This is a new publication-prioritized overlay, not a correction to already locked original research. Publishable refers to a TARGET and a stringent evidence gate, never a current claim of readiness. All six papers begin NOT_READY_TO_SUBMIT. Physical detections and observational null p-values are held until source-matched laws and calibration exist.

## Common observation contract

Metric signature (-,+,+,+), spatial epsilon_{123}=+1, and distinguish proper time / conformal time / redshift. Retain c in physical velocity, acceleration and optical response, and retain Planck thermodynamic temperature units until verified conversion. All kinematic terms in a physical identity use the same metric, u^a/congruence, epoch and matter/radiation rest frames.

The observational inverse problem is source-specific: raw released data y, selection S, calibration eta, foreground/null/systematics parameters nu, actual source transfer T and instrument/mask operator M generate p(y | M[T(psi)], S, eta, nu). Matching a reported C_l or apparent Hubble residual does not certify that T is the relevant Einstein-Boltzmann/Jacobi transfer.

All papers must fix: target estimand, observed release/product and immutable identity, operator/coordinates/frame, selected sample, covariance including cross-split and cross-window dependence, null/alternative and nuisance law, declared statistic/model comparison, injection recovery and covariance adequacy, baseline prior literature, and a reproducible observational figure. A null/negative result is valid if this evidence is supplied. Form-only packages and large PR counts are not publishable findings.

## P1: x, F, Pi, Q, G_F are different typed objects

Legacy Gauss/Friedmann budget, a conditional projection for one specified geometry-frame congruence:

    x_C = Sigma_G^2 - W_G^2 + Omega_tilt + DeltaOmega_k,
    Sigma_G^2 = sigma_ab sigma^ab/(6 H^2),
    W_G^2 = omega_ab omega^ab/(6 H^2),
    H = Theta/3.

The tilt term has a specific perfect-fluid source-frame form, e.g. Omega_tilt=(1+w) Omega_rest sinh^2(rho_RM) for one rest-frame fluid, and generalizes by sum_s under the appropriate common normal-frame stress decomposition. Rapidity rho is not the velocity fraction tanh(rho). Signed x_C is not a metric distance and may be negative. The curvature sign and same-congruence normal are not optional. Four-acceleration is NOT inserted as an arbitrary new positive term in this Gauss identity.

Historical scalar quotient Q = x_C / U_sigma where U_sigma=(3/2) B_sigma^2 is a registered shear-sector MES normalizer, positive on the defined domain. It is not a universally certified upper bound for total signed x_C (which includes tilt/curvature/vorticity). A new total anchor U_total requires its own physical proof; Q>1 does not by itself reject a cosmological model.

F is a samplewise normalized **sign-clean sector** fraction only where the registered positive sector ceiling U, sector amplitude and bounds make F admissible (original HTT/MIO diagnostics). F is not a material-volume occupation or a physical Bayesian model probability, and signed x_C cannot be clipped to [0,1] and relabeled F. Preserve the MIO owner/report firewall and HTT posterior owner. The bolometric exact angular moment F4=< (T/T0)^4 > and an observational forward map calligraphic F are distinct from the legacy filling diagnostic F.

Pi is the declared source-variable exceedance curve for a normalized coupled joint posterior/finite measure:

    Pi_Q(t) = sum_{i:defined} p_i 1[Q_i > t] plus unknown completion,
    sum_i p_i = 1, u = sum_{i:undefined} p_i,
    Pi_Q(t) in [ p_known_above(t), p_known_above(t)+u ].

Strict greater-than excludes exact threshold ties; posterior samples retain their original draw IDs, weights and cross-channel dependence. Pi is not an observed null p-value or probability that anisotropic cosmology is true. Analogous Pi_F and Pi_GF require their own declared source.

G_F is a **floor-stabilized depth contrast** between F values, only with specified depth bins, sky support, selection, common covariance, same normalization and a PREDECLARED positive floor delta:

    G_F = exp(log(max(F_comparison,delta)) - log(max(F_reference,delta))).

G_F does not classify local/global tilt, Bianchi family or geometric anisotropy. A real-data paper needs an actual observational likelihood or defensible partial-identification interval, not a table of mathematical helper outputs.

Sources: docs/PR_DELTAS/pr-066.md; htt/htt/htt/departure/posterior_pushforward.py; htt/mio/formalism/filling_fraction.py; htt/mio/formalism/isotropy_gap.py; docs/observational_upgrade_r2/R2-04/sources/research/LEGACY_THEORY_REUSE.md; docs/research_program/theory_obs_application_20261015/loop7_typed_defect/THEORY_LOOP_KO.md (last is local owner-untracked source, not part of branch).

## P2: morphology/anomaly rather than immediate cosmology identification

A single sky has real-harmonic temperature coefficients, genuine physical spin-2 E/B, mask/beam/noise and high-l transfer. Scalar temperature Q/U projection is not a substitute for a polarized E/B map. Matched simulation ranks need one independent latent realization per unit and the same source processing on observation and null. FFP10 999 CMB + 300 noise in the prior Loop9 is a conditional fixed-weight bank; it supplies a quantified mask effect but not full Planck end-to-end null exchangeability. A historical p=.039 and all method-dependent retrospective ranks remain historical, never combined as nine independent skies. Report invariant O(3) morphology with orientation-based features tracked separately; high-l leakage, trial choice, missing sky and sample size are part of the result.

Planck 2018 VII primary: https://doi.org/10.1051/0004-6361/201935201 .

## P3: H(z,n) is an observational estimator before being H=Theta/3

Distinguish H_W(z,n) inferred from redshift/distance sky windows from physical local expansion H and q. A fixed-distance illustrative linear law y_i=cz_i=n_i.B+r_i[H+n_i.A_H+n_i n_j S_H,ij]+rem_i demonstrates window leakage. B is km/s, H, A_H and S_H are km/s/Mpc. These fitting A_H and S_H are phenomenological angular coefficients, NOT material four-acceleration or geometry-frame shear without optical transport. An isotropic angular selection makes the monopole leakage vanish under symmetric design; incomplete masks do not.

Distance modulus/calibration/selection/peculiar velocities must be modeled in their appropriate forward likelihood, and overlapping depth bins/cross-method shared galaxy sources are correlated. The 35,970-group conditional STF and Schur rank result tests only a fixed Gaussian fitting operator. A full survey source law must be separately validated. The novelty gate explicitly demands comparison to 2024–26 studies with conflicting local H0-anisotropy conclusions.

Primary comparators: https://arxiv.org/abs/2412.14607 ; https://doi.org/10.1051/0004-6361/202556645 ; https://academic.oup.com/mnras/article/546/2/staf2048/8436862 ; https://arxiv.org/abs/2512.02526 .

## P4: source-frame observer motion versus global tilt

Distinguish radiation-observer velocity beta_RO, radiation-matter beta_RM, matter-observer beta_MO (and their finite Lorentz composition) and a finite survey-window bulk B_W. Convert v/c to rapidity rho=atanh(v/c), never insert a velocity fraction into sinh(rho) directly. The raw Solar CMB dipole is dominantly an observer motion and cannot be substituted as a cosmological intrinsic MES epsilon1.

Under an actual data covariance C and nuisance response N, the rank/robust singular values of projected distinct physical responses decide identifiable differences; duplicating the same endpoint observer boost as a global-history response makes a tautological nullspace. A joint likelihood requires source-frame histories and cross-probe selection, not just separate CF4 and CMB posterior means. Polarization, remote dipole/kSZ, noncollinear redshift/source windows may improve identification but require actual data response and astrophysical velocity/optical-depth modeling.

## P5: Bianchi identification is physical and source-based

Only mode- and initial-data-complete external Einstein–Boltzmann transfer with correct geometry/curvature convention, realistic T/E/B and polarization/recombination, and source-selected Planck likelihood permits a family result. Distinguish 11 canonical classes and the VI_-1/9 exceptional branch, not 12 independently admitted classes. Eigenaxis degeneracy and SO(3)/O(3) equivalence may leave families observationally identical. Evaluate type equivalence under an identical observation law and prior model selection, never from raw template orientation alone. A verified subset paper is preferable to falsely complete all-11 classification.

Baseline: Saadeh et al 2016 PRL https://doi.org/10.1103/PhysRevLett.117.131302 ; framework https://doi.org/10.1093/mnras/stw1731 .

## P6: what of sigma, omega, A, beta is observed?

For one u^a, sigma_ab is trace-free symmetric spatial shear (s^-1), omega_ab is antisymmetric (s^-1), omega^a=(1/2)epsilon^{abc}omega_bc is an axial spatial pseudovector, A^a=u^b nabla_b u^a is four-acceleration (m/s^2 with physical normalized 4-velocity convention), and beta_a is a typed matter/radiation frame-relative tilt vector, with v/c and rapidity separated. At first order a radial velocity gradient n^i n^j nabla_i v_j is insensitive to antisymmetric omega_ij exactly: n^i omega_ij n^j=0. A radial-only apparent Hubble quadrupole cannot measure vorticity.

The distance-modulus angular dipole is not A_a. Local STF2 fitting coefficients are not sigma_G_ab/H until a same-congruence optical/Jacobi transfer, sky/selection covariance, observer motions, and source clock are supplied. Where rank=0, report undefined/unbounded identified set, not a constructed narrow prior interval. A publishable analysis may measure only an identified subset and give well-calibrated upper limits/no-identification results on other modes.

Original MES low-l bounds require all fundamental observers' multipole spatial/time derivative controls and are not measured simply from one Planck sqrt(C_l)/T0. Local Loop9 provides the correctly normalized SAG PSTF conversion and quantifies finite mask leakage, but cannot supply the Copernican hypotheses. Sources: https://arxiv.org/abs/astro-ph/9501016 ; https://arxiv.org/abs/astro-ph/9904346 .

## Shared mandatory release & submission gates

A paper is ready only if:
1. All six evidence categories source, claim, physical/working observation law, uncertainty/coverage, independent comparator, and artifact/reproduction have direct receipts.
2. Statistical null/source windows and look-elsewhere selection are explicitly matched; signal processing variants of one physical sky are not independent samples.
3. Report includes actual figure, numerical tables (including negative and failed tests), reproducible commands/config/version/source manifest, and model/parameterization uncertainty.
4. One scoped technical verification and at most one justified independent adversarial review closes material findings. Completion of tests does not substitute for scientific likelihood validity.
5. No user-requested main merge, journal submission, or automatic publication is inferred from this research DAG.

Result classes: OBSERVATIONAL_PHYSICAL_SUPPORTED, CONDITIONAL_WORKING_LAW, SIMULATION_DIAGNOSTIC, MATHEMATICAL_DERIVATION, INPUT_BLOCKED. Each manuscript claim receives a class; only observational-physical-supported classes with justified scope can be represented as actual physical constraints. Positive null results and robust negative results are both publishable when novel and calibrated.
