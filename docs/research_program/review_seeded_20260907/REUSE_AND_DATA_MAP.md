# Existing code and data: reuse, replacement and admission map

Date: 2026-09-07. Owner: MAIN. Repository: cosmosapjw-quantum/htt_base.

This is a source-grounded architecture/data-product map, not a report that all files or all local data have been executed or validated. It completes the reuse decisions needed by the research plan. The separate final implementation specification will pin the minimal import/source closure after the three MAIN theory packs are closed.

## 1. What was inspected and what was not

The interrupted and resumed investigation read repository metadata and the default ref, requested branch and recursive-tree inventories, searched the default code index across local/global discrimination, CF4, DESI and CMB/MES components, and read the concrete code paths below. The large branch/tree responses were truncated; this is not an exhaustive byte audit of every branch or a full import-graph execution. GitHub code search covers the default branch, so no result there is not proof that a newer methodological branch lacks a feature.

The default ref observed is research/pr04-multicomponent at 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb. The newer accepted Q/O implementation is separately pinned at 9f7d06dec0fce1c3a8a53fa5372c84d9c679c037. The pedagogical/report publication 9c86759f4ac7054d01d88689290a658e8ffd5863 is the base of this planning branch, NOT a universal software execution baseline. Do not merge whole donor branches just because they share a repository.

The uploaded local inventory is metadata evidence supplied by the owner. It is not a fresh read of the workstation in MAIN. It reports 179 bundles, 456933 file paths and approximately 1.499 TB of logical content. Those quantities are not sample sizes or measures of scientific readiness. No re-hash of that volume is requested.

Let W=/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir and E=/mnt/sn850x2t/htt_base_e2e. The supplied index is W/asset_inventory_20260907, pointing to E/inventories/EXTERNAL_ASSETS_20260907T071735Z. Reuse its tables and inspect only the selected files' headers, release metadata and required columns before an authorised analysis. Preserve existing symlinks, data, environments and prior evidence.

## 2. Directly inspected code and disposition

### 2.1 STF representation and inverse: reuse the actual numerical kernel

Path: htt/src/common/mes_krylov_completion.py.
Source commit: 9f7d06dec0fce1c3a8a53fa5372c84d9c679c037.
Blob: f22132c7a3f247abd00f01cf1cce13dcad091070.

Inspected definitions include the full Frobenius STF validation, amplitude-safe normalisation, fixed seven-element STF3 basis and the start of the conditioned trilinear inverse. Its registered exact-source 28-test evidence was accepted earlier; it need not be repeated merely to plan this programme. Once integrated into a genuinely changed consumer, relevant regression tests must run for that consumer's actual bytes.

Reuse: Q/O carrier, moment packet, typed inverse-chart refusal, symmetry/orientation and image-replay controls. Preserve the original tensors even when the chart is unavailable. A many-component invariant packet is not a new source of information beyond Q/O. Add the projection-fraction distribution, covariance-aware inference and selection-aware null analysis in separate consumers, not by weakening this kernel's thresholds. OrbitChartUnavailable inherits OrbitInputError: classify the more specific condition first.

### 2.2 Local/global discrimination: metadata scaffold, not a physical response

Path: htt/htt/htt/infer/local_global_discrimination.py at default commit 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb.

The inspected source explicitly marks its manifest skeleton_only, pre_inference_only and not_posterior_odds. The response vectors are binary indicators for scalar_summary, direction, depth, template, BiPoSH, EE and BB availability; feature support contains weights such as 0.4, 0.6 and 0.9. The diagonal 'noise' used in that overlap is constructed from support values, not an observed or derived physical covariance.

Reuse: hypothesis names, ownership separation and metadata compatibility, after tests of the new interface. Replace for scientific inference: the feature-presence response and pseudo-noise overlap. Supply actual derivatives of the observation model and actual joint covariance from T1/T2. An overlap of schema capabilities cannot be presented as a Fisher degeneracy of local boost and global tilt. No support-score threshold automatically authorises a physical detection.

### 2.3 Joint survey hierarchy: retain requirements, implement their numerical content

Path: htt/htt/htt/infer/joint_survey_hierarchy.py.
Default-source blob: 20aabbe394a13a3deffba6c2d8b9d7aaf12796f1.

The complete file is explicitly schema-only. Required fields are cross_probe_covariance, mask_selection_metadata, survey_calibration_nuisance, shared_lss_covariance and heldout_predictive. Status strings trigger its conditional admission property.

Reuse: these requirements and ownership boundaries. Upgrade: numerical covariance blocks, grouped calibration variables, selection kernels and actual held-out predictions. A string 'bound' or 'passed' is not evidence that a matrix was evaluated or that samples are independent. The proposed analysis will consume actual arrays/operators with shape, units and source identities, not toggle these strings to make a model ready.

### 2.4 Local/global mixture: reusable containers, no completed global-tilt likelihood

Path: htt/htt/htt/departure/local_global_mixture.py.
Default-source blob: 4fa06149e75fd780357b673da8871aa4b121a2a1.

The inspected prefix explicitly calls this a gated, diagnostic pre-solver skeleton. It separates local_boost, global_tilt, survey_systematic and noise blocks and validates finite covariance/design objects.

Reuse: component separation and applicable generic linear-algebra helpers once their metric/units are verified. Replace: proxy templates with the sealed physical or expressly phenomenological response. Absolute eigenvalue tolerances from an old covariance helper cannot be transplanted to differently scaled variables without a declared numerical budget. Do not label a fitted phenomenological redshift dipole as a Bianchi solution. A native-family model remains an external future response dependency.

### 2.5 CF4 object data: useful adapter, quarantined old numerical producers

Path: htt/obsstat/catalogs/cf4.py.
Default-source blob: abdc855683708de7a83f71a27fc449a026f31bca.

The inspected adapter defines object_id, ra_deg, dec_deg, redshift, distance_variable, distance_uncertainty, group_id, is_grouped, method_flag and calibration_flag. It distinguishes logdistance, distance_modulus, metric_distance and peculiar_velocity. Its present products are diagnostic; transformed velocities do not automatically have independent Gaussian errors. Joint survey combination is explicitly conditional on further covariance/selection/calibration content.

Reuse: raw-object/group ingestion and field/type checks. New likelihood: the original distance observable, latent or grouped distance, redshift-frame convention, calibration offsets, selection and shared-structure covariance as derived in T2. Avoid treating the catalogue's estimated peculiar velocities or reconstructed grid cells as independent Gaussian observations merely because they are stored as arrays.

Path: scripts/cf4_p0_quarantine_producer.py.
Default-source blob: 6e5fddf0cf89660989f092c6bb54bf849544525a.

The active mv/mock/ml/gls entry points emit a quarantine block. Historical numerical code is accessible only through explicit legacy reproduction. The existence of scripts/cf4_mv_bulkflow.py therefore does NOT imply a current admitted bulk-flow producer. Keep those cards frozen. A new catalogue-level model must address their scientific failure classes, not delete the quarantine. Reconstruction-conditioned CF4++ and 2M++/CORAS/Lilow products can serve as labelled sensitivity templates, not independent extra data copies.

### 2.6 DESI ingestion and dipole: reuse input primitives, repair the estimator

Path: dl_pipeline/scripts/extract_desi_compact.py.
Default-source blob: 02120d7413f8a3b6d6a998f9c0209bdb780cb981.

The inspected code constructs n_hat from RA/Dec, so the vector is equatorial. The extended compact file retains redshift, weights, target ID, tile and photometric-system fields where available. Its first-matching weight aliases and missing-weight fallback are not a substitute for the release's exact selection definition. The final analysis specification must bind the intended weight product, frame, redshift convention and missing-column behaviour. A compressed product lacking target IDs or selection columns cannot be promoted by inventing them.

Path: scripts/desi_dipole_measure.py.
Default-source blob: 3ca7c465364322ece5afb6633367f811c691c4d2.

The actual path reads those equatorial vectors and random RA/Dec vectors but compares the result to a Galactic CMB (l,b) vector and labels the result Galactic. No frame rotation occurs in the inspected path. Separately, its Dhat=3<delta n>_R estimator has linear response 3 Cov_R(n) when alpha is fitted from the same selection; it is not a generally deconvolved dipole. For a uniformly weighted northern hemisphere the response is diag(1,1,1/4). The detailed derivation is Section 9 of THEORY_RESULTS_AND_CORRECTIONS.md. The zero-amplitude case also needs an explicit undefined direction rather than division by zero.

Reuse: FITS/compact reads, random-count accumulation and per-cap metadata where valid. Replace: implicit frame comparison, scalar factor-three inversion and the generic hard-coded kinematic reference. The proposed joint angular fit must include per-cap normalisation and nuisance multipoles; the physically predicted number-count dipole must include the sealed flux/redshift/selection response. These are source-level findings; no production patch or numerical test has been executed here.

### 2.7 Useful discoveries requiring scoped source completion, not a global rewrite

Default-index searches locate scripts/desi_exact_selection_card.py, scripts/desi_official_mock_card.py and obsstat.desi_exact_selection_mock.per_mock_refit; also htt/htt/htt/nulls/selection_response_depth.py, htt/htt/htt/nulls/local_boost_depth_null.py and htt/htt/htt/departure/response_overlap.py. They are reuse candidates, not newly validated likelihoods. T3 must read their exact called paths and test bindings before choosing a minimal dependency closure.

Previously source-bound methodological paths include the observable-irrep branch at d62c24887a4b91ab063085d5785b3cf18e0e36b5, processed local-boost work at ecf22552c22a35ce34ec58e9d98adab68c6823d7, and continuum verifier scripts at 033e0d19d61448492489ed1469bc687b2ecb4552 with the separate Octave comparison at bf6cc2dd75336ec5584b86dccd8de5cb352ab8f3. Their earlier evidence remains graded by its own source, domain and runtime. Resolve only the needed files and dependencies, not all old generated outputs.

The inspected htt/README.md is a historical embedded BASS-Python document, not a current global readiness certificate. Its dated pass counts and restricted flags are not proof that a full native Bianchi pipeline is now available. No BASS/REC/REI implementation is activated by this plan.

## 3. Data-product map from the owner's 2026-09-07 inventory

Numbers and paths in this section are inventory reports, not freshly measured by MAIN. A filesystem entry is only a candidate input. The admission decision depends on product definition and the chosen likelihood.

| Supplied product/location | Intended role | Required qualification / exclusion |
|---|---|---|
| W/raw/planck_data; W/raw/planck_pr3_component_controls | Primary PR3 temperature-map and component-method controls | Read actual release, component, units, beam/pixel window, coordinate and monopole/dipole/kinematic-quadrupole treatment. Component methods analyse the same sky, not independent observations. |
| W/raw/planck_ffp10, reported 1312 files and about 735.9 GiB | Primary end-to-end null/noise/systematic candidate pool | Match signal realisation ID, component method, noise, release and processing. File count is not independent N. Exclude the reported five Commander .fits.partial files and transfer sidecars. Sidecar presence is not evidence an active download exists. |
| W/raw/planck_npipe_pr4, reported empty | Not an admitted primary input | Do not claim 'PR4 already available here'. The NPIPE release describes 600 full simulations, but their existence elsewhere is not local possession. |
| W/rrss_observational_inputs/PR4, reported nine files | Candidate upgrade or sensitivity inputs | Inspect which products the files actually contain; a directory name is not a full noise/null ensemble. Upgrade selection must occur before target-statistic inspection, not after a favourable result. |
| W/raw/wmap_9yr and W/raw/wmap_7yr_e2e_sim | Independent instrument/systematics comparison where properly matched | Seven-year simulations are not a nine-year end-to-end null. Shared cosmological sky remains correlated with Planck. |
| BeyondPlanck v2 and Cosmoglobe DR1 entries | Map-making/foreground modelling sensitivity | Preserve their data and prior overlap; no independent-sky multiplication. |
| W/raw/act_dr6_lensing and W/raw/act_dr6_lensing_sims | Optional projected-matter/lensing auxiliary | Kappa multipoles are not high-ell temperature maps or a ready observer-boost measurement. No substitution of lensing sims for temperature sims. |
| W/raw/cf4_full versus W/raw/cf4 compact grid | CF4 original objects/groups for T2; grid for labelled diagnostics | Original distance variable and covariance/group calibration are essential. A reconstructed velocity grid is not a set of independent distances. |
| DESI catalogue/random/mock entries; reported raw eight files and mock collection | Redshift-dependent number-count multipoles | Read exact tracer, release, cap, completeness, redshift and random/mock identities. Match rows and selection. Compressed full-shape/BAO products are not sky catalogues. |
| DESI dr1 full-shape BGS-bright v1.2 compressed products | Background cosmology constraints only if explicitly modelled | No reconstruction of dipole directions from compressed spectra or distance summaries lacking positions. |
| Union3 release and JWST distance entries | Optional distance/calibration comparison | Require individual coordinates, original likelihood and calibrator overlap. Binned distance summaries cannot be used for angular anisotropy. Shared calibrators are not independent probes. |
| HSC, KiDS, COSMOS/Web entries | Optional projected lensing/systematics information | Lensing shear is not the spacetime congruence shear in MES. Small footprints do not supply an all-sky dipole by themselves. |
| QUIJOTE MFI and CLASS-observatory products | Optional frequency/polarisation systematics constraints | The CLASS observatory is not the CLASS Boltzmann software. Product type and frequency response must be explicit. |
| Existing obs_bundle and compact/derived cards | Locators, provenance and potential safe I/O reuse | Retired scalar-MES observational ranks and quarantined significance cards are not current scientific results. Raw columns may be reusable even when an old interpretation is not. |

### Primary-product decision

The initial analysis design will use the existing PR3 SMICA path with its genuinely matched verified FFP10/component/noise counterparts as the primary CMB lane, because the supplied inventory supports that candidate route. This is a priority and eligibility rule, not a claim all pairs have been admitted. If matching fails, that lane is NOT_RUN with a precise missing product; no automatic noiseless substitute or preferred-map switch is allowed. Commander and other component maps are planned robustness comparisons when complete. PR4/NPIPE is an upgrade candidate only after the corresponding metadata and simulation support are known before unblinding.

The catalogue lane uses original CF4 distance/group information and DESI object/random/mock catalogues. It does not reuse old scalar anomaly values or quarantined bulk-flow amplitudes as data. Every analysis remains conditional on its real covariance/selection definition. A missing auxiliary product should disable that optional comparison, not trigger a search of all storage or stall a valid independent primary lane indefinitely.

### Software already present

The supplied inventory lists existing NumPy/SciPy/SymPy, healpy, ducc0, Astropy/FITS tools, CAMB/CLASS, covariance/optimisation and sampling libraries across several environments. This is not one coherent version lock and not evidence that every import works in the same interpreter. Use one existing compatible tested environment and record only the dependencies used. Do not install or audit every package. NumPy-first CPU reference implementations precede optional acceleration; a GPU backend is admitted only with the same quantities, tolerances and reproducibility criteria. Native Bianchi transfer is not a replacement for an isotropic CMB fiducial merely because a package has a solver-like name.

## 4. Source-level coding loop completed during planning

Observed source -> mathematical response -> minimal replacement design -> falsifying test has been completed for the DESI path. The tests are specified, not executed:

- Full sky with uniform randoms: per-cap-normalised dipole response reduces to identity.
- Northern hemisphere: the legacy moment responds with diag(1,1,1/4); a correctly solved joint design recovers the known injected vector when identifiable.
- Equatorial input and reference: an explicit Astropy/rotation-matrix adapter must agree with independently rotating both sides; no comparison of equatorial vectors with Galactic components.
- Disjoint caps: each fitted mean is a nuisance column; results use the actual block design, not one accidental shared normalisation.
- Zero injected vector: amplitude is zero and axis is undefined, not a reported physical direction with NaN components.
- Add a masked quadrupole: a dipole-only estimator must show its predictable leakage; the joint model or declared marginalisation must account for it rather than label all residual dipole kinematic.

Further code closure includes numeric joint covariance in place of metadata status, matched-null complete-map calibration, original-data CF4 distance inference and the retained typed Q/O chart refusal. These changes have a named scientific consumer. They are not a reason to rewrite all repository harnesses.

## 5. Interfaces to seal in T3 before execution release

These are mathematical input/output contracts, not claims that the following adapters already exist:

- SkyProduct: map/alm values, angular basis and real-coordinate metric, physical units, frequency/temperature conversion, release/processing and beam/pixel/mask, simulation-family and realisation ID.
- ObservableTensorRecord: Q[3,3], O[3,3,3] with temperature units; amplitude/shape distinction; propagated joint coefficient covariance or posterior samples; typed chart status. No silent STF projection of invalid data.
- ResponseBlocks: interest Jacobian A[m,p], nuisance map K[m,h], optional auxiliary H[k,h] and A_z[k,p]; full block covariance [m+k,m+k]; source/output metrics; parameter-dependent derivatives where needed. Source-coordinate Jacobians are not relabelled parameter Jacobians.
- CatalogueProduct: unique object/group/calibration IDs, sky frame, observed redshift frame, original distance variable and error model, release weights/selection/random IDs. Shared groups remain latent shared variables.
- ModelResult: declared parameter meaning, identified/compatible set or posterior under an explicit law, uncertainty and fit/refusal status, null/selection scope, and raw-to-result provenance. No generic 'bound' label substitutes for actual likelihood calculations.

Owner routing remains common for algebra/conventions, obsstat for measured features and response construction, HTT for likelihoods/posteriors, and MIO for model-family-independent diagnostics. T3 must bind these contracts to exact existing import roots and proposed file additions, with tests, before setting the execution release true. The current planning documents deliberately do not invent an unverified merge or a universal source lock.