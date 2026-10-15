# HTT six-paper publication DAG: simultaneous P1/P2/P3 scientific continuation

Date: 2026-10-15 KST, branch: research/htt-observation-lanes-20261015,
parent commit 58bb3fa00093e36b5915c8ba87f03d7b14568bd8.
Original repo checkout /home/cosmosapjw/Dropbox/bianchi/htt_base
HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54 and 57 dirty paths
unchanged. Only local tool execution, NO external local Codex, native subagent
NOT_RUN because no native spawn tool was available. Independent source paths,
tests and scripts were executed in separated local processes wherever safe.

## Lane P3 H01/H03: actual Cosmicflows-4 observed-source estimator

**Definition.** For each distinct released CF4 group, use z_i=Vcmb_i/c as
an observed redshift proxy, DMzp_i in mag, and D_i=10^[(DMzp_i-25)/5] Mpc.
Let

    h_i = log( (cz_i / D_i) / (1 km s^-1 Mpc^-1) )
        = log(c z_i) - (ln 10)/5 (DMzp_i-25).

This definition is exact algebra for the proxy, not a flat-LCDM physical
H(z)=Theta/3. No cosmic acceleration, shear, vorticity, global tilt or q(z)
has been measured by this estimator.

Under a *fixed conditional working law*, sigma_hi^2 =
[(ln10)/5 sigma_DM_i]^2 + [sigma_v/(c z_i)]^2, sigma_v=250 km/s
independent per group. This adds diagonal velocity scatter as an assumed
working error, not a calibrated cosmic velocity covariance. For each predeclared
window W with selected groups, a normalized row is

    L_Wi = 1[i in W] sigma_hi^-2 / Sum_j 1[j in W] sigma_hj^-2.

H_eff,W=exp(Sum_i L_Wi h_i) km/s/Mpc, with formal diagonal-law covariance
C_WV = Sum_i L_Wi sigma_hi^2 L_Vi.
Nested W and V share group IDs, producing correlation, even under a diagonal
conditional input covariance.

Derive the first-order Doppler/angular-response nuisance mixing:

    delta h_i = (n_i.B)/(c z_i) + n_i.D + n_i^a n_i^b S_ab + ...,
    k_B^a(W)=Sum_i L_Wi n_i^a/(c z_i)       [(km/s)^-1],
    k_D^a(W)=Sum_i L_Wi n_i^a                [dimensionless],
    k_S^{ab}(W)=Sum_i L_Wi(n_i^a n_i^b-delta_ab/3).

A_B is NOT four-acceleration. S_ab is an apparent angular log-H quadratic
response, NOT geometry sigma_ab/H. Observed source J2000 angles used; no
equatorial/Galactic rotation or physical aligned-mode inference is made.

**CAS:** Wolfram exact cube-corner test n=(±1,±1,±1)/sqrt3
and survey weight 1+(1/2)n_z has <n>=(0,0,1/6) and <nn-I/3>=0,
showing that survey direction selection leaks bulk flow to a Hubble monopole.
n Omega n=0 for every antisymmetric Omega, so radial flow gradients cannot
alone identify omega. Python injection tests validate these exact discrete
identities at observed floating-point roundoff.

**Actual 35,970 grouped source** (published selected source file hashed SHA256
86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c):

| z bin | group count | conditional geometric H_eff [km/s/Mpc] | ||k_B*300 km/s|| | ||k_D|| |
|---|---:|---:|---:|---:|
| [0.01,0.03) | 8581 | 74.08727 | 0.0068618 | 0.14870 |
| [0.03,0.05) | 7833 | 73.68044 | 0.0082371 | 0.32502 |
| [0.05,0.075) | 8818 | 71.31156 | 0.0100944 | 0.64378 |
| [0.075,0.10) | 10738 | 68.88624 | 0.0086809 | 0.73610 |

The FT/FP method composition changes drastically with depth:
- First bin FP1826, TF5981 (OTHER487, SN287);
- Last bin FP10653, TF14 (OTHER8, SN63).

Omitting FP from the most distant shell leaves only 85 groups, below the
predeclared min100 source-method-out check, so that check is preserved as
UNSUPPORTED and not reclassified into a zero/valid interval. The 4 disjoint
bins are formally uncorrelated under the *incomplete diagonal working law*,
but cumulative [0.01,0.05), [0.01,0.075), [0.01,0.10) strongly correlate
with other bins: for the last two cumulative bins correlation≈0.877.
The very small reported diagonal-law errors are NOT physical confidence
regions for H0 or cosmological acceleration; actual selection, shared
method zero-points, peculiar velocity and cosmic covariance are absent.

Source results:
results/H01_actual_cf4_v1/result.json,
cf4_hubble_window_trajectory.png,
REPORT_KO.md. H01 and narrow, conditional H03 outcomes are implementationally
executed. H02 empirical method selection remains BLOCKED_EXTERNAL and
prevents subsequent H04 physical/model comparison.

**Literature**: Tully et al 2023, ApJ 944:94 DOI 10.3847/1538-4357/ac94d8;
Stiskalek et al 2026, MNRAS 546:staf2048; Boubel 2024/25 arXiv:2412.14607;
Karim et al 2026, arXiv:2512.02526; Desmond et al 2025,
arXiv:2511.03394. Their existing radial-selection/peculiar covariance work
is an essential baseline; measured decline in this source diagnostic is
**not evidence of anisotropic cosmic expansion**.

## Lane P2 L01: actual Planck masked thermal high-mode response

Native mask from actual Planck 2018 SMICA HM/OE/official common Int FITS,
source FFP10 gate SHA 86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb,
NSIDE=2048 NESTED -> NSIDE64 RING common selected 26,846 temperature
pixels. Nine Planck products are ONE sky; analysis here is one gated actual
observed SMICA map and 48 uniquely identified but conditional FFP10 simulation
CMB maps, with a **shared** response operator. Simulations are descriptive
physical-source-conditional but not proven exchangeable with actual sky.

Y_lm real orthonormal basis, simultaneous estimator with ell0..ellmax,
no nuisance prior or forward polarization response:

    alpha_hat=(X_M^T X_M)^(-1) X_M^T y_M,
    L_high_to_low = [(X_0..5,M^T X_0..5,M)^(-1)
                     X_0..5,M^T X_6..ellmax,M]_(ell2,ell3 rows).

Nested high-mode inclusion makes norm(L) nondecreasing for a fixed
ell<=5 projector, since added columns increase L L^T by PSD blocks.
However the actual observed data's low-l fit may move nonmonotonically
when simultaneously marginalizing increasing high-ell sets.

Actual SAG-normalized epsilon_l (dimensionless, conditional projected-source)
measured as follows:

| ellmax fit | eps2 | eps3 | finite operator highmode norm |
|---|---:|---:|---:|
| 5 | 1.0704566e-5 | 2.1863310e-5 | 0 |
| 8 | 1.2518270e-5 | 3.2546558e-5 | 1.477612 |
| 10 | 1.1298973e-5 | 2.9296632e-5 | 1.593253 |
| 12 | 1.4843735e-5 | 2.4822258e-5 | 1.658653 |

The saved first48 FFP10 conditional sky pairs have RMS eps(lmax12)
minus eps(lmax5) ≈ [6.074735e-6, 5.076312e-6].
Neither lmax12 fit nor the high-mode operator norm are beam-deconvolved
true-sky multipoles or globally bounded remainder for ell>12. It shows
**truncation/source-processing sensitivity**, not independent detection
of Planck anomalous CMB morphology, not a calibrated Planck p. Full spin2
E/B/foreground/source-specific beam admission still missing, so L01
**PARTIAL_EXECUTED_PENDING** rather than complete.

Executed files: htt/obsstat/publication_lowell_response.py,
scripts/run_htt_planck_highmode_l01.py,
tests/obsstat/test_publication_lowell_response.py;
results/L01_actual_planck_v1. The initial runner failed because the
prior MES epsilon function accepted exactly 36 coefficient columns and
a higher-lmax result was supplied without projection. Corrected the
science-facing projection to the original first 36 columns and reran
without changing source harmonics. All 5 focused L01 tests passed.

References: Planck Collaboration IV, A&A 641 A4 (2020)
https://doi.org/10.1051/0004-6361/201833881;
Planck Collaboration VII, A&A 641 A7 (2020)
https://doi.org/10.1051/0004-6361/201935201.
The original Planck null splitting uses correlated source/systems; no
new confirmatory anomaly p is produced here.

## Lane P1 S01: typed statistical functionals (mathematical oracle only)

Following original HTT legacy and PR066/PR521, four named samplewise
dimensionless Gauss sectors must be available in ONE geometry/matter frame:

    x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k

with Sigma2>=0, W2>=0, nonnegative perfect-fluid tilt where adopted,
and signed curvature. Omega_vorticity is subtracted, not added.
Four-acceleration is NOT an arbitrary fifth positive Gauss budget term.

Q=x_C/U_sigma only with U_sigma>0; zero/missing denominator makes Q
undefined, not Q=0 or a separate truth probability. In the historical
MES branch U_sigma=(3/2)B_sigma^2 is a SHEAR ceiling, NOT a total-x bound.
F is separately a nonnegative, sign-clean sector fraction of its actual
sector ceiling; F4=<T^4>_sphere/T0^4 is NOT F.

For a finite joint weighted sample with normalized weights w_i,
let D=known Q atoms, U=sum_{i outside D}w_i. For every threshold t:

    known_strict(t) = Sum_{i in D} w_i 1[Q_i>t],
    Pi_Q(t) in [known_strict(t), known_strict(t)+U].

Proof: the event over undefined atoms can contribute between zero and
their total weight U. This is a conservative outer completion envelope;
it is NOT a null p-value, Bayesian probability of FLRW failure or
geometry/family classifier. At exact threshold ties, the comparison is
strictly > (no epsilon perturbation of the rule).

Let F_ref and F_cmp be separate depth-mean fractions and positive
predeclared floor delta. G_F=max(F_cmp,delta)/max(F_ref,delta).
Where either mean has partial interval [lo,hi] for missing samples,
the outer interval for G_F is

    [ max(F_cmp_lo,delta)/max(F_ref_hi,delta),
      max(F_cmp_hi,delta)/max(F_ref_lo,delta) ].

The monotone ratio gives a valid conservative enclosure, not necessarily
an optimal joint partial identification interval because unknown atoms
may share correlations across both bins.

The focused Python test suite has 10 cases (signed x, denominator zero,
missing sector, mixed congruence, strict atom tie, distinct depth
floor, MIO firewall, mass normalization). The executed finite
three-atom example is SYNTHETIC ONLY, with undefined Q mass=1/4
and G_F outer interval ≈[0.488889,1.68]. No Planck/CF4 observational
posterior has been supplied to S01, so it is a mathematical domain
and implementation contract and cannot be presented as a numerical
measurement of x or Q. S02 is the next natural publication node.

## Cross-repository theory reuse, read-only at pinned local identities

**rec_bianchi** local HEAD 5694a5c, source path
docs/continuation-20260930/SCREEN_BRIDGE.md and
rust/rec_microphysics/src/screen.rs. Its photon normal/material local
screen transformation for a source ray has D=gamma(1-beta dot e_n),
E_m=D E_n, a 2x2 orthogonal polarization screen overlap T, and
coherency F_m=T F_n T^T. Correct physical clock conversion occurs
once, after rotating the source collision block, not mixed into the
screen overlap. This is a relevant FUTURE source-physics adapter for
P4 observer/global tilt and P5/P6 polarization, but the module explicitly
does NOT implement line-of-sight Bianchi history, Stokes conventions,
or source-conditioned Planck likelihood. The local branch was behind
its remote by six commits on inspection, so do NOT assume it represents
the newest remote version without readback.

**rei_bianchi** local HEAD 0fcb2ddd, SOURCE07 C8 experiment:
positive multistate age quadrature retains 8/36 manufactured nodes,
with holdout heat max relative error ~4.33e-11 in its scoped synthetic
gas-state oracle. This informs optional future source-history
acceleration of reionization transport, but is neither cosmological
T/E/B atlas nor validated opacity/physical CMB likelihood.
Scientific bridge to P5 remains blocked, not silently imported.

## Precise remaining first-order obligations

P2 L01: native matched released beam/filter high ell covariance and
physical E/B spin2 response, followed by matched null. P3 H02: CF4
selection/zero point/cosmic peculiar velocity covariance; H_eff(z,n)
may move when method composition changes. P1 S02: actual physical
coupled posterior/identified-set measure with preserved undefined
sectors, not nine process variants as nine universes. P4 V03 and P5
B02 remain blocked on source-validated global tilt/history and native
polarized atlas. The mathematical no-radial-vorticity identity does
NOT license physical omega measurement.

Scope status: S01, H01 and H03 are implemented and source-conditional
where applicable; L01 is TEMP_SOURCE_OPERATOR_PARTIAL, not physically
complete. No journal manuscript is READY_TO_SUBMIT.


## Lane P6 K01 scoped actual-source angular rank (new local check)

Computed on the exact prior CF4 selected 35,970 J2000 unit lines of sight
under the explicitly **Euclidean, first-velocity-jet** operator.
G_ij=partial_i v_j=(Theta/3)delta_ij+sigma_ij+omega_ij with omega antisymmetric
and epsilon123=+1. For n unit, n_i n_j omega_ij=0 identically.
The 5 STF columns on this nonuniform sky have singular values
[87.79846193, 82.61720389, 69.92508587, 49.44057701, 45.95584202],
rank 5; three antisymmetric columns return exact zeros/rank 0.
Synthetic frame-rotation, orientation and jet-reconstruction tests pass.

This only classifies angular sensitivity of an idealized local spatial
velocity-gradient operator, NOT true GR kinematics measured from CF4,
and says nothing directly about time-dependent four-acceleration or
material-vs-radiation tilt. K01 remains PENDING for the full proper-frame
optical bridge; it has usable partial theory and numerical evidence.
Actual source artifact:
results/K01_actual_cf4_radial_oracle_v1/result.json.
