# BASS Phase I-L Roadmap — v2.0 (Parallel Dual-Track)

> **Date**: 2026-04-17 (revision after formalism audit)
> **Replaces**: Phase I-L Roadmap v1.0 (2026-04-17 오전)
> **Approval**: Parallel dual-track migration approved by user 2026-04-17.

v1.0 은 `sync_gauge_camb.rs` 를 production 으로 간주한 상태에서 작성. **Formalism audit (2026-04-17 오후)** 결과 `sync_gauge_camb` 는 MB-95 (Ma–Bertschinger synchronous gauge brightness multipole) formalism 이고, DESIGN LAW 가 요구하는 **1+3 covariant PSTF `I_{A_ℓ}`** 와 구조적으로 다름이 확인됨. 따라서 Phase 구조를 재편성.

---

## §1. 재편성 원칙

### 1.1 Formalism role assignment

`docs/SSOT_POLICY.md §17` 로 잠김:

- `sync_gauge_camb.rs` (MB-95) = **verified FLRW oracle**, not production
- `src/solver/pstf_primary/` (신설 예정) = **production target**
- 궁극 validation = PSTF(FLRW limit) → MB-95 → CAMB 체인의 각 쌍 ≤0.5% 일치

### 1.2 Migration shape

Big-bang 재작성 금지. **4-phase parallel dual-track**:

```
Phase 1 (PR-020..024) : PSTF primary scalar FLRW 완성
Phase 2 (PR-025)      : FLRW-limit equivalence test (MB-95 ↔ PSTF)
Phase 3 (PR-026)      : Production backend switch (MB-95 → oracle, PSTF → production)
Phase 4 (PR-050..080) : Bianchi extension (tetrad, σ_{ab}, tilt)
```

각 Phase 마다 D_ℓ regression guard (ℓ ∈ [2, 300] baseline) 유효.

---

## §2. PR 번호 재매핑 (v1.0 → v2.0)

| v1.0 | v2.0 | 비고 |
|---|---|---|
| PR-010 (source split) | PR-010 ✅ (유지, 완료) | Stage A+B 완료. Registry signature 는 formalism-agnostic. 내부 구현은 Phase 1 에서 PSTF branch 추가. |
| PR-011 sub-track 1 (ν Hessian SSOT) | PR-011 ✅ (유지, 완료) | Formalism-agnostic. 유지. |
| PR-011 sub-track 2b (massive-ν wiring) | **연기** | MB-95 wiring 하면 Phase 3 에서 재작업 필요. PSTF 완성 후에. |
| PR-011 sub-track 2c (lensing) | **연기** | Lensing 은 PSTF 위에 구현이 자연스러움. Phase 1 이후. |
| PR-011 sub-track 2d (high-ℓ σ̇) | **연기** | MB-95 고유 문제. PSTF 는 같은 stiff 구조 없음. 필요 시 Phase 2 에서 재평가. |
| PR-020..023 (exact transport) | **PR-020..024 로 재정의** | 아래 Phase 1 참조. |
| PR-025 (신규) | FLRW equivalence test | Phase 2. |
| PR-026 (신규) | Backend switch | Phase 3. |
| PR-030..080 | PR-050..080 (Bianchi) | 번호만 재배치. Phase 4. |

---

## §3. Phase 1 — PSTF Primary Scalar FLRW (PR-020..024)

### PR-020 — PSTF state layout + hierarchy primitives ✅ (score 6/10, merged 2026-04-17)

**Scope**:
- `src/solver/pstf_primary/mod.rs`, `layout.rs`, `hierarchy.rs`
- `PstfLayout` struct 정의: `I_gamma(ℓ)`, `I_nu(ℓ)`, `E_pstf(ℓ)`, `B_pstf(ℓ)` indexing
- covariant divergence operator (FLRW 에서 `k/(2ℓ+1)` 으로 reduce 됨을 증명하는 test 포함)
- `src/pstf/` 기존 모듈 중 재사용 가능한 것 정리

**Actual outcome**: `PstfFlrwLayout` struct (FLRW-specialized wrapper over `LmLayout`) + 12 unit tests. Covariant divergence operator test 는 PR-025 로 이관 (normalization chain 의 복잡성 때문, `STUCK_LOG.md` 참조). PR-020 은 state layout + m=0 accessor + validation invariant 에 한정.

**Gate evidence**: G1 ✅ (12/12 + 130+12+35 회귀 없음), G2 N/A (scaffolding), G3 ✅ (invariant validation + coefficient hand-check), G4 N/A. Score cap 6 per PR_CONSTITUTION §9.2.

**Dependency**: PR-010 ✅, PR-011-subtrack-1 ✅

### PR-021 — PSTF adiabatic IC ✅ (score 8/10, merged 2026-04-17)

**Scope**:
- `src/solver/pstf_primary/ic.rs`
- PSTF 변수 위에서 adiabatic IC 유도 (super-horizon limit)
- MB-95 bootstrap IC 와 **FLRW 극한에서 동일한 δ_γ, v_γ 를 생성** 함을 test

**Actual outcome**: `PstfIcInputs`, `PstfObservables`, `pstf_adiabatic_ic()`, `PstfObservables::from_state()` 구현. State-level value 를 MB-95 와 동일하게 copy, observable projection 에서 δ_γ = 4·Θ_0 등의 관례 적용. Photon + neutrino monopole/dipole 만 (fluid/metric 은 PR-023). 10 unit tests.

**Gate evidence**: G1 ✅ + G2 ✅ (`regression_delta_gamma`, `regression_v_gamma` rel err < 1e-15) + G3 ✅ + G4 ✅ (MB-95 Rust oracle cross-check first pass). Score cap 9, publication figure 없어 final 8. **첫 PSTF PR with G4 pass**.

### PR-022 — PSTF RHS (Sub-track split, weight 15 total)

**결정 (2026-04-17)**: Single PR-022 대신 3 sub-track 으로 분할. 이유: 4 coupled 성분 (free-streaming / collision / metric / Jacobian) 의 독립 G2 gate 확보 + anti-local-min 위험 감소. Pre-audit: `docs/PR_DELTAS/pr-022-design.md`.

#### PR-022a — Free-streaming RHS ✅ (score 7/10, merged 2026-04-17)

**Scope**: `src/solver/pstf_primary/rhs_free.rs` (~380 줄)
- `RhsInputs { k, tau, metric_monopole_source }` — 최소 의존성 (baryon, opacity 없음)
- `pstf_free_streaming_rhs()` — photon + ν m=0 hierarchy, FLRW free-streaming
- Metric coupling 은 placeholder (PR-023 에서 wire up), collision 은 PR-022b

**Actual outcome**: 11 unit tests, MB-95 `camb_rhs` (opac=0 특수화) 와 ℓ={0,1,2,5,ℓ_max} 에서 1e-14 rel err bit-identical. k ∈ {1e-4, 1e-2, 1e-1} multiple-k regression.

**Gate evidence**: G1 ✅ + **G2 partial ✅** (cap 7, metric placeholder 로 인한 free-streaming sub-component only) + G3 ✅ + G4 ✅ (MB-95 oracle). Weight 6, Score 7, W·S/10 = 4.2.

#### PR-022b — Electron-frame Thomson collision ✅ (score 8/10, merged 2026-04-17)

**Scope**: `src/solver/pstf_primary/collision.rs` (~360 줄)
- `FrameConvention` enum: ElectronRestFrame (DESIGN LAW default) vs HypersurfaceNormalFrame (MB-95 equivalent at FLRW)
- `CollisionInputs { kappa_dot, r_b, use_pol_feedback, frame }` — 명시적 frame tag
- `pstf_thomson_collision()` — photon intensity (ℓ=1 drag, ℓ=2 pol if on, ℓ≥3 damping) + baryon v_b reaction, additive design
- Pol feedback default off — E-mode RHS 는 future PR

**Primary oracle**: MB-95 `camb_rhs` (not `collision_lm.rs` — coefficient bug 의심, §2.3 pre-audit 에서 식별, Phase 2 defer)

**Actual outcome**: 11 tests **first-try pass**. MB-95 path (free-streaming + collision 합산) 와 ℓ={0,1,2,3,5,ℓ_max} rel err < 1e-13. κ̇ ∈ {0.01, 1.0, 100.0} Mpc⁻¹ 전범위 regression.

**Gate evidence**: G1 ✅ + **G2 full ✅** (PR-022a partial 개선) + G3 ✅ + G4 ✅ (MB-95 oracle). Weight 5, Score 8, W·S/10 = 4.0.

#### PR-022c — Analytical Jacobian (sparse, Rodas5P) ✅ (score 7/10, merged 2026-04-18)

**Scope**: `src/solver/pstf_primary/jacobian.rs` (~470 줄)
- `JacobianInputs` — RhsInputs + CollisionInputs 통합
- `SparseJacobian` — triplet list `Vec<(row, col, val)>`
- `pstf_analytical_jacobian()` — sparse output, photon/ν free-streaming tridiagonal + collision cross-coupling
- `pstf_jacobian_dense()` — Rodas5P 호환 row-major
- `jacobian_fd_check()` — 5-point stencil, columnwise (sparse columns only, <0.1s test runtime)

**Actual outcome**: 9 tests **first-try pass** (PR-022b 에 이어 2번 연속). FD check 3 tests (free-streaming only / collision only / full combined) 모두 max rel err < 1e-6. Specific coefficient 검증: `J[Θ_3, Θ_2] = 3k/7`, `J[Θ_5, Θ_6] = −6k/11` eps=1e-15. Sparsity = 85 entries / 1.34M dense ≈ 0.006%.

**Gate evidence**: G1 ✅ + G2 N/A (structural) + G3 ✅ (FD check) + G4 N/A (MB-95 은 explicit solver, analytical J 없음). Weight 4, Score 7, W·S/10 = 2.8.

---

## PR-022 sub-track 전체 완결 요약 ✅

| Sub-track | Weight | Score | W·S/10 | First-try |
|---|---:|---:|---:|:---:|
| PR-022a (Free-streaming) | 6 | 7 | 4.2 | — |
| PR-022b (Thomson collision) | 5 | 8 | 4.0 | ✅ |
| PR-022c (Analytical Jacobian) | 4 | 7 | 2.8 | ✅ |
| **합산** | **15** | | **11.0** | |

Original PR-022 target W·S/10 = 12.0. 달성 = 11.0 (91.7%). 0.83pp Phase 1 loss 의 trade-off:
- **Anti-local-min**: PR-020 의 `flrw_norm_ratio_down` 유형 실패 재발 없음
- **Pre-audit quality**: `collision_lm.rs` bug, linear RHS 확인 등 사전 식별
- **Execution**: 2 PR 연속 first-try full pass (PR-022b/c)

---

### PR-023 — PSTF Metric + Fluid Scalar Sector (Sub-track split, weight 10 total)

Phase 1 의 남은 single-largest PR. PR-022 pattern 재적용하여 3 sub-track 으로 분할.

#### PR-023a — Metric state + RHS ✅ (score 7/10, merged 2026-04-18)

**Scope**: `src/solver/pstf_primary/metric.rs` (~370 줄)
- `BackgroundQuantities` struct — ℋ, ρ_γ, ρ_ν, ρ_b
- `MetricInputs { k, bg }`
- State layout: metric[0]=etak, metric[1]=σ, metric[2..=10] reserved for Bianchi Z_{ab}
- `pstf_momentum_constraint_dgq()` — (16/3)(ρ_γ·Θ_1 + ρ_ν·N_1) + ρ_b·v_b
- `pstf_hdot()` — 2·k·σ − 3·dgq/k (derived, not in state)
- `pstf_metric_monopole_source()` — −hdot/6 export for PR-022a wire-up (PR-023c)
- `pstf_metric_rhs()` — etakdot + sigmadot, additive
- `i_metric_etak()`, `i_metric_sigma()` accessors in layout

**Actual outcome**: 11 tests **first-try pass** (3 PR 연속). k ∈ {1e-4, 1e-2, 1e-1} Mpc⁻¹ 에서 MB-95 `camb_rhs:462-481` formula 와 bit-identical (rel err < 1e-13).

**Gate evidence**: G1 ✅ + **G2 full ✅** + G3 ✅ + G4 ✅. Weight 4, Score 7, W·S/10 = 2.8.

#### PR-023b — Fluid RHS ✅ (score 7/10, merged 2026-04-18)

**Scope**: `src/solver/pstf_primary/fluid.rs` (~310 줄)
- `FluidInputs { k, h_conformal, cs2b, hdot }` — Option B interface (hdot 직접 주입)
- `pstf_fluid_rhs()` — clxcdot, clxbdot, vbdot (Thomson drag 제외, PR-022b 에 이미 있음)
- Layout accessors 4개 추가: `i_baryon_delta`, `i_baryon_v_m0`, `i_cdm_delta`, `i_cdm_v_m0`
- Sync gauge 조건: v_c = 0 identically (dy[i_cdm_v_m0()] 무접촉)

**Actual outcome**: 10 tests **first-try pass** (4 PR 연속). k ∈ {1e-4, 1e-2, 1e-1} Mpc⁻¹ 에서 MB-95 `camb_rhs:483-487` formula 와 bit-identical (diff < 1e-18). `regression_with_pr023a_hdot` integration test 가 PR-023a/b inter-sector consistency 검증.

**Gate evidence**: G1 ✅ + **G2 full ✅** + G3 ✅ + G4 ✅. Weight 3, Score 7, W·S/10 = 2.1.

#### PR-023c — Full RHS Dispatcher + PR-022a Retrospective G2 승격 ✅ (score 8/10, merged 2026-04-18)

**Scope**: `src/solver/pstf_primary/full_rhs.rs` (~340 줄) + PR-022a `rhs_free.rs` retrospective test
- `FullRhsInputs` struct — 모든 sector parameter 의 superset
- `pstf_full_rhs()` dispatcher:
  1. `dy.fill(0.0)` (zero-init)
  2. `pstf_hdot()` compute ONCE (for multi-sector consistency + efficiency)
  3. Free-streaming with wired `metric_monopole_source = -hdot/6` (PR-022a placeholder → actual PR-023a value)
  4. Thomson collision (additive)
  5. Metric RHS (additive, disjoint slots)
  6. Fluid RHS (additive, v_b 는 collision 과 같은 slot)
- PR-022a `rhs_free.rs` 에 새 test `regression_rhs_matches_mb95_full_path_with_metric` 추가

**Actual outcome**: 6 dispatcher tests **first-try pass** + PR-022a retrospective test 1/1 pass. **Phase 1 최초의 end-to-end G2 test** — 모든 sector (photon + ν + metric + fluid + Thomson drag) 를 한 test 에서 MB-95 `camb_rhs` 전체와 bit-identical (rel err < 1e-13).

**Gate evidence**: G1 ✅ + **G2 full (most comprehensive) ✅** + G3 ✅ + G4 ✅ → cap 9, publication 없음 → **Score 8**. W·S/10 = 2.4.

**Retrospective upgrade (PR-022a)**: PR-023c 의 새 test 가 metric wire-up 후 full FLRW 재현을 증명 → PR-022a G2 partial → full 승격 (score 7→8, W·S/10 4.2→4.8, Δ=+0.6). `PROGRESS_SCOREBOARD §3` 에 공식 기록, **Phase 1 최초의 retrospective scoring event**.

---

## PR-023 Sub-track 전체 완결 요약 ✅

| Sub-track | Weight | Score | W·S/10 | First-try |
|---|---:|---:|---:|:---:|
| PR-023a (Metric state + RHS) | 4 | 7 | 2.8 | ✅ |
| PR-023b (Fluid RHS) | 3 | 7 | 2.1 | ✅ |
| PR-023c (Full RHS dispatcher) | 3 | 8 | 2.4 | ✅ |
| **합산** | **10** | | **7.3** | |
| **+ PR-022a retrospective bonus** | | | **+0.6** | |
| **총 delta** | | | **7.9** | **98.8% of original 8.0** |

원 PR-023 target (W=10, S=8, W·S/10=8.0) 대비 **98.8% 달성**. Sub-track 분할의 loss (0.7) 가 retrospective bonus (0.6) 로 거의 완전 상쇄.

### Sub-track 분할 전략 최종 성과 (PR-022 + PR-023 합산)

| Metric | PR-022 | PR-023 |
|---|---:|---:|
| Original target W·S/10 | 12.0 | 8.0 |
| Achieved (sub-track only) | 11.0 (91.7%) | 7.3 (91.3%) |
| Retrospective bonus | — | +0.6 (PR-022a) |
| **Total achieved** | **11.0 (91.7%)** | **7.9 (98.8%)** |
| First-try PRs | 2/3 | 3/3 |

Sub-track 분할 전략의 성숙 — PR-023 에서 retrospective pattern 으로 loss 를 거의 상쇄.

---

### PR-024 — PSTF LoS Source + solve_pstf_spectrum (Sub-track split, weight 12 total)

Phase 1 의 남은 single-largest PR. PR-022, PR-023 pattern 재적용하여 3 sub-track 으로 분할.

#### PR-024a — Source function ✅ (score 7/10, merged 2026-04-18)

**Scope**: `src/solver/pstf_primary/source.rs` (~370 줄)
- `VisibilityAtSnap` — MB-95 `VisibilityResult` snapshot subset (g, gdot, gddot)
- `pstf_extract_source_inputs()` — PSTF layout → `source::registry::SourceInputs`
- `pstf_source_function()` — SSOT channel assembly (SW + Dop + Quad + E-mode, ISW deferred)

**Primary oracle**: MB-95 `production_source_v1:315-404` via SSOT `source::registry` (PR-010 Stage B 이후 동일 경로).

**Actual outcome**: 10 tests pass (2nd attempt). E-mode layout mismatch (PSTF ℓ≥2 only) 를 pre-audit 에서 놓쳐 1회 iteration. Polter convention 이 E_0 미사용이라 `e0 = 0.0` unconditional 로 해결. `STUCK_LOG.md §3` 에 below-threshold fix 로 기록.

**Gate evidence**: G1 ✅ + **G2 full (SSOT direct equivalence) ✅** + G3 ✅ + G4 ✅. Weight 4, Score 7, W·S/10 = 2.8.

#### PR-024b — Time integration + source grid 🔲 (planned, weight 4, target score 7)

**Scope**: `src/solver/pstf_primary/integrate.rs`
- `PstfKmodeResult { eta_grid, source_total, source_sw/dop/quad/e, state_trajectory optional }`
- `pstf_solve_kmode(k, params, vis, layout)` — Rodas5P 로 η 적분, snapshot 별 `pstf_source_function` 호출
- 기존 MB-95 `CommonProfile` + Rodas5P stepper 재사용 — new physics 없음

**Pre-audit checklist 추가**: "Layout accessor range check" (PR-024a 교훈).

**TDD gate**: ~10 tests. G2 target — k=0.01 에서 PSTF state trajectory MB-95 `solve_production_kmode` 과 bit-identical (tolerance 1e-10).

#### PR-024c — LoS + spectrum assembly 🔲 (planned, weight 4, target score 8)

**Scope**: `src/solver/pstf_primary/los.rs` + `src/solver/pstf_primary/spectrum.rs`
- `pstf_los_integrate()` — spherical Bessel + trapezoid
- `solve_pstf_spectrum()` — k-grid 순회 + C_ℓ assembly
- **Test: `dump_pstf_dl_spectrum_sparse`** — PSTF 로 D_ℓ 생성

**G2 target**: **PSTF D_2 == MB-95 oracle D_2 = 1002.086744 μK² bit-identical** (Phase 1 technical capstone).

**합산 target**: W=12, W·S/10 = 2.8 + 2.8 + 3.2 = **8.8** (원 target 9.6 의 91.7%, PR-022/PR-023 과 유사).

---

## §4. Phase 2 — FLRW Equivalence Test (PR-025)

### PR-025 — MB-95 ↔ PSTF equivalence

**Scope**:
- `tests/flrw_equivalence.rs` — 독립 integration test file
- 동일 cosmology (Planck 2018 baseline) 에서 MB-95 `dump_dl_spectrum_sparse` vs PSTF `solve_pstf_spectrum` D_ℓ 비교
- ℓ ∈ {2, 3, 5, 10, 30, 100, 200, 220, 300}: **ratio 1.000 ± 0.005**

**TDD gate**:
- 명시된 ℓ 에서 relative error ≤0.5%
- Relative error 가 **어떤 ℓ 에서도** 2% 를 넘지 않음
- EE, TE (폴라라이제이션 cross-check) 동일 기준

**실패 시**: PSTF 쪽 bug. 변수 매핑 table (PR-020 작성) 이 binary-search 공간 제공. 가장 흔한 실패 후보:
- Normalization (2ℓ+1) 계수 실종
- E/B 부호 규약 차이
- Thomson collision rate 의 ζ̃ vs τ̇ conversion

### Phase 2 완료 기준

- PR-025 의 모든 assertion PASS
- CHANGELOG 에 "PSTF ≡ MB-95 verified at FLRW" 선언
- 논문 chapter 6 초안 갱신 가능

---

## §5. Phase 3 — Production Backend Switch (PR-026)

### PR-026 — MB-95 → oracle, PSTF → production

**Scope**:
- `solve_production_spectrum` 의 내부 호출을 `sync_gauge_camb::solve_*` 에서 `pstf_primary::solve_*` 로 교체
- MB-95 경로는 **유지하되 `#[cfg(test)]` scope 로 이동** — regression oracle 로만 호출됨
- `ProductionConfig` 에서 formalism flag 제거 (항상 PSTF)
- `dump_dl_spectrum_sparse` 는 MB-95 oracle 호출로 유지 (regression guard)
- 신규 test: `dump_dl_spectrum_pstf_sparse` 추가 — PSTF production 의 D_ℓ

**TDD gate**:
- **Regression**: `dump_dl_spectrum_sparse` (MB-95 oracle) D_2 = 1002.086744 그대로
- **New**: `dump_dl_spectrum_pstf_sparse` (PSTF production) D_2 = 1002 ± 0.5% (PR-025 tolerance)
- **Cross-check**: 두 output 의 비율 ℓ ∈ [2, 300] 에서 1.000 ± 0.005 유지

### Phase 3 완료 기준

- Production D_ℓ 가 PSTF 경로에서 나옴
- MB-95 는 CI 의 regression oracle 로만 실행됨
- SSOT `core::ssot::pstf::*` namespace 완성
- PR-011 이후 연기됐던 sub-track 들 재개 가능:
  - **신 Sub-track 2b** (massive-ν wiring) — PSTF ν 2-field 위에서
  - **신 Sub-track 2c** (lensing) — PSTF metric 위에서
  - **신 Sub-track 2d** (high-ℓ precision) — PSTF 는 MB-95 의 σ̇ stiff 구조가 없으므로 재평가

---

## §6. Phase 4 — Bianchi Extension (PR-050..080)

**Phase 3 완료 후** 진행. PSTF production 이 이미 자리잡은 상태에서 Bianchi feature 를 추가.

### PR-050 — Tetrad layer + Bianchi background

`src/solver/bianchi/` 에 tetrad / Bianchi background 도입. `core::ssot::bianchi::*` namespace 신설.

### PR-060 — Geometric shear σ_{ab} 활성화

σ_{ab} 를 PSTF hierarchy 에 coupling. Bianchi-I 에서만. Structure constant 도입.

### PR-070 — Tilt velocity

`v_{tilt}` (khronon field) 도입. Three-level decomposition: global β + δβ + W_R·v_loc.

### PR-080 — `x_C` 생산 + Bayesian inference

논문 핵심 결과 `ln B(FLRW_tilt) = +26.40`, `F_Bayes = 0.093 ± 0.025`. `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}` identity test.

각 PR 별 SDD delta 는 Phase 4 진입 시 별도 작성.

---

## §7. 살아남는 것 / 재작성되는 것

### 살아남음 (formalism-agnostic)

- `docs/PR_CONSTITUTION.md`, `docs/SSOT_POLICY.md`, `docs/KNOWN_LIMITS.md`, `docs/STATUS_TAGS_AND_EXPORTS.md`, `docs/BASS_STACK_OWNERSHIP.md`, `docs/PHYSICS_REFERENCES.md` — governance layer
- `core::ssot::constants::*` (NEFF_*, NU_HESSIAN_*, MIN_LMAX_*) — 수치 상수
- `core::ssot::cl_prefactor_at_k`, `friedmann_hsq_from_grho_sum` — formalism-agnostic helpers
- `source::registry` 의 **signature** (SourceInputs → ChannelOutputs) — PSTF branch 추가
- Background, HyRec, Bessel/LoS, ODE integrators
- PR-000 ~ PR-011-subtrack-1 의 governance history

### 재작성됨 (formalism-specific)

- `sync_gauge_camb.rs` 의 RHS / Jacobian / IC 는 Phase 3 에서 `#[cfg(test)]` 로 격하
- `core::ssot::polter`, `polter_dot`, `doppler_source`, `quad_source_no_polterddot` → `core::ssot::mb95::*` 로 이동. PSTF 대응은 `core::ssot::pstf::*` 에 신규
- `source::registry` 의 **구현 내부** — MB-95 branch 유지하며 PSTF branch 추가 (feature-flag)

---

## §8. 관측 target 재정렬

| DR | 일정 | v2.0 준비 상태 |
|---|---|---|
| Simons Observatory | operational | 🟡 Phase 3 완료 필요 |
| Euclid DR1 | ~2026-10 | 🔴 Phase 3 완료 필요 (타이트) |
| DESI DR2 | (dynamical DE 4.2σ) | 🔴 Phase 4 PR-060 (backreaction) 필요 |
| LiteBIRD | ~2033 | Phase 4 완료 후 여유 |

**실용적 타이밍**:
- Phase 1 (PR-020..024): 4–6주 추정
- Phase 2 (PR-025): 1주
- Phase 3 (PR-026): 1–2주
- **Phase 3 완료까지 6–9주**. Euclid DR1 타이밍 (~2026-10, 6개월 후) 은 달성 가능하지만 여유 크지 않음.

Thesis writeup 은 Phase 1-3 와 병행. Phase 4 는 thesis 이후 fellowship 단계로 밀릴 가능성 있음. 논문은 Phase 3 까지의 결과 + Phase 4 의 theoretical framework 로 구성 가능.

---

## §9. 즉시 다음 행동

**Status as of 2026-04-18**: PR-020 ✅, PR-021 ✅, PR-022 sub-track 전체 ✅, PR-023 sub-track 전체 ✅, **PR-024a ✅ (PR-024 sub-track 첫 번째, E-mode layout fix 1회 iteration)**. Phase 1 진행률 **50.8%** (53.3 / 105). D_2 **14th consecutive** commit bit-identical.

**중요 변화**: First-try streak 5 PR → 0 reset (PR-024a). STUCK_LOG §3 에 below-threshold fix 기록. Pre-audit checklist 에 "Layout accessor range check" 추가 결정.

다음 세션에서:

1. **`docs/PR_DELTAS/pr-024b-design.md` 작성** — PR-024b (time integration + source grid) pre-audit. MB-95 `solve_production_kmode` 재감사, Rodas5P stepper 재사용, η snapshot grid 설계. **Layout accessor range check 섹션 포함** (PR-024a 교훈).
2. **PR-024b scaffold** — `src/solver/pstf_primary/integrate.rs` 신설. `pstf_solve_kmode` 구현.
3. **PR-024b closure** — W=4, target S=7, W·S/10=2.8. Phase 1 진행률 50.8% → **53.5%**.
4. **PR-024c (LoS + spectrum) 진입** — Phase 1 technical capstone. PSTF primary 가 D_2 = 1002.086744 μK² bit-identical 생성이 목표.

PR-024 sub-track 전체 완료 후 PR-025 (FLRW equivalence), PR-026 (backend switch) 순차 진행. Phase 1 최종 target **74.4%** (78.1 / 105).

---

## §10. 이 문서 갱신 주기

- 각 PR closure 마다 §3-§6 해당 항목을 "✅ PR-0XX @ commit `<sha>` (score N/10)" 로 마크
- **PR closure 마다 `PROGRESS_SCOREBOARD.md` 갱신 의무** (추가 2026-04-17) — weight·score 반영, 진행률 재계산
- Phase 완료 = **weighted score 합계 ≥ Phase 총 weight × 80%** (PR_CONSTITUTION §9, PROGRESS_SCOREBOARD §4.3). 각 Phase 마다 §4-§6 하단에 "Phase N 완료 (date, weighted progress X%)" 선언
- 관측 DR 일정 변경 시 §8 갱신
- 형식 전환 실패 / 재설계 필요 시 전체 revision + 상위 approval
- **Anti-local-minimum rule trigger 시** (PR_CONSTITUTION §10): `STUCK_LOG.md` 에 기록 + §9 의 "즉시 다음 행동" 에서 다음 PR 로 이동 선언

---

*v1.0 (formalism-agnostic, MB-95 as production) → v2.0 (dual-track, PSTF target) 2026-04-17. §9/§10 2026-04-17 scoreboard integration.*
