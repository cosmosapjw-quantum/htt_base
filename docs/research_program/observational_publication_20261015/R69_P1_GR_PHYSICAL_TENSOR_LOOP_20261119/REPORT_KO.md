# R69 continuation: P1 physical tensor inference, complete bounded theory R1–R10

Date: 2026-11-19 KST
Project: cosmosapjw-quantum/htt_base
Branch/source HEAD at input: research/r69-observable-physics-bridges-20261118 / 8dd029d934f8fe287691c06c5cf7e256608965b5
Parent R69: docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118
Status: NEW SCIENTIFIC DERIVATION + NUMERICALLY CHECKED REAL-SKY GEOMETRY; NOT A COSMOLOGICAL DETECTION; NOT REVIEWED INDEPENDENTLY; NOT ADMITTED TO SIX-PAPER DAG.
Scope: P1 (selected signed STF/tensorized inference) with auxiliary P6 and P3 physical maps, not seven new likelihoods. Original 42 science nodes/acceptance unchanged.

## R1. Controlling physics question
Can the actual P1 STF5 observable distinguish GR-congruence shear and acceleration from optical calibration, peculiar-flow dipoles and observer motion? If an ideal map is locally identifiable, does the signal have a realistic chance of being measured in the actual CF4 source geometry?

## R2. Provenance and prior work
R69 exact Heinesen vertex expansion, radiation/kinetic law and mask leakage are input, not new inventions. R61 data: 35,970 CF4 groups, 32D four-monopole-removed response, joint 11D alpha=(V3,dH3,kappa5), seven shared-source variants and calibration body. P1 selected Gaussian actual-data result is a separate 274-row 15D estimand with fixed covariance shapes and conditional optical bridge. R67 original group-overlap FP/TF/SN calibration quotient is already known; do not recount it as new.
External physics: Heinesen (arXiv:2010.06534), Maartens et al. (arXiv:2312.09875), Adamek et al. (arXiv:2402.12165), Kalbouneh et al. (arXiv:2401.12291); all cover covariant anisotropic cosmography and relevant multipoles, so no universal novelty priority claim.

## R3. Typed state and physical assumptions
Metric (-,+,+,+), timelike u.u=-c², sourceward unit spatial n, H=Theta/3>0, d=-A/(cH), S=sigma/H in STF(3), observer locally comoving with same smooth source congruence, Etherington reciprocity and regular z→0 lightcone vertex.
Hdir(n)=H[1+u(n)], u(n)=d.n+n.S.n, epsilon=sup_{n in S²}|u(n)|<1.
Leading redshift-distance law D_L=cz/Hdir(n)+O(z²). For distance-modulus residual against a consistent isotropic reference:
Delta_mu(n)=-(5/ln10)log(1+u(n))+O(z).
This is a leading-vertex statement only, NOT the exact finite-z or boosted-observer luminosity-distance law. The actual P1 apparent B_5, R61 kappa5, Gaia E2 and matter-normal sigma are different quantities until source transfer qualifies them.

## R4. Divergent candidate routes
A. Exact local Q_H positivity and physical F_sky occupancy, fast scalar constraints but no new observation law.
B. Nonlinear log-H harmonic closure (l3 from d⊗S, l4 from S⊗S), physically tied high harmonics and potential shear/calibration self-identification. Needs full raw rows, finite-z transfer.
C. Angular+radial dipole (constant cosmographic d versus 1/r observer/relative velocity), evaluate actual CF4 source geometry and projected Fisher. Preferred near-term source-level program.
D. Einstein evolution and signed chi dot from total normal anisotropic stress and spatial Ricci STF, only in selected congruence and closure. Do NOT equate observed K1 redshift derivative to shear proper-time derivative.
E. Same-group method calibration quotient, established R67 negative control; cannot be multiplied into independent CF4 likelihood.

## R5. Concrete new P1-specialized results and proofs
The polynomial algebra is standard; here it is applied to a constrained P1 observable response, not asserted as a new GR law.

Let k=5/ln10 and q_S(n)=n.S.n. Expansion
Delta_mu=-k u+(k/2)u²+R, |R|<=k epsilon³/[3(1-epsilon)]+O(z), uniformly.
Define P_4(S;n)=q_S(n)²-(4/7)n.(S²)_STF.n-(2/15)tr(S²), and
P_3(d,S;n)=(d.n)q_S(n)-(2/5)(Sd).n.
By harmonic decomposition of 1⊗2 and 2⊗2:
(Delta_mu)_{l3}=k P_3(d,S;n)+O(epsilon³,z);
(Delta_mu)_{l4}=(k/2)P_4(S;n)+O(epsilon³,z).
Exact expansion of u² on S² has l0=|d|²/3+2tr(S²)/15,
l1=(4/5)(Sd).n,
l2=[STF(dd^T)+(4/7)STF(S²)]:nn,
l3=2P_3, l4=P_4.
The l4 depends on S but NOT d to this order; l3 depends bilinearly on d and S, not a freely fitted octupole.

Theorem P1-T1 (quadratic l4 identifiability): phi(S)=STF4(S⊙S) obeys phi(S1)=phi(S2) iff S1=±S2. Proof: for homogeneous harmonic degree-2 polynomials q_S(x)=x.S.x, equality of degree-4 harmonic projections means r²=x²+y²+z² divides q_1²-q_2². The real quadratic r² is irreducible (hence prime in R[x,y,z]), so divides q_1−q_2 or q_1+q_2. Both are homogeneous harmonic degree-2; the only such multiple of r² is zero. Thus S1=±S2. Additionally Dphi_S[T]=2STF4(S⊙T) has rank5 at every S!=0 by the same divisibility argument. At S=0 the derivative vanishes, so a Gaussian toy whose harmonic coefficient noise scales N^(-1/2) gives nonregular shear identification scale N^(-1/4), not a standard Wilks chi-square law.

Theorem P1-T2 (restricted radial separation): for the phenomenological, first-order, fixed-frame, low-z rate model
Y(r,n)=H+H d.n+H S:nn+(v_rel.n)/r+errors,
the l<=2 angular design has 9 columns, and adding three (1/r)n columns yields rank12 whenever the observed directions and radii span them. If r=r0 identically, (1/r0)n is exactly proportional to the angular dipole and rank<=9. Distinct radial support alone is not sufficient under an arbitrary angle-distance correlation; full column rank must be checked on actual sources. A free radial flow v_rel(r) or arbitrary source calibration can reinstate a kernel. This is a model-identifiability result, NOT an exact frame transformation: full Maartens boost law includes aberration and distance/redshift correction.

Theorem P1-T3 (axial occupancy counterexample): with S=s(pp-I/3), d=0, s≠0, define F_Omega=area{n:u(n)>0}/4pi on one physical observer sky. If s>0 then F_Omega=1−1/sqrt(3); if s<0 then F_Omega=1/sqrt(3). Thus amplitude |s| may evolve while F_Omega and a physical same-sky G_F remain constant, provided actual observer/screen transport preserves p and the sky measure. At s=0 the strict event has an exceptional boundary; no smooth conclusion there. F_Omega is a solid-angle event, not photon energy occupancy or parameter-prior occupancy.

## R6. Adversarial tests and hard counterexamples
(1) Arbitrary optical l4 nuisance makes phi(S) unidentifiable again: b4(n) can offset any competing phi(S). P1's old unrestricted optical bias already precludes universal physical S identification.
(2) At finite z, deceleration, spatial derivatives, photon optics and lensing generate high harmonics; a nonzero measured l4 alone is NOT shear evidence.
(3) Helio/matter observer boost adds aberration and changes luminosity-distance normalization; naive observer velocity/r separation is not a covariant transform.
(4) Mask and survey indicator selection mix multipoles. A mathematically rank-full unweighted design can have negligible calibrated Fisher rank.
(5) Near S=0, use nonlinear profile/null injection, not chi²5 Wilks based on the degenerate l4 Jacobian.
(6) CF4 source variants, FP/TF/SN overlaps and P1 selected rows must not be counted as independent repeated cosmological data.
(7) A depth slope K1 is a redshift response, NOT a proper-time derivative D_t sigma.
(8) P1 physical Q_H is not the old statistical Q or a Bianchi family label; Pi is law-conditioned; F requires its explicit measure; G_F needs physical transport.

## R7. Executed algebra, symbolic CAS and actual-sky numerical checks
Exact Wolfram Laplacians for both P4(S;x) and P3(d,S;x) polynomial harmonic projections are {0,0}. Independent NumPy pointwise decomposition on 12,000 random unit directions: maximal |u²−sum_l u²_l| = 6.505213034913027e−19.
Legendre axial S=s(pp−I/3) with d=0: predicted l4 coefficient (4k/35)s². At s=.01,.03,.1: predicted 0.02481683,0.22335145,2.48168275 millimag; exact log-H projection 0.02475706,0.22175854,2.42529861 millimag. Cubic-order error behaves as expected. At d=.02,s=.04, predicted axial l3 0.00069487117 mag; exact log 0.00068071569 mag. These are deterministic toy values.

Read original CF4 group table4.dat, raw byte SHA-256 b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94; 38,053 valid groups, sky positions and catalogue Dist (Mpc), unweighted. Source geometry matrix uses columns [1,n3,STF5:n n,(100Mpc/r)n3], each normalized to unit Euclidean column norm before computing condition. 40–400 Mpc: n=31649, rank 12/12, angular-only rank9/9, combined cond 5.27698; 80–220: n=13670, rank12/12, cond9.41668; 140–220: n=7040, rank12/12, cond21.26929.
Synthetic axial S=.03 on actual CF4 40–400 Mpc directions: quadratic l4 amplitude template RMS .08612595 millimag, after eliminating l<=2 sky basis RMS .06560074 millimag, local five-component l4 Jacobian rank5 and condition1.93678; apparent STF5 magnitude coefficient error when fitting only l<=2 to exact nonlinear template is .31313909 millimag. 80–220 Mpc residual l4 RMS .06706476 millimag. No CF4 observed residual values or source covariance were used.

Illustrative independent homoscedastic magnitude error of 0.2 mag per group would imply ideal matched-template SNR only ~0.058 for the S=.03 example, ignoring all systematic covariance. This IS NOT a CF4 calibrated SNR.

## R8. Convergence and scientific selection
Accept P1-T1 as a valid conditional mathematical identification result, not a practical CF4 detection method. Reject any claim that an l4 detection has occurred, that physical s is measured, or that it constitutes a new universal GR theorem.
Select P1-T2/source-matched radial Fisher design as the more useful physical analysis candidate because actual CF4 radial support gives a testable 12-column geometry but its effective Fisher after nuisance projection remains UNKNOWN.
Keep P1-T3 as a no-go warning against interpreting F_Omega or G_F as shear amplitude.
Use R67 group-contrast as the negative control/benchmark, not a new independent likelihood.
An unvalidated radial peculiar-velocity model, source calibration covariance, heliocentric boost operator or finite-z optical response is a blocker, not a reason to invent a prior.

## R9. Explicit real-data forward/inference contract
Use ONE set of original selected data and one likelihood:
y_g=mu_ref(z_g)+M_g{-k log[1+d.n_g+n_g.S.n_g]}+X_cal,g gamma
    +T_pv,g V + residual_finite_z,g(theta_opt)+epsilon_g.
Operators M, X_cal, T_pv must come from source selection, observer/matter frames, beam/optical transfer and physics. Covariance C=N_stat+S_pv+J_cal Sigma_cal J_cal^T+C_selection with nonzero cross-source blocks when shared.
For shear column J_S and nuisance N, F_eff=J_S^T[C^-1−C^-1N(N^T C^-1N)^+N^T C^-1]J_S. The source-qualified kernel of F_eff, not angular rank12, controls physical identification. The nonlinear l4 branch requires source-level rows, not STF5-only compressed carriers. Compare physical P1 model with and without tied l4 at heldout source IDs, profile nuisance and use parametric/bootstrap null because the null is singular. Do not profile six independent papers as six independent probes.
Typed five views: x = signed 11D/15D carrier with explicit observable versus physical status; Q_H=-min_n[d.n+n.S.n] if physical d,S source-qualified and H>0; Pi=actual matched-law tail (currently UNAVAILABLE for physical shear); F_Omega=defined angular sign occupancy, distinguished from photon-energy and parameter occupancy; G_F needs the SAME physical observer/source mapping and actual temporal/depth transport (currently UNAVAILABLE).

## Seven cross-axis bridges to address in later loops (P1 is executed here)
A1 P1 itself: source-qualified tensor/selected likelihood, tied l3/l4 and conditional identification theorem, derived here.
A2 P1×P2 low-ell photon morphology: map kinematic S through exact/perturbative Einstein-Boltzmann and beam/null before claiming shared Q_gamma and signed chi, blocked.
A3 P1×radio count dipole: Doppler count slope plus source mask and selection, joint observer-v / density nuisance, blocked.
A4 P1×P6 beyond-FLRW kinematics: d,S plus omega and matter congruence, no omega from leading distance law, partially established R61.
A5 P1×P5 Bianchi: R69 geodesic-normal shear shape driver and Codazzi/curvature, physical S not yet measured, blocked.
A6 P1×P3 directional H(z,n): 12-column radial rank, finite-z expansion and survey covariance, selected.
A7 P1×P4 observer boost vs global tilt: proper covariant boost D_L/redshift + external Gaia proper-motion transfer; no equivalence of Gaia E2 and normal S, blocked.
This is a roadmap, NOT seven completed independent physics fits.

## R10. Closure, tests and reproducibility
R1–R10 bounded theory route executed: formulation, primary context, typed variables, alternatives, proofs, adversarial checks, Wolfram and actual CF4 geometry, decision, forward contract, written handoff. No new native physical solver and no agent-run independent manuscript review. External novelty priority remains unresolved; conditional harmonic algebra is not submitted as first-ever theorem.
Next proposed noncanonical coding slice: R69-P1-C1, use original R61/R64 source/selection and calibrated full CF4 covariance to compute the nuisance-projected Fisher singular spectrum under the correct observer/matter lightcone law. Compare baseline versus tied-log-H l3/l4, bootstrap heldout coverage, require test improvement not just additional harmonic dimensions. Stop if physical source map or covariance missing; retain honest geometry-only result.
Do NOT edit R69 source results or P1–P6 original 42 DAG gates; no public physical anisotropy significance.
