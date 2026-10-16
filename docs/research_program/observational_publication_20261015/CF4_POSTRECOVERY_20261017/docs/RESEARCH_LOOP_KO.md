# HTT six-paper: CF4 CDS fixed-width 수집 후 H02/S04 + L01/L03 연구

2026-10-17 KST; physicist-level report. Parent Draft PR #549 (`5a83a165449a06194517e44759cc417257fc2a53`), six-paper/42 DAG 14 completed_scoped, 28 pending. No submission. Native subagent not available: offline isolated scripts tested; an independent model review is NOT_RUN.

## Source trust and scope: do not confuse transport with physics

User's local receipts from `/mnt/extdrive/workdir/htt_open_data`:
- CDS `J/ApJ/944/94` Table2 55,877 rows SHA256 `8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f`.
- CDS Table3 38,053 rows SHA256 `c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d`.
- CDS Table4 38,053 rows SHA256 `b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94`.
- Original ReadMe SHA256 `2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4`.
- Six Planck PR3 masks, full native NSIDE2048 each 201,335,040 bytes, user-local SHA receipts preserved in `src/planck_mask_gate.py`.

**Verified by user's local execution**, not independently rehashed from all 55,877+38,053+38,053 bytes in the current ChatGPT sandbox. Production script `cf4_raw_audit.py` will refuse SHA mismatch and count mismatch when run locally. Historical GitHub source crosswalk previously already knew Table3/4 hashes. The public paper's narrative count 38,065 groups differs from the CDS archived *records* 38,053. Do not alter the locked expected row count.

## H02/source support: actual source joins vs physical survey selection

`src/cf4_raw_audit.py` reads the **official fixed-width ranges** (the exact source ReadMe) and binds `1PGC`, individual PGC, method-specific distance modulus/error pairs, group-level method counts, direct calibrators, common group scale DMzp and CMB-frame velocity. It validates three full raw byte hashes, row counts, group-table key set, zero-point differences, method co-occurrence and an angular method-profiled linear-design rank. Optional `--selected-npz data/selected_source_observables.npz` reconciles each of 35,970 prior-source 1PGC keys/DMzp/sky directions against the complete Table4 and reports any literal join discrepancies without inventing a match. It saves `/mnt/extdrive/workdir/htt_open_data/provenance/CF4_RAW_FULL_SOURCE_AUDIT.json`.

Table2 `DM` is already a cross-method MCMC combined output and Table3 `DMav` is a weighted cross-method output; Table3/4 `DMzp` are calibrated aggregate results, not new statistically independent measurements. The overlap graph is **a dependency warning**, not automatic multiplication of channel Gaussian likelihoods. A method label/marginal e_DM is not a calibrated selection function nor a common zero-point covariance.

**Previous actual-source outputs recovered during this session** from Dropbox `.../loop4/results/cf4_release_source_map_v2/result.json` and `.../cf4_galaxy_calibrator_join_v1/result.json`:
- Table3 37,825 group records with positive DMav/e_DMav have `DMzp-DMav=-0.147` mag at source 0.001 mag precision.
- 228 group records lack such a group-average and have direct DMcal.
- 336 directly calibrated groups; 108 also have method-averaged distance.
- 311/336 directly calibrated groups map to individual calibrators using the literal 1PGC group identity; **25 do not**. The 25 unresolved group IDs are a specific host/group mapping problem, not zero-valued anchors.
- Counted individual direct-family records: TRGB 446, Cepheid 69, SNIa 1004, Maser 6. These are individual channel records, not independent global anchors.

These figures are from prior source calculations, not recomputed in the current sandbox. Local executable reproduces and checks corresponding source fields and will output its own independently hashed receipt.

### Formal non-identification lemma

Let `q_i` be the observed normalized probability law on selected source objects, and let `p_i>0` be any normalized parent law on the same finite support. Choose a scalar `c=min_i(p_i/q_i)` and selection `s_i=c q_i/p_i`, where `0<s_i<=1`. Then

`p_i s_i / sum_j p_j s_j = q_i`.

Thus a normalized selected catalogue **alone** does not identify its parent population law or selection probabilities. This is a constructive counterexample, not a theorem that external known selection or parent coverage *cannot* resolve the problem. Source-independent parent counts, observing cuts, survey targeting history, and calibrated masks are the missing physical inputs. For W1 TF, use the raw candidate/accepted catalogue and inclination/line-width/SNR/magnitude cuts rather than the aggregate 1PGC group method tag.

An equally important covariance counterexample is `C_rho=diag[sigma_i²(1-rho)]+rho sigma sigma^T` for `0<=rho<1`. Every `C_rho` has the same released marginal errors, but different shared covariance. Neither the individual e_DM nor the group e_DM alone determine shared calibration/velocity covariance. This prevents H02 admission even though raw three-table transport is closed.

### Data-bound new result: 35,970 selected group source sample

Re-read the prior **actual source-derived** selected NPZ, exact SHA256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`, included in `data/selected_source_observables.npz`. The source has unique 1PGC IDs, J2000 sourceward unit vectors, method family, DMzp and e_DMzp. Recomputed, not borrowed from a report:

| Label | N_selected | norm of J2000 mean direction |
|---|---:|---:|
| FP | 26916 | 0.61670202 |
| TF | 7614 | 0.15149811 |
| SN | 700 | 0.16648215 |
| OTHER | 740 | 0.21026483 |

Global selected-source J2000 mean direction = `(-0.422026836333,-0.030873151033,+0.237209036316)` (norm ~0.48510610). Four mutually exclusive method-family dummy intercepts have rank 4; the phenomenological dipole + STF quadrupole 8 columns retain rank 8 after profiling method intercepts, combined rank 12. Neither these means nor the rank are a physical Hubble dipole or likelihood significance; the particularly nonuniform FP support explains a high risk of selection/calibration leakage into apparent anisotropy.

The **assumed** method-composition weight box `w_m in [1/Gamma,Gamma]`, with Gamma=2, produces exact per-Cartesian-component ratio extrema by checking 16 vertices:
- selected aggregate first moment `(-0.422027,-0.030873,0.237209)`;
- first-component box `[-0.511944,-0.255788]`, second `[-0.044347,-0.005963]`, third `[0.194834,0.260129]`;
- perfectly equally method-balanced (not selection corrected) direction mean `(-0.188316,+0.008737,+0.152640)`.

This is a **sensitivity scenario** with stated arbitrary Gamma=2, *not* a measured survey completeness or posterior bound. It cannot close H02 and should not be interpreted as physical amplitude.

## L01/L03: six actual PR3 mask byte identities, matched support and spin2 response

`src/planck_mask_gate.py` verifies the six local FITS masks by streamed SHA-256, file size and FITS header. With optional `healpy` it reads one NSIDE2048 map at a time, converts into canonical RING, averages to NSIDE64 and computes registered threshold 0.5 support for common/HM/OE Int and Pol, intersections, unions and polarity support mismatch. The masks are distinct release products, not independent skies. It outputs `PLANCK_MASK_SUPPORT_AUDIT.json`. **No actual six files were accessible in this sandbox**, so verification/read-map was *not executed* here; the user-local 6 SHA receipts are input binding only. `pip install healpy astropy` is required for `--analyse`, not for hash verification.

Spin-weighted E/B mixing has separate operators K_{+2} and K_{-2}; the E-to-B mixing amplitude is `|K_+ - K_-|/2` at one selected mode. For the nonnegative **synthetic** mask W=1+epsilon*cos(theta), at ell=m=2 spin +2 Y has angular power `(1-x)^4`, spin -2 Y has `(1+x)^4` with x=cos(theta). Their mask responses are `1-2epsilon/3` and `1+2epsilon/3`; the mixing amplitude is **`2|epsilon|/3`**, i.e. 0.133333 for epsilon=0.2. Independent Wolfram exact polynomial integration confirms signed moments -2/3 and +2/3. This is an analytic spin-2 leakage regression *not* a measured Planck leakage coefficient. L01 remains PENDING and L03 physical E2E null stays external-missing until native beam/transfer/full-sky simulations and actual T/Q/U/source-matched processing are run.

## Publication admission boundary and next run

- `H02`: original CF4 raw data SOURCE_QUALIFIED locally; group+individual statistical dependence traced, **parent selection and calibrated C_eff still absent**. `H02` scientific PASS not granted.
- `S04`: no full geometric/tilt/curvature posterior; signed functional still undefined for physical source.
- `L01`: six masks available, exact operator and actual polarization transfer pending.
- `L03`: no release-matched real null exchangeability.
- `V03`: no global matter-radiation tilt source history.
- `B02`: no verified full Einstein–Boltzmann/recombination atlas; public AniCLASS five-branch approximation remains candidate.
- `K03`: no calibrated nonradial observational source.
- `K04`: no physical finite-redshift Jacobi/kinematic source bridge and full selection.

Authoritative six papers remain NOT_READY_TO_SUBMIT; 14/42 completed_scoped, 28 pending, seven external_missing. New work is prerequisite/scoped research, not DAG node promotion. Native subagents NOT_RUN; full-repo CI NOT_RUN.

## External sources (as of 2026-10-17)

- Tully et al. 2023 official CDS fixed-width schema: https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/944/94?format=html&tex=true
- Stiskalek, Desmond and Lavaux MNRAS 546(2) 2026: https://doi.org/10.1093/mnras/staf2048
- Salzano et al. PDU 53 2026: https://doi.org/10.1016/j.dark.2026.102382 (conservative distance-modulus cuts and peculiar velocity correction)
- Duangchan et al A&A 708 A119 (2026): https://doi.org/10.1051/0004-6361/202556645
- Planck Legacy Archive PR3: https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps
