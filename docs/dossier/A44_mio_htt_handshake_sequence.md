# A44 · MIO → HTT cross-check handshake sequence

**Appendix**: A44 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W16D5 draft (documentation-only; no code landing).
**Status**: **specification**. The TSC-06 filling-fraction cross-check
(landed W7) is the concrete reference implementation; HJ-03 evidence
anatomy and HJ-04 FLRW tension will follow the same sequence once their
HTT dependencies land.
**Code anchors (reference)**:
[`bass_py/tsc/integration/htt_bridge.py`](../../bass_py/tsc/integration/htt_bridge.py)
(TSC-06 — currently the only fully wired cross-check);
[`bass_py/workspace/contracts/mio_certificate.py`](../../bass_py/workspace/contracts/mio_certificate.py)
(producer contract);
[`bass_py/mio/coherence/directional.py`](../../bass_py/mio/coherence/directional.py)
(HJ-02a producer — advisory, not a numerical cross-check per A34.3).
**Parent references**:
v3 §4.5.4 (G19 hard separation);
v3 §10.2 (HTT ↔ MIO contract table);
[A32 MioCertificate schema](A32_mio_certificate_schema.md);
[A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md) — the
property 1–5 definition this sequence is a *temporal* companion to;
[A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md) —
§A41.6 worked example for HJ-03 is the extension vehicle for this
sequence;
[A42 evidence anatomy stub](A42_evidence_anatomy.md) — the first HJ-03
consumer of this handshake;
W6 FM6 (`git_commit` resolves at instantiation time);
W11 F5 (same finding documented for HJ-02b).

---

## A44.1 Purpose

A34 specifies **what** a G19-compliant cross-check is (five structural
properties). This appendix specifies **when** each side writes and reads
its part — the ordering contract that preserves G19 across the
`MIO → HTT cross-check` call edge. A44 is the *execution-order* companion
to A34's *structural* definition: a cross-check that satisfies all five
A34 properties but inverts the MIO-first / HTT-second order below is
still at risk of the leakage modes enumerated in §A44.5.

The sequence is a five-step invariant:

1. MIO instantiates a `MioCertificate` — provenance SHA captured at
   instantiation time (§A44.3, W6 FM6 / W11 F5).
2. MIO emits the certificate artefact (REG-02 `mio_` filename gate).
3. HTT reads the MIO certificate as an advisory input *only* — never as
   a likelihood input (A32.5 rule 2).
4. The cross-check harness (`tsc.integration.htt_bridge` or sibling)
   draws the paired HTT scalar and constructs a frozen
   `is_cross_check=True` report.
5. `assert_<channel>_consistent` is the only consumer; the report is
   surfaced for agreement / disagreement reporting and never returns
   to HTT as a posterior update.

Any re-ordering of (1)–(4) — in particular, HTT reading MIO state
*before* MIO has fixed its provenance SHA, or the cross-check
harness consuming HTT output *before* the counter-part certificate is
emitted — reopens the leakage modes catalogued in §A44.5.

## A44.2 Sequence diagram

```
Caller                MIO producer         HTT Phase F            Cross-check harness
  │                        │                     │                        │
  ├── run MIO job ────────►│                     │                        │
  │                        │                     │                        │
  │                        │ t₁: instantiate     │                        │
  │                        │     MioCertificate  │                        │
  │                        │     • git_commit    │                        │
  │                        │     • config_hash   │                        │
  │                        │     • input_data_   │                        │
  │                        │       hashes        │                        │
  │                        │                     │                        │
  │                        │ t₂: emit_*_artefact │                        │
  │                        │     (REG-02 `mio_`) │                        │
  │                        │                     │                        │
  ├── run HTT job ─────────┼────────────────────►│                        │
  │                        │                     │                        │
  │                        │                     │ t₃: Phase F            │
  │                        │                     │     posterior / ln B   │
  │                        │                     │     (independent       │
  │                        │                     │      code path)        │
  │                        │                     │                        │
  ├── run cross-check ─────┼─────────────────────┼───────────────────────►│
  │                        │                     │                        │
  │                        │                     │                        │ t₄: read both
  │                        │                     │                        │     sides, build
  │                        │                     │                        │     FFCrossCheck
  │                        │                     │                        │     Report(is_
  │                        │                     │                        │     cross_check=
  │                        │                     │                        │     True, frozen)
  │                        │                     │                        │
  ├────────────────────────┼─────────────────────┼────────── return ──────┤ t₅: assert_*_
  │                        │                     │                        │     consistent
  ▼                        ▼                     ▼                        ▼
agreement /            (immutable              (Phase F writes        (never returns
disagreement           certificate —            once; no MIO-         to HTT as
reported, no           git_commit froze         driven update)         posterior
downstream             at t₁ per                                       update)
likelihood             W6 FM6 / W11 F5)
update
```

Three temporal invariants the diagram enforces:

- **t₁ before t₂**: provenance SHA is captured at dataclass construction,
  BEFORE artefact emission. W6 FM6 documented this for HJ-02a; W11 F5
  extended it to HJ-02b. A reader of a persisted `mio_*` artefact
  therefore sees the commit active at certificate-build time, not the
  commit active at read time (by-design; see A44.3).
- **t₂ before t₄**: the cross-check harness reads the MIO certificate
  AFTER emission. A harness that synthesises a `MioCertificate` in-band
  (skipping t₂) sidesteps the provenance record and is a G19 anti-
  pattern — catch it in A41 checklist step 4.
- **t₃ independent of t₁–t₂**: HTT Phase F must never peek at the MIO
  certificate during posterior evaluation (that would collapse the two
  code paths A34.2 rule 1 requires). The harness is the only place
  both sides meet.

## A44.3 Provenance-SHA capture (W6 FM6 / W11 F5 contract)

`MioCertificate.git_commit` is the SHA of HEAD *at the moment the
dataclass is constructed*, not at artefact-emission time. Two reasons:

1. **Reproducibility over lateness.** A user who re-runs artefact
   emission from a cached certificate expects the commit that produced
   the numbers, not the commit that persisted them.
2. **No git state inside `emit_*_artefact`.** The emitter is a pure
   IO leaf; it must not shell out to `git rev-parse`.

Consequences documented in prior audits:

- W6 FM6 — logged for `mio.coherence.directional`; "by design, no
  action".
- W11 F5 — same shape for `mio.coherence.redshift_binned.emit_
  redshift_coherence_artefact`; inherited the W6 FM6 resolution.

The handshake sequence relies on this capture ordering. The t₁ → t₄
arrow in §A44.2 is NOT a re-resolution — if HEAD has advanced between
t₁ and t₄, the SHA stored on the certificate remains the t₁-time SHA,
and the cross-check report's provenance references *that* certificate.
A44.6 documents the single exception (cache-replay path).

## A44.4 Artefact-first vs. in-memory hand-off

Two hand-off modes are allowed:

### A44.4.1 In-memory (same-process) hand-off

```python
# caller / orchestrator process
mio_cert = to_mio_certificate(probes, p_iso, resultant)   # t₁
emit_directional_coherence_artefact(out_path, probes)     # t₂ (optional)
htt_posterior = htt_phase_F.run_all(...)                  # t₃
report = ff_htt_mc_cross_check(                           # t₄
    mio_cert=mio_cert,
    htt_posterior=htt_posterior,
    seed=20260419,
)
assert_cross_check_consistent(report, rtol=5e-2)          # t₅
```

- t₂ is optional but recommended — the artefact is the durable
  audit trail even when the in-memory object is sufficient for t₄.
- No file IO on the `mio_cert` → harness edge.

### A44.4.2 Artefact-replay (cross-process or re-audit) hand-off

```python
# later session — re-audit or cross-process
mio_cert = MioCertificate.from_json(out_path.read_text())    # reads t₂ output
htt_posterior = htt_phase_F.run_all(...)                     # t₃ this session
report = ff_htt_mc_cross_check(mio_cert, htt_posterior, ...) # t₄
```

- `MioCertificate.git_commit` is whatever was stored at t₁ *in the
  original session*, not the current HEAD. This is the feature; the
  harness anchors against the certificate's intent.
- The harness MUST NOT overwrite the certificate's provenance fields
  when it reads an artefact back in. A patch that silently "refreshes"
  `git_commit` at t₄ is a G19 anti-pattern — it erases the separation
  between the run that produced the numbers and the run that audited
  them.

Both modes satisfy A44.2. Choice is caller preference; the TSC-06
current harness uses mode A44.4.1 because the producer and
cross-check run in the same pytest session.

## A44.5 Failure modes the sequence catches

1. **HTT reading MIO mid-flight.** If HTT Phase F consumed
   `MioCertificate` during posterior evaluation (between t₁ and t₃),
   the two "independent code paths" required by A34.2 rule 1 collapse
   — both become functions of the MIO output. The sequence forbids
   this by construction (t₃ has no MIO input arrow).
2. **Provenance-SHA shear.** If the certificate's `git_commit` were
   resolved at t₂ or t₄ rather than t₁, a commit landing between t₁
   and t₂ would stamp the artefact with a SHA that did *not* produce
   the numbers. W6 FM6's at-instantiation resolution prevents this.
3. **In-band certificate synthesis by the harness.** A harness that
   constructs a `MioCertificate` *inside* `ff_htt_mc_cross_check`
   (skipping t₁–t₂ entirely) bypasses the provenance record. The
   A41 checklist step 4 (acceptance test list) rejects this by
   requiring the harness signature to take `mio_cert` as input, not
   construct it.
4. **Posterior-update loop.** If the report from t₅ were passed back
   to HTT Phase F as a likelihood input, a feedback loop would form
   (HTT → MIO → harness → HTT). The `is_cross_check=True` frozen tag
   plus the type-level ban on `as_posterior_bundle()` blocks this;
   see A34.6 for the architectural consequences of relaxing this.
5. **Cache-replay drift.** If the cached MIO artefact drifts from the
   live producer (e.g. the user edited the certificate JSON by hand),
   re-audit at t₄ would feed stale numbers into the harness. A44.6
   documents the hash-chain guard.

## A44.6 Cache-replay guard

When the harness consumes a persisted MIO artefact (mode A44.4.2),
the following two hashes must be re-verified before t₄ proceeds:

- `MioCertificate.config_hash` — must match the caller's intended
  config (if the caller supplied one; if `None` on disk, the replay
  is accepted only with an explicit `allow_unsigned_config=True`
  caller flag — see W15 F3 / A43 for the digest upgrade path).
- `MioCertificate.input_data_hashes` — must hash-match the data
  bundle being fed into the HTT path at t₃. The harness otherwise
  refuses to proceed, raising a replay-drift error.

Neither check exists in the TSC-06 in-memory harness (mode A44.4.1)
because there is no cache edge to drift. The check lands with HJ-03
(first cross-process harness; see A41.6 / A42).

## A44.7 Extension vehicle — HJ-03 evidence anatomy

HJ-03 is the first cross-check that will exercise the cache-replay
path (A44.4.2) because HTT Phase F ln-B decomposition is expensive
and naturally cached. The A41 checklist step that lands HJ-03 must
therefore:

1. Follow the A34.7 structural steps (1)–(5) unchanged.
2. Add the A44.6 cache-replay guard to the harness signature.
3. Point the `MioCertificate(report_type="evidence_anatomy")` at
   the A42 payload schema once HTT Phase F freezes its
   `HTTEvidenceDecomposition` contract.
4. Regression-test the t₁ → t₂ → t₄ time-ordering with a
   deliberately-stale artefact (edit `git_commit` on disk, expect
   replay-drift error).

HJ-04 (FLRW tension) follows the same pattern with no cache edge
if the harness runs in-process; otherwise it inherits the same
A44.6 guard.

## A44.8 Relation to other appendices

- **A32** — field-by-field certificate schema. A44 is the temporal
  companion; A32 is the structural one.
- **A34** — cross-check protocol (five structural properties). A44
  specifies when each property is realised.
- **A41** — report_type extension checklist. A41.6 worked example
  (HJ-03 `"evidence_anatomy"`) is the first adopter of A44.
- **A42** — evidence anatomy stub. A42's "Inputs (planned)" table
  binds to t₃ in A44's sequence.
- **A43** — schema-hash digest. A43's digest-on-extension rule
  protects the certificate payload *structure*; A44 protects the
  call-edge *timing*. The two are complementary: a cross-check that
  imports a new digest (A43) but inverts the t₁ / t₃ / t₄ order
  (A44) still violates G19.
- **A40** — G19 architectural stance (the "why not merge"). A44 is
  the "how to call in order without merging" operational note.

## A44.9 No code landing in this appendix

A44 is specification-only. The TSC-06 reference implementation
already satisfies the sequence (mode A44.4.1; no cache edge). The
HJ-03 / HJ-04 checklists in A41 / A42 are the landing vehicles.

Re-audit trigger: if a future PR changes `MioCertificate`'s
`git_commit` resolution to be emission-time or read-time rather than
instantiation-time, A44.3 must be rewritten and every existing
cross-check harness audited for SHA-shear.
