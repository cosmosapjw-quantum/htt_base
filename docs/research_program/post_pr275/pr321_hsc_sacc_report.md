# HSC S19A/Y3 Fourier-SACC readiness report

## Outcome

The exact HSC S19A/Y3 Fourier-space SACC file passed a bounded HSC-only
release-vector inspection.  Its terminal state is
`READY_FOR_WINDOW_CONVOLVED_REFERENCE`.

This is not a cosmological fit or a null-test result.  The released file does
not provide a preregistered HTT reference vector or a finite matched-null
ensemble, so no residual statistic, p-value, source label, cross-survey result,
or family-identification claim was computed.

## Exact input

- release: `HSC_S19A_Y3`
- product: `dalal23/hsc_y3_fourier_space_data_vector.sacc`
- bytes: `22340160`
- SHA-256: `a28f9e2e088e92d96d2d87083a6eeeac4c0c84c6b48e033bd3d1dc1bf0d8958f`
- loader: `sacc==2.1.2`
- analysis-code commit: `31c5406aae4648a751fbeda3b727f1e7c48854cb`
- analysis-code tree: `71d47b881f6edf120e73e76a7bbd123babc812d5`
- worker SHA-256: `672f3025ae6ee9d6a892f04691b9c2c2bdd195d19eb6e002a17db972a3886e28`

The compact generated result is
`docs/generated/pr321_hsc_sacc_result.json` (SHA-256
`3f543eaa823d80e6f09e37dfbfb9e7075a7970122be048922025c87f0673e576`).
It records hashes of the decoded float64 data vector and covariance without
redistributing their numerical values.

## Bound operator surface

The file contains only `cl_ee` data:

- four galaxy-shear redshift tracers, ordered `wl_0` through `wl_3`;
- ten upper-triangular tomographic tracer pairs;
- seventeen bandpowers per pair, for a 170-element released vector;
- one declared `15274 x 17` bandpower-window matrix per tracer pair;
- a symmetric positive-definite `170 x 170` full covariance.

The covariance is Cholesky-ready, has rank 170, and has spectral condition
number approximately `5.37745e5`.  It was not diagonalized.  Bandpower-window
column sums range from approximately `0.999815` to `1.034995`; therefore a
future theoretical vector must be convolved with the stored windows rather
than evaluated only at the reported effective multipoles.

## Scientific interpretation

The useful result is an input/operator decision:

> The downloaded HSC release vector, tomography order, bandpower windows, and
> full covariance form a numerically usable HSC-only input surface for a
> separately preregistered window-convolved reference calculation.

It does not establish E/B closure because the product is EE-only.  It also does
not solve HSC-KiDS covariance: the combined lane still requires an exact paired
same-sky null ensemble on the common overlap and registered survey operators.

## Reproduction

```bash
HSC_SACC_ROOT=/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/data/external/hsc_s19a_y3

PYTHONPATH=htt:htt/src:htt/htt \
python -B scripts/observed_runs/run_hsc_kids.py \
  --inspect-hsc-sacc \
  --hsc-sacc "${HSC_SACC_ROOT}/dalal23/hsc_y3_fourier_space_data_vector.sacc" \
  --confirm-input-sha256 a28f9e2e088e92d96d2d87083a6eeeac4c0c84c6b48e033bd3d1dc1bf0d8958f \
  --output docs/generated/pr321_hsc_sacc_result.json
```

The still-growing tract/photo-z download tree was not consumed by this run.
The result remains candidate-stack evidence until the stacked PR lineage is
landed and any later scientific reference calculation is separately frozen.
