# V5 Gap-Closure — Next-Session Handoff

_Last updated 2026-04-24 end-of-session. Handoff baseline: 1366 passed, 1 skipped (6 new `multipole_cutoff` tests added since the previous baseline of 1360). FLRW D_2 Route-B bit-identity preserved._

> **2026-04-24 runtime-track CLOSED** — Blockers 1 and 2 both resolved within the session via two rounds of cross-session algebraic audit + 8 physics-level patches to `bass/hierarchy/ver3_layout_protocol.py`. λ_max(A_right) at machine precision (1e-16) across L_max ∈ {4,6,8,12,16} for both γ_T=0 and γ_T=1; cosmological η=261→14147 Mpc IMEX completes in 130 s (previously failed at η≈4740 Mpc). Blocker 3 (real-IC injection) is now actionable on a stable operator. See `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md` for full findings + remaining items (Round-3 source-block audit, `geom_scale` replacement, non-Type-I family law).

---

## What landed in the previous session

| Commit | Stage | Summary |
|--------|-------|---------|
| `dea07b8` | **S0** | D_2 Route-B MM-curve anchors + v5 verification-pack CI gate. Python-side bit-identity of `ROUTE_B_C1/C2` + MM curve points. CAMB τ=0 Planck-2018 cross-check documented (BASS 1002.086744 within 0.17% of CAMB). |
| `76b0299` | **S1** | `bass.statistics` single-surface module: canonical `chi_squared`, `chi_squared_by_mode`, `log_gaussian`, `ResidualPack`, `CovariancePack`, `merge_residual_packs`. `CosmologicalFrameLikelihood` refactored to call `chi_squared` — bit-identical to pre-refactor. |
| `5fdb547` | **S2** | `bass/transport/exact_transport.py` — unified Tier-A facade with FLRW early-return. `ExactTransportBundle`, `FamilyTransportKernel` Protocol, `build_exact_transport`, `register_family_kernel`, `list_registered_families`. Legacy `lowell_los` path stays bit-identical. |
| `8656d56` | **S3** | `bass/los/families/` module tree: `base.py` (LegacyDelegationKernel, NotImplementedKernel, FamilyMetadata), `type_i.py` real reference impl, 10 skeleton kernels (II–IX). `__init__.py` exposes `KNOWN_FAMILIES`, `IMPLEMENTED_FAMILIES`, `SKELETON_FAMILIES`, `register_all_defaults`, `unregister_all_defaults`. |
| `f3593c2` | **S4** | Wave A family numerics: **IX** (Wigner-D compact SU(2), Gauss-Legendre seed norm), **VI_0** (class-A solvable directional, piecewise-constant seed), **II** (nil-Heisenberg, Bessel J_0 finite-disc via scipy), **III** (class-B hyperbolic h=-1, Legendre P_2 on sinh²ξ measure). 72 new tests. |
| `221f6ab` | **S5** | Wave B family numerics: **VII_0** (helical Euclidean, spherical_jn), **V** (open hyperbolic, re-uses Type III hyperbolic seed), **VII_h** (helical open-h, h-dependent cutoff), **VI_h** (class-B negative-h twist), **IV** (solvable-group anisotropic, r·exp(-r/L) seed), **VIII** (SL(2,ℝ) discrete series via scipy lpmv on compactified disc). 90 new tests. |
| `741ceb6` | **S6** | `bass/los/families/residual_report.py` — `build_family_residual_packs`, `merge_family_residual_packs`, `default_family_residual_report`. `bass.validation.ver3_gate_stop.family_backend_gate_bundle_from_packs` aggregates per-family packs into a `family_backend_gate` `GateBundle`. `bass/forward/ver3_output_archive.py::write_family_residual_archive` sidecar writes `family_residuals.json`. LegacyDelegationKernel gains default `residual_pack_from_bundle`. |
| `ed9df36` | **S7** | Type VIII **continuous principal series** via lazy `mpmath.hyp2f1`. `principal_series_plancherel_weight(ν) = ν·tanh(πν)`, `continuous_principal_series_norm`, `continuous_series_l2_residual`. Translator now routes `("mu_sl2r", "continuous_principal", component)` → `m`-storage. Closes v5 plan Open-Question 1. |
| `85c2270` | **S8/S9 REVERT** | Removed `bass/spectrum/flrw_pipeline.py` and `test_flrw_pipeline.py`. The Sachs-Wolfe plateau approximation they shipped (`(Θ_0+Ψ)_* = -R/5`) is a toy MD analytic model, forbidden by the user's "no toy / no surrogate / no pretend-perturbation-as-nonperturbative" directive. The CAMB comparison is still the goal — but it must be driven by the real Tier-B hierarchy. |

**Key invariants preserved through all 9 commits:**
- `D_2 = 1002.086744 μK²` (Rust MB-95 oracle) — Route-B MM-curve Python mirror bit-identical
- `verification/crosscheck_results.json` `crosscheck_pass: True`
- Legacy `build_lowell_line_of_sight_propagator` numerics unchanged for all 11 Bianchi families (FLRW early-return + dispatch-table layering)
- Every family kernel's ResidualPack passes on the canonical observer surface

---

## Runtime gap that blocks S8/S9 (E2E CAMB comparison)

The user's "no toy / no approximation / must follow v5 spec exactly" directive combined with investigation of `execute_tier_b_solver` revealed **three runtime-level blockers** that a single session cannot patch without producing a surrogate:

### Blocker 1: `multipole_cutoff` validation hardcoded to `{4, 6, 8}`

`bass/runtime/ver2_execution.py` `RuntimeControlBlock.__post_init__` (line ~153) allows only `multipole_cutoff ∈ {4, 6, 8}` unless `diagnostic_l2_override=True`. No developmental path exists for `L = 16, 20, 30, 40` which is what a low-ℓ CAMB comparison needs. Extending the validation is a few lines; but extending downstream is not (see Blocker 2).

### Blocker 2: IMEX integrator overflows at real cosmological η-range

Direct test: `execute_tier_b_solver` with `L_max=8`, `eta_initial=261 Mpc` (recombination), `eta_final=14147 Mpc` (today), Planck 2018 species:

```
RuntimeWarning: overflow encountered in add
RuntimeError: IMEX split executor failed to find a finite accepted substep before η=4669.236346067752
```

The integrator diverges at ~1/3 of the path to today. Every existing unit test uses toy ranges like `eta_initial=0.5, eta_final=1.0`. The IMEX split + closure machinery is not yet stable over the cosmological conformal-time range it needs to cover.

### Blocker 3: No existing IC-injection path from real recombination state

All existing tests initialize with `eta_initial=0.5` — a synthetic pre-recombination sentinel, not `η(z ≈ 1089.94)`. Proper FLRW CMB requires IC injection at (or before) recombination from the real background_monitor state. This path doesn't exist as a stable/tested surface.

### Downstream consequences

- S8 (FLRW SW-plateau pipeline): abandoned per toy-model directive. Replacement requires Blockers 1-3 resolved first.
- S9 (CAMB low-ℓ D_ℓ comparison): requires a working S8.
- S10 (reionization τ-sweep): `recombination/reionization.py` is real physics and complete, but the τ-sweep validation wants to see the visibility difference propagate through the full pipeline — requires S8.
- S11 (Tier-A+B unified facade): `compare_tier_a_to_tier_b` exists in `ver2_execution.py:1805`, but both tiers need to produce real CMB spectra first.

**Estimated runtime-track effort:** 2-3 weeks of integrator-engineering work (not per-session patches).

---

## What's safe to attempt in the next session (v5-compliant, no runtime changes)

### Option A — Finish the physics-layer audit (S12)

For each of the 11 Bianchi family kernels, verify the v5 `03A_INTRINSIC_FAMILY_TEMPLATE_CARDS.md` and `03B_FROZEN_BACKEND_CONSTANTS_AND_LOOKUP_RESOLUTION.md` checklist item-by-item:

- Every native-label field from `_NATIVE_LABELS` / `_CHART_DEFAULTS` represented in the kernel's translator
- Every forbidden shortcut from `_MUST_NOT_DO` tracked in `bundle.metadata["forbidden_shortcut_tracked"]`
- Every required residual from `_FAMILY_RESIDUALS` computed by `_compute_residuals` and within tolerance
- Every frozen lookup constant from `_FROZEN_SOLVABLE_LOOKUP` (for II, III, IV, etc.) referenced in kernel metadata
- Branch-flag handling matches `_DEFAULT_BRANCH_FLAGS`

Deliverable: a single `test_v5_spec_compliance.py` that parametrizes over all 11 families and asserts every v5 contract clause is represented in the kernel + metadata. This is the final scoreboard that the v5 `family_backend_gate` is fully closed.

### Option B — Deepen the verification bundle coupling

`docs/bianchi_design_pack_v5/verification/crosscheck_results.json` has frozen symbolic/numeric checks. Currently kernels report `verification_crosscheck_pass = True` unconditionally. A tighter binding:

- Per-family crosscheck residual extraction (not just the global `crosscheck_pass` flag)
- Numeric bound propagation (e.g., `classB_max_abs_err < 1.4e-14` from the bundle must flow into Type III's `class_b_branch_consistency` tolerance)
- Symbolic-check enforcement (e.g., `typeVIII_mu_evenness` must be asserted inside `type_viii.py` at kernel-construction time)

Deliverable: per-family verification-bundle consumers that make `family_backend_gate.passed` actually depend on the bundle content.

### Option C — Family-specific residuals beyond the current set

Current residuals per family cover translator / seed / boundary / branch — three residuals each. V5 §03A hints at additional physics checks per family that aren't yet computed (e.g., for Type VIII the `typeVIII_specialcase_max_abs_err`, for class-B the `classB_max_abs_err` bundle values). Extending each kernel's `_compute_residuals` to include these numeric bounds and asserting them against the verification bundle tightens the gate further.

### Option D (runtime-track, multi-session)

Only if the user explicitly endorses 2-3 weeks of integrator work:

1. Refactor `RuntimeControlBlock.multipole_cutoff` validation to allow `{4, 6, 8, 12, 16, 20, 30, 40}` + prove downstream memory/layout handle it
2. Stabilize the IMEX split executor over the full cosmological η-range
3. Add real-IC injection path from `background_monitor` at `η(z_*)`
4. End-to-end FLRW D_TT, D_EE, D_TE production at ℓ=2..30
5. CAMB cross-check
6. Reionization τ-sweep automation
7. Tier-A vs Tier-B cross-check

This track is an engineering programme, not a deliverable; it requires sustained iteration and cannot be guaranteed in N sessions.

---

## How to start the next session

**Suggested opener prompt** (copy-paste into a fresh session):

> v5 gap-closure 작업을 이어서 할게. 이전 세션에서 S0~S7이 commit 됐고(커밋 `dea07b8` → `ed9df36`), S8/S9의 toy SW-plateau는 user directive에 따라 제거됨(`85c2270`). 현재 tree는 clean, 1360 tests pass, FLRW D_2 bit-identity 유지.
>
> `docs/V5_HANDOFF_NEXT_SESSION.md`를 먼저 읽어 맥락을 복원하고, 특히 "Runtime gap" 섹션에서 설명한 세 가지 blocker (multipole_cutoff validation, IMEX overflow, 실 IC-injection 경로 부재)를 파악해줘.
>
> 다음 단계로 [A/B/C/D 중 하나 선택]를 진행하고 싶어:
> - A: v5 11-family spec compliance audit (S12) — 형식 검증 + scoreboard
> - B: verification bundle 세분화 (per-family crosscheck residual 바인딩)
> - C: family-specific 추가 residual 확장
> - D: runtime-track — multipole_cutoff validation 완화 + IMEX 안정화 (수주 규모)
>
> 시작해줘.

Replace `[A/B/C/D 중 하나 선택]` with the desired next-step option before sending.

---

## Key file paths (for cold-start reference)

**Family kernels (v5 PR-08 body, landed):**
- `htt/bass/los/families/__init__.py` — registry hub
- `htt/bass/los/families/base.py` — LegacyDelegationKernel, NotImplementedKernel
- `htt/bass/los/families/type_{i,ii,iii,iv,v,vi_0,vi_h,vii_0,vii_h,viii,ix}.py` — 11 family kernels
- `htt/bass/los/families/residual_report.py` — per-family + aggregate residual report
- `htt/bass/los/families/test_*.py` — 192 tests passing, 1 skipped

**Transport facade (v5 PR-05):**
- `htt/bass/transport/exact_transport.py` — single-entry `build_exact_transport`
- `htt/bass/transport/test_exact_transport.py`

**Statistics (v5 PR-03):**
- `htt/bass/statistics.py` — ResidualPack, CovariancePack, chi_squared
- `htt/bass/test_statistics.py`

**Validation gates:**
- `htt/bass/validation/ver3_gate_stop.py::family_backend_gate_bundle_from_packs` (S6 addition)
- `htt/bass/validation/test_d2_regression_anchor.py` (S0)
- `htt/bass/validation/test_verification_pack.py` (S0)
- `htt/bass/validation/_d2_anchor_golden.json` (S0)

**Output archive (v5 PR-10):**
- `htt/bass/forward/ver3_output_archive.py::write_family_residual_archive` (S6 addition)

**V5 authoritative spec:**
- `docs/bianchi_design_pack_v5/` (unchanged)
- `docs/bianchi_design_pack_v5/verification/crosscheck_results.json` — frozen oracle

**Runtime (upstream, NOT modified):**
- `htt/bass/runtime/ver2_execution.py` — `execute_tier_b_solver`, `RuntimeControlBlock`, `compare_tier_a_to_tier_b`
- `htt/bass/hierarchy/ver2_native_integrator.py` — `Ver2TierBIntegrator` (5,260 LOC)
- `htt/bass/hierarchy/ver3_layout_protocol.py` — `HierarchyLayout`, `build_hierarchy_layout`, `flatten`
- `htt/bass/recombination/reionization.py` — tanh reionization (real physics, untouched)

---

## Regression baseline

```
pytest htt/bass/los/ htt/bass/transport/ htt/bass/spectrum/ \
       htt/bass/forward/ htt/bass/validation/test_d2_regression_anchor.py \
       htt/bass/validation/test_verification_pack.py \
       htt/bass/validation/test_ver3_gate_stop.py \
       htt/bass/test_statistics.py
→ 1360 passed, 1 skipped, 2 warnings
```

D_2 MM-curve anchor bit-identical, v5 verification bundle crosscheck_pass=True, all 11 family residual packs pass on the canonical observer surface.
