# Phase-boundary audit — Independent Tracks Week 14

**Phase tag**: `IND_TRACKS_W14`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12+ continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 14 (cross-producer
σ parity test + A36 → A36a link + HJ-04 → HJ-03 naming sweep +
CatWISE/BiPoSH σ_cone placeholder retirement).
Execution: W14D1 parity test (D1), W14D2 A36 → A36a link (D2),
W14D3 HJ-04 → HJ-03 naming sweep (D3), W14D5 CatWISE retirement
+ placeholder infrastructure (D5), W14D6 BiPoSH retirement (D6),
this audit + NEXT_SESSION rotation (D7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.3.2 row 2 (HJ-02a / HJ-02b probe catalogue);
v3 §4.5.4 (G19 hard separation — unchanged);
v3 §11.14.6 (dossier convention — A36 / A36a / A34 / A40 / A42 cross-refs);
v3 §16.2 FM2 (σ_cone placeholders — CatWISE + BiPoSH legs closed);
W6 FM2 / W11 F3 (σ_cone — code-side retirement half now landed);
W12 F1 (cross-lane contamination — pre-commit gate exercised; see §6);
W13 F1 (HJ-04/HJ-03 naming drift — closed this phase);
W13 F2 (cross-producer σ parity coverage gap — closed this phase);
W13 R3 (A36 → A36a link — landed W14D2);
A36a.5 / A36a.6 (promotion criterion + per-probe tag infrastructure).

**Baseline head**: `833b8ba` (`IND_TRACKS_W13: phase audit +
next-session prompt rotation`). Two intervening cross-lane commits
landed during this phase (`4eb044b`, `e7af284` — both labelled
`FB-1.4: anisotropic_3_curvature 11-type consolidation`); see §6 for
the FM discussion.

**Commits this phase**:

- `W14D1` — `593a7b6` `W14D1: MIO cross-producer sigma parity
  (W13 F2)`. One-file commit appending
  `test_standard_probes_have_consistent_sigma_cone_across_producers`
  to `bass_py/mio/tests/test_probe_name_registry.py` (+37 L). Zips
  `STANDARD_PROBES` (HJ-02a) ↔ `STANDARD_Z_PROBES` (HJ-02b) by
  `.name` and asserts `sigma_cone_deg` / `l_deg` / `b_deg` match
  exactly per probe. MIO contribution 95 → 96.
- `W14D2` — `491ecfd` `W14D2: AUDIT(W13 R3): A36 link to A36a`.
  One-file dossier commit (`docs/dossier/A36_mio_channel_weighting.md`,
  +10 L) — §A36.4 gains a *Provenance anchor (W13D3 / W14D2)*
  paragraph linking to A36a.2 / A36a.3 / A36a.5 and cross-referencing
  the W14D1 parity test.
- `W14D3` — **landed inside** `4eb044b` (FB-1.4 commit; see §6 FM
  discussion). Four-file dossier rename scoped exactly as planned:
  `docs/dossier/A34_g19_cross_check_protocol.md`,
  `docs/dossier/A36_mio_channel_weighting.md`,
  `docs/dossier/A40_g19_architectural_stance.md`,
  `docs/dossier/A42_evidence_anatomy.md`. Rename target: "HJ-04
  evidence anatomy" → "HJ-03 evidence anatomy" (adopting the A32 /
  A41 schema-authoritative binding documented in A42.6); HJ-04 ↔
  `flrw_tension` references intentionally preserved. Post-commit
  gate: `grep -rn "HJ-04 evidence" docs/dossier/` = zero matches.
- `W14D5` — `2951c84` `W14D5: MIO retire CatWISE sigma placeholder
  (A36a.5)`. Six-file commit. New module
  `bass_py/mio/interface/sigma_cone_provenance.py` (75 L) owns the
  A36a.5 promotion SSOT — `PROMOTED_SIGMA_CONE_PROBES:
  frozenset({"CatWISE"})` +
  `PLACEHOLDER_CAVEAT_SUFFIX = "_sigma_cone_plan_placeholder"` +
  `placeholder_caveats_for` / `is_promoted` helpers. Producers
  (`mio.coherence.directional.to_mio_certificate` and
  `mio.coherence.redshift_binned.to_mio_certificate`) updated to
  append per-probe placeholder tags to caller-supplied
  `domain_caveats`, deduplicated. New test file
  `bass_py/mio/tests/test_sigma_cone_provenance.py` (8 tests).
  Paired A36.4 prose update + A36a.2 CatWISE row promotion + A36a.5
  Promotion log + A36a.6 bullets 1 & 2 ticked. MIO contribution
  96 → 104.
- `W14D6` — `9e85d83` `W14D6: MIO retire BiPoSH sigma placeholder
  (A36a.5)`. Three-file commit extending the promoted set from
  `{"CatWISE"}` to `{"BiPoSH", "CatWISE"}`; +1 test
  (`test_promoted_set_contains_biposh_post_w14d6`) pinning the
  W14D6 post-state and guarding against accidental demotion of
  `CMB` / `Radio` / `CF4pp`; paired A36a.2 BiPoSH row promotion +
  A36a.5 Promotion log row. MIO contribution 104 → 105.
- `W14D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1075 passed, 0 failed, 4 skipped**. Week 14 delta
vs Week 13 (1065 / 0 / 4): **+10 tests pass (all from this lane —
+1 W14D1, +8 W14D5, +1 W14D6), 0 skip change, 0 regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed
(unchanged from W13 — no TSC code change this week).

**MIO contribution**: 105 tests (+10 vs W13's 95; gate ≥ 47 met
with 58 to spare). Composition: 19 directional-coherence (W6) +
8 certificate-generator (W6) + 5 boot (W6) + 5 bridges (W6/W7) +
5 masked-sky (W6) + 4 masked-sky APPLY-BIAS-AMP (W12D2) +
19 HJ-01 (W10D3) + 15 HJ-02b z-binned-coherence (W11D3) +
6 HJ-02b exact-enumeration (W12D3) + 8 A37 grammar (W12D1) +
7 A37.3 PROBE_ID registry (W13D2 6 + W14D1 1 cross-producer σ
parity, shared file) + 9 A36a.5 sigma-cone-provenance (W14D5 8 +
W14D6 1). Cross-check: `pytest bass_py/mio/ --collect-only -q |
tail -1` = `105 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY), 1 × `fig_certification_matrix` family
(W9), 1 × `test_bulkflow_likelihood.py:303` dynesty contract guard
(W10D1).

---

## 1. Audit target reconstruction

Five landings, three distinct audit targets.

### W14D1 — cross-producer σ_cone parity (closes W13 F2)

- **Core claim**: whenever `STANDARD_PROBES` and `STANDARD_Z_PROBES`
  share a PROBE_ID, the three direction-on-sky fields
  (`sigma_cone_deg`, `l_deg`, `b_deg`) must match exactly; a paired
  update that drifts only one producer will fail CI.
- **Algorithm**: dict-build by `.name` on both producer SSOTs, set-
  equality on the name sets, per-name equality on the three
  direction fields. `z_eff` intentionally excluded (HJ-02a is
  z-agnostic per A36.1).
- **Output**: +1 test in `bass_py/mio/tests/test_probe_name_registry.py`
  (shared file; keeps the A37.3 / parity gates in one place).

### W14D2 — A36 § A36.4 ↔ A36a provenance link (closes W13 R3)

- **Core claim**: a reader arriving at A36 §A36.4 should have a
  one-hop link to A36a's per-PROBE_ID literature record, §A36a.3
  Δ table, and §A36a.5 retirement criterion.
- **Algorithm**: documentation; a ten-line paragraph inserted at the
  bottom of §A36.4.
- **Output**: `docs/dossier/A36_mio_channel_weighting.md` +10 L.

### W14D3 — cross-dossier HJ-04 → HJ-03 sweep (closes W13 F1)

- **Core claim**: A32 and A41 (schema-authoritative, binding
  `report_type` strings to HJ numbers) consistently use
  `HJ-03 ↔ evidence_anatomy` and `HJ-04 ↔ flrw_tension`; the tabular
  dossiers (A34, A36, A40) were historically labelling evidence-
  anatomy as HJ-04, generating reader confusion documented in
  W13D5 A42.6. Post-sweep all five dossiers agree.
- **Algorithm**: targeted text replacement — nine occurrences across
  four files (A34 ×3, A36 ×3 including §A36.1 bullet and §A36.3
  heading, A40 ×3, A42 §A42.3 parenthetical + §A42.6 closure
  paragraph). HJ-04 ↔ `flrw_tension` references (A41, A42.6) left
  intact.
- **Output**: 4 dossier files touched, net +22 L / −22 L (per the
  commit stat inside `4eb044b`, see §6 FM discussion).

### W14D5 — CatWISE σ_cone placeholder retirement (A36a.5 #1)

- **Core claim**: (a) `*_sigma_cone_plan_placeholder` is now a real
  runtime contract, not dossier prose — HJ-02a / HJ-02b certificates
  carry one tag per non-promoted probe; (b) CatWISE is promoted
  per A36a.5's three-condition rule (Δ = +0.1°; DOI-anchored to
  Secrest+2021 arXiv:2009.14826; paired dossier + code commit).
- **Algorithm**:
  `placeholder_caveats_for(names)` = sorted deterministic list of
  `"{name}_sigma_cone_plan_placeholder"` for `name ∉
  PROMOTED_SIGMA_CONE_PROBES`. Producers call it over
  `(p.name for p in probes)` and append non-duplicate results to
  the caller's `domain_caveats`. Frozen `frozenset` prevents
  runtime mutation.
- **Output**:
  + `bass_py/mio/interface/sigma_cone_provenance.py` (new, 75 L);
  + `bass_py/mio/tests/test_sigma_cone_provenance.py` (new, 8 tests);
  + 3-line wiring patches in
    `bass_py/mio/coherence/{directional,redshift_binned}.py`;
  + A36a.2 CatWISE row promotion status + §A36a.5 Promotion log +
    §A36a.6 bullet 2 tick;
  + A36.4 prose update — flagged list now `{Radio, CF4++, CMB}`
    (three, not three-of-five; post-W14D6 matches A36a.5 narrative).

### W14D6 — BiPoSH σ_cone placeholder retirement (A36a.5 #2)

- **Core claim**: BiPoSH meets A36a.5's three-condition rule
  (Δ within the Planck 2015 XVI arXiv:1506.07135 cone range of
  15-25°; paired dossier + code commit). Promotion set extends to
  `{"BiPoSH", "CatWISE"}`; remaining flagged set is
  `{CMB, Radio, CF4pp}` per §A36a.5 narrative.
- **Algorithm**: same as W14D5 with the promoted set extended;
  new test pins `BiPoSH ∈ set` AND `{CMB, Radio, CF4pp} ∩ set = ∅`
  so a future accidental demotion of a flagged probe trips the gate.
- **Output**: 3 files (provenance module, test, A36a.2 BiPoSH row +
  §A36a.5 Promotion log).

---

## 2. Contract / interface audit

| Surface | Before W14 | After W14 | Δ |
|---|---|---|---|
| `MioCertificate` dataclass schema | v1, hash-frozen per A32.5 | unchanged | 0 |
| `domain_caveats` emission contract | caller-supplied only | caller-supplied + auto-appended per-probe `{PROBE_ID}_sigma_cone_plan_placeholder` (deduplicated) for HJ-02a / HJ-02b producers | **+auto-tag wiring** |
| A37.2 / A37.3 probe surface | frozen | unchanged | 0 |
| Cross-producer σ_cone parity | ungated (W13 F2) | gated by `test_standard_probes_have_consistent_sigma_cone_across_producers` | **+regression gate** |
| A36a.5 promotion SSOT | markdown-only | code-side `PROMOTED_SIGMA_CONE_PROBES` frozenset + paired dossier rows | **+code mirror** |
| Tabular HJ-04 evidence-anatomy label in A34 / A36 / A40 | drifted from A32 / A41 | renamed to HJ-03 | **RESOLVED** (W13 F1) |

All extensions are additive. No schema-hash rotation, no field
retype, no field removal. The `domain_caveats` list was already a
`List[str]`; auto-appending tags before `build_mio_certificate` does
not change the field type or the certificate hash (payload content
changes but the schema doesn't).

---

## 3. Phys-math audit

### Cross-producer σ_cone parity (W14D1)

Five PROBE_IDs, three equality assertions each (σ_cone_deg / l_deg /
b_deg) = 15 exact-equality checks. Current tree values:

| PROBE_ID | l_deg | b_deg | σ_cone_deg | (HJ-02a, HJ-02b agree) |
|---|---:|---:|---:|:---:|
| `CMB` | 264.021 | 48.253 | 0.5 | ✓ |
| `CatWISE` | 238.2 | 28.8 | 6.0 | ✓ |
| `Radio` | 251.0 | 38.0 | 10.0 | ✓ |
| `CF4pp` | 289.0 | 30.0 | 15.0 | ✓ |
| `BiPoSH` | 220.0 | 65.0 | 20.0 | ✓ |

No physical claim is being made beyond A36.1 / A36a (already audited
W13). The test is a code-path invariant: any future edit that drifts
one producer's dataclass fails the gate.

### Placeholder-tag arithmetic (W14D5 + W14D6)

- Post-W14D5: `PROMOTED = {CatWISE}`; flagged =
  `{BiPoSH, CF4pp, CMB, Radio}`; tag count per
  `STANDARD_PROBES = 4`.
- Post-W14D6: `PROMOTED = {BiPoSH, CatWISE}`; flagged =
  `{CF4pp, CMB, Radio}`; tag count per `STANDARD_PROBES = 3`.
- `placeholder_caveats_for` output is ASCII-alphabetical →
  bit-identical certificate JSON across two successive runs
  (`test_placeholder_caveats_for_is_deterministic_and_sorted`).

No floating-point arithmetic in this layer; all string operations.

### HJ-03/HJ-04 naming consistency (W14D3)

Post-sweep invariants:
- `grep -rn "HJ-04 evidence" docs/dossier/` = 0 matches.
- `grep -rn "HJ-03 evidence" docs/dossier/` matches in A34 / A36 /
  A40 (renamed) + A41 (already correct) + A42 (closure note).
- HJ-04 ↔ `flrw_tension` bindings in A41 (§A41.2 line 32 and §A41.4)
  and A42.6 preserved.

---

## 4. Code path audit

- **W14D1** test is a pure-Python dict-build + per-key equality
  loop; no numpy, no dossier-file I/O, no import beyond the two
  coherence-module SSOTs. Deterministic and O(5).
- **W14D5 / W14D6** `mio.interface.sigma_cone_provenance` imports
  only `typing.FrozenSet, Iterable, List`. No side-effects at
  import. The producer integration is two-line:
  `for placeholder in placeholder_caveats_for(...): if ... append`
  — exercised by the two existing `test_to_mio_certificate_*`
  tests (which still pass since they don't assert an empty caveats
  list) plus six new test assertions on the tag shape.
- The producer change does NOT alter the `probe_name` concatenation
  (A37.2 alphabetical-bundle rule) nor the `reduction_status`
  binding — both remain `'diagnostic-only'` for HJ-02a / HJ-02b
  per A36.1 design.
- No `bass_py/bass/*` file touched (lane discipline); no
  `plots/physics_gallery/` file touched (gallery-lane discipline).

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (no numerics landed this phase). |
| Tolerance sensitivity | W14D1 parity uses set-equality and `==`; no tolerance. |
| Underflow / overflow | n/a — string / bool / dict surface only. |
| Conditioning | n/a. |
| Cache / state leakage | `PROMOTED_SIGMA_CONE_PROBES` is a module-level immutable frozenset; `placeholder_caveats_for` returns a fresh list per call. |
| Seed / reproducibility | n/a (deterministic pure functions). |
| Baseline reproduction | `pytest bass_py/mio/` = 105/105 green in ~1.7 s; touched-surface 1075/0/4 (+10). |
| OOD / misspecification | `placeholder_caveats_for` passes unregistered names through (they fail the A37.3 registry gate upstream in `probe_name_registry`); `is_promoted` is strict-equality only. |

---

## 6. Ranked failure modes (P0–P3)

Per the NEXT_SESSION §2 Week 14 Day 7 directive this section MUST
include (a) a W12 F1 cross-lane-contamination recurrence check and
(b) a verification that the W13D1 pre-commit `git status --short`
gate was followed on every W14 commit.

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| W14 check #1 | **FAILED (documented)** | process (W12 F1 recurrence) | W14D3's four staged dossier files (`docs/dossier/A34_*.md`, `A36_*.md`, `A40_*.md`, `A42_*.md`) landed inside commit `4eb044b` whose subject line reads `FB-1.4: anisotropic_3_curvature 11-type consolidation (Phase FB-1 exit)`. `git show --stat 4eb044b` proves the commit contains **only** the four dossier paths (31 insertions / 31 deletions) with zero bass-lane or gallery-lane paths, despite the FB-1.4 subject line. The bass-lane then re-fired their content in a separate commit `e7af284` carrying the actual six-file FB-1.4 payload. | concurrent staging race: at the moment the other lane's `git commit` ran, the index contained only this lane's reset-then-restaged W14D3 dossier files; their commit ate whatever was in the index. Symmetric to the W12D3 `99465e5` pattern but with the lane roles reversed. | the W13D1 pre-commit `git status --short` gate catches contamination *into* this lane's commits but cannot catch commits from another lane that run in the brief window between our `git reset` and our `git commit`. A stronger mitigation would be per-file-path staging on both lanes (scoped `git add` + scoped `git commit -- <paths>`) OR a repo-level staging lock. | a reader of `git log --oneline` will see no `W14D3` commit and conclude the rename never landed; `git show --stat 4eb044b` is necessary to find the actual W14D3 work. |
| W14 check #2 | **PASSED** | process (gate-followed verification) | Per `git show --stat 593a7b6 491ecfd 2951c84 9e85d83` (the four in-lane W14 commits): W14D1 = 1 file changed; W14D2 = 1 file changed; W14D5 = 6 files changed; W14D6 = 3 files changed. Every file belongs to this lane's owned surface (`bass_py/mio/*`, `docs/dossier/*`); no bass-lane (`bass_py/bass/*`) or gallery-lane (`plots/physics_gallery/*`, `scripts/make_physics_gallery.py`) files pulled in. | the W13D1 pre-commit `git status --short` gate worked as designed on the four clean commits. | n/a — positive finding. | the contamination-gate assertion holds per-commit, not per-phase; the W14D3 race (check #1) is a separate failure mode. |
| F1 | **P2** | process | The W12 F1 recurrence mitigation relies on per-session pre-commit diligence, but the W14D3 race demonstrates two concurrent lanes can still collide if they stage + reset + commit on overlapping time windows. | no inter-lane coordination beyond the memory-level convention "additive commits only". | option (a): per-commit scoped `git add` + `git commit -- <paths>` (tell git the exact paths at commit time — refuses to pull in unstaged files); option (b): one lane at a time (single writer convention for any given calendar hour). (a) is cheaper and preserves parallel work. | a future W15 session's commit could be mis-labelled identically to W14D3's. |
| F2 | **P3** | coverage | `test_hj02a_certificate_carries_placeholder_tags_for_non_promoted_probes` uses `issubset` rather than set-equality: an implementation that emits *extra* placeholder tags (e.g. for an unregistered name) would pass. | deliberate: leaves room for caller-supplied caveats to coexist. | optional follow-up — assert tag count == expected_flagged set size when no caller caveats are supplied. | a producer that over-emits would not be caught by these eight tests. |
| F3 | **P3** | coverage | A36a.3 literature Δ summary table is still not programmatically tested (inherited W13 F4 carry-forward). A future σ_cone edit that drifts the dossier claim remains silent. | dossier contains plain-English numerical claims; mechanising them would require a YAML / JSON sidecar parser. | not a blocker — the W14D1 cross-producer parity test prevents a *producer-level* silent drift; the W13 F4 risk remains only for *literature-level* drift. | a reviewer citing A36a.3 might over-trust numbers that the code silently changed. |
| F4 | **P3** | docs | The A36a.2 CatWISE row (pre-W14D5) previously read "No placeholder flag warranted"; W14D5 overwrote it with the promotion-log entry. A reader arriving via an old PR comment linking to the pre-W14D5 line would find different content. | dossier versioning is commit-history only (no row-level changelog). | optional: preserve the pre-W14D5 status as a short historical line. | minor; zero code impact. |

**No P0 / P1 items found.** W14 check #1 (W12 F1 recurrence) is a
genuine FAILED finding, documented as F1 **P2** with a concrete
mitigation path. The rename content itself is bit-identical to what
W14D3 intended; only the commit label is wrong.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **passed** — CatWISE σ=6.0° matches
  Secrest+2021 bootstrap 5.9° within 0.1° (A36a.2); BiPoSH σ=20.0°
  sits at the midpoint of the Planck 2015 XVI 15-25° cone range.
- **dimensional consistency**: **n/a** — string / bool surface.
- **sign / normalization**: **n/a**.
- **positivity / admissibility**: **passed** — frozenset membership
  is a closed predicate.

**B. Code verifier**
- **contract satisfaction**: **passed** — `PROMOTED_SIGMA_CONE_PROBES`
  is `FrozenSet[str]`; mutation impossible.
  `placeholder_caveats_for` output is deterministic, sorted, and
  suffix-terminated (three tests).
- **actual code-path usage**: **passed** — both
  `mio.coherence.directional.to_mio_certificate` and
  `mio.coherence.redshift_binned.to_mio_certificate` exercise the
  helper; both HJ-02a and HJ-02b certificate emissions are covered
  by integration tests.
- **regression risk**: **low** — touched-surface 1065 → 1075 (+10),
  0 failures, 0 skip-change. Full `bass_py/mio/` suite 105/105
  in ~1.7 s.
- **reproducibility**: **passed** — tag list sorting guarantees
  cross-run bit-identity.

**C. Numerical verifier**
- **tolerance robustness**: **n/a**.
- **convergence / stability**: **n/a**.
- **baseline reproducibility**: **passed** — two independent pytest
  runs during the W14D5 landing returned identical test counts.
- **uncertainty / misspecification**: **n/a**.

**D. Dossier verifier**
- **W14D2 A36 → A36a link resolves**: **passed** — relative
  markdown link in A36.4 resolves to `A36a_sigma_cone_literature.md`
  at the same directory level.
- **W14D3 HJ-04/HJ-03 sweep self-consistency**: **passed** —
  `grep -rn "HJ-04 evidence" docs/dossier/` returns zero; A42.6
  closure note cross-references the three renamed files; A41
  HJ-04 ↔ `flrw_tension` binding preserved.
- **W14D5 / W14D6 A36a.5 cross-references resolve**: **passed** —
  every mention of `PROMOTED_SIGMA_CONE_PROBES` in A36a /
  A36.4 points at
  `bass_py/mio/interface/sigma_cone_provenance.py` (file exists).
- **A36a.6 checklist accurate**: **passed** — bullets 1 and 2
  ticked with landing-commit shas; bullet 3 (MANU-CH12 §12.2 DOI
  citation) correctly left open.

---

## 8. Minimal repair plan

No P0 / P1 repair needed. Four opportunistic patches for W15+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | Per-commit scoped `git commit -- <paths>` convention on both lanes (in-lane durable memory entry + cross-lane handoff note). | **yes (P2)** | F1 — W12 F1 recurrence via the W14D3 race pattern. | n/a (process). | zero. |
| R2 | Tighten `test_hj02a_certificate_carries_placeholder_tags_for_non_promoted_probes` to assert tag count equals `|flagged set|` when no caller caveats are supplied. | no (P3). | F2 — catches over-emission. | optional (+1). | zero; additive. |
| R3 | YAML sidecar for A36a.3 literature Δ table + a parser-backed test that σ_code values in `STANDARD_PROBES` agree with the table's "C" column per probe. | no (P3). | F3 — catches code-vs-dossier literature-Δ drift. | optional (+1). | additive. |
| R4 | CMB σ = 0.5° placeholder retirement candidate review. A36a.5 explicitly excludes CMB from the W14-ready set, but a future decision to promote with "catalogue-conservative by 50x" justification would be a one-line `PROMOTED_SIGMA_CONE_PROBES` extension + A36a.2 CMB-row edit. | no (P3 decision). | removes the last non-physical-drift placeholder. | optional (+0 to +1). | additive. |

All four are deferrable; none block W15 execution.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `pytest bass_py/mio/` → 105/105 green
  in ~1.7 s.
- **Edge / adversarial**:
  `test_standard_probes_have_consistent_sigma_cone_across_producers`
  (one drift-direction-or-axis value break fails the gate);
  `test_is_promoted_rejects_typos` (strict equality, no case fold);
  `test_placeholder_caveats_for_is_deterministic_and_sorted`
  (input-order permutation invariance);
  `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags`
  (dedup on caller-provided placeholder).
- **Physics sanity**: n/a — no numerical claim landed; literature
  agreement is asserted via A36a.2 prose citations.
- **Regression**: full touched-surface `1075 / 0 / 4` (+10 over
  W13 baseline).

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W14 다섯 landings (cross-producer σ
  parity + A36 link + HJ-04/HJ-03 sweep + CatWISE 퇴역 + BiPoSH 퇴역)
  모두 contract ↔ code ↔ test 일관. MIO contribution 95 → 105.
  **W12 F1 재발 발생함** — W14D3가 다른 lane의 FB-1.4 commit에
  흡수되어 mislabelled; 내용은 bit-identical하지만 커밋 라벨이
  틀림. §6 W14 check #1 FAILED로 기록, §8 R1에 mitigation path
  (per-commit scoped `git commit -- <paths>`) 제안. W13D1 pre-commit
  gate는 네 in-lane 커밋(W14D1, D2, D5, D6)에 대해 정상 동작
  (§6 W14 check #2 PASSED).
- **지금 당장 구현/수정할 1개**: 없음. F1 (W12 F1 재발)은 process
  개선 사안이며, rename 내용 자체는 이미 commit tree에 존재.
- **지금 손대면 안 되는 1개**: `bass_py/mio/coherence/*`의 실제
  `sigma_cone_deg` 숫자 값. A36a.4 "caller's judgement" 원칙은
  W14D5/D6 placeholder 퇴역 이후에도 유효 — 퇴역은 **caveat flag**
  를 제거할 뿐 σ 값을 변경하지 않는다. σ 숫자 변경은 별도 커밋 +
  A36a.2 행 + 회귀 rationale 번들로 진행해야 함.

---

## Week-14 final gate (per NEXT_SESSION §2 Week 14)

- [x] W13 F2 cross-producer σ parity test landed (+1 MIO test;
      MIO contribution 95 → 96 after W14D1, 96 → 105 after W14D5/D6).
- [x] W13 F1 naming sweep landed (W14D3; all three dossier files +
      A42 closure note updated). Note: landed inside cross-lane
      commit `4eb044b` — see §6 W14 check #1.
- [x] At least one A36a.5 placeholder retirement landed — **two
      landed** (W14D5 CatWISE + W14D6 BiPoSH), exceeding gate.
- [x] Phase-boundary audit log written (this file); §6 includes
      W12 F1 recurrence check (**FAILED, documented**) and the
      W14 in-lane pre-commit-gate verification (**PASSED**).
- [x] No touched-surface regressions (1075 passed; +10 over W13;
      0 failed; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W14` closes with one
documented process finding (F1 P2) for W15 mitigation.
