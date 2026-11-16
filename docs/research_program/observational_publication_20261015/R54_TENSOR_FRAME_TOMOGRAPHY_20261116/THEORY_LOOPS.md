# R54 theory loops (2026-11-16)

All numbers below are generated from `RESULTS/*.json`. Decisions and review dimensions are in `state/HYPOTHESIS_GRAPH.md`.
The decisions in this file are the ones that stand after the independent review (`INDEPENDENT_REVIEW.json`).

## Equation register

- **R54-EQ-01**: `dTheta/dN = -s - kappa[(9/10)Theta + (sqrt6/10)Ecal]`
- **R54-EQ-02**: `dEcal/dN = -kappa[(sqrt6/10)Theta + (4/10)Ecal]; kappa = n_e sigma_T c/H = dtau/dln(1+z)`
- **R54-EQ-03**: `K_T(tau) = (6 e^-tau + e^(-3tau/10))/7 ; K_E(tau) = (sqrt6/7)(e^(-3tau/10) - e^-tau)`
- **R54-EQ-04**: `Sigma_T = -Theta(0) = int K_T(tau(N)) s(N) dN ; Sigma_E = +Ecal(0) = int K_E(tau(N)) s(N) dN ; a^T_2m <-> -T0 n.Sigma_T.n ; a^E_2m <-> -T0 n.Sigma_E.n`
- **R54-EQ-05**: `ds/dN = -(3 + dlnH/dN) s + (8/5)[Omega_gamma(N) Theta + Omega_nu(N) Ncal] ; dNcal/dN = -s`
- **R54-EQ-06**: `massive collisionless species, k = 0, first order: pi_ij = -(2/15) beta_ij Kcal, beta_ij = int s_ij dN, Kcal = 4 pi int dp f0 p^4 (4p^2 + 5m^2)/E^3 ; W(mu) = Kcal/(4 rho_massless), mu = m a/T_nu0, W(0) = 1 ; the neutrino term of R54-EQ-05 is multiplied by the species mean of W`
- **R54-EQ-10**: `u_lm(r) = 4 pi f H0 i^l int d^3k/(2pi)^3 (delta_k/k) j_l'(kr) Y*_lm(k)`
- **R54-EQ-11**: `C_l^{ww'} = (2/pi)(f H0)^2 int dk P(k) I_l^w(k) I_l^{w'}(k) ; I_l^w(k) = int dr Wcal_w(r) j_l'(kr)`
- **R54-EQ-12**: `Var(H) = C_0/(4pi) ; Cov(D_i) = (3/(4pi)) C_1 ; Cov(q_a) = (15/(8pi)) C_2`
- **R54-EQ-20**: `Theta_c = {theta: (theta-m)^T F (theta-m) <= c^2}, F m = t ; Q_min/max = min/max of p_K0 over Theta_c ; Q_max = inf if F singular`
- **R54-EQ-21**: `Q_min = sup_v [-h_Theta(-v)]_+/h_K0(v) ; Q_max = sup_v h_Theta(v)/h_K0(v) ; h_K0(v) = sqrt(v^T B v)`
- **R54-EQ-22**: `Pi = P[stat >= stat_obs | named law]`
- **R54-EQ-23**: `chi2_transport = min_x (y - (tau (x) I)x)^T C^-1 (y - (tau (x) I)x), dof = d(K-1)`
- **R54-EQ-30**: `Psi_perp(r) = (f H0)^2/(2 pi^2) int dk P(k) j_1(kr)/(kr) ; Psi_par(r) = (f H0)^2/(2 pi^2) int dk P(k) [j_0(kr) - 2 j_1(kr)/(kr)]`
- **R54-EQ-31**: `C_uu(i,j) = Psi_perp(r_ij)(n_i.n_j) + [Psi_par(r_ij) - Psi_perp(r_ij)](n_i.rhat_ij)(n_j.rhat_ij) ; r_ij = |d_i n_i - d_j n_j|`
- **R54-EQ-32**: `C_1 = (2/pi) int dk k^2 P(k) [int dchi W(chi) b(z) D(z) j_1(k chi)]^2 ; Var(d_i) = (3/(4pi)) C_1 for delta(n) = d.n`
- **R54-EQ-33**: `flat LCDM: chi_hat(z) = int_0^z dz'/E ; y(z) = c (1+z) chi_hat = H0 d_L(z) [km/s] ; g(z) = [(1+z)/(E chi_hat) - 1]/c = d ln(y/d_L,obs)/du`
- **R54-EQ-34**: `eta_i = ln[y(z_i)/d_i] = h + delta.n_i + n_i.kappa.n_i + g(z_i) u_i - s_i eps_i ; s_i = (ln10/5) e_mu,i ; weights W(z_i)/tau_i^2, tau_i^2 = s_i^2 + (sigma_* g_i)^2`
- **R54-EQ-35**: `R36 linear estimator: c z_i = d_i (H + D.n_i + n_i.q.n_i), weights W(z_i)/hypot(250, 70 (ln10/5) d_i e_mu,i)^2 ; biased by errors in d_i (exp(+s^2/2) for homogeneous errors)`
- **R54-EQ-36**: `Delta mu = -(5/ln10) Delta eta ; hemisphere step s: Delta mu(north - south) = -(5/ln10) 2 s`
- **R54-EQ-37**: `exact body of an operator O acting on eta: O diag(g) C_uu diag(g) O^T with C_uu of R54-EQ-31 at redshift-space positions r_i = (c/H_fid) chi_hat(z_i)`
- **R54-EQ-38**: `global-tilt closure across depths: V_CF4 + c beta_excess(counts) = 0 with beta_excess = D/c_EB - beta_CMB`

## CORE: tensorized five views on a precision-form carrier

A probe contributes a carrier (F, t) in typed coordinates. Independent probes add; nuisance is profiled by a Schur
complement; the null space of F is reported. With a declared body K0 = {theta^T B^-1 theta <= 1}:

- **Proposition (polar duality, R54-EQ-21).** For the confidence set Theta_c of R54-EQ-20,
  Q_min = sup_v [-h_Theta(-v)]_+ / h_K0(v) and Q_max = sup_v h_Theta(v) / h_K0(v).
  Proof sketch: p_K0 is the support function of the polar body K0^o = {v : h_K0(v) <= 1}, so
  max_Theta p_K0 = max_Theta max_(v in K0^o) v.theta = max_(v in K0^o) h_Theta(v); the minimum follows from the
  separating hyperplane at the touching point of Theta_c and Q_min K0. Checked by exact enumeration in two
  dimensions to 1e-8 and at the touching point in the tests.
- If F is singular, Q_max = +infinity and F_upper = +infinity along unidentified directions. This is a result, not a failure.
- G_F is a GLS test of y_k = tau_k x with the full cross-depth covariance; dof = d(K-1).
- None of the views changes a GLS estimate. The R53 tie with the exact likelihood stands.
- The F view needs a declared convex body in parameter space. It is AVAILABLE on the CMB lane only; the axis scans of the
  low-redshift lanes are template statistics and are recorded under Pi.
- Finite-MC law: for a sample covariance with n = N - 1 degrees of freedom the GLS estimate has true sd / plug-in sd =
  sqrt[n(n-1)/((n-p+k)(n-p+k-1))], which is 1 for a square carrier (p = k), where the Wald statistic follows the Hotelling law.

The five views are a reporting convention (H-C1); no novelty is claimed for them.

Prior work applied: support functions for partially identified sets (econometrics), eigenstructure inference for
symmetric-matrix data (E26), matrix-valued multipole statistics (E28), tensor Minkowski functionals (E27). The last
two motivated the STF invariant layer; they are not used as estimators here.

## Loop L1: low-ell morphology and physical observables

Contract: which linear functionals of the kinematic history does the ell = 2 temperature and polarization measure?
Derivation: at k = 0 the Thomson hierarchy closes on (Theta, Ecal) with collision matrix M (eigenvalues 1, 3/10);
the propagator is exp(-M tau) and gives R54-EQ-03/04. Thomson scattering of an unpolarized quadrupole gives
Q + iU = -(sqrt6/10) sum a^T_2m 2Y_2m per unit depth, so the healpy E tensor has the sign of the T tensor.
Shear dynamics: sigma_dot + 3H sigma = 8 pi G pi with pi = (8/15) rho Theta for free-streaming radiation gives R54-EQ-05;
a collisionless species of mass m carries the stress weight W(mu) of R54-EQ-06 (W = 1 massless, stress -> -2 P beta_ij when non-relativistic).
Prior art: the first-order polarized transfer in a spatially flat anisotropic universe was solved in E46 (see also E48 and E47);
R54-EQ-01 to R54-EQ-04 are a re-derivation in the present conventions.

Results: r_E(perfect fluid) = 0.0711; K_E peaks at 0.1462; with photon stress s0/Sigma_T = -0.000244;
in the two-mode family s0 = c_T Sigma_T + c_E Sigma_E with (c_T, c_E) = (0.00166, -0.0254) for massless neutrinos and
(0.000858, -0.0147) for minimal normal ordering. Initial-state sweep over z_i from 1e+09 to 3e+10:
Sigma_T per unit initial shear changes sign between an assumed free-streaming onset at z_i = 1.5e+10 (T_nu = 2.5 MeV) and 2e+10 (3.4 MeV), an interval that contains the decoupling estimate of 3.12 MeV for muon and tau neutrinos (E49; 1.87 MeV for electron neutrinos) (r_E from 0.050 to 0.109 before the sign change, -1.057 to 0.109 over all 8 points); s0/Sigma_T spans [-0.00111, 0.0285].
Late-time sensitivity (shear confined to z < 0.2): int K_T dN = 0.182 and int K_E dN = 9.59e-06; a sign-changing history
with Sigma_T = 0 is bounded only through E, at an rms of 0.0729 (diagnostic lane).

Adversarial points recorded: (a) the kernel result is a re-derivation (E46); (b) the stress dependence is established physics in the
magnetic case (E05) and its novelty for shear limits is unverified; (c) the present-shear numbers are illustrations: they move by a factor
of about two between the two neutrino-mass variants and Sigma_T changes sign in the initial-state sweep; (d) the two-mode family has free
initial data, so T and E tensors need not be collinear; (e) late-time anisotropic stress evades the T functional (E44).

Decision: PROMOTE H-L1a (re-derivation), H-L1b (qualitative statement); REJECT H-L1c, H-L1d.

## Loop L2: dipole anomaly

Frame algebra (R52, retained): CMB dipole = beta_MO - beta_RM; counts = c_EB beta_MO; distances respond to the observer
velocity relative to each shell. The owned receipt estimator shows no excess (p = 0.27, 0.46; common excess
p = 0.12), but its power against a dipole twice the kinematic one is 0.20 at the 5% level, so the non-detection
decides nothing. The published anomaly (E19) rests on CatWISE-type samples and dedicated estimators; the fair comparison is to
run those estimators on the owned catalogues with a clustering body (R54-EQ-32) and a same-estimator null (R54-L03).

Decision: HOLD H-L2a (underpowered), H-L2b; REOPEN the R52 frame inconsistency (H-L2c).

## Loop L3: beyond-FLRW kinematic quantities

Identifiability by irreducible block and parity at first order (inherited from R52, no new computation): STF2 (sigma) is identified by
the CMB functionals and by low-z quadrupoles; the axial vector (omega) has no column in any owned observable once the reference frame
rotation is free; a constant polar dH dipole (A) is a gauge direction of one distance-indicator sample.
Transport inside type I. Without late-time anisotropic stress the present shear allowed by the CMB functionals is
|s0| <= 6.65e-08 (massless two-mode) or 3.43e-08 (minimal normal ordering), against a CF4 quadrupole of 2.5% of H.
With late-time stress this does not hold: for a shear confined to z < 0.2 the T functional bounds a constant-sign history at
0.000225 and is blind to a sign-changing one, and the E functional bounds its rms at 0.0729
(0.0112 for z < 0.5, 0.000692 for z < 2), above the CF4 value.
Several distance indicators do not identify A either, but they test whether a dipole is common to them (Loop L5, item 4).

Decision: PROMOTE H-L3a, H-L3b (inherited structural statements) and H-L3d (conditional statement); REJECT H-L3c (unconditional statement).

## Loop L4: anisotropy evaluation and classification

Carrier-level classification is the orbit type of the measured STF tensor under rotations: amplitude, shape
(sqrt6 tr M^3 / (tr M^2)^(3/2) in [-1,1]) and frame, with an axisymmetry statistic. Family-level identification of
Bianchi types needs source-bound transfers beyond type I and stays blocked (AGENTS boundary 1 and 7).
Executed (log estimator, exact body): the constant CF4 quadrupole is 2.5% of H with its principal axis 9.5 deg from the
equatorial pole; the axis moves by tens of degrees under the zero-point split, so eigen-axes of a marginal tensor are not reported as directions.
The invariants have no null calibration on an owned carrier yet.

Decision: HOLD H-L4a.

## Loop L5: redshift- and direction-dependent Hubble factor

First pass (R54-L5, superseded for CF4). Model per window: cz = d (H_w + D_w.n + n.q_w.n) on the committed R36 multipoles with the
ideal-sky body R54-EQ-11/12. It gave nulls of 5.71e-05 and 1.07e-05 and a template axis 2.8 deg from the equatorial
pole (sky fraction 0.0005). The adversarial points recorded against it were: ideal-sky body; working covariance without
calibration terms; mode coupling of a monopole depth trend into survey-aligned multipoles. All three were then tested.

Second pass (R54-L05, catalogue level, executed on the 35970 committed groups).

1. Estimator. With c z = H d and d = D exp(s eps) the weighted regression of c z on d is biased; for homogeneous errors and
   weights ~ 1/d^2 the fitted rate is H exp(+s^2/2) (R54-EQ-35, checked by Monte Carlo in the unit test). With errors that differ
   between surveys the bias is direction dependent. The same-estimator null of the R36 operator shows that the bias carries
   14-40% of its pole dipole and, once subtracted, moves the quadrupole null from 0.00343 to 0.129
   and the pole sky fraction from 0 to 0.0755. The replacement is the log-distance ratio eta = ln[H0 d_L(z)/d] (R54-EQ-34),
   linear in the noisy distance modulus, with the exact velocity response g(z) of R54-EQ-33.
2. Body. O diag(g) C_uu diag(g) O^T with the linear velocity correlation tensor (R54-EQ-30/31/37), accumulated over all pairs.
   The pair-sum routine equals the dense 3-vector form to 1e-9 and the ideal-sky harmonic form to 2% on a full shell (unit test).
   Exact/ideal sd ratios on CF4: dipole 1.00-1.61, quadrupole 1.15-1.93.
3. Results by zero-point nuisance model (pooled / method monopoles / method x hemisphere steps). Joint null p:
   0.000344 / 0.00277 / 0.112 (pooled with the body doubled: 0.188). Calibrated locking tail of the two-parameter axis
   template (4000 null draws from the exact body): 0.0242 / 0.0085 / 0.147. Class under the coded rule:
   EXCESS_NOT_POLE_LOCKED / UNRESOLVED_POLE_LOCKED / LCDM_BODY_COMPATIBLE; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL.
   The third model removes the hemisphere direction by construction, so its dipole null is not evidence.
   Window split (pooled): inner windows joint p = 0.00558, outer windows 3.89e-06; at z >= 0.055 the sample is 98% FP,
   95% of it northern, so the outer dipoles compare northern FP with the rest.
   Power of the pole_locked flag for an injected hemisphere step of the observed size: 17% (1% without injection).
4. Indicator transport (a G_F view across distance indicators instead of depths). A physical dipole and a flow are common to all
   indicators; a calibration term of one indicator is not. Per-method hemisphere steps: FP -1.66, TF -1.96, SN -1.65,
   OTHER -2.22 (% of H), consistency p = 0.867, common step -1.66 +- 0.53%;
   with white errors the same step would have p = 2.97e-39. The common dipole vector of the four families has Wald p = 0.43.
5. Look-elsewhere correction of the step. The sign(dec) split was chosen after the first pass. Scan over 151 split axes with the exact
   body (18351 groups at z < 0.055): single-axis tail 0.0017; tail of the scan maximum 0.0339; the celestial pole ranks
   1 of 151 by |z|; under the null the best axis lies within 10 deg of the pole in a fraction 0.02 of draws.
   The four family estimates share the body: variance of the best single family / variance of the common step = 1.15 (4 if independent).
   The step (z < 0.055) and the window excess (stronger in the outer windows) are different measurements.

Adversarial points that remain: no selection function and no calibration covariance; hemisphere is a proxy for survey; indicators share
a calibration chain; the constant-quadrupole Wald statistic is a posteriori; every entry of the forking-path register below.

Prior art checked in this session: E43 applies a log-distance estimator to CF4 and its constituent catalogues and reports larger
dipoles for TFR and 6dFGS than for SDSS and SN; E09 and E33 find the Tully-Fisher dipole compatible with LCDM flows once radial
freedom is allowed. Equal steps at family level may therefore have different causes, and the common-mode reading stays on HOLD.

Decision: PROMOTE H-L5f; HOLD H-L5a, H-L5c, H-L5g, H-L5h; REJECT H-L5e.

## Loop L6: local boost versus global tilt

Depth laws: observer boost or coherent flow gives D proportional to 1/d; a zero-point or acceleration term is constant;
a global tilt is a constant velocity at every depth including the count-dipole shells; LCDM flows are a zero-mean body
with strong cross-depth correlation. On CF4 with the exact body the pooled fit prefers the constant term (chi2 10.4 against 16.2),
but the preference disappears when method monopoles are marginalised (6.7 against 7.3).
Injections on the real footprint (constant law preferred for an injected step / an injected flow): 93% / 24% at
0.05 mag and 300 km/s, and 82% / 20% at the observed sizes
(0.036 mag, 371 km/s); with the method-monopole operator 83% / 22%.
At the observed sizes the laws are not told apart at the 90% / 10% level written down before that run was read (H-C3 HOLD).
Tilt closure (R54-EQ-38): one matter-radiation frame offset at all depths requires V_CF4 = -c beta_excess(counts); the test gives
p = 0.0895 (V only) and 0.0123 (constant dipole marginalised), preliminary because the count side has no clustering body
and low power. The velocity term fitted next to the constant term is 456 km/s, 11 deg from the CMB apex, Wald 5.42/3.
Published anchors for the joint node: E21, E22.

Decision: HOLD H-L6a, H-L6b, H-L6c.

## Forking-path register

Analysis choices that were made, or could have been made, after looking at data. Each entry states what is reported to compensate.

| id | choice | status | what is reported |
|---|---|---|---|
| FP-01 | sign(dec) as the hemisphere-split axis | chosen after the first pass located the pole on the same data | tail of the scan maximum over 151 axes next to the single-axis tail |
| FP-02 | redshift range 0.01-0.055 of the per-family tests | fixed after tabulating coverage by method and hemisphere, before the body was attached | stability over the two halves of the range is a step of R54-L04 |
| FP-03 | decision rule and thresholds of the CF4 class | coded before the exact-body numbers were read, not committed beforehand | not called pre-specified; class per nuisance model and the first-draft rule are both in the result file |
| FP-04 | threshold of the 'removed by split' flag | pole gain after the split is 10.00 against the threshold 9.21 | the near miss is stated; the class is reported per model instead of relying on the flag |
| FP-05 | two-parameter axis template and reference axes | inherited from the first pass | null law drawn with the identical grid statistic |
| FP-06 | cut z_i <= 1e10 on the neutrino-decoupling sweep in the report builder | removed after the independent review | the full sweep, including the sign change of Sigma_T |
| FP-07 | constant-quadrupole Wald statistic | a posteriori | H-L5h on HOLD; the 20-dof null is quoted with it |
| FP-08 | injection amplitudes | the first amplitudes were not matched to the data | observed-size injections added; their amplitudes are data-derived and labelled so |
| FP-09 | nuisance model of the locking test | first run on the pooled operator only | three nuisance models; R54-L04 adds four more that are fixed in the contract before they are run |
| FP-10 | primary CMB carrier | fixed by the B-null gate rule before the intervals were computed | no change |
| FP-11 | number of null draws and random streams | raised from 2000 to 4000 draws with one stream per block after the review; seed unchanged | precision only |
| FP-12 | scan grid (151 axes, minimum 50 objects per family and side) | fixed in the script before the scan was run | no change |
