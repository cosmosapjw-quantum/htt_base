# Independent Tracks — next-session resumption prompt

**As of**: 2026-04-19, post-`IND_TRACKS_W5` phase.
**Last audited**: 2026-04-19
(`docs/audits/AUDIT_PHASE_IND_TRACKS_W5_2026-04-19.md`;
prior phases `AUDIT_PHASE_IND_TRACKS_W4_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W3_2026-04-19.md`).
**Governing plan**: `INDEPENDENT_TRACKS_PLAN.md` **v1.2** (PART II MIO
integration patch + PART III Week-5+ realignment landed 2026-04-19;
Week 1–5 routine shipped; Week 6 routine detailed in plan §21).
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

## §1d. What was designed in the 2026-04-19 planning session

No code landed in this planning pass — only plan documents. Two new
planning artefacts and two new plan-revision sections.

| Artefact | Location | Summary |
|---|---|---|
| Parent plan v3 | `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` | v2 → v3 upgrade: MIO added as 4th pillar (Model-Independent Observatory, not "certification engine"). Interface contracts (`HttForwardOutput`, `MioCertificate`, `AtlasEntry`), G19 hard-separation rule, Phase J (HJ-01~07), ch12 new manuscript chapter, MIO appendix A31–A40. |
| Governing plan PART II | `INDEPENDENT_TRACKS_PLAN.md` §10–§17 | MIO integration patch: PATCH-01~05 identification + new tracks CONTRACTS-01, G19-ENFORCE-01, CONTRACTS-02, MIO-BOOT-01, MIO-HJ-02a, MIO-HJ-06a, MIO-BRIDGES-01, MIO-HJ-05a-lite, MANU-CH11-REDESIGN, MANU-CH12-NEW, DOS-A30-MIO, REG-02. |
| Governing plan PART III | `INDEPENDENT_TRACKS_PLAN.md` §18–§22 | Code-inspection realignment (based on commit `115f505` LB-5 + IND_TRACKS_W4). Identifies RED-01 (F3), SKIP-17/02a/02b/02c, PLACEHOLDER-01, SEMANTIC-01, AMBIG-01. Adds 7 new tracks (WS-BOOT-01, HTT-FIG-SHIM, HTT-OBS-FIXTURE, PR13AH-v2-WIRE, PR13AM-MIO-TAG, LEGACY-README, FIG-MIO-SKIP-GATE). Replaces Week 5–9 day-by-day schedule. |

**Reading order for the next session**: governing plan §21 Week 6
day schedule → §12.2 MIO-BOOT-01 → §12.3 MIO-HJ-02a → §12.4 MIO-HJ-06a
→ §12.5 MIO-BRIDGES-01 → §12.6 MIO-HJ-05a-lite → §19.7 FIG-MIO-SKIP-GATE.
The day schedule below (§2) is a distilled view of Week 6 from §21.

## §2. Active priorities for the next session (Week 6)

**"MIO 패키지 부팅 + HJ-02 선행"** — distilled from
`INDEPENDENT_TRACKS_PLAN.md` §21 Week 6.

### Day 1 (Mon) — MIO package bootstrap + figure skip cascade

**MIO-BOOT-01** (plan §12.2). Create `bass_py/mio/` skeleton:
`{__init__.py, coherence/__init__.py, extraction/__init__.py,
tension/__init__.py, decomposition/__init__.py, diagnostics/__init__.py,
interface/{__init__.py, mio_certificate.py}, bridges/__init__.py,
tests/{__init__.py, test_boot.py}}`. Register in `bass_py/pyproject.toml`
`[tool.setuptools.packages.find]` include list.

**FIG-MIO-SKIP-GATE** (plan §19.7). Verify that the 2 `No module named
'mio'` skips in `test_figures_smoke.py` auto-clear once MIO package is
importable. Add regression `test_figures_mio_skip_should_activate_after_mio_boot`.

- Commit tag: `W6D1_BOOT: mio package skeleton`
- Gate: `import bass_py.mio` succeeds; `test_figures_smoke.py` mio-skip
  count drops 2 → 0.

### Day 2 (Tue) — MioCertificate generator API

**MIO-HJ-06a** (plan §12.4). `bass_py/mio/interface/mio_certificate.py`
with `build_mio_certificate(report_type, probe_name, channel,
departure_variables, adequacy_indicators, consistency_metrics, *,
domain_caveats, reduction_status, generated_by, input_data_hashes,
htt_cross_check_suggested=None)` that auto-populates git_commit +
config_hash + returns a `workspace.contracts.MioCertificate`. Reject
`posterior`-keyword fields.

- Commit tag: `W6D2: MioCertificate generator API`
- Gate: 3 tests — `test_build_certificate_frozen`,
  `test_build_rejects_posterior_keyword`,
  `test_provenance_auto_populated`.

### Days 3–5 (Wed–Fri) — Directional coherence (HJ-02a)

**MIO-HJ-02a** (plan §12.3). `bass_py/mio/coherence/directional.py` (~350 L):
- `DirectionalProbe` frozen dataclass
- `resultant_vector(probes)` weighted unit-sum
- `isotropy_pvalue(probes, n_mock, rng)` Fisher-distribution or permutation
- `pairwise_separations(probes)` 5×5 separation matrix
- `coherence_chi2(probes)` χ² for common-axis hypothesis
- `to_mio_certificate(probes, p_iso, resultant, config_hash)` integration
- `STANDARD_PROBES` hardcoded 5-probe SSOT (CMB / CatWISE / Radio / CF4pp / BiPoSH)

- Commit tag: `W6D5: mio directional coherence`
- Gate: 5 tests —
  `test_isotropic_null_pvalue_gt_0p05` (10k isotropic mocks, no false detection),
  `test_aligned_probes_pvalue_lt_0p01` (5 probes within 20° detected),
  `test_resultant_vector_antipodal_probes_R_zero`,
  `test_pairwise_separations_cmb_catwise_literature_ge_28deg` (Secrest+2020),
  `test_to_mio_certificate_has_no_posterior_field`.
  Generates artefact `mio_directional_coherence_v1.json`.

### Day 6 (Sat) — PR13AM re-export through MIO bridges

**MIO-BRIDGES-01** (plan §12.5). `bass_py/mio/bridges/__init__.py` does
`from htt.PR13AM_te_sign_d1d3_bridge import *  # noqa` (option A —
semantic re-export, no file move, preserves existing import paths).
`test_pr13am_mio_ownership_tag` already exists (W5D5); add integration
test confirming both import paths coexist.

- Commit tag: `W6D6: mio bridges PR13AM re-export`
- Gate: existing PR13AM tests unchanged; new integration test for dual
  import path.

### Day 7 (Sun) — Masked-sky caveats

**MIO-HJ-05a-lite** (plan §12.6). `bass_py/mio/diagnostics/masked_sky_caveats.py`
(~250 L) with `SkyCoverageReport` frozen dataclass + `build_report(mask_pix,
nside, zoa_cfg, provenance)` + `as_caveats_list(report)` for
`MioCertificate.domain_caveats` consumption.

- Commit tag: `W6D7: mio masked_sky_caveats`
- Gate: 2 tests — `test_f_sky_consistency`, `test_zoa_applied_then_f_sky_less_than_one`.

### Week 6 final gate (plan §21)

- [ ] `import bass_py.mio` succeeds.
- [ ] HJ-02a 5 tests green + `mio_directional_coherence_v1.json` artefact
      produced.
- [ ] `test_figures_smoke.py` MIO-skip count 2 → 0 (`bounds`-related 2
      skips remain, deferred to Week 8).
- [ ] `MioCertificate.as_posterior_bundle()` raises `NotImplementedError`
      end-to-end through the new generator.
- [ ] Phase-boundary audit written to
      `docs/audits/AUDIT_PHASE_IND_TRACKS_W6_YYYY-MM-DD.md`.

### Deferred to Week 7+ (not Week-6 targets but part of this lane)

- **TSC-03 / TSC-05 / TSC-06** — Week 7 (plan §21). Plan sections §3.3 /
  §4.2 / §4.3.
- **CONTRACTS-02** G19 cross-check protocol docs — Week 7.
- **W4 F4** Θ⁴ bridge htt audit tightening — Week 7 (combine with
  TSC-03/05/06).
- **W4 F1** mock coverage sandwich — opportunistic in Week 7–8 when
  `C_pix` non-uniform support is needed.
- **MANU-CH11-REDESIGN + MANU-CH12-NEW §12.0/12.2/12.6/12.7 drafts** —
  Week 8.
- **HTT-STAB final** — Week 8 (2 `bounds`-related + 5
  `/mnt/user-data`-pipeline-data figure skips — the latter is the
  SKIP-05-LATENT carry-forward from the W5 audit).
- **DOS-A13 remaining 12 models** — Week 9.
- **APPLY-BIAS-AMP refinement** (W5 audit carry-forward) — opportunistic
  when `ChannelSummary` gains a velocity-amplitude field.

## §3. Carry-forward items from W1–W5 audits + 2026-04-19 inspection

Recorded here per audit R2 so the next session doesn't rediscover them.
Severity legend: **P0** = Day-1 blocker, **P1** = Week-6 target, **P2** = later
week, **P3** = out-of-lane. W5 additions at the bottom.

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
| INSPECT-19 SKIP-02b | P1 | 2 figure skips with `No module named 'mio'`. | **Week 6 Day 1 target** — auto-resolves when MIO-BOOT-01 lands. FIG-MIO-SKIP-GATE verifies the cascade. |
| INSPECT-19 SKIP-02c | — | **RESOLVED W5D5** — HTT-OBS-FIXTURE landed `bass_py/workspace/data/obs_defaults.json` with v3 §9.2 SSOT constants + `dipole_observations` block. | No further action. |
| INSPECT-19 PLACEHOLDER-01 | — | **RESOLVED W5D6** — PR13AH-v2-WIRE added `mock_bias_correction` kwarg + `_apply_bias_to_direction`. When bias supplied, `calibration_pending=False`. | No further action. |
| INSPECT-19 SEMANTIC-01 | — | **RESOLVED W5D5** — PR13AM-MIO-TAG added `__mio_owned__`, `__mio_rationale__`, `_mio_artifact_name`. | No further action. |
| INSPECT-19 AMBIG-01 | — | **RESOLVED W5D7** — LEGACY-README banner prepended; original body preserved. | No further action. |
| PATCH-05 | P3 | `src/common/contracts.py` `PreferredAxis` v3 extra fields — v1.1 §10.2 marked optional. | Defer; current field set is sufficient. Revisit only if a downstream consumer demands richer provenance. |
| W5 SKIP-05-LATENT | P2 | 5 `test_figures_smoke.py` skips on `/mnt/user-data/outputs/<fname>.json/npz` (`FLRW_tilt_results.json`, `IS06_3D_posterior.npz` ×2, `robustness_sweeps_integrated.json` ×2, `fig_colin_beta.png`). Latent issue surfaced by HTT-FIG-SHIM. | Week 8 HTT-STAB — ship synthetic fixture stubs at `bass_py/workspace/pipeline_outputs/` + honour `HTT_PIPELINE_OUTDIR` env var. |
| W5 DYNESTY-DEP | P2 | 1 skip in `fig_MES_three_bounds.py` on `No module named 'dynesty'`. | `venv/bin/pip install dynesty` at the next convenient window. |
| W5 APPLY-BIAS-AMP | P2 | `_apply_bias_to_direction` scales by `\|V_true\|` not measurement amplitude because `ChannelSummary` has no velocity amplitude field yet. | Opportunistic during Week 7–8 when the amplitude field is introduced; update helper to use `amp_meas * u_hat`. |

## §4. Environment and quickstart

```bash
# Repo root
cd /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot

# Sanity: touched-surface test run.  As of 2026-04-19 post-W5:
# 839 passed, 0 failed, 8 skipped (RED-01 cleared by WS-BOOT-01).
venv/bin/pytest bass_py/htt/tests/ bass_py/src/ \
                bass_py/tsc/admissibility/ \
                bass_py/tsc/diagnostics/ bass_py/tsc/charts/ \
                bass_py/workspace/

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
* `bass_py/mio/*` — new MIO package (Week 6). Distinct from `legacy/mio/`
  which is the v2 "certification engine" era snapshot (read-only, banner
  added in Week 5 Day 7).
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
