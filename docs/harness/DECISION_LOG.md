# Decision Log

Record accepted, rejected, and deferred design decisions.

## 2026-07-27 - PR-247 local completion

- Accepted: candidate C `b431da78...`, seal `4facb9...`, passed its complete
  registered read-only review and latest-target integration against
  `be2d545...`; PR-247 may close as an internal process-integrity card.
- Accepted: the status/SSoT amendment is a new Git candidate and must be
  resealed, reviewed, and integrated before handoff. Candidate-C evidence is
  completion input but cannot masquerade as evidence for the amended bytes.
- Boundary: completion creates no external publisher authorization, GitHub PR,
  publication readiness, or scientific claim. Those remain separate actions
  and evidence lanes.

## 2026-07-27 - PR-247 candidate-B invalidation

- Accepted: candidate `f3521b42...` and seal `0fdfe9...` are invalidated. Its
  complete registered read-only review reproduced a publication bypass when
  the adapter received Google's codelab-documented top-level
  `tool_args.CommandLine` Antigravity envelope.
- Accepted: the current `toolCall.name`/`toolCall.args` Antigravity contract
  remains primary, while the documented legacy top-level envelope is also
  inspected. Current calls return decision JSON; legacy calls use nonzero-exit
  denial. Missing, malformed, mixed, or unmatched-tool envelopes are denied
  fail-closed. Hook registration retains the current official schema.
- Evidence boundary: the candidate-B review is a valid FAIL artifact, not
  readiness evidence. The repair requires a new commit, seal, registered
  read-only result, and latest-target integration receipt.

## 2026-07-27 - PR-247 candidate-A invalidation

- Accepted: candidate `c1d2716f...` and seal `b5d845...` are invalidated. A
  bundled inline option such as `/bin/bash -lc` bypassed the static publication
  classifier, and resolving the selected venv launcher before execution
  discarded its pytest environment.
- Accepted: runtime-wrapper parsing covers bundled short options and long
  inline-code options. The `{python}` token preserves its absolute invocation
  path while separately receipting the resolved binary path and byte hash.
- Rejected: changing the Codex hook matcher away from `^Bash$`. Current
  official Codex documentation states that shell and unified `exec_command`
  calls both reach hooks under canonical tool name `Bash`.
- Evidence boundary: the first frozen reviewer produced structural-only
  coverage but timed out before a registered result envelope. Its findings are
  preliminary repair input, not a completed independent review or readiness
  decision.
- Kill switch: any repaired bytes require a new commit, seal, registered
  read-only result, and latest-target integration receipt.

## 2026-07-26 - PR-247 change-set and publication boundary

- Accepted: an internal DAG work card, a coherent Git change-set, and an
  external GitHub publication group are three distinct identities. One failure
  type maps to a finding or commit; one coherent change-set maps to at most one
  open GitHub PR.
- Accepted: unattended agents normally end with local commits, a candidate
  seal/review/integration recommendation when possible, and zero GitHub PRs.
  Publisher is not an assignment role.
- Accepted: review and integration authority begins only after a committed,
  clean candidate binds the exact target, candidate, merge-base, tree, commit
  set, binary diff, file set, remote destination, GitHub repository identity,
  and integration-policy bytes.
- Accepted: any candidate, target, repository, policy, review, integration,
  inventory, or authorization drift invalidates downstream evidence. A repair
  after first review creates a new candidate and requires a new review.
- Accepted: the first reviewer verdict is read-only and carries an executable
  coverage matrix. Same-model repetition is correlated review, not an
  independent oracle; R2/R3 require at least one executable externalized
  oracle.
- Accepted: integration-policy argv is sealed and must be nonpublication;
  publication-capable commands are rejected before a rehearsal subprocess can
  run beneath provider hooks.
- Accepted: the policy uses a portable `{python}` token rather than assuming
  bare system Python or a host-specific venv path. The rehearsal preserves the
  selected invocation path and separately receipts the real executable path
  and byte hash.
- Accepted: repository hooks deny ordinary-agent publication as a defense in
  depth. The hard capability boundary is a serialized external publisher whose
  credential, authorization key, and nonce ledger are unavailable to agent
  sandboxes and whose live repository inventory is bound to the sealed remote.
- Accepted: the repository gate may validate and consume a short-lived
  one-time authorization but never execute `git push`, create a PR, or select
  publisher authority.
- Rejected: implicit `main`, branch-name-sourced push authorization,
  self-declared publisher roles, repo-local publisher secrets, point-in-time
  inventory for an unbound `--repo-slug`, credential-bearing remote URLs, and
  green per-card CI as evidence of combined change-set safety.
- Deferred: provider-authenticated execution/read telemetry, richer
  domain-specific coverage generation, existing PR-topology cleanup,
  merge-queue deployment, and full CI cost re-tiering.
- Status boundary: this architecture is implemented but PR-247 stays
  `in_progress` until a repaired candidate has a clean seal, complete
  independent read-only result, and latest-target integration receipt. No
  scientific or publication-readiness claim changes.

## 2026-07-20 - PR-176 conservative non-identification boundary

- Accepted: the scientific terminal follows only the frozen response/rank
  router and is `NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE`; the failed covariance
  self-consistency axis is reported separately and cannot silently replace it.
- Accepted: all raw affine coefficients remain candidate diagnostics because
  the frozen covariance battery fails. Null and non-identification are valid
  reproducible closeouts and satisfy the card dependency without fabricating a
  positive measurement.
- Accepted: the physical STF diagonal basis uses explicit trace-free tensor
  differences. The semantic erratum corrects this basis without changing
  radii, frame, seeds, thresholds, response authorities, or covariance
  authority.
- Accepted: candidate packs cannot authorize their own scientific closeout.
  The external adjudication receipt is bound by exact path, hash, manifest,
  and generation root; any candidate-byte change requires fresh adjudication.
- Rejected: independence-based joint likelihoods, PR-148 covariance reuse,
  inferred q response, post-result reseeding/rethresholding, theta apex,
  leakage immunity, and promotion to acceleration, tilt, anisotropy,
  geometry/family, transfer/native, or public claims.
- Deferred: PR-151 finalize and PR-155--158 until all 1,025 mocks, observed
  authentication, 15 audits, full rehash, and producer/runner receipts are
  terminal. PR-178 follows those cards; PR-180 remains locked by PR-172;
  PR-181 remains covariance-deferred; hypothesis/native lanes remain closed.

## 2026-07-20 - PR-179 raw-CF4 conditional boundary

- Accepted: the prospectively frozen raw-CF4 estimand terminates literally as
  `H_ONLY_SELECTION_SYSTEMATICS_CONDITIONAL`; its exact H-only matched-null
  rank is subordinate supporting evidence and cannot rename the terminal.
- Accepted: q fails the five-fold directional-cubic response gate and every q
  coefficient, axis, envelope, and rank is withheld rather than repaired.
- Accepted: `H_cat` is a catalogue-fit label. The result remains conditional on
  selection, method mix, reported marginal errors, sky/depth support, and
  restricted-residual exchangeability; depth reversal is a material caveat.
- Accepted: raw value access is an executable capability boundary, not a prose
  allowlist. CF4 reconstruction, cosmology-corrected, Cartesian, distance, and
  P0 values never enter the production object.
- Accepted: multi-file scientific packs use measured execution provenance and
  lock/journal/recovery/fsync/manifest-last publication. A passing pack must
  replay byte-for-byte and preserve earlier failed/inconclusive reviews.
- Accepted: the user-planned checkpoint-110 sequence is recorded separately at
  the honest 108/130 completed count. It does not override the canonical
  five-completion checkpoint due at 110 completed cards.
- Rejected: interpreting `2/20000`, the H amplitude/axis, or response-design
  diagnostics as a cosmological p-value, directional Hubble measurement,
  peculiar-flow attribution, isotropy/anisotropy result, HTT evidence,
  geometry/family result, or transfer/native validation.
- Deferred: PR-180 until PR-172 success (currently unsatisfied), PR-178 until
  terminal PR-151 plus PR-155--158, PR-181 until covariance closure, and all
  typed native-dependent work until authenticated external delivery.

## 2026-07-16 - PR-122 evidence-authority boundary

- Accepted: process result, evidence availability/integrity, and scientific
  status are orthogonal axes. A process PASS with blocked science may enter an
  explicitly caveated audit disclosure but cannot authorize claim release.
- Accepted: release evidence is a typed, acyclic, content-addressed graph whose
  root binds generator/verifier code, selector and execution identities,
  execution environment, parent receipt, authority registry, artifact
  manifest, and downstream consumers.
- Accepted: trusted verifier identity includes code plus decision-bearing
  closure/default/global/callable state. A caller-declared digest is never an
  independent substitute for verifiable semantics.
- Accepted: ready matched-null inference requires an exact canonical
  `MatchedNullCompetitionReport` that can be rebuilt from typed content,
  source lineage, FPR threshold, and report hash. A compact hook or scalar is
  not evidence by itself.
- Accepted: the literal-only release-pin fields remain outside the
  verifier/graph hash cycle as an explicit commit-reviewed trust root. They are
  parsed without module import or execution, and the authoritative environment
  permits no import-origin exclusions.
- Accepted: authoritative graph, freeze, and package CLIs start through the
  tracked source-only launcher before site hooks or workspace bytecode can run.
  PR-122 consumes an immutable exact-scope authority snapshot; later global
  principal registrations cannot broaden or invalidate the historical slice.
- Accepted: the active MES inventory remains blocked until PR-124 supplies a
  typed independently supported theorem/convention successor and nonzero D2
  authority. Legacy triples and diagnostic witnesses are not promoted.
- Rejected: self-signed/circular receipts, correlated internal identities as
  external replication, arbitrary readiness flags, zero-test authority,
  caller pseudo-PPC/Bayes values, fabricated matched-null hashes, dead MES
  pointer decoys, and unbound/opaque verifier or pytest-environment state.
- Deferred: scientific estimand, matched data/null/covariance, transfer,
  native solver, morphology, geometry, and family validation remain downstream
  work. PR4 data work remains entirely skipped by user scope.

## 2026-07-16 - PR-122 harness integration and suite acceleration

- Accepted: the uploaded shared-context packet is repository-scoped and
  versioned. Every subagent spawn uses a built context pack, registered unique
  assignment, exact four-field header, bounded fan-out, isolated result path,
  and schema-checked stop envelope. Independent results are merged before
  adjudication; missing evidence fingerprints fail closed.
- Accepted: installer upgrades are merge-or-refuse. Existing `AGENTS.md`,
  `agent.md`, `AGENTS.md.fragment`, and `.codex` files are never overwritten
  when divergent or symlinked; conflicts stop before destination writes.
- Measured: the original 195-test PR-122 consumer suite took 889.86 seconds.
  A single payload profile attributed 58.345 cumulative seconds to entry-row
  construction, including 559 repeated policy loads (57.002 seconds) and 564
  YAML parses (41.037 seconds). The unprofiled payload fell from 41.413 to
  17.284 seconds with one validated build-local policy snapshot, a 58.3%
  reduction.
- Accepted: package builders may reuse one immutable reviewed-binary pin map
  only within a single payload construction and must rehash canonical policy
  bytes before returning. There is no production module-global/LRU policy
  cache. Pure assertion tests may share canonical JSON/archive bytes only when
  every caller receives an independent object; mutation, CLI, determinism, and
  fail-closed tests remain fresh.
- Rejected for this workload: GPU offload and NumPy vectorization. The measured
  work is YAML/path/stat/regex/SHA/Git/DEFLATE control flow rather than a dense
  numerical kernel; transfer overhead and a larger trusted dependency surface
  would dominate.
- Deferred: `pytest-xdist` or process-parallel repository scanning. The host
  has 12 physical/24 logical CPU cores and an RTX 3080 Ti, but xdist is not
  installed. Parallel execution is considered only after duplicate work is
  removed and artifact-writing tests are isolated, with unchanged sorted
  findings, ZIP bytes, mutation kills, RSS bounds, and cold/warm benchmarks.
- Measured after the change: the focused 19-test audit-package generator suite
  completed in 246.09 seconds. A broader six-package/PR-120 pre-reseal run
  completed in 766.28 seconds with 168 passes and four expected closeout
  failures: three stale package manifests and one obsolete direct package
  check. The direct check was corrected to the source-only launcher; the
  failures remain recorded. After canonical reseal, the exact four failing
  cases passed in 81.03 seconds. The full PR-122 consumer suite then passed all
  196 tests in 430.47 seconds, a 51.6% wall-time reduction from the 889.86-second
  baseline despite one additional test.

## 2026-07-14 - PR-118 final adversarial-audit decision

- Accepted: preserve all 55 prior findings as `KNOWN_OPEN`, keep the 14 audit
  gaps separate, and admit only 33 source-deduplicated new atomic deltas.
- Accepted: the as-shipped manuscript decision is REJECT; a defensible object
  requires a new methods/negative-audit submission after major rebuild.
- Accepted: prioritize pre-solver exchangeable null calibration,
  non-identification/theorem-domain work, independent numerical oracles, and
  authenticated CF4/DESI rebuilds.
- Accepted: keep native-atlas/equivalence candidates as post-native interface
  hypotheses only. `hypothesis_only=true` and `public_use=false` remain hard.
- Accepted: final CRAG scope is frozen to 12 independently shortlisted
  candidates. The authoritative packet is pruned to 12 queries and 22
  primary/official sources; full raw lookups remain hash-bound.
- Rejected: retaining any present anisotropy, global-tilt, FLRW-violation,
  precision-evidence, geometry, or family-identification headline.
- Deferred: the nine staged `AUD-R01A`-`AUD-R05C` follow-up cards are proposed only;
  they are not inserted into the completed active DAG without a new intake.

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

## 2026-06-12 - PR-071 OBSSTAT harmonic/spin convention boundary

- Accepted: `htt.obsstat.alm_conventions` is the OBSSTAT-owned convention
  registry for harmonic feature export. COMMON keeps the canonical
  `ObservableVector` schema, and OBSSTAT owns this feature-extraction policy.
- Accepted: scalar alm metadata records `scipy.special.sph_harm_y` evaluator
  provenance, colatitude/longitude angle ordering, Condon-Shortley phase,
  orthonormal normalization, coordinate frame, healpy-style m-major storage,
  scalar reality condition, and `lmax/mmax`.
- Accepted: spin-2 metadata records Q-then-U paired-map order and
  `healpy_map2alm_spin` transform provenance, but records no E/B sign export
  because the checked healpy API documentation does not specify enough
  semantics for PR-071 to assert that claim.
- Accepted: OBSSTAT alm export now requires channel-local
  `convention_metadata`; parent/root metadata does not satisfy child harmonic
  payloads because mixed scalar/spin blocks would otherwise be ambiguous.
- Accepted: convention metadata rejects unknown fields, coordinate-frame
  mismatches against `SkySupport`, and healpy-storage coefficient vectors with
  the wrong shape.
- Deferred: computing alms, validating map transforms, transfer provenance,
  null/mask/covariance calibration, morphology compatibility, and geometry or
  family claims remain downstream work.

## 2026-06-12 - PR-080 BASS external transfer adapter boundary

- Accepted: the PR-card path `htt/src/bass/transfer/...` is stale for this
  checkout. New BASS transfer adapter code lives under the active package root
  `htt/bass/transfer`.
- Accepted: `bass.transfer.registry.default_external_transfer_registry()`
  returns a pure PR-014 `TransferRegistry`, while
  `default_external_transfer_adapter_registry()` returns lazy wrappers that can
  evaluate legacy callables with attached provenance.
- Accepted: current AniCLASS-calibrated legacy callables are registered as
  `AniCLASS_external`; the BASS power-law comparison callable is registered as
  `empirical_proxy`.
- Accepted: PR-014 `TransferValidRange.k_min/k_max` remains present for schema
  compatibility, but scalar legacy callable domains are separately recorded
  and enforced as `callable_input_domain` over `x_h` or `Sigma2`.
- Accepted: adapter metadata uses canonical `claim_tier="conditional"`,
  `production_status="diagnostic_only"`, `transfer_conditional=True`, and
  `native_solver_result=False`.
- Rejected: no live CLASS/AniCLASS execution, no native low-ell solver stub
  returning values, no external-as-native validation label, and no HTT/MIO
  evidence or certificate merge is introduced by PR-080.
- Deferred: migrating downstream HTT inference producers, MIO diagnostics, or
  OBSSTAT feature producers to consume the registry remains downstream DAG
  work.

## 2026-06-12 - PR-030 TSC legacy boundary

- Accepted: `tsc` remains import-compatible and does not emit import-time
  deprecation warnings, because strict warning harnesses must still be able to
  import legacy overlays and tests.
- Accepted: `tsc_legacy` is the canonical metadata surface for the frozen
  TSC/Teff boundary. It records `TSC_LEGACY`, `tsc_legacy`, legacy
  reproduction bundle authority, and a conditional or diagnostic-only claim
  ceiling.
- Accepted: raw legacy pack refs with `owner="TSC"` may remain in generated
  VER2 provenance fixtures only when bridge loaders normalize them to canonical
  `TSC_LEGACY` manifests.
- Accepted: current production `tsc.*` imports in MIO/HTT/BASS are pinned by a
  static allowlist and are advisory/caveat-only. New production imports require
  explicit claim-gate review.
- Rejected: no new active TSC owner role, no HTT evidence/posterior ownership,
  no MIO certificate ownership, no BASS transfer/native validation ownership,
  no OBSSTAT feature ownership, no runtime gate ownership, and no family-claim
  path are introduced by PR-030.
- Deferred: extracting generic source/propagation/observable semantic guards
  from legacy TSC language remains PR-031.

## 2026-06-12 - PR-113 manuscript figure inventory boundary

- Accepted: `scripts/audit_manuscript_figures.py` is a COMMON/MANUSCRIPT
  diagnostic inventory tool. It parses TeX `\includegraphics` and
  `\graphicspath` usage, resolves extensionless graphics paths, and joins
  current PR-011 quarantine state from `common.artifact_manifest`.
- Accepted: the generated reports live at
  `docs/generated/manuscript_figure_inventory.md` and
  `docs/generated/missing_figure_references.md` with owner, scope, claim tier,
  transfer source, config hash, input hashes, caveats, generating command, git
  commit, and worktree state.
- Accepted: PR-113 text checks compose with
  `common.semantic_guards.no_overclaim.scan_text` and add narrow
  manuscript-specific risk findings for manual status numbers,
  solver-validation wording, overstrong validation wording, production-value
  wording, and pre-native family-identification language. Explicit negative
  wording such as family identification not being established is allowed.
- Accepted: `--dry-run` remains non-mutating and exits zero so the PR-card
  command can be used for inventory generation and review. Final manuscript
  freeze is blocked by the report contents, not by changing the PR-113 dry-run
  command into a strict release gate.
- Rejected: no figure regeneration, no manifest promotion, no LaTeX
  buildability claim, no native solver validation, no external-transfer-as-native
  validation, no HTT evidence, no MIO certificate, and no family-identification
  claim are introduced by PR-113.
- Deferred: strict release gating for freeze, manifest-backed figure
  regeneration, stale generated VER2 status replacement, and manuscript text
  edits remain downstream manuscript/export PR work.

## 2026-06-13 - PR-051 BudgetSpec denominator-policy boundary

- Accepted: `mio.formalism.budget_spec` is the MIO-owned diagnostic
  denominator-policy contract for PR-051. It records explicit
  `MES_linear`, `external_transfer`, `atlas_quantile`, and `observational`
  policies, positive finite denominator values, owner/scope/claim metadata,
  config/input hashes, assumptions, caveats, and policy-specific provenance.
- Accepted: `external_transfer` budgets and sensitivity points require PR-014
  transfer metadata and cannot claim native validation or certified filling.
- Accepted: `atlas_quantile` remains pre-solver schema scaffolding only and
  accepts only controlled pre-solver-safe atlas status values.
- Accepted: observational budgets require explicit sky-support, covariance,
  and null/mock status metadata.
- Accepted: the legacy COMMON/BASS descriptive departure bridge is restricted
  to explicit `MES_linear`/`linear_MES`; it must not relabel legacy budgets as
  external-transfer, atlas, or observational policies without the MIO contract.
- Rejected: implicit denominator policy, generic `atlas_or_mes_ceiling`,
  non-positive denominator values, transfer metadata loss in sensitivity
  points, external/native conflation, atlas-quantile classifier semantics,
  and any MIO posterior/evidence/certification semantics.
- Deferred: Q normalized score, certified F, Pi exceedance, G_F depth-gap,
  richer migration of legacy COMMON `BudgetSpec`, and full VER2 artifact
  export runtime validation remain downstream work.

## 2026-06-13 - PR-053 certified F boundary

- Accepted: `mio.formalism.CertifiedFillingFraction` is the MIO-owned
  diagnostic-only F contract. It computes F sample-wise as signed sign-clean
  `x_C / U` under a PR-051 admissible certified ceiling.
- Accepted: `F_Bayes` is the arithmetic mean of sample-wise F values and the
  payload records `ratio_of_means_used=false`.
- Accepted: invalid negative sectors, non-positive or non-finite ceilings,
  and values outside `0<=F<=1` are rejected rather than clipped or serialized
  as physical occupancy.
- Accepted: F payloads require owner, scope, claim tier, config/input hashes,
  generating command, git or worktree provenance, transfer provenance, and
  sky/covariance/null status metadata.
- Rejected: deriving F from Q, `abs(x_C)`, positive-part clipping, ratio of
  means, legacy BASS proxy filling paths, external/native conflation, HTT
  evidence/posterior semantics, diagnostic truth-attestation semantics, or
  geometry/family-identification language.
- Deferred: Pi exceedance, G_F depth-gap, calibrated F null ensembles,
  PPC/LOOCV, and any native morphology atlas integration remain downstream.

## 2026-06-13 - PR-054 Pi exceedance boundary

- Accepted: `mio.formalism.ExceedanceCurve` is the MIO-owned diagnostic-only
  Pi contract. It records strict `sample_value > threshold` exceedance curves
  over explicit Q or certified-F diagnostic samples.
- Accepted: every Pi payload requires explicit `measure_kind`, threshold grid,
  threshold-policy metadata, sample counts, source metadata, config/input
  hashes, generating command, and git or worktree provenance.
- Accepted: selected-threshold summaries require pre-registered metadata.
  Otherwise Pi artifacts remain curve-only.
- Accepted: null/mock measures require non-default covariance and null/mock
  support status metadata.
- Accepted: transfer-labelled direct or bridged Pi sources require PR-014
  consumable transfer metadata and remain transfer-conditional.
- Rejected: implicit measure defaults, hidden selected-threshold metadata,
  post-hoc threshold selection, direct native transfer labels, signed-Q bridge
  inputs, non-JSON metadata, truth probability, posterior/evidence semantics,
  p-value/FPR claims without matched calibration, and geometry/family language.
- Deferred: calibrated p-values/FPR, PPC/LOOCV, report-card integration,
  posterior-pushforward boundaries, G_F depth-gap, and native morphology atlas
  integration remain downstream.

## 2026-06-13 - PR-075 BiPoSH feature boundary

- Accepted: `htt.obsstat.biposh_features` is the OBSSTAT-owned
  diagnostic-only feature surface for caller-supplied sparse BiPoSH or
  off-diagonal covariance coefficients.
- Accepted: payloads must carry PR-071 harmonic convention metadata, required
  rotation metadata, deterministic canonical sparse-entry hashes, duplicate
  rejection, threshold retained/discarded accounting, support statuses, caveats,
  config/input hashes, generating command, and git or worktree provenance.
- Accepted: transfer-derived BiPoSH features require PR-014 transfer metadata
  and remain transfer-conditional.
- Rejected: deriving BiPoSH from BASS/native transfer in this PR, relying on
  sparse duplicate summation, adding p-values without matched null metadata,
  collapsing deterministic template-fit and covariance-feature branches, or
  promoting a nonzero BiPoSH feature to geometry/family evidence.
- Deferred: map-to-BiPoSH estimators, matched null ensembles, full covariance
  calibration, HTT model likelihoods, MIO report-card use, native morphology
  atlas comparison, and family-equivalence gates remain downstream.

## 2026-06-13 - PR-055 G_F depth-gap boundary

- Accepted: `mio.formalism.IsotropyGap` is the MIO-owned diagnostic-only
  `G_F` / `log_g_F` depth-gap contract. It compares certified-F depth-bin
  summaries with an explicit positive finite floor.
- Accepted: `log_g_F` is defined as
  `log(max(F_comparison,floor))-log(max(F_reference,floor))`, and `G_F` is
  `exp(log_g_F)`. Raw F, effective F, and floor activation are serialized.
- Accepted: depth-bin export requires bin interval/convention, selection and
  assignment hashes, sky/mask support status, non-default covariance and
  null/mock status plus metadata, denominator-evolution status, and sample
  count.
- Accepted: covariance/null metadata use controlled status vocabularies and
  reject uncalibrated labels rather than treating arbitrary status strings as
  sufficient calibration.
- Accepted: G_F records denominator-evolution split fields with sample-wise
  x_C, denominator, and F arrays. Mean x_C and denominator deltas are marked
  non-decompositional because `F_Bayes` is the mean of sample-wise ratios.
- Accepted: transfer-derived F records remain transfer-conditional and must
  have matching transfer source/spec IDs and canonical transfer metadata hashes
  across compared bins.
- Rejected: raw unstabilized ratios, hidden floor clipping, missing depth-bin
  metadata, default covariance/null statuses, mixed transfer comparisons,
  HTT posterior/evidence semantics, MIO certificate semantics, native solver
  validation, p-value/FPR claims, morphology compatibility, geometry claims,
  family claims, or global-tilt claims from G_F alone.
- Deferred: calibrated local/global null ensembles, response-rank audits,
  MIO report cards, PPC/LOOCV, and native morphology atlas integration remain
  downstream.

## 2026-07-14 - PR-116 physmath audit harness boundary

- Accepted: treat both supplied GPT-5.6 packages as hash-pinned,
  unauthenticated methodology snapshots under separate immutable vendor roots.
- Accepted: activate only the repo-owned `htt-physmath-audit` adapter. COMMON
  owns the audit bundle; audited owner is recorded separately as
  `subject_owner`.
- Accepted: mutable run state lives under `docs/audits/<run>/state`; upstream
  initializers may be exercised only in disposable copies.
- Accepted: installer reuse is idempotent only for a byte-identical vendor
  destination and fails closed on extra, missing, or modified files.
- Accepted: counterfactual family/geometry work maps to exploratory,
  internal-only metadata and never enters public or production claim surfaces.
- Rejected: root extraction, generic nested-skill activation, vendor mutation,
  workflow checks as scientific validation, multi-agent votes as independent
  replication, or external transfer as native evidence.
- Deferred: the actual delta audit, legacy disposition ledger, advocate
  ranking, and referee decision belong to PR-117 and PR-118.

## 2026-07-15 - PR-119 remediation-state and DAG authority decision

- Accepted: `docs/codex_handoff/pr_backlog.yaml` is the canonical active DAG
  root; JSON and `machine_readable/` copies are generated mirrors.
- Accepted: intake exactly `PR-119..166` now; defer `PR-167..183` to PR-167.
- Accepted: orchestration state, execution resolution, and scientific status
  are orthogonal typed axes. A completed PR does not imply evidence readiness.
- Accepted: terminal negative receipts may satisfy only an explicit
  `requires_terminal_receipt` aggregation edge. `requires_success` accepts only
  a receipted success; scientific consumption needs an independently
  authenticated adjudicated claim subset.
- Accepted: claim levels are scheme-qualified. Identically spelled `C1` values
  in family-gate and roadmap-planning schemes have no automatic mapping.
- Accepted: the bootstrap authority registry is default-deny, bounded, and
  grants internal author/adjudicator roles only. Internal subagents are
  correlated review, not external replication, and cannot promote science.
- Accepted: adjudication/native dependency edges load repository-local receipt
  bytes only through path+SHA-256 pointers and typed authority validation.
  Native delivery is bound to `native_low_ell_delivery`; the progress CLI has
  no implicit trust callback, so authenticated edges remain unsatisfied until
  an explicit trusted verifier is integrated.
- Accepted: the 102 authoritative findings start and remain `OPEN`; historical
  response dispositions and contradictory prose do not override the structured
  active root.
- Accepted: checkpoint 065 and the PR-118 audit package remain immutable and
  validate against the Git seal tree, not mutable live status sidecars.
- Accepted: PR-150 records PR3/FFP10 download complete and PR4/NPIPE download
  not started; all PR4 data analysis is skipped by explicit user instruction.
  The original joint `roadmap_rescue_v1:C3` gate remains unavailable and the
  active lane is capped at PR3-conditional diagnostic
  `roadmap_rescue_v1:C2`.
- Rejected: active TEFF/TSC ownership, bare claim levels, self-adjudication,
  boolean or shape-only receipt assertions, terminal bucket/resolution
  mismatch, hidden completed cards, premature PR-167 intake, synthetic
  native-delivery substitution, and any inference from process success to
  scientific rescue.
