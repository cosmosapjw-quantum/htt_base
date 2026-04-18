# Phase-boundary audit — Independent Tracks Week 5

**Phase tag**: `IND_TRACKS_W5`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.2 §21 Week 5 day-by-day schedule
— WS-BOOT-01 (Day 1), CONTRACTS-01 (Day 2), G19-ENFORCE-01 (Day 3),
REG-02 + HTT-FIG-SHIM (Day 4), PR13AM-MIO-TAG + HTT-OBS-FIXTURE (Day 5),
PR13AH-v2-WIRE (Day 6), LEGACY-README + DOS-A30-MIO drafts (Day 7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**: v3 §4.5.2 / §4.5.2.1 / §4.5.4 (MioCertificate
+ G19), §10.2 / §10.2bis (interface table + enforcement), §12.2bis (MIO
first-line defences), §14.1 (artifact prefix), §6.3 (4-summary
integrity), §0.1bis (distributed epistemic ownership).
**Baseline head**: `e08e418` (prior independent-tracks phase
`IND_TRACKS_W4: land COMMON-D/E/F + TSC-02 + TSC-04 + DOS-A14`).
**Commits this phase**: `3e96075` (W5D1), `19c3ec6` (W5D2), `f97f056`
(W5D3), `5a012cf` (W5D4), `491f9f5` (W5D5), `6e4a690` (W5D6), `974fb4d`
(W5D7). LB-6 (`fd66a3f`) and IMEX-00/01 (`cc35fbd`, `661044d`) landed
on the bass-side lane in between and are not part of this audit.
**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/ bass_py/tsc/charts/
bass_py/workspace/` → **839 passed, 0 failed, 8 skipped**. `htt/tests/`
alone: **201 passed, 0 failed, 8 skipped** (from 181 / 23 in W4). The
W5 delta is +20 tests and RED-01 cleared.

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Physics/math | MIO is an observatory, not a certification engine — its outputs are diagnostic reports, not posteriors | `workspace/contracts/mio_certificate.py` `MioCertificate` + `as_posterior_bundle` NotImplementedError | Parent plan v3 §4.5.2.1 verbatim |
| Physics/math | Four cross-package frozen contracts (`PosteriorExportBundle`, `MioCertificate`, `HttForwardOutput`, `AtlasEntry`) anchor the HTT↔MIO↔BASS boundary | `workspace/contracts/*` 4 files | Parent plan v3 §10.2 table |
| Physics/math | MIO-owned semantic tag `__mio_owned__` on `PR13AM_te_sign_d1d3_bridge` | `bass_py/htt/htt/PR13AM_te_sign_d1d3_bridge.py` module globals | Parent plan v3 §1.4.1 + §12.2bis |
| Physics/math | Mock-calibrated channel in PR13AH's 4-summary is no longer a placeholder when a COMMON-F `InjectedMockReport` is supplied | `htt/htt/PR13AH_observables_reintegration.py` `reintegrate_observables(..., mock_bias_correction=...)` + `_apply_bias_to_direction` | Parent plan v3 §6.3 + INDEPENDENT_TRACKS_PLAN v1.2 §19.4 |
| Physics/math | Direction de-bias = subtract `(E[V_hat] - V_true)` from `|V_true| * u_hat`, renormalise | `_apply_bias_to_direction` | Parent plan §6.7 + §6.3; extension of `common.mock_calibration.apply_bias_correction` |
| Physics/math | T_CMB SSOT fixture uses htt-side canonical `2.72548 K` (Fixsen 2009 central value), NOT bass-side legacy `2.7255 K` | `bass_py/workspace/data/obs_defaults.json` `T_CMB_K = 2.72548` | `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` F5 |
| Contracts | `as_posterior_bundle()` raises `NotImplementedError` on every `MioCertificate` instance | `test_miocertificate_no_posterior_access` (+ G19 suite duplicate) | v3 §10.2bis row 1 |
| Contracts | HTT likelihood entry points reject `MioCertificate` inputs | `test_g19_htt_cannot_ingest_miocertificate_as_likelihood` | v3 §10.2bis row 2 |
| Contracts | No `MioCertificate`-plus-HTT scalar-sum expression anywhere under `bass_py/{bass,htt/htt,mio,src/common,tsc,workspace}` | `test_g19_no_scalar_sum_of_mio_and_htt` (text-scan lint) | v3 §10.2bis row 3 |
| Contracts | MIO-owned modules produce artefact filenames beginning with `mio_` | `test_mio_artifact_filename_has_mio_prefix` (forward guard) | v3 §14.1 |
| Contracts | W1-W2 F3 `ModuleNotFoundError: No module named 'contracts'` extinct | `test_to_mio_builds_bundle` passes after WS-BOOT-01 | INDEPENDENT_TRACKS_PLAN §19.1 |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `PosteriorExportBundle` | 12 summary scalars + tuples + `model_evidences` dict + `is_cross_check_only=True` | frozen dataclass | ✓ frozen; `__post_init__` raises `ValueError` if `is_cross_check_only=False` |
| `MioCertificate` | 14 fields (report_type / probe_name / channel + diagnostic maps + caveats + provenance + optional cross-check hint) | frozen dataclass | ✓ frozen; `as_posterior_bundle` raises `NotImplementedError`; no `*posterior*` field (G19 schema token ban) |
| `HttForwardOutput` | model_name + bianchi_type + axis + ell grid + 3 C_ell vectors + directional_summary + shear/tilt amplitudes + atlas hashes + provenance | frozen dataclass | ✓ frozen; ell 1-D; C_ell shape == ell shape; b ∈ [−90°, 90°]; `shear_Sigma2 ≥ 0`; no `*posterior*` field |
| `AtlasEntry` | atlas_name + bianchi_type + parameter_point + ell + kernel_values + kernel_name + provenance + entry_hash + caveats | frozen dataclass | ✓ frozen; ell / kernel_values 1-D; shape match; `entry_hash` non-empty; no `*posterior*` field |
| `_mio_artifact_name(stem, version=1)` | str + int | str | ✓ prepends `mio_pr13am_` if absent; respects existing `mio_` prefix |
| `_apply_bias_to_direction(l_deg, b_deg, bias_report)` | floats + `InjectedMockReport` | `{l_deg, b_deg}` dict | ✓ no-op fallback when `V_true` absent / `amp_true = 0` / zero-norm correction; unit-vector via `common.sky_geometry.{lb_to_unitvec, unitvec_to_lb}` |
| `reintegrate_observables(..., mock_bias_correction=None)` | catalog + sky_config + optional `InjectedMockReport` | 4-summary dict | ✓ default `None` keeps W4 placeholder behaviour; supplied report flips `calibration_pending=False`, propagates `amp_bias_fraction`, `direction_bias_deg`, `n_mock` into `meta` |
| `build_posterior_bundle(results_path, model)` | JSON path + model name | `PosteriorExportBundle` | ✓ minimal fixture in `workspace/results/` makes the W1-W2 F3 regression gate pass |

## 3. Phys-math audit ledger

| Check | Verdict | Why |
|---|---|---|
| Definition / notation consistency across `MioCertificate` fields and v3 §4.5.2.1 | pass | Field names, types, and docstrings match v3 verbatim. |
| G19 three-rule consistency (no posterior, no truth, no merge) | pass | Class-level `NotImplementedError`, schema token ban, text-scan lint all present. |
| PR13AH 4-summary integrity (v3 §6.3) | pass | `calibration_pending=False` only when bias is supplied; `selection_aware_summary.calibration_pending` remains False by construction; placeholder path preserved under `None`. |
| Bias-correction residual orientation | **partial** | `_apply_bias_to_direction` scales the measured unit vector by `|V_true|` before subtracting the residual. This yields the right *direction* correction but assumes the measurement's amplitude equals the truth amplitude; PR13AH's `ChannelSummary` does not yet carry a velocity amplitude. Noted as P2-APPLY-BIAS. |
| T_CMB SSOT consistency | pass | `obs_defaults.json.T_CMB_K = 2.72548` matches `htt.core.ssot.C.T0_K`; bass-side 2.7255 noted in SSOT_TCMB_DRIFT audit as a separate carry-forward. |
| Distributed epistemic ownership (v3 §0.1bis) | pass | A39 table enumerates 18 domains, each with a single primary owner; no G19 merge paths introduced. |
| AtlasEntry / HttForwardOutput domain/range | pass | `b ∈ [−90°, 90°]`, `shear_Sigma2 ≥ 0`, non-empty entry_hash, shape consistency. |
| HTT-FIG-SHIM import path | pass | `htt/core/` prepend is additive only; does not pollute production imports (the module already lives at `htt.core.plot_style`); exposed latent figure-data-file skips (documented in §6). |

## 4. Equation-to-code mapping audit

| Claim | Implementing file | Notes |
|---|---|---|
| "MIO cannot generate posteriors" → `NotImplementedError` | `workspace/contracts/mio_certificate.py` `as_posterior_bundle` | Verbatim v3 §4.5.2.1. |
| "HTT likelihood cannot ingest MioCertificate" → TypeError | `test_g19_htt_cannot_ingest_miocertificate_as_likelihood` | Test-level: passes a `MioCertificate` into `LowellLikelihood.directional_log_likelihood`; fails with `TypeError`/`AttributeError`. No new runtime guard needed — duck typing suffices. |
| "MioCertificate + HTT lnB is forbidden" | `test_g19_no_scalar_sum_of_mio_and_htt` | Static regex scan across `bass_py/{bass,htt/htt,mio,src/common,tsc,workspace}` excluding tests. |
| "MIO artifact filename carries mio_ prefix" | `_mio_artifact_name` + `test_mio_artifact_filename_has_mio_prefix` | Forward guard: scans `bass_py/mio/**.py` (Week 6+) and `PR13AM_*.py` modules marked `__mio_owned__`. Today vacuous / trivially green. |
| "4-summary channel integrity" | `PR13AH_observables_reintegration.reintegrate_observables` | 4 channels unchanged in count; mock channel now has a non-placeholder path when bias is supplied. Existing 8 tests + 3 new tests green. |
| "Figures top-level import `plot_style` / `bounds`" | `htt/htt/figures/__init__.py` (+ figures/conftest.py sibling) | `__init__.py` prepend fires on figure-package import — necessary because conftest.py under `figures/` only runs when tests are collected under that dir; the smoke test lives under `htt/tests/` so the shim must be on the package. |
| "T_CMB SSOT at 2.72548" | `obs_defaults.json` + `htt.core.ssot.C.T0_K` | Consistent; bass-side drift is documented separately. |

## 5. Numerical / pipeline audit

| Check | Finding |
|---|---|
| Seeding / determinism | All new tests seed via `np.random.default_rng(0)` or `rng.default_rng(seed=0/42)`; `_injected_mock_report` builds a deterministic fixture by tiling `V_true + residual` n_mock times — `recovered_bias` sample-mean is exact. |
| save_fig output dir handling | Modified to (a) honour `HTT_FIG_OUTDIR` env var, (b) attempt `os.makedirs(exist_ok=True)`, (c) silently close on `OSError`. Production behaviour unchanged when `/mnt/user-data/outputs` is writable. |
| Underflow / overflow | `_apply_bias_to_direction` uses unit-vector renormalisation; zero-norm guard routes to the input direction. |
| State leakage across imports | `bass_py/conftest.py` prepends both `src/` (COMMON-A) and `./` (WS-BOOT-01) once per session, idempotent via `in sys.path` check. `figures/__init__.py` shim is also idempotent. |
| Pre-computed pipeline inputs | The fig smoke test now exposes 5 `/mnt/user-data` file-not-found skips (`FLRW_tilt_results.json`, `IS06_3D_posterior.npz` ×2, `robustness_sweeps_integrated.json` ×2, `fig_colin_beta.png`). These are latent — masked behind plot_style failure pre-shim. Deferred to Week 8 HTT-STAB. |

## 6. Ranked failure modes

| Tag | Type | Severity | Symptom | Root cause | Cheapest test | Mis-interpretation risk |
|---|---|---|---|---|---|---|
| **SKIP-05-LATENT** | interface/testing | P2 | 5 skips in `test_figures_smoke.py` tied to `/mnt/user-data/outputs/<fname>.json/npz` | Figure scripts expect HTT pipeline inputs that are not in the repo. Pre-shim these were hidden behind `plot_style` ImportError. | Generate fixture stubs at `bass_py/workspace/pipeline_outputs/` + honour `HTT_PIPELINE_OUTDIR` env var. | Low — skip behaviour is honest; do NOT confuse with a regression. |
| **DYNESTY-DEP** | environment | P2 | 1 skip in `fig_MES_three_bounds.py` on `ModuleNotFoundError: No module named 'dynesty'` | `dynesty` is not installed in the venv; lazy-imported by `htt.core.analysis_extended`. | `venv/bin/pip install dynesty` + re-run. | Low. |
| **APPLY-BIAS-AMP** | implementation | P2 | `_apply_bias_to_direction` scales by `|V_true|` not the measurement amplitude | PR13AH's `ChannelSummary` does not carry a velocity amplitude; only `resultant_R ∈ [0,1]`. | When `ChannelSummary` gains an amplitude field, update the helper to use `amp_meas * u_hat`. | Medium — mis-reading this as an amplitude de-bias would be wrong; the helper only corrects the *direction*. |
| **SCHEMA-HASH-DOC** | doc | P3 | `test_miocertificate_schema_frozen` docstring mentions a "digest" but the assertion is a field-name set comparison | Implementation simplification; set comparison is equivalent but the docstring is stale. | Update docstring. | Low. |
| **LEGACY-BANNER-MD** | doc | P3 | Markdownlint `MD041` warning on first-line heading | Intentional blockquote first line per plan §19.6 spec. | Add `<!-- markdownlint-disable MD041 -->` hint. | Low. |
| **FIG-DATA-FIXTURES** | infra | P3 | 6 figures still skip on pipeline-input-file absence | Same root as SKIP-05-LATENT but split into individual fixtures. | Ship synthetic fixture stubs. | Low. |

No P0 / P1 findings in Week 5.

## 7. Verifier results

| Verifier | Verdict | Evidence |
|---|---|---|
| A. Physics verifier | **passed (with one partial)** | Known-limit recovery: `_apply_bias_to_direction` returns input unchanged when `config['V_true']` is absent or zero-amplitude. G19 three rules encoded verbatim. One partial: bias-amp-coupling (P2-APPLY-BIAS-AMP). |
| B. Code verifier | **passed** | 839 passed / 0 failed / 8 skipped on the touched-surface run. 22 new contract tests + 3 PR13AH tests + 2 PR13AM tests + 0 regressions. |
| C. Numerical verifier | **passed** | Deterministic seeds; OSError-tolerant save_fig; zero-norm guards on unit-vector conversions. |

## 8. Minimal repair plan

| # | Patch | Why load-bearing | Failure mode prevented | New test | Baseline / regression impact |
|---|---|---|---|---|---|
| 1 | *Deferred to Week 8 HTT-STAB* — ship synthetic stub fixtures at `bass_py/workspace/pipeline_outputs/` with schema matching `FLRW_tilt_results.json`, `IS06_3D_posterior.npz`, `robustness_sweeps_integrated.json`. | Drops 5 SKIP-05-LATENT skips without touching production code. | SKIP-05-LATENT | One fixture-presence test per pipeline file. | Zero impact — smoke test skip behaviour already correctly handles absence. |
| 2 | *Deferred to Week 6 MIO-BOOT-01* — register `bass_py.mio` package so the 2 `mio` smoke-test skips auto-clear (FIG-MIO-SKIP-GATE). | Cascade-resolves INSPECT-19 SKIP-02b. | (plan §19.7) | `test_figures_mio_skip_should_activate_after_mio_boot`. | Zero impact on current lane. |
| 3 | *Later refinement* — when `ChannelSummary` gains a velocity-amplitude field, rewrite `_apply_bias_to_direction` to use `amp_meas * u_hat` instead of `amp_true * u_hat`. | Tightens the direction de-bias to the full bias-vector correction. | APPLY-BIAS-AMP | `test_apply_bias_uses_measured_amplitude`. | Backwards-compatible: existing test fixtures use `|V_true|` as the amplitude, so they remain valid until the amplitude field is added. |

## 9. Minimal test set (for any future cross-check run)

1. **Baseline reproduction** —
   `pytest bass_py/workspace/contracts/tests/test_mio_certificate.py::test_miocertificate_no_posterior_access`
   must pass; regression anchor for G19 rule 1.
2. **Edge / adversarial** —
   `pytest bass_py/workspace/contracts/tests/test_htt_to_mio_roundtrip.py::test_cross_check_only_enforced`
   must pass; enforces `is_cross_check_only=False` → `ValueError`.
3. **Physics sanity** —
   `pytest bass_py/htt/tests/test_PR13AH.py::test_mock_calibration_direction_shift_matches_bias`
   must pass; asserts residual-opposing direction shift.
4. **Numerical stability** —
   `pytest bass_py/htt/tests/test_figures_smoke.py -q`
   must report skip classes only in {`mio`, `/mnt/user-data`, `dynesty`}; any other skip class is a regression.
5. **Regression** —
   `pytest bass_py/htt/tests/test_integration.py::TestHTTIntegrationAdapters::test_to_mio_builds_bundle`
   must pass; RED-01 anchor.

## 10. 최종 판정

**통과 (phase complete, no P0/P1 findings).** Week 5 gate summary:

- ✅ RED-01 resolved (`test_to_mio_builds_bundle` passes).
- ✅ SKIP-17 plot_style skips → 0.
- ✅ SKIP-02a bounds skips → 0 (earlier than the plan's Week-8 target).
- ✅ SKIP-02c `obs_defaults.json not found` → 0.
- ✅ PLACEHOLDER-01 (PR13AH mock calibration) extinct.
- ✅ SEMANTIC-01 (PR13AM MIO tag) extinct.
- ✅ AMBIG-01 (legacy README banner) extinct.
- ✅ CONTRACTS-01 — 17 contract tests green (5 beyond the plan's 4-test minimum).
- ✅ G19-ENFORCE-01 — 5 enforcement tests green (2 beyond the plan's 3-test minimum).
- ✅ v1.1 PATCH-01 / 02 / 03 / 04 all extinct.
- ⚠️ Skip count 8 in `htt/tests/` vs plan's ≤4 target. Delta = 4 latent fig-data / dep skips that were masked pre-shim and are now honestly reported. No new code regression.

**지금 당장 구현 / 수정할 1개**: nothing — all P0/P1 remediations in-phase. The one outstanding substantive refinement (APPLY-BIAS-AMP) is P2 and waits for the upstream ChannelSummary amplitude field.

**지금 손대면 안 되는 1개**: the `_apply_bias_to_direction` helper's amplitude scaling. Touching it before ChannelSummary grows an amplitude field would introduce a half-measure that breaks the deterministic direction-correction semantics.

---

## Physics-gallery regeneration (memory rule `feedback_phase_boundary_gallery.md`)

**No-op phase**. Week 5 lands only Python interface contracts
(`workspace/contracts/`), test shims (`figures/__init__.py` sys.path
prepend + `save_fig` OSError fallback), observational fixtures
(`obs_defaults.json`, `integrated_pipeline_results.json`), a PR13AH
wiring patch, and manuscript / dossier documentation. No new forward
solver, no new PSTF primary outputs, no new spectrum regressions — so
`plots/physics_gallery/` has nothing to extend or regenerate this
phase. The gallery remains at the IND_TRACKS_W4 / LB-6 state.

## Commits applied in this audit pass

None. No P0/P1 findings require in-session `AUDIT(IND_TRACKS_W5):` commits.

## Outstanding carry-forwards (P2/P3)

| Tag | Destination |
|---|---|
| SKIP-05-LATENT (5 fig-data skips) | Week 8 HTT-STAB (plan §16.2 / §21 Week 8). |
| DYNESTY-DEP | Environment note; `pip install dynesty` at the next convenient window. |
| APPLY-BIAS-AMP | Queue for the ChannelSummary-amplitude enlargement (no scheduled week yet — opportunistic during Week 7-8 manuscript cycle). |
| SCHEMA-HASH-DOC | One-line docstring touch-up; defer. |
| LEGACY-BANNER-MD | Cosmetic markdownlint warning; defer. |
| FIG-DATA-FIXTURES | Subsumed by SKIP-05-LATENT. |
