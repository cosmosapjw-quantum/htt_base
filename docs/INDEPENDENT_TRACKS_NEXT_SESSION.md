# Independent Tracks — next-session resumption prompt

**As of**: 2026-04-19, post-`IND_TRACKS_W6` phase.
**Last audited**: 2026-04-19
(`docs/audits/AUDIT_PHASE_IND_TRACKS_W6_2026-04-19.md`;
prior phases `AUDIT_PHASE_IND_TRACKS_W5_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W4_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W3_2026-04-19.md`).
**Governing plan**: `INDEPENDENT_TRACKS_PLAN.md` **v1.2** (PART II MIO
integration patch + PART III Week-5+ realignment landed 2026-04-19;
Week 1–6 routine shipped; Week 7 routine detailed in plan §21).
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

Final test tally over the touched surface: **795 passed, 1 pre-existing
failure (F3 carry-forward — now scoped as Week-5 Day-1 target, see §2
WS-BOOT-01), 23 cleanly-skipped**
(`bass_py/htt/tests/ bass_py/src/ bass_py/tsc/admissibility/
bass_py/tsc/diagnostics/ bass_py/tsc/charts/`).  W3 numbers (305
passed) were preserved identically; the +490 delta comes from 94 new
W4 tests landing in `bass_py/src/common/` + `bass_py/tsc/diagnostics/`
+ `bass_py/tsc/charts/` and from the `bass_py/tsc/` suite-extension
that follows TSC-02/TSC-04.

## §1c-2. What shipped in Week 5

Commits `3e96075` (W5D1) → `974fb4d` (W5D7). Seven daily landings, one
audit. All v1.1 PATCH-01 / 02 / 03 / 04 extinct; RED-01 + SKIP-17 +
SKIP-02a + SKIP-02c all resolved.

| Track | Artefact | Status |
|---|---|---|
| WS-BOOT-01 (Day 1) | `bass_py/workspace/{__init__.py, contracts/{__init__.py, htt_to_mio.py, tests/test_htt_to_mio_roundtrip.py}}` + fixture `workspace/results/integrated_pipeline_results.json`; `htt/htt/integration/to_mio.py` sys.path hack stripped; `conftest.py` prepends workspace root (4 contract tests + `test_to_mio_builds_bundle` RED-01 anchor all green) | landed |
| CONTRACTS-01 (Day 2) | `workspace/contracts/{mio_certificate.py, htt_forward_output.py, atlas_entry.py}` + `tests/{test_mio_certificate.py, test_htt_forward_output.py, test_atlas_entry.py}` (13 new tests incl. schema hash + posterior-field ban) | landed |
| G19-ENFORCE-01 (Day 3) | `workspace/contracts/tests/test_g19_enforcement.py` — 5 tests covering (1) NotImplementedError, (2) HTT likelihood rejects MioCertificate, (3) MioCertificate is not a PosteriorExportBundle, (4) no posterior field on any non-HTT contract, (5) static scalar-sum lint across `bass_py/{bass,htt/htt,mio,src/common,tsc,workspace}` production code | landed |
| HTT-FIG-SHIM (Day 4) | `htt/htt/figures/__init__.py` prepend `htt/core/` to sys.path; `htt/htt/core/plot_style.py` save_fig now tolerant of missing outdir (HTT_FIG_OUTDIR env var + OSError fallback); `htt/tests/test_figures_smoke.py` known-external list gains `/mnt/user-data` + `dynesty`; figures smoke 36 passed / 21 skipped → 49 passed / 8 skipped (plot_style 17 → 0, bounds 2 → 0) | landed |
| REG-02 (Day 4) | `workspace/contracts/tests/test_reg02_artifact_prefix.py` — forward-guard lint scanning `bass_py/mio/` (Week 6+) and `__mio_owned__`-flagged modules for `mio_`-prefix compliance on produced artefact filename literals | landed |
| PR13AM-MIO-TAG (Day 5) | `htt/htt/PR13AM_te_sign_d1d3_bridge.py` gets module-level `__mio_owned__ = True` + `__mio_rationale__` + `_mio_artifact_name(stem, version)` helper; 2 new tests in `test_PR13AM_production_gate.py` | landed (v1.1 PATCH-01 extinct) |
| HTT-OBS-FIXTURE (Day 5) | `bass_py/workspace/data/obs_defaults.json` — SSOT v3 §9.2 constants (T_CMB_K=2.72548, Omega_m=0.3153, eps1_kin=1.2336e-3, …) + `dipole_observations` block consumed by `DipoleVectorLikelihood` (Planck / CatWISE / Radio / CF4 dipoles) | landed (SKIP-02c 2 → 0) |
| PR13AH-v2-WIRE (Day 6) | `htt/htt/PR13AH_observables_reintegration.py` gains keyword `mock_bias_correction: InjectedMockReport \| None = None` + `_apply_bias_to_direction` helper; when a COMMON-F report is supplied, `mock_calibrated_summary.calibration_pending = False` with direction shifted opposite to the residual; 3 new tests (+8 existing unchanged) | landed (v1.1 PATCH-02 extinct) |
| LEGACY-README (Day 7) | `legacy/README.md` prepended blockquote banner pointing to v3 RESEARCH_PLAN + `workspace/contracts/`; original body preserved | landed (v1.1 PATCH-04 extinct) |
| DOS-A30-MIO drafts (Day 7) | `docs/dossier/A32_mio_certificate_schema.md`, `A33_htt_forward_output_atlas_entry.md`, `A39_per_module_epistemic_ownership.md` | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W5_2026-04-19.md` | landed |

Final test tally over the touched surface
(`bass_py/htt/tests/ bass_py/src/ bass_py/tsc/admissibility/
bass_py/tsc/diagnostics/ bass_py/tsc/charts/ bass_py/workspace/`):
**839 passed, 0 failed, 8 skipped**. `htt/tests/` specifically:
**201 passed / 0 failed / 8 skipped** (from 181 / 23 in W4 — +20 tests,
RED-01 cleared, 15 skips migrated to different classes with 17
plot_style skips fully resolved).

## §1c-3. What shipped in Week 6

Commits `6d66058` (W6D1) → `0e534c8` (W6D7). Five daily landings, one
phase-boundary audit. `bass_py/mio/` package booted and populated with
directional coherence (HJ-02a), MioCertificate generator (HJ-06a),
masked-sky caveats (HJ-05a-lite), and PR13AM re-export bridge.

| Track | Artefact | Status |
|---|---|---|
| MIO-BOOT-01 (Day 1) | `bass_py/mio/{__init__.py, coherence/__init__.py, extraction/__init__.py, tension/__init__.py, decomposition/__init__.py, diagnostics/__init__.py, interface/{__init__.py, mio_certificate.py}, bridges/__init__.py, tests/{__init__.py, test_boot.py}}` + `pyproject.toml` `[tool.setuptools.packages.find]` / `testpaths` include `mio*` + `workspace*` | landed |
| FIG-MIO-SKIP-GATE (Day 1) | `bass_py/workspace/contracts/tests/test_fig_mio_skip_gate.py` — `test_figures_mio_skip_should_activate_after_mio_boot` + `test_mio_boot_subpackages_do_not_raise_on_import` | landed |
| MIO-HJ-06a (Day 2) | `bass_py/mio/interface/mio_certificate.py::build_mio_certificate(...)` — auto-populates git_commit + config_hash; raises ValueError on any `posterior`-keyword; 10 tests covering all plan §12.4 gates | landed |
| MIO-HJ-02a (Days 3-5) | `bass_py/mio/coherence/directional.py` (~310 L) — `DirectionalProbe`, `STANDARD_PROBES` (5-probe SSOT), `resultant_vector`, `pairwise_separations`, `coherence_chi2`, `isotropy_pvalue`, `to_mio_certificate`, `emit_directional_coherence_artefact`; 12 tests; artefact `bass_py/workspace/results/mio_directional_coherence_v1.json` persisted (R=0.9990, p_iso≈3e-4, χ²/dof=9.45 with seed 20260419) | landed |
| MIO-BRIDGES-01 (Day 6) | `bass_py/mio/bridges/__init__.py` re-exports `htt.PR13AM_te_sign_d1d3_bridge` via option A (semantic identity via Python `is`); existing PR13AM tests unchanged; 5 integration tests | landed |
| MIO-HJ-05a-lite (Day 7) | `bass_py/mio/diagnostics/masked_sky_caveats.py` — `SkyCoverageReport` + `build_report` + `as_caveats_list`; reuses `common.healpix_selection.build_zoa_mask`; 7 tests | landed |
| Phase audit | `docs/audits/AUDIT_PHASE_IND_TRACKS_W6_2026-04-19.md` | landed |

Final test tally over the touched surface
(`bass_py/htt/tests/ bass_py/src/ bass_py/tsc/admissibility/
bass_py/tsc/diagnostics/ bass_py/tsc/charts/ bass_py/workspace/
bass_py/mio/`): **878 passed, 0 failed, 8 skipped** (+39 tests vs
W5's 839; skip count unchanged, composition shifted — see carry-
forward W6 SKIP-02b-v3-LEGACY below).

## §1d. What was designed in the 2026-04-19 planning session

No code landed in this planning pass — only plan documents. Two new
planning artefacts and two new plan-revision sections.

| Artefact | Location | Summary |
|---|---|---|
| Parent plan v3 | `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` | v2 → v3 upgrade: MIO added as 4th pillar (Model-Independent Observatory, not "certification engine"). Interface contracts (`HttForwardOutput`, `MioCertificate`, `AtlasEntry`), G19 hard-separation rule, Phase J (HJ-01~07), ch12 new manuscript chapter, MIO appendix A31–A40. |
| Governing plan PART II | `INDEPENDENT_TRACKS_PLAN.md` §10–§17 | MIO integration patch: PATCH-01~05 identification + new tracks CONTRACTS-01, G19-ENFORCE-01, CONTRACTS-02, MIO-BOOT-01, MIO-HJ-02a, MIO-HJ-06a, MIO-BRIDGES-01, MIO-HJ-05a-lite, MANU-CH11-REDESIGN, MANU-CH12-NEW, DOS-A30-MIO, REG-02. |
| Governing plan PART III | `INDEPENDENT_TRACKS_PLAN.md` §18–§22 | Code-inspection realignment (based on commit `115f505` LB-5 + IND_TRACKS_W4). Identifies RED-01 (F3), SKIP-17/02a/02b/02c, PLACEHOLDER-01, SEMANTIC-01, AMBIG-01. Adds 7 new tracks (WS-BOOT-01, HTT-FIG-SHIM, HTT-OBS-FIXTURE, PR13AH-v2-WIRE, PR13AM-MIO-TAG, LEGACY-README, FIG-MIO-SKIP-GATE). Replaces Week 5–9 day-by-day schedule. |

**Reading order for the next session**: governing plan §21 Week 7
day schedule → §3.3 TSC-03 → §4.2 TSC-05 → §4.3 TSC-06 →
v1.1 §14.3 G19 cross-check guard → v1.1 §11.3 CONTRACTS-02 →
v1.1 §13.3 DOS-A30-MIO A35/A38/A40.
The day schedule below (§2) is a distilled view of Week 7 from §21.

## §2. Active priorities for the next session (Week 7)

**"tsc 잔여 + 선행 가능 appendix"** — distilled from
`INDEPENDENT_TRACKS_PLAN.md` §21 Week 7.

### Days 1–2 (Mon–Tue) — TSC three-bound hierarchy

**TSC-03** (plan §3.3). Ship
`bass_py/tsc/admissibility/three_bound_hierarchy.py` together with a
cross-check test against `htt.bounds`. Exposes the Planck / WMAP / CF4
three-bound comparator ordering used elsewhere in the manuscript and
derives the identical ceilings from the `htt` side for the
cross-validation anchor.

- Commit tag: `W7D2: tsc three-bound hierarchy`
- Gate: `three_bound_hierarchy` + `test_three_bound_hierarchy_matches_htt_bounds`
  green (values agree to rtol 1e-10).

### Day 3 (Wed) — TSC MES Michaelis-Menten export

**TSC-05** (plan §4.2). `bass_py/tsc/charts/michaelis_menten_export.py`
exposes the Route B SSOT mirror of the MES
Michaelis-Menten coefficients so downstream chart scripts consume a
single source rather than scattering constants.

- Commit tag: `W7D3: tsc michaelis_menten export`
- Gate: 3 tests — SSOT match, zero drift from `bass.observational.planck_mes_bounds`,
  JSON schema freeze.

### Days 4–5 (Thu–Fri) — TSC ↔ HTT integration bridge

**TSC-06** (plan §4.3 + v1.1 §14.3). `bass_py/tsc/integration/htt_bridge.py`
computes F_Bayes on the tsc side and automates the cross-check against
the htt Gaussian-posterior regression. Must set `is_cross_check=True`
on every output (v1.1 §14.3 G19 guard) so the result is never mistaken
for a primary posterior.

- Commit tag: `W7D5: tsc htt_bridge with G19 guard`
- Gate: 5 tests — F_Bayes match within published band [0.068, 0.118];
  `is_cross_check=True` asserted; mismatch test fails loudly.

### Day 6 (Sat) — G19 cross-check protocol doc

**CONTRACTS-02** (plan v1.1 §11.3). `docs/dossier/A34_g19_cross_check_protocol.md`
writing up the G19 cross-check channel (HTT ↔ TSC via TSC-06) and
enumerating the failure modes that a non-`is_cross_check=True` path
would introduce.

- Commit tag: `W7D6: G19 cross-check protocol doc`
- Gate: A34 draft + appendix hash check.

### Day 7 (Sun) — MIO appendix A35 / A38 / A40 drafts

**DOS-A30-MIO** (plan v1.1 §13.3 remainder). A35 directional coherence
appendix (cross-reference for MIO-HJ-02a), A38 masked-sky caveats
appendix (cross-reference for MIO-HJ-05a-lite), A40 G19 architectural
stance.

- Commit tag: `W7D7: MIO appendix A35/A38/A40 drafts`
- Gate: 3 markdown files, each with the DOS-A30 template header.

### Week 7 final gate (plan §21)

- [ ] `bass_py/tsc/` 테스트 ≥ 700 (현재 615 + TSC-03 / 05 / 06 ≈ +~85).
- [ ] tsc ↔ htt F_Bayes cross-check 자동화 + 불일치 시 fail.
- [ ] TSC-06 출력에 `is_cross_check=True` 명시 + G19 guard 테스트 green.
- [ ] CONTRACTS-02 문서 + A35 / A38 / A40 초안 착륙.
- [ ] Phase-boundary audit written to
      `docs/audits/AUDIT_PHASE_IND_TRACKS_W7_YYYY-MM-DD.md`.

### Deferred to Week 8+ (not Week-7 targets but part of this lane)

- **MANU-CH11-REDESIGN + MANU-CH12-NEW §12.0 / §12.2 / §12.6 / §12.7
  drafts** — Week 8 (plan §21).
- **HTT-STAB final** — Week 8. Resolves the `/mnt/user-data` pipeline-data
  5 skips (W5 SKIP-05-LATENT) and the W6 SKIP-02b-v3-LEGACY 2 skips via
  per-figure v3 rewrites (FM1 root-cause patch).
- **`venv/bin/pip install dynesty`** — Week 7–8 convenient window
  (closes W5 DYNESTY-DEP).
- **W4 F4** Θ⁴ bridge htt audit tightening — bundle with TSC-03/05/06
  natural continuation.
- **W4 F1** mock coverage sandwich — opportunistic during TSC-06 work
  when `C_pix` non-uniform support is needed.
- **DOS-A13 remaining 12 models** — Week 9.
- **APPLY-BIAS-AMP refinement** (W5 audit carry-forward) — opportunistic
  when `ChannelSummary` gains a velocity-amplitude field.

## §3. Carry-forward items from W1–W6 audits + 2026-04-19 inspection

Recorded here per audit R2 so the next session doesn't rediscover them.
Severity legend: **P0** = Day-1 blocker, **P1** = Week-7 target, **P2** = later
week, **P3** = out-of-lane. W6 additions at the bottom.

| Tag | Severity | Description | Where to act |
|---|---|---|---|
| W1-W2 F2 | P2 | Two copies of `PreferredAxis` (htt.PR13AJ and common.contracts).  Intended — collapsed later. | When htt starts consuming `common.contracts`, expose `htt.PreferredAxis = common.contracts.PreferredAxis` alias and remove the htt-local copy.  Add a one-line import-equivalence test. |
| W1-W2 F3 | — | **RESOLVED W5D1** — WS-BOOT-01 landed `bass_py/workspace/contracts/htt_to_mio.py` + stripped the sys.path hack. Commit `3e96075`. | No further action. |
| W1-W2 F5 | P2 | `htt.core.ssot.C.T0_uK = 2.7255e6` inconsistent with `T0_K = 2.72548`. | Change `T0_uK = C.T0_K * 1e6`, then run the `eps_ell` / `D_ell_from_eps` numerical regression sweep.  Commit-side test: remove or invert `test_tcmb_ssot_drift_documented` so the fix is asserted, not the drift. |
| W1-W2 F6 | P3 | `bass.observational.planck_mes_bounds.T_CMB_K = 2.7255` drifts from canonical Fixsen value. | **Bass-side**, not to be touched in this independent-tracks lane.  When bass_py session is quiescent, coordinate a bass-side `T_CMB_K → 2.72548` commit with D_2 anchor re-calibration.  Wire via `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md`. |
| W3 F1 | P2 | Pixelization is an equal-area iso-latitude ring scheme, not HEALPix RING. | Swap `lb_to_pix` / `pixel_centers` / `nside_to_npix` for `healpy` backends when the project adopts healpy (parent plan §7.5). |
| W3 F4 | — | **RESOLVED** — `MANU-CH03 §3.X+3 Θ⁴ bridge` landed via W4 TSC-04 + manuscript subsection. | No further action. |
| W4 F1 | P2 | `run_zoa_null_mocks` coverage drifts outside [0.60, 0.76] when `C_pix` is non-uniform (sandwich cov needed). | Address in Week 7 (plan §21) — opportunistic during TSC-03/05/06. |
| W4 F2 | P2 | F_Bayes regression validated on Gaussian posterior; htt numerical equivalence not yet checked. | Address in Week 7 (plan §21) via TSC-06 `tsc.integration.htt_bridge`. |
| W4 F4 | P2 | Θ⁴ bridge htt audit uses FD at `h = 1e-2` (`tol_htt = 5e-3`). | Address in Week 7 (plan §21) when htt lands a native `_a2_coefficient_table` — swap the FD extraction in `tsc.charts.theta4_bridge_verify._extract_htt_a2_coefficient`. |
| INSPECT-19 RED-01 | — | **RESOLVED W5D1** — WS-BOOT-01 landed. Same fix as W1-W2 F3. | No further action. |
| INSPECT-19 SKIP-17 | — | **RESOLVED W5D4** — HTT-FIG-SHIM via `htt/figures/__init__.py` sys.path prepend (conftest approach won't fire for tests outside figures/; moved to package `__init__`). plot_style 17 → 0. | No further action. |
| INSPECT-19 SKIP-02a | — | **RESOLVED W5D4** — same HTT-FIG-SHIM fix. bounds 2 → 0. | No further action. |
| INSPECT-19 SKIP-02b | — | **PARTIALLY RESOLVED W6D1** — `import bass_py.mio` now succeeds (plan §19.7 gate + `test_figures_mio_skip_should_activate_after_mio_boot` green). The literal skip count is unchanged because the two figures (`fig_certification_matrix.py`, `fig_identified_reporting_split.py`) reference v2 legacy submodules `mio.core.ceiling_families` / `mio.reporting.identified_vs_reporting` that are NOT in the v3 skeleton. See `W6 SKIP-02b-v3-LEGACY` below. | See W6 SKIP-02b-v3-LEGACY. |
| INSPECT-19 SKIP-02c | — | **RESOLVED W5D5** — HTT-OBS-FIXTURE landed `bass_py/workspace/data/obs_defaults.json` with v3 §9.2 SSOT constants + `dipole_observations` block. | No further action. |
| INSPECT-19 PLACEHOLDER-01 | — | **RESOLVED W5D6** — PR13AH-v2-WIRE added `mock_bias_correction` kwarg + `_apply_bias_to_direction`. When bias supplied, `calibration_pending=False`. | No further action. |
| INSPECT-19 SEMANTIC-01 | — | **RESOLVED W5D5** — PR13AM-MIO-TAG added `__mio_owned__`, `__mio_rationale__`, `_mio_artifact_name`. | No further action. |
| INSPECT-19 AMBIG-01 | — | **RESOLVED W5D7** — LEGACY-README banner prepended; original body preserved. | No further action. |
| PATCH-05 | P3 | `src/common/contracts.py` `PreferredAxis` v3 extra fields — v1.1 §10.2 marked optional. | Defer; current field set is sufficient. Revisit only if a downstream consumer demands richer provenance. |
| W5 SKIP-05-LATENT | P2 | 5 `test_figures_smoke.py` skips on `/mnt/user-data/outputs/<fname>.json/npz` (`FLRW_tilt_results.json`, `IS06_3D_posterior.npz` ×2, `robustness_sweeps_integrated.json` ×2, `fig_colin_beta.png`). Latent issue surfaced by HTT-FIG-SHIM. | Week 8 HTT-STAB — ship synthetic fixture stubs at `bass_py/workspace/pipeline_outputs/` + honour `HTT_PIPELINE_OUTDIR` env var. |
| W5 DYNESTY-DEP | P2 | 1 skip in `fig_MES_three_bounds.py` on `No module named 'dynesty'`. | `venv/bin/pip install dynesty` at the next convenient window. |
| W5 APPLY-BIAS-AMP | P2 | `_apply_bias_to_direction` scales by `\|V_true\|` not measurement amplitude because `ChannelSummary` has no velocity amplitude field yet. | Opportunistic during Week 7–8 when the amplitude field is introduced; update helper to use `amp_meas * u_hat`. |
| W6 SKIP-02b-v3-LEGACY | P2 | 2 `test_figures_smoke.py` skips migrated from `No module named 'mio'` → `No module named 'mio.core'` / `No module named 'mio.reporting'`. The two figures (`fig_certification_matrix.py`, `fig_identified_reporting_split.py`) still reference v2 "certification engine" vocabulary. | Week 8+ MANU-CH12-NEW phase. Either rewrite the figures in v3 "observatory" terms, OR retire them in favour of new HJ-02 / HJ-05 figures. Do NOT port v2 legacy modules into the v3 skeleton — it would contaminate the semantic scope (see W6 audit FM1 and legacy/README.md banner). |
| W6 FM2 PROBE-SIGMA | P2 | `STANDARD_PROBES` σ_cone values for Radio (10°) / CF4pp (15°) / BiPoSH (20°) are plan-suggested placeholders, not paper-cited. Dominated by CMB (σ=0.5°) so changes are in-the-weeds for R and p_iso. | Opportunistic during Week 8 MANU-CH12-NEW §12.2 draft — cite NVSS+RACS / Tully+2023 / Planck BiPoSH values with refs. |
| W6 FM4 MC-VECTORISE | P3 | `_sample_isotropic_unit_vectors` loops per-mock inside `isotropy_pvalue`. Fine at `n_mock=10k` (~50 ms), slow at `1e6`. | Revisit only if HJ-02a moves to a 1e6-mock regime. Rewrite as a single `rng.uniform((m, n, 3))` vectorised draw. |
| W6 FM5 PROBE-NAME-SCHEMA | P3 | Generated MioCertificate stores `probe_name = "CMB+CatWISE+Radio+CF4pp+BiPoSH"` string join. Functional but ad hoc. | Deferred — a structured `probe_names: list[str]` field would trip `test_miocertificate_schema_frozen` and needs CONTRACTS-01 freeze-policy coordination. |
| W6 FM6 GIT-SHA-DRIFT | P3 | `build_mio_certificate` resolves `git_commit` at instantiation time; a long-lived session that commits between builds tags different certs with different SHAs. | Expected behaviour for diagnostic provenance (documented in docstring). No action unless a client demands atomic-build-session SHA pinning. |

## §4. Environment and quickstart

```bash
# Repo root
cd /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot

# Sanity: touched-surface test run.  As of 2026-04-19 post-W6:
# 878 passed, 0 failed, 8 skipped (+39 new tests vs W5).
venv/bin/pytest bass_py/htt/tests/ bass_py/src/ \
                bass_py/tsc/admissibility/ \
                bass_py/tsc/diagnostics/ bass_py/tsc/charts/ \
                bass_py/workspace/ bass_py/mio/

# Full monorepo suite (slower; tsc alone is ~18 s).
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
  shipped LB-0 through LB-5 (`115f505` unified Lowell-Bianchi integrator
  + TCA dispatch). Uncommitted modifications to `bass_py/bass/hierarchy/__init__.py`
  and `bass_py/pyproject.toml` in the working tree are bass-side in-progress
  work — do not stage or commit them from this lane.
* W10-02 CAMB V-gate, W11-01/02/03, W12-01/02, W13-01/02, W14-01,
  W15-01/02/03 (post-LB-5 roadmap) — parent plan v3 §7.
* **MIO HJ-01 / HJ-03 / HJ-04 / HJ-05-full** require bass_py outputs
  (W10-02 K_ℓ atlas, W11-02 BiPoSH, HTT Phase F posteriors). Governing
  plan §17.3 catalogues the dependency wait list. **This lane's MIO
  work (Week 6) is limited to HJ-02a directional coherence + boot
  infrastructure + HJ-05a-lite masked_sky_caveats** — the modules that
  do not depend on bass_py deliverables.
* `plots/physics_gallery/` — gallery refresh is bass_py's per-phase rule.

### §5a. This lane's new territory (2026-04-19 planning session)

Directories that **this** lane now owns (created or will be created
per the v1.2 plan — bass_py session must not touch):

* `bass_py/src/common/*` — ZoA / bulk-flow common modules (Week 1–4 landed).
* `bass_py/workspace/` + `bass_py/workspace/contracts/*` — interface
  contracts (Week 5 Day 1–2).
* `bass_py/mio/*` — new MIO package. Week 6 shipped the skeleton +
  MIO-HJ-02a directional coherence + MIO-HJ-06a MioCertificate generator +
  MIO-BRIDGES-01 PR13AM re-export + MIO-HJ-05a-lite masked-sky caveats.
  Distinct from `legacy/mio/` which is the v2 "certification engine"
  era snapshot (read-only, banner added in Week 5 Day 7).
* `docs/dossier/A13_*`, `A14_*`, `A32_*`, `A33_*`, `A35_*`, `A38_*`,
  `A39_*`, `A40_*` — manuscript dossier (`A13_02_*` through `A13_14_*`
  land in Week 9).
* `project/00_manuscript/ch03_framework.tex` (MANU-CH03 subsections;
  Week 1–4 landed; ~800 L gap vs v3 §11.3 target remains).
* `project/00_manuscript/ch11_error_hierarchy.tex` (MANU-CH11-REDESIGN, Week 8).
* `project/00_manuscript/ch12_mio_observatory_results.tex` **(new file)** —
  MANU-CH12-NEW (Week 8 draft for §12.0/§12.2/§12.6/§12.7).

If either lane is tempted to touch the other's area, stop and ask the
user first.
