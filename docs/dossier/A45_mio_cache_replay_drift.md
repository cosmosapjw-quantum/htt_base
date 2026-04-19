# A45 · MIO cache-replay drift protocol

**Appendix**: A45 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W17D5 design dossier (documentation-only; no
code landing — the guard lands with HJ-03, the first cross-process
harness; see A45.3).
**Status**: **deferred-to-trigger** — specifies the hash-chain
verification mechanism A44.6 names but does not detail. The code-side
check only lands when a harness first consumes a persisted MIO
artefact (HJ-03 evidence anatomy is the expected trigger per A42.6
+ A44.7).
**Code anchors (reference, no A45 landing today)**:
[`bass_py/workspace/contracts/mio_certificate.py`](../../bass_py/workspace/contracts/mio_certificate.py)
(current `config_hash` + `input_data_hashes` field contract);
[`bass_py/mio/interface/mio_certificate.py`](../../bass_py/mio/interface/mio_certificate.py)
(`_hash_config` 16-char sha256 generator);
[`bass_py/tsc/integration/htt_bridge.py`](../../bass_py/tsc/integration/htt_bridge.py)
(TSC-06 — mode A44.4.1, no cache edge, reference for the in-memory
path that A45 does **not** regulate).
**Parent references**:
v3 §4.5.4 (G19 hard separation);
v3 §10.2 (HTT ↔ MIO contract table);
[A32 MioCertificate schema](A32_mio_certificate_schema.md) (§A32.4
provenance requirements — A45 specifies how the four provenance fields
are consumed at replay time);
[A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md)
(property 1 — two independent code paths; A45 proves the replay path
does not collapse them);
[A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md)
(§A41.6 HJ-03 worked example — the landing vehicle for A45's code);
[A42 evidence anatomy stub](A42_evidence_anatomy.md) (§A42.5 —
HJ-03 is the first HJ that needs cache replay);
[A43 schema-hash digest](A43_schema_hash_digest.md) (A45 is the
*content-hash* companion to A43's *structure-hash* mechanism; the
`allow_unsigned_config=True` escape hatch in §A45.5 upgrades cleanly
once A43 lands);
[A44 MIO → HTT handshake sequence](A44_mio_htt_handshake_sequence.md)
(§A44.4.2 artefact-replay mode; §A44.6 names this guard);
W15 F3 (A43 digest test deferred-to-trigger; A45's escape-hatch
gating depends on A43's upgrade path).

---

## A45.1 Purpose

A44.6 declares that the cross-check harness must re-verify
`MioCertificate.config_hash` and `MioCertificate.input_data_hashes`
before consuming a persisted artefact (A44.4.2 mode) but does not
specify *how*. This appendix writes the check so the HJ-03 author has
a mechanical recipe and the reviewer has a single paragraph to check
the PR against.

A45 is **not** a request to retrofit the guard onto the TSC-06
in-memory harness. TSC-06 runs in mode A44.4.1 (same process,
`mio_cert` object handed directly to `ff_htt_mc_cross_check`) and has
no cache edge to drift. The trigger is §A45.3 — the first harness
that crosses a persistence boundary, which is HJ-03 by A42.5 + A44.7.

The hash chain A45 enforces runs along two axes:

1. **Config drift** — did someone edit the certificate JSON by hand
   between `emit_*_artefact` and replay? The stored `config_hash` is
   the 16-char sha256 prefix of the diagnostic payload tuple
   computed at t₁ (A44.2). Recomputing the same digest at replay
   time from the re-parsed certificate surfaces any field-level
   edit.
2. **Input-data drift** — is the data bundle being fed into the
   HTT path at t₃ (A44.2) the same bundle whose hashes were
   recorded on the certificate at t₁? If a Planck TT posterior file
   has been re-downloaded with a different pipeline version, the
   replay cross-check is cross-checking against a different set of
   numbers than the certificate advertised.

## A45.2 Guard algorithm

Pseudocode for `verify_cache_replay(mio_cert, htt_input_bundle,
*, allow_unsigned_config=False)`; the HJ-03 harness calls this
immediately after `MioCertificate.from_json(...)` and before
constructing its frozen `is_cross_check=True` report (t₄ in A44.2):

```
1. recomputed_config_hash = _hash_config(
       mio_cert.report_type,
       mio_cert.probe_name,
       mio_cert.channel,
       mio_cert.departure_variables,
       mio_cert.adequacy_indicators,
       mio_cert.consistency_metrics,
   )
2. if mio_cert.config_hash == "":
       if not allow_unsigned_config:
           raise CacheReplayDriftError("unsigned certificate; "
               "pass allow_unsigned_config=True to accept")
       # else: bypass recorded, proceed to (4)
   else:
       if mio_cert.config_hash != recomputed_config_hash:
           raise CacheReplayDriftError(
               f"config drift: stored={mio_cert.config_hash} "
               f"recomputed={recomputed_config_hash}")
3. observed_input_hashes = [
       sha256_hex_prefix(path) for path in htt_input_bundle.paths
   ]
4. if set(observed_input_hashes) != set(mio_cert.input_data_hashes):
       raise CacheReplayDriftError(
           f"input-data drift: certificate={mio_cert.input_data_hashes} "
           f"bundle={observed_input_hashes}")
5. return  # harness proceeds to t₄
```

Four properties this algorithm guarantees:

- **Hand-edit detection.** Any field in the payload tuple that the
  caller edits post-emission rotates the recomputed hash and fails
  step 2 — even a single-bit edit to `departure_variables["x_C"]`.
- **Order-insensitivity on input paths.** Step 4 compares *sets*,
  not lists, because `input_data_hashes` is documented as an
  unordered bag of content-digests (A32.4; bass_py readers sort it
  before emission).
- **No re-resolution of `git_commit`.** A45 intentionally does not
  touch the provenance SHA — it is the t₁-time HEAD per A44.3 and
  the replay path treats it as opaque metadata. Any check that
  recomputed `git_commit` at t₄ would violate A44.3.
- **No posterior leakage.** `verify_cache_replay` reads only the
  certificate and the HTT input-bundle descriptors; it never
  constructs a posterior or consumes one. The harness's G19 posture
  (A34.1–A34.5) is preserved.

## A45.3 CI trigger point — when this dossier becomes code

A45 lands as a test + helper in the same PR as the first harness
that consumes a persisted MIO artefact. Candidates per
`INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 "Deferred to Week 17+":

1. **HJ-03 evidence anatomy** (expected first adopter). Per A42.5
   + A44.7, HJ-03 crosses a persistence boundary because HTT Phase F
   ln-B decomposition is expensive and naturally cached. The HJ-03
   harness PR lands:
     - `bass_py/mio/interface/cache_replay.py` (new file) with
       `verify_cache_replay` + `CacheReplayDriftError`;
     - three acceptance tests per §A45.6 below (clean / edited /
       drifted input);
     - an A41 checklist step-4 entry pointing at the harness
       signature's `mio_cert` input.
2. **HJ-04 FLRW tension** (may or may not need A45). If HJ-04's
   harness runs in-process it inherits TSC-06's posture and needs
   no A45 guard. If a persistence boundary is introduced (e.g. the
   MIO side writes to disk for a re-audit job), A45's landed code
   is reused unchanged.
3. **Future MIO-MIO cross-check** (hypothetical). Same posture —
   the landed `verify_cache_replay` is the canonical entry point.

Landing A45 pre-trigger would freeze an un-exercised API surface
and force a one-line refactor on the HJ-03 PR — no information
gain. The mechanism specification in this appendix is the
deliverable; the code follows the first consumer.

## A45.4 Failure modes A45 catches (vs. A34 / A43 / A44)

| Drift mode | Who catches | Mechanism |
|---|---|---|
| New `MioCertificate` field added silently | A43 | Schema-hash digest rotation on extension |
| New `report_type` / `channel` value added | A41 | Extension checklist (7 steps) |
| Hand-edit to `departure_variables["x_C"]` on disk | A45 | `config_hash` recomputation at replay time |
| Pipeline re-download changes Planck TT checksum | A45 | `input_data_hashes` set-equality |
| HTT reading MIO mid-flight (t₃ before t₂) | A44 | Sequence diagram's missing arrow |
| Harness constructs `MioCertificate` in-band | A41 | Step-4 acceptance test requires `mio_cert` input |
| HTT ingests MIO as a likelihood | A34 / G19 | `as_posterior_bundle()` raises; static lint |

A45 is **strictly content-level**: it asserts the replay is the
same run numerically. A43 is **strictly structural**: it asserts
the replay is the same run *contractually*. The two are orthogonal
— a future PR that both extends the schema (A43) and drifts the
payload values (A45) must pass both gates.

## A45.5 The `allow_unsigned_config` escape hatch

The A45.2 algorithm treats `config_hash == ""` as the unsigned
case. Two circumstances this path is expected to see:

1. **Pre-W6 legacy certificates**. MIO-HJ-06a (Week 6) introduced
   `build_mio_certificate`'s auto-populated `config_hash`; any
   certificate written by the hand-constructed path before that
   commit carries an empty hash. Opening such an artefact for
   re-audit requires the caller to pass
   `allow_unsigned_config=True` with a domain caveat added to the
   replay report.
2. **Synthetic / test certificates.** The
   `workspace.contracts.tests.test_mio_certificate._certificate`
   helper constructs certificates with a stub `"cafef00d"` hash.
   A unit test that exercises the replay path on a stub artefact
   must opt in explicitly.

The flag is **deliberately** a kwarg and not a default: an invisible
fallback would silently accept every unsigned certificate as valid.
The W15 F3 / A43 upgrade path plans to replace the 16-char sha256
prefix with A43's structure-aware digest; at that point, the
unsigned case narrows to pre-A43 artefacts only, and the flag
can transition from "any unsigned cert" to "artefacts from commits
before A43's landing". §A43.3 is the trigger; A45 inherits the
upgrade without rewriting the algorithm — step 2's `""` check
simply becomes a `digest_version < A43_INTRODUCED_VERSION` check.

The escape hatch is **never** a way to bypass input-data drift.
Step 4 runs unconditionally — a caller who wants to replay against
a different data bundle is writing a new cross-check, not
re-auditing an old one, and must construct a fresh `MioCertificate`
at t₁ rather than patching around the guard.

## A45.6 Acceptance test list (paste-ready for HJ-03 PR)

**Harness-signature note (W17 F2 / W18D3).** This test block
presumes the HJ-03 replay harness exposes the two-argument signature
`verify_cache_replay(mio_cert, htt_input_bundle, *,
allow_unsigned_config=False)` described in §A45.2, with
`htt_input_bundle` carrying a `.paths` iterable for the step-3
sha256 digest computation. A41.6's HJ-03 worked example (step 6.5)
is the authoritative place to freeze that signature: if HJ-03 lands
with a different input shape — e.g. a `bundle.digests` tuple in
lieu of `bundle.paths`, or a `replay_context` object wrapping both
— the harness-signature freeze and the paste-replace of this block
must land in the same PR so the pseudocode, the worked example,
and the tests agree at the point of first use. See A41.6 step 6.5
for the reciprocal note.

The HJ-03 landing PR's test block must include at least these
five acceptance tests (name the file `test_cache_replay.py` under
`bass_py/mio/tests/`):

1. `test_verify_cache_replay_clean_passes_through` — freshly-emitted
   certificate + matching input bundle → returns None (harness
   continues).
2. `test_verify_cache_replay_hand_edited_payload_raises` —
   recompute the `config_hash` on an artefact whose
   `departure_variables["x_C"]` was edited post-emission; expect
   `CacheReplayDriftError` with `"config drift:"` prefix.
3. `test_verify_cache_replay_missing_input_hash_raises` — drop one
   entry from the HTT bundle's hash list relative to the
   certificate's `input_data_hashes`; expect drift error with
   `"input-data drift:"` prefix.
4. `test_verify_cache_replay_unsigned_requires_opt_in` — certificate
   with `config_hash == ""` raises by default; passing
   `allow_unsigned_config=True` returns None with a caveat
   appended to the replay report (caveat surfacing is the HJ-03
   harness's responsibility, not A45's).
5. `test_verify_cache_replay_does_not_touch_git_commit` — monkeypatch
   subprocess to raise if called; verify the guard returns None on
   a clean artefact without invoking any git shell-out.

Test (5) mirrors the W17D1 workspace-layer microtest
(`test_git_commit_is_capture_time_not_lazy`) at the MIO layer;
the two together lock A44.3 at both the contract and harness
surfaces.

## A45.7 Relation to other appendices

- **A32** — field contract. A45 does not change the schema; it only
  specifies how the four provenance fields are *consumed* at replay.
- **A34** — structural G19 cross-check properties. A45's guard is a
  pre-condition for property 1 (two independent code paths) to hold
  across a persistence boundary; without the guard, an edited
  certificate would collapse the two paths' inputs.
- **A41** — report_type extension protocol. A41's step 4 (acceptance
  tests) now includes §A45.6's five tests for every new harness that
  may replay across processes.
- **A42** — HJ-03 evidence anatomy. A42 is the first consumer; the
  §A45.6 test list lands in the same PR.
- **A43** — schema-hash digest. A43 protects structure, A45
  protects content. §A45.5's escape hatch upgrades cleanly when A43
  lands — the version-gated unsigned-case narrows automatically.
- **A44** — handshake sequence. A44.6 names this guard; A45
  specifies the algorithm. An A45 violation at t₄ is a handshake
  abort: the harness must fail loudly rather than return a report
  (t₅ never runs).

## A45.8 No code landing in this appendix

A45 is specification-only. The HJ-03 PR (A41.6 worked example) is
the landing vehicle; §A45.6 is the exact test block to paste.

Re-audit trigger: if a future PR introduces a harness that replays
a persisted MIO artefact *without* calling `verify_cache_replay`
first, A45.2's algorithm is no longer the single source of truth
for replay integrity and this appendix must be rewritten.
