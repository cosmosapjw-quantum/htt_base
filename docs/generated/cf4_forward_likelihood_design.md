# CF4 Forward-Likelihood Adapter Design

owner: HTT
implementation_scope: htt
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: cf4_object_catalog_coordinates_required
null_mock_status: not_statistical
config_hash: `sha256:33d2c8dc9cd21399beb1618d59d4fc41bb8fa63b0f6619906765a9d86d2b79a5`
input_hashes:
- `sha256:c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a`
- `sha256:e59353019191d5c0cd7c448e9105db9295896c080cf6ae58e918d0b5f37feb30`
- `sha256:4257f3305dd284bf9a08fbb9665833c4c810bb77415ca419bb6e92b2abde6c94`
input_sources:
- `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`
- `htt/obsstat/catalogs/cf4.py`
- `htt/htt/htt/rest_frame/cf4_likelihood.py`
caveats:
- Schema-bound diagnostic adapter only.
- `.npz` catalog loads compare declared checksum to file bytes.
- Compact CF4 query grids are not object-level diagnostic-score catalogs.
- Transformed peculiar velocity variables cannot use exact Gaussian semantics without a readable JSON Gaussian velocity manifest with hash provenance and an approved Gaussian noise-model label.
- The score is diagonal-only; group, method, and calibration-correlated covariance is not bound.
- Local/global response overlap is not externally audited, and rank-deficient designs carry blockers.
- No HTT evidence, posterior odds, native solver validation, or morphology-atlas claim is created.
generating_command: `Codex apply_patch REV-R081; venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py htt/test_packaging_imports.py`
git_commit_or_worktree_state: `431026f+dirty`
artifact_path: docs/generated/cf4_forward_likelihood_design.md

## Scope

REV-R081 introduces a two-lane CF4 track:

1. `obsstat.catalogs.cf4` validates object-level CF4-like rows and release metadata.
2. `htt.rest_frame.cf4_likelihood` evaluates a diagonal diagnostic distance-variable Gaussian score for tests and design exercises only.

The OBSSTAT lane requires object/group identifiers, sky coordinates, redshift frame metadata, a distance-like variable, uncertainty, grouping flags, method/calibration flags, release, and checksum. The HTT lane consumes that schema-bound object and returns a blocked diagnostic payload with matched-null, covariance, PPC, and LOOCV blockers.

## Required CF4 Object Fields

| Field | Requirement |
| --- | --- |
| `object_id` | non-empty one-dimensional object or group identifier |
| `ra_deg`, `dec_deg` | finite ICRS-like sky coordinates |
| `redshift` | positive finite observed redshift in the declared frame |
| `distance_variable` | finite distance-like variable |
| `distance_uncertainty` | positive finite uncertainty |
| `group_id`, `is_grouped` | group membership metadata |
| `method_flag` | distance-indicator method or reconstruction method |
| `calibration_flag` | calibration provenance label |

## Likelihood Skeleton

The diagnostic model is:

```text
predicted_distance_variable =
    baseline_distance_variable
  + local_flow_basis @ local_flow_coefficients
  + n_hat @ global_vector
  + calibration_offset
```

The diagonal Gaussian score is computed on the distance-like variable with the declared distance uncertainty. If the distance variable is a transformed peculiar velocity, exact Gaussian likelihood semantics are blocked unless the CF4 metadata includes a readable JSON `gaussian_velocity_manifest_ref` whose file bytes, config hash, input hashes, frame, calibration status, and strict Gaussian noise-model label validate. When loading a `.npz` catalog, the declared catalog checksum is compared against the file bytes.

## Promotion Blockers

- production object-level CF4 catalog binding not present,
- matched nulls not bound,
- publication-grade covariance not bound,
- group, method, and calibration-correlated covariance not bound,
- local/global response overlap not externally audited,
- rank-deficient response designs marked no-claim,
- PPC and LOOCV not bound,
- no native morphology atlas and no native low-ell solver output.
