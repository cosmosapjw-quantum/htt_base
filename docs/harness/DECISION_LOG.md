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

## 2026-06-12 - PR-015 COMMON semantic claim-language boundary

- Accepted: `common.semantic_guards.no_overclaim` is the active COMMON
  implementation point for claim-language blocking; it does not import HTT,
  MIO, BASS, TSC, or OBSSTAT packages.
- Accepted: `scripts/check_claim_language.py` is the deterministic CLI for
  active docs/manuscript/report scans. It supports stable text/JSON output,
  reports missing paths, returns 1 on findings, and returns 2 only when all
  requested roots are missing.
- Accepted: explicit negative/governance text is allowed by guardrail-context
  suppression so AGENTS, skills, PR deltas, and decision logs can state what is
  blocked without failing their own linter.
- Accepted: archived/generated/provenance paths are skipped by default to keep
  active production scans actionable; `--include-archives` is available for
  historical audits.
- Accepted: the first rule set targets pre-native overclaim families: scalar or
  low-ell surrogate wording used for blocked geometry/family claims, TSC/Teff
  full-solver or full-polarisation wording, MIO diagnostic promotion into
  posterior/evidence wording, and external-transfer/native conflation.
- Deferred: this is not a complete natural-language classifier. Future PRs
  should add focused rules from real claim-drift findings instead of turning
  the linter into a broad word blacklist.

## 2026-06-12 - PR-050 MIO signed-departure formalism boundary

- Accepted: the stricter PR-050 `DepartureBundle` lives under
  `mio.formalism`; the older `common.departure_contracts.DepartureBundle`
  remains stable for existing BASS plumbing until a separate migration PR.
- Accepted: canonical `B_C` component order is `Sigma2_std`, `W2_std`,
  `Omega_tilt`, `Omega_k_aniso`; canonical projection signs are
  `+1, -1, +1, +1`.
- Accepted: `x_C` is a signed comparator projection that may be negative or
  cancel to zero. It is not an anisotropy norm, and no positive-part export is
  included in this bundle.
- Accepted: exporting `x_C` requires non-empty comparator, frame, units,
  config hash, input hashes, caveats, and complete finite canonical components.
- Accepted: `cancellation_index` is algebraic bookkeeping:
  `1 - abs(x_C) / sum(abs(component_values))`, with zero component mass mapped
  to zero cancellation rather than division by zero.
- Accepted: transfer-derived bundles require PR-014-compatible transfer
  metadata and use the COMMON transfer guard to block external/native
  provenance drift.
- Deferred: component calibration, frame transforms, covariance/null
  calibration, response-rank metadata, and certificate generation remain
  downstream MIO/HTT/obsstat PRs.

## 2026-06-12 - PR-041 HTT ZoA support-mode ladder boundary

- Accepted: the new ZoA ladder lives at the importable HTT package path
  `htt/htt/htt/zoa/selection_ladder.py`; the PR-card path
  `htt/src/htt/zoa/selection_ladder.py` is not a live package root in this
  checkout.
- Accepted: COMMON retains the pixelization primitive. PR-041 only adds
  `common.healpix_selection.source_mask_from_pixel_mask()` so HTT can map
  sky-support masks to source masks without duplicating pixel math.
- Accepted: `htt.zoa.selection_ladder` separates raw, ZoA-masked,
  angular-completeness, and mock-calibrated support summaries and can export
  the existing COMMON `DirectionalSummary` four-channel wrapper.
- Accepted: every PR-041 ladder summary remains diagnostic support metadata
  with `production_allowed=False`; even adequate mock-calibration support does
  not become a posterior-derived production axis.
- Accepted: `production_mode=True` is a strictness flag, not a promotion flag.
  It forbids uniform fallback through `SkySelectionConfig` and requires
  explicit adequate mock-calibration weights.
- Deferred: posterior-derived axis promotion, statistical mock-coverage
  calibration, null/FPR accounting, and downstream `a_lm`/`a_2m` synthesis
  locks remain PR-042/PR-043 work.

## 2026-06-12 - PR-023 COMMON progress scoreboard boundary

- Accepted: `skipped` is an explicit status list parsed by
  `scripts/codex_harness/progress_report.py`; skipped PRs are neither
  completed nor blocked.
- Accepted: skipped PRs do not count toward percent completion, do not satisfy
  dependencies, and are excluded from `unblocked_next`.
- Accepted: status overlap among `completed`, `blocked`, `skipped`, and
  `in_progress` is a hard progress-report failure.
- Accepted: `--write-scoreboard` emits deterministic current progress markdown
  under `docs/generated/progress_checkpoints/progress_scoreboard.md`, including
  blocked, skipped, unblocked-next, checkpoint, and replan state.
- Accepted: checkpoint 020 is the five-PR checkpoint for PR-015, PR-050,
  PR-041, and PR-023 plus the already-completed PR count since checkpoint 015;
  progress advanced by 5, so no replan PR is required.
- Deferred: the harness cannot prove a manually edited completed PR was truly
  reviewed. That remains enforced by the per-PR delta, tests, claim scans, and
  commit loop.
