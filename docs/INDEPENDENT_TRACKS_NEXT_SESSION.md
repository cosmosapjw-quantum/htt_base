# Independent Tracks — next-session resumption prompt

**As of**: 2026-04-19, post-`IND_TRACKS_W4` phase.
**Last audited**: 2026-04-19
(`docs/audits/AUDIT_PHASE_IND_TRACKS_W4_2026-04-19.md`;
prior phase `AUDIT_PHASE_IND_TRACKS_W3_2026-04-19.md`).
**Governing plan**: `INDEPENDENT_TRACKS_PLAN.md` (Week 4 routine
landed; Week 5+ routine below).
**Parent plan**: `BASS_PY_HTT_TSC_RESEARCH_PLAN.md` v2.

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
failure (F3 carry-forward), 23 cleanly-skipped**
(`bass_py/htt/tests/ bass_py/src/ bass_py/tsc/admissibility/
bass_py/tsc/diagnostics/ bass_py/tsc/charts/`).  W3 numbers (305
passed) were preserved identically; the +490 delta comes from 94 new
W4 tests landing in `bass_py/src/common/` + `bass_py/tsc/diagnostics/`
+ `bass_py/tsc/charts/` and from the `bass_py/tsc/` suite-extension
that follows TSC-02/TSC-04.

## §2. Active priorities for the next session (Week 5)

Order suggested.  Each entry includes the plan reference; read only
that slice of the plan rather than the whole file.

1. **TSC-03** — `tsc.diagnostics.three_bound_hierarchy` (§3.3).
   `B_σ > B_ω > B_u̇` check across 9 Bianchi types; cross-checks with
   `htt.core.bounds`. ~350 L + ~20 tests.

2. **TSC-06** — `tsc.integration.htt_bridge` (§4.3).
   Cross-validate `tsc.diagnostics.filling_fraction` (TSC-02, W4)
   against `htt.core.analysis_extended.FillingFraction` at `rel_err
   < 1 %`.  Also addresses audit W4 F2 (tsc ⇔ htt numerical
   equivalence).  ~150 L + `test_ff_consistency.py`.

3. **TSC-05** — `tsc.charts.michaelis_menten_export` (§4.2).
   Mirror Route B `C_1, C_2` SSOT with anti-regression test; target
   `D_2(Σ² = 1e-8) = 0.174112 μK²`.  ~200 L.

4. **F4 follow-up** — Θ⁴ bridge htt audit tightening.  Once htt lands
   a native `_a2_coefficient_table`, swap the FD extraction in
   `tsc.charts.theta4_bridge_verify._extract_htt_a2_coefficient`.
   Tracked as audit W4 F4.

5. **F1 / coverage sandwich** — widen
   `common.mock_calibration.run_zoa_null_mocks` to support a
   sandwich covariance or bootstrap covariance when `C_pix` is
   non-uniform.  Tracked as audit W4 F1.

## §3. Carry-forward items from W1–W4 audits

Recorded here per audit R2 so the next session doesn't rediscover them.

| Tag | Severity | Description | Where to act |
|---|---|---|---|
| W1-W2 F2 | P2 | Two copies of `PreferredAxis` (htt.PR13AJ and common.contracts).  Intended — collapsed later. | When htt starts consuming `common.contracts`, expose `htt.PreferredAxis = common.contracts.PreferredAxis` alias and remove the htt-local copy.  Add a one-line import-equivalence test. |
| W1-W2 F3 | P1 | Pre-existing `test_to_mio_builds_bundle` failure — `ModuleNotFoundError: No module named 'contracts'`.  Not introduced by W1-2 or W3 or W4 work. | Either provide a minimal `workspace/contracts/htt_to_mio.py` stub or mark the test as `pytest.importorskip("contracts")`.  Treat as a dedicated commit under its own track label. |
| W1-W2 F5 | P2 | `htt.core.ssot.C.T0_uK = 2.7255e6` inconsistent with `T0_K = 2.72548`. | Change `T0_uK = C.T0_K * 1e6`, then run the `eps_ell` / `D_ell_from_eps` numerical regression sweep.  Commit-side test: remove or invert `test_tcmb_ssot_drift_documented` so the fix is asserted, not the drift. |
| W1-W2 F6 | P3 | `bass.observational.planck_mes_bounds.T_CMB_K = 2.7255` drifts from canonical Fixsen value. | **Bass-side**, not to be touched in this independent-tracks lane.  When bass_py session is quiescent, coordinate a bass-side `T_CMB_K → 2.72548` commit with D_2 anchor re-calibration.  Wire via `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md`. |
| W3 F1 | P2 | Pixelization is an equal-area iso-latitude ring scheme, not HEALPix RING. | Swap `lb_to_pix` / `pixel_centers` / `nside_to_npix` for `healpy` backends when the project adopts healpy (parent plan §7.5). |
| W3 F4 | — | **RESOLVED** — `MANU-CH03 §3.X+3 Θ⁴ bridge` landed via W4 TSC-04 + manuscript subsection. | No further action. |
| W4 F1 | P2 | `run_zoa_null_mocks` coverage drifts outside [0.60, 0.76] when `C_pix` is non-uniform (sandwich cov needed). | Address in Week 5 priority #5. |
| W4 F2 | P2 | F_Bayes regression validated on Gaussian posterior; htt numerical equivalence not yet checked. | Address in Week 5 priority #2 (TSC-06). |
| W4 F4 | P2 | Θ⁴ bridge htt audit uses FD at `h = 1e-2` (`tol_htt = 5e-3`). | Address in Week 5 priority #4. |

## §4. Environment and quickstart

```bash
# Repo root
cd /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot

# Sanity: touched-surface test run.  As of 2026-04-19 post-W4:
# 795 passed, 1 pre-existing fail (F3 carry-forward), 23 skipped.
venv/bin/pytest bass_py/htt/tests/ bass_py/src/ \
                bass_py/tsc/admissibility/ \
                bass_py/tsc/diagnostics/ bass_py/tsc/charts/

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

* `bass_py/bass/hierarchy/*` (LB-2a / LB-2b PSTF work; `hierarchy_rhs.py`,
  `test_hierarchy_rhs.py` are currently uncommitted in the working tree).
* `bass_py/bass/collision/*` (N4/N5 PSTF collision + polarization —
  uncommitted in the working tree).
* W10-02 CAMB V-gate, W11-01/02/03, W12-01/02, W13-01/02, W14-01 — parent
  plan §7.
* `plots/physics_gallery/` — gallery refresh is bass_py's per-phase rule.

If either lane is tempted to touch the other's area, stop and ask the
user first.
