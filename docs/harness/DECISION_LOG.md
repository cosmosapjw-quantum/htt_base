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

## 2026-06-12 - PR-040 sky-support boundary

- Accepted: `common.contracts.SkySupport` remains the canonical sky-support
  dataclass; `common.sky_support` supplies construction, hashing, and
  validation helpers without redefining the schema.
- Accepted: deterministic mask hashes are SHA-256 payload hashes over mask
  bits plus coordinate frame, pixelization, and optional `nside`.
- Accepted: sky-facing manifest validation requires coordinate frame,
  mask hash, sky-support hash, sky fraction, and completeness status; a
  status string alone is insufficient.
- Accepted: sky-facing `sky_support_status` uses a bounded support-status
  vocabulary; over-strong tokens such as `production_validated` are rejected.
- Accepted: production-facing directional summaries must use unit-vector
  spherical means, not raw longitude/latitude arithmetic means.
- Deferred: migrating every artifact producer and summary writer to call the
  PR-040 validators remains downstream HTT/MIO/BASS integration work.

## 2026-06-12 - PR-012 generated status authority

- Accepted: `common.status_snapshot` is the canonical generator for public
  PR-DAG status sidecars under `docs/generated/*`.
- Accepted: `docs/generated/status_snapshot.json`,
  `docs/generated/claim_ledger.json`, and `docs/generated/status_matrix.md`
  are generated together from `pr_backlog.yaml` and `pr_status.yaml`.
- Accepted: generated PR-DAG rows are diagnostic-only bookkeeping and always
  keep `production_validated` false until explicit scientific validation gates
  exist outside DAG-status accounting.
- Accepted: PR-card owner aliases are normalized at the generator boundary:
  `BASS_PY` becomes canonical `BASS`/`bass_py`, `MANUSCRIPT` becomes
  `COMMON`, and legacy `TSC` becomes `TSC_LEGACY`/`tsc_legacy`.
- Accepted: old manual `docs/status_matrix.md` and `docs/claim_ledger.md`
  surfaces are generated-authority indexes, not independent SSoTs.
- Deferred: migrating older VER2 manuscript generated snippets to consume the
  new DAG-status sidecars remains downstream manuscript/export work.

## 2026-06-12 - PR-022 PR delta generator boundary

- Accepted: `scripts/codex_harness/new_pr_delta.py` renders PR deltas from the
  active DAG backlog and `docs/PR_DELTAS/TEMPLATE.md`.
- Accepted: default output names are lowercase `pr-xxx.md`, and existing
  outputs are not overwritten unless `--force` is supplied.
- Accepted: PR delta scaffolds include structured safe defaults for owner,
  implementation scope, claim tier, transfer source, sky support, null/mock
  status, covariance status, PPC status, and LOOCV status.
- Accepted: generator-boundary owner aliases normalize `TSC` to `TSC_LEGACY`,
  `BASS_PY` to `BASS`, and `MANUSCRIPT` to `COMMON`.
- Deferred: a separate machine-readable review JSON artifact remains
  unnecessary until a downstream harness consumes it.

## 2026-06-12 - PR-070 OBSSTAT ObservableVector facade boundary

- Accepted: `common.contracts.ObservableVector` remains the single observable
  vector schema authority.
- Accepted: `htt.obsstat` is an OBSSTAT facade for diagnostic observable
  feature packaging, not a new schema layer and not an inference owner.
- Accepted: implementation files live in the top-level `obsstat` package under
  `htt/obsstat`, and the installed `htt` wrapper aliases that package as
  `htt.obsstat`; package discovery must include `obsstat*`.
- Accepted: OBSSTAT feature payloads may hold alm, scalar, morphology, null,
  template, covariance, and BiPoSH feature dictionaries when accompanied by an
  OBSSTAT-owned diagnostic-only manifest and canonical `SkySupport`.
- Accepted: p-value features require a non-empty null ensemble reference and
  tracked/corrected look-elsewhere provenance, even when nested inside
  non-null feature blocks.
- Accepted: transfer-derived feature blocks require COMMON transfer metadata
  and cannot claim native transfer status without explicit native validation
  gates; this applies to every OBSSTAT feature block, not just template or
  covariance branches.
- Accepted: OBSSTAT rejects HTT likelihood/evidence/posterior keys,
  MIO-certificate semantics, and premature Bianchi family-identification,
  geometry-detection, or family-ranking keys/phrases.
- Deferred: shape validation, harmonic-convention validation, null ensemble
  construction, and richer morphology feature validation remain downstream
  obsstat PRs.
