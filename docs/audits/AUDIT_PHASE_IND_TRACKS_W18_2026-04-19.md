# Phase-boundary audit — Independent Tracks Week 18

**Phase tag**: `IND_TRACKS_W18`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12+ continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 18 (W17 F1 / R1
`_hash_config` docs-↔-code anchor + W17 F2 / R2 A45.6 ↔ A41.6
cross-link + one A4x dossier).
Execution: W18D1 A45.2 `_hash_config` docs-↔-code anchor test (D1),
W18D3 A45.6 ↔ A41.6 harness-signature cross-link (D3), W18D5 DOS-A46
three-lane race stress-test protocol (D5), this audit + NEXT_SESSION
rotation (D7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.4 (G19 hard separation — A46 is the process-hygiene
companion to A44 / A45's structural + content-hash companions to
A34);
v3 §10.2 (HTT ↔ MIO contract table — W18D1 anchors the `_hash_config`
helper that A45.2's replay pseudocode consumes, keeping the contract
table's provenance columns bound to a runtime assertion);
v3 §11.14.7 (dossier convention — A46 added under the A4x family;
first three-lane-race protocol specified in the repo's history);
[A44.3](../dossier/A44_mio_htt_handshake_sequence.md) (git_commit
at-instantiation invariant — W17D1 is the runtime gate; W18D1 is the
docs-↔-code helper-anchor for the same handshake);
[A45.2 / A45.6](../dossier/A45_mio_cache_replay_drift.md) (cache-
replay pseudocode + paste-ready acceptance block — W18D1 anchors
A45.2; W18D3 binds A45.6 to A41.6);
[A41.6](../dossier/A41_mio_report_type_extension_protocol.md)
(HJ-03 extension checklist — W18D3 inserts step 6.5 "Freeze the
replay-harness signature");
[A46](../dossier/A46_three_lane_race_stress_test.md) (three-lane
race protocol — new, W18D5);
[W12 F1](AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md) +
[W14 F1](AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md) (cross-lane
contamination mitigations — §6 below records the W18 recurrence
check);
[W16 F1 addendum](AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md) +
[W17 audit §6](AUDIT_PHASE_IND_TRACKS_W17_2026-04-19.md) (first
and second adversarial stress-tests of the scoped-pathspec rule —
W18 adds a third observation, see §6).

**Baseline head**: `6f6df1c` (`IND_TRACKS_W17: phase audit + next-
session prompt rotation`). **One intervening cross-lane commit on
`main` this phase** — `92cefa2` (bass lane, `FB-2.3: Class B III /
IV / VI_h / VII_h twist-coupled nabla_tilde + T1 Ricci hook
activation`) landed after W18D5's `7cc5a42` and before this audit
commit. The bass commit touches `docs/audits/AUDIT_PHASE_FB2_
2026-04-19.md` (bass-lane owned) and `docs/lowell_bianchi/NEXT_
SESSION_PROMPT.md` (bass-lane planning doc); neither is in this
lane's owned surface. The scoped-pathspec rule on the three W18
commits excluded it by construction (the bass lane's `92cefa2`
shares no files with any of `0d2fc9f` / `23fefbb` / `7cc5a42`).
§6 W18 check #1 below records this as the third adversarial stress-
test of the W15D1 rule (first post-A46 observation; two-lane case,
not three).

**Commits this phase**:

- `W18D1` — `0d2fc9f` `W18D1: A45.2 _hash_config docs-↔-code anchor
  (W17 F1)`. One-file commit (+50 L) appending
  `test_hash_config_matches_a45_2_pseudocode_shape` to
  `bass_py/mio/tests/test_mio_certificate_generator.py`. The test
  imports `_hash_config` from `mio.interface.mio_certificate` by
  the exact name A45.2 names in its pseudocode, asserts the
  `__name__` attribute as a rename-detector, calls the helper with
  the exact six-field tuple (`report_type`, `probe_name`,
  `channel`, `departure_variables`, `adequacy_indicators`,
  `consistency_metrics`) from `_base_payload()`, asserts the
  return value is a 16-character lowercase hex string, and cross-
  checks that `build_mio_certificate(**payload).config_hash`
  returns the same digest — otherwise A45.2's
  `recomputed_config_hash` step would drift from the build-time
  hash. Closes W17 F1 — A45.2's pseudocode is now runtime-anchored
  to the helper it names. Touched surface 1079 → 1080; MIO
  contribution 108 → 109.
- `W18D3` — `23fefbb` `W18D3: AUDIT(W17 F2): A45.6 ↔ A41.6
  harness-signature cross-link`. Two-file dossier-prose commit
  (+25 L total). `docs/dossier/A45_mio_cache_replay_drift.md`
  §A45.6 gains a new up-front "Harness-signature note (W17 F2 /
  W18D3)" paragraph (+14 L) binding the paste-ready five-test
  block to the two-argument signature
  `verify_cache_replay(mio_cert, htt_input_bundle, *,
  allow_unsigned_config=False)` and deferring the signature
  freeze decision to A41.6 step 6.5. `docs/dossier/A41_mio_
  report_type_extension_protocol.md` §A41.6 gains a reciprocal
  step 6.5 "Freeze the replay-harness signature (W17 F2 / W18D3)"
  (+11 L) between step 6 and step 7 of the HJ-03 worked example,
  with a forward pointer to A45.6 and the "same PR as paste-
  replace" rule. Closes W17 F2 — the HJ-03 author cannot paste-
  copy §A45.6 without hitting the A41.6 step 6.5 gate first.
  Touched surface unchanged (prose-only).
- `W18D5` — `7cc5a42` `W18D5: DOS-A46 three-lane race stress-test
  protocol (W17 F3)`. One-file commit (+182 L) creating
  `docs/dossier/A46_three_lane_race_stress_test.md`. Eight
  sections: §A46.1 Purpose (narrates the two already-observed
  adversarial scenarios — W16D7 concurrent-commit, W17D3 working-
  tree-drift — and the missing third), §A46.2 "Same audit window"
  definition (`T_prev` / `T_curr` audit-commit bracket; three lane-
  ownership prefix sets: ind-tracks / bass / gallery), §A46.3
  Adversarial recipe (three-terminal reproduction, non-finding-by-
  design property), §A46.4 §6 audit row template (paste-ready
  with `<ind>`/`<bass>`/`<gallery>` sha placeholders and "first
  three-lane observation" phrasing), §A46.5 Failure-pattern
  fingerprint (for the case where the scoped rule ever fails),
  §A46.6 Relation to A41 / A44 / memory `feedback_git_workflow.md`,
  §A46.7 No code landing. Closes W17 F3's deferred-to-observation
  aspect (the audit-time protocol is now specified; the landing
  trigger remains first three-lane observation).
- `W18D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `htt/htt/tests/ htt/src/
htt/tsc/admissibility/ htt/tsc/diagnostics/ htt/tsc/charts/
htt/tsc/integration/ htt/workspace/ htt/mio/` (working-tree mirror;
see Note below) → **1080 passed, 0 failed, 4 skipped**. Week 18
delta vs Week 17 (1079 / 0 / 4): **+1 test (W18D1 +1), 0 skip
change, 0 regressions**.

**Note on working-tree layout** (audit-transparency). Between the
W17 audit (`6f6df1c`) and the W18 window, the user re-pointed the
venv editable-install finder from `bass_phase1_snapshot_2026-04-18/
bass_phase1_snapshot/` to `htt_base/htt/htt/` (per the bass-lane
`92cefa2` commit body) and the bass-lane commits moved the live
working-tree layout from `bass_py/` to `htt/`. The canonical paths
in `HEAD` + every commit in this phase are `bass_py/...`, matching
the governing plan's naming convention. The canonical paths in the
working tree are `htt/...`, byte-identical to their `bass_py/`
siblings. Pytest was run against the live working-tree paths
(`htt/...`) because the commit-side `bass_py/...` working copies
are deleted entries (`git status -sM`: `D bass_py/...`). The W18D1
test was mirrored into `htt/mio/tests/test_mio_certificate_
generator.py` for runtime verification only; only the `bass_py/`
copy is tracked. The 1079 → 1080 delta confirms on the mirror that
the new test passes and no regression was introduced. **This
audit-transparency paragraph is reader-facing only; no process
rule is affected** — the scoped-pathspec commits continue to carry
the canonical tracked path per W15D1.

**TSC-standalone test count**: 602 passed (unchanged from W13–W17
— no TSC code change this week).

**MIO contribution**: 109 tests (+1 vs W17's 108; gate ≥ 47 met
with 62 to spare). Composition: `test_mio_certificate_generator.py`
10 → 11 tests (W18D1 adds the `_hash_config` docs-↔-code anchor);
all other MIO test files unchanged. Cross-check: `venv/bin/python
-m pytest htt/mio/ --collect-only -q | tail -1` = `109 tests
collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY), 1 × `fig_certification_matrix` family
(W9), 1 × `test_bulkflow_likelihood.py:303` dynesty contract guard
(W10D1).

---

## 1. Audit target reconstruction

Three landings, three distinct audit targets — runtime anchor for a
dossier-named helper (W18D1), bidirectional prose cross-link between
two dossier checklists (W18D3), and new process-hygiene dossier for
the three-lane race scenario (W18D5). Two of the three close a W17
residual finding; the third specifies the audit-time protocol for
a scenario that has not yet been observed but is visible on the
recurrence-check horizon.

### W18D1 — A45.2 `_hash_config` docs-↔-code anchor (closes W17 F1)

- **Core claim**: A45.2's `verify_cache_replay` pseudocode names
  `_hash_config` as the re-hashing helper. The helper lives in
  `mio/interface/mio_certificate.py`; no test asserted that the
  dossier's name, its positional-argument signature (the six
  payload fields), or its output shape (16-char lowercase-hex)
  corresponded to the code. A silent refactor (rename, arg-
  reorder, hex-prefix length change) would have drifted the
  pseudocode from the code it describes and the HJ-03 author
  (paste-copying §A45.6) would either ship the wrong pseudocode
  or discover the drift at review time.
- **Algorithm**: import `_hash_config` by its exact name; assert
  `__name__ == "_hash_config"` (explicit rename-detector on top of
  the implicit `ImportError`); call with the six-field tuple from
  `_base_payload()`; assert the return is a `str` of length 16,
  equal to its own lowercase form, with every character in
  `string.hexdigits.lower()`; call `build_mio_certificate(**
  payload)` on the same payload and assert `cert.config_hash ==
  digest` — the A45.2 `recomputed_config_hash` step only works if
  build-time and replay-time hashing agree bit-for-bit on the same
  six-field tuple.
- **Output**: 1 file changed (`bass_py/mio/tests/test_mio_
  certificate_generator.py`, +50 L), +1 test; MIO contribution
  108 → 109; touched surface 1079 → 1080.

### W18D3 — A45.6 ↔ A41.6 harness-signature cross-link (closes W17 F2)

- **Core claim**: §A45.6's five-test block is paste-ready only if
  the HJ-03 harness exposes the signature
  `verify_cache_replay(mio_cert, htt_input_bundle, *,
  allow_unsigned_config=False)` spelled out in §A45.2. Nothing in
  the dossier tree bound that signature to the HJ-03 extension
  checklist (A41.6), so a future HJ-03 PR that chose a different
  input shape (e.g. `bundle.digests` tuple, `replay_context`
  wrapper) would either paste-replace a broken test block or
  discover the divergence at review time.
- **Algorithm**: dossier-prose only. A45.6 gains a new up-front
  "Harness-signature note (W17 F2 / W18D3)" paragraph that
  (a) names the signature explicitly, (b) names the `.paths`
  iterable contract used in step 3 of §A45.2's pseudocode,
  (c) defers the freeze decision to A41.6 step 6.5, and (d)
  requires any adaptation of the test block to land in the same
  PR as the §A45.6 prose edit. A41.6 gains a reciprocal step 6.5
  "Freeze the replay-harness signature (W17 F2 / W18D3)" between
  step 6 (cross-check channel entry) and step 7 (dossier creation)
  that (a) names the §A45.2 signature, (b) lists the two
  adaptation paths (per-item translation of §A45.6 vs fresh
  freeze), and (c) binds the A45.6 prose edit to the same PR as
  the HJ-03 code landing.
- **Output**: 2 files changed (`docs/dossier/A45_mio_cache_replay_
  drift.md` +14 L; `docs/dossier/A41_mio_report_type_extension_
  protocol.md` +11 L); total +25 L prose; no code change, no test
  change.

### W18D5 — DOS-A46 three-lane race stress-test protocol (closes W17 F3 spec, landing deferred to observation)

- **Core claim**: the W15D1 scoped-`git commit -- <paths>` rule
  has been adversarially stress-tested in two distinct scenarios
  so far — W16D7 concurrent-commit (a cross-lane commit landed in
  the audit-window gap) and W17D3 working-tree-drift (four
  unstaged bass-lane files present during a scoped-pathspec
  commit). The three-lane race (ind-tracks + bass + gallery all
  committing into the same audit window) has not yet been
  observed in the repo's history. When it first occurs, the audit
  author should not have to invent the §6 row format in the
  moment.
- **Algorithm**: dossier-only (182 L, eight sections). §A46.1
  Purpose narrates the two observed scenarios. §A46.2 defines the
  audit window (between two phase-boundary audit commits) and the
  three lane-ownership prefix sets (ind-tracks: `bass_py/mio/**`,
  `bass_py/workspace/**`, `bass_py/src/common/**`, `bass_py/tsc/**`,
  `docs/dossier/A*`, `docs/INDEPENDENT_TRACKS_*`, `docs/audits/
  AUDIT_PHASE_IND_TRACKS_*`, `project/00_manuscript/ch{03,11,12}_
  *.tex`, A46 itself; bass: `bass_py/bass/**` + bass-side plan /
  audit paths; gallery: `plots/physics_gallery/**`). §A46.3 gives
  the three-terminal adversarial recipe and establishes the non-
  finding-by-design property under the scoped-pathspec rule.
  §A46.4 is the paste-ready §6 row template with `<ind>` / `<bass>`
  / `<gallery>` sha placeholders and the "first three-lane
  observation" phrasing (retires on second observation). §A46.5
  is the failure-pattern fingerprint for the case where the rule
  ever fails under three lanes (a pre-commit hook becomes load-
  bearing at that point). §§A46.6–7 cross-reference A41.6 / A44.3
  and commit to documentation-only until observation.
- **Output**: 1 file changed (`docs/dossier/A46_three_lane_race_
  stress_test.md`, +182 L, new file); no code change, no test
  change.

---

## 2. Contract / interface audit

| Surface | Before W18 | After W18 | Δ |
|---|---|---|---|
| `mio.interface.mio_certificate._hash_config` helper name + signature + output-shape invariant | referenced by A45.2 pseudocode; no runtime assertion | +1 docs-↔-code anchor test asserting `__name__`, six-arg positional signature via `_base_payload()`, 16-char lowercase-hex output, and `cert.config_hash == _hash_config(...)` build-↔-replay parity (W18D1) | **+runtime anchor** |
| A45.6 paste-ready test block ↔ A41.6 HJ-03 worked example | independent dossiers; no bidirectional anchor; §A45.6 silently assumed the HJ-03 harness signature | §A45.6 gains a "Harness-signature note" paragraph deferring to A41.6 step 6.5; A41.6 gains a reciprocal step 6.5 with forward pointer to A45.6 (W18D3) | **+bidirectional docs anchor** |
| Three-lane race scenario (ind-tracks + bass + gallery concurrent commits) | W15D1 scoped-pathspec rule applies by induction; §6 audit row format unspecified | A46 dossier specifies the audit-window definition, the adversarial recipe, the §6 row template, the failure-pattern fingerprint, and the landing trigger (W18D5) | **+process-hygiene dossier** |
| `MioCertificate` schema-hash digest mechanism (A43) | specified W15D3; test deferred to first extension | unchanged (test still deferred per §A43.3) | 0 |
| §0 first-order rules (commit hygiene) | status-gate (W13D1) + scoped pathspec (W15D1) | unchanged | 0 |
| All other surfaces (probe registry, A37 grammar, A36/A36a/A42/A44/A45 dossier text, MIO producers, TSC bridges, workspace contracts) | as-of W17 | unchanged | 0 |

All extensions are additive. No schema-hash rotation, no field
retype, no field removal, no producer-side runtime change. The
single new assertion (W18D1) exercises existing state under stricter
gates; W18D3 and W18D5 are documentation-only.

---

## 3. Phys-math audit

No physics or numerical-method change landed this phase. All three
landings are runtime-contract anchor / dossier-surface additions.

- **W18D1**: string-equality and hex-character assertions on the
  output of an existing pure function; hashlib sha256 is
  deterministic and already covered by `test_config_hash_is_
  deterministic_for_same_payload` + `test_config_hash_changes_
  with_payload`. The W18D1 addition is *not* a re-test of the
  hash's value-level properties but of the helper's A45.2-
  pseudocode-matching contract (name, positional args, prefix
  length).
- **W18D3**: prose-only. No numerical claim.
- **W18D5**: prose-only. No numerical claim. A46.3's "non-finding-
  by-design" property follows from the well-defined semantics of
  the git `--` pathspec separator, not from any numerical
  argument.

---

## 4. Code path audit

- **W18D1**: pure-Python test addition to MIO's generator tests.
  Uses the module's existing `_base_payload()` helper. Imports
  `_hash_config` via `from mio.interface.mio_certificate import
  _hash_config` — a leaf import on a helper that is not included
  in the module's public `__all__` (`__all__ = ["build_mio_
  certificate"]`), so the test exercises the *implementation*-side
  contract of the helper the dossier names. This is intentional:
  the A45.2 pseudocode names the helper by its internal name, so
  the anchor must be on the internal name.
- **W18D3**: two dossier files under `docs/dossier/`. No Python
  file touched; no test added.
- **W18D5**: one new dossier file under `docs/dossier/`. No Python
  file touched; no test added.
- No `bass_py/bass/*` file touched (lane discipline); no
  `plots/physics_gallery/` file touched (gallery-lane discipline);
  no `project/*` file touched (W8 FM1 /
  `feedback_project_local_only`). `git status --short` during each
  W18 commit was audited; pre-commit status gate (W13D1) applied;
  scoped-pathspec rule (W15D1) applied — every W18 commit line
  ended with `-- <explicit-paths>` matching the described file
  set exactly.

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (no numerics landed this phase). |
| Tolerance sensitivity | **W18D1** — assertions are integer bracket + exact-string identity tests; no tolerance knob exposed. |
| Underflow / overflow | n/a. |
| Conditioning | n/a. |
| Cache / state leakage | `_hash_config` is a pure function reading only its arguments; no global state; test runs in pytest's default isolation. |
| Seed / reproducibility | n/a (deterministic pure function + file-read for dossiers). |
| Baseline reproduction | `pytest htt/mio/` = 109/109 green in ~1.7 s; `pytest htt/htt/tests/ htt/src/ htt/tsc/{admissibility,diagnostics,charts,integration}/ htt/workspace/ htt/mio/` = 1080/4/0 in ~35 s. Two independent pytest runs during W18D7 returned identical counts. |
| OOD / misspecification | W18D1 does not exercise off-happy-path payload shapes (non-dict `departure_variables`, non-str `probe_name`, etc.) — those are covered by existing `test_generator_rejects_unknown_kwargs` and `test_build_rejects_posterior_keyword` invariants. The anchor is narrow by design: rename / resize / arg-reorder of `_hash_config` itself. |

---

## 6. Ranked failure modes (P0–P3)

Per the NEXT_SESSION §2 Week 18 Day 7 directive this section MUST
include a §6 W12 F1 / W14 F1 cross-lane-contamination recurrence
check verifying the W15D1 scoped-commit rule was followed on every
W18 sha via `git show --stat`, with an adversarial-stress-test
narrative if any lane-overlap occurred during the W18 window. It
must also explicitly note whether the three-lane race (W17 F3 /
A46) was triggered.

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| W18 check #1 | **PASSED** | process (W12 F1 / W14 F1 recurrence) | `git show --stat 0d2fc9f 23fefbb 7cc5a42` returns (1 file: `bass_py/mio/tests/test_mio_certificate_generator.py`) + (2 files: `docs/dossier/A41_mio_report_type_extension_protocol.md` + `docs/dossier/A45_mio_cache_replay_drift.md`) + (1 file: `docs/dossier/A46_three_lane_race_stress_test.md`). Every path is on this lane's owned surface per A46.2 (ind-tracks: `bass_py/mio/**` + `docs/dossier/A*`); no `bass_py/bass/*`, no `plots/physics_gallery/*`, no `project/*`, no unrelated dossier paths. **One cross-lane commit landed on `main` during the W18 window** — `92cefa2` (bass-lane, `FB-2.3: Class B III / IV / VI_h / VII_h twist-coupled nabla_tilde + T1 Ricci hook activation`, 2026-04-19 22:26:10) arrived between W18D5 `7cc5a42` and this audit commit. `git show --stat 92cefa2` returns two files — `docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` + `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md` — both bass-lane owned per A46.2 (bass-side plan / audit paths). Zero ind-tracks files in `92cefa2`; zero bass-lane files in any of `0d2fc9f` / `23fefbb` / `7cc5a42`. **Third distinct adversarial stress-test of the W15D1 scoped-pathspec rule, first observation post-A46 landing, second observation of the concurrent-commit scenario (W16D7 being the first).** | both the W13D1 status-gate and the W15D1 scoped-pathspec rule held; the bass-lane `92cefa2` body explicitly mentions a venv editable-install re-point ("re-pointed from the deleted bass_phase1_snapshot path to htt_base/htt/htt/htt via pip install -e reinstall (no code change)") which is bass-lane environmental plumbing, not a lane-overlap signal. | n/a — positive finding. | the audit-window contained **two lanes** (ind-tracks + bass), **not three** — the three-lane case (ind-tracks + bass + gallery) remains unobserved in the repo's history. A46.4's "first three-lane observation" phrasing has not yet been applied. |
| W18 check #2 | **PASSED** | process (A46 definition applied to this window) | A46.2's lane-classification applied to the four W18-window shas (`0d2fc9f`, `23fefbb`, `7cc5a42`, `92cefa2`) produces: ind-tracks = `{0d2fc9f, 23fefbb, 7cc5a42}`, bass = `{92cefa2}`, gallery = `{}`. Two lanes observed, not three. The A46.4 audit row template is not triggered this phase; the steady-state §6 phrasing (this row) is the correct variant. | A46 specifies the protocol pre-observation; this phase is the first to run the classification algorithm. | n/a — positive finding; A46.2 resolves unambiguously on four shas. | A46 readers should note that the first three-lane window will *additionally* require the A46.4 paste-replace; this phase's two-lane result does not exercise that path. |
| F1 | **P3** | docs (A45.2 helper-signature evolution) | The W18D1 anchor test asserts `_hash_config.__name__ == "_hash_config"` and the six-arg positional form. If a future refactor adds a keyword-only argument (e.g. `_hash_config(..., *, digest_length=16)` to introduce the A43 schema-hash digest) the anchor still passes (positional signature unchanged, name unchanged) but A45.2's pseudocode becomes subtly incomplete. | the anchor is tight on name + length + positional signature but lax on kwarg evolution. | optional W19+ follow-up: when A43 lands its digest upgrade, extend the W18D1 anchor to assert `inspect.signature(_hash_config).parameters` against a frozen list that includes any new keyword-only arg. | a reader assumes A45.2 is faithful; a new kwarg lands; HJ-03 replay misses the kwarg at paste time and loses A43's digest protection. |
| F2 | **P3** | docs (A46 three-lane window lifecycle) | A46.4's §6 row template is paste-ready only on the *first* three-lane observation; §A46 explicitly says subsequent observations "drop the 'first three-lane observation' language and resume the steady-state phrasing". The current text defers the "steady-state three-lane phrasing" to the first phase that needs it — which means the second three-lane-observer also has to invent wording in the moment. | A46.4 specifies first-observation phrasing without specifying second-observation phrasing. | optional W19+ follow-up (cheap): extend §A46.4 with a two-line "steady-state three-lane phrasing" block once the first observation lands, so the second observation is fully paste-ready. | the second three-lane audit author writes ad-hoc prose and the two audits' §6 rows drift in style. |
| F3 | **P3** | coverage (post-W18D1 runtime scope) | The W18D1 anchor lives in `test_mio_certificate_generator.py`, which imports `mio.interface.mio_certificate` and therefore presupposes the MIO package's conftest-managed sys.path wiring. A future repo reorganisation (e.g. moving `mio/` under a different package root, or splitting the interface module into two) would break the test by import — which is correct — but the test would then need to be re-homed before A45.2's anchor is restored. | the anchor is correct but location-sensitive. | no repair; continue periodic re-verification on lane boundaries. Note for future HJ-03 PR: if the replay harness lives in a new `mio.interface.cache_replay` module, consider moving or cloning the W18D1 anchor into that test file so the two guards stay adjacent. | the anchor is silently retired during a reorg without replacement, and A45.2 drifts free. |

**No P0 / P1 items found.** The W12 F1 / W14 F1 process pattern
did not recur this phase (W18 check #1 PASSED under the concurrent-
commit scenario — second observation of the W16D7 variant; third
adversarial stress-test overall). A46's three-lane race scenario
was *not* triggered (W18 check #2); the A46.4 first-observation
row remains paste-ready for a future phase. The three residual P3
items are soft surfaces — F1 is a docs-freshness hedge for a
kwarg-evolution scenario, F2 is a lifecycle completion of §A46.4,
F3 is a location-sensitivity note for the W18D1 anchor. None block
W19 execution.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **n/a** — no numerical claim landed.
- **dimensional consistency**: **n/a** — string / hex / docs
  surface.
- **sign / normalization**: **n/a**.
- **positivity / admissibility**: **n/a** — no physics state
  touched.

**B. Code verifier**
- **contract satisfaction**: **passed** — `_hash_config` signature
  unchanged; the W18D1 anchor exercises the existing six-arg
  positional form via `_base_payload()`. A45.6 / A41.6 prose
  edits resolve (grep: `A41.6 / §A41.6` = 4 hits in A45.md; `A45.6
  / §A45.6` = 3 hits in A41.md). A46 cross-refs resolve (A41.6,
  A44.3, W15D1, W16 F1, W17 F3 all cite correctly).
- **actual code-path usage**: **passed** — W18D1 exercises
  `mio.interface.mio_certificate._hash_config` with the exact
  six-field tuple A45.2 names, plus `build_mio_certificate`
  round-trip parity on the same payload; W18D3 / W18D5 add no
  code path.
- **regression risk**: **low** — touched-surface 1079 → 1080
  (+1), 0 failures, 0 skip-change. Full `pytest htt/mio/` 109/109
  in ~1.7 s. Full touched-surface pytest 1080/0/4 in ~35 s.
- **reproducibility**: **passed** — two independent pytest runs
  during W18D7 returned identical test counts.

**C. Numerical verifier**
- **tolerance robustness**: **passed** — W18D1 uses exact string
  equality (`__name__`, hex-subset), exact integer length (`== 16`),
  and exact hash-value equality (`cert.config_hash == digest`);
  no tolerance knob.
- **convergence / stability**: **n/a**.
- **baseline reproducibility**: **passed** — two independent
  pytest runs returned identical test counts; `_hash_config` is
  deterministic.
- **uncertainty / misspecification**: **n/a**.

**D. Dossier verifier**
- **A45.6 ↔ A41.6 cross-references resolve**: **passed** — both
  directions grep clean. `docs/dossier/A45_mio_cache_replay_drift.
  md` references `§A41.6` in the new harness-signature note; `docs/
  dossier/A41_mio_report_type_extension_protocol.md` references
  `§A45.6` in the new step 6.5.
- **A46 cross-references resolve**: **passed** — A41.6, A44.3,
  W15D1, W16 F1, W17 F3 all cite correctly. Relative markdown
  links to sibling dossier files (`A41_*.md`, `A44_*.md`) resolve
  at the same directory level.
- **W17 F1 / F2 / F3 carry-forward closure**: **passed** — F1
  closed by W18D1 (runtime anchor); F2 closed by W18D3 (bidir
  prose cross-link); F3 spec closed by W18D5 (audit-time protocol
  specified; landing trigger deferred to first three-lane
  observation). The §3 carry-forward table rows (in §8) record the
  closures; W18D7 NEXT_SESSION rotation drops them.
- **A46 + W18D1 anchor alignment**: **passed** — W18D1's anchor
  is specifically scoped to the A45.2 helper-name contract; A46
  does not reference `_hash_config` (it is process-hygiene, not
  content-hash). No overlap, no conflict.

---

## 8. Minimal repair plan

No P0 / P1 repair needed. Three opportunistic patches for W19+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | Extend W18D1's anchor with `inspect.signature(_hash_config).parameters` frozen-list assertion so a future keyword-only argument addition (e.g. A43 digest-upgrade `*, digest_length=16`) is caught at anchor-time. | no (P3 docs-↔-code anchor evolution). | F1 — kwarg evolution silently passing the current anchor. | +1 assertion on the existing anchor test. | additive (0 count delta). |
| R2 | Extend §A46.4 with a "steady-state three-lane phrasing" paragraph once the first three-lane observation lands, so the second observer has a paste-ready template. | no (P3 docs lifecycle). | F2 — second-observation audit writes ad-hoc prose. | 0. | additive prose. |
| R3 | A43 digest test landing at first actual schema extension (HJ-03 / HJ-04 / TSC-05 v2). **Unchanged from W15 R3 / W16 R3 / W17 R3 — still gated on trigger arrival.** | no (P3 timing, blocked on external trigger). | W7 FM3 code-side closure. | +2 (one per contract). | additive (+2). |

All three are deferrable; none block W19 execution.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `venv/bin/python -m pytest htt/mio/` →
  109/109 green in ~1.7 s; touched-surface `venv/bin/python -m
  pytest htt/htt/tests/ htt/src/ htt/tsc/{admissibility,diagnostics,
  charts,integration}/ htt/workspace/ htt/mio/` → 1080/0/4 (+1
  over W17 baseline).
- **Edge / adversarial**:
  `test_hash_config_matches_a45_2_pseudocode_shape` (W18D1 —
  imports `_hash_config` by exact name; asserts `__name__`,
  six-arg positional signature, 16-char lowercase-hex output
  shape, and `cert.config_hash == _hash_config(...)` build-↔-
  replay parity on the same payload).
- **Physics sanity**: n/a — no numerical claim landed; the test
  is a docs-↔-code anchor.
- **Regression**: full touched-surface `1080 / 0 / 4` (+1 over
  W17 baseline); MIO contribution 108 → 109; tsc standalone 602
  unchanged.

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W18 세 landings (W17 F1 A45.2
  `_hash_config` docs-↔-code anchor + W17 F2 A45.6 ↔ A41.6
  harness-signature cross-link + A46 three-lane race dossier)
  모두 contract ↔ code ↔ test (해당하는 범위에서) 일관. MIO
  contribution 108 → 109; 전체 touched surface 1079 → 1080.
  **W12 F1 / W14 F1 재발 없음** — §6 W18 check #1 PASSED; 세
  W18 commits 각각 단일 lane-owned path만 포함. 한 개 cross-
  lane 커밋 (`92cefa2` FB-2.3, bass-lane, W18D5 직후 도착) 은
  bass-lane 소유 파일 두 개만 포함 — 우리 세 commits 와 파일
  겹침 영집합. **W18D5의 A46 dossier 는 착지 직후 첫 번째 cross-
  lane 스트레스 테스트를 받아 (concurrent-commit 변종; W16D7
  시나리오의 두 번째 관측) 통과**. 세 lane race (ind-tracks +
  bass + gallery) 은 이번 phase 에 triggered 되지 않음 — W18
  check #2 는 2 lanes 관측, A46.4 first-observation row 템플릿
  미사용.
- **지금 당장 구현/수정할 1개**: 없음. W18 gate 네 항목 전부
  green; W19 active priorities 는 §8 R1–R3 중 하나 (또는 W18
  F1/F2/F3 중 하나를 닫거나 신규 A4x dossier) 로 caller 판단.
- **지금 손대면 안 되는 1개**: A43 digest 테스트의 즉시 착지
  (W15 R3 / W16 R3 / W17 R3 / W18 R3 반복 — trigger 가 아직
  미도착; 현재 schema 에 freeze 하면 첫 확장 PR 이 paste-replace
  를 강요받을 뿐 추가 catch 는 없음). HJ-03 production wiring
  또한 htt W10-02 K_ℓ atlas 착지 전까지 금지 (governing plan
  §17.3 의존 대기 목록; 현재 주 BASS_PY_HTT_TSC_MIO_RESEARCH_
  PLAN.md v3 §17.3 유지).

---

## Week-18 final gate (per NEXT_SESSION §2 Week 18)

- [x] W17 F1 / W17 R1 A45.2 `_hash_config` docs-↔-code anchor
      landed (W18D1 `0d2fc9f`; +1 test; MIO 108 → 109).
- [x] W17 F2 / W17 R2 A45.6 ↔ A41.6 cross-link landed (W18D3
      `23fefbb`; +25 L prose; bidirectional resolution verified).
- [x] One of A46 dossier / MANU-CH03 extension landed — **A46
      picked** (W18D5 `7cc5a42`; new dossier, 182 L; closes W17 F3
      spec with landing trigger deferred to first three-lane
      observation).
- [x] Phase-boundary audit log written (this file); §6 W12 F1 /
      W14 F1 recurrence check returns **PASSED** (`git show
      --stat` on the three W18 commits shows only this lane's
      owned paths; one cross-lane bass-lane commit `92cefa2`
      landed during the window but touched only bass-owned paths
      — zero file overlap with any W18 commit; A46.4's three-lane
      template not triggered this phase — W18 check #2 shows two
      lanes only).
- [x] No touched-surface regressions (1080 passed; +1 over W17;
      0 failed; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W18` closes with
zero new P0/P1/P2 findings; three documented P3 residuals
(F1 / F2 / F3) feed the W19 repair plan.
