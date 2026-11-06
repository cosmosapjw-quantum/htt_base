# R39 data, observation-operator and Cobaya plan

## Data status

The R38 inventory JSON reports 42 local files totalling 10,471,574,322 bytes. R39 verified that metadata record on GitHub only. It did not access or rehash the physical files. Treat all local paths/SHA values as user-local receipts until local rehash.

Raw maps/catalogues/chains must not be committed to Git. Publish source release identity, retrieval recipe, row keys, SHA256 and compact diagnostics only.

## Probe sequence

### P0 Planck PR3/PR4 CMB

Require observed frequency/component maps, T/Q/U conventions, split maps, intensity/polarization masks, beam and pixel windows, bandpass/calibration metadata, and matched FFP/noise/foreground simulations. Observed maps provide the science data vector. Simulations calibrate estimator covariance, mask/beam response and null distribution. They do not replace the observed vector.

PR3 SMICA/Commander and PR4 Commander are processing views of the same sky. Choose one predeclared primary product and use others as correlated robustness checks unless cross-covariance is constructed. Build signed T/E harmonic carriers, BipoSH boost response and morphology functional bundle, preserving the actual transfer.

### P1 Quaia, NVSS and RACS counts

Require original source rows, random catalogues/completeness maps, flux/spectral/redshift columns, Galactic and declination masks, component grouping and cross-match IDs. Quaia/NVSS paths are reported in R38 inventory; RACS is not confirmed there and must be acquired from its official release if absent.

Fit the source-specific response over the full selection, not one universal Ellis-Baldwin coefficient. Model local clustering separately. Test count overdispersion and multi-component sources; compare Poisson with negative-binomial/hierarchical likelihood. Do not double-count shared catalogue objects.

### P2 Gaia DR3/CRF3 VSH

Require source-level proper motions, full astrometric covariance, exact source selection, cross-match IDs, redshift, magnitude/color and scanning-law templates. Fit E1 glide, B1 spin, E2 STF2-like modes and higher nuisance templates in one declared basis. A residual E2 coefficient is not metric shear without the cosmological response and scan systematic control.

### P3 Pantheon+ and CF4 distances

Pantheon+: exact 1701-row table and matching full covariance. Any selected subset uses C[np.ix_(idx,idx)] on both axes with stable ordered row keys. Track calibrators, heliocentric/CMB frames, peculiar-velocity correction, redshift window and calibration nuisance.

CF4: reconcile official Table 2 galaxy rows, Table 3 groups, Table 4 summary/velocity records and method-specific versus pooled distance modulus. Recheck 1PGC/PGC identity, group/galaxy hierarchy, calibrators, method pooling, redshift/velocity frame and source cuts. The R38 selected 35,970 groups are a project operator, not the complete public release.

Fit finite-z directional distance multipoles phenomenologically first. Do not identify them with local optical H or physical shear without a validated finite-z light-cone transfer.

### P4 DESI

Isotropic compressed BAO vector/covariance constrain background H(z), D_M(z), not sky-axis multipoles. Directional claims require full angular LSS catalogue, randoms, window, redshift selection and covariance.

## Common source-conditioned model

For each probe p,

\[
d_p={\cal O}_p(Z,\eta_p;W_p)+n_p.
\]

Construct the complete covariance, including known cross-probe blocks caused by shared sky, objects, calibration, large-scale structure and map processing. A missing covariance block means joint likelihood unavailable or conditional independence explicitly assumed, not zero cross-covariance.

Whiten only on the positive covariance support; project nuisance directions in the same metric. Derive J from the actual observation and estimator operator, not a hand-authored response matrix. Report raw/whitened singular values, scaling, null and weak directions, supported quotient condition number and mask/cut sensitivity.

## Model ladder

- M0: isotropic background + observer boost + probe selection/calibration/foreground/local-structure nuisance.
- M1: M0 + gauge-invariant residual radiation long-mode response.
- M2: M1 + redshift-evolving STF shear; matter-radiation tilt enters only if an independent likelihood mode survives nuisance projection.
- M3: family-specific Bianchi I dynamics and transfer. V, VII0, VIIh and IX need their own structure/curvature and polarized transfer.

Compare models with the same observations, masks, rows, likelihood normalization, nuisance basis and covariance. AIC/BIC are screening diagnostics only. Bayesian evidence requires normalized likelihood and proper priors or a validated evidence procedure.

## Tensorized HTT output

Construct a joint posterior or simultaneous identified region for the common typed state first. Then compute x[s,alpha] and set images K_alpha(D). Attach each functional's representation rank, parity, frame, units, epoch/window, domain and provenance. Compute Q/F/Pi/G_F from the same region/law according to the pinned theorem. Never treat x components or the five HTT outputs as independent likelihood terms.

Run an x_C-only vs vector/tensor-x ablation on exactly the same admitted data and injections. A tensor representation earns scientific value only if the gain in calibrated prediction, functional identification or coverage is demonstrated.

## Fail-closed Cobaya

Observed-data mode requires explicit data/covariance/selection/window paths, release IDs, SHA, row IDs, frame, units and operator identity. Missing/mismatched values raise before sampling. Synthetic fixtures use a separate configuration and cannot produce observed claim tiers.

Sampler receipt includes exact YAML, package versions, code/data hashes, full chains, Rhat/multiple-chain diagnostics, ESS/autocorrelation, posterior predictive and leave-one-probe-out results. Chain convergence does not validate the likelihood.

## Execution order

1. Local rehash and source/row/covariance reconciliation.
2. Repair and test frame/dimensional APIs and fail-closed adapters.
3. One-probe Planck, counts, Gaia, distance validation.
4. Cross-probe dependence model and actual observation-operator Jacobian.
5. Nuisance-projected identifiable quotient and tensor functional images.
6. Cobaya posterior and HTT outputs.
7. Family-specific Bianchi branch only after observed fit and native transfer.
8. Independent review and paper claim freeze.
