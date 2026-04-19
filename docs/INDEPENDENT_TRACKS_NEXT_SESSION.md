# Independent Tracks — next-session resumption prompt

**As of**: 2026-04-19, post-`IND_TRACKS_W20` phase.
**Last audited**: 2026-04-19
(`docs/audits/AUDIT_PHASE_IND_TRACKS_W20_2026-04-19.md`;
prior phases `AUDIT_PHASE_IND_TRACKS_W19_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W18_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W17_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W15_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W13_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W11_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W10_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W9_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W8_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W6_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W5_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W4_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W3_2026-04-19.md`).
**Governing plan**: `INDEPENDENT_TRACKS_PLAN.md` **v1.3** (W10 F4
closure landed 2026-04-19: §21 now formally covers Week 10 + Week 11
with post-W8-FM1 `/project` rule explicitly spelled out — no more
stale "force-add contract" wording anywhere in the tree;
Week 1–11 routine shipped; Week 12+ continuation routine referenced
below).
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
* **pre-commit `git status --short` gate** — before every `git commit`
  in this lane, run `git status --short` and visually verify the
  staged set matches the commit body. Rationale: W12D3 `99465e5`
  pulled unrelated bass-lane + gallery-lane files into an HJ-02b
  commit; the one-line gate would have caught it (W12 F1 / W13 R1).
* **scoped `git commit -- <paths>` rule** — every `git commit`
  invocation in this lane MUST pass the explicit pathspec list as
  trailing `-- <path1> <path2> ...` arguments. The pathspec form
  makes git commit only those paths from the index; any files
  staged by a concurrent lane in the brief gap between our
  `git status` check and our `git commit` are excluded by
  construction. Rationale: W14D3 `4eb044b` recurred W12 F1 even
  with the W13D1 status-gate in place because the gate cannot
  detect a concurrent lane's commit that lands in the gap. The
  pathspec form closes that race window (W14 F1 / W15D1).
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

## §1c-7. What shipped in Week 10

Session of 2026-04-19 (compressed: one session covered Week-10
Days 1-7). Two committed landings + one working-tree-only
manuscript landing + one phase-boundary audit
(`AUDIT_PHASE_IND_TRACKS_W10_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W5-DYNESTY-DEP close (Days 1-2) | `docs/audits/pip_freeze_2026-04-19_W10D1.txt`; verified `dynesty==3.0.0` already in venv (no install actually needed); `fig_departure_summary.py` smoke went from SKIPPED → PASSED; new composition-swap skip on `test_bulkflow_likelihood.py::test_run_dynesty_raises_clear_runtime_error` (the contract guard self-skips when dynesty IS installed) — net touched-surface skip count holds at 4, within-`test_figures_smoke.py` count drops 4 → 3 | landed (`5ad2e55`) |
| MIO HJ-01 skeleton (Days 3-4) | `bass_py/mio/extraction/hj01_shear.py` (~430 L) + `bass_py/mio/extraction/__init__.py` re-exports + `bass_py/mio/tests/test_hj01_shear.py` (19 tests). Public surface: `ShearExtractor` / `ShearExtractorConfig` / `ShearExtractorReport`; `extract_from_kl_atlas` (dict path) + `extract_from_atlas_entry` (workspace.contracts.AtlasEntry adapter); `validate_kl_atlas_schema` + `KL_ATLAS_REQUIRED_KEYS`; `to_mio_certificate` (always carries `DIAGNOSTIC_ONLY_CAVEAT` until bass_py W10-02 V-gate signs the K_ℓ atlas, parent plan §17.3 risk row); `emit_shear_extraction_artefact` with REG-02 `mio_` filename gate. χ²-tail SF via NR §6.2 incomplete-gamma — no scipy import dependency. MIO contribution 37 → 56 (gate ≥47 met) | landed (`695baf9`) |
| MANU-CH12 §12.3 (Days 5-6) | `project/00_manuscript/ch12_mio_observatory_results.tex` 702 → 903 L (+201 L delta in §12.3 alone, gate ≥150 met). Six new subsections covering tension-metric overview, COMMON-F mock-calibration engine, A14 N1–N5 null-family stream (cited verbatim by filename), W4 F1 sandwich-coverage caveat reproduced verbatim in a `quote` env, x_C direct-estimate forward pointer, diagnostic-only status until V-gate. Banned-vocab scan = 0 hits. **NOT COMMITTED** — `/project` is gitignored per memory `feedback_project_local_only.md` (W8 FM1 RESOLVED). | landed (working tree only) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W10_2026-04-19.md` | landed |

Final test tally over the touched surface at W10 boundary:
**1026 passed, 0 failed, 4 skipped** (+19 vs W9's 1007; net 0 skip
change, composition swap on `test_bulkflow_likelihood.py:303` — see
W10 audit §5). Composition of the 4 remaining skips: 2 ×
mio.core/reporting (W6 carry — blocked on MANU-CH12-NEW figure
retirement), 1 × `test_figures_smoke.py::fig_certification_matrix`
family (`fig_direction_posterior` + `fig_identified_reporting_split`
under one parametrise — different legacy root, W9 carry), 1 × the
new dynesty-installed compositional swap (W10D1, by-design).

Week 10 final gate — **all five items green**:
- [x] DYNESTY install verified; `fig_departure_summary.py` smoke skip retired (figures_smoke skip 4 → 3).
- [x] MIO HJ-01 skeleton landed; 19 new tests; MIO contribution 37 → 56 (gate ≥ 47 met with 9 to spare).
- [x] MANU-CH12 §12.3 drafted at 201 L (gate ≥ 150 met); A14 N1–N5 cited verbatim; W4 F1 reproduced verbatim; banned-vocab scan = 0 hits.
- [x] Phase-boundary audit log written.
- [x] No touched-surface regressions (1026 passed; +19 over W9; 0 failed).

## §1c-9. What shipped in Week 12

Session of 2026-04-19 (compressed: one session covered Week-12
Days 1-7). Four committed landings + one phase-boundary audit
(`AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W12D1 W11 F4 close — A37 grammar acceptance tests | `bass_py/mio/tests/test_probe_name_grammar.py` (new, 8 tests) + producer tightening across `mio/coherence/directional.py` (alphabetical bundle), `mio/coherence/redshift_binned.py` (alphabetical bundle), `mio/extraction/hj01_shear.py` (new `_bianchi_type_to_model_id` normaliser + MODEL_ID-only `probe_name`; legacy `atlas_name:bianchi_type` form retired). A37 dossier §A37.1 examples + §A37.6 landed note updated. MIO contribution 71 → 79. | landed (`015246d`) |
| W12D2 AUDIT(W5-APPLY-BIAS-AMP) — HJ-05a-lite hardening | `bass_py/mio/diagnostics/masked_sky_caveats.py` + `bass_py/mio/tests/test_masked_sky_caveats.py` (4 new tests). Adds `BIAS_AMP_CAVEAT` constant + `apply_bias_amp_caveat()` helper + `build_report(..., mock_bias_applied=False)` kwarg. Upstream `htt/PR13AH._apply_bias_to_direction` intentionally untouched per W5 audit directive (§APPLY-BIAS-AMP: "never patch the helper before ChannelSummary grows a velocity-amplitude field"). MIO contribution 79 → 83. | landed (`cd220a6`) |
| W12D3 W11 F1 close — HJ-02b exact-enumeration drift_pvalue | `bass_py/mio/coherence/redshift_binned.py` gains `exact: bool = False` kwarg + `EXACT_ENUMERATION_MAX_PERMUTATIONS = 10_000` ceiling; 6 new tests (15 → 21). Refuses N ≥ 8 (40 320 perms > ceiling) with explicit `ValueError`. Exact path is deterministic (ignores `rng`) and returns `count / N!` without Lidstone smoothing. MIO contribution 83 → 89. Cross-lane contamination (**W12 FM1 below**) — commit body describes only HJ-02b changes but the commit also pulled `bass_py/bass/transport/*` + gallery-lane files from the index; cannot be retroactively split per the additive-commits rule. | landed (`99465e5`, mixed) |
| W12D5 DOS-A41 — report_type extension protocol | `docs/dossier/A41_mio_report_type_extension_protocol.md` (new, ~200 L). Seven-step mechanical checklist for adding a new `MioCertificate.report_type` value (HJ-03 / HJ-04 / beyond) without rotating the v1 schema hash. Covers A32 / A34 / A37 / A39 / A40 cross-references per A35/A36/A37 dossier convention; A41.5 explicitly documents the W7 FM3 literal-freeze interaction; A41.6 walks HJ-03 `"evidence_anatomy"` through the checklist as a worked example. | landed (`27d0fed`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W12_2026-04-19.md` | landed |

Final test tally over the touched surface at W12 boundary:
**1059 passed, 0 failed, 4 skipped** (+18 vs W11's 1041; 0 skip
change; 0 regressions). Skip composition unchanged from W11
end-of-phase (2 × mio.core/reporting W6 carry, 1 ×
`fig_certification_matrix` family W9 carry, 1 × dynesty
composition-swap W10D1 carry).

Week 12 final gate — **all five items green**:
- [x] W11 F4 (A37 grammar tests) closed (W12D1); W11 F1 (exact-
      enumeration) closed (W12D3).
- [x] W5 APPLY-BIAS-AMP closed via caveat-surfacing hardening
      (W12D2); upstream helper intentionally untouched.
- [x] At least one new A4x dossier file landed (W12D5 — A41).
- [x] Phase-boundary audit log written.
- [x] No touched-surface regressions (+18 over W11; 0 failed;
      4 skipped unchanged).

## §1c-8. What shipped in Week 11

Session of 2026-04-19 (compressed: one session covered Week-11
Days 1-7). Three committed landings + one phase-boundary audit
(`AUDIT_PHASE_IND_TRACKS_W11_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W11D1 W10-F4 + W10-F5 closures | `INDEPENDENT_TRACKS_PLAN.md` committed for the first time with a **v1.3** §21 Week 10 + Week 11 entry that spells out the post-W8-FM1 `/project` rule (never stage project/ paths); `bass_py/mio/tests/test_hj01_shear.py::test_extract_drops_zero_kernel_multipoles` rewritten to compute `expected_window = cfg.ell_max - cfg.ell_min + 1` from `ShearExtractorConfig()` defaults instead of hardcoding `27` | landed (`8aefbb8`) |
| W11D3 MIO HJ-02b | `bass_py/mio/coherence/redshift_binned.py` (~350 L) + `bass_py/mio/coherence/__init__.py` docstring update + `bass_py/mio/tests/test_redshift_binned_coherence.py` (15 tests). Public surface: `RedshiftBinnedProbe` / `STANDARD_Z_PROBES` (5-probe SSOT with literature `z_eff` tags) / `DEFAULT_Z_BINS` (3-bin low / mid-AGN / CMB) / `assign_probes_to_bins` / `per_bin_resultants` / `total_drift_deg` / `drift_pvalue` (permutation null test) / `to_mio_certificate` (`reduction_status='diagnostic-only'`) / `emit_redshift_coherence_artefact` (REG-02 `mio_` prefix gate). MIO contribution 56 → 71 (gate ≥ 47 met with 24 to spare) | landed (`06de6d3`) |
| W11D5 DOS-A36 + A37 | `docs/dossier/A36_mio_channel_weighting.md` (~130 L; three weighting categories + per-statistic specs for HJ-01 / HJ-02a / HJ-02b / HJ-04); `docs/dossier/A37_mio_probe_name_schema.md` (~140 L; frozen BNF grammar v1 + PROBE_ID registry + migration path to structured `probe_names: list[str]`) | landed (`5a7bf2a`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W11_2026-04-19.md` | landed |

Final test tally over the touched surface at W11 boundary:
**1041 passed, 0 failed, 4 skipped** (+15 vs W10's 1026; 0 skip
change; 0 regressions). Skip composition unchanged from W10
end-of-phase (2 × mio.core/reporting W6 carry, 1 ×
`fig_certification_matrix` family W9 carry, 1 × dynesty
composition-swap W10D1 carry).

Week 11 final gate — **all five items green**:
- [x] W10 F4 + W10 F5 closed (W11D1).
- [x] HJ-02b landed; MIO contribution 56 → 71; 15 new tests.
- [x] Two new A3x dossier files landed (A36 + A37).
- [x] Phase-boundary audit log written.
- [x] No touched-surface regressions (1041 passed / 0 failed / 4 skipped).

## §1c-10. What shipped in Week 13

Session of 2026-04-19 (compressed: one session covered Week-13
Days 1-7). Four committed landings + one phase-boundary audit
(`AUDIT_PHASE_IND_TRACKS_W13_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W13D1 process discipline (W12 F1/R1) | `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 first-order rules +5 L (pre-commit `git status --short` gate); paired durable entry in memory `feedback_git_workflow.md`. | landed (`41b7200`) |
| W13D2 MIO PROBE_ID registry SSOT (W12 F3/R2) | `bass_py/mio/interface/probe_name_registry.py` (~55 L) + `bass_py/mio/tests/test_probe_name_registry.py` (6 tests). Public surface: `REGISTERED_PROBE_IDS: Tuple[str, ...]` (alphabetical, immutable) + `is_registered_probe_id(name) -> bool`. Parser test reads A37.3 markdown at import time; set-equality against code tuple guards the three-file invariant (code ↔ dossier ↔ `STANDARD_PROBES`/`STANDARD_Z_PROBES`). MIO contribution 89 → 95. | landed (`b7607ef`) |
| W13D3 DOS-A36a σ_cone literature (W6 FM2 / W11 F3 docs close) | `docs/dossier/A36a_sigma_cone_literature.md` (~234 L). DOI/arXiv-anchors σ_cone per PROBE_ID (Planck 2018 LVI / Secrest+2021 / Rubart-Schwarz / Darling / Tully+2023 / Planck 2015 XVI) with Δ summary and three-condition retirement criterion (§A36a.5). Code-side σ values intentionally unchanged per "caller's judgement" plan directive. | landed (`ed2c9b1`) |
| W13D5 DOS-A42 HJ-03 evidence_anatomy stub | `docs/dossier/A42_evidence_anatomy.md` (~198 L). Deferred design stub for HJ-03 — purpose (anatomy / sign-coherence / consistency), planned HTT input bundle, unweighted per-channel computation, decomposition-residual floor 1e-3, MioCertificate contract table, G19 posture, 5-test acceptance plan. §A42.6 documents the A34/A36/A40 "HJ-04 evidence anatomy" ↔ A32/A41 "HJ-03 evidence_anatomy" naming drift and adopts the schema-authoritative binding. | landed (`9dd64fa`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W13_2026-04-19.md` (includes mandatory §6 W12 FM1 recurrence check — returns **PASSED**; every W13 commit is scoped exactly to its described content) | landed |

Final test tally over the touched surface at W13 boundary:
**1065 passed, 0 failed, 4 skipped** (+6 vs W12's 1059; 0 skip
change; 0 regressions). Skip composition unchanged from W10
end-of-phase (2 × mio.core/reporting W6 carry, 1 ×
`fig_certification_matrix` family W9 carry, 1 × dynesty
composition-swap W10D1 carry).

Week 13 final gate — **all five items green**:
- [x] W12 R1 process note added (`41b7200` + memory
      `feedback_git_workflow.md` durable entry).
- [x] W12 R2 PROBE_ID registry landed (`b7607ef`; 6 new tests;
      MIO 89 → 95).
- [x] Two new A4x dossier files landed (A36a + A42 — exceeds
      single-file gate).
- [x] Phase-boundary audit log written; W12 FM1 recurrence check
      included in §6 and returns **PASSED**.
- [x] No touched-surface regressions (1065 passed; +6 over W12;
      0 failed; 4 skipped unchanged).

## §1c-11. What shipped in Week 14

Session of 2026-04-19 (compressed: one session covered Week-14
Days 1-7). Four committed in-lane landings + one cross-lane-
contaminated landing + one phase-boundary audit
(`AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W14D1 cross-producer σ_cone parity (W13 F2) | `bass_py/mio/tests/test_probe_name_registry.py` +37 L = new `test_standard_probes_have_consistent_sigma_cone_across_producers` — zips `STANDARD_PROBES` ↔ `STANDARD_Z_PROBES` by `.name` and asserts `sigma_cone_deg` / `l_deg` / `b_deg` exact equality per probe. MIO contribution 95 → 96. | landed (`593a7b6`) |
| W14D2 A36 → A36a link (W13 R3) | `docs/dossier/A36_mio_channel_weighting.md` §A36.4 +10 L — Provenance anchor paragraph linking to A36a.2 / A36a.3 / A36a.5 and cross-referencing the W14D1 parity test. | landed (`491ecfd`) |
| W14D3 HJ-04 → HJ-03 naming sweep (W13 F1) | `docs/dossier/A34_g19_cross_check_protocol.md`, `A36_mio_channel_weighting.md`, `A40_g19_architectural_stance.md`, `A42_evidence_anatomy.md` — 9 occurrences of "HJ-04 evidence anatomy" / "HJ-04 Δln B" renamed to HJ-03; A42.6 closure note added; HJ-04 ↔ `flrw_tension` bindings (A41, A42.6) intentionally preserved. Gate: `grep -rn "HJ-04 evidence" docs/dossier/` = 0. | landed **inside** `4eb044b` — cross-lane contamination (**W14 F1 below**); commit label reads `FB-1.4: anisotropic_3_curvature 11-type consolidation` but file contents are exclusively the four W14D3 dossier renames |
| W14D5 CatWISE σ placeholder retirement (A36a.5 #1) | NEW `bass_py/mio/interface/sigma_cone_provenance.py` (75 L) — `PROMOTED_SIGMA_CONE_PROBES: frozenset({"CatWISE"})` + `PLACEHOLDER_CAVEAT_SUFFIX` + `placeholder_caveats_for` / `is_promoted` helpers; producers `mio.coherence.directional.to_mio_certificate` + `mio.coherence.redshift_binned.to_mio_certificate` append per-probe tags (deduplicated); NEW `bass_py/mio/tests/test_sigma_cone_provenance.py` (8 tests). A36.4 prose updated; A36a.2 CatWISE row promotion; A36a.5 Promotion log + A36a.6 bullets 1 + 2 ticked. MIO 96 → 104. | landed (`2951c84`) |
| W14D6 BiPoSH σ placeholder retirement (A36a.5 #2) | `PROMOTED_SIGMA_CONE_PROBES` extended to `frozenset({"BiPoSH", "CatWISE"})`; +1 test (`test_promoted_set_contains_biposh_post_w14d6`) pins BiPoSH in + CMB/Radio/CF4pp out; A36a.2 BiPoSH row promotion + A36a.5 Promotion log. MIO 104 → 105. Remaining flagged set: `{CMB, Radio, CF4pp}`. | landed (`9e85d83`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W14_2026-04-19.md` — §6 includes W12 F1 recurrence check (**FAILED**, documented as F1 P2) + W14 in-lane pre-commit-gate verification (**PASSED** on the four clean in-lane commits). | landed |

Final test tally over the touched surface at W14 boundary:
**1075 passed, 0 failed, 4 skipped** (+10 vs W13's 1065; 0 skip
change; 0 regressions). Skip composition unchanged from W10 end-of-
phase.

Week 14 final gate — **all five items green**:

- [x] W13 F2 cross-producer σ parity test landed (W14D1).
- [x] W13 F1 naming sweep landed (W14D3, via `4eb044b`).
- [x] At least one A36a.5 placeholder retirement — **two** landed
      (W14D5 CatWISE + W14D6 BiPoSH), exceeds gate.
- [x] Phase-boundary audit log written with §6 W12 F1 recurrence
      check (documented as FAILED with mitigation R1 in §8).
- [x] No touched-surface regressions.

## §1c-12. What shipped in Week 15

Session of 2026-04-19 (compressed: one session covered Week-15
Days 1-7). Three committed in-lane landings + one phase-boundary
audit (`AUDIT_PHASE_IND_TRACKS_W15_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W15D1 scoped-commit rule (W14 F1) | `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 +10 L — new fourth first-order rule prescribing `git commit -- <paths>` per commit; paired durable entry in memory `feedback_git_workflow.md`. Closes the race window that the W13D1 `git status --short` gate could not catch (concurrent lane's commit between our status check and our commit). | landed (`d48b920`) |
| W15D3 DOS-A43 schema-hash digest design (W7 FM3 mech-resolved) | `docs/dossier/A43_schema_hash_digest.md` (~306 L). Specifies the hash-digest mechanism (field name + normalised type + default kind + field order) that catches structural drift without rotating on value-level edits (`report_type` / `channel` value additions, payload-dict key additions, default-value retunes). Test spec in §A43.6 ready for paste-on-extension; trigger per §A43.3 is first actual schema extension (HJ-03 / HJ-04 / TSC-05 v2). Cross-refs resolve into A32.5 / A41.2 / A41.5 / A42.5. No code change. | landed (`8fae1ba`) |
| W15D5 MIO tighten placeholder-tag count (W14 R2) | `bass_py/mio/tests/test_sigma_cone_provenance.py` +25 L = new `test_hj02a_certificate_caveat_count_equals_flagged_set_with_no_caller_caveats`. Asserts set-equality + length-equality on the no-caller-caveats path, closing the over-emission gap the W14D5 `issubset` test missed. MIO 105 → 106. | landed (`293652a`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W15_2026-04-19.md` — §6 W12 F1 / W14 F1 recurrence check returns **PASSED** (three W15 commits scoped exactly to their own paths; symmetric verification on the cross-lane `3dcc505` commit shows only bass-lane files). | landed |

Final test tally over the touched surface at W15 boundary:
**1076 passed, 0 failed, 4 skipped** (+1 vs W14's 1075; 0 skip
change; 0 regressions). Skip composition unchanged from W10
end-of-phase.

Week 15 final gate — **all five items green**:

- [x] W14 F1 scoped-commit rule landed (durable memory + §0 note;
      W15D1 `d48b920`).
- [x] A43 schema-hash digest dossier landed (W15D3 `8fae1ba`).
- [x] One of W14 R2 / R3 landed — **R2 picked** (W15D5 `293652a`;
      +1 test; MIO 105 → 106).
- [x] Phase-boundary audit log written; §6 W12 F1 / W14 F1
      recurrence check returns **PASSED**.
- [x] No touched-surface regressions (1076 passed; +1 over W14;
      0 failed; 4 skipped unchanged).

## §1c-13. What shipped in Week 16

Session of 2026-04-19 (compressed: one session covered Week-16
Days 1-7). Three committed in-lane landings + one phase-boundary
audit (`AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W16D1 MIO caller-caveats union-equality (W15 F1) | `bass_py/mio/tests/test_sigma_cone_provenance.py` +18 L / -1 L — `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags` gains a final `set(cert.domain_caveats) == set(caller_caveats) \| expected_tags` assertion. Closes the over-emission-with-caller-caveats gap left by the W15D5 no-caller-caveats guard. Assertion strengthening on existing test (no count delta). | landed (`cd952ee`) |
| W16D3 DOS-A36a YAML sidecar + parity test (W14 R3 / W13 F4 / W15 F2) | NEW `docs/dossier/A36a_sigma_cone_literature.yaml` (60 L) + `bass_py/mio/tests/test_sigma_cone_provenance.py` +57 L (`test_standard_probes_sigma_code_matches_a36a_yaml`) + `docs/dossier/A36a_sigma_cone_literature.md` +11 L (Machine-readable mirror pointer in §A36a.3). Scalar-reduction (midpoint) convention for the three ranged-σ probes with optional `sigma_lit_range_deg: [min, max]` field preserving full dossier claim. Closes W13 F4 / W14 F3 / W15 F2. MIO 106 → 107. | landed (`5765e0b`) |
| W16D5 DOS-A44 MIO-HTT handshake sequence | NEW `docs/dossier/A44_mio_htt_handshake_sequence.md` (~281 L). Temporal companion to A34's structural cross-check protocol. Specifies the t1→t5 sequence (MioCertificate instantiation with `git_commit` frozen per W6 FM6 / W11 F5 → artefact emission → HTT Phase F independent posterior → cross-check harness builds `is_cross_check=True` frozen report → `assert_*_consistent` loud-fail). §A44.4.1 in-memory / §A44.4.2 artefact-replay hand-off modes; §A44.6 `config_hash` + `input_data_hashes` cache-replay guard. Cross-refs A32 / A34 / A40 / A41 / A42 / A43. No code change. | landed (`484ffed`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md` — §6 W12 F1 / W14 F1 recurrence check returns **PASSED** (three W16 commits each scoped to own lane's paths; zero cross-lane commits in the W16 window). | landed |

Final test tally over the touched surface at W16 boundary:
**1077 passed, 0 failed, 4 skipped** (+1 vs W15's 1076; 0 skip
change; 0 regressions). Skip composition unchanged from W10
end-of-phase.

Week 16 final gate — **all five items green**:

- [x] W15 F1 caller-caveats union-equality landed (W16D1
      `cd952ee`).
- [x] A36a YAML sidecar + parity test landed (W16D3 `5765e0b`;
      closes W13 F4 / W14 F3 / W15 F2; MIO 106 → 107).
- [x] One of A44 dossier / MANU-CH03 extension landed —
      **A44 picked** (W16D5 `484ffed`; new dossier, ~281 L).
- [x] Phase-boundary audit log written; §6 W12 F1 / W14 F1
      recurrence check returns **PASSED**.
- [x] No touched-surface regressions (1077 passed; +1 over W15;
      0 failed; 4 skipped unchanged).

## §1c-14. What shipped in Week 17

Session of 2026-04-19 (compressed: one session covered Week-17
Days 1-7). Three committed in-lane landings + one phase-boundary
audit (`AUDIT_PHASE_IND_TRACKS_W17_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W17D1 MIO git_commit capture-time runtime gate (W16 F2) | `bass_py/workspace/contracts/tests/test_mio_certificate.py` +37 L — new `test_git_commit_is_capture_time_not_lazy` locks A44.3's at-instantiation capture invariant (W6 FM6 / W11 F5). Constructs `MioCertificate(git_commit="a1b2c3d4…")`, monkeypatches `subprocess.run` to raise and (defensively) `mio.interface.mio_certificate._resolve_git_commit` to return a sentinel, reads `cert.git_commit` via attribute access and `dataclasses.asdict(cert)`, asserts both return the construction-time value, and asserts `type(cert).__dict__.get("git_commit", None) is None` (bans a class-level descriptor / property that would silently re-resolve HEAD on read). Touched-surface 1077 → 1078; MIO contribution holds at 107 (workspace-layer test). | landed (`151fbc4`) |
| W17D3 DOS-A36a YAML range-bracketing hedge (W16 F3) | `bass_py/mio/tests/test_sigma_cone_provenance.py` +47 L — new `test_a36a_yaml_range_brackets_midpoint` iterates every YAML row carrying the optional `sigma_lit_range_deg: [min, max]` field and asserts (a) two-element list shape, (b) `min <= max`, (c) `min <= sigma_lit_deg <= max`, plus an "at least one row carries the range field" convention guard. All three current range-carrying rows (Radio 10–14 / CF4pp 10–12 / BiPoSH 15–25) satisfy the bracket at midpoint (12 / 11 / 20) by construction; the test hedges a future ranged-σ addition to a currently-scalar probe or a range/midpoint typo. Touched-surface 1078 → 1079; MIO 107 → 108 (`test_sigma_cone_provenance.py` 11 → 12). | landed (`3137cc0`) |
| W17D5 DOS-A45 MIO cache-replay drift protocol | NEW `docs/dossier/A45_mio_cache_replay_drift.md` (~269 L). Content-hash companion to A44's execution-order companion to A34. §A45.2 specifies the `verify_cache_replay(mio_cert, htt_input_bundle, allow_unsigned_config=False)` pseudocode (recompute `config_hash` via `_hash_config`; set-equality-check `input_data_hashes`; raise `CacheReplayDriftError` on either drift). §A45.3 declares landing deferred to the first harness crossing a persistence boundary (HJ-03 per A42.5 + A44.7). §A45.5 names the `allow_unsigned_config=True` escape-hatch semantics + clean upgrade path once A43's schema-hash digest lands (W15 F3 / A43.3 trigger). §A45.6 ships a paste-ready five-test acceptance block for the HJ-03 PR; test (5) mirrors W17D1 at the MIO harness surface. Cross-refs A32 / A34 / A41 / A42 / A43 / A44. No code change. | landed (`a4dc670`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W17_2026-04-19.md` — §6 W12 F1 / W14 F1 recurrence check returns **PASSED** (three W17 commits each scoped exactly to a single lane-owned path; zero cross-lane commits on `main` in the W17 window; W17D3 uniquely exercised the scoped-pathspec rule against working-tree bass-lane drift — four unstaged `bass_py/bass/hierarchy/*` files were excluded by construction). | landed |

Final test tally over the touched surface at W17 boundary:
**1079 passed, 0 failed, 4 skipped** (+2 vs W16's 1077; 0 skip
change; 0 regressions). Skip composition unchanged from W10
end-of-phase.

Week 17 final gate — **all five items green**:

- [x] W16 F2 `MioCertificate.git_commit` runtime-gate microtest
      landed (W17D1 `151fbc4`; +1 test; workspace-layer).
- [x] W16 F3 A36a YAML range-bracketing hedge landed (W17D3
      `3137cc0`; +1 test; MIO 107 → 108).
- [x] One of A45 dossier / MANU-CH03 extension landed —
      **A45 picked** (W17D5 `a4dc670`; new dossier, ~269 L).
- [x] Phase-boundary audit log written; §6 W12 F1 / W14 F1
      recurrence check returns **PASSED** (W17D3 = second
      adversarial stress-test of the W15D1 scoped-pathspec rule,
      working-tree-drift variant).
- [x] No touched-surface regressions (1079 passed; +2 over W16;
      0 failed; 4 skipped unchanged).

## §1c-15. What shipped in Week 18

Session of 2026-04-19 (compressed: one session covered Week-18
Days 1-7). Three committed in-lane landings + one phase-boundary
audit (`AUDIT_PHASE_IND_TRACKS_W18_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W18D1 A45.2 `_hash_config` docs-↔-code anchor (W17 F1) | `bass_py/mio/tests/test_mio_certificate_generator.py` +50 L — new `test_hash_config_matches_a45_2_pseudocode_shape` imports `_hash_config` by exact name used in A45.2's pseudocode, asserts `__name__ == "_hash_config"` (rename-detector on top of the implicit `ImportError`), calls it with the six-field tuple from `_base_payload()` (`report_type`, `probe_name`, `channel`, `departure_variables`, `adequacy_indicators`, `consistency_metrics`), asserts the return is a 16-char lowercase-hex string (length + case + `string.hexdigits.lower()` subset), and cross-checks `cert.config_hash == _hash_config(...)` build-↔-replay parity on the same payload. Touched surface 1079 → 1080; MIO contribution 108 → 109 (`test_mio_certificate_generator.py` 10 → 11). | landed (`0d2fc9f`) |
| W18D3 A45.6 ↔ A41.6 harness-signature cross-link (W17 F2) | `docs/dossier/A45_mio_cache_replay_drift.md` +14 L — new up-front "Harness-signature note (W17 F2 / W18D3)" paragraph in §A45.6 binding the paste-ready five-test block to the two-argument `verify_cache_replay(mio_cert, htt_input_bundle, *, allow_unsigned_config=False)` signature from §A45.2 and deferring the freeze decision to A41.6 step 6.5. `docs/dossier/A41_mio_report_type_extension_protocol.md` +11 L — new reciprocal step 6.5 "Freeze the replay-harness signature" inserted between step 6 and step 7 of the §A41.6 HJ-03 worked example with a forward pointer to §A45.6 and the "same PR as paste-replace" rule. Bidirectional cross-reference resolution verified (grep: `A41.6 / §A41.6` = 4 hits in A45.md; `A45.6 / §A45.6` = 3 hits in A41.md). | landed (`23fefbb`) |
| W18D5 DOS-A46 three-lane race stress-test protocol (W17 F3) | NEW `docs/dossier/A46_three_lane_race_stress_test.md` (182 L, eight sections). §A46.1 narrates the two already-observed adversarial scenarios (W16D7 concurrent-commit, W17D3 working-tree-drift) and the missing third (three-lane race). §A46.2 defines the audit window (`T_prev` → `T_curr` phase-boundary audit commits) and the three lane-ownership prefix sets (ind-tracks / bass / gallery). §A46.3 gives the three-terminal adversarial recipe and establishes the non-finding-by-design property of the W15D1 scoped-pathspec rule under three concurrent commits. §A46.4 is the paste-ready §6 audit row template for the first three-lane observation. §A46.5 is the failure-pattern fingerprint for the case where the rule ever fails (pre-commit hook becomes load-bearing). §§A46.6–7 cross-reference A41.6 / A44.3 / memory `feedback_git_workflow.md` and commit to documentation-only until observation. Closes W17 F3 spec; landing trigger deferred to first three-lane window. | landed (`7cc5a42`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W18_2026-04-19.md` (521 L) — §6 W12 F1 / W14 F1 cross-lane-contamination recurrence check returns **PASSED** (three W18 commits each scoped exactly to a single lane-owned path; one cross-lane commit `92cefa2` landed between W18D5 and the audit commit but touched only bass-lane-owned paths — zero file overlap with any W18 commit). §6 W18 check #2 applies A46.2's lane-classification to the four W18-window shas and resolves to **two lanes observed (ind-tracks + bass), not three** — A46.4 first-observation template not triggered this phase. Includes working-tree-layout transparency paragraph noting the venv editable-install finder re-point from `bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot/` to `htt_base/htt/htt/` (per bass-lane `92cefa2` body); pytest runs against the `htt/...` working-tree mirror; all tracked `bass_py/...` paths per W15D1 scoped-pathspec rule. | landed |

Final test tally over the touched surface at W18 boundary:
**1080 passed, 0 failed, 4 skipped** (+1 vs W17's 1079; 0 skip
change; 0 regressions). Skip composition unchanged from W10
end-of-phase.

Week 18 final gate — **all five items green**:

- [x] W17 F1 / W17 R1 A45.2 `_hash_config` docs-↔-code anchor
      landed (W18D1 `0d2fc9f`; +1 test; MIO 108 → 109).
- [x] W17 F2 / W17 R2 A45.6 ↔ A41.6 cross-link landed (W18D3
      `23fefbb`; +25 L prose; bidirectional resolution verified).
- [x] One of A46 dossier / MANU-CH03 extension landed — **A46
      picked** (W18D5 `7cc5a42`; new dossier, 182 L; closes W17 F3
      spec with landing trigger deferred to first three-lane
      observation).
- [x] Phase-boundary audit log written; §6 W12 F1 / W14 F1
      recurrence check returns **PASSED** (third distinct
      adversarial stress-test of the W15D1 scoped-pathspec rule —
      second observation of the concurrent-commit scenario,
      following W16D7; A46.4 three-lane template not triggered
      this phase).
- [x] No touched-surface regressions (1080 passed; +1 over W17;
      0 failed; 4 skipped unchanged).

## §1c-16. What shipped in Week 19

Session of 2026-04-19 (compressed: one session covered Week-19
Days 1-7). Three committed in-lane landings + one phase-boundary
audit (`AUDIT_PHASE_IND_TRACKS_W19_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W19D1 `_hash_config` signature-anchor extension (W18 F1) | `bass_py/mio/tests/test_mio_certificate_generator.py` +32 L — augments the existing `test_hash_config_matches_a45_2_pseudocode_shape` with two assertions: `tuple(inspect.signature(_hash_config).parameters) == ("parts",)` and `tuple(p.kind for p in params.values()) == (VAR_POSITIONAL,)`. Freezes the current signature shape so a future keyword-only argument addition (e.g. `*, digest_length=16` for A43's schema-hash digest upgrade) is flagged at anchor time rather than silently passing. Assertion strengthening on the existing W18D1 test (no +1 count delta). Each failing assertion's message names §A45.2 / §A45.6 / the relevant upgrade so the breaking PR's author is pointed at the dossier edit required in the same PR. Touched surface 1080 → 1080 (held); MIO contribution 109 → 109 (held). | landed (`3f2129f`) |
| W19D3 §A46.{5,6} expansion (W18 F2) | `docs/dossier/A46_three_lane_race_stress_test.md` +46 / −1 L — new §A46.5.1 "Common failure-mode invocations" (three named bypass shapes: missing trailing `--`, `git add -A` + `git commit -m`, `git commit -am`; each with symptom / failure-mode / per-shape repair pointer into memory `feedback_git_workflow.md`) + §A46.6 HJ-03 three-file triplet paragraph (A42 evidence anatomy + §A41.6 step 6.5 + §A45.6 paste block all fall under ind-tracks ownership, so the HJ-03 bundle commit resolves to a single lane via A46.2 regardless of concurrent lane activity). Unblocked alternative to §A46.4's "steady-state three-lane phrasing" which remains gated on the first three-lane observation (W19 did not observe a three-lane window — see W19 audit §6 check #2). Closes W18 F2. | landed (`ad27ee5`) |
| W19D5 DOS-A47 HJ-03 acceptance-test paste-replace protocol | NEW `docs/dossier/A47_hj03_acceptance_test_paste_replace_protocol.md` (~301 L, ten sections). Sits between §A41.6 step 6.5 (freeze the replay-harness signature) and §A45.6 (five-test paste block). §A47.2 five input prerequisites; §A47.3 ownership argument (harness at `bass_py/mio/interface/cache_replay.py`, NOT `bass_py/workspace/contracts/**`); §A47.4 `_make_cache_pair` fixture factory contract (three kwargs, must use `build_mio_certificate`); §A47.5 per-test translation table (tests [1]/[2]/[4]/[5] verbatim; [3] per-signature if HTT bundle shape deviates from `.paths` default); §A47.6 single-PR rule (signature-freeze + paste in same commit); §A47.7 eight-box reviewer checklist; §A47.8 two-anchor coexistence (W18D1/W19D1 contract surface + A47.5 test 1 harness surface); §A47.10 three re-audit triggers. Cross-refs A32 / A34 / A41 / A42 / A43 / A44 / A45 / A46. No code change. Caller's choice between A47 new dossier vs MANU-CH03 extension — A47 picked because it concretely unblocks the HJ-03 PR and builds on the §A41.6 step 6.5 + §A45.6 cross-link that W18D3 just landed. | landed (`6d87082`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W19_2026-04-19.md` — §6 W12 F1 / W14 F1 cross-lane-contamination recurrence check returns **PASSED** (three W19 commits each scoped exactly to a single lane-owned path; zero cross-lane commits landed during the W19 window — fourth distinct phase exercising the scoped-pathspec rule, first with zero concurrent pressure, classified as *non-adversarial* stress-test). §6 W19 check #2 applies A46.2's lane-classification to the three W19-window shas and resolves to **one lane observed (ind-tracks), not three** — A46.4 first-observation template not triggered this phase (second consecutive phase with ≤ two-lane result). | landed |

Final test tally over the touched surface at W19 boundary:
**1080 passed, 0 failed, 4 skipped** (unchanged vs W18's 1080; 0
skip change; 0 regressions). Skip composition unchanged from W10
end-of-phase.

Week 19 final gate — **all five items green**:

- [x] W18 F1 / W18 R1 `_hash_config` signature-anchor extension
      landed (W19D1 `3f2129f`; +2 assertions on existing test;
      no count delta; MIO contribution holds at 109).
- [x] W18 F2 / W18 R2 §A46.{5,6} expansion landed (W19D3
      `ad27ee5`; +46/−1 L; §A46.5.1 failure-mode invocations +
      §A46.6 HJ-03 triplet grammar deepening; unblocked
      alternative to A46.4 steady-state phrasing).
- [x] One of A47 dossier / MANU-CH03 extension landed — **A47
      picked** (W19D5 `6d87082`; new dossier, 301 L, ten
      sections; HJ-03 acceptance-test paste-replace protocol).
- [x] Phase-boundary audit log written; §6 W12 F1 / W14 F1
      recurrence check returns **PASSED** (fourth distinct
      adversarial stress-test phase of the W15D1 scoped-pathspec
      rule; first non-adversarial single-lane window in the
      stress-test record — rule held trivially).
- [x] No touched-surface regressions (1080 passed; unchanged vs
      W18; 0 failed; 4 skipped unchanged).

## §1c-17. What shipped in Week 20

Session of 2026-04-19 (compressed: one session covered Week-20
Days 1-7). Three committed in-lane landings + one phase-boundary
audit (`AUDIT_PHASE_IND_TRACKS_W20_2026-04-19.md`).

| Track | Artefact | Status |
|---|---|---|
| W20D1 `_hash_config` anchor scope-clarity docstring (W19 F3 / R3) | `bass_py/mio/tests/test_mio_certificate_generator.py` +15 L — adds an "Anchor scope (W19 F3 / W20D1)" paragraph inside the existing `test_hash_config_matches_a45_2_pseudocode_shape` docstring naming the three refactor kinds that intentionally trigger the W19D1 frozen-list assertion: (i) A43 schema-hash digest upgrade (REQUIRES paired §A45.2 edit); (ii) cache-replay strict-mode flag added independently of A43 (MAY require §A45.2 edit — caller's judgement); (iii) any non-`*parts` signature shape change (caller's judgement per §A47.6 single-PR rule). Pure documentation clarity; no assertion change; no production-code change. Closes W19 F3. Touched surface 1080 → 1080 (held); MIO contribution holds at 109. | landed (`9fb1407`) |
| W20D3 §A46.3 concrete git commands (W19 R-carry) | `docs/dossier/A46_three_lane_race_stress_test.md` +24 L — adds a paste-ready shell block to §A46.3 spelling out the exact `git add` / `git status --short` / `git commit -- <path>` per terminal, plus the post-arrival `git log --oneline -3` + `git show --stat <sha>` verification. Each terminal uses a representative path under its lane's ownership prefix (A46.2): Terminal A `bass_py/mio/tests/test_foo.py` (ind-tracks); Terminal B `bass_py/bass/hierarchy/bar.py` (bass); Terminal C `plots/physics_gallery/01_species_background/baz.png` (gallery). Unblocked alternative to W19 F1 / F2 closure (both HJ-03-PR-gated; no HJ-03 PR landed in W20). Section numbering unchanged. Touched surface unchanged. | landed (`5391dc8`) |
| W20D5 DOS-A48 MIO → HTT dependency-wait contract | NEW `docs/dossier/A48_mio_htt_dependency_wait_contract.md` (157 L, six sections). §A48.1 Purpose; §A48.2 Dependency matrix (eight-row table: HJ-01, HJ-03, HJ-04, HJ-05-full, MANU-CH12 §§12.1 / 12.4 / 12.5 / 12.8, A43 digest test — each with (a) current status, (b) upstream milestone tag, (c) consumed output, (d) paste target, (e) audit ref); §A48.3 Per-row promotion conditions; §A48.4 Audit §8 ledger mechanics (R<n> rows dereference into §A48.2 rows); §A48.5 Relation to other appendices (supersedes v3 §17.3's partial list); §A48.6 No code landing and steady-state ledger discipline (re-read every Week-N plan rotation; NEXT_SESSION §2 "Deferred" block is a projection of §A48.2). Cross-refs A32 / A34 / A41 / A42 / A44 / A45 / A47 / v3 §7 / v3 §10.2 / v3 §17.3. Caller's choice (option 2 of three W20D5 A48 candidates from §2 Week 20 Days 5–6) — option 1 (anchor-location protocol) and option 3 (cross-check channel catalogue extension) remain unpicked for W21+. No code change. | landed (`4d7a3ed`) |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W20_2026-04-19.md` — §6 W12 F1 / W14 F1 cross-lane-contamination recurrence check returns **PASSED** (three W20 commits each scoped exactly to a single lane-owned path; zero cross-lane commits landed during the W20 window at audit-write time; two concurrent drift vectors in the staging index and working tree (68 gallery renames from W19 + bass-lane deletions from W18 working-tree reorg) both excluded by the scoped-pathspec rule). §6 W20 check #2 applies A46.2's lane-classification to the three W20-window shas and resolves to **one lane observed (ind-tracks), not three** — A46.4 first-observation template not triggered this phase (three consecutive phases with ≤ two-lane result: W18 two-lane, W19 two-lane post-addendum, W20 one-lane). Fifth distinct phase exercising the scoped-pathspec rule; second distinct phase with active staging-index drift absorbed by construction (W19 addendum was the first). Addendum protocol notice included at the bottom: the "cross-lane commit arrives between audit-write and audit-commit" pattern has now occurred twice (W16/W18/W19); if it recurs on W20, a W20 F4 post-audit addendum will be appended following the W19 F4 precedent. | landed |

Final test tally over the touched surface at W20 boundary:
**1080 passed, 0 failed, 4 skipped** (unchanged vs W19's 1080;
0 skip change; 0 regressions). Skip composition unchanged from
W10 end-of-phase.

Week 20 final gate — **all five items green**:

- [x] W19 F3 / W19 R3 `_hash_config` anchor scope-clarity
      docstring landed (W20D1 `9fb1407`; +15 L docstring on
      existing test; no assertion change; MIO contribution
      holds at 109).
- [x] W19 F1 / W19 F2 close (HJ-03-PR-gated; not landed) OR
      unblocked alternative W18/earlier carry landed — **§A46.3
      concrete git commands picked** (W20D3 `5391dc8`; +24 L
      paste-ready shell block).
- [x] One of A48 dossier / MANU-CH03 extension landed — **A48
      picked** (W20D5 `4d7a3ed`; new dossier, 157 L, six
      sections; MIO → HTT dependency-wait contract).
- [x] Phase-boundary audit log written; §6 W12 F1 / W14 F1
      recurrence check returns **PASSED** (fifth distinct
      adversarial-stress-test phase; second phase with active
      staging-index drift absorbed by construction).
- [x] No touched-surface regressions (1080 passed; unchanged
      vs W19; 0 failed; 4 skipped unchanged).

## §1d. What was designed in the 2026-04-19 planning session

(Preserved here for provenance; unchanged from earlier rotations.
See v3 research plan + PART II + PART III of the governing plan.)

## §2. Active priorities for the next session (Week 21)

**"W20 R1 §A46.3 pedagogical-paths note (unblocked) + one W20
F-residual / W19 F-residual close + one A4x dossier / §A46
expansion / §A47 sharpening / MANU-CH03 extension"**. Week 20
landed all five gate items (W19 F3 `_hash_config` anchor
scope-clarity docstring + §A46.3 concrete git commands +
A48 MIO → HTT dependency-wait contract + phase audit), MIO
contribution held at 109, touched-surface held at 1080 (W20D1
is docstring-only on the existing test; W20D3 + W20D5 are
docs-only). The W12 F1 / W14 F1 cross-lane pattern did NOT
recur (W20 audit §6 check #1 PASSED — three W20 commits scoped
exactly to own paths; zero cross-lane commits landed during the
W20 window at audit-write time — fifth distinct phase exercising
the W15D1 scoped-pathspec rule; two concurrent drift vectors
(gallery renames from W19 + bass-lane deletions from W18) sat in
the staging index / working tree and were excluded by the
scoped-pathspec rule on every W20 commit). A46.4's three-lane
audit row template did NOT trigger this phase (W20 audit §6
check #2 — one lane observed, not three; three consecutive
phases with ≤ two-lane result — W18 two-lane, W19 two-lane
post-addendum, W20 one-lane). W21 targets the three P3 residuals
from W20 audit §8 (R1 §A46.3 pedagogical-paths note, R2 A48.3
producer-contract reciprocity, R3 A48.2 milestone tag YAML
sidecar hedge).

Week 21 remains in the dependency-wait window: HJ-01 production
wiring, HJ-03 evidence anatomy, HJ-04 departure skeleton, and
MANU-CH12 §§12.1 / 12.4 / 12.5 / 12.8 are still blocked on
bass_py W10-02 (K_ℓ atlas) and bass_py W11-02 (BiPoSH) — now
consolidated in `docs/dossier/A48_mio_htt_dependency_wait_
contract.md` §A48.2 as the SSOT ledger. A43 digest test itself
stays deferred-to-trigger per §A43.3 (also W20 R3-blocker — still
trigger-gated). A46.4 first-three-lane-observation row stays
paste-ready for the first phase that needs it. A47.5 per-test
translation table and §A46.6 code-surface file list are both
HJ-03-PR-gated (W19 R1 / W19 R2).

### Days 1–2 — W20 R1 §A46.3 pedagogical-paths note (unblocked; cheapest)

1. **W20 F1 — §A46.3's paste-ready shell block (W20D3) uses
   pedagogical paths (`bass_py/mio/tests/test_foo.py`,
   `bass_py/bass/hierarchy/bar.py`,
   `plots/physics_gallery/01_species_background/baz.png`) that
   do not exist in the repo.** A reviewer copy-pasting the block
   verbatim hits "file does not exist" on `git add`. The non-
   executable default is intentional (the block is an adversarial
   recipe; the reviewer is expected to substitute real lane-owned
   paths from their own session) but the prose does not say so.
2. Edit to `docs/dossier/A46_three_lane_race_stress_test.md`
   §A46.3 (2 L above the shell block, inside the "Paste-ready
   shell block" introductory paragraph):
   - add a one-line note: "Paths are pedagogical — substitute
     real lane-owned paths from the reviewer's session before
     executing; `test_foo.py` / `hierarchy/bar.py` / `baz.png`
     do not exist in the repo."
3. No code change; no test change; pure clarity edit.

- Commit tag: `W21D1: AUDIT(W20 F1): §A46.3 pedagogical-paths note`.
- Gate: `docs/dossier/A46_*.md` +2 L; cross-reference resolution
  unchanged; touched-surface 1080 → 1080 (0 count delta); MIO
  contribution holds at 109.

### Days 3–4 — One W20 F-residual or W19/W18-carry alternative

1. **W20 R2 + W20 R3 are partially gated** — R2 on HJ-01 PR
   landing (producer-side bass_py contract edit would ride the
   HJ-01 PR; consumer-side cross-reference note in §A48.3 is
   unblocked if preferred), R3 on first observed bass_py
   milestone rename (trigger-gated).
2. **Unblocked alternatives (W19/W18/earlier carries still open
   per §3 table)**:
   - **§A47 re-audit trigger sharpening.** §A47.10 names three
     re-audit triggers (non-default bundle shape, A43 lands
     first, module layout reorg). Add a fourth trigger —
     "`CacheReplayDriftError` gains a third message prefix
     beyond `config drift:` / `input-data drift:`" — and
     cross-reference §A45.2 step 2 / step 4 (~5-10 L). W19-
     carry alternative.
   - **W20 R2 consumer-side cross-reference.** Add a "bass_py
     side must publish `v_gate_sha` in the atlas provenance"
     note to §A48.3 HJ-01 row, with a forward pointer to the
     HJ-01 PR where the bilateral contract is finalised. ~3-5 L.
   - **§A48.6 machine-readable SSOT scaffold.** Start a
     `docs/dossier/A48_mio_htt_dependency_wait_contract.yaml`
     sidecar (analogous to A36a.yaml) mirroring §A48.2's eight
     rows; land it behind a `test_a48_matrix_matches_yaml`
     parity test for A48.2 structural drift detection.
     Preemptive R3 close; ~50-80 L dossier YAML + ~30-50 L test.
   - **W16 SKIP-02b-v3-LEGACY examination.** The 2 ×
     `test_figures_smoke.py` `mio.core` / `mio.reporting`
     skips are W6-era carries blocked on MANU-CH12-NEW figure
     retirement (still unaddressed through W20). Dossier-only
     or thin `test_nulls.py`-style smoke consolidation —
     caller's judgement on commit scope (~150-200 L dossier or
     ~30-50 L test refactor).
3. Caller's choice per W21 priorities; default to §A47.10 if
   unblocked / HJ-01 still not landed.

- Commit tag: `W21D3: <AUDIT(W20 Rx) or DOS-A4x or AUDIT(W6 SKIP)>
  <scope>`.
- Gate: +3-80 L prose edit (or +30-50 L test refactor); cross-
  reference resolution; no production-code change in the dossier
  paths.

### Days 5–6 — One new A4x dossier or MANU-CH03 extension

Pick ONE per caller's judgement — both are in-scope per the
governing plan's dependency-wait window:

1. **DOS-A49 (new A4x dossier — caller chooses topic).** Candidate
   topics from the W18+ unpicked-option pool and the W20 audit:
   - **A49 W18 F3 anchor-location protocol** (carry-forward from
     Week-18/19/20 unpicked option). Specifies the procedure for
     relocating the W18D1/W19D1 `_hash_config` anchor if the MIO
     package layout is reorganised. Includes a "two-anchor
     coexistence" paragraph for the HJ-03-landed-but-W18/W19-
     anchor-still-valid interim. ~100-150 L. Cross-refs A41 /
     A45 / A47.3 / A47.8 / A48.6.
   - **A49 cross-check channel catalogue extension** — extends
     A34.3's channel catalogue with a third entry for HJ-03
     (once it lands) or for the W7 FM3 TSC-05 schema-hash
     freeze (on first schema extension). ~100-150 L. Cross-refs
     A32 / A34 / A41 / A43 / A48.2.
   - **A49 audit §6 post-commit recurrence-check addendum
     protocol.** Formalises the "cross-lane commit arrives
     between audit-write and audit-commit" pattern that has now
     occurred three times (W16 F1 addendum, W19 F4 addendum, W20
     addendum-protocol notice). Names the required re-run of
     `git log T_prev..HEAD` at audit-commit time and the
     paste-ready addendum section format. ~100-150 L. Cross-refs
     A46.2 / memory `feedback_git_workflow.md` / the three audit
     addendum precedents.
2. **MANU-CH03 §3.X+8 extension (carry-forward from
   W16/W17/W18/W19/W20 options).** Extend
   `project/00_manuscript/ch03_framework.tex` with the W4
   Θ⁴-bridge → A43 schema-hash subsection. Remember: `/project`
   gitignored, no force-add (W8 FM1 rule); the gate is "+≥ 150 L
   with banned-vocab scan = 0 hits", verified in audit §7 only.

- Commit tag: `W21D5: DOS-A49 <chosen topic>` OR `W21D5: MANU-CH03
  §3.X+8 a₂-to-observations (uncommitted)`.
- Gate (option 1): new A49 file + cross-reference resolution; no
  code change. Gate (option 2): ch03_framework.tex +≥ 150 L;
  banned-vocab scan = 0; NOT committed (W8 FM1).

### Day 7 — Phase audit + NEXT_SESSION rotation

Standard phase-boundary audit per `feedback_phase_boundary_audit.md`.
Write to `docs/audits/AUDIT_PHASE_IND_TRACKS_W21_2026-04-19.md`
(date may shift). Audit MUST include a §6 recurrence check for
W12 F1 / W14 F1 cross-lane contamination (verify the W15D1
scoped-commit rule was followed on every W21 sha via
`git show --stat`), plus the A46.2 lane-classification check
that determines whether the A46.4 three-lane observation row
fires. The W15D1 scoped-pathspec rule has now been stress-tested
under five distinct phases (W16D7 concurrent-commit, W17D3
working-tree-drift, W18D5→W18D7 second concurrent-commit,
W19D5→W19D7 third concurrent-commit + staging-index drift,
W20 single-lane with two inactive drift vectors absorbed); W21
§6 continues the per-phase check as routine hygiene. **If a
three-lane commit window materialises during W21**, the audit §6
row uses §A46.4's paste-ready "first three-lane observation"
phrasing and W21 acquires the R1 follow-up of landing §A46.4's
steady-state phrasing. **Audit §6 MUST re-run `git log
T_prev..HEAD` at audit-commit time** per the W20 audit addendum
protocol notice (close the stale-body case before committing).

### Week 21 final gate

- [ ] W20 F1 / W20 R1 §A46.3 pedagogical-paths note landed
      (W21D1).
- [ ] One W20 F-residual / W19 F-residual / W18-carry alternative
      landed (W21D3; caller picks per unblocked status).
- [ ] One of A49 dossier / MANU-CH03 extension landed (caller's
      choice; W21D5).
- [ ] Phase-boundary audit log written; §6 W12 F1 / W14 F1
      recurrence check returns PASSED (plus A46.2 lane
      classification resolving to ≤ two lanes, or the first
      three-lane-observation row firing); §6 check re-run at
      audit-commit time per W20 addendum protocol.
- [ ] No touched-surface regressions (≥ 1080 passed, 0 failed;
      4 skipped unchanged unless new skips explicitly documented).

### Deferred to Week 21+ (not Week-21 targets) — see `A48.2` SSOT ledger

- **HJ-01 production wiring** — when bass_py W10-02 K_ℓ atlas lands.
  Replace the diagonal independence χ² with the per-ℓ-covariance
  weighted χ² (W10 F2); promote `reduction_status` from
  `'diagnostic-only'` to `'theory-direct'`; remove
  `DIAGNOSTIC_ONLY_CAVEAT` from the certificate's first slot;
  enable `MANU-CH12 §12.1` writeup (depends on the production
  HJ-01 numbers).
- **HJ-03 / HJ-04 / HJ-05-full** — same gating; see governing
  plan §17.3 dependency wait list.
- **MANU-CH12 §12.4 / §12.5 / §12.8** — blocked on HTT Phase F
  posteriors and the production HJ-01 / HJ-03 numbers.
- **W10 F1 / F2 / F3** — production-HJ-01 hardening list (warn on
  `_gammaincc` non-convergence; folded covariance χ²; Bonferroni
  knob on `flrw_consistent_within_band`).
- **W4 F1 mock coverage sandwich** — opportunistic; the manuscript
  layer now scopes the caveat (W10D5 §12.3.4).
- **W4 F4 Θ⁴ bridge htt audit tightening** — when htt lands
  `_a2_coefficient_table`.
- **W7 FM3 TSC-05 schema hash freeze** — add digest test on first
  schema extension.
- **W8 FM2** palette unification — opportunistic on figure
  regeneration.
- **W8 FM6** `clustering` vs `clustering_dipole` name mismatch —
  cross-lane rename; record only.

## §3. Carry-forward items from W1–W10 audits

Severity legend: **P0** = Day-1 blocker, **P1** = Week-N target,
**P2** = later week, **P3** = out-of-lane. W10 F4 + F5 are
RESOLVED (W11D1 `8aefbb8`); new W11 additions (F1–F5) at the
bottom.

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
| W5 APPLY-BIAS-AMP | **RESOLVED W12D2** | `_apply_bias_to_direction` scales by `\|V_true\|` not measurement amplitude. | Surfaced via `mio.diagnostics.masked_sky_caveats.BIAS_AMP_CAVEAT` + `build_report(..., mock_bias_applied=True)` kwarg in `cd220a6`; upstream helper intentionally untouched per W5 audit directive. |
| W6 SKIP-02b-v3-LEGACY | P2 | 2 `test_figures_smoke.py` skips on `mio.core` / `mio.reporting`. | Week 8+ MANU-CH12-NEW rewrite or retire the two figures. |
| W6 FM2 PROBE-SIGMA | **DOCS-RESOLVED W13D3** | Radio / CF4++ / BiPoSH σ_cone plan-placeholders. | `docs/dossier/A36a_sigma_cone_literature.md` (`ed2c9b1`) DOI/arXiv-anchors every σ and records Δ per probe. Code-side σ values intentionally unchanged per A36a.4 "caller's judgement" rule; §A36a.5 records the three-condition retirement criterion for the `*_sigma_cone_plan_placeholder` caveat flag. |
| W6 FM4 MC-VECTORISE | P3 | `_sample_isotropic_unit_vectors` per-mock loop. | Only if HJ-02a moves to 1e6-mock regime. |
| W6 FM5 PROBE-NAME-SCHEMA | P3 | ad-hoc probe_name string-join. | Deferred — CONTRACTS-01 schema-hash coordination. |
| W6 FM6 GIT-SHA-DRIFT | P3 | git_commit resolves at instantiation time. | Expected behaviour; no action. |
| **W7 FM1** | **P2** | **`bass_py/tsc/` test count is 598, not 615/700 as earlier §2 Week-7 gate assumed.** **The +116-test Week-7 delta over-delivers the ~+85 planned.** The ≥ 700 absolute-count gate was a stale figure. | **Use 598 as the Week-8 baseline; the new modules landed all tests planned.** |
| **W7 FM2** | **P2** | TSC-06 re-seeds `numpy.random.default_rng(seed)` and redraws eps1/eps2/eps3 in the same order as `FillingFraction.mc_posterior`; a future htt PR that reorders the draws (or inserts an extra rng.normal call) would silently break stream alignment. | Refactor `FillingFraction.mc_posterior` to accept a pre-drawn triple when the bass/htt lane is quiet. |
| **W7 FM3** | **MECH-RESOLVED W15D3** | TSC-05 JSON schema freeze is literal-based (`SCHEMA_VERSION = "TSC-05/v1"` + literal key-set test), not hash-based like `MioCertificate`. | `docs/dossier/A43_schema_hash_digest.md` (`8fae1ba`) specifies the digest mechanism (field name + normalised type + default kind + field order); §A43.6 contains paste-ready test spec. Test landing deferred to first schema extension per §A43.3 (HJ-03 / HJ-04 / TSC-05 v2 trigger). Landing pre-trigger would freeze the wrong digest. |
| **W7 FM4** (inherited W6 FM2) | **P2** | σ_cone placeholders. | See W6 FM2 row. |
| **W7 FM5** | **P3** | `bass_py/tsc/integration/` is new surface; not explicitly listed in `pyproject.toml` but covered by default glob. | No action; note only. |
| **W8 FM1** | **RESOLVED post-W8** | `/project` is intentionally gitignored; "landed" in the audit log means "working-tree updated", not "committed". The three force-added files (ch11, ch12, main.tex) were untracked via `git rm --cached` after user clarification; files preserved on disk. Durable rule added to memory `feedback_project_local_only.md`. | No action — never stage project/ paths. |
| **W8 FM2** | **P2** | 9 of 28 HTT figure scripts skip `apply_style()` (5 use local `set_style()`, 4 rely on explicit `dpi=300` kwarg). DPI uniform; palette not. | Opportunistic when figures are regenerated. |
| **W8 FM3** | **P2** | `fig_rho_sweep.py`, `fig_departure_summary.py`, `fig_v_pushforward.py` still hard-code `/mnt/user-data/outputs`. Applying W8D6 pattern drops 2-3 more skips. | Week 9 §2 Day 4 extension. |
| **W8 FM4** | **P3** | `fig_departure_summary` skip message now surfaces `dynesty` rather than the underlying file-not-found, due to import-order. Cleanly skipped; no regression. | No action; documentation only. |
| **W8 FM5** | **P3** | `TestRunnerSmoke` covers only the fast-path analytical approximation; production nested-sampling ~40 h CI cost is out of scope. | By design; no action. |
| **W8 FM6** | **P3** | `NULL_REGISTRY` keys `ClusteringDipoleNull` under `'clustering'` while its `.name` attribute is `'clustering_dipole'`. Pre-existing. | Cross-lane rename; record only. |
| **W10 F1** | **P3** | `mio.extraction.hj01_shear._gammaincc` 200-iter cap is silent on non-convergence. | Add `warnings.warn` in the iteration loop; bundled with HJ-01 production wiring (W12+). |
| **W10 F2** | **P3** | HJ-01 independence χ² treats per-ℓ residuals as iid; ignores cosmic-variance C_ℓ correlations. | Swap to weighted χ² with bass_py W10-02 covariance; production HJ-01 prerequisite. |
| **W10 F3** | **P3** | `flrw_consistent_within_band` 2σ default has ~75 % false-flag rate on 29 iid multipoles. | Document or change default to 3σ (Bonferroni-aware) or expose a `bonferroni=True` knob; production HJ-01 prerequisite. |
| **W10 F4** | **RESOLVED W11D1** | INDEPENDENT_TRACKS_PLAN v1.2 §21 Week 10 Day 5-6 wording "force-add contract (W8 FM1)" was stale post-W8-FM1. | Fixed in `8aefbb8` — plan bumped to v1.3 with §21 Week 10 + Week 11 entries that spell out the post-W8-FM1 `/project` rule verbatim. |
| **W10 F5** | **RESOLVED W11D1** | `test_extract_drops_zero_kernel_multipoles` hardcoded `report.ell.size == 27`. | Fixed in `8aefbb8` — now computes `cfg.ell_max - cfg.ell_min + 1 - len(dropped)` from `ShearExtractorConfig()` defaults. |
| **W11 F1** | **RESOLVED W12D3** | `mio.coherence.redshift_binned.drift_pvalue` has no exact-enumeration path for small-N reproducibility. | Landed in `99465e5` — `exact: bool = False` kwarg + `EXACT_ENUMERATION_MAX_PERMUTATIONS = 10_000` ceiling + 6 new tests. |
| **W11 F2** | **P3** | permutation null distribution degenerate for (N ≤ 8, K = 2, antipodal injection) test designs. | Documentation-only; enforced culturally via "≥ 3 bins or N > 12" guidance in W11 audit §6. |
| **W11 F3** | **DOCS-RESOLVED W13D3** | HJ-02b inherits σ_cone placeholders from HJ-02a (v3 §16.2 FM2 / W6 FM2). | Same resolution as W6 FM2 — A36a literature anchoring; §A36a.5 retirement criterion applies per-probe to both HJ-02a and HJ-02b. |
| **W11 F4** | **RESOLVED W12D1** | A37 grammar acceptance tests (`test_probe_name_is_alphabetical_bundle`, `test_probe_name_matches_grammar_v1`) deferred pending CONTRACTS-01 v2 hash-digest infrastructure. | Landed in `015246d` — 8 new tests in `test_probe_name_grammar.py`; producer tightening across all 3 MIO emitters (alphabetical sort + HJ-01 MODEL_ID singleton). |
| **W11 F5** | **P3** | `emit_redshift_coherence_artefact` provenance SHA = `MioCertificate.git_commit` (instantiation-time; inherited from MIO-HJ-06a, already documented as W6 FM6). | No action — by design. |
| **W12 F1** | **RESOLVED W13D1** | W12D3 commit (`99465e5`) pulled in unrelated bass-lane + gallery-lane files (working-tree drift from a concurrent lane's staging). Cannot retroactively split per additive-commits rule. | Mitigation landed in `41b7200` + memory `feedback_git_workflow.md` durable entry — pre-commit `git status --short` gate. Verified effective on all four W13 commits (W13 audit §6 check = PASSED). |
| **W12 F2** | **P3** (docs) | A41 checklist is not mechanised — no acceptance test parses existing MIO modules to verify compliance. | Optional follow-up when HJ-03 lands: add `test_mio_report_types_pass_a41_checklist`. |
| **W12 F3** | **RESOLVED W13D2** | A37.3 registered PROBE_IDs only exist in markdown; code has no frozen registry. A new unregistered 12-char-alnum name would pass the regex. | Landed in `b7607ef` — `bass_py/mio/interface/probe_name_registry.py` with `REGISTERED_PROBE_IDS: Tuple[str, ...]` + `is_registered_probe_id` helper + 6 tests (code↔dossier parity via markdown parser; `STANDARD_PROBES ∪ STANDARD_Z_PROBES` parity). |
| **W12 F4** | **P3** (coverage) | `build_report(mock_bias_applied=True)` is a documentation-only contract — a caller that lies about it mislabels the certificate. | Optional follow-up: require a `mock_bias_report: Optional[InjectedMockReport] = None` when flag is set. |
| **W12 F5** | **P3** (testing) | `test_drift_pvalue_exact_matches_mc_at_small_N` uses `abs < 0.05` — loose enough to mask a 2σ MC bias. | Tighten to `abs < 3·sqrt(p·(1-p)/n)` only if precision becomes load-bearing; not currently blocking. |
| **W13 F1** | **P3** (docs drift) | A34 / A36 / A40 tabular rows still label evidence-anatomy as **HJ-04**, while A32 / A41 / W13D5 A42 bind it to **HJ-03** (the schema-authoritative binding). | W14D3 candidate — one-pass `sed` rename across the three dossiers; batch with HJ-03 landing commit if opportunistic. Logged verbatim in A42.6. |
| **W13 F2** | **P3** (coverage) | W13D2 `test_standard_probes_agree_with_registry` checks `name` set-equality only; σ_cone / l / b drift between HJ-02a and HJ-02b producers would silently pass. | **Slated for W14D1** — land `test_standard_probes_have_consistent_sigma_cone_across_producers`. |
| **W13 F3** | **P3** (coverage) | W13D2 A37.3 markdown parser fails silently on cosmetic table-format drift (switching backtick to bold renders the regex zero-match). | Docstring comment on `_parse_a37_3_probe_ids_from_markdown`; no code change needed. |
| **W13 F4** | **P3** (testing) | A36a.3 literature Δ table is not programmatically tested — a future σ edit could silently drift the dossier claim. | Opportunistic; add a YAML/JSON sidecar parser only if >1 σ update lands in a single session. W15 R3 candidate (slated). |
| **W13 F2** | **RESOLVED W14D1** | W13D2 `test_standard_probes_agree_with_registry` compared only `name` set-equality. | Landed in `593a7b6` — `test_standard_probes_have_consistent_sigma_cone_across_producers` asserts `sigma_cone_deg / l_deg / b_deg` exact-equality per PROBE_ID across HJ-02a ↔ HJ-02b. |
| **W13 F1** | **RESOLVED W14D3** | A34 / A36 / A40 tabular rows labelled evidence-anatomy as HJ-04 while A32 / A41 / A42 bind it to HJ-03. | Landed inside `4eb044b` (FB-1.4-labelled cross-lane commit; rename content exact, commit label wrong — see W14 F1). `grep -rn "HJ-04 evidence" docs/dossier/` now returns zero. |
| **W13 R3** | **RESOLVED W14D2** | A36 §A36.4 had no pointer to A36a's DOI-anchored σ record. | Landed in `491ecfd` — A36.4 gains a "Provenance anchor (W13D3 / W14D2)" paragraph linking A36a.2 / A36a.3 / A36a.5. |
| **W14 F1** | **RESOLVED W15D1** | W12 F1 recurrence on W14D3 — the dossier rename landed inside `4eb044b` labelled `FB-1.4`; another lane's concurrent commit ate our staged index. The W13D1 pre-commit gate catches contamination *into* this lane's commits but not commits from other lanes firing in the brief reset→commit window. | Landed in `d48b920` + memory `feedback_git_workflow.md` durable entry — scoped `git commit -- <paths>` rule. Verified effective on all three W15 commits (W15 audit §6 check #1 = PASSED; symmetric verification on cross-lane `3dcc505` shows only bass-lane files). |
| **W14 F2** | **RESOLVED W15D5** | `test_hj02a_certificate_carries_placeholder_tags_for_non_promoted_probes` uses `issubset` rather than set-equality; an over-emission path would pass silently. | Landed in `293652a` — new `test_hj02a_certificate_caveat_count_equals_flagged_set_with_no_caller_caveats` asserts set-equality + length-equality on the no-caller-caveats path. Caller-caveats residual tracked as W15 F1. |
| **W14 F3** | **P3** (docs / testing) | Inherited W13 F4 — A36a.3 Δ table still unmechanised. | W16 R2 candidate (W15 deferred in favour of R2 per plan "Pick ONE"; YAML sidecar + parity test). |
| **W14 F4** | **P3** (docs) | A36a.2 CatWISE row pre-W14D5 text ("No placeholder flag warranted") was overwritten by the promotion log; readers following an old link see different content. | Optional preservation note; zero code impact. |
| **W15 F1** | **P3** (coverage) | W15D5 over-emission guard exercises only the no-caller-caveats path. An over-emission coexisting with caller-supplied caveats would pass `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags` (dedup-count focused). | W16D1 — extend the caller-caveats test with `set(cert.domain_caveats) == set(caller_caveats) ∪ expected_tags` (union-equality). |
| **W15 F2** | **P3** (docs) | Residual W14 F3 — A36a.3 literature-Δ table still unmechanised (W15D5 picked R2). | W16D3 — land the YAML sidecar + parity test. |
| **W15 F3** | **P3** (timing) | A43 digest test is spec-only until first schema extension lands. If neither HJ-03 / HJ-04 / TSC-05 v2 lands within W16–W25, W7 FM3 code-side closure stays pending. | §A43.3 — lands in same PR as the first extension; no standalone action. |
| **W13 F4** | **RESOLVED W16D3** | A36a.3 literature Δ table unmechanised. | Landed in `5765e0b` — `docs/dossier/A36a_sigma_cone_literature.yaml` (5 rows, machine-readable mirror) + paired test `test_standard_probes_sigma_code_matches_a36a_yaml` (code parity on `STANDARD_PROBES[*].sigma_cone_deg` + YAML self-consistency). Scalar-reduction (midpoint) convention for the three ranged-σ probes; optional `sigma_lit_range_deg: [min, max]` preserves full range. |
| **W14 F3** | **RESOLVED W16D3** | Inherited W13 F4 — A36a.3 Δ table still unmechanised. | Same resolution — `5765e0b`. |
| **W15 F1** | **RESOLVED W16D1** | Over-emission-with-caller-caveats coverage gap on `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags`. | Landed in `cd952ee` — union-equality assertion `set(cert.domain_caveats) == set(caller_caveats) \| expected_tags` appended to the existing test (no +1 count; assertion strengthening). |
| **W15 F2** | **RESOLVED W16D3** | Inherited W13 F4 / W14 F3 — A36a.3 table unmechanised (W15D5 picked R2 instead). | Same resolution as W13 F4 — `5765e0b`. |
| **W16 F1** | **RESOLVED W16D7 (post-audit addendum)** | Initial W16 §6 check observed zero cross-lane commits during W16 landings, flagged as "not adversarially stress-tested". | Revised post-audit: cross-lane `4c50313` (`FB-2.2: Class A II/VI_0/VIII nabla_tilde`) landed between W16D5 `484ffed` and the audit commit `646784b`. Symmetric `git show --stat` verification: audit commit is 2 ind-tracks files only, zero bass contamination; `4c50313` is 6 bass files only, zero ind-tracks contamination. **W15D1 scoped-pathspec rule PASSED its first real adversarial stress test.** Addendum at bottom of `AUDIT_PHASE_IND_TRACKS_W16_2026-04-19.md`. |
| **W16 F2** | **RESOLVED W17D1** | A44.3 pins `MioCertificate.git_commit` at-instantiation capture time; no runtime assertion guarded a future refactor to emission- or read-time resolution. | Landed in `151fbc4` — `test_git_commit_is_capture_time_not_lazy` in `bass_py/workspace/contracts/tests/test_mio_certificate.py` (+37 L): constructs `MioCertificate` with a concrete `git_commit`, monkeypatches `subprocess.run` to raise + `_resolve_git_commit` to return a sentinel, asserts attribute access and `dataclasses.asdict` both return the construction-time value, and bans a class-level descriptor on the field. |
| **W16 F3** | **RESOLVED W17D3** | A36a YAML `sigma_lit_range_deg: [min, max]` optional field was not self-consistency-checked. | Landed in `3137cc0` — `test_a36a_yaml_range_brackets_midpoint` (+47 L) iterates every row with the optional range field and asserts `min <= max` + `min <= sigma_lit_deg <= max`, plus an "at least one row carries the range field" convention guard. MIO 107 → 108. |
| **W17 F1** | **RESOLVED W18D1** | A45.2's `verify_cache_replay` pseudocode names `_hash_config` as the re-hashing helper; no dossier-test catches a silent rename / resize / signature reorder of the helper. | Landed in `0d2fc9f` — `test_hash_config_matches_a45_2_pseudocode_shape` in `bass_py/mio/tests/test_mio_certificate_generator.py` (+50 L): imports `_hash_config` by exact name used in A45.2, asserts `__name__`, asserts six-arg positional form returns 16-char lowercase-hex string, cross-checks `cert.config_hash == _hash_config(...)` build-↔-replay parity. MIO 108 → 109. |
| **W17 F2** | **RESOLVED W18D3** | §A45.6's five-test paste-ready block assumes the HJ-03 harness signature (`mio_cert` input, `htt_input_bundle` descriptor shape). HJ-03 landing with a different signature would require per-item translation of the block. | Landed in `23fefbb` — §A45.6 gains an up-front "Harness-signature note (W17 F2 / W18D3)" paragraph (+14 L) binding the paste-ready block to the two-arg signature and deferring the freeze decision to A41.6 step 6.5; §A41.6 gains a reciprocal step 6.5 (+11 L) with a forward pointer to §A45.6 and the "same PR as paste-replace" rule. |
| **W17 F3** | **RESOLVED W18D5** (spec; landing trigger deferred to first three-lane observation) | The W15D1 scoped-pathspec rule has been stress-tested under two adversarial scenarios (W16D7 concurrent-commit, W17D3 working-tree-drift); the three-lane race (ind-tracks + bass + gallery all committing into the same audit window) has not yet been observed in the repo's history. | Landed in `7cc5a42` — `docs/dossier/A46_three_lane_race_stress_test.md` (182 L, eight sections): audit-window definition (§A46.2), adversarial recipe (§A46.3), paste-ready §6 row template for the first three-lane observation (§A46.4), failure-pattern fingerprint (§A46.5). Landing trigger for §A46.4's first-observation phrasing = first phase where A46.2 lane-classification resolves to all three lanes. W18 check #2 observed two lanes (ind-tracks + bass), not three. |
| **W18 F1** | **P3** (docs freshness) | W18D1's `_hash_config` anchor asserts `__name__`, positional signature, and 16-char lowercase-hex output. A future refactor that adds a keyword-only argument (e.g. `*, digest_length=16` for the A43 schema-hash digest upgrade) passes the current anchor unchanged but leaves A45.2's pseudocode subtly incomplete. | **Slated for W19D1 (W18 R1)** — extend the W18D1 anchor with `inspect.signature(_hash_config).parameters` frozen-list assertion; +1 assertion on the existing test (no +1 count). |
| **W18 F2** | **P3** (docs lifecycle) | §A46.4 specifies the "first three-lane observation" §6 row phrasing but does NOT specify the steady-state (second+) phrasing. When the second three-lane observation lands, the audit author has to invent wording in the moment. **Blocked until first observation.** | **Slated for W19D3 (W18 R2)** — if the first three-lane observation lands in W19, extend §A46.4 with a steady-state phrasing paragraph; otherwise pick an unblocked alternative (§A46.5 failure-mode fingerprint expansion OR §A46.6 grammar deepening). |
| **W18 F3** | **P3** (coverage location) | W18D1's anchor lives in `test_mio_certificate_generator.py` and presupposes the MIO package's conftest-managed sys.path wiring. A future repo reorganisation (splitting the interface module into two, moving `mio/` under a new package root) would need to re-home the anchor. | No repair; continue periodic re-verification on lane boundaries. Note for future HJ-03 PR: if the replay harness lives in a new `mio.interface.cache_replay` module, consider moving or cloning the W18D1 anchor into that test file so the two guards stay adjacent. W19+ DOS-A47 candidate topic. |
| **W18 F1** | **RESOLVED W19D1** | W18D1 anchor was lax on kwarg evolution. | Landed in `3f2129f` — `tuple(inspect.signature(_hash_config).parameters) == ("parts",)` + `tuple(p.kind for p in params.values()) == (VAR_POSITIONAL,)` frozen-list assertions on the existing `test_hash_config_matches_a45_2_pseudocode_shape` (no +1 count; assertion strengthening). |
| **W18 F2** | **PARTIALLY RESOLVED W19D3** | §A46.4 steady-state three-lane phrasing still deferred-to-first-observation; §A46.{5,6} expansion picked as unblocked alternative. | Landed in `ad27ee5` — §A46.5.1 (three common bypass invocations: missing `--`, `git add -A` + `git commit -m`, `git commit -am`) + §A46.6 HJ-03 three-file triplet. §A46.4 steady-state phrasing remains gated on first three-lane observation (W20+ when observation lands). |
| **W19 F1** | **P3** (docs first-use) | A47.5 per-test translation table is specification-first; no HJ-03 PR has exercised it. A first-PR surprise may indicate a spec gap rather than a PR bug. | HJ-03-PR-gated. Record in that PR's §6 audit row which of A47.5 [1]–[5] required adaption; update §A47.5 / §A47.10 re-audit trigger accordingly. No standalone W20 action. |
| **W19 F2** | **P3** (docs completeness) | §A46.6 HJ-03 three-file triplet names only dossier paths; the PR will also touch `bass_py/mio/interface/cache_replay.py` + `bass_py/mio/tests/test_cache_replay.py` (new files per A47.3). | HJ-03-PR-gated. When HJ-03 lands, extend §A46.6 with a "code-surface file list" sub-bullet naming the two new `bass_py/mio/*` paths alongside the dossier triplet. |
| **W19 F3** | **RESOLVED W20D1** | W19D1's frozen-list assertion stricter than §A45.2's pseudocode strictly requires. | Landed in `9fb1407` — "Anchor scope (W19 F3 / W20D1)" paragraph added inside `test_hash_config_matches_a45_2_pseudocode_shape` docstring naming three refactor kinds (A43 digest upgrade — REQUIRES paired §A45.2 edit; cache-replay strict-mode — MAY require §A45.2 edit; non-`*parts` signature shape change — caller's judgement per §A47.6). No assertion change; pure docs clarity. |
| **W20 F1** | **P3** (docs usability) | §A46.3's W20D3 paste-ready shell block uses pedagogical paths (`bass_py/mio/tests/test_foo.py`, `bass_py/bass/hierarchy/bar.py`, `plots/physics_gallery/01_species_background/baz.png`) that do not exist in the repo. A reviewer copy-pasting the block verbatim hits "file does not exist" on `git add`. | **Slated for W21D1 (W20 R1)** — add a one-line "Paths are pedagogical — substitute real lane-owned paths before executing" note above the shell block in §A46.3 (~2 L). Unblocked, cheapest W20 residual. |
| **W20 F2** | **P3** (docs drift) | §A48.2's "Upstream milestone" column uses bass_py roadmap tags (e.g. `W10-02 (K_ℓ atlas V-gate)`) that mirror the bass_py lane's internal vocabulary as of 2026-04-19. A bass_py roadmap rename or re-sequence drifts the tags silently until the next AUDIT(Wx Rn) fix commit. | **W21+ opportunistic (W20 R3)** — trigger-gated on first observed milestone rename. Optional early close: sidecar `docs/dossier/A48_mio_htt_dependency_wait_contract.yaml` with a parity test (analogous to A36a.yaml + `test_standard_probes_sigma_code_matches_a36a_yaml`). |
| **W20 F3** | **P3** (docs contract reciprocity) | §A48.3 HJ-01 promotion conditions state the V-gated atlas JSON "carries `v_gate_sha=...` in its provenance" but do not cross-reference a bass_py producer-side contract guaranteeing this. A bass_py edit that drops the field would be caught late (at HJ-01 landing). | **W21+ opportunistic (W20 R2)** — partially HJ-01-PR-gated (producer-side edit would ride the HJ-01 PR); consumer-side cross-reference note in §A48.3 is unblocked and could be picked up in W21D3. |

## §4. Environment and quickstart

```bash
# Repo root
cd /home/cosmosapjw/Dropbox/bianchi/htt_base

# Sanity: touched-surface test run.  As of 2026-04-19 post-W20:
# 1080 passed, 0 failed, 4 skipped (0 delta vs W19; 0 skip change —
# W20D1 is docstring-only; W20D3/W20D5 docs-only).
#
# NOTE (W18D7 working-tree transparency): the canonical tracked
# paths are `bass_py/...` per every commit through W18D5. The
# bass-lane `92cefa2` (W18 window) re-pointed the venv editable
# install from `bass_phase1_snapshot_2026-04-18/...` to
# `htt_base/htt/htt/` and moved the live working tree to
# `htt/...` (untracked mirror). Run pytest against the `htt/...`
# tree; tracked commits still carry the `bass_py/...` prefix.
venv/bin/python -m pytest htt/htt/tests/ htt/src/ \
                htt/tsc/admissibility/ \
                htt/tsc/diagnostics/ htt/tsc/charts/ \
                htt/tsc/integration/ \
                htt/workspace/ htt/mio/

# tsc standalone (~14 s; 602 passed post-W9; unchanged W10-W19).
venv/bin/python -m pytest htt/tsc/

# MIO standalone (collection check — 109 tests post-W18D1; W19/W20 held).
venv/bin/python -m pytest htt/mio/ --collect-only -q | tail -1

# Full monorepo suite (slower).
venv/bin/python -m pytest htt/
```

Path notes:

* Canonical vs live tree: commits through W18D5 use `bass_py/...`
  paths; the live working-tree layout is `htt/...` (byte-identical
  mirror; untracked as of W18). New W19+ edits should continue to
  target `bass_py/...` paths for tracked commits and mirror into
  `htt/...` for pytest verification, until the bass lane formally
  commits the rename.
* `bass_py/src/common/` is importable via `bass_py/conftest.py` (which
  prepends `src/` to sys.path) and via `bass_py/pyproject.toml` (which
  adds `src/` to the setuptools package-find).
* `htt` is its own editable install (`bass_py/htt/setup.py`).  If the
  next session fails to import `htt.core.ssot`, verify
  `venv/bin/pip install -e bass_py/htt/` has run in this venv.
* `dynesty` **is now installed** at version 3.0.0 (post-W10D1).
  `common.bulkflow_likelihood.run_dynesty` consumes it directly;
  the contract-guard test
  `test_bulkflow_likelihood.py::test_run_dynesty_raises_clear_runtime_error`
  self-skips ("dynesty installed — RuntimeError path not exercised").
  Tests that need the stub-injection still pass `dynesty_module=
  SimpleNamespace(NestedSampler=...)` to bypass the real sampler for
  speed.

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
* **MIO HJ-01 production wiring / HJ-03 / HJ-04 / HJ-05-full** require
  bass_py outputs (W10-02 K_ℓ atlas, W11-02 BiPoSH, HTT Phase F
  posteriors). Governing plan §17.3 catalogues the dependency wait
  list. **This lane's MIO work as of W11 covers HJ-02a directional
  coherence + boot infrastructure + HJ-05a-lite masked_sky_caveats
  (all W6) plus the HJ-01 *skeleton* (W10D3) plus HJ-02b z-binned
  directional coherence (W11D3), both gated to
  `reduction_status='diagnostic-only'` until the bass_py W10-02
  V-gate signs the K_ℓ atlas** — see W11 audit §3 for the contract.
* `plots/physics_gallery/` — gallery refresh is bass_py's per-phase rule.

### §5a. This lane's new territory (updated post-W18)

Directories that **this** lane now owns (created or will be created
per the v1.3 plan — bass_py session must not touch):

* `bass_py/src/common/*` — ZoA / bulk-flow common modules (Week 1–4 landed).
* `bass_py/workspace/` + `bass_py/workspace/contracts/*` — interface
  contracts (Week 5 Days 1–2 landed).
* `bass_py/mio/*` — MIO package. Week 6 shipped the skeleton +
  MIO-HJ-02a directional coherence + MIO-HJ-06a certificate generator +
  MIO-BRIDGES-01 PR13AM re-export + MIO-HJ-05a-lite masked-sky caveats;
  Week 10 added `mio/extraction/hj01_shear.py` (HJ-01 skeleton);
  Week 11 added `mio/coherence/redshift_binned.py` (HJ-02b);
  Week 12 added A37 grammar tests + producer tightening
  (alphabetical bundle, HJ-01 MODEL_ID singleton); APPLY-BIAS-AMP
  caveat surfacing in `mio/diagnostics/masked_sky_caveats.py`;
  exact-enumeration path on `mio.coherence.redshift_binned.drift_pvalue`;
  Week 13 added `mio/interface/probe_name_registry.py` (frozen
  `REGISTERED_PROBE_IDS` tuple + A37.3 markdown-vs-code parity test);
  Week 14 added `mio/interface/sigma_cone_provenance.py`
  (`PROMOTED_SIGMA_CONE_PROBES` frozenset + per-probe placeholder
  caveat emission; wired into both HJ-02a and HJ-02b producers) +
  `mio/tests/test_sigma_cone_provenance.py` (9 tests);
  **Week 15 added**: +1 over-emission guard test
  (`test_hj02a_certificate_caveat_count_equals_flagged_set_with_
  no_caller_caveats`) extending the W14 file to 10 tests. MIO
  contribution 105 → 106.
  **Week 16 added**: union-equality assertion on
  `test_hj02a_caller_caveats_preserved_alongside_placeholder_tags`
  (W16D1, no +1 count) + `test_standard_probes_sigma_code_matches_
  a36a_yaml` (W16D3, +1 test) → `test_sigma_cone_provenance.py`
  now 11 tests. MIO contribution 106 → 107.
  **Week 17 added**: `test_a36a_yaml_range_brackets_midpoint`
  (W17D3, +1 test) → `test_sigma_cone_provenance.py` now 12 tests;
  plus `test_git_commit_is_capture_time_not_lazy` (W17D1, +1 test)
  on `bass_py/workspace/contracts/tests/test_mio_certificate.py`
  (workspace-layer, not counted under MIO). MIO contribution
  107 → 108; touched surface 1077 → 1079.
  **Week 18 added**: `test_hash_config_matches_a45_2_pseudocode_
  shape` (W18D1, +1 test) on `bass_py/mio/tests/test_mio_
  certificate_generator.py` → `test_mio_certificate_generator.py`
  now 11 tests. Docs-↔-code anchor for the A45.2 `_hash_config`
  helper (name + six-arg positional signature + 16-char
  lowercase-hex output shape + build-↔-replay parity). MIO
  contribution 108 → 109; touched surface 1079 → 1080.
  **Week 19 added**: W19D1 strengthens the W18D1 anchor with
  `inspect.signature(_hash_config).parameters` frozen-list
  assertions (names `("parts",)` + kinds `(VAR_POSITIONAL,)`);
  +2 assertions on the existing test, no +1 count delta.
  `test_mio_certificate_generator.py` holds at 11 tests; MIO
  contribution holds at 109; touched surface holds at 1080.
* **`bass_py/tsc/integration/*`** — NEW Week-7 subpackage; currently
  holds TSC-06 `htt_bridge` + tests. Distinct from `bass_py/tsc/{admissibility, charts, diagnostics}/`.
* `docs/dossier/A13_*`, `A14_*`, `A32_*`, `A33_*`, `A34_*`,
  `A35_*`, `A36_*`, `A36a_*` (W13), `A37_*`, `A38_*`,
  `A39_*`, `A40_*`, `A41_*` (W12), `A42_*` (W13), `A43_*` (W15),
  `A44_*` (W16), `A45_*` (W17), `A46_*` (W18), `A47_*` (W19) —
  manuscript dossier. Week 7 added
  A34 + A35 + A38 + A40; `A13_02_*` through `A13_14_*` landed
  Week 9; A36 + A37 landed Week 11; A41 landed Week 12; A36a +
  A42 landed Week 13; Week 14 extended A34 / A36 / A40 / A42
  (HJ-04 → HJ-03 naming sweep) and grew A36.4 + A36a.2 + A36a.5 +
  A36a.6 with the CatWISE + BiPoSH placeholder retirement narrative;
  **Week 15 added `A43_schema_hash_digest.md`** (~306 L) —
  W7 FM3 mechanism dossier, test spec ready for paste-on-extension;
  **Week 16 added `A44_mio_htt_handshake_sequence.md`** (~281 L) —
  temporal companion to A34 specifying the t₁→t₅ MIO→HTT cross-check
  execution order; `A36a_sigma_cone_literature.yaml` (60 L) SSOT
  mirror of §A36a.3 + A36a.md §A36a.3 gains a machine-readable
  pointer paragraph;
  **Week 17 added `A45_mio_cache_replay_drift.md`** (~269 L) —
  content-hash companion to A44's execution-order companion to
  A34: §A45.2 `verify_cache_replay` pseudocode for HJ-03 replay
  harness, §A45.5 `allow_unsigned_config=True` escape-hatch +
  clean A43-digest upgrade path, §A45.6 paste-ready five-test
  acceptance block (test 5 mirrors W17D1 at the MIO harness
  surface).
  **Week 18 added `A46_three_lane_race_stress_test.md`** (182 L,
  eight sections) — process-hygiene companion to A44 / A45
  covering the three-lane race scenario (ind-tracks + bass +
  gallery concurrent commits into the same audit window); §A46.2
  lane-classification algorithm + §A46.3 adversarial recipe +
  §A46.4 paste-ready §6 row template + §A46.5 failure-pattern
  fingerprint; landing trigger deferred to first three-lane
  observation. §A45.6 + §A41.6 also gained bidirectional cross-
  link (+14/+11 L) binding the HJ-03 replay-harness signature
  freeze to the acceptance-test paste-replace.
  **Week 19 added `A47_hj03_acceptance_test_paste_replace_protocol.md`**
  (~301 L, ten sections) — HJ-03 landing-PR protocol sitting
  between §A41.6 step 6.5 and §A45.6; §A47.2 five input
  prerequisites, §A47.3 ownership (harness at `bass_py/mio/
  interface/cache_replay.py`), §A47.4 fixture-factory contract,
  §A47.5 per-test translation table, §A47.6 single-PR rule,
  §A47.7 eight-box reviewer checklist, §A47.8 two-anchor
  coexistence (W18D1/W19D1 contract surface + A47.5 test 1
  harness surface), §A47.10 three re-audit triggers. Plus §A46
  grew §A46.5.1 (three common bypass invocations) + §A46.6
  HJ-03 three-file triplet (+46/−1 L).
  **Week 20 added `A48_mio_htt_dependency_wait_contract.md`**
  (157 L, six sections) — MIO → HTT dependency-wait SSOT ledger.
  §A48.2 is an eight-row matrix cataloguing the ind-tracks
  artefacts (HJ-01, HJ-03, HJ-04, HJ-05-full, MANU-CH12 §§12.1 /
  12.4 / 12.5 / 12.8, A43 digest test) whose promotion is
  blocked on upstream bass_py / HTT milestones, with per-row
  (current status, upstream milestone tag, consumed output,
  paste target, audit ref) columns. §A48.3 per-row promotion
  conditions; §A48.4 audit §8 ledger mechanics (R-rows
  dereference into §A48.2 rows); §A48.5 cross-refs A34 / A41 /
  A42 / A45 / A47 and supersedes v3 §17.3's partial list; §A48.6
  documents the steady-state ledger discipline (re-read every
  Week-N plan rotation; NEXT_SESSION §2 "Deferred" block
  projects §A48.2). Plus §A46.3 grew a paste-ready shell block
  (+24 L) spelling out the three-terminal adversarial recipe as
  executable commands (`git add` / `git status --short` /
  `git commit -- <path>` per lane). Plus W20D1 added an "Anchor
  scope (W19 F3 / W20D1)" paragraph inside the W18D1/W19D1
  `_hash_config` anchor docstring (+15 L, docstring-only) naming
  three refactor kinds (A43 digest upgrade, cache-replay strict-
  mode, non-`*parts` signature shape change).
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
