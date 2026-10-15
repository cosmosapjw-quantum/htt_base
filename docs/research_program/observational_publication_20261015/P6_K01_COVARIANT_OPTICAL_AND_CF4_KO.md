# HTT K01: 1+3 covariant photon energy operator and real CF4/Planck source geometry

2026-10-15 KST. Parent commit 47d1b0a8434a65becd46ef9ff996df8a2f6a7649, independent branch research/htt-k01-covariant-optical-20261015. This research combines original legacy HTT kinematic beyond-FLRW x, F, Pi, Q, G_F programme; modern 1+3 covariant/STF and Lorentz observer-vs-tilt frame; and actual 35,970 grouped Cosmicflows-4 look directions plus nine source-dependent products of ONE physical Planck CMB sky.

## Exact covariant one-event optical derivation

Use metric (-,+,+,+), spatial epsilon123=+1, unit timelike congruence u^a, acceleration A^a=u^b∇_b u^a, h_ab=g_ab+u_a u_b, Theta=∇_a u^a, shear sigma_ab, antisymmetric vorticity omega_ab.

  nabla_a u_b = -u_a A_b + (Theta/3) h_ab + sigma_ab + omega_ab.

At one local orthonormal tetrad, u^a=(1,0,0,0) and photon future null k^a=E(u^a+e^a) with e^a unit spatial PROPAGATION. Energy E=-u_a k^a. Since k^a ∇_a k^b=0,
  dE/dlambda = -k^a k^b ∇_a u_b
             = -E² [Theta/3 + A_a e^a + sigma_ab e^a e^b].
For observer proper time increment dt_u/dlambda=E, this gives

  -d ln E/dt_u = H + A_a e^a + sigma_ab e^a e^b,
  H=Theta/3.

Sky LOOK direction n from observer to source is opposite incoming photon propagation: e=-n. Therefore

  -d ln E/dt_u = H - A_a n^a + sigma_ab n^a n^b.

This is the exact one-event coefficient operator in units of s^-1, not a direct numerical estimate of the observed CMB temperature quadrupole or CF4 luminosity-distance H_eff(z,n). Omega enters the photon direction evolution and the time-integrated optical calculation but cancels in the instant energy contraction:
  n^a omega_ab n^b=0.
Wolfram exact symbolic expansion of n^T omega n returned zero for generic n and three independent omega modes, generic symmetric trace-free sigma produced only even quadratic harmonics. This is a local algebraic lemma, NOT a global vorticity no-go.

The dimensionless normalized shear is Sigma=|sigma|/H with |sigma|=sqrt(sigma_ab sigma^ab/2), only for H>0 in the present expanding-cosmology lane. For later Bianchi/tilted runs, all tensor entries must be fixed to one common congruence; an apparent galaxy velocity STF, processed CMB quadrupole, or observer boost is not a geometric shear measurement.

## Real Cosmicflows-4 sightline geometry and synthetic physical 1+3 injection

Read existing source-verified 35,970 CF4 GROUPED directions n_J2000 and source redshifts z_CMB from selected_source_observables.npz SHA-256 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c. The source n is LOOK, and the photon's e=-n sign is explicit.

Physical *one-event* design columns [H, 3 acceleration A, 5 STF shear sigma, 3 antisymmetric omega]. The 35,970×9 H/A/STF design has rank **9**, condition **5.3660955182**, and singular values
[226.5250, 118.4896, 97.0104, 86.3553, 61.4614, 56.8373, 52.2071, 46.7204, 42.2141].
Three omega columns are identically zero, hence rank0. The five STF column singular values exactly reproduce earlier K01 Euclidean source-geometry oracle: [87.79846,82.61720,69.92509,49.44058,45.95584]. Angular acceleration dipole -n and a *hypothetical* local observer boost dipole n span the same three-dimensional angular space but have different source transfer and units: A [s^-1] versus beta=v/c dimensionless. This is NOT a physical local-vs-global tilt no-go.

Synthetic rates were injected into these REAL directions (NOT fitted to distance data): H=74.6 km/s/Mpc, A=(2,-4,1) km/s/Mpc, sigma STF coefficients=(1,-2,3,0.5,-1) km/s/Mpc, omega=(5,-7,9) km/s/Mpc. The resulting Sigma=0.03701528491 is a **manufactured test value** only. Least-squares re-extraction across 35,970 source directions recovers all nine injected angular coefficients with max error 2.84217e-14 km/s/Mpc. Full 4×4 tetrad contraction versus decomposed angular design max residual 1.92593e-33 s^-1; turning off the nonzero omega changes the source optical drift only by 1.15556e-33 s^-1. Original Euclidean first-velocity-jet angular rate n_i G_ij n_j/MPC_KM matches the geodesic acceleration-zero limit to 1.54e-33 s^-1. These are strong code/theory local-limit identities but NOT a real GR kinematic inference from CF4.

## Redshift-dependent angular survey selection

The CF4 source bins were kept disjoint (0.01–0.03, 0.03–0.05, 0.05–0.075, 0.075–0.10), all z_CMB, total 35,970 groups. The first moment ||<n>_W|| and STF second moment ||<n_i n_j>_W-I/3|| are directly source-measured sky-coverage geometry:

| redshift | actual groups | ||mean n|| | ||STF second moment|| |
|---|---:|---:|---:|
| .010–.030 | 8,581 | 0.13138785 | 0.21482180 |
| .030–.050 | 7,833 | 0.27273491 | 0.21589712 |
| .050–.075 | 8,818 | 0.69102270 | 0.38987558 |
| .075–.100 | 10,738 | 0.77914123 | 0.39212556 |

For the *hypothetical one-event* rate, the actual angular survey bin monopole obeys exactly
   <y>_W = H - A·<n>_W + sigma_ij[<n_i n_j>_W - delta_ij/3].
This demonstrates how REAL depth-dependent sky selection generates different response to the SAME injected A/sigma even without physical evolution of A/sigma with z. Source numerical examples for the manufactured amplitudes are in result.json: the synthetic monopole y/H ranges from 1.0022786843 to 1.0076352727 across the four source windows. These are not observed redshift-dependent Hubble deviations; the true CF4 distance indicator, source selection, velocity covariance and photon optical transport are not included.

## Planck/CMB angular source chart: an independently verified *nonphysical joint* bridge

The observed Planck processed l2 real coefficients are in a **Galactic** spherical harmonic frame, while the CF4 n_J2000 look directions are **ICRS**. Used Astropy SkyCoord to rotate all 35,970 actual source directions ICRS→Galactic before comparing them with the modern Planck l2 STF *TEMPERATURE* tensor \(Q^{(T)}_{ij}\). The angular pattern q(n)=n_i Q^{(T)}_ij n_j is a deterministic source product.

SMICA_FULL real source:
  full-sky ell2-only RMS DeltaT/T0 = 3.90878762058e-6;
  CF4 selected sky-sampling RMS = 2.93648784662e-6;
  CF4 selected-source angular mean = +8.202952222995385e-7.
The CF4 angular-sampling mean is not zero because the actual galaxy sky window is not uniform, even though an STF quadrupole has zero *full-sky* angular mean. In source shells, this mean varies from -1.5788e-7 to +1.3520e-6. THIS IS NOT an observed Planck-CF4 correlation, a gravitational shear amplitude or a new independent likelihood. The actual Planck nine processing maps are ONE physical CMB sky and inherit shared foreground/beam/covariance. The corresponding Galactic STF and real spherical harmonic spatial evaluation on 50 actual rotated CF4 sightlines agree under a direct independent chart test.

## Scientific output and downstream DAG

K01 scientific contract concerns ONE u^a, Theta/sigma/omega/A and their units, and the radial vorticity-null counterexample, not final calibrated galaxy or CMB inferences. It is now mathematically/source geometrically completed in scoped sense, with new exact tetrad kinematics and actual-sightline inject/recovery, without modifying legacy MES authorities (legacy vs current Bomega normalizers differ by ~375–379×).

K02 becomes the next READY P6 observation task: determine which linear combinations of the actual CF4 *apparent* STF can relate to a qualified physical optical response given selection, congruence and redshift kernels. K03 remains externally blocked for physically matched nonradial curl, acceleration and tilt signal; K04 physical posterior blocked by survey selection/cosmological optical likelihood. No new observational physical shear/omega/A/beta detection, no Bianchi family identification and no paper submission is claimed.

Code:
htt/obsstat/covariant_optical_kinematics.py
scripts/run_htt_covariant_optical_cf4_planck.py
tests/obsstat/test_covariant_optical_kinematics.py
tests/obsstat/test_htt_k01_covariant_source_acceptance.py

Canonical new result:
docs/research_program/observational_publication_20261015/results/K01_covariant_optical_CF4_Planck_v1/ (result.json, source_sky_operator_geometry.npz, CF4 sky window diagnostic figure, REPORT_KO.md). Based on source-gated prior K01 Euclidean result, CF4 NPZ and Planck original retained one-sky low ell NPZ. The original repo 57 dirty paths remained unchanged.

Sources: Ellis & van Elst, "Cosmological Models (Cargèse Lectures 1998)" arXiv:gr-qc/9812046, sections 2.1.2 and 8.3–8.4; Stoeger–Araujo–Gebbie (1997) astro-ph/9904346; the original legacy 2026 HTT x/F/Pi/Q/G_F reports; Cosmicflows-4 Tully et al. ApJ 944 94 (2023), doi:10.3847/1538-4357/ac94d8; Planck 2018 IV A&A 641 A4 (2020), doi:10.1051/0004-6361/201833881; prior real K01 and finite observer-boost V01 local branch.

native_subagent NOT_RUN (no native dispatch exposed); local Codex NOT_USED. This is one bounded physical theory and scientific coding cycle; no automatic global physical posterior inference or submission.
