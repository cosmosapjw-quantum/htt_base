# R107 cloud: theory foundations for the open nodes

Start commit `bd0c6f492955b7311f369f93cf0c4ed547984f6e` (R106). Each section states
what is established (with source), what this round derived, how it was checked, and
what it does not establish. Numbers come from `RESULTS/HYBRID_LOS_CONVERGENCE.json`,
the R107 tests, or the cited R105/R106 files.

## TF1. Exact-characteristic line-of-sight solution for homogeneous Bianchi skies (B02, SQ-NATIVE)

Established: in a spatially homogeneous background the photon transport equation is an
advection on the sphere of directions plus a redshift factor and a collision term; its
characteristics are the null geodesics of the homogeneous tetrad, and the formal
solution along them is the line-of-sight integral (Seljak and Zaldarriaga 1996 for the
idea; the native operator `GeneralLieStokesOperator` already uses these geodesics for
its Lie advection and screen twist).

Derived here: with X the native quarter-intensity Stokes increment (T channel
(I/Ibar - 1)/4), the native equation is
dX/dN = M_Lie X - 4 sigma_ij n^i n^j (1/4 + X) + kappa (1 + n.beta) [S_f - (1/4 + X)].
Writing Y = 1/4 + X removes the shear source: the background term is the -4 sigma n n
multiplier acting on 1/4. Along a backward characteristic the energy ratio obeys
d ln E/dN = -(1 + sigma_pp) because Gamma^0_ab = theta_ab in the normal frame
(class-B structure constants do not enter), so Y_obs = Y(N') exp(-4 Delta) with
Delta = ln(E/E_obs) + N'. Polarization is carried in the parallel-transported Sachs
basis, which is rotated by chi from (e_theta, e_phi) of the local sky direction, so
(Q + iU)_Sachs = exp(-2 i chi) (Q + iU)_local. The source function per unit directional
depth is J/(1 + n.beta) with J the native gain (rank-9 Thomson for rest electrons, the
`MovingCollisionStage` gain plus net background scatter-in otherwise). Between nodes
the source is taken linear in optical depth; the exact weights are
a = (1 - e^-d) - r and b = r with r = (1 - e^-d - d e^-d)/d.

Checked (tests in `htt/bass/transport/test_hybrid_los_transfer.py`):
- Bianchi I with constant H-normalised shear: observed T equals the closed form
  (e^{-4 Delta} - 1)/4 with Delta = (1/2) ln sum_i n_i^2 e^{-2 s_i N_E} to < 1e-10, and the
  emission direction equals the conserved-momentum direction to < 1e-10.
- FLRW static source: T, Q, U, V reproduced to machine precision.
- Boosted blackbody behind a thick shell with moving electrons: reproduced to 1e-12;
  observed dipole -n.beta to second order in beta.
- Class-B (VII_h-like) geometry with a finite tanh recombination: line of sight versus
  native hierarchy at ell <= 4 agrees to 2e-6 (T) and 1e-4 (E, B); the residual falls by
  about 4 when the node spacing halves (second order), so it is discretisation error.
- Intermediate observer (`history_window`): native state at N = -3 reproduced (T 1e-4,
  E 1e-3), which gives independent photon moments at matched solver times.
- Native and HEALPix (T, E, B) harmonic conventions agree to 1e-14.

Not established: agreement with an external solver on a physical family (TF4), a
qualified null, any family attribution.

## TF2. Truncation of the source (why ell <= 2 or 3 suffices)

For rest electrons the Thomson gain G = U diag(1, 7/10 x5, 1/2 x3) U^T has rank 9: it
emits only the T monopole, the (T2, E2) combination and the V dipole. Hence the
line-of-sight source is band-limited exactly at ell = 2, whatever the native L; all
higher-ell structure of the observed sky comes from the characteristics. Moving
electrons add components of order beta^ell; `los_sky` measures the discarded norm on
every node and fails above `max_source_truncation` (default 1e-8).

## TF3. Native truncation estimator

Because the line-of-sight result needs only the native ell <= 2 source, the difference
between it and the native hierarchy at ell <= L/2 measures the hierarchy truncation.
Synthetic focusing class-B geometry (a/H = 0.3, n/H = 0.6): native L = 8 deviates by
1e-2 to 2e-1 at ell <= 4 (T4 0.11, E4 0.19), L = 12 by <= 4e-3, L = 16 by <= 1.6e-4.
Weak geometry (a/H = 0.05, n/H = 0.3): L = 8 is already converged. The R105/R106
production runs used L = 4 to 8; each family run should report this estimator.
Line-of-sight convergence (same file): Nside 32 versus 64 changes C_ell by <= 5e-5
(ell <= 56), ray step 0.02 versus 0.01 by <= 1e-6, node doubling by <= 5e-3 (EE, BB)
and 7e-4 (TT). Cost: 31 s for 49,152 rays and 301 nodes on one core.

## TF4. Independent comparator for Bianchi VII_h and the parameter dictionary

Established: the Barrow, Juszkiewicz and Sonoda (1985) temperature template for open
dust VII_h, in the form of McEwen et al. (2006, MNRAS 369, 1858, appendix A,
eqs. A1-A12), used by the WMAP and Planck isotropy analyses. Kogut, Hinshaw and Banday
(1997) print the C2 bracket of A with the opposite sign of the 3 sqrt(h) sin psi_E term
and combine A sin phi + B cos phi. Both variants are implemented
(`htt/bass/transport/bjs_bianchi_vii_h.py`); their maps differ.

Derived here (dictionary to the native H-normalised Lie variables, isotropic limit):
for a_b = a e_z and n_ab = diag(n, n, 0) the spatial curvature is
3R = -6 a^2 - (1/2) tr(n^2) + (1/4) (tr n)^2 = -6 a^2 (Jacobi n a = 0), so
1 - Omega = Omega_k = (a/H)^2; the class-B parameter of VII_h is h = a^2/(n_2 n_3) =
(a/n)^2; therefore x = sqrt(h/(1 - Omega)) = H/n, i.e. n/H = 1/x and a/H = sqrt(1 - Omega).
Checks of the curvature formula: Bianchi IX gives +3 n^2/4 > 0, VII_0 gives 0, V gives
-6 a^2.

Matched comparison protocol (local, task S4 of the handoff): evolve an open-dust
(Omega_Lambda = Omega_r = 0) VII_h state with `evolve_general_tilted_bianchi`, record
(sigma/H, a/H, n/H)(N), run `los_sky` with an instantaneous last-scattering shell at
z_E = 1100 and zero source increment (pure geodesic redshift, the BJS assumption), and
compare with `bjs_temperature` after a fitted rotation and amplitude. Pass: shape
correlation >= 0.99 over the sky for one of the two variants; the other variant and
the handedness convention are then decided by data, not assumed.

## TF5. Normal-frame flux identity for SQ-LIE-FLUX

Established: in an orthonormal frame of a spatially homogeneous model the momentum
(Codazzi) constraint ties the total normal-frame energy flux q_a algebraically to the
shear and the structure constants (Wainwright and Ellis 1997, ch. 1; implemented with
the repository sign convention in `htt/bass/background/codazzi_tilt_rhs.py`, which is
the reference for signs). Consequence used here: an independent estimate of q_a tests a
fixed linear combination of (sigma, a, n); for the exceptional VI_{-1/9} family the
combination has a left-null direction (PHY-05), so the flux test is blind there and must
be reported as such. Independent q candidates: CMB kinematic frame versus radio-count
frame (SQ-RADIO), CF4 large-radius bulk flow (SQ-CF4), each with its covariance and
local-structure remainder. Not established: that any of these measures a homogeneous
tilt rather than local structure; that question is V03/V04.

## TF6. Physical anchor for P1 (proposal, not a DAG edge)

SQ-P1-ANCHOR asks for one identified physical x with source covariance. Proposal: use
the calibrated template response d a_lm / d(sigma/H)_0 of each family from B02 (TF1),
projected through the Planck response in B03, as the physical scale for the 274-row P1
functional. This needs B02/B03 outputs; it is recorded as a route, not as progress.

## TF7. Independent C1 for the radio dipole (SQ-RADIO)

R106 shows every NVSS differential-field p-value depends on the dipole power C1 of the
count field and finds p crossing 0.05 at C1 = 1.62, 2.06, 2.39 x 10^-3 (RED, MID, FLAT).
Established route: the large-scale-structure angular power at ell = 1,
C1 = (2/pi) int dk k^2 P(k) [int dz b(z) n(z) D(z) j_1(k chi(z))]^2 (plus redshift-space
and magnification terms), evaluated without the Limber approximation for brackets of
the source redshift distribution n(z) and bias b(z) used in the radio-dipole
literature; and an empirical cross-check from an independent survey (RACS-low DR1, item
D11). Not computed in R107; specified as local task S9.

## TF8. Electron history below z = 4

The rei_bianchi driver stops at z = 4 by construction. For z <= 4 hydrogen and HeI are
ionized, so n_e is fixed up to HeII reionization timing. `rei_lowz_continuation`
continues the donor x_e(4) = 1.08339435 continuously to 1 + 2 f_He at z = 0 with a tanh in
y = (1+z)^{3/2}. Its integrator reproduces the R105 common-foreground depths
0.02112795923 and 0.02243045425 to 2e-10. Donor-matched depths tau(0 -> 4) =
0.0221961, 0.0224021, 0.0225124 for z_HeII = 3.0, 3.5, 3.9 (sensitivity only). A
physical REI continuation below z = 4 needs a quasar HeII-ionizing emissivity and a UV
background in the Rust driver (local task S8).
