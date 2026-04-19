# Phase-boundary audit — Independent Tracks Week 12

**Phase tag**: `IND_TRACKS_W12`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.3 §21 (Week 12 continuation
routine); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 12. Execution:
W11 F4 grammar-tests close (Day 1), W5 APPLY-BIAS-AMP hardening
(Day 2), W11 F1 exact-enumeration drift_pvalue (Day 3), DOS-A41
extension protocol (Day 5), this audit + NEXT_SESSION rotation
(Day 7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.2.1 (`MioCertificate` dataclass body — unchanged);
v3 §4.5.3.2 row 2 (HJ-02b z-binned coherence);
v3 §4.5.3.1 (HJ-01 shear extraction);
v3 §4.5.4 (G19 hard separation — unchanged);
v3 §12.2bis (REG-02 `mio_` prefix rule);
v3 §16.2 FM5 (probe-name grammar formalised by A37, enforced by W12D1);
W7 FM3 (schema-hash vs. literal freeze — referenced by A41.5);
W11 F1 (drift_pvalue exact path — closed);
W11 F4 (A37 grammar tests — closed);
W5 APPLY-BIAS-AMP (amp_true vs amp_meas — surfaced via W12D2 caveat).

**Baseline head**: `a43e6ff` (`IND_TRACKS_W11: phase audit +
next-session prompt rotation`). No out-of-lane intervening commits
between W11 audit and W12D1.

**Commits this phase** (this lane):

- `W12D1` — `015246d` `W12D1: MIO A37 grammar acceptance tests`.
  Adds `bass_py/mio/tests/test_probe_name_grammar.py` (8 tests) +
  tightens the three MIO certificate producers for A37.2
  compliance: `mio/coherence/directional.py` +
  `mio/coherence/redshift_binned.py` switch to alphabetical
  `"+".join(sorted(...))`; `mio/extraction/hj01_shear.py` gains
  a `_bianchi_type_to_model_id` helper and emits a MODEL_ID
  singleton instead of the legacy `atlas_name:bianchi_type`
  colonned form. A37 dossier examples + A37.6 section updated.
  MIO contribution 71 → 79.
- `W12D2` — `cd220a6` `W12D2: AUDIT(W5-APPLY-BIAS-AMP): HJ-05a
  hardening`. Adds `BIAS_AMP_CAVEAT` constant + `apply_bias_amp_caveat()`
  helper + `build_report(..., mock_bias_applied=False)` kwarg to
  `mio/diagnostics/masked_sky_caveats.py`, plus 4 tests. The flag
  is default-off so the pre-W12 call surface is preserved verbatim.
  No upstream `htt/PR13AH._apply_bias_to_direction` change — the
  helper's amplitude scaling remains untouched per the W5 audit
  directive (§APPLY-BIAS-AMP: "never patch the helper before
  ChannelSummary grows a velocity-amplitude field"). MIO
  contribution 79 → 83.
- `W12D3` — `99465e5` `W12D3: MIO HJ-02b exact-enumeration (W11 F1)`.
  Adds `exact: bool = False` kwarg to `drift_pvalue`; when set,
  enumerates every `z_eff` permutation via `itertools.permutations`
  and returns `count / N!` (no Lidstone smoothing). Guardrail
  `EXACT_ENUMERATION_MAX_PERMUTATIONS = 10 000` refuses N ≥ 8
  with a clear `ValueError`. Six new tests (15 → 21 in HJ-02b).
  MIO contribution 83 → 89. **Cross-lane contamination finding —
  see W12 FM1 below.**
- `W12D5` — `27d0fed` `W12D5: DOS-A41 extension protocol`. New
  `docs/dossier/A41_mio_report_type_extension_protocol.md` (~200 L)
  — seven-step mechanical checklist for adding a new
  `MioCertificate.report_type` string (HJ-03 evidence_anatomy,
  HJ-04 flrw_tension, future) without rotating the v1 schema hash.
  Cross-references A32 + A34 + A37 + A39 + A40 per dossier convention.
- `W12D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1059 passed, 0 failed, 4 skipped**. Week 12
delta vs Week 11 (1041 / 0 / 4): **+18 tests pass (8 A37 grammar +
4 APPLY-BIAS-AMP + 6 exact drift_pvalue), 0 skip change,
0 regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed
(unchanged from W11 — no TSC code change this week).

**MIO contribution**: 89 tests (+18 vs W11's 71; gate ≥ 47 met
with 42 to spare). Composition: 19 directional-coherence (W6) +
8 certificate-generator (W6) + 5 boot (W6) + 5 bridges (W6/W7) +
5 masked-sky (W6) + 4 masked-sky APPLY-BIAS-AMP (W12D2, new) +
19 HJ-01 (W10D3) + 15 HJ-02b z-binned-coherence (W11D3) +
6 HJ-02b exact-enumeration (W12D3, new) + 8 A37 grammar
(W12D1, new). Cross-check: `pytest bass_py/mio/ --collect-only -q
| tail -1` = `89 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase composition — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY, unchanged until MANU-CH12-NEW figure
retirement), 1 × `test_figures_smoke.py::fig_certification_matrix`
family (W9 carry), 1 × `test_bulkflow_likelihood.py:303` dynesty
contract guard (W10D1 composition swap, by-design).

---

## 1. Audit target reconstruction

This phase ships four artefacts; each has a distinct audit target:

### W12D1 — A37 grammar acceptance tests + producer tightening

- **Core claim**: every MIO-certificate-producing module emits a
  `probe_name` string that parses under A37.2 v1 grammar
  (singleton | bundle | atlas_label). Bundle-form output is
  alphabetically sorted (A37.2 rule 2) so cross-cert aggregation
  keys are stable.
- **Algorithm**: not applicable — grammar is declarative
  regex enforcement; producer fix is an ordering + string-format
  change.
- **Output**: 8 new tests + three-module probe-name producer
  tightening. No dataclass field change → no schema hash rotation.

### W12D2 — HJ-05a-lite APPLY-BIAS-AMP caveat surfacing

- **Core claim**: any MIO certificate that (a) runs on a masked-
  sky catalogue AND (b) applies the PR13AH mock-bias correction
  should propagate the amp_true-vs-amp_meas limitation to its
  `domain_caveats` so downstream readers know the direction
  de-bias used the injected-truth amplitude, not a measured
  amplitude.
- **Algorithm**: not applicable — caveat is a string.
- **Output**: `BIAS_AMP_CAVEAT` constant + one helper + one additive
  kwarg on `build_report`. Default-off preserves pre-W12 call
  surface exactly. Four tests.

### W12D3 — HJ-02b exact-enumeration drift_pvalue

- **Core physical claim**: under the null "probe direction is
  independent of the probe's effective redshift", the drift
  statistic is a permutation invariant of the z_eff labels. The
  **exact** distribution of the drift under the null is the set
  `{drift(π(z)) : π ∈ S_N}` over all `N!` label permutations. For
  small N this set is finite and tractable, giving a bit-
  reproducible p-value `k / N!` where k = #{π : drift(π) ≥
  drift(identity)}.
- **Algorithm**:
  1. Compute the observed drift via the existing
     `total_drift_deg(per_bin_resultants(probes))`.
  2. If `exact=True`: iterate
     `itertools.permutations(z_labels)`; for each perm rebuild
     the probe list with permuted `z_eff`, recompute drift; count
     the fraction matching-or-exceeding. Return `count / N!`.
  3. Refuse N! > `EXACT_ENUMERATION_MAX_PERMUTATIONS` (= 10 000)
     so an N = 8 (40 320 perms) call fails-loud instead of stalling.
- **Output**: new kwarg + new module constant; 6 new tests.

### W12D5 — DOS-A41 extension protocol

- **Core claim**: adding a new `MioCertificate.report_type` value
  (HJ-03 `"evidence_anatomy"`, HJ-04 `"flrw_tension"`, future) is
  a value-level extension, not a schema bump; the v1 schema hash
  does **not** rotate on this class of change, so HJ-03 / HJ-04
  authors do not need a CONTRACTS-01 v2 coordination.
- **Algorithm**: not applicable (documentation).
- **Output**: `docs/dossier/A41_mio_report_type_extension_protocol.md`
  (~200 L; seven-step mechanical checklist; non-scope box;
  W7 FM3 interaction section; worked HJ-03 example).

---

## 2. Contract / interface table

### W12D1 — A37 grammar (module-level)

| Field | Value |
|---|---|
| **Grammar regex (local test constants)** | `PROBE_ID_RE = ^[A-Za-z][A-Za-z0-9]{0,23}$`; `MODEL_ID_RE = ^(FLRW \| Bianchi(I\|II\|V\|VI(0\|h)\|VII(0\|h)\|VIII\|IX) \| Tilted[A-Z][A-Za-z]+)$`; `BUNDLE_RE = PROBE_ID("+"PROBE_ID)+`; `ATLAS_LABEL_RE = MODEL_ID("_vs_"MODEL_ID \| ("+"MODEL_ID)+)?` |
| **HJ-01 producer** | `probe_name = _bianchi_type_to_model_id(bianchi_type)` — singleton atlas_label; maps `"I"` → `"BianchiI"`, `"VIIh"` → `"BianchiVIIh"`, `"FLRW"` → `"FLRW"` idempotent |
| **HJ-02a producer** | `probe_name = "+".join(sorted(p.name for p in probes))` — alphabetical bundle |
| **HJ-02b producer** | same alphabetical bundle |
| **Invariants** | (a) `sorted` is idempotent — re-running the producer on a sorted set is a no-op; (b) regex parsers are pure — no hidden state; (c) grammar is forward-compatible with the A37.5 `probe_names: list[str]` migration |

### W12D2 — APPLY-BIAS-AMP caveat

| Field | Value |
|---|---|
| **Input** | boolean `mock_bias_applied: bool = False` |
| **Output** | `SkyCoverageReport.caveats` optionally contains the canonical `BIAS_AMP_CAVEAT` string |
| **String constant** | `apply_bias_to_direction_scales_by_amp_true_not_amp_meas (W5 APPLY-BIAS-AMP carry-forward; valid until ChannelSummary grows a velocity-amplitude field — see htt/PR13AH _apply_bias_to_direction + W5 audit §APPLY-BIAS-AMP)` |
| **Default behaviour** | identical to pre-W12 `build_report` (caveat NOT appended); additive call surface |
| **G19 posture** | caveat is metadata, not a score; cannot be combined into any likelihood |

### W12D3 — exact-enumeration drift_pvalue

| Field | Value |
|---|---|
| **New kwarg** | `exact: bool = False` (keyword-only) |
| **Ceiling constant** | `EXACT_ENUMERATION_MAX_PERMUTATIONS = 10 000` (`7! = 5 040 < 10 000 ≤ 8! = 40 320`) |
| **Exact return form** | `count / N!` where count includes the identity tie (∴ 1 ≤ count ≤ N!, p ∈ [1/N!, 1]) — **no Lidstone smoothing** |
| **MC return form** | unchanged: `(count + 1) / (n_mock + 1)` |
| **Determinism** | `exact=True` path ignores `rng` / `n_mock` — two calls produce bit-identical p-values |
| **Failure mode** | `exact=True` with N ≥ 8 raises `ValueError` naming the permutation count (40 320 for N=8) and pointing at the ceiling |

### W12D5 — A41 dossier

| Field | Value |
|---|---|
| **Checklist length** | 7 steps (pick string → author module → channel vocab → probe-name grammar → reduction_status tier → tests → dossier entry) |
| **Non-scope** | 4 items (no dataclass mutation, no A34 cross-check auto-add, no G19 relaxation, no report_type rename/retire) |
| **Hash-freeze interaction** | A41.5 — `report_type` is a field value, not a field; hash does **not** rotate on addition |
| **Cross-references** | A32 + A34 + A37 + A39 + A40 (verified by link inspection during authoring) |

---

## 3. Phys-math audit ledger

| Item | Verdict | Evidence |
|---|---|---|
| **Definition / notation** (A37.2 BNF vs. implementation) | **pass** | Regex constants are a literal transcription of A37.2; test `test_grammar_regex_accepts_model_ids` exercises all DOS-A13 Bianchi types (I/II/V/VI0/VIh/VII0/VIIh/VIII/IX) + FLRW + TiltedOrthogonal. |
| **Index / trace consistency** | **n/a** | Grammar / caveat / enumeration — no PSTF content at this level. |
| **Sign / normalization** | **pass** | Exact p-value is a rational in [1/N!, 1]; MC p-value is a rational in [1/(n+1), 1]. |
| **Units / dimensions** | **n/a** (grammar, caveat, p-value are dimensionless). |
| **Known-limit recovery** | **pass** | (a) sorted-of-sorted = sorted (A37 rule 2 idempotence); (b) HJ-02b exact vs MC at N=6 agrees within 0.05 (test `test_drift_pvalue_exact_matches_mc_at_small_N`); (c) single-probe exact path returns 1.0 (short-circuit inherited from MC path). |
| **Boundary / regularity / positivity** | **pass** | N=7 ≤ ceiling, N=8 ≥ ceiling — bracket tested by `test_exact_enumeration_max_permutations_is_tractable`. Oversize raises `ValueError` (`test_drift_pvalue_exact_raises_on_oversize_N`). |
| **Hidden assumptions** | **documented** | Exact path assumes the probe *directions* are fixed and only `z_eff` labels are permuted — same assumption as the MC null already audited in W11 §3. |
| **Adversarial special case** | **pass** | `test_drift_pvalue_exact_returns_count_over_n_factorial` asserts `p · N!` is an integer, catching any accidental Lidstone-style off-by-one drift into the exact path. |

---

## 4. Equation-to-code mapping audit

| Equation (prose) | Module function | Test evidence |
|---|---|---|
| A37.2 BNF: `probe_name := singleton \| bundle \| atlas_label` | producer code paths in `directional.py`, `redshift_binned.py`, `hj01_shear.py` | `test_probe_name_matches_grammar_v1_{HJ01, HJ02a, HJ02b}` (regex check on emitter payload) |
| A37.2 rule 2: bundle alphabetical | `"+".join(sorted(p.name for p in probes))` | `test_probe_name_is_alphabetical_bundle_{HJ02a, HJ02b}` |
| `p_exact = #{π : drift(π) ≥ drift(id)} / N!` | `drift_pvalue(..., exact=True)` | `test_drift_pvalue_exact_returns_count_over_n_factorial` + `test_drift_pvalue_exact_matches_mc_at_small_N` |
| Default-off caveat surfacing | `build_report(..., mock_bias_applied=False)` no-op; `=True` appends `BIAS_AMP_CAVEAT` | `test_build_report_{excludes, includes}_bias_amp_caveat_{by_default, when_flag_set}` |

**Approximation / regime compliance**: Exact path is closed-form
over the permutation orbit — no approximations. MC path's Lidstone
`(k+1)/(n+1)` smoothing is preserved for backward bit-identity
with W11 tests.

**Production-path check**: every test invokes the public module
entry points (`emit_directional_coherence_artefact`,
`emit_redshift_coherence_artefact`,
`emit_shear_extraction_artefact`, `build_report`, `drift_pvalue`)
— no surrogate test harness.

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | n/a (regex / string / combinatorial). |
| Tolerance sensitivity | Exact-vs-MC test uses `abs(p_exact - p_mc) < 0.05` — generous because N=6 MC @ n=2 000 has ~2% sampling noise. |
| Underflow / overflow | None; p-values ≥ 1/N! ≥ 1/5040 > 0. |
| Conditioning | n/a. |
| Cache / state leakage | Exact path is a pure function of inputs — no RNG, no state. |
| Seed / reproducibility | Exact path is deterministic by construction; MC unchanged. |
| Baseline reproduction | `pytest bass_py/mio/` = 89/89 green in ~0.9 s on the dev box; touched-surface 1059/0/4. |
| OOD / misspecification | Exact path refuses N ≥ 8 loud-fail; no quiet fallback. A37 grammar regex is strict (no whitespace, no colons) — HJ-01 colonned legacy strings are rejected by design. |

---

## 6. Ranked failure modes (P0–P3)

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| F1 | **P2** | process | W12D3 commit (`99465e5`) accidentally pulled in unrelated bass_py-lane + gallery-lane working-tree changes (`bass_py/bass/transport/*`, `docs/audits/AUDIT_PHASE_FB1_*`, `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md`, `scripts/make_physics_gallery.py`, `plots/physics_gallery/11_integrator/09..12_*.png`). The W12D3 commit body describes only the HJ-02b exact-enumeration landing. | staged index likely contaminated by a concurrent bass_py session doing `git add` outside this lane's visibility; without a pre-commit `git status` check the subsequent `git commit` collected every staged entry. | `feedback_git_workflow.md` forbids history rewrite (additive commits only), so the mixed commit cannot be retroactively split. Mitigation for W13+: always `git status --short` before committing; only `git add <explicit path>` is insufficient when the index is already populated. | A future reader git-bisecting for the bass FB-1.3 background-solver landing might find W12D3 and conclude the IND-tracks lane owns that work — misleading. |
| F2 | **P3** | docs | A41 defines a seven-step extension checklist but does not ship an acceptance test that parses existing MIO modules to verify they all pass the checklist. | the checklist is a docs contract; mechanising it would require a registry or AST scan, which is disproportionate to the payload at this lane's current scope. | not a blocker; add an optional `test_mio_report_types_pass_a41_checklist` when the HJ-03 module lands to avoid checklist drift. | an author might follow steps 1-6 but skip step 7 (dossier entry) and nothing catches the omission. |
| F3 | **P3** | coverage | The W12D1 grammar regex constants are duplicated in the test file — if a producer coins a new unregistered PROBE_ID the regex self-tests won't catch it until someone re-reads A37.3. | single-source-of-truth for the registered PROBE_IDs list lives in A37.3 markdown, not in code. | opportunistic: land a `mio.interface.probe_name_registry` with a frozen `REGISTERED_PROBE_IDS: Tuple[str, ...]` that the A37.3 table mirrors verbatim. | a future module using `name = "LSS_dipole"` would pass the regex (12 alnum chars) but not correspond to any A37.3-registered probe. |
| F4 | **P3** | coverage | The W12D2 `mock_bias_applied` flag is set by the caller; there is no runtime assertion that the caller has *actually* applied the PR13AH mock-bias correction before flipping the flag. | the flag is a documentation contract, not a behavioural one. A caller that lies about it will silently mislabel a certificate. | optional: add a sibling contract parameter `mock_bias_report: Optional[InjectedMockReport] = None` that the caller MUST supply when `mock_bias_applied=True`. | a downstream reader might treat a falsely-flagged caveat as ground truth. |
| F5 | **P3** | testing | Exact-enumeration agreement test uses `abs(p_exact - p_mc) < 0.05` tolerance — loose enough to mask a 2σ MC bias. | the test is a sanity check, not a statistical verifier; tightening to 2% would fail ~5% of runs from Monte-Carlo noise alone. | already tight enough for acceptance; could be tightened to `abs < 3 * sqrt(p*(1-p)/n_mock)` if precision becomes load-bearing. | a structural bug that shifts the exact path by 2-3% could slip through. |

**No P0 / P1 items found.** W12 FM1 is a P2 process finding worth
calling out prominently, but it is not a code correctness issue —
it is a workflow hygiene issue. Mitigation documented below in §8.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **passed** — sorted idempotence, exact
  vs MC agreement at N=6, single-probe short-circuit at exact=True.
- **dimensional consistency**: **n/a** for strings / booleans /
  rational p-values.
- **sign / normalization**: **passed** — exact p-value bounded in
  [1/N!, 1].
- **positivity / admissibility**: **passed** — ceiling enforces
  N < 8 for exact path.
- **alternative explanation**: exact p-value saturation
  (p = k/720 large for all-permutation-equivalent injections) is
  explained by bin-internal symmetry, not by bug; see W12D3 commit
  message and §6 F5.

**B. Code verifier**
- **contract satisfaction**: **passed** — A37 producer fixes
  preserve dataclass immutability and field types; MioCertificate
  schema hash unchanged (verified by running
  `bass_py/workspace/contracts/tests/test_mio_certificate.py` —
  all certificate construction tests green).
- **actual code-path usage**: **passed** — every grammar test
  invokes `emit_*_artefact(...)` (production path) and inspects
  `payload["certificate"]["probe_name"]`.
- **regression risk**: **low** — `bass_py/mio/ bass_py/htt/tests/
  bass_py/src/ bass_py/tsc/{admissibility,charts,diagnostics,
  integration}/ bass_py/workspace/` touched-surface 1041 → 1059 (+18),
  0 failures, 0 skip-change.
- **reproducibility**: **passed** — exact path is deterministic;
  MC path seeded.

**C. Numerical verifier**
- **tolerance robustness**: **passed** — exact path is closed-form.
- **convergence / stability**: **n/a** (no iteration).
- **baseline reproducibility**: **passed** — touched-surface bit-
  stable across two independent runs.
- **uncertainty / misspecification**: **documented in F5** —
  exact-vs-MC tolerance is deliberately loose.

**D. Dossier verifier**
- **A41 references exist**: **passed** — A32 / A34 / A37 / A39 /
  A40 all resolve to existing files; link paths verified by
  `grep -l 'A41' docs/dossier/ | head` and reverse cross-check.
- **Policy consistency**: **passed** — A41 non-scope box aligns
  with A32.5 hash-freeze rule + A34 cross-check sovereignty
  (A41 does not create cross-checks).
- **A37.6 landed-note consistency**: **passed** — the docs edit
  in W12D1 references the exact test file and 8-test count that
  actually landed.

---

## 8. Minimal repair plan

No P0/P1 repair needed. Two opportunistic patches for W13+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | Always run `git status --short \| grep '^[MA ]'` immediately before `git commit` (both in this file as process-doc and on the next-session rotation). | **yes (process)** | F1 — avoids future lane cross-contamination in the same way W8 FM1 forbids `/project` staging. | n/a | n/a |
| R2 | Land `bass_py/mio/interface/probe_name_registry.py` with a frozen `REGISTERED_PROBE_IDS` tuple and a test asserting A37.3 dossier table matches the code registry verbatim. | no (P3 coverage) | F3 — single-source-of-truth for PROBE_ID catalogue. | `test_probe_name_registry_matches_A37_3` | zero; additive. |

W12 FM1 is already mitigated implicitly by committing this audit as
a standalone commit (following the pattern of prior phase-audit
commits) — it re-establishes the clean separation the W12D3 commit
violated.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `pytest bass_py/mio/` → 89/89 green in
  ~0.9 s.
- **Edge / adversarial**: `test_drift_pvalue_exact_raises_on_oversize_N`
  (N=8 loud-fail); `test_drift_pvalue_exact_returns_count_over_n_factorial`
  (integer rationality); `test_grammar_regex_accepts_model_ids`
  (negative cases: `FLRW:I`, `Bianchi-VIIh`, `CMB CatWISE`, empty).
- **Physics sanity**: `test_drift_pvalue_exact_matches_mc_at_small_N`
  (exact vs MC agreement at N=6).
- **Numerical stability / sensitivity**: `test_drift_pvalue_exact_is_deterministic`
  (two calls, bit-identity).
- **Regression**: full touched-surface `1059 / 0 / 4` (+18 over W11
  baseline).

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W12 네 landings (grammar tests +
  APPLY-BIAS-AMP caveat + exact-enumeration + A41 dossier) 모두
  contract ↔ equation ↔ code ↔ test 일관.
- **지금 당장 구현/수정할 1개**: 없음. 모든 발견 사항(F1–F5)은
  P2 process / P3 coverage / by-design / 상류 의존 대기. F1 프로세스
  결함은 이 audit 커밋이 깨끗하게 분리되어 있다는 사실로 이미
  완화(이후 커밋은 `git status` 사전검사 원칙을 적용).
- **지금 손대면 안 되는 1개**: `htt/PR13AH._apply_bias_to_direction`의
  amplitude scaling. W5 audit가 명시적으로 "ChannelSummary가
  velocity-amplitude field를 얻기 전까지 건드리지 말 것"이라고
  지시했으며, W12D2 은 이 경고에 따라 upstream을 건드리지 않고
  caveat만 surface했다. 이 원칙은 W13+ 까지 계속 유지한다.

---

## Week-12 final gate (per NEXT_SESSION §2 Week 12)

- [x] W11 F4 (A37 grammar tests) closed (W12D1 `015246d`); W11 F1
      (exact-enumeration) closed (W12D3 `99465e5`).
- [x] W5 APPLY-BIAS-AMP closed via caveat-surfacing hardening
      (W12D2 `cd220a6`); upstream `_apply_bias_to_direction`
      intentionally untouched per W5 audit directive.
- [x] At least one new A4x dossier file landed (W12D5 `27d0fed` —
      A41, ~200 L).
- [x] Phase-boundary audit log written (this file).
- [x] No touched-surface regressions (1059 passed, 0 failed, +18
      over W11; 4 skipped unchanged).

All five gate items green. Phase `IND_TRACKS_W12` closes cleanly.
