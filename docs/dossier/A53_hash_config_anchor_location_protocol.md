# A53 · `_hash_config` anchor-location protocol

**Appendix**: A53 (§11.14.14 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-20 W25D5 design dossier (documentation-only;
no code landing — this appendix specifies where the W18D1 / W19D1
`_hash_config` anchor lives when the MIO package layout changes,
and how to relocate it without opening a coverage gap).
**Status**: **steady-state, reorg-triggered** — the anchor already
exists today; A53 activates only when a future PR moves the helper,
splits the package root, or adds a second harness-level anchor that
must coexist with the contract-surface anchor.
**Governance anchors**:
[A45 MIO cache-replay drift protocol](A45_mio_cache_replay_drift.md)
(§A45.2 pseudocode names `_hash_config`; §A45.6 is the first
consumer-side paste block);
[A47 HJ-03 acceptance-test paste-replace protocol](A47_hj03_acceptance_test_paste_replace_protocol.md)
(§A47.6 single-PR rule; §A47.8 two-anchor coexistence);
[A48 MIO → HTT dependency-wait contract](A48_mio_htt_dependency_wait_contract.md)
(HJ-03 remains deferred, so the anchor-location rule must stay
ready without requiring code landing);
`htt/mio/tests/test_mio_certificate_generator.py`
(`test_hash_config_matches_a45_2_pseudocode_shape` — current
contract-surface anchor).
**Parent references**:
W18 F3 (coverage-location carry: the anchor's present home works,
but a future repo reorganisation would need an explicit move rule);
W19D1 (signature-frozen-list extension on the same anchor);
W20D1 (anchor-scope clarification in the docstring);
W24D5 A52 (lifecycle companion — A53 is narrower and code-surface
specific).

---

## A53.1 Purpose

The W18D1 anchor test currently lives in
`test_mio_certificate_generator.py`, imports `_hash_config`
through the installed MIO package, and asserts the helper's name,
signature shape, and 16-char lowercase-hex output. That location is
correct **today**, because the generator test file is the closest
existing MIO-lane surface to `build_mio_certificate`, the helper's
first producer-side consumer.

What W18 F3 left unspecified is the **relocation rule** if the code
surface moves. Examples:

* `mio.interface.mio_certificate` is split into
  `mio.interface.hashing` + `mio.interface.builder`;
* the repo's live package root changes again (`bass_py/mio/` →
  `htt/mio/` today; potentially another move later);
* HJ-03 lands a harness-level replay test file whose local factory
  now sits closer to the helper than the generator tests do.

A53 answers a narrow question: when that happens, **which file owns
the anchor, when do two anchors coexist, and what has to move in the
same PR?**

## A53.2 The anchor's invariant

The anchor is not "the test in this exact path". The invariant is:

1. There is always at least **one** MIO-lane test importing the
   production `_hash_config` helper by its live module path and
   checking the A45.2 contract surface (name, signature, output
   shape, and round-trip parity through `build_mio_certificate`).
2. That test lives in the **same review surface** as the helper's
   nearest producer-side caller, so a refactor author sees the
   contract guard while editing the helper-adjacent tests.
3. Any temporary duplication is explicit, short-lived, and justified
   as a coexistence window rather than an accidental fork.

The invariant is therefore **semantic adjacency**, not filename
stability.

## A53.3 Default home selection rule

Absent a reorganisation trigger, the default home remains the
current one:

* contract-surface anchor in
  `mio.tests.test_mio_certificate_generator`;
* helper under `mio.interface.mio_certificate`;
* behavioural replay anchor, once HJ-03 lands, in
  `mio.tests.test_cache_replay` per A47.8.

If a future PR moves `_hash_config` but does **not** change the
closest producer-side caller, keep the anchor in the generator test
file and update only the import path plus the docstring pointers.

If a future PR moves both the helper **and** the nearest producer-
side caller, move the anchor to the new producer-adjacent test file
in the same PR.

## A53.4 Relocation protocol

When a PR changes the helper's location or the package root, apply
the following steps in one scoped commit series:

1. Move or clone the anchor into the new producer-adjacent test
   module.
2. Update the import in the moved test to the helper's new live
   module path.
3. Re-run the W18D1/W19D1 assertions unchanged first; only then
   decide whether a true contract change also requires an A45 edit.
4. If the old test file remains in the tree, either delete the old
   anchor or reduce it to a one-line forwarding smoke test in the
   same PR. Never leave two full, divergent copies behind.
5. Update any dossier text that cites the old location:
   A45.2/A45.6 if the helper signature or consumer path changed,
   A47.8 if the coexistence story changed, and A48.2 if HJ-03's
   dependency row starts consuming the moved harness.

The relocation PR is incomplete if it moves code without also moving
the anchor surface that watches it.

## A53.5 Temporary coexistence rule

Two anchors may coexist temporarily in exactly two situations:

1. **Package/layout migration.** The old anchor continues to prove
   the pre-move import path still resolves while the new anchor
   proves the post-move path is wired.
2. **HJ-03 lands.** A47.8's harness-surface test is added while the
   original contract-surface anchor remains in place.

During coexistence:

* both anchors must assert the **same** `_hash_config` contract;
* the PR body names which anchor is contract-surface and which is
  harness-surface;
* the coexistence window ends in the same PR or the immediately
  following phase's planned cleanup commit.

Anything longer is no longer "coexistence"; it is an undocumented
fork of the guard surface.

## A53.6 What must not move

Some parts of the anchor are intentionally frozen across relocation:

* the helper name `_hash_config` unless A45.2 is edited in the same
  PR;
* the `inspect.signature(...).parameters == ("parts",)` +
  `VAR_POSITIONAL` check unless the PR is intentionally changing the
  A45.2 pseudocode contract;
* the parity assertion that
  `_hash_config(*six_fields) == build_mio_certificate(...).config_hash`;
* the MIO-lane ownership of the test file.

Moving the test is permitted. Relaxing these assertions without the
paired dossier edits is not.

## A53.7 Reviewer checklist

When reviewing a helper-move PR, confirm:

* the anchor still exists exactly once as a full contract-surface
  test after the PR's final commit;
* any temporary second anchor is explicitly labelled as coexistence;
* A45.2 / A47.8 were updated if the helper path, signature, or
  anchor story changed;
* the moved test still imports the **production** helper, not a
  local test stub;
* the W15D1 scoped-pathspec rule kept the move in the ind-tracks
  lane only.

## A53.8 Re-audit triggers

A53 must be revisited if any of the following occurs:

* `_hash_config` is renamed, split, or wrapped by a new public
  helper;
* A43's digest-upgrade path changes the helper signature enough that
  the existing W19D1 frozen-list assertion is no longer the right
  anchor;
* HJ-03 or a later harness introduces a third stable anchor and
  A47.8's "two-anchor coexistence" becomes a persistent
  three-surface story;
* the repo's package root changes again and the current
  `htt/mio/tests/...` location stops being producer-adjacent.

## A53.9 Relation to other appendices

* **A45** remains the authoritative spec for what `_hash_config`
  means. A53 says where the anchor lives, not what the helper does.
* **A47** remains authoritative for the harness-surface replay
  tests. A53 only governs the contract-surface anchor and the
  coexistence boundary.
* **A48** remains the SSOT for when HJ-03 actually lands. A53 is
  deliberately pre-trigger documentation.
