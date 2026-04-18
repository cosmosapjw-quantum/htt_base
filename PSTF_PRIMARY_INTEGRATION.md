# bass_rs — Phase 1 PSTF Primary Migration Integrated

> 사용자의 local `bass/` crate 에 **Phase 1 PSTF Primary Migration (PR-020~PR-024b)** 전체를 통합한 빌드 가능 스냅샷.
>
> **Build status**: ✅ `cargo check --lib --tests` clean (0 errors, 441 warnings — 기존 crate 수준과 동일)
> **Integration date**: 2026-04-18

---

## §1. 통합된 내용

### 신규 모듈

```
src/core/ssot.rs                        (NEW — PR-010 Stage B SSOT primitives)
src/source/mod.rs                       (NEW — PR-010 source registry module root)
src/source/registry.rs                  (NEW — SSOT-routed source channel helpers)
src/solver/pstf_primary/                (NEW — 12 modules, PR-020~PR-024b)
    ├── mod.rs
    ├── layout.rs        (PR-020  — PstfFlrwLayout, scaffold)
    ├── ic.rs            (PR-021  — pstf_adiabatic_ic)
    ├── rhs_free.rs      (PR-022a — free-streaming RHS, G2 full via retro)
    ├── collision.rs     (PR-022b — Thomson collision)
    ├── jacobian.rs      (PR-022c — sparse analytical Jacobian)
    ├── metric.rs        (PR-023a — metric state + RHS, pstf_hdot)
    ├── fluid.rs         (PR-023b — CDM + baryon fluid RHS)
    ├── full_rhs.rs      (PR-023c — 4 sector dispatcher)
    ├── source.rs        (PR-024a — LoS source function, PstfSourceTerms)
    ├── matrix.rs        (PR-024b — coefficient matrix via unit-vector)
    └── integrate.rs     (PR-024b — Rodas5P time integration)
```

### 수정된 기존 파일

```
src/core/mod.rs          → `pub(crate) mod ssot;` 1 line 추가
src/lib.rs               → `pub(crate) mod source;` 1 line 추가
src/solver/mod.rs        → `pub(crate) mod pstf_primary;` 1 line 추가
```

**Cargo.toml 은 변경 없음** — 신규 외부 dependency 없음 (pure stdlib).

### 신규 governance docs

```
docs/PROGRESS_SCOREBOARD.md     (Phase 1 weighted scoring, 50.8% at snapshot)
docs/ROADMAP_PHASE_I_TO_L.md    (Phase 1~L roadmap)
docs/STUCK_LOG.md               (Rule §10 events log)
docs/SSOT_POLICY.md             (SSOT 정책)
docs/PR_CONSTITUTION.md         (PR 프로세스 헌법, §9 4-Gate)
docs/PHYSICS_REFERENCES.md
docs/CHANGELOG_PSTF_PRIMARY.md  (PR-020~PR-024a closure 기록. 기존 CHANGELOG.md 는 보존)
docs/PR_DELTAS/                 (23 files — 각 PR 의 design + closure)
```

---

## §2. 빌드 및 검증

### 최소 명령

```bash
cd bass/
cargo check --lib           # library compile — 0 errors
cargo check --lib --tests   # test harness compile — 0 errors, build ~2분
```

### PSTF primary 단위 테스트 (Release 권장)

```bash
# 가벼운 테스트부터
cargo test --lib --release solver::pstf_primary::matrix -- --nocapture
cargo test --lib --release solver::pstf_primary::layout -- --nocapture
cargo test --lib --release solver::pstf_primary::ic -- --nocapture

# RHS 모듈들 (중간 무게)
cargo test --lib --release solver::pstf_primary::rhs_free
cargo test --lib --release solver::pstf_primary::collision
cargo test --lib --release solver::pstf_primary::metric
cargo test --lib --release solver::pstf_primary::fluid
cargo test --lib --release solver::pstf_primary::full_rhs

# 무거운 테스트 (integrate: CommonProfile 빌드 + ODE 적분, 테스트당 40s+)
cargo test --lib --release solver::pstf_primary::integrate::tests::identity_solve_kmode_runs -- --nocapture
```

### D_2 regression 확인 (PSTF primary 변경이 production path 에 영향 없는지)

```bash
cargo test --lib --release solver::sync_gauge_camb::dump_dl_spectrum_sparse -- --ignored --nocapture
```
**기대값**: `D_2 = 1002.086744 μK²` (통합 전 baseline 과 동일)

---

## §3. 주요 설계 결정 (우리 세션)

### 3.1 `PstfSourceTerms` (source.rs §0)

이 local bass crate 의 `sync_gauge_camb::SourceTerms` 는 4 fields (`s_total, s_sw, s_dop, s_quad`) 만 보유. 우리 세션 작업은 `s_e` + `polterdot` 추가 필드가 필요 (PATCH 3B polterdot 용).

**선택한 해결**: 기존 `SourceTerms` 수정하지 않고 `pstf_primary::source::PstfSourceTerms` 로컬 struct 도입 (6 fields: 기존 4 + s_e + polterdot). 향후 PR-025 equivalence 시 변환 helper 로 처리.

### 3.2 Unit-vector matrix build (matrix.rs)

`pstf_analytical_jacobian` (PR-022c) 은 PR-023a/b 이전 작성이라 metric/fluid sector coverage gap 있음. PR-024b 는 **Jacobian 확장 대신** `pstf_full_rhs` 의 linearity 를 활용하여 column-by-column coefficient matrix 구축:

```
M(τ)[:, j] = pstf_full_rhs(state = e_j, ...)
```

**Trade-off**: per-snapshot n_state column evaluations — 현재 `build_camb_matrix_into` 의 hand-analytic 대비 ~100× 느림. **User 의 최적화 작업 대상**.

### 3.3 Layout accessor range 교훈 (PR-024a)

PSTF `LmLayout` 의 E-mode storage 는 ℓ≥2 only (`n_photon_e = (lg+1)² − 4`). MB-95 `CambLayout` 은 `e_mode(0)` slot 보유 (PiBass convention 용). PR-024a 에서 `i_photon_e_m0(0)` 호출이 assertion panic → `e0 = 0.0` unconditional 로 fix (Polter convention 에서 E_0 미사용).

모든 PR-024b+ 작업에 "Layout accessor range check" pre-audit checklist 추가.

### 3.4 tau filtering (integrate.rs)

`common.tau_profile` 의 초기 몇 snapshot 은 τ ≤ 0 가능. `pstf_free_streaming_rhs` 의 tau-based ℓ_max truncation `(ℓ+1)/τ · Θ_ℓmax` 는 τ > 0 요구. MB-95 `solve_camb_kmode` 는 `tau_ic_min = 0.5` 로 filter — 이를 PR-024b `TAU_IC_MIN = 0.5` constant 로 도입. `pstf_solve_kmode_adiabatic` wrapper 가 filter boundary 에서 IC 자동 생성.

---

## §4. 주요 현황 및 미해결 이슈

### 세션 완료 상태

- **Phase 1 progress**: 50.8% (53.3 / 105 W·S/10)
- **D_2 baseline**: 1002.086744 μK² bit-identical across 14 consecutive commits (통합 전까지)
- **Test counts (release build 에서 verified)**:
  - `pstf_primary::layout` 12 passed
  - `pstf_primary::ic` 10 passed
  - `pstf_primary::rhs_free` 12 passed (retrospective G2 포함)
  - `pstf_primary::collision` 11 passed
  - `pstf_primary::jacobian` 9 passed
  - `pstf_primary::metric` 11 passed
  - `pstf_primary::fluid` 10 passed
  - `pstf_primary::full_rhs` 6 passed
  - `pstf_primary::source` 10 passed
  - `pstf_primary::matrix` 3 passed
  - `pstf_primary::integrate` 1/8 verified (나머지 7 통합 환경에서 재확인 필요)

### Known Issues (docs/PROGRESS_SCOREBOARD.md 의 §5)

1. **`pstf_analytical_jacobian` sector coverage gap** — PR-023a/b/c 기여 반영 안 됨
2. **PR-024b 성능 병목** — unit-vector matrix build 의 O(n_state × n_snaps) cost
3. **PR-024b integrate tests 4번 이상 실행 대기** — step-back fix (tau_min filter) 후 통합 환경에서 재검증 필요
4. **PR-024b bootstrap 불완전성** — MB-95 의 full bootstrap_ic lookup 미반영 (tau_min=0.5 filter 만 도입)
5. **E-mode PiBass convention 미지원** — Polter 만 지원, PiBass 활성화 시 E_0 저장 필요
6. 세션 말미 CHANGELOG 일부 sync 누락 가능성

---

## §5. 다음 작업

### 즉시 (user 의 최적화 후)

- **PR-024b 성능 최적화** — `build_pstf_matrix_into` 의 analytic form 작성, 또는 `pstf_analytical_jacobian` 확장
- **PR-024b integrate 8 tests 재확인**
- **D_2 15th consecutive bit-identical 확인**
- **PR-024b closure delta** + scoreboard 갱신 (50.8% → ~53.5%)

### Phase 1 잔여

- **PR-024c** (W=4, target S=8) — LoS integration + C_ℓ spectrum. **Phase 1 technical capstone — PSTF primary 가 D_2 = 1002.086744 μK² bit-identical 생성**
- **PR-025** (W=12, target S=9) — MB-95 ↔ PSTF FLRW equivalence test
- **PR-026** (W=10, target S=8) — Production backend switch (MB-95 → oracle, PSTF → prod)

Phase 1 완료 target: 78.1 / 105 = **74.4%**

---

## §6. 파일 inventory

```
bass/
├── Cargo.toml              (변경 없음)
├── Cargo.lock              (변경 없음)
├── CHANGELOG.md            (기존 보존)
├── src/
│   ├── lib.rs              (+1 line: pub(crate) mod source;)
│   ├── core/
│   │   ├── mod.rs          (+1 line: pub(crate) mod ssot;)
│   │   ├── ssot.rs         (NEW)
│   │   └── ... (기존 파일들)
│   ├── source/             (NEW directory)
│   │   ├── mod.rs
│   │   └── registry.rs
│   ├── solver/
│   │   ├── mod.rs          (+1 line: pub(crate) mod pstf_primary;)
│   │   ├── pstf_primary/   (NEW directory, 12 modules)
│   │   └── ... (기존 파일들)
│   └── ... (기존 모듈들)
├── docs/
│   ├── ... (기존 2 파일)
│   ├── PROGRESS_SCOREBOARD.md      (NEW)
│   ├── ROADMAP_PHASE_I_TO_L.md     (NEW)
│   ├── STUCK_LOG.md                (NEW)
│   ├── SSOT_POLICY.md              (NEW)
│   ├── PR_CONSTITUTION.md          (NEW)
│   ├── PHYSICS_REFERENCES.md       (NEW)
│   ├── CHANGELOG_PSTF_PRIMARY.md   (NEW, 기존 CHANGELOG.md 와 별개)
│   └── PR_DELTAS/                  (NEW, 23 files)
└── tests/, scripts/, logs/         (변경 없음)
```

---

## §7. Regression anchor

```
D_2 = 1002.086744 μK²
```

이것은 production path 의 불변 baseline. 우리 세션 작업 (PR-020 ~ PR-024b) 모든 변경은 이 값을 **건드리지 않음** — PSTF primary 는 별도 module tree 로 구축. PR-026 backend switch 전까지 production 은 MB-95 sync_gauge_camb 가 유지.

통합 후 가장 먼저 실행 권장:

```bash
cargo test --lib --release solver::sync_gauge_camb::dump_dl_spectrum_sparse -- --ignored --nocapture
```

`ℓ=2, D_ℓ = 1002.086744` 가 출력되면 통합이 production path 에 영향 없음 확인.

---

*Integrated into local bass/ crate: 2026-04-18.
Build: cargo check --lib (0 errors), cargo check --lib --tests (0 errors).
Cargo.toml 변경 없음 — 추가 의존성 없이 pure integration.*
