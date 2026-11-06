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

### P2 Gaia DR3/CRF3 VSH and local optical angular drift

Require source-level proper motions, full astrometric covariance, exact source selection, cross-match IDs, redshift, magnitude/color and scanning-law templates. Fit E1 glide, B1 spin, E2 shear-like modes and higher nuisance templates in one declared basis.

Reuse the existing LOOP C local optical inverse. In the sourceward convention,
\[
d(n)=H+\sigma_{ij}n^in^j-A_i n^i/c,\quad
\mu_{\rm FW}=P(n)\sigma n+n\times\omega,\quad
\mu_{\rm cat}=k[P(n)\sigma n+n\times(\omega+\Omega)].
\]
The physical acceleration term does not enter the leading transverse drift. The B1 catalogue mode is the sum of physical vorticity and catalogue triad rotation; constrain \(\Omega\) from independent frame/gyro/calibrator data or leave that combination unidentified. Source proper motion, source slip, centroid structure, observer translation and the clock-scale factor must be modeled, not interpreted as kinematic \(\omega\).

The ideal full-sphere inverse is a benchmark only. For real Gaia rows, compute the source-level Jacobian in the actual tangent bases, pass it through scanning-law/selection and frame operators, use the complete astrometric and cross-source covariance, and project E1/B1/E2 systematics in the same metric. The R39 kernel's local_optical_jacobian is unwhitened and pre-selection; it is not the empirical Gaia response.


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

## Existing likelihood/provider audit and reuse decision

The following modules were read on the current R39 branch. They are not equivalent to the target source-conditioned joint kinematical likelihood.

| Existing module | Current implementation boundary | R39 reuse decision |
|---|---|---|
| common.bulkflow_likelihood.BulkFlowLikelihood | Normalized Gaussian radial bulk-flow likelihood for a 3-vector V, with active-row selection and optional SamplingCovariance. It models u_i=n_hat_i dot V plus noise, not sigma, omega, A, beta_RM and beta_MO jointly. | Reuse source-row, selection and covariance mechanics where semantically applicable to a specific radial channel; extend the mean/operator and nuisance model rather than relabel V as the full kinematic state. |
| bass.likelihood.observer_frame_adapter.ObserverFrameLikelihood | Wraps an FB-7 cosmological-frame likelihood and applies observer boost remapping. Supports a finite boost support and discrete marginalization/profile over support points. | Reuse the observer-frame remapping path only after matching its boost convention and full-sky/processed operator domain. The current support-point average is not an exact continuous prior marginal unless quadrature weights/convergence justify it. |
| bass.inference.planck_likelihood.PlanckLikelihood | Explicitly separates synthetic fixtures from real data and blocks real fitting until its gate ladder is met. Its C_l-only route is not a full tensor/harmonic covariance likelihood. | Reuse the fail-closed dataset tier and gate semantics. A real R39 CMB lane needs the source-bound T/E/B harmonic or map likelihood and full processed covariance. |
| htt.htt.rest_frame.cf4_likelihood.evaluate_cf4_forward_likelihood | Self-declared diagnostic-only; independent diagonal distance-variable Gaussian score; group/method/calibration covariance, matched nulls and PPC/LOOCV not admitted. | Reuse its typed catalog/hash/preflight checks; do not use its log-likelihood as evidence-grade CF4 likelihood. |
| common.cobaya_adapters.likelihoods.HTTJointMultiProbeLikelihood | Current adapter initializes Planck with a zero data vector/identity-like covariance; NVSS/Quaia use hard-coded dipole summaries and diagonal covariance; CF4 uses zero summaries/diagonal covariance; Pantheon can enter a zero/random-direction fixture fallback; Gaia uses zero vectors; DESI zero fallback is present; the joint class loops over providers and sums marginal logp values. | Diagnostic/legacy only. Must not emit an observed-data or tensorized posterior claim. Replace observed mode with source-bound provider contracts and a common latent/cross-covariance model. |
| htt.htt.infer.dipole_vector_likelihood.DipoleVectorLikelihood | Axis/amplitude directional likelihood. | A narrow projection/diagnostic only, not the common state likelihood. |

### Required replacement boundary

The observed-data Cobaya adapter must have separate observed and synthetic modes. In observed mode:
1. Require real source paths, release IDs, SHA-256, ordered row IDs, units, frame, selection/window, covariance identity and provider version for each probe.
2. Validate each full within-probe covariance and every required cross-probe block or an explicit conditional-independence model.
3. Fail before sampling if a required block is missing, instead of instantiating zero vectors or identity covariances.
4. Construct one common latent-state likelihood or an equivalent proven joint summary likelihood, not a blind sum of separately marginalized probe likelihoods.
5. Derive x, Q, Pi, F, G_F only after the common posterior/compatibility region is formed.

The legacy adapters remain useful as bounded fixtures or narrow likelihood components after their inputs and semantics are qualified. They must not be silently promoted or used to manufacture a data likelihood.
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
