# Data acquisition, likelihood and sampler plan — HTT R38

## 1. Acquisition policy

First inventory the local data assets; do not download blindly. Compare exact bytes and SHA256 against prior receipts and the project catalog. An old source path is not proof that the file exists today. The project catalog SQLite (10.82 GB uncompressed, 57 compressed parts) is an asset index, not the raw Planck/CF4/SN observation payload.

Raw FITS, full catalogues, chains and large covariance files stay outside Git. Version only release metadata, per-file SHA256, byte size, URL/DOI, retrieval date, FITS headers, row order, units, frames, selection/mask identities and covariance hashes. If bytes differ from an old receipt, preserve the original and write a new immutable path.

## 2. Priority data matrix

| Priority | Probe and official source | Minimum products | Scientific role | Main caveat |
|---|---|---|---|---|
| P0 | Planck PR4/NPIPE: https://data.cmb-s4.org/planck_pr4.html and NASA LAMBDA https://lambda.gsfc.nasa.gov/product/planck/curr/planck_prod_irsa.html | Frequency maps, matched splits/nulls, beams, masks, pixel windows, low-resolution covariance/noise and bandpass metadata | Primary full-sky CMB T response and boost/morphology tests | Do not download the entire low-resolution 155.4 GiB bundle by default; choose only matched channels/splits |
| P0 | Planck PR3 component products: https://irsa.ipac.caltech.edu/data/Planck/release_3/docs/README.html | SMICA, Commander, NILC/SEVEM where appropriate; T/Q/U, masks, beams, noise and FFP simulations | Processing robustness on the same CMB sky | Processed maps are not independent primordial skies; temperature is not bolometric intensity |
| P0 | Quaia: https://irsa.ipac.caltech.edu/data/Quaia/overview.html; DOI 10.26131/IRSA640; Zenodo https://zenodo.org/records/10403370 | G<20.0 catalogue, selection-function HEALPix map, matching random catalogue, redshift/error and quality columns | Quasar number-count dipole in redshift/magnitude bins; overlap with Gaia astrometry | Full G<20.5 has 1,295,502 objects; cleaner G<20.0 has 755,850. The two cuts have different selection and random products |
| P0 | Cosmicflows-4, VizieR J/ApJ/944/94: https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJ/944/94 | Table 2 galaxy distances; grouped Tables 3/4; source/method identifiers; calibration/grouping metadata | Local velocity field, directional Hubble windows and method/sky response | Public release has 55,877 individual-galaxy rows and 38,053 group rows. Existing project 35,970-group operator is a selected subset |
| P0 | Pantheon+SH0ES: https://github.com/PantheonPlusSH0ES/DataRelease | Data vector, redshift-frame columns, full STAT+SYS covariance, calibration metadata and exact selected subblocks | Directional SN distance modulus and low-z Hubble contrasts | Main vector has 1,701 rows. Match row order and covariance by exact source identity. Existing 490/705-row products do not certify all 1,701 rows |
| P1 | NVSS and RACS-low; 2024 joint analysis https://academic.oup.com/mnras/article/531/4/4545/7688468 | Source positions, integrated fluxes, completeness/depth maps, tile masks, flux calibration, spectral-index model and selection/random maps | Independent source-count dipole and flux/redshift stability | NVSS declination coverage and RACS-low footprint differ; literature finds sample/mask/flux-cut sensitivity |
| P1 | Gaia DR3 archive: https://gea.esac.esa.int/archive/ | Quasar/AGN astrometry, proper motions, quality flags, frame systematics and redshift cross-match | VSH dipole/quadrupole and transverse kinematics | Frame spin/glide and selection can mimic low-order VSH terms |
| P1 | DESI DR2 official papers/data: https://data.desi.lbl.gov/doc/papers/dr2/ | BAO vector/covariance first; later LSS catalogues, randoms, angular masks and window functions if sky-direction fit is justified | Redshift-distance history, radial/transverse AP and optional angular anisotropy | Compressed BAO points alone do not preserve enough angular information for a sky-axis dipole/quadrupole |
| P2 | WMAP LAMBDA: https://lambda.gsfc.nasa.gov/product/wmap/ | Frequency T/Q/U maps, beams, masks, noise and simulations | Independent-instrument low-ell cross-check | Same primordial CMB realization as Planck; include shared cosmic variance |
| P2 | ACT DR6.02 LAMBDA: https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/index.html | 90/150/220 GHz maps, null maps, beams incl. T-to-pol leakage, passbands, masks and PSPIPE covariance | Higher-resolution T/E/B and foreground/beam check | About 19,000 deg², not full sky; support channel only for low-ell |
| P3 | DES-SN5YR: https://zenodo.org/records/12720778 and https://github.com/des-science/DES-SN5YR | Data vector, covariance, selection metadata and calibration | Independent SN-survey replication | Acquire after Pantheon+ pipeline/covariance gates pass |
| P3 | HSC S19A / KiDS-1000 DR4.1 | Shear catalogues, masks, redshift distributions, response and full cross-survey covariance | Optional lensing/spin-2 consistency check | Existing PR-310 is operator closure with observed lane blocked |

## 3. Size and sequencing

The PR4 portal lists 27 full-sky map files totalling 10.4 GiB, 90 half-ring maps totalling 77.3 GiB, 63 low-resolution files totalling 155.4 GiB, and effective beams totalling 312.7 MiB. Start from the matched maps/splits/beams/masks required by the registered low-ell likelihood. The full low-resolution archive is not a first-step requirement.

Quaia has a compact path: the published G<20.0 catalogue is about 100 MB, its 10x random about 151 MB, and its selection map about 0.4 MB. Verify release/DOI and checksum before reuse.

The first low-cost set is Quaia G<20.0 plus random/selection, exact CF4 release tables, Pantheon+ selected covariance and row map, and existing Planck map/mask products only if local hashes verify. Only then decide whether PR4 half-ring/low-resolution covariance, DESI LSS, ACT DR6 or DES-SN5YR is needed.

## 4. Local asset reconciliation

### CF4

Do not equate:
- VizieR Table 2: 55,877 galaxy distance rows.
- VizieR grouped Tables 3/4: 38,053 group rows.
- Prior project operator: 35,970 selected rows.

The local agent must identify exact join keys, row ordering, PGC/1PGC mapping, source-method inclusion, group averaging, duplicate handling, velocity frame and exclusions that produce 35,970. A directional sky centroid or method-mean direction is sample geometry, not physical Hubble anisotropy.

### Pantheon+

The official repository has distinct data, calibration, model, distance/covariance and simulation folders. The 1,701-row vector and STAT+SYS covariance require exact row identity. Project 490/705-row blocks are conditional source-qualified inputs. Do not silently expand the domain, symmetrize a failed full covariance, or replace full covariance with its diagonal. Upstream issues discuss Cholesky-whitened solves and a diagonal uncertainty/covariance comparison; these require explicit validation.

### Planck

Distinguish frequency maps, component-separated products, common/HM/OE masks, half-ring/half-mission splits, FFP simulations, beam/pixel windows, T/Q/U versus E/B, thermodynamic temperature versus intensity units, and processing provenance. Prior PR3 mask/FITS receipts may live only in the user's external asset root. Do not claim to have read them until local hash verification succeeds.

### Catalogues and randoms

For Quaia/NVSS/RACS and DESI, store catalogue and random-catalogue identities separately. Derive expected count maps from the supplied selection function, not observed counts. Keep Galactic extinction, stars, local bright sources, flux scale, tile depth, declination boundaries and redshift uncertainty explicit.

## 5. Data intake manifest

Each input row records dataset, release, table/product, official URL, DOI, retrieval time, relative path, byte size, SHA256, compression, FITS HDU/header digest, row count, row-order hash, stable object key, duplicate policy, coordinate/redshift frame, units, calibration, mask/selection/random/beam/pixel-window/passband identities, covariance path/hash/row identity, symmetry residual, minimum eigenvalue, Cholesky status, condition number, selection expression, quality cuts, flux limits, z bins, completeness model, upstream PR/receipt, code commit and claim ceiling.

A manifest is admitted only after a second independent read of downloaded bytes confirms size and SHA256. Preserve originals; write derived/subset products under new names with a row-index mapping.

## 6. Cobaya likelihood architecture

Use Cobaya as sampler/orchestrator, not as automatic full-sky data downloader or anisotropic Boltzmann solver. Its custom Theory and Likelihood interfaces can expose derived response quantities; acquisition remains a separate checksum-locked stage.

Proposed adapters, mapped onto existing repository conventions after local inspection:
1. KinematicResponseTheory: beta_MO, beta_RM, d_int, STF shear history, vorticity and acceleration response; declare provided quantities.
2. PlanckLowEllLikelihood: map/harmonic likelihood with mask, beam, frequency, T/Q/U, FFP/noise and foreground model; preserve signed phase information.
3. RadioCountLikelihood: NVSS/RACS flux bins and actual selection/random operator.
4. QuaiaLikelihood: quasar count multipoles with selection/random/redshift errors; separate Gaia proper-motion likelihood.
5. CF4Likelihood: source/group rows, calibration/method/selection and full covariance.
6. PantheonLikelihood: exact row-filtered distance vector and two-axis covariance subsetting.
7. DESIBAOLikelihood: official DR2 BAO vector/covariance; directional parameters only if angular product/window exists.
8. GaiaVSHLikelihood: VSH coefficients and covariance with frame-spin/glide nuisance.

No likelihood may substitute a processed map for frequency response or a scalar dipole for the tensor carrier. Do not count Planck SMICA, Commander and NPIPE as independent CMB skies. Model shared cosmic variance and independent instrument/foreground terms correctly.

### Sampler sequence

- Implement deterministic adapters and unit tests; verify a known Gaussian likelihood and exact covariance whitening.
- Fit each data family separately with common response conventions; run injection/recovery and selection-preserving null coverage.
- Run M0 first, then nested M1/M2 additions. Use MCMC for posterior exploration after rank stability. Use nested sampling/evidence only when priors are normalized, likelihoods proper and model supports match.
- Run joint posterior after single-probe and cross-covariance review. Freeze seeds, package versions, configs, chain hashes and resume files.
- Report posterior predictive checks, prior-to-posterior contraction, null modes, leave-one-probe-out stability, selection/mask/beam/foreground sensitivity and convergence diagnostics.

## 7. Joint observable vector and covariance

A target data vector may contain CMB a_lm(T,E,B), radio and Quaia counts by flux/redshift, SN distance modulus by z, CF4 radial/group velocities, Gaia VSH by redshift, and DESI radial/transverse distances. Every carrier retains source frame, units, selection, window and covariance. The covariance is block-structured; off-diagonal blocks are retained wherever common sky, calibration, host/source overlap, cross-survey overlap or shared nuisance generates correlations. Zero cross-covariance is an assumption to justify, not a default.

The five HTT variables (x,Q,F,Pi,G_F) are a structured inference product, not five terms added to the Cobaya log-likelihood.

## 8. Required code corrections before production

Inspect existing source and tests first. Make focused changes only:
- central covariance validation and whitening with Cholesky/triangular solves; fail closed on non-PD or misordered arrays;
- identical row selection in y and both covariance axes, with persisted source-key map;
- bind dataset/response to release+mask+beam+bandpass+selection+frame+code identities;
- separate Planck frequency maps, component maps, simulations and observations; no same-sky double count;
- keep E1/B1 polar/axial carrier distinct from E2/STF5 shear-history carrier;
- nuisance-projected SVD and null-space export; no prior-induced rank inflation;
- exact units/frame/velocity conventions and beta^2 terms where kinetic quadrupole matters;
- failure tests for covariance mutation, wrong row order, silent diagonalization, missing selection/random maps, unsupported response, frame mismatch and duplicate same-sky likelihood;
- synthetic fixtures validate software/coverage only, never substitute for observed data.

No code was changed or tested in the current GitHub-only research pass. Tests and implementation verification are mandatory local gates before any PASS label.

## 9. Additional downloads recommended after inventory

If absent, first acquire: (1) Quaia G<20.0 plus matching random/selection; (2) exact CF4 Table 2 and group Tables 3/4 to reconcile selected rows; (3) Pantheon+ full data/covariance and selected row map; (4) Planck PR4 frequency maps with matched splits/beams/masks/noise; (5) NVSS/RACS catalogues plus depth/selection maps; (6) Gaia DR3 quasar astrometry/redshift cross-match; (7) DESI DR2 BAO vector/covariance. Add WMAP, ACT DR6 and DES-SN5YR only for a specific robustness or redshift-range reason. Do not acquire every map/simulation archive merely because public.