# Independent Tracks — next-session resumption prompt

**As of**: 2026-04-19, post-`IND_TRACKS_W9` phase.
**Last audited**: 2026-04-19
(`docs/audits/AUDIT_PHASE_IND_TRACKS_W9_2026-04-19.md`;
prior phases `AUDIT_PHASE_IND_TRACKS_W8_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W6_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W5_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W4_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W3_2026-04-19.md`).
**Governing plan**: `INDEPENDENT_TRACKS_PLAN.md` **v1.2** (PART II MIO
integration patch + PART III Week-5+ realignment landed 2026-04-19;
Week 1–9 routine shipped; Week 10+ extension routine referenced below).
**Parent plan**: **`BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3** (MIO
added as 4th pillar; supersedes `BASS_PY_HTT_TSC_RESEARCH_PLAN.md` v2
which remains referenced from historical carry-forwards).

---

## §0. How to use this file

Open a **fresh** Claude Code session in this repository and paste or
point the agent at this file. It is designed to be self-contained —
the agent does not need to re-read `INDEPENDENT_TRACKS_PLAN.md`
end-to-end, only the specific sections referenced below.

First-order rules (copy-pasted from the governing plan):

* **additive commits only** (memory `feedback_git_workflow.md` — no
  branch rewrite; Python + Rust share one repo).
* **do not touch `bass_py/bass/*`** — that is the bass_py session's
  lane.
* **do not touch `plots/physics_gallery/`** — bass_py session
  auto-manages per-phase gallery regeneration
  (`feedback_phase_boundary_gallery.md`).
* **self-trigger `docs/audits/AUDIT_PROMPT.md`** before any
  phase-complete commit. P0/P1 must be fixed in-session with
  `AUDIT(<tag>):` prefix.

## §1. What shipped in Week 1–2

| Track | Artefact | Status |
|---|---|---|
| SSOT-01 | `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` + `bass_py/htt/tests/test_ssot_drift.py` | landed |
| HTT-P0-AM | `bass_py/htt/htt/PR13AM_te_sign_d1d3_bridge.py` + 4 tests | landed |
| HTT-P0-AJ | `bass_py/htt/htt/PR13AJ_full_a2m_restoration.py` + 7 tests | landed |
| HTT-P0-AH | `bass_py/htt/htt/PR13AH_observables_reintegration.py` + 8 tests (incl. R1 regression) | landed (audit R1 wiring COMMON-A `spherical_mean`) |
| TSC-01 | `bass_py/tsc/admissibility/test_realizability_extras.py` (+10 extras on top of 40 existing) | landed |
| COMMON-A | `bass_py/src/common/{contracts,sky_geometry,__init__}.py` + 34 tests; pyproject updated | landed |
| HTT-P0-ZOA20 | `bass_py/htt/htt/core/constants.py` + `bass_py/htt/tests/test_zoa20_sweep.py` + `docs/audits/ZOA20_SWEEP_2026-04-19.md` | landed (forward guard — sweep found 0 hits) |
| HTT-STAB / HTT-NULL | `bass_py/htt/htt/figures/conftest.py` + `test_figures_smoke.py`; `test_nulls.py` adds dl_pipeline candidate | landed |
| DOS-A13 | `docs/dossier/{A13_template, A13_00_FLRW, A13_01_FLRW_tilt}.md` | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W1W2_2026-04-19.md` | landed |

## §1b. What shipped in Week 3

| Track | Artefact | Status |
|---|---|---|
| COMMON-B | `bass_py/src/common/healpix_selection.py` + `test_healpix_selection.py` (24 tests incl. REG-01 `test_zoa_ladder_no_fallback_leak`) | landed |
| COMMON-C | `bass_py/src/common/bulkflow_estimator.py` + `test_bulkflow_estimator.py` (17 tests incl. REG-01 `test_weights_decomposition_logged`) | landed |
| MANU-CH03 (code-independent) | `project/00_manuscript/ch03_framework.tex` — new §"Observational framework for direction-resolved inference" (§3.X+5 Clarkson–Maartens, §3.X+6 spherical mean, §3.X+7 selection-aware likelihood); +444 L | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W3_2026-04-19.md` | landed |

## §1c. What shipped in Week 4

| Track | Artefact | Status |
|---|---|---|
| COMMON-D | `bass_py/src/common/bulkflow_likelihood.py` + `test_bulkflow_likelihood.py` (22 tests — `BulkFlowLikelihood`, `prior_transform`, `BulkFlowConfig`, `run_dynesty` with stub-injection for tests) | landed |
| COMMON-E | `bass_py/src/common/posterior_summary.py` + `test_posterior_summary.py` (19 tests — `samples_to_lb_posterior`, `credible_cone`, `hpd_region_healpix`, `axis_from_posterior`, `posterior_summary_dict`) | landed |
| COMMON-F | `bass_py/src/common/mock_calibration.py` + `test_mock_calibration.py` (17 tests **incl. REG-01 `test_mock_coverage_within_bounds` — coverage_68 = 0.670 ∈ [0.60, 0.76]**) | landed |
| TSC-02 | `bass_py/tsc/diagnostics/filling_fraction.py` + `test_filling_fraction.py` (22 tests — `FillingFractionReport`, `compute_filling_fraction`, `gaussian_posterior_F_Bayes`; published regression F_Bayes ∈ [0.068, 0.118] reproduced) | landed |
| TSC-04 | `bass_py/tsc/charts/theta4_bridge_verify.py` + `test_theta4_bridge_verify.py` (17 tests — `THETA4_A2_COEFFS_EXACT`, `gaunt_P_ell_int`, `verify_theta4_a2_coefficients`; closed-form {4, 4, 12/7, 44/7} at rtol 1e-10) | landed (P2 — ahead of schedule to unblock MANU-CH03 §3.X+3) |
| DOS-A14 | `docs/dossier/A14_N{1..5}_*.md` — 5 null-family derivations (scanning-law, mask-leakage, clustering-dipole, selection-response, survey-axis) | landed |
| MANU-CH03 | `project/00_manuscript/ch03_framework.tex` — new subsection `§3.X+3 Θ⁴ bridge` with boxed `a_2 = 4Q + 4A² + (12/7)Q² + (44/7)A²Q + …` identity + tsc verifier cross-reference; +93 L | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W4_2026-04-19.md` | landed |

## §1c-2. What shipped in Week 5

(see `AUDIT_PHASE_IND_TRACKS_W5_2026-04-19.md` for the full Week-5
ledger; retained for provenance but trimmed here to keep this file
useful as a next-session brief.)

Commits `3e96075` (W5D1) → `974fb4d` (W5D7). Seven daily landings +
audit. WS-BOOT-01, CONTRACTS-01, G19-ENFORCE-01, HTT-FIG-SHIM,
REG-02, PR13AM-MIO-TAG, HTT-OBS-FIXTURE, PR13AH-v2-WIRE,
LEGACY-README, DOS-A30-MIO (A32/A33/A39 drafts).

## §1c-3. What shipped in Week 6

(see `AUDIT_PHASE_IND_TRACKS_W6_2026-04-19.md`.) Commits `6d66058`
(W6D1) → `0e534c8` (W6D7). MIO-BOOT-01, FIG-MIO-SKIP-GATE,
MIO-HJ-06a, MIO-HJ-02a (directional coherence + artefact),
MIO-BRIDGES-01, MIO-HJ-05a-lite.

## §1c-4. What shipped in Week 7

Commits `75b51c5` (W7D2) → `acef13f` (W7D7). Five landings, one
phase-boundary audit (`AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| TSC-03 (Days 1-2) | `bass_py/tsc/admissibility/three_bound_hierarchy.py` — independent Fraction-routed MES-bound evaluators + `ThreeBoundReport` + `evaluate_all_bianchi_types` + hero `compare_against_htt_bounds`; 51 tests incl. `test_three_bound_hierarchy_matches_htt_bounds` (rtol 1e-10) | landed |
| TSC-05 (Day 3) | `bass_py/tsc/charts/michaelis_menten_export.py` — frozen Route B mirror (`ROUTE_B_C1=1.753e7`, `ROUTE_B_C2=6.825e5`, sentinel 0.17411 μK²) + scalar/array `d2_route_b` + `MichaelisMentenExport` dataclass + schema-frozen JSON; 33 tests incl. `assert_mirror_matches_bass_ssot` anchor | landed |
| TSC-06 (Days 4-5) | `bass_py/tsc/integration/{__init__.py, htt_bridge.py, test_htt_bridge.py}` (new subpackage) — `FFCrossCheckReport(is_cross_check=True frozen)` + `ff_htt_mc_cross_check` (S3 in band) + `ff_gaussian_cross_check` + `assert_cross_check_consistent`; 32 tests incl. `TestTscHttFfCrossCheckNotMerged` G19 merge-prohibition battery | landed |
| CONTRACTS-02 (Day 6) | `docs/dossier/A34_g19_cross_check_protocol.md` — five-property definition of a G19-compliant cross-check, channel catalogue (TSC-06 + siblings), failure-mode vs merge-regression comparison, extension protocol | landed |
| DOS-A30-MIO A35/A38/A40 (Day 7) | `docs/dossier/A35_directional_coherence.md`, `A38_masked_sky_caveats.md`, `A40_g19_architectural_stance.md` | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md` | landed |

Final test tally over the touched surface (`bass_py/htt/tests/
bass_py/src/ bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/`): **994 passed, 0 failed, 8 skipped** (+116 new tests
vs W6's 878; skip composition unchanged). The `bass_py/tsc/`
standalone test count is **598** (up from 482 post-W6 — W7 FM1 in the
audit documents that the prior "615" estimate in this file was stale).

## §1c-5. What shipped in Week 8

Commits `ab1297b` (W8D3) → `64327b8` (W8D7). Four landings, one
phase-boundary audit (`AUDIT_PHASE_IND_TRACKS_W8_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| MANU-CH11-REDESIGN (Days 1-3) | `project/00_manuscript/ch11_error_hierarchy.tex` 596→1087 L — three new v3 §11.14.2 subsections (`sec:err-mio-semantic`, `sec:err-g19`, `sec:err-epistemic`); `truth certificate` mention count = 9 ≥ 4 gate; banned-vocab scan = 0 hits | landed |
| MANU-CH12-NEW (Days 4-5) | `project/00_manuscript/ch12_mio_observatory_results.tex` (new file, 702 L) — §12.0 Philosophy (150 L), §12.2 Cross-channel directional coherence (170 L, HJ-02a numbers verbatim from A35), §12.6 HTT↔MIO cross-validation (177 L, A34 channel catalogue), §12.7 Scope and limitations (165 L); each ≥ 150 L gate; main.tex inputs it after ch11 | landed |
| HTT-STAB final (Day 6) | `bass_py/htt/tests/fixtures/pipeline_outputs/{FLRW_tilt_results,robustness_sweeps_integrated}.json` + HTT_PIPELINE_OUTDIR env-var wiring in `htt/figures/__init__.py` + `htt/figures/conftest.py` + patches to `fig_evidence_decomposition.py` and `fig_channel_ablation_heatmap.py`; test_figures_smoke.py skip count 8→6 (−2 gate met); 300 DPI already uniform across all 28 figure scripts | landed |
| HTT-NULL smoke green (Day 7) | `bass_py/htt/tests/test_nulls.py` +58 L = new `TestRunnerSmoke` class (5 tests: imports, 5-family instantiation, runner builds stub pipeline, family-result schema, JSON round-trip); test_nulls.py 11→16 passed; full green gate met | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W8_2026-04-19.md` | landed |

Final test tally over the touched surface at W8 boundary:
**1001 passed, 0 failed, 6 skipped** (+7 vs W7's 994; −2 skips
resolved; no regressions). Composition of the remaining 6 skips:
2 × mio.core/reporting (W6 carry), 1 × dynesty (W5 carry), 3 ×
remaining /mnt/user-data fixtures (W5 SKIP-05-LATENT partially
resolved; `fig_rho_sweep`, `fig_departure_summary`, and
`fig_v_pushforward` still blocked — see W8 FM3 for the
extension path).

Note on manuscript file tracking: the `/project` directory is
gitignored at `.gitignore:126`. Prior audits' "landed" claims
for `project/00_manuscript/ch03_framework.tex` et al. touched
the working tree only and were never committed. W8D3 / W8D5
force-added the three manuscript files (ch11, ch12, main.tex)
to unblock the Week-8 gate. Documented as **W8 FM1** — policy
question deferred to the user.

## §1c-6. What shipped in Week 9

Session of 2026-04-19 (compressed: one session covered Week-9
Days 1-7). Six landings + one phase-boundary audit
(`AUDIT_PHASE_IND_TRACKS_W9_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| DOS-A13 (Days 1-3) | 12 new dossier files `A13_02_BI_orth.md` … `A13_13_BVIIh_tilt.md` (BI_orth, BVII0_orth, BII_orth, BVI0_orth, BVIII_orth, BIX_orth, BVIIh_orth + BVIIh_orth_grow inline, BI_tilt, BV_tilt, BIII_tilt, BIX_tilt, BVIIh_tilt + BVIIh_tilt_grow inline). Each file uses the §1–§9 template from `A13_template.md` and references the corresponding `htt.core.evidence_models_R03a` class by name + prior. 14 total numbered A13 files (template + 14 model files) | landed |
| HTT-STAB round 2 (Day 4) | `robustness_sweeps_integrated.json` extended with `sweep_A_rho` key (11 rows, lnB monotone in ρ); new `IS06_3D_posterior.npz` fixture (n=2000 β/ℓ/b arrays); HTT_PIPELINE_OUTDIR pattern applied to `fig_rho_sweep.py`, `fig_departure_summary.py`, `fig_v_pushforward.py`; typo fix `catalog_velocity_likelihood` → `catalog_likelihood` in fig_v_pushforward; `test_figures_smoke.py` skip count 6 → 4 | landed (fig_departure_summary remains dynesty-blocked per W8 FM4 — by design) |
| W7 FM2 close (Day 5) | `FillingFraction.mc_posterior` accepts keyword-only `pre_drawn_eps=(e1, e2, e3)` triple; `ff_htt_mc_cross_check` draws the triple once on the bridge side and hands it to both paths; 4-test `TestW7FM2StreamAlignment` class validates pre-drawn acceptance + shape-mismatch raise + reordering-proof bit-identity + rtol round-trip | landed |
| Full-regression audit (Days 6-7) | Touched surface 1001 → 1007 passed; 6 → 4 skipped; tsc standalone 598 → 602 (+4 FM2); MIO contribution = 37 ≥ 25 gate; full `bass_py/` 3193 tests collected. MIO gap rank: HJ-01 shear extraction + HJ-03 evidence anatomy + HJ-04 departure skeleton — blocked on bass_py K_ℓ atlas / HTT posterior draws (v3 §17.3) — not actionable in this lane until bass_py LB-7+ lands | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W9_2026-04-19.md` | landed |

Final test tally over the touched surface at W9 boundary:
**1007 passed, 0 failed, 4 skipped** (+6 vs W8's 1001; −2 skips
resolved). Composition of the 4 remaining skips: 2 × mio.core/reporting
(W6 carry — blocked on MANU-CH12-NEW figure retirement), 1 × dynesty
(W5 carry — `fig_departure_summary`; `venv/bin/pip install dynesty`
unblocks), 1 × `fig_certification_matrix` / `fig_identified_reporting_split`
/ `fig_direction_posterior` family (different legacy root — W9 carry).

Week 9 final gate — **all four items green**:
- [x] DOS-A13 14 numbered A13 files present (template + 14 model dossiers covering all 16 ALL_MODELS entries, with `*_grow` variants folded into their `_orth` / `_tilt` parents).
- [x] W9D4 skip reduction: 6 → 4 (dynesty blocker noted separately).
- [x] W7 FM2 TSC-06 RNG stream refactor landed + regression locked.
- [x] Full-regression audit log written to `docs/audits/AUDIT_PHASE_IND_TRACKS_W9_2026-04-19.md`.
- [x] MIO contribution ≥ 25 tests (37 — unchanged vs W8; no MIO code change this week).

## §1d. What was designed in the 2026-04-19 planning session

(Preserved here for provenance; unchanged from earlier rotations.
See v3 research plan + PART II + PART III of the governing plan.)

## §2. Active priorities for the next session (Week 10)

**"MIO gap-closure + MANU-CH12 continuations + opportunistic
carry-forwards"** — distilled from `INDEPENDENT_TRACKS_PLAN.md` §21
post-Week 9. Week 9 closed all scheduled landings; no W9 rollovers.
The session should treat the W9 FM1–FM6 ledger in
`AUDIT_PHASE_IND_TRACKS_W9_2026-04-19.md` (all P3, by-design) as
background only — none are action items for Week 10.

Week 10 is the first week where the MIO gap list becomes actionable.
Read `§3 Carry-forward items` and the parent plan v3 §17.3 before
picking up.

### Days 1–2 — DYNESTY-DEP install + dynesty-blocked figure unlock

Deferred since W5; Week 10 is a convenient window before MIO
HJ-01 work. `venv/bin/pip install dynesty` unblocks
`fig_departure_summary.py` (skip count 4 → 3) and enables the
`TestHttMcCrossCheck` family to exercise the nested-sampling path
end-to-end (not just the analytical approximation).

- Commit tag: `W10D1: AUDIT(W5-DYNESTY-DEP): install + smoke`
- Gate: `test_figures_smoke.py` skip count drops to ≤ 3; pip-freeze
  committed alongside; no new test regressions on touched surface.

### Days 3–4 — MIO HJ-01 skeleton (shear extraction)

Governing plan §17.3 + v3 §9.1. HJ-01 is the MIO shear-extraction
primitive: given a bass_py K_ℓ atlas output, produce a shear
estimator with a documented MES cap. Since bass_py K_ℓ atlas is
not yet landed (bass_py session is still on the hierarchy
integrator / LB lane), Week 10 lands the **skeleton only**:

- module `bass_py/mio/extraction/hj01_shear.py` with `ShearExtractor`
  dataclass + `extract_from_kl_atlas(kl: dict) -> ShearExtractorReport`;
- stub consumer that documents the bass_py K_ℓ atlas schema the
  module expects (keyed to the `"truth certificate"` language
  from ch11);
- unit tests using a synthetic K_ℓ dict (no bass_py dependency);
- target 10–15 new tests, bringing MIO contribution from 37 to
  ≥ 47.

- Commit tag: `W10D3: MIO HJ-01 shear extraction skeleton`
- Gate: new `bass_py/mio/extraction/` surface imports cleanly;
  tests pass; no bass_py import required.

### Days 5–6 — MANU-CH12 §12.1 or §12.3 (pick whichever is less
blocked on bass_py outputs)

§12.1 depends on the HJ-01 skeleton above; §12.3 depends on COMMON-F
mock-calibration (landed W4). §12.3 is therefore the cleanest
Week-10 target. Text-only — lands in the same `/project` gitignored
path as ch11 / ch12, with the same force-add contract (W8 FM1).

- Commit tag: `W10D5: MANU-CH12 §12.3 mock calibration`
- Gate: §12.3 ≥ 150 L; cites A14 null-family derivations verbatim;
  incorporates W4 F1 sandwich-coverage caveat; no banned vocab.

### Day 7 — Phase audit + NEXT_SESSION rotation

Standard phase-boundary audit per `feedback_phase_boundary_audit.md`.
Write to `docs/audits/AUDIT_PHASE_IND_TRACKS_W10_2026-04-19.md`
(date may shift).

### Week 10 final gate

- [ ] DYNESTY installed; `fig_departure_summary.py` smoke skip
      retired.
- [ ] MIO HJ-01 skeleton landed; ≥ 10 new tests; MIO contribution ≥ 47.
- [ ] MANU-CH12 §12.3 drafted OR explicit deferral rationale.
- [ ] Phase-boundary audit log written.
- [ ] No touched-surface regressions (≥ 1007 passed, 0 failed).

### Deferred to Week 11+ (not Week-10 targets)

- **MANU-CH12 remaining sections** (§12.1, §12.3, §12.4, §12.5,
  §12.8) — blocked on bass_py K_ℓ atlas, HTT posterior draws,
  BiPoSH coefficients.
- **Full regression ≥ 1,800** — spill target; Week 9 lands the
  intermediate checkpoint.
- **W4 F1 mock coverage sandwich** — opportunistic during
  MANU-CH12 §12.3 write-up.
- **W4 F4 Θ⁴ bridge htt audit tightening** — when htt lands
  `_a2_coefficient_table`.
- **W5 DYNESTY-DEP** — install when convenient;
  `venv/bin/pip install dynesty` unblocks ≥ 2 figure smoke skips.
- **W7 FM3 TSC-05 schema hash freeze** — add digest test on first
  schema extension.
- **W8 FM1** `/project` .gitignore policy — user decision.
- **W8 FM2** palette unification — opportunistic on figure
  regeneration.
- **W8 FM6** `clustering` vs `clustering_dipole` name mismatch —
  cross-lane rename; record only.

## §3. Carry-forward items from W1–W8 audits

Severity legend: **P0** = Day-1 blocker, **P1** = Week-9 target,
**P2** = later week, **P3** = out-of-lane. W7 additions above W8
additions at the bottom.

| Tag | Severity | Description | Where to act |
|---|---|---|---|
| W1-W2 F2 | P2 | Two copies of `PreferredAxis` (htt.PR13AJ and common.contracts). | Alias + remove htt-local copy when htt starts consuming `common.contracts`. |
| W1-W2 F5 | P2 | `htt.core.ssot.C.T0_uK = 2.7255e6` inconsistent with `T0_K = 2.72548`. | Change `T0_uK = C.T0_K * 1e6`; run eps_ell regression sweep. |
| W1-W2 F6 | P3 | `bass.observational.planck_mes_bounds.T_CMB_K = 2.7255` drifts from canonical Fixsen value. | Bass-side; coordinate separately. |
| W3 F1 | P2 | Equal-area iso-latitude ring scheme, not HEALPix RING. | Swap when `healpy` adopted (parent plan §7.5). |
| W4 F1 | P2 | `run_zoa_null_mocks` coverage drifts outside [0.60, 0.76] when `C_pix` non-uniform (sandwich cov needed). | Opportunistic during Week 8 ch12 draft. |
| W4 F2 | **RESOLVED W7** | F_Bayes htt numerical equivalence cross-check. | TSC-06 landed `tsc.integration.htt_bridge.ff_htt_mc_cross_check` with rtol 1e-6 agreement on the S3 scenario. |
| W4 F4 | P2 | Θ⁴ bridge htt audit uses FD at h = 1e-2. | Swap when htt lands a native `_a2_coefficient_table`. |
| W5 SKIP-05-LATENT | **PARTIALLY RESOLVED W8** | 2 of 5 `/mnt/user-data` fixture skips resolved via HTT_PIPELINE_OUTDIR pattern (fig_evidence_decomposition + fig_channel_ablation_heatmap); 3 still blocked (fig_rho_sweep, fig_departure_summary, fig_v_pushforward). | Extend pattern in Week 9 — see W9 §2 Day 4. |
| W5 DYNESTY-DEP | P2 | 1 skip on `dynesty`. | `venv/bin/pip install dynesty`. |
| W5 APPLY-BIAS-AMP | P2 | `_apply_bias_to_direction` scales by `|V_true|` not measurement amplitude. | Opportunistic Week 8+. |
| W6 SKIP-02b-v3-LEGACY | P2 | 2 `test_figures_smoke.py` skips on `mio.core` / `mio.reporting`. | Week 8+ MANU-CH12-NEW rewrite or retire the two figures. |
| W6 FM2 PROBE-SIGMA | P2 | Radio / CF4++ / BiPoSH σ_cone plan-placeholders. | Opportunistic during Week 8 MANU-CH12-NEW §12.2 (literature citations). |
| W6 FM4 MC-VECTORISE | P3 | `_sample_isotropic_unit_vectors` per-mock loop. | Only if HJ-02a moves to 1e6-mock regime. |
| W6 FM5 PROBE-NAME-SCHEMA | P3 | ad-hoc probe_name string-join. | Deferred — CONTRACTS-01 schema-hash coordination. |
| W6 FM6 GIT-SHA-DRIFT | P3 | git_commit resolves at instantiation time. | Expected behaviour; no action. |
| **W7 FM1** | **P2** | **`bass_py/tsc/` test count is 598, not 615/700 as earlier §2 Week-7 gate assumed.** **The +116-test Week-7 delta over-delivers the ~+85 planned.** The ≥ 700 absolute-count gate was a stale figure. | **Use 598 as the Week-8 baseline; the new modules landed all tests planned.** |
| **W7 FM2** | **P2** | TSC-06 re-seeds `numpy.random.default_rng(seed)` and redraws eps1/eps2/eps3 in the same order as `FillingFraction.mc_posterior`; a future htt PR that reorders the draws (or inserts an extra rng.normal call) would silently break stream alignment. | Refactor `FillingFraction.mc_posterior` to accept a pre-drawn triple when the bass/htt lane is quiet. |
| **W7 FM3** | **P3** | TSC-05 JSON schema freeze is literal-based (`SCHEMA_VERSION = "TSC-05/v1"` + literal key-set test), not hash-based like `MioCertificate`. | Add hash digest test on first schema extension. |
| **W7 FM4** (inherited W6 FM2) | **P2** | σ_cone placeholders. | See W6 FM2 row. |
| **W7 FM5** | **P3** | `bass_py/tsc/integration/` is new surface; not explicitly listed in `pyproject.toml` but covered by default glob. | No action; note only. |
| **W8 FM1** | **RESOLVED post-W8** | `/project` is intentionally gitignored; "landed" in the audit log means "working-tree updated", not "committed". The three force-added files (ch11, ch12, main.tex) were untracked via `git rm --cached` after user clarification; files preserved on disk. Durable rule added to memory `feedback_project_local_only.md`. | No action — never stage project/ paths. |
| **W8 FM2** | **P2** | 9 of 28 HTT figure scripts skip `apply_style()` (5 use local `set_style()`, 4 rely on explicit `dpi=300` kwarg). DPI uniform; palette not. | Opportunistic when figures are regenerated. |
| **W8 FM3** | **P2** | `fig_rho_sweep.py`, `fig_departure_summary.py`, `fig_v_pushforward.py` still hard-code `/mnt/user-data/outputs`. Applying W8D6 pattern drops 2-3 more skips. | Week 9 §2 Day 4 extension. |
| **W8 FM4** | **P3** | `fig_departure_summary` skip message now surfaces `dynesty` rather than the underlying file-not-found, due to import-order. Cleanly skipped; no regression. | No action; documentation only. |
| **W8 FM5** | **P3** | `TestRunnerSmoke` covers only the fast-path analytical approximation; production nested-sampling ~40 h CI cost is out of scope. | By design; no action. |
| **W8 FM6** | **P3** | `NULL_REGISTRY` keys `ClusteringDipoleNull` under `'clustering'` while its `.name` attribute is `'clustering_dipole'`. Pre-existing. | Cross-lane rename; record only. |

## §4. Environment and quickstart

```bash
# Repo root
cd /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot

# Sanity: touched-surface test run.  As of 2026-04-19 post-W8:
# 1001 passed, 0 failed, 6 skipped (+7 vs W7; 2 skips resolved).
venv/bin/pytest bass_py/htt/tests/ bass_py/src/ \
                bass_py/tsc/admissibility/ \
                bass_py/tsc/diagnostics/ bass_py/tsc/charts/ \
                bass_py/tsc/integration/ \
                bass_py/workspace/ bass_py/mio/

# tsc standalone (18 s; 598 passed post-W7; unchanged W8).
venv/bin/pytest bass_py/tsc/

# Full monorepo suite (slower).
venv/bin/pytest bass_py/
```

Path notes:

* `bass_py/src/common/` is importable via `bass_py/conftest.py` (which
  prepends `src/` to sys.path) and via `bass_py/pyproject.toml` (which
  adds `src/` to the setuptools package-find).
* `htt` is its own editable install (`bass_py/htt/setup.py`).  If the
  next session fails to import `htt.core.ssot`, verify
  `venv/bin/pip install -e bass_py/htt/` has run in this venv.
* `dynesty` is **not** installed.  `common.bulkflow_likelihood.run_dynesty`
  lazy-imports it and raises a clear `RuntimeError` otherwise; tests
  inject a stub via `dynesty_module=SimpleNamespace(NestedSampler=...)`.

## §5. Non-scope for this lane

To avoid rediscovery, the following are explicitly the bass_py
session's responsibility and must not be touched here:

* `bass_py/bass/*` — entire `bass/` subtree. bass_py session has now
  shipped LB-0 through LB-6 + AUDIT(LB-cleanup) cleanup. Uncommitted
  modifications to `bass_py/bass/hierarchy/__init__.py` and
  `bass_py/pyproject.toml` in the working tree are bass-side in-progress
  work — do not stage or commit them from this lane.
* W10-02 CAMB V-gate, W11-01/02/03, W12-01/02, W13-01/02, W14-01,
  W15-01/02/03 (post-LB-6 roadmap) — parent plan v3 §7.
* **MIO HJ-01 / HJ-03 / HJ-04 / HJ-05-full** require bass_py outputs
  (W10-02 K_ℓ atlas, W11-02 BiPoSH, HTT Phase F posteriors). Governing
  plan §17.3 catalogues the dependency wait list. **This lane's MIO
  work remains limited to HJ-02a directional coherence + boot
  infrastructure + HJ-05a-lite masked_sky_caveats** (all landed in
  Week 6) — the modules that do not depend on bass_py deliverables.
* `plots/physics_gallery/` — gallery refresh is bass_py's per-phase rule.

### §5a. This lane's new territory (updated post-W8)

Directories that **this** lane now owns (created or will be created
per the v1.2 plan — bass_py session must not touch):

* `bass_py/src/common/*` — ZoA / bulk-flow common modules (Week 1–4 landed).
* `bass_py/workspace/` + `bass_py/workspace/contracts/*` — interface
  contracts (Week 5 Days 1–2 landed).
* `bass_py/mio/*` — MIO package. Week 6 shipped the skeleton +
  MIO-HJ-02a directional coherence + MIO-HJ-06a certificate generator +
  MIO-BRIDGES-01 PR13AM re-export + MIO-HJ-05a-lite masked-sky caveats.
* **`bass_py/tsc/integration/*`** — NEW Week-7 subpackage; currently
  holds TSC-06 `htt_bridge` + tests. Distinct from `bass_py/tsc/{admissibility, charts, diagnostics}/`.
* `docs/dossier/A13_*`, `A14_*`, `A32_*`, `A33_*`, **`A34_*`**,
  **`A35_*`**, **`A38_*`**, `A39_*`, **`A40_*`** — manuscript dossier
  (Week 7 added A34 + A35 + A38 + A40; `A13_02_*` through `A13_14_*`
  land in Week 9).
* `project/00_manuscript/ch03_framework.tex` (MANU-CH03 subsections;
  Week 1–4 landed; ~800 L gap vs v3 §11.3 target remains).
* `project/00_manuscript/ch11_error_hierarchy.tex` — MANU-CH11-REDESIGN
  three new §11.14.2 subsections landed Week 8; 596→1087 L.
* `project/00_manuscript/ch12_mio_observatory_results.tex` (new file,
  702 L) — MANU-CH12-NEW §12.0 / §12.2 / §12.6 / §12.7 landed Week 8;
  §12.1 / §12.3 / §12.4 / §12.5 / §12.8 deferred to Phase J.
* `project/00_manuscript/main.tex` — inputs ch12 after ch11 (first
  tracked landing W8D5; `/project` gitignored, force-added).
* `bass_py/htt/tests/fixtures/pipeline_outputs/` — NEW Week-8 fixture
  directory (FLRW_tilt_results.json + robustness_sweeps_integrated.json
  synthetic stubs with HTT_PIPELINE_OUTDIR wiring in htt/figures/).

If either lane is tempted to touch the other's area, stop and ask the
user first.
