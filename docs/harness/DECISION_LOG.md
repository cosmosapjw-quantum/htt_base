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

## 2026-06-12 - PR-013 MIO/HTT type boundary

- Accepted: `workspace.contracts.htt_posterior.HTTPosteriorBundle` is the
  canonical new HTT posterior contract path for PR-013; it accepts only
  `HttLikelihoodTerm` entries and an HTT-owned manifest.
- Accepted: `MioCertificate` remains diagnostic-only. It exposes explicit
  diagnostic query properties and raises if converted to an HTT likelihood
  term or posterior bundle.
- Accepted: recursive guards reject direct certificates, MIO-shaped dict
  payloads, MIO cross-check row/table objects, and MIO diagnostic scalar keys
  in likelihood-input paths.
- Deferred: migrating every legacy HTT inference entry point to the new
  `HTTPosteriorBundle` constructor remains downstream HTT inference work.

## 2026-06-12 - PR-014 transfer provenance boundary

- Accepted: `common.transfer_registry.TransferFunctionSpec` is the canonical
  transfer-provenance record. `workspace.contracts.transfer` is a thin alias
  only.
- Accepted: every transfer-dependent result path must be able to carry source,
  family, valid range, observable kind, normalization, calibration status,
  caveats, and validation gates.
- Accepted: external/AniCLASS and empirical-proxy transfer sources cannot use
  native calibration status or native validation gates.
- Accepted: future native gate-passed transfer specs require an explicit native
  transfer or native solver validation gate.
- Deferred: migrating existing BASS/HTT/MIO producers to emit
  `TransferFunctionSpec` is downstream adapter and transfer-registry work.
