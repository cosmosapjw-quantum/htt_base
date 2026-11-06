# Data analysis plan / source contract

이 GitHub-only 작업에서는 raw FITS/catalogue를 다운로드하지 않았고, 새로운 local fit도 수행하지 않았다. 이 문서는 실제 데이터 분석의 source contract와 acceptance gate다.

## Shared observable SSOT

각 feature/row는 정확한 release/file/checksum/row order, sky ID/split/pipeline, coordinate frame/direction sign, observer/source/normal/radiation frame, redshift/distance definition, units, selection/randoms, mask/beam/transfer, covariance identity, nuisance set, finite-remainder identity, claim tier를 보존한다. Processing variants of one sky are not independent realizations. Shared source covariance is consumed once.

## Dataset workstreams

### Planck PR4 / NPIPE

Official release: https://portal.nersc.gov/cfs/cmb/planck2020/ and https://data.cmb-s4.org/planck_pr4.html. Reuse the pinned Commander MC100 aggregate/review as the current C0 anchor. First reconcile Commander vs old 30-GHz A/B pilot. Then audit map and simulation role, Q/U convention, mask, beam/pixel window, component-separation transfer and foreground uncertainty. Compare pipelines only if the same estimand and matched processed null exist. T/E/B are separate channels. No Bianchi inference without native validated T/E/B transfer.

### CMB observer boost

Reuse the PR180/FFP10 source identity only as a PR3 diagnostic. Estimate temperature dipole, Doppler modulation and aberration independently under common beam/mask/units; remove intensity-to-temperature conversion leakage and apply the same boost operator to observed and simulations. PR3 is not a PR4 result.

### DESI DR1 LSS / number-count dipole tomography

Official data docs: https://data.desi.lbl.gov/doc/releases/dr1/. DR1 docs list public LSS clustering catalogues, random catalogues and public mocks (1000 EZmocks, 25 AbacusSummit). Lock exact version v1.2/v1.5, tracer, NGC/SGC, data/random, observed-redshift bins, weights, completeness, fiber assignment, vetoes and imaging-depth systematics. Refit the complete dipole estimator separately in every mock and calculate full cross-bin/tracer covariance. Historical PR151 covariance was invalidated; public mocks alone do not certify this estimator. Include the von Hausegger–Dalang observed-redshift migration term and test bin-edge response.

### Radio / quasar counts

Candidate public tracers include NVSS, RACS-low, CatWISE and selected quasar samples. Measure \(x(S)\), \(\alpha(S)\), source fragmentation, local-source removal, mask, extinction, stellar contamination, flux calibration and redshift evolution. Wagenveld et al. (2025) already analyze joint radio/AGN dipoles; new value must be redshift/tracer response and same-covariance physical separation, not another catalogue dipole vector.

### Cosmicflows-4

Paper/data entry: https://arxiv.org/abs/2209.11238. Existing selected 35,970-group derived source NPZ is retained in prior H01/H03 work; previous SHA prefix/identity must be confirmed in the actual local file before use. Verify raw-source completeness, group membership, distance methods/offsets, group covariance, Vcmb, selection and row order. Measure finite-window flow and directional expansion separately; never identify bulk flow with homogeneous tilt.

### Pantheon+ / DES-SN5YR

Official releases: https://github.com/PantheonPlusSH0ES/DataRelease and https://github.com/des-science/DES-SN5YR. Preserve zHEL, zCMB, zHD, mb_corr, calibrator IDs, released row masks, full covariance and source order. Reproduce the released mean law exactly. Directional fits require SN survey/calibrator, host-mass, PV covariance, calibration and Malmquist controls. Current retained low-z SN and cosmic-chronometer windows do not justify a direct low-z CBL result.

### Gaia DR3 proper motions

Reuse separate E1/B1 24D carrier and E2/STF5 history response. Verify source IDs, PM covariance, epoch/time baseline, parallax/distance, redshift, quasar selection, reference-frame spin/glide and depth law. Do not merge feature vectors without an explicit common response/covariance mapping.

### ACT DR6

Use as higher-\u2113/lensing/foreground cross-check only; not a substitute for full-sky Planck low-\u2113 support. Require exact released map/beam/mask/covariance products.

## Preregistered analysis sequence

1. Freeze statistics, redshift bins, flux thresholds, tracer classes, masks and look-elsewhere scan before inspecting new residuals.
2. Lock source/observer/normal/radiation frame definitions and exact redshift corrections.
3. Define boost-only, local-structure, coherent material motion, shear/Bianchi and systematics-only forward models.
4. Bind data/random/mocks through the identical estimator and selection pipeline; full per-mock refit.
5. Build one joint covariance with cross-bin, cross-tracer, cross-survey and common calibration terms; never double-count map splits or catalogue variants.
6. Use held-out bins/tracers/groups for recovery and adequacy. Preserve out-of-family residual and abstention.
7. Release small results/configuration/masks/selection descriptors/source hashes/code revision, while raw catalogues remain outside Git.

## Execution boundary

이번 세션은 GitHub inspection과 theory/plan synthesis만 수행했다. Raw FITS/catalogues 다운로드, local data fits, PR4 map replay, mock generation, xAct/Lean, native Boltzmann evolution은 수행하지 않았다.
