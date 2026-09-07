# Code/data reuse map and downstream execution contract

Date: 2026-09-07. This is the planning contract consumed after T1–T4 scientific closure. It is not an instruction to start observational analysis now.

## 1. Scope of repository discovery

Read-only GitHub discovery inspected the root and relevant subtrees, code search on the observed default branch, selected source files, PR451's exact changed-file list, the accepted report branch and the existing redshift programme. Large recursive responses were truncated. No all-files semantic audit, all-branches enumeration, native import check or whole-repository build was completed. The inventory below explicitly distinguishes actual source reading from path/symbol discovery and prior execution receipts.

Observed default code ref: `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb` (`research/pr04-multicomponent`).
Accepted explanatory source/ref: `9c86759f4ac7054d01d88689290a658e8ffd5863`.
Exact-source decoder donor: `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037`.

Do not start the implementation by merging the entire report/evidence branch into the code branch. At release, record the selected integration base and the relevant donor differences. Prefer the newest scientifically relevant actual source, not the most recently edited documentation or a default-branch name assumed to be authoritative for every component.

## 2. Reusable capability inventory

| Existing path / donor | Evidence read here | Reuse and upgrade decision |
|---|---|---|
| `htt/src/common/mes_krylov_completion.py`, exact decoder donor above; blob `f22132c7a3f247abd00f01cf1cce13dcad091070` | Actual source first 130 lines, scale/type checks, STF3 basis; PR451 filenames. Prior 28-test acceptance remains separately attributed | Reuse actual Q/O finite-dimensional algebra. DEFAULT_CONDITION_LIMIT=1e6 and DEFAULT_ATOL=1e-10 are existing defaults, not scientifically prescribed refusal rates. Forward statistics need not invoke inverse decoding. Preserve original tensors |
| `tests/common/test_mes_krylov_completion.py`, `test_mes_krylov_stable_decoder.py` | PR451 file list and previously accepted evidence, not newly executed | Run only affected integration tests after a real source composition/change; do not rerun merely to re-prove an unchanged accepted donor |
| `htt/obsstat/alm_conventions.py`, blob `c3537e47a86def9234e238065c30f4974abe4328` | Tree and exported symbols | Reuse coordinate metadata/isometry guards. Verify actual K_CMB/microK, raw-real/sqrt2, harmonic phase and sky-direction conventions on imported functions |
| `htt/obsstat/__init__.py` at default; blob `9a7e7d697f44d72074c01e3f9b9687922311685f` | Entire export/module-alias source | Existing poles, matched counterpairs, physical orbit catalogue, depth transport and data-admission interfaces are present. Explicit imports and `module.__file__` are necessary because nested package aliases can select different copies |
| `htt/obsstat/lowell_poles.py`, `lowell_counterpairs.py`, `shell_alms.py`, `morphology.py`, `null_ensembles.py` | Export/filename discovery, not full implementation validation | Use for pole types, rotational controls, correlated shell draws and null bookkeeping; add joint covariance/selection tests. Do not call a shared-kernel mock an independent sky |
| `htt/obsstat/orbit_catalogue_v3.py` and `htt/src/common/orbit_catalogue_v2.py` | Discovered physical shear/vector catalogue symbols and source excerpts | Do NOT substitute the physical-state orbit catalogue for temperature STF2/STF3. Reuse generic typed action/metadata only after input semantics match |
| `htt/obsstat/affine_flow.py`; blob `8c7d57c69b35f0260a56d2b2e904b0cf37492e68` | Actual source first 165 lines, decomposition, LS, bootstrap, injection | Reuse full-3D affine diagnostics, km/s and Mpc conventions. Add rank/finiteness checks and full-versus-half shear norm adapter. Cell bootstrap is uncalibrated, not a guaranteed lower uncertainty bound; curl injection validates a full-field estimator, not radial-data sensitivity |
| `htt/obsstat/constrained_realizations.py`; blob `5378aa4f8c6560decbd997c5eda898a4b19f4c2c` | Entire source | Retain toy mechanics but repair 'zero datum = no response' confusion in the new conditional-Gaussian primitive. Posterior variance SN/(S+N) versus S is an exact discriminator. Never promote a toy CR ensemble to measured CF4 vorticity |
| `htt/obsstat/cf4_forward_simulator.py`, `cf4_growth_covariance.py`, `cf4_velocity_estimators.py`, `cf4_identified_set.py`, `bulkflow_mle.py`, `catalogs/cf4_raw.py` | Tree inventory only | Candidate donors for likelihood-native observables, cross-covariance, calibration nuisances and raw-group selection. C0 reads these selected bodies and tests before selecting actual functions; not all are certified by their names |
| `htt/obsstat/catalogs/spectroscopic_dipole.py`, `catalogs/redshift_selection.py`, `desi_exact_selection_mock.py` | Exports and tree entries | Reuse data/random estimators and exact-selection mocks after matching actual catalogue columns, redshift frame and survey window. Compressed full-shape products are not angular catalogues |
| `htt/obsstat/depth_path.py`, `htt/src/common/depth_path.py`, `htt/htt/htt/infer/depth_path.py`, `depth_path_calibration.py`, `htt/mio/formalism/depth_path.py` | Paths/exports and search excerpts | Preserve OBSSTAT feature, common transport, HTT inference and MIO diagnostic ownership. A depth or mask ladder is not automatically a martingale or a set of independent experiments |
| `htt/htt/htt/infer/local_global_discrimination.py`; blob `995c516b01610753ccd688f7ad07397a6a3d769c` | Actual first 180 lines | Its default templates/manifest are `skeleton_only`, `pre_inference_only`; whitening uses diagonal noise. Reuse semantic labels, not a fully computed global response. New likelihood uses full cross covariance |
| `htt/htt/htt/departure/local_global_mixture.py`, nulls `local_boost_depth_null.py`, `selection_response_depth.py`, `clustering_dipole_depth.py` | Paths/imports/search | Candidate diagnostic and null-framework reuse; no posterior authority without declared response and calibrated generative model |
| `htt/obsstat/egs2_*`, `egs3_*`, `directional_cosmography.py` | Path inventory only | Older formula/model machinery, not blanket admission. Select only under the closed T4 physics. Do not revive scalar-only observational ranks or treat filenames containing Bianchi as native solver output |
| `external_fusion_round3/docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md`; blob `9da98a1159eeb34448d629070a7064b71f7b86dc` | Entire document | Reuse four pole types, shell/endpoint separation and H_LOCAL/H_LSS/H_GLOBAL_PHENO/H_GLOBAL_NATIVE distinctions. Its road map is not execution evidence |
| `external_fusion_round3/src/htt_ext/lowell`, `.../remote` | Referenced by existing programme, bodies not read | Optional reference implementation donors, not cosmological transfer validation |

These are source-grade statements. The local data manifest, module imports and current test evidence remain separate. In particular, the default `obsstat.__init__` contains more interfaces than the report branch's earlier export file; do not assume a single branch already combines every donor upgrade.

## 3. Owned data: use the existing inventory, not another 1.5TB scan

User-provided local inventory reports 179 bundles and 1.499TB of inode-deduplicated logical bytes. It is metadata/presence evidence, not a content or execution audit. Read `workdir/asset_inventory_20260907/assets.json`, `git_repositories.csv`, the existing manifests and relevant file headers. Hash only the selected final inputs/caches that a replay actually consumes. Do not recreate symlinks, relocate datasets or re-download archives merely to standardise paths.

Roots:
- W = `/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir`
- E = `/mnt/sn850x2t/htt_base_e2e`

| Data group | Actual supplied inventory | Programme role and admission rule |
|---|---|---|
| PR3 maps/masks/spectra | W/raw/planck_data: 11 paths; component controls: four | Primary CMB candidate. Bind each product's component-separation, beam, pixelisation, units, monopole/dipole and kinematic-quadrupole convention |
| FFP10 | W/raw/planck_ffp10: 1312 paths, 735.907GiB | Primary matched null candidate. Count unique simulation IDs and their matched signal/noise/processing, not file paths. Preserve five Commander partial FITS; exclude incomplete products without deleting them |
| PR4 | W/raw/planck_npipe_pr4 empty; W/rrss_observational_inputs/PR4 has nine paths | Separate product admission only. Never assume locally owned NPIPE 600 matched component simulations or infer download completeness from an empty directory |
| WMAP9 / WMAP7 simulations | Separate nine-year observations and seven-year simulation release | WMAP9 is a cross-instrument check on the same cosmic sky. WMAP7 simulations are not release-matched by name alone |
| Cosmoglobe / BeyondPlanck | 36 and 32 file paths | Product/control candidates; determine whether maps, chains or archives. A posterior draw is not an independent null-sky realisation |
| CF4 raw/full and compact products | W/raw/cf4, cf4_full, compact_products/cf4, obs_bundle/pecvel | Reuse raw distance-observable likelihood where present; reconstructed Cartesian velocities are model-conditioned features. Missing angular/distance metadata blocks that data lane |
| Carrick/CORAS/Lilow | W/raw/carrick_2mpp, coras_2mrs, lilow_nn_2mrs | Compare reconstruction and local-structure assumptions; do not multiply their likelihoods as independent data without overlapping-data covariance |
| DESI catalogs/randoms/mocks | W/raw/desi, desi_dr1_mocks, BGS fullshape v1.2 | Redshift-shell/angular analysis only from actual catalogs plus selection/random weights and matched mocks. Bandpower products constrain different statistics |
| ACT DR6 lensing and 400 lensing simulations | W/raw/act_dr6_lensing(_sims) | Lensing/LSS support. They are NOT high-resolution temperature observations or kSZ/aberration mocks |
| KiDS/HSC/COSMOS-Web/Union3/JWST | Actual products listed in inventory | Optional late-time/selection/depth comparisons. Lensing shear is not congruence shear; a pencil beam does not measure an all-sky pole. Not required by the first methods paper |
| CAMB/CLASS/GLASS and numerical libraries | Installation metadata with multiple environment versions | Reuse selected installed environment after actual import check. Presence does not prove execution. No blanket reinstall/upgrade |
| ELC and new remote-field products | Not established by supplied inventory | Optional future acquisition, outside automatic current-data analysis. Do not block the primary PR3 path waiting for them |

C0 resolves actual immutable dataset products, not just directory names. Required metadata can come from the file header, its supplied release metadata or the explicit source report. If not recoverable, return a typed missing-product/missing-matched-null result. Do not invent a noise model and call it FFP10.

## 4. Scientific interfaces to close in T2–T4

The future implementation should use these mathematical interfaces, with consistent real-valued coordinates and explicit units. Array conventions and supported rank must be part of the frozen spec; a schema string alone is insufficient.

### Observable tensor/uncertainty record

Input: real harmonic coefficient mean a of dimension p, joint covariance C_a (p by p), harmonic/frame/unit metadata, or draws generated under one explicitly identified posterior/sampling procedure. Output: Q (3 by 3), O (3 by 3 by 3), retained raw alms, polynomial invariants, optional normalised packet, and chart status. Carry the rotation frame when comparing to dipole/Galactic axes. If a tensor has zero norm, normalised statistics are unavailable but raw data remain. Never delete a reference row because its inverse chart is ill-conditioned.

### Nuisance comparison

Input: A (m by d), K (m by h), S (h by h), N_yy and optional C,L,N_yz,N_zz plus actual vectors. Output: weighted cancellation cost or infeasibility, Gaussian marginal/conditional mean and covariance, full Fisher including any parameter-dependent covariance, uncertainty region and metric. Four modes are explicitly named, not inferred from a missing S. With a full-rank finite matrix, diagonal-noise convenience helpers cannot stand in for a correlated covariance.

### Observer forward

Input: positive absolute sky or harmonics including T0, beta_RO, declared beam/pixel and processing operator, nuisance/source model. Output: processed sky, source and velocity derivatives as distinct arrays, and approximation residual relative to the exact/controlled reference. A first-order retained monopole null and a nonzero second-order kinematic quadrupole are both required controls.

### Depth observation

Input: typed raw distance/catalog data or reconstructed field, redshift/distance window, coordinate frame, cross-covariance model and selection randoms. Output: data-supported bulk/symmetric affine moments or angular multipoles, pole/gap/status and window response. ShellSourcePole, CumulativeObserverPole and remote poles are separate return types. Antisymmetric affine modes must remain unsupported by radial data absent extra information.

## 5. Planned code changes: small components, actual reuse first

Names below are proposed NEW module paths, not claims that these modules already exist. Their exact exported signatures and tests are frozen in SCIENCE_RELEASE after T1–T4. Do not ask Codex to choose scientific priors, statistics or depth bins at implementation time.

- `htt/obsstat/qo_response_diagnostics.py`: forward geometric f_B, beta-coordinate risk and their ideal-null reference; consumes actual Q/O helper/basis rather than reimplementing STF projection.
- `htt/htt/htt/infer/gaussian_nuisance_conditioning.py`: full joint Gaussian conditioning, supported-subspace solves and Fisher. The general H-observation primitive also supplies the corrected CR toy, with H=0 distinct from d=0.
- `htt/htt/htt/infer/bounded_nuisance_cost.py`: weighted minimum cancellation cost/feasibility, positivity sufficient bound; distinguish a baseline radius from two-state difference radius.
- `htt/obsstat/processed_response_comparison.py`: preserve the known fit/order, source derivatives and velocity derivatives, finite/continuum response identities and basis adapters; consumes existing processed-response code when its source is located/validated rather than inventing a parallel physical operator.
- Extend only the necessary `affine_flow.py` checks and norm adapters; use existing CF4/DESI builders for real data. New likelihood semantics belong to HTT, not OBSSTAT.
- One run driver per CMB/depth experiment consuming frozen configuration and input manifests. Avoid a new global registry, task framework or extra model server.

Before a same-name change, inspect the file's actual content and import identity on the release base. If an equivalent function already exists, reuse and test it; do not add the proposed filename only to satisfy the plan. Semantic equivalence and protected APIs matter more than manufacturing new files.

## 6. What each implementation unit must produce

### C0 — selective integration/data admission

Read the theory release and selected repository-local AGENTS/skills. Isolate a clean task worktree; record actual base, donor blobs and `module.__file__`. Compare relevant default/report/donor sources before copying anything. Read the existing local inventory and selected headers/manifests. Produce an admitted-input table with reasons for any exclusions, supported null IDs, units/beam/frame definitions, dataset paths and small benchmark memory/time. No all-disk import census, mass hashing, installer or download loop.

A missing actual data product disables its own analysis branch, not algebra/unit tests or another admitted branch. The first phase uses owned PR3/FFP10 candidates. Actual CMB significance remains disabled if a matched null law is not established. Alternative own-Gaussian results are explicitly model-conditional simulations, not replacement observations.

### C1 — coherent code integration

Write focused tests from the frozen equations before production changes. Record feature-missing failures separately from import/environment failures. Implement the new transforms/covariance primitives using existing source conventions. Include the exact numerical controls in `01_DERIVATIONS_AND_REVIEW.md`, especially H=0 versus d=0, shear norm adapters, deficient design rank and true source/beta Jacobians. Preserve old APIs/evidence; extend only the affected tests. A related implementation defect may be fixed repeatedly within scope without a new approval round trip.

### C2 — response and finite-operator checks

Re-use the accepted axial certificate as reference and add the minimal L=10 interpretation, not a duplicate broad CAS campaign. Compare direct angular/pixel and harmonic/Gaunt paths for the SAME declared target; include mask harmonic truncation/normalisation errors. Test full-sky zero high-band first-order leakage, mask perturbation scaling and bounded cancellation cost. Certify one finite target with derived entry/solve bounds where possible. If a proof-bound route does not close, report empirical convergence separately and do not relabel it certified. Data noise is not matrix-evaluation error.

### C3 — finite-dimensional/statistical validation

Analytic Beta/variance and covariance fixtures are mandatory. Test normalized chart-condition distributions only under the specified ensemble, not the referee's undeclared empirical oracle. Train/calibrate/test simulation families remain disjoint where the selected procedure requires independence. The frozen primary statistic must retain all valid input rows, use the fixed tie rule and apply data adaptation symmetrically or reproduce it inside each simulated analysis. Estimated noise covariance and null parameters are part of the generative procedure.

### C4 — full synthetic experiment

Inject complete skies and sources BEFORE the same observation/processing path used for actual data. Retain exact or controlled monopole/dipole boost terms and the chosen smoothing/mask/fitting order. Vary the registered null/alternative and nuisance families; compute parameter bias, joint tensor/region coverage, null size, power and abstention with finite-Monte-Carlo uncertainty. Include degenerate/near-cyclic, weak-amplitude, foreground-mismatch and H_UNKNOWN cases. A scientific low-power or nonidentification result is valid; do not tune thresholds until an artificial desired detection appears.

### C5A — CMB analysis; C5B — depth analysis

Execute the frozen choices on admitted data. CMB yields joint Q/O uncertainty, stable external-direction comparisons, four nuisance treatments and control-map/mask differences. Depth yields window-matched summaries/likelihoods for actual supported bulk/symmetric affine/dipole modes, not automatic global tilt or cosmic vorticity. Preserve shared-sky/shared-catalog covariance. Only the initial primary confirmatory analysis has the frozen inferential interpretation; later exploratory contrasts are labelled accordingly, not quietly promoted using the same sky.

### C6 — scientific return

Produce figures with generating tables, local plots viewed, uncertainty/status and source identities, plus concise interpretation. Required figures are nuisance radius/information/compatible-region comparison; mask size versus singular spectrum and cancellation cost; calibration size/coverage/power/abstention; map/window/depth stability. Required tables identify actual available inputs and any conditional/unresolved results. Do not turn absence of a signal into a software failure, or an implementation pass into a claim that a physical hypothesis is true.

Push one isolated result branch non-force and create Draft PR(s) at coherent deliverable boundaries. Return immutable links to source, outputs, raw command logs, patch/tests and a compact RETURN_TO_MAIN. No forced manual ZIP relay; no simultaneous MAIN/local source writers. No merge, ready transition, repository visibility change, external sending or canonical/scientific promotion is authorised by this planning package.

## 7. Explicit choices that MAIN must finish before release

These are the bounded contents of T3/T4, not discretion delegated to the implementation agent:

- One primary anomaly/calibration score, complete list of secondary controls, alternative families and how observational covariance is propagated through the nonlinear packet. Avoid pretending the overcomplete packet has a Gaussian chi-square law with nine degrees of freedom.
- Exact simulation split/seed schedule, matched-null admission semantics, sample-count stopping policy and multiple-comparison construction. Numeric tolerance follows an error target/conditioning domain rather than the referee's arbitrary common 1e-8 for all matrices.
- Exact depth-window kernels and treatment of low-z distance observables, redshift-frame conversion, shared reconstruction covariance and persistent phenomenological source basis.
- Exact source/pixel/harmonic target for each finite operator and quantitative solve/entry/truncation error allowance; rigorous versus empirical output labels.

The need to resolve these items is why `execution_release` is currently false. They are scientific research deliverables, not 'ask Codex to think harder' instructions. The overall programme structure, reuse strategy, exclusions and closure criteria in this plan are fixed. After MAIN closes them, the downstream phase becomes a single implementation/data delegation with normal autonomous debugging rather than new model design.
