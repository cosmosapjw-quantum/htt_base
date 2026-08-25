# HSC S19A/Y3 Fourier-SACC readiness report

## Outcome and identity

The exact HSC S19A/Y3 Fourier SACC passed bounded HSC-only inspection with
`READY_FOR_WINDOW_CONVOLVED_REFERENCE`. It is not a fit or null result: no
reference vector or finite matched-null ensemble was supplied, so no residual,
p-value, source label, cross-survey result or family claim was computed.

- product: `dalal23/hsc_y3_fourier_space_data_vector.sacc`
- bytes/SHA-256: `22340160` /
  `a28f9e2e088e92d96d2d87083a6eeeac4c0c84c6b48e033bd3d1dc1bf0d8958f`
- loader: `sacc==2.1.2`
- analysis code: commit `9b5bd132b22670b83feb67c3493d717c2690f102`, tree
  `85d3151112d9103db2bc2359874f76329099c509`
- worker SHA-256: `5abc18ee535961dd64d64d17bbf99d7f8524124d4ec9bb74025c49e6c6ce4b92`
- compact result: `docs/generated/pr321_hsc_sacc_result.json`, SHA-256
  `bf391b4ff6cd61194baaf60b37100786855e5e17230576750db669a2600ce59f`

Hashing and parsing consume one byte snapshot, preventing a path replacement
from mixing one file identity with another decoded payload. The result stores
only decoded vector/covariance hashes, not numerical bandpowers.

## Bound surface and interpretation

The release contains only `cl_ee`: four `galaxy_shear` tracers (`wl_0..wl_3`),
ten upper-triangular pairs, 17 bandpowers per pair, a `15274 x 17` window per
pair, and a symmetric positive-definite full `170 x 170` covariance. Covariance
rank is 170, condition number is about `5.37745e5`, and no diagonalization was
used. Window column sums span `0.999815..1.034995`, so a future reference must
be convolved with the stored windows.

The machine result explicitly records no transfer, no null ensemble, native
SACC `cl_ee` units without conversion, window-normalization requirements, and
`response_rank.status=NOT_EVALUATED`. This establishes neither E/B closure nor
HSC-KiDS covariance; the latter still needs a common paired same-sky null
ensemble and registered survey operators.

## Reproduction

```bash
PYTHONPATH=htt:htt/src:htt/htt python -B scripts/observed_runs/run_hsc_kids.py \
  --inspect-hsc-sacc \
  --hsc-sacc /home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/data/external/hsc_s19a_y3/dalal23/hsc_y3_fourier_space_data_vector.sacc \
  --confirm-input-sha256 a28f9e2e088e92d96d2d87083a6eeeac4c0c84c6b48e033bd3d1dc1bf0d8958f \
  --output docs/generated/pr321_hsc_sacc_result.json
```

The growing tract/photo-z tree was not consumed. This remains candidate-stack
evidence until its lineage lands and a later reference calculation is frozen.
