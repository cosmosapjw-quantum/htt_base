# Data, atlas and foreground blocker reconciliation — 2026-10-27

This bounded R2/R3/R5 pass reopens productive work on three explicit alternate estimands: PR4 processed-sky morphology, bounded polarized foreground contamination, and public standardized SN distances. It also defines an external Bianchi-product intake. It does not change the original 42-node acceptance or report a new survey-calibrated measurement. No cosmological solver, ODE integrator, map download, or author contact was executed.

The inputs reviewed were the supplied `htt_obs_bridge_run/RESEARCH_RUN_REPORT.md`, `review/DECISION_GATE.md`, `state/EVIDENCE_LEDGER.md` and their L03, B02, M-01/M-02/M-05, R31/R32 and SN claims. Source discovery used both Exa and SciSpace; admitted factual evidence below is from primary papers, official release pages, or author repositories. Exa's Pantheon repository fetch returned unrelated metadata; that result was discarded and replaced by direct GitHub file/commit inspection. This is a bounded source audit, not an assertion of exhaustive product absence.

## Decisions and immediate work

| Item | This pass | Productive action | Original acceptance |
|---|---|---|---|
| NPIPE common parent sky | Partially resolved: documented construction starts each Monte Carlo iteration from one CMB sky; per-file mapping still required | Qualify cached triplet genealogy, then a coherent frequency set and processed null | L03 PR3 HOLD preserved |
| `(A−B)×full <1%` genealogy gate | Rejected mathematically | Replace by input identity plus response-aware residual checks | No completion credit |
| PR4 morphology lane | Executable acquisition/analysis contract | Public-product inventory and cache reuse can proceed now | Separate estimand |
| AniLoS/AniCLASS scope | Public code and covered subset verified; accepted external atlas not acquired | Validate already-produced templates if supplied; continue convention algebra without solving | B02 HOLD preserved |
| Foreground radius | Constructive bound and calibration contract supplied | Compute finite radii only from declared spectral-support/amplitude or calibrated moment constraints | Numerical sky radius still open |
| Public Pantheon+ lane | Data locations, release pin and schema verified | Reuse/download 33,864,243 bytes, then fit release-level angular residuals | Nominal SALT2 binding still open |

These branches can run concurrently. A missing Bianchi atlas must not prevent public-SN fitting or foreground geometry; a PR4 result must not silently replace PR3 processing acceptance. The old procedural holds remain history, while a new attempt has its own contract and receipts.

## 1. PR4: parent sky, transfer and the minimum usable null

The [NPIPE primary paper](https://www.aanda.org/articles/aa/pdf/2020/11/aa38073-20.pdf), §§4.1.5, 4.3, 5 and Appendix I, describes 600 simulations, with one input CMB realization per iteration and FFP10 CMB inputs. Many instrumental effects and the foreground model are fixed across realizations. The 30/44 GHz A/B split is temporal, unlike higher-frequency detector splits, and its systematics need not be independent. Low-multipole polarization is processing-suppressed. These facts establish a useful conditional null and require a processing-matched analysis; they do not provide the missing filename-to-input-hash receipt. [S1]

The [official portal](https://portal.nersc.gov/project/cmb/planck2020/) exposes some products publicly and points to NERSC account access for the complete release. Its [frequency index](https://portal.nersc.gov/cfs/cmb/planck2020/frequency_maps/) was opened directly from the portal. No unverified simulation path pattern is admitted here. The portal's LoLLiPoP likelihood is a spectrum likelihood, not a supplied realization-level morphology law. [S2]

**Genealogy lemma (derived here).** Let observed/output vectors obey

\[
m_A=R_A s+n_A,\quad m_B=R_B s+n_B,\quad m_F=R_F s+n_F,
\]

where all three share the same random parent sky \(s\), and its errors have zero cross-covariance with the sky. Then

\[
\mathbb E[(m_A-m_B)m_F^\dagger]
=(R_A-R_B)C_sR_F^\dagger+N_{AF}-N_{BF}.
\]

Thus a nonzero difference-cross-full statistic need not indicate different parent skies. It can arise from unequal transfer, unequal noise, or a finite-sample fluctuation. For \(R_A=R_B=R_F=1\), \(m_F=(m_A+m_B)/2\), independent noise with variances 1 and 4 gives expectation \(-1.5\), despite an exactly common sky. A scalar cross-spectrum also fails to certify phase-level identity. The external review's universal 1% pass/10% kill thresholds are therefore invalid genealogy criteria.

`validate_data_atlas_lemmas.py` verifies this counterexample by exact eight-point product quadrature: the observed fixture mean is −1.5. This is an algebra fixture, not Planck evidence.

**Acquisition and acceptance contract.** The local host should:

1. Reuse existing PR4 receipts, maps and header records. Establish whether cached `030 mc_00200` denotes a simulation, a parent input, or a processed total. Treat that label as a prior-report claim until its actual receipt is read.
2. Build a manifest with release, frequency, split definition, realization ID, parent input CMB identifier, foreground-model identifier, total/noise/input component, beam and low-resolution filter, pixel ordering, coordinate frame, Stokes sign, units, provenance URL and local SHA256. A file-index equality alone is not sufficient parent evidence.
3. Qualify one coherent A/B/full triplet using header/schema checks plus parent-ID or pipeline provenance. An algebraic or statistical residual check is supplementary. A lone 30 GHz map does not supply a CMB-clean morphology null.
4. Freeze a frequency-selection and component-separation recipe. Acquire those frequencies and all required split/parent/processed products for the *same* realization IDs. Apply masks, smoothing, E/B extraction, fitted cleaning weights, nuisance fitting and any maximization identically to the observed realization and every simulation. Refit data-dependent weights within each simulation unless conditional fixed weights are the declared estimand.
5. Validate the low-\(\ell\) response on retained input/output coefficients, including anisotropic coupling. A scalar \(C_\ell\) correction alone is not a certificate for phase-sensitive tensor morphology.
6. Reserve training/calibration simulations separately when needed, or use a justified exchangeable construction. One parent sky is one null draw; A/B/full are not three independent draws. For \(B\) valid exchangeable null draws and a fixed statistic, use \((1+\#\{T_b\ge T_{obs}\})/(B+1)\). With 600 eligible draws its attainable minimum is \(1/601\), with 50 it is \(1/51\). No claim of 600 eligible downloaded draws is made here.

Finite foreground uncertainty can be added to this conditional null through a separately calibrated nuisance class (section 3). Fixed Commander foregrounds do not themselves sample that class. A combined confidence statement must account for calibration uncertainty and dependence; simply pooling different products does not do so.

## 2. Bianchi atlas: actual scope and an external-product contract

[Vicente, Pereira and Pitrou v2, 13 February 2026](https://arxiv.org/html/2506.07786v2) describes regular vector and tensor calculations for nearly isotropic models. The implemented family covers VII\(_h\), IX and V/VII\(_0\) limits; irregular modes and the general Bianchi family are not supplied by that implementation. IX has physical multipoles only \(\ell=|m|=2\). An array stop value of 3 must not be reported as octupole coverage. The physical result depends on initial conditions and thermal/background history. The paper explicitly permits additional late-time sources to change this restricted model class. [S3]

The [author AniLoS repository](https://github.com/jgvicente/AniLoS/tree/9b7a2611882dcca80a1491bcad2b8f05635faca7) was inspected at commit `9b7a2611882dcca80a1491bcad2b8f05635faca7`; `src/anilos/anilos.py` has Git blob `6347e3fc04ad1c06e19093dd28d5ecf8b18f2c31`. Its vector options include `iso` and `oct`; tensor and vector harmonic methods are present. `Omega_K=0` is replaced internally by a small nonzero value, so an exact flat-limit validation cannot be inferred from that invocation. The inspected repository has code and examples; a validated production all-m T/E/B atlas was not located in that inspected tree. [S4]

**Product identity.** “All-m” must mean a complete, documented harmonic representation, including symmetry zeros and reality-related coefficients. A canonical-frame mode with fixed helicity does not contain independently evolved values for every m. Once correctly normalized coefficients are supplied, orientation is a representation operation:

\[
a'^{X}_{\ell m}=\sum_{m'}D^{\ell}_{mm'}(R)a^{X}_{\ell m'},\qquad X\in\{T,E,B\}.
\]

This preserves the harmonic norm for each \(\ell,X\); it supplies an immediate static validation without a Boltzmann solve. Proper rotation does not reverse parity; a handedness/parity change must have its own convention.

**External intake fields.** Require code/paper pin; family; mode/helicity; regular/irregular flag; IC at the stated start time; curvature and spiral conventions; physical amplitude definition and conversion to \((\sigma/H)_0\); background and recombination/visibility-history receipt; observer frame; temperature normalization (dimensionless versus K\(_{CMB}\)); spin/Condon–Shortley/i\(^\ell\)/B-sign conventions; Euler convention; all retained \((\ell,m,T,E,B)\); reality and rotation checks; units/beam status; convergence comparison; independent reference/comparison; file hashes and license. Missing values remain explicit, not zero-filled.

**Pass conditions.** A product passes only for its declared family/mode/history and tolerance. Verify complete harmonic slots, conjugacy, zero-amplitude limit, linear-amplitude scaling, norm-preserving rotations and an independent convention-sensitive comparison. Shapes or EE/BB ratios alone cannot verify an overall sign, normalization or a parity-sensitive TB/EB convention. A same-code comparison at different settings is convergence evidence, not independent physical validation. No solver command is authorized or executed in this pass; the external review's proposed `tensor_solver()` is removed from the present workflow. B02 remains open until an actual qualified external product exists.

## 3. A finite foreground set with physical units

[Chluba, Hill and Abitbol](https://arxiv.org/abs/1701.00274) derive foreground moments from spectral-parameter averaging. [Vacher et al.](https://www.aanda.org/articles/aa/full_html/2023/01/aa43913-22/aa43913-22.html) extend this to the complex spin-2 field \(Q+iU\), where emission-angle mixing makes the moments complex and can rotate the net polarization with frequency. [Vacher et al. 2025](https://arxiv.org/abs/2411.11649) constructs data-compatible foreground-complexity examples. These are stronger stress-test families than a single d1/s1 sky; their agreement with selected power spectra is not a coverage theorem for every low-\(\ell\) phase statistic. [S5–S7]

**Bounded-moment proposition (derived here).** Let \(s(\theta)\in\mathbb C^k\) be the *bandpass-integrated* spectrum in declared map units. A finite complex measure \(\nu\) encodes emitting amplitudes and polarization phases, and

\[
y=\int s(\theta)\,d\nu(\theta),\qquad
M_i=\int\delta\theta_i\,d\nu,\quad
M_{ij}=\int\delta\theta_i\delta\theta_j\,d\nu.
\]

For \(s\in C^3\) on a convex parameter domain, support \(\|\delta\theta\|\le d\), and total variation \(\|\nu\|_{TV}\le A_{TV}\), the second-order expansion is

\[
y=s(\bar\theta)M_0+\sum_i s_iM_i+
\tfrac12\sum_{ij}s_{ij}M_{ij}+r_3.
\]

For a fixed linear map \(K\) encoding channel cleaning, harmonic projection, masking or whitening,

\[
\|Kr_3\|\le {A_{TV}d^3\over6}
\sup_{\theta}\|K D^3s(\theta)\|_{op}=\epsilon_3.
\]

**Proof.** Use the multivariate Taylor formula with integral remainder on each line segment, apply K, and integrate the norm against \(|\nu|\). The constant follows from \(\int_0^1(1-t)^2dt/2=1/6\). Dimensionful parameter coordinates require declared scaling in the norm; derivatives transform accordingly. For nonlinear data-dependent cleaning K, either condition on fixed K or validate a uniform bound over the allowed operators and reproduce fitting in the null law.

This theorem converts physical spectral support, amplitudes and channel response into a finite nuisance set. It does not infer those bounds from a reported sky-average \(\operatorname{Var}(\beta)\). In polarization \(|M_0|\) can vanish while higher moments do not; replacing \(A_{TV}\) by the net polarized amplitude is invalid. The included two-emitter fixture has \(|M_0|=0\), \(A_{TV}=2\), nonzero channel signal and remainder 0.00443955 below its rigorous 0.00503235 bound. These arbitrary-unit numbers demonstrate the algebra only.

**Connect to the existing tensorized analysis.** Let \(x\) be measured low-\(\ell\) coefficients, \(F_1\) the first-order nuisance span, \(Q\) its declared quotient/projection and \(D_2u\) the omitted-moment contribution after that projection. Given a calibrated ellipsoid \(u^THu\le\rho^2\), \(H\succ0\), and a remainder ball \(\|r\|\le\epsilon_3\), any linear functional v has sharp ellipsoid support

\[
\sup |v^T(D_2u+r)|
=\rho\sqrt{v^TD_2H^{-1}D_2^Tv}+\epsilon_3\|v\|.
\]

For complex moments, first stack real and imaginary parts. Positivity of an intensity covariance does not impose positive semidefiniteness on a complex polarized moment matrix. If H is singular and its null directions remain unbounded, report an unbounded support where appropriate rather than use a pseudoinverse to erase those directions.

This makes the old second-order rank collapse productive: unrestricted moments destroy point identification, but bounded physically calibrated moments yield explicit directional intervals. A positive finite interval is a result. The reported R32 threshold 0.379 μK is a comparison target inherited from the internal work, not a newly measured foreground radius. It is meaningful only after the same projection, metric, units and target direction are bound to the radius calculation.

**Calibration protocol.** Reuse exact RIMO passbands, nuisance columns, mask and low-\(\ell\) operator; declare the target coefficient norm. Fit real/imaginary moments jointly using multi-frequency Q/U information and channel covariance; retain cross-moments and bandwidth derivatives. Derive either support/TV bounds or a confidence set for u with a separately bounded truncation remainder. Propagate independent calibration uncertainty or include the calibration data in one joint law. Report a sensitivity curve when only conditional radii can be justified. For simultaneous confidence, a nuisance-set coverage error \(\alpha_F\) plus analysis error \(\alpha_A\) gives the conservative union-bound budget \(\alpha_F+\alpha_A\), without an independence assumption. \(\Pi\) belongs to that declared law; \(G_F\) carries actual joint sky/processing realizations, not merely matched labels.

## 4. Public Pantheon+: an observable lane that is ready

The [author release](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b/Pantheon%2B_Data/4_DISTANCES_AND_COVAR), pinned at `c447f0fea703fcd0fff57de5000947b5ca81286b`, supplies standardized magnitudes, redshifts, coordinates, flags and a full 1701-row total covariance. The [README](https://github.com/PantheonPlusSH0ES/DataRelease/blob/c447f0fea703fcd0fff57de5000947b5ca81286b/Pantheon%2B_Data/4_DISTANCES_AND_COVAR/README) states that zHD already has CMB/PV correction and that duplicated light-curve rows have correlated scatter. MU_SH0ES includes a Cepheid calibration; diagonal plotting uncertainties are not a fitting covariance. [S8]

| Product | Git blob SHA1 (not SHA256) | Bytes |
|---|---|---:|
| `Pantheon+SH0ES.dat` | `cce857db0c15e9ce7a0e0ce77452b6ff62af969a` | 579,283 |
| `Pantheon+SH0ES_STAT+SYS.cov` | `d1a1498154e7ba826df14bdbef35ebcb7f5efba1` | 33,284,960 |

The total is 33,864,243 bytes (32.30 MiB), before cache reuse. Both pinned raw URLs are recorded in JSON. The presence of public SALT2-related files does not prove the specific nominal PS1/training/FITRES binding. Replace “public products cannot provide it” with “that binding has not been located in the checked release.”

**Executable acceptance.** Verify local SHA256 and Git object identity; parse the named schema; require exactly 1701 original data rows, covariance header N=1701 and N²=2,893,401 numeric entries. Preserve row order and duplicates. Require finite retained entries; validate covariance symmetry, scale-aware positive semidefiniteness, retained rank and Cholesky/eigen treatment without an unrecorded jitter fix. Retain CID, IDSURVEY, RA, DEC, redshift conventions/errors, m_b_corr, calibrator/Hubble-flow flags and relevant nuisance columns. Slice covariance with exactly the same row indices as data. Data selection, thresholds and angular/depth bases must be saved before evaluating significance.

**Observable-level estimator (derived here).** Write standardized-magnitude residuals as \(y=X\gamma+B b+e\), with nuisance X (at least a global intercept) and angular/depth design B. For declared covariance C, positive definite on the retained data support,

\[
P=C^{-1}-C^{-1}X(X^TC^{-1}X)^+X^TC^{-1},\qquad
\hat b=(B^TPB)^+B^TPy.
\]

Only estimable combinations are admitted; report the rank, singular values and null directions. This delivers angular magnitude/distance residuals and, after an explicit first-order conversion, apparent Hubble anisotropy. It does not by itself measure physical acceleration or the unmodified Einstein–Boltzmann response. Profile the absolute-magnitude intercept for an anisotropy-only fit. Use total covariance once; do not add its existing PV/calibration contributions again. A zCMB/no-PV sensitivity lane needs a corresponding correction/covariance contract, not only a changed redshift column. A joint CF4/Pantheon result needs overlap/shared-PV handling and is not automatically independent.

Recommended outputs are b and its estimable covariance, dipole and STF-quadrupole maps by depth, standardized residual diagnostics, survey and calibrator deletions, zHD sensitivity with its stated law, and comparisons to the existing CF4 apparent tensors. Nominal SALT2 processing derivatives remain a separate task; this observable result need not wait for them.

## 5. Scope and reproducibility

The four small checks in `DATA_ATLAS_VALIDATION.json` pass. They establish the genealogy counterexample and the finite complex-moment remainder fixture. No map/observational fit, external atlas ingestion, or numerical foreground calibration is claimed. Original42 remains 17/42 in this audit; alternate work is counted separately. The local controller should schedule the PR4, foreground and SN branches independently, while external atlas validation waits for a qualified product rather than repeatedly executing a solver.

Sources: S1 Planck Collaboration 2020, A&A 643 A42, arXiv:2007.04997; S2 official NPIPE portal; S3 Vicente et al., arXiv:2506.07786v2; S4 author AniLoS code pin above; S5 Chluba et al., arXiv:1701.00274v2; S6 Vacher et al., A&A 2023, DOI 10.1051/0004-6361/202243913; S7 Vacher et al., A&A 697 A212 (2025), arXiv:2411.11649v2; S8 PantheonPlusSH0ES public-release commit and README above. The JSON contains the machine-readable source and action contracts.
