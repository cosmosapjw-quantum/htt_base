# PR-023c Design Document — Full RHS Composition + PR-022a G2 승격

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-18
> **Target PR**: PR-023c (sub-track c of PR-023, 마지막)
> **Dependency**: PR-020~022c ✅, PR-023a ✅, PR-023b ✅
> **Weight**: 3
> **Target score**: 8
> **Special**: PR-022a G2 partial → full **retrospective 승격** (+0.6 W·S/10)

---

## §1. Scope

PSTF primary 의 모든 sector (free-streaming + collision + metric + fluid) 를 합성하는 `pstf_full_rhs()` dispatcher 구현. 이를 통해 PR-022a 의 `metric_monopole_source: f64 = 0.0` placeholder 를 **실제 PR-023a 값으로 wire-up**. 이 wire-up 의 결과로 PR-022a 의 G2 partial (cap 7, score 7) 이 **full FLRW (cap 8, score 8) 로 승격 가능**.

### 포함된 것
- `src/solver/pstf_primary/full_rhs.rs` (예상 ~220 줄)
  - `FullRhsInputs` struct — 모든 sector 의 input 통합
  - `pstf_full_rhs()` — hdot 한 번 compute 후 4 sector 합성 (additive)
- PR-022a `rhs_free.rs` 에 새 test `regression_rhs_matches_mb95_full_path_with_metric` 추가
- `PROGRESS_SCOREBOARD.md` §2.1 에서 PR-022a score 7 → 8 retrospective 갱신 + footnote 추가
- `CHANGELOG.md` 에 retrospective 승격 명시

### 포함되지 않은 것
- LoS source / production integration: PR-024
- MB-95 ↔ PSTF equivalence test: PR-025
- Backend switch: PR-026
- Massive ν contribution: future PR

---

## §2. Dispatcher design

### 2.1 hdot compute-once pattern

4 sector (free_streaming, collision, metric, fluid) 중 **3개** 가 `hdot` 을 간접 또는 직접 의존:

- free_streaming (PR-022a): `metric_monopole_source = −hdot/6` → photon/ν ℓ=0
- metric (PR-023a): `sigmadot` 에 `etak` 포함, 내부에서 hdot 계산하지 않음 (etakdot 은 dgq/2 이므로 직접 계산)
- fluid (PR-023b): `clxcdot = −hdot/2`, `clxbdot = −k·v_b − hdot/2`
- collision (PR-022b): hdot 무관

**Efficient pattern**:
```rust
pub(crate) fn pstf_full_rhs(
    state: &[f64], dy: &mut [f64],
    inputs: &FullRhsInputs, layout: &PstfFlrwLayout
) {
    // 1. Read v_b from state (needed for both metric and fluid)
    let v_b = state[layout.i_baryon_v_m0()];
    
    // 2. Compute hdot ONCE via PR-023a
    let metric_inputs = MetricInputs { k: inputs.k, bg: inputs.bg };
    let hdot = pstf_hdot(state, v_b, &metric_inputs, layout);
    let metric_monopole_source = -hdot / 6.0;
    
    // 3. Compose 4 sectors (additive)
    let rhs_inputs = RhsInputs {
        k: inputs.k, tau: inputs.tau,
        metric_monopole_source,  // ← wire-up PR-022a placeholder
    };
    pstf_free_streaming_rhs(state, dy, &rhs_inputs, layout);  // PR-022a
    
    let coll_inputs = CollisionInputs { ... };
    pstf_thomson_collision(state, dy, &coll_inputs, layout);  // PR-022b
    
    pstf_metric_rhs(state, dy, v_b, &metric_inputs, layout);  // PR-023a
    
    let fluid_inputs = FluidInputs {
        k: inputs.k, h_conformal: inputs.bg.h_conformal,
        cs2b: inputs.cs2b, hdot,
    };
    pstf_fluid_rhs(state, dy, &fluid_inputs, layout);  // PR-023b
}
```

### 2.2 FullRhsInputs struct

```rust
pub(crate) struct FullRhsInputs {
    pub(crate) k: f64,
    pub(crate) tau: f64,
    pub(crate) bg: BackgroundQuantities,
    pub(crate) kappa_dot: f64,
    pub(crate) r_b: f64,
    pub(crate) use_pol_feedback: bool,
    pub(crate) frame: FrameConvention,
    pub(crate) cs2b: f64,
}
```

기존 sector-specific struct (RhsInputs, CollisionInputs, MetricInputs, FluidInputs) 와 dispatch 관계. `FullRhsInputs` 은 모든 parameter 의 superset — dispatcher 가 sub-struct 를 생성하여 sector 로 전달.

### 2.3 Dy initialization 정책

`pstf_full_rhs()` 는 **dy 를 zero-initialize**. 개별 sector RHS 들은 additive 이지만 dispatcher 자체는 "full RHS" 이므로 초기화 책임. Caller 는 pre-filled dy 를 건네면 안됨 (assertion 추가 고려).

---

## §3. PR-022a G2 retrospective 승격 전략

### 3.1 기존 G2 test 와 새 test 구분

- 기존 test `regression_rhs_matches_mb95_freestream_kappa_zero` — **유지** (partial G2, metric source = 0.0 specific)
- 새 test `regression_rhs_matches_mb95_full_path_with_metric` — **추가** (full G2, wire-up 후)

이렇게 두 test 를 **공존** 시키는 이유:
- 기존 test 가 통과 상태여야 PR-022a 의 original quality 보존 증명
- 새 test 가 통과해야 metric wire-up 후 full FLRW 재현 증명
- 두 test 가 모두 통과 → PR-022a 가 metric 유무 양쪽에서 올바르게 작동 → **G2 full**

### 3.2 새 test 의 구조

```rust
#[test]
fn regression_rhs_matches_mb95_full_path_with_metric() {
    let (layout, state, v_b, rhs_inputs, metric_inputs) = test_fixture_with_metric();
    
    // Compute metric_monopole_source via PR-023a
    let hdot = pstf_hdot(&state, v_b, &metric_inputs, &layout);
    let source = -hdot / 6.0;
    let rhs_in_wired = RhsInputs {
        k: rhs_inputs.k,
        tau: rhs_inputs.tau,
        metric_monopole_source: source,  // wire-up
    };
    
    let mut dy = vec![0.0; layout.n_state];
    pstf_free_streaming_rhs(&state, &mut dy, &rhs_in_wired, &layout);
    
    // Expected: MB-95 `camb_rhs` photon ℓ=0/1/2/... with ACTUAL hdot
    // (opac = 0 to isolate free-streaming + metric coupling)
    let k = rhs_inputs.k;
    let theta = |ell: usize| state[layout.i_photon_i_m0(ell)];
    
    // ℓ=0: dΘ_0 = −k·Θ_1 − hdot/6
    let mb95_0 = -k * theta(1) - hdot / 6.0;
    let got_0 = dy[layout.i_photon_i_m0(0)];
    assert!((got_0 - mb95_0).abs() < 1e-13,
        "ℓ=0 with metric: {} vs MB-95 {}", got_0, mb95_0);
    
    // ℓ=1..ℓ_max: same as PR-022a but with source wired
    // ...
}
```

이 test 가 통과하면 PR-022a 의 G2 는 **metric wire-up 하에서 full FLRW path** 재현을 증명. Cap 7 → cap 8 승격 정당.

### 3.3 Scoreboard 갱신 절차

PR-023c closure 의 일환으로:

```
PR-022a 행: score 7 → 8
           W·S/10: 4.2 → 4.8
           "G2 partial" → "G2 full (retrospectively via PR-023c)"
           각주 ³ 갱신 또는 새 각주 추가

§2.3 진행률 재계산: +0.6 W·S/10 추가 반영
§2.4 해석 업데이트
§3 retroactive scoring 에 "PR-023c 후 PR-022a retrospective 승격 이벤트" 추가
```

### 3.4 Retrospective 의 안전성

PR-022a 의 기존 test 는 **건드리지 않음** — 기존 `regression_rhs_matches_mb95_freestream_kappa_zero` 이 그대로 pass 하는 것을 확인하고 새 test 추가. 즉 기존 G2 partial evidence 를 **제거하지 않고**, 새 evidence 로 **승격**.

이것은 scoring discipline (`PR_CONSTITUTION §9.5`) 의 "scoring retroactive 는 evidence 강화 시에만 허용, 약화 시 불가" 규칙 준수.

---

## §4. TDD gate (예상 tests)

### Dispatcher tests (5 tests) — `full_rhs.rs`

- `identity_dispatcher_composes_all_sectors` — dispatcher 의 dy 결과가 4 sector 개별 compute 의 합과 정확히 일치
- `regression_dispatcher_matches_mb95_full_path` — **G2 full** — `pstf_full_rhs()` 결과가 MB-95 `camb_rhs` 전체 (photon + ν + metric + fluid, opac 포함) 와 rel err < 1e-13 bit-identical at ℓ={0,1,2,3,5,ℓ_max}
- `regression_dispatcher_multiple_k` — k ∈ {1e-4, 1e-2, 1e-1} 전범위
- `limit_zero_kappa_dot_free_plus_metric_only` — κ̇=0 에서 collision term 모두 zero, free-streaming + metric + fluid 합산만 남음
- `caveat_hdot_computed_once` — dispatcher 내부에서 hdot 이 한 번만 compute 됨을 간접 검증 (performance invariant, 구현상 inline 추적)

### PR-022a retrospective test (1 test) — `rhs_free.rs` 에 추가

- `regression_rhs_matches_mb95_full_path_with_metric` — PR-022a metric wire-up 후 full FLRW 재현 (§3.2 specification)

**총 6 tests** (PR-023c 신규) + 1 test (PR-022a retrospective).

---

## §5. Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일 + PR-022a test 1개 추가, 기존 회귀 없음 |
| **G2 FLRW (full)** | **✅** | `regression_dispatcher_matches_mb95_full_path` 이 MB-95 `camb_rhs` 전체 (metric + fluid + photon/ν + collision) 와 bit-identical. **Phase 1 에서 가장 comprehensive G2 test** — 모든 sector 통합 |
| G3 PHYS | ✅ | Identity (dispatcher composition) + limit (κ̇=0) + caveat (hdot compute once) |
| G4 CROSS | ✅ | MB-95 `camb_rhs` 전체 직접 대조. Partial comparison 없이 full end-to-end |

**Score: 8/10** forecast.
- G1+G2 full+G3+G4 → cap 9
- Publication figure 없음 → final 8
- **Dispatcher 가 Phase 1 내 가장 comprehensive 한 test** 이므로 score 8 가 타당 (PR-022b/PR-023a 와 동일 tier)

Weighted: W=3 × S=8/10 = **W·S/10 = 2.4** (forecast 정확).

**Retrospective bonus**: PR-022a score 7→8, W·S/10 4.2 → 4.8, **Δ = +0.6**.

**합산 delta**: 2.4 + 0.6 = **3.0**.

Phase 1 진행률: 45.2% → **48.3%** (47.5 + 3.0)/105.

---

## §6. Anti-local-min triggers

1. **Dy accumulation double counting** — 4 sector 가 additive 인 가정. 만약 어떤 sector 가 dy 를 zero-initialize 하면 이전 sector 의 기여가 사라짐. **확인**: PR-022a `pstf_free_streaming_rhs` 는 `dy[idx] = ...` (assignment) 이 아니라 `dy[idx] += ...` 또는 overwrite? 재검증 필요.

2. **Metric monopole source sign 혼동** — `−hdot/6` 의 sign. PR-022a 기존 test 가 placeholder=0.0 이므로 sign 검증 없음. `regression_rhs_matches_mb95_full_path_with_metric` 이 catch.

3. **hdot 재계산 실수** — dispatcher 에서 hdot 을 compute 하고 free_streaming source + fluid 에 둘 다 전달해야 함. 둘 사이에 값이 다르면 inconsistent. Structure: 변수 `let hdot = ...` 로 저장 후 양쪽에서 참조.

---

## §7. PR-022a `pstf_free_streaming_rhs` 의 dy 쓰기 방식 재확인

Anti-local-min §6.1 trigger 해소를 위해 사전 확인:

**Expected**: `pstf_free_streaming_rhs` 는 `dy[idx] += ...` (additive) 이어야 dispatcher pattern 작동.

만약 assignment (`dy[idx] = ...`) 이면 dispatcher 에서 순서 중요 (free_streaming 을 가장 먼저 호출해야 함). PR-022a pre-audit 에서 이것을 확인:

- PR-022a 의 additive pattern 이 보장되었는지 → `rhs_free.rs` 소스 직접 조회 필요
- 만약 assignment 면 dispatcher 에서 free_streaming 을 **가장 먼저** 호출하여 dy 를 zero 로 시작 → 다른 sector 들이 additive 로 추가

**해결책**: Dispatcher 에서 (1) `dy.fill(0.0)` 로 zero-init (2) 4 sector 순차 호출. 어느 sector 가 assignment 든 additive 든 동일 결과 — 단 sector 호출 순서는 상관없어야 함.

PR-023c 구현 시 각 sector 의 실제 write 방식 (assignment vs +=) 을 grep 으로 확인하여 dispatcher 호출 순서 결정.

---

## §8. 즉시 다음 행동

동일 turn 내:
1. **`pstf_free_streaming_rhs` 의 dy 쓰기 방식 확인** (assignment vs +=)
2. **PR-023c scaffold** — `src/solver/pstf_primary/full_rhs.rs` 신설
3. `FullRhsInputs`, `pstf_full_rhs()` 구현
4. 6 tests 작성 (§4)
5. PR-022a retrospective test 추가 (`rhs_free.rs` tests mod 에 1개)
6. D_2 13th consecutive 재확인
7. `pr-023c.md` closure delta + scoreboard retrospective 갱신 (PR-022a score 7→8, Phase 1 진행률 45.2% → **48.3%**)

---

*PR-023c 는 PR-023 sub-track 의 마지막 + Phase 1 최초의 **retrospective 승격 이벤트**. Dispatcher 구현은 technical 하나 retrospective logic (PR-022a evidence 강화) 은 scoring discipline 의 precedent 설정. PR-024 (LoS source + solve_pstf_spectrum, W=12) 가 다음 대상 — Phase 1 남은 single-largest PR.*
