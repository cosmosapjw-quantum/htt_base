# htt_base 물리 입력 7개 수용조건: 구성적 이론 연구 v1

2026-10-16 KST. Authority: six-paper 42-node `PUBLICATION_DAG.json` @ previously published PR #546, completed_scoped 14/42 and seven physical-source blockers retained. This work is a standalone **mathematical/conditional** layer and does **not** change the canonical publication DAG or main. Metric signature (-,+,+,+), timelike matter congruence fixed when used, c explicit. Derivations below apply within precisely stated domains; they are not new astronomical detections.

## Source distinction and key boundary

* Original source observations: CF4 VizieR release includes 55,877 individual-galaxy rows; Table 3/4 VizieR group views have 38,053 rows; source article quotes 38,065 groups. These counts may differ due to catalog construction. Earlier HTT P3 uses 35,970 **selected** unique group rows. Distinguish every row-set, aggregation, and frame.
* Planck PR3 SMICA T/Q/U products and masks come from **one** cosmological sky even when full, HM, OE and component separated variants coexist. SMICA-noSZ full FITS contains only temperature and an in-painted temperature field, not polarization.
* Legacy source formalisms, finite CAS proof components, and archived BASS Rust operator tests are not observational likelihoods and not complete native astrophysical transfer solvers.

## S04: signed defect + partial identification (derived; 2 validations)

Fix one congruence, nonzero H=Theta/3, same comparator and curvature normal. Define x_C=(sigma_ab sigma^ab - omega_ab omega^ab)/(6H^2) + Omega_tilt + DeltaOmega_k. This is a signed dimensionless algebraic combination. If an identified part is x_K and the unmeasured remainder r is physically restricted to [r_-,r_+], its sharp projection is I_x=[x_K+r_-,x_K+r_+] (the Minkowski interval sum), provided every r in the range is attainable with a common underlying physical model. Without such attainability it is a conservative outer interval. If r is genuinely unbounded below/above, interval endpoints are infinite and must not be set to zero. The shear-only anchor U_sigma=(3/2)B_sigma^2>0 is not in general an upper ceiling of total x_C; Q=x_C/U_sigma can be signed and exceed unity.

For a **fixed normalized joint** draw measure p_i, defined indicator values f_i on known K, and unknown event U, a_t=sum_{K}p_i 1[f_i>t], u=sum_U p_i gives Pi(t) in [a_t,a_t+u]. The bound is mathematically sharp under *unrestricted completion of unknown events*. Physical coupling/energy constraints may narrow it, so this is not automatically a sharp physical interval. Exact ties are excluded by >. Multiple thresholds share the same unknown draw and obey monotone coupling, not independent intervals. Tested [-inf,.1] signed example and Pi in [.3,.8].

Acceptance next: source-bound R2/CF4/Planck joint physical sector/posterior or pre-justified partial-identification support; coverage test of true supplied selected likelihood; trace physical clock/frame, proper priors and source overlap. Legacy `filling_fraction(x_obs,x_max)` on arbitrary signed x is **not** a certified F. Return domain-uncertified rather than `inf` where x_max<=0.

## L03: hierarchical same-sky matched null (derived; tested toy)

Let S_s be one independent latent CMB sky (s=1,...,N_s), R_r a released noise/systematics realization, and p a processing method/split. A matched observation model is Y_{s,r,p}=M_p(T[S_s],F_r,R_r;mask_p,beam_p,compsep_p). Shared s across methods and reused r across s create correlations. Independent effective test units are NOT N_s*N_r*N_p. A synthetic 4096-sky, four-method toy with shared sky plus independent sigma_n=.3 noise returned offdiagonal correlation ≈.919, close to 1/(1+.3^2)=.91743. This is manufactured and not a Planck measurement.

A predeclared one-sided Monte Carlo rank has p=(1+# {T_s >= T_obs})/(N_s+1) **only when observation and matched sky-level null statistics are exchangeable after identical procedure, and each T_s represents a valid independent null unit**. If a trial scans masks/ell/axes, apply the same scan in every T_s. For source-realistic Planck PR3, fixed-weight component-separation signal and released E2E residual sets must be matched by method/split ID. 999 CMB and 300 noise/systematics simulations do not imply 299,700 independent skies. Temperature-only diagnostics do not certify spin-2 E/B and foreground adequacy.

Acceptance next: officially released PR3 effective beam transfer and masks, source-processed Q/U spin2 `alm2map_spin` or equivalent against the actual mask, high-l leakage, foreground model and registered null PTE/coverage. Do not use SMICA-noSZ I-only product as zero B.

## H02: selected CF4 likelihood and true calibration (derived; normalized toy)

For one observed y generated from density p(y|theta,eta) and a known source-selection region A, the fixed-observed-count density is

 p(y|theta,eta,S=1) = 1_A(y) p(y|theta,eta) / Z_A(theta,eta),   Z_A=integral_A p(y|theta,eta) dy.

A different **population count model** additionally requires intensity and Poisson-count normalization; do not mix these likelihoods without declaring the observed count scheme. For a Gaussian y~N(mu,sigma²) selected on l<y<u, divide by Phi((u-mu)/sigma)-Phi((l-mu)/sigma). In the y>0, mu=0,sigma=1 example, E[y|S=1]=sqrt(2/pi)=0.79788456, not zero. Omitting normalization can create a spurious parameter preference. The sandbox implementation uses log-CDF differences and tests numerical normalization even in high tails.

For source groups i, one defensible model treats method presence as metadata, group modulus as ONE aggregated measurement, calibrated covariance C=C_group+Z Lambda Z^T+C_vel, and a source/sky/radial selection law S(i|mu,m,z,n). As seen in previous P3/H03, free method zero-points can contain the global apparent monopole, so the physical H0 is not identifiable until proper absolute anchors/priors are inserted. CF4 VizieR group data alone do not identify the original parent TF/FP/SN selection. **Priority smallest valid subproblem:** W1 TF-specific published photometry, magnitude limit, linewidth and calibration; use Kourkchi et al CF4 TF parent catalog to construct a single-method forward selected likelihood. Then explicitly propagate grouped overlap and test held-out mocks and method covariance. Existing R2-02 `cf4_product_provider.py` and R2-05 normalized joint provider are useful if their source assumptions are supplied and verified.

Acceptance next: release/source exact ids, fitted angular + radial completeness, host method/calibration covariance and heldout mocks reflecting those laws, likelihood normalization and coverage. Do not mark H02 fulfilled because a toy selected Gaussian test passes.

## V03: genuinely distinct tilt time history (derived conditional rank)

A finite source-conditioned observed harmonic/dipole response is schematically
  d_i = R_{i,O} beta_{RO}(eta_0) + integral W_i(eta) beta_{RM}(eta)deta + nuisance_i.

For a two-channel toy with normalized W_i and beta_RM(eta)=beta_0+beta_1 q(eta), this reduces to d_i=beta_O+beta_0+beta_1<q>_i. The two-row design has rank 2 for distinct <q>_i but ALWAYS has null vector (1,-1,0); different source windows alone distinguish history *slope* but not constant matter tilt from a free local boost. The numerical check gives rank 2/3 for two toy visibility epochs. Distinct frame-history physics and a local-boost anchor (e.g., aberration/modulation) or independent time-varying response are needed. Spectral response from T/E/B, remote dipole/kSZ or redshift-dependent probes can help only with actual calibrated transfer and astrophysical nuisance.

Acceptance next: derived Einstein/momentum evolution and recombination/reionization visibility for each mode, verified line-of-sight transfer, independent injection after astrophysical nuisance projection; no duplicate endpoint boost labeled global tilt.

## B02: qualified polarized subset versus all-11 atlas (literature-supported+scoped implementation)

The 11 canonical Bianchi Lie types are I, II, III, IV, V, VI_0, VI_h, VII_0, VII_h, VIII, IX. VI_-1/9 is a distinguished VI_h branch, not an independent twelfth type. Bianchi class A has a_alpha=0 and includes VI_0,VII_0; class B includes IV,V,VI_h,VII_h and III (as VI_-1); all classifications require sign, curvature and exceptional-condition convention.

AniCLASS implements nearly FLRW I,V,VII_0,VII_h,IX with adapted Boltzmann hierarchy T/E/B, but this is *not* a complete native all-11, all-m, arbitrary-tilt, high-shear polarized solver. The uploaded historical BASS Rust `PHYSICAL_KINETIC_HOSTILE_REVIEW.md` preserves screen-projection finite arithmetic guards and selected repaired polarized kinetic components; another report explicitly separates Krylov residual estimate from a forward-error certificate. These are reusable numerical tests, not full physical atlas acceptance.

A **scientifically defensible subset result** should pin AniCLASS git revision, input chart/signature, expansion/shear parameters, recombination + Thomson polarization law, convergence in ell and energy/angular quadratures, normalized initial mode amplitudes, and physical Planck masks/noise. Run I and near-FLRW limits first, then V/VII0/VIIh/IX. To change B02's formal target to a restricted subset, explicitly update the paper scope and verify new scientific novelty beyond Saadeh et al (2016); never relabel the current all-11 target passed silently.

## K03: nonradial proper-motion plus frame-spin degeneracy (derived numerical linear algebra)

For a local 3x3 spatial velocity gradient G and sky unit n, the ideal radial response is y_r=n^T G n, rank 6 (trace + STF5); antisymmetric G is exactly absent. The transverse response is y_t=(I-nn^T)Gn, so joint radial+tangent (with known frame) has rank 9 for generic directions. BUT an unknown celestial-reference spin omega_frame gives y_t,obs=y_t + omega_frame x n. The antisymmetric G modes themselves produce omega_G x n and are exactly degenerate with the frame spin: the 12-column joint design remains rank 9 in the toy, even though radial+tangent rank 9 on G alone. This is a *specific structural counterexample*, not a global no-go.

Gaia DR3 quasar proper motion (`agn_cross_id`+`gaia_source`) is suitable to calibrate reference-frame rotation/secular aberration. It is not a measure of cosmic matter vorticity. Actual matter proper-motion signals require matched galaxies/distance/epoch/selection and instrumental/time covariance. Before combining CF4 radial and Gaia transverse measurements, include frame-spin, secular-aberration glide, reference-axis rotation and source class astrophysical proper motion nuisance.

## K04: optical/Jacobi conditional no-caustic bridge (direct derivation)

For u^a u_a=-c², h_ab=g_ab+u_a u_b/c² and physical acceleration a^b=u^c∇_c u^b, the 1+3 gradient is
  ∇_a u_b = -(u_a/c²)a_b + (Theta/3)h_ab + sigma_ab + omega_ab.
Let k^a=(E/c²)u^a+(E/c)e^a be future-directed outgoing photon with e^a spatial unit. Contracting k^ak^b gives
  (c²/E²)k^a k^b∇_a u_b = Theta/3 + sigma_ab e^a e^b + (a_a e^a)/c.
If n=-e is the sourceward direction, acceleration term is -(a.n)/c. This is a **local** directional Hubble coefficient. It is not the finite-window CF4 working H_W and does not imply the measured CF4 STF2 is geometric shear; the observer/matter normal must match.

For the optical screen Jacobi equation D''(s)=-R(s)D(s), D(0)=0,D'(0)=I on 0≤s≤L, suppose ||R(s)||_2≤K≥0 in a fixed screen transport frame. The Volterra equation is
  D(s)=s I - integral_0^s (s-t)R(t)D(t)dt.
Iterated comparison with scalar f''=Kf, f(0)=0,f'(0)=1 yields ||D(s)||≤sinh(s sqrt(K))/sqrt(K), and
  ||D(s)-sI|| ≤ sinh(s sqrt(K))/sqrt(K)-s = s delta_K(s),
  delta_K(s)=sinh(s sqrt(K))/(s sqrt(K))-1,
using K→0 continuous limits. If delta_K(L)<1, the smallest singular value of D(s) is ≥s(1-delta_K(s))>0 for 0<s≤L, so no screen caustic there and det D(s)>0 (orientation fixed by vertex). This is a **conditional** proof on the supplied curvature majorant. K units are affine-length^-2; it does not derive K from raw CF4 or verify the true null congruence. Independent tests include a constant-curvature sin(s sqrt(K))/sqrt(K) screen.

Acceptance next: source spacetime + null Jacobi transport, emitter/observer proper clocks and motion, redshift-affine map, curvature and Ricci/Weyl bounds, matching d_A/d_L and finite-z source sample. CAS07 proofs can bound supplied optical maps but cannot supply the map or validate the physical data by themselves.

## Legacy hostile salvage decisions

| Original exact user-supplied file | Finding and physics effect | Resolution/path |
|---|---|---|
| `code_data_package/.../bounds.py`, `x_defect` | Docstring asserts `x >= 0` for every physical configuration, but the explicit formula has negative vorticity and signed curvature; no universal positivity proof supplied | Preserve signed x; separate positive sector ceiling; reject silent clipping |
| same `bounds.py`, `_TYPE_INFO` | Registers `VI0` as class B and `VIIh` as class A; standard orthonormal Bianchi class assignment is the reverse. Conflates tilted vorticity with only VIIh | Reconstruct from Lie algebra C, n,a and branch parameter; fail misclassified classes |
| `bounds.py/filling_fraction` | Returns `inf` for nonpositive denominator and treats total signed ratio as physical filling | Introduce typed undefined/bound certification. F only sign-clean certified sector; signed Q distinct |
| `manuscript_source.zip/ch07_results.tex` | Declares eight likelihood channels independent without source-level joint covariance; takes CF4 bulk velocity as material tilt beta | Rebuild proper shared latent likelihood + overlap graph; claim source-conditional until independent physical responses |
| `manuscript_source.zip/ch03_bianchi_bounds.tex` | MES bound requires Copernican extension and relevant observer multipole derivatives; one CMB sky rms cannot silently satisfy them | Declare all derivative/frames/remainder assumptions and test external transfer; use bounds as conditional comparator |
| `manuscript_source.zip/ch05_teff.tex` | Exact F4 of a finite angular T_eff ansatz does not determine full spectral distribution or high-energy tail | Preserve F4 algebra; add spectral moments/energy-bin response and independent high-E validation |
| `HTT(...)/htt/catalog_likelihood.py` | Describes fixed-direction vs 3D beta likelihood and prior historical beta normalization repair; no survey-frame-calibrated physical global-tilt likelihood | Reuse code only after source ID, cosmological vs Doppler redshift and Jacobian/selection proven |
| `BASS_HOSTILE...` kinetic review | Some screen and Krylov components are source-scoped; residual estimates are not universal forward error certificates | Reuse strong negative/control fixtures for B02 transfer only, verify exact Rust tree/physics anew |

## Source verification and next bounded experiments

Source provenance and exact ZIP/member SHA-256 in `LEGACY_SOURCE_IDENTITIES.json`; actual sandbox tests and numerical receipt in `NUMERIC_GATE_DIAGNOSTICS.json`. Credible initial open-data path: (1) H02 W1 TF single-family selected likelihood with parent photometry/linewidth completeness and mocks; (2) Planck PR3 common T/Pol masked low-ell spin2 response + FFP10 paired bank; (3) AniCLASS near-FLRW five-mode physical convergence study; (4) Gaia quasar spin/secular-aberration calibration independent from matter proper motions. P1 S04 remains a physical posterior integration task, not an opportunity to fabricate a positive anisotropy result. **Seven physical source gates remain UNRESOLVED.**

### Original source references

- Tully et al, 2023, Cosmicflows-4: https://doi.org/10.3847/1538-4357/ac94d8
- Planck 2018 IV/VII: https://doi.org/10.1051/0004-6361/201833881 ; https://doi.org/10.1051/0004-6361/201935201
- Pontzen & Challinor, MNRAS 380 (2007): https://doi.org/10.1111/j.1365-2966.2007.12221.x
- Saadeh et al 2016: https://doi.org/10.1103/PhysRevLett.117.131302 ; https://doi.org/10.1093/mnras/stw1731
- Heinesen 2021 covariant luminosity-distance H law: https://doi.org/10.1088/1475-7516/2021/05/008
- Duangchan et al 2026 CF4 selected mocks: https://doi.org/10.1051/0004-6361/202556645
- Pantheon+ covariance release: https://github.com/PantheonPlusSH0ES/DataRelease
- AniCLASS documentation: https://github.com/CyrilPitrou/aniclass/wiki
