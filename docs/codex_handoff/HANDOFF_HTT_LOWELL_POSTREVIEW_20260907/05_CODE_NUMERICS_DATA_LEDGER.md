# 05 — CODE / NUMERICS / DATA LEDGER

## A. Repository/runtime identity

- Repository: `https://github.com/cosmosapjw-quantum/htt_base`
- Visibility: **private**
- Default branch: `research/pr04-multicomponent`
- Fresh-read default HEAD: `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`
- Default HEAD tree: `42ef66d9746f4c9049fcfdf723ed10eb1301914e`
- Active research-plan branch: `research/htt-referee-seeded-program-20260907-r1` @ `0e2d6e3a890ae44303440e8534fb6080d1dac881`
- Current local checkout cleanliness in MAIN: `UNKNOWN / NOT INSPECTED`
- Uncommitted/untracked local state: `UNKNOWN`
- Latest MAIN native runtime: `ClientError` before observable process result. No new native code/CAS/Monte Carlo/data execution in PR462–464.
- New campaign execution versions: **NOT YET FROZEN**. Use one existing compatible workstation environment after THEORY_FREEZE and record only actually used dependencies.

## B. Code ledger

| Component | File/module/donor | Status | Known bug/debt | Test status | Exact next action |
|---|---|---|---|---|---|
| Q/O representation + conditioned inverse | `htt/src/common/mes_krylov_completion.py` @ `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037` | FACT reusable | chart-unavailable is typed; thresholds are implementation defaults, not science priors | exact-source 28/28 PASS | reuse, do not rewrite; run affected tests only after a changed consumer |
| Harmonic conventions | `htt/obsstat/alm_conventions.py` | source-discovered reusable | import/source identity and coordinate metric must be resolved on integration base | no new programme execution | M1 freezes exact coordinates/units; C0 resolves import |
| Exact local observer boost | donor `29427a1f7f2c5d46e43ffe03053c4ac13e969228` | FACT reusable scoped oracle | output/local lane only; not global tilt/electron tilt | previous accepted scoped evidence | M1 fixes exact product preprocessing/monopole/order |
| Processed response | donor `de73549c16ac6ceb63f924c86611e0a5ceb4711d` | PARTIAL/CONDITIONAL | finite-pixel error membership/subspace unresolved | source-equivalent/local evidence + continuum evidence | M1/M3 choose selected finite target and error policy |
| Local/global discrimination | `htt/htt/htt/infer/local_global_discrimination.py` | interface/skeleton only | binary capability vectors, support weights and diagonal pseudo-noise are not a physical response/covariance | no scientific validation | reuse labels/ownership only; replace inference content after freeze |
| Joint survey hierarchy | `htt/htt/htt/infer/joint_survey_hierarchy.py` | schema-only | status strings do not evaluate matrices or independence | none | reuse requirements, implement numerical content only under frozen model |
| Local/global mixture | `htt/htt/htt/departure/local_global_mixture.py` | diagnostic pre-solver skeleton | proxy templates are not global-tilt likelihood | none | do not call statistics-ready |
| Constrained realisations | `htt/obsstat/constrained_realizations.py` | toy mechanics reusable | `d=0` conditional variance `SN/(S+N)` must not be confused with absent response `H=0` variance `S` | source-level finding not executed | add exact H=0 vs d=0 regression in C1 |
| Affine flow | `htt/obsstat/affine_flow.py` | reusable diagnostic with debt | half/full shear norm adapter; design rank not guaranteed by `n_cells>=4`; cell bootstrap uncalibrated for correlated field | source read only | M2 freezes observable; C1 adds adapter/rank checks |
| CF4 typed adapter | `htt/obsstat/catalogs/cf4.py` | reusable I/O | transformed velocities/reconstructions are not independent Gaussian observations | source read | M2 defines native distance likelihood |
| CF4 old producers | `scripts/cf4_p0_quarantine_producer.py` + legacy paths | DEPRECATED/QUARANTINED | old headline results scientifically inadmissible | quarantine intentional | never revive; raw inputs may be reused under new model |
| DESI compact ingestion | `dl_pipeline/scripts/extract_desi_compact.py` | partially reusable | release-specific weight aliases/fallback need explicit semantics | source read | M2 fixes product/weight/frame |
| DESI legacy dipole | `scripts/desi_dipole_measure.py` | NEEDS REPAIR before scientific use | equatorial vectors compared to Galactic reference; `3<delta n>` response is `3 Cov_R(n)`, not identity; zero-axis handling | source derivation/tests specified, not run | M2/M3 freeze corrected estimator; C1 implements/tests |

### Proposed module names are NOT current files by evidence

Possible post-freeze modules named in plans:

- `htt/obsstat/qo_response_diagnostics.py`
- `htt/htt/htt/infer/gaussian_nuisance_conditioning.py`
- `htt/htt/htt/infer/bounded_nuisance_cost.py`
- `htt/obsstat/processed_response_comparison.py`

At C0, inspect actual current files/imports first. Reuse an equivalent implementation if present; do not manufacture filenames to satisfy the plan.

## C. Numerical ledger

| Experiment | Configuration | Result | Error/tolerance | Reproducibility | Interpretation |
|---|---|---|---|---|---|
| Q/O exact-source suite | CPython 3.12.3, NumPy 2.4.6, pytest 8.4.2; donor `9f7d06...` | 28/28 PASS | existing declared decoder thresholds | durable PR456 evidence | named decoder test contract, not universal inverse success |
| Historical Q/O stress | seed 20260903; 10,000 forward pairs | 10,000 accepted; 7 typed unavailable; 0 silent replay failures; max packet residual ~5.2119e-9; max Krylov cond ~4.77108e4 | source-equivalent grade | historical receipt | stress evidence only |
| Authority/T2 | CPython3.12.3 / pytest8.4.2 / PyYAML6.0.3 | 80 PASS | exact assertions + positive/negative mutation cases | PR455 | source/document contract |
| PR450 replay | repaired source + actual PR405 Git object | 90 PASS; two replay surfaces byte-identical; 37 rows=36 included+1 deferred | exact byte equality | PR458 | source-surface reproducibility, not theorem truth |
| R2 formal | SymPy1.14 + mpmath1.3 + Lean4.31 + mathlib `fabf563...` | both axes PASS for four obligations | exact symbolic/proof scope | PR453 | four supporting lemmas only |
| Continuum axial | registered wide-mask continuum operator | exact row rank 32; post-review minimal cutoff L=10 | inherited exact minors | durable artifact + deduction | continuum only |
| Non-axial continuum | six registered directions at L=12 | historical numerical full rank 32 and recorded smallest singular values | multi-engine numerical evidence | historical | not finite-pixel |
| Finite-HEALPix matched control | registered older task | RANK_UNRESOLVED | actual error-class/subspace admission incomplete | preserved evidence | no finite-pixel no-go |
| PR462 T1–T10 | direct derivations + selected scalar calculator | `DERIVED_NOT_NATIVE_TESTED` | n/a | durable Git text | scientific specification/oracles, not native receipt |

## D. Data ledger

Owner-reported roots:

- `W=/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir`
- `E=/mnt/sn850x2t/htt_base_e2e`
- inventory: `W/asset_inventory_20260907` -> `E/inventories/EXTERNAL_ASSETS_20260907T071735Z`

Inventory metadata: **179 bundles, 456,933 file paths, ~1.499 TB logical content**. This is presence metadata, not sample count, admission, or full checksum validation.

| Dataset/artifact | Version/source | Selection/preprocessing status | Provenance | Missing risk |
|---|---|---|---|---|
| Planck PR3 maps/component controls | existing `W/raw/planck_data`, controls | primary candidate: SMICA; exact units/beam/pixel/frame/dipole/KQ convention still to freeze | owner inventory | M1 blocker if exact product semantics unavailable |
| FFP10 | existing `W/raw/planck_ffp10`, reported 1312 paths/~735.9 GiB | product-matched signal/noise/processing and unique realization IDs required | owner inventory | file count is not N; five Commander partial FITS excluded not deleted |
| NPIPE/PR4 default path | `W/raw/planck_npipe_pr4` reported empty | NOT PRESENT as complete primary lane | owner inventory | must not be silently substituted |
| RRSS PR4 | separate nine files | upgrade/sensitivity only after product inspection | owner inventory | not proof of complete NPIPE/null ensemble |
| WMAP9 / WMAP7 sims | separate releases | cross-instrument/control candidate | inventory | release mismatch and same-sky dependence |
| BeyondPlanck/Cosmoglobe | map-making/foreground controls | posterior draws must not be treated as null universes | inventory | shared data/prior dependence |
| ACT DR6 lensing | lensing auxiliary | not primary CMB temperature/boost map | inventory | kappa != temperature |
| CF4 raw/full | distance/group candidate | original observable, grouping, calibration, selection and covariance needed | inventory + source map | reconstructed grids not independent distances |
| Carrick/CORAS/Lilow | reconstruction controls | sensitivity/model dependence only | inventory | shared inputs, not independent anchors |
| DESI catalogues/randoms/mocks | redshift/angular candidate | exact release/tracer/cap/weights/frame/matched mocks needed | inventory + source map | compressed spectra not sky catalogues |

No whole-storage rescan, relocation, mass hashing or automatic download is part of continuation.
