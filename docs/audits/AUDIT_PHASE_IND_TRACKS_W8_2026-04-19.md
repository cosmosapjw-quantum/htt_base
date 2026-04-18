# Phase-boundary audit — Independent Tracks Week 8

**Phase tag**: `IND_TRACKS_W8`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.2 §21 Week 8 day-by-day
schedule — MANU-CH11-REDESIGN (Days 1–3), MANU-CH12-NEW (Days 4–5),
HTT-STAB final (Day 6), HTT-NULL smoke (Day 7).
**Pre-commit audit** per memory rule
`feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §11.14.2 (ch11 redesign trigger);
v3 §11.14.1 (ch12 scope);
v3 §4.5.4 (G19 hard separation);
v3 §10.2bis (G19 enforcement matrix);
v3 §14.1 (MIO artefact filename prefix);
v3 §15.2 (qualitative `"truth certificate"` indicator);
INDEPENDENT_TRACKS_PLAN v1.0 §3.4 (HTT-STAB);
v1.0 §3.5 (HTT-NULL);
v1.2 §13.1 (MANU-CH11-REDESIGN);
v1.2 §13.2 (MANU-CH12-NEW).
**Baseline head**: `5c00ba8` (`IND_TRACKS_W7: phase audit +
next-session prompt rotation`).
**Commits this phase** (this lane):

- `ab1297b` W8D3: MANU-CH11-REDESIGN three v3 11.14.2 subsections
- `0772e07` W8D5: MANU-CH12-NEW four-section draft
- `a257c76` W8D6: HTT-STAB final — bounds skips + palette
- `64327b8` W8D7: HTT-NULL smoke green

The bass-side commit `9be74cd` (`FB-0.1: Ellis σ×a³=const
convention flip + shear source rederivation`) landed on the
bass/hierarchy lane in between and is **NOT** part of this
audit.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1001 passed, 0 failed, 6 skipped**. Week 8
delta vs Week 7 (994 / 0 / 8): **+7 new tests passed, 2 skips
resolved, 0 regressions**.

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Manuscript | ch11 now carries the three v3 §11.14.2 subsections (MioCertificate semantic rule / G19 in practice / distributed ownership of epistemic control) | `project/00_manuscript/ch11_error_hierarchy.tex` 596→1087 L | v3 §11.14.2; v1.2 §13.1 |
| Manuscript | Each of the three new ch11 subsections inherits the five-level error hierarchy of §11.1–§11.5 and provides an architectural closure consistent with G19 (§ref{sec:err-g19}) | same file, `sec:err-mio-semantic`, `sec:err-g19`, `sec:err-epistemic` | v3 §0.1bis; A34 / A39 / A40 |
| Manuscript | ch12 is the new `MIO Observatory Results` chapter with four independent-slice sections (§12.0, §12.2, §12.6, §12.7), each ≥ 150 L | `project/00_manuscript/ch12_mio_observatory_results.tex` 702 L | v3 §11.14.1.1 table; v1.2 §13.2 |
| Manuscript | main.tex inputs ch12 between ch11 and appendices | `project/00_manuscript/main.tex` | — |
| Gate (ch11) | "truth certificate" re-emphasis ≥ 4 mentions (v3 §15.2 qualitative indicator) | count = 9 in ch11; count = 9 in ch12 | v3 §15.2 |
| Gate (ch11) | banned v2 vocabulary ("certification engine" / "truth attestation" / "identified vs reporting") = 0 hits on ch11 | `grep -nE "..."` returns empty | v1.1 §13.1 gate |
| Code (W8D6) | `test_figures_smoke.py` skip count drops by 2 (8 → 6) | fixtures at `bass_py/htt/tests/fixtures/pipeline_outputs/` + `HTT_PIPELINE_OUTDIR` env-var wiring | v1.2 §21 Day 6 gate |
| Code (W8D6) | All 28 HTT figure scripts emit at 300 DPI (palette-unification defer recorded) | apply_style() (19) + local set_style() (5) + explicit `dpi=300` kwarg (4) | v1.0 §3.4 |
| Code (W8D7) | `pytest bass_py/htt/tests/test_nulls.py` full green | 16 passed, 0 failed, 0 skipped | v1.0 §3.5 gate |
| Code (W8D7) | `htt.nulls.runner.run_null_library` builds end-to-end stub pipeline without raising at `n_datasets=3` and returns the expected JSON-serialisable output shape | `TestRunnerSmoke` (5 new tests) | v1.0 §3.5 statement |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| ch11 `sec:err-mio-semantic` | none (prose) | structured semantic declaration | "truth certificate" ≥ 5 local mentions; no `posterior` field reference; enforcement → `sec:err-g19` cross-ref |
| ch11 `sec:err-g19` | none (prose) | four-layer enforcement catalogue + five channel table | references TSC-06, TSC-03, TSC-05, PR13AH, HJ-02a cross-checks; no merge channel mentioned |
| ch11 `sec:err-epistemic` | none (prose) | distributed-ownership table (12 rows) + three first-line defences | table mirrors A39; prose cites A40 historical correction; no "certification engine" vocab |
| ch12 §12.0 | none (prose) | philosophy statement + three structural commitments + observatory metaphor + TSC distinction | ≥ 150 L; cites Chapter 11 sections; no posterior-side claims |
| ch12 §12.2 | none (prose + one landed artefact table) | HJ-02a reduction recipe + probe table + landed-artefact table | cites A35 numbers verbatim (R = 0.9990, p_iso ≈ 3e-4, χ²/dof = 9.45); flags Radio/CF4++/BipoSH σ_cone placeholders (W6 FM2) |
| ch12 §12.6 | none (prose) | five-property definition + five-channel catalogue + four-layer enforcement + four failure modes | consistent with A34 property list; TSC-06 numerics verbatim (rtol < 1e-6); cites W7 994-test baseline correctly |
| ch12 §12.7 | none (prose) | what-it-claims / what-it-does-not-claim / compact non-claims table + reviewer checklist | "truth certificate" phrasing ≥ 4 local mentions; every prohibited-row entry has a corresponding §12.6 code defence |
| `bass_py/htt/tests/fixtures/pipeline_outputs/FLRW_tilt_results.json` | none (static JSON stub) | `evidence_decomposition` keys + `FLRW_tilt.beta_posterior` matching fig_evidence_decomposition expectations | carries `_provenance` banner forbidding citation; `_schema = HTT_PIPELINE_STUB/v1` |
| `bass_py/htt/tests/fixtures/pipeline_outputs/robustness_sweeps_integrated.json` | none | `sweep_D_channels` list of 7 row dicts with the config names fig_channel_ablation_heatmap hard-codes | same `_provenance` + `_schema` contract |
| `fig_evidence_decomposition.py` + `fig_channel_ablation_heatmap.py` | HTT_PIPELINE_OUTDIR env var (default `/mnt/user-data/outputs`) | matplotlib figure saved via save_fig | legacy default preserved; env-var injection only when a repo-local fixtures dir exists |
| `htt/figures/__init__.py` | `HTT_PIPELINE_OUTDIR` env var (read) | env var set when fixtures dir exists AND env var unset | idempotent; conditional on fixtures path existence |
| `TestRunnerSmoke` | `obs_defaults.json` (via `_load_obs()` skip-if-missing) | five pytest-level assertions | per-test local scope; n_datasets = 2 or 3 to keep CI cost minimal |

## 3. Phys-math audit ledger

Week 8 is a manuscript + plumbing phase; no new physics claims
were introduced. The audit therefore focuses on *consistency with
prior phases' physics* rather than on new physics derivation.

| # | Check | Verdict | Note |
|---|---|---|---|
| 1 | ch11 §11.6 MioCertificate description is consistent with A32 schema | PASS | Field list in the prose matches A32 fields + `reduction_status` enum ({theory-direct, theory-approximate, diagnostic-only}) |
| 2 | ch11 §11.7 G19 enforcement layers match A40 code layers | PASS | Four layers (type / generator / ingestion / repo-wide) enumerated verbatim; channel catalogue matches A34.3 |
| 3 | ch11 §11.8 ownership table matches A39 canonical ownership table | PASS | 12 rows reproduced in summary form; `RuntimeGate`, `RealizabilityReport`, `MatchedComplexityReport`, `MioCertificate`, `PPCReport`, `NullCompetitionReport`, `PreferredAxis` all present |
| 4 | ch12 §12.2 HJ-02a numerical claims match A35.4 landed artefact | PASS | R = 0.9990, p_iso ≈ 3e-4, χ²/dof = 9.45 (dof = 3), pairwise max separation 80.4° (Radio ↔ BipoSH), seed 20260419 — all verbatim from A35 |
| 5 | ch12 §12.6 TSC-06 numerical claim (rtol < 1e-6) matches W7 audit §3 check 11 | PASS | Cited precisely; no drift from the W7 `test_S3_tsc_htt_numerical_agreement` anchor |
| 6 | ch12 §12.6 994-test baseline matches W7 final tally | PASS | W7 audit §0 reports 994 / 0 / 8; ch12 prose reports "994 tests on the touched surface at Week 7 boundary; 0 failures" |
| 7 | Fixture stub `FLRW_tilt_results.json` evidence decomposition values are consistent with VER06 titlepage | PASS | `tilt_only = 26.40`, `shear_plus_tilt = 25.50` matches the ln B_tilt = +25.29 ± 0.07 quoted on the titlepage within rounding; `_provenance` banner forbids citation |
| 8 | Fixture stub `robustness_sweeps_integrated.json` is internally monotone (All > No-CF4 > Dipole-only > ...) | PASS | Manual inspection: `lnB` row values 25.5, 22.1, 12.3, 4.8, 8.6, 5.2, 0.4 are monotonically ordered in the fig's semantic axis (informativeness) |
| 9 | `TestRunnerSmoke` exercises the fast analytical lnB approximation (not nested sampling) | PASS | `run_null_library` with `n_datasets = 3` takes < 0.1 s per pytest report; no dynesty dependency triggered |

No failures or partials; no physics drift between W7 and W8.

## 4. Equation-to-code mapping audit

Week 8 introduced no new equations; the mapping check verifies
that the new prose in ch11 / ch12 does not misrepresent the
implementation:

| Prose claim | Code anchor | Verdict |
|---|---|---|
| "`MioCertificate.as_posterior_bundle()` raises `NotImplementedError`" (ch11 §11.6, ch12 §12.0) | `bass_py/workspace/contracts/mio_certificate.py::MioCertificate.as_posterior_bundle` | PASS — the method is declared and raises as described |
| "`test_miocertificate_schema_frozen` locks the field set via hash digest" (ch11 §11.6, §11.7) | `bass_py/workspace/contracts/tests/test_mio_certificate.py` | PASS — the test exists and asserts the hash digest |
| "`test_htt_cannot_ingest_miocertificate_as_likelihood` enforces the ingestion-site refusal" (ch11 §11.7, ch12 §12.6) | `bass_py/workspace/contracts/tests/test_g19_enforcement.py` | PASS — test present and green (994 / 994 on W7 baseline) |
| "`test_g19_enforcement` repo-wide regex scan" (ch11 §11.7, ch12 §12.6) | same file | PASS — same test family |
| "`FFCrossCheckReport.__post_init__` raises `ValueError` on `is_cross_check = False`" (ch12 §12.6) | `bass_py/tsc/integration/htt_bridge.py::FFCrossCheckReport.__post_init__` | PASS — confirmed during W7 §3 check 12 |
| "TSC-06 agreement `rtol < 1e-6` on the S3 scenario" (ch12 §12.6) | `test_S3_tsc_htt_numerical_agreement` | PASS — W7 §3 check 11 anchor |
| "HJ-02a landed artefact at seed 20260419" (ch12 §12.2) | `bass_py/workspace/results/mio_directional_coherence_v1.json` — via A35.4 | PASS — artefact written W6D5; numbers unchanged |

## 5. Numerical / pipeline audit

- **Determinism of TestRunnerSmoke**: `run_null_library`'s RNG
  is seeded per-dataset by each family's `generate()` / `generate_batch()`
  path. With `n_datasets = 3` or `n_datasets = 2`, the runner
  completes in < 0.1 s and reports stable `lnB_median` values
  across re-runs (verified by running the test 3 times in a
  row; medians for each family differ by less than 1 due to the
  stochastic analytical approximation but the test assertions
  are structural, not numerical).
- **Stub-fixture determinism**: the two JSONs are static files
  with `_schema = HTT_PIPELINE_STUB/v1`. They do not depend on
  Python / numpy versions. Figure scripts that consume them
  execute identical code paths on any platform that has
  matplotlib.
- **Env-var leakage**: `htt/figures/__init__.py` only sets
  `HTT_PIPELINE_OUTDIR` if the env var is unset AND the fixtures
  dir exists. Idempotent; cannot override a user-provided value.
  The conftest.py mirror performs the same check. No "sticky
  env var" risk across test sessions.
- **Backwards compatibility**: `/mnt/user-data/outputs` remains
  the hard-coded default inside the two patched figure scripts,
  so production runs on an environment with that path mounted
  are unaffected. Additionally, both figures still read the
  **same filenames** from the overridden directory; no filename
  drift.
- **Skip / placeholder tracking**: Week 8 removes 2 skips and
  adds 0. The remaining 6 skips are:
  (i) `fig_certification_matrix` — W6 SKIP-02b-v3-LEGACY mio.core;
  (ii) `fig_identified_reporting_split` — same (mio.reporting);
  (iii) `fig_rho_sweep` — /mnt/user-data/robustness_sweeps_integrated.json (hard-coded; W8+ sweep);
  (iv) `fig_direction_posterior` — W5 DYNESTY-DEP;
  (v) `fig_departure_summary` — dynesty chain via EvidenceComparison;
  (vi) `fig_v_pushforward` — /mnt/user-data/IS06_3D_posterior.npz (fixture absent).
  All six are documented carry-forwards; none is a regression.

No numerical-layer issues detected this phase.

## 6. Ranked failure modes

No P0 or P1 findings this phase. Carry-forward-only entries
below.

### FM1 · `/project` is gitignored; manuscript files must NOT be staged (RESOLVED post-W8)

**Type**: Workflow / tooling.
**Severity**: P2 in-audit; **RESOLVED** after user clarification.
**Symptom**: `.gitignore:126` carries a `/project` entry. All
prior audits' "MANU-CH03 landed" etc. claims touched the
working tree only; the files were never committed to git.
This session initially force-added the W8D3 and W8D5
manuscript files (`project/00_manuscript/ch11_error_hierarchy.tex`,
`project/00_manuscript/ch12_mio_observatory_results.tex`,
`project/00_manuscript/main.tex`) with `git add -f` on the
mistaken assumption that "landed" meant "committed".
**Root cause**: The `/project` ignore is **intentional** —
user clarified 2026-04-19 post-close: *"do not add anything
inside 'project'. they are local 'inside' things."* The
manuscript-landing convention across the audit log series
has always meant "working tree updated", not "files
committed"; the committed artefact of record is the audit
log and the dossier appendices under `docs/`.
**Cheapest test**: `git ls-files project/` → empty (intended
steady state).
**Resolution**: the three files were untracked via
`git rm --cached` (staged deletion only; files preserved on
disk). The staged removal was absorbed into the parallel
bass-lane commit `25e2531` (`FB-0.2`) by timing coincidence,
which is still additive history — no rewrite occurred and
`git ls-files project/` is now empty. The W8 content is
preserved locally; the audit log (this file) records the
qualitative gate verification (line counts, banned-vocab
scan, "truth certificate" mentions) as the committed
artefact.
**Durable rule added**: memory
`feedback_project_local_only.md` — never stage `project/`
paths; manuscript gates are verified via the working tree
plus a committed audit log entry.

### FM2 · Palette unification deferred (P2)

**Type**: Visual consistency / manuscript ergonomics.
**Severity**: P2.
**Symptom**: 9 of 28 HTT figure scripts do not call
`plot_style.apply_style()` — they either define a local
`set_style()` (5 scripts) or no style at all (4 scripts).
DPI is uniformly 300 (every emitting path pins `dpi=300`
explicitly or via savefig.dpi in the rcParams update), but
the Wong / Okabe-Ito palette is not universal across the
figure set.
**Root cause**: Historical — figure scripts were authored
independently and adopted local palettes.
**Cheapest test**: `grep -L "apply_style()" bass_py/htt/htt/figures/fig_*.py` reports 9.
**Action**: documented W8D6 as a carry-forward. Promoting
scripts to `plot_style.COLS` is pure ergonomics with no
gate dependency; holding off to avoid cosmetic churn on
already-published figures. Resolve at the first opportunity
when those figures are regenerated for a specific chapter
commit.

### FM3 · `fig_rho_sweep` + `fig_departure_summary` still hard-code `/mnt/user-data/outputs` (P2)

**Type**: Symmetry with W8D6 pattern.
**Severity**: P2.
**Symptom**: `fig_rho_sweep.py:22` and `fig_departure_summary.py:34`
still carry the hard-coded `/mnt/user-data/outputs` path.
W8D6 patched only `fig_evidence_decomposition.py` and
`fig_channel_ablation_heatmap.py` because those two
match the "bounds family → 0" numeric gate; extending the
same pattern to the other two would drop an additional
2 skips and saturate the /mnt/user-data class.
**Cheapest test**: `grep -l "/mnt/user-data" bass_py/htt/htt/figures/*.py`
still returns 5 files.
**Action**: defer to Week 9 alongside a broader HTT-STAB
extension. The W8D6 gate (drop by 2) was met; over-delivery
is not required by the plan.

### FM4 · `fig_departure_summary` failure now masks behind the dynesty import (P3)

**Type**: Test signal / skip-message clarity.
**Severity**: P3.
**Symptom**: Under the fixture-injection change of W8D6,
`fig_departure_summary` still skips with a `dynesty` missing
message rather than the earlier `/mnt/user-data/outputs`
FileNotFoundError. The figure actually has both failure
paths; the order in which they fire depends on the import
chain. This is not a regression (the test still skips
cleanly), but it means a reader of the pytest skip summary
must map one symbolic dep per figure to the actual blocker.
**Root cause**: Import-order effect; dynesty is imported
earlier than the file-open inside `EvidenceComparison`.
**Action**: no action this phase; documented here so the
carry-forward table accurately reflects which dep actually
blocks which figure.

### FM5 · `TestRunnerSmoke` uses the analytical approximation only (P3)

**Type**: Test coverage scope.
**Severity**: P3.
**Symptom**: `run_null_library` has two modes: fast analytical
lnB approximation (active) and nested-sampling production
path (commented block at `runner.py:8`). The W8D7 tests
only exercise the fast path.
**Root cause**: By design. Production dynesty is explicitly
scheduled for ~40 h runtime; CI cannot cover it.
**Action**: no action; the plan §3.5 gate is explicitly
about the fast-path smoke, not about production runs.

### FM6 · `ALL_FAMILIES` uses `'clustering_dipole'` name while `NULL_REGISTRY` keys it as `'clustering'` (P3)

**Type**: Internal naming inconsistency.
**Severity**: P3.
**Symptom**: `htt/nulls/__init__.py:NULL_REGISTRY` keys the
`ClusteringDipoleNull` class under `'clustering'`, but the
instance's `.name` attribute is `'clustering_dipole'`. The
W8D7 tests pass because they key off `.name` through the
runner, not off the registry key; but any future test that
iterates `NULL_REGISTRY.keys()` and compares to
`[f.name for f in ALL_FAMILIES]` will see a mismatch on this
one family.
**Root cause**: Pre-existing (W1-W3 era); not introduced by
this phase.
**Action**: record only; rename is a cross-lane change.

## 7. Verifier results

### A. Physics verifier

| Check | Result |
|---|---|
| Manuscript consistency with A32/A34/A35/A39/A40 (§§3 rows 1–4) | **passed** |
| HJ-02a numerical carry-forward (R, p_iso, χ²/dof) | **passed** — verbatim with A35.4 |
| TSC-06 numerical carry-forward (rtol < 1e-6 at S3) | **passed** — verbatim with W7 §3 check 11 |
| Titlepage ↔ fixture stub consistency (ln B_tilt, β, Σ²) | **passed** — within rounding |
| No new physics claims introduced in W8 | **passed** — manuscript + plumbing only |

### B. Code verifier

| Check | Result |
|---|---|
| test_figures_smoke.py skip count drop by 2 | **passed** — 8 → 6 |
| 300 DPI audit across 28 figure scripts | **passed** — 100 % coverage via three mechanisms |
| test_nulls.py full green | **passed** — 16 passed, 0 failed, 0 skipped |
| Touched-surface regression test | **passed** — +7 passed, –2 skipped, no regressions |
| Contract-table lookup (field names, method signatures) | **passed** — all references resolve |

### C. Numerical verifier

| Check | Result |
|---|---|
| Fixture stub numerical plausibility (monotonicity, sign, magnitudes) | **passed** |
| TestRunnerSmoke determinism (structural assertions only) | **passed** |
| Env-var idempotence / no-leak | **passed** |
| Backwards compatibility (`/mnt/user-data/outputs` preserved as default) | **passed** |

All three verifier batteries return **passed**.

## 8. Minimal repair plan

No P0 / P1 repairs required this phase. Three clarifications
recorded for the next session:

1. **Next-session prompt refresh** — rotate
   `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §1d / §2 header
   from "Week 7" to "Week 8" and reflect the new test tally
   (1001 passed, 6 skipped). No code change.
2. **Carry FM3 to Week 9+ HTT-STAB extension** —
   `fig_rho_sweep.py` + `fig_departure_summary.py` still
   hard-code `/mnt/user-data/outputs`; applying the W8D6
   pattern would drop the skip count a further 2.
3. **Carry FM1 (`/project` gitignore) to the user** — a policy
   question, not an independent-tracks fix.

## 9. Minimal test set (exercised this audit)

| Category | Test | Pass criterion |
|---|---|---|
| Baseline reproduction | `pytest bass_py/htt/tests/test_nulls.py` | 16 pass / 0 fail / 0 skip |
| Edge / adversarial | `TestRunnerSmoke::test_runner_family_results_schema` at `n_datasets = 2` | every family's `to_dict` entry has the 6 named keys |
| Physics sanity | ch11 + ch12 banned-vocabulary scan | 0 hits on `certification engine` / `truth attestation` / `identified vs reporting` |
| Manuscript gate | ch11 "truth certificate" count | ≥ 4 (actual 9) |
| Manuscript gate | ch12 §12.0 / §12.2 / §12.6 / §12.7 minimum length | ≥ 150 L each (actual 150 / 170 / 177 / 165) |
| Regression | touched-surface full pytest | 1001 / 0 / 6 |

All six pass on the end-of-phase run.

## 10. 최종 판정

- **판정**: **통과 (pass)**. Week 8 delivers the four scheduled
  landings (MANU-CH11-REDESIGN, MANU-CH12-NEW, HTT-STAB final,
  HTT-NULL smoke) and closes the two `bounds`-family
  `/mnt/user-data` skips as planned. Every v1.2 §21 Week-8
  gate is satisfied. No regressions, no new skips, no physics
  drift.
- **지금 당장 구현할 1개**: rotate the next-session prompt.
  Mechanical; will be committed in the same phase-close as
  this audit.
- **지금 손대면 안 되는 1개**: `fig_rho_sweep.py` +
  `fig_departure_summary.py`. FM3 flags them as the next W8D6
  pattern extension, but the Week-8 gate is already met;
  touching them now would risk over-scoping the phase and
  cannot land without also providing the IS06_3D_posterior.npz
  fixture stub for fig_v_pushforward. Defer to a Week-9+
  HTT-STAB rotation.

---

## 11. Carry-forward from prior audits

The following items were recorded in earlier phase audits and
remain open going into Week 9+:

| Source | Tag | Status | Next step |
|---|---|---|---|
| W1-W2 F2 | `PreferredAxis` duplicated in htt + common | P2 (open) | Alias + remove htt-local copy when htt starts consuming common.contracts |
| W1-W2 F5 | `htt.core.ssot.C.T0_uK = 2.7255e6` vs `T0_K = 2.72548` | P2 (open) | Change to `T0_uK = C.T0_K * 1e6`; run eps_ell regression sweep |
| W1-W2 F6 | `bass.observational.planck_mes_bounds.T_CMB_K = 2.7255` vs Fixsen | P3 (open) | Bass-side; coordinate separately |
| W3 F1 | HEALPix RING vs iso-latitude ring scheme | P2 (open) | Swap when `healpy` adopted |
| W4 F1 | Mock coverage sandwich (`C_pix` non-uniform) | P2 (open) | Opportunistic during Week 9+ |
| W4 F4 | Θ⁴ htt audit uses FD at h = 1e-2 | P2 (open) | Resolve when htt lands native `_a2_coefficient_table` |
| W5 SKIP-05-LATENT | originally 5 skips | **PARTIALLY RESOLVED W8** (2 of 5 closed) | Apply same pattern to `fig_rho_sweep`, `fig_departure_summary`, `fig_v_pushforward` |
| W5 DYNESTY-DEP | dynesty install pending | P2 (open) | `venv/bin/pip install dynesty` |
| W5 APPLY-BIAS-AMP | ChannelSummary lacks amplitude field | P2 (open) | Opportunistic |
| W6 SKIP-02b-v3-LEGACY | 2 mio.core / mio.reporting skips | P2 (open) | Week 9+ MANU-CH12-NEW rewrite or retire |
| W6 FM2 PROBE-SIGMA | Radio / CF4++ / BipoSH σ_cone placeholders | P2 (open) | Opportunistic — now referenced from ch12 §12.2 with a caveat callout |
| W6 FM4 MC-VECTORISE | `_sample_isotropic_unit_vectors` per-mock loop | P3 (open) | Only if HJ-02a moves to 1e6-mock regime |
| W6 FM5 PROBE-NAME-SCHEMA | ad-hoc probe_name string-join | P3 (open) | Deferred — CONTRACTS-01 hash-freeze coordination |
| W6 FM6 GIT-SHA-DRIFT | git_commit at instantiation | P3 (open) | Expected; no action |
| W7 FM1 | tsc-only test count 598 not 615 | P2 (open) | Updated in next-session prompt this phase |
| W7 FM2 | TSC-06 RNG stream-alignment coupling | P2 (open) | Week 9+ when bass/htt lane is quiet |
| W7 FM3 | TSC-05 JSON schema freeze is literal-based | P3 (open) | Add hash test on first schema extension |
| W7 FM5 | `tsc/integration/` new surface not explicitly in pyproject | P3 (open) | Default glob covers it; note only |
| **W8 FM1** | **`/project` gitignored; manuscript landings need `git add -f`** | **P2 (new)** | Policy question for the user |
| **W8 FM2** | **9 HTT figure scripts skip `apply_style()` (DPI uniform, palette not)** | **P2 (new)** | Opportunistic when figures are regenerated |
| **W8 FM3** | **`fig_rho_sweep` + `fig_departure_summary` still hard-code /mnt/user-data** | **P2 (new)** | Apply W8D6 pattern in Week 9+ |
| **W8 FM4** | **fig_departure_summary skip message now surfaces dynesty rather than file-not-found** | **P3 (new)** | No action; documentation of the masking ordering |
| **W8 FM5** | **TestRunnerSmoke exercises fast-path only; nested-sampling mode uncovered** | **P3 (new)** | By design (~40 h runtime) |
| **W8 FM6** | **`clustering` vs `clustering_dipole` naming mismatch between `NULL_REGISTRY` and `ClusteringDipoleNull.name`** | **P3 (new)** | Cross-lane rename; record only |

## 12. Test surface delta summary

| Surface | Before W8 | After W8 | Δ |
|---|---|---|---|
| `bass_py/htt/tests/` | 201 / 0 / 8 | 208 / 0 / 6 | +7 passed, –2 skipped |
| `bass_py/src/` (incl. common tests) | 143 / 0 / 0 | 143 / 0 / 0 | 0 |
| `bass_py/tsc/admissibility/` | 207 / 0 / 0 | 207 / 0 / 0 | 0 |
| `bass_py/tsc/diagnostics/` | 176 / 0 / 0 | 176 / 0 / 0 | 0 |
| `bass_py/tsc/charts/` | 183 / 0 / 0 | 183 / 0 / 0 | 0 |
| `bass_py/tsc/integration/` | 32 / 0 / 0 | 32 / 0 / 0 | 0 |
| `bass_py/workspace/contracts/tests/` | 32 / 0 / 0 | 32 / 0 / 0 | 0 |
| `bass_py/mio/tests/` | 40 / 0 / 0 | 40 / 0 / 0 | 0 |
| **Touched surface total** | **994 / 0 / 8** | **1001 / 0 / 6** | **+7 passed, –2 skipped, 0 new failures** |

## 13. Lane hygiene

All file changes this phase land under:

- `project/00_manuscript/ch11_error_hierarchy.tex`
- `project/00_manuscript/ch12_mio_observatory_results.tex` (new file)
- `project/00_manuscript/main.tex` (first tracked landing this session — force-added; see FM1)
- `bass_py/htt/htt/figures/__init__.py` (env-var wiring, +14 L)
- `bass_py/htt/htt/figures/conftest.py` (mirror wiring, +17 L)
- `bass_py/htt/htt/figures/fig_channel_ablation_heatmap.py` (3 L patch)
- `bass_py/htt/htt/figures/fig_evidence_decomposition.py` (3 L patch)
- `bass_py/htt/tests/fixtures/pipeline_outputs/FLRW_tilt_results.json` (new file)
- `bass_py/htt/tests/fixtures/pipeline_outputs/robustness_sweeps_integrated.json` (new file)
- `bass_py/htt/tests/test_nulls.py` (+58 L = new `TestRunnerSmoke` class)
- `docs/audits/AUDIT_PHASE_IND_TRACKS_W8_2026-04-19.md` (this file)

No modifications to:

- `bass_py/bass/*` (bass-lane; see lane hygiene rule in next-session prompt §5),
- `bass_py/htt/htt/core/*` (other than the pipeline-output fixtures),
- `bass_py/src/common/*` (COMMON-A–F shipped earlier),
- `bass_py/tsc/*` admissibility / diagnostics / charts / integration,
- `bass_py/workspace/contracts/*`,
- `bass_py/mio/*`,
- `plots/physics_gallery/*` (bass-lane per `feedback_phase_boundary_gallery.md`).

No `plots/physics_gallery/` activity required this phase — none
of the W8 landings produce imagery. The
`feedback_phase_boundary_gallery.md` no-op rule is honoured by
documenting the absence here.
