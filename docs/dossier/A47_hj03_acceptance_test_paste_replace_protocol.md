# A47 · HJ-03 acceptance-test paste-replace protocol

**Appendix**: A47 (§11.14.8 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W19D5 design dossier (documentation-only;
no code landing — the code lands with HJ-03 itself, see §A47.7).
**Status**: **deferred-to-trigger** — the protocol is mechanical
and paste-ready; it activates when bass_py W10-02 K_ℓ atlas +
HTT Phase F posterior-decomposition infrastructure land and the
HJ-03 author opens the evidence-anatomy PR (§A42.5 + §A45.3).
**Governance anchors**:
[A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md)
(§A41.6 step 6.5 — freeze the replay-harness signature before paste);
[A45 MIO cache-replay drift protocol](A45_mio_cache_replay_drift.md)
(§A45.6 — five-test paste block; §A45.2 — harness pseudocode);
[A42 evidence anatomy stub](A42_evidence_anatomy.md)
(§A42.5 — HJ-03 is the first cache-crossing consumer);
[A44 MIO ↔ HTT handshake sequence](A44_mio_htt_handshake_sequence.md)
(§A44.4.2 — artefact-replay mode; §A44.6 — guard-invocation site);
[A46 three-lane race stress-test protocol](A46_three_lane_race_stress_test.md)
(§A46.6 — HJ-03 three-file ind-tracks triplet).
**Parent references**:
W17 F2 / W18D3 (A45.6 ↔ A41.6 harness-signature cross-link);
W18D1 (`test_hash_config_matches_a45_2_pseudocode_shape` is the
contract-surface twin of A47's proposed MIO-surface tests);
W19D1 (kwarg-evolution hedge on the W18D1 anchor);
W19D3 (§A46.5.1 failure-mode invocations — relevant if the HJ-03
multi-file landing brushes up against a concurrent bass-lane
commit window).

---

## A47.1 Purpose

§A45.6 defines a five-test block and §A41.6 step 6.5 says "freeze
the replay-harness signature before pasting". A47 sits between
them: it specifies, test-by-test, **which tests translate
verbatim** and **which require signature-level adaption**, what
the fixture factory has to deliver, and what the HJ-03 PR reviewer
should check in each test. The goal is that the HJ-03 author opens
the PR with §A45.6 as a ready-to-land commit, not as a template to
reinterpret; and that the reviewer can step through A47's checklist
without re-reading the whole A41/A45 dossier chain.

A47 also formalises the "signature-freeze in the same PR as paste-
replace" rule: the two must travel together so a future reader
diffing §A45.6 against the landed test file sees a single commit,
not an in-flight mismatch across two PRs.

## A47.2 Inputs the HJ-03 PR must have ready

Before §A45.6 can be paste-replaced, the PR author must have
landed or drafted:

1. **The production `verify_cache_replay` helper.** Lives in the
   module that owns the replay harness — candidate location
   `bass_py/mio/interface/cache_replay.py` (see §A47.8 for the
   layout decision); exposes the two-argument signature from
   §A45.2 (`mio_cert`, `htt_input_bundle`, `*, allow_unsigned_config
   = False`). Raises `CacheReplayDriftError` with the two prefix
   strings §A45.2 names.
2. **A `CacheReplayDriftError` class.** Subclass of `RuntimeError`
   or a dedicated error base; lives adjacent to the helper; does
   not leak posterior content (G19 hard separation per §A40 / v3
   §4.5.4).
3. **A `htt_input_bundle` shape-freeze** matching §A41.6 step 6.5.
   The default shape is an object carrying a `.paths` iterable of
   `Path` objects whose sha256 digests collectively equal the
   certificate's `input_data_hashes` field; §A45.6 test (3) and
   test (5) depend on this. Any shape change (e.g. `.digests`
   tuple, `replay_context` wrapper) requires the per-item adaption
   table in §A47.5 — not a block-level rewrite.
4. **A fixture factory** that can synthesise a `(MioCertificate,
   htt_input_bundle)` pair on demand; §A47.4 specifies the minimum
   factory contract.
5. **A clean HTT Phase F evidence-anatomy output** (or a stub that
   mimics its shape) so the clean-pass-through test can exercise
   the full call path without relying on production HTT Phase F
   running in CI. §A42.5's HTT Phase F interface list is
   authoritative.

If any of 1–5 is missing, the HJ-03 PR is premature; the §A45.6
paste will either fail to import (error 1), fail to raise with the
expected message prefix (errors 2, 3), or pass trivially without
exercising the guard (errors 4, 5).

## A47.3 Ownership and module location

A47 presumes the replay harness lives **inside** the MIO package
(`bass_py/mio/**`) rather than in `bass_py/workspace/contracts/**`.
Rationale:

- `workspace/contracts` is the SSOT for *data-shape* invariants
  (frozen dataclass, field types, forbidden-posterior G19
  enforcement). The W17D1 microtest
  `test_git_commit_is_capture_time_not_lazy` lives there because
  it polices an invariant of the dataclass itself.
- The replay harness is a *behaviour* (hash re-computation,
  input-bundle digest matching) that consumes the dataclass plus
  external state (HTT bundle paths). It belongs to the MIO lane's
  reader/consumer API, not the contract.

Concretely: the helper lives at `bass_py/mio/interface/cache_replay.py`;
the tests at `bass_py/mio/tests/test_cache_replay.py`. This
places the HJ-03 replay code alongside the HJ-03 producer
(`bass_py/mio/decomposition/evidence_anatomy.py` per A41.6 step 2)
and under the same lane ownership for the per-phase audits.

## A47.4 Fixture factory contract

The §A45.6 test block presupposes a factory callable of the shape:

```python
def _make_cache_pair(
    *,
    hand_edit_config: bool = False,
    drop_one_input_hash: bool = False,
    unsigned_config: bool = False,
) -> tuple[MioCertificate, HTTInputBundle]:
    ...
```

Each keyword corresponds exactly to one A45.6 test; the factory
does the minimum payload setup the test needs. Defaults produce a
clean pair that test (1) consumes unchanged.

The factory **must** use `build_mio_certificate` from
`mio.interface.mio_certificate` (not construct a `MioCertificate`
by hand), so the `config_hash` and `input_data_hashes` are
populated by the production path, not by the test. Rationale:
A45.2's guard is defined relative to `_hash_config`'s output
shape (W18D1 anchor freezes that shape); a test that sidesteps
`build_mio_certificate` would silently pass even under a
`_hash_config` regression that the W18D1 anchor catches.

The fixture factory lives in the same test module as the §A45.6
tests (module-scoped private helper), **not** in a separate
`conftest.py`, because the factory's keyword-knob set is HJ-03-
specific and would confuse cross-lane consumers. A per-HJ factory
may be lifted to `conftest.py` later if HJ-04 / HJ-05-full reuse
the same shape.

## A47.5 Per-test translation table

The §A45.6 block contains five tests. This table pairs each with
its verbatim / per-signature-adaption status and the fixture-
factory knob it consumes.

| §A45.6 test | Translation | Fixture knob | Expected failure mode |
|---|---|---|---|
| (1) `test_verify_cache_replay_clean_passes_through` | **verbatim** | defaults (all knobs False) | `verify_cache_replay(...) is None`; if it raises, §A45.2 algorithm is mis-implemented on the clean path |
| (2) `test_verify_cache_replay_hand_edited_payload_raises` | **verbatim** | `hand_edit_config=True` | `CacheReplayDriftError` raised, message starts with `"config drift:"` |
| (3) `test_verify_cache_replay_missing_input_hash_raises` | **per-signature** — field-name adaption if `.paths` → `.digests` | `drop_one_input_hash=True` | `CacheReplayDriftError`, message starts with `"input-data drift:"` |
| (4) `test_verify_cache_replay_unsigned_requires_opt_in` | **verbatim** | `unsigned_config=True` | defaults raise; `allow_unsigned_config=True` returns None + caveat appended to replay report |
| (5) `test_verify_cache_replay_does_not_touch_git_commit` | **verbatim** | defaults | monkeypatched `subprocess.run` is never invoked; parity microtest with W17D1 |

Tests (1), (2), (4), (5) translate **verbatim**: the §A45.6 block
pastes byte-for-byte into `test_cache_replay.py`. Test (3) is the
only one that may need per-signature adaption, because its setup
reaches into the HTT input bundle's field layout; the adaption is
a single kwarg change on the factory (`drop_one_input_hash`) and
a single assertion on the bundle shape, not a rewrite. If HJ-03
freezes the bundle signature to the §A45.2 default (`.paths`
iterable), test (3) is also verbatim.

The five tests together satisfy A45.2's §A45.6 gate. No test in
the block overlaps with the W18D1 contract-surface anchor, so the
W18D1 test continues to serve its role (catch `_hash_config`
drift at the dataclass-generator surface) while A47.5's tests
serve their role (catch replay drift at the HJ-03 harness surface).

## A47.6 Signature-freeze-and-paste single-PR rule

The HJ-03 PR **MUST** land the signature freeze (§A41.6 step 6.5
addendum, §A45.6 harness-signature note) in the same commit as
the tests that consume it. Rationale:

- A mid-flight state where §A45.6's prose describes a signature
  that differs from `verify_cache_replay`'s live definition is
  exactly the W17 F2 failure mode that W18D3 repaired (prose-code
  drift on the replay-harness signature). Splitting the freeze
  into a separate PR re-opens that gap.
- The audit-trail search (`grep "A45.6" docs/dossier/` +
  `grep "verify_cache_replay" bass_py/mio/**/*.py`) must return a
  consistent pair in every commit post-HJ-03. A two-PR split
  breaks that invariant for the intermediate commit.

Mechanically: the PR diff contains exactly
`bass_py/mio/interface/cache_replay.py` (new file),
`bass_py/mio/tests/test_cache_replay.py` (new file), plus any
`docs/dossier/A45_mio_cache_replay_drift.md` / `A41_mio_report_type_
extension_protocol.md` edits if the signature changed from §A45.2's
default. The A47 dossier itself is not edited in the HJ-03 PR
unless §A47.5's per-signature adaption row needs updating.

## A47.7 Reviewer checklist

When reviewing the HJ-03 PR, confirm:

- [ ] `verify_cache_replay` module location matches A47.3
      (`bass_py/mio/interface/cache_replay.py`). If not, a
      deviation note appears in the PR body justifying the move.
- [ ] `CacheReplayDriftError` is a subclass of a well-defined
      error base; its message prefixes match §A45.2's
      `"config drift:"` / `"input-data drift:"` pair.
- [ ] `_make_cache_pair` factory is module-private (leading
      underscore), uses `build_mio_certificate`, and exposes the
      three keyword knobs in §A47.4.
- [ ] Five §A45.6 tests present, named exactly per the per-test
      translation table, and test (5) monkeypatches `subprocess.run`
      (W17D1 parity).
- [ ] `config_hash` round-trips through `_hash_config` (W18D1
      anchor parity — the factory's clean pair should satisfy
      `_hash_config(*six_fields) == cert.config_hash`).
- [ ] If `htt_input_bundle` shape deviates from §A45.2 default,
      §A45.6 is edited in the same commit to reflect the new
      shape, and test (3)'s adaption row in §A47.5 is updated.
- [ ] No test leaks posterior content from the HTT bundle into the
      assertion strings (G19 hard separation).
- [ ] The §6 audit check for the HJ-03 landing phase confirms the
      commit is scoped to ind-tracks (A46.2 lane classification);
      §A46.6's HJ-03 triplet guarantee should hold by construction.

Any un-ticked box is a blocker; the PR does not land with partial
compliance.

## A47.8 Two-anchor coexistence (post-HJ-03, pre-A43-digest)

Once HJ-03 lands, two anchors guard `_hash_config`:

1. `bass_py/mio/tests/test_mio_certificate_generator.py::
   test_hash_config_matches_a45_2_pseudocode_shape` (W18D1 +
   W19D1 signature frozen-list) — **contract surface**, exercises
   the helper directly and freezes its name / signature / output
   shape against §A45.2.
2. `bass_py/mio/tests/test_cache_replay.py::test_verify_cache_
   replay_clean_passes_through` (A47.5 test 1) — **harness
   surface**, exercises the helper indirectly via
   `verify_cache_replay` on a freshly-built pair.

Both anchors live in the MIO lane; both travel with the W15D1
scoped-pathspec rule on every phase-boundary audit; neither
subsumes the other. A future refactor that relocates the helper
(e.g. the A43 schema-hash digest upgrade extends `_hash_config`
with a `*, digest_length=32` kwarg) must thread through both: the
W19D1 frozen-list assertion flags the kwarg addition at anchor
time, and the A47.5 clean-pass-through test flags any
behavioural regression the kwarg introduces. The two anchors
together constitute the full `_hash_config` coverage per A45's
content-hash axis until A43's digest-version machinery lands.

## A47.9 Related appendices

- **A32** — MioCertificate schema. The factory's clean pair is an
  instance of this schema; no A32 field changes are induced by
  A47.
- **A34** — G19 cross-check protocol. The §A45.6 block lands in
  the same PR as the A34.3 cross-check channel entry for HJ-03;
  A47's paste-replace protocol is silent on A34 updates (those
  follow A41.6 step 7).
- **A41** — report_type extension protocol. A47 is the
  "test-block" slice of A41's seven-step mechanical checklist;
  A41.6 step 4 (acceptance tests) points at §A45.6, and A45.6
  points here.
- **A42** — HJ-03 evidence anatomy. A42.5's HTT Phase F interface
  list is the shape reference for A47.2 point 5 (clean HTT input).
- **A43** — schema-hash digest. If A43 lands before HJ-03, the
  W19D1 frozen-list assertion changes expected value
  (`("parts", "digest_length")` with mixed kinds); A47.8 then
  reads "three-anchor coexistence" and §A45.6 test (4) picks up a
  second branch for the signed vs unsigned variants.
- **A44** — handshake sequence. A47's signature-freeze-and-paste
  rule is the A44.6 invocation-site's precondition: the guard must
  exist, with the expected signature, before t₄ can call it.
- **A45** — cache-replay drift protocol. Parent appendix; A47
  does not restate A45's algorithm, it only specifies how to land
  §A45.6's test block.
- **A46** — three-lane race stress-test. §A46.6's HJ-03 triplet
  is the audit-time companion to A47's PR-time checklist; both
  ring-fence the HJ-03 commit against cross-lane contamination.

## A47.10 Re-audit trigger

A47 must be rewritten if any of the following happens:

- **HJ-03 PR lands with a non-default `htt_input_bundle` shape**
  and the per-signature adaption applies to more than one test
  (§A47.5 row (3)). A47 then gains a full per-signature table
  rather than a single flagged row.
- **A43 schema-hash digest lands first.** A47.8's "two-anchor
  coexistence" becomes "three-anchor coexistence"; the W19D1
  frozen-list assertion's expected value needs updating in the
  same PR.
- **Module layout reorganisation** (A41.6 `bass_py/mio/decomposition/
  evidence_anatomy.py` is split into two, or the interface module
  is relocated under a new package root). §A47.3's location
  presumption then drifts from reality; the HJ-03 PR reviewer
  checklist needs a new location row.
- **`CacheReplayDriftError` gains a third message prefix beyond
  `"config drift:"` / `"input-data drift:"`** (W21D3 / W19-carry).
  §A45.2 currently has three raise sites: step 2 emits
  `"unsigned certificate; ..."` (a *setup-phase* guard, not a
  drift prefix); steps 3 + 4 emit the two drift prefixes the
  §A47.7 reviewer checklist + §A47.5 tests (2)/(3) pin. A future
  edit that adds a third drift-prefix raise site (e.g.
  `"schema drift:"` for the A43 digest-upgrade path, or
  `"git-commit drift:"` for an A44.3 contract extension) silently
  passes the existing five-test block — no test asserts the
  *complete* prefix set, only the two known prefixes per row. A47
  then needs (a) a new §A47.5 row pinning the new prefix, (b) a
  reviewer-checklist update naming the prefix triple/quadruple,
  and (c) a paired §A45.2 algorithm step describing when the new
  raise fires. Cross-references: §A45.2 step 2 / step 4 (raise-
  site shape), §A47.5 row (2) / row (3) (prefix-text pinning),
  §A47.7 bullet 2 (reviewer checklist's `"config drift:"` /
  `"input-data drift:"` pair).

Until one of these triggers fires, A47 is stable and its
paste-replace protocol remains the authoritative route for
landing §A45.6.
