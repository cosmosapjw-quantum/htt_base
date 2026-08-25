# PR-321 re-audit delta — MES-boundary and observed-state corrections

## Precedence

This delta supplements the controlling PR-321 re-audit package at commit
`11b2cdaf557a601e183e68d7be4c46aa5e122892`.  Where this file is more specific,
it controls.  Existing findings on fiducial scale selection, tracer N(z), legacy
row-order replay, status-URL provenance, and semantic scope remain unchanged.

## Additional blocking findings

```yaml
current_PR321_science_surface:
  P0: 0
  P1: 8

MES_integration_boundary:
  P0: 2
  P1: 1

terminal: BLOCKED_PR321_REAUDIT_REPAIR_AND_LOCAL_RERUN
```

### P0 — directionless spectra cannot enter the MES directional lane

The released `cl_ee` vector is a rotationally invariant tomographic power
spectrum.  It preserves redshift-bin dependence but not sky direction or
harmonic phase.  The required result fields are:

```yaml
directional_support_status: NONE_COMPRESSED_ROTATION_INVARIANT_POWER_SPECTRA
mes_methodology_role: SCALAR_TOMOGRAPHIC_CONTROL_ONLY
vector_tensor_moment_eligibility: FORBIDDEN_NO_DIRECTION_INDEXED_FIELD
local_boost_global_tilt_eligibility: NOT_APPLICABLE_NO_DIRECTIONAL_RESPONSE
```

The existing P1 role warning is promoted to a P0 scientific-integrity boundary
for any MES-labelled or local/global result.

Required test:

```text
test_pr321_sacc_is_scalar_tomographic_control_not_directional_mes_input
```

### P0 — CMB MES anchors are cross-channel incompatible with HSC shear spectra

A dimensionless HSC shear statistic must not be divided by a CMB almost-EGS
shear/vorticity ceiling without an explicit channel-matched response/transfer,
frame, congruence, normalization and covariance contract.

```yaml
CMB_MES_anchor_compatibility: BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER
```

Required test:

```text
test_pr321_rejects_cmb_mes_anchor_without_channel_matched_transfer
```

### P1 — observed-statistic provenance

The worker parses and hashes `payload.mean`, so the observed released summary
statistic was seen even though no HTT-derived statistic or inference was run.

```yaml
observed_payload_validated: true
observed_released_data_vector_parsed: true
observed_summary_statistic_present: true
observed_statistic_seen: true
htt_derived_statistic_computed: false
observed_science_inference_executed: false
```

### P1 — portable exact operator identities

The repaired compact result must bind the canonical window support and weights,
the ordered fiducial index set, and the 60-vector/60x60 covariance bytes:

```yaml
window_support_sha256_float64_le:
window_weight_sha256_float64_le:
fiducial_ordered_index_sha256:
fiducial_data_vector_sha256_float64_le:
fiducial_covariance_sha256_float64_le:
```

### P1 — MES-plan ancestry

PR-411 and PR-321 are sibling descendants of PR-320.  MES implementation must
not begin until its branch descends from the repaired PR-321 terminal and
contains the exact accepted PR-411 planning package.

```text
BLOCKED_MES_PLAN_NOT_DESCENDED_FROM_REPAIRED_PR321
```

PR-321 is not eligible as the directional low-z consumer; an object/map-level
HSC shape product with exact admission and a registered directional operator is
required for that future role.
