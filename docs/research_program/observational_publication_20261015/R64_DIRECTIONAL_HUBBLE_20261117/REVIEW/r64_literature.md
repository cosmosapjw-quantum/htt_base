# R64 R2/C2 — primary-source comparison for redshift- and direction-dependent expansion
Date: 2026-11-17 (UTC). Role: bounded source researcher, not final reviewer. Requested model/effort: gpt-6.1-sol/high; observed identity: UNKNOWN. Selected stage only: R2/C2, PhysMath Research Loop 1.3.0. No new data fits, remote mutations, child agents or universal no-go result.

## Principal result
The proposed fixed-ray distance-rate construction is mathematically useful, but its derivative inverse, low-redshift cosmographic limit, logarithmic-distance field, GLS, STF angular representation and calibration degeneracy each have substantial precedents. The most credible potential contribution is a **real-data, common-window, calibration-invariant radial-shape measurement with the full joint signed tensor covariance**, accompanied by explicit optical/kinematic interpretation and radial-response checks. More specifically, the parent's source-integrated full36 radial eta construction, constant-angle calibration quotient, and weakly identified nonlinear H_D/q_D confidence image form a defensible combination to investigate. This is a constructive candidate, not a novelty theorem or an executed new measurement.

Three recent CF4 papers materially overlap the proposed work:
- Kalbouneh et al. 2510.02510v2 already analyze logarithmic expansion-rate fluctuations in radial shells and fit covariant cosmographic multipoles.
- Vicente et al. 2607.07821v1 already reconstruct all 2l+1 angular DOFs of l=1,2,3 with STF tensors, mask kernels and Monte Carlo covariance.
- Salzano et al. 2512.02526v2 already use logarithmic Hubble-law fits, radial shells, selection diagnostics and PV-correction comparisons.
Consequently “use eta,” “recover the full tensor,” “use covariance,” and “study radial evolution” are insufficient standalone novelty claims.

## Source and execution provenance
Actual discovery tools used: Exa web_search_exa (5+10+5+5 requested results = sources_reviewed 25) and SciSpace search (two queries; 15 and 8 requested limits). Exa web_fetch_exa read primary arXiv full text. Generic web retrieval opened the accessible primary papers; returned refids are recorded below. Exa/SciSpace metadata were treated as discovery, not equation authority. In particular, Exa generated incorrect Author headers for Vicente and Salzano; the primary bylines and arXiv abstracts correct them.

Prior local evidence read: r61_kinematic_sources.md and r63_literature.md. Their unchanged boost, photon-frame, finite-depth and PV-formula results are reusable within their original assumptions. Parent-provided H01/H03, R37, R61 and R63 summaries were context, not independently rerun numerical evidence.

A system1 query with exact arXiv URL text returned irrelevant results; those results were excluded. Some primary URLs were unavailable to generic web retrieval but were successfully read with Exa; this is a retrieval limitation, not missing scientific evidence. One attempt to persist all raw fetched text through an oversized shell argument failed with Argument list too long; no scientific computation failed, and only bounded distilled outputs are saved here.

## 1. Three distinct objects and source-supported conventions
Use signature (-,+,+,+), sourceward unit n, physical expansion/shear rates Theta and sigma (1/time), physical four-acceleration A (length/time^2), luminosity distance with length units, and a single declared source/observer congruence. A fixed observer-sky ray is held fixed in partial_z.

1. Physical redshift propagation rate:
   Hcal(n)=Theta/3+sigma_ab n^a n^b-A_a n^a/c.
   Heinesen 2010.06534v2: original Eqs (2.11),(4.1); HTML sequential Eq(11). The minus sign follows the future incoming photon convention k=E(u-e) with e sourceward. Koksbang 2412.12637v3 Eq(3) independently displays the c-restored formula with this acceleration sign.
2. Distance-defined rate:
   D_M=D_L/(1+z), H_D=c/(partial_z D_M).
   This is a rate constructed from a radial derivative of an optical observable; its equality to physical H needs additional geometry and frame assumptions.
3. Finite survey coefficient H_W:
   A fitted constant, polynomial coefficient or multipole is a response of the actual redshift/angular window, weights, covariance and nuisance model. Distinct selection/window operators need not estimate the same local tensor or ideal-sphere volume flow.

Literature-supported optical separation: Heinesen original Eqs (2.11),(2.14),(2.16), HTML Eqs(11),(14),(16):
   dE/dlambda=-E^2 Hcal;
   d^2 D_A/dlambda^2=-(sigmahat^2+R_ab k^a k^b/2)D_A;
   D_L=(1+z)^2 D_A.
The first transports redshift; the second transports beam area. Their independent appearance explains why H_D is not automatically Hcal away from the vertex. Assumptions include geometric optics, photon conservation for distance duality, a regular light cone without problematic caustics, and locally invertible lambda -> z.

Derived direct consequence, in the source's c=1 affine convention and E_o=1:
   partial_z[(1+z)D_A] = D_A - (dD_A/dlambda)/[(1+z)Hcal].
Thus the distance derivative also depends on optical expansion. This elementary chain-rule identity is not a new literature result.

At the observer, the general smooth matter-frame cosmographic expansion gives
   D_L=cz/Hcal_o+c(1-Qcal_o)z^2/(2Hcal_o)+O(z^3).
Hence H_D(0,n)=Hcal_o(n) and q_D(0,n)=Qcal_o(n), with q_D=-1+(1+z)partial_z ln H_D. This is a local limit under the above congruence/frame and regularity assumptions; a finite-window fit does not establish it automatically. Maartens et al. also show that a boosted observer's uncorrected D_L slope requires a correction; transport the actual catalogue operation from R63 before applying this limit.

## 2. Exact inverse-distance identity and curvature counterexample
Let the reference distance be flat-form D_L,ref=(1+z)chi_ref with chi_ref'=c/H_ref, and eta=ln(D_L,ref/D_L). Then
   D_M=chi_ref exp(-eta),
   H_D/H_ref=exp(eta)/[1-B eta_z],  B=H_ref chi_ref/c.
This is a derived algebraic identity for differentiable positive distances where its denominator is nonzero. eta_z is taken at fixed observed direction. “Exact” applies to this definition, not to a claim about arbitrary-spacetime physical expansion.

Seikel, Clarkson & Smith 1204.2832v2, Eqs(3.1),(3.2), already give for normalized D=(H0/c)D_M in spatially flat FLRW:
   H=H0/D',  q=-(1+z)D''/D'-1.
The eta expression is a useful reparameterization of this established inverse-derivative construction.

Clarkson, Bassett & Lu 0712.3457v2 Eq(2), with c restored and dimensional D_M:
   Omega_k=[(H D_M'/c)^2-1]/[(H0 D_M/c)^2].
Therefore, even in curved FLRW,
   H_D=H/sqrt[1+Omega_k(H0 D_M/c)^2].
The positive branch assumes D_M'>0 over the domain. Spatial flatness is a sufficient FLRW closure for H_D=H, while a curved FLRW counterexample is enough to reject a geometry-free identification. This is not a theorem ruling out reconstruction after adding the correct closure or another probe.

CBL Eq(3) supplies the associated consistency combination in c=1 units:
   C(z)=1+H^2(DD''-D'^2)+H H' D D'=0  (FLRW).
The paper explicitly notes derivative-error amplification and that C=0 alone is not a sufficient characterization of FLRW.

## 3. Relation to the existing eta literature and calibration quotient
Kalbouneh et al. Eq(1) and Vicente et al. Eq(2) define
   eta_K(z,n)=log10[z/D_L(z,n)]-<log10[z/D_L]>_Omega.
Consequently, for an isotropic reference,
   eta-<eta>_Omega = ln(10) eta_K.
The proposed eta retains a declared reference/monopole and uses natural logs; the published field removes a shell monopole and uses decimal logs. Never copy amplitudes without ln(10), and never identify removal of a global monopole with removal of an arbitrary angular calibration field.

Derived calibration transformation:
   eta -> eta+a(n), D_M -> exp[-a(n)]D_M,
   H_D -> exp[a(n)]H_D.
Thus H_D(z1,n)/H_D(z2,n), partial_z ln H_D and q_D are invariant under a redshift-independent angular zero point. This does not remove radial calibration evolution a(z,n), opacity evolution, population/selection changes, or differently projected angular zero points in different windows.

A practical parent-owned response test is needed: construct the same angular calibration columns through every actual window, then select contrasts annihilating that response. Merely subtracting differently weighted radial-bin coefficients does not guarantee cancellation on an incomplete sky. Since existing H01/H03 outputs already have 4 windows and joint signed multipoles, checking this map can reuse their full response/covariance without claiming a new fit.

## 4. Primary source register (12 core sources)

### S01 — Kristian & Sachs (1966)
Observations in Cosmology, ApJ 143,379; DOI 10.1086/148522.
Primary scan: https://adsabs.harvard.edu/pdf/1966ApJ...143..379K
Exa read the primary scan. Sec III.2, p393-394, Eqs(68),(70)-(74): corrected luminosity distance r, directional z=Wr+Xr^2/2+..., and W's expansion-monopole/shear-quadrupole decomposition for the geodesic-dust case. The paper separately discusses an acceleration dipole outside that case. Reuse: foundational local anisotropic distance/redshift cosmography; r in Eq(68) is not to be silently identified with modern D_L. No claim of novelty for a directional linear law. Generic web PDF access failed; use Exa or original scan for any further equation import.

### S02 — Heinesen (2021)
Multipole decomposition of the general luminosity distance 'Hubble law' — a new framework for observational cosmology, JCAP05(2021)008; arXiv:2010.06534v2, version 2021-04-23.
Primary: https://arxiv.org/html/2010.06534v2
Refs: turn505925076view2, turn887747889view1, turn976421727view0.
Original numbering (PDF): (2.11), (2.14), (2.16), (3.9),(3.10),(4.1),(4.5)-(4.7). HTML uses sequential (11),(14),(16),(24),(25), etc.; distinguish these numbering schemes.
Reuse: redshift-energy transport, focusing and reciprocity, finite multipoles, local H/Q/J/R expansion. c=1, (-+++), sourceward e. The leading H has 1+3+5=9 DOFs; higher-order normalized parameters have constrained multipole structure.
Known source errata: as recorded in R61 from Heinesen–Korzyński 2024, selected shear-evolution/curvature/acceleration-vorticity terms in the old paper need corrections. The leading H expression used here is not implicated; do not blindly import all appendices.

### S03 — Clarkson, Bassett & Lu (2008)
A general test of the Copernican Principle, PRL101,011301; arXiv:0712.3457v2, version 2008-03-17; published 2008-07-02.
Primary: https://arxiv.org/html/0712.3457v2
Refs: turn405904473view3, turn379130618view3.
Eqs(1)-(3), Appendix Eqs(4),(5): distance-curvature-expansion consistency, transverse vs radial LTB rates. c=1 in source; D=(1+z)D_A dimensional. Reuse: curved-FLRW closure counterexample and need for an independent expansion observable; not an unrestricted anisotropic reconstruction theorem.

### S04 — Seikel, Clarkson & Smith (2012)
Reconstruction of dark energy and expansion dynamics using Gaussian processes, JCAP06(2012)036; arXiv:1204.2832v2, version 2012-05-31; published 2012-06-25.
Primary: https://arxiv.org/html/1204.2832
Read: Exa full primary text (generic web unavailable).
Eqs(1.1),(2.15)-(2.25),(3.1),(3.2),(3.4): inverse distance derivative, q, derivative GP covariance, modulus calibration combination.
Reuse: joint function/derivative law and observational covariance C; finite smoothness and kernel/hyperparameter dependence are explicit inference assumptions. It is not a theorem that sparse noisy differentiation is prior-free.

### S05 — Maartens, Santiago, Clarkson, Kalbouneh & Marinoni (2024)
Covariant cosmography: the observer-dependence of the Hubble parameter; arXiv:2312.09875v3, version 2024-06-14.
Primary: https://arxiv.org/html/2312.09875v3
Ref: turn887747889view2; detailed unchanged formula checks reused from r61_kinematic_sources.md.
Eqs(19),(27),(34a-c),(67), Sec4.2 and Appendix A.6. Geodesic matter frame H has monopole+shear quadrupole; boosted measured multipoles acquire velocity and shear-aberration contributions. Eq(67) distinguishes the corrected luminosity-distance slope. Reuse: exact observation-frame contract and distinction between H and inverse-H bin fits; not a second independent new response derivation.

### S06 — Dhawan, Borderies, Macpherson & Heinesen (2023)
The quadrupole in the local Hubble parameter: first constraints using Type Ia supernova data and forecasts for future surveys, MNRAS519,4841; arXiv:2205.12692.
Primary: https://arxiv.org/html/2205.12692
Read: Exa full primary text.
Eqs(1)-(3), (10)-(16),(18); Sec2.3 and Sec3. Full general-cosmography motivation specialized to a Hubble quadrupole and deceleration dipole with scale-decay ansatz. Eq(12) H=Hm+Hq:ee F_quad(z,S); Eq(18) uses full SN covariance in modulus space.
JLA analysis reports an approximately 10% upper limit on H quadrupole at ~100 h^-1 Mpc; no significant quadrupole detection. The deceleration dipole depends on frame/PV corrections (heliocentric ~3sigma, CMB ~2sigma, PV-corrected insignificant). Reuse: direct prior work on scale-dependent anisotropic cosmography and covariance; exponential decay is a model ansatz, not a general light-cone transport law.

### S07 — Koksbang (2025)
Testing inhomogeneous cosmography in our cosmic neighborhood using CosmicFlows-4, PRD111,123516; arXiv:2412.12637v3, version 2025-10-31.
Primary: https://arxiv.org/html/2412.12637v3
Ref: turn140327146view4.
Eqs(2)-(4), SecIV.1.1 and discussion. A CF4-informed weak-field model tests third-order Taylor coefficients against ray tracing and empirical polynomial fits, including interpolation/resolution/smoothing changes.
Important precise qualification: low-redshift breakdown of a third-order truncation does not establish the exact infinite-series radius of convergence; slow convergence can also matter. A good finite polynomial fit can remain informative while probing smoothed effective parameters. Reuse: dataset/model-specific truncation and window checks. It is not a universal no-go against useful cosmographic fitting.

### S08 — Kalbouneh et al. (2026)
The anisotropic expansion rate of the local Universe and its covariant cosmographic interpretation, JCAP03(2026)084; arXiv:2510.02510v2, version 2026-03-09.
Primary: https://arxiv.org/html/2510.02510v2
Refs: turn405904473view0, turn976421727view1, turn379130618view1, turn505925076view1.
Eq(1) eta_K; Eq(12) redshift series; Eqs(13),(14) CC fit; Appendix A Eqs(15)-(21) simultaneous monopole+SH GLS, coefficient covariance and explicit omitted-mode bias.
CF4 0.01<z_CMB<0.1; four broad display slices [0.01,.03],[.03,.05],[.05,.075],[.075,.1], finer shells for CC fits. Assumes independent CF4 modulus errors because catalogue supplies no full covariance; Pantheon+ full covariance used. Estimates unrestricted SH first, then common-axis Legendre coefficients and restricted CC parameter family. Monopole excluded from the CC fit, leaving H2/H0 rather than absolute H2.
Reported CF4 H2/H0=(2.8±0.4)e-2 (~7 SNR), Q1=2.0±0.4, Q3=.9±.3; these are within the axial/CC/measurement model. Sec6 explicitly distinguishes formal local derivatives from nonlocal empirical fitting (HTML lines467-475). Its claim of distance-independent selection immunity should not be transported as a theorem for arbitrary angular calibration or survey mixtures; its Appendix A itself quantifies angular/radial leakage. Reuse: exact eta mapping and a direct comparison target; no new generic eta/GLS claim.

### S09 — Vicente, Pereira, Rodrigues, Vitenti & Gomes (2026)
Multipolar structure of the local expansion rate from incomplete sky data; arXiv:2607.07821v1, submitted 2026-07-08 (18:04:25 UTC).
Primary: https://arxiv.org/html/2607.07821 ; https://arxiv.org/abs/2607.07821
Discovery ref: turn622015173academia37; full text/abstract successfully read with Exa; generic full-text unavailable.
Eqs(2),(4)-(9): eta_K and low-z velocity response eta_K=v/(cz ln10), inverse-variance pixel average. Eqs(10)-(12): mask coupling kernel. Eqs(13)-(18): STF/multipole-vector representation. Eqs(26)-(29): covariance-aware harmonic likelihood, MC covariance and theoretical spectrum. Eqs(30)-(32): full-vector alignment statistics.
Uses individual objects in 0.01<=z_CMB<=0.05 (24,646 before mask), masks at Nside=4,8,16, pixel population thresholds 14,5,3, ±10 degree Galactic strip, iterative neighbor criterion. Adds independent nonlinear velocity scatter nominally 300 km/s; correlated signal is compared using theory/MC. The spectrum has a specified radial-bin integration and simulations use mean cosmological redshift per pixel, so this is not an exact substitute for another estimator's actual position/weight covariance.
Reports dipole 3.3sigma above its LambdaCDM prediction, direction (290,-4)±5 degrees, mostly .03<z<.05; quadrupole and octupole consistent at95%. Although extrema align, complete multipole-vector tests show no anomalous alignment (p roughly32%-94%). Reuse: full STF and mask corrections are already demonstrated; retain signed tensor information and compare matching operators.

### S10 — Salzano, Beltrán Jiménez, Bettoni, Brax & Valade (2026)
Updates on dipolar anisotropy in local measurements of the Hubble constant from Cosmicflows-4; arXiv:2512.02526v2, submitted v1 2025-12-02, version v2 2026-04-15.
Primary: https://arxiv.org/html/2512.02526v2 ; https://arxiv.org/abs/2512.02526
Refs: turn935913186view0, turn140327146view1, turn887747889view0.
Use arXiv version date, not the dynamically rendered “August24,2026” body date or inconsistent discovery metadata.
Eqs(5)-(14): HL ratio, cosmographic factors, logarithmic modulus formulation and PV-redshift correction; Eqs(15)-(21): weights, intrinsic scatter tuned per shell, residual statistics; Eqs(22)-(24): harmonic model and likelihood; Tables1-5.
Works with grouped CF4 observed z_CMB and comparison reconstructed-PV-corrected redshifts; 1+z_cosmo=(1+z_CMB)/(1+z_pec), Eq(10). Uses conservative selected ranges mu in[31,36] and z in[.03,.06], evaluated as alternative binning routes, not necessarily their intersection. Conditionallly independent Gaussian modulus errors; no supplied full heterogeneous calibration covariance. Uses fixed flat-FLRW q0=-.595,j0=1 in its baseline series correction. Fitting log-H0 with an angular H0 model differs from H_D, and displayed tables chiefly summarize a chosen aligned multipole representation.
Observed example Table1 mu-selected dipole-only fit: a10=9.7±.4 km/s/Mpc, lnB=310 relative monopole; PV-corrected a10=2.9±.4, lnB=76. Table4 z[.03,.04]: a10=7.8(+.8,-.9), lnB=45; Table5 corrected same shell a10=2.9(+.9,-1.0), lnB=6. These are model-specific evidence/coefficient quantities, not global trial-corrected Gaussian detection significances. Reuse: direct log-law and PV/selection radial sensitivity; no robust monotonic radial trend reported.

### S11 — Stiskalek, Desmond & Lavaux (2026)
No evidence for local H0 anisotropy from Tully–Fisher or supernova distances, MNRAS546(2),staf2048; arXiv:2509.14997v2, version2025-11-17; journal published2026-01-22.
Primary: https://academic.oup.com/mnras/article/546/2/staf2048/8436862 ; https://arxiv.org/html/2509.14997v2
Prior r61 checks reused. Exa fulltext at v2 URL labels embedded text “v1”; do not claim byte/version identity from that output alone. Core equations and method match prior verified source and publisher abstract.
Sec3, Eqs(8),(9): dipolar tracer-zero-point and DeltaH0/H0=10^(DeltaZP/5)-1. Forward model fits apparent magnitude, linewidth, observed redshift and latent distances, reconstruction-scaled internal PV plus external flow, and selection effects. Primary W1 CF4 sample after cuts3246, z_CMB roughly<.05, quality5, eta_linewidth>-.3, |b|>7.5deg; this eta is a linewidth variable, not the expansion eta. Uses reconstructed C15 velocities plus small-scale dispersion; Pantheon+ covariance PV terms removed to avoid double counting with explicit PV model.
Reported CF4 zero-point dipole .087±.019mag (4.1±.9%), evidence odds877:1 for the restricted dipole model. Radial Cartesian external-flow interpolation at0,20,40,60,80,100 h^-1Mpc reveals growth then decay rather than a persistent linearly-growing effective flow. Thus “no evidence” refers to interpretation after the more flexible velocity comparison; the paper does detect a strong restricted zero-point dipole. Reuse: explicit calibration-flow confounding and constructive radial discrimination, not a universal impossibility claim.

### S12 — Nusser & Tully (2026)
Cosmicflows-4 and the Cosmological Consistency of Large-Scale Motions; arXiv:2608.14265v1, submitted2026-08-14.
Primary: https://arxiv.org/html/2608.14265 ; https://arxiv.org/abs/2608.14265
Read with Exa full primary text; actual discovery includes Exa. Generic primary retrieval unavailable.
SecIII Eqs(1)-(12): CMB-redshift positions and nonoverlapping bins, log-distance velocity u_ln=-K_i(ln10/5)Delta_mu, error floor100km/s, measurement-weighted monopole/dipole fit beta=A u with A=(X^T W X)^-1X^T W. SecIV Eqs(14)-(21): measurement plus linear-theory velocity covariance, including cross-window covariance; covariance is propagated through the actual A, not used to redefine the weighting as a total-covariance GLS.
Baseline measurement covariance diagonal; shared catalogue calibration covariance omitted, with illustrative correlated SDSS scale test. The predicted signal covariance uses actual positions, weights and windows. Not an ideal-sphere bulk flow and no l=2 analysis.
Reports all-individual six-bin dipole/joint deviations2.29sigma/2.36sigma through300h^-1Mpc; .12-.16Gpc/h bin |Vdip|628±82km/s with dipole3.40sigma. Removing6dFGS lowers it1.56sigma; removingSN raises it3.77sigma. Not adjusted for catalogue/bin/component multiplicity. SN vs6dFGS differences can remain covariance-consistent despite opposite pulls on a combined fit. Reuse: common estimator/window prediction and cross-bin covariance are essential for a comparison to LambdaCDM.

## 5. Covariance and weak derivative route: reusable mathematics, useful new measurement
Seikel Eqs(2.15),(2.16) establish Cov[f(x),f'(y)]=partial_y k and Cov[f'(x),f'(y)]=partial_x partial_y k; Eqs(2.20)-(2.25) include observational C and the derivative conditional covariance. This is direct prior work on derivative reconstructions. Fixed-kernel derivative GP assumptions, boundary behavior and hyperparameter treatment must remain explicit.

For the proposed eta, eta_i=ln D_L,ref(z_i) -(ln10/5)(mu_i-25) (D_L measured in Mpc). Therefore C_eta=(ln10/5)^2 C_mu under fixed reference/redshifts and the declared Gaussian modulus law, before extra PV/redshift/reference nuisances. Cross-window covariance must be retained.

Derived weak form: for differentiable eta and a fixed compactly supported phi with vanishing boundary values,
   integral phi eta_z dz = -integral phi' eta dz.
It is affine in the modulus residual field after a fixed linear reconstruction, and it annihilates a z-independent angular offset. It avoids numerically differentiating a noisy plotted curve, but it requires a declared window/reconstruction and does not create pointwise information absent from the data. Conversely weak derivatives of D_M=chi exp(-eta) are nonlinear in Gaussian eta; do not claim exact Gaussianity after exponentiation.

Practical estimand choices (component mathematics is established; the actual dataset-specific joint result remains to be produced):
A. Report radial contrasts of the **signed** log-distance dipole and all5 STF coefficients after explicitly annihilating common angular calibration columns. Supply their joint covariance and actual response kernels.
B. Report finite-window weak eta_z or finite radial log H_D ratios with denominator control, jointly propagate eta and its derivative, and compare to the same windows under a declared PV/optical model.
C. Construct a shared-observable comparison of the CF4 estimators above by transporting each through its actual angular/radial operator and calibration/PV law. This addresses a real discrepancy in interpretation without ranking published sigma values as equivalent tests.
These choices can add a data-specific result even though their elementary algebra and GLS are established.

## Closeout and exact remaining obligation
R2/C2 source work is complete within this bounded assignment. Literature-supported: distinct kinematic/optical/window estimands and substantial overlap with recent CF4 work. Derived: eta identity, angular calibration transformation, local limit and weak-form suggestions. No new survey fit, empirical significance, corrected CF4 calibration covariance or universal identifiability theorem was produced.
Parent's next concrete scientific action: choose a window-matched calibration-annihilating radial-shape estimand on the existing joint tensor carrier, prove its actual observation-operator invariance, and quantify it only within the separately authorized fitting/computation stages. A selected closure or independent probe is required to promote H_D beyond its distance-defined meaning.
