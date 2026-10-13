# R2-02 implementation return

Candidate prepared for independent review; scientific admission remains **HOLD**. Requested executor `gpt-6.1-sol/medium`; observed runtime `UNKNOWN`. Frozen base `4dbe588698f15eb0a93df657d5bc7b5d0acd1e06`, branch `r2/02-cf4-provider-20261014`. No commit or publication performed. Upstream proofs accepted by owner; no proof audit rerun.

## Implemented capability

The HTT module `cf4_product_provider.py` reuses the grouped OBS02 loader, R7 `SelectedLatentBlock`/`build_cf4_law`, and reviewed R2-01 structured core. One `1PGC` contributes one `(DMzp,Vh)` pair with `e_DMzp`, J2000 sourceward direction and method-presence metadata. Table 3 supplies presence only; Table 4 derived Dist/Vpec fields are not read. `build_group_law_factory` binds one group to the existing R7 law and names the shared zero-point/velocity latent IDs. The catalogue law snapshots observation arrays and integrates a single proper shared zero point after summing row log densities.

Response branches are explicit: affine9 = bulk3 + isotropic/STF expansion6; weak12 adds expansion dipole3; endpoint13 adds free scalar intercept. Coefficients use km/s or km/s/Mpc. STF coefficients use the OBS02 Frobenius orthonormal basis. Endpoint crosswalk is `b0=c*(zeta0-1)`, `B=c*zeta_vector`; it is tested against the existing Cartesian endpoint design. Spatial basis is J2000 equatorial, sourceward; observer/redshift reference must agree. The actual loader remains heliocentric; no CMB-frame correction is inferred.

The provider uses angular-diameter distance `dA`; modulus prediction uses `dL=(1+z)^2*dA`. Catalogue `Vh/c` is a declared redshift proxy for the local sensitivity, not a separately measured true latent redshift. The provider refuses an unknown finite-distance remainder. A positive deterministic bound requires an explicit supplied remainder; it is not extra Gaussian noise. Exact-zero remainder appears only in the manufactured truncated model.

Global, method-presence and angular magnitude calibration templates have separate names. Method presence is an illustrative supplied nuisance basis; it is not fractional weighting of the published aggregate modulus or a calibrated per-method likelihood. Correlated residual errors are refused by the independent-slot law; they require an appropriate supplied joint block. Source-motion/velocity-field assumptions, source intensity, selection and covariance identities are explicit.

## Conditional latent law and checks

The supplied slot law integrates uniform log-area-distance and uniform bounded source motion. Independent Gaussian measurement errors are conditional on the shared calibration/velocity field. Selection is a declared observed-magnitude interval, with its parameter-dependent Gaussian-CDF normalization retained. The count scheme is fixed selected slots: the proper zero-point prior is conditional on this scheme. This is not a population Poisson/count likelihood or a model of the full CF4 survey.

The small selected block is an R7 block subtype: two-dimensional source integration, with Gaussian measurement-selection integration evaluated analytically. It agrees with tensor Gauss-Legendre and independent nested SciPy measurement normalization at the test tolerances. QUADPACK's absolute error estimate is checked; `epsrel=0` is explicit. Estimates/refinement differences are numerical diagnostics, not formal certificates. No-selection/narrow-source limits agree with a dense Gaussian law having one rank-one shared calibration covariance. Row permutation and selection-normalizer effects are tested. A factory-interface omission was found by the first factory test, corrected, and retained in `raw/tests_second.log`.

Final affected test suite: **63 passed** (`raw/tests_final2.log`), including CF4 product, existing information/likelihood and R2-01 structured-core tests. The prior 10-test run and 11-pass/1-fail factory run remain preserved.

## Actual CF4 and manufactured injection

`raw/diagnostic.json` reads **38,053 unique actual groups**. It records source SHA/schema, stable input bytes across execution, actual radius/method coverage, full/20–200 Mpc/narrow-radius views and seven method-presence exclusion views. Four declared velocity/source-motion/calibration scenarios retain fixed coefficient scales and report SVD/rank/null-space sensitivity. Exclusions reuse the published DMzp; they do not rederive a group distance or constitute independent repeated observations. The R2-01 core receives the existing OBS02 scenario-whitened response and reports its identity/rank; no observed physical response is fit.

The 24-slot selected manufactured draw uses two shells, Bx=120 km/s and Ax=1.2 km/s/Mpc, with H=70 and other coefficients fixed. The conditional fit gives Bx=15.909 +/- 93.063 km/s and Ax=2.3543 +/- 1.1094 km/s/Mpc, correlation -0.8641. The local joint Mahalanobis displacement from truth is 1.2727. This is **one-draw compatibility only**, with observed-Hessian conditional errors; empirical coverage and actual-product bias remain uncalibrated. Optimizer success, gradient, evaluation count, source/selection assumptions and seed are recorded.

At fixed B scale 100 km/s and A scale 1 km/s/Mpc, the two-shell radial singular values are (380.8755,94.5191); one 80 Mpc shell gives (362.2154,3.88e-14), exposing the Bx+r Ax degeneracy. Refining latent/calibration orders from (24,32) to (40,48) changes fitted-point log likelihood by 4.26e-14; this does not certify the entire parameter domain.

## Exact remaining inputs

Actual-product posterior admission needs an all-method source/selection law, joint calibrated modulus/redshift/grouping/flow covariance, method mixing/calibration metadata appropriate to the published aggregate DMzp, explicit velocity-frame/true-redshift conventions and a justified finite-distance remainder. Public grouped tables and an SDSS FP-subset mock release do not supply these full inputs. Their absence remains HOLD. No survey weights are used as selection probabilities and no missing physical covariance is replaced by a claimed measured zero.

## Sources and claim audit

Tully et al. 2023, DOI https://doi.org/10.3847/1538-4357/ac94d8; local CDS release `J/ApJ/944/94` ReadMe/table3/table4 provide the schema and actual product. DOI opening via web tool failed during this task; local ReadMe was inspected. EDD is the paper's referenced database at http://edd.ifa.hawaii.edu/. Author notebook source pin supplied by controller: `2f4c23c8810c35b494bf4d7c86b38e114109a022`; not independently fetched by this worker. https://zenodo.org/records/6824749 was read on 2026-10-14 and identifies an SDSS peculiar-velocity data/random/mock release, version 1.1.0. It is a subset source, not evidence of a full CF4 all-method selection law. OBS03 commit `5f3fbbee1d48d348bdf889fe2e27abdcb05073f4` was inspected with `git show`; its manufactured selected-latent/logsumexp conventions were reused, not treated as real CF4 calibration.

Claim owner HTT; status IMPLEMENTED/CONDITIONAL/DIAGNOSTIC_ONLY; transfer source none; no native solver, family identification, geometric-normal inference, global tilt evidence or actual calibrated posterior is claimed. Tests support the supplied numerical implementation; catalogue coverage/SVD support sensitivity statements only. Independent reviewer receives candidate hashes, raw failures, code and this bounded return.
