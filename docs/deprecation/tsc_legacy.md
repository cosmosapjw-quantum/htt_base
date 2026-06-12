# TSC_LEGACY Deprecation Boundary

PR-030 freezes TSC as a legacy reproduction surface. Existing `import tsc`
paths stay available so old overlays, tests, and generated reproducibility
bundles can still load, but new claim-bearing framework work must not use TSC
as an active science owner.

Canonical metadata:

- owner: `TSC_LEGACY`
- implementation_scope: `tsc_legacy`
- allowed bundle kind: `legacy_reproduction`
- claim ceiling: `conditional` or `diagnostic-only`

Allowed language:

- `legacy reproduction`
- `diagnostic-only chart diagnostic`
- `advisory TSC context`
- `cross-check only`

Blocked language:

- not a native solver
- not HTT evidence
- not a MIO certificate
- not family identification
- not a posterior-producing or likelihood-producing layer
- not transfer validation

Operational rule:

New artifacts may accept legacy `owner="TSC"` inputs only when the canonical
contract normalizes them to `TSC_LEGACY`/`tsc_legacy` and the artifact remains a
legacy reproduction bundle. All active inference, evidence, transfer,
observable-feature, certificate, and runtime-decision ownership stays with
HTT, BASS, OBSSTAT, MIO, and COMMON according to the current contract layer.
