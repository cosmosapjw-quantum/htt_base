# Phase-boundary audit — Independent Tracks Week 19

**Phase tag**: `IND_TRACKS_W19`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12+ continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 19 (W18 F1 / R1
`_hash_config` signature-anchor extension + W18 F2 / R2 §A46.{5,6}
expansion + one A4x dossier or MANU-CH03 extension).
Execution: W19D1 AUDIT(W18 F1): `_hash_config` signature-anchor
extension (D1), W19D3 AUDIT(W18 F2): §A46.{5,6} expansion (D3),
W19D5 DOS-A47 HJ-03 acceptance-test paste-replace protocol (D5),
this audit + NEXT_SESSION rotation (D7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.4 (G19 hard separation — A47 is the paste-replace slice of
A41's extension protocol, ring-fencing the HJ-03 PR against a mid-
flight signature/prose divergence);
v3 §10.2 (HTT ↔ MIO contract table — W19D1 extends the W18D1 anchor
with kwarg-evolution coverage; A47.8 formalises the two-anchor
coexistence post-HJ-03);
v3 §11.14.7 (dossier convention — A47 added under the A4x family;
§A46.5.1 + §A46.6 grammar expansion strengthens A46's failure-mode
coverage);
[A41.6](../dossier/A41_mio_report_type_extension_protocol.md)
(HJ-03 extension checklist — A47.5 is the test-block slice of
A41.6 step 4);
[A45.2 / A45.6](../dossier/A45_mio_cache_replay_drift.md) (cache-
replay pseudocode + paste-ready five-test block — W19D1 extends
the anchor guarding §A45.2; A47 is the paste-replace slice of
§A45.6);
[A46](../dossier/A46_three_lane_race_stress_test.md) (three-lane
race protocol — W19D3 adds §A46.5.1 failure-mode invocations +
§A46.6 HJ-03 triplet);
[A47](../dossier/A47_hj03_acceptance_test_paste_replace_protocol.md)
(HJ-03 acceptance-test paste-replace protocol — new, W19D5);
[W12 F1](AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md) +
[W14 F1](AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md) (cross-lane
contamination mitigations — §6 below records the W19 recurrence
check);
[W16 F1 addendum](AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md) +
[W17 audit §6](AUDIT_PHASE_IND_TRACKS_W17_2026-04-19.md) +
[W18 audit §6](AUDIT_PHASE_IND_TRACKS_W18_2026-04-19.md) (first
through third adversarial stress-tests of the scoped-pathspec
rule — W19 adds a fourth observation in §6 below).

**Baseline head**: `7a285b4` (`IND_TRACKS_W18: phase audit + next-
session prompt rotation`). **Zero intervening cross-lane commits
on `main` this phase** — all three W19 commits (`3f2129f`, `ad27ee5`,
`6d87082`) landed in single-lane sequence with no bass-lane or
gallery-lane commits arriving in the gaps. §6 W19 check #1 below
records this as the fourth distinct phase in which the scoped-
pathspec rule has been exercised without contamination; unlike
W16D7 / W17D3 / W18D5→W18D7, this phase did **not** observe a
concurrent cross-lane commit, so the exercise is a *non-adversarial*
stress-test of the rule (the rule held trivially because nothing
contested it).

**Commits this phase**:

- `W19D1` — `3f2129f` `W19D1: AUDIT(W18 F1): _hash_config
  signature-anchor extension`. One-file commit (+32 L) extending
  the existing W18D1 `test_hash_config_matches_a45_2_pseudocode_
  shape` in `bass_py/mio/tests/test_mio_certificate_generator.py`
  with an `inspect.signature(_hash_config).parameters` frozen-list
  assertion. The addition freezes both the parameter list
  (`("parts",)`) and the kind (`VAR_POSITIONAL`) so a future
  refactor that adds a keyword-only argument (e.g. `_hash_config
  (..., *, digest_length=16)` to introduce A43's schema-hash digest
  upgrade) is flagged at anchor time rather than silently passing.
  Assertion strengthening on the existing test — no +1 count delta.
  Closes W18 F1. Touched surface 1080 → 1080 (held); MIO contribution
  109 → 109 (held).
- `W19D3` — `ad27ee5` `W19D3: AUDIT(W18 F2): §A46.{5,6} expansion`.
  One-file dossier-prose commit (+47 / −1 L net) extending
  `docs/dossier/A46_three_lane_race_stress_test.md`. Two new
  paragraphs: §A46.5.1 "Common failure-mode invocations" names
  three known invocation shapes that bypass the W15D1 scoped-
  pathspec rule (missing trailing `--`, `git add -A` + `git commit
  -m`, `git commit -am`) with per-shape repair guidance pointing
  at memory `feedback_git_workflow.md`; §A46.6 adds the HJ-03
  three-file triplet (A42 evidence anatomy + §A41.6 step 6.5 +
  §A45.6 paste-ready block) naming concrete multi-path ind-tracks
  landings that could incidentally coincide with bass or gallery
  commits. Unblocked alternative to the A46.4 "steady-state three-
  lane phrasing" that is gated on a first three-lane observation
  (which did not occur in W19). Closes W18 F2. Touched surface
  unchanged (prose-only).
- `W19D5` — `6d87082` `W19D5: DOS-A47 HJ-03 acceptance-test paste-
  replace protocol`. One-file commit (+301 L) creating `docs/
  dossier/A47_hj03_acceptance_test_paste_replace_protocol.md`.
  Ten sections: §A47.1 Purpose, §A47.2 "Inputs the HJ-03 PR must
  have ready" (five prerequisites), §A47.3 Ownership and module
  location (`bass_py/mio/interface/cache_replay.py` rather than
  `bass_py/workspace/contracts/**`), §A47.4 Fixture-factory
  contract (`_make_cache_pair(hand_edit_config, drop_one_input_
  hash, unsigned_config)`), §A47.5 Per-test translation table
  ([1]/[2]/[4]/[5] verbatim, [3] per-signature if bundle shape
  deviates), §A47.6 "Signature-freeze and paste in the same PR"
  single-PR rule, §A47.7 Reviewer checklist (eight boxes), §A47.8
  Two-anchor coexistence (W18D1/W19D1 contract surface + A47.5
  test 1 harness surface), §A47.9 Related appendices, §A47.10
  Three re-audit triggers. Cross-refs A32 / A34 / A41 / A42 / A43 /
  A44 / A45 / A46. Caller's choice between the two W19D5 options
  (A47 new dossier vs MANU-CH03 extension) — A47 picked because
  it concretely unblocks the HJ-03 PR and builds directly on the
  §A41.6 step 6.5 + §A45.6 cross-link that W18D3 just landed.
  Touched surface unchanged (docs-only).
- `W19D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `htt/htt/tests/ htt/src/
htt/tsc/admissibility/ htt/tsc/diagnostics/ htt/tsc/charts/
htt/tsc/integration/ htt/workspace/ htt/mio/` (working-tree mirror;
see Note below) → **1080 passed, 0 failed, 4 skipped**. Week 19
delta vs Week 18 (1080 / 0 / 4): **0 test delta, 0 skip change, 0
regressions**. W19D1 is assertion-strengthening on an existing
test (no +1 count); W19D3 + W19D5 are docs-only (no test surface
touched).

**Note on working-tree layout** (audit-transparency, unchanged
from W18). Canonical paths in `HEAD` + every W19 commit are
`bass_py/...` matching the governing plan. The live working-tree
layout is `htt/...`, byte-identical to the `bass_py/` siblings
(the bass-lane `92cefa2` re-pointed the venv editable install in
W18). Pytest runs against `htt/...`; the single W19D1 test file
edit was mirrored into `htt/mio/tests/test_mio_certificate_
generator.py` for runtime verification only; the W19D3 + W19D5
dossier files live only at `docs/dossier/A4{6,7}_*.md` (not
mirrored — `docs/` has a single copy). Only the `bass_py/` /
`docs/` copies are tracked. The 1080 → 1080 hold confirms on the
mirror that the W19D1 signature-anchor strengthening passes and
no regression was introduced.

**TSC-standalone test count**: 602 passed (unchanged from W13–W18
— no TSC code change this week).

**MIO contribution**: 109 tests (unchanged vs W18; gate ≥ 47 met
with 62 to spare). No MIO test file gained or lost a test this
phase. Composition unchanged from W18 end-of-phase. Cross-check:
`venv/bin/python -m pytest htt/mio/ --collect-only -q | tail -1`
= `109 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY), 1 × `fig_certification_matrix` family
(W9), 1 × `test_bulkflow_likelihood.py:303` dynesty contract guard
(W10D1).

---

## 1. Audit target reconstruction

Three landings, three distinct audit targets — runtime anchor
strengthening (W19D1), dossier failure-mode + grammar expansion
(W19D3), and new paste-replace protocol dossier (W19D5). Two of
the three close a W18 residual finding; the third unblocks a
future cross-process landing (HJ-03) by concretising the §A45.6
test-block landing procedure.

### W19D1 — `_hash_config` signature-anchor extension (closes W18 F1)

- **Core claim**: W18D1's anchor asserted `__name__`, six-arg
  positional call shape (via the positional `_base_payload()`
  call), and 16-char lowercase-hex output. It did **not** assert
  anything about `inspect.signature(_hash_config).parameters`.
  A future refactor that adds a keyword-only argument (e.g.
  `*, digest_length=16` to introduce A43's schema-hash digest
  upgrade) still satisfies the existing assertions — positional
  call unchanged, name unchanged, output shape unchanged — but
  §A45.2's pseudocode would silently become incomplete (the
  HJ-03 author paste-copying §A45.6 would miss the new kwarg
  and lose A43's digest protection).
- **Algorithm**: import `inspect`; freeze
  `EXPECTED_PARAM_NAMES = ("parts",)` and
  `EXPECTED_PARAM_KINDS = (inspect.Parameter.VAR_POSITIONAL,)`
  as tuples; compare against
  `tuple(inspect.signature(_hash_config).parameters)` and
  `tuple(p.kind for p in params.values())` via exact-equality.
  Each failing assertion emits a message naming A45.2 / §A45.6
  / the relevant upgrade (A43 schema-hash digest) so the
  future breaking PR's author is pointed at the dossier edit
  required in the same PR.
- **Output**: 1 file changed (`bass_py/mio/tests/test_mio_
  certificate_generator.py`, +32 L), +2 assertions on an
  existing test; MIO contribution 109 → 109 (held); touched
  surface 1080 → 1080 (held).

### W19D3 — §A46.{5,6} expansion (closes W18 F2)

- **Core claim**: §A46.4's "first three-lane observation"
  phrasing is deferred-to-trigger; §A46.5 originally named only
  a generic "re-read the `git commit -- <paths>` command used"
  mitigation for the failure-pattern fingerprint; §A46.6 named
  A41.6 as a potential multi-path ind-tracks landing candidate
  without giving concrete file paths. The W18 F2 alternative
  path (since no three-lane observation landed) said to pick
  one of §A46.5 or §A46.6 expansion.
- **Algorithm**: dossier-prose only. §A46.5.1 "Common failure-
  mode invocations" adds three named invocation shapes
  (missing trailing `--`, `git add -A` + `git commit -m`,
  `git commit -am`) each with a symptom / failure-mode pair
  and a specific-shape reinforcement entry for memory
  `feedback_git_workflow.md`. §A46.6 HJ-03 triplet names the
  three-file paste-replace set (A42 evidence anatomy update,
  §A41.6 step 6.5, §A45.6 paste block) and notes that all
  three paths fall under the ind-tracks ownership prefix so
  A46.2 classification resolves to a single lane regardless of
  concurrent lane activity — preserving the single-lane
  guarantee for the HJ-03 commit.
- **Output**: 1 file changed (`docs/dossier/A46_three_lane_
  race_stress_test.md`, +46 / −1 L); no code change, no test
  change.

### W19D5 — DOS-A47 HJ-03 acceptance-test paste-replace protocol

- **Core claim**: §A45.6 gives a five-test paste-ready block;
  §A41.6 step 6.5 says "freeze the replay-harness signature
  before pasting"; nothing between them specifies which of
  the five tests translate verbatim, which need per-signature
  adaption, or what the fixture factory must look like. The
  HJ-03 author opens the PR facing a non-mechanical set of
  decisions; the reviewer can only check compliance after the
  fact.
- **Algorithm**: dossier-only (301 L, ten sections).
  §A47.2 enumerates the five inputs that must be landed or
  drafted before §A45.6 pastes (production
  `verify_cache_replay`, `CacheReplayDriftError` class,
  `htt_input_bundle` shape-freeze, fixture factory, clean
  HTT Phase F evidence-anatomy output). §A47.3 argues the
  harness lives in `bass_py/mio/interface/cache_replay.py`
  (MIO reader API, not `workspace/contracts/**` which is the
  data-shape SSOT). §A47.4 specifies the fixture-factory
  contract — private to the test module, uses
  `build_mio_certificate`, three kwargs each matching one
  test. §A47.5 gives the per-test translation table: tests
  [1], [2], [4], [5] verbatim; test [3] per-signature only
  if the HTT bundle shape deviates from §A45.2's default
  `.paths` iterable. §A47.6 formalises the single-PR rule
  (signature freeze + paste must share a commit, closing the
  W17 F2 prose-code drift gap permanently). §A47.7 gives a
  reviewer checklist of eight boxes. §A47.8 specifies the
  post-HJ-03 two-anchor coexistence (W18D1/W19D1 contract
  surface + A47.5 test 1 harness surface). §A47.10 lists
  three re-audit triggers (non-default bundle shape, A43
  lands first, module layout reorg).
- **Output**: 1 file changed (`docs/dossier/A47_hj03_
  acceptance_test_paste_replace_protocol.md`, +301 L, new
  file); no code change, no test change.

---

## 2. Contract / interface audit

| Surface | Before W19 | After W19 | Δ |
|---|---|---|---|
| `mio.interface.mio_certificate._hash_config` helper | W18D1 anchor asserts `__name__`, positional six-arg shape, 16-char lowercase-hex output, build-↔-replay parity | + `inspect.signature(...).parameters` frozen-list assertion on names (`("parts",)`) and kinds (`VAR_POSITIONAL`) (W19D1) | **+kwarg-evolution hedge** on the existing anchor |
| A46 three-lane race protocol | §A46.5 generic re-read mitigation; §A46.6 named A41.6 generically | + §A46.5.1 (three specific bypass invocations + per-shape repair pointer); §A46.6 HJ-03 three-file triplet (A42 + §A41.6 step 6.5 + §A45.6) (W19D3) | **+failure-mode specificity + grammar depth** |
| HJ-03 PR landing procedure | A41.6 7-step checklist + A45.6 5-test paste block + A41.6 step 6.5 signature-freeze gate; no step-by-step paste-replace specification | + A47 (301 L, 10 sections) specifying inputs, ownership, fixture factory, per-test translation table, single-PR rule, reviewer checklist, two-anchor coexistence, re-audit triggers (W19D5) | **+paste-replace protocol** (10-section dossier) |
| `MioCertificate` schema-hash digest mechanism (A43) | specified W15D3; test deferred to first extension | unchanged (test still deferred per §A43.3) | 0 |
| §0 first-order rules (commit hygiene) | status-gate (W13D1) + scoped pathspec (W15D1) | unchanged | 0 |
| All other surfaces (probe registry, A37 grammar, A36/A36a/A42/A44/A45 dossier text, MIO producers, TSC bridges, workspace contracts) | as-of W18 | unchanged | 0 |

All extensions are additive. No schema-hash rotation, no field
retype, no field removal, no producer-side runtime change. The
W19D1 strengthening joins an existing test (no +1 count);
W19D3 + W19D5 are documentation-only.

---

## 3. Phys-math audit

No physics or numerical-method change landed this phase. All three
landings are runtime-contract strengthening / dossier-surface
additions.

- **W19D1**: two `inspect.Parameter` equality assertions on an
  existing pure function's signature; `inspect` is a standard-
  library introspection module and returns deterministic values
  for a static function. No numerical claim.
- **W19D3**: prose-only. No numerical claim. §A46.5.1's three
  invocation shapes are all git-shell-command-level facts; the
  "non-finding-by-design" property of the scoped-pathspec rule is
  preserved (§A46.3 unchanged).
- **W19D5**: prose-only. No numerical claim. A47 is specification
  for a future PR; no code path is exercised by A47 itself.

---

## 4. Code path audit

- **W19D1**: pure-Python assertion addition to the existing W18D1
  test. Uses `inspect.signature(_hash_config).parameters` — a
  standard-library call that requires no additional imports at
  module scope (the test imports `inspect` locally). The frozen
  expected tuple is a module-local constant inside the test
  function (not a module-level `EXPECTED_*` variable, to keep the
  test self-contained per the W18D1 pattern). Test (1) the
  imports resolve cleanly; (2) the pytest run returns PASSED
  with the new assertions active; (3) the test fails loudly if
  `_hash_config` signature is altered (manually verified by
  inspecting the assertion shape).
- **W19D3**: one dossier file under `docs/dossier/`. No Python
  file touched; no test added. Markdown section numbering
  follows the §A46.N.M convention (new §A46.5.1 subsection added
  beneath §A46.5).
- **W19D5**: one new dossier file under `docs/dossier/`. No
  Python file touched; no test added. Markdown section numbering
  follows the §A47.N convention (ten top-level sections).
- No `bass_py/bass/*` file touched (lane discipline); no
  `plots/physics_gallery/` file touched (gallery-lane discipline);
  no `project/*` file touched (W8 FM1 /
  `feedback_project_local_only`). `git status --short` during
  each W19 commit was audited; pre-commit status gate (W13D1)
  applied; scoped-pathspec rule (W15D1) applied — every W19
  commit line ended with `-- <explicit-path>` matching the
  described file set exactly (single-file commits; §6 below).

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (no numerics landed this phase). |
| Tolerance sensitivity | **W19D1** — assertions are tuple-equality on `inspect.Parameter.kind` enum values + tuple-equality on `str` parameter names; no tolerance knob. |
| Underflow / overflow | n/a. |
| Conditioning | n/a. |
| Cache / state leakage | `_hash_config` is a pure function reading only its arguments; `inspect.signature` is a static introspection call with no side effects; test runs in pytest's default isolation. |
| Seed / reproducibility | n/a (deterministic introspection + deterministic pure function). |
| Baseline reproduction | `pytest htt/mio/` = 109/109 green in ~1.6 s; `pytest htt/htt/tests/ htt/src/ htt/tsc/{admissibility,diagnostics,charts,integration}/ htt/workspace/ htt/mio/` = 1080/0/4 in ~35 s. Two independent pytest runs during W19D7 returned identical counts. |
| OOD / misspecification | W19D1 does not exercise off-happy-path signature forms — those would require mutating `_hash_config` at runtime (which the test is anchoring *against*). The anchor is narrow by design: kwarg-addition, positional-reorder, kind-change of the existing single parameter. |

---

## 6. Ranked failure modes (P0–P3)

Per the NEXT_SESSION §2 Week 19 Day 7 directive this section MUST
include a §6 W12 F1 / W14 F1 cross-lane-contamination recurrence
check verifying the W15D1 scoped-commit rule was followed on every
W19 sha via `git show --stat`, plus the A46.2 lane-classification
check that determines whether the A46.4 three-lane observation row
fires.

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| W19 check #1 | **PASSED** | process (W12 F1 / W14 F1 recurrence) | `git show --stat 3f2129f ad27ee5 6d87082` returns: (1 file: `bass_py/mio/tests/test_mio_certificate_generator.py`) + (1 file: `docs/dossier/A46_three_lane_race_stress_test.md`) + (1 file: `docs/dossier/A47_hj03_acceptance_test_paste_replace_protocol.md`). Every path is on this lane's owned surface per A46.2 (ind-tracks: `bass_py/mio/**` + `docs/dossier/A*`); no `bass_py/bass/*`, no `plots/physics_gallery/*`, no `project/*`, no unrelated dossier paths. **Zero cross-lane commits landed on `main` during the W19 window** — `git log 7a285b4..HEAD` returns exactly the three W19 commits above. This is the first phase post-W16D7 where the scoped-pathspec rule held in a *single-lane* window; the rule's adversarial stress-tests now span four distinct phases (W16D7 concurrent-commit, W17D3 working-tree-drift, W18D5→W18D7 second concurrent-commit observation, W19 single-lane). | both the W13D1 status-gate and the W15D1 scoped-pathspec rule held; the single-lane nature of the W19 window meant no lane had a reason to interleave. | n/a — positive finding. | the audit-window contained **one lane** (ind-tracks), **not two or three** — A46.2 classification is unambiguously single-lane. The four-phase cumulative stress-test record should be read as "the rule has held across qualitatively different windows", not "adversarial pressure has been exhaustive". |
| W19 check #2 | **PASSED** | process (A46.2 applied to this window) | A46.2's lane-classification applied to the three W19-window shas (`3f2129f`, `ad27ee5`, `6d87082`) produces: ind-tracks = `{3f2129f, ad27ee5, 6d87082}`, bass = `{}`, gallery = `{}`. **One lane observed, not three.** The A46.4 audit row template is not triggered this phase; the steady-state §6 phrasing (this row) is the correct variant. W18 F2 / R2 §A46.4 steady-state phrasing accordingly remains gated on the first three-lane observation — W19D3 picked the unblocked alternative path (§A46.5.1 + §A46.6 expansion). | A46 specifies the protocol pre-observation; three phases now (W18, W19) have exercised §A46.2 on real windows and returned ≤ two lanes. | n/a — positive finding; A46.2 resolves unambiguously on three shas. | readers may notice that the three-lane window has still not materialised despite three phases of classification; this is consistent with the rule's design and does not indicate A46.4 is unnecessary — the first three-lane window will land eventually and A46.4 is the only paste-ready template when it does. |
| F1 | **P3** | docs (A47 first-use feedback) | A47.5's per-test translation table is specification-first; no HJ-03 PR has exercised it yet. When the first HJ-03 PR lands, a single test that deviates from the table's verbatim / per-signature split would indicate the table is incomplete or mis-calibrated. | A47.5 is a paste-replace prediction; validation requires real PR feedback. | when the HJ-03 PR lands, record in its own §6 audit row which of A47.5 [1]–[5] required adaption and update §A47.5 / §A47.10 re-audit trigger accordingly. | a future reader treats A47.5 as proven-out rather than spec-first; the first real PR surprise is misread as a bug in the PR rather than a spec gap. |
| F2 | **P3** | docs (§A46.6 HJ-03 triplet completeness) | §A46.6 names the three-file HJ-03 triplet (A42 evidence anatomy, §A41.6 step 6.5, §A45.6 paste block) but the actual HJ-03 PR will also touch `bass_py/mio/interface/cache_replay.py` + `bass_py/mio/tests/test_cache_replay.py` (new files per A47.3). The "three-file triplet" phrasing is dossier-accurate (dossier paths only) but PR-incomplete (code paths omitted). | §A46.6 was written with the dossier-surface axis in mind; the PR's full file list is broader. | optional W20+ follow-up: when HJ-03 lands, extend §A46.6 with a separate "code-surface file list" sub-bullet listing the two new `bass_py/mio/...` paths alongside the dossier triplet. Not blocking — the scoped-pathspec rule covers both code and docs paths uniformly. | a reader expects exactly three files in the HJ-03 PR diff and is confused by the five-to-six-file actual landing; the additional files don't signal cross-lane contamination, they are core code. |
| F3 | **P3** | coverage (W19D1 anchor + A47.8 coexistence) | W19D1's kwarg-evolution hedge is scoped to the current `_hash_config` signature. If the first keyword-only argument lands **before** A43's digest-version machinery is ready (e.g. a non-A43-related refactor adds `*, strict=True` for input validation), the frozen list must be updated in the same PR or the anchor blocks unrelated work. | the anchor is stricter than A45.2's pseudocode strictly requires (A45.2 only names the helper and the six-field positional form). | optional W20+ follow-up (cheap): add a docstring-comment at the top of `test_hash_config_matches_a45_2_pseudocode_shape` naming the three kinds of refactor that intentionally trigger the anchor (A43 digest upgrade, cache-replay strict-mode, any non-`*parts` signature change). | a PR author hits the anchor on a signature change that was deliberately decoupled from A45.2, reads the message, and re-edits A45.2 unnecessarily; a one-line docstring disambiguates the anchor's scope. |

**No P0 / P1 items found.** The W12 F1 / W14 F1 process pattern
did not recur this phase (W19 check #1 PASSED on a single-lane
window — fourth distinct phase exercising the scoped-pathspec
rule, first with zero concurrent cross-lane pressure). A46's
three-lane race scenario was *not* triggered (W19 check #2);
A46.4's first-observation row remains paste-ready for a future
phase. The three residual P3 items are soft surfaces — F1 is a
first-use feedback hedge for A47.5, F2 is a completeness note on
§A46.6's HJ-03 triplet, F3 is a scope-clarity note on the W19D1
anchor. None block W20 execution.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **n/a** — no numerical claim landed.
- **dimensional consistency**: **n/a** — string / enum / docs
  surface.
- **sign / normalization**: **n/a**.
- **positivity / admissibility**: **n/a** — no physics state
  touched.

**B. Code verifier**
- **contract satisfaction**: **passed** — `_hash_config` signature
  unchanged; the W19D1 assertion freezes the current shape
  (`("parts",)`, `VAR_POSITIONAL`) which matches the production
  signature at `bass_py/mio/interface/mio_certificate.py:44`. A46
  cross-refs resolve (grep: `A41.6` = 3 hits in A46.md now; `A45.6`
  = 2 hits; `feedback_git_workflow.md` = 2 hits; all positive). A47
  cross-refs resolve (all of A32 / A34 / A41 / A42 / A43 / A44 /
  A45 / A46 / §A46.6 HJ-03 triplet cited; A47.3's filepath
  candidate `bass_py/mio/interface/cache_replay.py` does not yet
  exist, as noted in §A47.3 itself).
- **actual code-path usage**: **passed** — W19D1 strengthens an
  existing test path (the W18D1 anchor runs unchanged on the
  clean-pass path; the two new `inspect` assertions run before
  the existing hex-output assertions). W19D3 / W19D5 add no code
  path.
- **regression risk**: **low** — touched-surface 1080 → 1080
  (0 delta), 0 failures, 0 skip-change. Full `pytest htt/mio/`
  109/109 in ~1.6 s. Full touched-surface pytest 1080/0/4 in
  ~35 s.
- **reproducibility**: **passed** — two independent pytest runs
  during W19D7 returned identical test counts.

**C. Numerical verifier**
- **tolerance robustness**: **passed** — W19D1 uses exact tuple
  equality on enum values and strings; no tolerance knob.
- **convergence / stability**: **n/a**.
- **baseline reproducibility**: **passed** — two independent
  pytest runs returned identical test counts; `_hash_config`
  signature is static across test invocations.
- **uncertainty / misspecification**: **n/a**.

**D. Dossier verifier**
- **A46 § numbering coherent**: **passed** — new §A46.5.1
  subsection fits inside §A46.5 cleanly; §A46.6 expansion adds
  to the existing paragraph without breaking its cross-references
  (A41.6 step 6.5 pointer still resolves; A44.3 / memory
  `feedback_git_workflow.md` cross-refs unchanged).
- **A47 cross-references resolve**: **passed** — all of A32,
  A34, A41, A41.6 step 6.5, A42, A42.5, A43, A44, A44.6, A45,
  A45.2, A45.6, A46, A46.2, A46.6 cited with section anchors;
  the filepath reference `bass_py/mio/interface/cache_replay.py`
  is explicitly marked as "candidate location" in §A47.3 since
  the file does not yet exist.
- **W18 F1 / F2 / F3 carry-forward closure**: **passed** — F1
  closed by W19D1 (kwarg-evolution hedge); F2 closed by W19D3
  (unblocked alternative: §A46.5.1 + §A46.6 expansion); F3 has
  a forward-looking reference in §A47.3 (A47.3 names the
  replay-harness module location that F3 would need to update
  on a reorg, partial mitigation; full repair still deferred as
  F3 is opportunistic per W18 audit §8). The §3 carry-forward
  table rows (in §8) record the closures; W19D7 NEXT_SESSION
  rotation drops them.
- **A47 + W19D1 anchor alignment**: **passed** — A47.8 explicitly
  names the W18D1/W19D1 anchor as the "contract surface" guard
  for `_hash_config`; A47.5 test (1) is the "harness surface"
  guard; both are non-overlapping and travel together per
  A47.6's single-PR rule.

---

## 8. Minimal repair plan

No P0 / P1 repair needed. Three opportunistic patches for W20+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | When the HJ-03 PR lands, record in its own §6 audit row which of A47.5 [1]–[5] required adaption and update §A47.5 / §A47.10 re-audit trigger accordingly. | no (P3 first-use feedback; HJ-03-trigger-gated). | F1 — A47.5 treated as proven rather than spec-first. | 0 (dossier edit only). | additive prose. |
| R2 | Extend §A46.6 with a "code-surface file list" sub-bullet when HJ-03 lands, naming the two new `bass_py/mio/interface/cache_replay.py` + `bass_py/mio/tests/test_cache_replay.py` paths alongside the dossier triplet. | no (P3 completeness; HJ-03-trigger-gated). | F2 — "three-file triplet" reading omits code paths. | 0. | additive prose. |
| R3 | Add a one-line docstring comment at the top of `test_hash_config_matches_a45_2_pseudocode_shape` naming the three refactor kinds that intentionally trigger the anchor (A43 digest upgrade, cache-replay strict-mode, any non-`*parts` signature change). | no (P3 scope clarity). | F3 — PR author mis-identifies the anchor's scope and edits A45.2 unnecessarily. | 0 (comment on existing test). | additive (0 count delta). |

All three are deferrable; none block W20 execution. R1 and R2 are
gated on the HJ-03 PR landing (external trigger — bass_py W10-02
K_ℓ atlas + HTT Phase F infrastructure). R3 is unblocked and could
be picked up opportunistically in any W20+ session.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `venv/bin/python -m pytest htt/mio/` →
  109/109 green in ~1.6 s; touched-surface `venv/bin/python -m
  pytest htt/htt/tests/ htt/src/ htt/tsc/{admissibility,diagnostics,
  charts,integration}/ htt/workspace/ htt/mio/` → 1080/0/4
  (unchanged from W18 baseline).
- **Edge / adversarial**:
  `test_hash_config_matches_a45_2_pseudocode_shape` (W18D1 anchor
  + W19D1 kwarg-evolution hedge — now asserts `__name__`, frozen
  parameter names tuple `("parts",)`, frozen parameter kinds
  tuple `(VAR_POSITIONAL,)`, six-arg positional call output shape,
  16-char lowercase-hex digest, and `cert.config_hash ==
  _hash_config(...)` build-↔-replay parity on the same payload).
- **Physics sanity**: n/a — no numerical claim landed; the
  strengthened W18D1/W19D1 test is a docs-↔-code anchor.
- **Regression**: full touched-surface `1080 / 0 / 4` (unchanged
  from W18 baseline); MIO contribution 109 unchanged; tsc
  standalone 602 unchanged.

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W19 세 landings (W18 F1 `_hash_
  config` signature-anchor extension + W18 F2 §A46.{5,6} expansion
  + A47 HJ-03 acceptance-test paste-replace protocol) 모두 기존
  contract ↔ code ↔ test 구조를 strengthen 하거나 새 dossier 를
  추가하는 additive 변경. MIO contribution 109 held; 전체 touched
  surface 1080 held (+2 assertions on existing test, 0 count delta).
  **W12 F1 / W14 F1 재발 없음** — §6 W19 check #1 PASSED; 세 W19
  commits 각각 단일 lane-owned path 하나만 포함; audit window 기간
  중 다른 lane 의 커밋 영집합 — 네 번째 phase 의 scoped-pathspec
  rule stress-test (이번엔 concurrent pressure 없음, 즉 *non-
  adversarial* 통과). 세 lane race (ind-tracks + bass + gallery)
  은 이번 phase 에 다시 triggered 되지 않음 — W19 check #2 는 1
  lane 관측, A46.4 first-observation row 템플릿 미사용 (W18 → W19
  연속 미사용).
- **지금 당장 구현/수정할 1개**: 없음. W19 gate 네 항목 전부 green;
  W20 active priorities 는 §8 R1–R3 중 하나 (R1/R2 는 HJ-03 PR
  trigger-gated; R3 는 unblocked 이므로 W20 caller 가 picker)
  또는 W19 F1/F2/F3 중 하나를 닫거나 신규 A4x dossier (A48?) /
  MANU-CH03 extension.
- **지금 손대면 안 되는 1개**: A43 digest 테스트의 즉시 착지
  (W15 R3 / W16 R3 / W17 R3 / W18 R3 / W19 R3 반복 — trigger 가
  아직 미도착; 현재 schema 에 freeze 하면 첫 확장 PR 이 paste-
  replace 를 강요받을 뿐 추가 catch 는 없음). HJ-03 production
  wiring 또한 htt W10-02 K_ℓ atlas 착지 전까지 금지 (governing
  plan §17.3 의존 대기 목록; 현재 주 BASS_PY_HTT_TSC_MIO_RESEARCH_
  PLAN.md v3 §17.3 유지).

---

## Week-19 final gate (per NEXT_SESSION §2 Week 19)

- [x] W18 F1 / W18 R1 `_hash_config` signature-anchor extension
      landed (W19D1 `3f2129f`; +2 assertions on existing test;
      no count delta; MIO contribution holds at 109).
- [x] W18 F2 / W18 R2 §A46.{5,6} expansion landed (W19D3 `ad27ee5`;
      +46 / −1 L; §A46.5.1 failure-mode invocations + §A46.6 HJ-03
      triplet grammar deepening; unblocked alternative to A46.4
      steady-state phrasing which remains gated on first three-
      lane observation).
- [x] One of A47 dossier / MANU-CH03 extension landed — **A47
      picked** (W19D5 `6d87082`; new dossier, 301 L, ten sections;
      HJ-03 acceptance-test paste-replace protocol; sits between
      §A41.6 step 6.5 + §A45.6 and specifies per-test translation
      table + fixture factory + reviewer checklist).
- [x] Phase-boundary audit log written (this file); §6 W12 F1 /
      W14 F1 recurrence check returns **PASSED** (`git show
      --stat` on the three W19 commits shows only this lane's
      owned paths; zero cross-lane commits landed during the
      window — fourth distinct phase exercising the scoped-
      pathspec rule, first with zero concurrent pressure;
      A46.4's three-lane template not triggered this phase —
      W19 check #2 shows one lane only, consecutive with W18's
      two-lane result).
- [x] No touched-surface regressions (1080 passed; unchanged vs
      W18; 0 failed; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W19` closes with
zero new P0/P1/P2 findings; three documented P3 residuals
(F1 / F2 / F3) feed the W20 repair plan, of which F3's docstring
clarification is the only unblocked option (R1 and R2 are HJ-03-
PR-gated).
