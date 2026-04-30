# Claim Ledger

**Status**: maintained by hand; updated whenever a claim's tier changes (PA-11).
**Last updated**: 2026-04-29 (R17-P3 audit closure cycle).

This is the single source of truth for *what is currently provable from the code* vs *what is documented*. Every headline claim in `README.md` / `CLAUDE.md` / `docs/manuscript/` must map to a row here, and every row must cite either a passing test (file:line) or the explicit gate that blocks it.

A claim is **allowed** only if its row is `gate_status: open` AND the `evidence_path` resolves to a passing assertion.

---

## Schema

| Field | Meaning |
|---|---|
| `claim_id` | Stable handle (e.g. `D2_ANCHOR_RUST`). |
| `claim_text` | One-line claim as it appears in headline docs. |
| `tier` | `production` / `research_goal` / `interface_only` / `restricted_envelope`. |
| `path` | `python_pstf` / `rust_mb95` / `dual_track`. |
| `gate_status` | `open` / `closed_xfail` / `closed_envelope`. |
| `evidence_path` | File path + assertion that locks the claim (or the explicit gate that blocks it). |
| `notes` | Provenance, related PR, audit reference. |

---

## Solver-readiness claims

| claim_id | claim_text | tier | path | gate_status | evidence_path | notes |
|---|---|---|---|:---:|---|---|
| `PSTF_TETRAD_LOWELL` | "1+3 covariant PSTF / tetrad low-ℓ E-B solver, ver2 native integrator is the production owner" | production | python_pstf | open | `htt/bass/hierarchy/ver2_native_integrator.py:1-15` + `test_integrator.py` | T1 + T7-9 + collision K wired; T2/T3 (gradient ∇̃) and T4/T5/T6 (accel/vorticity) default-off (`hierarchy_rhs.py:377-380`). Mode-mixing A_mix unit-tested but not in production RHS. |
| `EXACT_THOMSON_PROD` | "exact electron-frame Thomson scattering on the production code path" | production | python_pstf | open | `htt/bass/collision/electron_frame.py:139-160,192-299` + `test_ver3_exact_thomson.py` | Boost-to-electron-frame → classical Thomson → boost-back; tilted Layer-B wired when β≠0. |
| `TILT_BOOST_SEPARATION` | "type-level separation of orthogonal / globally-tilted / observer-boost layers" | production | dual_track | open | `htt/bass/observer/composition.py:22-31,72-76` + `test_codazzi_tilt_rhs.py:TestFLRWLimit` + `test_beta_to_orthogonal_continuity.py` | `GlobalTiltState` ≠ `ObserverBoost`; `TypeError` on cross-coercion; β→0 continuity pinned by PA-4. |
| `INFERENCE_ENVELOPE` | "inference layer hard-stops requests outside the supported envelope before any solver call" | production | python_pstf | open | `htt/bass/inference/envelope.py:enforce_inference_envelope` + `test_envelope.py` (35 tests) | PA-12: `EnvelopeError` raised at CLI entry; covers dataset-kind, target families, headline-science opt-in, surrogate opt-in. |
| `FITTING_GATE_LADDER` | "validation gate enforces FittingBlockedError before any posterior call" | production | python_pstf | open | `htt/bass/validation/ver3_gate_stop.py:21-37,264-294` + `inference/live_binding.py:48-63,213-236` | 14 gates required; surrogate Planck likelihood currently keeps the ladder closed. |
| `OUTPUT_SPLIT_NON_LEAKAGE` | "deterministic / stochastic / boost archive components are non-leakable" | production | python_pstf | open | `htt/bass/forward/test_output_split_non_leakage.py` (7 tests) | PA-10: per-component metadata-kind locked; cross-channel non-leakage pinned at byte-equality. |
| `RUNTIME_CONSTRAINT_REPORTER` | "Codazzi / Gauss / Bianchi residuals reported per η-checkpoint with threshold flags" | production | python_pstf | open | `htt/bass/background/runtime_constraint_reporter.py` + `test_runtime_constraint_reporter.py` (11 tests) | PA-6: non-destructive observer; sidecar JSON for archive. |
| `OPTIMIZATION_FAIRNESS_PROD_CUTOFF` | "parallel/sequential bit-identity at production cutoff L_max=8" | production | python_pstf | open | `htt/bass/runtime/test_optimization_fairness.py::test_parallel_matches_sequential_at_production_cutoff` | PA-7: tightened from L_max=4 to L_max=8 with rtol=1e-12. |
| `LMAX_CONVERGENCE_PYTHON` | "Python PSTF pipeline shows monotone L_max convergence at L ∈ {4,6,8}" | production | python_pstf | open | `htt/bass/runtime/test_optimization_fairness.py::test_python_pipeline_lmax_convergence` | PA-3: locks the convergence pattern; does not lock the absolute D_2 value. |

## Family coverage claims

| claim_id | claim_text | tier | path | gate_status | evidence_path | notes |
|---|---|---|---|:---:|---|---|
| `FAMILIES_REGISTRY_11` | "all 11 Bianchi types registered; shear sources validated for all 11" | production | python_pstf | open | `htt/bass/background/bianchi_types.py:508-729` + `test_bianchi_types.py` + `transport/shear_sources.py` | `STRONG_FAMILIES` and `TEMPLATE_CARD_FAMILIES` are disjoint; full union of 11. |
| `FAMILIES_FULL_MODE_4` | "full-mode end-to-end LoS coverage for FLRW, I, V, IX" | production | python_pstf | open | `htt/bass/los/family_propagators/` + `los/families/` + `integration/test_full_bianchi_coverage.py` | `STRONG_FAMILIES = {FLRW, I, V, IX}` (`hierarchy/seed_factory.py:66`). |
| `FAMILIES_RESTRICTED_8` | "II, III, IV, VI₀, VI_h, VII₀, VII_h, VIII restricted to axis-aligned mode subsets" | restricted_envelope | python_pstf | closed_envelope | `htt/bass/hierarchy/nabla_dispatch.py` raises `NotImplementedError('FB-5.2')` off-axis; `inference/envelope.py` requires `allow_template_card=True` | These families have template-card IC only; off-axis modes are deferred research. |

## Numerical-maturity claims

| claim_id | claim_text | tier | path | gate_status | evidence_path | notes |
|---|---|---|---|:---:|---|---|
| `LSODA_COSMOLOGICAL_RANGE` | "LSODA stable across η ∈ [261, 14147] Mpc" | production | python_pstf | open | `htt/bass/runtime/test_cosmological_config.py:80-102` + `runtime/test_end_to_end_wiring.py:55-88` | Round-15 P0 + 8-patch IMEX algebraic audit. |
| `TCA_SWITCH_SMOOTH` | "TCA on/off switch is smooth; Γ_T·Θ_2 invariant" | production | python_pstf | open | `htt/bass/hierarchy/test_tca_switch_smoothness.py:78-154` (rtol=1e-12) | Inline DAE relaxation, not a pre-phase. |
| `LOS_GRID_DECOUPLED` | "LoS quadrature grid decoupled from IMEX η-grid" | production | python_pstf | open | `htt/bass/los/los_grid_builder.py:55-80` + `test_los_grid_builder.py` | Round-15 P0 fix; median ratio 8.3 → 1.0, max 3687 → 266. |
| `FLRW_LIMIT_BIT_EXACT` | "σ → 0 limit recovers FLRW propagator bit-exactly" | production | python_pstf | open | `htt/bass/los/test_bianchi_propagator.py::TestFLRWRecovery::test_recovery_at_sigma_zero_bit_exact` (T_rel == 0.0, E_rel == 0.0) | Existing armor; PA-4 supplements with β→0 continuity. |
| `BETA_TO_ORTHOGONAL_CONTINUITY` | "tilted-branch trajectory converges smoothly to orthogonal as β → 0" | production | python_pstf | open | `htt/bass/background/test_beta_to_orthogonal_continuity.py` (10 tests) | PA-4: Σ²(η) gap shrinks; Ω_tilt ∝ β² scaling; Friedmann budget bounded. |

## D_2 anchor claim

| claim_id | claim_text | tier | path | gate_status | evidence_path | notes |
|---|---|---|---|:---:|---|---|
| `D2_ANCHOR_RUST` | "D_2 = 1002.086744 μK² bit-identical for the FLRW limit" | production | rust_mb95 | open | `bass_rs dump_dl_spectrum_sparse` (Rust binary) + `htt/bass/validation/_d2_anchor_golden.json` | Rust MB-95 path; 14-commit anchor. **NOT** the Python PSTF path. |
| `D2_PYTHON_PSTF` | "Python PSTF FLRW pipeline reproduces D_2 = 1002.086744 μK² bit-identically" | research_goal | python_pstf | closed_xfail | `htt/bass/spectrum/test_d2_pstf_closure.py` (`xfail("PR-024c open")`) + progressive-closure tracker | Currently in `ten_orders` closure tier (rel_gap ≈ 6.4×10⁹). PA-1: progressive-closure tracker (`test_d2_pstf_progressive_closure.py`) catches drift even before strict closure. |
| `ROUTE_B_MM_CURVE` | "Route-B Michaelis-Menten curve constants frozen" | production | python_pstf | open | `htt/bass/validation/test_d2_regression_anchor.py` (5 anchor tests) | C1, C2, sentinel constant bit-identical to golden JSON. |
| `CAMB_CROSS_CHECK` | "BASS Rust D_2 agrees with CAMB(τ=0) to within 1 %" | production | rust_mb95 | open | `htt/bass/validation/test_d2_regression_anchor.py::test_rust_flrw_reference_metadata_present` | Sanity band only; not a tolerance pin. |

## Headline-science claims (research goals)

| claim_id | claim_text | tier | path | gate_status | evidence_path | notes |
|---|---|---|---|:---:|---|---|
| `LN_B_FLRW_TILT_PLUS_26_40` | "ln B(FLRW_tilt) = +26.40" | research_goal | dual_track | closed_envelope | `inference/envelope.py:HEADLINE_SCIENCE_FORBIDDEN_KEYS` blocks unless `allow_research_goal_only=True` | No production code path emits this number. README.md will be updated. |
| `BETA_1P36_EM3` | "β = 1.360×10⁻³" | research_goal | dual_track | closed_envelope | same | Diagnostic value only; no fitting gate. |
| `F_BAYES_0P093` | "F_Bayes = 0.093 ± 0.025" | research_goal | dual_track | closed_envelope | same | No F_Bayes pipeline in code. |
| `PLANCK_2018_FIT` | "fits Planck 2018 data" | research_goal | python_pstf | closed_envelope | `htt/bass/likelihood/planck2018_flrw_match.py:39-40` raises `SurrogatePlanckValidationError` | No real `clik` wrapper; surrogate validator only. |

## Optimization claims

| claim_id | claim_text | tier | path | gate_status | evidence_path | notes |
|---|---|---|---|:---:|---|---|
| `PATTERN_CACHE_BIT_IDENTICAL` | "Tier 1A v2 pattern-cache preserves D_2 bit-identically" | production | rust_mb95+python_pstf | open | `CHANGELOG.md` "V5 Round-17 P3.5 Tier 1A v2"; smoke V0d D_2 = 5.850968e+03 pre/post | Bit-identical at smoke V0d only; production-cutoff bit-identity now also enforced by `test_optimization_fairness.py::test_parallel_matches_sequential_at_production_cutoff` (PA-7). |
| `PARALLEL_19X_SPEEDUP` | "1.9× cumulative parallel speedup at the 4-worker baseline" | production | python_pstf | open | CHANGELOG.md + `test_optimization_fairness.py::test_parallel_matches_sequential_*` | Same-physics fairness pinned at L_max=4 and L_max=8. |

---

## Audit metadata

The H2 verdict from the R17-P3 adversarial audit (`/home/cosmosapjw/Dropbox/bianchi/htt_base` cycle 2026-04-29) classifies the codebase as "strong exploratory solver / serious low-ℓ package with major revision needed". The PA-1 / PA-3..7 / PA-10..12 patches (this cycle) close the *enforcement* and *regression armor* gap. The remaining research-level work — Python D_2 closure (PR-024c), real Planck `clik` wrapper, off-axis Bianchi modes, full PSTF nine-term hierarchy — is tracked in CLAUDE.md §3 and is intentionally outside this cycle's scope.
