# TSC_LEGACY Boundary

`tsc` remains import-compatible for old Teff-chart overlays, admissibility
checks, and reproducibility fixtures. New DAG work must treat this surface as
`TSC_LEGACY` with implementation scope `tsc_legacy`.

Allowed status:

- legacy reproduction
- diagnostic-only chart and admissibility reports
- advisory cross-check context with explicit caveats

Blocked status:

- not a native solver
- not HTT evidence
- not a MIO certificate
- not family identification
- not a runtime allow/block owner

Use `tsc_legacy.assert_legacy_reproduction_manifest()` when a legacy artifact
needs an explicit owner/scope check. The helper accepts only canonical
`TSC_LEGACY`/`tsc_legacy` manifests with conditional or diagnostic-only claim
tiers.
