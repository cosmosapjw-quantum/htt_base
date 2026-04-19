# Phase-boundary audit — Independent Tracks Week 15

**Phase tag**: `IND_TRACKS_W15`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12+ continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 15 (W14 F1
process remediation + A43 schema-hash dossier + W14 R2 over-emission
guard).
Execution: W15D1 scoped-commit rule (D1), W15D3 A43 dossier (D3),
W15D5 R2 placeholder-tag count tightening (D5), this audit +
NEXT_SESSION rotation (D7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §10.2bis (G19 enforcement matrix — schema freeze layer);
v3 §11.14.6 (dossier convention — A43 added under the A4x family);
v3 §16.2 FM2 (σ_cone placeholders — caveat-emission contract from W14
now has an over-emission guard);
[W7 FM3](AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md#fm3-schema-bump-vs-frozen-hash-coordination-p3)
(literal-vs-hash schema freeze — A43 fixes the mechanism without
landing the test);
[W12 F1](AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md) (cross-lane
contamination — pre-commit-gate rule W13D1; recurrence W14D3 = W14 F1);
[W14 F1](AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md#6-ranked-failure-modes-p0p3)
(W12 F1 recurrence under the W13D1 gate — closed by W15D1
scoped-pathspec rule);
[W14 F2](AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md#6-ranked-failure-modes-p0p3)
(over-emission gap on `test_hj02a_certificate_carries_placeholder_
tags_for_non_promoted_probes` issubset assertion — closed by W15D5
R2 tightening test).

**Baseline head**: `40342d3` (`IND_TRACKS_W14: phase audit +
next-session prompt rotation`). One intervening cross-lane commit
landed during this phase (`3dcc505` `FB-2.1: nabla_tilde dispatch
for FLRW / I / V / VII_0 / IX harmonic modes`); see §6 for the FM
discussion (positive finding — no contamination this phase).

**Commits this phase**:

- `W15D1` — `d48b920` `W15D1: AUDIT(W14 F1): scoped git commit --
  <paths> rule`. One-file commit (+10 L) extending §0 first-order
  rules with a "scoped `git commit -- <paths>` rule" bullet that
  makes git refuse to commit anything outside the listed paths from
  the index. Paired durable update to memory
  `feedback_git_workflow.md` (rule lands in the same paragraph that
  already carries the W13D1 `git status --short` gate). No code
  change. Closes W14 F1 by removing the race window the
  status-only gate could not catch.
- `W15D3` — `8fae1ba` `W15D3: DOS-A43 schema hash digest design`.
  One-file commit creating
  `docs/dossier/A43_schema_hash_digest.md` (~306 L). Specifies the
  hash-digest mechanism that catches structural drift (field
  add/remove/rename, normalised type-string change, default-kind
  change, field-order change) without rotating on value-level edits
  (new `report_type` / `channel` values, payload-dict key additions,
  default-value retunes). §A43.6 contains the test specification
  ready for landing on first schema extension; §A43.5 worked
  example walks the no-trigger HJ-03 case
  (`consistency_metrics["decomposition_residual"]` is value-level →
  digest invariant) and the trigger case
  (top-level `cross_check_evidence` field rotates the digest,
  requires AUDIT-trail entry). Cross-references resolve into A32.5,
  A41.2, A41.5, A42.5. No code change.
- `W15D5` — `293652a` `W15D5: MIO tighten placeholder-tag count
  (W14 R2)`. One-file commit (+25 L) appending
  `test_hj02a_certificate_caveat_count_equals_flagged_set_with_no_
  caller_caveats` to
  `bass_py/mio/tests/test_sigma_cone_provenance.py`. Asserts
  set-equality + length-equality on the no-caller-caveats path
  (`p_iso=0.001`, no `domain_caveats=` kwarg), closing the
  over-emission gap the W14D5 `issubset` test missed. MIO
  contribution 105 → 106.
- `W15D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1076 passed, 0 failed, 4 skipped**. Week 15 delta
vs Week 14 (1075 / 0 / 4): **+1 test (W15D5), 0 skip change, 0
regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed
(unchanged from W13–W14 — no TSC code change this week).

**MIO contribution**: 106 tests (+1 vs W14's 105; gate ≥ 47 met
with 59 to spare). Composition unchanged from W14 except the new
test sits inside `test_sigma_cone_provenance.py` (was 9 tests; now
10). Cross-check: `pytest bass_py/mio/ --collect-only -q | tail -1`
= `106 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY), 1 × `fig_certification_matrix` family
(W9), 1 × `test_bulkflow_likelihood.py:303` dynesty contract guard
(W10D1).

---

## 1. Audit target reconstruction

Three landings, three distinct audit targets — process, schema-layer
docs, runtime-contract coverage. No code surface added under
`bass_py/mio/` beyond the new test.

### W15D1 — scoped `git commit -- <paths>` rule (closes W14 F1)

- **Core claim**: the W13D1 pre-commit `git status --short` gate
  catches contamination *into* this lane's commit, but cannot catch
  files staged by a concurrent lane's `git commit` that runs in the
  brief gap between our `git status --short` check and our `git
  commit` invocation. The `-- <paths>` pathspec form makes git
  commit only the listed paths from the index; any concurrent
  staging is excluded by construction. Paired durable update to
  memory `feedback_git_workflow.md`.
- **Algorithm**: git-internal — `git commit -- a b c` writes a
  commit object whose tree contains exactly the index entries at
  paths `a`, `b`, `c` (and whatever is in HEAD elsewhere). Files
  staged at other paths between status and commit do not enter the
  new commit object.
- **Output**: `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` +10 L
  (§0 fourth bullet) + memory file paragraph extension. No code
  change.

### W15D3 — A43 schema-hash digest dossier (W7 FM3 closure)

- **Core claim**: A43 fixes the digest mechanism that closes W7 FM3
  without prematurely landing the test. Both `MioCertificate` and
  `MichaelisMentenExport` currently enforce schema "freeze" via
  literal key-set / version-tag tests; `test_miocertificate_schema_
  frozen` even *computes* a SHA-256 prefix but only asserts on the
  field-name set. A43 specifies (a) what is included in the digest
  (field name + normalised type + default kind + field order),
  (b) what is excluded (docstrings, default values, payload-dict
  keys, legal-value sets for `report_type` / `channel`),
  (c) when the test lands (first schema extension, not first
  opportunity), and (d) the type-normalisation rule to make the
  digest version-stable across Python releases.
- **Algorithm**: dossier-only; the test specification in §A43.6 is
  Python prose ready for paste-on-extension.
- **Output**: `docs/dossier/A43_schema_hash_digest.md` (~306 L).
  Cross-references A32.5 (existing schema-enforcement table row
  "Schema hash anti-regression" now points here for the mechanism),
  A41.2 + A41.5 (value-vs-field boundary that A43 mechanises on
  the field side), A42.5 (HJ-03 contract table — the most likely
  trigger candidate). No code change.

### W15D5 — placeholder-tag over-emission guard (closes W14 F2)

- **Core claim**: W14D5's
  `test_hj02a_certificate_carries_placeholder_tags_for_non_promoted_
  probes` uses `issubset` — catches under-emission but passes
  silently on over-emission (e.g. accidentally emitting a tag for a
  promoted probe like CatWISE, or duplicating a tag, or emitting
  for an unregistered name). The new test exercises the
  no-caller-caveats path and asserts set-equality + length-equality.
- **Algorithm**: zero-caller-caveats invocation
  `to_cert_hj02a(STANDARD_PROBES, p_iso=0.001, resultant=resultant)`
  with no `domain_caveats=` kwarg. Compute
  `expected_tags = sorted(f"{n}{PLACEHOLDER_CAVEAT_SUFFIX}"
  for n in STANDARD_PROBES.names if n ∉ PROMOTED_SIGMA_CONE_PROBES)`.
  Assert `sorted(cert.domain_caveats) == expected_tags` AND
  `len(cert.domain_caveats) == len(expected_flagged)`. Set-equality
  alone would still admit duplicates; length-equality alone would
  still admit substitution. Both together close the over-emission
  surface for the no-caller-caveats path.
- **Output**: 1 file changed
  (`bass_py/mio/tests/test_sigma_cone_provenance.py`, +25 L);
  9 → 10 tests in this file; MIO contribution 105 → 106; touched
  surface 1075 → 1076.

---

## 2. Contract / interface audit

| Surface | Before W15 | After W15 | Δ |
|---|---|---|---|
| `MioCertificate` dataclass schema | v1, hash-frozen per A32.5 (literal key-set test) | unchanged | 0 |
| Schema-hash digest mechanism | undocumented (W7 FM3 open) | specified in A43; landing deferred to first extension | **+docs** |
| `domain_caveats` over-emission gate | `issubset` only (W14 F2) | `issubset` + set-equality + length-equality (no-caller-caveats path) | **+regression gate** |
| §0 first-order rules (commit hygiene) | `git add` specificity + `git status --short` gate (W13D1) | + `git commit -- <paths>` scoped pathspec (W15D1) | **+process gate** |
| `feedback_git_workflow.md` durable memory | W13D1 gate paragraph | + W15D1 scoped-pathspec paragraph | **+durable rule** |
| All other surfaces (probe registry, A37 grammar, A36/A36a/A42 dossier text, MIO producers) | as-of W14 | unchanged | 0 |

All extensions are additive. No schema-hash rotation, no field
retype, no field removal, no producer-side runtime change. The new
test exercises an existing code path under stricter assertions; it
adds no new surface to be maintained.

---

## 3. Phys-math audit

No physics or numerical-method change landed this phase. The W15D5
test is a pure-string set-equality assertion over the
`PLACEHOLDER_CAVEAT_SUFFIX` output of `placeholder_caveats_for`.
Per the W14 audit §3, `placeholder_caveats_for` output is
ASCII-alphabetical and deterministic; the W15D5 test exercises the
same arithmetic from the certificate-emission side (assertions on
`cert.domain_caveats` rather than on `placeholder_caveats_for`
directly).

A43.5 worked example does NOT touch physics; it walks the value-
vs-field boundary on the schema layer using HJ-03's planned
`consistency_metrics["decomposition_residual"]` field as the
no-trigger illustration (per A42.3 step 3). No claim on the
floor value (1e-3, per A42.4) is altered or asserted by A43.

---

## 4. Code path audit

- **W15D1**: documentation-only (NEXT_SESSION + memory). The rule
  itself is enforced by future-session discipline; no Python imports
  or runtime hooks are added. The memory file is loaded via
  `MEMORY.md` index per the auto-memory protocol; the new paragraph
  sits inside the existing `Git workflow — avoid branch/rewrite`
  entry so it is read in lock-step with the W13D1 status-gate rule.
- **W15D3**: documentation-only (`docs/dossier/A43_*.md`). No
  Python file touched; no test added. The `<paste-on-extension>`
  digest placeholder in §A43.6 is intentional — landing the digest
  today would freeze the wrong value.
- **W15D5**: pure-Python test addition; no production code touched.
  The new test imports `to_cert_hj02a`, `STANDARD_PROBES`,
  `resultant_vector`, `PROMOTED_SIGMA_CONE_PROBES`,
  `PLACEHOLDER_CAVEAT_SUFFIX` (all already imported in this file).
  Determinism: `placeholder_caveats_for` output is sorted; the
  test sorts `cert.domain_caveats` before comparison so insertion
  order in `to_cert_hj02a` cannot drift the assertion.
- No `bass_py/bass/*` file touched (lane discipline); no
  `plots/physics_gallery/` file touched (gallery-lane discipline);
  no `project/*` file touched (W8 FM1 / `feedback_project_local_only`).

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (no numerics landed this phase). |
| Tolerance sensitivity | n/a — string set-equality. |
| Underflow / overflow | n/a. |
| Conditioning | n/a. |
| Cache / state leakage | `PROMOTED_SIGMA_CONE_PROBES` (frozenset) and `PLACEHOLDER_CAVEAT_SUFFIX` (str) are module-level immutables; W14D5 audit confirmed; W15D5 inherits. |
| Seed / reproducibility | n/a (deterministic pure functions). |
| Baseline reproduction | `pytest bass_py/mio/` = 106/106 green in ~1.6 s; touched-surface 1076/0/4 (+1). Two independent pytest invocations during W15D5 landing returned identical counts. |
| OOD / misspecification | The W15D5 test only exercises the no-caller-caveats path. The caller-caveats path retains the W14D5 `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags` (set-membership + dedup count == 1) — over-emission *with* caller caveats is structurally bounded by the dedup branch but not gated by an equality assertion. F2 below records this as the residual surface. |

---

## 6. Ranked failure modes (P0–P3)

Per the NEXT_SESSION §2 Week 15 Day 7 directive this section MUST
include a §6 W12 F1 / W14 F1 cross-lane-contamination recurrence
check verifying the W15D1 scoped-commit rule was followed on every
W15 sha via `git show --stat`.

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| W15 check #1 | **PASSED** | process (W12 F1 / W14 F1 recurrence) | `git show --stat d48b920 8fae1ba 293652a` = (1 file: `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md`) + (1 file: `docs/dossier/A43_schema_hash_digest.md`) + (1 file: `bass_py/mio/tests/test_sigma_cone_provenance.py`). Every file belongs to this lane's owned surface; no `bass_py/bass/*`, no `plots/physics_gallery/*`, no `project/*` paths pulled in. The intervening cross-lane commit `3dcc505` (`FB-2.1: nabla_tilde dispatch`) carries six bass-lane files (`bass_py/bass/hierarchy/*`) and zero ind-tracks files — symmetric verification from the other lane. | Both lanes used scoped pathspecs (W15D1 rule) and/or coincidental clean sequencing this phase. Concretely, the three W15 commits each used `git commit -- <single-path>` per the new rule. | n/a — positive finding. | the gate held this phase, but a single observation is not a long-running invariant; W16 audit must repeat the check. |
| F1 | **P3** | coverage (residual W14 F2) | The W15D5 over-emission guard exercises only the no-caller-caveats path. A producer that over-emits *while* a caller supplies caveats — e.g. emits `"CatWISE_sigma_cone_plan_placeholder"` for promoted CatWISE alongside a caller-supplied `"masked_sky_partial"` — would still pass `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags` (only checks dedup count == 1 on caller-supplied tags). | the existing caller-caveats test is dedup-focused, not over-emission-focused; W15D5 deliberately scoped to the cleanest possible test signal. | optional W16 R1 — extend the caller-caveats test with `assert set(cert.domain_caveats) == set(caller_caveats) ∪ expected_tags` (union-equality). One-line addition; +0 tests. | a producer-side over-emission bug coexisting with caller-supplied caveats slips past both W14D5 and W15D5 tests. |
| F2 | **P3** | docs (residual W14 F3) | A36a.3 literature Δ summary table remains unmechanised. Inherited W13 F4 / W14 F3. | mechanising requires a YAML / JSON sidecar parser (W14 R3). W15D5 chose R2 instead per the §2 Days 5-6 "Pick ONE" directive. | W16 R2 — pick R3 next phase if W16 has spare bandwidth. | a future σ_cone edit could silently drift the dossier claim; the W14D1 cross-producer parity gate prevents *producer-level* drift but not *literature-level* drift. |
| F3 | **P3** | timing (A43 trigger uncertainty) | A43 specifies the digest mechanism but the test stays unlanded until first schema extension. If neither HJ-03, HJ-04, nor a TSC-05 extension lands within Weeks 16-25, the dossier remains design-only and W7 FM3 stays open in the carry-forward table. | trigger gating is design-correct (avoid landing the wrong digest) but means the test is a deferred deliverable. | acceptance: the deferred status is recorded in §A43.3 and in §3 of `INDEPENDENT_TRACKS_NEXT_SESSION.md` carry-forward (W7 FM3 row remains "deferred — see A43"). | a reader skimming the W7 FM3 carry-forward row might conclude no progress was made; the row footer needs to point at A43. |

**No P0 / P1 items found.** The W12 F1 / W14 F1 process pattern
did not recur this phase (W15 check #1 PASSED). The two residual
P3 items (F1 over-emission-with-caller-caveats; F2 dossier-vs-code
drift) are explicit non-trivial scope tradeoffs documented at
landing time, not findings of latent bugs.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **n/a** — no numerical claim landed.
- **dimensional consistency**: **n/a** — string / docs surface.
- **sign / normalization**: **n/a**.
- **positivity / admissibility**: **passed** — frozenset membership
  inherited from W14D5/D6 audit; W15D5 does not alter the set.

**B. Code verifier**
- **contract satisfaction**: **passed** — `to_cert_hj02a` signature
  unchanged; the new test only adds an additional invocation under
  the existing kwargs. `cert.domain_caveats` remains a `List[str]`.
- **actual code-path usage**: **passed** — the no-caller-caveats
  branch in `mio.coherence.directional.to_mio_certificate`
  (`caveats = list(domain_caveats) if domain_caveats is not None else []`
  → empty list initialisation) is exercised; the placeholder-append
  loop is exercised; `build_mio_certificate`'s `domain_caveats=
  list(domain_caveats)` pass-through is exercised.
- **regression risk**: **low** — touched-surface 1075 → 1076 (+1),
  0 failures, 0 skip-change. Full `bass_py/mio/` suite 106/106
  in ~1.6 s.
- **reproducibility**: **passed** — `cert.domain_caveats` order is
  insertion-order (loop over sorted `placeholder_caveats_for`
  output); the W15D5 test sorts before comparing so the assertion
  is order-stable.

**C. Numerical verifier**
- **tolerance robustness**: **n/a** (no float comparison).
- **convergence / stability**: **n/a**.
- **baseline reproducibility**: **passed** — two independent pytest
  runs during W15D5 landing returned identical test counts.
- **uncertainty / misspecification**: **n/a**.

**D. Dossier verifier**
- **A43 cross-references resolve**: **passed** — relative markdown
  links to `A32_mio_certificate_schema.md`,
  `A34_g19_cross_check_protocol.md`,
  `A41_mio_report_type_extension_protocol.md`,
  `A42_evidence_anatomy.md` all resolve at the same directory
  level; back-references from the cited dossiers (A32.5 row,
  A41.2 / A41.5, A42.5 table) are textual mentions and remain
  consistent (no edits to those files this phase).
- **A43 anchor links**: **passed** — internal anchors `#a431-purpose`
  through `#a439-related-appendices` follow the GitHub markdown
  slug rule (lowercase, dot/dash → dash); reader-side rendering
  verified by spot-checking a handful in the local Markdown
  preview.
- **W7 FM3 carry-forward pointer**: **action item for §8 R3** — the
  §3 carry-forward table row "W7 FM3" should now read "**MECH-
  RESOLVED W15D3**: A43 specifies the digest mechanism; test lands
  at first schema extension per A43.3" instead of the current
  "P3 / Add hash digest test on first schema extension". Handled
  in W15D7 NEXT_SESSION rotation.
- **§0 first-order rules update**: **passed** — the new "scoped
  `git commit -- <paths>` rule" bullet sits as the fourth
  first-order rule, immediately after the existing W13D1
  status-gate bullet, preserving the read order Status → Scope.

---

## 8. Minimal repair plan

No P0 / P1 repair needed. Three opportunistic patches for W16+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | Extend `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags` with a union-equality assertion `set(cert.domain_caveats) == set(caller_caveats) ∪ expected_tags`. | no (P3). | F1 — closes the over-emission-with-caller-caveats residual. | optional (+0 to +1, depending on whether to extend or split). | zero; additive. |
| R2 | A36a.3 YAML sidecar + parity test (W14 R3 carry-forward). | no (P3). | F2 — catches code-vs-dossier literature-Δ drift. | optional (+1). | additive. |
| R3 | A43 digest test landing at first actual schema extension (HJ-03 / HJ-04 / TSC-05 v2). The §A43.6 test is paste-ready; the only blocker is "first extension actually arrives". | no (P3 timing). | F3 — closes W7 FM3 in code, not just docs. | required at trigger (+2 — one per contract). | additive (+2). |

All three are deferrable; none block W16 execution.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `pytest bass_py/mio/` → 106/106 green
  in ~1.6 s; touched-surface 1076/0/4 (+1 over W14 baseline).
- **Edge / adversarial**:
  `test_hj02a_certificate_caveat_count_equals_flagged_set_with_no_caller_caveats`
  (W15D5 — set-equality + length-equality on the no-caller-caveats
  path; over-emission surface).
- **Physics sanity**: n/a — no numerical claim landed; the test is
  a runtime-contract check.
- **Regression**: full touched-surface `1076 / 0 / 4` (+1 over
  W14 baseline); MIO contribution 105 → 106; tsc standalone 602
  unchanged.

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W15 세 landings (W14 F1 process
  remediation + A43 schema-hash 도시에 + W14 R2 over-emission guard)
  모두 contract ↔ code ↔ test 일관. MIO contribution 105 → 106.
  **W12 F1 / W14 F1 재발 없음** — §6 W15 check #1 PASSED;
  three W15 commits 각각 단일 lane-owned path만 포함, 동시간대
  cross-lane commit (`3dcc505`)도 자기 lane 파일만 포함 (대칭
  검증). W15D1 scoped-pathspec 규칙은 §0 + memory 양쪽에 등재 —
  W16+ 세션이 자동 적용 가능.
- **지금 당장 구현/수정할 1개**: 없음. 세 가지 P3 잔존 항목
  (F1 over-emission with caller caveats, F2 A36a.3 sidecar,
  F3 A43 digest test 착지)은 전부 deferrable; W16 routine에서
  bandwidth 여유가 있을 때 진행.
- **지금 손대면 안 되는 1개**: A43 digest 테스트의 즉시 착지.
  현재 schema가 stable한 상태에서 freeze해 두면 첫 확장 PR이
  one-line digest paste를 강요받을 뿐, 추가 catch가 없음. 트리거
  (HJ-03 / HJ-04 / TSC-05 v2)가 도착했을 때 함께 land해야 의미가
  있음.

---

## Week-15 final gate (per NEXT_SESSION §2 Week 15)

- [x] W14 F1 scoped-commit rule landed (durable memory + §0 note;
      W15D1 `d48b920`).
- [x] A43 schema-hash digest dossier landed (W15D3 `8fae1ba`).
- [x] One of W14 R2 / R3 landed — **R2 picked** (W15D5 `293652a`;
      +1 test; MIO 105 → 106).
- [x] Phase-boundary audit log written (this file); §6 W12 F1 /
      W14 F1 recurrence check returns **PASSED** (`git show --stat`
      per W15 commit shows only this lane's owned paths; symmetric
      check on cross-lane `3dcc505` shows only bass-lane files).
- [x] No touched-surface regressions (1076 passed; +1 over W14;
      0 failed; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W15` closes with
zero new P0/P1/P2 findings; three documented P3 residuals
(F1/F2/F3) deferred to W16+.
