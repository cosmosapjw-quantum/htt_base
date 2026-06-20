# Spectroscopic Data-Random Dipole Estimator Design

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: data_random_sky_coordinates_bound
mask_status: random_catalog_bound_mask_not_certified
null_mock_status: not_bound
covariance_status: not_bound
production_status: diagnostic_only
config_hash: `sha256:1d914b2c8694222f3cd852b2baf64669a62d9c568e75e76d7f3f8367f053bfb9`
input_hashes:
- `sha256:c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a`
- `sha256:390ea1e2cb035745a40b23f0cd6b50cb4bbb7641afecde515d0048d23e7bce37`
- `sha256:1618002933e3e939abf7b1a9304711eb6587ddf5f74f5a1ff0bec389671f71a0`
input_sources:
- `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`
- `htt/obsstat/catalogs/redshift_selection.py`
- `htt/obsstat/catalogs/spectroscopic_dipole.py`
generating_command: `Codex apply_patch REV-R082; venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_spectroscopic_dipole.py tests/obsstat/test_redshift_selection.py htt/test_packaging_imports.py`
git_commit_or_worktree_state: `586c4c0+dirty`
artifact_path: docs/generated/spectroscopic_dipole_design.md

## Scope

REV-R082 adds an OBSSTAT-only spectroscopic data-random dipole feature contract. It is a feature extractor and metadata binder, not an HTT likelihood, not a posterior/evidence surface, and not an observed-result claim.

The estimator contract is:

```text
dipole = first_moment(data, weights) - alpha * first_moment(randoms, weights)
```

`first_moment` is the weighted mean of unit sky-direction vectors. The implementation records `alpha_definition` and catalog weight definitions so the scaling is not silently promoted into a calibrated survey result.

## Required Metadata

The data and random catalogs must share:

- release,
- tracer,
- region,
- redshift-bin id.

Each catalog carries role, source path, checksum, redshift frame, redshift-selection status, weight definition, claim tier, and allowed-use metadata. Missing random catalogs, parity mismatches, nonfinite coordinates, nonpositive redshifts, negative weights, and zero total weight fail closed.

## Redshift-Selection Correction

For observed-redshift selected bins, the correction metadata is required. The current implementation provides a metadata-only hook and a toy vector correction for tests. A toy vector may change the diagnostic vector in tests, but it does not close the survey-specific redshift-selection blocker. The relevant literature source is von Hausegger and Dalang, Phys. Rev. D 111, 123547, DOI `10.1103/PhysRevD.111.123547`, which motivates treating redshift-selection corrections as a required model component rather than an optional caption note.

## Promotion Blockers

- survey random/mask certification not complete,
- certified selection weights not complete,
- matched nulls not bound,
- covariance not bound,
- survey systematics not bound,
- PPC/LOOCV not bound,
- response/rank and local/global interpretation gates not bound,
- survey-specific redshift-selection correction not bound for observed-redshift bins,
- no native morphology atlas and no native low-ell solver output.

## Safe Use

This artifact may be used to test data-random bookkeeping, import surfaces, redshift-selection metadata wiring, and future survey-readiness gates. It must not be used as a public spectroscopic dipole measurement, HTT evidence term, MIO certificate, native solver result, or morphology/family claim.
