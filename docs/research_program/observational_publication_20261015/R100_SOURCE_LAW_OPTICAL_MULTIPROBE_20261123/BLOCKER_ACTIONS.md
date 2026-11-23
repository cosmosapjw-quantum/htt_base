# R100 Execution Preparation & Blocker Resolution Ledger

- Canonical R78 DAG SHA-256: `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11` (60 nodes, 129 edges, `next_id=SQ-CF4`)
- Frozen R99 Overlay SHA-256: `7bcf01630318b4701ac0a8973a0180de727c527aa2ba542e8660b2a5d84a235e`
- Original 42 Gates Payload SHA-256: `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d` (`new_science_nodes_promoted=0`)

| Blocker | Category | Lane Tag | Remaining Physical/External Block | R100 Delta Summary |
|---|---|---|---|---|
| `D01` | DATA | `BLOCKED_DATA` | Pre-intercalibration unshifted SNIa/TF/SBF/TRGB/Cepheid/maser tables, zero-point covariance, and authoritative CF4 pipeline sign provenance for SDSS vs 6dF. | R100 ingested bounded SDSS_PV_public.dat (34,059 rows, 20,231,640 B, MD5 verified) and 6dFGSv table1.txt (8,885 rows incl. 6,219 -1 sentinels, 696,070 B, MD5 verified), matched 34,045 SDSS PGCs + 8,885 6dFGSv IDs to CF4 table2/table3/table4, proved native SDSS ldc and 6dF delta_d agree positively (+0.7733 on 45 shared galaxies), yet discovered table2 DMfp assigns +4.978*ldc to SDSS vs -5.027*delta_d to 6dFGSv (Dec>0 dipole reversal sensitivity quantified). |
| `D02` | DATA | `BLOCKED_DATA` | Full-union CF4 pre-selection rejected parent denominators across TF, SNIa, and SBF. | Constructed 6-stage SDSS (34,059 -> 28,285/z-cut/table2) and 6dFGSv (8,885 -> 2,666 grouped -> matched) population ledgers, fitted empirical probit inclusion laws, and evaluated normalized joint_selected_logpdf on matched 6dFGSv. |
| `M01` | MODEL | `MODEL_CONDITIONAL` | Authoritative uncalibrated zero-point/selection physical generative law and independent physical holdout. | Computed full 3-band [1e-4, 1.0] h/Mpc correlated PV S_PV matrices matrix-free via per-panel FINUFFT across R={5,10,20} Mpc/h and all 4 observables (WF_log, background_proxy, native_comoving, bolometric), assembled 4-term C_36 trace budget (N_meas + N_nl150 + S_PV + J_cal Sigma_cal J_cal^T + C_sel), and octant CV. |
| `M02` | MODEL | `MODEL_CONDITIONAL` | Release-qualified physical Gaia/CF4 joint astrometric+PV likelihood calibration and source-frame closure. | Derived and verified exact finite-z position drift dn/dtau_o across FLRW, I, V, VII_h, VI_h (Bianchi I coordinate-ray oracle 4.41e-9, Milne Type V zero drift, SO(3) equivariance 1.50e-12, secular aberration 3.11e-15 uas/yr), separated observer vs emitter T_C(z) and T_G(z) kernels, and quantified VI_h finite-z E2/B2 helical proper motion (B2/E2=4.62% at z=2.461; 15.06% z=2 remainder). |
| `M03` | MODEL | `BLOCKED_DATA` | Physical body/anchor calibration for P1 finite-law likelihood. | Preserved exact correlated four-window P1 signed weights alongside full-k 4-term C_36. |
| `D03` | DATA | `BLOCKED_EXTERNAL` | PR4/NPIPE component-separated maps and independent FFP12-style paired noise ensemble remain external. | Verified exact SHA-256 preservation of R98 PR3 CMB_GROUPED_FULL_CACHE.json and CMB_OBSERVED_SPLITS.json without altering noise genealogy. |
| `M04` | MODEL | `BLOCKED_EXTERNAL` | Matched component-separation/foreground null ensemble for PR4/PR3 splits. | Preserved grouped noise cross-fitting guard (commander_null_qualified=false, physical_Pi=None). |
| `D04` | DATA | `BLOCKED_DATA` | Gaia release-calibrated AGIS spatial scan error law and independent AGN host/centroid controls. | Audited pmra/pmdec provenance (zero parallax substitution) and isolated separate 15/30/60 deg C_sys outside rank-47 C_jk. |
| `M05` | MODEL | `MODEL_CONDITIONAL` | Uncalibrated AGIS scan+AGN+physical Bianchi normal-frame covariance closure. | Executed rank-47 positive eigenspace whitening (avoiding 64D/160D inversion), separated constant 16D floor + beta_o + beta_e + VI_h finite-z across 4 Quaia shells, and quantified joint CF4+Gaia profiled Fisher SV gain. |
| `D05` | DATA | `BLOCKED_EXTERNAL` | Per-mosaic weight holes & local RMS/completeness maps reside in SURF tape HP-misc-*.tar (HTTP 202 deferred). | Audited all 1,580 LoTSS DR3 mosaics (4.04e11 px, 1.62 TB primary FITS metadata) and proved unmasked LoTSS_DR3_outer_b15 adds 112 zero-count cells elevating 50 mJy NB1 dipole from 0.0110 (legacy966) to 0.8469. |
| `M06` | MODEL | `MODEL_CONDITIONAL` | Physical shared-source Cox/LSS mocks calibrated against LoTSS completeness & PyBDSF RMS maps. | Fitted fixed-offset Poisson, NB1_Pearson, NB1_MLE, NB2_CoxLSS GLMs across all 5 radio surveys (19 cuts) with zero-cell retention and exact scale invariance, plus exact finite-boost Doppler/aberration/SED reselection. |
| `M07` | MODEL | `MODEL_CONDITIONAL` | Independent physical normal-frame velocity calibration across optical+radio+PV. | Constructed matched position-drift T_G(z) and luminosity-distance T_C(z) kernels separating beta_o vs beta_e, exposing single-survey FLRW near-collinearity vs joint CF4+Gaia profiled Fisher SV separation. |
| `D06` | DATA | `BLOCKED_DATA` | Independent external normal-frame photon/matter flux measurements. | Preserved exact normal-frame species stress-energy book-keeping; derived optical drift + Thomson momentum constraints. |
| `M08` | MODEL | `MODEL_CONDITIONAL` | All-family native linear Boltzmann perturbation transfer atlas (SQ-NATIVE) remains external. | Implemented Radau iterated k=0..4 coupled radiation-shear-baryon Thomson drag + pi_gamma(N) backreaction across FLRW, I, V, VII_h, VI_h preserving Hamiltonian/Codazzi < 1e-6, zero 4-momentum defect, and full contraction. |
| `M09` | MODEL | `BLOCKED_EXTERNAL` | Self-consistent anisotropic recombination chemistry solved simultaneously on curved Bianchi hypersurfaces. | Preserved coupled baryon-photon recombination/reionization opacity timeline without tuning physical thermal parameters. |
| `A01` | ADDITIONAL_ANALYSIS | `MODEL_CONDITIONAL` | Physical source-law validation once upstream unshifted tables/sign provenance resolve D01/D02. | Completed CF4 octant CV & 4-term C_36 decomposition across full [1e-4, 1.0] h/Mpc k-band. |
| `A02` | ADDITIONAL_ANALYSIS | `BLOCKED_EXTERNAL` | Matched PR4/FFP12 calibration. | Preserved P2 SHA guard & raw SMICA fold-0 tail provenance. |
| `A03` | ADDITIONAL_ANALYSIS | `BLOCKED_EXTERNAL` | Full external native all-m solver atlas. | Verified Radau vs DOP853 parity & k=0..4 convergence across 5 canonical Bianchi families + AniLoS near-FLRW. |
| `A04` | ADDITIONAL_ANALYSIS | `MODEL_CONDITIONAL` | Common physically calibrated mock lightcone covariance across CF4+Gaia+Radio+CMB. | Computed rank-47 Gaia+CF4 joint profiled Fisher SVD and 5-survey 48-patch radio GLS sensitivity. |
| `A05` | ADDITIONAL_ANALYSIS | `MODEL_CONDITIONAL` | Calibrated completeness-aware physical mock injection campaigns. | Quantified SDSS vs 6dF DMfp sign flip, empty-cell LoTSS exposure effect, and NB2 vs NB1 likelihood gain. |
| `A06` | ADDITIONAL_ANALYSIS | `MODEL_CONDITIONAL` | Upstream D01-D05, M01-M09 resolutions required prior to manuscript claim promotion. | Updated R100 manifest, claim firewalls (physical_Pi=None, physical_GF=None, calibrated_p=None), and zero gate promotions. |

## Selected Progress Nodes

| Node | Science Status | R100 Lane Tags | Updated Blockers |
|---|---|---|---|
| `S02` | `SCIENCE_BLOCKED` | `BLOCKED_DATA, MODEL_CONDITIONAL` | `D01, D02, M01, M02, M03` |
| `L03` | `SCIENCE_BLOCKED` | `BLOCKED_EXTERNAL` | `A02, D03, M04` |
| `H02` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA` | `A01, D01, D02, M01` |
| `V04` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA, BLOCKED_EXTERNAL` | `A01, A04, A05, D01, D02, D05, M01, M02, M06, M07` |
| `B02` | `SCIENCE_BLOCKED` | `BLOCKED_EXTERNAL, MODEL_CONDITIONAL` | `A03, M08, M09` |
| `K03` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA` | `A05, D04, M02, M05` |
| `SQ-CF4` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA` | `A01, D01, D02, M01` |
| `SQ-GAIA` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA` | `A05, D04, M05` |
| `SQ-RADIO` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_EXTERNAL` | `A05, D05, M06` |
| `SQ-FRAME` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL` | `M02, M07` |
| `SQ-P1-ANCHOR` | `SCIENCE_BLOCKED` | `BLOCKED_DATA` | `M03` |
| `SQ-CMB-NULL` | `SCIENCE_BLOCKED` | `BLOCKED_EXTERNAL` | `A02, D03, M04` |
| `SQ-PHOTON-FLUX` | `SCIENCE_BLOCKED` | `BLOCKED_DATA, MODEL_CONDITIONAL` | `D06, M08` |
| `SQ-LIE-FLUX` | `SCIENCE_BLOCKED` | `BLOCKED_DATA, MODEL_CONDITIONAL` | `D06, M08` |
| `SQ-OPTICAL` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL` | `M02, M07` |
| `SQ-CROSS-COV` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA, BLOCKED_EXTERNAL` | `A01, A04, A05, D01, D02, D04, D05, M01, M02, M05, M06, M07` |
| `SQ-NATIVE` | `SCIENCE_BLOCKED` | `BLOCKED_EXTERNAL` | `A03, M08, M09` |
| `PHY-01` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA` | `A01, A04, D01, D02, D06, M01, M02, M07, M08` |
| `PHY-02` | `SCIENCE_BLOCKED` | `BLOCKED_EXTERNAL, BLOCKED_DATA, MODEL_CONDITIONAL` | `A02, D03, D06, M04, M08` |
| `PHY-03` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_EXTERNAL, BLOCKED_DATA` | `A04, A05, D05, D06, M02, M06, M07, M08` |
| `PHY-04` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA, BLOCKED_EXTERNAL` | `A04, A05, D04, D05, M02, M05, M06, M07` |
| `PHY-05` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA` | `A04, D06, M02, M07, M08` |
| `PHY-06` | `SCIENCE_BLOCKED` | `BLOCKED_EXTERNAL, BLOCKED_DATA, MODEL_CONDITIONAL` | `A02, D03, D06, M02, M04, M07, M08, M09` |
| `PHY-07` | `SCIENCE_BLOCKED` | `MODEL_CONDITIONAL, BLOCKED_DATA, BLOCKED_EXTERNAL` | `A01, A04, A05, D01, D02, D05, M01, M02, M06, M07` |
