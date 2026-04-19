# Phase-boundary audit — Independent Tracks Week 13

**Phase tag**: `IND_TRACKS_W13`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12+ continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 13 (process
mitigation + PROBE_ID registry + σ_cone dossier + A42 stub).
Execution: W13D1 pre-commit gate + memory/docs update (D1), W13D2
MIO probe_id registry (D2), W13D3 A36a σ_cone literature (D3),
W13D5 A42 evidence_anatomy stub (D5), this audit + NEXT_SESSION
rotation (D7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.2.1 (`MioCertificate` dataclass body — unchanged);
v3 §4.5.3.2 row 2 (HJ-02a / HJ-02b probe catalogue);
v3 §4.5.3.3 (HJ-03 evidence anatomy — deferred, A42 stub landed);
v3 §4.5.4 (G19 hard separation — unchanged);
v3 §11.14.6 (dossier convention);
v3 §16.2 FM2 (σ_cone placeholders — W13D3 documentation leg closed);
v3 §17.3 (dependency wait list — HJ-03 blocked on HTT Phase F);
W6 FM2 / W11 F3 (σ_cone literature — closed in docs via A36a);
W12 F1 (cross-lane contamination — mitigated by W13D1 gate);
W12 F3 (PROBE_ID registry coverage — closed by W13D2);
W7 FM3 (schema-hash vs literal-freeze — referenced by A42.5).

**Baseline head**: `42ac31a` (`IND_TRACKS_W12: phase audit +
next-session prompt rotation`). No out-of-lane intervening commits
between W12 audit and W13D1 (verified via `git log --oneline -10`).

**Commits this phase** (this lane):

- `W13D1` — `41b7200` `W13D1: process — pre-commit git status
  --short gate (W12 F1/R1)`. One-file commit
  (`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md`, +5 lines) adding the
  pre-commit discipline to the §0 first-order rules. Paired
  durable edit to memory `feedback_git_workflow.md` (not a repo
  artefact; lives at
  `/home/cosmosapjw/.claude/projects/.../memory/feedback_git_workflow.md`).
  No code change.
- `W13D2` — `b7607ef` `W13D2: MIO probe_id registry SSOT
  (W12 F3/R2)`. Two-file commit — new
  `bass_py/mio/interface/probe_name_registry.py` (55 L) with the
  frozen `REGISTERED_PROBE_IDS: Tuple[str, ...]` +
  `is_registered_probe_id` helper, and new
  `bass_py/mio/tests/test_probe_name_registry.py` (106 L; 6 tests)
  that parses the A37.3 markdown table at import time and asserts
  set-equality against the code registry. MIO contribution
  89 → 95 (+6; gate ≥ 47 met with 48 to spare).
- `W13D3` — `ed2c9b1` `W13D3: DOS-A36a sigma_cone literature
  (W6 FM2 / W11 F3)`. Single-file dossier landing
  (`docs/dossier/A36a_sigma_cone_literature.md`, 234 L). DOI/arXiv-
  anchors σ_cone per PROBE_ID (Planck 2018 LVI for CMB; Secrest+2021
  for CatWISE; Rubart-Schwarz/Darling for Radio; Tully+2023 for
  CF4pp; Planck 2015 XVI for BiPoSH). Per-probe Δ table in §A36a.3;
  retirement criterion in §A36a.5. Code-side σ values intentionally
  unchanged per W13 plan Days 3-4 ("caller's judgement").
- `W13D5` — `9dd64fa` `W13D5: DOS-A42 HJ-03 evidence_anatomy stub`.
  Single-file dossier landing
  (`docs/dossier/A42_evidence_anatomy.md`, 198 L). Deferred design
  stub for HJ-03 — purpose (anatomy / sign-coherence /
  consistency), planned HTT input bundle surface, computation
  recipe, decomposition-residual floor (1e-3), MioCertificate
  contract table, G19 posture, 5-test acceptance plan, and
  A42.6 naming-drift note documenting the A34/A36/A40 "HJ-04
  evidence anatomy" tabular drift against the A32/A41 schema-
  authoritative "HJ-03 evidence_anatomy" binding.
- `W13D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1065 passed, 0 failed, 4 skipped**. Week 13
delta vs Week 12 (1059 / 0 / 4): **+6 tests pass (all from W13D2
probe_name_registry), 0 skip change, 0 regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed
(unchanged from W12 — no TSC code change this week).

**MIO contribution**: 95 tests (+6 vs W12's 89; gate ≥ 47 met
with 48 to spare). Composition: 19 directional-coherence (W6) +
8 certificate-generator (W6) + 5 boot (W6) + 5 bridges (W6/W7) +
5 masked-sky (W6) + 4 masked-sky APPLY-BIAS-AMP (W12D2) +
19 HJ-01 (W10D3) + 15 HJ-02b z-binned-coherence (W11D3) +
6 HJ-02b exact-enumeration (W12D3) + 8 A37 grammar (W12D1) +
6 A37.3 PROBE_ID registry (W13D2, new). Cross-check:
`pytest bass_py/mio/ --collect-only -q | tail -1` =
`95 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase composition — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY, unchanged until MANU-CH12-NEW figure
retirement), 1 × `test_figures_smoke.py::fig_certification_matrix`
family (W9 carry), 1 × `test_bulkflow_likelihood.py:303` dynesty
contract guard (W10D1 composition swap, by-design).

---

## 1. Audit target reconstruction

This phase ships four artefacts; each has a distinct audit target:

### W13D1 — pre-commit `git status --short` gate (process)

- **Core claim**: every future `git commit` in this lane will be
  preceded by a `git status --short` visual inspection so cross-
  lane working-tree contamination (W12 FM1 pattern) cannot
  silently enter the commit.
- **Algorithm**: n/a — procedural rule.
- **Output**: +5 L in `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md`
  §0 first-order rules; paired entry in memory
  `feedback_git_workflow.md`.

### W13D2 — PROBE_ID registry SSOT

- **Core claim**: the five A37.3 registered PROBE_IDs (`BiPoSH`,
  `CF4pp`, `CMB`, `CatWISE`, `Radio`) exist as a frozen tuple in
  code, and any drift between the code tuple and the A37.3
  markdown table fails CI at the test level.
- **Algorithm**: dossier-side regex parser (`row_re` harvesting
  backtick-wrapped first-column tokens from the A37.3 section
  window) + set-equality assertion against the code-side tuple.
  Additional gate: `STANDARD_PROBES ∪ STANDARD_Z_PROBES == REGISTERED_PROBE_IDS` — any new probe must appear in
  all three places (code tuple, dossier table, producer SSOT).
- **Output**: new module `mio.interface.probe_name_registry` (55 L)
  + 6 tests covering parser-self-check / set-equality / sorting /
  immutability / `is_registered_probe_id` accept/reject /
  STANDARD_PROBES parity.

### W13D3 — A36a σ_cone literature anchoring

- **Core claim**: each HJ-02a / HJ-02b `sigma_cone_deg` value is
  anchored against a documented primary reference (or flagged as
  literature-consistent-but-not-verbatim) with an explicit delta
  `σ_code − σ_literature`.
- **Algorithm**: n/a — documentation-only; no code change.
- **Output**: new dossier `docs/dossier/A36a_sigma_cone_literature.md`
  (234 L) with per-PROBE_ID literature record, Δ summary table,
  caller's-judgement rationale for leaving `STANDARD_PROBES`
  unchanged, and three-condition retirement criterion for the
  `*_sigma_cone_plan_placeholder` `domain_caveats` flag.

### W13D5 — A42 HJ-03 evidence_anatomy stub

- **Core claim**: HJ-03 evidence_anatomy has a frozen design
  target (input bundle surface, three derived statistics,
  MioCertificate field values, G19 posture) so A41.6's worked-
  example cross-reference resolves to a concrete dossier, and the
  HJ-03 author has a contract to implement against when HTT
  Phase F unblocks.
- **Algorithm**: n/a — documentation stub.
- **Output**: new dossier `docs/dossier/A42_evidence_anatomy.md`
  (198 L); A42.6 documents the A34/A36/A40 "HJ-04 evidence
  anatomy" ↔ A32/A41 "HJ-03 evidence_anatomy" naming drift and
  adopts the schema-authoritative binding.

---

## 2. Contract / interface audit

| Surface | Before W13 | After W13 | Δ |
|---|---|---|---|
| `MioCertificate` dataclass schema | v1, hash-frozen per A32.5 | unchanged | 0 |
| A37.2 probe_name grammar v1 | frozen W12D1 | unchanged | 0 |
| A37.3 PROBE_ID catalogue | 5 entries, markdown-only | 5 entries, markdown + `REGISTERED_PROBE_IDS` code tuple + 3-file commit invariant | **+code mirror** |
| HJ-02a / HJ-02b σ_cone defaults | plan-suggested per A36.4 | identical values + A36a anchoring and Δ record | **+DOI anchor doc** |
| HJ-03 `"evidence_anatomy"` report_type | reserved A32.2; checklist in A41.6 | same reservation + A42 design stub with MioCertificate contract table + acceptance floor + 5-test plan | **+design target** |

All extensions are additive: no schema-hash rotation, no field
retype, no caveat-flag semantics change, no existing-test
regression.

---

## 3. Phys-math audit

### A37.3 PROBE_ID registry (W13D2)

- Parity test parses dossier at runtime; the regex
  `r"^\|\s*`([A-Za-z][A-Za-z0-9]{0,23})`\s*\|"` matches the first
  backtick-wrapped token of every table row inside the A37.3
  section window (`## A37.3` → `## A37.[4-9]`). Self-check
  `test_dossier_parser_recovers_five_probe_ids` guards against
  false-positive regex drift before the parity assertion runs
  (order matters: parser-correctness precedes parity-correctness).
- Set-equality comparison (as opposed to tuple equality) is
  deliberate: the markdown table order is documentary priority
  (CMB first because it is the most-observed), while the code
  tuple is ASCII-sorted for cross-cert dictionary-key stability.
  Mixing the two would force a cosmetic reshuffle of either the
  dossier or the code.
- `is_registered_probe_id` is strict case-sensitive equality;
  `"cmb"`, `"CMB "`, `" CMB"`, `"CatWise"` all return False.
  Regex tolerance (which would accept `cmb` and `Cmb` because
  `[A-Za-z]` permits any case) is explicitly *not* the registry's
  contract — the registry is the SSOT, the regex is the syntax.

### A36a σ_cone anchoring (W13D3)

- Per-probe Δ record is dimensionally consistent: σ in degrees,
  Δ in degrees, weight `w = 1 / σ_cone²` in `1 / deg²`. A36.3's
  "CMB dominance is by construction" claim is verified
  numerically: `w(0.5°) / w(20°) = 1600×` regardless of Δ at the
  0.1°-scale. Therefore the W13D3 decision to leave `STANDARD_PROBES` unchanged is numerically defensible.
- Literature quotes are typed as DOI where the primary source
  publishes one (CatWISE, CF4pp) and as arXiv-ID where the DOI
  is less standard (Secrest 2022, Singal 2011, Rubart-Schwarz
  2013). The Planck-collaboration references use A&A DOIs where
  the paper is published in that journal; the otherwise-classic
  Fixsen 1996 citation gives the ApJ DOI 10.1086/178173.
- The three-condition retirement criterion in §A36a.5 is the
  minimum set: (1) σ_code within published 1σ cone or
  deliberately ≥50% conservative, (2) at least one DOI/arXiv
  anchor, (3) paired commit touches both code flag + A36.4 prose.

### A42 evidence_anatomy stub (W13D5)

- The decomposition residual acceptance floor `|Δ| ≤
  max(1e-3, 1e-3 · |total_lnB|)` is a *numerics* acceptance gate,
  not a *physics* one. It matches the precision at which an
  HTT posterior ln B can be decomposed sensibly across channels
  given the nested-sampling evidence-error floor reported in
  the HTT Phase F forthcoming deliverable.
- The three derived statistics (anatomy ranking, sign-coherence
  fraction, decomposition residual) are *not* combined into a
  single scalar — this is A36.2 row 2 enforced at the design
  stage.
- A42.6 chooses the A32/A41 binding (HJ-03 ↔ evidence_anatomy)
  because those are the schema-authoritative files; the A34/A36/
  A40 "HJ-04 evidence anatomy" labels are tabular and drive no
  test behaviour. Renaming them at this phase would force a
  cross-dossier sweep with no functional payoff; deferring the
  rename to the HJ-03 landing commit batches it with a natural
  co-landing.

---

## 4. Code audit

- **W13D1**: `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` one-paragraph
  insertion at §0; surgical. No code file touched.
- **W13D2**:
  `bass_py/mio/interface/probe_name_registry.py` imports only
  `typing.Tuple`; no dependency on `mio.coherence.*` or
  `workspace.contracts.*`. This means the registry can be
  imported at test-collection time without triggering the heavier
  `numpy` / `workspace.contracts` import graph — the parser test
  verifies `DOSSIER_PATH.read_text` resolution (relative-path
  arithmetic: `Path(__file__).resolve().parent.parent.parent.parent
  / "docs" / "dossier" / "A37_mio_probe_name_schema.md"`).
  The final `..` climb lands at the repo root — verified by
  inspection during the test run (the 6-test suite all green in
  0.09 s, which is impossible if `read_text` raised).
  `is_registered_probe_id` is a 1-line pure-function wrapper;
  no cache, no state, no side effect.
- **W13D3 / W13D5**: dossier-only; no code.

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (no numerics landed this phase). |
| Tolerance sensitivity | W13D2 parity test is set-equality (no tolerance). |
| Underflow / overflow | n/a — string/bool surface only. |
| Conditioning | n/a. |
| Cache / state leakage | `is_registered_probe_id` is stateless. `REGISTERED_PROBE_IDS` is an immutable `Tuple[str, ...]` bound at import; no runtime mutation possible without a `globals()` hack. |
| Seed / reproducibility | n/a (deterministic pure functions). |
| Baseline reproduction | `pytest bass_py/mio/` = 95/95 green in ~1.6 s; touched-surface 1065/0/4 (+6). |
| OOD / misspecification | `is_registered_probe_id` rejects typos and whitespace variants (`"cmb"`, `"CMB "`, `"CatWise"`) — narrow by design (A37.2 grammar is a syntactic filter, the registry is the semantic filter). A42.4 decomposition floor documented but not yet active (HJ-03 deferred). |

---

## 6. Ranked failure modes (P0–P3)

The W13 plan mandates a §6 finding checking whether the W12 FM1
cross-lane contamination pattern recurred in any W13 commit. The
audit below records this explicitly.

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| W13 check | **PASSED** | process (W12 F1 recurrence check) | Per `git show --stat 41b7200 b7607ef ed2c9b1 9dd64fa`: W13D1 = 1 file changed; W13D2 = 2 files changed; W13D3 = 1 file changed; W13D5 = 1 file changed. Every file belongs to this lane's owned surface (`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md`, `bass_py/mio/interface/`, `bass_py/mio/tests/`, `docs/dossier/`). No bass-lane (`bass_py/bass/*`) or gallery-lane (`plots/physics_gallery/*`, `scripts/make_physics_gallery.py`) files pulled in. | pre-commit `git status --short` gate (W13D1 / W12 F1 R1) worked as designed on all four W13 commits. | n/a — this is a positive finding, no action. | n/a. |
| F1 | **P3** | docs (naming drift) | A34 §A34.3 channel table, A36 §A36.3 "HJ-04 Δln B (planned)", A40 module ownership table all label evidence-anatomy as **HJ-04**; A32 §A32.3.2 + A41 §A41.6 + W13D5 A42 bind it to **HJ-03**. The governing `INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 uses the HJ-03 binding. | historical: the HJ-03/HJ-04/HJ-05 numbering was renumbered mid-plan (v3 §4.5.3.x) and the tabular dossier entries were never updated. | three-file `sed` pass swapping "HJ-04 evidence anatomy" → "HJ-03 evidence anatomy" across A34/A36/A40. | a reader consulting A40 for ownership might file a paper under "HJ-04" while the code module lives under `mio.decomposition.evidence_anatomy` with report_type `"evidence_anatomy"`. |
| F2 | **P3** | coverage | W13D2 `test_standard_probes_agree_with_registry` compares set-equality on `{p.name for p in STANDARD_PROBES ∪ STANDARD_Z_PROBES}` vs `REGISTERED_PROBE_IDS`; it does *not* verify the σ_cone values inside the dataclass match across the two producers. If HJ-02a drifted to `σ=5.9` for CatWISE while HJ-02b stayed at `6.0`, the parity test would still pass. | the registry is a PROBE_ID SSOT, not a probe-dataclass SSOT. | opportunistic: add `test_standard_probes_have_consistent_sigma_cone_across_producers` — same PROBE_ID must share `sigma_cone_deg` and `l_deg` / `b_deg` between HJ-02a and HJ-02b. | a paired-commit σ update could touch only one producer, leaving a silent inconsistency. |
| F3 | **P3** | coverage | W13D2 parser is tolerant to markdown formatting drift: if A37.3 switches from `| ``CMB`` |` to `| **CMB** |` the regex fails and the parity test errors rather than yielding a meaningful diff. | deliberate tradeoff — a tolerant parser would risk false-positive matches on unrelated backtick content. | already acceptable; document the tight coupling in a docstring comment on `_parse_a37_3_probe_ids_from_markdown`. | a dossier author editing A37.3 cosmetically would see a cryptic `AssertionError` rather than a clean "parity violated" message. |
| F4 | **P3** | testing | A36a §A36a.3 literature deltas are *documented* but not *tested*. A future σ_cone value edit could silently drift the dossier claim without failing any test. | dossier contains plain-English claims; mechanising them would require a JSON sidecar or YAML frontmatter parser. | not a blocker; revisit when >1 σ update lands. | a reviewer citing the dossier might over-trust numbers that the code silently changed. |

**No P0 / P1 items found.** The W13 FM-check passed cleanly —
W12 FM1 cross-lane contamination did not recur on any of the four
W13 commits, validating the W13D1 pre-commit gate as an effective
mitigation. F1–F4 are all P3 coverage / docs items with concrete
follow-up paths; none block the next-session rotation.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **passed** — `is_registered_probe_id`
  short-circuits all five registry members; rejects all 7 typo /
  whitespace / novel-name negatives.
- **dimensional consistency**: **n/a** — string / bool surface.
- **sign / normalization**: **n/a**.
- **positivity / admissibility**: **passed** — tuple membership
  is a closed predicate.
- **alternative explanation**: n/a; no numerical claims this
  phase.

**B. Code verifier**
- **contract satisfaction**: **passed** — `REGISTERED_PROBE_IDS`
  is a `Tuple[str, ...]` (verified by
  `test_registry_is_alphabetical_and_immutable`); no mutation
  possible. `STANDARD_PROBES ∪ STANDARD_Z_PROBES == registry`
  holds verbatim.
- **actual code-path usage**: **passed** — parity test reads the
  dossier file from disk rather than a string constant, so any
  drift between filesystem-dossier and code-tuple is caught.
- **regression risk**: **low** — touched-surface
  1059 → 1065 (+6), 0 failures, 0 skip-change. `pytest bass_py/`
  (full suite) not rerun this phase; relying on touched-surface
  discipline from W10 pattern.
- **reproducibility**: **passed** — registry is a literal tuple
  bound at import; every test run returns the identical
  `REGISTERED_PROBE_IDS`.

**C. Numerical verifier**
- **tolerance robustness**: **n/a**.
- **convergence / stability**: **n/a**.
- **baseline reproducibility**: **passed** — touched-surface
  bit-stable across two independent `pytest` runs during the
  W13D2 landing.
- **uncertainty / misspecification**: **n/a**.

**D. Dossier verifier**
- **A36a cross-references exist**: **passed** — A36 (parent),
  A37 (PROBE_ID catalogue), A38 (caveat pattern), A35 (concrete
  statistic) all resolve to existing files.
- **A42 cross-references exist**: **passed** — A32, A34, A36,
  A39, A40, A41, A37 all resolve. A42.6 naming-drift note
  flags the A34/A36/A40 ↔ A32/A41 inconsistency and adopts the
  schema-authoritative binding.
- **A42 self-consistency**: **passed** — §A42.5 MioCertificate
  field values align with A32.2 field definitions;
  `reduction_status="diagnostic-only"` pattern matches the W10D3
  HJ-01 precedent; `mio_evidence_anatomy_v1.json` artefact name
  matches REG-02 `mio_` prefix rule.
- **A37.3 code↔dossier parity**: **passed** — 6/6 W13D2 tests
  green; W6 FM5 PROBE-NAME-SCHEMA carry-forward now fully closed
  (W12 closed §A37.6 grammar; W13 closes §A37.3 catalogue).

---

## 8. Minimal repair plan

No P0/P1 repair needed. Three opportunistic patches for W14+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | One-pass `sed` cross-dossier rename "HJ-04 evidence anatomy" → "HJ-03 evidence anatomy" across A34 / A36 / A40. Batch with the HJ-03 landing commit when HTT Phase F unblocks. | no (docs drift) | F1 — avoids reader confusion about module identity. | n/a (or extend `test_dossier_hj_numbering_consistency`). | zero; additive. |
| R2 | Add `test_standard_probes_have_consistent_sigma_cone_across_producers` — HJ-02a and HJ-02b must agree on `sigma_cone_deg`, `l_deg`, `b_deg` per PROBE_ID. | no (P3 coverage) | F2 — catches silent producer-drift on paired σ update. | yes (+1 test). | additive; MIO contribution 95 → 96. |
| R3 | Edit A36 §A36.4 to link to A36a as the new provenance anchor for the `*_sigma_cone_plan_placeholder` caveat explanation. | no (docs) | improved discoverability; prerequisite for the A36a.5 retirement-criterion commits. | n/a. | zero; dossier-only. |

All three are deferrable; none block W14 execution.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `pytest bass_py/mio/` → 95/95 green
  in ~1.6 s.
- **Edge / adversarial**:
  `test_is_registered_probe_id_rejects_typos_and_novel_names`
  (case-drift, whitespace-drift, novel-name rejection);
  `test_registry_is_alphabetical_and_immutable` (`list` /
  `set` wrapper regression guard);
  `test_standard_probes_agree_with_registry` (drift between
  producer SSOT and registry caught at import time).
- **Physics sanity**: n/a — no numerical claim landed.
- **Numerical stability / sensitivity**: n/a.
- **Regression**: full touched-surface `1065 / 0 / 4` (+6 over
  W12 baseline).

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W13 네 landings (process gate +
  PROBE_ID registry + σ_cone literature + HJ-03 stub) 모두
  contract ↔ equation ↔ code ↔ test 일관. W12 FM1 cross-lane
  contamination 재발 없음 (§6 W13 check = PASSED).
- **지금 당장 구현/수정할 1개**: 없음. 모든 발견 사항(F1–F4)은
  P3 coverage / docs drift. F1 naming drift는 HJ-03 landing
  커밋에 묶어서 일괄 처리 (W14+ deferred).
- **지금 손대면 안 되는 1개**: `bass_py/mio/coherence/*`의
  `sigma_cone_deg` 기본값. A36a.4는 "caller's judgement" 원칙 하에
  이 값을 W13D3 documentation pass에서 **의도적으로 미변경**
  상태로 유지한다고 명시. 수치 변경은 별도 커밋 + A36.4 갱신 +
  caveat flag 퇴역과 함께 묶여야 한다 (§A36a.5 3-condition rule).

---

## Week-13 final gate (per NEXT_SESSION §2 Week 13)

- [x] W12 R1 process note added (one line in NEXT_SESSION
      `41b7200` + memory `feedback_git_workflow.md` durable entry).
- [x] W12 R2 PROBE_ID registry landed (W13D2 `b7607ef` — 6 new
      tests; MIO contribution 89 → 95).
- [x] At least one new A4x dossier file landed (A36a W13D3
      `ed2c9b1` + A42 W13D5 `9dd64fa` — two landings, exceeds gate).
- [x] Phase-boundary audit log written (this file); W12 FM1
      recurrence check included in §6 and returns PASSED.
- [x] No touched-surface regressions (1065 passed; +6 over W12;
      0 failed; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W13` closes cleanly.
