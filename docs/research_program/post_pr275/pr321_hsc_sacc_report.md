# HSC S19A/Y3 Fourier-SACC readiness report

## Outcome and identity

The exact HSC S19A/Y3 Fourier SACC passed bounded HSC-only inspection with
`READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE`. It is not a fit
or null result: no reference vector or finite matched-null ensemble was
supplied, so no residual, p-value, source label, cross-survey result or family
claim was computed. Parsing `payload.mean` means the released observed summary
statistic was seen; no HTT-derived statistic or science inference was executed.

- product: `dalal23/hsc_y3_fourier_space_data_vector.sacc`
- bytes/SHA-256: `22340160` /
  `a28f9e2e088e92d96d2d87083a6eeeac4c0c84c6b48e033bd3d1dc1bf0d8958f`
- loader: `sacc==2.1.2`
- candidate base before repair: commit `8751557bdba616879cf238998d435b959bbc2eeb`
- science module SHA-256:
  `4bd7d8090e32682c998665b637b6bf5117449af1dcaee6e2df4b72fddf21e821`
- worker SHA-256:
  `8189ba2b946caffe530115a8c85a01e4699cdd155c02d24690c5e35792fbddb8`
- compact result: `docs/generated/pr321_hsc_sacc_result.json`, SHA-256
  `34dc946fec94c2c62f2733b6360dd4a5481906704c88ee46f0145aea3bc6d0cb`

Hashing and parsing consume one byte snapshot, preventing a path replacement
from mixing one file identity with another decoded payload. The result stores
only decoded vector/covariance hashes, not numerical bandpowers.
It also conforms to the controlling
`htt.pr321.hsc_sacc_repaired_result.v1` machine shape; this repair changes no
scientific value or claim boundary.

## Bound surface and interpretation

The release contains only `cl_ee`: four `galaxy_shear` tracers (`wl_0..wl_3`),
ten upper-triangular pairs, 17 bandpowers per pair, a `15274 x 17` window per
pair, and a symmetric positive-definite full `170 x 170` covariance. Covariance
rank is 170, condition number is about `5.37745e5`, and no diagonalization was
used. The common harmonic support and all ten pair-ordered weight matrices are
bound by SHA-256 `5665f979...d2d6108c` and
`9cef74b0...f6f2e501`, respectively. Window column sums span
`0.999815..1.034995`, so a future reference must be convolved with the stored
windows.

Each tracer binds 161 strictly increasing z samples and a nonnegative N(z) by
float64-le content hash. The unmodified raw trapezoidal integral is `0.025`
(up to float64 rounding) for each tracer; the worker does not silently
renormalize these arrays. The official fiducial
selection keeps ell centers `350, 500, 700, 900, 1200, 1600` for every pair,
giving 60 entries. Its matching 60x60 covariance has numerical rank 60,
minimum eigenvalue `1.6056562094228387e-22`, and condition number about
`1.03155e3`. The ordered index set is bound by SHA-256
`d765dcaa...cff7c180`. The full 170-vector is retained separately as
archive/inspection release-snapshot evidence and is not promoted as the
fiducial science selection.

The legacy-format warning is not its own authority: row values were checked
against `payload.mean`, pair blocks against the registered ordering, and SACC
pair-selection indices/values plus covariance indices against stored rows.

The machine result explicitly records no transfer, no null ensemble, native
SACC `cl_ee` units without conversion, window-normalization requirements, and
`response_rank.status=NOT_EVALUATED`. This establishes neither E/B closure nor
HSC-KiDS covariance; the latter still needs a common paired same-sky null
ensemble and registered survey operators.

For the MES programme this release is
`SCALAR_TOMOGRAPHIC_CONTROL_ONLY`. Its rotation-invariant `cl_ee` compression
contains no direction-indexed field, so vector/STF moments are forbidden and
local-boost/global-tilt response is not applicable. A CMB MES anchor is also
blocked because no channel-matched physical transfer, frame, normalization or
covariance contract exists.

```yaml
observed_statistic_seen: true
htt_derived_statistic_computed: false
observed_science_inference_executed: false
directional_support_status: NONE_COMPRESSED_ROTATION_INVARIANT_POWER_SPECTRA
vector_tensor_moment_eligibility: FORBIDDEN_NO_DIRECTION_INDEXED_FIELD
CMB_MES_anchor_compatibility: BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER
```

## Reproduction

```bash
PYTHONPATH=htt:htt/src:htt/htt python -B scripts/observed_runs/run_hsc_kids.py \
  --inspect-hsc-sacc \
  --hsc-sacc "${HTT_HSC_SACC_PATH}" \
  --confirm-input-sha256 a28f9e2e088e92d96d2d87083a6eeeac4c0c84c6b48e033bd3d1dc1bf0d8958f \
  --output docs/generated/pr321_hsc_sacc_result.json
```

Set `HTT_HSC_SACC_PATH` to the exact local release file before invoking the
command. The growing tract/photo-z tree was not consumed. This remains
candidate-stack evidence until its lineage lands and a later reference
calculation is frozen.
