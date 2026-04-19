# Phase-boundary audit — Independent Tracks Week 20

**Phase tag**: `IND_TRACKS_W20`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12+ continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 20 (W19 F3 / R3
`_hash_config` anchor scope-clarity docstring + one W19 F-residual
close OR W18-carry alternative + one A4x dossier / §A46 expansion /
MANU-CH03 extension).
Execution: W20D1 AUDIT(W19 F3): `_hash_config` anchor scope-clarity
docstring (D1), W20D3 AUDIT(W19 R-carry): §A46.3 concrete git
commands (D3), W20D5 DOS-A48 MIO → HTT dependency-wait contract
(D5), this audit + NEXT_SESSION rotation (D7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.4 (G19 hard separation — A48 consolidates the "deferred
to bass_py promotion" surface into one ledger, supersedes the
partial list in v3 §17.3);
v3 §10.2 (HTT ↔ MIO contract table — W20D1 docstring clarifies
the scope of the W19D1 kwarg-evolution hedge; A48.2 is the
calendar ledger that pins when the A41.6 checklist fires);
v3 §11.14.7 / v3 §11.14.9 (dossier convention — A48 enters under
the A4x family at §11.14.9; §A46.3 concrete-command expansion
completes the three-terminal adversarial recipe);
[A41.6](../dossier/A41_mio_report_type_extension_protocol.md)
(HJ-03 extension checklist — A48.2 row "HJ-03" dereferences this
checklist when the upstream milestone lands);
[A45.2 / A45.6](../dossier/A45_mio_cache_replay_drift.md) (cache-
replay pseudocode + paste-ready five-test block — W20D1 docstring
scopes the W19D1 anchor's interaction with §A45.2);
[A46](../dossier/A46_three_lane_race_stress_test.md) (three-lane
race protocol — W20D3 adds paste-ready shell block to §A46.3);
[A47](../dossier/A47_hj03_acceptance_test_paste_replace_protocol.md)
(HJ-03 acceptance-test paste-replace protocol — A48.3 row "HJ-03"
names A47 as the landing-PR shape);
[A48](../dossier/A48_mio_htt_dependency_wait_contract.md)
(MIO → HTT dependency-wait contract — new, W20D5);
[W12 F1](AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md) +
[W14 F1](AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md) (cross-lane
contamination mitigations — §6 below records the W20 recurrence
check);
[W16 F1 addendum](AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md) +
[W17 audit §6](AUDIT_PHASE_IND_TRACKS_W17_2026-04-19.md) +
[W18 audit §6](AUDIT_PHASE_IND_TRACKS_W18_2026-04-19.md) +
[W19 audit §6 + post-audit addendum](AUDIT_PHASE_IND_TRACKS_W19_2026-04-19.md)
(first through fourth adversarial stress-tests of the scoped-
pathspec rule — W20 adds a fifth observation in §6 below).

**Baseline head**: `184b06c` (`IND_TRACKS_W19 (post-audit
addendum): W19 F4 A46.2 window re-classification`).

**Commits this phase**:

- `W20D1` — `9fb1407` `W20D1: AUDIT(W19 F3): _hash_config anchor
  scope-clarity docstring`. One-file commit (+15 L) inside
  `bass_py/mio/tests/test_mio_certificate_generator.py`. Adds an
  "Anchor scope (W19 F3 / W20D1)" paragraph inside the existing
  `test_hash_config_matches_a45_2_pseudocode_shape` docstring
  naming the three refactor kinds that intentionally trigger the
  W19D1 frozen-list assertion: (i) A43 schema-hash digest upgrade
  — REQUIRES paired §A45.2 edit in the same PR; (ii) cache-replay
  strict-mode flag added independently of A43 — MAY require an
  §A45.2 edit if the pseudocode forwards the flag; (iii) any
  non-`*parts` signature shape change — caller's judgement per
  §A47.6 single-PR rule. Pure documentation clarity; no assertion
  change; no production-code change. Closes W19 F3. Touched
  surface 1080 → 1080 (held); MIO contribution 109 → 109 (held).
- `W20D3` — `5391dc8` `W20D3: AUDIT(W19 R-carry): §A46.3 concrete
  git commands`. One-file dossier-prose commit (+24 L) inside
  `docs/dossier/A46_three_lane_race_stress_test.md`. Adds a
  paste-ready shell block to §A46.3 spelling out the exact
  `git add` / `git status --short` / `git commit -- <path>` per
  terminal, plus the post-arrival `git log --oneline -3` +
  `git show --stat <sha>` verification. Each terminal uses a
  representative path under its lane's ownership prefix (A46.2):
  Terminal A `bass_py/mio/tests/test_foo.py` (ind-tracks);
  Terminal B `bass_py/bass/hierarchy/bar.py` (bass); Terminal C
  `plots/physics_gallery/01_species_background/baz.png` (gallery).
  Unblocked alternative to W19 F1 / F2 closure (both HJ-03-PR-
  gated; no HJ-03 PR landed in W20). Touched surface unchanged
  (docs-only).
- `W20D5` — `4d7a3ed` `W20D5: DOS-A48 MIO → HTT dependency-wait
  contract`. One-file commit (+157 L) creating
  `docs/dossier/A48_mio_htt_dependency_wait_contract.md`. Six
  sections: §A48.1 Purpose, §A48.2 Dependency matrix (eight-row
  table: HJ-01, HJ-03, HJ-04, HJ-05-full, MANU-CH12 §§12.1 / 12.4
  / 12.5 / 12.8, A43 digest test), §A48.3 Per-row promotion
  conditions, §A48.4 Audit §8 ledger mechanics (R<n> rows
  dereference into §A48.2 rows), §A48.5 Relation to other
  appendices, §A48.6 No code landing and steady-state ledger
  discipline. Cross-refs A32 / A34 / A41 / A42 / A44 / A45 / A47 /
  v3 §17.3 (A48 supersedes the partial list there). Caller's
  choice (option 2 of the three W20D5 A48 candidates from
  NEXT_SESSION §2 Week 20 Days 5–6) — option 1 (anchor-location
  protocol) and option 3 (cross-check channel catalogue extension)
  remain unpicked for W21+. Touched surface unchanged (docs-only).
- `W20D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `htt/htt/tests/ htt/src/
htt/tsc/admissibility/ htt/tsc/diagnostics/ htt/tsc/charts/
htt/tsc/integration/ htt/workspace/ htt/mio/` (working-tree mirror;
see Note below) → **1080 passed, 0 failed, 4 skipped**. Week 20
delta vs Week 19 (1080 / 0 / 4): **0 test delta, 0 skip change,
0 regressions**. W20D1 is docstring-only on an existing test (no
+1 count); W20D3 + W20D5 are docs-only (no test surface touched).

**Note on working-tree layout** (audit-transparency, unchanged
from W18–W19). Canonical paths in `HEAD` + every W20 commit are
`bass_py/...` (for the W20D1 test file) / `docs/...` (for W20D3
+ W20D5). The live working-tree layout for Python files is
`htt/...`, byte-identical to the `bass_py/` siblings. Pytest
runs against `htt/...`; the single W20D1 test file edit was
mirrored into `htt/mio/tests/test_mio_certificate_generator.py`
for runtime verification only; the W20D3 + W20D5 dossier files
live only at `docs/dossier/A4{6,8}_*.md` (not mirrored — `docs/`
has a single copy). Only the `bass_py/` / `docs/` copies are
tracked. The 1080 → 1080 hold confirms on the mirror that the
W20D1 docstring addition introduces no test-collection change
and no regression.

**TSC-standalone test count**: 602 passed (unchanged from W13–W19
— no TSC code change this week).

**MIO contribution**: 109 tests (unchanged vs W19; gate ≥ 47 met
with 62 to spare). No MIO test file gained or lost a test this
phase. Composition unchanged from W19 end-of-phase. Cross-check:
`venv/bin/python -m pytest htt/mio/ --collect-only -q | tail -1`
= `109 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY), 1 × `fig_certification_matrix` family
(W9), 1 × `test_bulkflow_likelihood.py:303` dynesty contract guard
(W10D1).

---

## 1. Audit target reconstruction

Three landings, three distinct audit targets — runtime-docstring
scope clarity (W20D1), dossier failure-mode reproducibility
expansion (W20D3), and new dependency-wait ledger dossier (W20D5).
One closes a W19 residual (W19 F3); one provides a paste-ready
shell block for the as-yet-unobserved three-lane race; one
consolidates the scattered MIO → HTT dependency-wait surface.

### W20D1 — `_hash_config` anchor scope-clarity docstring (closes W19 F3)

- **Core claim**: W19D1's `inspect.signature(_hash_config).
  parameters` frozen-list assertion is stricter than §A45.2's
  pseudocode strictly requires. A reader who hits the anchor on a
  signature change decoupled from §A45.2 (e.g. a non-A43 refactor
  that adds `*, strict=True` for input validation) may misread
  the assertion message and edit §A45.2 unnecessarily. The anchor
  message names §A45.2 because that is the most common fix site,
  not the only one.
- **Algorithm**: docstring-only edit. Add a paragraph inside the
  existing `test_hash_config_matches_a45_2_pseudocode_shape`
  function docstring naming three refactor kinds that
  intentionally trigger the frozen-list assertion. Kind (i) — A43
  schema-hash digest upgrade — REQUIRES a paired §A45.2 edit;
  kinds (ii) cache-replay strict-mode flag and (iii) any
  non-`*parts` signature shape change — MAY require an §A45.2
  edit, caller's judgement per §A47.6 single-PR rule. The docstring
  lives inside the function (not a module-level comment) so it
  travels with the test under any future relocation (W19 F3
  location hedge).
- **Output**: 1 file changed (`bass_py/mio/tests/test_mio_
  certificate_generator.py`, +15 L), docstring-only; no assertion
  change; MIO contribution 109 → 109 (held); touched surface 1080
  → 1080 (held).

### W20D3 — §A46.3 concrete git commands (W19 R-carry unblocked alternative)

- **Core claim**: §A46.3's three-terminal adversarial recipe was
  specification-prose only; steps 1–4 described what each
  terminal does but not what commands to type. A reviewer
  reproducing the race post-observation had to translate each
  step into a shell command in the moment, inviting invocation
  drift (e.g. accidentally using `git commit -am` which §A46.5.1
  flags as non-compliant). The W19 F1 / F2 items were HJ-03-PR-
  gated; the W18/W19 plan §2 explicitly named §A46.3 command-
  level expansion as an unblocked alternative.
- **Algorithm**: dossier-prose only. Add a paste-ready shell
  block (+24 L) after §A46.3 step 4. Three terminals each
  execute `git add <own-lane-path>` → `git status --short` →
  `git commit -m "…" -- <own-lane-path>`, representing the
  three ownership lanes (A46.2): ind-tracks
  (`bass_py/mio/tests/test_foo.py`), bass
  (`bass_py/bass/hierarchy/bar.py`), gallery
  (`plots/physics_gallery/01_species_background/baz.png`). The
  paste block closes with post-arrival verification commands:
  `git log --oneline -3` + `git show --stat <sha>`. The non-
  finding-by-design property (§A46.3 prose unchanged) is
  preserved; the block only materialises the commands.
- **Output**: 1 file changed (`docs/dossier/A46_three_lane_
  race_stress_test.md`, +24 / 0 L); no code change, no test
  change.

### W20D5 — DOS-A48 MIO → HTT dependency-wait contract (new)

- **Core claim**: The ind-tracks lane has eight distinct
  artefacts whose promotion to `reduction_status='theory-direct'`
  or to a "committed & cited in ch12" state is blocked on
  upstream bass_py or HTT milestones. Currently the blocked
  surface is spread across v3 §17.3 (a partial list), per-week
  audit §8 repair rows, and per-artefact dossier "deferred to"
  clauses (A41.6 / A42.5 / A45.3 / A47.2). A reader who wants to
  know "what lands when bass_py W10-02 K_ℓ atlas V-gates?" has
  to cross-reference four documents.
- **Algorithm**: new dossier (157 L, six sections). §A48.2 is an
  eight-row matrix with columns (ind-tracks artefact | current
  status | upstream milestone | consumed output | paste target |
  audit ref). §A48.3 gives per-row promotion conditions (HJ-01 /
  HJ-03 / HJ-04 / HJ-05-full / MANU-CH12 sections / A43 digest
  test). §A48.4 specifies the audit §8 ledger mechanics — each
  row in §A48.2 corresponds to an `R<n>` repair row with a
  landing-trigger sentence and an ind-tracks-action sentence;
  when the upstream milestone lands, the R-row flips to
  `RESOLVED <W>D<M>`. §A48.5 cross-refs A34 / A41 / A42 / A45 /
  A47 and notes A48 supersedes v3 §17.3's partial list. §A48.6
  explicitly declares "no code landing" and documents the
  steady-state ledger discipline (re-read every Week-N plan
  rotation; NEXT_SESSION §2 "Deferred" block is a projection of
  §A48.2).
- **Output**: 1 file changed (`docs/dossier/A48_mio_htt_
  dependency_wait_contract.md`, +157 L, new file); no code
  change, no test change.

---

## 2. Contract / interface audit

| Surface | Before W20 | After W20 | Δ |
|---|---|---|---|
| `mio.interface.mio_certificate._hash_config` anchor docstring | W19D1 kwarg-evolution hedge; no scope-clarity paragraph | + "Anchor scope (W19 F3 / W20D1)" paragraph naming three refactor kinds (W20D1) | **+scope clarity** (docstring only) |
| A46 §A46.3 three-terminal recipe | prose description of steps 1–4 | + paste-ready shell block (three terminal shell sessions + post-arrival verification) (W20D3) | **+paste-readiness** (prose-accurate, command-level detail) |
| Dependency-wait ledger | scattered across v3 §17.3 + per-week audit §8 + per-dossier "deferred to" clauses | + A48 (157 L, 6 sections) with eight-row dependency matrix, promotion conditions, audit §8 ledger mechanics (W20D5) | **+single SSOT ledger** superseding v3 §17.3 partial list |
| `_hash_config` runtime signature assertions | W19D1 frozen-list (`("parts",)`, `VAR_POSITIONAL`) | unchanged | 0 |
| `MioCertificate` schema-hash digest mechanism (A43) | specified W15D3; test deferred to first extension | unchanged (test still deferred per §A43.3) | 0 |
| §0 first-order rules (commit hygiene) | status-gate (W13D1) + scoped pathspec (W15D1) | unchanged | 0 |
| All other surfaces (probe registry, A37 grammar, A36/A36a/A42/A44/A45/A47 dossier text, MIO producers, TSC bridges, workspace contracts) | as-of W19 | unchanged | 0 |

All extensions are additive. No schema-hash rotation, no field
retype, no field removal, no producer-side runtime change. W20D1
adds documentation to an existing test; W20D3 + W20D5 are
documentation-only.

---

## 3. Phys-math audit

No physics or numerical-method change landed this phase. All
three landings are runtime-docstring strengthening / dossier-
surface additions.

- **W20D1**: docstring paragraph inside an existing pure-function
  anchor test. No numerical claim; no assertion added or changed.
- **W20D3**: prose-only. No numerical claim. §A46.3's non-finding-
  by-design property of the scoped-pathspec rule is unchanged;
  the added shell block materialises the prose into executable
  commands but does not change the rule or its reachable states.
- **W20D5**: prose-only. No numerical claim. A48 is a ledger
  dossier describing what lands when; no code path is exercised
  by A48 itself.

---

## 4. Code path audit

- **W20D1**: pure-docstring edit inside
  `test_hash_config_matches_a45_2_pseudocode_shape`. Docstring
  text sits between the existing `W19D1` paragraph and the
  function body; the function body (imports + assertions +
  payload-call) is unchanged byte-for-byte. Test (1) pytest
  collection finds `test_hash_config_matches_a45_2_pseudocode_
  shape` unchanged; (2) `pytest htt/mio/tests/test_mio_
  certificate_generator.py` → 11/11 passed in 0.10 s; (3) the
  docstring is picked up on `test.__doc__` inspection
  (manually verified by reading the file post-edit).
- **W20D3**: one dossier file under `docs/dossier/`. No Python
  file touched; no test added. Markdown added to §A46.3 as a
  fenced `bash` code block between step 4 and the closing prose
  paragraph — no new section number, no cross-reference drift.
- **W20D5**: one new dossier file under `docs/dossier/`. No
  Python file touched; no test added. Markdown section
  numbering follows the §A48.N convention (six top-level
  sections).
- No `bass_py/bass/*` file touched (lane discipline); no
  `plots/physics_gallery/` file touched (gallery-lane
  discipline); no `project/*` file touched (W8 FM1 /
  `feedback_project_local_only`). `git status --short` during
  each W20 commit was audited; pre-commit status gate (W13D1)
  applied; scoped-pathspec rule (W15D1) applied — every W20
  commit line ended with `-- <explicit-path>` matching the
  described file set exactly (single-file commits; §6 below).

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (no numerics landed this phase). |
| Tolerance sensitivity | n/a — W20D1 docstring edit does not change existing assertion behaviour. |
| Underflow / overflow | n/a. |
| Conditioning | n/a. |
| Cache / state leakage | `_hash_config` is a pure function reading only its arguments; `inspect.signature` is a static introspection call with no side effects; test runs in pytest's default isolation (unchanged from W19). |
| Seed / reproducibility | n/a (deterministic introspection + deterministic pure function). |
| Baseline reproduction | `pytest htt/mio/` = 109/109 green in ~1.6 s; `pytest htt/htt/tests/ htt/src/ htt/tsc/{admissibility,diagnostics,charts,integration}/ htt/workspace/ htt/mio/` = 1080/0/4 in ~34 s. Two independent pytest runs during W20D7 returned identical counts. |
| OOD / misspecification | W20D1 adds no runtime behaviour; the docstring has no programmatic reader in the test infrastructure (no `pydoc` check, no `mkdocs` scrape). Its effect is purely on human readers hitting the failing assertion. |

---

## 6. Ranked failure modes (P0–P3)

Per the NEXT_SESSION §2 Week 20 Day 7 directive this section MUST
include a §6 W12 F1 / W14 F1 cross-lane-contamination recurrence
check verifying the W15D1 scoped-commit rule was followed on
every W20 sha via `git show --stat`, plus the A46.2 lane-
classification check that determines whether the A46.4 three-lane
observation row fires.

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| W20 check #1 | **PASSED** | process (W12 F1 / W14 F1 recurrence) | `git show --stat 9fb1407 5391dc8 4d7a3ed` returns: (1 file: `bass_py/mio/tests/test_mio_certificate_generator.py`, +15 L) + (1 file: `docs/dossier/A46_three_lane_race_stress_test.md`, +24 L) + (1 file: `docs/dossier/A48_mio_htt_dependency_wait_contract.md`, +157 L new). Every path is on this lane's owned surface per A46.2 (ind-tracks: `bass_py/mio/**` + `docs/dossier/A*`); no `bass_py/bass/*`, no `plots/physics_gallery/*`, no `project/*`, no unrelated dossier paths. `git log 184b06c..HEAD` returns exactly the three W20 commits above at audit-write time; the W19 post-audit-addendum precedent means a final check at audit-commit time is required (see addendum protocol below). | both the W13D1 status-gate and the W15D1 scoped-pathspec rule held on all three W20 commits; each commit used the `git commit -- <explicit-path>` form. | n/a — positive finding. | Two distinct drift vectors observed in the working tree during W20 staging: (a) 68 gallery-lane rename entries inherited from W19 (pre-staged `plots/... → figures/...` renames — same as W19 audit addendum), and (b) a large set of bass-lane deletions (`bass_py/bass/*`, `bass_py/htt/*`, `bass_py/src/*`, `bass_py/tsc/*`, etc. from the working-tree reorg where the live tree moved to `htt/...` in W18). Neither was part of any W20 commit — the scoped-pathspec form excluded both drift vectors by construction. This is the second distinct phase exercising the rule under active staging-index drift (W19 addendum was the first). |
| W20 check #2 | **PASSED** | process (A46.2 applied to this window) | A46.2's lane-classification applied to the three W20-window shas (`9fb1407`, `5391dc8`, `4d7a3ed`) produces: ind-tracks = `{9fb1407, 5391dc8, 4d7a3ed}`, bass = `{}`, gallery = `{}`. **One lane observed, not three.** A46.4 audit row template not triggered this phase. W18 → W19 → W20 three consecutive phases where A46.2 resolves to ≤ two lanes; the A46.4 first-observation template remains paste-ready for a future phase. W19D3 picked the §A46.5.1 + §A46.6 unblocked alternative; W20D3 picked the §A46.3 command-level expansion unblocked alternative; the A46.4 steady-state phrasing remains gated on the first three-lane observation. | A46 specifies the protocol pre-observation; three phases now (W18, W19, W20) have exercised §A46.2 on real windows and returned ≤ two lanes. | n/a — positive finding; A46.2 resolves unambiguously on three shas. | readers may notice that the three-lane window has still not materialised despite three phases of classification; this does not indicate A46.4 is unnecessary — the first three-lane window will land eventually and A46.4 is the only paste-ready template when it does. The W19 post-audit-addendum pattern shows that a cross-lane commit can arrive between audit-write and audit-commit, which would flip the classification to two-lane (but not three-lane, since the gallery lane has not committed in three phases). |
| F1 | **P3** | docs (§A46.3 command-block example-path realism) | §A46.3's paste-ready shell block uses `bass_py/mio/tests/test_foo.py`, `bass_py/bass/hierarchy/bar.py`, `plots/physics_gallery/01_species_background/baz.png` — three plausible ownership-prefix paths but not real files in the repo. A reviewer copy-pasting the block verbatim would hit "file does not exist" on `git add`; the block is pedagogical, not executable-as-is. | the block is an adversarial recipe for a reviewer *deliberately* staging files to reproduce the race; the reviewer is expected to substitute real paths from their own lane. The non-executable default is intentional (avoids accidental `git add` of real repo paths during a pedagogical exercise) but the current prose does not say so. | optional W21+ follow-up (cheap): add a one-line "paths are pedagogical — replace with real lane-owned paths before executing" note above the shell block. | a reviewer interprets the "file does not exist" error as a §A46.3 bug and re-files the dossier. |
| F2 | **P3** | docs (A48.2 bass_py milestone tag drift risk) | §A48.2's "Upstream milestone" column uses tags like `W10-02 (K_ℓ atlas V-gate)` that mirror the bass_py lane's internal roadmap vocabulary as of 2026-04-19. If the bass_py lane renames or re-sequences milestones (e.g. W10-02 splits into two), A48.2's references become stale until the next AUDIT(Wx Rn) fix commit. | A48.6 already names this case ("If the bass_py roadmap rearranges, A48.2's 'Upstream milestone' column is updated in a dedicated AUDIT(Wx Rn) commit before the next promotion PR lands") but this is a documentation cadence rule, not an enforcement mechanism. | optional future follow-up: link A48.2 to a machine-readable bass_py roadmap JSON (analogous to A36a's YAML sidecar pattern) so milestone tag drift can be detected by a parity test. Not urgent — the bass_py roadmap is re-stated in every BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md rotation, so drift would be caught during plan-version-bump cycles. | a reviewer treats A48.2's milestone tags as canonical when they have drifted from the bass_py lane's current naming; the consumed-output + paste-target columns still resolve correctly (they cite code paths, not milestone names), so the error is cosmetic, not operational. |
| F3 | **P3** | docs (A48 trigger-ownership ambiguity on ind-tracks ↔ bass coordination) | §A48.3 promotion conditions for HJ-01 say "the upstream atlas must … pass bass_py's V-gate signature … (the atlas JSON carries `v_gate_sha=...` in its provenance)". This places the verification inside the HJ-01 promotion PR, i.e. the ind-tracks lane. It does not specify whether the bass_py lane has the reciprocal contract (must the V-gated atlas JSON *always* carry a `v_gate_sha` field, or only if an ind-tracks consumer requires it?). | A48.3 is written from the ind-tracks-consumer side only. The bass_py lane's producer contract is not cross-referenced (and may not exist in writing). | optional W21+ follow-up: coordinate with the bass_py lane to ensure the V-gate JSON always carries the provenance field; if the bass_py lane's producer contract already specifies this, add a cross-reference to A48.3; otherwise add a "bass_py side must publish `v_gate_sha` in the atlas provenance" note. Not blocking — HJ-01 promotion PR would catch the absence at first consumption. | a reader treats A48.3 as a complete bilateral contract when it is only the consumer half; a bass_py lane change that drops `v_gate_sha` would be caught late (at HJ-01 landing) rather than early. |

**No P0 / P1 items found.** The W12 F1 / W14 F1 process pattern
did not recur this phase (W20 check #1 PASSED on a single-lane
window with two concurrent drift vectors absorbed — fifth
distinct phase exercising the scoped-pathspec rule). A46's
three-lane race scenario was *not* triggered (W20 check #2);
A46.4's first-observation row remains paste-ready for a future
phase. The three residual P3 items are soft surfaces — F1 is a
pedagogical-path note on the W20D3 shell block, F2 is a drift
risk on A48's milestone tags, F3 is a producer-contract
reciprocity gap on A48.3. None block W21 execution.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **n/a** — no numerical claim landed.
- **dimensional consistency**: **n/a** — docstring / shell / docs
  surface.
- **sign / normalization**: **n/a**.
- **positivity / admissibility**: **n/a** — no physics state
  touched.

**B. Code verifier**
- **contract satisfaction**: **passed** — `_hash_config` signature
  unchanged; the W19D1 frozen-list assertion continues to match
  the production signature at `bass_py/mio/interface/mio_
  certificate.py:44`. W20D1 adds no new assertion. A46 cross-refs
  resolve (grep: `A46.3` = 6 hits in A46.md post-W20D3, consistent
  with three added internal references + three pre-existing).
  A48 cross-refs resolve (all of A32, A34, A41, A41.6, A42, A42.5,
  A44, A45, A45.3, A47, A47.2, A47.6, v3 §7, v3 §10.2, v3 §17.3,
  `feedback_project_local_only.md`, `docs/INDEPENDENT_TRACKS_
  NEXT_SESSION.md` §2 cited with section anchors; `bass_py/mio/
  interface/cache_replay.py` is explicitly marked as "candidate
  location" per A47.3, and `bass_py/mio/decomposition/hj03_
  evidence_anatomy.py` + `bass_py/mio/decomposition/hj04_
  departure.py` are marked as "new" per A48.2's paste-target
  column).
- **actual code-path usage**: **passed** — W20D1 adds docstring
  text to an already-running test path; the test body itself is
  unchanged. W20D3 / W20D5 add no code path.
- **regression risk**: **low** — touched-surface 1080 → 1080
  (0 delta), 0 failures, 0 skip-change. Full `pytest htt/mio/`
  109/109 in ~1.6 s. Full touched-surface pytest 1080/0/4 in
  ~34 s.
- **reproducibility**: **passed** — two independent pytest runs
  during W20D7 returned identical test counts.

**C. Numerical verifier**
- **tolerance robustness**: n/a — no tolerance knob added.
- **convergence / stability**: **n/a**.
- **baseline reproducibility**: **passed** — two independent
  pytest runs returned identical test counts.
- **uncertainty / misspecification**: **n/a**.

**D. Dossier verifier**
- **A46 § numbering coherent**: **passed** — the W20D3 shell
  block slots inside §A46.3 without a new section number; the
  surrounding prose (closing paragraph on "non-finding by
  design") is unchanged; §A46.3 now has a 24-L block between
  step 4 and the closing paragraph.
- **A48 cross-references resolve**: **passed** — the eleven
  sibling appendices / plan sections cited (A32, A34, A41,
  A41.6, A42, A42.5, A44, A45, A45.3, A47, A47.2, A47.6, v3
  §7, v3 §10.2, v3 §17.3) all exist in the repo. Internal
  §A48.N cross-references resolve (§A48.2 ↔ §A48.3 ↔ §A48.4
  bidirectional; §A48.5 cites A48.2 implicitly via "this
  matrix").
- **A48 dependency matrix well-formed**: **passed** — eight
  rows, each with six columns; each row's "Paste target"
  column names a concrete repo path or a "new" file per §A48.3
  promotion conditions; each row's "Audit ref" column names a
  specific audit finding (W10 F1–F3, A42.5, A45.3, A47.2,
  W5 APPLY-BIAS-AMP resolution, v3 §17.3, W15 F3, A43.3).
- **W19 F1 / F2 / F3 carry-forward closure**: **partial** —
  F3 closed by W20D1 (docstring scope-clarity); F1 and F2 are
  HJ-03-PR-gated and remain paste-ready in A47 / §A46.6
  respectively (tracked in §8 below). The §3 carry-forward
  table rows record F3 RESOLVED.

---

## 8. Minimal repair plan

No P0 / P1 repair needed. Three opportunistic patches for W21+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | Add a one-line "paths are pedagogical — replace with real lane-owned paths before executing" note above the W20D3 shell block in §A46.3. | no (P3 usability clarity). | F1 — a reviewer hits "file does not exist" on verbatim paste and re-files the dossier. | 0 (dossier edit only; ~2 L). | additive prose. |
| R2 | Coordinate with the bass_py lane to ensure V-gated atlases always carry `v_gate_sha` in provenance; add a cross-reference note in §A48.3. (HJ-01-PR-gated follow-up if the producer contract gap is real; otherwise a cross-reference edit only.) | no (P3 completeness; HJ-01-trigger-gated if producer-side edit needed). | F3 — A48.3 is read as bilateral when it is consumer-only. | 0 (dossier edit only; or 1-line addition to bass_py producer docs). | additive. |
| R3 | Optional: sidecar A48.2 with a `bass_py_milestones.yaml` machine-readable mirror of the "Upstream milestone" column + parity test (analogous to A36a.yaml / `test_standard_probes_sigma_code_matches_a36a_yaml`). Defer until a bass_py roadmap rename drifts tags in §A48.2. | no (P3 drift hedge; trigger-gated on first observed milestone rename). | F2 — A48.2 milestone tags drift from bass_py roadmap silently. | +1 parity test if sidecar is added. | additive. |

All three are deferrable; none block W21 execution. R1 is
unblocked and the cheapest; R2 is partially gated on HJ-01 PR
landing (consumer-side cross-reference is unblocked, producer-
side edit would land in the HJ-01 PR); R3 is trigger-gated on
first observed milestone rename.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `venv/bin/python -m pytest htt/mio/` →
  109/109 green in ~1.6 s; touched-surface `venv/bin/python -m
  pytest htt/htt/tests/ htt/src/ htt/tsc/{admissibility,diagnostics,
  charts,integration}/ htt/workspace/ htt/mio/` → 1080/0/4
  (unchanged from W19 baseline).
- **Edge / adversarial**:
  `test_hash_config_matches_a45_2_pseudocode_shape` (W18D1 anchor
  + W19D1 kwarg-evolution hedge + W20D1 scope-clarity docstring —
  the docstring does not add runtime assertions but scopes the
  anchor's intended triggers for future PR authors).
- **Physics sanity**: n/a — no numerical claim landed; all three
  W20 landings are docs-↔-code anchor text or dossier prose.
- **Regression**: full touched-surface `1080 / 0 / 4` (unchanged
  from W19 baseline); MIO contribution 109 unchanged; tsc
  standalone 602 unchanged.

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W20 세 landings (W19 F3 `_hash_
  config` anchor scope-clarity docstring + §A46.3 concrete git
  commands + A48 MIO → HTT dependency-wait contract) 모두 기존
  contract ↔ code ↔ test 구조를 strengthen 하거나 신규 dossier 를
  추가하는 additive 변경. MIO contribution 109 held; 전체 touched
  surface 1080 held (W20D1 는 docstring-only, 0 count delta).
  **W12 F1 / W14 F1 재발 없음** — §6 W20 check #1 PASSED; 세 W20
  commits 각각 단일 lane-owned path 하나만 포함; audit window
  기간 중 다른 lane 의 커밋 영집합 (단, working-tree 에는 W19
  post-audit-addendum 에서 언급된 68 개 gallery-lane 스테이징
  index rename + bass-lane 의 대규모 삭제 drift 가 계속 존재;
  scoped-pathspec rule 이 두 drift 벡터를 construction-time 에
  제외함). 다섯 번째 phase 의 scoped-pathspec rule stress-test.
  세 lane race (ind-tracks + bass + gallery) 는 이번 phase 에
  도 triggered 되지 않음 — W20 check #2 는 1 lane 관측 (W18 →
  W19 → W20 연속 ≤ two-lane).
- **지금 당장 구현/수정할 1개**: 없음. W20 gate 네 항목 전부 green;
  W21 active priorities 는 §8 R1–R3 중 하나 (R1 은 unblocked 최소
  2 L 수정; R2 는 HJ-01 PR-gated partially; R3 는 trigger-gated)
  또는 W20 F1/F2/F3 중 하나를 닫거나 신규 A4x dossier / MANU-CH03
  extension.
- **지금 손대면 안 되는 1개**: A43 digest 테스트의 즉시 착지
  (W15 R3 / W16 R3 / W17 R3 / W18 R3 / W19 R3 / W20 R3 반복 —
  trigger 가 아직 미도착; 현재 schema 에 freeze 하면 첫 확장 PR
  이 paste-replace 를 강요받을 뿐 추가 catch 는 없음). HJ-03
  production wiring 또한 htt W10-02 K_ℓ atlas 착지 전까지 금지
  (governing plan §17.3 / A48.2 의존 대기 목록; A48 이 이제 해당
  ledger 의 SSOT 이므로 future rotation 은 v3 §17.3 대신 A48.2
  를 참조).

---

## Week-20 final gate (per NEXT_SESSION §2 Week 20)

- [x] W19 F3 / W19 R3 `_hash_config` anchor scope-clarity
      docstring landed (W20D1 `9fb1407`; +15 L docstring on
      existing test; no assertion change; MIO contribution
      holds at 109).
- [x] W19 F1 / W19 F2 close (HJ-03-PR-gated; **not landed** —
      no HJ-03 PR in W20) OR unblocked alternative W18/earlier
      carry landed — **§A46.3 concrete git commands picked**
      (W20D3 `5391dc8`; +24 L paste-ready shell block; closes
      the terse-recipe gap that the §A46 minor-expansion option
      explicitly named in NEXT_SESSION §2 Week 20 Days 3–4).
- [x] One of A48 dossier / MANU-CH03 extension landed —
      **A48 picked** (W20D5 `4d7a3ed`; new dossier, 157 L, six
      sections; MIO → HTT dependency-wait contract consolidates
      the scattered blocked-on-bass_py surface into an eight-row
      dependency matrix; supersedes v3 §17.3's partial list).
- [x] Phase-boundary audit log written (this file); §6 W12 F1 /
      W14 F1 recurrence check returns **PASSED** (`git show
      --stat` on the three W20 commits shows only this lane's
      owned paths; zero cross-lane commits landed during the
      window at audit-write time; two concurrent drift vectors
      (68 gallery renames from W19 + bass-lane deletions from
      W18 working-tree reorg) sit in the staging index and
      working tree but are excluded by the scoped-pathspec
      rule on every W20 commit; A46.4's three-lane template
      not triggered this phase — W20 check #2 shows one lane
      only, consecutive with W18 two-lane and W19 two-lane
      results).
- [x] No touched-surface regressions (1080 passed; unchanged
      vs W19; 0 failed; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W20` closes with
zero new P0/P1/P2 findings; three documented P3 residuals
(F1 shell-block pedagogical paths, F2 A48.2 milestone tag drift
risk, F3 A48.3 producer-contract reciprocity gap) feed the W21
repair plan, of which R1 is the only fully unblocked option
(R2 is partially HJ-01-PR-gated; R3 is trigger-gated on first
observed milestone rename).

---

## Addendum protocol notice

The W19 post-audit addendum observed a bass-lane commit
(`d7d25da`) landing on `main` between W19D5 and the audit
commit (`bb82dd3`), two minutes before audit-commit. The
pattern — a cross-lane commit arriving after the audit body is
written but before the audit is committed — has now occurred
twice (W16D7 → W16 audit, W18D5 → W18 audit, W19D5 → W19 audit
— all bass-lane arrivals). This audit's §6 W20 check #1 is
written against `git log 184b06c..HEAD` at the time of drafting
(three W20 commits, zero bass-lane arrivals). **If a cross-lane
commit arrives between audit-write and audit-commit**, a
W20 F4 post-audit addendum is appended with the revised A46.2
classification, following the W19 F4 precedent. This note is
kept explicit here so the addendum pattern is protocol-level,
not improvised per-phase.

---

## Post-audit addendum (W20 F4 — A46.2 window re-classification)

**Committed 2026-04-19, post `5dfcf2d`.** The audit body above
was written against the then-current `git log 184b06c..HEAD`
output and declared the W20 window **single-lane** (W20 §6
check #1 narrative: "zero cross-lane commits landed during the
W20 window at audit-write time"; W20 §6 check #2 classification:
"one lane observed, not three"). That declaration held at the
time of writing (and was explicitly hedged by the addendum
protocol notice) but was invalidated by the bass-lane commit
**`9336280`** (`FB-3.1: TiltedSpeciesBackground abstraction +
beta->0 limit recovery (Phase FB-3 entry)`, 2026-04-19
23:14:55 +0900), which landed on `main` between W20D5
`4d7a3ed` (23:04:xx) and the audit commit `5dfcf2d`
(23:15:xx) — approximately one minute before my audit commit.

This mirrors the W16 F1 / W16D7 and W19 F4 post-audit addendum
patterns (third occurrence of the same scenario; the addendum
protocol notice at the top of this section pre-documented the
expected recurrence). Mechanical re-verification:

- `git show --stat 9336280` returns: `docs/audits/AUDIT_PHASE_
  FB3_2026-04-19.md` + `docs/lowell_bianchi/00_conventions.md`
  + `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md`. Under A46.2's
  ind-tracks ownership prefix (`bass_py/mio/**`, `bass_py/
  workspace/**`, `bass_py/src/common/**`, `bass_py/tsc/**`,
  `docs/dossier/A*`, `docs/INDEPENDENT_TRACKS_*`, `docs/audits/
  AUDIT_PHASE_IND_TRACKS_*`, `project/00_manuscript/ch{03,11,12}
  _*.tex`): zero paths match. `docs/audits/AUDIT_PHASE_FB3_*.md`
  is bass-lane-owned (bass-audit prefix, distinct from
  `AUDIT_PHASE_IND_TRACKS_*`); `docs/lowell_bianchi/*` is
  bass-lane-owned per the governing plan. **All three paths are
  bass-lane per A46.2.** Zero gallery-lane paths.
- `git show --stat 5dfcf2d` returns: `docs/audits/AUDIT_PHASE_
  IND_TRACKS_W20_2026-04-19.md` + `docs/INDEPENDENT_TRACKS_
  NEXT_SESSION.md` — **both ind-tracks-owned per A46.2**. Zero
  bass or gallery paths. The W15D1 scoped-pathspec rule excluded
  the same two concurrent drift vectors (68 W19 gallery renames
  + W18 bass-lane deletions) that had sat in the staging index
  / working tree throughout the W20 window.

### Revised §6 check #1 — W12 F1 / W14 F1 recurrence check

**PASSED** (unchanged verdict). `git show --stat` on the five
W20-window shas (`9fb1407`, `5391dc8`, `4d7a3ed`, `9336280`,
`5dfcf2d`) shows each commit scoped to a single lane:

- ind-tracks: `{9fb1407, 5391dc8, 4d7a3ed, 5dfcf2d}` — four
  commits, each touching exactly one or two ind-tracks files
  (`bass_py/mio/tests/test_mio_certificate_generator.py`,
  `docs/dossier/A46_*.md`, `docs/dossier/A48_*.md`,
  `docs/audits/AUDIT_PHASE_IND_TRACKS_W20_*.md` +
  `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md`).
- bass: `{9336280}` — one commit, touching only
  `docs/audits/AUDIT_PHASE_FB3_*.md` + `docs/lowell_bianchi/*`
  paths.
- gallery: `{}` — zero commits.

Zero file overlap between the ind-tracks and bass commit sets.
The two concurrent drift vectors (staging-index gallery renames
+ working-tree bass-lane deletions) are still not in any of
the five commits; they remain in the working-tree index,
consistent with the W19 addendum observation that these drifts
are long-running and lane-side. The scoped-pathspec rule held:
`5dfcf2d` contains exactly the two docs paths I listed in the
commit command, not the broader drift surface.

### Revised §6 check #2 — A46.2 lane classification

A46.2 applied to the five W20-window shas produces:
`{ind-tracks: 4, bass: 1, gallery: 0}`. **Two lanes observed,
not three.** A46.4's first-three-lane-observation template
remains paste-ready for a future phase; W18 → W19 → W20 three
consecutive phases now resolve to ≤ two-lane windows. (The
W20 audit body's "single-lane" classification is corrected
here to "two-lane post-addendum", matching the W19 precedent
where the audit body's single-lane declaration was similarly
corrected.)

### Stress-test ledger update

The W15D1 scoped-pathspec rule has now been exercised under
the following adversarial windows:

- **W16D7** — concurrent-commit (bass-lane `4c50313` between
  W16D5 and audit).
- **W17D3** — working-tree-drift (four unstaged
  `bass_py/bass/hierarchy/*` files at commit time).
- **W18D5→W18D7** — second concurrent-commit observation
  (bass-lane `92cefa2` between W18D5 and audit).
- **W19D5→W19D7** — third concurrent-commit observation
  (bass-lane `d7d25da` between W19D5 and audit) + staging-
  index drift (68 gallery renames).
- **W20D5→W20D7** — fourth concurrent-commit observation
  (bass-lane `9336280` between W20D5 and audit) + staging-
  index drift (68 gallery renames carried from W19) +
  working-tree drift (W18 bass-lane deletions). First phase
  where **three** independent drift vectors coincided in the
  same audit window (lane arrival + staging-index
  contamination + working-tree-drift carry); all three
  absorbed by the W15D1 rule with zero manual intervention
  beyond the required pathspec form.

### Carry-forward W20 F4 → §3 table

W20 F4 (this addendum — stale single-lane declaration in the
audit body, corrected here) is **RESOLVED by this addendum**;
no W21 repair is required beyond continuing the addendum-
protocol discipline pre-documented in the top notice. The
"status-gate at audit-commit time" optional W20+ follow-up
raised in W19 F4's carry-forward remains optional: the
addendum-pattern is now protocol-level (three recurrences
locked), which is a sufficient workflow guarantee until a
future phase where the addendum itself fails (i.e. the
scoped-pathspec rule would fail under some yet-unobserved
scenario). Memory `feedback_git_workflow.md` could be updated
with a "status-gate at audit-commit time" entry; this remains
optional for W21+.

Phase `IND_TRACKS_W20` closure re-affirmed with the corrected
two-lane window narrative; no gate re-test needed (all five
items remain green under the corrected classification).
