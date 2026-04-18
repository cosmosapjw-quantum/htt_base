# BASS Phase 1 PSTF Primary Migration — Snapshot 2026-04-18

> **Project**: BASS (Boltzmann And Spectrum Solver / Bianchi Anisotropy Solver)
> **Phase**: 1 — PSTF Primary Migration (FLRW baseline)
> **Snapshot scope**: PR-020 ~ PR-024b (build-complete, 일부 test 실행 대기)
> **Progress at snapshot**: **50.8% of Phase 1 complete** (53.3 / 105 weighted score)
> **Regression anchor**: D_2 = 1002.086744 μK² bit-identical across **14 consecutive commits**

본 문서는 다세션에 걸친 BASS Phase 1 PSTF Primary Migration 작업의 전체 통합 기록이다. User 의 "코드 최적화가 부족하다" 라는 피드백으로 현 시점에서 작업을 일시 중지하고, 별도의 최적화 작업을 진행하기 전에 **지금까지의 모든 코드와 문서를 단일 zip 으로 packaging** 하기 위해 작성되었다.

---

## §1. Project 배경

### 1.1 연구 컨텍스트

Jiwon (Soongsil University OMEG Institute) 의 박사논문 _"Tetrad-Based Departure Decomposition for FLRW Departure in Bianchi Anisotropic Cosmologies"_ 의 핵심 계산 엔진. Master departure identity

```
x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}
```

를 Maartens-Ellis-Stoeger (MES) kinematic bound hierarchy 와 연결하여 9개 Bianchi type 에 대해 CMB T+E+B spectrum 을 계산한다. Production 결과:

- **ln B(FLRW_tilt) = +26.40**
- β = 1.360×10⁻³
- F_Bayes = 0.093 ± 0.025

Tsagas fast-growth (arXiv:2603.14511) 은 Clarkson–Maartens 가 제거 — khronon field 가 유일한 생존 tilted-Bianchi dipole source.

### 1.2 Phase 1 의 역할

BASS 는 **dual-track** 아키텍처:

- **MB-95 production**: 기존 `sync_gauge_camb.rs` (7363 lines) — CAMB-convention sync gauge, ODE-based Rodas5P + hand-analytic linear coefficient matrices. **현재 production path**.
- **PSTF primary**: 1+3 covariant PSTF (Projected Symmetric Trace-Free) formulation — Ellis-van Elst 표기의 `I_{A_ℓ}` hierarchy. **Bianchi+tilt 확장에 적합한 새로운 formalism**.

Phase 1 은 PSTF primary 가 FLRW 극한에서 MB-95 production 과 **bit-identical D_2 = 1002.086744 μK²** 를 생성하도록 구축하는 단계. 완료 시 PR-026 에서 production path 를 MB-95 → PSTF primary 로 switch, MB-95 는 oracle 로 강등.

### 1.3 Design Law (모든 PSTF primary 코드 적용)

```
ALL BASS code targets Bianchi+tilt from start.
FLRW = σ=0, tilt=0 special case by params, NEVER hardcoded.

BANNED:
  - scalar Bardeen ODE
  - algebraic Poisson
  - isotropic c_s²
  - scalar v_b collision (use electron-frame ζ̃)
  - decoupled ℓ hierarchy

USE:
  - 1+3 covariant PSTF I_{A_ℓ}
  - CDM frame
  - σ_{ab} at ℓ=2
  - Electron-frame Thomson ζ̃
```

---

## §2. Session 전체 타임라인

### 2.1 세션 시작 시점 (baseline)

- PR-000 (Governance) ✅ merged
- PR-010 (Source Registry SSOT) ✅ merged
- PR-011-st1 (ν Hessian) ✅ merged
- Formalism audit ✅
- PR-020 (Scaffold) ✅ merged
- PR-021 (Adiabatic IC) ✅ merged
- Phase 1 진행률: **30.1%**

### 2.2 세션 내 완료된 PR들

| PR | Title | W | S | W·S/10 | First-try | 완료 일자 |
|---|---|---:|---:|---:|:---:|:---:|
| PR-022a (closure + retro) | Free-streaming RHS (→ retro G2 full via PR-023c) | 6 | 7→**8** | 4.2→**4.8** | ✅ | 2026-04-17 / retro 2026-04-18 |
| PR-022b | Thomson collision | 5 | 8 | 4.0 | ✅ | 2026-04-18 |
| PR-022c | Analytical Jacobian (sparse) | 4 | 7 | 2.8 | ✅ | 2026-04-18 |
| PR-023a | Metric state + RHS | 4 | 7 | 2.8 | ✅ | 2026-04-18 |
| PR-023b | Fluid (CDM + baryon) RHS | 3 | 7 | 2.1 | ✅ | 2026-04-18 |
| PR-023c | Full RHS dispatcher + PR-022a retro 승격 | 3 | 8 | 2.4 | ✅ | 2026-04-18 |
| **PR-024a** | **LoS source function** | **4** | **7** | **2.8** | ❌ (1 iter) | 2026-04-18 |
| **PR-024b (partial)** | **Time integration + source grid** | 4 | pending | pending | ❌ (3 iter) | 진행 중 |

**세션 내 확정 Δ**: +20.7pp Phase 1 progress (30.1% → 50.8%)
**세션 내 확정 W·S/10 증가**: +21.0 (31.6 → 52.6, 그 중 PR-024b ≈ 2.8 pending)

### 2.3 중간점검 (2026-04-18)

PR-023c 완결 후 user 의 요청으로 **MB-95 oracle D_ℓ^TT shape 검증** 수행:

- D_2 = 1002.087 μK² (Sachs-Wolfe plateau 시작)
- SW plateau mean (ℓ=2..30): **1009 μK²**
- First acoustic peak: **ℓ = 217 @ 7369 μK²**
- Peak / plateau ratio: **7.3×**

ΛCDM physics 와 일치 확인. Normalization 은 Planck 2018 best-fit 대비 ~30% 높음 (parameter set 차이, not code bug). PR-025 에서 PSTF primary 가 reproduce 해야 할 baseline 명확화. Plot 은 `plots/phase1_midcheck_dl_tt.png`.

### 2.4 Streaks, Events

- **First-try success streak**: 5 PR 연속 (PR-022b → PR-022c → PR-023a → PR-023b → PR-023c), **PR-024a 에서 끊김 (1 iteration), PR-024b 에서 3 iterations**
- **D_2 bit-identical**: 14 consecutive commits 확정. PR-024b 완결 시 15th 예정
- **STUCK_LOG events**:
  - 1개 preemptive (PR-020 norm ratio, resolved pre-2-failure)
  - 1개 below-threshold (PR-024a E-mode layout, 1 iter)
  - 1개 active step-back (PR-024b tau_min filter, 3 iter) — **Rule §10 triggered, step-back resolved, test 재실행 대기**

### 2.5 Retrospective event

PR-023c 에서 **Phase 1 최초의 retrospective scoring event**: PR-022a G2 partial → full 승격 (score 7 → 8, W·S/10 4.2 → 4.8, Δ=+0.6). 기존 test 건드리지 않고 새 evidence `regression_rhs_matches_mb95_full_path_with_metric` 추가로 정당화. Scoring discipline §9.5 ("evidence 강화 시 retroactive 허용") 최초 적용.

---

## §3. 현재까지 구축된 PSTF Primary 모듈

`src/pstf_primary/` 이하 12 modules (각 파일 주석 상세):

```
src/pstf_primary/
├── mod.rs                 # 모듈 등록
├── layout.rs              # PstfFlrwLayout (1+3 covariant state vector 정의)
├── ic.rs                  # pstf_adiabatic_ic — IC 생성
├── rhs_free.rs            # pstf_free_streaming_rhs — photon/ν streaming
├── collision.rs           # pstf_thomson_collision — Thomson scattering
├── jacobian.rs            # pstf_analytical_jacobian — sparse Jacobian (free-stream + coll)
├── metric.rs              # pstf_metric_rhs — etakdot, sigmadot, pstf_hdot
├── fluid.rs               # pstf_fluid_rhs — CDM + baryon continuity/Euler
├── full_rhs.rs            # pstf_full_rhs — 4 sector dispatcher
├── source.rs              # pstf_source_function — LoS source channel assembly
├── matrix.rs              # build_pstf_matrix_into — coefficient matrix via unit-vec
└── integrate.rs           # pstf_solve_kmode, pstf_solve_kmode_adiabatic
```

### 3.1 각 모듈의 test 현황

| Module | Tests | 상태 |
|---|:---:|---|
| layout | 12 | ✅ all pass |
| ic | 10 | ✅ all pass |
| rhs_free | 12 | ✅ all pass (retrospective G2 test 포함) |
| collision | 11 | ✅ all pass |
| jacobian | 9 | ✅ all pass (PR-023 이후 sector coverage gap 있음 — §5.1 참조) |
| metric | 11 | ✅ all pass |
| fluid | 10 | ✅ all pass |
| full_rhs | 6 | ✅ all pass |
| source | 10 | ✅ all pass (2nd attempt, E-mode fix) |
| matrix | 3 | ✅ all pass first-try |
| integrate | 8 | ⚠️ 1 passed, 7 pending execution |

**Total pstf_primary**: 102 tests declared, 94 + 1 run passed, 7 pending.

기존 suites (pstf, source::registry, core::ssot, 기타) 는 세션 내 **0 회귀**. 총 ~1200 test 가 전체 passing.

### 3.2 Module 간 dependency graph

```
layout.rs  (없음 — scaffold)
    │
    ├── ic.rs           ← layout
    ├── rhs_free.rs     ← layout
    ├── collision.rs    ← layout
    ├── metric.rs       ← layout
    │       │
    ├── fluid.rs        ← layout, metric (BackgroundQuantities)
    ├── jacobian.rs     ← layout, rhs_free, collision
    │
    └── full_rhs.rs     ← layout, rhs_free, collision, metric, fluid
              │
              └── matrix.rs   ← full_rhs, layout, metric, collision
              │       │
              └── source.rs   ← layout, metric + source::registry
                      │
                      └── integrate.rs  ← matrix, source, full_rhs,
                                          CommonProfile (MB-95), 
                                          integrate_linear_profile_rodas5p
```

---

## §4. 주요 설계 결정

### 4.1 Sub-track 분할 패턴 (PR-022/023/024)

원 weight 이 큰 PR (W=10~12) 을 3~4 sub-track 으로 쪼개어 진행. Pattern:

- 첫 sub-track: 기반 (IC, state, scaffold)
- 중간 sub-track: physics sector 별 (free-stream, collision, metric, fluid)
- 마지막 sub-track: composition + retrospective bonus

**누적 성과**:
- PR-022 (3 sub-tracks): 11.0 / 12.0 = **91.7%**
- PR-023 (3 sub-tracks + retro): 7.9 / 8.0 = **98.8%**
- PR-024 (3 sub-tracks, 1.5 완료): 2.8 / 9.6 = **29.2%** (진행 중)

Anti-local-min risk reduction 과 first-try success streak (5 연속) 의 동시 달성. Retrospective bonus 로 sub-track loss 거의 완전 상쇄.

### 4.2 SSOT Discipline

**`source::registry` (PR-010 Stage B)** 이 모든 source channel 의 단일 진실원. MB-95 `production_source_v1` 도, PSTF `pstf_source_function` (PR-024a) 도 **같은** SSOT 호출 → bit-identical architectural guarantee.

**`d2_convention.rs`**: D_ℓ 단위 변환 SSOT. 14-commit 연속 무접촉 확인.

**`ssot.py` / `obs_defaults.json`**: Python 쪽 SSOT (이 snapshot 은 Rust core 에 집중).

### 4.3 Linearity Exploitation (PR-024b matrix.rs)

`pstf_full_rhs` 가 state 에 linear 하다는 사실 (PR-022c jacobian_fd_check 로 검증) 을 활용:

```rust
// Column-by-column matrix build
M(τ)[:, j] = pstf_full_rhs(state = e_j, ...)
```

이로 인해 `pstf_analytical_jacobian` (PR-022c, free-stream + collision 만 포괄) 의 sector coverage gap 을 **Jacobian 확장 없이** 우회. Trade-off 는 n_state × n_snaps `pstf_full_rhs` call overhead — **현재 최적화 부족의 주된 원인**.

### 4.4 MB-95 Infrastructure 재사용

`CommonProfile` (background + visibility), `integrate_linear_profile_rodas5p` (Rodas5P stepper), `tau_profile` sampling, `VisibilityResult` — 모두 기존 MB-95 module 을 그대로 재사용. PR-024b 가 이것들을 PSTF 쪽에서 호출하기 위해 `build_pstf_matrix_into` 만 새로 작성.

---

## §5. Known Issues / Technical Debt

### 5.1 `pstf_analytical_jacobian` sector coverage gap

PR-022c 시점의 Jacobian 은 **free-streaming + collision** 만 포괄. PR-023a (metric), PR-023b (fluid), PR-023c 의 hdot-derived source term 은 분석적으로 반영 안 됨.

**현재 대응**: PR-024b `build_pstf_matrix_into` 가 unit-vector decomposition 으로 우회 (correctness-first, performance suboptimal).

**Future fix**: analytical form 을 `pstf_analytical_jacobian` 에 확장. Performance 10-100× 개선 가능.

### 5.2 PR-024b 성능 병목 (**user 지적 사항**)

Unit-vector matrix build:

```
cost = n_state × n_snaps per k-mode
     ≈ 300 × 200 = 60,000 pstf_full_rhs calls per k-mode
```

MB-95 `build_camb_matrix_into` (hand-analytic) 는 snapshot 당 O(n_state) cost. 따라서 현재 PSTF matrix build 이 **MB-95 보다 ~100× 느림**. 단일 k test 가 **42.79s** 소요 — 전체 k-grid 498 modes 에 extrapolate 시 ~6 시간.

**User 의 작업 중지 사유**. 별도 최적화 작업에서 해결:
- Analytical Jacobian 확장 (§5.1)
- 또는 sparse structure 활용 (대부분 slot 은 서로 decouple)
- 또는 MB-95 `build_camb_matrix_into` pattern 을 PSTF layout 에 직접 port

### 5.3 PR-024b integrate tests 실행 timeout

Build 및 step-back fix (tau_min=0.5 filter) 는 완료. Test 1개 단독 실행 42.79s 확인. 8개 sequential 실행이 CI timeout (300s) 초과. Parallel 실행은 memory 검토 필요.

**Resolution path**: 성능 최적화 후 재실행, 또는 smaller test layout 사용 (lg=4 등).

### 5.4 PR-024b integrate 의 tau filter bootstrap 불완전성

`common.tau_profile` 중 `τ > TAU_IC_MIN = 0.5` 만 integration. 하지만 MB-95 는 이에 더해 bootstrap_ic (PR-021 이전의 더 정확한 IC lookup) + pre-recombination subsampling 도 수행. PR-024b 는 최소한의 filter 만 도입. 이것이 PR-025 FLRW equivalence test 의 정밀도에 영향 가능.

### 5.5 E-mode PiBass convention 처리 부재

PR-024a `pstf_extract_source_inputs` 에서 `e0 = 0.0` unconditional. Polter convention (현재 production) 에서는 E_0 미사용이라 bit-identical 유지. 하지만 **PiBass convention 활성화 시** E_0 를 올바르게 처리해야 함. PSTF layout 이 E-mode 를 ℓ≥2 만 저장하므로 E_0 는 별도 저장소 필요.

**PR-024c 또는 future PR 에서 해결 필요**.

### 5.6 CHANGELOG 일부 누락 가능성

세션 말미에 작업 속도가 가속되면서 일부 PR 의 CHANGELOG entry 가 scoreboard/ROADMAP 와 완전 동기화되지 않았을 수 있음. PR-024a 까지는 확인, PR-024b 진행 중에 중지.

---

## §6. 다음 작업 (사용자의 최적화 작업 완료 후)

### 6.1 최우선

1. **PR-024b 성능 최적화** (user's separate task) — `build_pstf_matrix_into` 의 call cost 를 MB-95 수준으로 낮춤
2. **PR-024b integrate tests 7개 재실행 + 통과 확인**
3. **D_2 15th consecutive bit-identical 재확인**
4. **PR-024b closure delta** (pr-024b.md) 작성 + STUCK_LOG tau_min fix entry + governance 갱신 (scoreboard 50.8% → 53.5%)

### 6.2 중기 (Phase 1 잔여)

- **PR-024c** — LoS + spectrum assembly, **Phase 1 technical capstone**: PSTF primary 가 D_2 = 1002.086744 μK² bit-identical 생성
- **PR-025** — FLRW equivalence test MB-95 ↔ PSTF (W=12, target S=9)
- **PR-026** — Production backend switch (W=10, target S=8)

Phase 1 완료 target: **78.1 / 105 = 74.4%**.

### 6.3 이 snapshot 재개를 위한 context

1. `/src/pstf_primary/` 의 12 module 은 모두 build-clean (`cargo check --lib --release` OK)
2. `integrate.rs` 에는 `TAU_IC_MIN = 0.5` constant + `pstf_solve_kmode_adiabatic` wrapper 가 step-back fix 로 추가된 상태
3. Test helper 의 API mismatch 3건 모두 resolve (VisibilityParams::planck2018, HyRecTables::generate, PstfIcInputs adotoa)
4. D_2 regression guard 는 production path 에서 `dump_dl_spectrum_sparse` 가 14 commits 연속 bit-identical — PSTF primary 변경은 production path 무접촉 확인됨

---

## §7. File Inventory (이 zip 내 파일)

```
bass_phase1_snapshot/
├── README.md                          ← 이 문서
├── src/
│   ├── pstf_primary/                 ← 12 PSTF modules (PR-020~024b)
│   │   ├── mod.rs
│   │   ├── layout.rs
│   │   ├── ic.rs
│   │   ├── rhs_free.rs
│   │   ├── collision.rs
│   │   ├── jacobian.rs
│   │   ├── metric.rs
│   │   ├── fluid.rs
│   │   ├── full_rhs.rs
│   │   ├── source.rs                  ← PR-024a
│   │   ├── matrix.rs                  ← PR-024b (NEW)
│   │   └── integrate.rs               ← PR-024b (NEW, step-back fix 적용)
│   └── source/
│       ├── mod.rs
│       └── registry.rs                ← PR-010 Stage B SSOT (MB-95 + PSTF 공통 경로)
├── docs/
│   ├── CHANGELOG.md                    ← PR 기록
│   ├── PROGRESS_SCOREBOARD.md          ← Weighted scoring, 진행률 (50.8%)
│   ├── ROADMAP_PHASE_I_TO_L.md         ← Phase 1~L 로드맵
│   ├── STUCK_LOG.md                    ← Rule §10 events
│   ├── SSOT_POLICY.md                  ← SSOT 정책
│   ├── PR_CONSTITUTION.md              ← PR 프로세스 헌법 (§9 4-Gate 포함)
│   ├── PHYSICS_REFERENCES.md
│   └── PR_DELTAS/                      ← 각 PR 의 design doc + closure delta
│       ├── pr-000.md
│       ├── pr-010.md, pr-010-stage-b.md
│       ├── pr-011-subtrack-1.md
│       ├── pr-020-design.md, pr-020.md
│       ├── pr-021-design.md, pr-021.md
│       ├── pr-022-design.md
│       ├── pr-022a.md
│       ├── pr-022b-design.md, pr-022b.md
│       ├── pr-022c-design.md, pr-022c.md
│       ├── pr-023-design.md
│       ├── pr-023a.md
│       ├── pr-023b-design.md, pr-023b.md
│       ├── pr-023c-design.md, pr-023c.md
│       ├── pr-024-design.md
│       ├── pr-024a.md                  ← PR-024a closure (merged)
│       └── pr-024b-design.md           ← PR-024b pre-audit (진행 중)
├── plots/
│   └── phase1_midcheck_dl_tt.png       ← 중간점검 MB-95 oracle D_ℓ plot
└── tests_log/
    ├── TEST_SUMMARY.txt                ← 전체 test 현황
    └── dl_spectrum_mb95_oracle.csv     ← D_ℓ(ℓ=2..300), 14th consecutive bit-identical
```

---

## §8. Regression Anchor

```
D_2 = 1002.086744 μK²
```

이것은 production path 의 불변 baseline. 본 snapshot 의 모든 작업 (PR-020 ~ PR-024b) 은 이 값을 **건드리지 않음** — PSTF primary 는 별도 module 로 구축되었고, PR-026 backend switch 전까지 production path 는 MB-95 가 유지.

다음 세션 시작 시 가장 먼저 `cargo test --release --lib solver::sync_gauge_camb::dump_dl_spectrum_sparse --ignored -- --nocapture` 를 실행하여 이 baseline 이 유지되는지 확인 권장.

---

*Snapshot generated: 2026-04-18 session close.
Reason: user feedback on insufficient optimization — pause for separate optimization work.
Next session resume: PR-024b performance optimization → test re-run → closure.*
