# R63 R2/C2 primary-source review: local boost and global tilt
Date: 2026-11-17. Scope: source/formula review only; no inference run, no new global solution, no child agents.
Requested execution model: gpt-6.1-sol/high. Observed model/effort: UNKNOWN (not exposed by runtime). Policy: PhysMath Research Loop 1.3.0 R2/C2 + POLICY_INTEGRATION.

## Result and conventions

**Literature-supported:** A local observer boost and a physical radiation–matter relative tilt are different objects. A scalar dipole can be shared by them, but this does not imply equality of their complete distance, aberration, remote-dipole or time-dependent responses. **Derived:** Their identifiability can be studied constructively from the rank of the selected response matrix, after nuisance columns and cross-probe covariance are specified. No universal no-go follows from this review.

Use signature (-,+,+,+), sourceward unit vector n, physical three-velocities v, beta=v/c, a_o=1, chi(z)=c integral_0^z dz'/H(z'), and A(z)=c(1+z)/(H(z)chi(z))=c/(aHchi). H is proper-time Hubble rate, chi has length units, and A is dimensionless. Quantities below are first order in peculiar velocities unless marked exact. The distance formula is a velocity-only restriction of scalar-perturbed FLRW, not the complete gravitational/lensing response and not a solved tilted-Bianchi universe.

## 1. Luminosity-distance and redshift frame response

Primary read: Hui & Greene, PRD 73,123526 (2006), DOI 10.1103/PhysRevD.73.123526, arXiv:astro-ph/0512159v5, Sec IV.1 Eqs (11)–(15),(18), Appendix C:
https://arxiv.org/html/astro-ph/0512159v5 .
Web ref: turn541416566view1; metadata/version ref: turn513667840view0.

Their n is already sourceward. Restoring c, at the same background emission event:
  1+z_H=(1+zbar)[1+n·(v_s−v_o)/c],
  D_L^H=Dbar_L(zbar)[1+2 n·v_s/c−n·v_o/c].
The factor 2 for source motion and −1 for observer motion are not interchangeable. Taylor expanding the background relation at the **fixed observed** redshift gives
  delta_D(z_H,n)=[D_L^H−Dbar_L(z_H)]/Dbar_L(z_H)
               =(1−A)n·v_s/c+A n·v_o/c.
This is their Eq (15). The low-z dominant term is n·(v_o−v_s)/(cz), so a source receding faster than the observer makes the distance smaller at fixed observed z. At high enough z where A=1, the source coefficient crosses zero; the observer coefficient does not.

Independent primary check: Bonvin, Durrer & Gasparini, PRD 73,023523 (2006), DOI 10.1103/PhysRevD.73.023523; erratum PRD85,029901 (2012), DOI 10.1103/PhysRevD.85.029901; arXiv:astro-ph/0511183v5 (2011-11-21), Eq (59), first line:
https://arxiv.org/html/astro-ph/0511183v5 .
This paper uses signature (-,+,+,+), but its Eq (59) is for a source at direction **−n_paper**. Its velocity terms are −A v_o·n_paper−(1−A)v_s·n_paper, which reproduce the formula above after n=−n_paper. Copying Eq (59) without this direction translation reverses both signs. Eqs (3)–(7) give the invariant flux/Jacobi/redshift definitions.

Primary treatment of data correction: Davis et al., ApJ741,67 (2011), DOI10.1088/0004-637X/741/1/67, arXiv:1012.2912v2, Eqs (5),(6),(8)–(11),(18):
https://arxiv.org/html/1012.2912v2 .
They explicitly require correction of distance/flux as well as redshift if one wants a completely transformed CMB-frame pair. Their Eq(18) has two source redshift factors but one observer factor. SciSpace search/fetch independently resolved this record:
https://scispace.com/papers/the-effect-of-peculiar-velocities-on-supernova-cosmology-3evyc1m254 .
SciSpace metadata duplicated some authors; arXiv/publisher authority is used for identity.

### Computational correction contract (derived from the read equations)

Let a catalogue correct redshift by a declared dimensionless vector q:
  delta ln(1+z_q)=n·q,
and correct the flux-derived distance by a declared vector p:
  D_q=D_H[1+n·p].
To first order, d ln Dbar_L/d ln(1+z)=1+A. Therefore
  delta_D^q = n·[(1−A) beta_s+A beta_o−(1+A)q+p].

Cases:
- Native heliocentric redshift and flux-distance: q=p=0; observer coefficient A.
- Redshift correction only, using the actual beta_o: q=beta_o,p=0; observer coefficient −1.
- Both redshift and bolometric flux-distance fully deboosted using actual beta_o: q=p=beta_o; observer coefficient 0.
- A CMB dipole inferred correction q need not equal physical beta_o if an intrinsic dipole is allowed. Retain q as a recorded catalogue operation rather than reinterpreting it as an independent observer measurement.
- A distance pipeline using (1+zHEL)chi(zCMB), source-PV corrections, K corrections, calibration and standardized photometry must be traced from its actual definition. The table is not permission to assume all published distances are raw bolometric values.
- For distance-modulus residual, delta_mu=(5/ln10)delta_D at first order. This adds magnitude calibration columns which must be retained.

C2 suggested input fields: sourceward n_i, native zHEL_i, corrected redshift values plus exact correction q_i, which redshift enters the distance prefactor and radial integral, raw/calibrated magnitude provenance, p_i if a distance deboost was actually applied, source-velocity history beta_s(z_i), background H(z), chi(z), source/magnitude/PV covariance. Do not silently feed zHD into the native formula.

Primary contemporary warning: Sorrenti, Durrer & Kunz, arXiv:2212.10328v2 (2023-10-24), “The Dipole of the Pantheon+SH0ES Data”, Eq(2.1) full scalar response and Eqs(2.3),(2.4), Sec4.6 source-PV corrections:
https://arxiv.org/html/2212.10328v2 .
Their low-z observer interpretation assumes source velocities average out; a coherent source bulk changes that interpretation. Their data discrepancy is therefore not a measurement of an unrestricted global tilt.

### Equivalence-principle and history condition

Kaiser & Hudson, MNRAS450,883 (2015), DOI10.1093/mnras/stv693, arXiv:1411.6339v2 (2015-03-25), Sec3 (after Sec2.4 comparison):
https://arxiv.org/html/1411.6339 .
Read primary text establishes that the apparent “absolute source velocity” dependence of the velocity-only distance expression is resolved by including velocity time evolution, and, for structure on scales comparable to source–observer separation, gravitational redshift. Thus setting identical constant endpoint velocities while discarding the metric terms is not an equivalence-principle test of an evolved long mode. A finite source-history ansatz remains a legitimate declared endpoint/test-congruence experiment; it is not automatically a self-consistent dust/Bianchi history.

## 2. Local radiation/matter/observer frames and finite boosts

**Derived exact local definitions:** At the same event, normalize U_A·U_A=−c². Define
  Gamma_AB=−U_A·U_B/c²,
  V_{B|A}=U_B/Gamma_AB−U_A.
Then U_A·V=0 and |V|²=c²(1−Gamma_AB^−2). Gamma_mgamma>1 is invariant under a common change of tetrad; an observer boost cannot erase a physical matter–radiation relative velocity. Comparing velocities at distant events requires a specified transport/congruence and light-cone history, not a subtraction of unrelated coordinate components.

If a frame S' moves with physical velocity b relative to S, and a particle has S-velocity u, write parallel and perpendicular to b. The exact S' velocities are
  u'_parallel=(u_parallel−b)/(1−b·u/c²),
  u'_perp=u_perp/[gamma_b(1−b·u/c²)].
Non-collinear boosts include a Wigner rotation of spatial axes; naive vector addition/subtraction is a first-order approximation only. For calculations use tetrad four-vectors and Lorentz matrices, then project into the explicitly chosen axes.

For an incoming photon k at the observer, E_o=−k·U_o and
  1+z=(k·U_s)_s/(k·U_o)_o
is exact for the connected null ray. For a local reference tetrad and sourceward n, E_o/E_ref=gamma_o(1+beta_o·n_ref), so
  1+z_ref=(1+z_o)gamma_o(1+beta_o·n_ref).
If using the moving observer's sourceward n_o instead, the same factor is 1/[gamma_o(1−beta_o·n_o)]. Mixing the direction convention between these two exact forms generates a second-order error.

A pure monopole blackbody boosted by beta gives
  T_o(n_o)=T_ref/[gamma_o(1−beta·n_o)].
With a pre-existing anisotropic field use the aberrated argument and its frequency/spectral transformation; a local zero temperature-dipole frame, an energy-flux eigenframe, and an assumed statistically isotropic frame require distinct definitions outside the perfect blackbody/isotropic case.

Primary global-tilt construction: Cembranos, Maroto & Villarrubia-Rojo, JCAP06(2019)041, DOI10.1088/1475-7516/2019/06/041, arXiv:1903.11009v1, Eqs(5)–(9),(17)–(28),(49):
https://arxiv.org/html/1903.11009 .
To first order in nonrelativistic homogeneous fluid velocities an FLRW background is compatible with
  sum_s (epsilon_s+p_s) beta_s=0
(center-of-momentum condition, Eq7). This is not an exact all-orders isotropy statement: individual boosted fluid stresses include O(beta²) anisotropic terms, Eq49c. For noninteracting constant-w fluids at linear velocity order, beta_s∝a^(3w−1), so beta_r is constant and beta_m∝a^−1. Eqs21,25,27 give the finite-speed evolution in the fixed RW kinematic treatment (not an independent exact Einstein/Bianchi solution):
  d beta/d eta=[(1−beta²)(3w−1)/(1−w beta²)] Hcal beta  (constant w),
  beta_m(a)=beta_m0/sqrt[beta_m0²+a²(1−beta_m0²)].
A global tilt specification includes IC, species momentum balance, interactions/decoupling, metric response and history, not just beta at one observer event.

The 2019 construction predates any proposed R63 physical distinction. Novelty cannot be claimed for “matter and radiation can have different frames” or merely “multiple observables distinguish them.”

## 3. CMB Doppler/aberration: actual information and numerical anchors

Planck2013 XXVII, A&A571,A27 (2014), DOI10.1051/0004-6361/201321556, arXiv:1303.5087v2 (2014-11-10):
https://arxiv.org/html/1303.5087v2 .
Eq(11) off-diagonal covariance, Eqs(12)–(14) separate aberration and modulation templates W_beta=W_phi+b_nu W_tau, and the estimator sections/figures supply mask/noise simulation calibration. The signal couples ell to ell±1 and is a two-point response rather than just the ell1 temperature coefficient.

Published projection along the known temperature-dipole direction (l,b)=(264°,48°):
  v_parallel=384±78(stat)±115(syst) km/s.
This is an actual one-dimensional projection, not a 3D covariance. Its systematics error is not automatically an independent Gaussian variance. This 2013 estimator also has dipole-distortion information from intensity→temperature conversion; it must not be advertised as entirely independent of the measured dipole.

Ferreira & Quartin, PRD104,063503 (2021), DOI10.1103/PhysRevD.104.063503, arXiv:2107.10846v1, SecII Eqs(3)–(10), SecV–VI, and SecVIII:
https://arxiv.org/html/2107.10846v1 .
They remove intensity/temperature “dipole distortion”, masking/noise bias and aberration–Doppler leakage with realistic simulations. Dipole/distortion removal changes which information is independent; tSZ leakage cross-checks can remain physically degenerate with the temperature dipole. Public implementation:
https://github.com/pdsferreira/cmb-aber-dopp
(read README version0.2; no commit SHA or posterior file was fetched here). It provides simulated vectors and estimators, plus some plot source data. No full science-grade released joint betaA/betaD 6D covariance was obtained by this review.

Companion measurement: Ferreira & Quartin, PRL127,101301 (2021), DOI10.1103/PhysRevLett.127.101301, arXiv:2011.08385v2 (2021-07-23):
https://arxiv.org/html/2011.08385v2 .
Web ref turn513667840view3. Eq(1) makes the degeneracy explicit:
  Delta1=beta+Delta_int,
  betaD=beta+(1+alphaNG)Delta_int,
  betaA=beta+L_d.
Here L_d is a dipolar lensing contribution. Gaussian intrinsic fluctuations have alphaNG=0 in the stated treatment, so betaD=Delta1; adding that statistic alone does not distinguish the intrinsic contribution. Aberration supplies another response, with L_d as an explicit nuisance. An arbitrary intrinsic remapping/pointing or calibration field can likewise mimic particular response templates; model it if admitted.

Admissible published numerical summaries (Table1, not raw likelihoods):
- SMICA TT+EE aberration: amplitude300±99(stat)±13(syst) km/s; Galactic longitude276±32±0.1 deg, latitude51±19±0.7 deg.
- NILC TT+EE aberration:296±100±10 km/s;280±32±0.3 deg,50±20±0.3 deg.
- Their lensing-marginalized velocity posterior: SMICA300^(+111)_(-93) km/s, (276±33,51±19) deg.
- Standard-ΛCDM dipolar lensing amplitude adopted in their analysis L_d=2.06e−4 (dimensionless), treated stochastically with unknown direction.
Do not transform these angular/amplitude marginal bars into a fabricated Gaussian Cartesian covariance. SMICA and NILC use the same sky and are not independent data sets. Public Planck SMICA statistics or simulations are not Commander MC and are not the existing user's Commander likelihood.

Statistical assumptions: an unboosted statistically isotropic C_l model, instrument/foreground/mask/noise calibration, small boost order with controlled multipole covariance, and an intrinsic modulation/lensing model are required to interpret these estimators as physical velocity. A full joint covariance includes betaA–betaD leakage and cross-probe overlap; independent observable form does not imply statistical independence.

## 4. Remote dipole kSZ and other independent responses

Krywonos, Hotinli & Johnson, arXiv:2408.05264v1 (2024-08-09), Eqs(1)–(7), section “Probing the rest-frame of LSS”, SM B–C:
https://arxiv.org/html/2408.05264v1 .
Web ref turn513667840view4; metadata ref turn541416566view5.
Publisher currently lists PRD114,083542 (2026-10-28), DOI10.1103/qwwp-xbby; publisher abstract was read via Exa and differs in some PNG/CIP interval values from v1. No publication-version detailed formula equality is asserted here.

With velocity units restored, their Eq1 is
  Theta_kSZ(n)=−integral dchi sigma_T a n_e [v_eff(chi,n)/c].
For subhorizon adiabatic modes v_eff≈n·v_e. On horizon scales the remote radiation dipole contains SW/ISW/last-scattering Doppler contributions and is not simply matter velocity. It measures radiation incident at remote electrons, so it probes spacetime response unavailable to a single endpoint Doppler dipole. Our local observer boost must be transformed in the measured map but does not physically create remote electron-frame dipoles everywhere.

Their Planck×unWISE reconstruction averages roughly0.2<z<1, uses an optical-depth–galaxy cross-spectrum model C_l^(tau g), and carries optical-depth bias b_v. A Gaussian low-ell QML likelihood, ΛCDM dipole signal variance C1=4.76e2 b_v²(km/s)² and an intrinsic spatial dipole template
  v_int(n)=D_int Y10(rotated n)
give D_int<14km/s(68%) and<26km/s(95%), after direction/optical-depth-bias marginalization. D_int is a **spherical-harmonic template amplitude**, not automatically the amplitude V of a Cartesian V cos(theta) field (D=V sqrt(4pi/3)). It is not an unrestricted bound on every global tilt history or all possible CMB intrinsic dipoles. Applicability requires mapping the candidate global history to their remote template, nuisance treatment and covariance.

Recent method novelty already in primary literature: Lai, Kvasiuk & Münchmeyer, arXiv:2506.21684, ACTDR6×DESI-LSDR9 tomographic QML kSZ reconstruction; fetched page requested v2(2026-10-09) but Exa rendered metadata saying “Full text of v1.” Therefore the11.7sigma cross-correlation and A=0.39±0.04 cited in returned content are **v1 content only**, not certified as v2 numerical results:
https://arxiv.org/abs/2506.21684 .
Do not turn a reconstruction detection significance into a global-tilt likelihood.

Cosmic parallax original: Quercellini et al., PRD80,063527(2009), DOI10.1103/PhysRevD.80.063527, arXiv:0905.4853, Eqs(4)–(7):
https://arxiv.org/html/0905.4853 .
For BianchiI comoving sources, direction changes involve directional Hubble differences/shear; the leading pattern is quadrupolar. Observer acceleration produces time-varying aberration dipole, transverse velocity produces distance-dependent parallax, and source motions add further terms. A single static local boost does not specify any of these time derivatives; use the actual worldline and distances.

Quartin & Amendola, PRD81,043522(2010), arXiv:0909.4954, DOI10.1103/PhysRevD.81.043522:
https://arxiv.org/html/0909.4954 .
This is an existing constructive comparison of cosmic parallax and redshift drift in LTB versus dark energy. The FLRW comoving baseline is exact:
  dz/dtau_o=(1+z)H_o−H(z).
For source and observer velocities/accelerations one must differentiate the invariant redshift on successive rays and include potential/time-evolution terms. Redshift drift adds history/acceleration response; it is not reconstructed from an ordinary list of source redshifts.

Number counts: Wagenveld et al., A&A697,A112(2025), DOI10.1051/0004-6361/202453397, arXiv:2503.02470, Eq(1):
https://www.aanda.org/articles/aa/full_html/2025/05/aa53397-24/aa53397-24.html .
For ideal flux-limited unresolved sources, N(>S)∝S^(−x), S_nu∝nu^(−alpha),
  D_kin=[2+x(1+alpha)] beta_o.
This sample-dependent response enables multiple-catalogue tests, but selection slopes, masks, correlated structure and residual dipoles are part of the experiment. Their common free kinematic plus free residual vector model was not fully separated by current catalogues. Their5.5sigma residual with CMB boost fixed is a conditional model result, not a model-independent tilt detection.

Yoo, Magi & Huterer, PRD112,123013(2025), DOI10.1103/ks44-qt3b, arXiv:2507.08931v2(2025-12-05):
https://arxiv.org/html/2507.08931v2 .
Web ref turn541416566view4. SecII,Eqs(1)–(3), SecIV Eq(20),(23),(31)–(32), SecV Eqs(44)–(49) give fully relativistic/window-dependent dipole transfers. Relative velocities must be compared at a common event; the effective source-sample velocity at the observer is transfer/window dependent. The superhorizon cancellation uses metric and velocity terms together. This directly limits novelty of a generic “compare CMB/SN/count dipoles” claim and shows why replacing every sample by the same literal endpoint source velocity is not valid.

## 5. Constructive rank statement and transport to code

For a specified finite experiment y=R_o beta_o+R_t theta_t+N eta+noise, C positive definite, whiten with L such that L C L^T=I and project off admitted nuisance columns:
  P_perp=I−(LN)(LN)^+,
  R_eff=P_perp L [R_o,R_t].
A local boost parameter and a tilt/history parameter are separately estimable only in directions outside ker(R_eff). SVD measures conditioned separation; it does not establish that theta_t is a self-consistent global solution. Statistical independence is unnecessary if the full C is available.

Explicit distance-only example, one Cartesian component and one shell, constant source beta_s and observer beta_o:
  delta_D=A beta_o+(1−A)beta_s.
This is one row for two unknowns: rank≤1. Two genuinely different shell A values give determinant A1−A2, so endpoint coefficients can be algebraically separated if beta_s is shared across those shells. Allowing independent beta_s(z_i), arbitrary dipolar calibration per shell or missing flux operations changes this conclusion. A measured CMB dipole adds beta_o−beta_gamma plus intrinsic fields, not automatically beta_o alone. Aberration, remote dipoles and time derivatives supply distinct columns only under their documented nuisance and transport models.

C2 source-to-code map for parent:
- distance observer/source coefficients: A and1−A with native observed redshift, plus declared correction terms −(1+A)q+p;
- radiation/matter relative boost: exact U contractions and tetrad projections, preserving axis orientation;
- history: specify beta_s(a) as phenomenology or solve fluid/metric IC equations; never relabel one as the other;
- CMB likelihood: use released/derived joint samples or covariance with provenance; numerical summaries only support their declared 1D or marginal statement;
- remote kSZ: predicted v_eff(a,n), galaxy/electron window and b_v, SW/ISW terms when relevant;
- parallax/drift/counts: observed worldlines, selection and covariance, with no invented data.

## Evidence and closeout

R2 complete for this bounded source/formula review. C2 is a formula/data contract, not implementation verification. No numerical posterior or global-tilt constraint was computed. Primary full text was read through Exa; SciSpace search/fetch verified the Davis record. Web fetch failures for some arXiv/A&A routes were bypassed by successful Exa primary full-text retrieval. HTML renderer date strings such as “August24,2026” were not used as paper revision dates; explicit arXiv version metadata controls identity. Search coverage is targeted, not exhaustive. No strong no-go is admitted, and no absence of a Boltzmann implementation is promoted into a prohibition.

No external writes/publication/git. Parent owns persistence and final user-facing artifacts. Exact remaining prerequisite for a data-driven joint tilt claim: retrieve the actual suitable joint likelihood/covariance or reconstruct it with the relevant source pipeline; specify the candidate global dynamics and predicted remote/history responses.


## Frame clarification at closeout (derived; prevents an interpretation error)

The F in the velocity-only distance formula is the declared FLRW/statistical reference frame. It need not coincide with the local radiation energy-rest frame R once an intrinsic temperature dipole is admitted. For a direction-dependent blackbody T_F(n)=T0[1+Delta_int·n], with sourceward n and incoming photon momentum directed along −n, bolometric intensity obeys I_F(n)=I0[1+4Delta_int·n]. Its local energy flux is therefore
  q_F=−(4/3)epsilon_gamma c Delta_int.
Writing the radiation velocity relative F as beta_R|F gives q_F=(epsilon_gamma+p_gamma)c beta_R|F, with p_gamma=epsilon_gamma/3 at this order. Hence
  beta_R|F=−Delta_int,
  Delta_obs=beta_O|F+Delta_int=beta_O|R.
All relations are first order, local at the same event, and assume bolometric blackbody radiation without spectral dipoles; anisotropic stress and products of perturbations enter at higher order. If rho denotes mass density rather than energy density, factors of c change and must not be suppressed.

Thus a nonzero intrinsic dipole in a fiducial statistical frame is compatible with a purely kinematic dipole relative to the actual local radiation energy rest frame. The Ferreira–Quartin abstract explicitly calls beta the velocity relative to the Hubble flow, and Eq1 decomposes the temperature dipole relative to that fiducial description. Their aberration estimator infers the boost of the statistical small-scale pattern under its source/lensing hypotheses; it does not by itself show that the measured temperature dipole fails to measure the local radiation energy-rest velocity. Avoid calling both F and R the same “CMB rest frame.” For physical matter–radiation tilt, use U_m and the local radiation energy eigenvector U_R; for statistical anisotropy, separately preserve F and its ensemble assumptions.
