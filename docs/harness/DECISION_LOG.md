# Decision Log

Record accepted, rejected, and deferred design decisions.

## 2026-06-12 - PR-011 artifact quarantine boundary

- Accepted: keep `common.contracts.ArtifactManifest` as the canonical manifest
  dataclass and put PR-011 scanner/provenance validation in
  `common.artifact_manifest`.
- Accepted: unmanifested legacy figures/PDFs are quarantined and listed, not
  deleted, regenerated, captioned, or interpreted.
- Accepted: native-transfer provenance requires explicit native transfer or
  native solver validation gates; morphology-atlas support is separate
  downstream evidence.
- Deferred: full generated result-pack/table manifest validation remains for
  downstream artifact-ledger/status-snapshot PRs.
