# R69-P1 Theory Loop II: physical five-view morphology, finite-z optics and typed 6 papers × 7 combinations

Date: 2026-11-19 KST. Current source HEAD at intake: 49156d68f1f24d1140e2f2dda08d7041acfd0ca7, branch research/r69-observable-physics-bridges-20261118.
Source: htt_base R68/R69, R61/R62/R64/R65/R66/R67, P1 selected-data Gaussian law; project AGENTS.md.
This report is a **new bounded theory R1–R10** focused on P1, not a relabelling of the previously completed R69-P1 loop. All P1–P6 42 original science nodes and acceptance conditions stay unchanged. No cosmological anisotropy detection or physical shear posterior is asserted.
Evidence: verify_physics.py → RESULT.json (real CF4 sky/geometry plus tensor from actual R62, no data likelihood); verify_optics.py → OPTICS_RESULT.json (ODE and tilted stress synthetic checks).
Native independent subagent NOT_RUN (not exposed); R6 self-review, Wolfram spot check. Repo state dirty before work, 318 unrelated untracked entries. No unrequested push/merge/commit.

## R1. Bounded target and output contract
For one shared physical referent/observer/source frame, find concrete links between signed STF5 x and the physically typed Q, Pi, F, G_F, including settings in which only the scale-free shape chi and full-sky area occupancy F_Omega are defensible. Extend the meaning of P1 from a local ell=2 fitted coefficient to arbitrary low ell and finite-z Sachs-Jacobi transport. Differentiate truly identifiable physical information from selection geometry; test on original CF4 directions. Other five papers and R69's exactly seven PHY-01..PHY-07 combinations receive formula-bearing derivative applications, **not** seven claims of independent verification.

## R2. Retained evidence and primary literature
Sources read: R69/PHYSICAL_THEOREMS_KO.md and X_TO_FIVEVIEW_PHYSICAL_RESPONSE_KO.md (signed carriers and source limitations); R69-P1/GENERAL_LOWELL_TILTED_BIANCHI_KO.md (general Lie + tilt); R62 actual apparent K0 STF5, R61 actual 11D conditional CF4 and 5x32 depth bias operator, P1 selected actual 274-row 15D Gaussian law; R67 seven research axes and 42 unchanged science DAG. Original table4.dat 38,053 valid parsed rows, SHA-256 b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94. Use frame rotation Galactic→ICRS.
Literature: Saldanha & Tomei (1996, LAA 245 335-351 DOI 10.1016/0024-3795(94)00339-4): distribution of quadratic forms over S², so F(chi) is a geometrical corollary, not novel probability. Maartens et al. JCAP 2024 09 070 DOI 10.1088/1475-7516/2024/09/070: moving-observer H multipoles, aberration and spurious octupole. Heinesen/Korzyński PRD 110 043525 DOI 10.1103/PhysRevD.110.043525: cosmic drift, GR kinematics. Perlick (Living Rev. Rel. 2004) lensing Jacobi and Sachs optical tidal. Głód arXiv:2001.02782: covariant Sachs fields/area distance. Tully et al. Cosmicflows-4 ApJ 944,94 and 2026 velocity/method analyses: survey selection and calibration overlap. For tilted Bianchi two-fluid literature see 2026 Fournodavlos-Marshall-Oliynyk "Future Stability..." (Ann. Henri Poincare). No source-dependent theorem originality is claimed.

## R3. Physics typing and assumptions
Signature (-,+,+,+), c, G, ħ, k_B kept for physical equations. For local regular observer/source congruence u.u=-c², H=Theta/3>0, d=-A/(cH), S=sigma/H in STF(3), sourceward n:
Hdir(n)=H[1+d.n+n.S.n]; D_L=cz/Hdir+O(z²). This is vertex only, NOT complete finite-z or heliocentric boosted law.
P1 optical apparent K0 is a 5-vector response in ICRS/J2000, not measured normal-frame sigma. 38,053 table4 raw groups and 35,970 selected data groups differ. Source table4 sky positions are Galactic and must be transformed before applying ICRS STF.
Distinct objects: x (signed actual tensor and source law), Q_H physical directional positivity only when d,S are physically measured, Pi conditional on matched likelihood/null, F_Omega angular solid-angle event, G_F physical occupancy transport (NOT simply depth labels). Shape chi is a supplementary SO(3) orbit invariant, not a fifth independent likelihood.

## R4. Divergent physical candidates
Route A: exact SO(3) orbit relation between shape chi and sign-domain fraction F_Omega. Distinguish full-sky shape from mask-supported occupancy. Highest immediate interpretability, no new Fisher data.
Route B: nonregular nodal topology near chi=0 and its consequences for delta-method tests, tilted Bianchi shape crossings. Test saddle asymptotics.
Route C: two-depth source-specific optical shear versus common angular calibration. Derive Schur rank and evaluate original CF4 sky geometry; physically qualify g(z) before inferencing.
Route D: finite-redshift Jacobi transport and Weyl/Ricci sensitivity of apparent distance tensor. Test exact/ODE examples and tilted matter contributions.
Route E: arbitrary higher ell and hemispherical parity; maintain actual W_z mode-coupling and field law; do not infer from scalar F alone.
Route F: generic Bianchi Lie algebra with tilt and multiple fluids, via prior R69 Jacobi/Codazzi plus a NEW P1-relevant null Ricci focusing bridge. Preserve Type I–IX class A/B, not only non-tilted I.
Prune purely formal new x-only score inventions; all routes above yield concrete physical observables/counterexamples.

## R5. Constructive derivations

### Theorem P1-II-T1: exact STF5 shape-to-sky morphology reduction
For S in STF(3)\{0}, define q_S(n)=n_i S_ij n_j and I2=tr S²>0, I3=tr S³, chi=sqrt(6)I3/I2^(3/2). The eigenvalues are uniquely determined up to permutation and positive scale by (I2,chi), because the characteristic polynomial is lambda³-(I2/2)lambda-(I3/3)=0. SO(3) rotation changes eigendirections but not the solid-angle area. Thus F_Omega(S)=measure_S²{q_S>0}/4pi = mathcal F(chi).
For lambda1<=lambda2<=lambda3 with lambda1<0<lambda3, polar t=|cos(theta)| about eigenvector lambda3, and phi azimuth, positive q requires
cos² phi < [lambda2(1-t²)+lambda3 t²]/[(lambda2-lambda1)(1-t²)].
Put ta=sqrt(-lambda1/(lambda3-lambda1)) and tb=sqrt(-lambda2/(lambda3-lambda2)) if lambda2<0 else 0. Then:
F_Omega=1-ta+integral_(tb)^(ta) (2/pi) arcsin sqrt{[lambda2(1-t²)+lambda3 t²]/[(lambda2-lambda1)(1-t²)]} dt.
Use continuous limits for double eigenvalues. Hence F(+axis,chi=+1)=1-1/sqrt3, F(chi=0)=1/2, F(chi=-1)=1/sqrt3. F(-S)=1-F(S) for any S≠0.
**Novelty status:** formal corollary of classical quadratic-form sphere distribution; the physics use as a source/mask contrast is the project application. It does NOT make chi and F_Omega independent observables.

### Theorem P1-II-T2: nonregular morphology at chi=0
Consider S_delta=diag(-1,delta,1-delta) near delta=0. Then chi(S_delta)=-(3sqrt3/2)delta+O(delta²). Its exact full-sky F obeys:
F(S_delta)=1/2 + [delta/(2pi)] log(1/|delta|) + O(delta)
=1/2 - [chi/(3sqrt3 pi)] log(1/|chi|) + O(chi).
Proof sketch with controlled local geometry: F_delta=(4pi)^-1 integral Theta(q_delta) dOmega. At delta=0, q=z²-x², its nodal contours cross at y=±1, where the intrinsic spherical gradient vanishes. In local coordinates u=z-x, v=z+x at each crossing, q_delta=uv+delta+smooth higher-order terms and dOmega=(1/2+O(u²+v²)) du dv. Differentiating the area with a cutoff around uv=-delta yields a log(1/|delta|) term: both crossings together give F'(delta)=(1/2pi)log(1/|delta|)+O(1); integrate. On the remaining regular zero-set, coarea gives a bounded C^1 contribution, hence O(delta). This is a nodal topology/saddle effect, NOT singular GR dynamics.
Consequence: ordinary differentiable delta-method uncertainty propagation for F(chi) can be unreliable near chi=0, a locus relevant to untilted normal-j=0 Type V and other Bianchi shape strata. At actual finite sky resolution, noise/masks regularize or distort it; calibrate via source-level simulations rather than a naive Gaussian χ² pivot.
Derived analytical coefficient numerically checked: delta 10^-4 to 10^-5 finite-log slope 0.1591299479, expected 1/(2pi)=0.1591549431.

### Theorem P1-II-T3: shear response separation from common angular calibration
In two nonoverlapping redshift bins, assume linearized optical/shear response with the SAME physical STF5 S and SAME additive angular calibration b, but distinct scalar, physically specified response g_i:
y_i=B_i(b+g_i S)+epsilon_i,
E epsilon_i=0, Cov(epsilon_i)=C_i, independent bins for closed form, A_i=B_i^T C_i^-1 B_i>0 on STF5, i=1,2.
The joint Fisher for (b,S) has blocks A1+A2, g1A1+g2A2, g1²A1+g2²A2. Profiling b yields exactly
F_{S|b}=(g1-g2)² (A1^-1 + A2^-1)^-1.
Proof: block Schur complement and parallel-sum identity. Thus g1=g2 gives ZERO identified physical shear even with arbitrarily many sources; g1≠g2 and both full-rank angular operators yield five identifiable directions. Independent per-bin b_i renders S unidentifiable again. Source cross-bin covariance changes the closed expression but retains the general projected-Jacobian criterion.
**General Bianchi and tilted 5x5 response theorem:** let the physical shear state be s in a single transported observer STF frame, and replace each scalar g_i by a general 5x5 optical/kinematic linearized transfer G_i, so y_i=B_i(b+G_i s)+epsilon_i. The exact profiled information is
F_{s|b}=(G_2-G_1)^T (A_1^-1 + A_2^-1)^-1 (G_2-G_1).
Consequently rank F = rank(G_2-G_1) when A_i>0, including general noncommuting shear eigenframe histories and tilted matter response, provided G_i are source-qualified physical transfers, NOT coordinate rotations. If G_1=I5 and G_2=D^(2)[R_z(phi)] is only an illustrative l=2 rotation response, generic angle phi leaves the axial m=0 STF mode unobservable, giving rank4. At phi=pi rank2 and at phi=0 rank0; a genuine 10% amplitude transfer change combined with phi=.37 gives full rank5. A mere change in tetrad coordinates is gauge and creates NO observable information. This is a conditional physical-response design theorem, not an observed Bianchi model or a source-validated g(z).
Actual R62/R61 apparent K(z) or distance labels are NOT a qualified physical g(z); finite-z Sachs optical or other calibrated transfer is required. This theorem is a precision-target/design formula, NOT a claimed increased observed Fisher information.

### Theorem P1-II-T4: finite-z Jacobi optics and distinct Ricci/Weyl responses
For a twist-free regular lightcone before caustics, choose a parallel-transported Sachs screen and pastward increasing affine distance lambda, with Jacobi matrix J(0)=0, J'(0)=I2. Then
J''(lambda)= -T(lambda)J(lambda), T=[(R_ab k^a k^b)/2]I2 + W^TF_{AB},
D_A=sqrt(det J), D_L=(1+z)^2D_A.
Here W is screen tracefree Weyl tidal and k is affine null tangent. In a shear-free reference with J0=lambda I and delta T small at FIXED affine lambda:
delta log D_A(L)=-(1/(2L)) int_0^L (L-s)s tr(delta T(s))ds
=-(1/(2L)) int_0^L (L-s)s delta(Rkk)(s) ds.
Thus a pure tracefree Weyl perturbation changes area distance at second rather than first order around that reference, though first-order image ellipticity is present. A constant tracefree W=diag(eps,-eps) gives exact J+ = sin(sqrt eps L)/sqrt eps and J- = sinh(sqrt eps L)/sqrt eps (eps>0), hence
D_A/L=1-eps² L^4/180 + O(eps^4 L^8).
A constant scalar focusing T=kappa I yields D_A/L=sin(sqrt kappa L)/(sqrt kappa L)=1-kappa L²/6+O(kappa²).
These are analytic/ODE toy forward checks, not cosmological solutions. At fixed observed z, source/observer redshift and lambda_s(z,n) perturbations must be included, so the fixed-affine formula alone is NOT the luminosity distance law measured by P1.

### Theorem P1-II-T5: universal tilted-matter null Ricci focusing and hidden quadrupole
For any Bianchi class A/B (indeed arbitrary local spacetime), let N^aN_a=-1 be the homogeneous hypersurface normal, U^a=c Gamma(N^a+beta^i e_i^a) a tilted perfect-fluid four-velocity, k^a=omega(N^a+e^i e_i^a) a future null tangent with e²=1, gamma=(1-beta²)^(-1/2). The source stress-energy T_ab=(epsilon+p)U_aU_b/c²+p g_ab. Since k²=0 and Einstein equations imply Rkk=(8piG/c^4)Tkk, independent of Lambda:
Rkk=(8piG/c^4)(epsilon+p)Gamma² omega²(1-beta·e)².
This produces l=0,1,2 local angular factors; if beta=beta zhat:
A0=Gamma²(1+beta²/3), A1=-2Gamma² beta, A2=(2/3)Gamma² beta² (Legendre P_l coefficients).
Two equal-enthalpy, oppositely tilted fluids ±beta have total normal momentum j_N=0 (compatible with Bianchi I Codazzi) but:
Rkk_total /[(8piG/c^4)(epsilon+p)omega²] =2Gamma²[1+beta² mu²],
so A1 cancels but A2=(4/3)Gamma² beta² remains, along with nonzero normal anisotropic stress. At beta=.3, A0=2.2637362637, A2=.1318681319, A2/A0=.05825242718. This is a direct algebraic compatibility counterexample to "zero total flux implies isotropic Ricci focusing". Whether a full Bianchi solution realizes it over cosmic history requires Euler/Einstein constraints and evolution, not only local Tkk. The Lie structure only governs admissible total matter momentum and curvature response: C_i=-3sigma_ij a^j+eps_ijk sigma^j_l N^{lk}=-(8piG/c³)j^N_i from R69, valid with its fixed conventions; Jacobi N^{ij}a_j=0. **Neither theorem restricts the family to untilted type I.**

## R6. One bounded adversarial self-audit
- F(chi) no independent Fisher information: different labels for same deterministic STF5; mark as descriptive two-view only.
- Full-sky area and unweighted catalogue occupancy are different measures. Equivariance to SO(3) holds for the full sky, NOT fixed survey footprint.
- R62 K0 is an apparent CF4 tensor; direct normal-frame sigma and observational Q_H or Bianchi family membership remain UNAVAILABLE.
- Near chi=0 derivative singular: do not use ordinary delta method or assert cosmic parameter singularity.
- Two-bin closed Schur requires independent bin noise and one identical calibration b_5 plus known g_i. Unmodeled calibration drift b_i or arbitrary physical peculiar velocity destroys identification.
- Perlick/Sachs fixed-affine perturbation is NOT fixed-z and does not bypass observer boost, optical caustic, Weyl shear or GR geodesic transfer.
- Opposite-flow dust example has total j=0 but pi≠0; full 3+1 Hamiltonian and Einstein–Euler evolution not demonstrated here.
- No seven-source p-value multiplication; shared PR3/PR4 and CF4 variants inherit original provenance.
- Full-width support of survey mask is not physical lensing shear; scientific status remains conditional.

## R7. Actual executed checks and outcomes
Input original CF4 table4 raw SHA b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94; parse 38,053 valid groups. Input R62 apparent STF5 K0=(-0.0127031280,-0.0199524708,-0.0002071600,+0.0062355643,+0.0008323007), chi=-0.1227664664766674. Exact full-sky angular F=0.5236421641269079 (R69 pre-existing Gauss sky numerical F=0.52362060546875). Directional conversion raw Galactic → ICRS with Astropy, round-trip maximum ~1.3e-13 rad; independent uniform random sky ~0.522 agrees finite Monte Carlo.
On raw CF4 groups 40–400 Mpc, 31,649 directions, F_sample=0.26300988972795347, gap to true full-sky -0.2606322743989544. Galactic-north separately F+=0.2304235938074425, F-=0.37430245535714285: hemispherical contrast -0.14387886154970034 despite q(n) exactly EVEN under n→−n. By distance 80–140 Mpc F_sample 0.2692307692, 140–220 0.2985795455, 220–400 0.2249388753; all are geometric footprint samples, not observation p-values or weighted R62 source-matched estimator.
Unweighted paired-bin geometry (C_i=Id, response contrast g1-g2 normalized to 1): 40–80 / 80–140 Mpc: A1+A2, profiled 5x5 response Schur eigenvalues [202.1244,232.5832,356.9100,421.4317,456.0952], cond(sqrt eigen ratio)=1.50217. 80–140 / 140–220 eigenvalues [240.7182,266.2991,487.5711,581.9523,677.9550], cond=1.67821. This proves source geometry can distinguish two differing scalar response factors, not that their actual physics is observed; g source response, calibration law and cross-bin covariance not supplied.
Saddle morphology numeric as deltas 10^-2,...,10^-5, rescaled logarithmic slopes approach 1/(2pi) after constant O(delta). Exact axial endpoints and F(-S)=1-F(S) tested.
Matrix-response test on the same CF4 40–80/80–140 source geometry, 5x5 SO(3) STF representation and arbitrary noncommuting G_1,G_2: direct Schur versus transfer-difference formula Frobenius residual 5.35e-13. Pure rotation phi=0/.37/pi has profiled rank 0/4/2 against the fixed unprofiled source-geometry scale; physical amplitude x1.1 with phi=.37 has rank5. Values in RESPONSE_RESULT.json. The initial rank test wrongly compared all-zero Fisher to its own machine-roundoff maximum; fixed by comparison to unprofiled A1+A2 scale, preserving the failed diagnostic as evidence.
Optical: solve_ivp Jacobi ODE with rtol1e-12, atol1e-14 vs exact sin/sinh formulas for Weyl eps=.2,.1,.05,.025: pure-Weyl area deficits 0.00022223986,0.00005555666,0.00001388896,0.00000347223 versus eps²/180, error higher order. Scalar Ricci k=.2,.1,.05 also checked. Legendre multipole quadrature tilted ±0.3 matched analytical P0/P1/P2. An overly large 400-point Gauss rule gave ~1.57e-13 roundoff versus overly strict 5e-14 tolerance; diagnosed and replaced with 64-point polynomial-exact Gaussian quadrature, achieving asserted equality without inflating tolerances. Initial Python import failure fixed by explicit PYTHONPATH=.; no physical inference affected.

## R8. Convergent scientific ranking
Selected for P1 immediate paper explanation:
(1) T1 plus actual source-footprint contrast: highest explanatory benefit, low computational cost, no new Fisher information. A clear method to prevent mask-induced hemisphere claims.
(2) T3 with a real source-qualified g(z), plus original R61 5x32 bias operator and R64 covariance: most actionable *potential* physical identifiability advance. Must compare actual nuisance-projected spectra, not declare detection from rank.
(3) T4 exact Jacobi + T5 tilted matter focusing: correct physical forward response for nonlinear redshift, general Bianchi, all source frames; currently no real full pipeline.
(4) T2 near-chi=0 cusp: useful warning for bootstrap and geometric family strata.
Deprioritized: adding free l3/l4 multipoles with no transfer, inventing new statistical p-values, interpreting R62/Gaia/CMB tensor shapes as same sigma without frame/transport, source-agnostic F or G_F.

## R9. Six paper routes and the seven original R69 PHY combinations

### Six actual paper tracks (P4 contains two of seven scientific axes)
| Paper | Concrete physical equation and conditional 5 views | Evidence/next calculation |
| P1 selected tensorized inference | x=STF5 / joint 15D source carrier; physical Hdir>0 gives Q_H if qualified; F_Omega=F(chi) for pure even STF, Pi matched selected Gaussian law, G_F only physical transport | T1–T5 plus actual raw CF4 geometry; selected 274-row law not rerun |
| P2 low-ell CMB morphology | photon intensity f_n obeys Liouville/Thomson Boltzmann; moment cone M=[[1,f^T],[f,I/3+S]]>=0 sets Q_gamma. Pi needs full T/E/B, cosmic variance, beam/noise. Angular energy occupancy needs higher photon moments or closure; single sky no G_F | R66 PR3/PR4 retained stress, physical source history lacking |
| P3 directional Hubble | Hdir=H−A.n/c+sigma:nn locally; general z H_D/H_ref=e^eta/(1−B eta_z) under R64 flat-ref convention. Q_D positivity denominator and Q_H local have DISTINCT meanings. Pi original source covariance; F morphology from same redshift shell, G_F needs transport | R64 source operator 68/72D; local→finite z solver needed |
| P4 radio dipole/boost/tilt | radio d_b=k_b beta+u_b, source flux selection; local Gamma_MR=−g(U_M,U_R)/c². Q_beta=|beta| only when physical velocity identified, Pi clustering+instrument null, F survey source occupancy, G_F physical tilt history (not flux cut) | R65 shared NVSS and R63 compensated CF4; no independent joint physical likelihood |
| P5 all Bianchi with tilt | Jacobi N a=0; universal normal momentum C_i=−(8piG/c³)j_i, Hamiltonian and shape driver D_t chi=3sqrt6/I2^(3/2)[tr(sigma²D)−(I3/I2)tr(sigma D)], D=(8piG/c²)pi_N−c²Ricci3_STF. Q_Lie when DEC+rho_N; Pi family-specific and nonregular; F area/defined compact measure; G_F exact time transport | R69 Lie-Codazzi CAS and T5 tilted null focusing; no Bianchi posterior |
| P6 beyond-FLRW kinematics | x=(Theta,sigma,omega,A,beta) plus optical response; Hdir sees Theta,A,sigma but not omega at vertex. Q physical causality/positivity, Pi R61 conditional response, F full sky angular event, G_F require cosmic drift/transport | R61 real 11D conditional confidence, omega unidentifiable |

### Seven specific R69 combinatorial routes (same IDs and source limits)
| R69 ID | Typed combination | Concrete conditional bridge | Interpretation/stop |
| PHY-01 | P3+P6+P5 | Hdir=H−A.n/c+sigma:nn; p hemisphere mean difference −A.p/c on full sky, mask adds sigma:(M_+−M_-)_STF; Bianchi C_i ties normal shear to total flux | CF4 mask diagnostic yes, physical source/GR calibration pending |
| PHY-02 | P2+P6+P5 | collisionless photon lowell moments along geodesics plus T5 Rkk tilt focusing and R69 D_t chi shape driver; same normal frame required | photon stress is not local congruence shear; recombination/Thomson optics needed |
| PHY-03 | P2+P4 | boosted rest-isotropic radiation stress pi/rho=[4beta²/(3+beta²)]STF(vhat vhat), chi=+1; contrast T5 single-fluid l1/l2 tilt factors with CMB intrinsic moments | pure-boost algebraic necessary conditions only, real Commander noise/joint response needed |
| PHY-04 | P6+P4+P5 | local-affine screen proper motion grad E2 + rotation B1, no independent B2 from this simple local model; Lie tilt may produce extra optical terms finite z | Gaia apparent B2 may be selection/AGN/optical, not directly omega; physical VSH transfer needed |
| PHY-05 | P5+P6 | Lie-Codazzi with arbitrary a,N tilt; Type V j=0 gives sigma a=0→chi=0, but tilted j≠0 lifts it. T2 reveals F cusp at chi=0 | cannot reject tilted V by chi alone; actual normal-frame tensor needed |
| PHY-06 | P1+P2+P5+P6 | joint physical tensor constraint: shear history sigma→curvature+stress via D_t chi; photons T_ab→Ricci/Weyl Sachs→signed CMB and distance STF. Full tensor alignment/commutator must be checked after frame transfer | shape scalar agreement not a physical cross-probe posterior |
| PHY-07 | P1+P3+radio dipole | source angular odd/even expansions, direct local dipole d, radio k(S)beta, tied higher l3 from d⊗sigma, exact mask M_lm,l'm'. T3 yields two-depth calibration criterion | shared mask/selection and full covariance needed; mixed dipoles not automatically a global tilt |

The seven rows are conditional results/derivation targets, **not seven executed data analyses**. P1 is this loop's only complete R1–R10 focus; downstream applications must preserve respective source semantics.

## R10. Freeze and handoff
- Results are stored in this directory only. Reproducible commands (from htt_base root):
  PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R69_P1_FIVEVIEW_PHYSICS_LOOP2_20261119/verify_physics.py
  PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R69_P1_FIVEVIEW_PHYSICS_LOOP2_20261119/verify_optics.py
- Source authority: intake HEAD 49156d68f1f24d1140e2f2dda08d7041acfd0ca7; current working tree contains many unrelated untracked files. Do not clean them or overwrite canonical R69 evidence.
- Label: R1–R10 **COMPLETED_SCOPED_THEORY** with analytic derivations and finite checks; **independent mathematical review NOT_RUN, R61/P1 actual selected likelihood NOT rerun, physical cosmological posterior NOT_RUN, repository commit/push NOT_RUN**.
- Exact executable next research slice for coding loop after selection: recover R61/R64 selected 35,970 source weights/full covariance and 5x32 depth-bias operator, model one physically justified g_i via finite-z Jacobi + observer-frame transfer, recompute profiled F_S|cal including cross-bin C, compare heldout predictive score and source bootstrap under common calibration vs depth-dependent nuisance. If g_i cannot be physically qualified, retain source-geometry rank and no physical significance claim.
