# Independent Tracks — next-session resumption prompt

**As of**: 2026-04-19, post-`IND_TRACKS_W3` phase.
**Last audited**: 2026-04-19 (`docs/audits/AUDIT_PHASE_IND_TRACKS_W3_2026-04-19.md`;
previous phase: `AUDIT_PHASE_IND_TRACKS_W1W2_2026-04-19.md`).
**Governing plan**: `INDEPENDENT_TRACKS_PLAN.md` (Week 4 routine, §6 steps 13–15).
**Parent plan**: `BASS_PY_HTT_TSC_RESEARCH_PLAN.md` v2.

---

## §0. How to use this file

Open a **fresh** Claude Code session in this repository and paste or point
the agent at this file. It is designed to be self-contained — the agent does
not need to re-read `INDEPENDENT_TRACKS_PLAN.md` end-to-end, only the
specific sections referenced below.

First-order rules (copy-pasted from the governing plan):

* **additive commits only** (memory `feedback_git_workflow.md` — no branch
  rewrite; Python + Rust share one repo).
* **do not touch `bass_py/bass/*`** — that is the bass_py session's lane.
* **do not touch `plots/physics_gallery/`** — bass_py session auto-manages
  per-phase gallery regeneration (`feedback_phase_boundary_gallery.md`).
* **self-trigger `docs/audits/AUDIT_PROMPT.md`** before any phase-complete
  commit. P0/P1 must be fixed in-session with `AUDIT(<tag>):` prefix.

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

Final test tally over the touched surface: **305 passed, 1 pre-existing
failure (F3 carry-forward), 23 cleanly-skipped**
(`bass_py/htt/tests/ bass_py/src/ bass_py/tsc/admissibility/`).
Full `bass_py/tsc/` also green at **443 passed**.

## §2. Active priorities for the next session (Week 4)

Order suggested. Each entry includes the plan reference; read only that
slice of the plan rather than the whole file.

1. **COMMON-D → COMMON-E → COMMON-F** sequential (§3.1).
   COMMON-F is the largest (~300 L) and blocks the `calibration_pending=True`
   flag currently set on `PR13AH_observables_reintegration.ChannelSummary`'s
   mock_calibrated slot.

2. **TSC-02** — `bass_py/tsc/diagnostics/filling_fraction.py` (§3.2).
   F_Bayes = E[Q | D] posterior-mean; ~400 L + ~30 tests.

3. **DOS-A14** — 5 null-family derivations (§4.4).

4. **MANU-CH03 §3.X+3 Θ⁴ bridge** (unblocks once TSC-04 lands — audit W3 F4).

## §3. Carry-forward items from the W1-W2 audit

Recorded here per audit R2 so the next session doesn't rediscover them.

| Tag | Severity | Description | Where to act |
|---|---|---|---|
| F2 | P2 | Two copies of `PreferredAxis` (htt.PR13AJ and common.contracts). Intended — collapsed later. | When COMMON-F lands, expose `htt.PreferredAxis = common.contracts.PreferredAxis` alias and remove the htt-local copy. Add a one-line import-equivalence test. |
| F3 | P1 | Pre-existing `test_to_mio_builds_bundle` failure — `ModuleNotFoundError: No module named 'contracts'`. Not introduced by W1-2 work. | Either provide a minimal `workspace/contracts/htt_to_mio.py` stub or mark the test as `pytest.importorskip("contracts")`. Treat as a dedicated commit under its own track label. |
| F5 | P2 | `htt.core.ssot.C.T0_uK = 2.7255e6` inconsistent with `T0_K = 2.72548`. | Change `T0_uK = C.T0_K * 1e6`, then run the `eps_ell` / `D_ell_from_eps` numerical regression sweep. Commit-side test: remove or invert `test_tcmb_ssot_drift_documented` so the fix is asserted, not the drift. |
| F6 | P3 | `bass.observational.planck_mes_bounds.T_CMB_K = 2.7255` drifts from canonical Fixsen value. | **Bass-side**, not to be touched in this independent-tracks lane. When bass_py session is quiescent, coordinate a bass-side `T_CMB_K → 2.72548` commit with D_2 anchor re-calibration. Wire via `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md`. |

All four are tracked — do not re-audit them before landing the tracked fix.

## §4. Environment and quickstart

```bash
# Repo root
cd /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot

# Sanity: touched-surface test run (should be 264 passed, 1 pre-existing
# fail, 23 skipped as of 2026-04-19).
venv/bin/pytest bass_py/htt/tests/ bass_py/src/ bass_py/tsc/admissibility/

# Full monorepo suite (slower; tsc alone is ~18 s).
venv/bin/pytest bass_py/
```

Path notes:

* `bass_py/src/common/` is importable via `bass_py/conftest.py` (which
  prepends `src/` to sys.path) and via `bass_py/pyproject.toml` (which
  adds `src/` to the setuptools package-find).
* `htt` is its own editable install (`bass_py/htt/setup.py`). If the
  next session fails to import `htt.core.ssot`, verify
  `venv/bin/pip install -e bass_py/htt/` has run in this venv.

## §5. Non-scope for this lane

To avoid rediscovery, the following are explicitly the bass_py session's
responsibility and must not be touched here:

* `bass_py/bass/hierarchy/*` (LB-2a / LB-2b PSTF work; `hierarchy_rhs.py`,
  `test_hierarchy_rhs.py` are currently uncommitted in the working tree).
* W10-02 CAMB V-gate, W11-01/02/03, W12-01/02, W13-01/02, W14-01 — parent
  plan §7.
* `plots/physics_gallery/` — gallery refresh is bass_py's per-phase rule.

If either lane is tempted to touch the other's area, stop and ask the user
first.
