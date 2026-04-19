# Phase-boundary audit — Independent Tracks Week 9

**Phase tag**: `IND_TRACKS_W9`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.2 §21 Week 9 day-by-day
schedule — DOS-A13 remaining 12 models (Days 1–3), HTT-STAB round 2
(Day 4), W7 FM2 TSC-06 RNG stream refactor (Day 5), full-regression
audit + MIO midpoint (Days 6–7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §11.10.1 (A13 dossier structure);
v3 §11.14.6 (15-model ladder);
v3 §15.1 (regression target trajectory);
INDEPENDENT_TRACKS_PLAN v1.0 §3.4 (HTT-STAB);
v1.0 §14.3 / A34 (G19 cross-check protocol);
v1.2 §21 (Week 9 day-by-day).
**Baseline head**: `e94d8d8` (`FB-0.3: close LB-6 F2 carry; seal
Phase FB-0`) + `98fff7c` (`IND_TRACKS_W8: phase audit +
next-session prompt rotation`). The W9 work sits atop main.
**Commits this phase** (this lane — proposed tags; commits authored
in the same session):

- `W9D1–D3`: DOS-A13 12 new dossiers (A13_02 … A13_13 — covers all
  14 non-FLRW models in `htt.core.evidence_models_R03a.ALL_MODELS`,
  with the two `*_grow` siblings folded into their `_orth` / `_tilt`
  parents per W8 FM6-style cross-variant grouping).
- `W9D4`: AUDIT(W8-FM3) HTT-STAB round 2 — `/mnt/user-data` pattern
  extended to `fig_rho_sweep.py` + `fig_v_pushforward.py` +
  `fig_departure_summary.py`; fixtures for `sweep_A_rho` rows and
  `IS06_3D_posterior.npz`; smoke-test skip count 6 → 4 (fig_rho_sweep
  and fig_v_pushforward newly pass; fig_departure_summary still skips
  — dynesty blocker noted).
- `W9D5`: AUDIT(W7-FM2) FillingFraction stream refactor —
  `FillingFraction.mc_posterior` now accepts `pre_drawn_eps=`
  kwarg; `ff_htt_mc_cross_check` draws the triple once and passes it
  to both paths. Adds 4-test `TestW7FM2StreamAlignment` class
  (shape-mismatch, pre-drawn acceptance, reordering-proof
  bit-identity, rtol round-trip).
- `W9D7` (= W9 phase audit): this file + NEXT_SESSION rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1007 passed, 0 failed, 4 skipped**. Week 9 delta
vs Week 8 (1001 / 0 / 6): **+6 tests pass (+4 new FM2 regression +
2 formerly-skipped figures now green), 2 skips resolved (W8 FM3
HTT-STAB round 2 close-out), 0 regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed (up from
598 post-W7; +4 from the W7 FM2 stream-alignment battery; composition
otherwise unchanged).

**MIO contribution**: 37 tests (W6 baseline; no MIO work this week —
track remains ahead of the ≥ 25 Week-9 gate).

**Full-monorepo collection** (informational, includes the bass_py
session's lane which is out-of-scope for this audit):
`bass_py/` collects 3 193 tests. Per-package breakdown: bass = 2 091,
tsc = 602, htt = 214, common (src) = 133, mio = 37, workspace = 25.

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Docs (DOS-A13) | 14 numbered A13 files present covering template + FLRW + FLRW_tilt + 12 Bianchi-family dossiers, with every non-FLRW entry in `ALL_MODELS` referenced at least once | `docs/dossier/A13_00_FLRW.md` (pre-W9), `A13_01_FLRW_tilt.md` (pre-W9), `A13_02_BI_orth.md` … `A13_13_BVIIh_tilt.md` (W9D1-D3) | v3 §11.10.1 + INDEPENDENT_TRACKS_PLAN v1.2 §21 Week 9 Days 1–3 gate |
| Docs (DOS-A13) | Each dossier follows `A13_template.md` section order (Model identity / Free parameters / Kinematic signature / Distinguishing channels / Scenarios / Posterior / Pitfalls / Figures / Provenance) | inspection of each A13_NN file | `A13_template.md` |
| Docs (DOS-A13) | Each dossier quotes the corresponding `htt.core.evidence_models_R03a` class name and prior specification verbatim | §1 and §2 of each A13_NN file | `bass_py/htt/htt/core/evidence_models_R03a.py` |
| Code (W9D4) | `HTT_PIPELINE_OUTDIR` env-var pattern applied to three remaining `/mnt/user-data/outputs`-hard-coded figures | `bass_py/htt/htt/figures/fig_rho_sweep.py`, `fig_departure_summary.py`, `fig_v_pushforward.py` | v1.0 §3.4 + W8D6 precedent |
| Code (W9D4) | `fig_v_pushforward.py` catalogue-likelihood import typo fixed (`catalog_velocity_likelihood` → `catalog_likelihood`) | same file, L137 | `bass_py/htt/htt/core/catalog_likelihood.py` (hellinger_distance export) |
| Code (W9D4) | Fixture: `robustness_sweeps_integrated.json` extended with `sweep_A_rho` list (11 rows, monotone in ρ) | `bass_py/htt/tests/fixtures/pipeline_outputs/robustness_sweeps_integrated.json` | v1.2 §21 Week 9 Day 4 gate |
| Code (W9D4) | Fixture: `IS06_3D_posterior.npz` (β/ℓ/b arrays, n=2000, seed 42) | same dir | same gate |
| Code (W9D4) | Smoke-test skip count drops to ≤ 4 (from 6) | `pytest bass_py/htt/tests/test_figures_smoke.py` → 53 pass / 4 skip | v1.2 §21 Week 9 Day 4 gate |
| Code (W9D5) | `FillingFraction.mc_posterior` accepts keyword-only `pre_drawn_eps=` triple; shape mismatch raises `ValueError` | `bass_py/htt/htt/core/analysis_extended.py` L99–L143 | W7 FM2 close |
| Code (W9D5) | `ff_htt_mc_cross_check` draws (ε₁, ε₂, ε₃) once on the bridge side and passes the shared triple to both `FillingFraction.mc_posterior` and the tsc re-derivation | `bass_py/tsc/integration/htt_bridge.py::ff_htt_mc_cross_check` | W7 FM2 close |
| Code (W9D5) | TSC-06 rtol round-trip preserved at 1e-4 post-refactor | `test_S3_round_trip_through_guard` + `test_cross_check_rtol_preserved_post_refactor` | v1.0 §14.3 TSC-06 gate |
| Regression (W9D5) | Reordering-proof: if htt inserts a phony rng draw at the top of `mc_posterior`, bit-identical tsc/htt values are preserved via `pre_drawn_eps` | `test_cross_check_stable_under_htt_rng_reordering` | W7 FM2 root-cause sketch |
| Gate (W9 final) | Touched-surface pass count monotonic non-decreasing vs W8 (+6); skip count non-increasing (−2) | pytest summary | v1.2 §21 Week 9 final-gate rubric |
| Gate (W9 final) | MIO contribution ≥ 25 | 37 tests | v3 §15.1 midpoint |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `A13_NN_*.md` (W9) | none (prose) | structured 9-section dossier | every file preserves template section order; references htt `ALL_MODELS` name verbatim in §1; cites evidence-models prior in §2; §6 posterior remains placeholder ("pending Phase H") |
| `robustness_sweeps_integrated.json` `sweep_A_rho` | none (static JSON stub) | 11 rows keyed by `rho` ∈ {0.0, 0.1, …, 1.0} with {rho, lnB, beta_median, Q_median, Pi_01, q0_mean} keys matching `fig_rho_sweep.py` hard-coded accessors | `_provenance` banner forbids citation; `_schema = HTT_PIPELINE_STUB/v1` preserved; lnB monotone non-increasing in ρ (sanity) |
| `IS06_3D_posterior.npz` | none | `beta`, `l`, `b` arrays (n=2000) | `beta` shape matches the figure's sole consumer `beta_cat = cat_data['beta']`; `_provenance` array records synthetic origin |
| `fig_rho_sweep.py`, `fig_departure_summary.py`, `fig_v_pushforward.py` | `HTT_PIPELINE_OUTDIR` env var (default `/mnt/user-data/outputs`) | matplotlib figure via save_fig | legacy default preserved; env-var injection only when a repo-local fixtures dir exists (via `htt/figures/__init__.py` + conftest) |
| `FillingFraction.mc_posterior(..., pre_drawn_eps=None)` | scenario / N / seed OR `pre_drawn_eps=(e1, e2, e3)` triple (keyword-only) | `(F_samp, med, q16, q84, q025, q975)` | pre-W9 signature untouched when `pre_drawn_eps is None`; shape-mismatch raises `ValueError`; ε₁ clipped to `[0, ∞)` on both paths (pre-drawn path still clips) |
| `ff_htt_mc_cross_check(scenario, N, seed, w)` | scenario string + N + seed + w | `FFCrossCheckReport(is_cross_check=True)` | shared triple drawn via `np.random.default_rng(seed)` on the bridge side; both paths receive that triple; tsc `F_Bayes_tsc` and htt `F_Bayes_htt_mean` report distinct numbers but agree within rtol 1e-4 on S3 |

## 3. Phys-math audit ledger

Week 9 is primarily a docs + refactor + fixture phase; physics
content is second-hand (mirrors the R03a evidence-models priors and
the MES ceiling contract landed in earlier phases). The audit
focuses on *consistency with the htt code registry* rather than on
derivation.

| # | Check | Verdict | Note |
|---|---|---|---|
| 1 | Each A13 dossier's §1 `ALL_MODELS` name matches `htt.core.evidence_models_R03a.ALL_MODELS` keys exactly | PASS | A13_02 → `BI_orth`, A13_03 → `BVII0_orth`, A13_04 → `BII_orth`, A13_05 → `BVI0_orth`, A13_06 → `BVIII_orth`, A13_07 → `BIX_orth`, A13_08 → `BVIIh_orth` (+ `BVIIh_orth_grow` sibling), A13_09 → `BI_tilt`, A13_10 → `BV_tilt`, A13_11 → `BIII_tilt`, A13_12 → `BIX_tilt`, A13_13 → `BVIIh_tilt` (+ `BVIIh_tilt_grow` sibling) |
| 2 | Each A13 dossier's §2 prior matches the class `prior_transform` body in R03a | PASS | BI_orth: Σ² log-uniform [1e-30, 1e-4] ✓; BII_orth adds n₁ log-uniform [1e-6, 1] ✓; BVI0_orth adds a₁ log-uniform [1e-6, 1] ✓; BV_tilt Ω_k Gaussian μ=0.0007, σ=0.0019, clamped positive ✓; BIX_orth Ω_k folded-Gaussian clamped negative ✓; BVIIh_orth x_h log-uniform [1e-3, 1e3] ✓; BVIIh_tilt W² log-uniform [1e-24, 1e-10] + x_h ✓; R_WS_VIIH = 1.06 ✓ |
| 3 | Each A13 dossier's §5 S3 scenario flag matches `SCENARIOS['S3']` description | PASS | S3 = "Full anomaly" with eps1 = 1.476e-3, β = 1.334e-3; dossiers refer to "full stack (+ BAO + lensing)" consistent with the v3 labeling |
| 4 | Pre-drawn-eps refactor preserves the physics identity x_V / x_max | PASS | The `_tsc_filling_fraction_from_stream` branch and htt's `mc_posterior` body both compute xV = (1+w)Ω_m sinh²(ε₁/(1+η_u̇)) and x_max = 1.5 × [(1 + 2.69 ε₁_ref)((5/3) ε₁_ref + 3 ε₂ + (3/7) ε₃)]²; the pre_drawn_eps path skips only the rng draws — the arithmetic is identical |
| 5 | `_mes_ok` + ε₁ clipping still fires on the pre_drawn_eps path | PASS | `e1_samp = np.clip(e1_samp, 0, None)` is applied in both branches of the refactored `mc_posterior` |
| 6 | Synthetic `sweep_A_rho` row lnB values are monotonically non-increasing in ρ | PASS | 26.3 → 24.8 → 22.4 → 19.5 → 15.8 → 11.3 → 6.8 → 3.1 → 0.6 → −0.4 → −0.9; matches the physical expectation that ρ → 1 corresponds to fully correlated CatWISE / Radio, which kills the tilt evidence |
| 7 | `IS06_3D_posterior.npz` β samples lie in a physically admissible interval (β ≲ 0.01, consistent with v3 §9.2 prior and MES ceiling) | PASS | `beta ~ half-normal(1.4e-3, 0.3e-3)`, median = 1.39e-3, far below the 1e-1 MES upper prior edge |

No failures or partials.

## 4. Equation-to-code mapping audit

| Prose claim | Code anchor | Verdict |
|---|---|---|
| A13_09 §3 "ε₁ = eps1_from_beta(β) couples β to the Ellis-Bruni ε₁ invariant" | `htt.core.evidence_models_R03a.eps1_from_beta` | PASS — same name, no typo |
| A13_08 §2 "W² = R_WS_VIIH² × Σ² with R_WS_VIIH = 1.06 (Wainwright & Ellis)" | constant at `evidence_models_R03a.py:54` and usage at L655, L671 | PASS |
| A13_10 §2 "Σ² derived from Sig2_BV(β, Ω_k)" | `evidence_models_R03a.Sig2_BV` + usage at L705 | PASS |
| W9D5 "pre_drawn_eps arrays must share the same shape" | `FillingFraction.mc_posterior` shape check at L122–L128 (raises `ValueError`) | PASS — covered by `test_pre_drawn_shape_mismatch_raises` |
| W9D5 "bit-identical tsc / htt agreement when htt's rng call order is perturbed" | `test_cross_check_stable_under_htt_rng_reordering` | PASS — test runs, asserts equality on tsc / htt means and median |
| W9D4 fixture "sweep_A_rho keys match fig_rho_sweep's hard-coded accessors" | `fig_rho_sweep.py` L25–L30 — `p['rho']`, `p['lnB']`, `p['beta_median']`, `p['Q_median']`, `p['Pi_01']` | PASS — each row dict in `sweep_A_rho` has all five keys |
| W9D4 fixture "IS06_3D_posterior.npz → cat_data['beta']" | `fig_v_pushforward.py` L35 | PASS — npz has `beta` key |

## 5. Numerical / pipeline audit

- **Determinism of W7 FM2 refactor**: the bridge's
  `np.random.default_rng(20260419)` is a fixed seed; the shared
  triple is now the deterministic input to both paths. Verified
  bit-identical agreement on `F_Bayes_tsc` and `F_Bayes_htt_mean`
  across re-runs with the same seed. The `test_S3_round_trip_through_guard`
  test continues to pass at `rtol = 1e-4`.
- **Reordering-proof regression**: `test_cross_check_stable_under_htt_rng_reordering`
  replaces `FillingFraction.mc_posterior` with a wrapper that draws
  a phony `np.random.default_rng(seed).normal(size=7)` before
  delegating back. With the old (pre-W9D5) seed-re-draw design this
  would have silently desynchronised tsc and htt; with the new
  `pre_drawn_eps` pathway, the bridge hands the same triple to both
  paths and the F_Bayes comparison is unaffected. The test asserts
  bit-equality on three fields (`F_Bayes_tsc`, `F_Bayes_htt_mean`,
  `F_Bayes_htt_median`) before and after the perturbation.
- **IS06 NPZ load under pytest**: the 8-line save_fig fallback in
  `plot_style.save_fig` (writes `/mnt/user-data/outputs/…` but
  silently closes the figure on OSError) keeps the figure-script
  import from crashing when it tries to save under pytest. Verified
  by `test_figure_script_imports_or_skips_cleanly[fig_v_pushforward.py]
  PASSED`.
- **Smoke-test skip enumeration**: after W9D4, the 4 remaining
  skips are `fig_certification_matrix`, `fig_departure_summary`,
  `fig_direction_posterior`, `fig_identified_reporting_split`.
  `fig_departure_summary` is dynesty-blocked (W8 FM4 carry-forward);
  the other three route through patterns outside the `/mnt/user-data`
  family (certification-matrix depends on `equiv_class`, direction
  posterior on workspace dep, identified/reporting on a different
  legacy root). These three are not plan targets for Week 9.

No P0 / P1 failures.

## 6. Ranked failure modes

| # | Type | Severity | Symptom | Root cause | Cheapest test |
|---|---|---|---|---|---|
| FM1 | Interface | P3 | The §6 of every A13 dossier reports `*pending*` — Phase-H dynesty runs have not occurred | v3 §7 roadmap; Phase H is a post-Week-9 step | none — by design |
| FM2 | Docs | P3 | DOS-A13 covers 14 of 16 `ALL_MODELS` entries as dedicated files; `BVIIh_orth_grow` and `BVIIh_tilt_grow` are folded into their `_orth` / `_tilt` parent dossiers as "variant inline" sections | Week 9 plan requests 12 new dossiers; 14 ALL_MODELS entries need coverage; folding the two `*_grow` siblings inline preserves one-file-per-canonical-model while hitting the "14 A13 files present" gate | spot-check: each of the two folded grow variants is named at least once in its parent dossier + A13_08 and A13_13 tag the grow-mode prior-edge shift explicitly |
| FM3 | Docs | P3 | The plan phrasing "remaining 12 Bianchi models (BI, BII, BIII_tilt, BV, BVIIh_tilt, BVIIh_tilt_grow, BVIIh_tilt_dec, BVIIh_orth, BVIIh_orth_dec, BIX_tilt, and the two 'grow/dec' variants not yet enumerated)" enumerates `_dec` variants that don't exist in `ALL_MODELS` (the default is `_shear_mode='decay'` without a `_dec` suffix) | Plan text was written against an intermediate code version that may have split dec/grow naming differently; current R03a code has `BVIIh_orth` (+ `BVIIh_orth_grow`) and `BVIIh_tilt` (+ `BVIIh_tilt_grow`), no `_dec` suffix | none — names clarified in dossiers §1, no code change needed |
| FM4 | Testing | P3 | `TestW7FM2StreamAlignment.test_cross_check_stable_under_htt_rng_reordering` uses `monkey-patch` via direct attribute assignment (`htt_ae.FillingFraction.mc_posterior = reordered`), which leaves a brief window of non-thread-safety during the test | Standard pytest pattern; test is wrapped in try/finally that restores the original attribute; serial test run | none — acceptable per-convention |
| FM5 | Fixtures | P3 | `IS06_3D_posterior.npz` contains only β / l / b; the production npz would include additional columns (Omega_tilt samples, covariance structure, dynesty weights) | Synthetic stub is minimal by design — only the one key `beta` that `fig_v_pushforward.py` consumes is required | `_provenance` array records stub-only status |
| FM6 | Manuscript | P3 | No `/project` changes this phase; ch03 still has the ~800 L gap against v3 §11.3 target | Week 9 scope is docs dossier + code plumbing; manuscript writing is W10+ | documented on §4 W10+ spill |

All P3. No P0 / P1 / P2 items newly identified — the W9 close-out
carries zero rollovers.

## 7. Verifier results

A. **Physics verifier**:
- known-limit recovery — n/a (docs + refactor)
- dimensional consistency — PASS (dossier §2 priors use same
  units as R03a code; W9D5 refactor preserves dimensions)
- sign / normalization — PASS (sweep_A_rho sign of lnB matches
  the ρ → 1 null limit; NPZ β sampled from |N(·,·)| guarantees
  β ≥ 0)
- positivity / admissibility — PASS (ε₁ clip preserved on both
  mc_posterior branches)
- alternative explanation — N/A (no new physics)

B. **Code verifier**:
- contract satisfaction — PASS (see §2 table)
- actual code-path usage — PASS (dossier §2 priors quote the
  actual R03a class bodies; fixture keys match hard-coded
  accessors; pre_drawn_eps kwarg actively used by bridge and
  tested for bit-identity)
- regression risk — low (4 new tests lock the pre_drawn_eps
  behaviour; all 36 pre-existing tsc.integration tests continue
  to pass)
- reproducibility — PASS (fixed seeds; no stochastic state
  leakage; test re-runs produce identical numerical values on
  this machine)

C. **Numerical verifier**:
- tolerance robustness — PASS (`rtol = 1e-4` on the S3 round-trip
  continues to hold post-refactor)
- convergence / stability — N/A (closed-form + MC; no iteration)
- baseline reproducibility — PASS (touched-surface count grows
  from 1001 → 1007 monotonically; no tests became flaky)
- uncertainty / misspecification awareness — PASS (every
  synthetic fixture carries a `_provenance` banner forbidding
  citation; every A13 dossier marks posterior fields *pending
  Phase H*)

All verifiers: **PASS**.

## 8. Minimal repair plan

No P0 / P1 / P2 findings; no repair needed for Week 9 close-out.

Opportunistic follow-ups (already catalogued in §3 of the
next-session prompt):

1. **W5 DYNESTY-DEP**: installing `dynesty` in this venv unblocks
   `fig_departure_summary.py` (skip count drops 4 → 3). One-liner:
   `venv/bin/pip install dynesty`. Deferred until after Phase H
   starts consuming it; not a Week 10 target.
2. **A13 dedicated `_grow` dossiers** (resolve FM2): split
   `BVIIh_orth_grow` and `BVIIh_tilt_grow` into their own
   `A13_14_*` and `A13_15_*` files so every `ALL_MODELS` entry has
   a one-file dossier. Only worthwhile if v3 §0.3 cross-model
   tables are regenerated and insist on one-file-per-model. Record
   only.

## 9. Minimal test set

For reproducibility of the Week-9 gates, the following is the
minimum pytest invocation that exercises every touched surface:

```bash
# Touched-surface baseline + W9 additions
venv/bin/pytest bass_py/htt/tests/ bass_py/src/ \
                bass_py/tsc/admissibility/ \
                bass_py/tsc/diagnostics/ bass_py/tsc/charts/ \
                bass_py/tsc/integration/ \
                bass_py/workspace/ bass_py/mio/
# Expect: 1007 passed, 0 failed, 4 skipped.

# TSC-06 + W7 FM2 regression class
venv/bin/pytest bass_py/tsc/integration/ -v
# Expect: 36 passed (4 new in TestW7FM2StreamAlignment).

# HTT-STAB round 2 smoke test
venv/bin/pytest bass_py/htt/tests/test_figures_smoke.py -v
# Expect: 53 passed, 4 skipped; fig_rho_sweep & fig_v_pushforward
# newly PASSED.

# tsc-standalone reproducibility
venv/bin/pytest bass_py/tsc/
# Expect: 602 passed.
```

Pass / fail criteria:

- Baseline reproduction — touched-surface suite reports exactly
  1007 / 0 / 4 with the same skip composition documented in §5.
- Edge — `test_pre_drawn_shape_mismatch_raises` raises ValueError
  on a (10, 11, 10) triple.
- Physics sanity — `test_cross_check_stable_under_htt_rng_reordering`
  asserts bit-equality under htt rng reordering (regression for
  W7 FM2).
- Numerical stability — `test_cross_check_rtol_preserved_post_refactor`
  asserts `rtol ≤ 1e-4` on the S3 round-trip.
- Regression — `test_figure_script_imports_or_skips_cleanly[fig_rho_sweep.py]`
  and `[fig_v_pushforward.py]` both PASS (previously SKIPPED).

## 10. Final verdict

- **치명적 오류 있음 / 부분 통과 / 통과**: **통과**.
- **지금 당장 구현/수정할 1개**: none — no P0/P1/P2 findings
  from this audit. Week 9 closes all four scheduled landings
  without carry-forwards.
- **지금 손대면 안 되는 1개**: `bass_py/bass/*` — that lane is
  actively receiving bass_py session work (FB-0.1 through FB-0.3
  landed 2026-04-19 while this lane was parallel). Do not touch
  until the bass_py session rotates to LB-7+. Also `plots/
  physics_gallery/` — gallery regeneration is the bass_py lane's
  per-phase rule; W9 is a pure docs + plumbing phase here, so no
  new physics artefact needs a gallery entry. Recorded explicitly
  per `feedback_phase_boundary_gallery.md` ("no-op phases
  document explicitly in audit log").

---

## Gallery note (per `feedback_phase_boundary_gallery.md`)

Week 9 landings are (a) 12 new A13 dossier `.md` files, (b) two
JSON/NPZ synthetic fixtures, (c) three figure-script path-routing
patches, (d) one kwarg on `FillingFraction.mc_posterior`, (e) four
new pytest functions in `test_htt_bridge.py`. None of these
produces a new physics figure that belongs in
`plots/physics_gallery/`. The fixture-driven figures
(`fig_rho_sweep.py`, `fig_v_pushforward.py`) now import cleanly
under pytest but still *run* with synthetic stubs — they do not
produce publication-grade PNGs that the gallery should carry.
**No gallery regeneration required this phase**, documented per
rule.

## Outstanding P2 / P3 items carried forward

From W1–W8 ledgers (unchanged; see W8 audit §6 for full table):
W1-W2 F2, F5, F6; W3 F1; W4 F1, F4; W5 SKIP-05-LATENT (now 3
of 5 resolved after W9D4 — only `fig_departure_summary` remains,
dynesty-blocked), W5 DYNESTY-DEP, W5 APPLY-BIAS-AMP; W6 SKIP-02b-v3-LEGACY,
W6 FM2 (now also W7 FM4), W6 FM4, W6 FM5, W6 FM6; W7 FM2 **RESOLVED
W9D5**; W7 FM3, FM4 (= W6 FM2), FM5; W8 FM1 **RESOLVED post-W8**,
W8 FM2, W8 FM3 **RESOLVED W9D4** (2 of 3 figure siblings;
fig_departure_summary sub-item remains dynesty-blocked), W8 FM4,
W8 FM5, W8 FM6. The new W9 P3s (FM1–FM6 above) are by-design notes;
they do not block any Week-10+ gate.
